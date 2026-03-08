"""EN: Smoke checks for profile formulas from cosmic_profile_formulas.docx.
RU: Smoke-проверки формул профиля из cosmic_profile_formulas.docx.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data.gameplay.profile_math import (
    DEFAULT_CFG,
    calc_pay_raw,
    cheat_speed,
    triangular_speed_weight,
)


def _assert_close(actual: float, expected: float, eps: float = 1e-9) -> None:
    """EN: Assert floating values are approximately equal.
    RU: Проверить приблизительное равенство float-значений.
    """

    if abs(float(actual) - float(expected)) > float(eps):
        raise AssertionError(f"expected={expected}, actual={actual}")


def main() -> None:
    """EN: Run all mandatory checks and print concise status.
    RU: Запустить обязательные проверки и вывести краткий статус.
    """

    pay_raw_1, dbg_1 = calc_pay_raw(sis_sec=5000, reward_clicks=0, cfg=DEFAULT_CFG)
    assert int(dbg_1["banner_impr"]) == 1000
    _assert_close(pay_raw_1, 0.10)

    pay_raw_2, dbg_2 = calc_pay_raw(sis_sec=0, reward_clicks=1000, cfg=DEFAULT_CFG)
    _assert_close(float(dbg_2["reward_pay"]), 0.30)
    _assert_close(pay_raw_2, 0.30)

    _assert_close(
        triangular_speed_weight(DEFAULT_CFG.V_MID, DEFAULT_CFG.V_MIN, DEFAULT_CFG.V_MID, DEFAULT_CFG.V_MAX),
        1.0,
    )
    _assert_close(
        triangular_speed_weight(DEFAULT_CFG.V_MIN, DEFAULT_CFG.V_MIN, DEFAULT_CFG.V_MID, DEFAULT_CFG.V_MAX),
        0.0,
    )
    _assert_close(
        triangular_speed_weight(DEFAULT_CFG.V_MAX, DEFAULT_CFG.V_MIN, DEFAULT_CFG.V_MID, DEFAULT_CFG.V_MAX),
        0.0,
    )

    assert cheat_speed(record_pure=20, chis_sec=20, cfg=DEFAULT_CFG) is False
    assert cheat_speed(record_pure=20, chis_sec=60, cfg=DEFAULT_CFG) is True

    print("OK: profile_math checks passed")


if __name__ == "__main__":
    main()
