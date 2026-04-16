from __future__ import annotations

from dataclasses import dataclass

from client.gameplay.road.road_models import RoadRow
from client.gameplay.road.turn_corner_geometry import TURN_CORNER_BRANCH_START_RATIO, adjacent_pair, resolve_transition_source_dest


@dataclass(frozen=True)
class VisualRoadSegment:
    left: float
    right: float
    bottom: float
    top: float


def build_visual_row_segments(
    prev_row: RoadRow | None,
    row: RoadRow,
    next_row: RoadRow | None,
) -> tuple[VisualRoadSegment, ...]:
    lanes = tuple(sorted(int(lane) for lane in getattr(row, 'open_lanes', ())))
    if not lanes:
        return ()

    bottom = float(row.seq)
    top = bottom + 1.0
    if len(lanes) == 1:
        lane = lanes[0]
        return (
            VisualRoadSegment(
                left=float(lane) - 0.5,
                right=float(lane) + 0.5,
                bottom=bottom,
                top=top,
            ),
        )

    pair = adjacent_pair(row)
    if pair is not None:
        resolved = resolve_transition_source_dest(prev_row, row, next_row)
        if resolved is not None:
            source_lane, dest_lane = resolved
            branch_bottom = bottom + float(TURN_CORNER_BRANCH_START_RATIO)
            return (
                VisualRoadSegment(
                    left=float(source_lane) - 0.5,
                    right=float(source_lane) + 0.5,
                    bottom=bottom,
                    top=top,
                ),
                VisualRoadSegment(
                    left=float(dest_lane) - 0.5,
                    right=float(dest_lane) + 0.5,
                    bottom=branch_bottom,
                    top=top,
                ),
            )
        return tuple(
            VisualRoadSegment(
                left=float(lane) - 0.5,
                right=float(lane) + 0.5,
                bottom=bottom,
                top=top,
            )
            for lane in pair
        )

    return tuple(
        VisualRoadSegment(
            left=float(lane) - 0.5,
            right=float(lane) + 0.5,
            bottom=bottom,
            top=top,
        )
        for lane in lanes
    )
