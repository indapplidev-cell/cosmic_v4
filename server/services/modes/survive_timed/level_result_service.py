"""EN: DB service for per-level survive_timed result rows.
RU: Сервис БД для построчных результатов survive_timed по уровням.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select

from engine.modes.survive_timed.registry import get_max_level_number
from server.db import get_session
from server.models.modes.survive_timed.user_level_result import SurviveTimedUserLevelResult


def _serialize_result(row: SurviveTimedUserLevelResult) -> dict:
    """EN: Convert ORM result row into a stable plain dictionary.
    RU: Преобразовать ORM-строку результата в стабильный обычный словарь.
    """
    return {
        "user_id": int(row.user_id),
        "level_number": int(row.level_number),
        "best_survival_ms": int(row.best_survival_ms or 0),
        "last_survival_ms": int(row.last_survival_ms or 0),
        "attempts_count": int(row.attempts_count or 0),
        "completed_count": int(row.completed_count or 0),
        "last_result": str(row.last_result or "fail"),
        "first_completed_at": row.first_completed_at,
        "last_completed_at": row.last_completed_at,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def _get_or_create_result(session, user_id: int, level_number: int) -> SurviveTimedUserLevelResult:
    """EN: Return existing survive_timed level-result row or create a default one.
    RU: Вернуть существующую строку результата survive_timed или создать дефолтную.
    """
    row = session.scalar(
        select(SurviveTimedUserLevelResult).where(
            SurviveTimedUserLevelResult.user_id == int(user_id),
            SurviveTimedUserLevelResult.level_number == int(level_number),
        )
    )
    if row is not None:
        return row
    row = SurviveTimedUserLevelResult(
        user_id=int(user_id),
        level_number=int(level_number),
        best_survival_ms=0,
        last_survival_ms=0,
        attempts_count=0,
        completed_count=0,
        last_result="fail",
    )
    session.add(row)
    session.flush()
    return row


def _apply_level_result(
    row: SurviveTimedUserLevelResult,
    *,
    survival_ms: int,
    result: str,
    completed_at: datetime | None = None,
) -> None:
    """EN: Apply one survive_timed result mutation to an already loaded ORM row.
    RU: Применить одно изменение результата survive_timed к уже загруженной ORM-строке.
    """

    survival_ms_value = max(int(survival_ms), 0)
    result_value = str(result or "fail").strip().lower()
    row.attempts_count = int(row.attempts_count or 0) + 1
    row.last_survival_ms = survival_ms_value
    row.best_survival_ms = max(int(row.best_survival_ms or 0), survival_ms_value)
    row.last_result = result_value
    if result_value == "success":
        row.completed_count = int(row.completed_count or 0) + 1
        now = completed_at or datetime.utcnow()
        if row.first_completed_at is None:
            row.first_completed_at = now
        row.last_completed_at = now


def get_level_result(user_id: int, level_number: int) -> dict:
    """EN: Return one survive_timed result row for the given user and level.
    RU: Вернуть одну строку результата survive_timed для пользователя и уровня.
    """
    try:
        user_id_value = int(user_id)
        level_number_value = int(level_number)
    except Exception:
        return {"ok": False, "error": "FORMAT"}
    if user_id_value <= 0 or level_number_value < 1:
        return {"ok": False, "error": "FORMAT"}
    try:
        with get_session() as session:
            row = session.scalar(
                select(SurviveTimedUserLevelResult).where(
                    SurviveTimedUserLevelResult.user_id == user_id_value,
                    SurviveTimedUserLevelResult.level_number == level_number_value,
                )
            )
            return {"ok": True, "result": None if row is None else _serialize_result(row)}
    except Exception:
        return {"ok": False, "error": "DB_ERROR"}


def get_all_level_results(user_id: int) -> dict:
    """EN: Return all survive_timed level-result rows for the authenticated user.
    RU: Вернуть все строки результатов survive_timed для аутентифицированного пользователя.
    """
    try:
        user_id_value = int(user_id)
    except Exception:
        return {"ok": False, "error": "FORMAT"}
    if user_id_value <= 0:
        return {"ok": False, "error": "FORMAT"}
    try:
        with get_session() as session:
            rows = session.scalars(
                select(SurviveTimedUserLevelResult)
                .where(SurviveTimedUserLevelResult.user_id == user_id_value)
                .order_by(SurviveTimedUserLevelResult.level_number.asc())
            ).all()
            return {"ok": True, "results": [_serialize_result(row) for row in rows]}
    except Exception:
        return {"ok": False, "error": "DB_ERROR"}


def upsert_level_result(user_id: int, level_number: int, survival_ms: int, result: str) -> dict:
    """EN: Upsert one survive_timed level result with attempts and completion counters.
    RU: Обновить или создать результат уровня survive_timed со счётчиками попыток и прохождений.
    """
    try:
        user_id_value = int(user_id)
        level_number_value = int(level_number)
        survival_ms_value = max(int(survival_ms), 0)
        result_value = str(result or "fail").strip().lower()
    except Exception:
        return {"ok": False, "error": "FORMAT"}
    if user_id_value <= 0 or level_number_value < 1 or level_number_value > int(get_max_level_number()):
        return {"ok": False, "error": "FORMAT"}
    if result_value not in {"success", "fail"}:
        return {"ok": False, "error": "FORMAT"}
    try:
        with get_session() as session:
            row = _get_or_create_result(session, user_id_value, level_number_value)
            _apply_level_result(row, survival_ms=survival_ms_value, result=result_value)
            session.add(row)
            session.flush()
            return {"ok": True, "result": _serialize_result(row)}
    except Exception:
        return {"ok": False, "error": "DB_ERROR"}
