"""EN: DB-backed auth/account service without HTTP transport.
RU: Сервис авторизации/аккаунта на БД без HTTP-транспорта.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select

from server.db import get_session
from server.models.balance import Balance
from server.models.profile_game import ProfileGame
from server.models.profile_user import ProfileUser
from server.models.refresh_token import RefreshToken
from server.models.telegram_account import TelegramAccount
from server.models.user import User
from server.security.jwt import create_access_token, create_refresh_token, decode_refresh_token
from server.security.passwords import hash_password, needs_rehash, verify_password


def _normalize_profile_text(value: str | None) -> str:
    """EN: Normalize profile text values to stable non-empty UI-safe string.
    RU: Нормализовать текстовые поля профиля в стабильную непустую строку для UI.
    """

    cleaned = (value or "").strip()
    return cleaned if cleaned else "no data"


def _build_user_snapshot(session, user_id: int) -> dict | None:
    """EN: Build user snapshot by joining users/profile_users/profile_games.
    RU: Собрать snapshot пользователя через join users/profile_users/profile_games.
    """

    stmt = (
        select(
            User.id.label("user_id"),
            User.email.label("email"),
            ProfileUser.login.label("login"),
            ProfileUser.phone.label("phone"),
            ProfileUser.telegram.label("telegram"),
            TelegramAccount.telegram_user_id.label("telegram_user_id"),
            TelegramAccount.telegram_username.label("telegram_account_username"),
            TelegramAccount.verified_at.label("telegram_verified_at"),
            ProfileGame.record.label("record"),
            ProfileGame.rating.label("rating"),
            ProfileGame.balance.label("balance"),
        )
        .select_from(User)
        .outerjoin(ProfileUser, ProfileUser.user_id == User.id)
        .outerjoin(TelegramAccount, TelegramAccount.user_id == User.id)
        .outerjoin(ProfileGame, ProfileGame.user_id == User.id)
        .where(User.id == int(user_id))
    )
    row = session.execute(stmt).mappings().one_or_none()
    if row is None:
        return None

    return {
        "user_id": int(row["user_id"]),
        "email": str((row.get("email") or "").strip()),
        "login": _normalize_profile_text(row.get("login")),
        "phone": _normalize_profile_text(row.get("phone")),
        "telegram": _normalize_profile_text(row.get("telegram")),
        "telegram_username": _normalize_profile_text(row.get("telegram_account_username")),
        "telegram_user_id": int(row.get("telegram_user_id") or 0),
        "telegram_linked": bool(row.get("telegram_user_id")),
        "telegram_verified": bool(row.get("telegram_verified_at")),
        "record": int(row.get("record") or 0),
        "rating": int(row.get("rating") or 0),
        "balance": round(float(row.get("balance") or 0.0), 3),
    }


def _issue_tokens(
    session,
    *,
    user_id: int,
    email: str,
    user_agent: str | None = None,
    ip: str | None = None,
) -> dict:
    """EN: Issue access+refresh tokens and persist refresh JTI for revocation/rotation.
    RU: Выдать access+refresh токены и сохранить refresh JTI для отзыва/ротации.
    """

    access_token = create_access_token(user_id=int(user_id), email=email)
    refresh_token, refresh_jti, refresh_expires_at = create_refresh_token(user_id=int(user_id))
    if not access_token or not refresh_token or not refresh_jti:
        return {}

    session.add(
        RefreshToken(
            user_id=int(user_id),
            jti=str(refresh_jti),
            expires_at=refresh_expires_at,
            revoked_at=None,
            user_agent=str((user_agent or "").strip()) or None,
            ip=str((ip or "").strip()) or None,
        )
    )
    session.flush()
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
    }


def register_user(email: str, psw: str, *, user_agent: str | None = None, ip: str | None = None) -> dict:
    """EN: Register user, persist password hash, and bootstrap related rows.
    RU: Зарегистрировать пользователя, сохранить хеш пароля и создать связанные строки.
    """

    email_value = (email or "").strip()
    psw_value = (psw or "").strip()
    if not email_value or not psw_value:
        return {"ok": False, "error": "EMPTY_FIELDS"}

    try:
        with get_session() as session:
            exists = session.scalar(select(User.id).where(User.email == email_value))
            if exists is not None:
                return {"ok": False, "error": "EMAIL_EXISTS"}

            user = User(email=email_value, password_hash=hash_password(psw_value))
            session.add(user)
            session.flush()

            session.add(ProfileUser(user_id=user.id))
            session.add(ProfileGame(user_id=user.id))
            session.add(Balance(user_id=user.id))
            session.flush()
            snapshot = _build_user_snapshot(session, int(user.id))
            tokens = _issue_tokens(
                session,
                user_id=int(user.id),
                email=email_value,
                user_agent=user_agent,
                ip=ip,
            )
            if not tokens:
                return {"ok": False, "error": "CONFIG_INVALID"}
            result = {"ok": True, "user_id": int(user.id), "user": snapshot}
            result.update(tokens)
            return result
    except Exception:
        return {"ok": False, "error": "DB_ERROR"}


def login_user(email: str, psw: str, *, user_agent: str | None = None, ip: str | None = None) -> dict:
    """EN: Validate login against stored hash and upgrade hash cost when needed.
    RU: Проверить вход по сохранённому хешу и обновить cost хеша при необходимости.
    """

    email_value = (email or "").strip()
    psw_value = (psw or "").strip()
    if not email_value or not psw_value:
        return {"ok": False, "error": "EMPTY_FIELDS"}

    try:
        with get_session() as session:
            user = session.scalar(select(User).where(User.email == email_value))
            if user is None:
                return {"ok": False, "error": "NOT_FOUND"}
            if not verify_password(psw_value, user.password_hash):
                return {"ok": False, "error": "BAD_PASSWORD"}

            if needs_rehash(user.password_hash):
                user.password_hash = hash_password(psw_value)
                session.flush()

            snapshot = _build_user_snapshot(session, int(user.id))
            tokens = _issue_tokens(
                session,
                user_id=int(user.id),
                email=email_value,
                user_agent=user_agent,
                ip=ip,
            )
            if not tokens:
                return {"ok": False, "error": "CONFIG_INVALID"}
            result = {"ok": True, "user_id": int(user.id), "user": snapshot}
            result.update(tokens)
            return result
    except Exception:
        return {"ok": False, "error": "DB_ERROR"}


def get_user_id_by_email(email: str) -> dict:
    """EN: Resolve user id by email for legacy cache fallback paths.
    RU: Найти user id по email для fallback-путей со старым кешем.
    """

    email_value = (email or "").strip()
    if not email_value:
        return {"ok": False, "error": "EMPTY_FIELDS"}
    try:
        with get_session() as session:
            user_id = session.scalar(select(User.id).where(User.email == email_value))
            if user_id is None:
                return {"ok": False, "error": "NOT_FOUND"}
            return {"ok": True, "user_id": int(user_id)}
    except Exception:
        return {"ok": False, "error": "DB_ERROR"}


def get_user_snapshot(user_id: int) -> dict:
    """EN: Return user snapshot by user_id for startup cache validation/sync.
    RU: Вернуть snapshot пользователя по user_id для стартовой проверки/синхронизации кэша.
    """

    try:
        user_id_value = int(user_id)
    except Exception:
        return {"ok": False, "error": "BAD_USER_ID"}

    try:
        with get_session() as session:
            snapshot = _build_user_snapshot(session, user_id_value)
            if snapshot is None:
                return {"ok": False, "error": "NOT_FOUND"}
            return {"ok": True, "user": snapshot}
    except Exception:
        return {"ok": False, "error": "DB_ERROR"}


def get_user_snapshot_by_email(email: str) -> dict:
    """EN: Resolve user by email and return full user snapshot.
    RU: Найти пользователя по email и вернуть полный snapshot пользователя.
    """

    email_value = (email or "").strip()
    if not email_value:
        return {"ok": False, "error": "EMPTY_FIELDS"}

    try:
        with get_session() as session:
            user_id = session.scalar(select(User.id).where(User.email == email_value))
            if user_id is None:
                return {"ok": False, "error": "NOT_FOUND"}
            snapshot = _build_user_snapshot(session, int(user_id))
            if snapshot is None:
                return {"ok": False, "error": "NOT_FOUND"}
            return {"ok": True, "user": snapshot}
    except Exception:
        return {"ok": False, "error": "DB_ERROR"}


def delete_user(user_id: int) -> dict:
    """EN: Delete user row; related rows are removed by DB cascade.
    RU: Удалить пользователя; связанные записи удаляются каскадом БД.
    """

    try:
        user_id_value = int(user_id)
    except Exception:
        return {"ok": False, "error": "BAD_USER_ID"}

    try:
        with get_session() as session:
            user = session.get(User, user_id_value)
            if user is None:
                return {"ok": False, "error": "NOT_FOUND"}
            session.delete(user)
            return {"ok": True}
    except Exception:
        return {"ok": False, "error": "DB_ERROR"}


def refresh_auth(refresh_token: str, *, user_agent: str | None = None, ip: str | None = None) -> dict:
    """EN: Rotate refresh token and issue a new access token pair from a valid refresh JWT.
    RU: Ротировать refresh-токен и выдать новую пару токенов из валидного refresh JWT.
    """

    token_value = str((refresh_token or "").strip())
    if not token_value:
        return {"ok": False, "error": "UNAUTHORIZED"}

    payload = decode_refresh_token(token_value)
    if not isinstance(payload, dict):
        return {"ok": False, "error": "UNAUTHORIZED"}

    raw_sub = str((payload.get("sub") or "").strip())
    raw_jti = str((payload.get("jti") or "").strip())
    try:
        user_id = int(raw_sub)
    except Exception:
        return {"ok": False, "error": "UNAUTHORIZED"}
    if user_id <= 0 or not raw_jti:
        return {"ok": False, "error": "UNAUTHORIZED"}

    now_utc = datetime.now(timezone.utc)
    try:
        with get_session() as session:
            row = session.scalar(select(RefreshToken).where(RefreshToken.jti == raw_jti))
            if row is None:
                return {"ok": False, "error": "UNAUTHORIZED"}
            if int(row.user_id) != int(user_id):
                return {"ok": False, "error": "UNAUTHORIZED"}
            if row.revoked_at is not None or row.expires_at <= now_utc:
                return {"ok": False, "error": "UNAUTHORIZED"}

            user = session.get(User, int(user_id))
            if user is None:
                return {"ok": False, "error": "UNAUTHORIZED"}

            # EN: Rotation is mandatory: revoke old jti and issue a fresh pair.
            # RU: Ротация обязательна: отзываем старый jti и выдаём новую пару.
            row.revoked_at = now_utc
            tokens = _issue_tokens(
                session,
                user_id=int(user_id),
                email=str((user.email or "").strip()),
                user_agent=user_agent,
                ip=ip,
            )
            if not tokens:
                return {"ok": False, "error": "UNAUTHORIZED"}
            return {"ok": True, **tokens}
    except Exception:
        return {"ok": False, "error": "UNAUTHORIZED"}


def logout_user(refresh_token: str) -> dict:
    """EN: Revoke refresh token JTI so it cannot be used for future token refresh.
    RU: Отозвать refresh-token JTI, чтобы его нельзя было использовать для обновления токенов.
    """

    token_value = str((refresh_token or "").strip())
    if not token_value:
        return {"ok": False, "error": "UNAUTHORIZED"}

    payload = decode_refresh_token(token_value)
    if not isinstance(payload, dict):
        return {"ok": False, "error": "UNAUTHORIZED"}
    raw_jti = str((payload.get("jti") or "").strip())
    if not raw_jti:
        return {"ok": False, "error": "UNAUTHORIZED"}

    now_utc = datetime.now(timezone.utc)
    try:
        with get_session() as session:
            row = session.scalar(select(RefreshToken).where(RefreshToken.jti == raw_jti))
            if row is None:
                return {"ok": False, "error": "UNAUTHORIZED"}
            if row.revoked_at is None:
                row.revoked_at = now_utc
            return {"ok": True}
    except Exception:
        return {"ok": False, "error": "UNAUTHORIZED"}
