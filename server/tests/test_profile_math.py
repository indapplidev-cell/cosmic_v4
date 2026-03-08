"""EN: Unit tests for server-side profile math formulas.
RU: Юнит-тесты серверных формул profile math.
"""

from __future__ import annotations

from server.services.profile_math import (
    DEFAULT_CFG,
    calc_balance_delta,
    calc_pay_raw,
    cheat_fast_windows,
    cheat_speed,
    triangular_speed_weight,
)


def test_triangular_speed_weight_points() -> None:
    """EN: Check key points of triangular speed weight function.
    RU: Проверить ключевые точки функции треугольного веса скорости.
    """

    assert triangular_speed_weight(DEFAULT_CFG.V_MID, DEFAULT_CFG.V_MIN, DEFAULT_CFG.V_MID, DEFAULT_CFG.V_MAX) == 1.0
    assert triangular_speed_weight(DEFAULT_CFG.V_MIN, DEFAULT_CFG.V_MIN, DEFAULT_CFG.V_MID, DEFAULT_CFG.V_MAX) == 0.0
    assert triangular_speed_weight(DEFAULT_CFG.V_MAX, DEFAULT_CFG.V_MIN, DEFAULT_CFG.V_MID, DEFAULT_CFG.V_MAX) == 0.0


def test_pay_raw_and_balance_bound() -> None:
    """EN: Ensure payout math and balance bound condition are respected.
    RU: Убедиться, что математика выплат и ограничение balance <= pay_raw соблюдены.
    """

    pay_raw, _ = calc_pay_raw(sis_sec=5000, reward_clicks=1000, cfg=DEFAULT_CFG)
    balance_delta, _ = calc_balance_delta(
        pay_raw=pay_raw,
        rating=800,
        f_rec=0.8,
        f1=0.7,
        f2=0.6,
        f3=0.9,
        w_case=0.7,
        cfg=DEFAULT_CFG,
    )
    assert pay_raw > 0
    assert balance_delta <= pay_raw


def test_cheat_slow_and_fast_window() -> None:
    """EN: Validate slow cheat and fast window cheat checks.
    RU: Проверить slow cheat и fast-window cheat проверки.
    """

    assert cheat_speed(record_pure=20, chis_sec=60, cfg=DEFAULT_CFG) is True
    assert (
        cheat_fast_windows(
            anti_cheat_windows=[{"delta_score": 20, "delta_sec": 1.0}],
            cfg=DEFAULT_CFG,
        )
        is True
    )
