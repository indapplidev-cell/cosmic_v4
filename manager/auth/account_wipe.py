"""EN: Full user data wipe helpers.
RU: Утилиты полного удаления пользовательских данных.
"""

from __future__ import annotations

from pathlib import Path

from kivy.app import App

from ads.payment.balance_store import BalanceStore
from data.gameplay.rating_storage import RatingStorage
from data.gameplay.record_store import RecordStore
from data.user_cache.user_cache_reader import _cache_path
from data.user_cache.user_session import UserSession
from manager.gameover.gameover_counters import counters


def _safe_unlink(path: Path | None) -> None:
    """EN: Safely remove a file path if it exists.
    RU: Безопасно удалить файл, если он существует.
    """
    if path is None:
        return
    try:
        p = Path(path)
        if p.exists() and p.is_file():
            p.unlink()
    except Exception:
        return


def wipe_all_user_data() -> None:
    """EN: Remove user session/cache/progress JSON files and reset counters.
    RU: Удалить JSON сессии/кэша/прогресса и сбросить счётчики в памяти.
    """
    UserSession().clear()

    _safe_unlink(_cache_path())

    record_store = RecordStore()
    _safe_unlink(getattr(record_store, "_record_file", None))

    rating_store = RatingStorage()
    _safe_unlink(rating_store._path())

    balance_store = BalanceStore()
    _safe_unlink(getattr(balance_store, "_balance_file", None))

    counters.gameover_count = 0
    counters.receive_click_count = 0

    app = App.get_running_app()
    user_dir = Path(getattr(app, "user_data_dir", ".")) if app else Path(".")
    known_paths = [
        user_dir / "user_session.json",
        user_dir / "gameplay" / "record.json",
        user_dir / "ads" / "payment" / "balance.json",
    ]
    for path in known_paths:
        _safe_unlink(path)

