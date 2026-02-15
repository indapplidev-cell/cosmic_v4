# -*- coding: utf-8 -*-
"""
Touch adapter that maps input to step/linear controllers.

EN: Single tap triggers step; hold triggers linear after delay.
RU: Одиночный тап делает шаг; удержание включает линейный режим.
"""

from time import time

from kivy.clock import Clock


class TouchAdapter:
    """
    Bridge touch events to step/linear controllers.

    EN: Does not consume events unless needed.
    RU: Не перехватывает события, если это не нужно.
    """

    def __init__(self, stepper, linear) -> None:
        """
        Store step and linear controllers.

        EN: Keeps references to both control modes.
        RU: Хранит ссылки на оба режима управления.
        """
        self._stepper = stepper
        self._linear = linear
        self._widget = None
        self._hold_event = None
        self._hold_uid = None
        self._hold_dir = None
        self._hold_started_at = 0.0
        self._down_cb = self._on_touch_down
        self._up_cb = self._on_touch_up
        self._hold_delay = 0.02

    def _reset_internal_state(self) -> None:
        """EN: Clear hold state and timers.
        RU: Очистить состояние удержания и таймеры.
        """
        self._stop_hold()
        self._hold_started_at = 0.0

    def attach(self, widget) -> None:
        """
        Attach touch listeners to the widget.

        EN: Binds touch down/up handlers.
        RU: Привязывает обработчики on_touch_down/on_touch_up.
        """
        if self._widget and self._widget is not widget:
            self.detach(self._widget)
        self._widget = widget
        self._reset_internal_state()
        widget.unbind(on_touch_down=self._down_cb, on_touch_up=self._up_cb)
        widget.bind(on_touch_down=self._down_cb, on_touch_up=self._up_cb)

    def detach(self, widget=None) -> None:
        """
        Detach touch listeners from the widget.

        EN: Unbinds touch handlers.
        RU: Отписывает обработчики касаний.
        """
        if self._widget is None:
            return
        target = widget or self._widget
        target.unbind(on_touch_down=self._down_cb, on_touch_up=self._up_cb)
        self._reset_internal_state()
        self._widget = None

    def _on_touch_down(self, widget, touch):
        """
        Handle touch down to trigger step and start hold delay.

        EN: Determines direction by screen half.
        RU: Определяет направление по половине экрана.
        """
        if not widget.collide_point(touch.x, touch.y):
            return False
        local_x = touch.x - widget.x
        direction = "left" if local_x < widget.width / 2 else "right"
        if direction == "left":
            self._stepper.left()
        else:
            self._stepper.right()
        self._start_hold(direction, touch.uid)
        return False

    def _on_touch_up(self, _widget, touch):
        """
        Handle touch up to stop linear movement.

        EN: Stops linear mode on release.
        RU: Останавливает линейный режим при отпускании.
        """
        if self._hold_uid != touch.uid:
            return False
        self._linear.stop()
        self._stop_hold()
        return False

    def _start_hold(self, direction: str, uid) -> None:
        """EN: Start hold delay timer for linear mode.
        RU: Запустить таймер удержания для линейного режима.
        """
        self._hold_uid = uid
        self._hold_dir = direction
        self._hold_started_at = time()
        if self._hold_event:
            return
        self._hold_event = Clock.schedule_interval(self._hold_tick, 0)

    def _stop_hold(self) -> None:
        """EN: Stop hold delay timer.
        RU: Остановить таймер удержания.
        """
        if self._hold_event:
            self._hold_event.cancel()
        self._hold_event = None
        self._hold_uid = None
        self._hold_dir = None

    def _hold_tick(self, _dt) -> None:
        """EN: Start linear mode after hold delay.
        RU: Запустить линейный режим после задержки удержания.
        """
        if not self._hold_uid:
            return
        elapsed = time() - self._hold_started_at
        if elapsed < self._hold_delay:
            return
        if self._hold_dir == "left":
            self._linear.start_left()
        elif self._hold_dir == "right":
            self._linear.start_right()
        self._stop_hold()
