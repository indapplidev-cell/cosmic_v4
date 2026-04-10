"""EN: SQLAlchemy model for persisted Telegram account binding metadata.
RU: SQLAlchemy-модель для постоянного хранения данных привязки Telegram-аккаунта.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from server.db.sessions.session_factory import Base


class TelegramAccount(Base):
    """EN: Stores one-to-one mapping between app user and verified Telegram account.
    RU: Хранит связь один-к-одному между пользователем приложения и подтверждённым Telegram-аккаунтом.

    EN: The table keeps Telegram identity attributes used by server-side checks:
    telegram_user_id uniqueness protects against linking one Telegram account to different users,
    while user_id uniqueness enforces exactly one Telegram binding per app user.
    RU: Таблица хранит Telegram-атрибуты, используемые серверными проверками:
    уникальность telegram_user_id защищает от привязки одного Telegram к разным пользователям,
    а уникальность user_id гарантирует ровно одну Telegram-привязку на пользователя приложения.
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
    telegram_username: Mapped[str | None] = mapped_column(Text, nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
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

    user = relationship("User", back_populates="telegram_account")
