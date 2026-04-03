# -*- coding: utf-8 -*-
"""EN: Explicit registry for shipped survive_timed level profiles.
RU: Явный реестр встроенных профилей уровней survive_timed.
"""

from __future__ import annotations

from engine.modes.survive_timed.contracts import SurviveTimedLevelProfile
from engine.modes.survive_timed.profiles.level_01 import PROFILE as LEVEL_01
from engine.modes.survive_timed.profiles.level_02 import PROFILE as LEVEL_02
from engine.modes.survive_timed.profiles.level_03 import PROFILE as LEVEL_03
from engine.modes.survive_timed.profiles.level_04 import PROFILE as LEVEL_04
from engine.modes.survive_timed.profiles.level_05 import PROFILE as LEVEL_05
from engine.modes.survive_timed.profiles.level_06 import PROFILE as LEVEL_06
from engine.modes.survive_timed.profiles.level_07 import PROFILE as LEVEL_07
from engine.modes.survive_timed.profiles.level_08 import PROFILE as LEVEL_08
from engine.modes.survive_timed.profiles.level_09 import PROFILE as LEVEL_09
from engine.modes.survive_timed.profiles.level_10 import PROFILE as LEVEL_10


_LEVELS: dict[int, SurviveTimedLevelProfile] = {
    1: LEVEL_01,
    2: LEVEL_02,
    3: LEVEL_03,
    4: LEVEL_04,
    5: LEVEL_05,
    6: LEVEL_06,
    7: LEVEL_07,
    8: LEVEL_08,
    9: LEVEL_09,
    10: LEVEL_10,
}


def get_default_level_number() -> int:
    """EN: Return the first shipped survive_timed level number.
    RU: Вернуть номер первого встроенного уровня survive_timed.
    """

    return 1


def get_max_level_number() -> int:
    """EN: Return the last shipped survive_timed level number.
    RU: Вернуть номер последнего встроенного уровня survive_timed.
    """

    return max(_LEVELS)


def get_level_profile(level_number: int) -> SurviveTimedLevelProfile:
    """EN: Return survive_timed profile for the requested level number.
    RU: Вернуть профиль survive_timed для запрошенного номера уровня.
    """

    number = max(int(level_number), get_default_level_number())
    return _LEVELS.get(number, _LEVELS[get_max_level_number()])


def get_all_profiles() -> tuple[SurviveTimedLevelProfile, ...]:
    """EN: Return all shipped survive_timed profiles in ascending level order.
    RU: Вернуть все встроенные профили survive_timed по возрастанию уровней.
    """

    return tuple(_LEVELS[number] for number in sorted(_LEVELS))