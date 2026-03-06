"""EN: Profile/game DB service for update/clear operations.
RU: Сервис БД профиля/игры для операций обновления и очистки.
"""

from __future__ import annotations

from server.db import get_session
from server.models.profile_game import ProfileGame
from server.models.profile_user import ProfileUser

_PROFILE_USER_FIELDS = {"login", "phone", "telegram"}
_PROFILE_GAME_FIELDS = {"record", "rating", "balance"}


def _ensure_profile_user(session, user_id: int) -> ProfileUser:
    """EN: Get or create one-to-one ProfileUser row.
    RU: Получить или создать строку ProfileUser один-к-одному.
    """
    obj = session.query(ProfileUser).filter(ProfileUser.user_id == user_id).one_or_none()
    if obj is None:
        obj = ProfileUser(user_id=user_id)
        session.add(obj)
        session.flush()
    return obj


def _ensure_profile_game(session, user_id: int) -> ProfileGame:
    """EN: Get or create one-to-one ProfileGame row.
    RU: Получить или создать строку ProfileGame один-к-одному.
    """
    obj = session.query(ProfileGame).filter(ProfileGame.user_id == user_id).one_or_none()
    if obj is None:
        obj = ProfileGame(user_id=user_id)
        session.add(obj)
        session.flush()
    return obj


def update_profile_user(
    user_id: int,
    *,
    login: str | None = None,
    phone: str | None = None,
    telegram: str | None = None,
) -> dict:
    """EN: Update non-empty ProfileUser fields for provided user.
    RU: Обновить непустые поля ProfileUser для указанного пользователя.
    """
    try:
        user_id_value = int(user_id)
    except Exception:
        return {"ok": False, "error": "BAD_USER_ID"}

    try:
        with get_session() as session:
            obj = _ensure_profile_user(session, user_id_value)

            if login is not None and str(login).strip():
                obj.login = str(login).strip()
            if phone is not None and str(phone).strip():
                obj.phone = str(phone).strip()
            if telegram is not None and str(telegram).strip():
                obj.telegram = str(telegram).strip()

            session.flush()
            return {"ok": True}
    except Exception:
        return {"ok": False, "error": "DB_ERROR"}


def clear_profile_user_fields(user_id: int, fields: list[str]) -> dict:
    """EN: Reset selected ProfileUser fields to DB default literal value.
    RU: Сбросить выбранные поля ProfileUser к дефолтному литералу БД.
    """
    try:
        user_id_value = int(user_id)
    except Exception:
        return {"ok": False, "error": "BAD_USER_ID"}

    valid_fields = [f for f in fields if f in _PROFILE_USER_FIELDS]
    if not valid_fields:
        return {"ok": True}

    try:
        with get_session() as session:
            obj = _ensure_profile_user(session, user_id_value)
            for field in valid_fields:
                setattr(obj, field, "no data")
            session.flush()
            return {"ok": True}
    except Exception:
        return {"ok": False, "error": "DB_ERROR"}


def update_profile_game(
    user_id: int,
    *,
    record: int | None = None,
    rating: int | None = None,
    balance: int | None = None,
) -> dict:
    """EN: Update provided ProfileGame numeric fields.
    RU: Обновить переданные числовые поля ProfileGame.
    """
    try:
        user_id_value = int(user_id)
    except Exception:
        return {"ok": False, "error": "BAD_USER_ID"}

    try:
        with get_session() as session:
            obj = _ensure_profile_game(session, user_id_value)

            if record is not None:
                obj.record = int(record)
            if rating is not None:
                obj.rating = int(rating)
            if balance is not None:
                obj.balance = int(balance)

            session.flush()
            return {"ok": True}
    except Exception:
        return {"ok": False, "error": "DB_ERROR"}


def clear_profile_game_fields(user_id: int, fields: list[str]) -> dict:
    """EN: Reset selected ProfileGame fields to numeric zero.
    RU: Сбросить выбранные поля ProfileGame в числовой ноль.
    """
    try:
        user_id_value = int(user_id)
    except Exception:
        return {"ok": False, "error": "BAD_USER_ID"}

    valid_fields = [f for f in fields if f in _PROFILE_GAME_FIELDS]
    if not valid_fields:
        return {"ok": True}

    try:
        with get_session() as session:
            obj = _ensure_profile_game(session, user_id_value)
            for field in valid_fields:
                setattr(obj, field, 0)
            session.flush()
            return {"ok": True}
    except Exception:
        return {"ok": False, "error": "DB_ERROR"}

