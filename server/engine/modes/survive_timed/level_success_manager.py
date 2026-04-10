"""EN: Atomic survive_timed success orchestration across result and campaign progress.
RU: РђС‚РѕРјР°СЂРЅР°СЏ orchestration СѓСЃРїРµС…Р° survive_timed РјРµР¶РґСѓ result Рё campaign progress.
"""

from __future__ import annotations

from datetime import datetime

from server.db.sessions.session_factory import get_session
from server.engine.modes.survive_timed.campaign_progress_manager import (
    _apply_level_success,
    _get_or_create_progress,
    _serialize_progress,
)
from server.engine.modes.survive_timed.level_result_manager import (
    _apply_level_result,
    _get_or_create_result,
    _serialize_result,
)
from shared.constants.survive_timed_levels import get_max_level_number


def record_survive_timed_level_success(user_id: int, level_number: int, survival_ms: int) -> dict:
    """EN: Persist one survive_timed success atomically and return both result and progress snapshots.
    RU: РђС‚РѕРјР°СЂРЅРѕ СЃРѕС…СЂР°РЅРёС‚СЊ РѕРґРёРЅ СѓСЃРїРµС… survive_timed Рё РІРµСЂРЅСѓС‚СЊ snapshots result Рё progress.
    """

    try:
        user_id_value = int(user_id)
        level_number_value = int(level_number)
        survival_ms_value = max(int(survival_ms), 0)
    except Exception:
        return {"ok": False, "error": "FORMAT"}
    if user_id_value <= 0 or level_number_value < 1 or level_number_value > int(get_max_level_number()):
        return {"ok": False, "error": "FORMAT"}

    try:
        with get_session() as session:
            completed_at = datetime.utcnow()
            result_row = _get_or_create_result(session, user_id_value, level_number_value)
            _apply_level_result(result_row, survival_ms=survival_ms_value, result="success", completed_at=completed_at)
            progress_row = _get_or_create_progress(session, user_id_value)
            _apply_level_success(progress_row, level_number_value)
            session.add(result_row)
            session.add(progress_row)
            session.flush()
            return {
                "ok": True,
                "result": _serialize_result(result_row),
                "progress": _serialize_progress(progress_row),
            }
    except Exception:
        return {"ok": False, "error": "DB_ERROR"}

