# -*- coding: utf-8 -*-
"""
Runtime access layer for the currently active level profile.

EN: Bridges active level session state with the local default profile provider.
RU: Связывает состояние активного уровня с локальным provider runtime-профилей.
"""

from __future__ import annotations

from engine.levels.contracts import LevelRuntimeProfile
from engine.levels.default_level_provider import DefaultLevelProvider
from manager.levels import active_level_session


class LevelRuntimeManager:
    """
    Minimal accessor for the active gameplay level profile.

    EN: Resolves the selected level id and returns a runtime profile for gameplay startup.
    RU: Определяет выбранный id уровня и возвращает runtime-профиль для старта gameplay.
    """

    def __init__(self, provider: DefaultLevelProvider | None = None) -> None:
        """
        Store the provider used to resolve runtime profiles.

        EN: Uses the default local provider when no provider is supplied.
        RU: Использует локальный provider по умолчанию, если внешний provider не передан.
        """
        self._provider = provider or DefaultLevelProvider()

    def get_active_profile(self) -> LevelRuntimeProfile:
        """
        Return the runtime profile for the currently active level.

        EN: Reads the active level id from session state and resolves it through the provider.
        RU: Читает активный id уровня из session state и резолвит его через provider.
        """
        level_id = active_level_session.get_active_level_id()
        return self._provider.get_profile(level_id)

    def reset_to_default(self) -> None:
        """
        Reset the active level selection to the provider default.

        EN: Keeps session state aligned with the default shipped level.
        RU: Держит session state синхронизированным с дефолтным встроенным уровнем.
        """
        active_level_session.set_active_level_id(self._provider.get_default_level_id())

