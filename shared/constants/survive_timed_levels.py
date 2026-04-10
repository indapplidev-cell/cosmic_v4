# -*- coding: utf-8 -*-
"""EN: Explicit registry for shipped survive_timed level profiles.
RU: РЇРІРЅС‹Р№ СЂРµРµСЃС‚СЂ РІСЃС‚СЂРѕРµРЅРЅС‹С… РїСЂРѕС„РёР»РµР№ СѓСЂРѕРІРЅРµР№ survive_timed.
"""

from __future__ import annotations

from shared.contracts.survive_timed import SurviveTimedLevelProfile


_LEVELS: dict[int, SurviveTimedLevelProfile] = {
    1: SurviveTimedLevelProfile(
        level_number=1,
        level_code="survive_timed_level_01",
        title="Survive Timed 01",
        target_survival_sec=60,
        initial_speed_y_factor=0.50,
        difficulty_label="easy",
    ),
    2: SurviveTimedLevelProfile(
        level_number=2,
        level_code="survive_timed_level_02",
        title="Survive Timed 02",
        target_survival_sec=120,
        initial_speed_y_factor=0.52,
        difficulty_label="easy",
    ),
    3: SurviveTimedLevelProfile(
        level_number=3,
        level_code="survive_timed_level_03",
        title="Survive Timed 03",
        target_survival_sec=180,
        initial_speed_y_factor=0.54,
        difficulty_label="normal",
    ),
    4: SurviveTimedLevelProfile(
        level_number=4,
        level_code="survive_timed_level_04",
        title="Survive Timed 04",
        target_survival_sec=240,
        initial_speed_y_factor=0.56,
        difficulty_label="normal",
    ),
    5: SurviveTimedLevelProfile(
        level_number=5,
        level_code="survive_timed_level_05",
        title="Survive Timed 05",
        target_survival_sec=300,
        initial_speed_y_factor=0.58,
        difficulty_label="normal",
    ),
    6: SurviveTimedLevelProfile(
        level_number=6,
        level_code="survive_timed_level_06",
        title="Survive Timed 06",
        target_survival_sec=360,
        initial_speed_y_factor=0.60,
        difficulty_label="hard",
    ),
    7: SurviveTimedLevelProfile(
        level_number=7,
        level_code="survive_timed_level_07",
        title="Survive Timed 07",
        target_survival_sec=420,
        initial_speed_y_factor=0.62,
        difficulty_label="hard",
    ),
    8: SurviveTimedLevelProfile(
        level_number=8,
        level_code="survive_timed_level_08",
        title="Survive Timed 08",
        target_survival_sec=480,
        initial_speed_y_factor=0.64,
        difficulty_label="expert",
    ),
    9: SurviveTimedLevelProfile(
        level_number=9,
        level_code="survive_timed_level_09",
        title="Survive Timed 09",
        target_survival_sec=540,
        initial_speed_y_factor=0.66,
        difficulty_label="expert",
    ),
    10: SurviveTimedLevelProfile(
        level_number=10,
        level_code="survive_timed_level_10",
        title="Survive Timed 10",
        target_survival_sec=600,
        initial_speed_y_factor=0.68,
        difficulty_label="expert",
    ),
}


def get_default_level_number() -> int:
    """EN: Return the first shipped survive_timed level number.
    RU: Р’РµСЂРЅСѓС‚СЊ РЅРѕРјРµСЂ РїРµСЂРІРѕРіРѕ РІСЃС‚СЂРѕРµРЅРЅРѕРіРѕ СѓСЂРѕРІРЅСЏ survive_timed.
    """

    return 1


def get_max_level_number() -> int:
    """EN: Return the last shipped survive_timed level number.
    RU: Р’РµСЂРЅСѓС‚СЊ РЅРѕРјРµСЂ РїРѕСЃР»РµРґРЅРµРіРѕ РІСЃС‚СЂРѕРµРЅРЅРѕРіРѕ СѓСЂРѕРІРЅСЏ survive_timed.
    """

    return max(_LEVELS)


def get_level_profile(level_number: int) -> SurviveTimedLevelProfile:
    """EN: Return survive_timed profile for the requested level number.
    RU: Р’РµСЂРЅСѓС‚СЊ РїСЂРѕС„РёР»СЊ survive_timed РґР»СЏ Р·Р°РїСЂРѕС€РµРЅРЅРѕРіРѕ РЅРѕРјРµСЂР° СѓСЂРѕРІРЅСЏ.
    """

    number = max(int(level_number), get_default_level_number())
    return _LEVELS.get(number, _LEVELS[get_max_level_number()])


def get_all_profiles() -> tuple[SurviveTimedLevelProfile, ...]:
    """EN: Return all shipped survive_timed profiles in ascending level order.
    RU: Р’РµСЂРЅСѓС‚СЊ РІСЃРµ РІСЃС‚СЂРѕРµРЅРЅС‹Рµ РїСЂРѕС„РёР»Рё survive_timed РїРѕ РІРѕР·СЂР°СЃС‚Р°РЅРёСЋ СѓСЂРѕРІРЅРµР№.
    """

    return tuple(_LEVELS[number] for number in sorted(_LEVELS))
