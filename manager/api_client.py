"""EN: Minimal HTTP client wrapper for Cosmic backend API.
RU: Минимальная HTTP-обертка для API бэкенда Cosmic.
"""

from __future__ import annotations

import time
import uuid
from typing import Any, Tuple

import requests

from manager.config import API_BASE_URL
from manager.trace import TraceManager, trace_exception, trace_log
from manager.tg_debug_log import tglog


def _payload_keys(value: Any) -> list[str]:
    """EN: Return sorted payload keys for dict responses.
    RU: Вернуть отсортированные ключи payload для dict-ответов.
    """

    if isinstance(value, dict):
        return sorted(str(k) for k in value.keys())
    return []


def _safe_response_meta(payload: Any) -> dict[str, Any]:
    """EN: Build safe response metadata with masked sensitive values.
    RU: Собрать безопасные метаданные ответа с маскированием чувствительных значений.
    """

    tm = TraceManager.instance()
    out: dict[str, Any] = {
        "response_type": type(payload).__name__,
        "response_keys": _payload_keys(payload),
    }
    if isinstance(payload, dict):
        out["ok_field"] = bool(payload.get("ok"))
        out["error_field"] = payload.get("error")
        if "code" in payload:
            out["code"] = tm.mask_code(str(payload.get("code") or ""))
        if "start_token" in payload:
            out["start_token"] = tm.mask_code(str(payload.get("start_token") or ""))
        if "access_token" in payload:
            out["access_token"] = tm.mask_token(str(payload.get("access_token") or ""))
        if "refresh_token" in payload:
            out["refresh_token"] = tm.mask_token(str(payload.get("refresh_token") or ""))
    return out


def _auth_meta(headers: dict | None) -> tuple[bool, str, int]:
    """EN: Return (auth_present, auth_masked, auth_len) for request headers.
    RU: Вернуть (auth_present, auth_masked, auth_len) для заголовков запроса.
    """

    auth_header = ""
    if isinstance(headers, dict):
        auth_header = str((headers.get("Authorization") or "").strip())
    token = auth_header[7:].strip() if auth_header.startswith("Bearer ") else ""
    return bool(auth_header), TraceManager.instance().mask_token(token), len(token)


def request(
    method: str,
    path: str,
    json: dict | None = None,
    timeout: int = 10,
    params: dict | None = None,
    headers: dict | None = None,
) -> Tuple[bool, Any]:
    """EN: Send HTTP request and return (ok, payload_or_error).
    RU: Отправить HTTP-запрос и вернуть (ok, payload_или_ошибка).
    """
    url = f"{API_BASE_URL}/{path.lstrip('/')}"
    req_id = uuid.uuid4().hex[:8]
    auth_present, auth_masked, auth_len = _auth_meta(headers)
    json_keys = sorted(str(k) for k in (json or {}).keys()) if isinstance(json, dict) else []
    trace_log(
        "HTTP",
        "HTTP.REQUEST",
        request_id=req_id,
        method=method.upper(),
        path="/" + path.lstrip("/"),
        timeout=timeout,
        auth_present=auth_present,
        auth_masked=auth_masked,
        auth_len=auth_len,
        json_keys=json_keys,
    )
    if str(path or "").startswith("/telegram/"):
        tglog(
            f"[TGDBG] api_client: auth_header_present={auth_present} "
            f"auth_len={auth_len}"
        )
    started = time.perf_counter()
    try:
        response = requests.request(
            method=method.upper(),
            url=url,
            json=json,
            params=params,
            headers=headers,
            timeout=timeout,
        )
    except requests.RequestException as exc:
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        trace_exception(
            "HTTP",
            "HTTP.EXCEPTION",
            exc,
            request_id=req_id,
            method=method.upper(),
            path="/" + path.lstrip("/"),
            elapsed_ms=elapsed_ms,
        )
        return False, {"error": "NETWORK"}

    try:
        payload: Any = response.json()
    except ValueError:
        payload = {"error": "BAD_RESPONSE"}

    elapsed_ms = int((time.perf_counter() - started) * 1000)
    trace_log(
        "HTTP",
        "HTTP.RESPONSE",
        request_id=req_id,
        method=method.upper(),
        path="/" + path.lstrip("/"),
        status_code=int(response.status_code),
        elapsed_ms=elapsed_ms,
        ok=bool(response.ok),
        **_safe_response_meta(payload),
    )

    if response.ok:
        return True, payload

    if isinstance(payload, dict):
        return False, payload
    return False, {"error": "HTTP_ERROR"}


def request_with_meta(
    method: str,
    path: str,
    json: dict | None = None,
    timeout: int = 10,
    params: dict | None = None,
    headers: dict | None = None,
) -> tuple[bool, Any, int]:
    """EN: Send HTTP request and return (ok, payload_or_error, status_code).
    RU: Отправить HTTP-запрос и вернуть (ok, payload_или_ошибка, status_code).
    """

    url = f"{API_BASE_URL}/{path.lstrip('/')}"
    req_id = uuid.uuid4().hex[:8]
    auth_present, auth_masked, auth_len = _auth_meta(headers)
    json_keys = sorted(str(k) for k in (json or {}).keys()) if isinstance(json, dict) else []
    trace_log(
        "HTTP",
        "HTTP.REQUEST",
        request_id=req_id,
        method=method.upper(),
        path="/" + path.lstrip("/"),
        timeout=timeout,
        auth_present=auth_present,
        auth_masked=auth_masked,
        auth_len=auth_len,
        json_keys=json_keys,
    )
    if str(path or "").startswith("/telegram/"):
        tglog(
            f"[TGDBG] api_client: auth_header_present={auth_present} "
            f"auth_len={auth_len}"
        )
    started = time.perf_counter()
    try:
        response = requests.request(
            method=method.upper(),
            url=url,
            json=json,
            params=params,
            headers=headers,
            timeout=timeout,
        )
    except requests.RequestException as exc:
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        trace_exception(
            "HTTP",
            "HTTP.EXCEPTION",
            exc,
            request_id=req_id,
            method=method.upper(),
            path="/" + path.lstrip("/"),
            elapsed_ms=elapsed_ms,
        )
        return False, {"error": "NETWORK"}, 0

    try:
        payload: Any = response.json()
    except ValueError:
        payload = {"error": "BAD_RESPONSE"}

    elapsed_ms = int((time.perf_counter() - started) * 1000)
    trace_log(
        "HTTP",
        "HTTP.RESPONSE",
        request_id=req_id,
        method=method.upper(),
        path="/" + path.lstrip("/"),
        status_code=int(response.status_code),
        elapsed_ms=elapsed_ms,
        ok=bool(response.ok),
        **_safe_response_meta(payload),
    )

    if response.ok:
        return True, payload, int(response.status_code)
    if isinstance(payload, dict):
        return False, payload, int(response.status_code)
    return False, {"error": "HTTP_ERROR"}, int(response.status_code)


def healthz(timeout: int = 3) -> Tuple[bool, dict]:
    """EN: Ping backend health endpoint.
    RU: Проверить доступность backend по health-эндпоинту.
    """
    ok, payload = request("GET", "/healthz", timeout=timeout)
    if ok and isinstance(payload, dict):
        return bool(payload.get("ok")), payload
    if isinstance(payload, dict):
        return False, payload
    return False, {"error": "NETWORK"}


def compatibility(timeout: int = 3) -> Tuple[bool, dict]:
    """EN: Query backend compatibility endpoint with DB schema status details.
    RU: Запросить endpoint совместимости backend со статусом схемы БД.
    """

    ok, payload = request("GET", "/meta/compat", timeout=timeout)
    if ok and isinstance(payload, dict):
        return True, payload
    if isinstance(payload, dict):
        return False, payload
    return False, {"error": "NETWORK"}


def auth_me(user_id: int, timeout: int = 8) -> Tuple[bool, dict]:
    """EN: Request current user snapshot by user_id for startup cache sync.
    RU: Запросить snapshot текущего пользователя по user_id для синхронизации кэша при старте.
    """

    ok, payload = request("GET", "/auth/me", timeout=timeout, params={"user_id": int(user_id)})
    if ok and isinstance(payload, dict):
        return True, payload
    if isinstance(payload, dict):
        return False, payload
    return False, {"error": "NETWORK"}


def get_me(user_id: int, timeout: int = 8) -> Tuple[bool, dict]:
    """EN: Compatibility alias for auth_me user snapshot request.
    RU: Совместимый алиас для запроса snapshot пользователя через auth_me.
    """

    return auth_me(user_id=user_id, timeout=timeout)


def auth_exists(email: str, timeout: int = 8) -> Tuple[bool, dict]:
    """EN: Resolve user snapshot by email fallback when user_id is absent in cache.
    RU: Найти snapshot пользователя по fallback-email, если в кэше отсутствует user_id.
    """

    ok, payload = request("GET", "/auth/exists", timeout=timeout, params={"email": email})
    if ok and isinstance(payload, dict):
        return True, payload
    if isinstance(payload, dict):
        return False, payload
    return False, {"error": "NETWORK"}
