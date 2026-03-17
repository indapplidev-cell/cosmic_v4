"""EN: View for the startup loading screen.
RU: Представление стартового экрана загрузки.
"""

from pathlib import Path
from threading import Thread

from kivy.clock import Clock
from kivy.lang import Builder
from kivymd.uix.screen import MDScreen

from manager.session_manager import validate_cached_session
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
        self._validation_done = False
        self._validation_result = {"ok": False, "reason": "NO_CACHE"}

    def on_enter(self, *args):
        """EN: Start progress ticking when screen is shown.
        RU: Запустить обновление прогресса при входе на экран.
        """
        self._t = 0.0
        self.ids.pb.value = 0
        self._validation_done = False
        self._validation_result = {"ok": False, "reason": "NO_CACHE"}
        if self._ev:
            self._ev.cancel()
        self._ev = Clock.schedule_interval(self._tick, 1 / 30)
        self._run_startup_validation_async()

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

        if p >= 1.0 and self._validation_done:
            if self._ev:
                self._ev.cancel()
                self._ev = None

            initial = self._resolve_initial_route()
            self._manager.go(initial, push_history=False)
            return False
        return True

    def _run_startup_validation_async(self) -> None:
        """EN: Validate cached session in background to avoid blocking UI thread.
        RU: Проверить кэшированную сессию в фоне, чтобы не блокировать UI-поток.
        """

        def _worker() -> None:
            result = validate_cached_session(timeout=8, allow_offline=True)
            Clock.schedule_once(lambda _dt: self._set_validation_result(result), 0)

        Thread(target=_worker, daemon=True).start()

    def _set_validation_result(self, result: dict) -> None:
        """EN: Persist startup validation result received from background worker.
        RU: Сохранить результат стартовой проверки, полученный из фонового worker.
        """

        self._validation_result = result if isinstance(result, dict) else {"ok": False, "reason": "NO_CACHE"}
        self._validation_done = True

    def _resolve_initial_route(self) -> str:
        """EN: Resolve startup route based on cache/server validation result.
        RU: Определить стартовый маршрут на основе результата проверки кэша/сервера.
        """

        result = self._validation_result or {}
        if result.get("ok"):
            return START

        reason = str(result.get("reason", "NO_CACHE"))
        if reason in {"NO_CACHE", "SERVER_NOT_FOUND"}:
            return LOGIN
        if reason == "NETWORK":
            # EN: Strict policy: require online verification before auto-login.
            # RU: Строгая политика: требовать онлайн-проверку перед автологином.
            return LOGIN
        return LOGIN

    def get_shell_load_widget(self):
        """EN: Return the loading content widget for mounting into shared shell content host.
        RU: Вернуть loading-виджет контента для монтирования в общий content-host shell.
        """

        return self.children[0] if self.children else None
