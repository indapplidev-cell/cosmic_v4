"""EN: SQLAlchemy model for one-time payout deep-link codes.
RU: SQLAlchemy-модель одноразовых payout deep-link кодов.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from server.db.sessions.session_factory import Base


class PayoutLinkCode(Base):
    """EN: Store hashed one-time payout link codes issued from the app.
    RU: Хранить хешированные одноразовые payout link-коды, выдаваемые из приложения.

    EN: Only the hash is stored in DB. The plaintext code is returned once to the
    authenticated client and later consumed by the payout bot acknowledgement flow.
    RU: В БД хранится только хеш. Открытый код один раз возвращается
    аутентифицированному клиенту и затем поглощается payout-ботом через ack flow.
    """

    __tablename__ = "payout_link_codes"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    code_hash: Mapped[str] = mapped_column(Text, nullable=False, unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    purpose: Mapped[str] = mapped_column(String(32), nullable=False, server_default="payout")
