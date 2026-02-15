"""EN: Window configuration for desktop runs.
RU: Конфигурация окна для десктопного запуска.
"""

import os

from kivy.core.window import Window


def apply_window_config() -> None:
    """EN: Apply window size for landscape desktop runs.
    RU: Применить размер окна для ландшафтного десктопного запуска.
    """
    size_raw = os.getenv("COSMIC_WINDOW_SIZE", "").strip()
    if size_raw and "x" in size_raw:
        parts = size_raw.lower().split("x", maxsplit=1)
        try:
            width = int(parts[0].strip())
            height = int(parts[1].strip())
            Window.size = (width, height)
            return
        except ValueError:
            pass

    Window.size = (1008, 567)
