"""EN: View-model data for the login screen texts.
RU: Данные view-model для текстов экрана входа.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class LoginVM:
    """EN: Text container for login UI.
    RU: Контейнер текстов для UI входа.
    """

    title: str
    email_hint: str
    password_hint: str
    login_text: str
    register_text: str
    forgot_text: str
    error_text: str = ""
