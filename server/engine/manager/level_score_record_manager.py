"""EN: DB service for per-level user score records and level leaderboards.
RU: Сервис БД для рекордов пользователя по уровням и лидербордов уровня.
"""

from __future__ import annotations

from sqlalchemy import asc, case, desc, func, select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.sql import ColumnElement

from server.db.sessions.session_factory import get_session
from server.db.models.user_level_score_record import UserLevelScoreRecord


def _serialize_mapping(row: dict) -> dict:
    """EN: Normalize SQLAlchemy mapping/row dict into stable plain output fields.
    RU: Нормализовать mapping/row-словарь SQLAlchemy в стабильные поля обычного вывода.
    """

    return {
        "id": int(row["id"]),
        "user_id": int(row["user_id"]),
        "level_number": int(row["level_number"]),
        "best_score": int(row["best_score"] or 0),
        "best_elapsed_ms": None if row["best_elapsed_ms"] is None else int(row["best_elapsed_ms"]),
        "best_result": None if row["best_result"] is None else str(row["best_result"]),
        "best_attempts_used": None
        if row["best_attempts_used"] is None
        else int(row["best_attempts_used"]),
        "best_reward_used": bool(row["best_reward_used"]),
        "last_score": int(row["last_score"] or 0),
        "last_elapsed_ms": int(row["last_elapsed_ms"] or 0),
        "last_result": str(row["last_result"] or "unknown"),
        "runs_count": int(row["runs_count"] or 0),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _serialize_record(row: UserLevelScoreRecord) -> dict:
    """EN: Convert ORM row into a plain serializable dictionary.
    RU: Преобразовать ORM-строку в обычный сериализуемый словарь.
    """

    return _serialize_mapping(
        {
            "id": row.id,
            "user_id": row.user_id,
            "level_number": row.level_number,
            "best_score": row.best_score,
            "best_elapsed_ms": row.best_elapsed_ms,
            "best_result": row.best_result,
            "best_attempts_used": row.best_attempts_used,
            "best_reward_used": row.best_reward_used,
            "last_score": row.last_score,
            "last_elapsed_ms": row.last_elapsed_ms,
            "last_result": row.last_result,
            "runs_count": row.runs_count,
            "created_at": row.created_at,
            "updated_at": row.updated_at,
        }
    )


def _build_is_better_result(insert_stmt) -> ColumnElement[bool]:
    """EN: Build PostgreSQL SQL expression for best-result replacement on conflict.
    RU: Построить PostgreSQL SQL-выражение для замены лучшего результата при конфликте.
    """

    excluded = insert_stmt.excluded
    return (excluded.best_score > UserLevelScoreRecord.best_score) | (
        (excluded.best_score == UserLevelScoreRecord.best_score)
        & (
            UserLevelScoreRecord.best_elapsed_ms.is_(None)
            | (excluded.best_elapsed_ms < UserLevelScoreRecord.best_elapsed_ms)
        )
    )


def get_user_level_score_record(user_id: int, level_number: int) -> dict | None:
    """EN: Return one per-level user score record as a plain dict or `None`.
    RU: Вернуть один рекорд пользователя по уровню в виде словаря или `None`.
    """

    try:
        user_id_value = int(user_id)
        level_number_value = int(level_number)
    except Exception:
        return None
    if user_id_value <= 0 or level_number_value < 1:
        return None

    try:
        with get_session() as session:
            row = session.scalar(
                select(UserLevelScoreRecord).where(
                    UserLevelScoreRecord.user_id == user_id_value,
                    UserLevelScoreRecord.level_number == level_number_value,
                )
            )
            return None if row is None else _serialize_record(row)
    except Exception:
        return None


def upsert_level_score_record(
    *,
    user_id: int,
    level_number: int,
    score: int,
    elapsed_ms: int,
    result: str,
    attempts_used: int | None,
    reward_used: bool,
) -> dict:
    """EN: Atomically upsert one per-level score record via PostgreSQL ON CONFLICT.
    RU: Атомарно вставить или обновить один рекорд по уровню через PostgreSQL ON CONFLICT.
    """

    try:
        user_id_value = int(user_id)
        level_number_value = int(level_number)
        score_value = max(int(score), 0)
        elapsed_ms_value = max(int(elapsed_ms), 0)
        attempts_used_value = None if attempts_used is None else int(attempts_used)
        result_value = str(result or "unknown").strip() or "unknown"
        reward_used_value = bool(reward_used)
    except Exception:
        return {"ok": False, "error": "FORMAT"}

    if user_id_value <= 0 or level_number_value < 1:
        return {"ok": False, "error": "FORMAT"}

    try:
        with get_session() as session:
            insert_stmt = insert(UserLevelScoreRecord).values(
                user_id=user_id_value,
                level_number=level_number_value,
                best_score=score_value,
                best_elapsed_ms=elapsed_ms_value,
                best_result=result_value,
                best_attempts_used=attempts_used_value,
                best_reward_used=reward_used_value,
                last_score=score_value,
                last_elapsed_ms=elapsed_ms_value,
                last_result=result_value,
                runs_count=1,
            )
            is_better_result = _build_is_better_result(insert_stmt)
            stmt = (
                insert_stmt.on_conflict_do_update(
                    index_elements=[
                        UserLevelScoreRecord.user_id,
                        UserLevelScoreRecord.level_number,
                    ],
                    set_={
                        "last_score": insert_stmt.excluded.last_score,
                        "last_elapsed_ms": insert_stmt.excluded.last_elapsed_ms,
                        "last_result": insert_stmt.excluded.last_result,
                        "runs_count": UserLevelScoreRecord.runs_count + 1,
                        "updated_at": func.now(),
                        "best_score": case(
                            (is_better_result, insert_stmt.excluded.best_score),
                            else_=UserLevelScoreRecord.best_score,
                        ),
                        "best_elapsed_ms": case(
                            (is_better_result, insert_stmt.excluded.best_elapsed_ms),
                            else_=UserLevelScoreRecord.best_elapsed_ms,
                        ),
                        "best_result": case(
                            (is_better_result, insert_stmt.excluded.best_result),
                            else_=UserLevelScoreRecord.best_result,
                        ),
                        "best_attempts_used": case(
                            (is_better_result, insert_stmt.excluded.best_attempts_used),
                            else_=UserLevelScoreRecord.best_attempts_used,
                        ),
                        "best_reward_used": case(
                            (is_better_result, insert_stmt.excluded.best_reward_used),
                            else_=UserLevelScoreRecord.best_reward_used,
                        ),
                    },
                )
                .returning(
                    UserLevelScoreRecord.id,
                    UserLevelScoreRecord.user_id,
                    UserLevelScoreRecord.level_number,
                    UserLevelScoreRecord.best_score,
                    UserLevelScoreRecord.best_elapsed_ms,
                    UserLevelScoreRecord.best_result,
                    UserLevelScoreRecord.best_attempts_used,
                    UserLevelScoreRecord.best_reward_used,
                    UserLevelScoreRecord.last_score,
                    UserLevelScoreRecord.last_elapsed_ms,
                    UserLevelScoreRecord.last_result,
                    UserLevelScoreRecord.runs_count,
                    UserLevelScoreRecord.created_at,
                    UserLevelScoreRecord.updated_at,
                    case(
                        (text("xmax = 0"), True),
                        else_=is_better_result,
                    ).label("best_updated"),
                )
            )
            row = session.execute(stmt).mappings().one()
            return {
                "ok": True,
                "record": _serialize_mapping(dict(row)),
                "best_updated": bool(row["best_updated"]),
            }
    except Exception:
        return {"ok": False, "error": "DB_ERROR"}


def get_level_score_leaderboard(level_number: int, limit: int, offset: int = 0) -> list[dict]:
    """EN: Return leaderboard rows for one level ordered by best score, time and age.
    RU: Вернуть строки лидерборда одного уровня с сортировкой по очкам, времени и давности.
    """

    try:
        level_number_value = int(level_number)
        limit_value = max(1, min(int(limit), 500))
        offset_value = max(int(offset), 0)
    except Exception:
        return []
    if level_number_value < 1:
        return []

    try:
        with get_session() as session:
            rows = (
                session.execute(
                    select(UserLevelScoreRecord)
                    .where(UserLevelScoreRecord.level_number == level_number_value)
                    .order_by(
                        desc(UserLevelScoreRecord.best_score),
                        asc(UserLevelScoreRecord.best_elapsed_ms),
                        asc(UserLevelScoreRecord.updated_at),
                    )
                    .limit(limit_value)
                    .offset(offset_value)
                )
                .scalars()
                .all()
            )
            return [_serialize_record(row) for row in rows]
    except Exception:
        return []
