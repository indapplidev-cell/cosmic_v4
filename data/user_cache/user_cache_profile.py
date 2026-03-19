# -*- coding: utf-8 -*-
"""
Persistent user profile settings storage.

EN: Provides one JSON-backed source of truth for lightweight user settings.
RU: Предоставляет единый JSON-источник истины для лёгких пользовательских настроек.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


_DEFAULT_SETTINGS: dict[str, Any] = {
    "version": 1,
    "lang": "ru",
    "hud_layout_swapped": False,
    "sound_enabled": True,
}


def _profile_path() -> Path:
    """
    Return the absolute user profile settings path.

    EN: Resolves `data/user_cache/user_cache_profile.json` from the project root.
    RU: Определяет `data/user_cache/user_cache_profile.json` относительно корня проекта.
    """
    root = Path(__file__).resolve().parents[2]
    return root / "data" / "user_cache" / "user_cache_profile.json"


def _normalize_settings(data: dict[str, Any] | None) -> dict[str, Any]:
    """
    Normalize loaded settings against the supported schema.

    EN: Merges incoming data with safe defaults and coerces known value types.
    RU: Объединяет входные данные с безопасными дефолтами и приводит типы известных полей.
    """
    merged = dict(_DEFAULT_SETTINGS)
    if isinstance(data, dict):
        merged.update(data)
    merged["version"] = int(merged.get("version", 1) or 1)
    merged["lang"] = str(merged.get("lang", "ru") or "ru").strip().lower() or "ru"
    merged["hud_layout_swapped"] = bool(merged.get("hud_layout_swapped", False))
    merged["sound_enabled"] = bool(merged.get("sound_enabled", True))
    return merged


def load_user_profile_settings() -> dict[str, Any]:
    """
    Load persisted user profile settings with safe fallback.

    EN: Returns normalized defaults when the file is missing, empty, broken, or not a dict.
    RU: Возвращает нормализованные дефолты, если файл отсутствует, пустой, битый или не словарь.
    """
    path = _profile_path()
    if not path.exists():
        return dict(_DEFAULT_SETTINGS)
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return dict(_DEFAULT_SETTINGS)
    if not raw.strip():
        return dict(_DEFAULT_SETTINGS)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return dict(_DEFAULT_SETTINGS)
    if not isinstance(data, dict):
        return dict(_DEFAULT_SETTINGS)
    return _normalize_settings(data)


def save_user_profile_settings(data: dict[str, Any]) -> None:
    """
    Save user profile settings atomically.

    EN: Writes normalized JSON through a temporary file and `os.replace`.
    RU: Записывает нормализованный JSON через временный файл и `os.replace`.
    """
    path = _profile_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = _normalize_settings(data)
    tmp_path = path.with_suffix(".tmp")
    with tmp_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
    os.replace(tmp_path, path)


def update_user_profile_settings(patch: dict) -> dict[str, Any]:
    """
    Update selected profile settings fields and persist the merged result.

    EN: Applies a shallow patch to the current settings and returns saved data.
    RU: Применяет поверхностный patch к текущим настройкам и возвращает сохранённые данные.
    """
    data = load_user_profile_settings()
    if isinstance(patch, dict):
        data.update(patch)
    save_user_profile_settings(data)
    return load_user_profile_settings()


def get_user_setting(key: str, default=None):
    """
    Return a single setting value by key.

    EN: Reads from the unified profile settings storage with caller-provided fallback.
    RU: Читает значение из единого хранилища настроек профиля с fallback от вызывающей стороны.
    """
    if not key:
        return default
    return load_user_profile_settings().get(key, default)


def set_user_setting(key: str, value) -> None:
    """
    Persist a single setting value by key.

    EN: Updates one field in the unified profile settings storage.
    RU: Обновляет одно поле в едином хранилище настроек профиля.
    """
    if not key:
        return
    update_user_profile_settings({key: value})
