# -*- coding: utf-8 -*-
"""
Unified lifecycle manager for game controls.

EN: Wires step and linear controllers to keyboard/touch adapters.
RU: Подключает шаговый и линейный режимы к адаптерам клавиатуры и тача.
"""

from manager.game_control.adapters.keyboard_adapter import KeyboardAdapter
from manager.game_control.adapters.touch_adapter import TouchAdapter
from manager.game_control.linear.linear_controller import LinearController
from manager.game_control.stepper.step_controller import StepController


class GameControlManager:
    """
    Manage attach/detach of input controllers.

    EN: Exposes lifecycle for keyboard and touch bindings.
    RU: Предоставляет lifecycle для подписок клавиатуры и тача.
    """

    def __init__(self, runtime) -> None:
        """
        Initialize step/linear controllers and adapters.

        EN: Sets up controllers bound to the provided runtime.
        RU: Создаёт контроллеры, связанные с переданным runtime.
        """
        self._stepper = StepController(runtime)
        self._linear = LinearController(runtime)
        self._keyboard = KeyboardAdapter(self._stepper, self._linear, runtime)
        self._touch = TouchAdapter(self._stepper, self._linear)
        self._runtime = runtime
        self._hud_left = False
        self._hud_right = False
        self._hud_brake = False
        self._attached = False
        self._bound_widget = None

    def hud_event(self, action: str, pressed: bool) -> None:
        """EN: Route on-screen control events to the same logic as keyboard.
        RU: Маршрутизировать события экранных кнопок по логике клавиатуры.
        """
        if action == "left":
            self._hud_left = pressed
            self._apply_hud_x()
            return
        if action == "right":
            self._hud_right = pressed
            self._apply_hud_x()
            return
        if action == "brake":
            self._set_hud_brake(pressed)
            return

    def _apply_hud_x(self) -> None:
        """EN: Apply horizontal movement for on-screen controls.
        RU: Применить горизонтальное движение для экранных кнопок.
        """
        if self._hud_left and not self._hud_right:
            self._linear.start_left()
        elif self._hud_right and not self._hud_left:
            self._linear.start_right()
        else:
            self._linear.stop()

    def _set_hud_brake(self, pressed: bool) -> None:
        """EN: Toggle brake for on-screen controls.
        RU: Переключить торможение для экранных кнопок.
        """
        if pressed == self._hud_brake:
            return
        self._hud_brake = pressed
        if pressed:
            self._runtime.brake_on()
        else:
            self._runtime.brake_off()

    def hud_reset(self) -> None:
        """EN: Reset on-screen control state and stop movement/brake.
        RU: Сбросить состояние экранных кнопок и остановить движение/тормоз.
        """
        self._hud_left = False
        self._hud_right = False
        self._hud_brake = False
        self._linear.stop()
        self._runtime.brake_off()

    def attach(self, gameplay_widget) -> None:
        """
        Attach keyboard and touch to the gameplay widget.

        EN: Enables both keyboard and touch input.
        RU: Включает ввод с клавиатуры и тача.
        """
        if self._attached and self._bound_widget is gameplay_widget:
            return
        if self._attached:
            self.detach(self._bound_widget)
        self._bound_widget = gameplay_widget
        self._keyboard.attach(gameplay_widget)
        self._touch.attach(gameplay_widget)
        self._attached = True

    def detach(self, gameplay_widget=None) -> None:
        """
        Detach keyboard and touch from the gameplay widget.

        EN: Disables both keyboard and touch input.
        RU: Отключает ввод с клавиатуры и тача.
        """
        if not self._attached:
            return
        self._linear.stop()
        self._touch.detach(self._bound_widget)
        self._keyboard.detach()
        self._attached = False
        self._bound_widget = None
