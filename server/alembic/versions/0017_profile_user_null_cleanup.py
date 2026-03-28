"""profile_users nullable cleanup

Revision ID: 0017_profile_user_null_cleanup
Revises: 0016_user_level_score_records
Create Date: 2026-03-26 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0017_profile_user_null_cleanup"
down_revision = "0016_user_level_score_records"
branch_labels = None
depends_on = None


_LEGACY_TEXT_VALUES = ("no data", "нет данных", "new_login", "none", "null", "")


def _cleanup_profile_user_column(column_name: str) -> None:
    """EN: Normalize legacy placeholder literals to NULL for one profile_users text column.
    RU: Нормализовать legacy-строки-заглушки в NULL для одного текстового поля profile_users.
    """

    placeholders = ", ".join(f"'{value}'" for value in _LEGACY_TEXT_VALUES)
    op.execute(
        sa.text(
            f"""
            UPDATE profile_users
            SET {column_name} = NULL
            WHERE lower(btrim(COALESCE({column_name}, ''))) IN ({placeholders})
            """
        )
    )


def upgrade() -> None:
    """EN: Drop placeholder defaults and backfill legacy placeholder values to NULL.
    RU: Убрать placeholder-defaults и перевести legacy placeholder-значения в NULL.
    """

    for column_name in ("login", "phone", "telegram"):
        op.alter_column("profile_users", column_name, server_default=None, existing_type=sa.Text(), existing_nullable=True)
        _cleanup_profile_user_column(column_name)


def downgrade() -> None:
    """EN: Restore historical placeholder defaults used before cleanup migration.
    RU: Вернуть исторические placeholder-defaults, использовавшиеся до cleanup-миграции.
    """

    for column_name in ("login", "phone", "telegram"):
        op.alter_column(
            "profile_users",
            column_name,
            server_default=sa.text("'no data'"),
            existing_type=sa.Text(),
            existing_nullable=True,
        )
