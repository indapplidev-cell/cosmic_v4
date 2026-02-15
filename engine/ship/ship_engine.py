# -*- coding: utf-8 -*-
"""
Facade that coordinates ship model computation and rendering.

RU: Фасад, который связывает вычисления модели корабля и его рендер.
"""

from engine.renderers.ship_renderer import ShipRenderer
from engine.ship.ship_model import ShipModel


class ShipEngine:
    """
    Compute ship world points and render them using the provided canvas.

    The engine delegates geometry to ShipModel and rendering to ShipRenderer
    while keeping a simple update/get API for game logic.

    RU: Вычисляет мировые точки корабля и отрисовывает их на canvas.

    Движок делегирует геометрию ShipModel и рендер ShipRenderer, сохраняя
    простой API update/get для игровой логики.
    """
    def __init__(self, canvas, config):
        """
        Initialize ship model and renderer using the given canvas and config.

        RU: Инициализирует модель корабля и рендерер, используя canvas и конфиг.
        """
        self._config = config
        self._model = ShipModel()
        self._renderer = ShipRenderer(canvas)

    def update(self, perspective, size):
        """
        Compute world points and update the rendered ship triangle.

        RU: Вычисляет мировые точки и обновляет отрисованный треугольник корабля.
        """
        width, height = size
        world_points = self._model.compute_world_points(width, height, self._config)
        self._renderer.update(world_points, perspective, height)

    def get_ship_points_world(self):
        """
        Return the last computed ship points in world coordinates.

        RU: Возвращает последние вычисленные точки корабля в мировых координатах.
        """
        return self._model.get_last_world_points()

    def reset_to_start(self, state) -> None:
        """
        Reset the ship horizontal position to the starting center lane.

        EN: Sets the horizontal offset to zero and clears horizontal speed so
        the ship restarts centered without altering score or vertical progress.
        RU: Сбрасывает горизонтальное смещение в ноль и обнуляет скорость по X,
        чтобы корабль снова оказался по центру, не трогая очки и вертикальный
        прогресс.
        """
        state.current_offset_x = 0.0
        state.current_speed_x = 0
