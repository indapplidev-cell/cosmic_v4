from __future__ import annotations

from collections import deque

from client.gameplay.collision.offroad_guard import Bounds2D, OffRoadGuard
from client.gameplay.road.path.road_path_stream import RoadPathRow, RoadPathStream
from client.gameplay.road.road_profiles import NORMAL_PERSPECTIVE
from client.gameplay.road.turn_corner_geometry import TURN_CORNER_BRANCH_START_RATIO


def _ship_bounds(
    center_x: float,
    *,
    bottom: float,
    top: float,
    half_width: float = 0.10,
) -> Bounds2D:
    return Bounds2D(
        left=float(center_x) - half_width,
        right=float(center_x) + half_width,
        bottom=float(bottom),
        top=float(top),
    )


def _segments(*rows: RoadPathRow):
    stream = RoadPathStream()
    stream.configure(NORMAL_PERSPECTIVE)
    stream._rows = deque(rows)
    return stream.get_active_road_segments()


def test_ship_inside_source_stem_of_transition_row_is_onroad():
    guard = OffRoadGuard()

    assert guard.is_ship_on_road(
        ship_bounds=_ship_bounds(2.0, bottom=1.05, top=1.15),
        road_segments=_segments(
            RoadPathRow(seq=0, open_lanes=(2,)),
            RoadPathRow(seq=1, open_lanes=(2, 3)),
            RoadPathRow(seq=2, open_lanes=(3,)),
        ),
    ) is True


def test_ship_inside_destination_branch_lower_part_is_offroad_before_branch_opens():
    guard = OffRoadGuard()

    assert guard.is_ship_on_road(
        ship_bounds=_ship_bounds(3.0, bottom=1.05, top=1.15),
        road_segments=_segments(
            RoadPathRow(seq=0, open_lanes=(2,)),
            RoadPathRow(seq=1, open_lanes=(2, 3)),
            RoadPathRow(seq=2, open_lanes=(3,)),
        ),
    ) is False


def test_ship_inside_destination_branch_upper_part_is_onroad_after_branch_opens():
    guard = OffRoadGuard()
    branch_bottom = 1.0 + TURN_CORNER_BRANCH_START_RATIO

    assert guard.is_ship_on_road(
        ship_bounds=_ship_bounds(3.0, bottom=branch_bottom + 0.05, top=branch_bottom + 0.15),
        road_segments=_segments(
            RoadPathRow(seq=0, open_lanes=(2,)),
            RoadPathRow(seq=1, open_lanes=(2, 3)),
            RoadPathRow(seq=2, open_lanes=(3,)),
        ),
    ) is True


def test_old_full_union_rect_safe_zone_no_longer_exists():
    guard = OffRoadGuard()
    branch_bottom = 1.0 + TURN_CORNER_BRANCH_START_RATIO

    assert guard.is_ship_on_road(
        ship_bounds=_ship_bounds(3.0, bottom=branch_bottom - 0.20, top=branch_bottom - 0.10),
        road_segments=_segments(
            RoadPathRow(seq=0, open_lanes=(2,)),
            RoadPathRow(seq=1, open_lanes=(2, 3)),
            RoadPathRow(seq=2, open_lanes=(3,)),
        ),
    ) is False


def test_gap_between_disjoint_spans_remains_offroad():
    guard = OffRoadGuard()

    assert guard.is_ship_on_road(
        ship_bounds=_ship_bounds(2.0, bottom=0.0, top=0.18),
        road_segments=_segments(RoadPathRow(seq=0, open_lanes=(1, 3))),
    ) is False
