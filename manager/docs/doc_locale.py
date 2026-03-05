"""EN: Locale-aware document path and title selection for settings documents.
RU: Выбор локализованных путей и заголовков документов для экрана настроек.
"""

from __future__ import annotations

from manager.lang.lang_manager import lang, t

_SUPPORTED = {"ru", "en"}
_DOC_BASES = {"privacy_policy", "game_rules"}


def _normalize_lang(code: str | None) -> str:
    """EN: Normalize any language code to "ru"/"en" with "ru" as default.
    RU: Нормализовать любой код языка к "ru"/"en" с "ru" по умолчанию.
    """
    raw = (code or "").strip().replace("-", "_").lower()
    if raw in _SUPPORTED:
        return raw
    if raw.startswith("en"):
        return "en"
    if raw.startswith("ru"):
        return "ru"
    return "ru"


def get_lang_code() -> str:
    """EN: Return current app language code from lang manager as "ru" or "en".
    RU: Вернуть текущий код языка приложения из lang manager как "ru" или "en".
    """
    return _normalize_lang(getattr(lang, "code", "ru"))


def doc_path(base_name: str, lang: str | None = None) -> str:
    """EN: Build localized docs path for privacy policy or game rules.
    RU: Сформировать локализованный путь docs для политики или правил игры.
    """
    if base_name not in _DOC_BASES:
        raise ValueError(f"Unsupported document base name: {base_name}")
    code = _normalize_lang(lang) if lang is not None else get_lang_code()
    return f"docs/{base_name}_{code}.md"


def doc_title(base_name: str) -> str:
    """EN: Return localized document title, using i18n key first, then fallback.
    RU: Вернуть локализованный заголовок документа: сначала i18n-ключ, затем fallback.
    """
    code = get_lang_code()
    key_map = {
        "privacy_policy": "settings.docs.privacy_policy_title",
        "game_rules": "settings.docs.game_rules_title",
    }
    if base_name not in key_map:
        raise ValueError(f"Unsupported document base name: {base_name}")

    translated = t(key_map[base_name])
    if translated and translated != key_map[base_name]:
        return translated

    fallback = {
        "privacy_policy": {
            "ru": "Политика конфиденциальности",
            "en": "Privacy Policy",
        },
        "game_rules": {
            "ru": "Правила игры",
            "en": "Game Rules",
        },
    }
    return fallback[base_name][code]

