# -*- coding: utf-8 -*-
"""EN: Survive_timed profile for level 9.
RU: Профиль survive_timed для уровня 9.
"""

from engine.modes.survive_timed.contracts import SurviveTimedLevelProfile


PROFILE = SurviveTimedLevelProfile(
    level_number=9,
    level_code="survive_timed_level_09",
    title="Survive Timed 09",
    target_survival_sec=540,
    initial_speed_y_factor=0.66,
    difficulty_label="expert",
)