# -*- coding: utf-8 -*-
"""
Local default level provider used before remote level delivery exists.

EN: Resolves the default level id and returns a runtime profile with safe fallback.
RU: Возвращает id уровня по умолчанию и runtime-профиль с безопасным fallback.
"""

from __future__ import annotations

from engine.levels.contracts import LevelRuntimeProfile
from engine.levels.level_1.level_1_profile import build_level_1_profile


class DefaultLevelProvider:
    """
    Minimal local provider for runtime level profiles.

    EN: Keeps runtime independent from hardcoded level details and supports future provider replacement.
    RU: Держит runtime независимым от деталей уровней и готовит замену provider в будущем.
    """

    def get_default_level_id(self) -> str:
        """
        Return the local default level identifier.

        EN: Always resolves to the first shipped level.
        RU: Всегда возвращает идентификатор первого встроенного уровня.
        """
        return "level_1"

    def get_profile(self, level_id: str) -> LevelRuntimeProfile:
        """
        Return a runtime profile for the requested level id.

        EN: Falls back to the default level profile for unknown identifiers.
        RU: Делает fallback на профиль уровня по умолчанию для неизвестных идентификаторов.
        """
        if level_id == "level_1":
            return build_level_1_profile()
        return build_level_1_profile()

