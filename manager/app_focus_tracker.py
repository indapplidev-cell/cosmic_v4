"""EN: Track app focus/blur timestamps for Telegram open fallback decisions.
RU: Отслеживать таймстемпы фокуса/расфокуса приложения для решения по Telegram fallback.
"""

from __future__ import annotations

from time import time

last_blur_ts: float | None = None
last_focus_ts: float | None = None
last_focus_value: bool | None = None


def mark_blur() -> float:
    """EN: Store blur timestamp and return it.
    RU: Сохранить время ухода приложения в background и вернуть его.
    """

    global last_blur_ts, last_focus_value
    last_blur_ts = float(time())
    last_focus_value = False
    return last_blur_ts


def mark_focus() -> float:
    """EN: Store focus timestamp and return it.
    RU: Сохранить время возврата фокуса приложения и вернуть его.
    """

    global last_focus_ts, last_focus_value
    last_focus_ts = float(time())
    last_focus_value = True
    return last_focus_ts


def went_background_within(seconds: int | float, since_ts: float) -> bool:
    """EN: Check whether blur happened inside [since_ts, since_ts+seconds].
    RU: Проверить, был ли blur в интервале [since_ts, since_ts+seconds].
    """

    if last_blur_ts is None:
        return False
    start = float(since_ts)
    end = start + float(seconds)
    return start <= float(last_blur_ts) <= end
