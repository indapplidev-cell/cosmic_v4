"""Server-side branding asset helpers."""

from __future__ import annotations

from pathlib import Path


_HEADER_LOGO_PATH = Path(__file__).resolve().parent / "content" / "e2m_logo_header_white_1024.png"
_GAME_ICON_PATH = Path(__file__).resolve().parent / "content" / "e2m_game_512.png"
_PROFILE_ICON_PATH = Path(__file__).resolve().parent / "content" / "e2m_icon_512.png"


def get_e2m_header_logo_path() -> Path:
    """Return the absolute path to the public e2m header logo PNG."""

    return _HEADER_LOGO_PATH


def e2m_header_logo_exists() -> bool:
    """Return whether the public e2m header logo PNG exists."""

    return get_e2m_header_logo_path().is_file()


def get_e2m_game_icon_path() -> Path:
    """Return the absolute path to the public e2m game icon PNG."""

    return _GAME_ICON_PATH


def e2m_game_icon_exists() -> bool:
    """Return whether the public e2m game icon PNG exists."""

    return get_e2m_game_icon_path().is_file()


def get_e2m_profile_icon_path() -> Path:
    """Return the absolute path to the public e2m profile icon PNG."""

    return _PROFILE_ICON_PATH


def e2m_profile_icon_exists() -> bool:
    """Return whether the public e2m profile icon PNG exists."""

    return get_e2m_profile_icon_path().is_file()
