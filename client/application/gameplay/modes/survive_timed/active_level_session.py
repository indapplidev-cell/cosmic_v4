# -*- coding: utf-8 -*-
"""EN: In-memory active survive_timed level selection for the current process.
RU: In-memory РІС‹Р±РѕСЂ Р°РєС‚РёРІРЅРѕРіРѕ СѓСЂРѕРІРЅСЏ survive_timed РґР»СЏ С‚РµРєСѓС‰РµРіРѕ РїСЂРѕС†РµСЃСЃР°.
"""

from __future__ import annotations

from shared.constants.survive_timed_levels import get_default_level_number


_active_level_number: int | None = None


def get_current_active_level_number() -> int:
    """EN: Return active survive_timed level number or default first level.
    RU: Р’РµСЂРЅСѓС‚СЊ Р°РєС‚РёРІРЅС‹Р№ РЅРѕРјРµСЂ СѓСЂРѕРІРЅСЏ survive_timed РёР»Рё РґРµС„РѕР»С‚РЅС‹Р№ РїРµСЂРІС‹Р№ СѓСЂРѕРІРµРЅСЊ.
    """

    return int(_active_level_number or get_default_level_number())


def set_current_active_level_number(level_number: int) -> None:
    """EN: Store active survive_timed level number for the current process.
    RU: РЎРѕС…СЂР°РЅРёС‚СЊ Р°РєС‚РёРІРЅС‹Р№ РЅРѕРјРµСЂ СѓСЂРѕРІРЅСЏ survive_timed РґР»СЏ С‚РµРєСѓС‰РµРіРѕ РїСЂРѕС†РµСЃСЃР°.
    """

    global _active_level_number
    _active_level_number = max(int(level_number), get_default_level_number())


def reset_to_default() -> None:
    """EN: Reset active survive_timed level selection to default.
    RU: РЎР±СЂРѕСЃРёС‚СЊ РІС‹Р±РѕСЂ Р°РєС‚РёРІРЅРѕРіРѕ СѓСЂРѕРІРЅСЏ survive_timed Рє Р·РЅР°С‡РµРЅРёСЋ РїРѕ СѓРјРѕР»С‡Р°РЅРёСЋ.
    """

    global _active_level_number
    _active_level_number = None
