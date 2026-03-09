"""EN: Minimal HS256 JWT signing/verification helpers for authenticated API calls.
RU: Минимальные хелперы подписи/проверки HS256 JWT для авторизованных API-вызовов.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import jwt


def _jwt_secret() -> str:
    """EN: Read JWT secret from env and return trimmed value.
    RU: Прочитать JWT-секрет из окружения и вернуть очищенное значение.
    """

    return os.getenv("JWT_SECRET", "").strip()


def create_access_token(user_id: int, email: str, ttl_days: int = 7) -> str:
    """EN: Create signed JWT access token with user identity payload.
    RU: Создать подписанный JWT access token с payload идентичности пользователя.
    """

    secret = _jwt_secret()
    if not secret:
        return ""

    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(int(user_id)),
        "email": str((email or "").strip().lower()),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=max(1, int(ttl_days)))).timestamp()),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def decode_access_token(token: str) -> dict | None:
    """EN: Decode and verify JWT token, returning payload dict or None.
    RU: Декодировать и проверить JWT-токен, вернув payload dict или None.
    """

    secret = _jwt_secret()
    if not secret:
        return None
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        return payload if isinstance(payload, dict) else None
    except Exception:
        return None


def extract_bearer_token(auth_header: str | None) -> str:
    """EN: Extract bearer token value from Authorization header.
    RU: Извлечь значение bearer-токена из заголовка Authorization.
    """

    raw = (auth_header or "").strip()
    if not raw.lower().startswith("bearer "):
        return ""
    return raw[7:].strip()

