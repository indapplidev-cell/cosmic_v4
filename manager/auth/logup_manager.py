"""EN: Registration validation manager.
RU: Менеджер валидации регистрации.
"""

from __future__ import annotations

import re
from typing import Tuple

from manager.lang.lang_manager import t


class LogupManager:
    """EN: Validate registration inputs for email and password rules.
    RU: Проверять ввод при регистрации по правилам для email и пароля.
    """

    _EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

    @staticmethod
    def validate_email(email: str) -> bool:
        """EN: Check that the email has a basic valid format.
        RU: Проверить базовый корректный формат email.
        """
        if not email:
            return False
        return bool(LogupManager._EMAIL_RE.match(email.strip()))

    @staticmethod
    def validate_password(password: str) -> bool:
        """EN: Check password against length and character rules.
        RU: Проверить пароль по длине и наличию обязательных символов.
        """
        if not password:
            return False
        if not (8 <= len(password) <= 20):
            return False
        if not any(char.isupper() for char in password):
            return False
        if not any(char.islower() for char in password):
            return False
        if not any(char.isdigit() for char in password):
            return False
        if not any(not char.isalnum() for char in password):
            return False
        return True

    @staticmethod
    def validate(email: str, password: str, password2: str) -> Tuple[bool, str, str]:
        """EN: Validate all registration inputs and provide feedback.
        RU: Провалидировать все поля регистрации и вернуть подсказку.
        """
        if not LogupManager.validate_email(email):
            return False, t("register.validation.email_invalid"), "email"

        if not LogupManager.validate_password(password):
            header = t("register.validation.password_header")
            rules = [
                t("register.validation.rule.len"),
                t("register.validation.rule.upper"),
                t("register.validation.rule.lower"),
                t("register.validation.rule.digit"),
                t("register.validation.rule.special"),
            ]
            message = header + "\n" + "\n".join(f"- {rule}" for rule in rules)
            return False, message, "password"

        if password != password2:
            return False, t("register.validation.password2_mismatch"), "password2"

        return True, "", ""
