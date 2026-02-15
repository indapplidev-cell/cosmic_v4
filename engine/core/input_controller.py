# -*- coding: utf-8 -*-
"""
Input handling for keyboard and touch, mapping to lateral speed.

EN: Converts user input into changes of state.current_speed_x.
RU: Преобразует пользовательский ввод в изменения state.current_speed_x.
"""

from kivy.core.window import Window


class InputController:
    """
    Translate user input events into lateral speed changes with gating.

    EN: Applies left/right input to state.current_speed_x and can be disabled.
    RU: Применяет ввод влево/вправо к state.current_speed_x и умеет блокироваться.
    """

    def __init__(self, state, config):
        """
        Store references to state/config and initialize input bindings.

        EN: Keeps state and config, clears keyboard/widget references, and
        enables input by default.
        RU: Сохраняет state и config, очищает ссылки на клавиатуру/виджет и
        включает ввод по умолчанию.
        """
        self._state = state
        self._config = config
        self._keyboard = None
        self._widget = None
        self._enabled = True

    def attach(self, widget, is_desktop):
        """
        Bind touch and optional keyboard handlers to the given widget.

        EN: Hooks touch callbacks for all platforms and keyboard events on desktop.
        RU: Подключает обработчики касаний для всех платформ и клавиатуру на десктопе.
        """
        self._widget = widget
        widget.bind(on_touch_down=self.on_touch_down, on_touch_up=self.on_touch_up)
        if is_desktop:
            self._keyboard = Window.request_keyboard(self._keyboard_closed, widget)
            if self._keyboard:
                self._keyboard.bind(on_key_down=self.on_keyboard_down)
                self._keyboard.bind(on_key_up=self.on_keyboard_up)

    def detach(self):
        """
        Unbind any previously attached input handlers.

        EN: Removes touch and keyboard bindings and clears cached references.
        RU: Удаляет привязки касаний и клавиатуры и очищает сохраненные ссылки.
        """
        if self._widget:
            self._widget.unbind(on_touch_down=self.on_touch_down, on_touch_up=self.on_touch_up)
        if self._keyboard:
            self._keyboard.unbind(on_key_down=self.on_keyboard_down)
            self._keyboard.unbind(on_key_up=self.on_keyboard_up)
            self._keyboard = None
        self._widget = None

    def disable(self) -> None:
        """
        Disable input handling without altering gameplay state.

        EN: Prevents input callbacks from changing state.current_speed_x.
        RU: Запрещает обработчикам ввода изменять state.current_speed_x.
        """
        self._enabled = False

    def enable(self) -> None:
        """
        Enable input handling after a temporary disable.

        EN: Allows input callbacks to affect state.current_speed_x again.
        RU: Разрешает обработчикам ввода снова менять state.current_speed_x.
        """
        self._enabled = True

    def _keyboard_closed(self):
        """
        Cleanup callback invoked when the keyboard is closed.

        EN: Unbinds keyboard handlers and clears the keyboard reference.
        RU: Отвязывает обработчики клавиатуры и очищает ссылку на нее.
        """
        if not self._keyboard:
            return
        self._keyboard.unbind(on_key_down=self.on_keyboard_down)
        self._keyboard.unbind(on_key_up=self.on_keyboard_up)
        self._keyboard = None

    def on_keyboard_down(self, keyboard, keycode, text, modifiers):
        """
        Handle key-down and set lateral speed according to arrow keys.

        EN: Sets positive/negative lateral speed for left/right keys when enabled.
        RU: Устанавливает скорость влево/вправо при нажатии стрелок, если ввод активен.
        """
        if not self._enabled:
            return True
        if keycode[1] == "left":
            self._state.current_speed_x = self._config.SPEED_X
        elif keycode[1] == "right":
            self._state.current_speed_x = -self._config.SPEED_X
        elif keycode[1] == "down":
            self._state.speed_y_factor = self._config.SPEED_Y_SLOWDOWN_FACTOR
        return True

    def on_keyboard_up(self, keyboard, keycode):
        """
        Handle key-up and stop lateral movement.

        EN: Resets lateral speed to zero when a key is released, if enabled.
        RU: Сбрасывает боковую скорость в ноль при отпускании клавиши, если ввод активен.
        """
        if not self._enabled:
            return True
        if keycode[1] in ("left", "right"):
            self._state.current_speed_x = 0
        elif keycode[1] == "down":
            self._state.speed_y_factor = 1.0
        return True

    def on_touch_down(self, widget, touch):
        """
        Handle touch down and set lateral speed based on screen half.

        EN: Sets speed left/right by touch position while the run is active and input enabled.
        RU: Задает скорость влево/вправо по позиции касания, если забег активен и ввод включен.
        """
        if not self._enabled:
            return False
        if self._state.state_game_over or not self._state.state_game_has_started:
            return False
        if touch.x < widget.width / 2:
            self._state.current_speed_x = self._config.SPEED_X
        else:
            self._state.current_speed_x = -self._config.SPEED_X
        return False

    def on_touch_up(self, widget, touch):
        """
        Handle touch release and stop lateral movement.

        EN: Resets lateral speed to zero when touch ends, if enabled.
        RU: Сбрасывает боковую скорость в ноль при отпускании касания, если ввод активен.
        """
        if not self._enabled:
            return False
        self._state.current_speed_x = 0
        return False
