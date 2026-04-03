# -*- coding: utf-8 -*-
"""EN: Local campaign progression service for survive_timed levels.
RU: Локальный сервис кампании и прогресса уровней survive_timed.
"""

from __future__ import annotations

from data.gameplay.modes.survive_timed.local_level_progress_store import (
    load_campaign_progress,
    save_campaign_progress,
    save_campaign_progress_snapshot,
)
from engine.modes.survive_timed.registry import get_default_level_number, get_max_level_number


def apply_survive_timed_progress_from_server(progress_payload: object) -> dict | None:
    """EN: Apply one server progress snapshot to local survive_timed storage without merge heuristics.
    RU: Применить один server snapshot прогресса к локальному survive_timed storage без merge-эвристик.
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
    RU: Определять стартовый уровень и сохранять успешный прогресс кампании survive_timed.
    """

    def get_progress_state(self) -> dict:
        """EN: Return normalized survive_timed campaign progress snapshot.
        RU: Вернуть нормализованный снимок прогресса кампании survive_timed.
        """

        return dict(load_campaign_progress())

    def apply_server_progress(self, progress_payload: object) -> dict | None:
        """EN: Apply one server-authoritative progress snapshot to local storage.
        RU: Применить один server-authoritative snapshot прогресса к локальному storage.
        """

        return apply_survive_timed_progress_from_server(progress_payload)

    def resolve_start_level_number(self) -> int:
        """EN: Return current survive_timed start level respecting shipped bounds.
        RU: Вернуть стартовый уровень survive_timed с учётом границ встроенной кампании.
        """

        state = load_campaign_progress()
        current = int(state.get("current_level_number", get_default_level_number()) or get_default_level_number())
        return min(max(current, get_default_level_number()), get_max_level_number())

    def record_success(self, level_number: int) -> dict:
        """EN: Persist successful survive_timed completion and advance current level when possible.
        RU: Сохранить успешное прохождение survive_timed и продвинуть текущий уровень, когда это возможно.
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
