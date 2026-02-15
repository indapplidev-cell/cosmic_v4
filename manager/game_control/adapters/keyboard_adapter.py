# -*- coding: utf-8 -*-
"""
Keyboard adapter that maps input to step/linear controllers.

EN: Single press triggers step; hold triggers linear after delay.
RU: Одиночное нажатие делает шаг; удержание включает линейный режим.
"""

from time import time

from kivy.clock import Clock
from kivy.core.window import Window


class KeyboardAdapter:
    """
    Bridge keyboard events to step/linear controllers.

    EN: Prevents OS auto-repeat from spamming step inputs.
    RU: Предотвращает автоповтор ОС для шаговых команд.
    """

    def __init__(self, stepper, linear, runtime) -> None:
        """
        Store step and linear controllers.

        EN: Keeps references to both control modes.
        RU: Хранит ссылки на оба режима управления.
        """
        self._stepper = stepper
        self._linear = linear
        self._keyboard = None
        self._runtime = runtime
        self._pressed = set()
        self._hold_event = None
        self._hold_key = None
        self._hold_started_at = 0.0
        self._hold_dir = None
        self._left_pressed = False
        self._right_pressed = False
        self._brake_pressed = False

        self._on_key_down_cb = self._on_key_down
        self._on_key_up_cb = self._on_key_up
        self._sdl2_keycodes = {
            1073741904: "left",
            1073741903: "right",
            1073741905: "down",
        }
        self._sdl_scancodes = {
            80: "left",
            79: "right",
            81: "down",
        }
        self._legacy_keycodes = {
            276: "left",
            275: "right",
            274: "down",
            97: "a",
            100: "d",
            115: "s",
        }

        self._hold_delay = 0.02

    def _is_left(self, key_name) -> bool:
        """EN: Check if key represents left movement.
        RU: Проверить, что клавиша означает движение влево.
        """
        return key_name in ("left", "a")

    def _is_right(self, key_name) -> bool:
        """EN: Check if key represents right movement.
        RU: Проверить, что клавиша означает движение вправо.
        """
        return key_name in ("right", "d")

    def _is_brake(self, key_name, text) -> bool:
        """EN: Check if key represents brake action.
        RU: Проверить, что клавиша означает тормоз.
        """
        return (key_name in ("down", "s", "ы")) or (text in ("ы", "Ы"))

    def _resolve_key_name(self, key, scancode, codepoint):
        """EN: Resolve key name from codepoint, keycode, or scancode.
        RU: Определить имя клавиши по codepoint, keycode или scancode.
        """
        if codepoint:
            return codepoint.lower()
        if self._keyboard:
            try:
                name = self._keyboard.keycode_to_string(key)
                if name:
                    return name.lower()
            except Exception:
                pass
        return (
            self._sdl2_keycodes.get(key)
            or self._sdl_scancodes.get(scancode)
            or self._legacy_keycodes.get(key)
        )


    def _apply_x(self) -> None:
        """EN: Apply horizontal movement based on pressed state.
        RU: Применить горизонтальное движение по состоянию нажатий.
        """
        if self._left_pressed and not self._right_pressed:
            self._linear.start_left()
        elif self._right_pressed and not self._left_pressed:
            self._linear.start_right()
        else:
            self._linear.stop()

    def attach(self, widget=None) -> None:
        """
        Attach keyboard listeners.

        EN: Requests keyboard and binds key events.
        RU: Запрашивает клавиатуру и подписывается на события.
        """
        self._reset_internal_state()
        Window.unbind(on_key_down=self._on_key_down_cb, on_key_up=self._on_key_up_cb)
        Window.bind(on_key_down=self._on_key_down_cb, on_key_up=self._on_key_up_cb)
        if (self._keyboard is None) or getattr(self._keyboard, "closed", False):
            self._keyboard = Window.request_keyboard(self._keyboard_closed, widget)

    def detach(self) -> None:
        """
        Detach keyboard listeners.

        EN: Unbinds and releases keyboard.
        RU: Отписывается и освобождает клавиатуру.
        """
        self._reset_internal_state()
        Window.unbind(on_key_down=self._on_key_down_cb, on_key_up=self._on_key_up_cb)
        if self._keyboard:
            try:
                self._keyboard.release()
            except Exception:
                pass
        self._keyboard = None

    def _keyboard_closed(self) -> None:
        """EN: Cleanup when keyboard is closed.
        RU: Очистка при закрытии клавиатуры.
        """
        self.detach()

    def _on_key_down(self, _window, key, scancode, codepoint, _modifiers):
        """
        Handle key down for left/right.

        EN: Triggers step and starts hold timer.
        RU: Делает шаг и запускает таймер удержания.
        """
        key_name = self._resolve_key_name(key, scancode, codepoint)
        if not key_name:
            return True
        if key_name in self._pressed:
            return True
        self._pressed.add(key_name)
        if self._is_left(key_name):
            self._left_pressed = True
            self._apply_x()
            return True
        if self._is_right(key_name):
            self._right_pressed = True
            self._apply_x()
            return True
        if self._is_brake(key_name, codepoint):
            self._brake_pressed = True
            self._runtime.brake_on()
            return True
        return False

    def _on_key_up(self, _window, key, scancode):
        """
        Handle key up and stop linear movement.

        EN: Stops linear mode when a movement key is released.
        RU: Останавливает линейный режим при отпускании клавиши.
        """
        key_name = self._resolve_key_name(key, scancode, None)
        if key_name in self._pressed:
            self._pressed.remove(key_name)
        if self._is_left(key_name):
            self._left_pressed = False
            self._apply_x()
            return True
        if self._is_right(key_name):
            self._right_pressed = False
            self._apply_x()
            return True
        if self._is_brake(key_name, None):
            self._brake_pressed = False
            self._runtime.brake_off()
            return True
        return False

    def _start_hold(self, direction: str, key: str) -> None:
        """EN: Start hold delay timer for linear mode.
        RU: Запустить таймер удержания для линейного режима.
        """
        self._hold_key = key
        self._hold_started_at = time()
        if self._hold_event:
            return
        self._hold_event = Clock.schedule_interval(self._hold_tick, 0)
        self._hold_dir = direction

    def _stop_hold(self) -> None:
        """EN: Stop hold delay timer.
        RU: Остановить таймер удержания.
        """
        if self._hold_event:
            self._hold_event.cancel()
        self._hold_event = None
        self._hold_key = None
        self._hold_dir = None

    def _reset_internal_state(self) -> None:
        """EN: Clear pressed keys and stop hold timers.
        RU: Очистить состояние клавиш и таймеров удержания.
        """
        self._stop_hold()
        self._pressed.clear()
        self._left_pressed = False
        self._right_pressed = False
        self._brake_pressed = False

    def _hold_tick(self, _dt) -> None:
        """EN: Start linear mode after hold delay.
        RU: Запустить линейный режим после задержки удержания.
        """
        if not self._hold_key:
            return
        elapsed = time() - self._hold_started_at
        if elapsed < self._hold_delay:
            return
        if self._hold_dir == "left":
            self._linear.start_left()
        elif self._hold_dir == "right":
            self._linear.start_right()
        self._stop_hold()
