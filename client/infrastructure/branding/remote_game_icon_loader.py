"""Remote game icon loader with user-data cache."""

from __future__ import annotations

import os
from threading import Lock

import requests

from client.app.config.assets import (
    get_cached_game_icon_source,
    get_game_icon_cache_path,
    get_game_icon_url,
)


_DOWNLOAD_LOCK = Lock()
_DOWNLOAD_ATTEMPTED = False
_REQUEST_TIMEOUT_SEC = 4


def resolve_game_icon_source() -> str:
    """Return a cached local source path or download the game icon once per session."""

    cached_source = get_cached_game_icon_source()
    if cached_source:
        return cached_source

    global _DOWNLOAD_ATTEMPTED
    with _DOWNLOAD_LOCK:
        cached_source = get_cached_game_icon_source()
        if cached_source:
            return cached_source
        if _DOWNLOAD_ATTEMPTED:
            return ""
        _DOWNLOAD_ATTEMPTED = True
        return _download_game_icon_to_cache()


def _download_game_icon_to_cache() -> str:
    """Download the remote game icon into user_data_dir cache and return its local source."""

    cache_path = get_game_icon_cache_path()
    tmp_path = cache_path.with_name(f"{cache_path.name}.tmp")
    try:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        response = requests.get(get_game_icon_url(), timeout=_REQUEST_TIMEOUT_SEC)
        if int(response.status_code) != 200:
            return ""
        payload = response.content or b""
        if not payload:
            return ""
        tmp_path.write_bytes(payload)
        if not tmp_path.is_file() or tmp_path.stat().st_size <= 0:
            return ""
        os.replace(tmp_path, cache_path)
        return get_cached_game_icon_source()
    except Exception:
        return ""
    finally:
        try:
            if tmp_path.exists():
                tmp_path.unlink()
        except Exception:
            pass
