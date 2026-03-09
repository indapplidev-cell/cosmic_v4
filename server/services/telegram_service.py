"""EN: Telegram link/reset services with hashed tokens and outbox retry queue.
RU: Сервисы привязки/reset через Telegram с хешированными токенами и retry-очередью outbox.
"""

from __future__ import annotations

import os
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update

from server.db import get_session
from server.models.password_reset import PasswordResetToken
from server.models.telegram_account import TelegramAccount
from server.models.telegram_link_token import TelegramLinkToken
from server.models.telegram_outbox import TelegramOutbox
from server.models.user import User
from server.security.passwords import hash_password
from server.security.tokens import gen_6digit_code, hash_code


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


def request_link_code(user_id: int) -> dict:
    """EN: Create one-time Telegram deep-link start token for authenticated user.
    RU: Создать одноразовый deep-link start token для привязки Telegram авторизованного пользователя.
    """

    secret = _reset_secret()
    if not secret:
        return {"ok": False, "error": "RESET_SECRET_MISSING"}

    ttl_sec = max(60, _env_int("TG_LINK_TTL_SEC", 600))
    start_token = secrets.token_urlsafe(36)
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
            return {"ok": True, "start_token": start_token, "ttl_sec": ttl_sec}
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
