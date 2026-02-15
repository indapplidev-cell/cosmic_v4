# -*- coding: utf-8 -*-
"""
Step-based controller for discrete lateral moves.

EN: Delegates to runtime step methods without changing math.
RU: Делегирует шаговые команды в runtime без изменения математики.
"""


class StepController:
    """
    Perform discrete left/right steps.

    EN: Uses runtime step methods as-is.
    RU: Использует шаговые методы runtime без изменений.
    """

    def __init__(self, runtime) -> None:
        """
        Store runtime reference.

        EN: Keeps runtime for step calls.
        RU: Хранит runtime для шаговых вызовов.
        """
        self._rt = runtime

    def left(self) -> None:
        """EN: Perform one left step.
        RU: Выполнить один шаг влево.
        """
        self._rt.input_left_step()

    def right(self) -> None:
        """EN: Perform one right step.
        RU: Выполнить один шаг вправо.
        """
        self._rt.input_right_step()
