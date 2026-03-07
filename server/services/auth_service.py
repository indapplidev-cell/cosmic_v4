"""EN: DB-backed auth/account service without HTTP transport.
RU: Сервис авторизации/аккаунта на БД без HTTP-транспорта.
"""

from __future__ import annotations

from sqlalchemy import select

from server.db import get_session
from server.models.balance import Balance
from server.models.profile_game import ProfileGame
from server.models.profile_user import ProfileUser
from server.models.user import User
from server.security.passwords import hash_password, needs_rehash, verify_password


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
            return {"ok": True, "user_id": int(user.id)}
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

            return {"ok": True, "user_id": int(user.id)}
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
