# -*- coding: utf-8 -*-
"""EN: Survive_timed profile for level 3.
RU: Профиль survive_timed для уровня 3.
"""

from engine.modes.survive_timed.contracts import SurviveTimedLevelProfile


PROFILE = SurviveTimedLevelProfile(
    level_number=3,
    level_code="survive_timed_level_03",
    title="Survive Timed 03",
    target_survival_sec=180,
    initial_speed_y_factor=0.54,
    difficulty_label="normal",
)

