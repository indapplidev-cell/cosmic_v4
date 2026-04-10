"""EN: Rating leaderboard DB service.
RU: Сервис БД для таблицы лидерборда рейтинга.
"""

from __future__ import annotations

from sqlalchemy import desc, select

from server.db.sessions.session_factory import get_session
from server.db.models.profile_game import ProfileGame
from server.db.models.profile_user import ProfileUser
from server.db.models.user import User
from server.engine.validation.user_value_normalizer import normalize_user_value_for_output


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
            login_raw = normalize_user_value_for_output(row.get("login"))
            email_raw = (row.get("email") or "").strip()
            user_name = login_raw or email_raw

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
