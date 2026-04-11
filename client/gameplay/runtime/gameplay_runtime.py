# -*- coding: utf-8 -*-
"""Gameplay runtime orchestrator for the lane-based segment road pipeline."""

from __future__ import annotations

import math
from time import perf_counter

from client.gameplay.road.road_profiles import get_level_road_profile_id
from client.gameplay.collision.collision_engine import CollisionEngine
from client.gameplay.collision.offroad_guard import Bounds2D, OffRoadGuard
from client.gameplay.engine.config import GameConfig
from client.gameplay.runtime.game_loop import GameLoop
from client.gameplay.engine.game_session_manager import GameSessionManager, LossOutcome
from client.gameplay.engine.game_state import GameState
from client.gameplay.engine.respawn_reset import respawn_to_start
from client.gameplay.engine.road_motion_engine import RoadMotionEngine
from client.gameplay.engine.lane_motion import LaneMotion
from client.gameplay.engine.lane_state import LaneState
from client.gameplay.road.path.road_path_stream import RoadPathStream
from client.gameplay.road.projection.perspective_projector import PerspectiveProjector
from client.gameplay.road.render.gameplay_renderer import GameplayRenderer
from client.gameplay.road.road_models import FrameSnapshot
from client.gameplay.ship.ship_engine import ShipEngine
from client.gameplay.widgets.gameplay_surface import GameplaySurface
from client.infrastructure.logging.debug_input_trace import trace_input
from client.application.gameplay.levels.level_runtime_manager import LevelRuntimeManager

FIXED_DT = 1.0 / 120.0
MAX_FRAME_DT = 0.05
MAX_FIXED_STEPS = max(int(MAX_FRAME_DT / FIXED_DT), 1)


class GameplayRuntime:
    """Runtime that owns state, logic, renderers, and the tick loop."""

    def __init__(self, surface: GameplaySurface, fps: int = 60) -> None:
        self._surface = surface
        self._fps = fps

        self._config = GameConfig()
        self._state = GameState()
        self._session = GameSessionManager(max_attempts=3)
        self._motion = RoadMotionEngine()
        self._collision = CollisionEngine()
        self._offroad_guard = OffRoadGuard()
        self._segment_stream = RoadPathStream()
        self._lane_state = LaneState(
            self._config.road_profile.lane.lane_count,
            self._config.road_profile.lane.resolved_start_lane,
        )
        self._lane_motion = LaneMotion(self._config.road_profile.lane.lane_change_speed)
        self._perspective_projector = PerspectiveProjector()
        self._gameplay_renderer = GameplayRenderer(surface.canvas, self._config, self._perspective_projector)
        self._ship_engine = ShipEngine(surface.actor_canvas, self._config)
        self._level_runtime = LevelRuntimeManager()
        self._loop = GameLoop()
        self._control_manager = None
        self.on_game_over = None
        self.on_loss = None
        self._paused_for_ad = False
        self._dt_accumulator = 0.0
        self._previous_world_x = 0.0
        self._current_world_x = 0.0
        self._previous_world_y = 0.0
        self._current_world_y = 0.0
        self._previous_render_rows = ()
        self._current_render_rows = ()
        self._brake_pressed = False
        self._brake_active = False
        self._brake_locked_until_release = False
        self._brake_started_at = 0.0
        self._brake_max_sec = 3.0

        self._segment_stream.configure(self._config.road_profile)
        self._segment_stream.reset(0)
        self._lane_motion.reset(self._lane_state)
        self._sync_render_state_from_simulation()
        surface.bind_engines(
            self.build_frame_snapshot,
            self._gameplay_renderer,
            self._ship_engine,
        )

    def bind_control_manager(self, control_manager) -> None:
        self._control_manager = control_manager

    def prepare_scene(self) -> None:
        self._state.reset()
        self._reset_brake_state()
        self._apply_active_level_profile()
        self._reset_lane_pipeline(base_seq=0)
        self._ship_engine.reset_to_start(self._state)
        self._reset_timing()
        if self._surface.width <= 0 or self._surface.height <= 0:
            return
        self._sync_render_state_from_simulation()
        self._surface.render()

    def start(self) -> None:
        self._state.reset()
        self._session.reset()
        self._reset_brake_state()
        self._apply_active_level_profile()
        self._reset_lane_pipeline(base_seq=0)
        self._ship_engine.reset_to_start(self._state)
        self._state.mark_started()
        self._paused_for_ad = False
        self._reset_timing()
        self._sync_render_state_from_simulation()
        self._loop.start(self._tick, fps=self._fps)

    def receive_reward(self) -> None:
        self._session.reset()
        self._apply_active_level_profile()
        respawn_to_start(
            self._state,
            self._ship_engine,
            self._segment_stream,
            self._lane_state,
            self._lane_motion,
            self._config,
        )
        self._state.mark_started()
        self._reset_timing()
        self._sync_render_state_from_simulation()
        self.resume_after_ad()

    def stop(self) -> None:
        self._paused_for_ad = False
        self._loop.stop()
        self.set_x_input_direction(0)

    def request_redraw(self) -> None:
        width = self._surface.width
        height = self._surface.height
        if width <= 0 or height <= 0:
            return
        self._sync_render_state_from_simulation()
        self._surface.render()

    def pause_for_ad(self) -> None:
        self._paused_for_ad = True
        self._loop.stop()
        self.set_x_input_direction(0)
        self._reset_timing()
        self._reset_brake_state()

    def resume_after_ad(self) -> None:
        self._paused_for_ad = False
        self._reset_timing()
        self._sync_render_state_from_simulation()
        self._loop.start(self._tick, fps=self._fps)

    def brake_on(self) -> None:
        if self._paused_for_ad or self._brake_pressed:
            return
        self._brake_pressed = True
        if self._brake_locked_until_release:
            self._trace_runtime('brake_on_ignored')
            return
        self._brake_active = True
        self._brake_started_at = perf_counter()
        self._apply_brake_state()
        self._trace_runtime('brake_on')

    def brake_off(self) -> None:
        self._brake_pressed = False
        self._brake_active = False
        self._brake_locked_until_release = False
        self._brake_started_at = 0.0
        self._apply_brake_state()
        self._trace_runtime('brake_off')

    def input_left(self) -> None:
        self.set_x_input_direction(-1)

    def input_right(self) -> None:
        self.set_x_input_direction(1)

    def input_stop(self) -> None:
        self.set_x_input_direction(0)

    def set_x_input_direction(self, direction: int) -> None:
        normalized = -1 if int(direction) < 0 else 1 if int(direction) > 0 else 0
        if self._paused_for_ad and normalized != 0:
            return
        self._lane_motion.set_input_direction(normalized)
        self._sync_current_speed_x_mirror()
        self._trace_runtime(f'set_x_input_direction={normalized}')

    def _tick(self, dt: float) -> None:
        if self._paused_for_ad:
            return
        width = self._surface.width
        height = self._surface.height
        if width <= 0 or height <= 0:
            return

        self._update_brake()
        frame_dt = min(max(dt, 0.0), MAX_FRAME_DT)
        self._dt_accumulator += frame_dt

        fixed_steps = 0
        while self._dt_accumulator >= FIXED_DT and fixed_steps < MAX_FIXED_STEPS:
            self._capture_previous_simulation_state()
            self._fixed_update(FIXED_DT)
            self._current_world_x = self._simulation_world_offset_x()
            self._current_world_y = self._world_y()
            self._current_render_rows = self._snapshot_render_rows()
            self._dt_accumulator -= FIXED_DT
            fixed_steps += 1
        if fixed_steps == MAX_FIXED_STEPS and self._dt_accumulator > FIXED_DT:
            self._dt_accumulator = FIXED_DT

        alpha = min(max(self._dt_accumulator / FIXED_DT, 0.0), 1.0)
        self._update_render_state(alpha)
        self._surface.render()

    def _fixed_update(self, dt: float) -> None:
        if not self._state.state_game_has_started or self._state.state_game_over:
            return

        if self._control_manager is not None:
            self._control_manager.advance_control_state(dt)

        self._lane_motion.update(dt, self._lane_state)
        self._sync_current_speed_x_mirror()

        motion = self._motion.step(dt, self._state, (self._surface.width, self._surface.height), self._config)
        if motion.advanced_rows:
            self._segment_stream.advance(motion.advanced_rows)

        road_segments = self._segment_stream.get_active_road_segments()
        ship_bounds = self._current_ship_bounds()
        if not self._offroad_guard.is_ship_on_road(
            ship_bounds=ship_bounds,
            road_segments=road_segments,
        ):
            self._trigger_loss()
            return

        if (
            self._lane_state.transition_active
            and self._lane_motion.has_reached_target_center(self._lane_state)
            and self._collision.can_commit_target_lane(
                self._lane_state,
                self._segment_stream,
                self._state,
                self._config.road_profile,
            )
        ):
            self._lane_state.finish_transition()
            if self._lane_motion.input_dir != 0:
                self._lane_state.begin_transition(self._lane_motion.input_dir)

        ship_is_safe = self._collision.is_ship_safe(
            self._lane_state,
            self._segment_stream,
            self._state,
            self._config.road_profile,
        )
        if ship_is_safe:
            return

        self._trigger_loss()

    def _current_ship_bounds(self) -> Bounds2D:
        footprint = self._config.ship_collision_footprint
        center_x = float(self._lane_motion.x_pos_tiles)
        world_y = self._world_y()
        return Bounds2D(
            left=center_x - footprint.half_width_tiles,
            right=center_x + footprint.half_width_tiles,
            bottom=world_y - footprint.back_offset_rows,
            top=world_y + footprint.front_offset_rows,
        )

    def _trigger_loss(self) -> None:
        outcome = self._session.register_loss()
        if outcome == LossOutcome.SOFT_RESET:
            self.set_x_input_direction(0)
            respawn_to_start(
                self._state,
                self._ship_engine,
                self._segment_stream,
                self._lane_state,
                self._lane_motion,
                self._config,
            )
            self._sync_render_state_from_simulation()
        else:
            self._state.mark_game_over()
            if self.on_game_over:
                self.on_game_over()
        if self.on_loss:
            self.on_loss()

    def _apply_active_level_profile(self) -> None:
        profile = self._level_runtime.get_active_profile()
        self._state.speed_y_factor = profile.initial_speed_y_factor
        profile_id = getattr(profile, 'road_profile_id', None) or get_level_road_profile_id(profile.level_id)
        self._config.apply_road_profile(profile_id)
        self._segment_stream.configure(self._config.road_profile)
        self._lane_state.configure(
            self._config.road_profile.lane.lane_count,
            self._config.road_profile.lane.resolved_start_lane,
        )
        self._lane_motion.configure(self._config.road_profile.lane.lane_change_speed)

    def _reset_lane_pipeline(self, base_seq: int) -> None:
        self._state.current_speed_x = 0.0
        self._lane_state.reset(self._config.road_profile.lane.resolved_start_lane)
        self._lane_motion.reset(self._lane_state)
        self._segment_stream.reset(base_seq)

    def _update_brake(self) -> None:
        if not self._brake_active:
            return
        if (perf_counter() - self._brake_started_at) < self._brake_max_sec:
            return
        self._brake_active = False
        self._brake_locked_until_release = True
        self._apply_brake_state()

    def _apply_brake_state(self) -> None:
        if self._paused_for_ad:
            return
        if self._brake_active:
            self._state.speed_y_factor = self._config.road_profile.motion.brake_speed_factor
            return
        self._state.speed_y_factor = self._level_runtime.get_active_profile().initial_speed_y_factor

    def _reset_brake_state(self) -> None:
        self._brake_pressed = False
        self._brake_active = False
        self._brake_locked_until_release = False
        self._brake_started_at = 0.0
        self._apply_brake_state()

    def _world_y(self) -> float:
        return float(self._state.current_y_loop) + float(self._state.current_offset_y)

    def _capture_previous_simulation_state(self) -> None:
        self._previous_world_x = self._simulation_world_offset_x()
        self._previous_world_y = self._world_y()
        self._previous_render_rows = self._snapshot_render_rows()

    def _sync_render_state_from_simulation(self) -> None:
        world_offset_x = self._simulation_world_offset_x()
        self._state.world_offset_x = world_offset_x
        self._previous_world_x = world_offset_x
        self._current_world_x = world_offset_x
        self._state.render_offset_y = self._state.current_offset_y
        self._state.render_y_loop = self._state.current_y_loop
        world_y = self._world_y()
        self._previous_world_y = world_y
        self._current_world_y = world_y
        rows_snapshot = self._snapshot_render_rows()
        self._previous_render_rows = rows_snapshot
        self._current_render_rows = rows_snapshot
        self._state.render_path_rows = rows_snapshot

    def _update_render_state(self, alpha: float) -> None:
        self._state.world_offset_x = self._lerp(self._previous_world_x, self._current_world_x, alpha)
        render_world_y = self._lerp(self._previous_world_y, self._current_world_y, alpha)
        render_y_loop = math.floor(render_world_y)
        self._state.render_y_loop = render_y_loop
        self._state.render_offset_y = render_world_y - render_y_loop
        if render_y_loop < self._state.current_y_loop:
            self._state.render_path_rows = self._previous_render_rows
        else:
            self._state.render_path_rows = self._current_render_rows

    def _simulation_world_offset_x(self) -> float:
        return self._lane_motion.get_world_offset_x(self._config.road_profile)

    def build_frame_snapshot(self) -> FrameSnapshot:
        rows = tuple(self._state.render_path_rows or self._segment_stream.visible_rows())
        return FrameSnapshot(
            rows=rows,
            render_offset_y=float(self._state.render_offset_y),
            world_offset_x=float(self._state.world_offset_x),
            ship_lane_x=float(self._lane_motion.x_pos_tiles),
        )

    def _sync_current_speed_x_mirror(self) -> None:
        self._state.current_speed_x = float(self._lane_motion.input_dir)

    def _snapshot_render_rows(self) -> tuple:
        if not self._segment_stream.has_rows():
            return ()
        return self._segment_stream.visible_rows()

    def _trace_runtime(self, action: str) -> None:
        trace_input(
            'runtime',
            f'action={action} x={self._lane_motion.x_pos_tiles:.3f} dir={self._lane_motion.input_dir} current_speed_x={self._state.current_speed_x:.1f} brake={int(self._brake_active)} speed_y_factor={self._state.speed_y_factor:.2f} locked={int(self._brake_locked_until_release)}',
        )

    @staticmethod
    def _lerp(start: float, end: float, alpha: float) -> float:
        return start + (end - start) * alpha

    def _reset_timing(self) -> None:
        self._dt_accumulator = 0.0
