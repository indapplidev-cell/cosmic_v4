"""EN: Telegram link/reset services with hashed tokens and outbox retry queue.
RU: Сервисы привязки/reset через Telegram с хешированными токенами и retry-очередью outbox.
"""

from __future__ import annotations

import base64
import logging
import os
import re
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from server.db.sessions.session_factory import get_session
from server.db.models.profile_user import ProfileUser
from server.db.models.refresh_token import RefreshToken
from server.db.models.telegram_account import TelegramAccount
from server.db.models.telegram_link_token import TelegramLinkToken
from server.db.models.telegram_outbox import TelegramOutbox
from server.db.models.telegram_reset_challenge import TelegramResetChallenge
from server.db.models.telegram_reset_request import TelegramResetRequest
from server.db.models.telegram_verify_challenge import TelegramVerifyChallenge
from server.db.models.user import User
from server.app.security.passwords import hash_password
from server.app.security.tokens import gen_6digit_code, hash_code
from server.app.security.validators import reject_control_chars
from server.engine.validation.user_value_normalizer import (
    normalize_user_value_for_storage,
)

_LOG = logging.getLogger("cosmic.telegram_service")
_TOKEN_ALLOWED = re.compile(r"^[A-Za-z0-9_-]{1,48}$")


def _env_int(name: str, default: int) -> int:
    """EN: Read integer env value safely with fallback.
    RU: Безопасно прочитать целочисленное env-значение с fallback.
    """

    raw = os.getenv(name, str(default)).strip()
    try:
        return int(raw)
    except Exception:
        return int(default)


def _reset_secret() -> str:
    """EN: Read reset secret used for hashing one-time codes.
    RU: Прочитать reset-секрет, используемый для хеширования одноразовых кодов.
    """

    return os.getenv("RESET_SECRET", "").strip()


def _mask_token(token: str) -> str:
    """EN: Mask token value for logs without exposing full secret.
    RU: Замаскировать токен в логах без раскрытия полного секрета.
    """

    value = str((token or "").strip())
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}...{value[-4:]}"


def _mask_code(code: str) -> str:
    """EN: Mask one-time code/token for diagnostics without revealing full value.
    RU: Маскировать одноразовый код/токен для диагностики без раскрытия полного значения.
    """

    value = str((code or "").strip())
    if not value:
        return "-"
    if len(value) <= 8:
        return f"{value[:1]}...{value[-1:]}(len={len(value)})"
    return f"{value[:4]}...{value[-4:]}(len={len(value)})"


def _gen_reset_link_code() -> str:
    """EN: Generate opaque reset_link_code token (not 6-digit) for Telegram reset flow.
    RU: Сгенерировать непрозрачный reset_link_code токен (не 6-значный) для Telegram reset flow.
    """

    token = base64.urlsafe_b64encode(os.urandom(24)).decode("ascii").rstrip("=")
    token = str(token).strip()
    if token.isdigit():
        token = f"A{token}"
    return token[:48]


def _normalize_telegram_username(raw_value: str | None) -> str:
    """EN: Normalize Telegram username for safe comparisons/logs.
    RU: Нормализовать Telegram username для безопасных сравнений/логов.
    """

    value = str((raw_value or "")).strip().lower()
    if value.startswith("@"):
        value = value[1:]
    return value


def _sync_username_to_profile_tables(session, user_id: int, telegram_username: str | None) -> list[str]:
    """EN: Synchronize confirmed Telegram username to all user-scoped profile columns.
    RU: Синхронизировать подтверждённый Telegram username во все пользовательские профильные колонки.

    EN: This helper updates only rows that belong to the provided user_id and is called
    strictly after successful app-side `/telegram/link/confirm`.
    RU: Этот helper обновляет только строки указанного user_id и вызывается
    строго после успешного app-side `/telegram/link/confirm`.
    """

    normalized_username = str((telegram_username or "").strip()) or None
    normalized_expected = _normalize_telegram_username(normalized_username)
    updated_targets: list[str] = []

    profile_row = session.scalar(select(ProfileUser).where(ProfileUser.user_id == int(user_id)).limit(1))
    if profile_row is not None:
        profile_row.telegram = normalized_username
        updated_targets.append("profile_users.telegram")

    account_row = session.scalar(select(TelegramAccount).where(TelegramAccount.user_id == int(user_id)).limit(1))
    if account_row is not None:
        account_row.telegram_username = normalized_username
        updated_targets.append("telegram_accounts.telegram_username")

    session.execute(
        update(TelegramLinkToken)
        .where(TelegramLinkToken.user_id == int(user_id))
        .values(expected_tg_username=normalized_expected)
    )
    updated_targets.append("telegram_link_tokens.expected_tg_username")

    return updated_targets


def link_or_update_telegram_account(
    session,
    user_id: int,
    telegram_user_id: int,
    telegram_username: str | None,
) -> tuple[bool, str | None]:
    """EN: Create or update Telegram account binding for user with conflict-safe checks.
    RU: Создать или обновить Telegram-привязку пользователя с безопасной проверкой конфликтов.

    EN: Returns `(True, None)` on success, or `(False, \"TG_ALREADY_LINKED\")` when the same
    Telegram account is already linked to another application user.
    RU: Возвращает `(True, None)` при успехе или `(False, \"TG_ALREADY_LINKED\")`, если этот
    Telegram-аккаунт уже привязан к другому пользователю приложения.
    """

    now_utc = datetime.now(timezone.utc)
    user_id_value = int(user_id)
    tg_user_id_value = int(telegram_user_id)
    tg_username_value = str((telegram_username or "")).strip() or None

    existing_by_tg = session.scalar(
        select(TelegramAccount).where(TelegramAccount.telegram_user_id == tg_user_id_value)
    )
    if existing_by_tg is not None and int(existing_by_tg.user_id) != user_id_value:
        _LOG.info(
            "event=TG_ACCOUNT_LINK_CONFLICT user_id=%s telegram_user_id=%s owner_user_id=%s",
            user_id_value,
            tg_user_id_value,
            int(existing_by_tg.user_id),
        )
        return False, "TG_ALREADY_LINKED"

    account = session.scalar(select(TelegramAccount).where(TelegramAccount.user_id == user_id_value))
    if account is None:
        session.add(
            TelegramAccount(
                user_id=user_id_value,
                telegram_user_id=tg_user_id_value,
                telegram_username=tg_username_value,
                verified_at=now_utc,
            )
        )
    else:
        account.telegram_user_id = tg_user_id_value
        if tg_username_value is not None:
            account.telegram_username = tg_username_value
        account.verified_at = now_utc

    try:
        session.flush()
    except IntegrityError:
        _LOG.info(
            "event=TG_ACCOUNT_LINK_CONFLICT_DB user_id=%s telegram_user_id=%s",
            user_id_value,
            tg_user_id_value,
        )
        return False, "TG_ALREADY_LINKED"

    _LOG.info(
        "event=TG_ACCOUNT_LINK_SAVED user_id=%s telegram_user_id=%s telegram_username=%s",
        user_id_value,
        tg_user_id_value,
        tg_username_value or "-",
    )
    return True, None


def _generate_start_token() -> str:
    """EN: Generate URL-safe Telegram deep-link token with strict allowed charset and max length 48.
    RU: Сгенерировать URL-safe токен deep-link Telegram со строгим набором символов и длиной до 48.
    """

    for _ in range(8):
        raw = base64.urlsafe_b64encode(os.urandom(24)).decode("ascii").rstrip("=")[:48]
        if _TOKEN_ALLOWED.fullmatch(raw):
            return raw
    raise RuntimeError("TOKEN_GEN_FAILED")


def _generate_request_id() -> str:
    """EN: Generate short request id for confirm-code storage rows.
    RU: Сгенерировать короткий request id для строк хранения confirm-кода.
    """

    raw = base64.b32encode(os.urandom(10)).decode("ascii").rstrip("=").lower()
    return raw[:16]


def _invalidate_active_reset_challenges(session, user_id: int, now_utc: datetime) -> None:
    """EN: Mark previous active reset challenges as used so only the newest confirm challenge remains valid.
    RU: Пометить предыдущие активные reset-challenge как использованные, чтобы валидным оставался только самый новый.
    """

    session.execute(
        update(TelegramResetChallenge)
        .where(
            TelegramResetChallenge.user_id == int(user_id),
            TelegramResetChallenge.used_at.is_(None),
            TelegramResetChallenge.expires_at > now_utc,
        )
        .values(used_at=now_utc)
    )


def request_link_code(user_id: int) -> dict:
    """EN: Create one-time Telegram deep-link start token for authenticated user.
    RU: Создать одноразовый deep-link start token для привязки Telegram авторизованного пользователя.
    """

    secret = _reset_secret()
    if not secret:
        return {"ok": False, "error": "RESET_SECRET_MISSING"}

    ttl_sec = max(60, _env_int("TG_LINK_TTL_SEC", 600))
    try:
        start_token = _generate_start_token()
    except Exception:
        return {"ok": False, "error": "TOKEN_GEN_FAILED"}
    code_hash = hash_code(start_token, secret)
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_sec)
    now_utc = datetime.now(timezone.utc)
    expected_tg_username = ""

    try:
        with get_session() as session:
            user = session.get(User, int(user_id))
            if user is None:
                return {"ok": False, "error": "NOT_FOUND"}
            profile_user = session.scalar(
                select(ProfileUser).where(ProfileUser.user_id == int(user_id)).limit(1)
            )
            expected_tg_username = _normalize_telegram_username(
                normalize_user_value_for_storage(profile_user.telegram if profile_user else None)
            )
            if not expected_tg_username:
                return {"ok": False, "error": "TELEGRAM_NOT_SET"}

            session.execute(
                update(TelegramLinkToken)
                .where(
                TelegramLinkToken.user_id == int(user_id),
                TelegramLinkToken.used_at.is_(None),
            )
            .values(used_at=now_utc, used=True)
            )
            token = TelegramLinkToken(
                user_id=int(user_id),
                code_hash=code_hash,
                expected_tg_username=expected_tg_username,
                telegram_user_id=None,
                expires_at=expires_at,
                used=False,
                used_at=None,
                attempts=0,
            )
            session.add(token)
            session.flush()
            _LOG.info(
                "LINK_TOKEN_ISSUED user_id=%s token_mask=%s ttl=%s",
                int(user_id),
                _mask_token(start_token),
                int(ttl_sec),
            )
            return {"ok": True, "code": start_token, "start_token": start_token, "ttl_sec": ttl_sec}
    except Exception:
        return {"ok": False, "error": "DB_ERROR"}


def get_last_link_status(user_id: int) -> dict:
    """EN: Return used/confirmed/ttl status for latest Telegram deep-link code of a user.
    RU: Вернуть used/confirmed/ttl-статус для последнего Telegram deep-link кода пользователя.
    """

    now_utc = datetime.now(timezone.utc)
    with get_session() as session:
        row = session.scalar(
            select(TelegramLinkToken)
            .where(TelegramLinkToken.user_id == int(user_id))
            .order_by(TelegramLinkToken.created_at.desc())
            .limit(1)
        )
        account = session.scalar(
            select(TelegramAccount)
            .where(TelegramAccount.user_id == int(user_id))
            .limit(1)
        )
        confirmed = bool(account is not None and account.verified_at is not None)
        if row is None:
            return {"ok": True, "used": False, "confirmed": confirmed, "ttl_sec": 0}
        ttl_sec = max(0, int((row.expires_at - now_utc).total_seconds()))
        return {
            "ok": True,
            "used": bool(row.used_at is not None or row.used),
            "confirmed": confirmed,
            "ttl_sec": int(ttl_sec),
        }


def confirm_link_latest(telegram_user_id: int, tg_username: str) -> dict:
    """EN: Confirm latest active pending link for Telegram username and issue separate 6-digit confirm_code.
    RU: Подтвердить последний активный pending link по Telegram username и выдать отдельный 6-значный confirm_code.
    """

    secret = _reset_secret()
    incoming_username = str((tg_username or "").strip())
    incoming_username_norm = _normalize_telegram_username(incoming_username)
    tg_user_id_value = int(telegram_user_id or 0)
    now_utc = datetime.now(timezone.utc)
    confirm_ttl_sec = max(60, _env_int("TG_CONFIRM_TTL_SEC", 600))

    if not secret:
        return {"ok": False, "error": "DB_ERROR"}
    if tg_user_id_value <= 0 or not incoming_username_norm:
        return {"ok": False, "error": "NO_PENDING"}

    try:
        with get_session() as session:
            latest_for_username = session.scalar(
                select(TelegramLinkToken)
                .where(TelegramLinkToken.expected_tg_username == incoming_username_norm)
                .order_by(TelegramLinkToken.created_at.desc())
                .limit(1)
            )
            if latest_for_username is None:
                return {"ok": False, "error": "NO_PENDING"}
            if bool(latest_for_username.used) or latest_for_username.used_at is not None:
                return {"ok": False, "error": "ALREADY_USED"}
            if latest_for_username.expires_at <= now_utc:
                return {"ok": False, "error": "NO_PENDING"}

            expected_norm = _normalize_telegram_username(latest_for_username.expected_tg_username)
            if expected_norm != incoming_username_norm:
                return {"ok": False, "error": "MISMATCH"}

            user_id_value = int(latest_for_username.user_id)
            linked_ok, linked_error = link_or_update_telegram_account(
                session=session,
                user_id=user_id_value,
                telegram_user_id=tg_user_id_value,
                telegram_username=incoming_username,
            )
            if not linked_ok:
                return {"ok": False, "error": str(linked_error or "TG_ALREADY_LINKED")}

            latest_for_username.telegram_user_id = tg_user_id_value
            latest_for_username.used = True
            latest_for_username.used_at = now_utc

            confirm_code = gen_6digit_code()
            confirm_hash = hash_code(confirm_code, secret)
            expires_at = now_utc + timedelta(seconds=confirm_ttl_sec)

            request_id = _generate_request_id()
            while session.scalar(
                select(TelegramVerifyChallenge.id).where(TelegramVerifyChallenge.request_id == request_id)
            ) is not None:
                request_id = _generate_request_id()

            session.add(
                TelegramVerifyChallenge(
                    user_id=user_id_value,
                    request_id=request_id,
                    code_hash=confirm_hash,
                    telegram_user_id=tg_user_id_value,
                    telegram_username=incoming_username or None,
                    expires_at=expires_at,
                    sent_at=now_utc,
                    used_at=None,
                    attempts=0,
                )
            )
            session.flush()
            return {
                "ok": True,
                "confirm_code": confirm_code,
                "user_id": user_id_value,
                "tg_username": incoming_username or "",
                "telegram_user_id": tg_user_id_value,
            }
    except Exception:
        _LOG.exception(
            "event=TG_CONFIRM_LATEST_EXCEPTION tg_uid=%s tg_username=%s",
            tg_user_id_value,
            incoming_username_norm or "-",
        )
        return {"ok": False, "error": "DB_ERROR"}


def open_link_token(start_token: str, telegram_user_id: int) -> dict:
    """EN: Validate deep-link token from `/start` and bind it to current Telegram user context.
    RU: Проверить deep-link токен из `/start` и привязать его к контексту текущего Telegram пользователя.
    """

    secret = _reset_secret()
    token_value = str((start_token or "").strip())
    if not secret or not token_value:
        return {"ok": False, "error": "INVALID_TOKEN"}

    now_utc = datetime.now(timezone.utc)
    max_attempts = max(1, _env_int("TG_LINK_MAX_ATTEMPTS", 5))
    token_hash = hash_code(token_value, secret)
    try:
        with get_session() as session:
            token_row = session.scalar(
                select(TelegramLinkToken)
                .where(
                    TelegramLinkToken.code_hash == token_hash,
                    TelegramLinkToken.used_at.is_(None),
                    TelegramLinkToken.expires_at > now_utc,
                )
                .order_by(TelegramLinkToken.created_at.desc())
                .limit(1)
            )
            if token_row is None:
                return {"ok": False, "error": "INVALID_TOKEN"}
            if int(token_row.attempts or 0) >= max_attempts:
                return {"ok": False, "error": "INVALID_TOKEN"}

            token_row.telegram_user_id = int(telegram_user_id)
            token_row.attempts = int(token_row.attempts or 0) + 1
            session.flush()
            return {"ok": True, "token_id": int(token_row.id), "user_id": int(token_row.user_id)}
    except Exception:
        return {"ok": False, "error": "DB_ERROR"}


def confirm_link_token(token_id: int, telegram_user_id: int) -> dict:
    """EN: Confirm Telegram account binding using active deep-link token context.
    RU: Подтвердить привязку Telegram-аккаунта, используя активный контекст deep-link токена.
    """

    now_utc = datetime.now(timezone.utc)
    try:
        with get_session() as session:
            token_row = session.get(TelegramLinkToken, int(token_id))
            if token_row is None:
                return {"ok": False, "error": "INVALID_TOKEN"}
            if token_row.used_at is not None or token_row.expires_at <= now_utc:
                return {"ok": False, "error": "INVALID_TOKEN"}
            if int(token_row.telegram_user_id or 0) != int(telegram_user_id):
                return {"ok": False, "error": "INVALID_TOKEN"}

            linked_ok, linked_error = link_or_update_telegram_account(
                session=session,
                user_id=int(token_row.user_id),
                telegram_user_id=int(telegram_user_id),
                telegram_username=None,
            )
            if not linked_ok:
                return {"ok": False, "error": str(linked_error or "TG_ALREADY_LINKED")}

            token_row.used = True
            token_row.used_at = now_utc
            session.flush()
            return {"ok": True}
    except Exception:
        return {"ok": False, "error": "DB_ERROR"}


def confirm_link_code(code: str, telegram_user_id: int) -> dict:
    """EN: Confirm Telegram link code from bot and upsert verified account mapping.
    RU: Подтвердить код привязки Telegram из бота и выполнить upsert подтвержденной связки аккаунта.
    """

    secret = _reset_secret()
    code_value = (code or "").strip()
    if not secret or not code_value or not code_value.isdigit() or len(code_value) != 6:
        return {"ok": False, "error": "INVALID_CODE"}

    now_utc = datetime.now(timezone.utc)
    code_hash = hash_code(code_value, secret)

    try:
        with get_session() as session:
            token = session.scalar(
                select(TelegramLinkToken)
                .where(
                    TelegramLinkToken.code_hash == code_hash,
                    TelegramLinkToken.used_at.is_(None),
                    TelegramLinkToken.expires_at > now_utc,
                )
                .order_by(TelegramLinkToken.created_at.desc())
                .limit(1)
            )
            if token is None:
                return {"ok": False, "error": "INVALID_CODE"}

            token.used_at = now_utc
            linked_ok, linked_error = link_or_update_telegram_account(
                session=session,
                user_id=int(token.user_id),
                telegram_user_id=int(telegram_user_id),
                telegram_username=None,
            )
            if not linked_ok:
                return {"ok": False, "error": str(linked_error or "TG_ALREADY_LINKED")}
            session.flush()
            return {"ok": True}
    except Exception:
        return {"ok": False, "error": "DB_ERROR"}


def confirm_link_by_code(telegram_user_id: int, link_code: str, tg_username: str | None = None) -> dict:
    """EN: Confirm pending link_code for telegram_user_id, bind account, and issue separate 6-digit confirm_code.
    RU: Подтвердить pending link_code для telegram_user_id, привязать аккаунт и выдать отдельный 6-значный confirm_code.
    """

    secret = _reset_secret()
    link_code_value = str((link_code or "").strip())
    incoming_username_norm = _normalize_telegram_username(tg_username)
    if not secret or not link_code_value:
        _LOG.info(
            "event=TG_CONFIRM_BY_CODE_OUT ok=false error=NO_PENDING user_id=0 tg_uid=%s tg_username=%s link_code=%s detail=missing_secret_or_code",
            int(telegram_user_id or 0),
            incoming_username_norm or "-",
            _mask_code(link_code_value),
        )
        return {"ok": False, "error": "NO_PENDING"}

    now_utc = datetime.now(timezone.utc)
    link_hash = hash_code(link_code_value, secret)
    confirm_ttl_sec = max(60, _env_int("TG_CONFIRM_TTL_SEC", 600))
    tg_user_id_value = int(telegram_user_id)
    tg_username_value = str((tg_username or "").strip())

    try:
        with get_session() as session:
            token_row_any = session.scalar(
                select(TelegramLinkToken)
                .where(
                    TelegramLinkToken.code_hash == link_hash,
                )
                .order_by(TelegramLinkToken.created_at.desc())
                .limit(1)
            )
            if token_row_any is None:
                _LOG.info(
                    "event=TG_CONFIRM_BY_CODE_OUT ok=false error=NO_PENDING user_id=0 tg_uid=%s tg_username=%s link_code=%s detail=code_not_found found=false expired=false used=false ttl_left_sec=-1",
                    tg_user_id_value,
                    incoming_username_norm or "-",
                    _mask_code(link_code_value),
                )
                return {"ok": False, "error": "NO_PENDING"}

            ttl_left_sec = int((token_row_any.expires_at - now_utc).total_seconds())
            token_expired = bool(token_row_any.expires_at <= now_utc)
            token_used = bool(token_row_any.used_at is not None)
            if token_expired or token_used or bool(token_row_any.used):
                detail = "expired" if token_expired else "used"
                _LOG.info(
                    "event=TG_CONFIRM_BY_CODE_OUT ok=false error=NO_PENDING user_id=%s tg_uid=%s tg_username=%s link_code=%s detail=%s found=true expired=%s used=%s ttl_left_sec=%s",
                    int(token_row_any.user_id),
                    tg_user_id_value,
                    incoming_username_norm or "-",
                    _mask_code(link_code_value),
                    detail,
                    str(token_expired).lower(),
                    str(token_used).lower(),
                    int(ttl_left_sec),
                )
                return {"ok": False, "error": "NO_PENDING"}

            token_row = token_row_any

            if int(token_row.telegram_user_id or 0) != tg_user_id_value:
                _LOG.info(
                    "event=TG_CONFIRM_BY_CODE_OUT ok=false error=MISMATCH user_id=%s tg_uid=%s tg_username=%s link_code=%s detail=mismatch_telegram_user_id expected_tg_uid=%s incoming_tg_uid=%s",
                    int(token_row.user_id),
                    tg_user_id_value,
                    incoming_username_norm or "-",
                    _mask_code(link_code_value),
                    int(token_row.telegram_user_id or 0),
                    tg_user_id_value,
                )
                return {"ok": False, "error": "MISMATCH"}

            profile_row = session.scalar(
                select(ProfileUser).where(ProfileUser.user_id == int(token_row.user_id)).limit(1)
            )
            profile_tg_norm = _normalize_telegram_username(
                normalize_user_value_for_storage(profile_row.telegram if profile_row else None)
            )
            if profile_tg_norm and incoming_username_norm and profile_tg_norm != incoming_username_norm:
                _LOG.info(
                    "event=TG_CONFIRM_BY_CODE_OUT ok=false error=MISMATCH user_id=%s tg_uid=%s tg_username=%s link_code=%s detail=mismatch_profile_username profile_tg=%s incoming_tg=%s",
                    int(token_row.user_id),
                    tg_user_id_value,
                    incoming_username_norm or "-",
                    _mask_code(link_code_value),
                    profile_tg_norm,
                    incoming_username_norm,
                )
                return {"ok": False, "error": "MISMATCH"}

            linked_ok, linked_error = link_or_update_telegram_account(
                session=session,
                user_id=int(token_row.user_id),
                telegram_user_id=tg_user_id_value,
                telegram_username=tg_username_value,
            )
            if not linked_ok:
                _LOG.info(
                    "event=TG_CONFIRM_BY_CODE_OUT ok=false error=TG_ALREADY_LINKED user_id=%s tg_uid=%s tg_username=%s link_code=%s detail=telegram_user_already_linked",
                    int(token_row.user_id),
                    tg_user_id_value,
                    incoming_username_norm or "-",
                    _mask_code(link_code_value),
                )
                return {"ok": False, "error": "TG_ALREADY_LINKED"}

            token_row.used = True
            token_row.used_at = now_utc

            confirm_code = gen_6digit_code()
            while confirm_code == link_code_value:
                confirm_code = gen_6digit_code()
            confirm_hash = hash_code(confirm_code, secret)
            expires_at = now_utc + timedelta(seconds=confirm_ttl_sec)

            request_id = _generate_request_id()
            while session.scalar(
                select(TelegramVerifyChallenge.id).where(TelegramVerifyChallenge.request_id == request_id)
            ) is not None:
                request_id = _generate_request_id()

            session.add(
                TelegramVerifyChallenge(
                    user_id=int(token_row.user_id),
                    request_id=request_id,
                    code_hash=confirm_hash,
                    telegram_user_id=tg_user_id_value,
                    telegram_username=tg_username_value or None,
                    expires_at=expires_at,
                    sent_at=now_utc,
                    used_at=None,
                    attempts=0,
                )
            )
            session.flush()
            _LOG.info(
                "event=TG_CONFIRM_BY_CODE_OUT ok=true error=- user_id=%s tg_uid=%s tg_username=%s link_code=%s detail=confirmed",
                int(token_row.user_id),
                tg_user_id_value,
                incoming_username_norm or "-",
                _mask_code(link_code_value),
            )
            return {
                "ok": True,
                "confirm_code": confirm_code,
                "user_id": int(token_row.user_id),
                "tg_username": tg_username_value,
            }
    except Exception as exc:
        _LOG.exception(
            "event=TG_CONFIRM_BY_CODE_OUT ok=false error=DB_ERROR user_id=0 tg_uid=%s tg_username=%s link_code=%s detail=exception exc=%s",
            tg_user_id_value,
            incoming_username_norm or "-",
            _mask_code(link_code_value),
            exc.__class__.__name__,
        )
        return {"ok": False, "error": "DB_ERROR"}


def confirm_link(user_id: int, confirm_code: str) -> dict:
    """EN: Validate bot-issued confirm code and persist Telegram account binding for app user.
    RU: Проверить confirm-код, выданный ботом, и сохранить привязку Telegram-аккаунта для пользователя приложения.

    EN: This flow is the only trusted final confirmation from mobile/desktop client:
    the client sends user-entered 6-digit code, server validates TTL/used/attempts,
    then writes telegram_accounts and marks challenge as used.
    RU: Этот поток является финальным подтверждением со стороны клиента:
    клиент отправляет введённый 6-значный код, сервер проверяет TTL/used/attempts,
    затем записывает telegram_accounts и помечает challenge как использованный.
    """

    secret = _reset_secret()
    code_value = str((confirm_code or "").strip())
    user_id_value = int(user_id or 0)
    if not secret or user_id_value <= 0 or not code_value.isdigit() or len(code_value) != 6:
        return {"ok": False, "error": "CODE_INVALID"}

    now_utc = datetime.now(timezone.utc)
    max_attempts = max(1, _env_int("TG_VERIFY_MAX_ATTEMPTS", 5))
    code_hash = hash_code(code_value, secret)

    try:
        with get_session() as session:
            challenge = session.scalar(
                select(TelegramVerifyChallenge)
                .where(
                    TelegramVerifyChallenge.user_id == user_id_value,
                    TelegramVerifyChallenge.code_hash == code_hash,
                )
                .order_by(TelegramVerifyChallenge.created_at.desc())
                .limit(1)
            )
            if challenge is None:
                return {"ok": False, "error": "CODE_INVALID"}
            if challenge.used_at is not None:
                return {"ok": False, "error": "CODE_USED"}
            if challenge.expires_at <= now_utc:
                return {"ok": False, "error": "CODE_EXPIRED"}
            if int(challenge.attempts or 0) >= max_attempts:
                return {"ok": False, "error": "CODE_INVALID"}

            tg_uid = int(challenge.telegram_user_id or 0)
            if tg_uid <= 0:
                return {"ok": False, "error": "CODE_INVALID"}
            tg_username = str((challenge.telegram_username or "")).strip() or None

            linked_ok, linked_error = link_or_update_telegram_account(
                session=session,
                user_id=user_id_value,
                telegram_user_id=tg_uid,
                telegram_username=tg_username,
            )
            if not linked_ok:
                return {"ok": False, "error": str(linked_error or "TG_ALREADY_LINKED")}

            challenge.used_at = now_utc
            updated_targets = _sync_username_to_profile_tables(
                session=session,
                user_id=user_id_value,
                telegram_username=tg_username,
            )
            session.flush()
            account = session.scalar(
                select(TelegramAccount).where(TelegramAccount.user_id == user_id_value).limit(1)
            )
            _LOG.info(
                "event=TG_CONFIRM_SYNC_OK user_id=%s telegram_user_id=%s telegram_username=%s updated_targets=%s",
                int(user_id_value),
                int(account.telegram_user_id) if account is not None else int(tg_uid),
                str((account.telegram_username if account is not None else tg_username) or ""),
                ",".join(updated_targets),
            )
            return {
                "ok": True,
                "telegram_user_id": int(account.telegram_user_id) if account is not None else tg_uid,
                "telegram_username": str((account.telegram_username if account else tg_username) or ""),
                "telegram_verified": True,
            }
    except Exception:
        _LOG.exception("event=TG_CONFIRM_APP_EXCEPTION user_id=%s", user_id_value)
        return {"ok": False, "error": "DB_ERROR"}


def request_password_reset(email: str, channel: str, request_ip: str | None, user_agent: str | None) -> dict:
    """EN: Request Telegram reset_link_code; return code only for verified Telegram accounts.
    RU: ????????? Telegram reset_link_code; ??????? ??? ?????? ??? ???????????????? Telegram-?????????.
    """

    del request_ip, user_agent
    channel_value = str((channel or "").strip().lower())
    email_value = str((email or "").strip().lower())
    secret = _reset_secret()
    ttl_sec = max(60, _env_int("TG_RESET_LINK_TTL_SEC", 600))
    throttle_sec = max(1, _env_int("TG_RESET_LINK_THROTTLE_SEC", 30))

    if channel_value != "telegram":
        return {"ok": True, "reset_link_code": None, "ttl_sec": 0}
    if not secret or not email_value:
        return {"ok": True, "reset_link_code": None, "ttl_sec": 0}

    now_utc = datetime.now(timezone.utc)
    try:
        with get_session() as session:
            user = session.scalar(select(User).where(User.email == email_value))
            if user is None:
                return {"ok": True, "reset_link_code": None, "ttl_sec": 0}

            account = session.scalar(select(TelegramAccount).where(TelegramAccount.user_id == int(user.id)))
            if account is None or account.verified_at is None or int(account.telegram_user_id or 0) <= 0:
                return {"ok": True, "reset_link_code": None, "ttl_sec": 0}

            last_req = session.scalar(
                select(TelegramResetRequest)
                .where(
                    TelegramResetRequest.user_id == int(user.id),
                    TelegramResetRequest.used_at.is_(None),
                )
                .order_by(TelegramResetRequest.created_at.desc())
                .limit(1)
            )
            if last_req is not None and last_req.created_at is not None:
                age_sec = (now_utc - last_req.created_at).total_seconds()
                if age_sec < throttle_sec:
                    return {"ok": True, "reset_link_code": None, "ttl_sec": 0}

            reset_link_code = _gen_reset_link_code()
            code_hash = hash_code(reset_link_code, secret)
            expires_at = now_utc + timedelta(seconds=ttl_sec)
            session.add(
                TelegramResetRequest(
                    user_id=int(user.id),
                    reset_link_code_hash=code_hash,
                    expires_at=expires_at,
                    used_at=None,
                    attempts=0,
                    telegram_user_id=int(account.telegram_user_id),
                    telegram_username=str((account.telegram_username or "").strip()) or None,
                )
            )
            session.flush()
            _LOG.info(
                "event=TG_RESET_LINK_REQUEST ok=true user_id=%s has_link=true email_mask=%s",
                int(user.id),
                _mask_code(email_value),
            )
            return {"ok": True, "reset_link_code": reset_link_code, "ttl_sec": int(ttl_sec)}
    except Exception:
        _LOG.exception("event=TG_RESET_LINK_REQUEST_EXCEPTION email_mask=%s", _mask_code(email_value))
        return {"ok": True, "reset_link_code": None, "ttl_sec": 0}


def issue_reset_confirm_code(telegram_user_id: int, reset_link_code: str, tg_username: str | None) -> dict:
    """EN: Issue 6-digit confirm_code for password reset from bot-side reset_link_code.
    RU: ?????? 6-??????? confirm_code ??? ?????? ?????? ?? bot-side reset_link_code.
    """

    secret = _reset_secret()
    code_value = str((reset_link_code or "").strip())
    tg_uid = int(telegram_user_id or 0)
    tg_username_value = str((tg_username or "").strip()) or None
    if not secret:
        return {"ok": False, "error": "CONFIG_INVALID"}
    if not code_value or tg_uid <= 0:
        return {"ok": False, "error": "REQUEST_NOT_FOUND"}

    now_utc = datetime.now(timezone.utc)
    max_attempts = max(1, _env_int("TG_RESET_MAX_ATTEMPTS", 5))
    confirm_ttl_sec = max(60, _env_int("TG_RESET_CONFIRM_TTL_SEC", 600))
    code_hash = hash_code(code_value, secret)

    try:
        with get_session() as session:
            row = session.scalar(
                select(TelegramResetRequest)
                .where(TelegramResetRequest.reset_link_code_hash == code_hash)
                .order_by(TelegramResetRequest.created_at.desc())
                .limit(1)
            )
            if row is None:
                _LOG.info(
                    "event=TG_RESET_ISSUE_RESULT ok=false error=REQUEST_NOT_FOUND tg_uid=%s reset_link=%s reason=request_not_found",
                    tg_uid,
                    _mask_code(code_value),
                )
                return {"ok": False, "error": "REQUEST_NOT_FOUND"}
            if row.used_at is not None:
                _LOG.info(
                    "event=TG_RESET_ISSUE_RESULT ok=false error=CODE_USED user_id=%s tg_uid=%s reset_link=%s reason=request_already_used",
                    int(row.user_id),
                    tg_uid,
                    _mask_code(code_value),
                )
                return {"ok": False, "error": "CODE_USED"}
            if row.expires_at <= now_utc:
                _LOG.info(
                    "event=TG_RESET_ISSUE_RESULT ok=false error=CODE_EXPIRED user_id=%s tg_uid=%s reset_link=%s reason=request_expired",
                    int(row.user_id),
                    tg_uid,
                    _mask_code(code_value),
                )
                return {"ok": False, "error": "CODE_EXPIRED"}
            if int(row.attempts or 0) >= max_attempts:
                _LOG.info(
                    "event=TG_RESET_ISSUE_RESULT ok=false error=ATTEMPTS_EXCEEDED user_id=%s tg_uid=%s reset_link=%s reason=request_attempts_exceeded attempts=%s",
                    int(row.user_id),
                    tg_uid,
                    _mask_code(code_value),
                    int(row.attempts or 0),
                )
                return {"ok": False, "error": "ATTEMPTS_EXCEEDED"}

            account = session.scalar(select(TelegramAccount).where(TelegramAccount.user_id == int(row.user_id)))
            if account is None or account.verified_at is None or int(account.telegram_user_id or 0) <= 0:
                _LOG.info(
                    "event=TG_RESET_ISSUE_RESULT ok=false error=TELEGRAM_NOT_CONFIRMED user_id=%s tg_uid=%s reset_link=%s reason=telegram_not_confirmed",
                    int(row.user_id),
                    tg_uid,
                    _mask_code(code_value),
                )
                return {"ok": False, "error": "TELEGRAM_NOT_CONFIRMED"}
            if int(account.telegram_user_id) != tg_uid:
                row.attempts = int(row.attempts or 0) + 1
                session.flush()
                _LOG.info(
                    "event=TG_RESET_ISSUE_RESULT ok=false error=MISMATCH user_id=%s tg_uid=%s reset_link=%s reason=telegram_user_mismatch expected_tg_uid=%s actual_attempts=%s",
                    int(row.user_id),
                    tg_uid,
                    _mask_code(code_value),
                    int(account.telegram_user_id),
                    int(row.attempts or 0),
                )
                return {"ok": False, "error": "MISMATCH"}

            confirm_code = gen_6digit_code()
            while confirm_code == code_value:
                confirm_code = gen_6digit_code()
            confirm_hash = hash_code(confirm_code, secret)
            challenge_expires = now_utc + timedelta(seconds=confirm_ttl_sec)
            _invalidate_active_reset_challenges(session, int(row.user_id), now_utc)
            session.add(
                TelegramResetChallenge(
                    user_id=int(row.user_id),
                    confirm_code_hash=confirm_hash,
                    expires_at=challenge_expires,
                    used_at=None,
                    attempts=0,
                    telegram_user_id=tg_uid,
                    telegram_username=tg_username_value,
                )
            )
            row.used_at = now_utc
            row.telegram_user_id = tg_uid
            row.telegram_username = tg_username_value
            session.flush()
            _LOG.info(
                "event=TG_RESET_ISSUE_RESULT ok=true error=- user_id=%s tg_uid=%s reset_link=%s reason=confirm_code_issued",
                int(row.user_id),
                tg_uid,
                _mask_code(code_value),
            )
            return {
                "ok": True,
                "confirm_code": confirm_code,
                "user_id": int(row.user_id),
                "tg_username": tg_username_value or "",
                "telegram_user_id": tg_uid,
            }
    except Exception:
        _LOG.exception(
            "event=TG_RESET_ISSUE_EXCEPTION tg_uid=%s reset_link=%s",
            tg_uid,
            _mask_code(code_value),
        )
        return {"ok": False, "error": "DB_ERROR"}


def confirm_password_reset(email: str, code: str, new_password: str) -> dict:
    """EN: Confirm only the latest active Telegram reset challenge and update password hash with refresh revoke.
    RU: Подтвердить только последний активный Telegram reset-challenge и обновить хеш пароля с отзывом refresh-токенов.
    """

    secret = _reset_secret()
    email_value = str((email or "").strip().lower())
    code_value = str((code or "").strip())
    password_value = str(new_password or "")
    max_attempts = max(1, _env_int("TG_RESET_MAX_ATTEMPTS", 5))

    if not secret:
        return {"ok": False, "error": "CONFIG_INVALID"}
    if not email_value:
        return {"ok": False, "error": "CHALLENGE_NOT_FOUND"}
    if not code_value.isdigit() or len(code_value) != 6:
        return {"ok": False, "error": "CODE_INVALID"}
    if len(password_value) < 8 or len(password_value) > 72:
        return {"ok": False, "error": "PASSWORD_INVALID"}
    try:
        reject_control_chars(password_value)
    except Exception:
        return {"ok": False, "error": "PASSWORD_INVALID"}

    now_utc = datetime.now(timezone.utc)
    try:
        with get_session() as session:
            user = session.scalar(select(User).where(User.email == email_value))
            if user is None:
                _LOG.info(
                    "event=TG_RESET_CONFIRM_RESULT ok=false error=CHALLENGE_NOT_FOUND email_mask=%s reason=user_not_found",
                    _mask_code(email_value),
                )
                return {"ok": False, "error": "CHALLENGE_NOT_FOUND"}

            challenge = session.scalar(
                select(TelegramResetChallenge)
                .where(
                    TelegramResetChallenge.user_id == int(user.id),
                )
                .order_by(TelegramResetChallenge.created_at.desc())
                .limit(1)
            )
            if challenge is None:
                _LOG.info(
                    "event=TG_RESET_CONFIRM_RESULT ok=false error=CHALLENGE_NOT_FOUND user_id=%s email_mask=%s reason=challenge_not_found",
                    int(user.id),
                    _mask_code(email_value),
                )
                return {"ok": False, "error": "CHALLENGE_NOT_FOUND"}
            if challenge.used_at is not None:
                _LOG.info(
                    "event=TG_RESET_CONFIRM_RESULT ok=false error=CODE_USED user_id=%s email_mask=%s reason=challenge_used",
                    int(user.id),
                    _mask_code(email_value),
                )
                return {"ok": False, "error": "CODE_USED"}
            if challenge.expires_at <= now_utc:
                _LOG.info(
                    "event=TG_RESET_CONFIRM_RESULT ok=false error=CODE_EXPIRED user_id=%s email_mask=%s reason=challenge_expired",
                    int(user.id),
                    _mask_code(email_value),
                )
                return {"ok": False, "error": "CODE_EXPIRED"}
            if int(challenge.attempts or 0) >= max_attempts:
                _LOG.info(
                    "event=TG_RESET_CONFIRM_RESULT ok=false error=ATTEMPTS_EXCEEDED user_id=%s email_mask=%s reason=challenge_attempts_exceeded attempts=%s",
                    int(user.id),
                    _mask_code(email_value),
                    int(challenge.attempts or 0),
                )
                return {"ok": False, "error": "ATTEMPTS_EXCEEDED"}

            account = session.scalar(select(TelegramAccount).where(TelegramAccount.user_id == int(user.id)).limit(1))
            if account is None or account.verified_at is None or int(account.telegram_user_id or 0) <= 0:
                _LOG.info(
                    "event=TG_RESET_CONFIRM_RESULT ok=false error=TELEGRAM_NOT_CONFIRMED user_id=%s email_mask=%s reason=telegram_not_confirmed",
                    int(user.id),
                    _mask_code(email_value),
                )
                return {"ok": False, "error": "TELEGRAM_NOT_CONFIRMED"}

            code_hash = hash_code(code_value, secret)
            if str((challenge.confirm_code_hash or "")).strip() != code_hash:
                challenge.attempts = int(challenge.attempts or 0) + 1
                session.flush()
                error_code = "ATTEMPTS_EXCEEDED" if int(challenge.attempts or 0) >= max_attempts else "CODE_INVALID"
                _LOG.info(
                    "event=TG_RESET_CONFIRM_RESULT ok=false error=%s user_id=%s email_mask=%s reason=code_mismatch attempts=%s",
                    error_code,
                    int(user.id),
                    _mask_code(email_value),
                    int(challenge.attempts or 0),
                )
                return {"ok": False, "error": error_code}

            challenge.used_at = now_utc
            user.password_hash = hash_password(password_value)
            session.execute(
                update(RefreshToken)
                .where(
                    RefreshToken.user_id == int(user.id),
                    RefreshToken.revoked_at.is_(None),
                )
                .values(revoked_at=now_utc)
            )
            session.flush()
            _LOG.info(
                "event=TG_RESET_CONFIRM_RESULT ok=true error=- user_id=%s email_mask=%s reason=password_reset_confirmed",
                int(user.id),
                _mask_code(email_value),
            )
            return {"ok": True}
    except Exception:
        _LOG.exception("event=TG_RESET_CONFIRM_EXCEPTION email_mask=%s", _mask_code(email_value))
        return {"ok": False, "error": "DB_ERROR"}
def fetch_outbox_batch(limit: int = 20) -> list[dict]:
    """EN: Fetch pending outbox rows ready for delivery at current time.
    RU: Получить pending-строки outbox, готовые к отправке на текущий момент.
    """

    now_utc = datetime.now(timezone.utc)
    try:
        with get_session() as session:
            rows = (
                session.execute(
                    select(TelegramOutbox)
                    .where(
                        TelegramOutbox.status == "pending",
                        TelegramOutbox.next_attempt_at <= now_utc,
                    )
                    .order_by(TelegramOutbox.id.asc())
                    .limit(int(limit))
                )
                .scalars()
                .all()
            )
            items: list[dict] = []
            for row in rows:
                items.append(
                    {
                        "id": int(row.id),
                        "telegram_user_id": int(row.telegram_user_id),
                        "message": str(row.message),
                        "attempts": int(row.attempts or 0),
                    }
                )
            return items
    except Exception:
        return []


def mark_outbox_sent(item_id: int) -> None:
    """EN: Mark outbox item as sent.
    RU: Пометить элемент outbox как успешно отправленный.
    """

    now_utc = datetime.now(timezone.utc)
    try:
        with get_session() as session:
            item = session.get(TelegramOutbox, int(item_id))
            if item is None:
                return
            item.status = "sent"
            item.sent_at = now_utc
            item.last_error = None
            session.flush()
    except Exception:
        return


def mark_outbox_failed(item_id: int, error_type: str) -> None:
    """EN: Increment attempt counter and schedule retry with exponential backoff.
    RU: Увеличить счетчик попыток и запланировать повтор с экспоненциальным backoff.
    """

    now_utc = datetime.now(timezone.utc)
    try:
        with get_session() as session:
            item = session.get(TelegramOutbox, int(item_id))
            if item is None:
                return
            item.attempts = int(item.attempts or 0) + 1
            delay = min(300, 2 ** max(1, int(item.attempts)))
            item.next_attempt_at = now_utc + timedelta(seconds=delay)
            item.last_error = str((error_type or "SEND_ERROR").strip())[:256]
            if int(item.attempts) >= 10:
                item.status = "failed"
            else:
                item.status = "pending"
            session.flush()
    except Exception:
        return
