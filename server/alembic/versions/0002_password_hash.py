"""password_hash

Revision ID: 0002_password_hash
Revises: 0001_init
Create Date: 2026-03-07 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

from server.security.passwords import hash_password


# revision identifiers, used by Alembic.
revision = "0002_password_hash"
down_revision = "0001_init"
branch_labels = None
depends_on = None


def _has_column(bind: sa.Connection, table_name: str, column_name: str) -> bool:
    """EN: Return True when the specified table contains the target column.
    RU: Вернуть True, если указанная таблица содержит целевой столбец.
    """

    inspector = sa.inspect(bind)
    return any(column["name"] == column_name for column in inspector.get_columns(table_name))


def upgrade() -> None:
    """EN: Add password_hash, migrate plaintext passwords, then remove old psw column.
    RU: Добавить password_hash, мигрировать plaintext-пароли и удалить старый столбец psw.
    """

    bind = op.get_bind()

    if not _has_column(bind, "users", "password_hash"):
        op.add_column("users", sa.Column("password_hash", sa.Text(), nullable=True))

    if _has_column(bind, "users", "psw"):
        users_table = sa.table(
            "users",
            sa.column("id", sa.BigInteger),
            sa.column("psw", sa.Text),
            sa.column("password_hash", sa.Text),
        )

        rows = bind.execute(
            sa.select(users_table.c.id, users_table.c.psw).where(users_table.c.psw.is_not(None))
        ).fetchall()

        for row in rows:
            bind.execute(
                sa.update(users_table)
                .where(users_table.c.id == row.id)
                .values(password_hash=hash_password(str(row.psw)))
            )

    op.alter_column("users", "password_hash", nullable=False)

    if _has_column(bind, "users", "psw"):
        op.drop_column("users", "psw")


def downgrade() -> None:
    """EN: Recreate psw column for rollback compatibility without restoring original passwords.
    RU: Восстановить столбец psw для технического отката без восстановления исходных паролей.
    """

    bind = op.get_bind()

    if not _has_column(bind, "users", "psw"):
        op.add_column("users", sa.Column("psw", sa.Text(), nullable=True))

    if _has_column(bind, "users", "password_hash"):
        op.drop_column("users", "password_hash")
