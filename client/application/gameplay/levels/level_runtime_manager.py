# -*- coding: utf-8 -*-
"""
Runtime access layer for the currently active level profile.

EN: Bridges active level session state with the local default profile provider.
RU: РЎРІСЏР·С‹РІР°РµС‚ СЃРѕСЃС‚РѕСЏРЅРёРµ Р°РєС‚РёРІРЅРѕРіРѕ СѓСЂРѕРІРЅСЏ СЃ Р»РѕРєР°Р»СЊРЅС‹Рј provider runtime-РїСЂРѕС„РёР»РµР№.
"""

from __future__ import annotations

from client.gameplay.levels.contracts import LevelRuntimeProfile
from client.gameplay.levels.default_level_provider import DefaultLevelProvider
from client.application.gameplay.levels import active_level_session
from client.application.gameplay.modes.survive_timed.active_level_session import get_current_active_level_number, set_current_active_level_number
from client.application.gameplay.modes.survive_timed.mode_registry import SURVIVE_TIMED_MODE_CODE, get_default_game_mode_code
from shared.constants.survive_timed_levels import get_default_level_number as get_survive_timed_default_level_number
from shared.constants.survive_timed_levels import get_level_profile as get_survive_timed_level_profile


class LevelRuntimeManager:
    """
    Minimal accessor for the active gameplay level profile.

    EN: Resolves the selected level id and returns a runtime profile for gameplay startup.
    RU: РћРїСЂРµРґРµР»СЏРµС‚ РІС‹Р±СЂР°РЅРЅС‹Р№ id СѓСЂРѕРІРЅСЏ Рё РІРѕР·РІСЂР°С‰Р°РµС‚ runtime-РїСЂРѕС„РёР»СЊ РґР»СЏ СЃС‚Р°СЂС‚Р° gameplay.
    """

    def __init__(self, provider: DefaultLevelProvider | None = None) -> None:
        """
        Store the provider used to resolve runtime profiles.

        EN: Uses the default local provider when no provider is supplied.
        RU: РСЃРїРѕР»СЊР·СѓРµС‚ Р»РѕРєР°Р»СЊРЅС‹Р№ provider РїРѕ СѓРјРѕР»С‡Р°РЅРёСЋ, РµСЃР»Рё РІРЅРµС€РЅРёР№ provider РЅРµ РїРµСЂРµРґР°РЅ.
        """
        self._provider = provider or DefaultLevelProvider()

    def get_active_profile(self) -> LevelRuntimeProfile:
        """
        Return the runtime profile for the currently active level.

        EN: Reads the active level id from session state and resolves it through the provider.
        RU: Р§РёС‚Р°РµС‚ Р°РєС‚РёРІРЅС‹Р№ id СѓСЂРѕРІРЅСЏ РёР· session state Рё СЂРµР·РѕР»РІРёС‚ РµРіРѕ С‡РµСЂРµР· provider.
        """
        if get_default_game_mode_code() == SURVIVE_TIMED_MODE_CODE:
            profile = get_survive_timed_level_profile(get_current_active_level_number())
            return LevelRuntimeProfile(
                level_id=str(profile.level_code),
                level_number=int(profile.level_number),
                initial_speed_y_factor=float(profile.initial_speed_y_factor),
                target_score=0,
                time_limit_sec=int(profile.target_survival_sec),
                record_type="survive_timed",
            )
        level_id = active_level_session.get_active_level_id()
        return self._provider.get_profile(level_id)

    def reset_to_default(self) -> None:
        """
        Reset the active level selection to the provider default.

        EN: Keeps session state aligned with the default shipped level.
        RU: Р”РµСЂР¶РёС‚ session state СЃРёРЅС…СЂРѕРЅРёР·РёСЂРѕРІР°РЅРЅС‹Рј СЃ РґРµС„РѕР»С‚РЅС‹Рј РІСЃС‚СЂРѕРµРЅРЅС‹Рј СѓСЂРѕРІРЅРµРј.
        """
        if get_default_game_mode_code() == SURVIVE_TIMED_MODE_CODE:
            set_current_active_level_number(int(get_survive_timed_default_level_number()))
            return
        active_level_session.set_active_level_id(self._provider.get_default_level_id())



