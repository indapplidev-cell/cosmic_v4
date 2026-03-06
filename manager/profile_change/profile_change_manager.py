"""EN: Profile change manager for user cache updates.
RU: Менеджер изменения профиля для обновления user_cache.
"""

from __future__ import annotations

from manager import auth_backend
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
        self._sync_profile_user_db(patch or {})
        if patch:
            update_user_cache_fields(patch)
            if "email" in patch:
                UserSession().set_email(patch.get("email", ""))
        merged = get_user_cache() or {}
        return merged

    def _resolve_user_id(self) -> int | None:
        """EN: Resolve current user id from cache or session-email fallback.
        RU: Определить текущий user_id из кеша или fallback через email сессии.
        """
        cache = get_user_cache() or {}
        raw_user_id = cache.get("user_id")
        if isinstance(raw_user_id, int):
            return raw_user_id
        if isinstance(raw_user_id, str) and raw_user_id.isdigit():
            return int(raw_user_id)

        email = (cache.get("email") or "").strip() or (UserSession().get_email() or "").strip()
        if not email:
            return None
        ok, payload = auth_backend.resolve_user_id(email)
        if not ok:
            return None
        user_id = int(payload)
        update_user_cache_fields({"user_id": user_id})
        return user_id

    def _sync_profile_user_db(self, patch: dict) -> None:
        """EN: Sync profile_user DB row based on local patch semantics.
        RU: Синхронизировать строку profile_user в БД по семантике локального patch.
        """
        if not patch:
            return
        user_id = self._resolve_user_id()
        if user_id is None:
            return

        to_update = {}
        to_clear = []

        if "login" in patch:
            value = (patch.get("login") or "").strip()
            if value:
                to_update["login"] = value
            else:
                to_clear.append("login")

        if "phone" in patch:
            value = (patch.get("phone") or "").strip()
            if value:
                to_update["phone"] = value
            else:
                to_clear.append("phone")

        if "tg" in patch:
            value = (patch.get("tg") or "").strip()
            if value:
                to_update["telegram"] = value
            else:
                to_clear.append("telegram")

        if to_update:
            auth_backend.save_profile_user(user_id, **to_update)
        if to_clear:
            auth_backend.delete_profile_user_fields(user_id, to_clear)
