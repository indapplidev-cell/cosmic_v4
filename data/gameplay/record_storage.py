# -*- coding: utf-8 -*-
"""
Best score storage backed by JSON file.

EN: Reads/writes best score to a JSON file with atomic writes.
RU: Читает/пишет рекорд в JSON-файл с атомарной записью.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


class RecordStorage:
    """
    File-backed storage for the best score.

    EN: Uses record.json in data/gameplay by default.
    RU: По умолчанию использует record.json в data/gameplay.
    """

    def __init__(self, base_dir: Path | None = None) -> None:
        """
        Initialize storage with base directory.

        EN: base_dir defaults to the data/gameplay folder.
        RU: base_dir по умолчанию — папка data/gameplay.
        """
        self._base_dir = base_dir or Path(__file__).resolve().parent
        self._record_path = self._base_dir / "record.json"

    def get_best_score(self) -> int:
        """
        Read best score from disk.

        EN: Returns 0 when file is missing or corrupted.
        RU: Возвращает 0, если файла нет или он повреждён.
        """
        if not self._record_path.exists():
            return 0
        try:
            with self._record_path.open("r", encoding="utf-8") as fh:
                data: Any = json.load(fh)
            return int(data.get("best_score", 0))
        except Exception:
            return 0

    def try_update_best_score(self, current_score: int) -> bool:
        """
        Update best score if current score is higher.

        EN: Writes atomically and returns True if updated.
        RU: Записывает атомарно и возвращает True при обновлении.
        """
        best = self.get_best_score()
        current = int(current_score)
        if current <= best:
            return False

        self._base_dir.mkdir(parents=True, exist_ok=True)
        tmp_path = self._record_path.with_suffix(".json.tmp")
        payload = {"best_score": current}
        with tmp_path.open("w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False)
        os.replace(tmp_path, self._record_path)
        return True
