"""EN: Telegram verification challenge service for bot-confirmed account ownership.
RU: Сервис challenge-верификации Telegram для подтверждения владения аккаунтом через бота.
"""

from __future__ import annotations

import base64
import os
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from server.db import get_session
from server.models.profile_user import ProfileUser
from server.models.telegram_account import TelegramAccount
from server.models.telegram_outbox import TelegramOutbox
from server.models.telegram_verify_challenge import TelegramVerifyChallenge
from server.models.user import User
from server.security.tokens import gen_6digit_code, hash_code


def _env_int(name: str, default: int) -> int:
    """EN: Read integer env setting with safe fallback.
    RU: Прочитать целочисленную env-настройку с безопасным запасным значением.
    """

    raw = os.getenv(name, str(default)).strip()
    try:
        return int(raw)
    except Exception:
        return int(default)


def _reset_secret() -> str:
    """EN: Return secret used for hashing verification/reset codes.
    RU: Вернуть секрет, используемый для хеширования кодов верификации/сброса.
    """

    return os.getenv("RESET_SECRET", "").strip()


def gen_request_id(size_bytes: int = 8) -> str:
    """EN: Generate short non-secret request id using base32 alphabet.
    RU: Сгенерировать короткий не-секретный request id в base32-алфавите.
    """

    raw = secrets.token_bytes(max(6, int(size_bytes)))
    return base64.b32encode(raw).decode("ascii").rstrip("=").lower()[:12]


def request_verify(
    user_id: int,
    user_agent: str | None,
    request_ip: str | None,
) -> dict:
    """EN: Create a Telegram verification challenge and return request_id + TTL.
    RU: Создать challenge верификации Telegram и вернуть request_id + TTL.
    """

    del user_agent, request_ip
    ttl_sec = max(60, _env_int("TG_VERIFY_TTL_SEC", 600))
    throttle_sec = max(1, _env_int("TG_VERIFY_THROTTLE_SEC", 60))
    now_utc = datetime.now(timezone.utc)

    try:
        with get_session() as session:
            if session.get(User, int(user_id)) is None:
                return {"ok": False, "error": "NOT_FOUND"}
            profile_user = session.scalar(
                select(ProfileUser).where(ProfileUser.user_id == int(user_id)).limit(1)
            )
            telegram_value = ""
            if profile_user is not None and isinstance(profile_user.telegram, str):
                telegram_value = profile_user.telegram.strip()
            if not telegram_value or telegram_value.lower() == "no data":
                return {"ok": False, "error": "TELEGRAM_NOT_SET"}

            last_row = session.scalar(
                select(TelegramVerifyChallenge)
                .where(TelegramVerifyChallenge.user_id == int(user_id))
                .order_by(TelegramVerifyChallenge.created_at.desc())
                .limit(1)
            )
            if last_row is not None and last_row.created_at is not None:
                delta = now_utc - last_row.created_at
                if delta.total_seconds() < throttle_sec:
                    return {"ok": False, "error": "THROTTLED"}

            request_id = gen_request_id()
            while session.scalar(
                select(TelegramVerifyChallenge.id).where(TelegramVerifyChallenge.request_id == request_id)
            ) is not None:
                request_id = gen_request_id()

            session.add(
                TelegramVerifyChallenge(
                    user_id=int(user_id),
                    request_id=request_id,
                    code_hash=None,
                    telegram_user_id=None,
                    expires_at=now_utc + timedelta(seconds=ttl_sec),
                    sent_at=None,
                    used_at=None,
                    attempts=0,
                )
            )
            session.flush()
            return {"ok": True, "request_id": request_id, "ttl_sec": ttl_sec}
    except Exception:
        return {"ok": False, "error": "DB_ERROR"}


def bot_send_code(request_id: str, telegram_user_id: int) -> dict:
    """EN: Bind challenge to Telegram user, create hashed 6-digit code, and enqueue message.
    RU: Привязать challenge к Telegram user, создать хеш 6-значного кода и поставить сообщение в очередь.
    """

    secret = _reset_secret()
    if not secret:
        return {"ok": False, "error": "RESET_SECRET_MISSING"}

    request_id_value = (request_id or "").strip().lower()
    now_utc = datetime.now(timezone.utc)
    throttle_sec = max(1, _env_int("TG_VERIFY_THROTTLE_SEC", 60))
    ttl_sec = max(60, _env_int("TG_VERIFY_TTL_SEC", 600))

    try:
        with get_session() as session:
            challenge = session.scalar(
                select(TelegramVerifyChallenge)
                .where(
                    TelegramVerifyChallenge.request_id == request_id_value,
                    TelegramVerifyChallenge.used_at.is_(None),
                    TelegramVerifyChallenge.expires_at > now_utc,
                )
                .order_by(TelegramVerifyChallenge.created_at.desc())
                .limit(1)
            )
            if challenge is None:
                return {"ok": False, "error": "INVALID_REQUEST"}

            if challenge.sent_at is not None:
                delta = now_utc - challenge.sent_at
                if delta.total_seconds() < throttle_sec:
                    return {"ok": False, "error": "THROTTLED"}

            code = gen_6digit_code()
            challenge.code_hash = hash_code(code, secret)
            challenge.telegram_user_id = int(telegram_user_id)
            challenge.sent_at = now_utc

            ttl_min = max(1, int(ttl_sec // 60))
            session.add(
                TelegramOutbox(
                    telegram_user_id=int(telegram_user_id),
                    message=f"Cosmic: код подтверждения Telegram: {code}. Действует {ttl_min} минут.",
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


def confirm_verify(user_id: int, request_id: str, code: str) -> dict:
    """EN: Validate challenge code, mark challenge used, and upsert verified Telegram account.
    RU: Проверить код challenge, пометить challenge использованным и выполнить upsert подтверждённого Telegram-аккаунта.
    """

    secret = _reset_secret()
    if not secret:
        return {"ok": False, "error": "INVALID_CODE"}

    request_id_value = (request_id or "").strip().lower()
    code_value = (code or "").strip()
    max_attempts = max(1, _env_int("TG_VERIFY_MAX_ATTEMPTS", 5))
    now_utc = datetime.now(timezone.utc)

    try:
        with get_session() as session:
            challenge = session.scalar(
                select(TelegramVerifyChallenge)
                .where(
                    TelegramVerifyChallenge.user_id == int(user_id),
                    TelegramVerifyChallenge.request_id == request_id_value,
                    TelegramVerifyChallenge.used_at.is_(None),
                    TelegramVerifyChallenge.expires_at > now_utc,
                )
                .order_by(TelegramVerifyChallenge.created_at.desc())
                .limit(1)
            )
            if challenge is None:
                return {"ok": False, "error": "INVALID_CODE"}
            if challenge.code_hash is None or challenge.telegram_user_id is None:
                return {"ok": False, "error": "INVALID_CODE"}
            if int(challenge.attempts or 0) >= max_attempts:
                return {"ok": False, "error": "INVALID_CODE"}

            expected_hash = hash_code(code_value, secret)
            if expected_hash != challenge.code_hash:
                challenge.attempts = int(challenge.attempts or 0) + 1
                session.flush()
                return {"ok": False, "error": "INVALID_CODE"}

            existing_by_tg = session.scalar(
                select(TelegramAccount).where(TelegramAccount.telegram_user_id == int(challenge.telegram_user_id))
            )
            if existing_by_tg is not None and int(existing_by_tg.user_id) != int(user_id):
                return {"ok": False, "error": "ALREADY_LINKED"}

            challenge.used_at = now_utc
            account = session.scalar(select(TelegramAccount).where(TelegramAccount.user_id == int(user_id)))
            if account is None:
                account = TelegramAccount(
                    user_id=int(user_id),
                    telegram_user_id=int(challenge.telegram_user_id),
                    verified_at=now_utc,
                )
                session.add(account)
            else:
                account.telegram_user_id = int(challenge.telegram_user_id)
                account.verified_at = now_utc

            session.flush()
            return {"ok": True}
    except Exception:
        return {"ok": False, "error": "INVALID_CODE"}
