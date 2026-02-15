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


def save_user(email: str, password: str) -> None:
    """EN: Save user credentials to the cache JSON.
    RU: Сохранить учётные данные пользователя в JSON-кэш.
    """
    cache_path = _cache_path()
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = cache_path.with_suffix(".tmp")
    data = {
        "email": email,
        "password": password,
    }

    with tmp_path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)

    os.replace(tmp_path, cache_path)


def write_user_cache(email: str, password: str) -> None:
    """EN: Save user credentials to the cache JSON.
    RU: Сохранить учётные данные пользователя в JSON-кэш.
    """
    save_user(email, password)


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
