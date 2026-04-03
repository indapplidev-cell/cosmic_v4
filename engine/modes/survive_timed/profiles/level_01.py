# -*- coding: utf-8 -*-
"""EN: Survive_timed profile for level 1.
RU: Профиль survive_timed для уровня 1.
"""

from engine.modes.survive_timed.contracts import SurviveTimedLevelProfile


PROFILE = SurviveTimedLevelProfile(
    level_number=1,
    level_code="survive_timed_level_01",
    title="Survive Timed 01",
    target_survival_sec=60,
    initial_speed_y_factor=0.50,
    difficulty_label="easy",
)

