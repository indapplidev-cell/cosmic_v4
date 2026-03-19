# -*- coding: utf-8 -*-
"""
Runtime profile builder for level 1.

EN: Defines the default local level profile used on gameplay startup.
RU: Определяет профиль локального уровня по умолчанию для старта gameplay.
"""

from __future__ import annotations

from engine.levels.contracts import LevelRuntimeProfile


def build_level_1_profile() -> LevelRuntimeProfile:
    """
    Build the runtime profile for the default first level.

    EN: Returns level_1 with half of the current base vertical speed factor.
    RU: Возвращает level_1 с половиной текущего базового коэффициента вертикальной скорости.
    """
    return LevelRuntimeProfile(level_id="level_1", initial_speed_y_factor=0.5)

