"""EN: SQLAlchemy model for one-time Telegram Mini App verification sessions by purpose.
RU: SQLAlchemy-модель одноразовых Telegram Mini App verification-сессий по назначению.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from server.db.sessions.session_factory import Base


class PayoutMiniAppSession(Base):
    """EN: Persist one-time Telegram Mini App verification sessions per authenticated user and purpose.
    RU: Хранить одноразовые Telegram Mini App verification-сессии для авторизованного пользователя и purpose.

    EN: Only the hashed opaque session token is stored in DB. Verified session state is
    bound to the Telegram user id extracted from server-validated WebApp initData, while
    `purpose` separates trusted flows such as `payout` and `telegram_link`.
    RU: В БД хранится только хеш непрозрачного session-токена. Состояние verified
    жёстко привязывается к Telegram user id, извлечённому из server-validated WebApp initData,
    а `purpose` разделяет доверенные потоки вроде `payout` и `telegram_link`.
    """

    __tablename__ = "payout_miniapp_sessions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    purpose: Mapped[str] = mapped_column(Text, nullable=False, server_default="payout", index=True)
    session_token_hash: Mapped[str] = mapped_column(Text, nullable=False, unique=True, index=True)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="issued", index=True)
    telegram_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    telegram_username: Mapped[str | None] = mapped_column(Text, nullable=True)
    init_data_hash: Mapped[str | None] = mapped_column(Text, nullable=True)
    tg_auth_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    fail_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
