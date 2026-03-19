# -*- coding: utf-8 -*-
"""
In-memory active level selection for the current process.

EN: Stores the currently selected level id without persistence.
RU: Хранит идентификатор текущего выбранного уровня без постоянного сохранения.
"""

from __future__ import annotations

_DEFAULT_LEVEL_ID = "level_1"
_active_level_id: str | None = None


def get_active_level_id() -> str:
    """
    Return the active level id for the current process.

    EN: Falls back to level_1 when nothing was selected explicitly.
    RU: Делает fallback на level_1, если ничего не было выбрано явно.
    """
    return _active_level_id or _DEFAULT_LEVEL_ID


def set_active_level_id(level_id: str) -> None:
    """
    Set the active level id for the current process.

    EN: Stores the provided identifier or resets to the default when empty.
    RU: Сохраняет переданный идентификатор или сбрасывает на дефолтный, если он пустой.
    """
    global _active_level_id
    _active_level_id = level_id or _DEFAULT_LEVEL_ID


def reset_to_default() -> None:
    """
    Reset the active level selection to the default id.

    EN: Clears the current in-memory override.
    RU: Очищает текущее in-memory переопределение.
    """
    global _active_level_id
    _active_level_id = None

