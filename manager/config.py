"""EN: Runtime client configuration for backend API.
RU: Конфигурация клиента для API бэкенда во время выполнения.
"""

from __future__ import annotations

import os
from pathlib import Path


def _load_root_env_defaults() -> None:
    """EN: Load non-secret root .env defaults only when runtime env is not explicitly configured.
    RU: Подгрузить несекретные значения из корневого .env только когда runtime-env не задан явно.
    """

    if "APP_ENV" in os.environ or "API_BASE_URL" in os.environ:
        return

    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ.setdefault(key, value)


_load_root_env_defaults()

APP_ENV = os.getenv("APP_ENV", "dev").strip().lower()


def _resolve_api_base_url() -> str:
    """EN: Resolve backend API base URL from env and allow localhost fallback only in dev/local.
    RU: Определить базовый URL backend API из env и разрешать fallback на localhost только в dev/local.
    """

    raw_value = str((os.getenv("API_BASE_URL", "") or "").strip()).rstrip("/")
    if raw_value:
        return raw_value
    if APP_ENV in {"dev", "local"}:
        return "http://127.0.0.1:8000"
    raise RuntimeError("API_BASE_URL is required outside dev/local")


API_BASE_URL = _resolve_api_base_url()
TELEGRAM_BOT_USERNAME = os.getenv("TELEGRAM_BOT_USERNAME", "pswprotect_bot").strip().lstrip("@")
PAYOUT_TELEGRAM_BOT_USERNAME = os.getenv("PAYOUT_TELEGRAM_BOT_USERNAME", "escape2mars_bot").strip().lstrip("@")
TG_OPEN_TIMEOUT_SEC = int(os.getenv("TG_OPEN_TIMEOUT_SEC", "5"))
VERIFY_OPEN_TIMEOUT_SEC = int(os.getenv("VERIFY_OPEN_TIMEOUT_SEC", "10"))
TG_VERIFY_TIMEOUT_SEC = int(os.getenv("TG_VERIFY_TIMEOUT_SEC", "60"))
TG_LINK_STATUS_POLL_SEC = float(os.getenv("TG_LINK_STATUS_POLL_SEC", "1"))
DELAY_WARMUP_MS = int(os.getenv("DELAY_WARMUP_MS", "1500"))
DELAY_RETRY_MS = int(os.getenv("DELAY_RETRY_MS", "2500"))
TG_DEBUG_FLOW = os.getenv("TG_DEBUG_FLOW", "1").strip() in {"1", "true", "True", "yes", "YES"}
TELEGRAM_DEEPLINK_SCHEME = os.getenv(
    "TELEGRAM_DEEPLINK_SCHEME",
    "tg://resolve?domain={bot}&start={token}",
).strip()
TELEGRAM_WEB_LINK = os.getenv(
    "TELEGRAM_WEB_LINK",
    "https://t.me/{bot}?start={token}",
).strip()
APP_RETURN_DEEPLINK = os.getenv("APP_RETURN_DEEPLINK", "cosmic://return?screen=settings").strip()
