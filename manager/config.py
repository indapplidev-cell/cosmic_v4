"""EN: Runtime client configuration for backend API.
RU: Конфигурация клиента для API бэкенда во время выполнения.
"""

from __future__ import annotations

import os


API_BASE_URL = os.getenv("API_BASE_URL", "http://185.216.87.26:8000").rstrip("/")
TELEGRAM_BOT_USERNAME = os.getenv("TELEGRAM_BOT_USERNAME", "psw_protect_bot").strip().lstrip("@")
TELEGRAM_DEEPLINK_SCHEME = os.getenv(
    "TELEGRAM_DEEPLINK_SCHEME",
    "tg://resolve?domain={bot}&start={token}",
).strip()
TELEGRAM_WEB_LINK = os.getenv(
    "TELEGRAM_WEB_LINK",
    "https://t.me/{bot}?start={token}",
).strip()
