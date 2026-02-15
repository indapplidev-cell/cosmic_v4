"""EN: Time tracking manager for game session and gameplay.
RU: Менеджер учета времени для сессии и геймплея.
"""

from __future__ import annotations

from time import perf_counter


class TimeManager:
    """EN: Track game session and gameplay durations using a monotonic timer.
    RU: Отслеживать длительность сессии и геймплея с монотонным таймером.
    """

    def __init__(self) -> None:
        """EN: Initialize time manager state.
        RU: Инициализировать состояние менеджера времени.
        """
        self._session_t0 = None
        self._session_elapsed = None
        self._gameplay_t0 = None
        self._gameplay_elapsed = None

    def time_game_session(self, start: bool = False, stop: bool = False, reset: bool = False) -> float | None:
        """EN: Start, stop, reset, or get the current session duration.
        RU: Запустить, остановить, сбросить или получить длительность сессии.
        """
        if reset:
            self._session_t0 = None
            self._session_elapsed = None
        if start:
            self._session_t0 = perf_counter()
            self._session_elapsed = None
        if stop:
            if self._session_t0 is None:
                self._session_elapsed = None
            else:
                self._session_elapsed = perf_counter() - self._session_t0
            return self._session_elapsed
        if self._session_elapsed is not None:
            return self._session_elapsed
        return None

    def time_gameplay(self, start: bool = False, stop: bool = False, reset: bool = False) -> float | None:
        """EN: Start, stop, reset, or get the gameplay duration.
        RU: Запустить, остановить, сбросить или получить длительность геймплея.
        """
        if reset:
            self._gameplay_t0 = None
            self._gameplay_elapsed = None
        if start:
            self._gameplay_t0 = perf_counter()
            self._gameplay_elapsed = None
        if stop:
            if self._gameplay_t0 is None:
                self._gameplay_elapsed = None
            else:
                self._gameplay_elapsed = perf_counter() - self._gameplay_t0
            return self._gameplay_elapsed
        if self._gameplay_elapsed is not None:
            return self._gameplay_elapsed
        return None
