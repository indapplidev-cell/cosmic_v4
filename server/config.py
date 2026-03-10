"""EN: Environment-only database configuration for the server module.
RU: Конфигурация серверной БД только через переменные окружения.
"""

from __future__ import annotations

import os


DATABASE_URL: str = os.getenv("DATABASE_URL", "").strip()

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is required for server module. "
        "Set it via environment or Docker Compose env file."
    )

if not DATABASE_URL.startswith("postgresql"):
    raise RuntimeError(
        "Only PostgreSQL DATABASE_URL is supported in server/config.py. "
        f"Got DATABASE_URL={DATABASE_URL!r}"
    )


def require_env(name: str) -> str:
    """EN: Return required env value or raise RuntimeError when empty.
    RU: Вернуть обязательное env-значение или поднять RuntimeError, если оно пустое.
    """

    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} is required and must be non-empty")
    return value


def get_jwt_secret() -> str:
    """EN: Return non-empty JWT secret for auth token signing/verification.
    RU: Вернуть непустой JWT-секрет для подписи/проверки auth-токенов.
    """

    return require_env("JWT_SECRET")


def get_reset_secret() -> str:
    """EN: Return non-empty reset secret for one-time code hashing.
    RU: Вернуть непустой reset-секрет для хеширования одноразовых кодов.
    """

    return require_env("RESET_SECRET")
