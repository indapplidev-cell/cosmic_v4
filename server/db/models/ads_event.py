"""EN: SQLAlchemy model for persisted client ads diagnostics events.
RU: SQLAlchemy-модель для сохранения клиентских ads-событий диагностики.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, BigInteger, Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from server.db.sessions.session_factory import Base


class AdsEvent(Base):
    """EN: Persist banner/rewarded events reported by authenticated clients.
    RU: Сохранять banner/rewarded события, присылаемые аутентифицированными клиентами.
    """

    __tablename__ = "ads_events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    screen: Mapped[str] = mapped_column(String(32), nullable=False, server_default="Unknown")
    placement: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    event: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    flow_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    ok: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    meta: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict, server_default="{}")
