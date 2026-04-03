# -*- coding: utf-8 -*-
"""EN: Survive_timed profile for level 10.
RU: Профиль survive_timed для уровня 10.
"""

from engine.modes.survive_timed.contracts import SurviveTimedLevelProfile


PROFILE = SurviveTimedLevelProfile(
    level_number=10,
    level_code="survive_timed_level_10",
    title="Survive Timed 10",
    target_survival_sec=600,
    initial_speed_y_factor=0.68,
    difficulty_label="expert",
)