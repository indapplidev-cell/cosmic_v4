"""EN: Legacy rating wrapper module.
RU: Legacy-модуль-обёртка для расчёта рейтинга.
"""

from __future__ import annotations

from data.gameplay.profile_math import calc_rating


def calculate_rating_points(
    s_life: int,
    s_game: int,
    valid_starts: int,
    gameplay_sec: float | None,
) -> int:
    """EN: Compatibility wrapper that delegates rating calculation to profile_math.
    RU: Совместимая обёртка, делегирующая расчёт рейтинга в profile_math.
    """

    rating, _debug = calc_rating(
        record_prev=0,
        record_sis=int(max(0, s_game)),
        record_pure=int(max(0, s_game)),
        chis_sec=float(gameplay_sec or 0.0),
        attempts=max(1, int(valid_starts)),
        reward_clicks=0,
        best_life_score=int(max(0, s_life)),
        best_game_score=int(max(0, s_game)),
        valid_starts=int(max(0, valid_starts)),
    )
    return int(rating)
