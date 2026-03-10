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

from server.db import get_session
from server.models.password_reset import PasswordResetToken
from server.models.profile_user import ProfileUser
from server.models.telegram_account import TelegramAccount
from server.models.telegram_link_token import TelegramLinkToken
from server.models.telegram_outbox import TelegramOutbox
from server.models.telegram_verify_challenge import TelegramVerifyChallenge
from server.models.user import User
from server.security.passwords import hash_password
from server.security.tokens import gen_6digit_code, hash_code

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


def _normalize_telegram_username(raw_value: str | None) -> str:
    """EN: Normalize Telegram username for safe comparisons/logs.
    RU: Нормализовать Telegram username для безопасных сравнений/логов.
    """

    value = str((raw_value or "")).strip().lower()
    if value.startswith("@"):
        value = value[1:]
    return value


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

    try:
        with get_session() as session:
            user = session.get(User, int(user_id))
            if user is None:
                return {"ok": False, "error": "NOT_FOUND"}

            session.execute(
                update(TelegramLinkToken)
                .where(
                TelegramLinkToken.user_id == int(user_id),
                TelegramLinkToken.used_at.is_(None),
            )
            .values(used_at=now_utc)
            )
            token = TelegramLinkToken(
                user_id=int(user_id),
                code_hash=code_hash,
                telegram_user_id=None,
                expires_at=expires_at,
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

            existing_by_tg = session.scalar(
                select(TelegramAccount).where(TelegramAccount.telegram_user_id == int(telegram_user_id))
            )
            if existing_by_tg is not None and int(existing_by_tg.user_id) != int(token_row.user_id):
                return {"ok": False, "error": "ALREADY_LINKED"}

            existing_by_user = session.scalar(
                select(TelegramAccount).where(TelegramAccount.user_id == int(token_row.user_id))
            )
            if (
                existing_by_user is not None
                and int(existing_by_user.telegram_user_id) != int(telegram_user_id)
            ):
                return {"ok": False, "error": "USER_ALREADY_HAS_OTHER_TELEGRAM"}

            if existing_by_user is None:
                session.add(
                    TelegramAccount(
                        user_id=int(token_row.user_id),
                        telegram_user_id=int(telegram_user_id),
                        verified_at=now_utc,
                    )
                )
            else:
                existing_by_user.verified_at = now_utc

            token_row.used_at = now_utc
            session.flush()
            return {"ok": True}
    except Exception:
        return {"ok": False, "error": "DB_ERROR"}


def send_reset_code_for_link_token(token_id: int, telegram_user_id: int) -> dict:
    """EN: Send reset code to Telegram chat for user bound to active token, only after verification.
    RU: Отправить reset-код в Telegram-чат для пользователя активного токена, только после верификации.
    """

    secret = _reset_secret()
    if not secret:
        return {"ok": False, "error": "RESET_SECRET_MISSING"}

    now_utc = datetime.now(timezone.utc)
    ttl_min = max(1, _env_int("RESET_TOKEN_TTL_MIN", 15))
    try:
        with get_session() as session:
            token_row = session.get(TelegramLinkToken, int(token_id))
            if token_row is None:
                return {"ok": False, "error": "INVALID_TOKEN"}
            if token_row.used_at is not None or token_row.expires_at <= now_utc:
                return {"ok": False, "error": "INVALID_TOKEN"}
            if int(token_row.telegram_user_id or 0) != int(telegram_user_id):
                return {"ok": False, "error": "INVALID_TOKEN"}

            account = session.scalar(select(TelegramAccount).where(TelegramAccount.user_id == int(token_row.user_id)))
            if account is None or int(account.telegram_user_id) != int(telegram_user_id):
                return {"ok": False, "error": "NEED_CONFIRM_FIRST"}

            code = gen_6digit_code()
            token_hash = hash_code(code, secret)
            expires_at = now_utc + timedelta(minutes=ttl_min)
            session.execute(
                update(PasswordResetToken)
                .where(
                    PasswordResetToken.user_id == int(token_row.user_id),
                    PasswordResetToken.used_at.is_(None),
                )
                .values(used_at=now_utc)
            )
            session.add(
                PasswordResetToken(
                    user_id=int(token_row.user_id),
                    token_hash=token_hash,
                    expires_at=expires_at,
                    used_at=None,
                    request_ip=None,
                    user_agent=None,
                )
            )
            session.add(
                TelegramOutbox(
                    telegram_user_id=int(telegram_user_id),
                    message=f"Cosmic: код для сброса пароля: {code}. Действует {ttl_min} минут.",
                    status="pending",
                    attempts=0,
                    next_attempt_at=now_utc,
                    last_error=None,
                )
            )
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

            existing_by_tg = session.scalar(
                select(TelegramAccount).where(TelegramAccount.telegram_user_id == int(telegram_user_id))
            )
            if existing_by_tg is not None and int(existing_by_tg.user_id) != int(token.user_id):
                return {"ok": False, "error": "ALREADY_LINKED"}

            token.used_at = now_utc
            account = session.scalar(select(TelegramAccount).where(TelegramAccount.user_id == int(token.user_id)))
            if account is None:
                account = TelegramAccount(
                    user_id=int(token.user_id),
                    telegram_user_id=int(telegram_user_id),
                    verified_at=now_utc,
                )
                session.add(account)
            else:
                account.telegram_user_id = int(telegram_user_id)
                account.verified_at = now_utc
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
            if token_expired or token_used:
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
            profile_tg_norm = _normalize_telegram_username(profile_row.telegram if profile_row else "")
            if profile_tg_norm and profile_tg_norm != "no data" and incoming_username_norm and profile_tg_norm != incoming_username_norm:
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

            existing_by_tg = session.scalar(
                select(TelegramAccount).where(TelegramAccount.telegram_user_id == tg_user_id_value)
            )
            if existing_by_tg is not None and int(existing_by_tg.user_id) != int(token_row.user_id):
                _LOG.info(
                    "event=TG_CONFIRM_BY_CODE_OUT ok=false error=ALREADY_LINKED user_id=%s tg_uid=%s tg_username=%s link_code=%s detail=telegram_user_already_linked expected_user_id=%s actual_user_id=%s",
                    int(token_row.user_id),
                    tg_user_id_value,
                    incoming_username_norm or "-",
                    _mask_code(link_code_value),
                    int(token_row.user_id),
                    int(existing_by_tg.user_id),
                )
                return {"ok": False, "error": "ALREADY_LINKED"}

            existing_by_user = session.scalar(
                select(TelegramAccount).where(TelegramAccount.user_id == int(token_row.user_id))
            )
            if existing_by_user is None:
                session.add(
                    TelegramAccount(
                        user_id=int(token_row.user_id),
                        telegram_user_id=tg_user_id_value,
                        verified_at=now_utc,
                    )
                )
            else:
                existing_by_user.telegram_user_id = tg_user_id_value
                existing_by_user.verified_at = now_utc

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


def request_password_reset(email: str, channel: str, request_ip: str | None, user_agent: str | None) -> dict:
    """EN: Queue Telegram reset message when account is linked; keep anti-enumeration response.
    RU: Поставить в очередь Telegram reset-сообщение при привязанном аккаунте, сохранив anti-enumeration ответ.
    """

    del request_ip, user_agent
    channel_value = (channel or "").strip().lower()
    if channel_value != "telegram":
        # EN: Keep anti-enumeration response stable for non-telegram channels.
        # RU: Сохранять стабильный anti-enumeration ответ для не-telegram каналов.
        return {"ok": True}

    secret = _reset_secret()
    email_value = (email or "").strip().lower()
    ttl_min = max(1, _env_int("RESET_TOKEN_TTL_MIN", 15))
    throttle_sec = max(1, _env_int("RESET_THROTTLE_SEC", 60))
    prod_mode = os.getenv("APP_ENV", "prod").strip().lower() not in {"dev", "local"}

    if not secret or not email_value:
        return {"ok": True}

    now_utc = datetime.now(timezone.utc)
    delivery = "not_linked"
    try:
        with get_session() as session:
            user = session.scalar(select(User).where(User.email == email_value))
            if user is None:
                return {"ok": True}

            account = session.scalar(select(TelegramAccount).where(TelegramAccount.user_id == int(user.id)))
            if account is None or account.verified_at is None:
                return {"ok": True} if prod_mode else {"ok": True, "delivery": delivery}

            last_row = session.scalar(
                select(PasswordResetToken)
                .where(PasswordResetToken.user_id == int(user.id))
                .order_by(PasswordResetToken.created_at.desc())
                .limit(1)
            )
            if last_row is not None and last_row.created_at is not None:
                if (now_utc - last_row.created_at).total_seconds() < throttle_sec:
                    return {"ok": True} if prod_mode else {"ok": True, "delivery": "throttled"}

            code = gen_6digit_code()
            token_hash = hash_code(code, secret)
            expires_at = now_utc + timedelta(minutes=ttl_min)

            session.execute(
                update(PasswordResetToken)
                .where(
                    PasswordResetToken.user_id == int(user.id),
                    PasswordResetToken.used_at.is_(None),
                )
                .values(used_at=now_utc)
            )
            session.add(
                PasswordResetToken(
                    user_id=int(user.id),
                    token_hash=token_hash,
                    expires_at=expires_at,
                    used_at=None,
                    request_ip=None,
                    user_agent=None,
                )
            )
            message = f"Cosmic: код для сброса пароля: {code}. Действует {ttl_min} минут."
            session.add(
                TelegramOutbox(
                    telegram_user_id=int(account.telegram_user_id),
                    message=message,
                    status="pending",
                    attempts=0,
                    next_attempt_at=now_utc,
                    last_error=None,
                )
            )
            session.flush()
            delivery = "queued"
            return {"ok": True} if prod_mode else {"ok": True, "delivery": delivery}
    except Exception:
        return {"ok": True}


def confirm_password_reset(email: str, code: str, new_password: str) -> dict:
    """EN: Validate reset code and update password hash.
    RU: Проверить reset-код и обновить хеш пароля.
    """

    secret = _reset_secret()
    email_value = (email or "").strip().lower()
    code_value = (code or "").strip()
    new_password_value = new_password or ""
    max_attempts = max(1, _env_int("RESET_MAX_ATTEMPTS", 5))

    if not secret or not email_value or not code_value or not new_password_value:
        return {"ok": False, "error": "INVALID_CODE"}

    now_utc = datetime.now(timezone.utc)
    try:
        with get_session() as session:
            user = session.scalar(select(User).where(User.email == email_value))
            if user is None:
                return {"ok": False, "error": "INVALID_CODE"}

            token = session.scalar(
                select(PasswordResetToken)
                .where(
                    PasswordResetToken.user_id == int(user.id),
                    PasswordResetToken.used_at.is_(None),
                )
                .order_by(PasswordResetToken.created_at.desc())
                .limit(1)
            )
            if token is None or token.expires_at <= now_utc or int(token.attempts or 0) >= max_attempts:
                return {"ok": False, "error": "INVALID_CODE"}

            expected = hash_code(code_value, secret)
            if expected != token.token_hash:
                token.attempts = int(token.attempts or 0) + 1
                session.flush()
                return {"ok": False, "error": "INVALID_CODE"}

            token.used_at = now_utc
            user.password_hash = hash_password(new_password_value)
            session.execute(
                update(PasswordResetToken)
                .where(
                    PasswordResetToken.user_id == int(user.id),
                    PasswordResetToken.used_at.is_(None),
                    PasswordResetToken.id != int(token.id),
                )
                .values(used_at=now_utc)
            )
            session.flush()
            return {"ok": True}
    except Exception:
        return {"ok": False, "error": "INVALID_CODE"}


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
