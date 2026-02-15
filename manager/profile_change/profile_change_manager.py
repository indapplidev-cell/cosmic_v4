"""EN: Profile change manager for user cache updates.
RU: Менеджер изменения профиля для обновления user_cache.
"""

from __future__ import annotations

from data.user_cache.user_cache_reader import get_user_cache
from data.user_cache.user_cache_writer import update_user_cache_fields
from data.user_cache.user_session import UserSession
from manager.lang.lang_manager import t


class ProfileChangeManager:
    """EN: Provide profile data and apply selected updates.
    RU: Предоставлять данные профиля и применять выбранные изменения.
    """

    def load_current_user_data(self) -> dict:
        """EN: Load current user cache data with defaults.
        RU: Загрузить текущие данные пользователя с дефолтами.
        """
        cache = get_user_cache() or {}
        no_data = t("common.no_data")
        return {
            "login": cache.get("login") or no_data,
            "email": cache.get("email") or no_data,
            "phone": cache.get("phone") or no_data,
            "tg": cache.get("tg") or no_data,
            "password": cache.get("password") or no_data,
        }

    def apply_patch(self, patch: dict) -> dict:
        """EN: Apply patch to user cache and return merged data.
        RU: Применить patch к user_cache и вернуть итоговые данные.
        """
        if patch:
            update_user_cache_fields(patch)
            if "email" in patch:
                UserSession().set_email(patch.get("email", ""))
        merged = get_user_cache() or {}
        return merged
