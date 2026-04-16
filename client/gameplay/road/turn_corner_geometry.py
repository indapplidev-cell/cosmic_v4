from __future__ import annotations


TURN_CORNER_BRANCH_START_RATIO = 0.60


def single_lane(row) -> int | None:
    if row is None:
        return None
    lanes = tuple(int(lane) for lane in getattr(row, 'open_lanes', ()))
    if len(lanes) != 1:
        return None
    return int(lanes[0])


def adjacent_pair(row) -> tuple[int, int] | None:
    if row is None:
        return None
    lanes = tuple(sorted(int(lane) for lane in getattr(row, 'open_lanes', ())))
    if len(lanes) != 2:
        return None
    if abs(lanes[1] - lanes[0]) != 1:
        return None
    return lanes[0], lanes[1]


def resolve_transition_source_dest(prev_row, row, next_row) -> tuple[int, int] | None:
    pair = adjacent_pair(row)
    if pair is None:
        return None
    prev_lane = single_lane(prev_row)
    next_lane = single_lane(next_row)
    if prev_lane is None or next_lane is None:
        return None
    if prev_lane == next_lane:
        return None
    if prev_lane not in pair or next_lane not in pair:
        return None
    return int(prev_lane), int(next_lane)
