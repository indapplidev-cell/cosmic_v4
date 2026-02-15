# -*- coding: utf-8 -*-
"""
Render surface widget that delegates drawing to engine renderers.

EN: Hosts the game renderers and exposes a full-screen surface for drawing.
RU: Хостит рендеры игры и предоставляет полноэкранную поверхность для рисования.
"""

from kivy.uix.widget import Widget


class GameplaySurface(Widget):
    """
    Kivy widget that coordinates renderers with current state and geometry.

    EN: Owns renderer bindings and exposes size/pos used by the game engine.
    RU: Управляет связями с рендерами и предоставляет размер/позицию движку.
    """

    def __init__(self, **kwargs):
        """
        Initialize with no bound engines or renderers.

        EN: Sets up renderer references without external debug hooks.
        RU: Настраивает ссылки на рендеры без внешних отладочных связей.
        """
        super().__init__(**kwargs)
        self.opacity = 0
        self._road_grid = None
        self._tiles_renderer = None
        self._tiles_model = None
        self._ship_engine = None
        self._perspective = None
        self._state = None
        self._geometry = None
        self._config = None

    def bind_engines(
        self,
        road_grid,
        tiles_renderer,
        tiles_model,
        ship_engine,
        perspective,
        state,
        geometry,
        config,
    ):
        """
        Bind renderer and model components used for rendering each frame.

        EN: Stores the engine components that produce visuals for the scene.
        RU: Сохраняет компоненты движка, которые рисуют сцену.
        """
        self._road_grid = road_grid
        self._tiles_renderer = tiles_renderer
        self._tiles_model = tiles_model
        self._ship_engine = ship_engine
        self._perspective = perspective
        self._state = state
        self._geometry = geometry
        self._config = config

    def render(self):
        """
        Render grid, tiles, and ship in the correct order.

        EN: Updates renderers only when geometry and bindings are valid.
        RU: Обновляет рендеры только при валидной геометрии и связях.
        """
        if self.width < 2 or self.height < 2:
            self.opacity = 0
            return
        if (
            not self._road_grid
            or not self._tiles_renderer
            or not self._tiles_model
            or not self._ship_engine
        ):
            self.opacity = 0
            return
        if not getattr(self._tiles_model, "tiles_coordinates", None):
            self.opacity = 0
            return
        if self.opacity != 1:
            self.opacity = 1
        width = self.width
        height = self.height
        self._road_grid.update(self._state, self._perspective, self._geometry, width, height, self._config)
        self._tiles_renderer.update(
            self._tiles_model,
            self._state,
            self._perspective,
            self._geometry,
            width,
            height,
            self._config,
        )
        self._ship_engine.update(self._perspective, (width, height))
