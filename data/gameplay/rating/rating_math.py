"""EN: Rating math utilities.
RU: Утилиты расчета рейтинга.
"""

from __future__ import annotations

import math


def clamp01(x: float) -> float:
    """EN: Clamp value to the [0..1] range.
    RU: Ограничить значение диапазоном [0..1].
    """
    return max(0.0, min(1.0, x))


def norm_log(x: float, x_ref: float) -> float:
    """EN: Log normalization to [0..1] by reference value.
    RU: Логарифмическая нормализация в [0..1] по референсу.
    """
    if x_ref <= 0:
        return 0.0
    return clamp01(math.log1p(max(0.0, x)) / math.log1p(x_ref))


def norm_sat_starts(n: int, k: float = 0.35, n_max: int = 30) -> float:
    """EN: Saturating normalization for valid start count.
    RU: Насыщающая нормализация количества валидных стартов.
    """
    n = max(0, min(int(n), int(n_max)))
    if n <= 1:
        return 0.0
    return clamp01(1.0 - math.exp(-k * max(0, n - 1)))


def calculate_rating_points(
    s_life: int,
    s_game: int,
    valid_starts: int,
    gameplay_sec: float | None,
) -> int:
    """EN: Calculate rating points in [0..1000] from normalized components.
    RU: Рассчитать рейтинг в [0..1000] по нормализованным компонентам.
    """
    s_life_ref = 120.0
    s_game_ref = 300.0
    t_ref = 60.0

    f1 = norm_log(float(s_life), s_life_ref)
    f2 = norm_log(float(s_game), s_game_ref)
    f3 = norm_sat_starts(int(valid_starts), k=0.35, n_max=30)

    if gameplay_sec is None:
        w1, w2, w3 = 0.45, 0.40, 0.15
        rating_01 = w1 * f1 + w2 * f2 + w3 * f3
    else:
        f4 = norm_log(float(gameplay_sec), t_ref)
        w1, w2, w3, w4 = 0.40, 0.35, 0.10, 0.15
        rating_01 = w1 * f1 + w2 * f2 + w3 * f3 + w4 * f4

    rating_01 = clamp01(rating_01)
    return int(round(1000 * rating_01))
