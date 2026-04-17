from __future__ import annotations

from math import isclose
from types import SimpleNamespace

import client.gameplay.input.adapters.keyboard_adapter as keyboard_adapter_module
from client.application.gameplay.game_control_manager import GameControlManager
from client.gameplay.engine.continuous_x_controller import ContinuousXController
from client.gameplay.runtime.gameplay_runtime import FIXED_DT, GameplayRuntime
from client.gameplay.widgets.gameplay_surface import GameplaySurface
from client.gameplay.input.adapters.keyboard_adapter import KeyboardAdapter


class _RuntimeStub:
    def __init__(self) -> None:
        self.input_dir_calls: list[int] = []
        self.brake_calls: list[str] = []
        self.bound_control_manager = None

    def bind_control_manager(self, manager) -> None:
        self.bound_control_manager = manager

    def set_x_input_direction(self, direction: int) -> None:
        self.input_dir_calls.append(int(direction))

    def brake_on(self) -> None:
        self.brake_calls.append('on')

    def brake_off(self) -> None:
        self.brake_calls.append('off')


class _WidgetStub:
    x = 0
    width = 100

    @staticmethod
    def collide_point(x, y) -> bool:
        return True

    @staticmethod
    def bind(**_kwargs) -> None:
        return None

    @staticmethod
    def unbind(**_kwargs) -> None:
        return None


def _build_runtime() -> GameplayRuntime:
    surface = GameplaySurface()
    surface.size = (1000, 700)
    runtime = GameplayRuntime(surface)
    runtime._offroad_guard.is_ship_on_road = lambda *args, **kwargs: True
    runtime._state.mark_started()
    return runtime


def _keyboard_key_down(adapter, key: int, scancode: int, codepoint: str = '') -> bool:
    return adapter._on_key_down(None, key, scancode, codepoint, [])


def _keyboard_key_up(adapter, key: int, scancode: int) -> bool:
    return adapter._on_key_up(None, key, scancode)


def _touch_event(uid: int, x: int, y: int = 10):
    return SimpleNamespace(x=x, y=y, uid=uid)


def test_game_control_manager_press_left_sets_negative_direction():
    runtime = _RuntimeStub()
    manager = GameControlManager(runtime)

    manager.hud_event('left', True)
    manager.advance_control_state(FIXED_DT)

    assert runtime.input_dir_calls[-1] == -1


def test_game_control_manager_press_right_sets_positive_direction():
    runtime = _RuntimeStub()
    manager = GameControlManager(runtime)

    manager.hud_event('right', True)
    manager.advance_control_state(FIXED_DT)

    assert runtime.input_dir_calls[-1] == 1


def test_game_control_manager_release_left_stops_horizontal_motion():
    runtime = _RuntimeStub()
    manager = GameControlManager(runtime)

    manager.hud_event('left', True)
    manager.advance_control_state(FIXED_DT)
    manager.hud_event('left', False)
    manager.advance_control_state(FIXED_DT)

    assert runtime.input_dir_calls[-1] == 0


def test_game_control_manager_release_right_stops_horizontal_motion():
    runtime = _RuntimeStub()
    manager = GameControlManager(runtime)

    manager.hud_event('right', True)
    manager.advance_control_state(FIXED_DT)
    manager.hud_event('right', False)
    manager.advance_control_state(FIXED_DT)

    assert runtime.input_dir_calls[-1] == 0


def test_game_control_manager_opposite_buttons_resolve_to_zero():
    runtime = _RuntimeStub()
    manager = GameControlManager(runtime)

    manager.hud_event('left', True)
    manager.hud_event('right', True)
    manager.advance_control_state(FIXED_DT)

    assert runtime.input_dir_calls[-1] == 0


def test_continuous_x_controller_moves_left_while_input_negative():
    controller = ContinuousXController()
    controller.configure(lane_count=5, steer_speed_tiles_per_sec=3.0, start_lane=2)
    controller.set_input_direction(-1)

    controller.update(0.1)

    assert isclose(controller.x_pos_tiles, 1.7, rel_tol=0.0, abs_tol=1e-9)


def test_continuous_x_controller_moves_right_while_input_positive():
    controller = ContinuousXController()
    controller.configure(lane_count=5, steer_speed_tiles_per_sec=3.0, start_lane=2)
    controller.set_input_direction(1)

    controller.update(0.1)

    assert isclose(controller.x_pos_tiles, 2.3, rel_tol=0.0, abs_tol=1e-9)


def test_continuous_x_controller_stops_on_zero_input():
    controller = ContinuousXController()
    controller.configure(lane_count=5, steer_speed_tiles_per_sec=3.0, start_lane=2)
    controller.set_input_direction(1)
    controller.update(0.1)
    moved_x = controller.x_pos_tiles

    controller.set_input_direction(0)
    controller.update(0.1)

    assert isclose(controller.x_pos_tiles, moved_x, rel_tol=0.0, abs_tol=1e-9)


def test_continuous_x_controller_clamps_to_lane_envelope():
    controller = ContinuousXController()
    controller.configure(lane_count=5, steer_speed_tiles_per_sec=3.0, start_lane=0)
    controller.set_input_direction(-1)
    controller.update(1.0)
    assert isclose(controller.x_pos_tiles, 0.0, rel_tol=0.0, abs_tol=1e-9)

    controller.reset(4)
    controller.set_input_direction(1)
    controller.update(1.0)
    assert isclose(controller.x_pos_tiles, 4.0, rel_tol=0.0, abs_tol=1e-9)


def test_runtime_set_x_input_direction_updates_controller_input():
    runtime = _build_runtime()

    runtime.set_x_input_direction(1)
    assert runtime._x_controller.input_dir == 1
    assert runtime._state.current_speed_x == 1.0

    runtime.set_x_input_direction(0)
    assert runtime._x_controller.input_dir == 0
    assert runtime._state.current_speed_x == 0.0


def test_runtime_fixed_update_moves_ship_x_continuously():
    runtime = _build_runtime()
    runtime._motion.step = lambda *args, **kwargs: SimpleNamespace(advanced_rows=0)
    start_x = runtime._x_controller.x_pos_tiles

    runtime.set_x_input_direction(1)
    runtime._fixed_update(FIXED_DT)

    assert runtime._x_controller.x_pos_tiles > start_x
    assert isclose(runtime._x_controller.x_pos_tiles, start_x + (4.0 * FIXED_DT), rel_tol=0.0, abs_tol=1e-9)


def test_runtime_build_frame_snapshot_uses_controller_x():
    runtime = _build_runtime()
    runtime._state.render_path_rows = ()
    runtime._state.render_offset_y = 0.0
    runtime._state.world_offset_x = 0.0
    runtime._x_controller.reset(3)

    snapshot = runtime.build_frame_snapshot()

    assert snapshot.ship_lane_x == 3.0


def test_runtime_soft_reset_recenters_controller_x():
    runtime = _build_runtime()
    runtime.set_x_input_direction(1)
    runtime._x_controller._x_pos_tiles = 3.4
    runtime._state.current_y_loop = 5
    runtime._state.current_offset_y = 0.25

    runtime._trigger_loss()

    assert isclose(runtime._x_controller.x_pos_tiles, 2.0, rel_tol=0.0, abs_tol=1e-9)
    assert runtime._x_controller.input_dir == 0
    assert runtime._state.current_speed_x == 0.0
    assert runtime._state.state_game_over is False


def test_lane_config_default_speed_resolves_to_primary_mode():
    runtime = _build_runtime()

    assert runtime._config.road_profile.lane.resolved_default_steer_speed_tiles_per_sec == 4.0


def test_runtime_default_x_speed_mode_is_primary_and_uses_4_0():
    runtime = _build_runtime()

    assert runtime.get_x_speed_mode() == 'primary'
    assert runtime.get_x_speed_tiles_per_sec() == 4.0


def test_runtime_can_switch_to_secondary_3_0_mode():
    runtime = _build_runtime()

    runtime.set_x_speed_mode('secondary')

    assert runtime.get_x_speed_mode() == 'secondary'
    assert runtime.get_x_speed_tiles_per_sec() == 3.0


def test_runtime_can_switch_back_to_primary_4_0_mode():
    runtime = _build_runtime()

    runtime.set_x_speed_mode('secondary')
    runtime.set_x_speed_mode('primary')

    assert runtime.get_x_speed_mode() == 'primary'
    assert runtime.get_x_speed_tiles_per_sec() == 4.0


def test_toggle_x_speed_mode_switches_between_primary_and_secondary():
    runtime = _build_runtime()

    runtime.toggle_x_speed_mode()
    assert runtime.get_x_speed_mode() == 'secondary'
    assert runtime.get_x_speed_tiles_per_sec() == 3.0

    runtime.toggle_x_speed_mode()
    assert runtime.get_x_speed_mode() == 'primary'
    assert runtime.get_x_speed_tiles_per_sec() == 4.0


def test_continuous_x_controller_moves_faster_in_primary_mode_than_secondary():
    runtime = _build_runtime()
    runtime._motion.step = lambda *args, **kwargs: SimpleNamespace(advanced_rows=0)
    start_x = 2.0

    runtime._x_controller.reset(start_x)
    runtime.set_x_speed_mode('primary')
    runtime.set_x_input_direction(1)
    runtime._fixed_update(0.1)
    primary_x = runtime._x_controller.x_pos_tiles

    runtime._x_controller.reset(start_x)
    runtime.set_x_speed_mode('secondary')
    runtime.set_x_input_direction(1)
    runtime._fixed_update(0.1)
    secondary_x = runtime._x_controller.x_pos_tiles

    assert isclose(primary_x, start_x + 0.4, rel_tol=0.0, abs_tol=1e-9)
    assert isclose(secondary_x, start_x + 0.3, rel_tol=0.0, abs_tol=1e-9)


def test_reset_x_pipeline_preserves_selected_speed_mode():
    runtime = _build_runtime()

    runtime.set_x_speed_mode('secondary')
    runtime._reset_x_pipeline(base_seq=0)

    assert runtime.get_x_speed_mode() == 'secondary'
    assert runtime.get_x_speed_tiles_per_sec() == 3.0


def test_keyboard_adapter_no_runtime_dependency():
    runtime = _RuntimeStub()
    manager = GameControlManager(runtime)

    assert isinstance(manager._keyboard, KeyboardAdapter)
    assert not hasattr(manager._keyboard, '_runtime')


def test_keyboard_press_sets_left_pressed_state():
    runtime = _RuntimeStub()
    manager = GameControlManager(runtime)

    assert _keyboard_key_down(manager._keyboard, 1073741904, 80) is True
    manager.advance_control_state(FIXED_DT)

    assert manager._input_state.left_pressed is True


def test_keyboard_release_clears_left_pressed_state():
    runtime = _RuntimeStub()
    manager = GameControlManager(runtime)

    _keyboard_key_down(manager._keyboard, 1073741904, 80)
    manager.advance_control_state(FIXED_DT)
    assert _keyboard_key_up(manager._keyboard, 1073741904, 80) is True
    manager.advance_control_state(FIXED_DT)

    assert manager._input_state.left_pressed is False


def test_keyboard_press_right_sets_right_pressed_state():
    runtime = _RuntimeStub()
    manager = GameControlManager(runtime)

    assert _keyboard_key_down(manager._keyboard, 1073741903, 79) is True
    manager.advance_control_state(FIXED_DT)

    assert manager._input_state.right_pressed is True


def test_keyboard_adapter_desktop_keyboard_object_drives_shared_input_pipeline(monkeypatch):
    runtime = _RuntimeStub()
    manager = GameControlManager(runtime)
    widget = _WidgetStub()

    class _FakeKeyboard:
        def __init__(self) -> None:
            self.closed = False
            self._callbacks = {}
            self.released = False

        def bind(self, **kwargs) -> None:
            self._callbacks.update(kwargs)

        def unbind(self, **kwargs) -> None:
            for name, callback in kwargs.items():
                if self._callbacks.get(name) is callback:
                    self._callbacks.pop(name, None)

        def release(self) -> None:
            self.released = True
            self.closed = True

        def keycode_to_string(self, key: int) -> str | None:
            return {
                1073741903: 'right',
                1073741904: 'left',
            }.get(int(key))

    class _FakeWindow:
        def __init__(self, keyboard) -> None:
            self.keyboard = keyboard
            self.keyboard_focused = None

        def request_keyboard(self, _closed_cb, _widget):
            return self.keyboard

        @staticmethod
        def bind(**_kwargs) -> None:
            return None

        @staticmethod
        def unbind(**_kwargs) -> None:
            return None

    fake_keyboard = _FakeKeyboard()
    fake_window = _FakeWindow(fake_keyboard)
    monkeypatch.setattr(keyboard_adapter_module, 'Window', fake_window)
    monkeypatch.setattr(keyboard_adapter_module, 'kivy_platform', 'win')

    manager._keyboard.attach(widget)
    fake_keyboard._callbacks['on_key_down'](fake_keyboard, (1073741903, 'right'), '', [])
    manager.advance_control_state(FIXED_DT)

    assert manager._input_state.right_pressed is True

    fake_keyboard._callbacks['on_key_up'](fake_keyboard, (1073741903, 'right'))
    manager.advance_control_state(FIXED_DT)

    assert manager._input_state.right_pressed is False


def test_touch_press_and_release_update_pressed_state():
    runtime = _RuntimeStub()
    manager = GameControlManager(runtime)
    widget = _WidgetStub()

    assert manager._touch._on_touch_down(widget, _touch_event(1, 10)) is True
    manager.advance_control_state(FIXED_DT)
    assert manager._input_state.left_pressed is True

    assert manager._touch._on_touch_up(widget, _touch_event(1, 10)) is True
    manager.advance_control_state(FIXED_DT)
    assert manager._input_state.left_pressed is False
