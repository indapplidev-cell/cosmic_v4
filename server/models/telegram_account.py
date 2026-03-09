"""EN: Telegram account linkage model verified by one-time bot confirmation code.
RU: Модель привязки Telegram-аккаунта, подтверждаемая одноразовым кодом через бота.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from server.db import Base


class TelegramAccount(Base):
    """EN: Stores verified one-to-one binding between app user and telegram_user_id.
    RU: Хранит подтвержденную связь один-к-одному между пользователем приложения и telegram_user_id.
    """

    __tablename__ = "telegram_accounts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True, index=True)
    verified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

