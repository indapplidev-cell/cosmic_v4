# -*- coding: utf-8 -*-
"""
EN: Mode-specific level contract for survive_timed gameplay.
RU: РљРѕРЅС‚СЂР°РєС‚ СѓСЂРѕРІРЅСЏ СЂРµР¶РёРјР° survive_timed.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SurviveTimedLevelProfile:
    """EN: Immutable survive_timed level profile used by runtime and progression services.
    RU: РќРµРёР·РјРµРЅСЏРµРјС‹Р№ РїСЂРѕС„РёР»СЊ СѓСЂРѕРІРЅСЏ survive_timed, РёСЃРїРѕР»СЊР·СѓРµРјС‹Р№ runtime Рё СЃРµСЂРІРёСЃР°РјРё РїСЂРѕРіСЂРµСЃСЃРёРё.
    """

    level_number: int
    level_code: str
    title: str
    target_survival_sec: int
    initial_speed_y_factor: float
    difficulty_label: str = ""
