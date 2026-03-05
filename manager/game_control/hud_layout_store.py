"""EN: Persistent HUD touch-layout swap flag storage.
RU: Постоянное хранилище флага перестановки тач-раскладки HUD.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from kivy.app import App


def _path() -> Path:
    """EN: Resolve `<user_data_dir>/gameplay/hud_layout.json` path.
    RU: Определить путь `<user_data_dir>/gameplay/hud_layout.json`.
    """
    app = App.get_running_app()
    user_dir = Path(getattr(app, "user_data_dir", ".")) if app else Path(".")
    return user_dir / "gameplay" / "hud_layout.json"


def get_swapped() -> bool:
    """EN: Return stored swapped flag, or False for missing/invalid file.
    RU: Вернуть сохранённый флаг swapped, либо False при отсутствии/ошибке файла.
    """
    path = _path()
    if not path.exists():
        return False
    try:
        with path.open("r", encoding="utf-8") as fh:
            data: Any = json.load(fh)
        return bool(data.get("swapped", False))
    except Exception:
        return False


def set_swapped(val: bool) -> None:
    """EN: Persist swapped flag with atomic JSON write.
    RU: Сохранить флаг swapped атомарной JSON-записью.
    """
    path = _path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(".tmp")
    payload = {"swapped": bool(val)}
    with tmp_path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False)
    os.replace(tmp_path, path)


def toggle_swapped() -> bool:
    """EN: Toggle stored swapped flag and return the new value.
    RU: Переключить сохранённый флаг swapped и вернуть новое значение.
    """
    new_val = not get_swapped()
    set_swapped(new_val)
    return new_val

