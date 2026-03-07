"""EN: Input validation helpers for rejecting code-like payloads and invalid formats.
RU: Хелперы валидации ввода для отклонения code-like payload и неверных форматов.
"""

from __future__ import annotations

import re

_CONTROL_CHARS_RE = re.compile(r"[\x00-\x1F\x7F]")
_CODE_CHARS_RE = re.compile(r"[<>`{}\[\];$\\|&]")
_MULTI_SPACE_RE = re.compile(r"\s+")

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


def normalize_spaces(s: str) -> str:
    """EN: Trim string and collapse repeating spaces into a single space.
    RU: Обрезать строку и схлопнуть повторяющиеся пробелы в один.
    """

    return _MULTI_SPACE_RE.sub(" ", (s or "").strip())


def reject_control_chars(s: str) -> str:
    """EN: Reject strings containing ASCII control characters.
    RU: Отклонить строки, содержащие ASCII-управляющие символы.
    """

    if _CONTROL_CHARS_RE.search(s or ""):
        raise ValueError("CONTROL_CHARS")
    return s


def reject_code_like(s: str) -> str:
    """EN: Reject strings with dangerous symbols or code-like markers.
    RU: Отклонить строки с опасными символами или code-like маркерами.
    """

    value = s or ""
    if _CODE_CHARS_RE.search(value):
        raise ValueError("CODE_LIKE")

    low = value.lower()
    for marker in _CODE_MARKERS:
        if marker in low:
            raise ValueError("CODE_LIKE")

    return s


def _validate_by_regex(s: str, regex: re.Pattern[str]) -> str:
    """EN: Validate string against allowlist regex and return normalized value.
    RU: Проверить строку по allowlist regex и вернуть нормализованное значение.
    """

    if not regex.fullmatch(s):
        raise ValueError("FORMAT")
    return s


def validate_login(s: str) -> str:
    """EN: Validate login with normalization, hard reject rules, and allowlist format.
    RU: Проверить login через нормализацию, жёсткие запреты и allowlist-формат.
    """

    value = normalize_spaces(s)
    reject_control_chars(value)
    reject_code_like(value)
    return _validate_by_regex(value, _LOGIN_RE)


def validate_telegram(s: str) -> str:
    """EN: Validate Telegram username with normalization and allowlist.
    RU: Проверить Telegram-username через нормализацию и allowlist.
    """

    value = normalize_spaces(s)
    reject_control_chars(value)
    reject_code_like(value)
    return _validate_by_regex(value, _TELEGRAM_RE)


def validate_phone(s: str) -> str:
    """EN: Validate phone value with normalization and allowlist.
    RU: Проверить телефон через нормализацию и allowlist.
    """

    value = normalize_spaces(s)
    reject_control_chars(value)
    reject_code_like(value)
    return _validate_by_regex(value, _PHONE_RE)


def validate_nonneg_int(v: int, max_v: int = 2_000_000_000) -> int:
    """EN: Validate non-negative integer with upper bound.
    RU: Проверить неотрицательное целое число с верхней границей.
    """

    try:
        value = int(v)
    except Exception as exc:
        raise ValueError("FORMAT") from exc

    if value < 0 or value > int(max_v):
        raise ValueError("FORMAT")
    return value
