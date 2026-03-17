"""EN: Persist non-secret user cache fields to JSON.
RU: Сохранять в JSON только несекретные поля кэша пользователя.
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
    """EN: Save user identity fields in cache without storing password.
    RU: Сохранить поля идентификации пользователя в кэше без хранения пароля.

    EN: The `password` argument is kept only for backward compatibility of call sites.
    RU: Аргумент `password` оставлен только для обратной совместимости с существующими вызовами.
    """

    del password
    cache_path = _cache_path()
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = cache_path.with_suffix(".tmp")
    data = {
        "email": email,
    }
    if user_id is not None:
        data["user_id"] = int(user_id)

    with tmp_path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)

    os.replace(tmp_path, cache_path)


def write_user_cache(email: str, password: str, user_id: int | None = None) -> None:
    """EN: Compatibility alias for saving user identity fields without password.
    RU: Совместимый алиас для сохранения полей пользователя без пароля.
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


def remove_user_cache_fields(keys: list[str]) -> None:
    """EN: Remove selected keys from user cache JSON.
    RU: Удалить выбранные ключи из JSON-кэша пользователя.

    EN: Used to guarantee that sensitive fields (for example `password`) are not persisted.
    RU: Используется для гарантии, что чувствительные поля (например `password`) не сохраняются.
    """

    cache_path = _cache_path()
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    data = get_user_cache() or {}
    changed = False
    for key in keys or []:
        if key in data:
            data.pop(key, None)
            changed = True
    if not changed:
        return

    tmp_path = cache_path.with_suffix(".tmp")
    with tmp_path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
    os.replace(tmp_path, cache_path)
