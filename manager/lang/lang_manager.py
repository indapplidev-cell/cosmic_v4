from __future__ import annotations

from data.lang.lang_reader import load_lang_dict
from data.user_cache.user_cache_profile import get_user_setting, set_user_setting


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
