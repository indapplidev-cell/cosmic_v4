"""EN: Persistent store for ads balance.
RU: Персистентное хранилище баланса рекламы.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from kivy.app import App


class BalanceStore:
    """EN: JSON-backed balance store with atomic writes.
    RU: JSON-хранилище баланса с атомарной записью.
    """

    def __init__(self) -> None:
        """EN: Initialize path `<user_data_dir>/ads/payment/balance.json`.
        RU: Инициализировать путь `<user_data_dir>/ads/payment/balance.json`.
        """
        app = App.get_running_app()
        user_dir = Path(getattr(app, "user_data_dir", ".")) if app else Path(".")
        self._base_dir = user_dir / "ads" / "payment"
        self._balance_file = self._base_dir / "balance.json"

    def get_balance(self) -> float:
        """EN: Return stored balance, 0.0 for missing/invalid file.
        RU: Вернуть сохранённый баланс, 0.0 при отсутствии/ошибке файла.
        """
        if not self._balance_file.exists():
            return 0.0
        try:
            with self._balance_file.open("r", encoding="utf-8") as fh:
                data: Any = json.load(fh)
            return float(data.get("balance", 0.0))
        except Exception:
            return 0.0

    def set_balance(self, value: float) -> None:
        """EN: Set balance value with atomic JSON write.
        RU: Установить значение баланса с атомарной JSON-записью.
        """
        self._base_dir.mkdir(parents=True, exist_ok=True)
        tmp_file = self._balance_file.with_suffix(".tmp")
        payload = {"balance": float(value)}
        with tmp_file.open("w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False)
        os.replace(tmp_file, self._balance_file)

    def add(self, delta: float) -> float:
        """EN: Add delta to balance and return new value.
        RU: Прибавить delta к балансу и вернуть новое значение.
        """
        new_value = self.get_balance() + float(delta)
        self.set_balance(new_value)
        return new_value

