# -*- coding: utf-8 -*-
"""EN: Shared API auth helpers for bearer-protected endpoints.
RU: Общие auth-хелперы API для endpoint-ов, защищённых bearer-токеном.
"""

from __future__ import annotations

from fastapi import HTTPException, Request, status

from server.app.security.jwt import decode_access_token, extract_bearer_token


def get_authenticated_user_id(request: Request) -> int:
    """EN: Extract current authenticated user id from Authorization Bearer token.
    RU: Извлечь идентификатор текущего авторизованного пользователя из Authorization Bearer токена.
    """

    token = extract_bearer_token(request.headers.get("authorization"))
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"ok": False, "error": "UNAUTHORIZED"})

    payload = decode_access_token(token)
    if not isinstance(payload, dict):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"ok": False, "error": "UNAUTHORIZED"})

    raw_sub = payload.get("sub")
    try:
        user_id = int(raw_sub)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"ok": False, "error": "UNAUTHORIZED"}) from exc

    if user_id <= 0:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"ok": False, "error": "UNAUTHORIZED"})
    return user_id


def require_same_user(request: Request, requested_user_id: int) -> int:
    """EN: Ensure the authenticated user matches the requested user id.
    RU: Убедиться, что авторизованный пользователь совпадает с запрошенным user id.
    """

    auth_user_id = get_authenticated_user_id(request)
    if int(auth_user_id) != int(requested_user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={"ok": False, "error": "FORBIDDEN"})
    return auth_user_id
