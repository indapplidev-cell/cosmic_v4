# -*- coding: utf-8 -*-
"""
Best score storage for gameplay.

EN: Stores best score in JSON under app user_data_dir.
RU: Хранит рекорд в JSON в папке user_data_dir приложения.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from kivy.app import App


class RecordStore:
    """
    JSON-backed record store.

    EN: Reads and conditionally updates best score atomically.
    RU: Читает и условно обновляет рекорд атомарной записью.
    """

    def __init__(self) -> None:
        """
        Initialize storage path.

        EN: Uses `<user_data_dir>/gameplay/record.json`.
        RU: Использует `<user_data_dir>/gameplay/record.json`.
        """
        app = App.get_running_app()
        user_dir = Path(getattr(app, "user_data_dir", ".")) if app else Path(".")
        self._base_dir = user_dir / "gameplay"
        self._record_file = self._base_dir / "record.json"

    def get_best_score(self) -> int:
        """
        Return current best score.

        EN: Returns 0 if file does not exist or JSON is invalid.
        RU: Возвращает 0, если файл отсутствует или JSON поврежден.
        """
        if not self._record_file.exists():
            return 0
        try:
            with self._record_file.open("r", encoding="utf-8") as fh:
                data: Any = json.load(fh)
            return int(data.get("best_score", 0))
        except Exception:
            return 0

    def commit_if_higher(self, current_score: int) -> int:
        """
        Commit score only if it is higher than stored best.

        EN: Does not touch file when score is not an improvement.
        RU: Не изменяет файл, если счет не превышает рекорд.
        """
        best = self.get_best_score()
        current = int(current_score)
        if current <= best:
            return best

        self._base_dir.mkdir(parents=True, exist_ok=True)
        tmp_file = self._record_file.with_suffix(".tmp")
        payload = {"best_score": current}
        with tmp_file.open("w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False)
        os.replace(tmp_file, self._record_file)
        return current
