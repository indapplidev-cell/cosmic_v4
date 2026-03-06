"""EN: Client-side bridge to local server auth services.
RU: Клиентский мост к локальным серверным сервисам авторизации.
"""

from __future__ import annotations

from typing import Tuple

from server.services.auth_service import delete_user, get_user_id_by_email, login_user, register_user
from server.services.profile_service import (
    clear_profile_game_fields,
    clear_profile_user_fields,
    update_profile_game,
    update_profile_user,
)
from server.services.rating_service import get_top_ratings as get_top_ratings_service


def register(email: str, psw: str) -> Tuple[bool, str | int]:
    """EN: Register and return (ok, user_id|error_code).
    RU: Зарегистрировать и вернуть (ok, user_id|код_ошибки).
    """
    result = register_user(email, psw)
    if result.get("ok"):
        return True, int(result["user_id"])
    return False, str(result.get("error", "DB_ERROR"))


def login(email: str, psw: str) -> Tuple[bool, str | int]:
    """EN: Login and return (ok, user_id|error_code).
    RU: Выполнить вход и вернуть (ok, user_id|код_ошибки).
    """
    result = login_user(email, psw)
    if result.get("ok"):
        return True, int(result["user_id"])
    return False, str(result.get("error", "DB_ERROR"))


def resolve_user_id(email: str) -> Tuple[bool, str | int]:
    """EN: Resolve user id by email for legacy cache fallback.
    RU: Найти user id по email для fallback со старым кешем.
    """
    result = get_user_id_by_email(email)
    if result.get("ok"):
        return True, int(result["user_id"])
    return False, str(result.get("error", "DB_ERROR"))


def delete_account(user_id: int) -> bool:
    """EN: Delete account by user id.
    RU: Удалить аккаунт по user id.
    """
    result = delete_user(user_id)
    return bool(result.get("ok"))


def save_profile_user(
    user_id: int,
    *,
    login: str | None = None,
    phone: str | None = None,
    telegram: str | None = None,
) -> bool:
    """EN: Persist provided profile-user fields.
    RU: Сохранить переданные поля profile_user.
    """
    result = update_profile_user(user_id, login=login, phone=phone, telegram=telegram)
    return bool(result.get("ok"))


def delete_profile_user_fields(user_id: int, fields: list[str]) -> bool:
    """EN: Reset selected profile-user fields to defaults.
    RU: Сбросить выбранные поля profile_user к дефолтам.
    """
    result = clear_profile_user_fields(user_id, fields)
    return bool(result.get("ok"))


def save_profile_game(
    user_id: int,
    *,
    record: int | None = None,
    rating: int | None = None,
    balance: int | None = None,
) -> bool:
    """EN: Persist provided profile-game fields.
    RU: Сохранить переданные поля profile_game.
    """
    result = update_profile_game(user_id, record=record, rating=rating, balance=balance)
    return bool(result.get("ok"))


def delete_profile_game_fields(user_id: int, fields: list[str]) -> bool:
    """EN: Reset selected profile-game fields to defaults.
    RU: Сбросить выбранные поля profile_game к дефолтам.
    """
    result = clear_profile_game_fields(user_id, fields)
    return bool(result.get("ok"))


def get_top_ratings(limit: int = 100) -> list[dict]:
    """EN: Return leaderboard rows sorted by rating/record.
    RU: Вернуть строки лидерборда, отсортированные по rating/record.
    """
    return get_top_ratings_service(limit=limit)
