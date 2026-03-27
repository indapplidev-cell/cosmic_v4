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


def env_int(name: str, default: int) -> int:
    """EN: Return integer env value with explicit safe fallback for optional settings.
    RU: Вернуть целочисленное env-значение с явным безопасным fallback для optional-настроек.

    EN: This helper is used only for non-secret optional runtime tuning values.
    RU: Этот helper используется только для non-secret optional-параметров runtime-настройки.
    """

    raw = str((os.getenv(name, str(default)) or "").strip())
    try:
        return int(raw)
    except Exception:
        return int(default)


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


def get_pay_bot_token() -> str:
    """EN: Return non-empty payout bot token used for Telegram Mini App initData verification.
    RU: Вернуть непустой токен payout-бота для проверки Telegram Mini App initData.
    """

    return require_env("PAY_BOT_TOKEN")


def get_payout_miniapp_secret() -> str:
    """EN: Return non-empty secret used to hash payout Mini App session tokens.
    RU: Вернуть непустой секрет для хеширования payout Mini App session-токенов.
    """

    return require_env("PAYOUT_MINIAPP_SECRET")


def get_payout_miniapp_bot_username() -> str:
    """EN: Return payout Mini App bot username without leading at-sign.
    RU: Вернуть username payout Mini App бота без начального символа @.
    """

    return require_env("PAYOUT_MINIAPP_BOT_USERNAME").lstrip("@")


def get_payout_miniapp_short_name() -> str:
    """EN: Return configured Telegram Mini App short name for payout verification.
    RU: Вернуть настроенное short name Telegram Mini App для payout verification.
    """

    return require_env("PAYOUT_MINIAPP_SHORT_NAME")


def get_payout_miniapp_session_ttl_sec() -> int:
    """EN: Return payout Mini App session TTL in seconds with a documented default of 300.
    RU: Вернуть TTL payout Mini App session в секундах с документированным default 300.
    """

    return max(60, env_int("PAYOUT_MINIAPP_SESSION_TTL_SEC", 300))


def get_payout_miniapp_auth_max_age_sec() -> int:
    """EN: Return Telegram WebApp auth_date max age in seconds with a documented default of 300.
    RU: Вернуть максимально допустимый возраст Telegram WebApp auth_date в секундах с default 300.
    """

    return max(30, env_int("PAYOUT_MINIAPP_AUTH_MAX_AGE_SEC", 300))
