"""EN: DB service for survive_timed campaign progress per authenticated user.
RU: Сервис БД для прогресса кампании survive_timed по аутентифицированному пользователю.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select

from engine.modes.survive_timed.registry import get_default_level_number, get_max_level_number
from server.db import get_session
from server.models.modes.survive_timed.user_campaign_progress import SurviveTimedUserCampaignProgress


def _serialize_progress(row: SurviveTimedUserCampaignProgress) -> dict:
    """EN: Convert ORM progress row into stable plain output.
    RU: Преобразовать ORM-строку прогресса в стабильный обычный словарь.
    """
    return {
        "user_id": int(row.user_id),
        "last_completed_level_number": int(row.last_completed_level_number or 0),
        "current_level_number": int(row.current_level_number or get_default_level_number()),
        "campaign_completed": bool(row.campaign_completed),
        "completed_at": row.completed_at,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def _get_or_create_progress(session, user_id: int) -> SurviveTimedUserCampaignProgress:
    """EN: Return existing survive_timed campaign progress row or create a default one.
    RU: Вернуть существующую строку прогресса survive_timed или создать дефолтную.
    """
    row = session.scalar(
        select(SurviveTimedUserCampaignProgress).where(SurviveTimedUserCampaignProgress.user_id == int(user_id))
    )
    if row is not None:
        return row
    row = SurviveTimedUserCampaignProgress(
        user_id=int(user_id),
        last_completed_level_number=0,
        current_level_number=int(get_default_level_number()),
        campaign_completed=False,
    )
    session.add(row)
    session.flush()
    return row


def _apply_level_success(row: SurviveTimedUserCampaignProgress, level_number: int) -> None:
    """EN: Apply one level-success mutation without regressing already unlocked campaign state.
    RU: Применить одно изменение успеха уровня без отката уже открытого состояния кампании.
    """

    level_number_value = int(level_number)
    max_level = int(get_max_level_number())
    row.last_completed_level_number = max(int(row.last_completed_level_number or 0), level_number_value)
    if bool(row.campaign_completed) or int(row.last_completed_level_number or 0) >= max_level:
        row.last_completed_level_number = max_level
        row.current_level_number = max_level
        row.campaign_completed = True
        if row.completed_at is None:
            row.completed_at = datetime.utcnow()
        return
    row.current_level_number = max(int(row.current_level_number or get_default_level_number()), level_number_value + 1)
    row.campaign_completed = False


def get_campaign_progress(user_id: int) -> dict:
    """EN: Return survive_timed campaign progress, creating the default row on first access.
    RU: Вернуть прогресс кампании survive_timed, создавая дефолтную запись при первом доступе.
    """
    try:
        user_id_value = int(user_id)
    except Exception:
        return {"ok": False, "error": "FORMAT"}
    if user_id_value <= 0:
        return {"ok": False, "error": "FORMAT"}
    try:
        with get_session() as session:
            row = _get_or_create_progress(session, user_id_value)
            return {"ok": True, "progress": _serialize_progress(row)}
    except Exception:
        return {"ok": False, "error": "DB_ERROR"}


def record_level_success(user_id: int, level_number: int) -> dict:
    """EN: Mark one survive_timed level as completed and advance current level safely.
    RU: Отметить уровень survive_timed как пройденный и безопасно продвинуть текущий уровень.
    """
    try:
        user_id_value = int(user_id)
        level_number_value = int(level_number)
    except Exception:
        return {"ok": False, "error": "FORMAT"}

    max_level = int(get_max_level_number())
    if user_id_value <= 0 or level_number_value < 1 or level_number_value > max_level:
        return {"ok": False, "error": "FORMAT"}

    try:
        with get_session() as session:
            row = _get_or_create_progress(session, user_id_value)
            _apply_level_success(row, level_number_value)
            session.add(row)
            session.flush()
            return {"ok": True, "progress": _serialize_progress(row)}
    except Exception:
        return {"ok": False, "error": "DB_ERROR"}
