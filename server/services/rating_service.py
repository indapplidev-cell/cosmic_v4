"""EN: Rating leaderboard DB service.
RU: Сервис БД для таблицы лидерборда рейтинга.
"""

from __future__ import annotations

from sqlalchemy import desc, select

from server.db import get_session
from server.models.profile_game import ProfileGame
from server.models.profile_user import ProfileUser
from server.models.user import User


def get_top_ratings(limit: int = 100) -> list[dict]:
    """EN: Return top users by rating/record as plain dict list.
    RU: Вернуть топ пользователей по rating/record в виде списка словарей.
    """
    try:
        limit_value = int(limit)
    except Exception:
        limit_value = 100
    limit_value = max(1, min(limit_value, 100))

    try:
        with get_session() as session:
            stmt = (
                select(
                    User.id.label("user_id"),
                    User.email.label("email"),
                    ProfileUser.login.label("login"),
                    ProfileGame.record.label("record"),
                    ProfileGame.rating.label("rating"),
                )
                .select_from(ProfileGame)
                .join(User, User.id == ProfileGame.user_id)
                .outerjoin(ProfileUser, ProfileUser.user_id == User.id)
                .order_by(
                    desc(ProfileGame.rating),
                    desc(ProfileGame.record),
                    User.id.asc(),
                )
                .limit(limit_value)
            )
            rows = session.execute(stmt).mappings().all()

        result: list[dict] = []
        for row in rows:
            login_raw = (row.get("login") or "").strip()
            email_raw = (row.get("email") or "").strip()
            user_name = login_raw if login_raw and login_raw != "no data" else email_raw

            try:
                record_value = int(row.get("record") or 0)
            except Exception:
                record_value = 0
            try:
                rating_value = int(row.get("rating") or 0)
            except Exception:
                rating_value = 0

            result.append(
                {
                    "user": str(user_name or ""),
                    "record": record_value,
                    "rating": rating_value,
                }
            )
        return result
    except Exception:
        return []
