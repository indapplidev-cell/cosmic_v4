"""EN: Password reset workflow service using one-time email codes and hashed tokens.
RU: Сервис восстановления пароля по одноразовому email-коду и хешированным токенам.
"""

from __future__ import annotations

import hashlib
import logging
import os
import secrets
import smtplib
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage

from sqlalchemy import select, update

from server.db import get_session
from server.models.password_reset import PasswordResetToken
from server.models.user import User
from server.security.passwords import hash_password

logger = logging.getLogger(__name__)


def _env_int(name: str, default: int) -> int:
    """EN: Read integer env variable with safe fallback.
    RU: Прочитать целочисленную переменную окружения с безопасным fallback.
    """

    raw = os.getenv(name, str(default)).strip()
    try:
        return int(raw)
    except Exception:
        return int(default)


def _reset_secret() -> str:
    """EN: Return required secret for hashing reset codes.
    RU: Вернуть обязательный секрет для хеширования reset-кодов.
    """

    return os.getenv("RESET_SECRET", "").strip()


def _smtp_enabled() -> bool:
    """EN: Return True when SMTP target is configured.
    RU: Вернуть True, если SMTP-настройки заданы.
    """

    return bool(os.getenv("SMTP_HOST", "").strip())


def _dev_echo_enabled() -> bool:
    """EN: Return True when DEV response may include raw reset code.
    RU: Вернуть True, когда DEV-ответ может включать сырой reset-код.
    """

    return os.getenv("RESET_DEV_ECHO_CODE", "0").strip() == "1"


def _hash_code(code: str, secret_salt: str) -> str:
    """EN: Hash reset code with secret salt using SHA-256.
    RU: Хешировать reset-код с секретной солью через SHA-256.
    """

    payload = f"{code}{secret_salt}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _send_reset_email(to_email: str, code: str, ttl_min: int) -> bool:
    """EN: Send reset code email via configured SMTP transport.
    RU: Отправить email с кодом восстановления через настроенный SMTP-транспорт.
    """

    host = os.getenv("SMTP_HOST", "").strip()
    if not host:
        return False

    port = _env_int("SMTP_PORT", 587)
    user = os.getenv("SMTP_USER", "").strip()
    password = os.getenv("SMTP_PASSWORD", "")
    sender = os.getenv("SMTP_FROM", "").strip() or user
    use_tls = os.getenv("SMTP_TLS", "1").strip() == "1"

    if not sender:
        return False

    msg = EmailMessage()
    msg["Subject"] = "Password reset code"
    msg["From"] = sender
    msg["To"] = to_email
    msg.set_content(f"Your code: {code}. It expires in {ttl_min} minutes.")

    try:
        with smtplib.SMTP(host, port, timeout=15) as client:
            client.ehlo()
            if use_tls:
                client.starttls()
                client.ehlo()
            if user:
                client.login(user, password)
            client.send_message(msg)
        return True
    except Exception as exc:
        logger.warning("SMTP_RESET_FAILED type=%s", exc.__class__.__name__)
        return False


def request_password_reset(email: str, request_ip: str | None, user_agent: str | None) -> dict:
    """EN: Request password reset code and always return generic success to prevent enumeration.
    RU: Запросить код восстановления и всегда вернуть общий успех для защиты от enumeration.
    """

    email_value = (email or "").strip().lower()
    ttl_min = max(1, _env_int("RESET_TOKEN_TTL_MIN", 15))
    throttle_sec = max(1, _env_int("RESET_THROTTLE_SEC", 60))
    secret_salt = _reset_secret()

    if not email_value or not secret_salt:
        return {"ok": True}

    try:
        with get_session() as session:
            user = session.scalar(select(User).where(User.email == email_value))
            if user is None:
                return {"ok": True}

            last_row = session.scalar(
                select(PasswordResetToken)
                .where(PasswordResetToken.user_id == int(user.id))
                .order_by(PasswordResetToken.created_at.desc())
                .limit(1)
            )
            if last_row is not None:
                created_at = last_row.created_at
                if created_at is not None:
                    now_utc = datetime.now(timezone.utc)
                    delta = now_utc - created_at
                    if delta.total_seconds() < throttle_sec:
                        return {"ok": True}

            code = f"{secrets.randbelow(1_000_000):06d}"
            token_hash = _hash_code(code, secret_salt)
            expires_at = datetime.now(timezone.utc) + timedelta(minutes=ttl_min)

            session.execute(
                update(PasswordResetToken)
                .where(
                    PasswordResetToken.user_id == int(user.id),
                    PasswordResetToken.used_at.is_(None),
                )
                .values(used_at=datetime.now(timezone.utc))
            )

            token = PasswordResetToken(
                user_id=int(user.id),
                token_hash=token_hash,
                expires_at=expires_at,
                used_at=None,
                request_ip=(request_ip or "")[:128] or None,
                user_agent=(user_agent or "")[:512] or None,
            )
            session.add(token)
            session.flush()

            if _smtp_enabled():
                _send_reset_email(email_value, code, ttl_min)
            result = {"ok": True}
            if _dev_echo_enabled():
                result["dev_code"] = code
            return result
    except Exception:
        return {"ok": True}


def confirm_password_reset(
    email: str,
    code: str,
    new_password: str,
    request_ip: str | None,
    user_agent: str | None,
) -> dict:
    """EN: Validate reset code and set new password hash when code is valid and active.
    RU: Проверить reset-код и установить новый password_hash при валидном активном коде.
    """

    email_value = (email or "").strip().lower()
    code_value = (code or "").strip()
    new_password_value = new_password or ""
    max_attempts = max(1, _env_int("RESET_MAX_ATTEMPTS", 5))
    secret_salt = _reset_secret()

    if not email_value or not code_value or not new_password_value or not secret_salt:
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
            if token is None:
                return {"ok": False, "error": "INVALID_CODE"}

            if token.expires_at <= now_utc:
                return {"ok": False, "error": "INVALID_CODE"}

            if int(token.attempts or 0) >= max_attempts:
                return {"ok": False, "error": "INVALID_CODE"}

            expected_hash = _hash_code(code_value, secret_salt)
            if expected_hash != token.token_hash:
                token.attempts = int(token.attempts or 0) + 1
                token.request_ip = (request_ip or "")[:128] or token.request_ip
                token.user_agent = (user_agent or "")[:512] or token.user_agent
                session.flush()
                return {"ok": False, "error": "INVALID_CODE"}

            token.used_at = now_utc
            token.request_ip = (request_ip or "")[:128] or token.request_ip
            token.user_agent = (user_agent or "")[:512] or token.user_agent
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
