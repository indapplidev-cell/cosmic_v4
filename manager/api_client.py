"""EN: Minimal HTTP client wrapper for Cosmic backend API.
RU: Минимальная HTTP-обертка для API бэкенда Cosmic.
"""

from __future__ import annotations

from typing import Any, Tuple

import requests

from manager.config import API_BASE_URL


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
    try:
        response = requests.request(
            method=method.upper(),
            url=url,
            json=json,
            params=params,
            headers=headers,
            timeout=timeout,
        )
    except requests.RequestException:
        return False, {"error": "NETWORK"}

    try:
        payload: Any = response.json()
    except ValueError:
        payload = {"error": "BAD_RESPONSE"}

    if response.ok:
        return True, payload

    if isinstance(payload, dict):
        return False, payload
    return False, {"error": "HTTP_ERROR"}


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
