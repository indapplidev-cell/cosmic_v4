from __future__ import annotations

from data.lang.lang_reader import load_lang_dict


class LangManager:
    def __init__(self, code: str = "ru") -> None:
        self._code = code
        self._dict: dict[str, str] = load_lang_dict(code)

    @property
    def code(self) -> str:
        return self._code

    def set_lang(self, code: str) -> None:
        code = (code or "").strip().lower()
        if not code or code == self._code:
            return
        self._code = code
        self._dict = load_lang_dict(code)

    def t(self, key: str) -> str:
        if not key:
            return ""
        value = self._dict.get(key)
        return value if isinstance(value, str) else key


lang = LangManager()


def t(key: str) -> str:
    return lang.t(key)
