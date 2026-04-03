# -*- coding: utf-8 -*-
"""EN: Survive_timed profile for level 4.
RU: Профиль survive_timed для уровня 4.
"""

from engine.modes.survive_timed.contracts import SurviveTimedLevelProfile


PROFILE = SurviveTimedLevelProfile(
    level_number=4,
    level_code="survive_timed_level_04",
    title="Survive Timed 04",
    target_survival_sec=240,
    initial_speed_y_factor=0.56,
    difficulty_label="normal",
)

