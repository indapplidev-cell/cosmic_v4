# -*- coding: utf-8 -*-
"""
Ship world-space geometry model with no rendering dependencies.

RU: Модель геометрии корабля в мировых координатах без зависимостей от рендера.
"""

from typing import List, Tuple


class ShipModel:
    """
    Compute ship world-space triangle points based on screen size and config.

    The model contains no Kivy objects and only produces world-space points
    for gameplay logic such as collisions.

    RU: Вычисляет точки треугольника корабля в мировых координатах на основе
    размеров экрана и конфигурации.

    Модель не содержит объектов Kivy и возвращает только мировые точки для
    игровой логики, например коллизий.
    """
    def __init__(self):
        """
        Initialize storage for the last computed world points.

        RU: Инициализирует хранилище для последних вычисленных мировых точек.
        """
        self._last_world_points: List[Tuple[float, float]] = [(0, 0), (0, 0), (0, 0)]

    def compute_world_points(self, width: float, height: float, config):
        """
        Compute and return ship triangle points in world coordinates.

        Uses SHIP_WIDTH, SHIP_HEIGHT, and SHIP_BASE_Y from the config and
        centers the ship horizontally at width / 2.

        RU: Вычисляет и возвращает точки треугольника корабля в мировых координатах.
        Использует SHIP_WIDTH, SHIP_HEIGHT и SHIP_BASE_Y из конфигурации и
        центрирует корабль по X в width / 2.
        """
        center_x = width / 2
        base_y = config.SHIP_BASE_Y * height
        ship_half_width = config.SHIP_WIDTH * width / 2
        ship_height = config.SHIP_HEIGHT * height

        self._last_world_points = [
            (center_x - ship_half_width, base_y),
            (center_x, base_y + ship_height),
            (center_x + ship_half_width, base_y),
        ]
        return list(self._last_world_points)

    def get_last_world_points(self):
        """
        Return the last computed world-space ship points.

        RU: Возвращает последние вычисленные мировые точки корабля.
        """
        return list(self._last_world_points)
