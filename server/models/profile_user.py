"""EN: One-to-one personal profile model for user-facing fields.
RU: Модель персонального профиля один-к-одному для пользовательских полей.
"""

from __future__ import annotations

from sqlalchemy import ForeignKey, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from server.db import Base


class ProfileUser(Base):
    """EN: Stores login/phone/telegram for exactly one user.
    RU: Хранит login/phone/telegram ровно для одного пользователя.
    """

    __tablename__ = "profile_users"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    login: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        server_default=text("'no data'"),
    )
    phone: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        server_default=text("'no data'"),
    )
    telegram: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        server_default=text("'no data'"),
    )

    user = relationship("User", back_populates="profile_user", uselist=False)
