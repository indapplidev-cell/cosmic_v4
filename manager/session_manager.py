"""EN: Session validation/synchronization manager for startup real-time cache checks.
RU: Менеджер валидации/синхронизации сессии для realtime-проверки кэша при старте.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from data.user_cache.user_cache_reader import get_user_cache
from data.user_cache.user_cache_writer import remove_user_cache_fields, update_user_cache_fields
from data.user_cache.user_session import UserSession
from manager import api_client
from manager.trace import trace_log
from manager.tg_debug_log import tglog


def _safe_int(value: Any) -> int | None:
    """EN: Convert value to int when possible, otherwise return None.
    RU: Преобразовать значение в int при возможности, иначе вернуть None.
    """

    try:
        return int(value)
    except Exception:
        return None


def _cache_path() -> Path:
    """EN: Resolve local user cache JSON path.
    RU: Определить путь к локальному JSON-файлу кэша пользователя.
    """

    return Path(__file__).resolve().parents[1] / "data" / "user_cache" / "user_cache.json"


def clear_cached_session() -> None:
    """EN: Clear local user cache and session marker files.
    RU: Очистить локальные файлы кэша пользователя и маркера сессии.
    """

    cache_file = _cache_path()
    try:
        if cache_file.exists():
            cache_file.unlink()
    except Exception:
        pass
    UserSession().clear()


def has_valid_session(cache: dict | None = None) -> bool:
    """EN: Return True only when cache has positive user_id and non-empty refresh_token.
    RU: Вернуть True только если в кэше есть положительный user_id и непустой refresh_token.
    """

    src = cache if isinstance(cache, dict) else (get_user_cache() or {})
    user_id = _safe_int(src.get("user_id")) or 0
    refresh_token = str((src.get("refresh_token") or "").strip())
    return bool(user_id > 0 and refresh_token)


def get_session_user_id(cache: dict | None = None) -> int:
    """EN: Return current positive session user id or zero when session identity is unavailable.
    RU: Вернуть текущий положительный session user id или ноль, если идентификатор сессии недоступен.
    """

    src = cache if isinstance(cache, dict) else (get_user_cache() or {})
    user_id = _safe_int(src.get("user_id")) or 0
    return int(user_id) if int(user_id) > 0 else 0


def force_logout(reason: str = "UNKNOWN") -> None:
    """EN: Clear auth/session identifiers while preserving non-auth profile fields in cache.
    RU: Очистить auth/session идентификаторы, сохранив неавторизационные поля профиля в кэше.
    """

    tglog(f"[SESSION] force_logout reason={reason}")
    trace_log("SESSION", "SESSION.FORCE_LOGOUT", reason=str(reason))
    update_user_cache_fields(
        {
            "user_id": 0,
            "access_token": "",
            "refresh_token": "",
        }
    )
    remove_user_cache_fields(
        [
            "token",
            "authorization",
            "is_authorized",
            "authorized",
            "session_user_id",
        ]
    )
    UserSession().clear()


def sync_user_snapshot(user: dict) -> None:
    """EN: Persist server user snapshot into local cache/session fields.
    RU: Сохранить серверный snapshot пользователя в локальные поля кэша/сессии.
    """

    telegram_value = str((user.get("telegram") or "").strip())
    telegram_username_value = str((user.get("telegram_username") or "").strip())
    if not telegram_value and telegram_username_value:
        telegram_value = telegram_username_value
    patch = {
        "user_id": int(user.get("user_id") or 0),
        "email": str((user.get("email") or "").strip()),
        "login": str((user.get("login") or "").strip()),
        "phone": str((user.get("phone") or "").strip()),
        "tg": telegram_value,
        "telegram": telegram_value,
        "telegram_username": telegram_username_value,
        "telegram_user_id": int(user.get("telegram_user_id") or 0),
        "telegram_linked": bool(user.get("telegram_linked")),
        "telegram_verified": bool(user.get("telegram_verified")),
        "record": int(user.get("record") or 0),
        "rating": int(user.get("rating") or 0),
        "balance": round(float(user.get("balance") or 0.0), 3),
    }
    if patch["user_id"] > 0:
        update_user_cache_fields(patch)
    if patch["email"]:
        UserSession().set_email(patch["email"])


def sync_user_snapshot_from_payload(payload: dict) -> bool:
    """EN: Extract and persist user snapshot from API payload when present.
    RU: Извлечь и сохранить snapshot пользователя из API payload при наличии.
    """

    user = payload.get("user") if isinstance(payload, dict) else None
    if not isinstance(user, dict):
        return False
    try:
        sync_user_snapshot(user)
        access_token = (
            str((payload.get("access_token") or payload.get("token") or "").strip())
            if isinstance(payload, dict)
            else ""
        )
        refresh_token = (
            str((payload.get("refresh_token") or "").strip())
            if isinstance(payload, dict)
            else ""
        )
        if access_token:
            update_user_cache_fields({"access_token": access_token})
        if refresh_token:
            update_user_cache_fields({"refresh_token": refresh_token})
        # EN: Ensure password never persists in local cache.
        # RU: Гарантировать, что пароль не сохраняется в локальном кэше.
        remove_user_cache_fields(["password", "psw"])
        return True
    except Exception:
        return False


def validate_cached_session(timeout: int = 8, allow_offline: bool = True) -> dict:
    """EN: Validate cached account against server and sync cache in real time on startup.
    RU: Проверить кэшированный аккаунт с сервером и синхронизировать кэш в реальном времени при старте.
    """

    cache = get_user_cache() or {}
    if not cache:
        return {"ok": False, "reason": "NO_CACHE"}

    user_id_boot = _safe_int(cache.get("user_id")) or 0
    refresh_present = bool(str((cache.get("refresh_token") or "").strip()))
    tglog(f"[SESSION] boot user_id={user_id_boot} refresh_present={refresh_present}")
    trace_log(
        "SESSION",
        "SESSION.BOOT",
        user_id=int(user_id_boot),
        refresh_present=bool(refresh_present),
        access_present=bool(str((cache.get("access_token") or "").strip())),
    )
    if user_id_boot > 0 and not refresh_present:
        tglog("[SESSION] no refresh_token -> force_logout")
        trace_log("SESSION", "SESSION.BOOT_FAIL", reason="NO_REFRESH_TOKEN")
        force_logout("NO_REFRESH_TOKEN_BOOT")
        return {"ok": False, "reason": "NO_SESSION"}

    user_id = _safe_int(cache.get("user_id"))
    email = str((cache.get("email") or "").strip())

    if user_id is not None and int(user_id) <= 0:
        tglog("[SESSION] skip /auth/me (no user_id)")
        trace_log("SESSION", "SESSION.SKIP_AUTH_ME", user_id=int(user_id))
        return {"ok": False, "reason": "NO_CACHE"}

    if user_id is None and not email:
        return {"ok": False, "reason": "NO_CACHE"}

    if user_id is None and email:
        ok_exists, exists_payload = api_client.auth_exists(email, timeout=timeout)
        if not ok_exists:
            if allow_offline and isinstance(exists_payload, dict) and exists_payload.get("error") == "NETWORK":
                return {"ok": False, "reason": "NETWORK", "has_cache": True}
            return {"ok": False, "reason": "SERVER_NOT_FOUND"}
        if not exists_payload.get("ok"):
            if exists_payload.get("error") == "NOT_FOUND":
                clear_cached_session()
                return {"ok": False, "reason": "SERVER_NOT_FOUND"}
            return {"ok": False, "reason": "NETWORK"}

        user = exists_payload.get("user") if isinstance(exists_payload, dict) else None
        if not isinstance(user, dict):
            return {"ok": False, "reason": "SERVER_NOT_FOUND"}
        user_id = _safe_int(user.get("user_id"))
        if user_id is None:
            return {"ok": False, "reason": "SERVER_NOT_FOUND"}

    ok_me, me_payload = api_client.auth_me(int(user_id), timeout=timeout)
    if not ok_me:
        if allow_offline and isinstance(me_payload, dict) and me_payload.get("error") == "NETWORK":
            return {"ok": False, "reason": "NETWORK", "has_cache": True}
        return {"ok": False, "reason": "SERVER_NOT_FOUND"}

    if not me_payload.get("ok"):
        if me_payload.get("error") == "NOT_FOUND":
            clear_cached_session()
            return {"ok": False, "reason": "SERVER_NOT_FOUND"}
        return {"ok": False, "reason": "NETWORK"}

    user = me_payload.get("user") if isinstance(me_payload, dict) else None
    if not isinstance(user, dict):
        clear_cached_session()
        return {"ok": False, "reason": "SERVER_NOT_FOUND"}

    sync_user_snapshot(user)
    return {"ok": True, "user": user}
