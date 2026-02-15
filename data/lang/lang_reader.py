from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _lang_path(code: str) -> Path:
    return Path(__file__).resolve().parent / f"{code}.json"


def load_lang_dict(code: str) -> dict[str, str]:
    path = _lang_path(code)
    if not path.exists():
        return {}

    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return {}

    if not raw.strip():
        return {}

    try:
        data: Any = json.loads(raw)
    except json.JSONDecodeError:
        return {}

    if not isinstance(data, dict):
        return {}

    out: dict[str, str] = {}
    for k, v in data.items():
        if isinstance(k, str) and isinstance(v, str):
            out[k] = v
    return out
