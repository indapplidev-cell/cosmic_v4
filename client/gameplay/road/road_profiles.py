from __future__ import annotations

from dataclasses import dataclass


RGBA = tuple[float, float, float, float]


@dataclass(frozen=True)
class SegmentVisualVariant:
    variant_id: str
    road_color: RGBA
    lane_open_color: RGBA
    shoulder_color: RGBA
    grid_color: RGBA = (1.0, 1.0, 1.0, 0.82)


@dataclass(frozen=True)
class ObstacleVisualConfig:
    fill_color: RGBA = (0.10, 0.10, 0.12, 0.94)
    outline_color: RGBA = (1.0, 1.0, 1.0, 0.82)
    inset_x_ratio: float = 0.18
    inset_y_ratio: float = 0.22
    top_narrow_ratio: float = 0.14
    outline_width: float = 1.05


@dataclass(frozen=True)
class PerspectiveConfig:
    perspective_point_x_ratio: float
    horizon_y_ratio: float
    visible_segments: int
    recycle_buffer: int
    curve_power: float
    ship_anchor_depth: float
    far_opacity: float
    grid_line_width: float
    road_fill_alpha: float


@dataclass(frozen=True)
class WorldConfig:
    tile_size_world: float
    vertical_line_count: int
    horizontal_line_count: int
    vertical_spacing_ratio: float
    horizontal_spacing_ratio: float
    visible_depth_rows: int
    start_line_index: int
    end_line_index: int


@dataclass(frozen=True)
class LaneConfig:
    lane_count: int
    steer_speed_tiles_per_sec: float
    speed_modes: 'XSpeedModesConfig | None' = None
    start_lane: int | None = None

    @property
    def resolved_start_lane(self) -> int:
        if self.start_lane is not None:
            return self.start_lane
        return self.lane_count // 2

    @property
    def resolved_default_steer_speed_tiles_per_sec(self) -> float:
        if self.speed_modes is not None:
            if self.speed_modes.default_mode == 'primary':
                return float(self.speed_modes.primary_speed_tiles_per_sec)
            if self.speed_modes.default_mode == 'secondary':
                return float(self.speed_modes.secondary_speed_tiles_per_sec)
        return float(self.steer_speed_tiles_per_sec)


@dataclass(frozen=True)
class XSpeedModesConfig:
    primary_speed_tiles_per_sec: float
    secondary_speed_tiles_per_sec: float
    default_mode: str


@dataclass(frozen=True)
class ObstacleConfig:
    spawn_chance: float
    protected_start_segments: int
    min_free_lanes: int
    next_segment_collision_progress: float


@dataclass(frozen=True)
class PathGenerationConfig:
    initial_straight_rows: int
    min_straight_rows_after_turn: int
    max_straight_rows_after_turn: int
    min_turn_steps: int
    max_turn_steps: int
    straight_weight: int


@dataclass(frozen=True)
class MotionConfig:
    segment_speed_units_per_sec: float
    brake_speed_factor: float


@dataclass(frozen=True)
class RoadProfileConfig:
    profile_id: str
    perspective: PerspectiveConfig
    world: WorldConfig
    lane: LaneConfig
    obstacle: ObstacleConfig
    path_generation: PathGenerationConfig
    motion: MotionConfig
    visual_variants: tuple[SegmentVisualVariant, ...]
    obstacle_visual: ObstacleVisualConfig
    random_seed: int = 7

    @property
    def pool_size(self) -> int:
        return self.perspective.visible_segments + self.perspective.recycle_buffer


V3_WORLD = WorldConfig(
    tile_size_world=1.0,
    vertical_line_count=8,
    horizontal_line_count=15,
    vertical_spacing_ratio=0.4,
    horizontal_spacing_ratio=0.1,
    visible_depth_rows=10,
    start_line_index=-3,
    end_line_index=4,
)

V3_PERSPECTIVE = PerspectiveConfig(
    perspective_point_x_ratio=0.5,
    horizon_y_ratio=0.75,
    visible_segments=15,
    recycle_buffer=4,
    curve_power=4.0,
    ship_anchor_depth=0.18,
    far_opacity=0.28,
    grid_line_width=1.15,
    road_fill_alpha=0.16,
)

DEFAULT_PATH_GENERATION = PathGenerationConfig(
    initial_straight_rows=6,
    min_straight_rows_after_turn=4,
    max_straight_rows_after_turn=7,
    min_turn_steps=1,
    max_turn_steps=2,
    straight_weight=3,
)

NORMAL_PERSPECTIVE = RoadProfileConfig(
    profile_id='normal_perspective',
    perspective=V3_PERSPECTIVE,
    world=V3_WORLD,
    lane=LaneConfig(
        lane_count=5,
        steer_speed_tiles_per_sec=3.0,
        speed_modes=XSpeedModesConfig(
            primary_speed_tiles_per_sec=4.0,
            secondary_speed_tiles_per_sec=3.0,
            default_mode='primary',
        ),
        start_lane=2,
    ),
    obstacle=ObstacleConfig(
        spawn_chance=0.18,
        protected_start_segments=10,
        min_free_lanes=1,
        next_segment_collision_progress=0.6,
    ),
    path_generation=DEFAULT_PATH_GENERATION,
    motion=MotionConfig(
        segment_speed_units_per_sec=4.8,
        brake_speed_factor=0.10,
    ),
    visual_variants=(
        SegmentVisualVariant(
            variant_id='primary',
            road_color=(0.0, 0.0, 0.0, 1.0),
            lane_open_color=(0.98, 0.98, 0.98, 1.0),
            shoulder_color=(1.0, 1.0, 1.0, 0.90),
            grid_color=(1.0, 1.0, 1.0, 0.84),
        ),
        SegmentVisualVariant(
            variant_id='secondary',
            road_color=(0.0, 0.0, 0.0, 1.0),
            lane_open_color=(0.95, 0.95, 0.95, 0.98),
            shoulder_color=(1.0, 1.0, 1.0, 0.82),
            grid_color=(1.0, 1.0, 1.0, 0.76),
        ),
    ),
    obstacle_visual=ObstacleVisualConfig(),
    random_seed=11,
)

AGGRESSIVE_PERSPECTIVE = RoadProfileConfig(
    profile_id='aggressive_perspective',
    perspective=PerspectiveConfig(
        perspective_point_x_ratio=V3_PERSPECTIVE.perspective_point_x_ratio,
        horizon_y_ratio=V3_PERSPECTIVE.horizon_y_ratio,
        visible_segments=V3_PERSPECTIVE.visible_segments,
        recycle_buffer=V3_PERSPECTIVE.recycle_buffer,
        curve_power=V3_PERSPECTIVE.curve_power,
        ship_anchor_depth=V3_PERSPECTIVE.ship_anchor_depth,
        far_opacity=0.24,
        grid_line_width=1.10,
        road_fill_alpha=0.14,
    ),
    world=V3_WORLD,
    lane=NORMAL_PERSPECTIVE.lane,
    obstacle=NORMAL_PERSPECTIVE.obstacle,
    path_generation=NORMAL_PERSPECTIVE.path_generation,
    motion=MotionConfig(
        segment_speed_units_per_sec=5.3,
        brake_speed_factor=0.12,
    ),
    visual_variants=NORMAL_PERSPECTIVE.visual_variants,
    obstacle_visual=NORMAL_PERSPECTIVE.obstacle_visual,
    random_seed=17,
)

NARROW_ROAD = RoadProfileConfig(
    profile_id='narrow_road',
    perspective=PerspectiveConfig(
        perspective_point_x_ratio=V3_PERSPECTIVE.perspective_point_x_ratio,
        horizon_y_ratio=V3_PERSPECTIVE.horizon_y_ratio,
        visible_segments=V3_PERSPECTIVE.visible_segments,
        recycle_buffer=V3_PERSPECTIVE.recycle_buffer,
        curve_power=V3_PERSPECTIVE.curve_power,
        ship_anchor_depth=V3_PERSPECTIVE.ship_anchor_depth,
        far_opacity=V3_PERSPECTIVE.far_opacity,
        grid_line_width=V3_PERSPECTIVE.grid_line_width,
        road_fill_alpha=0.14,
    ),
    world=V3_WORLD,
    lane=LaneConfig(
        lane_count=5,
        steer_speed_tiles_per_sec=3.0,
        speed_modes=XSpeedModesConfig(
            primary_speed_tiles_per_sec=4.0,
            secondary_speed_tiles_per_sec=3.0,
            default_mode='primary',
        ),
        start_lane=2,
    ),
    obstacle=NORMAL_PERSPECTIVE.obstacle,
    path_generation=DEFAULT_PATH_GENERATION,
    motion=MotionConfig(
        segment_speed_units_per_sec=4.7,
        brake_speed_factor=0.10,
    ),
    visual_variants=NORMAL_PERSPECTIVE.visual_variants,
    obstacle_visual=NORMAL_PERSPECTIVE.obstacle_visual,
    random_seed=19,
)

WIDE_ROAD = RoadProfileConfig(
    profile_id='wide_road',
    perspective=PerspectiveConfig(
        perspective_point_x_ratio=V3_PERSPECTIVE.perspective_point_x_ratio,
        horizon_y_ratio=V3_PERSPECTIVE.horizon_y_ratio,
        visible_segments=V3_PERSPECTIVE.visible_segments,
        recycle_buffer=V3_PERSPECTIVE.recycle_buffer,
        curve_power=V3_PERSPECTIVE.curve_power,
        ship_anchor_depth=0.16,
        far_opacity=0.30,
        grid_line_width=1.18,
        road_fill_alpha=0.17,
    ),
    world=V3_WORLD,
    lane=LaneConfig(
        lane_count=5,
        steer_speed_tiles_per_sec=3.0,
        speed_modes=XSpeedModesConfig(
            primary_speed_tiles_per_sec=4.0,
            secondary_speed_tiles_per_sec=3.0,
            default_mode='primary',
        ),
        start_lane=2,
    ),
    obstacle=NORMAL_PERSPECTIVE.obstacle,
    path_generation=DEFAULT_PATH_GENERATION,
    motion=MotionConfig(
        segment_speed_units_per_sec=4.5,
        brake_speed_factor=0.09,
    ),
    visual_variants=NORMAL_PERSPECTIVE.visual_variants,
    obstacle_visual=NORMAL_PERSPECTIVE.obstacle_visual,
    random_seed=23,
)

ROAD_PROFILE_REGISTRY: dict[str, RoadProfileConfig] = {
    NORMAL_PERSPECTIVE.profile_id: NORMAL_PERSPECTIVE,
    AGGRESSIVE_PERSPECTIVE.profile_id: AGGRESSIVE_PERSPECTIVE,
    NARROW_ROAD.profile_id: NARROW_ROAD,
    WIDE_ROAD.profile_id: WIDE_ROAD,
}

LEVEL_ROAD_PROFILE_MAP: dict[str, str] = {
    'default': NORMAL_PERSPECTIVE.profile_id,
    'level_1': NORMAL_PERSPECTIVE.profile_id,
    'level_2': WIDE_ROAD.profile_id,
    'level_3': NARROW_ROAD.profile_id,
    'level_4': AGGRESSIVE_PERSPECTIVE.profile_id,
    'level_5': NORMAL_PERSPECTIVE.profile_id,
    'level_6': WIDE_ROAD.profile_id,
    'level_7': NARROW_ROAD.profile_id,
    'level_8': AGGRESSIVE_PERSPECTIVE.profile_id,
    'level_9': WIDE_ROAD.profile_id,
    'level_10': AGGRESSIVE_PERSPECTIVE.profile_id,
    'survive_timed_level_01': NORMAL_PERSPECTIVE.profile_id,
    'survive_timed_level_02': NORMAL_PERSPECTIVE.profile_id,
    'survive_timed_level_03': WIDE_ROAD.profile_id,
    'survive_timed_level_04': WIDE_ROAD.profile_id,
    'survive_timed_level_05': NARROW_ROAD.profile_id,
    'survive_timed_level_06': NARROW_ROAD.profile_id,
    'survive_timed_level_07': AGGRESSIVE_PERSPECTIVE.profile_id,
    'survive_timed_level_08': AGGRESSIVE_PERSPECTIVE.profile_id,
    'survive_timed_level_09': WIDE_ROAD.profile_id,
    'survive_timed_level_10': AGGRESSIVE_PERSPECTIVE.profile_id,
}


def get_road_profile(profile_id: str | None) -> RoadProfileConfig:
    resolved = str(profile_id or LEVEL_ROAD_PROFILE_MAP['default']).strip().lower()
    return ROAD_PROFILE_REGISTRY.get(resolved, NORMAL_PERSPECTIVE)


def get_level_road_profile_id(level_id: str | None) -> str:
    resolved = str(level_id or '').strip().lower()
    if resolved in LEVEL_ROAD_PROFILE_MAP:
        return LEVEL_ROAD_PROFILE_MAP[resolved]
    return LEVEL_ROAD_PROFILE_MAP['default']
