# -*- coding: utf-8 -*-
"""EN: Survive_timed profile for level 5.
RU: Профиль survive_timed для уровня 5.
"""

from engine.modes.survive_timed.contracts import SurviveTimedLevelProfile


PROFILE = SurviveTimedLevelProfile(
    level_number=5,
    level_code="survive_timed_level_05",
    title="Survive Timed 05",
    target_survival_sec=300,
    initial_speed_y_factor=0.58,
    difficulty_label="normal",
)
