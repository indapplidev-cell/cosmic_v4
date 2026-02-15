"""EN: View-model data for the register screen texts.
RU: Данные view-model для текстов экрана регистрации.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class RegisterVM:
    """EN: Text container for register UI.
    RU: Контейнер текстов для UI регистрации.
    """

    title_text: str
    email_hint: str
    password_hint: str
    password2_hint: str
    create_text: str
    login_text: str
    error_text: str = ""
