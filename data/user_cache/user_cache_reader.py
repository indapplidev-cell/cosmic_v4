"""EN: Read and validate user registration cache.
RU: Чтение и проверка кэша регистрации пользователя.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _cache_path() -> Path:
    """EN: Resolve the user cache JSON file path.
    RU: Определить путь к JSON-файлу кэша пользователя.
    """
    return Path(__file__).resolve().parent / "user_cache.json"


def get_user_cache() -> dict[str, Any] | None:
    """EN: Load user cache JSON if it exists and is valid.
    RU: Загрузить JSON кэша пользователя, если он существует и валиден.
    """
    cache_path = _cache_path()
    if not cache_path.exists():
        return None

    try:
        raw = cache_path.read_text(encoding="utf-8")
    except OSError:
        return None

    if not raw.strip():
        return None

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None

    return data if isinstance(data, dict) else None


def is_credentials_valid(email: str, password: str) -> bool:
    """EN: Validate credentials against cached registration data.
    RU: Проверить учетные данные по сохраненному кэшу регистрации.
    """
    cache = get_user_cache()
    if not cache:
        return False

    cached_email = cache.get("email")
    cached_password = cache.get("password")
    if not isinstance(cached_email, str) or not isinstance(cached_password, str):
        return False

    return cached_email == email.strip() and cached_password == password.strip()
