"""EN: Client bridge to backend HTTP API.
RU: Клиентский мост к backend HTTP API.
"""

from __future__ import annotations

from typing import Tuple

from data.user_cache.user_cache_reader import get_user_cache
from data.user_cache.user_cache_writer import update_user_cache_fields
from manager import api_client
from manager.session_manager import (
    clear_cached_session,
    force_logout as session_force_logout,
    has_valid_session,
    sync_user_snapshot_from_payload,
)
from manager.trace import trace_log
from manager.tg_debug_log import tglog
from manager.user_snapshot_store import UserSnapshotStore

_HEALTHCHECK_DONE = False
_BACKEND_READY = False


def _auth_log(event: str, **fields: object) -> None:
    """EN: Emit unified AUTH log line with stable key=value fields.
    RU: Вывести унифицированную строку AUTH-лога со стабильным форматом key=value.

    EN: This helper keeps diagnostics consistent across initial response and retry response
    events, so transport and payload states are not mixed in ad-hoc messages.
    RU: Этот helper поддерживает единый формат диагностики для первичного ответа и retry,
    чтобы не смешивать transport/payload состояния в разрозненных сообщениях.
    """

    parts = [f"{key}={value}" for key, value in fields.items()]
    suffix = f" {' '.join(parts)}" if parts else ""
    tglog(f"[AUTH] {event}{suffix}")


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


def _auth_headers() -> dict | None:
    """EN: Build Authorization header from cached access token when present.
    RU: Сформировать заголовок Authorization из кэшированного access token при наличии.
    """

    cache = get_user_cache() or {}
    token = str((cache.get("access_token") or "").strip())
    if not token:
        return None
    return {"Authorization": f"Bearer {token}"}


def mask_token(token: str) -> str:
    """EN: Return safe token representation with only edges and length for diagnostics.
    RU: Вернуть безопасное представление токена только с краями и длиной для диагностики.
    """

    value = str((token or "").strip())
    if not value:
        return "<empty>"
    if len(value) <= 8:
        return f"{value}(len={len(value)})"
    return f"{value[:4]}...{value[-4:]}(len={len(value)})"


def get_access_token() -> str:
    """EN: Return cached access token string or empty value.
    RU: Вернуть access-токен из кэша строкой или пустое значение.
    """

    cache = get_user_cache() or {}
    return str((cache.get("access_token") or "").strip())


def get_refresh_token() -> str:
    """EN: Return cached refresh token string or empty value.
    RU: Вернуть refresh-токен из кэша строкой или пустое значение.
    """

    cache = get_user_cache() or {}
    return str((cache.get("refresh_token") or "").strip())


def set_tokens(access_token: str | None, refresh_token: str | None) -> None:
    """EN: Persist access/refresh tokens in cache when provided.
    RU: Сохранить access/refresh токены в кэш, если они переданы.
    """

    patch: dict = {}
    if access_token is not None:
        patch["access_token"] = str((access_token or "").strip())
    if refresh_token is not None:
        patch["refresh_token"] = str((refresh_token or "").strip())
    if patch:
        update_user_cache_fields(patch)


def clear_tokens() -> None:
    """EN: Remove local auth tokens from cache on session-expired flows.
    RU: Удалить локальные auth-токены из кэша при истечении сессии.
    """

    set_tokens("", "")


def force_logout(reason: str = "UNKNOWN") -> None:
    """EN: Centralized client-side logout for expired/invalid session cases.
    RU: Единый клиентский logout для случаев истекшей/некорректной сессии.
    """

    trace_log("SESSION", "SESSION.FORCE_LOGOUT", reason=str(reason))
    session_force_logout(reason=reason)


def refresh_access_token() -> bool:
    """EN: Refresh access token using refresh token with mandatory server-side rotation.
    RU: Обновить access-токен через refresh-токен с обязательной серверной ротацией.
    """

    refresh_token = get_refresh_token()
    tglog(f"[TGDBG] refresh attempt: refresh={mask_token(refresh_token)}")
    tglog(f"[AUTH] refresh attempt refresh_present={bool(refresh_token)} refresh={mask_token(refresh_token)}")
    trace_log(
        "SESSION",
        "SESSION.REFRESH_ATTEMPT",
        refresh_present=bool(refresh_token),
        refresh_token=refresh_token,
    )
    if not refresh_token:
        tglog("[SESSION] blocked authorized request: no refresh_token path=/auth/refresh")
        tglog("[TGDBG] refresh result: ok=False")
        trace_log("SESSION", "SESSION.REFRESH_RESULT", ok=False, reason="NO_REFRESH_TOKEN")
        return False
    ok, payload = api_client.request(
        "POST",
        "/auth/refresh",
        json={"refresh_token": refresh_token},
        timeout=10,
    )
    is_ok = bool(ok and isinstance(payload, dict) and payload.get("ok"))
    if is_ok:
        access_token = str((payload.get("access_token") or "").strip())
        new_refresh_token = str((payload.get("refresh_token") or "").strip())
        if not access_token or not new_refresh_token:
            is_ok = False
        else:
            set_tokens(access_token, new_refresh_token)
    tglog(f"[TGDBG] refresh result: ok={is_ok}")
    tglog(f"[AUTH] refresh ok={bool(is_ok)}")
    trace_log(
        "SESSION",
        "SESSION.REFRESH_RESULT",
        ok=bool(is_ok),
        new_access_present=bool(str((payload.get("access_token") if isinstance(payload, dict) else "") or "").strip()),
        new_refresh_present=bool(str((payload.get("refresh_token") if isinstance(payload, dict) else "") or "").strip()),
    )
    return is_ok


def ensure_access_token(force_refresh: bool = False) -> str | None:
    """EN: Return access token from cache; optionally force refresh via refresh token.
    RU: Вернуть access-токен из кэша; при необходимости принудительно обновить через refresh-токен.
    """

    if not has_valid_session():
        tglog("[SESSION] blocked authorized request: no refresh_token path=ensure_access_token")
        trace_log("SESSION", "SESSION.NO_VALID_SESSION", path="ensure_access_token")
        return None

    cached_token = get_access_token()
    tglog(
        f"[TGDBG] token ensure: have={bool(cached_token)} force={bool(force_refresh)} "
        f"token={mask_token(cached_token)}"
    )
    if cached_token and not force_refresh:
        return cached_token
    if refresh_access_token():
        return get_access_token()
    return None


def _authorized_request_with_retry(
    method: str,
    path: str,
    *,
    json: dict | None = None,
    timeout: int = 10,
    params: dict | None = None,
) -> tuple[bool, object, int]:
    """EN: Execute authorized request and perform exactly one retry after refresh on UNAUTHORIZED.
    RU: Выполнить авторизованный запрос и сделать ровно один retry после refresh при UNAUTHORIZED.
    """

    _auth_log(
        "request",
        path=path,
        method=method.upper(),
        auth_present=bool(get_access_token()),
        refresh_present=bool(get_refresh_token()),
    )
    if not has_valid_session():
        tglog(f"[SESSION] blocked authorized request: no refresh_token path={path}")
        trace_log("SESSION", "SESSION.BLOCKED_REQUEST", path=path, reason="NO_REFRESH_TOKEN")
        return False, {"ok": False, "error": "NO_SESSION"}, 0

    token = ensure_access_token(force_refresh=False)
    if not token:
        tglog(f"[SESSION] blocked authorized request: no refresh_token path={path}")
        trace_log("SESSION", "SESSION.BLOCKED_REQUEST", path=path, reason="NO_ACCESS_TOKEN")
        return False, {"ok": False, "error": "NO_SESSION"}, 0
    headers = {"Authorization": f"Bearer {token}"}
    ok, payload, status_code = api_client.request_with_meta(
        method,
        path,
        json=json,
        params=params,
        headers=headers,
        timeout=timeout,
    )
    unauthorized = bool(
        status_code in (401, 403)
        or (isinstance(payload, dict) and str(payload.get("error") or "") == "UNAUTHORIZED")
    )
    transport_ok = bool(ok)
    payload_ok = bool(isinstance(payload, dict) and payload.get("ok") is True)
    _auth_log(
        "resp",
        path=path,
        status=status_code,
        transport_ok=transport_ok,
        payload_ok=payload_ok,
        unauthorized=unauthorized,
        did_retry=False,
    )
    if not unauthorized:
        return payload_ok, payload, status_code

    tglog(f"[TGDBG] authorized retry: path={path} reason=UNAUTHORIZED")
    _auth_log("unauthorized_refresh", path=path)
    if not refresh_access_token():
        tglog(f"[TGDBG] authorized retry: path={path} refresh_ok=False")
        _auth_log("refresh", path=path, ok=False)
        force_logout(reason=f"UNAUTHORIZED_REFRESH_FAILED:{path}")
        trace_log("SESSION", "SESSION.UNAUTHORIZED_RETRY_FAILED", path=path)
        return False, {"ok": False, "error": "NO_SESSION"}, status_code
    token2 = get_access_token()
    if not token2:
        tglog(f"[TGDBG] authorized retry: path={path} token_after_refresh=<empty>")
        force_logout(reason=f"UNAUTHORIZED_EMPTY_ACCESS:{path}")
        trace_log("SESSION", "SESSION.UNAUTHORIZED_EMPTY_ACCESS", path=path)
        return False, {"ok": False, "error": "NO_SESSION"}, status_code
    tglog(f"[TGDBG] authorized retry: path={path} refresh_ok=True auth={mask_token(token2)}")
    _auth_log("refresh", path=path, ok=True)
    headers2 = {"Authorization": f"Bearer {token2}"}
    ok2, payload2, status2 = api_client.request_with_meta(
        method,
        path,
        json=json,
        params=params,
        headers=headers2,
        timeout=timeout,
    )
    transport_ok2 = bool(ok2)
    payload_ok2 = bool(isinstance(payload2, dict) and payload2.get("ok") is True)
    unauthorized2 = bool(
        status2 in (401, 403)
        or (isinstance(payload2, dict) and str(payload2.get("error") or "") == "UNAUTHORIZED")
    )
    _auth_log(
        "retry",
        path=path,
        status=status2,
        transport_ok=transport_ok2,
        payload_ok=payload_ok2,
        unauthorized=unauthorized2,
        did_retry=True,
    )
    return payload_ok2, payload2, status2


def has_access_token() -> bool:
    """EN: Return True when local cache contains non-empty access token.
    RU: Вернуть True, если в локальном кэше есть непустой access token.
    """

    return bool(get_access_token())


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
        access_token = str((payload.get("access_token") or "").strip())
        refresh_token = str((payload.get("refresh_token") or "").strip())
        if not refresh_token:
            force_logout(reason="REGISTER_MISSING_REFRESH_TOKEN")
            return False, "API_ERROR"
        set_tokens(access_token, refresh_token)
        tglog(f"[TGDBG] login tokens: access={mask_token(access_token)} refresh={mask_token(refresh_token)}")
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
        access_token = str((payload.get("access_token") or "").strip())
        refresh_token = str((payload.get("refresh_token") or "").strip())
        if not refresh_token:
            force_logout(reason="LOGIN_MISSING_REFRESH_TOKEN")
            return False, "API_ERROR"
        set_tokens(access_token, refresh_token)
        tglog(f"[TGDBG] login tokens: access={mask_token(access_token)} refresh={mask_token(refresh_token)}")
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
    ok, payload, _status = _authorized_request_with_retry(
        "POST",
        "/profile/user/update",
        json=body,
        timeout=10,
    )
    return bool(ok and isinstance(payload, dict) and payload.get("ok"))


def delete_profile_user_fields(user_id: int, fields: list[str]) -> bool:
    """EN: Reset selected profile-user fields to defaults.
    RU: Сбросить выбранные поля profile_user к значениям по умолчанию.
    """
    if not _backend_ready():
        return False
    ok, payload, _status = _authorized_request_with_retry(
        "POST",
        "/profile/user/clear",
        json={"user_id": int(user_id), "fields": list(fields)},
        timeout=10,
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
    ok, payload, _status = _authorized_request_with_retry(
        "POST",
        "/profile/game/update",
        json=body,
        timeout=10,
    )
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
    ok, payload, _status = _authorized_request_with_retry(
        "POST",
        "/profile/game/clear",
        json={"user_id": int(user_id), "fields": list(fields)},
        timeout=10,
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


def password_reset_request(email: str, channel: str = "telegram") -> Tuple[bool, str]:
    """EN: Request password reset code by email without exposing account existence.
    RU: Запросить код восстановления пароля по email без раскрытия существования аккаунта.
    """

    _ensure_healthcheck_once()
    ok, payload = api_client.request(
        "POST",
        "/auth/password/reset/request",
        json={"email": email, "channel": str(channel or "telegram").strip().lower()},
        timeout=10,
    )
    if ok and isinstance(payload, dict) and payload.get("ok"):
        return True, ""
    return False, _error_code(payload, "API_ERROR")


def password_reset_confirm(email: str, code: str, new_psw: str) -> Tuple[bool, str]:
    """EN: Confirm reset code and set new password, clearing local cache on success.
    RU: Подтвердить reset-код и задать новый пароль, очищая локальный кэш при успехе.
    """

    _ensure_healthcheck_once()
    ok, payload = api_client.request(
        "POST",
        "/auth/password/reset/confirm",
        json={"email": email, "code": code, "new_psw": new_psw},
        timeout=10,
    )
    if ok and isinstance(payload, dict) and payload.get("ok"):
        clear_cached_session()
        return True, ""
    return False, _error_code(payload, "INVALID_CODE")


def telegram_link_request(user_id: int) -> Tuple[bool, dict]:
    """EN: Request one-time Telegram deep-link code for authenticated user.
    RU: Запросить одноразовый Telegram deep-link code для авторизованного пользователя.
    """

    _ensure_healthcheck_once()

    token = ensure_access_token(force_refresh=False)
    if not token:
        tglog("[TGDBG] step8 response status=0 ok=False body={'ok':False,'error':'NO_SESSION'}")
        return False, {"ok": False, "error": "NO_SESSION"}

    tglog(f"[TGDBG] link_request send: user_id={int(user_id)} auth={mask_token(token)}")
    ok, payload, status_code = _authorized_request_with_retry(
        "POST",
        "/telegram/link/request",
        json={"user_id": int(user_id)},
        timeout=10,
    )
    body_short = str(payload)[:200]
    tglog(f"[TGDBG] step8 response status={status_code} ok={ok} body={body_short}")

    code = str((payload.get("code") or "").strip()) if isinstance(payload, dict) else ""
    payload_ok = bool(isinstance(payload, dict) and payload.get("ok"))
    if ok and payload_ok and code:
        tglog(f"[TGDBG] step9 code={mask_token(code)}")
        return True, payload

    if isinstance(payload, dict):
        if payload_ok and not code:
            return False, {"ok": False, "error": "API_ERROR"}
        return False, payload
    return False, {"ok": False, "error": "API_ERROR"}


def telegram_verify_request(user_id: int) -> Tuple[bool, dict]:
    """EN: Request Telegram verification challenge for given user and return request_id/ttl.
    RU: Запросить challenge верификации Telegram для указанного пользователя и вернуть request_id/ttl.
    """

    _ensure_healthcheck_once()
    body: dict = {"user_id": int(user_id)}
    ok, payload, _status = _authorized_request_with_retry(
        "POST",
        "/telegram/verify/request",
        json=body,
        timeout=10,
    )
    if ok and isinstance(payload, dict) and payload.get("ok"):
        return True, payload
    if isinstance(payload, dict):
        return False, payload
    return False, {"ok": False, "error": "API_ERROR"}


def telegram_verify_confirm(user_id: int, request_id: str, code: str) -> Tuple[bool, str]:
    """EN: Confirm Telegram verification challenge code for given user.
    RU: Подтвердить код challenge верификации Telegram для указанного пользователя.
    """

    _ensure_healthcheck_once()
    ok, payload, _status = _authorized_request_with_retry(
        "POST",
        "/telegram/verify/confirm",
        json={"user_id": int(user_id), "request_id": request_id, "code": code},
        timeout=10,
    )
    if ok and isinstance(payload, dict) and payload.get("ok"):
        return True, ""
    return False, _error_code(payload, "INVALID_CODE")
