# -*- coding: utf-8 -*-
"""
Gameplay runtime orchestrator that wires engine components and ticks.

EN: Creates core engine objects, binds them to the render surface, and
controls the game loop lifecycle.
RU: Создаёт ключевые компоненты движка, связывает их с рендер-поверхностью
и управляет жизненным циклом игрового цикла.
"""

from __future__ import annotations

from engine.core.collision_engine import CollisionEngine
from engine.core.config import GameConfig
from engine.core.game_loop import GameLoop
from engine.core.game_session_manager import GameSessionManager, LossOutcome
from engine.core.game_state import GameState
from engine.core.input_controller import InputController
from engine.core.perspective import Perspective
from engine.core.respawn_reset import respawn_to_start
from engine.core.road_geometry import RoadGeometry
from engine.core.road_motion_engine import RoadMotionEngine
from engine.core.tiles_model import TilesModel
from engine.renderers.road_grid import RoadGridRenderer
from engine.renderers.tiles_renderer import TilesRenderer
from engine.ship.ship_engine import ShipEngine
from engine.widgets.gameplay_surface import GameplaySurface


class GameplayRuntime:
    """
    Runtime that owns engine components and runs the main tick loop.

    EN: Holds state, renderers, and motion/collision engines to update the scene.
    RU: Хранит состояние, рендереры и движки движения/коллизий для обновления сцены.
    """

    def __init__(self, surface: GameplaySurface, fps: int = 60) -> None:
        """
        Initialize engine objects and bind them to the render surface.

        EN: Creates core components, renderers, and prepares the loop controller.
        RU: Создаёт основные компоненты, рендереры и подготавливает контроллер цикла.
        """
        self._surface = surface
        self._fps = fps

        self._config = GameConfig()
        self._state = GameState()
        self._session = GameSessionManager(max_attempts=3)
        self._perspective = Perspective()
        self._geometry = RoadGeometry()
        self._motion = RoadMotionEngine()
        self._collision = CollisionEngine()
        self._tiles = TilesModel()

        self._road_grid = RoadGridRenderer(surface.canvas, self._config)
        self._tiles_renderer = TilesRenderer(surface.canvas, self._config)
        self._ship_engine = ShipEngine(surface.canvas, self._config)
        self._input = InputController(self._state, self._config)
        self._loop = GameLoop()
        self.on_game_over = None
        self.on_loss = None
        self._linear_speed_x = 0.0
        self._linear_active = False

        surface.bind_engines(
            self._road_grid,
            self._tiles_renderer,
            self._tiles,
            self._ship_engine,
            self._perspective,
            self._state,
            self._geometry,
            self._config,
        )

    def prepare_scene(self) -> None:
        """
        Prepare the initial scene without starting the motion loop.

        EN: Resets state, tiles, and ship, then renders once for visibility.
        RU: Сбрасывает состояние, тайлы и корабль, затем рендерит один раз.
        """
        self._state.reset()
        self._tiles.reset(self._state, self._config)
        self._ship_engine.reset_to_start(self._state)
        width = self._surface.width
        height = self._surface.height
        if width <= 0 or height <= 0:
            return
        self._perspective.set_perspective_point(width / 2, height * 0.75)
        self._surface.render()

    def start(self) -> None:
        """
        Start a new run and schedule the tick loop.

        EN: Resets runtime state and begins scheduled updates at the target FPS.
        RU: Сбрасывает состояние и запускает обновления с заданной частотой кадров.
        """
        self._state.reset()
        self._tiles.reset(self._state, self._config)
        self._ship_engine.reset_to_start(self._state)
        self._session.reset()
        self._state.mark_started()
        self._loop.start(self._tick, fps=self._fps)

    def receive_reward(self) -> None:
        """
        Continue after rewarded ad without resetting score.

        EN: Restores attempts, respawns safely, and resumes loop without
        resetting current_y_loop score progress.
        RU: Восстанавливает попытки, безопасно респавнит и возобновляет цикл
        без сброса прогресса current_y_loop.
        """
        self._session.reset()
        respawn_to_start(self._state, self._ship_engine, self._tiles, self._config)
        self._state.speed_y_factor = 1.0
        self._state.mark_started()
        self._loop.start(self._tick, fps=self._fps)

    def stop(self) -> None:
        """
        Stop the tick loop and detach input handlers.

        EN: Cancels scheduled updates and detaches input bindings.
        RU: Останавливает цикл обновлений и отключает обработчики ввода.
        """
        self._loop.stop()
        self._input.detach()

    def _tick(self, dt: float) -> None:
        """
        Execute a single frame update and handle motion/collisions.

        EN: Updates perspective, renders, advances motion, and applies loss logic.
        RU: Обновляет перспективу, рендерит, двигает сцену и применяет логику проигрыша.
        """
        width = self._surface.width
        height = self._surface.height
        if width <= 0 or height <= 0:
            return

        self._perspective.set_perspective_point(width / 2, height * 0.75)
        self._surface.render()

        if not self._state.state_game_has_started or self._state.state_game_over:
            return

        saved_speed_x = self._state.current_speed_x
        if self._linear_active:
            self._state.current_speed_x = 0
        motion = self._motion.step(dt, self._state, (width, height), self._config)
        if self._linear_active:
            self._state.current_speed_x = saved_speed_x
        for _ in range(motion.advanced_rows):
            self._tiles.prune_passed_tiles(self._state)
            self._tiles.generate_more(self._state, self._config)

        ship_points = self._ship_engine.get_ship_points_world()
        on_tiles = self._collision.get_ship_points_on_tiles(
            ship_points,
            self._tiles.tiles_coordinates,
            self._geometry,
            self._state,
            width,
            height,
            self._config,
            self._perspective.perspective_point_x,
            self._perspective.perspective_point_y,
        )
        if not on_tiles or not all(on_tiles):
            outcome = self._session.register_loss()
            if outcome == LossOutcome.SOFT_RESET:
                respawn_to_start(self._state, self._ship_engine, self._tiles, self._config)
            else:
                self._state.mark_game_over()
                if self.on_game_over:
                    self.on_game_over()
            if self.on_loss:
                self.on_loss()

    def request_redraw(self) -> None:
        """EN: Update perspective and render once without changing state.
        RU: Обновить перспективу и отрисовать один раз без изменения состояния.
        """
        width = self._surface.width
        height = self._surface.height
        if width <= 0 or height <= 0:
            return
        self._perspective.set_perspective_point(width / 2, height * 0.75)
        self._surface.render()

    def brake_on(self) -> None:
        """EN: Enable vertical brake by applying slowdown factor.
        RU: Включить вертикальный тормоз, применив коэффициент замедления.
        """
        self._state.speed_y_factor = self._config.SPEED_Y_BRAKE_FACTOR

    def brake_off(self) -> None:
        """EN: Disable vertical brake and restore default factor.
        RU: Отключить вертикальный тормоз и вернуть коэффициент по умолчанию.
        """
        self._state.speed_y_factor = 1.0

    def _max_x_offset(self, width: float) -> float:
        """
        Compute the maximum lateral offset from the center.

        EN: Uses road tile width minus half ship width in world units.
        RU: Использует ширину тайла дороги минус половину ширины корабля.
        """
        tile_half = (self._config.V_LINES_SPACING * width) / 2
        ship_half = (self._config.SHIP_WIDTH * width) / 2
        return max(tile_half - ship_half, 0)

    def _step_x(self, width: float) -> float:
        """
        Compute per-input step size toward the edge.

        EN: Divides max offset by INPUT_STEPS_TO_EDGE.
        RU: Делит максимальный сдвиг на INPUT_STEPS_TO_EDGE.
        """
        steps = max(int(getattr(self._config, "INPUT_STEPS_TO_EDGE", 1)), 1)
        return (self._max_x_offset(width) / steps) * 2

    def _dynamic_offset_bounds(self, width: float) -> tuple[float, float]:
        """
        Compute dynamic offset bounds from visible tiles near the ship.

        EN: Expands clamp based on current row tiles to allow side paths.
        RU: Расширяет clamp по текущим тайлам, чтобы переходить на боковые пути.
        """
        spacing_x = self._config.V_LINES_SPACING * width
        ppx = width / 2
        ship_half = (self._config.SHIP_WIDTH * width) / 2
        ship_left = ppx - ship_half
        ship_right = ppx + ship_half

        y0 = self._state.current_y_loop
        y1 = self._state.current_y_loop + 1
        tile_xs = [x for x, y in self._tiles.tiles_coordinates if y == y0 or y == y1]
        if not tile_xs:
            tile_xs = [0]
        min_tile_x = min(tile_xs)
        max_tile_x = max(tile_xs)
        min_line_index = min_tile_x
        max_line_index = max_tile_x + 1

        offset_min = ship_right - ppx - (max_line_index - 0.5) * spacing_x
        offset_max = ship_left - ppx - (min_line_index - 0.5) * spacing_x

        if offset_min > offset_max:
            offset_min, offset_max = offset_max, offset_min
        return offset_min, offset_max

    def input_left(self) -> None:
        """EN: Dispatch left input to the engine input controller.
        RU: Передать команду влево контроллеру ввода движка.
        """
        width = self._surface.width
        if width <= 0:
            return
        step = self._step_x(width)
        offset_min, offset_max = self._dynamic_offset_bounds(width)
        self._state.current_offset_x = min(
            offset_max, self._state.current_offset_x + step
        )
        self._state.current_offset_x = max(
            offset_min, self._state.current_offset_x
        )
        self._state.current_speed_x = 0

    def input_right(self) -> None:
        """EN: Dispatch right input to the engine input controller.
        RU: Передать команду вправо контроллеру ввода движка.
        """
        width = self._surface.width
        if width <= 0:
            return
        step = self._step_x(width)
        offset_min, offset_max = self._dynamic_offset_bounds(width)
        self._state.current_offset_x = max(
            offset_min, self._state.current_offset_x - step
        )
        self._state.current_offset_x = min(
            offset_max, self._state.current_offset_x
        )
        self._state.current_speed_x = 0

    def input_stop(self) -> None:
        """EN: Dispatch stop input to the engine input controller.
        RU: Передать команду стоп контроллеру ввода движка.
        """
        self._state.current_speed_x = 0

    def input_left_step(self) -> None:
        """EN: Step left using the existing step logic.
        RU: Сделать шаг влево, используя текущую шаговую логику.
        """
        self.input_left()

    def input_right_step(self) -> None:
        """EN: Step right using the existing step logic.
        RU: Сделать шаг вправо, используя текущую шаговую логику.
        """
        self.input_right()

    def set_speed_x_dir(self, direction: int) -> None:
        """EN: Set linear movement direction (-1 right, +1 left, 0 stop).
        RU: Установить направление линейного движения (-1 вправо, +1 влево, 0 стоп).
        """
        if direction == 0:
            self._linear_speed_x = 0.0
            self._linear_active = False
            self._state.current_speed_x = 0
            return
        self._linear_active = True
        speed = self._config.SPEED_X
        self._linear_speed_x = speed * direction
        self._state.current_speed_x = self._linear_speed_x

    def apply_linear_x(self, dt: float) -> None:
        """EN: Apply linear horizontal movement using V3 formula.
        RU: Применить линейное горизонтальное движение по формуле V3.
        """
        width = self._surface.width
        if width <= 0:
            return
        time_factor = dt * 60
        speed_x = (self._linear_speed_x * width) / 100
        self._state.current_offset_x += speed_x * time_factor
        offset_min, offset_max = self._dynamic_offset_bounds(width)
        if self._state.current_offset_x < offset_min:
            self._state.current_offset_x = offset_min
        elif self._state.current_offset_x > offset_max:
            self._state.current_offset_x = offset_max
