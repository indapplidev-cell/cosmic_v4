"""EN: Window configuration for desktop runs.
RU: Конфигурация окна для десктопного запуска.
"""

import os

from kivy.core.window import Window
from kivy.utils import platform as kivy_platform


def apply_window_config() -> None:
    """EN: Apply window settings for desktop and keep mobile platforms unmanaged.
    RU: Применить настройки окна для десктопа и не управлять размером окна на мобильных платформах.
    """
    if kivy_platform in ("android", "ios"):
        return

    size_raw = os.getenv("COSMIC_WINDOW_SIZE", "").strip()
    if size_raw and "x" in size_raw:
        parts = size_raw.lower().split("x", maxsplit=1)
        try:
            width = int(parts[0].strip())
            height = int(parts[1].strip())
            Window.size = (width, height)
            Window.maximize()
            return
        except ValueError:
            pass

    Window.size = (1008, 567)
    Window.maximize()
