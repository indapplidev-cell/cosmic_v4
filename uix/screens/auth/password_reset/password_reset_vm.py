"""EN: View-model for password reset screen text payload.
RU: View-model для текстового наполнения экрана восстановления пароля.
"""

from dataclasses import dataclass


@dataclass
class PasswordResetVM:
    """EN: Holds localized labels, hints, and error text for password reset UI.
    RU: Хранит локализованные подписи, хинты и текст ошибки для UI восстановления пароля.
    """

    title: str = ""
    email_hint: str = ""
    code_hint: str = ""
    new_password_hint: str = ""
    send_code_text: str = ""
    confirm_text: str = ""
    back_text: str = ""
    error_text: str = ""
