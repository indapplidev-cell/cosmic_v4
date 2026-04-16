from __future__ import annotations

from dataclasses import dataclass

from client.gameplay.road.turn_corner_geometry import (
    TURN_CORNER_BRANCH_START_RATIO,
    adjacent_pair,
    resolve_transition_source_dest,
    single_lane,
)


@dataclass(frozen=True)
class LogicalRoadSegment:
    left: float
    right: float
    bottom: float
    top: float


def build_contiguous_lane_spans(open_lanes) -> tuple[tuple[int, int], ...]:
    normalized = sorted({int(lane) for lane in open_lanes})
    if not normalized:
        return ()

    spans: list[tuple[int, int]] = []
    start = normalized[0]
    end = normalized[0]
    for lane in normalized[1:]:
        if lane == (end + 1):
            end = lane
            continue
        spans.append((start, end))
        start = lane
        end = lane
    spans.append((start, end))
    return tuple(spans)


def _single_lane(row) -> int | None:
    return single_lane(row)


def _adjacent_pair(row) -> tuple[int, int] | None:
    return adjacent_pair(row)


def _lane_rect_segment(lane: int, bottom: float, top: float) -> LogicalRoadSegment:
    lane_value = int(lane)
    return LogicalRoadSegment(
        left=float(lane_value) - 0.5,
        right=float(lane_value) + 0.5,
        bottom=float(bottom),
        top=float(top),
    )


def _resolve_transition_source_dest(prev_row, row, next_row) -> tuple[int, int] | None:
    return resolve_transition_source_dest(prev_row, row, next_row)


def build_row_logical_segments(prev_row, row, next_row) -> tuple[LogicalRoadSegment, ...]:
    lanes = tuple(sorted(int(lane) for lane in getattr(row, 'open_lanes', ())))
    if not lanes:
        return ()

    bottom = float(row.seq)
    top = bottom + 1.0
    if len(lanes) == 1:
        return (_lane_rect_segment(lanes[0], bottom, top),)

    pair = _adjacent_pair(row)
    if pair is not None:
        resolved = _resolve_transition_source_dest(prev_row, row, next_row)
        if resolved is not None:
            source_lane, dest_lane = resolved
            branch_bottom = bottom + float(TURN_CORNER_BRANCH_START_RATIO)
            return (
                _lane_rect_segment(source_lane, bottom, top),
                _lane_rect_segment(dest_lane, branch_bottom, top),
            )
        return tuple(_lane_rect_segment(lane, bottom, top) for lane in pair)

    return tuple(_lane_rect_segment(lane, bottom, top) for lane in lanes)


def build_rows_logical_segments(rows) -> tuple[LogicalRoadSegment, ...]:
    return tuple(
        segment
        for index, row in enumerate(rows)
        for segment in build_row_logical_segments(
            rows[index - 1] if index > 0 else None,
            row,
            rows[index + 1] if (index + 1) < len(rows) else None,
        )
    )
