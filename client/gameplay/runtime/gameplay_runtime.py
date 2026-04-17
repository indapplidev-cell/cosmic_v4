# -*- coding: utf-8 -*-
"""Gameplay runtime orchestrator for the continuous-X segment road pipeline."""

from __future__ import annotations

import math
from statistics import median
from time import perf_counter

from kivy.clock import Clock
from client.gameplay.runtime.display_refresh_probe import DisplayRefreshProbe
from client.gameplay.runtime.performance_monitor import FrameSample, PerformanceMonitor
from client.gameplay.runtime.render_performance_policy import (
    RenderPerformanceSnapshot,
    build_target_fps_ladder,
    default_render_performance_config,
    select_target_render_fps,
)
from client.gameplay.debug.gameplay_trace_flags import ENABLE_PERF_POLICY_INFO, ENABLE_RUNTIME_TRACE
from client.gameplay.road.road_profiles import get_level_road_profile_id
from client.gameplay.collision.offroad_guard import Bounds2D, OffRoadGuard
from client.gameplay.engine.config import GameConfig
from client.gameplay.runtime.game_loop import GameLoop
from client.gameplay.engine.game_session_manager import GameSessionManager, LossOutcome
from client.gameplay.engine.game_state import GameState
from client.gameplay.engine.respawn_reset import respawn_to_start
from client.gameplay.engine.road_motion_engine import RoadMotionEngine
from client.gameplay.engine.continuous_x_controller import ContinuousXController
from client.gameplay.road.path.road_path_stream import RoadPathStream
from client.gameplay.road.projection.perspective_projector import PerspectiveProjector
from client.gameplay.road.render.gameplay_renderer import GameplayRenderer
from client.gameplay.road.render.render_quality_profile import build_render_quality_profile
from client.gameplay.road.road_models import FrameSnapshot
from client.gameplay.road.world_grid_spec import WorldGridSpec
from client.gameplay.ship.ship_engine import ShipEngine
from client.gameplay.widgets.gameplay_surface import GameplaySurface
from client.infrastructure.logging.debug_input_trace import trace_input
from client.application.gameplay.levels.level_runtime_manager import LevelRuntimeManager

FIXED_DT = 1.0 / 120.0
MAX_FRAME_DT = 0.05
MAX_FIXED_STEPS = max(int(MAX_FRAME_DT / FIXED_DT), 1)
_schedule_once = getattr(Clock, 'schedule_once')


def _format_perf_bootstrap_log(
    display_hz_est: int | None,
    stable_device_fps: float,
    target_render_fps: int,
    quality_level: int,
    sample_count: int,
    probe_reason: str,
    median_dt: float,
) -> str:
    return (
        "[PERF] bootstrap "
        f"display_hz={display_hz_est} "
        f"stable_fps={float(stable_device_fps):.2f} "
        f"target_render_fps={int(target_render_fps)} "
        f"quality={int(quality_level)} "
        f"samples={int(sample_count)} "
        f"probe_reason={str(probe_reason)} "
        f"median_dt={float(median_dt):.4f}"
    )


def _format_perf_policy_change_log(
    reason: str,
    old_quality: int,
    new_quality: int,
    old_fps: int,
    new_fps: int,
    snapshot: RenderPerformanceSnapshot,
) -> str:
    return (
        "[PERF] policy_change "
        f"reason={str(reason)} "
        f"quality={int(old_quality)}->{int(new_quality)} "
        f"fps={int(old_fps)}->{int(new_fps)} "
        f"p95_frame_dt={float(snapshot.p95_frame_dt):.4f} "
        f"missed={int(snapshot.missed_frames)} "
        f"overflows={int(snapshot.fixed_step_overflows)}"
    )


def _format_perf_overload_breakdown_log(
    target_render_fps: int,
    quality_level: int,
    snapshot: RenderPerformanceSnapshot,
    sample_count: int,
) -> str:
    return (
        "[PERF] overload_breakdown "
        f"target_fps={int(target_render_fps)} "
        f"quality={int(quality_level)} "
        f"p95_frame_dt={float(snapshot.p95_frame_dt):.4f} "
        f"p95_sim_ms={float(snapshot.p95_sim_ms):.2f} "
        f"p95_render_ms={float(snapshot.p95_render_ms):.2f} "
        f"median_sim_ms={float(snapshot.median_sim_ms):.2f} "
        f"median_render_ms={float(snapshot.median_render_ms):.2f} "
        f"samples={int(sample_count)}"
    )


def _format_perf_steady_state_ok_log(
    target_render_fps: int,
    quality_level: int,
    snapshot: RenderPerformanceSnapshot,
) -> str:
    return (
        "[PERF] steady_state_ok "
        f"target_fps={int(target_render_fps)} "
        f"quality={int(quality_level)} "
        f"p95_frame_dt={float(snapshot.p95_frame_dt):.4f} "
        f"p95_render_ms={float(snapshot.p95_render_ms):.2f} "
        f"p95_sim_ms={float(snapshot.p95_sim_ms):.2f}"
    )


class GameplayRuntime:
    """Runtime that owns state, logic, renderers, and the tick loop."""

    def __init__(self, surface: GameplaySurface, fps: int = 60) -> None:
        self._surface = surface
        self._fps = fps

        self._config = GameConfig()
        self._state = GameState()
        self._session = GameSessionManager(max_attempts=3)
        self._motion = RoadMotionEngine()
        self._offroad_guard = OffRoadGuard()
        self._segment_stream = RoadPathStream()
        speed_modes = self._config.road_profile.lane.speed_modes
        self._x_speed_mode = str(speed_modes.default_mode) if speed_modes is not None else 'secondary'
        self._x_controller = ContinuousXController(
            self._config.road_profile.lane.resolved_default_steer_speed_tiles_per_sec
        )
        self._x_controller.configure(
            lane_count=self._config.road_profile.lane.lane_count,
            steer_speed_tiles_per_sec=self._config.road_profile.lane.resolved_default_steer_speed_tiles_per_sec,
            start_lane=self._config.road_profile.lane.resolved_start_lane,
        )
        self._x_controller.set_speed_tiles_per_sec(self._resolve_x_speed_for_mode(self._x_speed_mode))
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
        self._render_perf_config = default_render_performance_config()
        self._display_hz_est: int | None = None
        self._target_render_fps = int(self._fps)
        self._quality_level = 0
        self._performance_monitor = PerformanceMonitor(self._render_perf_config.rolling_window_seconds)
        self._display_refresh_probe = DisplayRefreshProbe(self._render_perf_config.bootstrap_probe_seconds)
        self._bootstrap_probe_start_event = None
        self._last_policy_change_at = 0.0
        self._policy_last_snapshot: RenderPerformanceSnapshot | None = None
        self._bootstrap_completed = False
        self._last_stable_policy_at: float | None = None
        self._policy_warmup_sec = 3.0
        self._policy_warmup_until = 0.0
        self._policy_warmup_min_samples = 90
        self._first_overload_diagnostic_emitted = False
        self._steady_state_ok_emitted = False
        self._steady_state_ok_after_sec = 5.0
        self._policy_downgrade_seen = False

        self._segment_stream.configure(self._config.road_profile)
        self._segment_stream.reset(0)
        self._apply_render_quality_profile()
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
        self._reset_x_pipeline(base_seq=0)
        self._ship_engine.reset_to_start(self._state)
        self._reset_timing()
        self._apply_render_quality_profile()
        if self._surface.width <= 0 or self._surface.height <= 0:
            return
        self._sync_render_state_from_simulation()
        self._surface.render()

    def start(self) -> None:
        self._state.reset()
        self._session.reset()
        self._reset_brake_state()
        self._apply_active_level_profile()
        self._reset_x_pipeline(base_seq=0)
        self._ship_engine.reset_to_start(self._state)
        self._state.mark_started()
        self._paused_for_ad = False
        self._reset_timing()
        self._loop.stop()
        self._display_refresh_probe.stop()
        self._sync_render_state_from_simulation()
        self._begin_render_bootstrap()

    def receive_reward(self) -> None:
        self._session.reset()
        self._apply_active_level_profile()
        respawn_to_start(
            self._state,
            self._ship_engine,
            self._segment_stream,
            self._x_controller,
            self._config,
        )
        self._state.mark_started()
        self._reset_timing()
        self._sync_render_state_from_simulation()
        self.resume_after_ad()

    def stop(self) -> None:
        self._paused_for_ad = False
        self._cancel_bootstrap_probe_start()
        self._display_refresh_probe.stop()
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
        self._cancel_bootstrap_probe_start()
        self._display_refresh_probe.stop()
        self._loop.stop()
        self.set_x_input_direction(0)
        self._reset_timing()
        self._reset_brake_state()

    def resume_after_ad(self) -> None:
        self._paused_for_ad = False
        self._reset_timing()
        self._sync_render_state_from_simulation()
        if self._bootstrap_completed:
            self._loop.start(self._tick, fps=self._target_render_fps)
            return
        self._begin_render_bootstrap()

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
        self._x_controller.set_input_direction(normalized)
        self._sync_current_speed_x_mirror()
        self._trace_runtime(f'set_x_input_direction={normalized}')

    def set_x_speed_mode(self, mode: str) -> None:
        normalized_mode = str(mode).strip().lower()
        if normalized_mode not in ('primary', 'secondary'):
            raise ValueError(f'Unsupported X speed mode: {mode}')
        self._x_speed_mode = normalized_mode
        self._x_controller.set_speed_tiles_per_sec(self._resolve_x_speed_for_mode(normalized_mode))
        self._trace_runtime(f'set_x_speed_mode={normalized_mode}')

    def toggle_x_speed_mode(self) -> None:
        if self._x_speed_mode == 'primary':
            self.set_x_speed_mode('secondary')
            return
        self.set_x_speed_mode('primary')

    def get_x_speed_mode(self) -> str:
        return self._x_speed_mode

    def get_x_speed_tiles_per_sec(self) -> float:
        return float(self._x_controller.speed_tiles_per_sec)

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

        tick_started = perf_counter()
        fixed_steps = 0
        fixed_step_overflow_hit = False
        while self._dt_accumulator >= FIXED_DT and fixed_steps < MAX_FIXED_STEPS:
            self._capture_previous_simulation_state()
            self._fixed_update(FIXED_DT)
            self._current_world_x = self._simulation_world_offset_x()
            self._current_world_y = self._world_y()
            self._current_render_rows = self._snapshot_render_rows()
            self._dt_accumulator -= FIXED_DT
            fixed_steps += 1
        if fixed_steps == MAX_FIXED_STEPS and self._dt_accumulator > FIXED_DT:
            fixed_step_overflow_hit = True
            self._dt_accumulator = FIXED_DT

        sim_finished = perf_counter()
        sim_ms = (sim_finished - tick_started) * 1000.0
        alpha = min(max(self._dt_accumulator / FIXED_DT, 0.0), 1.0)
        self._update_render_state(alpha)
        self._surface.render()
        tick_finished = perf_counter()
        render_ms = (tick_finished - sim_finished) * 1000.0
        self._performance_monitor.push(
            FrameSample(
                frame_dt=frame_dt,
                sim_ms=sim_ms,
                render_ms=render_ms,
                fixed_steps=fixed_steps,
                fixed_step_overflow=fixed_step_overflow_hit,
            )
        )
        self._reevaluate_render_policy()

    def _fixed_update(self, dt: float) -> None:
        if not self._state.state_game_has_started or self._state.state_game_over:
            return

        if self._control_manager is not None:
            self._control_manager.advance_control_state(dt)

        self._x_controller.update(dt)
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

        return

    def _current_ship_bounds(self) -> Bounds2D:
        footprint = self._config.ship_collision_footprint
        center_x = float(self._x_controller.x_pos_tiles)
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
            self._state.current_offset_y = 0.0
            self._state.state_game_over = False
            self._reset_x_pipeline(base_seq=self._state.current_y_loop)
            self._state.world_offset_x = self._simulation_world_offset_x()
            self._ship_engine.reset_to_start(self._state)
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
        if self._config.road_profile.lane.speed_modes is not None:
            if self._x_speed_mode not in ('primary', 'secondary'):
                self._x_speed_mode = str(self._config.road_profile.lane.speed_modes.default_mode)
        self._x_controller.configure(
            lane_count=self._config.road_profile.lane.lane_count,
            steer_speed_tiles_per_sec=self._config.road_profile.lane.resolved_default_steer_speed_tiles_per_sec,
            start_lane=self._config.road_profile.lane.resolved_start_lane,
        )
        self._x_controller.set_speed_tiles_per_sec(self._resolve_x_speed_for_mode(self._x_speed_mode))
        self._apply_render_quality_profile()

    def _reset_x_pipeline(self, base_seq: int) -> None:
        self._state.current_speed_x = 0.0
        self._x_controller.reset(self._config.road_profile.lane.resolved_start_lane)
        self._x_controller.set_speed_tiles_per_sec(self._resolve_x_speed_for_mode(self._x_speed_mode))
        self._segment_stream.reset(base_seq)

    def _resolve_x_speed_for_mode(self, mode: str) -> float:
        lane_cfg = self._config.road_profile.lane
        if lane_cfg.speed_modes is None:
            return float(lane_cfg.steer_speed_tiles_per_sec)
        if mode == 'primary':
            return float(lane_cfg.speed_modes.primary_speed_tiles_per_sec)
        if mode == 'secondary':
            return float(lane_cfg.speed_modes.secondary_speed_tiles_per_sec)
        return float(lane_cfg.resolved_default_steer_speed_tiles_per_sec)

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
        alpha = min(max(float(alpha), 0.0), 1.0)
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
        return self._x_controller.get_world_offset_x(self._config.road_profile)

    def build_frame_snapshot(self) -> FrameSnapshot:
        rows = tuple(self._state.render_path_rows or self._segment_stream.visible_rows())
        return FrameSnapshot(
            rows=rows,
            render_offset_y=float(self._state.render_offset_y),
            world_offset_x=float(self._state.world_offset_x),
            ship_lane_x=float(self._x_controller.x_pos_tiles),
        )

    def _sync_current_speed_x_mirror(self) -> None:
        self._state.current_speed_x = float(self._x_controller.input_dir)

    def _snapshot_render_rows(self) -> tuple:
        if not self._segment_stream.has_rows():
            return ()
        return self._segment_stream.visible_rows()

    def _trace_runtime(self, action: str) -> None:
        if not ENABLE_RUNTIME_TRACE:
            return
        trace_input(
            'runtime',
            f'action={action} x={self._x_controller.x_pos_tiles:.3f} dir={self._x_controller.input_dir} current_speed_x={self._state.current_speed_x:.1f} x_speed_mode={self._x_speed_mode} x_speed_tiles_per_sec={self._x_controller.speed_tiles_per_sec:.1f} brake={int(self._brake_active)} speed_y_factor={self._state.speed_y_factor:.2f} locked={int(self._brake_locked_until_release)}',
        )

    @staticmethod
    def _lerp(start: float, end: float, alpha: float) -> float:
        return start + (end - start) * alpha

    def _reset_timing(self) -> None:
        self._dt_accumulator = 0.0

    def _begin_render_bootstrap(self) -> None:
        self._loop.stop()
        self._cancel_bootstrap_probe_start()
        self._display_refresh_probe.stop()
        self._bootstrap_completed = False
        self._display_hz_est = None
        self._performance_monitor.reset()
        self._policy_last_snapshot = None
        self._last_stable_policy_at = None
        self._policy_warmup_until = 0.0
        self._first_overload_diagnostic_emitted = False
        self._steady_state_ok_emitted = False
        self._policy_downgrade_seen = False
        self._bootstrap_probe_start_event = _schedule_once(self._start_display_refresh_probe, 0.5)

    def _cancel_bootstrap_probe_start(self) -> None:
        if self._bootstrap_probe_start_event is not None:
            self._bootstrap_probe_start_event.cancel()
            self._bootstrap_probe_start_event = None

    def _start_display_refresh_probe(self, *_args) -> None:
        self._bootstrap_probe_start_event = None
        if self._paused_for_ad:
            return
        self._display_refresh_probe.start(self._complete_render_bootstrap)

    def _complete_render_bootstrap(self, display_hz_est: int | None, dt_samples: list[float]) -> None:
        if self._paused_for_ad:
            return
        self._display_hz_est = display_hz_est
        probe_diagnostics = self._display_refresh_probe.get_last_diagnostics()
        sample_count = int(probe_diagnostics.get("sample_count") or len(dt_samples))
        probe_reason = str(probe_diagnostics.get("reason") or "fallback_timeout")
        median_dt = float(probe_diagnostics.get("median_dt") or 0.0)
        if median_dt <= 0.0 and dt_samples:
            median_dt = float(median(float(dt) for dt in dt_samples if float(dt) > 0.0))
        stable_device_fps = (1.0 / median_dt) if median_dt > 0.0 else 60.0
        self._target_render_fps = select_target_render_fps(
            self._display_hz_est,
            stable_device_fps,
            self._render_perf_config.fps_candidates,
            self._render_perf_config.safety_factor,
        )
        self._bootstrap_completed = True
        self._last_policy_change_at = perf_counter()
        self._performance_monitor.reset()
        self._last_stable_policy_at = None
        self._apply_render_quality_profile()
        self._loop.start(self._tick, fps=self._target_render_fps)
        self._policy_warmup_until = perf_counter() + self._policy_warmup_sec
        self._first_overload_diagnostic_emitted = False
        self._steady_state_ok_emitted = False
        self._policy_downgrade_seen = False
        if ENABLE_PERF_POLICY_INFO:
            print(
                _format_perf_bootstrap_log(
                    display_hz_est=self._display_hz_est,
                    stable_device_fps=stable_device_fps,
                    target_render_fps=self._target_render_fps,
                    quality_level=self._quality_level,
                    sample_count=sample_count,
                    probe_reason=probe_reason,
                    median_dt=median_dt,
                ),
                flush=True,
            )

    def _reevaluate_render_policy(self) -> None:
        if not self._bootstrap_completed:
            return
        if not self._performance_monitor.has_samples():
            return
        snapshot = self._performance_monitor.snapshot(
            self._display_hz_est,
            self._target_render_fps,
            self._quality_level,
            self._render_perf_config.overload_frame_ratio,
        )
        self._policy_last_snapshot = snapshot
        now = perf_counter()
        if now < self._policy_warmup_until:
            return
        if self._performance_monitor_sample_count() < self._policy_warmup_min_samples:
            return
        target_frame_dt = 1.0 / max(int(self._target_render_fps), 1)
        severe_overload = (
            snapshot.p95_frame_dt > (target_frame_dt * self._render_perf_config.severe_overload_ratio)
            or snapshot.fixed_step_overflows >= 2
        )
        overload = (
            snapshot.p95_frame_dt > (target_frame_dt * self._render_perf_config.overload_frame_ratio)
            or snapshot.fixed_step_overflows > 0
            or snapshot.missed_frames > 0
        )
        if severe_overload:
            self._emit_overload_breakdown(snapshot)
        if overload:
            self._last_stable_policy_at = None
            if (now - self._last_policy_change_at) < self._render_perf_config.downgrade_cooldown_sec:
                return
            old_quality = self._quality_level
            old_fps = self._target_render_fps
            if self._apply_overload_policy(severe_overload):
                self._policy_downgrade_seen = True
                if ENABLE_PERF_POLICY_INFO:
                    print(
                        _format_perf_policy_change_log(
                            reason="severe_overload" if severe_overload else "normal_overload",
                            old_quality=old_quality,
                            new_quality=self._quality_level,
                            old_fps=old_fps,
                            new_fps=self._target_render_fps,
                            snapshot=snapshot,
                        ),
                        flush=True,
                    )
                self._last_policy_change_at = now
            return

        if self._last_stable_policy_at is None:
            self._last_stable_policy_at = now
            return
        if (
            not self._steady_state_ok_emitted
            and not self._policy_downgrade_seen
            and (now - self._last_stable_policy_at) >= self._steady_state_ok_after_sec
            and not severe_overload
        ):
            self._emit_steady_state_ok(snapshot)
        if (now - self._last_stable_policy_at) < self._render_perf_config.upgrade_cooldown_sec:
            return
        if (now - self._last_policy_change_at) < self._render_perf_config.upgrade_cooldown_sec:
            return
        old_quality = self._quality_level
        old_fps = self._target_render_fps
        if self._apply_upgrade_policy(snapshot):
            if ENABLE_PERF_POLICY_INFO:
                print(
                    _format_perf_policy_change_log(
                        reason="stable_upgrade",
                        old_quality=old_quality,
                        new_quality=self._quality_level,
                        old_fps=old_fps,
                        new_fps=self._target_render_fps,
                        snapshot=snapshot,
                    ),
                    flush=True,
                )
            self._last_policy_change_at = now
            self._last_stable_policy_at = None

    def _performance_monitor_sample_count(self) -> int:
        return len(getattr(self._performance_monitor, "_samples", ()))

    def _emit_overload_breakdown(self, snapshot: RenderPerformanceSnapshot) -> None:
        if self._first_overload_diagnostic_emitted or not ENABLE_PERF_POLICY_INFO:
            return
        print(
            _format_perf_overload_breakdown_log(
                target_render_fps=self._target_render_fps,
                quality_level=self._quality_level,
                snapshot=snapshot,
                sample_count=self._performance_monitor_sample_count(),
            ),
            flush=True,
        )
        self._first_overload_diagnostic_emitted = True

    def _emit_steady_state_ok(self, snapshot: RenderPerformanceSnapshot) -> None:
        if self._steady_state_ok_emitted or not ENABLE_PERF_POLICY_INFO:
            return
        print(
            _format_perf_steady_state_ok_log(
                target_render_fps=self._target_render_fps,
                quality_level=self._quality_level,
                snapshot=snapshot,
            ),
            flush=True,
        )
        self._steady_state_ok_emitted = True

    def _apply_overload_policy(self, severe_overload: bool) -> bool:
        changed = False
        if self._quality_level < 2:
            changed = self._set_quality_level(self._quality_level + 1) or changed
            if severe_overload:
                next_lower_fps = self._next_lower_render_fps()
                if next_lower_fps is not None:
                    changed = self._set_target_render_fps(next_lower_fps) or changed
            return changed
        next_lower_fps = self._next_lower_render_fps()
        if next_lower_fps is None:
            return False
        return self._set_target_render_fps(next_lower_fps)

    def _apply_upgrade_policy(self, snapshot) -> bool:
        next_higher_fps = self._next_higher_render_fps()
        if next_higher_fps is not None:
            stable_device_fps = 1.0 / max(snapshot.p95_frame_dt, 1e-6)
            safe_target = select_target_render_fps(
                self._display_hz_est,
                stable_device_fps,
                self._render_perf_config.fps_candidates,
                self._render_perf_config.safety_factor,
            )
            if next_higher_fps <= safe_target:
                return self._set_target_render_fps(next_higher_fps)
        if self._quality_level > 0:
            return self._set_quality_level(self._quality_level - 1)
        return False

    def _set_quality_level(self, quality_level: int) -> bool:
        resolved_level = max(0, min(int(quality_level), 2))
        if resolved_level == self._quality_level:
            return False
        self._quality_level = resolved_level
        self._apply_render_quality_profile()
        return True

    def _apply_render_quality_profile(self) -> None:
        visible_rows = int(
            WorldGridSpec.from_profile(self._config.road_profile).visible_row_end
            - WorldGridSpec.from_profile(self._config.road_profile).visible_row_start
            + 1
        )
        self._gameplay_renderer.set_quality_profile(
            build_render_quality_profile(self._quality_level, visible_rows)
        )

    def _set_target_render_fps(self, target_fps: int | None) -> bool:
        if target_fps is None:
            return False
        resolved_fps = int(target_fps)
        if resolved_fps == self._target_render_fps:
            return False
        self._target_render_fps = resolved_fps
        self._loop.set_target_fps(self._target_render_fps)
        return True

    def _current_fps_ladder(self) -> tuple[int, ...]:
        return build_target_fps_ladder(self._display_hz_est, self._render_perf_config.fps_candidates)

    def _next_lower_render_fps(self) -> int | None:
        ladder = self._current_fps_ladder()
        if self._target_render_fps not in ladder:
            return None
        index = ladder.index(self._target_render_fps)
        if index >= (len(ladder) - 1):
            return None
        return int(ladder[index + 1])

    def _next_higher_render_fps(self) -> int | None:
        ladder = self._current_fps_ladder()
        if self._target_render_fps not in ladder:
            return None
        index = ladder.index(self._target_render_fps)
        if index <= 0:
            return None
        return int(ladder[index - 1])
