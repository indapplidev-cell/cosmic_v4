"""EN: DB-backed auth/account service without HTTP transport.
RU: Сервис авторизации/аккаунта на БД без HTTP-транспорта.
"""

from __future__ import annotations

from sqlalchemy import select

from server.db import get_session
from server.models.balance import Balance
from server.models.profile_game import ProfileGame
from server.models.profile_user import ProfileUser
from server.models.telegram_account import TelegramAccount
from server.models.user import User
from server.security.jwt import create_access_token
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
        "telegram_linked": bool(row.get("telegram_user_id")),
        "telegram_verified": bool(row.get("telegram_verified_at")),
        "record": int(row.get("record") or 0),
        "rating": int(row.get("rating") or 0),
        "balance": round(float(row.get("balance") or 0.0), 3),
    }


def register_user(email: str, psw: str) -> dict:
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
            token = create_access_token(user_id=int(user.id), email=email_value)
            result = {"ok": True, "user_id": int(user.id), "user": snapshot}
            if token:
                result["access_token"] = token
            return result
    except Exception:
        return {"ok": False, "error": "DB_ERROR"}


def login_user(email: str, psw: str) -> dict:
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
            token = create_access_token(user_id=int(user.id), email=email_value)
            result = {"ok": True, "user_id": int(user.id), "user": snapshot}
            if token:
                result["access_token"] = token
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
