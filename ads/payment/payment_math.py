"""EN: Payment math for ads balance.
RU: Математика подсчёта баланса рекламы.
"""

from __future__ import annotations

import math


# Константы по ТЗ (не размазывать по проекту)
BANNER_COIN: float = 0.10
REWARDED_COIN: float = 0.30
BANNER_TIME_SEC: int = 10
BANNER_LOOK: int = 1000


def calc_banner_times(time_game_session_sec: float) -> int:
    """banner_times = floor(time_game_session_sec / banner_time)"""
    sec = float(time_game_session_sec)
    if sec <= 0:
        return 0
    return int(math.floor(sec / float(BANNER_TIME_SEC)))


def calc_banner_pay(time_game_session_sec: float) -> float:
    """
    banner_pay = (banner_coin * banner_times) / banner_look
    """
    banner_times = calc_banner_times(time_game_session_sec)
    return (BANNER_COIN * float(banner_times)) / float(BANNER_LOOK)


def calc_reward_pay(receive_click: int) -> float:
    """reward_pay = (reward_coin * receive_click) / 1000"""
    return (REWARDED_COIN * int(receive_click)) / 1000.0


def calc_balance(time_game_session_sec: float, receive_click: int) -> float:
    """balance = banner_pay + reward_pay"""
    return calc_banner_pay(time_game_session_sec) + calc_reward_pay(receive_click)


def format_balance(value: float) -> str:
    """
    Формат для UI без хардкода валюты.
    Чтобы не получить всегда '0.00' — держим 3 знака, без лишних нулей.
    """
    s = f"{float(value):.3f}"
    s = s.rstrip("0").rstrip(".")
    return s if s else "0"

