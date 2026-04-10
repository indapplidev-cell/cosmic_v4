"""EN: One-to-one personal profile model for user-facing fields.
RU: Модель персонального профиля один-к-одному для пользовательских полей.
"""

from __future__ import annotations

from sqlalchemy import BigInteger, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from server.db.sessions.session_factory import Base


class ProfileUser(Base):
    """EN: Stores login/phone/telegram for exactly one user.
    RU: Хранит login/phone/telegram ровно для одного пользователя.
    """

    __tablename__ = "profile_users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    login: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    phone: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    telegram: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    user = relationship("User", back_populates="profile_user", uselist=False)
