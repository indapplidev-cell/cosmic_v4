# -*- coding: utf-8 -*-
"""EN: Bootstrap helpers for selecting and activating survive_timed levels.
RU: Bootstrap-хелперы для выбора и активации уровней survive_timed.
"""

from __future__ import annotations

from engine.modes.survive_timed.contracts import SurviveTimedLevelProfile
from engine.modes.survive_timed.registry import get_level_profile
from manager.modes.survive_timed.active_level_session import get_current_active_level_number, set_current_active_level_number
from manager.modes.survive_timed.level_progress_service import SurviveTimedLevelProgressService


class SurviveTimedLevelBootstrapService:
    """EN: Resolve next survive_timed level to launch and keep active session aligned.
    RU: Определять следующий запускаемый уровень survive_timed и держать active-session синхронизированной.
    """

    def __init__(self, progress_service: SurviveTimedLevelProgressService | None = None) -> None:
        """EN: Store progress service dependency used for start-level resolution.
        RU: Сохранить зависимость progress-сервиса для определения стартового уровня.
        """

        self._progress_service = progress_service or SurviveTimedLevelProgressService()

    def resolve_start_level_number(self) -> int:
        """EN: Resolve and persist the survive_timed level number that should start next.
        RU: Определить и сохранить номер уровня survive_timed, который должен стартовать следующим.
        """

        level_number = self._progress_service.resolve_start_level_number()
        set_current_active_level_number(level_number)
        return level_number

    def activate_level(self, level_number: int) -> SurviveTimedLevelProfile:
        """EN: Activate one survive_timed level and return its shipped profile.
        RU: Активировать один уровень survive_timed и вернуть его встроенный профиль.
        """

        set_current_active_level_number(level_number)
        return get_level_profile(level_number)

    def get_active_profile(self) -> SurviveTimedLevelProfile:
        """EN: Return current active survive_timed profile from session state.
        RU: Вернуть текущий активный профиль survive_timed из session-state.
        """

        return get_level_profile(get_current_active_level_number())