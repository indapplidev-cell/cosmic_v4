"""
Clock-based scheduler for the main game tick.

RU: Планировщик игрового тика на базе Kivy Clock.
"""

from kivy.clock import Clock


class GameLoop:
    """
    Manage a single scheduled update loop with start/stop control.

    RU: Управляет одним запланированным циклом обновления с start/stop.
    """
    def __init__(self):
        """
        Initialize with no scheduled event.

        RU: Инициализирует объект без запланированного события.
        """
        self._event = None

    def start(self, tick_fn, fps=60):
        """
        Start scheduling the tick callback at the requested FPS.

        RU: Запускает планирование тика с указанной частотой кадров.
        """
        if self._event:
            return
        self._event = Clock.schedule_interval(tick_fn, 1.0 / fps)

    def stop(self):
        """
        Stop the scheduled tick if it is running.

        RU: Останавливает запланированный тик, если он запущен.
        """
        if not self._event:
            return
        self._event.cancel()
        self._event = None
