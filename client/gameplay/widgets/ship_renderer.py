# -*- coding: utf-8 -*-
"""Ship renderer that draws a screen-space ship triangle."""

from kivy.graphics.context_instructions import Color
from kivy.graphics.vertex_instructions import Triangle


class ShipRenderer:
    """Render the ship triangle using precomputed screen coordinates."""

    def __init__(self, canvas):
        self._color = Color(0, 0, 0)
        self._triangle = Triangle()
        canvas.add(self._color)
        canvas.add(self._triangle)

    def update(self, world_points):
        x1, y1 = world_points[0]
        x2, y2 = world_points[1]
        x3, y3 = world_points[2]
        self._triangle.points = [x1, y1, x2, y2, x3, y3]
