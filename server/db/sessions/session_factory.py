"""EN: SQLAlchemy engine/session/base setup for server persistence.
RU: Настройка SQLAlchemy engine/session/base для серверного слоя хранения.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from server.app.config.settings import DATABASE_URL


engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=1800,
    pool_timeout=10,
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    future=True,
)

Base = declarative_base()


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """EN: Yield transactional session and handle commit/rollback automatically.
    RU: Выдать транзакционную сессию и автоматически обработать commit/rollback.
    """
    session: Session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
