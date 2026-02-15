"""EN: View for the startup loading screen.
RU: Представление стартового экрана загрузки.
"""

from pathlib import Path

from kivy.clock import Clock
from kivy.lang import Builder
from kivymd.uix.screen import MDScreen

from data.user_cache.user_session import UserSession
from uix.screens.load_app.constants import LOAD_DURATION_SEC
from uix.screens.routes import LOGIN, START

KV_PATH = Path(__file__).with_name("load_app.kv")
Builder.load_file(str(KV_PATH))


class LoadAppScreenView(MDScreen):
    """EN: Simple timed loading screen with progress bar.
    RU: Простой экран загрузки с таймером и индикатором прогресса.
    """

    def __init__(self, manager, **kwargs):
        """EN: Store manager and initialize timer state.
        RU: Сохранить менеджер и инициализировать состояние таймера.
        """
        super().__init__(**kwargs)
        self._manager = manager
        self._ev = None
        self._t = 0.0

    def on_enter(self, *args):
        """EN: Start progress ticking when screen is shown.
        RU: Запустить обновление прогресса при входе на экран.
        """
        self._t = 0.0
        self.ids.pb.value = 0
        if self._ev:
            self._ev.cancel()
        self._ev = Clock.schedule_interval(self._tick, 1 / 30)

    def on_leave(self, *args):
        """EN: Stop ticking when leaving the loading screen.
        RU: Остановить таймер при уходе с экрана загрузки.
        """
        if self._ev:
            self._ev.cancel()
            self._ev = None

    def _tick(self, dt):
        """EN: Advance progress and navigate after timeout.
        RU: Обновить прогресс и перейти после завершения таймера.
        """
        self._t += dt
        p = min(self._t / LOAD_DURATION_SEC, 1.0)
        self.ids.pb.value = p * 100.0

        if p >= 1.0:
            if self._ev:
                self._ev.cancel()
                self._ev = None

            initial = START if UserSession().is_logged_in() else LOGIN
            self._manager.go(initial, push_history=False)
            return False
        return True
