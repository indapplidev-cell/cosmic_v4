"""EN: Server-side loader for localized settings documents.
RU: Серверный загрузчик локализованных документов для экрана настроек.
"""

from __future__ import annotations

from pathlib import Path


_DOC_DIR = Path(__file__).resolve().parent / "content"
_DOC_NAME_TO_BASE = {
    "policy": "policy",
    "rules": "rule",
    "about": "about",
}
_ALLOWED_LANGS = {"ru", "en"}


def get_doc_content(doc_key: str, lang: str) -> dict:
    """EN: Return JSON payload with localized markdown document content.
    RU: Вернуть JSON-ответ с содержимым локализованного markdown-документа.

    EN: Supported keys are `policy`, `rules`, `about`; supported languages are
    `ru` and `en`. Unknown keys/languages return stable business errors.
    RU: Поддерживаются ключи `policy`, `rules`, `about`; языки `ru` и `en`.
    Неизвестные ключи/языки возвращают стабильные business-ошибки.
    """

    safe_key = (doc_key or "").strip().lower()
    safe_lang = (lang or "").strip().lower()

    if safe_key not in _DOC_NAME_TO_BASE:
        return {"ok": False, "error": "DOC_NOT_FOUND"}
    if safe_lang not in _ALLOWED_LANGS:
        return {"ok": False, "error": "LANG_NOT_SUPPORTED"}

    filename = f"{_DOC_NAME_TO_BASE[safe_key]}_{safe_lang}.md"
    doc_path = _DOC_DIR / filename
    try:
        text = doc_path.read_text(encoding="utf-8")
    except Exception:
        return {"ok": False, "error": "DOC_NOT_FOUND"}

    return {"ok": True, "doc_key": safe_key, "lang": safe_lang, "content": text}
