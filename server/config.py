"""EN: Database configuration for the server module.
RU: Конфигурация базы данных для серверного модуля.
"""

from __future__ import annotations

import os
from typing import Any


DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./server/app.db")


def get_engine_connect_args(database_url: str | None = None) -> dict[str, Any]:
    """EN: Return SQLAlchemy engine connect args for the selected backend.
    RU: Вернуть параметры подключения SQLAlchemy engine для выбранного backend.
    """
    url = database_url or DATABASE_URL
    if url.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}
