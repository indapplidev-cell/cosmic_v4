# -*- coding: utf-8 -*-
"""EN: SQLAlchemy model for one survive_timed campaign progress row per user.
RU: SQLAlchemy-модель одной записи прогресса кампании survive_timed на пользователя.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, CheckConstraint, DateTime, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column

from server.db import Base


class SurviveTimedUserCampaignProgress(Base):
    """EN: Persist one survive_timed campaign progress row for each user.
    RU: Хранить одну запись прогресса кампании survive_timed для каждого пользователя.
    """

    __tablename__ = "survive_timed_user_campaign_progress"
    __table_args__ = (
        CheckConstraint("last_completed_level_number >= 0", name="ck_survive_timed_campaign_last_completed_nonneg"),
        CheckConstraint("current_level_number >= 1", name="ck_survive_timed_campaign_current_level_min"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    last_completed_level_number: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    current_level_number: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    campaign_completed: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())