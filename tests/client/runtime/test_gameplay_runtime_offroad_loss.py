from __future__ import annotations

from collections import deque
from types import SimpleNamespace

from client.gameplay.road.path.road_path_stream import RoadPathRow
from client.gameplay.road.road_models import RoadEntity
from client.gameplay.road.turn_corner_geometry import TURN_CORNER_BRANCH_START_RATIO
from client.gameplay.runtime.gameplay_runtime import FIXED_DT, GameplayRuntime
from client.gameplay.widgets.gameplay_surface import GameplaySurface


def _build_runtime() -> GameplayRuntime:
    surface = GameplaySurface()
    surface.size = (1000, 700)
    runtime = GameplayRuntime(surface)
    runtime._state.mark_started()
    return runtime


def _set_rows(runtime: GameplayRuntime, *rows: RoadPathRow) -> None:
    runtime._segment_stream._rows = deque(rows)


def test_runtime_does_not_trigger_loss_while_ship_bounds_stay_inside_real_segment():
    runtime = _build_runtime()
    runtime._motion.step = lambda *_args, **_kwargs: SimpleNamespace(advanced_rows=0)
    loss_calls: list[str] = []
    runtime.on_loss = lambda: loss_calls.append('loss')

    _set_rows(
        runtime,
        RoadPathRow(seq=0, open_lanes=(2,)),
        RoadPathRow(seq=1, open_lanes=(2,)),
        RoadPathRow(seq=2, open_lanes=(2,)),
    )
    runtime._fixed_update(FIXED_DT)

    assert loss_calls == []
    assert runtime._session.get_attempts_left() == 3


def test_runtime_triggers_loss_when_continuous_x_moves_ship_partly_outside_real_segment():
    runtime = _build_runtime()
    runtime._motion.step = lambda *_args, **_kwargs: SimpleNamespace(advanced_rows=0)
    loss_calls: list[str] = []
    runtime.on_loss = lambda: loss_calls.append('loss')

    _set_rows(
        runtime,
        RoadPathRow(seq=0, open_lanes=(2,)),
        RoadPathRow(seq=1, open_lanes=(2,)),
    )
    runtime._x_controller._x_pos_tiles = 2.27

    runtime._fixed_update(FIXED_DT)

    assert loss_calls == ['loss']


def test_runtime_treats_gap_between_disjoint_segments_as_offroad():
    runtime = _build_runtime()
    runtime._motion.step = lambda *_args, **_kwargs: SimpleNamespace(advanced_rows=0)
    loss_calls: list[str] = []
    runtime.on_loss = lambda: loss_calls.append('loss')

    _set_rows(
        runtime,
        RoadPathRow(seq=0, open_lanes=(1, 3)),
        RoadPathRow(seq=1, open_lanes=(1, 3)),
    )

    runtime._fixed_update(FIXED_DT)

    assert loss_calls == ['loss']


def test_runtime_continuous_x_motion_changes_ship_bounds_without_lane_transition_state():
    runtime = _build_runtime()
    runtime._motion.step = lambda *_args, **_kwargs: SimpleNamespace(advanced_rows=0)
    _set_rows(
        runtime,
        RoadPathRow(seq=0, open_lanes=(2,)),
        RoadPathRow(seq=1, open_lanes=(2,)),
        RoadPathRow(seq=2, open_lanes=(2,)),
    )
    start_x = runtime._x_controller.x_pos_tiles

    runtime.set_x_input_direction(1)
    runtime._fixed_update(FIXED_DT)

    assert runtime._x_controller.x_pos_tiles > start_x
    assert not hasattr(runtime, '_lane_motion')
    assert not hasattr(runtime, '_lane_state')


def test_runtime_active_loss_path_is_offroad_only():
    runtime = _build_runtime()
    runtime._motion.step = lambda *_args, **_kwargs: SimpleNamespace(advanced_rows=0)
    loss_calls: list[str] = []
    runtime.on_loss = lambda: loss_calls.append('loss')

    _set_rows(
        runtime,
        RoadPathRow(
            seq=0,
            open_lanes=(2,),
            entities=(RoadEntity(kind='obstacle', lane=2, row_seq=0),),
        ),
        RoadPathRow(seq=1, open_lanes=(2,), entities=()),
        RoadPathRow(seq=2, open_lanes=(2,), entities=()),
    )

    runtime._fixed_update(FIXED_DT)

    assert loss_calls == []


def test_runtime_does_not_trigger_loss_inside_transition_source_stem():
    runtime = _build_runtime()
    runtime._motion.step = lambda *_args, **_kwargs: SimpleNamespace(advanced_rows=0)
    loss_calls: list[str] = []
    runtime.on_loss = lambda: loss_calls.append('loss')
    runtime._state.current_y_loop = 1
    runtime._state.current_offset_y = 0.05
    runtime._x_controller._x_pos_tiles = 2.0

    _set_rows(
        runtime,
        RoadPathRow(seq=0, open_lanes=(2,)),
        RoadPathRow(seq=1, open_lanes=(2, 3)),
        RoadPathRow(seq=2, open_lanes=(3,)),
    )

    runtime._fixed_update(FIXED_DT)

    assert loss_calls == []


def test_runtime_triggers_loss_in_destination_lane_before_branch_opens():
    runtime = _build_runtime()
    runtime._motion.step = lambda *_args, **_kwargs: SimpleNamespace(advanced_rows=0)
    loss_calls: list[str] = []
    runtime.on_loss = lambda: loss_calls.append('loss')
    runtime._state.current_y_loop = 1
    runtime._state.current_offset_y = 0.05
    runtime._x_controller._x_pos_tiles = 3.0

    _set_rows(
        runtime,
        RoadPathRow(seq=0, open_lanes=(2,)),
        RoadPathRow(seq=1, open_lanes=(2, 3)),
        RoadPathRow(seq=2, open_lanes=(3,)),
    )

    runtime._fixed_update(FIXED_DT)

    assert loss_calls == ['loss']


def test_runtime_does_not_trigger_loss_in_destination_lane_after_branch_opens():
    runtime = _build_runtime()
    runtime._motion.step = lambda *_args, **_kwargs: SimpleNamespace(advanced_rows=0)
    loss_calls: list[str] = []
    runtime.on_loss = lambda: loss_calls.append('loss')
    runtime._state.current_y_loop = 1
    runtime._state.current_offset_y = TURN_CORNER_BRANCH_START_RATIO + 0.02
    runtime._x_controller._x_pos_tiles = 3.0

    _set_rows(
        runtime,
        RoadPathRow(seq=0, open_lanes=(2,)),
        RoadPathRow(seq=1, open_lanes=(2, 3)),
        RoadPathRow(seq=2, open_lanes=(3,)),
    )

    runtime._fixed_update(FIXED_DT)

    assert loss_calls == []
