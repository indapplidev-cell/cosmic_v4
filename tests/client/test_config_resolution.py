from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest


MODULE_NAME = "client.app.config.config"


def _load_config_module(monkeypatch, root_env_text: str | None, extra_env: dict[str, str] | None = None):
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("API_BASE_URL", raising=False)

    for key, value in (extra_env or {}).items():
        monkeypatch.setenv(key, value)

    repo_root_env = Path(__file__).resolve().parents[2] / ".env"
    original_exists = Path.exists
    original_read_text = Path.read_text

    def fake_exists(path: Path) -> bool:
        if path == repo_root_env:
            return root_env_text is not None
        return original_exists(path)

    def fake_read_text(path: Path, encoding: str | None = None, *args, **kwargs) -> str:
        if path == repo_root_env:
            if root_env_text is None:
                raise FileNotFoundError(path)
            return root_env_text
        return original_read_text(path, encoding=encoding, *args, **kwargs)

    monkeypatch.setattr(Path, "exists", fake_exists)
    monkeypatch.setattr(Path, "read_text", fake_read_text)
    sys.modules.pop(MODULE_NAME, None)
    importlib.invalidate_caches()
    return importlib.import_module(MODULE_NAME)


def test_client_config_loads_api_base_url_from_root_env(monkeypatch) -> None:
    config_module = _load_config_module(
        monkeypatch,
        "APP_ENV=production\nAPI_BASE_URL=https://tg.escape2mars.space/\n",
    )

    assert config_module.APP_ENV == "production"
    assert config_module.API_BASE_URL == "https://tg.escape2mars.space"


def test_client_config_loads_missing_api_base_url_from_root_env_when_app_env_already_set(monkeypatch) -> None:
    config_module = _load_config_module(
        monkeypatch,
        "API_BASE_URL=https://tg.escape2mars.space\n",
        extra_env={"APP_ENV": "production"},
    )

    assert config_module.APP_ENV == "production"
    assert config_module.API_BASE_URL == "https://tg.escape2mars.space"


def test_client_config_does_not_override_process_api_base_url_from_root_env(monkeypatch) -> None:
    config_module = _load_config_module(
        monkeypatch,
        "APP_ENV=production\nAPI_BASE_URL=https://tg.escape2mars.space\n",
        extra_env={"API_BASE_URL": "https://override.example.com"},
    )

    assert config_module.APP_ENV == "production"
    assert config_module.API_BASE_URL == "https://override.example.com"


def test_client_config_uses_localhost_fallback_in_dev(monkeypatch) -> None:
    config_module = _load_config_module(
        monkeypatch,
        None,
        extra_env={"APP_ENV": "dev", "API_BASE_URL": "   "},
    )

    assert config_module.API_BASE_URL == "http://127.0.0.1:8000"


def test_client_config_requires_api_base_url_in_production(monkeypatch) -> None:
    with pytest.raises(RuntimeError):
        _load_config_module(
            monkeypatch,
            None,
            extra_env={"APP_ENV": "production", "API_BASE_URL": "   "},
        )
