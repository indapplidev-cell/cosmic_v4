"""EN: Services for Telegram identity verification via purpose-aware Mini App sessions.
RU: Сервисы проверки Telegram identity через purpose-aware Mini App sessions.
"""

from __future__ import annotations

import base64
import hashlib
import logging
import os
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from server.config import (
    get_pay_bot_token,
    get_payout_miniapp_auth_max_age_sec,
    get_payout_miniapp_bot_username,
    get_payout_miniapp_session_ttl_sec,
    get_payout_miniapp_secret,
    get_payout_miniapp_short_name,
)
from server.db import get_session
from server.models.payout_miniapp_session import PayoutMiniAppSession
from server.models.telegram_account import TelegramAccount
from server.models.user import User
from server.security.telegram_miniapp import TelegramMiniAppValidationError, validate_telegram_miniapp_init_data
from server.security.tokens import hash_code
from server.services.telegram_service import link_or_update_telegram_account


_LOG = logging.getLogger("cosmic.payout_miniapp")
_ACTIVE_MINIAPP_STATUSES = ("issued", "verified")
_PURPOSE_PAYOUT = "payout"
_PURPOSE_TELEGRAM_LINK = "telegram_link"


def _mask_token(token: str) -> str:
    """EN: Mask session token for logs without exposing raw value.
    RU: Маскировать session-токен в логах без раскрытия raw-значения.
    """

    value = str((token or "").strip())
    if not value:
        return "-"
    if len(value) <= 8:
        return f"{value[:1]}...{value[-1:]}(len={len(value)})"
    return f"{value[:4]}...{value[-4:]}(len={len(value)})"


def _generate_session_token() -> str:
    """EN: Generate opaque URL-safe payout Mini App session token.
    RU: Сгенерировать непрозрачный URL-safe payout Mini App session-токен.
    """

    return base64.urlsafe_b64encode(os.urandom(24)).decode("ascii").rstrip("=")[:48]


def _session_token_hash(token: str) -> str:
    """EN: Hash opaque payout Mini App session token with dedicated server secret.
    RU: Хешировать непрозрачный payout Mini App session-токен выделенным серверным секретом.
    """

    return hash_code(str((token or "").strip()), get_payout_miniapp_secret())


def _init_data_hash(init_data_raw: str) -> str:
    """EN: Compute one-way SHA-256 hash for raw initData without storing plaintext.
    RU: Вычислить односторонний SHA-256-хеш raw initData без хранения plaintext.
    """

    return hashlib.sha256(str((init_data_raw or "").strip()).encode("utf-8")).hexdigest()


def _build_miniapp_url(start_param: str) -> str:
    """EN: Build Telegram Mini App launch URL through startapp using env-configured bot and short name.
    RU: Собрать URL запуска Telegram Mini App через startapp с bot и short name из env-конфига.

    EN: `PAYOUT_MINIAPP_SHORT_NAME` must match the Mini App short name registered in BotFather,
    and that BotFather configuration must point to the backend route serving `/paybot/miniapp`.
    RU: `PAYOUT_MINIAPP_SHORT_NAME` должен совпадать с short name Mini App, зарегистрированным в BotFather,
    а сама настройка BotFather должна указывать на backend-route, который отдаёт `/paybot/miniapp`.
    """

    bot_username = get_payout_miniapp_bot_username()
    short_name = get_payout_miniapp_short_name()
    return f"https://t.me/{bot_username}/{short_name}?startapp={start_param}"


def _close_active_sessions(session, user_id: int, purpose: str, now_utc: datetime) -> None:
    """EN: Invalidate previous active Mini App sessions of the same purpose for the same user.
    RU: Инвалидировать предыдущие активные Mini App sessions того же purpose для того же пользователя.
    """

    session.execute(
        update(PayoutMiniAppSession)
        .where(
            PayoutMiniAppSession.user_id == int(user_id),
            PayoutMiniAppSession.purpose == str(purpose),
            PayoutMiniAppSession.status.in_(_ACTIVE_MINIAPP_STATUSES),
            PayoutMiniAppSession.consumed_at.is_(None),
            PayoutMiniAppSession.expires_at > now_utc,
        )
        .values(status="expired", fail_reason="REPLACED_BY_NEW_SESSION")
    )


def _load_session_by_token(session, start_param: str) -> PayoutMiniAppSession | None:
    """EN: Load payout Mini App session by hashed opaque start parameter.
    RU: Загрузить payout Mini App session по хешированному непрозрачному start-параметру.
    """

    token_hash = _session_token_hash(start_param)
    return session.scalar(
        select(PayoutMiniAppSession)
        .where(PayoutMiniAppSession.session_token_hash == token_hash)
        .limit(1)
    )


def _load_latest_session_for_user(session, user_id: int, purpose: str, *, for_update: bool = False) -> PayoutMiniAppSession | None:
    """EN: Load the latest Mini App session of one purpose for a concrete authenticated user.
    RU: Загрузить последнюю Mini App session одного purpose для конкретного авторизованного пользователя.
    """

    statement = (
        select(PayoutMiniAppSession)
        .where(
            PayoutMiniAppSession.user_id == int(user_id),
            PayoutMiniAppSession.purpose == str(purpose),
        )
        .order_by(PayoutMiniAppSession.created_at.desc())
        .limit(1)
    )
    if for_update:
        statement = statement.with_for_update()
    return session.scalar(statement)


def _expire_session_if_needed(row: PayoutMiniAppSession, now_utc: datetime) -> bool:
    """EN: Mark active payout Mini App session as expired when TTL is over.
    RU: Пометить активную payout Mini App session как expired, если TTL истёк.
    """

    if row.expires_at > now_utc:
        return False
    if row.status in {"issued", "verified"}:
        row.status = "expired"
        row.fail_reason = row.fail_reason or "SESSION_EXPIRED"
    return True


def _verified_context(row: PayoutMiniAppSession) -> dict:
    """EN: Return normalized verification context from a verified or consumed session row.
    RU: Вернуть нормализованный verification-context из verified или consumed session.
    """

    return {
        "miniapp_session_id": int(row.id or 0),
        "user_id": int(row.user_id),
        "purpose": str(row.purpose),
        "telegram_user_id": int(row.telegram_user_id or 0),
        "telegram_username": str((row.telegram_username or "").strip()) or None,
        "verified_at": row.verified_at.isoformat() if row.verified_at is not None else None,
        "tg_auth_date": row.tg_auth_date.isoformat() if row.tg_auth_date is not None else None,
    }


def _request_miniapp_session(user_id: int, purpose: str) -> dict:
    """EN: Create one-time Mini App session for one authenticated user and purpose.
    RU: Создать одноразовую Mini App session для одного авторизованного пользователя и purpose.
    """

    now_utc = datetime.now(timezone.utc)
    try:
        ttl_sec = get_payout_miniapp_session_ttl_sec()
        session_token = _generate_session_token()
        session_token_hash = _session_token_hash(session_token)
        miniapp_url = _build_miniapp_url(session_token)
    except RuntimeError:
        return {"ok": False, "error": "CONFIG_INVALID"}

    try:
        with get_session() as session:
            if session.get(User, int(user_id)) is None:
                return {"ok": False, "error": "NOT_FOUND"}
            _close_active_sessions(session, int(user_id), str(purpose), now_utc)
            session.add(
                PayoutMiniAppSession(
                    user_id=int(user_id),
                    purpose=str(purpose),
                    session_token_hash=session_token_hash,
                    status="issued",
                    expires_at=now_utc + timedelta(seconds=ttl_sec),
                )
            )
            session.flush()
    except Exception:
        _LOG.exception("event=TG_MINIAPP_SESSION_REQUEST_FAIL user_id=%s purpose=%s", int(user_id), str(purpose))
        return {"ok": False, "error": "DB_ERROR"}

    _LOG.info(
        "event=TG_MINIAPP_SESSION_ISSUED user_id=%s purpose=%s token=%s ttl_sec=%s",
        int(user_id),
        str(purpose),
        _mask_token(session_token),
        int(ttl_sec),
    )
    return {"ok": True, "miniapp_url": miniapp_url, "ttl_sec": int(ttl_sec), "purpose": str(purpose)}


def _confirm_miniapp_session(init_data_raw: str, start_param: str, *, expected_purpose: str | None = None) -> dict:
    """EN: Validate Telegram Mini App initData and verify one Mini App session by its purpose.
    RU: Проверить Telegram Mini App initData и подтвердить одну Mini App session по её purpose.
    """

    raw_value = str((init_data_raw or "").strip())
    provided_start_param = str((start_param or "").strip())
    if not raw_value or not provided_start_param:
        return {"ok": False, "error": "INITDATA_INVALID"}

    try:
        payload = validate_telegram_miniapp_init_data(
            raw_value,
            get_pay_bot_token(),
            max_age_sec=get_payout_miniapp_auth_max_age_sec(),
        )
    except RuntimeError:
        return {"ok": False, "error": "CONFIG_INVALID"}
    except TelegramMiniAppValidationError as exc:
        return {"ok": False, "error": exc.error_code}

    validated_start_param = str((payload.start_param or "").strip())
    if validated_start_param != provided_start_param:
        return {"ok": False, "error": "START_PARAM_MISMATCH"}

    telegram_user_id = int(payload.user["id"])
    telegram_username = str((payload.user.get("username") or "").strip()) or None
    tg_auth_date = datetime.fromtimestamp(int(payload.auth_date), tz=timezone.utc)
    now_utc = datetime.now(timezone.utc)

    try:
        with get_session() as session:
            row = _load_session_by_token(session, validated_start_param)
            if row is None:
                return {"ok": False, "error": "SESSION_NOT_FOUND"}
            if expected_purpose and str(row.purpose) != str(expected_purpose):
                return {"ok": False, "error": "SESSION_PURPOSE_MISMATCH"}
            if row.status == "consumed" or row.consumed_at is not None:
                return {"ok": False, "error": "SESSION_CONSUMED"}
            if row.status == "verified":
                return {"ok": False, "error": "SESSION_ALREADY_VERIFIED"}
            if _expire_session_if_needed(row, now_utc):
                return {"ok": False, "error": "SESSION_EXPIRED"}
            if row.status != "issued":
                return {"ok": False, "error": "SESSION_REJECTED"}

            account = session.scalar(
                select(TelegramAccount).where(TelegramAccount.user_id == int(row.user_id)).limit(1)
            )
            if account is not None and int(account.telegram_user_id or 0) != telegram_user_id:
                row.status = "rejected"
                row.fail_reason = "TELEGRAM_ACCOUNT_MISMATCH"
                _LOG.info(
                    "event=PAYOUT_MINIAPP_SESSION_REJECT user_id=%s tg_uid=%s linked_tg_uid=%s reason=%s",
                    int(row.user_id),
                    telegram_user_id,
                    int(account.telegram_user_id or 0),
                    "TELEGRAM_ACCOUNT_MISMATCH",
                )
                return {"ok": False, "error": "TELEGRAM_ACCOUNT_MISMATCH"}

            linked_ok, linked_error = link_or_update_telegram_account(
                session,
                user_id=int(row.user_id),
                telegram_user_id=telegram_user_id,
                telegram_username=telegram_username,
            )
            if not linked_ok:
                row.status = "rejected"
                row.fail_reason = str(linked_error or "TG_ALREADY_LINKED")
                return {"ok": False, "error": str(linked_error or "TG_ALREADY_LINKED")}

            row.telegram_user_id = telegram_user_id
            row.telegram_username = telegram_username
            row.init_data_hash = _init_data_hash(raw_value)
            row.tg_auth_date = tg_auth_date
            row.verified_at = now_utc
            row.status = "verified"
            row.fail_reason = None
            session.flush()
            return {
                "ok": True,
                "user_id": int(row.user_id),
                "purpose": str(row.purpose),
                "telegram_user_id": telegram_user_id,
            }
    except IntegrityError:
        _LOG.exception(
            "event=PAYOUT_MINIAPP_SESSION_CONFIRM_CONFLICT tg_uid=%s",
            telegram_user_id,
        )
        return {"ok": False, "error": "TG_ALREADY_LINKED"}
    except Exception:
        _LOG.exception(
            "event=TG_MINIAPP_SESSION_CONFIRM_FAIL tg_uid=%s start_param=%s",
            telegram_user_id,
            _mask_token(validated_start_param),
        )
        return {"ok": False, "error": "DB_ERROR"}


def _get_miniapp_session_status(user_id: int, purpose: str) -> dict:
    """EN: Return current Mini App verification status for one authenticated user and purpose.
    RU: Вернуть текущий статус Mini App verification для одного авторизованного пользователя и purpose.
    """

    now_utc = datetime.now(timezone.utc)
    try:
        with get_session() as session:
            row = _load_latest_session_for_user(session, int(user_id), str(purpose))
            if row is None:
                return {"ok": True, "verified": False, "status": "missing", "ttl_sec": 0, "expired": True, "purpose": str(purpose)}

            expired = _expire_session_if_needed(row, now_utc)
            ttl_sec = max(0, int((row.expires_at - now_utc).total_seconds()))
            verified = bool(row.status == "verified" and row.verified_at is not None and not expired and row.consumed_at is None)
            return {
                "ok": True,
                "verified": verified,
                "status": str(row.status),
                "ttl_sec": int(ttl_sec),
                "expired": expired,
                "purpose": str(row.purpose),
                "telegram_user_id": int(row.telegram_user_id or 0) if verified else None,
            }
    except Exception:
        _LOG.exception("event=TG_MINIAPP_SESSION_STATUS_FAIL user_id=%s purpose=%s", int(user_id), str(purpose))
        return {"ok": False, "error": "DB_ERROR"}


def request_payout_miniapp_session(user_id: int) -> dict:
    """EN: Create one-time payout Mini App session and return launch URL for authenticated user.
    RU: Создать одноразовую payout Mini App session и вернуть launch URL для авторизованного пользователя.
    """

    return _request_miniapp_session(user_id=int(user_id), purpose=_PURPOSE_PAYOUT)


def request_telegram_link_miniapp_session(user_id: int) -> dict:
    """EN: Create one-time telegram_link Mini App session and return launch URL for authenticated user.
    RU: Создать одноразовую telegram_link Mini App session и вернуть launch URL для авторизованного пользователя.
    """

    return _request_miniapp_session(user_id=int(user_id), purpose=_PURPOSE_TELEGRAM_LINK)


def confirm_telegram_miniapp_session(init_data_raw: str, start_param: str) -> dict:
    """EN: Confirm one Mini App session using server-validated Telegram WebApp initData.
    RU: Подтвердить одну Mini App session через server-validated Telegram WebApp initData.
    """

    return _confirm_miniapp_session(init_data_raw=init_data_raw, start_param=start_param)


def confirm_payout_miniapp_session(init_data_raw: str, start_param: str) -> dict:
    """EN: Confirm payout-purpose Mini App session using server-validated Telegram WebApp initData.
    RU: Подтвердить Mini App session назначения payout через server-validated Telegram WebApp initData.
    """

    return _confirm_miniapp_session(init_data_raw=init_data_raw, start_param=start_param, expected_purpose=_PURPOSE_PAYOUT)


def get_payout_miniapp_session_status(user_id: int) -> dict:
    """EN: Return current payout Mini App verification status for authenticated user.
    RU: Вернуть текущий статус payout Mini App verification для авторизованного пользователя.
    """

    return _get_miniapp_session_status(user_id=int(user_id), purpose=_PURPOSE_PAYOUT)


def get_telegram_link_miniapp_session_status(user_id: int) -> dict:
    """EN: Return current telegram_link Mini App verification status for authenticated user.
    RU: Вернуть текущий статус telegram_link Mini App verification для авторизованного пользователя.
    """

    return _get_miniapp_session_status(user_id=int(user_id), purpose=_PURPOSE_TELEGRAM_LINK)


def consume_verified_payout_miniapp_session_in_session(session, user_id: int, *, now_utc: datetime | None = None) -> dict:
    """EN: Consume the latest verified payout Mini App session inside an existing transaction.
    RU: Потребить последнюю verified payout Mini App session внутри уже открытой транзакции.

    EN: This helper is the transactional core reused by payout request creation.
    RU: Этот helper является транзакционным ядром, которое переиспользуется при создании payout request.
    """

    now_value = now_utc or datetime.now(timezone.utc)
    row = _load_latest_session_for_user(session, int(user_id), _PURPOSE_PAYOUT, for_update=True)
    if row is None:
        return {"ok": False, "error": "SESSION_NOT_FOUND"}
    if row.status == "consumed" or row.consumed_at is not None:
        return {"ok": False, "error": "SESSION_CONSUMED"}
    if _expire_session_if_needed(row, now_value):
        return {"ok": False, "error": "SESSION_EXPIRED"}
    if row.status != "verified" or row.verified_at is None or int(row.telegram_user_id or 0) <= 0:
        return {"ok": False, "error": "SESSION_NOT_VERIFIED"}

    row.status = "consumed"
    row.consumed_at = now_value
    row.fail_reason = None
    session.flush()
    payload = _verified_context(row)
    payload.update({"ok": True, "status": "consumed", "consumed_at": now_value.isoformat()})
    return payload


def consume_verified_payout_miniapp_session(user_id: int) -> dict:
    """EN: Atomically consume the latest verified payout Mini App session for a user exactly once.
    RU: Атомарно потребить последнюю verified payout Mini App session пользователя ровно один раз.

    EN: This helper prepares the security contract for the next payout step and does not perform
    the payout business action itself.
    RU: Этот helper подготавливает security-контракт для следующего payout-шага и не выполняет
    саму бизнес-логику выплаты.
    """

    try:
        with get_session() as session:
            return consume_verified_payout_miniapp_session_in_session(session, int(user_id))
    except Exception:
        _LOG.exception("event=PAYOUT_MINIAPP_SESSION_CONSUME_FAIL user_id=%s", int(user_id))
        return {"ok": False, "error": "DB_ERROR"}
