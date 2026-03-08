"""profile_game_balance_numeric

Revision ID: 0003_pg_balance_num
Revises: 0002_password_hash
Create Date: 2026-03-08 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0003_pg_balance_num"
down_revision = "0002_password_hash"
branch_labels = None
depends_on = None


def _has_table(bind: sa.Connection, table_name: str) -> bool:
    """EN: Return True when target table exists.
    RU: Вернуть True, если целевая таблица существует.
    """

    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def _get_column_type(bind: sa.Connection, table_name: str, column_name: str) -> str | None:
    """EN: Return lowercase SQLAlchemy type string for a table column.
    RU: Вернуть строковое представление типа столбца в нижнем регистре.
    """

    inspector = sa.inspect(bind)
    for column in inspector.get_columns(table_name):
        if column.get("name") == column_name:
            return str(column.get("type", "")).lower()
    return None


def upgrade() -> None:
    """EN: Convert profile_games.balance to Numeric(12,3) for fractional payouts.
    RU: Перевести profile_games.balance в Numeric(12,3) для дробных выплат.
    """

    bind = op.get_bind()
    if not _has_table(bind, "profile_games"):
        return

    current_type = _get_column_type(bind, "profile_games", "balance")
    if current_type is None:
        return

    if "numeric" in current_type:
        return

    op.alter_column(
        "profile_games",
        "balance",
        existing_type=sa.Integer(),
        type_=sa.Numeric(12, 3),
        postgresql_using="balance::numeric(12,3)",
        existing_nullable=True,
    )


def downgrade() -> None:
    """EN: Revert profile_games.balance to Integer for schema rollback.
    RU: Вернуть profile_games.balance к Integer для технического отката схемы.
    """

    bind = op.get_bind()
    if not _has_table(bind, "profile_games"):
        return

    current_type = _get_column_type(bind, "profile_games", "balance")
    if current_type is None:
        return

    if "integer" in current_type or "int" in current_type:
        return

    op.alter_column(
        "profile_games",
        "balance",
        existing_type=sa.Numeric(12, 3),
        type_=sa.Integer(),
        postgresql_using="round(balance)::integer",
        existing_nullable=True,
    )
