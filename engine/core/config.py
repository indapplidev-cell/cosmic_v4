"""
Static configuration constants for gameplay geometry and movement.

RU: Статические константы конфигурации для геометрии и движения игры.
"""


class GameConfig:
    """
    Container for numeric tuning values used across the engine.

    RU: Контейнер числовых параметров, используемых по всему движку.
    """
    V_NB_LINES = 8
    V_LINES_SPACING = 0.4

    H_NB_LINES = 15
    H_LINES_SPACING = 0.1

    SPEED = 0.8
    SPEED_X = 3.0
    SPEED_Y_SLOWDOWN_FACTOR: float = 0.35
    SPEED_Y_BRAKE_FACTOR: float = 0.1

    NB_TILES = 16
    INPUT_STEPS_TO_EDGE = 3

    SHIP_WIDTH = 0.1
    SHIP_HEIGHT = 0.035
    SHIP_BASE_Y = 0.04
