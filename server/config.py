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
