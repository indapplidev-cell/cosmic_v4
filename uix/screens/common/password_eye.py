"""EN: Helper for wiring a clickable eye icon to password fields.
RU: Хелпер для привязки кликабельного глаза к полям пароля.
"""

from __future__ import annotations


def wire_password_eye(field, icon_btn, *, start_hidden: bool = True) -> None:
    """EN: Wire eye icon to toggle password visibility.
    RU: Привязать иконку глаза к переключению видимости пароля.
    """
    if getattr(field, "_pwd_eye_wired", False):
        return
    field._pwd_eye_wired = True

    field.password = bool(start_hidden)

    def _sync() -> None:
        """EN: Sync icon with current password state.
        RU: Синхронизировать иконку с текущим состоянием пароля.
        """
        icon_btn.icon = "eye-off" if field.password else "eye"

    def _toggle(*_args) -> None:
        """EN: Toggle password visibility and keep focus on field.
        RU: Переключить видимость пароля и оставить фокус на поле.
        """
        field.password = not field.password
        _sync()
        field.focus = True

    _sync()
    icon_btn.on_release = _toggle
