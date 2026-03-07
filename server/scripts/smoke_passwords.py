"""EN: Smoke checks for password hashing behavior and users schema.
RU: Smoke-проверки поведения хеширования паролей и схемы таблицы users.
"""

from __future__ import annotations

from uuid import uuid4

from sqlalchemy import inspect, select

from server.db import get_session
from server.models.user import User
from server.services.auth_service import delete_user, login_user, register_user


def main() -> None:
    """EN: Validate register/login flow and users columns for password_hash migration.
    RU: Проверить flow register/login и столбцы users после миграции на password_hash.
    """

    email = f"smoke_pwd_{uuid4().hex[:10]}@example.com"
    psw = "SmokePsw#123"

    reg_result = register_user(email, psw)
    print("register:", reg_result)
    if not reg_result.get("ok"):
        return

    user_id = int(reg_result["user_id"])

    with get_session() as session:
        inspector = inspect(session.bind)
        user_columns = {column["name"] for column in inspector.get_columns("users")}
        has_psw_column = "psw" in user_columns
        has_password_hash_column = "password_hash" in user_columns

        user = session.scalar(select(User).where(User.id == user_id))
        hash_looks_bcrypt = bool(user and user.password_hash.startswith("$2"))

        print(
            "users columns:",
            {
                "has_psw": has_psw_column,
                "has_password_hash": has_password_hash_column,
            },
        )
        print("password hash prefix check:", {"is_bcrypt_like": hash_looks_bcrypt})

    login_result = login_user(email, psw)
    print("login:", login_result)

    delete_result = delete_user(user_id)
    print("delete:", delete_result)


if __name__ == "__main__":
    main()
