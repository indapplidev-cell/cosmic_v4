# -*- coding: utf-8 -*-
"""
Game session attempt tracker that decides soft reset vs game over.

EN: Keeps only attempt counters and returns a loss outcome based on remaining
attempts. This module does not touch UI, scoring, or gameplay objects.
RU: Хранит только счётчик попыток и возвращает результат поражения на основе
оставшихся попыток. Модуль не трогает UI, очки и игровые объекты.
"""

from enum import Enum


class LossOutcome(Enum):
    """
    Outcome produced after a loss is registered.

    EN: Indicates whether the caller should perform a soft reset or end the
    game session. This enum carries no UI or gameplay state.
    RU: Указывает, должен ли вызывающий код выполнить мягкий сброс или
    завершить игровую сессию. Enum не содержит UI или игрового состояния.
    """

    SOFT_RESET = "soft_reset"
    GAME_OVER = "game_over"


class GameSessionManager:
    """
    Track remaining attempts and decide the next loss outcome.

    EN: Owns a max-attempts value and a mutable attempts-left counter. The
    manager only updates these numbers and returns the required outcome.
    RU: Хранит максимум попыток и текущий счётчик оставшихся попыток. Менеджер
    изменяет только эти числа и возвращает требуемый результат.
    """

    def __init__(self, max_attempts: int = 3) -> None:
        """
        Initialize the manager with a maximum attempts budget.

        EN: Sets the maximum attempts and resets the remaining counter to the
        same value so the session starts fully stocked.
        RU: Устанавливает максимум попыток и сбрасывает счётчик оставшихся
        попыток к этому значению, чтобы сессия начиналась с полным запасом.
        """
        self._max_attempts = max_attempts
        self._attempts_left = max_attempts

    def reset(self) -> None:
        """
        Reset the remaining attempts to the configured maximum.

        EN: Uses the stored max_attempts value and discards any previous
        attempt count.
        RU: Использует сохранённое значение max_attempts и полностью
        перезаписывает прошлое количество попыток.
        """
        self._attempts_left = self._max_attempts

    def register_loss(self) -> LossOutcome:
        """
        Decrement attempts and return the loss outcome for the caller.

        EN: Decreases attempts_left by one until it reaches zero. Returns
        SOFT_RESET while attempts remain and GAME_OVER once the counter hits
        zero or below.
        RU: Уменьшает attempts_left на единицу, пока счётчик не достигнет нуля.
        Возвращает SOFT_RESET, пока попытки ещё есть, и GAME_OVER, когда
        счётчик достиг нуля или ниже.
        """
        if self._attempts_left > 0:
            self._attempts_left -= 1
        if self._attempts_left > 0:
            return LossOutcome.SOFT_RESET
        return LossOutcome.GAME_OVER

    def get_attempts_left(self) -> int:
        """
        Return the current number of remaining attempts.

        EN: Exposes the mutable attempts_left counter for read-only access.
        RU: Возвращает текущее число оставшихся попыток без права изменения.
        """
        return self._attempts_left

    def get_max_attempts(self) -> int:
        """
        Return the configured maximum number of attempts.

        EN: Exposes the fixed max_attempts value for read-only access.
        RU: Возвращает фиксированное значение max_attempts без права изменения.
        """
        return self._max_attempts
