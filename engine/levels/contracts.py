# -*- coding: utf-8 -*-
"""
Contracts for level runtime data used by gameplay startup.

EN: Defines the minimal immutable runtime profile required to start a level.
RU: Определяет минимальный неизменяемый runtime-профиль, необходимый для старта уровня.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LevelRuntimeProfile:
    """
    Immutable runtime settings for a single level.

    EN: Holds only the fields required to initialize gameplay runtime behavior.
    RU: Хранит только поля, необходимые для инициализации поведения gameplay runtime.
    """

    level_id: str
    initial_speed_y_factor: float

