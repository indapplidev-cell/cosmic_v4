"""
Pure geometry calculations for road lines and tile rectangles.

RU: Чистые геометрические вычисления для дорожных линий и прямоугольников тайлов.
"""


class RoadGeometry:
    """
    Provide stateless helpers for road and tile coordinates.

    RU: Предоставляет статeless-хелперы для координат дороги и тайлов.
    """
    def vertical_line_range(self, config):
        """
        Compute the inclusive index range for vertical grid lines.

        RU: Вычисляет диапазон индексов (включительно) для вертикальных линий.
        """
        start_index = -int(config.V_NB_LINES / 2) + 1
        end_index = start_index + config.V_NB_LINES - 1
        return start_index, end_index

    def get_state_offset_x(self, state, use_render_state=False):
        """Return X offset for either simulation or render calculations."""
        if use_render_state:
            return getattr(state, "render_offset_x", state.current_offset_x)
        return state.current_offset_x

    def get_state_offset_y(self, state, use_render_state=False):
        """Return Y offset for either simulation or render calculations."""
        if use_render_state:
            return getattr(state, "render_offset_y", state.current_offset_y)
        return state.current_offset_y

    def get_state_y_loop(self, state, use_render_state=False):
        """Return Y loop index for either simulation or render calculations."""
        if use_render_state:
            return getattr(state, "render_y_loop", state.current_y_loop)
        return state.current_y_loop

    def get_line_x_from_index(self, index, width, perspective_point_x, current_offset_x, config):
        """
        Compute the world X of a vertical line by index.

        The grid is shifted by half a lane so that tile_x=0 is centered around
        the perspective point at startup without special-case offsets.

        RU: Вычисляет мировую X-координату вертикальной линии по индексу.
        Сетка смещена на половину полосы, чтобы tile_x=0 был центрирован
        вокруг точки перспективы при старте без специальных смещений.
        """
        spacing_x = config.V_LINES_SPACING * width
        centered_x = perspective_point_x + (index - 0.5) * spacing_x + current_offset_x
        return centered_x

    def get_line_y_from_index(self, index, height, perspective_point_y, current_offset_y, config):
        """
        Compute the world Y of a horizontal line by index.

        RU: Вычисляет мировую Y-координату горизонтальной линии по индексу.
        """
        spacing_y = config.H_LINES_SPACING * height
        centered_y = index * spacing_y - current_offset_y
        return centered_y

    def get_tile_rect_world(
        self,
        tile_x,
        tile_y,
        state,
        width,
        height,
        perspective_point_x,
        perspective_point_y,
        config,
        use_render_state=False,
    ):
        """
        Compute the world-space axis-aligned rectangle for a tile coordinate.

        RU: Вычисляет осевой прямоугольник тайла в мировых координатах.
        """
        offset_x = self.get_state_offset_x(state, use_render_state)
        offset_y = self.get_state_offset_y(state, use_render_state)
        y_loop = self.get_state_y_loop(state, use_render_state)
        adj_y = tile_y - y_loop
        xmin = self.get_line_x_from_index(
            tile_x,
            width,
            perspective_point_x,
            offset_x,
            config,
        )
        xmax = self.get_line_x_from_index(
            tile_x + 1,
            width,
            perspective_point_x,
            offset_x,
            config,
        )
        ymin = self.get_line_y_from_index(
            adj_y,
            height,
            perspective_point_y,
            offset_y,
            config,
        )
        ymax = self.get_line_y_from_index(
            adj_y + 1,
            height,
            perspective_point_y,
            offset_y,
            config,
        )
        return xmin, ymin, xmax, ymax
