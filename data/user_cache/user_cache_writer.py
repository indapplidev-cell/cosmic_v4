"""EN: Persist user registration cache to JSON.
RU: Сохранять кэш регистрации пользователя в JSON.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from data.user_cache.user_cache_reader import get_user_cache

def _cache_path() -> Path:
    """EN: Resolve the user cache JSON file path.
    RU: Определить путь к JSON-файлу кэша пользователя.
    """
    return Path(__file__).resolve().parent / "user_cache.json"


def save_user(email: str, password: str, user_id: int | None = None) -> None:
    """EN: Save credentials to JSON cache and optionally persist user_id.
    RU: Сохранить учётные данные в JSON-кэш и при необходимости записать user_id.
    """
    cache_path = _cache_path()
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = cache_path.with_suffix(".tmp")
    data = {
        "email": email,
        "password": password,
    }
    if user_id is not None:
        data["user_id"] = int(user_id)

    with tmp_path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)

    os.replace(tmp_path, cache_path)


def write_user_cache(email: str, password: str, user_id: int | None = None) -> None:
    """EN: Compatibility alias for saving credentials and optional user_id.
    RU: Совместимый алиас для сохранения учётных данных и опционального user_id.
    """
    save_user(email, password, user_id=user_id)


def update_user_cache_fields(fields: dict) -> None:
    """EN: Update selected fields in the user cache JSON.
    RU: Обновить выбранные поля в JSON-кэше пользователя.
    """
    cache_path = _cache_path()
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    data = get_user_cache() or {}
    data.update(fields)
    tmp_path = cache_path.with_suffix(".tmp")
    with tmp_path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
    os.replace(tmp_path, cache_path)


def update_user_cache(patch: dict) -> None:
    """EN: Update selected fields in the user cache JSON.
    RU: Обновить выбранные поля в JSON-кэше пользователя.
    """
    update_user_cache_fields(patch)
