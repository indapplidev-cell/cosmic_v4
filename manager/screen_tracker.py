"""EN: Central screen tracking helper for stable navigation and ads diagnostics.
RU: Центральный хелпер отслеживания экранов для стабильной навигационной и ads-диагностики.
"""

from __future__ import annotations


def normalize_screen_name(raw: object) -> str:
    """EN: Map internal route/screen identifiers to the fixed public log names.
    RU: Сопоставить внутренние route/screen идентификаторы с фиксированными публичными именами в логах.
    """

    value = str(raw or "").strip().lower()
    if value in {"start", "startscreen", "startscreenview"}:
        return "Start"
    if value in {"profile", "profilescreen", "profilescreenview"}:
        return "Profile"
    if value in {"profile_change", "profilechange", "profilechangeview", "profilechangescreen", "edit"}:
        return "Edit"
    if value in {"settings", "settingsscreen", "settingsscreenview"}:
        return "Settings"
    if value in {"game", "gamescreen", "gamescreenview"}:
        return "Game"
    return "Unknown"


class ScreenTracker:
    """EN: Tiny singleton-like holder used as the single source of truth for current screen logs.
    RU: Небольшой singleton-подобный контейнер, используемый как единый источник истины для логов текущего экрана.
    """

    current_screen: str = "Unknown"
    prev_screen: str | None = None

    @classmethod
    def set_screen(cls, name: str, reason: str = "nav") -> bool:
        """EN: Update tracked screen and emit one transition log block only when the value changed.
        RU: Обновить отслеживаемый экран и выдать один блок логов перехода только если значение изменилось.
        """

        new_screen = normalize_screen_name(name)
        old_screen = str(cls.current_screen or "Unknown")
        if old_screen == new_screen:
            return False
        cls.prev_screen = old_screen
        cls.current_screen = new_screen
        print(f"[NAV] screen_change from={old_screen} to={new_screen} reason={reason}", flush=True)
        if old_screen != "Unknown":
            print(f"[NAV] screen_exit screen={old_screen}", flush=True)
        print(f"[NAV] screen_enter screen={new_screen}", flush=True)
        return True

    @classmethod
    def get_screen(cls) -> str:
        """EN: Return the latest tracked screen name.
        RU: Вернуть последнее отслеженное имя экрана.
        """

        return str(cls.current_screen or "Unknown")
