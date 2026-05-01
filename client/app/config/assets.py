"""Application asset path helpers."""

from __future__ import annotations

from pathlib import Path

from kivy.app import App

from client.app.config.config import API_BASE_URL


CLIENT_ROOT = Path(__file__).resolve().parents[2]
LOAD_BACKGROUND_PATH = CLIENT_ROOT / "assets" / "images" / "e2m_bg_download.png"
HEADER_LOGO_ROUTE = "/branding/e2m_logo_header_white_1024.png"
HEADER_LOGO_FILENAME = "e2m_logo_header_white_1024.png"
GAME_ICON_ROUTE = "/branding/e2m_game_512.png"
GAME_ICON_FILENAME = "e2m_game_512.png"
PROFILE_ICON_ROUTE = "/branding/e2m_icon_512.png"
PROFILE_ICON_FILENAME = "e2m_icon_512.png"


def get_load_background_path() -> Path:
    """Return the absolute path to the startup loading background image."""

    return LOAD_BACKGROUND_PATH


def get_load_background_source() -> str:
    """Return the loading background source or an empty string when unavailable."""

    path = get_load_background_path()
    return str(path) if path.is_file() else ""


def get_header_logo_url() -> str:
    """Return the backend URL for the public e2m header logo PNG."""

    return f"{API_BASE_URL}{HEADER_LOGO_ROUTE}"


def get_header_logo_cache_path() -> Path:
    """Return the writable user-data cache path for the e2m header logo PNG."""

    app = App.get_running_app()
    user_data_dir = Path(getattr(app, "user_data_dir", Path.cwd()))
    return user_data_dir / "branding" / HEADER_LOGO_FILENAME


def get_cached_header_logo_source() -> str:
    """Return the cached header logo source when the local PNG already exists."""

    path = get_header_logo_cache_path()
    return str(path) if path.is_file() and path.stat().st_size > 0 else ""


def get_game_icon_url() -> str:
    """Return the backend URL for the public e2m game icon PNG."""

    return f"{API_BASE_URL}{GAME_ICON_ROUTE}"


def get_game_icon_cache_path() -> Path:
    """Return the writable user-data cache path for the e2m game icon PNG."""

    app = App.get_running_app()
    user_data_dir = Path(getattr(app, "user_data_dir", Path.cwd()))
    return user_data_dir / "branding" / GAME_ICON_FILENAME


def get_cached_game_icon_source() -> str:
    """Return the cached game icon source when the local PNG already exists."""

    path = get_game_icon_cache_path()
    return str(path) if path.is_file() and path.stat().st_size > 0 else ""


def get_profile_icon_url() -> str:
    """Return the backend URL for the public e2m profile icon PNG."""

    return f"{API_BASE_URL}{PROFILE_ICON_ROUTE}"


def get_profile_icon_cache_path() -> Path:
    """Return the writable user-data cache path for the e2m profile icon PNG."""

    app = App.get_running_app()
    user_data_dir = Path(getattr(app, "user_data_dir", Path.cwd()))
    return user_data_dir / "branding" / PROFILE_ICON_FILENAME


def get_cached_profile_icon_source() -> str:
    """Return the cached profile icon source when the local PNG already exists."""

    path = get_profile_icon_cache_path()
    return str(path) if path.is_file() and path.stat().st_size > 0 else ""
