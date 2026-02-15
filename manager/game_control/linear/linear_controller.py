# -*- coding: utf-8 -*-
"""
Linear controller for continuous lateral movement.

EN: Updates runtime offset continuously while input is held.
RU: Непрерывно обновляет смещение runtime во время удержания ввода.
"""

from kivy.clock import Clock


class LinearController:
    """
    Manage continuous left/right movement via runtime hook.

    EN: Starts/stops a tick that applies linear movement.
    RU: Запускает/останавливает тик для линейного движения.
    """

    def __init__(self, runtime) -> None:
        """
        Store runtime reference and init state.

        EN: Keeps runtime and disables ticking by default.
        RU: Хранит runtime и по умолчанию не тикает.
        """
        self._rt = runtime
        self._ev = None
        self._dir = 0

    def start_left(self) -> None:
        """EN: Start linear left movement.
        RU: Запустить линейное движение влево.
        """
        self._dir = -1
        self._rt.set_speed_x_dir(1)
        self._ensure()

    def start_right(self) -> None:
        """EN: Start linear right movement.
        RU: Запустить линейное движение вправо.
        """
        self._dir = 1
        self._rt.set_speed_x_dir(-1)
        self._ensure()

    def stop(self) -> None:
        """EN: Stop linear movement.
        RU: Остановить линейное движение.
        """
        self._dir = 0
        self._rt.set_speed_x_dir(0)
        self._stop()

    def _ensure(self) -> None:
        """EN: Ensure the tick is scheduled.
        RU: Убедиться, что тик запущен.
        """
        if not self._ev:
            self._ev = Clock.schedule_interval(self._tick, 0)

    def _stop(self) -> None:
        """EN: Stop the tick.
        RU: Остановить тик.
        """
        if self._ev:
            self._ev.cancel()
            self._ev = None

    def _tick(self, dt) -> None:
        """EN: Apply one linear movement tick.
        RU: Применить один тик линейного движения.
        """
        if self._dir == 0:
            return
        self._rt.apply_linear_x(dt)
