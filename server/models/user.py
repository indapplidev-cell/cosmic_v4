"""EN: User model with credentials and profile/statistics relations.
RU: Модель пользователя с учётными данными и связями профиля/статистики.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from server.db import Base

if TYPE_CHECKING:
    from server.models.balance import Balance
    from server.models.profile_game import ProfileGame
    from server.models.profile_user import ProfileUser


class User(Base):
    """EN: Primary user table with unique email and password string field.
    RU: Основная таблица пользователей с уникальным email и строковым полем пароля.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(Text, unique=True, index=True, nullable=False)
    psw: Mapped[str] = mapped_column(Text, nullable=False)

    profile_user: Mapped["ProfileUser"] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    profile_game: Mapped["ProfileGame"] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    balances: Mapped[list["Balance"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
