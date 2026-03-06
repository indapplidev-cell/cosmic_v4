"""EN: Client bridge to backend HTTP API.
RU: Клиентский мост к backend HTTP API.
"""

from __future__ import annotations

from typing import Tuple

from manager import api_client

_HEALTHCHECK_DONE = False


def _ensure_healthcheck_once() -> None:
    """EN: Run one lightweight API health probe and log result.
    RU: Выполнить один легкий health-пинг API и залогировать результат.
    """
    global _HEALTHCHECK_DONE
    if _HEALTHCHECK_DONE:
        return
    _HEALTHCHECK_DONE = True
    ok, payload = api_client.healthz(timeout=3)
    if ok:
        print("[API] /healthz OK", flush=True)
    else:
        print(f"[API] /healthz FAILED: {payload}", flush=True)


def _error_code(payload: object, default: str) -> str:
    """EN: Normalize API error payload into string code.
    RU: Нормализовать ошибку API в строковый код.
    """
    if isinstance(payload, dict):
        return str(payload.get("error", default))
    return default


def register(email: str, psw: str) -> Tuple[bool, str | int]:
    """EN: Register and return (ok, user_id|error_code).
    RU: Регистрация с ответом в формате (ok, user_id|код_ошибки).
    """
    _ensure_healthcheck_once()
    ok, payload = api_client.request("POST", "/auth/register", json={"email": email, "psw": psw})
    if not ok:
        return False, _error_code(payload, "NETWORK")
    if isinstance(payload, dict) and payload.get("ok"):
        return True, int(payload["user_id"])
    return False, _error_code(payload, "API_ERROR")


def login(email: str, psw: str) -> Tuple[bool, str | int]:
    """EN: Login and return (ok, user_id|error_code).
    RU: Вход с ответом в формате (ok, user_id|код_ошибки).
    """
    _ensure_healthcheck_once()
    ok, payload = api_client.request("POST", "/auth/login", json={"email": email, "psw": psw})
    if not ok:
        return False, _error_code(payload, "NETWORK")
    if isinstance(payload, dict) and payload.get("ok"):
        return True, int(payload["user_id"])
    return False, _error_code(payload, "API_ERROR")


def resolve_user_id(email: str) -> Tuple[bool, str | int]:
    """EN: Resolve user id by email for legacy cache fallback.
    RU: Получить user_id по email для fallback со старым кешем.
    """
    # EN: API contract currently has no dedicated endpoint for this lookup.
    # RU: В текущем API-контракте нет отдельного эндпоинта для этого поиска.
    _ = email
    return False, "NOT_SUPPORTED"


def delete_account(user_id: int) -> bool:
    """EN: Delete account by user id.
    RU: Удалить аккаунт по user_id.
    """
    _ensure_healthcheck_once()
    ok, payload = api_client.request("POST", "/auth/delete", json={"user_id": int(user_id)})
    if not ok:
        return False
    return bool(isinstance(payload, dict) and payload.get("ok"))


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
    _ensure_healthcheck_once()
    body = {"user_id": int(user_id)}
    if login is not None:
        body["login"] = login
    if phone is not None:
        body["phone"] = phone
    if telegram is not None:
        body["telegram"] = telegram
    ok, payload = api_client.request("POST", "/profile/user/update", json=body)
    return bool(ok and isinstance(payload, dict) and payload.get("ok"))


def delete_profile_user_fields(user_id: int, fields: list[str]) -> bool:
    """EN: Reset selected profile-user fields to defaults.
    RU: Сбросить выбранные поля profile_user к значениям по умолчанию.
    """
    _ensure_healthcheck_once()
    ok, payload = api_client.request(
        "POST",
        "/profile/user/clear",
        json={"user_id": int(user_id), "fields": list(fields)},
    )
    return bool(ok and isinstance(payload, dict) and payload.get("ok"))


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
    _ensure_healthcheck_once()
    body = {"user_id": int(user_id)}
    if record is not None:
        body["record"] = int(record)
    if rating is not None:
        body["rating"] = int(rating)
    if balance is not None:
        body["balance"] = int(balance)
    ok, payload = api_client.request("POST", "/profile/game/update", json=body)
    return bool(ok and isinstance(payload, dict) and payload.get("ok"))


def delete_profile_game_fields(user_id: int, fields: list[str]) -> bool:
    """EN: Reset selected profile-game fields to defaults.
    RU: Сбросить выбранные поля profile_game к значениям по умолчанию.
    """
    _ensure_healthcheck_once()
    ok, payload = api_client.request(
        "POST",
        "/profile/game/clear",
        json={"user_id": int(user_id), "fields": list(fields)},
    )
    return bool(ok and isinstance(payload, dict) and payload.get("ok"))


def get_top_ratings(limit: int = 100) -> list[dict]:
    """EN: Return leaderboard rows sorted by rating/record.
    RU: Вернуть строки рейтинга, отсортированные по rating/record.
    """
    _ensure_healthcheck_once()
    ok, payload = api_client.request("GET", "/rating/top", params={"limit": int(limit)})
    if not ok or not isinstance(payload, list):
        return []
    return payload
