from __future__ import annotations

from client.gameplay.road.logical_road_geometry import (
    LogicalRoadSegment,
    build_contiguous_lane_spans,
    build_row_logical_segments,
    build_rows_logical_segments,
)
from client.gameplay.road.road_models import RoadRow
from client.gameplay.road.turn_corner_geometry import TURN_CORNER_BRANCH_START_RATIO


def test_build_contiguous_lane_spans_groups_normalized_lanes():
    assert build_contiguous_lane_spans((2,)) == ((2, 2),)
    assert build_contiguous_lane_spans((2, 3)) == ((2, 3),)
    assert build_contiguous_lane_spans((3, 2, 2, 1, 5, 7, 6)) == ((1, 3), (5, 7))
    assert build_contiguous_lane_spans((1, 3)) == ((1, 1), (3, 3))


def test_build_logical_segments_for_straight_row_returns_one_full_height_rect():
    row = RoadRow(seq=10, open_lanes=(2,))

    assert build_row_logical_segments(None, row, None) == (
        LogicalRoadSegment(left=1.5, right=2.5, bottom=10.0, top=11.0),
    )


def test_build_logical_segments_for_right_turn_returns_stem_and_upper_branch():
    prev_row = RoadRow(seq=0, open_lanes=(2,))
    row = RoadRow(seq=1, open_lanes=(2, 3))
    next_row = RoadRow(seq=2, open_lanes=(3,))

    assert build_row_logical_segments(prev_row, row, next_row) == (
        LogicalRoadSegment(left=1.5, right=2.5, bottom=1.0, top=2.0),
        LogicalRoadSegment(
            left=2.5,
            right=3.5,
            bottom=1.0 + TURN_CORNER_BRANCH_START_RATIO,
            top=2.0,
        ),
    )


def test_build_logical_segments_for_left_turn_returns_stem_and_upper_branch():
    prev_row = RoadRow(seq=0, open_lanes=(3,))
    row = RoadRow(seq=1, open_lanes=(2, 3))
    next_row = RoadRow(seq=2, open_lanes=(2,))

    assert build_row_logical_segments(prev_row, row, next_row) == (
        LogicalRoadSegment(left=2.5, right=3.5, bottom=1.0, top=2.0),
        LogicalRoadSegment(
            left=1.5,
            right=2.5,
            bottom=1.0 + TURN_CORNER_BRANCH_START_RATIO,
            top=2.0,
        ),
    )


def test_malformed_transition_falls_back_to_two_full_height_rects():
    prev_row = RoadRow(seq=0, open_lanes=(2, 3))
    row = RoadRow(seq=1, open_lanes=(2, 3))
    next_row = RoadRow(seq=2, open_lanes=(2, 3))

    assert build_row_logical_segments(prev_row, row, next_row) == (
        LogicalRoadSegment(left=1.5, right=2.5, bottom=1.0, top=2.0),
        LogicalRoadSegment(left=2.5, right=3.5, bottom=1.0, top=2.0),
    )


def test_build_rows_logical_segments_aggregates_l_corner_row_segments():
    rows = (
        RoadRow(seq=0, open_lanes=(2,)),
        RoadRow(seq=1, open_lanes=(2, 3)),
        RoadRow(seq=2, open_lanes=(3,)),
    )

    assert build_rows_logical_segments(rows) == (
        LogicalRoadSegment(left=1.5, right=2.5, bottom=0.0, top=1.0),
        LogicalRoadSegment(left=1.5, right=2.5, bottom=1.0, top=2.0),
        LogicalRoadSegment(
            left=2.5,
            right=3.5,
            bottom=1.0 + TURN_CORNER_BRANCH_START_RATIO,
            top=2.0,
        ),
        LogicalRoadSegment(left=2.5, right=3.5, bottom=2.0, top=3.0),
    )
