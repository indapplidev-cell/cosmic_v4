from __future__ import annotations

from client.gameplay.engine.config import GameConfig
from client.gameplay.road.projection.perspective_projector import PerspectiveProjector
from client.gameplay.road.render.gameplay_renderer import GameplayRenderer
from client.gameplay.road.render.visual_road_geometry import VisualRoadSegment, build_visual_row_segments
from client.gameplay.road.road_models import RoadRow
from client.gameplay.road.road_profiles import NORMAL_PERSPECTIVE
from client.gameplay.road.turn_corner_geometry import TURN_CORNER_BRANCH_START_RATIO
from client.gameplay.road.world_grid_spec import WorldGridSpec

WIDTH = 1000
HEIGHT = 700
WORLD_ROW = 2.0


def _build_renderer():
    config = GameConfig()
    profile = NORMAL_PERSPECTIVE
    spec = WorldGridSpec.from_profile(profile)
    projector = PerspectiveProjector()
    projector.configure(WIDTH, HEIGHT, spec, profile.perspective)
    renderer = GameplayRenderer(None, config, projector)
    return renderer, spec, projector, profile


def test_renderer_builds_single_road_quad_for_single_lane_segment():
    renderer, spec, projector, profile = _build_renderer()
    row = RoadRow(seq=0, open_lanes=(2,))
    visual_segments = build_visual_row_segments(None, row, None)

    road_quads, road_outlines = renderer._build_row_road_segment_visuals(
        row,
        WORLD_ROW,
        spec,
        projector,
        profile,
        visual_segments=visual_segments,
    )
    full_width_quad = renderer._flatten_quad(
        renderer._build_visual_segment_quad(
            VisualRoadSegment(
                left=-0.5,
                right=profile.lane.lane_count - 0.5,
                bottom=0.0,
                top=1.0,
            ),
            WORLD_ROW,
            row.seq,
            spec.tile_size_world,
            spec.playable_column_start,
            projector,
        )
    )

    assert len(road_quads) == 1
    assert len(road_outlines) == 1
    assert road_quads[0][0] != full_width_quad


def test_renderer_builds_two_road_quads_for_l_corner_transition_segment():
    renderer, spec, projector, profile = _build_renderer()
    prev_row = RoadRow(seq=-1, open_lanes=(2,))
    row = RoadRow(seq=0, open_lanes=(2, 3))
    next_row = RoadRow(seq=1, open_lanes=(3,))
    visual_segments = build_visual_row_segments(prev_row, row, next_row)

    road_quads, road_outlines = renderer._build_row_road_segment_visuals(
        row,
        WORLD_ROW,
        spec,
        projector,
        profile,
        visual_segments=visual_segments,
    )

    assert len(road_quads) == 2
    assert len(road_outlines) == 2


def test_renderer_branch_quad_starts_above_row_bottom():
    renderer, spec, projector, profile = _build_renderer()
    prev_row = RoadRow(seq=-1, open_lanes=(2,))
    row = RoadRow(seq=0, open_lanes=(2, 3))
    next_row = RoadRow(seq=1, open_lanes=(3,))
    visual_segments = build_visual_row_segments(prev_row, row, next_row)

    road_quads, _road_outlines = renderer._build_row_road_segment_visuals(
        row,
        WORLD_ROW,
        spec,
        projector,
        profile,
        visual_segments=visual_segments,
    )

    stem_points = road_quads[0][0]
    branch_points = road_quads[1][0]
    full_height_branch = renderer._flatten_quad(
        renderer._build_visual_segment_quad(
            VisualRoadSegment(left=2.5, right=3.5, bottom=0.0, top=1.0),
            WORLD_ROW,
            row.seq,
            spec.tile_size_world,
            spec.playable_column_start,
            projector,
        )
    )

    assert branch_points != full_height_branch
    assert stem_points != branch_points
    assert visual_segments[1].bottom == TURN_CORNER_BRANCH_START_RATIO


def test_renderer_clips_grid_lines_to_real_segment_bounds():
    renderer, spec, projector, profile = _build_renderer()
    row = RoadRow(seq=0, open_lanes=(2,))
    visual_segments = build_visual_row_segments(None, row, None)

    grid_lines = renderer._build_grid_lines(
        row,
        WORLD_ROW,
        visual_segments,
        spec,
        projector,
        profile,
    )

    assert len(grid_lines) == 2
