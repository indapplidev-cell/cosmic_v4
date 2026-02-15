# -*- coding: utf-8 -*-
"""
Command router for game controls.

EN: Routes left/right/stop commands to provided callbacks.
RU: Маршрутизирует команды влево/вправо/стоп в заданные колбэки.
"""


class ControlsRouter:
    """
    Simple command router for input actions.

    EN: Calls bound callbacks for movement commands.
    RU: Вызывает привязанные колбэки для команд движения.
    """

    def __init__(self, on_left, on_right, on_stop=None) -> None:
        """
        Store callbacks for movement commands.

        EN: Keeps function references for left/right/stop actions.
        RU: Сохраняет ссылки на функции действий влево/вправо/стоп.
        """
        self._on_left = on_left
        self._on_right = on_right
        self._on_stop = on_stop

    def left(self) -> None:
        """EN: Dispatch left command.
        RU: Отправить команду влево.
        """
        if self._on_left:
            self._on_left()

    def right(self) -> None:
        """EN: Dispatch right command.
        RU: Отправить команду вправо.
        """
        if self._on_right:
            self._on_right()

    def stop(self) -> None:
        """EN: Dispatch stop command if provided.
        RU: Отправить команду стоп, если задана.
        """
        if self._on_stop:
            self._on_stop()

    def apply_steps(self, direction: str, steps: int) -> None:
        """EN: Apply multiple movement steps using existing commands.
        RU: Применить несколько шагов движения через существующие команды.
        """
        if steps <= 0:
            return
        if direction == "left":
            for _ in range(steps):
                self.left()
        elif direction == "right":
            for _ in range(steps):
                self.right()
