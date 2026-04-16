from __future__ import annotations

from client.gameplay.road.render.visual_road_geometry import VisualRoadSegment, build_visual_row_segments
from client.gameplay.road.road_models import RoadRow
from client.gameplay.road.turn_corner_geometry import TURN_CORNER_BRANCH_START_RATIO


def test_build_visual_segments_for_straight_row_returns_one_full_height_rect():
    row = RoadRow(seq=1, open_lanes=(2,))

    assert build_visual_row_segments(None, row, None) == (
        VisualRoadSegment(left=1.5, right=2.5, bottom=1.0, top=2.0),
    )


def test_build_visual_segments_for_transition_row_returns_l_corner_shape():
    prev_row = RoadRow(seq=0, open_lanes=(2,))
    row = RoadRow(seq=1, open_lanes=(2, 3))
    next_row = RoadRow(seq=2, open_lanes=(3,))

    assert build_visual_row_segments(prev_row, row, next_row) == (
        VisualRoadSegment(left=1.5, right=2.5, bottom=1.0, top=2.0),
        VisualRoadSegment(
            left=2.5,
            right=3.5,
            bottom=1.0 + TURN_CORNER_BRANCH_START_RATIO,
            top=2.0,
        ),
    )


def test_visual_segments_for_malformed_transition_fall_back_to_two_full_height_rects():
    prev_row = RoadRow(seq=0, open_lanes=(2, 3))
    row = RoadRow(seq=1, open_lanes=(2, 3))
    next_row = RoadRow(seq=2, open_lanes=(2, 3))

    assert build_visual_row_segments(prev_row, row, next_row) == (
        VisualRoadSegment(left=1.5, right=2.5, bottom=1.0, top=2.0),
        VisualRoadSegment(left=2.5, right=3.5, bottom=1.0, top=2.0),
    )
