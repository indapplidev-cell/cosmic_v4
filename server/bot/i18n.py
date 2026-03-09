"""EN: Minimal bot i18n helper backed by shared app language dictionaries.
RU: Минимальный i18n-хелпер бота на базе общих словарей языков приложения.
"""

from __future__ import annotations

import json
from pathlib import Path


_ROOT = Path(__file__).resolve().parents[2]
_LANG_DIR = _ROOT / "data" / "lang"


def _load_lang(code: str) -> dict[str, str]:
    """EN: Load language dictionary file safely with fallback to empty dict.
    RU: Безопасно загрузить словарь языка из файла с fallback на пустой dict.
    """

    path = _LANG_DIR / f"{code}.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return {str(k): str(v) for k, v in data.items()}
    except Exception:
        return {}
    return {}


_RU = _load_lang("ru")
_EN = _load_lang("en")


def t_bot(lang_code: str | None, key: str, **kwargs) -> str:
    """EN: Resolve bot text by key with RU/EN fallback and optional format kwargs.
    RU: Получить текст бота по ключу с fallback RU/EN и опциональным форматированием kwargs.
    """

    code = str((lang_code or "ru")).lower()
    base = _EN if code.startswith("en") else _RU
    text = base.get(key) or _EN.get(key) or _RU.get(key) or key
    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text
