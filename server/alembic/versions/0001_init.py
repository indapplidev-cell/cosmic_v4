"""init

Revision ID: 0001_init
Revises:
Create Date: 2026-03-06 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """EN: Create initial schema with users, profiles, and balances.
    RU: Создать начальную схему с пользователями, профилями и балансами.
    """
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("psw", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "profile_users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("login", sa.String(length=255), server_default=sa.text("'no data'"), nullable=True),
        sa.Column("phone", sa.String(length=255), server_default=sa.text("'no data'"), nullable=True),
        sa.Column("telegram", sa.String(length=255), server_default=sa.text("'no data'"), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )

    op.create_table(
        "profile_games",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("record", sa.Integer(), server_default=sa.text("0"), nullable=True),
        sa.Column("rating", sa.Integer(), server_default=sa.text("0"), nullable=True),
        sa.Column("balance", sa.Integer(), server_default=sa.text("0"), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )

    op.create_table(
        "balances",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("win", sa.Integer(), server_default=sa.text("0"), nullable=True),
        sa.Column("paid", sa.Integer(), server_default=sa.text("0"), nullable=True),
        sa.Column("date", sa.Date(), server_default=sa.text("'2000-01-01'"), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_balances_user_id", "balances", ["user_id"], unique=False)


def downgrade() -> None:
    """EN: Drop all tables and indexes created by the initial migration.
    RU: Удалить все таблицы и индексы, созданные начальной миграцией.
    """
    op.drop_index("ix_balances_user_id", table_name="balances")
    op.drop_table("balances")
    op.drop_table("profile_games")
    op.drop_table("profile_users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
