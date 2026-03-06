"""EN: Runtime client configuration for backend API.
RU: Конфигурация клиента для API бэкенда во время выполнения.
"""

from __future__ import annotations

import os


API_BASE_URL = os.getenv("API_BASE_URL", "http://185.216.87.26:8000").rstrip("/")
