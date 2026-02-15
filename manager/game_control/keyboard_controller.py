# -*- coding: utf-8 -*-
"""
Keyboard controller for game input.

EN: Maps keyboard events to left/right/stop commands.
RU: Привязывает события клавиатуры к командам влево/вправо/стоп.
"""

from time import time

from kivy.clock import Clock
from kivy.core.window import Window


class KeyboardController:
    """
    Listen for keyboard events and dispatch movement commands.

    EN: Uses Kivy keyboard events for left/right control.
    RU: Использует события клавиатуры Kivy для управления влево/вправо.
    """

    def __init__(self, router) -> None:
        """
        Store the command router.

        EN: Keeps a reference to the ControlsRouter.
        RU: Хранит ссылку на ControlsRouter.
        """
        self._router = router
        self._keyboard = None
        self._pressed = set()
        self._hold_event = None
        self._hold_key = None
        self._hold_started_at = 0.0

        self._hold_delay = 0.20
        self._boost_3_from = 0.80
        self._tick_dt = 0.06

    def attach(self, widget=None) -> None:
        """
        Attach keyboard listeners.

        EN: Requests keyboard and binds key events.
        RU: Запрашивает клавиатуру и подписывается на события.
        """
        if self._keyboard:
            return
        self._keyboard = Window.request_keyboard(self._keyboard_closed, widget)
        if not self._keyboard:
            return
        self._keyboard.bind(on_key_down=self.on_key_down)
        self._keyboard.bind(on_key_up=self.on_key_up)

    def detach(self) -> None:
        """
        Detach keyboard listeners.

        EN: Unbinds and releases keyboard.
        RU: Отписывается и освобождает клавиатуру.
        """
        if not self._keyboard:
            return
        self._stop_hold()
        self._keyboard.unbind(on_key_down=self.on_key_down)
        self._keyboard.unbind(on_key_up=self.on_key_up)
        self._keyboard.release()
        self._keyboard = None

    def _keyboard_closed(self) -> None:
        """EN: Cleanup when keyboard is closed.
        RU: Очистка при закрытии клавиатуры.
        """
        self.detach()

    def on_key_down(self, _keyboard, keycode, _text, _modifiers):
        """
        Handle key down for left/right.

        EN: Maps left/a to left, right/d to right.
        RU: Привязывает left/a к влево, right/d к вправо.
        """
        key = keycode[1]
        if key in self._pressed:
            return True
        self._pressed.add(key)
        if key in ("left", "a"):
            self._router.left()
            self._start_hold("left", key)
        elif key in ("right", "d"):
            self._router.right()
            self._start_hold("right", key)
        return True

    def on_key_up(self, _keyboard, keycode):
        """
        Handle key up and stop movement.

        EN: Stops movement when a movement key is released.
        RU: Останавливает движение при отпускании клавиши движения.
        """
        key = keycode[1]
        if key in self._pressed:
            self._pressed.remove(key)
        if key in ("left", "a", "right", "d"):
            self._router.stop()
            self._stop_hold()
        return True

    def _start_hold(self, direction: str, key: str) -> None:
        """EN: Start hold acceleration timer.
        RU: Запустить таймер ускорения удержания.
        """
        self._hold_key = key
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
        self._hold_key = None

    def _hold_tick(self, _dt) -> None:
        """EN: Apply accelerated steps while key is held.
        RU: Применять ускоренные шаги при удержании клавиши.
        """
        if not self._hold_key:
            return
        elapsed = time() - self._hold_started_at
        if elapsed < self._hold_delay:
            return
        steps = 2 if elapsed < self._boost_3_from else 3
        if self._hold_key in ("left", "a"):
            self._router.apply_steps("left", steps)
        elif self._hold_key in ("right", "d"):
            self._router.apply_steps("right", steps)
