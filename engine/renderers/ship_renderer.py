# -*- coding: utf-8 -*-
"""
Ship renderer that projects world points to screen using Kivy graphics.

RU: Рендерер корабля, проецирующий мировые точки на экран средствами Kivy.
"""

from kivy.graphics.context_instructions import Color
from kivy.graphics.vertex_instructions import Triangle


class ShipRenderer:
    """
    Render the ship triangle using a Kivy Triangle instruction.

    The renderer applies the perspective transform to world points and
    updates the triangle on the canvas; it does not compute geometry.

    RU: Рендерит треугольник корабля через Kivy Triangle.

    Рендерер применяет перспективное преобразование к мировым точкам и
    обновляет треугольник на canvas, но не вычисляет геометрию.
    """
    def __init__(self, canvas):
        """
        Create the Triangle instruction and set its color on the canvas.

        RU: Создает инструкцию Triangle и задает цвет на canvas.
        """
        with canvas:
            Color(0, 0, 0)
            self._triangle = Triangle()

    def update(self, world_points, perspective, height):
        """
        Project world points to screen space and update triangle points.

        RU: Проецирует мировые точки в экранные координаты и обновляет
        точки треугольника.
        """
        x1, y1 = perspective.transform(*world_points[0], height)
        x2, y2 = perspective.transform(*world_points[1], height)
        x3, y3 = perspective.transform(*world_points[2], height)

        self._triangle.points = [x1, y1, x2, y2, x3, y3]
