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


def _transition_rows():
    return (
        RoadRow(seq=0, open_lanes=(2,)),
        RoadRow(seq=1, open_lanes=(2, 3)),
        RoadRow(seq=2, open_lanes=(3,)),
    )


def test_transition_row_builds_two_l_corner_quads():
    renderer, spec, projector, profile = _build_renderer()
    prev_row, row, next_row = _transition_rows()
    visual_segments = build_visual_row_segments(prev_row, row, next_row)

    road_quads, _road_outlines = renderer._build_row_road_segment_visuals(
        row,
        WORLD_ROW,
        spec,
        projector,
        profile,
        visual_segments=visual_segments,
    )

    assert len(road_quads) == 2


def test_transition_row_lane_visual_uses_stem_and_upper_branch():
    renderer, spec, projector, profile = _build_renderer()
    prev_row, row, next_row = _transition_rows()
    visual_segments = build_visual_row_segments(prev_row, row, next_row)

    lane_quads = renderer._build_visual_lane_quads(
        visual_segments,
        WORLD_ROW,
        row.seq,
        spec,
        projector,
        profile.visual_variants[0].lane_open_color,
    )

    assert len(lane_quads) == 2


def test_transition_quads_match_stem_and_upper_branch_rectangles():
    renderer, spec, projector, profile = _build_renderer()
    prev_row, row, next_row = _transition_rows()
    visual_segments = build_visual_row_segments(prev_row, row, next_row)

    road_quads, _road_outlines = renderer._build_row_road_segment_visuals(
        row,
        WORLD_ROW,
        spec,
        projector,
        profile,
        visual_segments=visual_segments,
    )
    expected_stem = renderer._flatten_quad(
        renderer._build_visual_segment_quad(
            VisualRoadSegment(left=1.5, right=2.5, bottom=1.0, top=2.0),
            WORLD_ROW,
            row.seq,
            spec.tile_size_world,
            spec.playable_column_start,
            projector,
        )
    )
    expected_branch = renderer._flatten_quad(
        renderer._build_visual_segment_quad(
            VisualRoadSegment(
                left=2.5,
                right=3.5,
                bottom=1.0 + TURN_CORNER_BRANCH_START_RATIO,
                top=2.0,
            ),
            WORLD_ROW,
            row.seq,
            spec.tile_size_world,
            spec.playable_column_start,
            projector,
        )
    )

    assert road_quads[0][0] == expected_stem
    assert road_quads[1][0] == expected_branch


def test_transition_row_grid_lines_include_branch_boundaries():
    renderer, spec, projector, profile = _build_renderer()
    prev_row, row, next_row = _transition_rows()
    visual_segments = build_visual_row_segments(prev_row, row, next_row)

    grid_lines = renderer._build_grid_lines(
        row,
        WORLD_ROW,
        visual_segments,
        spec,
        projector,
        profile,
    )

    assert len(grid_lines) == 3
