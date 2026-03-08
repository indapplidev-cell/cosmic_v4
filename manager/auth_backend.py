"""EN: Client bridge to backend HTTP API.
RU: Клиентский мост к backend HTTP API.
"""

from __future__ import annotations

from typing import Tuple

from manager import api_client
from manager.session_manager import sync_user_snapshot_from_payload
from manager.user_snapshot_store import UserSnapshotStore

_HEALTHCHECK_DONE = False
_BACKEND_READY = False


def _ensure_healthcheck_once() -> None:
    """EN: Run one lightweight API health probe and log result.
    RU: Выполнить один легкий health-пинг API и залогировать результат.
    """
    global _HEALTHCHECK_DONE, _BACKEND_READY
    if _HEALTHCHECK_DONE:
        return
    _HEALTHCHECK_DONE = True
    ok, payload = api_client.healthz(timeout=3)
    if ok:
        print("[API] /healthz OK", flush=True)
    else:
        print(f"[API] /healthz FAILED: {payload}", flush=True)
        _BACKEND_READY = False
        return

    ok_meta, meta_payload = api_client.compatibility(timeout=3)
    db_ok = bool(
        ok_meta
        and isinstance(meta_payload, dict)
        and meta_payload.get("ok")
        and isinstance(meta_payload.get("db"), dict)
        and bool(meta_payload["db"].get("is_current"))
    )
    if db_ok:
        print("[API] /meta/compat OK (DB current)", flush=True)
    else:
        print(f"[API] /meta/compat FAILED: {meta_payload}", flush=True)
    _BACKEND_READY = db_ok


def _backend_ready() -> bool:
    """EN: Ensure backend checks are performed and return readiness flag.
    RU: Гарантировать выполнение backend-проверок и вернуть флаг готовности.
    """

    _ensure_healthcheck_once()
    return _BACKEND_READY


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
    # EN: Do not hard-block registration by cached readiness probe result.
    # RU: Не блокировать регистрацию жёстко по кэшированному результату readiness-проверки.
    _ensure_healthcheck_once()
    ok, payload = api_client.request("POST", "/auth/register", json={"email": email, "psw": psw})
    if not ok:
        return False, _error_code(payload, "NETWORK")
    if isinstance(payload, dict) and payload.get("ok"):
        sync_user_snapshot_from_payload(payload)
        return True, int(payload["user_id"])
    return False, _error_code(payload, "API_ERROR")


def login(email: str, psw: str) -> Tuple[bool, str | int]:
    """EN: Login and return (ok, user_id|error_code).
    RU: Вход с ответом в формате (ok, user_id|код_ошибки).
    """
    # EN: Do not hard-block login by cached readiness probe result.
    # RU: Не блокировать вход жёстко по кэшированному результату readiness-проверки.
    _ensure_healthcheck_once()
    ok, payload = api_client.request("POST", "/auth/login", json={"email": email, "psw": psw})
    if not ok:
        return False, _error_code(payload, "NETWORK")
    if isinstance(payload, dict) and payload.get("ok"):
        sync_user_snapshot_from_payload(payload)
        return True, int(payload["user_id"])
    return False, _error_code(payload, "API_ERROR")


def resolve_user_id(email: str) -> Tuple[bool, str | int]:
    """EN: Resolve user id by email for legacy cache fallback.
    RU: Получить user_id по email для fallback со старым кешем.
    """
    _ensure_healthcheck_once()
    ok, payload = api_client.auth_exists(email)
    if not ok:
        return False, _error_code(payload, "NETWORK")
    if not isinstance(payload, dict) or not payload.get("ok"):
        return False, _error_code(payload, "API_ERROR")
    user = payload.get("user") if isinstance(payload, dict) else None
    if not isinstance(user, dict):
        return False, "API_ERROR"
    try:
        return True, int(user["user_id"])
    except Exception:
        return False, "API_ERROR"


def delete_account(user_id: int) -> bool:
    """EN: Delete account by user id.
    RU: Удалить аккаунт по user_id.
    """
    if not _backend_ready():
        return False
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
    if not _backend_ready():
        return False
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
    if not _backend_ready():
        return False
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
    balance: float | None = None,
) -> bool:
    """EN: Persist provided profile-game fields.
    RU: Сохранить переданные поля profile_game.
    """
    if not _backend_ready():
        return False
    body = {"user_id": int(user_id)}
    if record is not None:
        body["record"] = int(record)
    if rating is not None:
        body["rating"] = int(rating)
    if balance is not None:
        body["balance"] = float(balance)
    ok, payload = api_client.request("POST", "/profile/game/update", json=body)
    is_ok = bool(ok and isinstance(payload, dict) and payload.get("ok"))
    if is_ok:
        UserSnapshotStore().patch_game(record=record, rating=rating, balance=balance)
    return is_ok


def delete_profile_game_fields(user_id: int, fields: list[str]) -> bool:
    """EN: Reset selected profile-game fields to defaults.
    RU: Сбросить выбранные поля profile_game к значениям по умолчанию.
    """
    if not _backend_ready():
        return False
    ok, payload = api_client.request(
        "POST",
        "/profile/game/clear",
        json={"user_id": int(user_id), "fields": list(fields)},
    )
    return bool(ok and isinstance(payload, dict) and payload.get("ok"))


def get_top_ratings(limit: int = 100, timeout: int = 8) -> list[dict]:
    """EN: Return leaderboard rows sorted by rating/record.
    RU: Вернуть строки рейтинга, отсортированные по rating/record.
    """
    if not _backend_ready():
        return []

    try:
        ok, payload = api_client.request(
            "GET",
            "/rating/top",
            params={"limit": int(limit)},
            timeout=int(timeout),
        )
    except Exception:
        return []

    if not ok:
        return []

    items: list[dict] = []
    if isinstance(payload, list):
        items = payload
    elif isinstance(payload, dict):
        if not payload.get("ok"):
            return []
        raw_items = payload.get("items")
        if isinstance(raw_items, list):
            items = raw_items
    else:
        return []

    normalized: list[dict] = []
    for row in items:
        if not isinstance(row, dict):
            continue
        user_value = str((row.get("user") or row.get("email") or "").strip())
        if not user_value:
            user_value = "no data"
        try:
            record_value = int(row.get("record") or 0)
        except Exception:
            record_value = 0
        try:
            rating_value = int(row.get("rating") or 0)
        except Exception:
            rating_value = 0
        normalized.append(
            {
                "user": user_value,
                "record": record_value,
                "rating": rating_value,
            }
        )

    return normalized


def finish_session_metrics(payload: dict, timeout: int = 10) -> Tuple[bool, dict]:
    """EN: Submit raw session metrics to server and sync local snapshot from /auth/me.
    RU: Отправить сырые метрики сессии на сервер и синхронизировать локальный snapshot через /auth/me.
    """

    _ensure_healthcheck_once()
    ok, response = api_client.request(
        "POST",
        "/game/session/finish",
        json=payload,
        timeout=int(timeout),
    )
    if not ok or not isinstance(response, dict) or not response.get("ok"):
        return False, response if isinstance(response, dict) else {"error": "NETWORK"}

    user_id = int(payload.get("user_id") or 0)
    if user_id > 0:
        me_ok, me_payload = api_client.auth_me(user_id, timeout=timeout)
        if me_ok and isinstance(me_payload, dict) and me_payload.get("ok"):
            sync_user_snapshot_from_payload(me_payload)

    if bool(response.get("cheat")):
        UserSnapshotStore().patch_game(record=0, rating=0, balance=0.0)

    return True, response
