"""EN: Manual smoke checks for auth service operations.
RU: Ручной smoke-скрипт проверки операций auth-сервиса.
"""

from __future__ import annotations

from sqlalchemy import func, select

from server.db import get_session
from server.models.balance import Balance
from server.models.profile_game import ProfileGame
from server.models.profile_user import ProfileUser
from server.services.auth_service import delete_user, login_user, register_user


def main() -> None:
    """EN: Run simple register/login/delete scenarios and print outcomes.
    RU: Запустить простые сценарии register/login/delete и вывести результаты.
    """
    email = "smoke_user@example.com"
    psw = "SmokePsw#123"

    reg1 = register_user(email, psw)
    print("register #1:", reg1)

    reg2 = register_user(email, psw)
    print("register #2:", reg2)

    login_ok = login_user(email, psw)
    print("login ok:", login_ok)

    login_bad = login_user(email, "Wrong#Pass1")
    print("login bad:", login_bad)

    if not login_ok.get("ok"):
        return

    user_id = int(login_ok["user_id"])

    with get_session() as session:
        pu = session.scalar(select(func.count(ProfileUser.id)).where(ProfileUser.user_id == user_id))
        pg = session.scalar(select(func.count(ProfileGame.id)).where(ProfileGame.user_id == user_id))
        bl = session.scalar(select(func.count(Balance.id)).where(Balance.user_id == user_id))
        print("related rows before delete:", {"profile_user": pu, "profile_game": pg, "balances": bl})

    deleted = delete_user(user_id)
    print("delete:", deleted)

    with get_session() as session:
        pu = session.scalar(select(func.count(ProfileUser.id)).where(ProfileUser.user_id == user_id))
        pg = session.scalar(select(func.count(ProfileGame.id)).where(ProfileGame.user_id == user_id))
        bl = session.scalar(select(func.count(Balance.id)).where(Balance.user_id == user_id))
        print("related rows after delete:", {"profile_user": pu, "profile_game": pg, "balances": bl})


if __name__ == "__main__":
    main()

