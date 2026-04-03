# -*- coding: utf-8 -*-
"""EN: In-memory active survive_timed level selection for the current process.
RU: In-memory выбор активного уровня survive_timed для текущего процесса.
"""

from __future__ import annotations

from engine.modes.survive_timed.registry import get_default_level_number


_active_level_number: int | None = None


def get_current_active_level_number() -> int:
    """EN: Return active survive_timed level number or default first level.
    RU: Вернуть активный номер уровня survive_timed или дефолтный первый уровень.
    """

    return int(_active_level_number or get_default_level_number())


def set_current_active_level_number(level_number: int) -> None:
    """EN: Store active survive_timed level number for the current process.
    RU: Сохранить активный номер уровня survive_timed для текущего процесса.
    """

    global _active_level_number
    _active_level_number = max(int(level_number), get_default_level_number())


def reset_to_default() -> None:
    """EN: Reset active survive_timed level selection to default.
    RU: Сбросить выбор активного уровня survive_timed к значению по умолчанию.
    """

    global _active_level_number
    _active_level_number = None