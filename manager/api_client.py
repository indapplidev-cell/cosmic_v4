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
