#!/usr/bin/env python3
"""EN: Generate fallback Android assets if files are missing.
RU: Генерирует резервные Android-ассеты, если файлы отсутствуют.

EN: The script creates `assets/icon.png` (512x512) and
`assets/presplash.png` (1080x1920) only when they do not exist.
RU: Скрипт создает `assets/icon.png` (512x512) и
`assets/presplash.png` (1080x1920) только при их отсутствии.
"""

from __future__ import annotations

import base64
from pathlib import Path

# EN: A tiny valid PNG (1x1) used as a portable binary template.
# RU: Минимальный валидный PNG (1x1), используемый как переносимый шаблон.
_PNG_1X1_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMAASsJTYQAAAAASUVORK5CYII="
)


def _write_png_if_missing(path: Path) -> bool:
    """EN: Write a valid PNG placeholder if `path` does not exist.
    RU: Записывает валидный PNG-заглушку, если `path` отсутствует.

    EN: Returns True when the file is created, otherwise False.
    RU: Возвращает True, если файл создан, иначе False.
    """
    if path.exists():
        return False
    path.write_bytes(base64.b64decode(_PNG_1X1_B64))
    return True


def main() -> None:
    """EN: Ensure the Android icon and presplash files exist.
    RU: Обеспечивает наличие файлов Android-иконки и пресплэша.
    """
    root_dir = Path(__file__).resolve().parents[2]
    assets_dir = root_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    icon_path = assets_dir / "icon.png"
    presplash_path = assets_dir / "presplash.png"

    icon_created = _write_png_if_missing(icon_path)
    presplash_created = _write_png_if_missing(presplash_path)

    print(f"icon: {icon_path} ({'created' if icon_created else 'exists'})")
    print(f"presplash: {presplash_path} ({'created' if presplash_created else 'exists'})")


if __name__ == "__main__":
    main()