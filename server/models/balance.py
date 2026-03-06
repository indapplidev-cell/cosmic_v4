"""EN: One-to-many balance history model.
RU: Модель истории баланса один-ко-многим.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import BigInteger, Date, ForeignKey, Integer, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from server.db import Base


class Balance(Base):
    """EN: Stores win/paid/date records linked to a single user.
    RU: Хранит записи win/paid/date, связанные с конкретным пользователем.
    """

    __tablename__ = "balances"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    win: Mapped[int | None] = mapped_column(Integer, nullable=True, server_default=text("0"))
    paid: Mapped[int | None] = mapped_column(Integer, nullable=True, server_default=text("0"))
    date: Mapped[date | None] = mapped_column(Date, nullable=True, server_default=text("'2000-01-01'"))

    user = relationship("User", back_populates="balances")
