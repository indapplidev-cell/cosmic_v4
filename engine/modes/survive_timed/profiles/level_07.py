# -*- coding: utf-8 -*-
"""EN: Survive_timed profile for level 7.
RU: Профиль survive_timed для уровня 7.
"""

from engine.modes.survive_timed.contracts import SurviveTimedLevelProfile


PROFILE = SurviveTimedLevelProfile(
    level_number=7,
    level_code="survive_timed_level_07",
    title="Survive Timed 07",
    target_survival_sec=420,
    initial_speed_y_factor=0.62,
    difficulty_label="hard",
)