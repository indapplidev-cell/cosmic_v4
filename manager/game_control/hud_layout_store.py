"""EN: Persistent HUD touch-layout swap flag storage.
RU: Постоянное хранилище флага перестановки тач-раскладки HUD.
"""

from __future__ import annotations

from data.user_cache.user_cache_profile import get_user_setting, set_user_setting


def get_swapped() -> bool:
    """EN: Return stored swapped flag from unified profile settings.
    RU: Вернуть сохранённый флаг swapped из единого профиля настроек.
    """
    return bool(get_user_setting("hud_layout_swapped", False))


def set_swapped(val: bool) -> None:
    """EN: Persist swapped flag into unified profile settings.
    RU: Сохранить флаг swapped в единый профиль настроек.
    """
    set_user_setting("hud_layout_swapped", bool(val))


def toggle_swapped() -> bool:
    """EN: Toggle stored swapped flag and return the new value.
    RU: Переключить сохранённый флаг swapped и вернуть новое значение.
    """
    new_val = not get_swapped()
    set_swapped(new_val)
    return new_val
