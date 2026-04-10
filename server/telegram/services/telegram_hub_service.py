"""EN: Shared Telegram Mini App hub service for verify/reset/payout actions.
RU: Общий сервис Telegram Mini App hub для действий verify/reset/payout.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from server.app.config.settings import (
    get_pay_bot_token,
    get_payout_miniapp_auth_max_age_sec,
    get_payout_miniapp_secret,
    get_payout_miniapp_session_ttl_sec,
)
from server.db.sessions.session_factory import get_session
from server.db.models.profile_user import ProfileUser
from server.db.models.payout_miniapp_session import PayoutMiniAppSession
from server.db.models.telegram_account import TelegramAccount
from server.db.models.user import User
from server.app.security.telegram_miniapp import TelegramMiniAppValidationError, validate_telegram_miniapp_init_data
from server.telegram.services import payout_miniapp_service
from server.engine.manager.payout_request_manager import create_hub_payout_request_in_session
from server.telegram.services.telegram_service import (
    _sync_username_to_profile_tables,
    confirm_password_reset,
    issue_reset_confirm_code,
    link_or_update_telegram_account,
    request_password_reset,
)


_LOG = logging.getLogger("cosmic.telegram_hub")
_PURPOSE_HUB = "hub"
_HUB_TOKEN_TTL_SEC = 300


def _mask_token(token: str) -> str:
    """EN: Mask token for logs without exposing sensitive values.
    RU: Маскировать токен в логах без раскрытия чувствительных значений.
    """

    return payout_miniapp_service._mask_token(token)


def _build_hub_miniapp_url(start_param: str) -> str:
    """EN: Build the single shared Telegram Mini App hub direct URL.
    RU: Собрать единый direct URL общего Telegram Mini App hub.
    """

    return payout_miniapp_service._build_miniapp_url(start_param)


def _hub_token_secret() -> str:
    """EN: Return secret used for short-lived hub-session token signing.
    RU: Вернуть секрет для подписи краткоживущего hub-session токена.
    """

    return get_payout_miniapp_secret()


def _encode_hub_token(session_id: int, user_id: int, telegram_user_id: int) -> str:
    """EN: Encode short-lived signed hub token from verified hub-session context.
    RU: Закодировать краткоживущий подписанный hub token из verified hub-session контекста.
    """

    payload = {
        "sid": int(session_id),
        "uid": int(user_id),
        "tg_uid": int(telegram_user_id),
        "exp": int(datetime.now(timezone.utc).timestamp()) + int(_HUB_TOKEN_TTL_SEC),
    }
    body = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8")).decode("ascii").rstrip("=")
    signature = hmac.new(
        _hub_token_secret().encode("utf-8"),
        body.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    sig = base64.urlsafe_b64encode(signature).decode("ascii").rstrip("=")
    return f"{body}.{sig}"


def _decode_hub_token(hub_token: str) -> dict:
    """EN: Validate signed hub token and return normalized payload.
    RU: Проверить подписанный hub token и вернуть нормализованный payload.
    """

    token_value = str((hub_token or "").strip())
    if "." not in token_value:
        return {"ok": False, "error": "HUB_TOKEN_INVALID"}
    body, sig = token_value.split(".", 1)
    expected_sig = base64.urlsafe_b64encode(
        hmac.new(
            _hub_token_secret().encode("utf-8"),
            body.encode("utf-8"),
            hashlib.sha256,
        ).digest()
    ).decode("ascii").rstrip("=")
    if not hmac.compare_digest(expected_sig, sig):
        return {"ok": False, "error": "HUB_TOKEN_INVALID"}
    try:
        padded = body + "=" * (-len(body) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8"))
        session_id = int(payload.get("sid") or 0)
        user_id = int(payload.get("uid") or 0)
        telegram_user_id = int(payload.get("tg_uid") or 0)
        exp_ts = int(payload.get("exp") or 0)
    except Exception:
        return {"ok": False, "error": "HUB_TOKEN_INVALID"}
    now_ts = int(datetime.now(timezone.utc).timestamp())
    if session_id <= 0 or user_id <= 0 or telegram_user_id <= 0 or exp_ts <= now_ts:
        return {"ok": False, "error": "HUB_TOKEN_EXPIRED"}
    return {
        "ok": True,
        "session_id": session_id,
        "user_id": user_id,
        "telegram_user_id": telegram_user_id,
    }


def _load_hub_session_by_token(session, start_param: str, *, for_update: bool = False) -> PayoutMiniAppSession | None:
    """EN: Load one hub Mini App session by hashed opaque startapp token.
    RU: Загрузить одну hub Mini App session по хешированному opaque startapp токену.
    """

    statement = (
        select(PayoutMiniAppSession)
        .where(
            PayoutMiniAppSession.session_token_hash == payout_miniapp_service._session_token_hash(start_param),
            PayoutMiniAppSession.purpose == _PURPOSE_HUB,
        )
        .limit(1)
    )
    if for_update:
        statement = statement.with_for_update()
    return session.scalar(statement)


def _load_hub_session_by_id(session, session_id: int, *, for_update: bool = False) -> PayoutMiniAppSession | None:
    """EN: Load hub Mini App session by DB id with optional row lock.
    RU: Загрузить hub Mini App session по id БД с optional row lock.
    """

    statement = select(PayoutMiniAppSession).where(
        PayoutMiniAppSession.id == int(session_id),
        PayoutMiniAppSession.purpose == _PURPOSE_HUB,
    )
    if for_update:
        statement = statement.with_for_update()
    return session.scalar(statement.limit(1))


def _resolve_reset_user_id(session, email: str) -> int:
    """EN: Resolve reset user_id from email only when Telegram account is already verified.
    RU: Получить user_id для reset по email только если Telegram-аккаунт уже подтверждён.
    """

    email_value = str((email or "").strip().lower())
    if not email_value:
        return 0
    user = session.scalar(select(User).where(User.email == email_value).limit(1))
    if user is None:
        return 0
    account = session.scalar(select(TelegramAccount).where(TelegramAccount.user_id == int(user.id)).limit(1))
    if account is None or account.verified_at is None or int(account.telegram_user_id or 0) <= 0:
        return 0
    return int(user.id)


def _hub_actions_context(session, row: PayoutMiniAppSession, account: TelegramAccount | None) -> dict:
    """EN: Build server-trusted hub menu context and action availability flags.
    RU: Собрать доверенный server-side hub context меню и флаги доступности действий.
    """

    available_balance = payout_miniapp_service._get_available_balance(session, int(row.user_id))
    linked_wallet = payout_miniapp_service._load_last_wallet_address(session, int(row.user_id))
    telegram_linked = bool(account is not None and int(account.telegram_user_id or 0) > 0)
    return {
        "ok": True,
        "hub_token": _encode_hub_token(int(row.id), int(row.user_id), int(row.telegram_user_id or 0)),
        "telegram": {
            "linked": telegram_linked,
            "telegram_user_id": int(row.telegram_user_id or 0),
            "telegram_username": str((row.telegram_username or "").strip()) or None,
        },
        "available_actions": {
            "verify": True,
            "reset": telegram_linked,
            "payout": float(available_balance) >= float(payout_miniapp_service._PAYOUT_MIN_AMOUNT),
        },
        "reset": {
            "available": telegram_linked,
        },
        "payout": {
            "available": float(available_balance) >= float(payout_miniapp_service._PAYOUT_MIN_AMOUNT),
            "balance": float(available_balance),
            "limits": {
                "min_amount": float(payout_miniapp_service._PAYOUT_MIN_AMOUNT),
                "max_amount": float(available_balance),
            },
            "network": payout_miniapp_service._PAYOUT_NETWORK,
            "linked_wallet": linked_wallet,
        },
        "session": {
            "status": str(row.status),
            "expires_at": row.expires_at.isoformat() if row.expires_at is not None else None,
        },
    }


def request_telegram_hub_session(
    *,
    entry_action: str,
    auth_user_id: int | None = None,
    requested_user_id: int | None = None,
    email: str | None = None,
) -> dict:
    """EN: Issue one shared Telegram hub Mini App session from app-side verify/reset/payout entry points.
    RU: Выдать одну общую hub Mini App session Telegram из app-side точек входа verify/reset/payout.
    """

    action_value = str((entry_action or "").strip().lower())
    if action_value not in {"verify", "reset", "payout"}:
        return {"ok": False, "error": "ENTRY_ACTION_INVALID"}

    now_utc = datetime.now(timezone.utc)
    try:
        ttl_sec = get_payout_miniapp_session_ttl_sec()
        session_token = payout_miniapp_service._generate_session_token()
        miniapp_url = _build_hub_miniapp_url(session_token)
    except RuntimeError:
        return {"ok": False, "error": "CONFIG_INVALID"}

    try:
        with get_session() as session:
            if action_value in {"verify", "payout"}:
                user_id_value = int(requested_user_id or 0)
                if int(auth_user_id or 0) <= 0:
                    return {"ok": False, "error": "UNAUTHORIZED"}
                if user_id_value <= 0 or int(auth_user_id) != user_id_value:
                    return {"ok": False, "error": "FORBIDDEN"}
                if session.get(User, user_id_value) is None:
                    return {"ok": False, "error": "NOT_FOUND"}
                if action_value == "payout":
                    available_balance = payout_miniapp_service._get_available_balance(session, user_id_value)
                    if available_balance < payout_miniapp_service._PAYOUT_MIN_AMOUNT:
                        return {"ok": False, "error": "BALANCE_INSUFFICIENT"}
            else:
                user_id_value = _resolve_reset_user_id(session, str(email or ""))
                if user_id_value <= 0:
                    return {"ok": False, "error": "RESET_UNAVAILABLE"}

            payout_miniapp_service._close_active_sessions(session, user_id_value, _PURPOSE_HUB, now_utc)
            session.add(
                PayoutMiniAppSession(
                    user_id=int(user_id_value),
                    purpose=_PURPOSE_HUB,
                    session_token_hash=payout_miniapp_service._session_token_hash(session_token),
                    status="issued",
                    expires_at=now_utc + timedelta(seconds=ttl_sec),
                )
            )
            session.flush()
    except Exception:
        _LOG.exception("event=TG_HUB_SESSION_REQUEST_FAIL action=%s", action_value)
        return {"ok": False, "error": "DB_ERROR"}

    _LOG.info(
        "event=TG_HUB_SESSION_ISSUED action=%s user_id=%s token=%s ttl_sec=%s",
        action_value,
        int(user_id_value),
        _mask_token(session_token),
        int(ttl_sec),
    )
    return {"ok": True, "miniapp_url": miniapp_url, "ttl_sec": int(ttl_sec), "short_name": "pay"}


def init_telegram_hub(init_data: str, start_param: str) -> dict:
    """EN: Validate Telegram initData once and establish trusted shared hub context.
    RU: Один раз проверить Telegram initData и установить доверенный общий hub context.
    """

    raw_init = str((init_data or "").strip())
    start_value = str((start_param or "").strip())
    if not raw_init or not start_value:
        return {"ok": False, "error": "INITDATA_INVALID"}

    try:
        payload = validate_telegram_miniapp_init_data(
            raw_init,
            get_pay_bot_token(),
            max_age_sec=get_payout_miniapp_auth_max_age_sec(),
        )
    except RuntimeError:
        return {"ok": False, "error": "CONFIG_INVALID"}
    except TelegramMiniAppValidationError as exc:
        return {"ok": False, "error": str(exc.error_code)}

    if str((payload.start_param or "").strip()) != start_value:
        return {"ok": False, "error": "START_PARAM_MISMATCH"}

    telegram_user_id = int(payload.user["id"])
    telegram_username = str((payload.user.get("username") or "").strip()) or None
    tg_auth_date = datetime.fromtimestamp(int(payload.auth_date), tz=timezone.utc)
    now_utc = datetime.now(timezone.utc)

    try:
        with get_session() as session:
            row = _load_hub_session_by_token(session, start_value, for_update=True)
            if row is None:
                return {"ok": False, "error": "SESSION_NOT_FOUND"}
            if payout_miniapp_service._expire_session_if_needed(row, now_utc):
                return {"ok": False, "error": "SESSION_EXPIRED"}
            if str(row.status) not in {"issued", "verified", "confirmed"}:
                return {"ok": False, "error": "SESSION_REJECTED"}

            account = session.scalar(select(TelegramAccount).where(TelegramAccount.user_id == int(row.user_id)).limit(1))
            if account is not None and int(account.telegram_user_id or 0) != telegram_user_id:
                row.status = "rejected"
                row.fail_reason = "TELEGRAM_ACCOUNT_MISMATCH"
                return {"ok": False, "error": "TELEGRAM_ACCOUNT_MISMATCH"}

            linked_ok, linked_error = link_or_update_telegram_account(
                session=session,
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
            row.init_data_hash = payout_miniapp_service._init_data_hash(raw_init)
            row.tg_auth_date = tg_auth_date
            row.verified_at = now_utc
            if str(row.status) == "issued":
                row.status = "verified"
            row.fail_reason = None
            session.flush()

            account = session.scalar(select(TelegramAccount).where(TelegramAccount.user_id == int(row.user_id)).limit(1))
            context = _hub_actions_context(session, row, account)
            _LOG.info(
                "event=TG_HUB_INIT_VERIFIED user_id=%s tg_uid=%s start_param=%s",
                int(row.user_id),
                telegram_user_id,
                _mask_token(start_value),
            )
            return context
    except Exception:
        _LOG.exception("event=TG_HUB_INIT_FAIL start_param=%s", _mask_token(start_value))
        return {"ok": False, "error": "DB_ERROR"}


def _validate_hub_action_session(session, hub_token: str, *, for_update: bool = False) -> tuple[dict | None, PayoutMiniAppSession | None]:
    """EN: Validate short-lived signed hub token and load corresponding verified hub session.
    RU: Проверить краткоживущий подписанный hub token и загрузить соответствующую verified hub session.
    """

    payload = _decode_hub_token(hub_token)
    if not payload.get("ok"):
        return {"ok": False, "error": str(payload.get("error"))}, None
    row = _load_hub_session_by_id(session, int(payload["session_id"]), for_update=for_update)
    if row is None:
        return {"ok": False, "error": "SESSION_NOT_FOUND"}, None
    now_utc = datetime.now(timezone.utc)
    if payout_miniapp_service._expire_session_if_needed(row, now_utc):
        return {"ok": False, "error": "SESSION_EXPIRED"}, None
    if str(row.status) not in {"verified", "confirmed"}:
        return {"ok": False, "error": "SESSION_NOT_VERIFIED"}, None
    if int(row.user_id) != int(payload["user_id"]) or int(row.telegram_user_id or 0) != int(payload["telegram_user_id"]):
        return {"ok": False, "error": "HUB_TOKEN_INVALID"}, None
    return None, row


def telegram_hub_action_verify(hub_token: str) -> dict:
    """EN: Persist Telegram verification/link state from an already trusted hub session.
    RU: Сохранить состояние верификации/привязки Telegram из уже доверенной hub session.
    """

    try:
        with get_session() as session:
            error_result, row = _validate_hub_action_session(session, hub_token, for_update=True)
            if error_result is not None or row is None:
                return error_result or {"ok": False, "error": "SESSION_NOT_FOUND"}
            linked_ok, linked_error = link_or_update_telegram_account(
                session=session,
                user_id=int(row.user_id),
                telegram_user_id=int(row.telegram_user_id or 0),
                telegram_username=row.telegram_username,
            )
            if not linked_ok:
                return {"ok": False, "error": str(linked_error or "TG_ALREADY_LINKED")}
            updated_targets = _sync_username_to_profile_tables(
                session=session,
                user_id=int(row.user_id),
                telegram_username=row.telegram_username,
            )
            session.flush()
            return {
                "ok": True,
                "telegram_verified": True,
                "telegram_user_id": int(row.telegram_user_id or 0),
                "telegram_username": str((row.telegram_username or "").strip()) or None,
                "updated_targets": updated_targets,
            }
    except Exception:
        _LOG.exception("event=TG_HUB_VERIFY_FAIL")
        return {"ok": False, "error": "DB_ERROR"}


def telegram_hub_action_reset(hub_token: str, new_password: str) -> dict:
    """EN: Execute password reset through the shared hub session using existing reset backend logic.
    RU: Выполнить сброс пароля через общую hub session с переиспользованием существующей reset-логики backend.
    """

    password_value = str(new_password or "")
    try:
        with get_session() as session:
            error_result, row = _validate_hub_action_session(session, hub_token, for_update=False)
            if error_result is not None or row is None:
                return error_result or {"ok": False, "error": "SESSION_NOT_FOUND"}
            user = session.get(User, int(row.user_id))
            if user is None:
                return {"ok": False, "error": "NOT_FOUND"}
            email_value = str((user.email or "").strip())
            reset_request = request_password_reset(email_value, "telegram", None, None)
            reset_link_code = str((reset_request.get("reset_link_code") or "").strip())
            if not reset_link_code:
                return {"ok": False, "error": "RESET_UNAVAILABLE"}
            confirm_issue = issue_reset_confirm_code(
                int(row.telegram_user_id or 0),
                reset_link_code,
                row.telegram_username,
            )
            if not confirm_issue.get("ok"):
                return {"ok": False, "error": str(confirm_issue.get("error") or "RESET_UNAVAILABLE")}
            confirm_result = confirm_password_reset(
                email_value,
                str(confirm_issue["confirm_code"]),
                password_value,
            )
            if not confirm_result.get("ok"):
                return {"ok": False, "error": str(confirm_result.get("error") or "RESET_FAILED")}
            return {"ok": True, "status": "password_reset"}
    except Exception:
        _LOG.exception("event=TG_HUB_RESET_FAIL")
        return {"ok": False, "error": "DB_ERROR"}


def telegram_hub_action_payout_context(hub_token: str) -> dict:
    """EN: Return fresh payout context for hub payout section from server-side state only.
    RU: Вернуть свежий payout context для payout-секции hub только из server-side состояния.
    """

    try:
        with get_session() as session:
            error_result, row = _validate_hub_action_session(session, hub_token, for_update=False)
            if error_result is not None or row is None:
                return error_result or {"ok": False, "error": "SESSION_NOT_FOUND"}
            account = session.scalar(select(TelegramAccount).where(TelegramAccount.user_id == int(row.user_id)).limit(1))
            return _hub_actions_context(session, row, account)["payout"] | {"ok": True}
    except Exception:
        _LOG.exception("event=TG_HUB_PAYOUT_CONTEXT_FAIL")
        return {"ok": False, "error": "DB_ERROR"}


def telegram_hub_action_payout_confirm(hub_token: str, *, amount: object, wallet_address: str, network: str) -> dict:
    """EN: Confirm payout from hub using short-lived hub token and repeated server-side checks.
    RU: Подтвердить payout из hub через краткоживущий hub token и повторные server-side проверки.
    """

    network_value = str((network or "").strip()).upper()
    if network_value != payout_miniapp_service._PAYOUT_NETWORK:
        return {"ok": False, "error": "PAYOUT_NETWORK_UNSUPPORTED"}
    try:
        with get_session() as session:
            error_result, row = _validate_hub_action_session(session, hub_token, for_update=True)
            if error_result is not None or row is None:
                return error_result or {"ok": False, "error": "SESSION_NOT_FOUND"}
            if str(row.status) == "confirmed":
                return {"ok": False, "error": "PAYOUT_ALREADY_CONFIRMED"}
            result = create_hub_payout_request_in_session(
                session,
                user_id=int(row.user_id),
                telegram_user_id=int(row.telegram_user_id or 0),
                amount=amount,
                wallet_address=wallet_address,
                miniapp_session_id=int(row.id),
            )
            if not result.get("ok"):
                return result
            row.status = "confirmed"
            row.fail_reason = None
            session.flush()
            result["network"] = payout_miniapp_service._PAYOUT_NETWORK
            return result
    except Exception:
        _LOG.exception("event=TG_HUB_PAYOUT_CONFIRM_FAIL")
        return {"ok": False, "error": "DB_ERROR"}
