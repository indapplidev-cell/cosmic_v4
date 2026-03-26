from __future__ import annotations

from data.lang.lang_reader import load_lang_dict
from data.user_cache.user_cache_profile import get_user_setting, set_user_setting


def _build_no_data_variants() -> set[str]:
    """EN: Collect normalized `common.no_data` translations across supported dictionaries.
    RU: Собрать нормализованные переводы `common.no_data` из всех поддерживаемых словарей.
    """
    variants: set[str] = {"no data"}
    for code in ("ru", "en"):
        translated = load_lang_dict(code).get("common.no_data")
        if isinstance(translated, str):
            normalized = translated.strip().casefold()
            if normalized:
                variants.add(normalized)
    return variants


_NO_DATA_VARIANTS = _build_no_data_variants()
_LEGACY_USER_VALUE_VARIANTS = _NO_DATA_VARIANTS | {"new_login", "none", "null"}


class LangManager:
    def __init__(self, code: str = "ru") -> None:
        self._code = self._normalize_code(code)
        self._dict: dict[str, str] = load_lang_dict(self._code)

    def _normalize_code(self, code: str) -> str:
        """
        Normalize a language code to a supported value.

        EN: Falls back to `ru` for empty or unsupported codes.
        RU: Возвращает `ru` для пустых или неподдерживаемых кодов.
        """
        normalized = (code or "").strip().lower()
        return normalized if normalized in {"ru", "en"} else "ru"

    @property
    def code(self) -> str:
        return self._code

    def set_lang(self, code: str, persist: bool = False) -> None:
        """
        Apply a language code and optionally persist it.

        EN: Updates in-memory translations immediately and saves to profile settings when requested.
        RU: Сразу обновляет переводы в памяти и сохраняет их в профиль настроек при необходимости.
        """
        code = self._normalize_code(code)
        if code == self._code:
            if persist:
                set_user_setting("lang", code)
            return
        self._code = code
        self._dict = load_lang_dict(code)
        if persist:
            set_user_setting("lang", code)

    def bootstrap_from_profile(self) -> None:
        """
        Restore persisted language from unified profile settings.

        EN: Loads the saved language before screen construction without forcing a second storage path.
        RU: Загружает сохранённый язык до построения экранов без второго пути хранения.
        """
        self.set_lang(str(get_user_setting("lang", self._code or "ru")), persist=False)

    def t(self, key: str) -> str:
        if not key:
            return ""
        value = self._dict.get(key)
        return value if isinstance(value, str) else key


lang = LangManager()


def t(key: str) -> str:
    return lang.t(key)


def is_missing_user_value(value: object) -> bool:
    """EN: Detect empty and legacy placeholder values for user-facing profile data.
    RU: Определить пустые и legacy placeholder-значения для пользовательских данных в UI.

    EN: Values like empty string, `None`, `null`, `new_login`, and translated `No data`
    placeholders are treated as missing user data rather than real profile content.
    RU: Значения вроде пустой строки, `None`, `null`, `new_login` и переведённых заглушек
    `Нет данных` считаются отсутствующими данными, а не реальным содержимым профиля.
    """
    normalized = str(value or "").strip()
    if not normalized:
        return True
    return normalized.casefold() in _LEGACY_USER_VALUE_VARIANTS


def user_value_for_storage(value: object) -> str:
    """EN: Normalize user-facing cache values before persistence.
    RU: Нормализовать пользовательские cache-значения перед сохранением.

    EN: Missing or legacy placeholder values are collapsed to an empty string so they do not
    circulate through cache and UI as if they were real user data.
    RU: Отсутствующие и legacy placeholder-значения схлопываются в пустую строку, чтобы они
    не гуляли по кэшу и UI как будто это настоящие данные пользователя.
    """
    return "" if is_missing_user_value(value) else str(value or "").strip()


def user_value_text(value: object) -> str:
    """EN: Render user-facing profile values using the single localized `common.no_data` fallback.
    RU: Отрисовать пользовательские значения профиля через единый локализованный fallback `common.no_data`.
    """
    normalized = user_value_for_storage(value)
    return normalized if normalized else t("common.no_data")


def topbar_value_text(value: object) -> str:
    """EN: Normalize shared top-bar user/login text through the unified user-value fallback.
    RU: Нормализовать текст пользователя/логина в верхней панели через единый fallback пользовательских данных.
    """
    return user_value_text(value)
