"""EN: Minimal HS256 JWT signing/verification helpers for authenticated API calls.
RU: Минимальные хелперы подписи/проверки HS256 JWT для авторизованных API-вызовов.
"""

from __future__ import annotations

import os
import secrets
from uuid import uuid4
from datetime import datetime, timedelta, timezone

import jwt
from server.config import get_jwt_secret


def _jwt_secret() -> str:
    """EN: Read JWT secret from env and return trimmed value.
    RU: Прочитать JWT-секрет из окружения и вернуть очищенное значение.
    """

    try:
        return get_jwt_secret()
    except Exception:
        return ""


def _access_ttl_minutes() -> int:
    """EN: Resolve access token TTL in minutes from env with safe fallback.
    RU: Получить TTL access-токена в минутах из env с безопасным fallback.
    """

    try:
        return max(1, int(os.getenv("ACCESS_TOKEN_TTL_MIN", "15")))
    except Exception:
        return 15


def _refresh_ttl_days() -> int:
    """EN: Resolve refresh token TTL in days from env with safe fallback.
    RU: Получить TTL refresh-токена в днях из env с безопасным fallback.
    """

    try:
        return max(1, int(os.getenv("REFRESH_TOKEN_TTL_DAYS", "30")))
    except Exception:
        return 30


def _to_unix(dt: datetime) -> int:
    """EN: Convert timezone-aware datetime to integer unix timestamp.
    RU: Преобразовать datetime с timezone в целочисленный unix timestamp.
    """

    return int(dt.timestamp())


def create_access_token(user_id: int, email: str, ttl_minutes: int | None = None) -> str:
    """EN: Create signed short-lived access JWT with explicit type claim.
    RU: Создать подписанный короткоживущий access JWT с явным claim type.
    """

    secret = _jwt_secret()
    if not secret:
        return ""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(int(user_id)),
        "email": str((email or "").strip().lower()),
        "type": "access",
        "iat": _to_unix(now),
        "exp": _to_unix(now + timedelta(minutes=max(1, int(ttl_minutes or _access_ttl_minutes())))),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def create_refresh_token(user_id: int, ttl_days: int | None = None) -> tuple[str, str, datetime]:
    """EN: Create signed refresh JWT with unique JTI and return token+jti+expiry.
    RU: Создать подписанный refresh JWT с уникальным JTI и вернуть token+jti+expiry.
    """

    secret = _jwt_secret()
    if not secret:
        return "", "", datetime.now(timezone.utc)

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=max(1, int(ttl_days or _refresh_ttl_days())))
    jti = uuid4().hex + secrets.token_hex(8)
    payload = {
        "sub": str(int(user_id)),
        "type": "refresh",
        "jti": jti,
        "iat": _to_unix(now),
        "exp": _to_unix(expires_at),
    }
    token = jwt.encode(payload, secret, algorithm="HS256")
    return token, jti, expires_at


def _decode_token(token: str) -> dict | None:
    """EN: Decode and verify JWT token signature/expiry and return payload dict.
    RU: Декодировать и проверить JWT-токен (подпись/срок) и вернуть payload dict.
    """

    secret = _jwt_secret()
    if not secret:
        return None
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        return payload if isinstance(payload, dict) else None
    except Exception:
        return None


def decode_access_token(token: str) -> dict | None:
    """EN: Decode access JWT and validate `type=access`.
    RU: Декодировать access JWT и проверить `type=access`.
    """

    payload = _decode_token(token)
    if not isinstance(payload, dict):
        return None
    if str(payload.get("type") or "") != "access":
        return None
    return payload


def decode_refresh_token(token: str) -> dict | None:
    """EN: Decode refresh JWT and validate `type=refresh` plus `jti` presence.
    RU: Декодировать refresh JWT и проверить `type=refresh` и наличие `jti`.
    """

    payload = _decode_token(token)
    if not isinstance(payload, dict):
        return None
    if str(payload.get("type") or "") != "refresh":
        return None
    if not str(payload.get("jti") or "").strip():
        return None
    return payload


def extract_bearer_token(auth_header: str | None) -> str:
    """EN: Extract bearer token value from Authorization header.
    RU: Извлечь значение bearer-токена из заголовка Authorization.
    """

    raw = (auth_header or "").strip()
    if not raw.lower().startswith("bearer "):
        return ""
    return raw[7:].strip()
