"""EN: One-to-one game profile model with aggregate game metrics.
RU: Модель игрового профиля один-к-одному с агрегированными игровыми метриками.
"""

from __future__ import annotations

from sqlalchemy import BigInteger, ForeignKey, Integer, Numeric, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from server.db import Base


class ProfileGame(Base):
    """EN: Stores record/rating/balance summary for exactly one user.
    RU: Хранит сводные record/rating/balance ровно для одного пользователя.
    """

    __tablename__ = "profile_games"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    record: Mapped[int | None] = mapped_column(Integer, nullable=True, server_default=text("0"))
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True, server_default=text("0"))
    balance: Mapped[float | None] = mapped_column(Numeric(12, 3), nullable=True, server_default=text("0"))
    reserved_balance: Mapped[float | None] = mapped_column(Numeric(12, 3), nullable=True, server_default=text("0"))

    user = relationship("User", back_populates="profile_game", uselist=False)
