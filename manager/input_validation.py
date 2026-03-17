"""EN: Lightweight client-side input validation for UX before API calls.
RU: Лёгкая клиентская валидация ввода для UX перед вызовами API.
"""

from __future__ import annotations

import re
from typing import Tuple

_CONTROL_CHARS_RE = re.compile(r"[\x00-\x1F\x7F]")
_CODE_CHARS_RE = re.compile(r"[<>`{}\[\];$\\|&]")
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_LOGIN_RE = re.compile(r"^[a-zA-Z0-9_.-]{3,32}$")
_TELEGRAM_RE = re.compile(r"^@?[a-zA-Z0-9_]{5,32}$")
_PHONE_RE = re.compile(r"^\+?[0-9]{7,15}$")

_CODE_MARKERS = (
    "select ",
    "insert ",
    "update ",
    "delete ",
    "drop ",
    "alter ",
    "create ",
    "--",
    "/*",
    "*/",
    "<script",
    "javascript:",
    "${jndi:",
)


def _has_control_chars(value: str) -> bool:
    """EN: Check whether input contains ASCII control characters.
    RU: Проверить, содержит ли ввод ASCII-управляющие символы.
    """

    return bool(_CONTROL_CHARS_RE.search(value or ""))


def _is_code_like(value: str) -> bool:
    """EN: Check whether input looks like code or injection payload.
    RU: Проверить, похож ли ввод на код или инъекционный payload.
    """

    text = value or ""
    if _CODE_CHARS_RE.search(text):
        return True
    low = text.lower()
    return any(marker in low for marker in _CODE_MARKERS)


def validate_register(email: str, psw: str) -> Tuple[bool, str, str]:
    """EN: Validate registration email/password for UX pre-check.
    RU: Проверить email/пароль регистрации для UX pre-check.
    """

    email_value = (email or "").strip()
    psw_value = psw or ""

    if not _EMAIL_RE.fullmatch(email_value):
        return False, "EMAIL_FORMAT", "email"
    if len(psw_value) < 8 or len(psw_value) > 72:
        return False, "PASSWORD_LENGTH", "password"
    if _has_control_chars(psw_value):
        return False, "CONTROL_CHARS", "password"
    return True, "", ""


def validate_login(email: str, psw: str) -> Tuple[bool, str, str]:
    """EN: Validate login email/password for UX pre-check.
    RU: Проверить email/пароль входа для UX pre-check.
    """

    return validate_register(email, psw)


def validate_profile_user(
    login: str | None,
    phone: str | None,
    telegram: str | None,
) -> Tuple[bool, str, str]:
    """EN: Validate optional profile user fields before API request.
    RU: Проверить опциональные поля профиля пользователя до API-запроса.
    """

    if login is not None and login.strip():
        login_value = login.strip()
        if _has_control_chars(login_value):
            return False, "CONTROL_CHARS", "login"
        if _is_code_like(login_value):
            return False, "CODE_LIKE", "login"
        if not _LOGIN_RE.fullmatch(login_value):
            return False, "FORMAT", "login"

    if phone is not None and phone.strip():
        phone_value = phone.strip()
        if _has_control_chars(phone_value):
            return False, "CONTROL_CHARS", "phone"
        if _is_code_like(phone_value):
            return False, "CODE_LIKE", "phone"
        if not _PHONE_RE.fullmatch(phone_value):
            return False, "FORMAT", "phone"

    if telegram is not None and telegram.strip():
        tg_value = telegram.strip()
        if _has_control_chars(tg_value):
            return False, "CONTROL_CHARS", "telegram"
        if _is_code_like(tg_value):
            return False, "CODE_LIKE", "telegram"
        if not _TELEGRAM_RE.fullmatch(tg_value):
            return False, "FORMAT", "telegram"

    return True, "", ""
