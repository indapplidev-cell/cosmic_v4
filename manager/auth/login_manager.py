"""EN: Login verification manager.
RU: Менеджер проверки входа.
"""

from __future__ import annotations

from data.user_cache.user_cache_reader import is_credentials_valid


class LoginManager:
    """EN: Validate login credentials against cached user data.
    RU: Проверять учётные данные входа по сохранённому кэшу.
    """

    @staticmethod
    def check(email: str, password: str) -> bool:
        """EN: Return True if cached credentials match.
        RU: Вернуть True, если сохранённые данные совпадают.
        """
        return is_credentials_valid(email, password)
