# -*- coding: utf-8 -*-
"""EN: Survive_timed profile for level 6.
RU: Профиль survive_timed для уровня 6.
"""

from engine.modes.survive_timed.contracts import SurviveTimedLevelProfile


PROFILE = SurviveTimedLevelProfile(
    level_number=6,
    level_code="survive_timed_level_06",
    title="Survive Timed 06",
    target_survival_sec=360,
    initial_speed_y_factor=0.60,
    difficulty_label="hard",
)