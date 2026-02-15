"""EN: Helper for attaching show/hide behavior to password fields.
RU: Хелпер для подключения показа/скрытия пароля к полям ввода.
"""

from __future__ import annotations


def attach_password_toggle(field, icon, *, start_hidden: bool = True) -> None:
    """EN: Attach password visibility toggle to a field and trailing icon.
    RU: Подключить переключатель видимости пароля к полю и правой иконке.
    """
    if getattr(field, "_pwd_toggle_attached", False):
        return

    field.password = start_hidden

    def _sync_icon() -> None:
        """EN: Update icon to reflect current password state.
        RU: Обновить иконку в соответствии с текущим состоянием пароля.
        """
        icon.icon = "eye-off" if field.password else "eye"

    def _toggle() -> None:
        """EN: Toggle password visibility without touching field text.
        RU: Переключить видимость пароля без изменения текста поля.
        """
        field.password = not field.password
        _sync_icon()
        field.focus = True

    _sync_icon()
    icon.bind(on_release=lambda *_: _toggle())
    field._pwd_toggle_attached = True
