"""EN: One-time Telegram link token model (code stored as hash only).
RU: Модель одноразовых токенов привязки Telegram (код хранится только в виде хеша).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from server.db.sessions.session_factory import Base


class TelegramLinkToken(Base):
    """EN: Stores hashed temporary link codes used by bot `/link <code>` confirmation.
    RU: Хранит хешированные временные коды привязки для подтверждения через `/link <код>` в боте.
    """

    __tablename__ = "telegram_link_tokens"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    code_hash: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    expected_tg_username: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    telegram_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    used: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false", index=True)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
