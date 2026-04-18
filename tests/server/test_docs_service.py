"""EN: Tests for server-side localized settings documents loader.
RU: Тесты серверного загрузчика локализованных документов настроек.
"""

from __future__ import annotations

from pathlib import Path

from server.app.docs import docs_service


def test_get_doc_content_reads_from_docs_content_directory() -> None:
    """EN: Loader must read existing markdown from the real docs/content directory.
    RU: Загрузчик должен читать существующий markdown из реального каталога docs/content.
    """

    expected_dir = Path(docs_service.__file__).resolve().parent / "content"

    assert docs_service._DOC_DIR == expected_dir

    result = docs_service.get_doc_content("policy", "ru")

    assert result["ok"] is True
    assert result["doc_key"] == "policy"
    assert result["lang"] == "ru"
    assert isinstance(result["content"], str)
    assert result["content"].strip()


def test_get_doc_content_returns_doc_not_found_when_file_missing(monkeypatch, tmp_path) -> None:
    """EN: Missing file in the configured docs directory must keep stable DOC_NOT_FOUND response.
    RU: Отсутствующий файл в настроенном каталоге документов должен сохранять стабильный ответ DOC_NOT_FOUND.
    """

    monkeypatch.setattr(docs_service, "_DOC_DIR", tmp_path)

    result = docs_service.get_doc_content("policy", "ru")

    assert result == {"ok": False, "error": "DOC_NOT_FOUND"}
