# -*- coding: utf-8 -*-
"""EN: Survive_timed profile for level 8.
RU: Профиль survive_timed для уровня 8.
"""

from engine.modes.survive_timed.contracts import SurviveTimedLevelProfile


PROFILE = SurviveTimedLevelProfile(
    level_number=8,
    level_code="survive_timed_level_08",
    title="Survive Timed 08",
    target_survival_sec=480,
    initial_speed_y_factor=0.64,
    difficulty_label="expert",
)