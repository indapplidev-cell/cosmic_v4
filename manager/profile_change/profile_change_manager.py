"""EN: Profile change manager for user cache updates.
RU: Менеджер изменения профиля для обновления user_cache.
"""

from __future__ import annotations

from manager import auth_backend
from manager.input_validation import validate_profile_user
from data.user_cache.user_cache_reader import get_user_cache
from data.user_cache.user_cache_writer import update_user_cache_fields
from data.user_cache.user_session import UserSession
from manager.lang.lang_manager import t, user_value_text


class ProfileChangeManager:
    """EN: Provide profile data and apply selected updates.
    RU: Предоставлять данные профиля и применять выбранные изменения.
    """

    def load_current_user_data(self) -> dict:
        """EN: Load current user cache data with defaults.
        RU: Загрузить текущие данные пользователя с дефолтами.
        """
        cache = get_user_cache() or {}
        return {
            "login": user_value_text(cache.get("login")),
            "email": user_value_text(cache.get("email")),
            "phone": user_value_text(cache.get("phone")),
            "tg": user_value_text(cache.get("tg") or cache.get("telegram") or cache.get("telegram_username")),
            "password": t("common.no_data"),
        }

    def apply_patch(self, patch: dict) -> dict:
        """EN: Apply patch to user cache and return operation status with merged data.
        RU: Применить patch к user_cache и вернуть статус операции с итоговыми данными.
        """
        login_value = patch.get("login") if "login" in patch else None
        phone_value = patch.get("phone") if "phone" in patch else None
        tg_value = patch.get("tg") if "tg" in patch else None
        ok_validate, error_code, error_field = validate_profile_user(login_value, phone_value, tg_value)
        if not ok_validate:
            return {"ok": False, "error": error_code, "field": error_field}

        self._sync_profile_user_db(patch or {})
        if patch:
            cache_patch = {key: value for key, value in patch.items() if key != "password"}
            if cache_patch:
                update_user_cache_fields(cache_patch)
                if "email" in cache_patch:
                    UserSession().set_email(cache_patch.get("email", ""))
        merged = get_user_cache() or {}
        return {"ok": True, "data": merged}

    def _resolve_user_id(self) -> int | None:
        """EN: Resolve current user id from cache or protected current-session snapshot.
        RU: Определить текущий user_id из кэша или через защищённый snapshot текущей сессии.
        """
        cache = get_user_cache() or {}
        raw_user_id = cache.get("user_id")
        if isinstance(raw_user_id, int) and raw_user_id > 0:
            return raw_user_id
        if isinstance(raw_user_id, str) and raw_user_id.isdigit() and int(raw_user_id) > 0:
            return int(raw_user_id)

        ok, payload = auth_backend.get_current_user_id()
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
