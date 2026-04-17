from __future__ import annotations

from types import SimpleNamespace

from client.application.ads.ads_types import RewardedResult
from client.gameplay.runtime.gameplay_runtime import GameplayRuntime
from client.gameplay.widgets.gameplay_surface import GameplaySurface
from client.presentation.screens.game.game_view import GameScreenView


def _make_view() -> GameScreenView:
    view = GameScreenView.__new__(GameScreenView)
    view._pending_survive_timed_fail_after_reward = False
    view._pending_survive_timed_fail_reason = "game_over"
    view._session_started = True
    view._level_transition_active = False
    view._level_completed_flag = False
    view._active_level_profile = object()
    view._shell = None
    view._time_manager = SimpleNamespace(resume_game_session=lambda: None)
    return view


def _build_runtime() -> GameplayRuntime:
    surface = GameplaySurface()
    surface.size = (1000, 700)
    runtime = GameplayRuntime(surface)
    runtime._state.mark_started()
    return runtime


def test_survive_timed_game_over_routes_to_reward_offer_instead_of_immediate_fail():
    view = _make_view()
    calls: list[str] = []

    view._is_survive_timed_mode_active = lambda: True
    view._show_hud_after_loss = lambda: calls.append("hud_after_loss")
    view._fail_survive_timed_level_on_game_over = lambda: calls.append("fail_now")

    GameScreenView._on_runtime_game_over(view)

    assert calls == ["hud_after_loss"]
    assert view._pending_survive_timed_fail_after_reward is True


def test_soft_reset_loss_does_not_open_reward_offer():
    view = _make_view()
    reward_offer_calls: list[str] = []
    runtime = _build_runtime()

    view._is_survive_timed_mode_active = lambda: True
    view._show_hud_after_loss = lambda: reward_offer_calls.append("hud_after_loss")
    runtime.on_game_over = lambda: GameScreenView._on_runtime_game_over(view)

    runtime._trigger_loss()

    assert reward_offer_calls == []
    assert view._pending_survive_timed_fail_after_reward is False
    assert runtime._session.get_attempts_left() == 2
    assert runtime._state.state_game_over is False


def test_reward_granted_resumes_same_run_and_clears_pending_fail():
    view = _make_view()
    calls: list[str] = []
    view._pending_survive_timed_fail_after_reward = True
    view._resume_after_reward = lambda: calls.append("resume_after_reward")
    view._finalize_survive_timed_fail_after_reward_denied = lambda: calls.append("finalize_fail")
    view._show_ads_info_popup = lambda *_args, **_kwargs: calls.append("ads_popup")

    GameScreenView._apply_rewarded_result(
        view,
        RewardedResult(
            reward_granted=True,
            placement="rewarded_gameover",
            provider="test_provider",
        ),
    )

    assert calls == ["resume_after_reward"]
    assert view._pending_survive_timed_fail_after_reward is False


def test_reward_denied_finalizes_survive_timed_fail():
    view = _make_view()
    calls: list[object] = []
    view._pending_survive_timed_fail_after_reward = True
    view._resume_after_reward = lambda: calls.append("resume_after_reward")
    view._finalize_survive_timed_fail_after_reward_denied = lambda: calls.append("finalize_fail")

    def _show_ads_info_popup(message: str, on_dismiss=None) -> None:
        calls.append(("ads_popup", message))
        if callable(on_dismiss):
            on_dismiss()

    view._show_ads_info_popup = _show_ads_info_popup

    GameScreenView._apply_rewarded_result(
        view,
        RewardedResult(
            reward_granted=False,
            placement="rewarded_gameover",
            provider="test_provider",
            message="reward denied",
        ),
    )

    assert calls == [("ads_popup", "reward denied"), "finalize_fail"]
    assert view._pending_survive_timed_fail_after_reward is False


def test_non_survive_timed_branch_keeps_legacy_rewarded_flow():
    view = _make_view()
    calls: list[str] = []

    view._is_survive_timed_mode_active = lambda: False
    view._show_hud_after_loss = lambda: calls.append("hud_after_loss")
    view._show_survive_timed_reward_offer_after_game_over = lambda: calls.append("survive_offer")

    GameScreenView._on_runtime_game_over(view)

    assert calls == ["hud_after_loss"]
    assert view._pending_survive_timed_fail_after_reward is False
