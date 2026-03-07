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


class UserSnapshotStore:
    """EN: Read/write helpers for server-synchronized user snapshot fields.
    RU: Хелпер чтения/записи полей snapshot пользователя, синхронизированных с сервером.
    """

    def load(self) -> dict[str, Any]:
        """EN: Load current snapshot-like data from user cache.
        RU: Загрузить текущие snapshot-поля из user cache.
        """

        cache = get_user_cache() or {}
        return {
            "user_id": _as_int(cache.get("user_id"), 0),
            "email": str((cache.get("email") or "").strip()),
            "login": str((cache.get("login") or "").strip()),
            "phone": str((cache.get("phone") or "").strip()),
            "telegram": str((cache.get("telegram") or cache.get("tg") or "").strip()),
            "record": _as_int(cache.get("record"), 0),
            "rating": _as_int(cache.get("rating"), 0),
            "balance": _as_int(cache.get("balance"), 0),
        }

    def save(self, snapshot: dict[str, Any]) -> None:
        """EN: Persist full snapshot payload into user cache fields.
        RU: Сохранить полный payload snapshot в поля user cache.
        """

        patch = {
            "user_id": _as_int(snapshot.get("user_id"), 0),
            "email": str((snapshot.get("email") or "").strip()),
            "login": str((snapshot.get("login") or "").strip()),
            "phone": str((snapshot.get("phone") or "").strip()),
            "telegram": str((snapshot.get("telegram") or "").strip()),
            "tg": str((snapshot.get("telegram") or "").strip()),
            "record": _as_int(snapshot.get("record"), 0),
            "rating": _as_int(snapshot.get("rating"), 0),
            "balance": _as_int(snapshot.get("balance"), 0),
        }
        update_user_cache_fields(patch)

    def patch_game(
        self,
        *,
        record: int | None = None,
        rating: int | None = None,
        balance: int | None = None,
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
            patch["balance"] = int(balance)
        if patch:
            update_user_cache_fields(patch)

    def get_game(self) -> tuple[int, int, int]:
        """EN: Return (record, rating, balance) from cached snapshot.
        RU: Вернуть (record, rating, balance) из кэшированного snapshot.
        """

        data = self.load()
        return int(data["record"]), int(data["rating"]), int(data["balance"])
