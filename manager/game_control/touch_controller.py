# -*- coding: utf-8 -*-
"""
Touch controller for game input.

EN: Maps taps and swipes to left/right commands.
RU: Привязывает тапы и свайпы к командам влево/вправо.
"""

from time import time

from kivy.clock import Clock
from kivy.metrics import dp


class TouchController:
    """
    Listen for touch events and dispatch movement commands.

    EN: Uses touch down/up to detect swipes or taps.
    RU: Использует касания для определения свайпов или тапов.
    """

    def __init__(self, router, swipe_threshold_dp: float = 30) -> None:
        """
        Store router and swipe threshold.

        EN: Keeps router reference and swipe threshold in dp.
        RU: Хранит роутер и порог свайпа в dp.
        """
        self._router = router
        self._threshold = dp(swipe_threshold_dp)
        self._widget = None
        self._touch_start = {}
        self._hold_event = None
        self._hold_uid = None
        self._hold_dir = None
        self._hold_started_at = 0.0

        self._hold_delay = 0.20
        self._boost_3_from = 0.80
        self._tick_dt = 0.06

    def attach(self, widget) -> None:
        """
        Attach touch listeners to the widget.

        EN: Binds touch down/up handlers.
        RU: Привязывает обработчики on_touch_down/on_touch_up.
        """
        if self._widget:
            return
        self._widget = widget
        widget.bind(on_touch_down=self.on_touch_down, on_touch_up=self.on_touch_up)

    def detach(self, widget) -> None:
        """
        Detach touch listeners from the widget.

        EN: Unbinds touch handlers.
        RU: Отписывает обработчики касаний.
        """
        if self._widget is None:
            return
        widget.unbind(on_touch_down=self.on_touch_down, on_touch_up=self.on_touch_up)
        self._touch_start.clear()
        self._stop_hold()
        self._widget = None

    def on_touch_down(self, widget, touch):
        """
        Record touch start for swipe detection.

        EN: Stores the starting position of the touch.
        RU: Сохраняет начальную позицию касания.
        """
        if not self._is_inside(widget, touch):
            return False
        self._touch_start[touch.uid] = (touch.x, touch.y)
        local_x = touch.x - widget.x
        direction = "left" if local_x < widget.width / 2 else "right"
        self._router.apply_steps(direction, 1)
        self._start_hold(direction, touch.uid)
        return False

    def on_touch_up(self, widget, touch):
        """
        Handle touch release to detect swipe or tap.

        EN: Executes left/right based on swipe or tap side.
        RU: Вызывает left/right по свайпу или половине экрана.
        """
        if touch.uid not in self._touch_start:
            return False
        start_x, start_y = self._touch_start.pop(touch.uid)
        dx = touch.x - start_x
        dy = touch.y - start_y
        if abs(dx) > self._threshold and abs(dx) >= abs(dy):
            if dx > 0:
                self._router.apply_steps("right", 1)
            else:
                self._router.apply_steps("left", 1)
            self._stop_hold()
            return False
        self._stop_hold()
        return False

    def _start_hold(self, direction: str, uid) -> None:
        """EN: Start hold acceleration timer.
        RU: Запустить таймер ускорения удержания.
        """
        self._hold_dir = direction
        self._hold_uid = uid
        self._hold_started_at = time()
        if self._hold_event:
            return
        self._hold_event = Clock.schedule_interval(self._hold_tick, self._tick_dt)

    def _stop_hold(self) -> None:
        """EN: Stop hold acceleration timer.
        RU: Остановить таймер ускорения удержания.
        """
        if self._hold_event:
            self._hold_event.cancel()
        self._hold_event = None
        self._hold_uid = None
        self._hold_dir = None

    def _hold_tick(self, _dt) -> None:
        """EN: Apply accelerated steps while touch is held.
        RU: Применять ускоренные шаги при удержании тача.
        """
        if not self._hold_uid or not self._hold_dir:
            return
        elapsed = time() - self._hold_started_at
        if elapsed < self._hold_delay:
            return
        steps = 2 if elapsed < self._boost_3_from else 3
        self._router.apply_steps(self._hold_dir, steps)

    def _is_inside(self, widget, touch) -> bool:
        """
        Check if touch is within widget bounds.

        EN: Uses widget coordinates to validate the touch location.
        RU: Проверяет, находится ли касание внутри границ виджета.
        """
        return widget.collide_point(touch.x, touch.y)
