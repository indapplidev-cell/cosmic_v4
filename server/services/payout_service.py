"""EN: Legacy services for payout bot deep-link issuance and acknowledgement.
RU: Legacy-сервисы выдачи и подтверждения payout bot deep-link кодов.
"""

from __future__ import annotations

import base64
import logging
import os
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from server.db import get_session
from server.models.payout_link_code import PayoutLinkCode
from server.models.user import User
from server.security.tokens import hash_code


_LOG = logging.getLogger("cosmic.payout_service")


def _env_int(name: str, default: int) -> int:
    """EN: Read integer env value with safe fallback.
    RU: Прочитать целочисленное env-значение с безопасным fallback.
    """

    raw = str((os.getenv(name, str(default)) or "").strip())
    try:
        return int(raw)
    except Exception:
        return int(default)


def _reset_secret() -> str:
    """EN: Return RESET_SECRET used for hashing payout codes.
    RU: Вернуть RESET_SECRET, используемый для хеширования payout-кодов.
    """

    return str((os.getenv("RESET_SECRET", "") or "").strip())


def _mask_code(code: str) -> str:
    """EN: Mask payout code for logs without revealing plaintext.
    RU: Замаскировать payout-код в логах без раскрытия открытого значения.
    """

    value = str((code or "").strip())
    if not value:
        return "-"
    if len(value) <= 8:
        return f"{value[:1]}...{value[-1:]}(len={len(value)})"
    return f"{value[:4]}...{value[-4:]}(len={len(value)})"


def _gen_payout_code() -> str:
    """EN: Generate opaque 32-char-ish urlsafe payout link code.
    RU: Сгенерировать непрозрачный urlsafe payout link-код длиной около 32 символов.
    """

    return base64.urlsafe_b64encode(os.urandom(24)).decode("ascii").rstrip("=")[:48]


def request_payout_link_code(user_id: int) -> dict:
    """EN: Issue or reuse legacy payout deep-link code for non-security fallback UX only.
    RU: Выдать или переиспользовать legacy payout deep-link код только для non-security fallback UX.
    """

    secret = _reset_secret()
    if not secret:
        return {"ok": False, "error": "RESET_SECRET_MISSING"}

    ttl_sec = max(60, _env_int("PAYOUT_LINK_TTL_SEC", 600))
    throttle_sec = max(1, _env_int("PAYOUT_LINK_THROTTLE_SEC", 30))
    now_utc = datetime.now(timezone.utc)

    with get_session() as session:
        user = session.get(User, int(user_id))
        if user is None:
            return {"ok": False, "error": "NOT_FOUND"}

        latest = session.scalar(
            select(PayoutLinkCode)
            .where(PayoutLinkCode.user_id == int(user_id))
            .order_by(PayoutLinkCode.created_at.desc())
            .limit(1)
        )
        if (
            latest is not None
            and latest.used_at is None
            and latest.expires_at > now_utc
            and latest.created_at >= now_utc - timedelta(seconds=throttle_sec)
        ):
            reused_code = _gen_payout_code()
            latest.code_hash = hash_code(reused_code, secret)
            latest.expires_at = now_utc + timedelta(seconds=ttl_sec)
            latest.last_attempt_at = None
            _LOG.info(
                "event=PAYOUT_LINK_REUSED user_id=%s code=%s ttl_sec=%s",
                int(user_id),
                _mask_code(reused_code),
                int(ttl_sec),
            )
            return {"ok": True, "code": reused_code, "ttl_sec": ttl_sec}

        code = _gen_payout_code()
        session.add(
            PayoutLinkCode(
                user_id=int(user_id),
                code_hash=hash_code(code, secret),
                expires_at=now_utc + timedelta(seconds=ttl_sec),
            )
        )
        session.flush()
        _LOG.info(
            "event=PAYOUT_LINK_ISSUED user_id=%s code=%s ttl_sec=%s",
            int(user_id),
            _mask_code(code),
            int(ttl_sec),
        )
        return {"ok": True, "code": code, "ttl_sec": ttl_sec}


def ack_payout_link_code(code: str, telegram_user_id: int, telegram_username: str | None) -> dict:
    """EN: Consume legacy payout link code after bot `/start <code>` acknowledgement.
    RU: Поглотить legacy payout link-код после подтверждения ботом через `/start <code>`.

    EN: This flow is kept only as legacy UX fallback and must not be used as a
    security boundary for payout identity verification.
    RU: Этот flow оставлен только как legacy UX fallback и не должен использоваться
    как security boundary для payout identity verification.
    """

    secret = _reset_secret()
    if not secret:
        return {"ok": False, "error": "RESET_SECRET_MISSING"}

    code_value = str((code or "").strip())
    if not code_value:
        return {"ok": False, "error": "CODE_INVALID"}

    now_utc = datetime.now(timezone.utc)
    code_hash = hash_code(code_value, secret)

    with get_session() as session:
        row = session.scalar(
            select(PayoutLinkCode)
            .where(PayoutLinkCode.code_hash == code_hash)
            .limit(1)
        )
        if row is None:
            _LOG.info(
                "event=PAYOUT_LINK_ACK ok=false error=CODE_NOT_FOUND tg_uid=%s tg_username=%s code=%s",
                int(telegram_user_id or 0),
                str((telegram_username or "").strip()) or "-",
                _mask_code(code_value),
            )
            return {"ok": False, "error": "CODE_INVALID"}
        if row.used_at is not None:
            return {"ok": False, "error": "CODE_USED"}
        if row.expires_at <= now_utc:
            return {"ok": False, "error": "CODE_EXPIRED"}

        row.used_at = now_utc
        row.last_attempt_at = now_utc
        row.attempts = int(row.attempts or 0) + 1
        _LOG.info(
            "event=PAYOUT_LINK_ACK ok=true user_id=%s tg_uid=%s tg_username=%s code=%s",
            int(row.user_id),
            int(telegram_user_id or 0),
            str((telegram_username or "").strip()) or "-",
            _mask_code(code_value),
        )
        return {"ok": True, "user_id": int(row.user_id)}


def get_last_payout_link_status(user_id: int) -> dict:
    """EN: Return used/ttl status for the latest payout link code of a user.
    RU: Вернуть used/ttl-статус для последнего payout link-кода пользователя.
    """

    now_utc = datetime.now(timezone.utc)
    with get_session() as session:
        row = session.scalar(
            select(PayoutLinkCode)
            .where(PayoutLinkCode.user_id == int(user_id))
            .order_by(PayoutLinkCode.created_at.desc())
            .limit(1)
        )
        if row is None:
            return {"ok": True, "used": False, "ttl_sec": 0}
        ttl_sec = max(0, int((row.expires_at - now_utc).total_seconds()))
        return {
            "ok": True,
            "used": bool(row.used_at is not None),
            "ttl_sec": int(ttl_sec),
        }
