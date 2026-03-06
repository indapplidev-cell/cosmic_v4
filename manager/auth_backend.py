"""EN: Client-side bridge to local server auth services.
RU: Клиентский мост к локальным серверным сервисам авторизации.
"""

from __future__ import annotations

from typing import Tuple

from server.services.auth_service import delete_user, get_user_id_by_email, login_user, register_user


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

