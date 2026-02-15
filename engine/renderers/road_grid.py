"""
Renderer for road grid lines using Kivy Line instructions.

RU: Рендерер дорожной сетки на базе Kivy Line.
"""

from kivy.graphics.context_instructions import Color
from kivy.graphics.vertex_instructions import Line


class RoadGridRenderer:
    """
    Create and update Kivy line objects for the road grid.

    RU: Создаёт и обновляет Kivy-линии для дорожной сетки.
    """
    def __init__(self, canvas, config):
        """
        Initialize line lists and allocate Line objects on the canvas.

        RU: Инициализирует списки линий и создаёт Line-объекты на canvas.
        """
        self._config = config
        self.vertical_lines = []
        self.horizontal_lines = []
        self._init_lines(canvas)

    def _init_lines(self, canvas):
        """
        Allocate vertical and horizontal Line objects with white color.

        RU: Создаёт вертикальные и горизонтальные линии белого цвета.
        """
        with canvas:
            Color(1, 1, 1)
            for _ in range(0, self._config.V_NB_LINES):
                self.vertical_lines.append(Line())
            for _ in range(0, self._config.H_NB_LINES):
                self.horizontal_lines.append(Line())

    def update(self, state, perspective, geometry, width, height, config):
        """
        Update all line points based on current state and geometry.

        RU: Обновляет точки всех линий на основе текущего состояния и геометрии.
        """
        self._update_vertical_lines(state, perspective, geometry, width, height, config)
        self._update_horizontal_lines(state, perspective, geometry, width, height, config)

    def _update_vertical_lines(self, state, perspective, geometry, width, height, config):
        """
        Update vertical grid lines using geometry and perspective transform.

        RU: Обновляет вертикальные линии сетки через геометрию и перспективу.
        """
        start_index, end_index = geometry.vertical_line_range(config)
        ppx = perspective.perspective_point_x
        for idx in range(start_index, end_index + 1):
            pos = idx - start_index
            line_x = geometry.get_line_x_from_index(
                idx,
                width,
                ppx,
                state.current_offset_x,
                config,
            )
            x1, y1 = perspective.transform(line_x, 0, height)
            x2, y2 = perspective.transform(line_x, height, height)
            self.vertical_lines[pos].points = [x1, y1, x2, y2]

    def _update_horizontal_lines(self, state, perspective, geometry, width, height, config):
        """
        Update horizontal grid lines using geometry and perspective transform.

        RU: Обновляет горизонтальные линии сетки через геометрию и перспективу.
        """
        start_index, end_index = geometry.vertical_line_range(config)
        ppx = perspective.perspective_point_x
        ppy = perspective.perspective_point_y
        xmin = geometry.get_line_x_from_index(
            start_index,
            width,
            ppx,
            state.current_offset_x,
            config,
        )
        xmax = geometry.get_line_x_from_index(
            end_index,
            width,
            ppx,
            state.current_offset_x,
            config,
        )
        for i in range(0, config.H_NB_LINES):
            line_y = geometry.get_line_y_from_index(
                i,
                height,
                ppy,
                state.current_offset_y,
                config,
            )
            x1, y1 = perspective.transform(xmin, line_y, height)
            x2, y2 = perspective.transform(xmax, line_y, height)
            self.horizontal_lines[i].points = [x1, y1, x2, y2]
