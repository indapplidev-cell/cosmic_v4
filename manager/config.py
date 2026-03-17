"""EN: Runtime client configuration for backend API.
RU: Конфигурация клиента для API бэкенда во время выполнения.
"""

from __future__ import annotations

import os


API_BASE_URL = os.getenv("API_BASE_URL", "http://185.216.87.26:8000").rstrip("/")
TELEGRAM_BOT_USERNAME = os.getenv("TELEGRAM_BOT_USERNAME", "pswprotect_bot").strip().lstrip("@")
PAYOUT_TELEGRAM_BOT_USERNAME = os.getenv("PAYOUT_TELEGRAM_BOT_USERNAME", "payprotect_bot").strip().lstrip("@")
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
