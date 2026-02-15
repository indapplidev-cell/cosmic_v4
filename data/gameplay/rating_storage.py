"""EN: Persist and load rating points to JSON storage.
RU: Сохранять и загружать рейтинг из JSON-хранилища.
"""

from __future__ import annotations

import json
from pathlib import Path


class RatingStorage:
    """EN: JSON storage helper for rating points.
    RU: Помощник для хранения рейтинга в JSON.
    """

    def _path(self) -> Path:
        """EN: Resolve rating JSON path next to record.json.
        RU: Определить путь к rating.json рядом с record.json.
        """
        return Path(__file__).resolve().parent / "rating.json"

    def load_points(self) -> int:
        """EN: Load rating points from JSON or return 0 on failure.
        RU: Загрузить рейтинг из JSON или вернуть 0 при ошибке.
        """
        path = self._path()
        if not path.exists():
            return 0
        try:
            raw = path.read_text(encoding="utf-8")
        except OSError:
            return 0
        if not raw.strip():
            return 0
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return 0
        points = data.get("points") if isinstance(data, dict) else None
        return int(points) if isinstance(points, int) else 0

    def save_points(self, points: int) -> None:
        """EN: Save rating points to JSON.
        RU: Сохранить рейтинг в JSON.
        """
        path = self._path()
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"points": int(points)}
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
