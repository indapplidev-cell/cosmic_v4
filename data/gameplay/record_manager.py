# -*- coding: utf-8 -*-
"""
Record manager for best score commit on Back after game over.

EN: Commits best score only after game over and Back button.
RU: Сохраняет рекорд только после game over и нажатия Назад.
"""

from __future__ import annotations

from data.gameplay.record_storage import RecordStorage


class RecordManager:
    """
    Manage best score commit rules.

    EN: Allows commit only after game over and Back pressed.
    RU: Разрешает запись только после game over и кнопки Назад.
    """

    def __init__(self, storage: RecordStorage) -> None:
        """
        Initialize with a storage backend.

        EN: Keeps reference to the storage instance.
        RU: Хранит ссылку на хранилище.
        """
        self._storage = storage
        self._can_commit = False
        self._final_score = 0

    def on_game_over(self, final_score: int) -> None:
        """
        Capture final score and allow commit on Back.

        EN: Prints current best score to console.
        RU: Печатает текущий рекорд в консоль.
        """
        self._final_score = int(final_score)
        self._can_commit = True

    def on_back_pressed(self) -> None:
        """
        Commit record only if allowed.

        EN: Resets internal state after processing.
        RU: Сбрасывает внутреннее состояние после обработки.
        """
        if not self._can_commit:
            return
        self._storage.try_update_best_score(self._final_score)
        self._can_commit = False
        self._final_score = 0

    def get_best_score(self) -> int:
        """
        Get current best score from storage.

        EN: Proxy to the storage.
        RU: Прокси к хранилищу.
        """
        return self._storage.get_best_score()
