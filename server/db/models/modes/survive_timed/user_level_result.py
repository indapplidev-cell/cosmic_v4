# -*- coding: utf-8 -*-
"""EN: SQLAlchemy model for per-user survive_timed level results.
RU: SQLAlchemy-модель результатов survive_timed по уровням на пользователя.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from server.db.sessions.session_factory import Base


class SurviveTimedUserLevelResult(Base):
    """EN: Persist one survive_timed result row for each `(user_id, level_number)` pair.
    RU: Хранить одну запись результата survive_timed для каждой пары `(user_id, level_number)`.
    """

    __tablename__ = "survive_timed_user_level_results"
    __table_args__ = (
        CheckConstraint("level_number >= 1", name="ck_survive_timed_results_level_min"),
        CheckConstraint("best_survival_ms >= 0", name="ck_survive_timed_results_best_nonneg"),
        CheckConstraint("last_survival_ms >= 0", name="ck_survive_timed_results_last_nonneg"),
        CheckConstraint("attempts_count >= 0", name="ck_survive_timed_results_attempts_nonneg"),
        CheckConstraint("completed_count >= 0", name="ck_survive_timed_results_completed_nonneg"),
        Index("ix_survive_timed_results_user_level", "user_id", "level_number", unique=True),
        Index("ix_survive_timed_results_user_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    level_number: Mapped[int] = mapped_column(Integer, nullable=False)
    best_survival_ms: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    last_survival_ms: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    attempts_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    completed_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    last_result: Mapped[str] = mapped_column(String(32), nullable=False, server_default="unknown")
    first_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
