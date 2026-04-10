"""EN: Shared normalization helpers for optional user/profile text values.
RU: Общие helper-функции нормализации необязательных текстовых user/profile-значений.
"""

from __future__ import annotations


_LEGACY_MISSING_USER_VALUES = {
    "",
    "no data",
    "нет данных",
    "new_login",
    "none",
    "null",
}


def is_missing_user_value(value: object) -> bool:
    """EN: Return True when value is empty or matches known legacy placeholder literals.
    RU: Вернуть True, если значение пустое или совпадает с известными legacy-строками-заглушками.
    """

    if value is None:
        return True
    normalized = str(value).strip()
    if not normalized:
        return True
    return normalized.casefold() in _LEGACY_MISSING_USER_VALUES


def normalize_user_value_for_storage(value: object) -> str | None:
    """EN: Convert missing/legacy values to None and preserve real user text as stripped string.
    RU: Преобразовать пустые/legacy-значения в None и сохранить реальный пользовательский текст как trimmed-строку.
    """

    if is_missing_user_value(value):
        return None
    return str(value).strip()


def normalize_user_value_for_output(value: object) -> str:
    """EN: Return sanitized text for payload output, using empty string for missing values.
    RU: Вернуть очищенный текст для payload-вывода, используя пустую строку для отсутствующих значений.
    """

    normalized = normalize_user_value_for_storage(value)
    return normalized or ""
