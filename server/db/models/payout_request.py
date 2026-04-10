"""EN: SQLAlchemy model for internal payout requests with reserved user balance.
RU: SQLAlchemy-модель внутренних payout request с резервированием пользовательского баланса.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Numeric, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from server.db.sessions.session_factory import Base


class PayoutRequest(Base):
    """EN: Persist internal payout request state before any external provider transfer starts.
    RU: Хранить состояние внутреннего payout request до запуска любого внешнего provider-transfer.

    EN: This row is created only after Mini App verification is consumed and the requested
    amount is moved from available balance into reserved balance.
    RU: Эта запись создаётся только после consume Mini App verification и переноса
    запрошенной суммы из available balance в reserved balance.
    """

    __tablename__ = "payout_requests"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    wallet_address: Mapped[str] = mapped_column(Text, nullable=False)
    asset_code: Mapped[str] = mapped_column(Text, nullable=False, server_default="USDT")
    amount: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="reserved", index=True)
    miniapp_session_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("payout_miniapp_sessions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
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
    fail_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
