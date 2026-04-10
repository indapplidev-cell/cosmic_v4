# -*- coding: utf-8 -*-
"""EN: Local campaign progression service for survive_timed levels.
RU: Р›РѕРєР°Р»СЊРЅС‹Р№ СЃРµСЂРІРёСЃ РєР°РјРїР°РЅРёРё Рё РїСЂРѕРіСЂРµСЃСЃР° СѓСЂРѕРІРЅРµР№ survive_timed.
"""

from __future__ import annotations

from client.infrastructure.storage.gameplay.modes.survive_timed.local_level_progress_store import (
    load_campaign_progress,
    save_campaign_progress,
    save_campaign_progress_snapshot,
)
from shared.constants.survive_timed_levels import get_default_level_number, get_max_level_number


def apply_survive_timed_progress_from_server(progress_payload: object) -> dict | None:
    """EN: Apply one server progress snapshot to local survive_timed storage without merge heuristics.
    RU: РџСЂРёРјРµРЅРёС‚СЊ РѕРґРёРЅ server snapshot РїСЂРѕРіСЂРµСЃСЃР° Рє Р»РѕРєР°Р»СЊРЅРѕРјСѓ survive_timed storage Р±РµР· merge-СЌРІСЂРёСЃС‚РёРє.
    """

    if not isinstance(progress_payload, dict):
        return None
    try:
        return save_campaign_progress_snapshot(
            {
                "last_completed_level_number": int(progress_payload.get("last_completed_level_number", 0) or 0),
                "current_level_number": int(progress_payload.get("current_level_number", get_default_level_number()) or get_default_level_number()),
                "campaign_completed": bool(progress_payload.get("campaign_completed", False)),
                "updated_at": str(progress_payload.get("updated_at", "") or ""),
            }
        )
    except Exception:
        return None


class SurviveTimedLevelProgressService:
    """EN: Resolve start level and persist successful campaign progression for survive_timed.
    RU: РћРїСЂРµРґРµР»СЏС‚СЊ СЃС‚Р°СЂС‚РѕРІС‹Р№ СѓСЂРѕРІРµРЅСЊ Рё СЃРѕС…СЂР°РЅСЏС‚СЊ СѓСЃРїРµС€РЅС‹Р№ РїСЂРѕРіСЂРµСЃСЃ РєР°РјРїР°РЅРёРё survive_timed.
    """

    def get_progress_state(self) -> dict:
        """EN: Return normalized survive_timed campaign progress snapshot.
        RU: Р’РµСЂРЅСѓС‚СЊ РЅРѕСЂРјР°Р»РёР·РѕРІР°РЅРЅС‹Р№ СЃРЅРёРјРѕРє РїСЂРѕРіСЂРµСЃСЃР° РєР°РјРїР°РЅРёРё survive_timed.
        """

        return dict(load_campaign_progress())

    def apply_server_progress(self, progress_payload: object) -> dict | None:
        """EN: Apply one server-authoritative progress snapshot to local storage.
        RU: РџСЂРёРјРµРЅРёС‚СЊ РѕРґРёРЅ server-authoritative snapshot РїСЂРѕРіСЂРµСЃСЃР° Рє Р»РѕРєР°Р»СЊРЅРѕРјСѓ storage.
        """

        return apply_survive_timed_progress_from_server(progress_payload)

    def resolve_start_level_number(self) -> int:
        """EN: Return current survive_timed start level respecting shipped bounds.
        RU: Р’РµСЂРЅСѓС‚СЊ СЃС‚Р°СЂС‚РѕРІС‹Р№ СѓСЂРѕРІРµРЅСЊ survive_timed СЃ СѓС‡С‘С‚РѕРј РіСЂР°РЅРёС† РІСЃС‚СЂРѕРµРЅРЅРѕР№ РєР°РјРїР°РЅРёРё.
        """

        state = load_campaign_progress()
        current = int(state.get("current_level_number", get_default_level_number()) or get_default_level_number())
        return min(max(current, get_default_level_number()), get_max_level_number())

    def record_success(self, level_number: int) -> dict:
        """EN: Persist successful survive_timed completion and advance current level when possible.
        RU: РЎРѕС…СЂР°РЅРёС‚СЊ СѓСЃРїРµС€РЅРѕРµ РїСЂРѕС…РѕР¶РґРµРЅРёРµ survive_timed Рё РїСЂРѕРґРІРёРЅСѓС‚СЊ С‚РµРєСѓС‰РёР№ СѓСЂРѕРІРµРЅСЊ, РєРѕРіРґР° СЌС‚Рѕ РІРѕР·РјРѕР¶РЅРѕ.
        """

        number = min(max(int(level_number), get_default_level_number()), get_max_level_number())
        state = load_campaign_progress()
        last_completed = max(int(state.get("last_completed_level_number", 0) or 0), number)
        if number < get_max_level_number():
            current_level = number + 1
            campaign_completed = bool(state.get("campaign_completed", False))
        else:
            current_level = get_max_level_number()
            campaign_completed = True
        return save_campaign_progress(
            {
                "last_completed_level_number": last_completed,
                "current_level_number": current_level,
                "campaign_completed": campaign_completed,
            }
        )

