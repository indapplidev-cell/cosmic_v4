"""EN: SQLAlchemy model for per-user best score records on individual levels.
RU: SQLAlchemy-модель рекордов пользователя по очкам на отдельных уровнях.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, String, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from server.db.sessions.session_factory import Base

if TYPE_CHECKING:
    from server.db.models.user import User


class UserLevelScoreRecord(Base):
    """EN: Store one score-record row for each `(user_id, level_number)` pair.
    RU: Хранить одну строку рекорда для каждой пары `(user_id, level_number)`.
    """

    __tablename__ = "user_level_score_records"
    __table_args__ = (
        CheckConstraint("level_number >= 1", name="ck_user_level_score_records_level_number"),
        CheckConstraint("best_score >= 0", name="ck_user_level_score_records_best_score"),
        CheckConstraint("last_score >= 0", name="ck_user_level_score_records_last_score"),
        CheckConstraint("runs_count >= 0", name="ck_user_level_score_records_runs_count"),
        Index(
            "ix_user_level_score_records_user_id_level_number",
            "user_id",
            "level_number",
            unique=True,
        ),
        Index(
            "ix_user_level_score_records_level_score_elapsed",
            text("level_number"),
            text("best_score DESC"),
            text("best_elapsed_ms ASC"),
        ),
        Index("ix_user_level_score_records_user_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    level_number: Mapped[int] = mapped_column(Integer, nullable=False)
    best_score: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    best_elapsed_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    best_result: Mapped[str | None] = mapped_column(String(32), nullable=True)
    best_attempts_used: Mapped[int | None] = mapped_column(Integer, nullable=True)
    best_reward_used: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    last_score: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    last_elapsed_ms: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    last_result: Mapped[str] = mapped_column(String(32), nullable=False, server_default="unknown")
    runs_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    user: Mapped["User"] = relationship("User", back_populates="level_score_records")
