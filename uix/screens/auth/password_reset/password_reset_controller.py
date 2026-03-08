"""EN: Controller for password reset actions and callbacks.
RU: Контроллер действий и колбэков экрана восстановления пароля.
"""

from typing import Callable, Optional


class PasswordResetController:
    """EN: Dispatch-only controller for password reset screen.
    RU: Контроллер только для диспетчеризации экрана восстановления пароля.
    """

    def __init__(
        self,
        on_back: Optional[Callable[[], None]] = None,
    ) -> None:
        """EN: Store navigation callback for back action.
        RU: Сохранить навигационный колбэк для действия «назад».
        """

        self._on_back = on_back

    def back(self) -> None:
        """EN: Dispatch back navigation action.
        RU: Диспетчеризовать действие навигации назад.
        """

        if self._on_back:
            self._on_back()
