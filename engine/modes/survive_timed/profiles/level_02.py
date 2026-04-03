# -*- coding: utf-8 -*-
"""EN: Survive_timed profile for level 2.
RU: Профиль survive_timed для уровня 2.
"""

from engine.modes.survive_timed.contracts import SurviveTimedLevelProfile


PROFILE = SurviveTimedLevelProfile(
    level_number=2,
    level_code="survive_timed_level_02",
    title="Survive Timed 02",
    target_survival_sec=120,
    initial_speed_y_factor=0.52,
    difficulty_label="easy",
)

