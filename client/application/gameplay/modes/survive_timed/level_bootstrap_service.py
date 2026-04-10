# -*- coding: utf-8 -*-
"""EN: Bootstrap helpers for selecting and activating survive_timed levels.
RU: Bootstrap-С…РµР»РїРµСЂС‹ РґР»СЏ РІС‹Р±РѕСЂР° Рё Р°РєС‚РёРІР°С†РёРё СѓСЂРѕРІРЅРµР№ survive_timed.
"""

from __future__ import annotations

from client.application.gameplay.modes.survive_timed.active_level_session import get_current_active_level_number, set_current_active_level_number
from client.application.gameplay.modes.survive_timed.level_progress_service import SurviveTimedLevelProgressService
from shared.constants.survive_timed_levels import get_level_profile
from shared.contracts.survive_timed import SurviveTimedLevelProfile


class SurviveTimedLevelBootstrapService:
    """EN: Resolve next survive_timed level to launch and keep active session aligned.
    RU: РћРїСЂРµРґРµР»СЏС‚СЊ СЃР»РµРґСѓСЋС‰РёР№ Р·Р°РїСѓСЃРєР°РµРјС‹Р№ СѓСЂРѕРІРµРЅСЊ survive_timed Рё РґРµСЂР¶Р°С‚СЊ active-session СЃРёРЅС…СЂРѕРЅРёР·РёСЂРѕРІР°РЅРЅРѕР№.
    """

    def __init__(self, progress_service: SurviveTimedLevelProgressService | None = None) -> None:
        """EN: Store progress service dependency used for start-level resolution.
        RU: РЎРѕС…СЂР°РЅРёС‚СЊ Р·Р°РІРёСЃРёРјРѕСЃС‚СЊ progress-СЃРµСЂРІРёСЃР° РґР»СЏ РѕРїСЂРµРґРµР»РµРЅРёСЏ СЃС‚Р°СЂС‚РѕРІРѕРіРѕ СѓСЂРѕРІРЅСЏ.
        """

        self._progress_service = progress_service or SurviveTimedLevelProgressService()

    def resolve_start_level_number(self) -> int:
        """EN: Resolve and persist the survive_timed level number that should start next.
        RU: РћРїСЂРµРґРµР»РёС‚СЊ Рё СЃРѕС…СЂР°РЅРёС‚СЊ РЅРѕРјРµСЂ СѓСЂРѕРІРЅСЏ survive_timed, РєРѕС‚РѕСЂС‹Р№ РґРѕР»Р¶РµРЅ СЃС‚Р°СЂС‚РѕРІР°С‚СЊ СЃР»РµРґСѓСЋС‰РёРј.
        """

        level_number = self._progress_service.resolve_start_level_number()
        set_current_active_level_number(level_number)
        return level_number

    def activate_level(self, level_number: int) -> SurviveTimedLevelProfile:
        """EN: Activate one survive_timed level and return its shipped profile.
        RU: РђРєС‚РёРІРёСЂРѕРІР°С‚СЊ РѕРґРёРЅ СѓСЂРѕРІРµРЅСЊ survive_timed Рё РІРµСЂРЅСѓС‚СЊ РµРіРѕ РІСЃС‚СЂРѕРµРЅРЅС‹Р№ РїСЂРѕС„РёР»СЊ.
        """

        set_current_active_level_number(level_number)
        return get_level_profile(level_number)

    def get_active_profile(self) -> SurviveTimedLevelProfile:
        """EN: Return current active survive_timed profile from session state.
        RU: Р’РµСЂРЅСѓС‚СЊ С‚РµРєСѓС‰РёР№ Р°РєС‚РёРІРЅС‹Р№ РїСЂРѕС„РёР»СЊ survive_timed РёР· session-state.
        """

        return get_level_profile(get_current_active_level_number())
