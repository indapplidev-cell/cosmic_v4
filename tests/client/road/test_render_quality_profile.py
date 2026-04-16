from __future__ import annotations

from client.gameplay.engine.config import GameConfig
from client.gameplay.road.projection.perspective_projector import PerspectiveProjector
from client.gameplay.road.render.gameplay_renderer import GameplayRenderer
from client.gameplay.road.render.render_quality_profile import build_render_quality_profile
from client.gameplay.road.render.visual_road_geometry import build_visual_row_segments
from client.gameplay.road.road_models import RoadRow
from client.gameplay.road.road_profiles import NORMAL_PERSPECTIVE
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


def test_quality_level_zero_keeps_grid_and_outlines():
    renderer, spec, projector, profile = _build_renderer()
    row = RoadRow(seq=0, open_lanes=(2,))
    visual_segments = build_visual_row_segments(None, row, None)
    renderer.set_quality_profile(build_render_quality_profile(0, 10))

    _road_quads, road_outlines = renderer._build_row_road_segment_visuals(row, WORLD_ROW, spec, projector, profile, visual_segments=visual_segments)
    grid_lines = renderer._build_grid_lines(row, WORLD_ROW, visual_segments, spec, projector, profile)

    assert len(road_outlines) == 1
    assert len(grid_lines) == 2


def test_quality_level_one_disables_grid_and_keeps_outlines():
    renderer, spec, projector, profile = _build_renderer()
    row = RoadRow(seq=0, open_lanes=(2,))
    visual_segments = build_visual_row_segments(None, row, None)
    renderer.set_quality_profile(build_render_quality_profile(1, 10))

    _road_quads, road_outlines = renderer._build_row_road_segment_visuals(row, WORLD_ROW, spec, projector, profile, visual_segments=visual_segments)
    grid_lines = renderer._build_grid_lines(row, WORLD_ROW, visual_segments, spec, projector, profile)

    assert len(road_outlines) == 1
    assert grid_lines == ()


def test_quality_level_two_disables_grid_and_outlines():
    renderer, spec, projector, profile = _build_renderer()
    row = RoadRow(seq=0, open_lanes=(2,))
    visual_segments = build_visual_row_segments(None, row, None)
    renderer.set_quality_profile(build_render_quality_profile(2, 10))

    _road_quads, road_outlines = renderer._build_row_road_segment_visuals(row, WORLD_ROW, spec, projector, profile, visual_segments=visual_segments)
    grid_lines = renderer._build_grid_lines(row, WORLD_ROW, visual_segments, spec, projector, profile)

    assert road_outlines == ()
    assert grid_lines == ()


def test_quality_profile_limits_visible_rows_without_breaking_renderer_api():
    renderer, _spec, _projector, _profile = _build_renderer()
    renderer.set_quality_profile(build_render_quality_profile(2, 10))
    visible_rows = tuple((RoadRow(seq=index, open_lanes=(2,)), index, float(index)) for index in range(10))

    limited_rows = renderer._apply_visible_row_limit(visible_rows)

    assert len(limited_rows) == 6
    assert hasattr(renderer, 'set_quality_profile')


def test_quality_profile_clamps_quality_level():
    assert build_render_quality_profile(-1, 5).quality_level == 0
    assert build_render_quality_profile(9, 5).quality_level == 2
