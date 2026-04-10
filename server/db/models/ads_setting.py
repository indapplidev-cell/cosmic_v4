"""EN: SQLAlchemy model for global ads mediation settings singleton.
RU: SQLAlchemy-модель singleton-настроек глобальной ads-медиации.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from server.db.sessions.session_factory import Base


class AdsSetting(Base):
    """EN: Store one global row with provider/unit ids and mediation toggles.
    RU: Хранить одну глобальную строку с провайдером, unit id и флагами медиации.
    """

    __tablename__ = "ads_settings"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    provider: Mapped[str] = mapped_column(String(32), nullable=False, server_default="dummy")
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    banner_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    rewarded_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    admob_app_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    banner_topbar_world: Mapped[str | None] = mapped_column(Text, nullable=True)
    banner_topbar_cis: Mapped[str | None] = mapped_column(Text, nullable=True)
    rewarded_gameover_world: Mapped[str | None] = mapped_column(Text, nullable=True)
    rewarded_gameover_cis: Mapped[str | None] = mapped_column(Text, nullable=True)
    refresh_sec: Mapped[int] = mapped_column(Integer, nullable=False, server_default="30")
    min_banner_sec: Mapped[int] = mapped_column(Integer, nullable=False, server_default="5")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
