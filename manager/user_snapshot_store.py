"""EN: Unified local cache store for server user snapshot.
RU: Единое локальное хранилище snapshot пользователя с сервера.
"""

from __future__ import annotations

from typing import Any

from data.user_cache.user_cache_reader import get_user_cache
from data.user_cache.user_cache_writer import update_user_cache_fields


def _as_int(value: Any, default: int = 0) -> int:
    """EN: Convert value to int with safe fallback.
    RU: Безопасно преобразовать значение в int с запасным значением.
    """

    try:
        return int(value)
    except Exception:
        return int(default)


def _as_float(value: Any, default: float = 0.0) -> float:
    """EN: Convert value to float with safe fallback.
    RU: Безопасно преобразовать значение в float с запасным значением.
    """

    try:
        return float(value)
    except Exception:
        return float(default)


class UserSnapshotStore:
    """EN: Read/write helpers for server-synchronized user snapshot fields.
    RU: Хелпер чтения/записи полей snapshot пользователя, синхронизированных с сервером.
    """

    def load(self) -> dict[str, Any]:
        """EN: Load current snapshot-like data from user cache.
        RU: Загрузить текущие snapshot-поля из user cache.
        """

        cache = get_user_cache() or {}
        telegram_value = str((cache.get("telegram") or cache.get("tg") or "").strip())
        telegram_username_value = str((cache.get("telegram_username") or "").strip())
        if not telegram_value and telegram_username_value:
            telegram_value = telegram_username_value
        return {
            "user_id": _as_int(cache.get("user_id"), 0),
            "email": str((cache.get("email") or "").strip()),
            "login": str((cache.get("login") or "").strip()),
            "phone": str((cache.get("phone") or "").strip()),
            "telegram": telegram_value,
            "telegram_username": telegram_username_value,
            "telegram_user_id": _as_int(cache.get("telegram_user_id"), 0),
            "telegram_linked": bool(cache.get("telegram_linked")),
            "telegram_verified": bool(cache.get("telegram_verified")),
            "record": _as_int(cache.get("record"), 0),
            "rating": _as_int(cache.get("rating"), 0),
            "balance": _as_float(cache.get("balance"), 0.0),
        }

    def save(self, snapshot: dict[str, Any]) -> None:
        """EN: Persist full snapshot payload into user cache fields.
        RU: Сохранить полный payload snapshot в поля user cache.
        """

        telegram_value = str((snapshot.get("telegram") or "").strip())
        telegram_username_value = str((snapshot.get("telegram_username") or "").strip())
        if not telegram_value and telegram_username_value:
            telegram_value = telegram_username_value
        patch = {
            "user_id": _as_int(snapshot.get("user_id"), 0),
            "email": str((snapshot.get("email") or "").strip()),
            "login": str((snapshot.get("login") or "").strip()),
            "phone": str((snapshot.get("phone") or "").strip()),
            "telegram": telegram_value,
            "telegram_username": telegram_username_value,
            "telegram_user_id": _as_int(snapshot.get("telegram_user_id"), 0),
            "telegram_linked": bool(snapshot.get("telegram_linked")),
            "telegram_verified": bool(snapshot.get("telegram_verified")),
            "tg": telegram_value,
            "record": _as_int(snapshot.get("record"), 0),
            "rating": _as_int(snapshot.get("rating"), 0),
            "balance": _as_float(snapshot.get("balance"), 0.0),
        }
        update_user_cache_fields(patch)

    def patch_game(
        self,
        *,
        record: int | None = None,
        rating: int | None = None,
        balance: float | None = None,
    ) -> None:
        """EN: Update only game-related snapshot fields in cache.
        RU: Обновить в кэше только игровые поля snapshot.
        """

        patch: dict[str, Any] = {}
        if record is not None:
            patch["record"] = int(record)
        if rating is not None:
            patch["rating"] = int(rating)
        if balance is not None:
            patch["balance"] = float(balance)
        if patch:
            update_user_cache_fields(patch)

    def get_game(self) -> tuple[int, int, float]:
        """EN: Return (record, rating, balance) from cached snapshot.
        RU: Вернуть (record, rating, balance) из кэшированного snapshot.
        """

        data = self.load()
        return int(data["record"]), int(data["rating"]), float(data["balance"])
