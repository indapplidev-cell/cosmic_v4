from __future__ import annotations


class ContinuousXController:
    """Own continuous horizontal position and input state for gameplay X motion."""

    def __init__(self, steer_speed_tiles_per_sec: float = 0.0) -> None:
        self._x_pos_tiles = 0.0
        self._input_dir = 0
        self._speed_tiles_per_sec = max(float(steer_speed_tiles_per_sec), 0.0)
        self._min_x = 0.0
        self._max_x = 0.0
        self._lane_count = 1

    def configure(
        self,
        *,
        lane_count: int,
        steer_speed_tiles_per_sec: float,
        start_lane: int | None = None,
    ) -> None:
        self._lane_count = max(int(lane_count), 1)
        self._min_x = 0.0
        self._max_x = float(self._lane_count - 1)
        self._speed_tiles_per_sec = max(float(steer_speed_tiles_per_sec), 0.0)
        if start_lane is not None:
            self.reset(start_lane)

    def reset(self, start_lane: int | None = None) -> None:
        if start_lane is None:
            start_lane = self._lane_count // 2
        self._x_pos_tiles = self._clamp_x(float(start_lane))
        self._input_dir = 0

    def set_input_direction(self, direction: int) -> None:
        direction = int(direction)
        if direction < 0:
            self._input_dir = -1
        elif direction > 0:
            self._input_dir = 1
        else:
            self._input_dir = 0

    def update(self, dt: float) -> None:
        dt = max(float(dt), 0.0)
        self._x_pos_tiles += float(self._input_dir) * self._speed_tiles_per_sec * dt
        self._x_pos_tiles = self._clamp_x(self._x_pos_tiles)

    def set_speed_tiles_per_sec(self, speed: float) -> None:
        self._speed_tiles_per_sec = max(float(speed), 0.0)

    def get_world_offset_x(self, road_profile) -> float:
        center_lane = float(road_profile.lane.resolved_start_lane)
        tile_size_world = float(road_profile.world.tile_size_world)
        return (center_lane - self.x_pos_tiles) * tile_size_world

    @property
    def x_pos_tiles(self) -> float:
        return self._x_pos_tiles

    @property
    def input_dir(self) -> int:
        return self._input_dir

    @property
    def speed_tiles_per_sec(self) -> float:
        return self._speed_tiles_per_sec

    def _clamp_x(self, value: float) -> float:
        return max(self._min_x, min(float(value), self._max_x))
