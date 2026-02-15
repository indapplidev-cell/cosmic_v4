"""
Kivy renderer for tile quads based on the tile model.

RU: Kivy-рендерер тайловых квадов на основе модели тайлов.
"""

from kivy.graphics.context_instructions import Color
from kivy.graphics.vertex_instructions import Quad


class TilesRenderer:
    """
    Allocate and update Kivy Quad objects for tiles.

    RU: Создаёт и обновляет Kivy Quad объекты для тайлов.
    """
    def __init__(self, canvas, config):
        """
        Initialize quad list on the given canvas.

        RU: Инициализирует список квадов на указанном canvas.
        """
        self._config = config
        self._tiles = []
        self._init_quads(canvas)

    def _init_quads(self, canvas):
        """
        Create the Quad objects and set drawing color.

        RU: Создаёт Quad-объекты и устанавливает цвет рисования.
        """
        with canvas:
            Color(1, 1, 1)
            for _ in range(0, self._config.NB_TILES):
                self._tiles.append(Quad())

    def update(self, model, state, perspective, geometry, width, height, config):
        """
        Update quad points from model coordinates using geometry and perspective.

        RU: Обновляет точки квадов по координатам модели через геометрию и перспективу.
        """
        ppx = perspective.perspective_point_x
        ppy = perspective.perspective_point_y
        for i in range(0, config.NB_TILES):
            tile = self._tiles[i]
            tile_coordinates = model.tiles_coordinates[i]
            xmin, ymin, xmax, ymax = geometry.get_tile_rect_world(
                tile_coordinates[0],
                tile_coordinates[1],
                state,
                width,
                height,
                ppx,
                ppy,
                config,
            )

            x1, y1 = perspective.transform(xmin, ymin, height)
            x2, y2 = perspective.transform(xmin, ymax, height)
            x3, y3 = perspective.transform(xmax, ymax, height)
            x4, y4 = perspective.transform(xmax, ymin, height)

            tile.points = [x1, y1, x2, y2, x3, y3, x4, y4]
