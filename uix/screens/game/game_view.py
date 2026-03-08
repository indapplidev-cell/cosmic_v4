"""EN: View for the game screen.
RU: РџСЂРµРґСЃС‚Р°РІР»РµРЅРёРµ СЌРєСЂР°РЅР° РёРіСЂС‹.
"""

from pathlib import Path
import time
from collections import deque
from time import perf_counter

from kivy.clock import Clock
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.uix.anchorlayout import AnchorLayout
from kivymd.uix.screen import MDScreen

from engine.runtime.gameplay_runtime import GameplayRuntime
from engine.widgets.gameplay_surface import GameplaySurface
from manager.life.attempts_session import GameSessionManager
from manager.life.life_manager import LifeManager
from manager.life.lives_indicator import LivesIndicator
from manager.game_control.game_control_manager import GameControlManager
from manager.game_control.hud_layout_store import get_swapped
from manager.score.score_manager import ScoreManager
from manager.score.score_widget import ScoreLabel
from manager.time.time_manager import TimeManager
from data.gameplay.rating.rating_session import RatingSession
from data.gameplay.rating_storage import RatingStorage
from data.gameplay.record_store import RecordStore
from ads.payment.balance_store import BalanceStore
from manager.gameover.gameover_counters import counters
from manager.lang.lang_manager import t
from manager import auth_backend
from data.user_cache.user_cache_reader import get_user_cache
from data.user_cache.user_cache_writer import update_user_cache_fields
from data.user_cache.user_session import UserSession
from manager.user_snapshot_store import UserSnapshotStore
from uix.debug.debug_borders import apply_debug_borders_to_ids
from uix.screens.common.button_text_style import apply_button_text_style, caps
from ads.rewarded.rewarded_modal import RewardedAdModal

from .game_controller import GameScreenController
from .game_layout import GAME_DEBUG_IDS, apply_game_layout, set_hud_visible
from .game_vm import GameScreenVM

KV_PATH = Path(__file__).with_name("game.kv")
Builder.load_file(str(KV_PATH))
ATTEMPTS_BASE = 3


class GameScreenView(MDScreen):
    """EN: Game screen view that wires layout, VM, and controller.
    RU: РџСЂРµРґСЃС‚Р°РІР»РµРЅРёРµ РёРіСЂС‹, СЃРІСЏР·С‹РІР°СЋС‰РµРµ СЂР°СЃРєР»Р°РґРєСѓ, VM Рё РєРѕРЅС‚СЂРѕР»Р»РµСЂ.
    """

    def __init__(self, **kwargs):
        """EN: Initialize game view state.
        RU: РРЅРёС†РёР°Р»РёР·РёСЂРѕРІР°С‚СЊ СЃРѕСЃС‚РѕСЏРЅРёРµ СЌРєСЂР°РЅР° РёРіСЂС‹.
        """
        super().__init__(**kwargs)
        self._record_store = RecordStore()
        self._balance_store = BalanceStore()
        self._game_over_flag = False
        self._time_manager = TimeManager()
        self._session_started = False
        self._receive_click_start = 0
        self._start_pressed_at = 0.0
        self._sis_started_at = 0.0
        self._chis_segment_started_at = 0.0
        self._chis_accum_sec = 0.0
        self._reward_click_start = 0
        self._reward_used = False
        self._record_sis_max = 0
        self._record_pure_max = 0
        self._attempts_total = ATTEMPTS_BASE
        self._cheat_flag = False
        self._cheat_points_window = deque(maxlen=64)
        self._snapshot_store = UserSnapshotStore()

    def on_kv_post(self, base_widget) -> None:
        """EN: Apply layout after KV is ready.
        RU: РџСЂРёРјРµРЅРёС‚СЊ СЂР°СЃРєР»Р°РґРєСѓ РїРѕСЃР»Рµ Р·Р°РіСЂСѓР·РєРё KV.
        """
        apply_game_layout(self)
        self.apply_hud_layout()
        apply_button_text_style(self, [self.ids.game_btn_text, self.ids.back_btn_text])
        apply_debug_borders_to_ids(self, GAME_DEBUG_IDS)
        self.touch_controls_hide()
        if not getattr(self, "_hud_injected", False):
            self._inject_hud_widgets()
            self._hud_injected = True
        if not hasattr(self, "_gameplay_runtime"):
            host = self.ids.gameplay_layout
            surface = GameplaySurface(size_hint=(1, 1))
            host.add_widget(surface)
            runtime = GameplayRuntime(surface)
            runtime.on_game_over = self._show_hud_after_loss
            runtime.on_loss = self._on_runtime_loss
            Clock.schedule_once(lambda *_: runtime.prepare_scene(), 0)
            surface.bind(size=lambda *_: runtime.request_redraw())
            self._gameplay_surface = surface
            self._gameplay_runtime = runtime
            self._state = runtime._state
            self._runtime_session = runtime._session
            if hasattr(self, "_life"):
                self._life._session = runtime._session
                self._life.sync()
            self._game_control = GameControlManager(runtime)
            self._start_hud_sync()
    def configure(self, vm: GameScreenVM, controller: GameScreenController) -> None:
        """EN: Configure texts and bind callbacks.
        RU: РќР°СЃС‚СЂРѕРёС‚СЊ С‚РµРєСЃС‚С‹ Рё РїСЂРёРІСЏР·Р°С‚СЊ РєРѕР»Р±СЌРєРё.
        """
        self.ids.title_lbl.text = vm.title
        self.ids.game_btn_text.text = caps(vm.game_text)
        self.ids.back_btn_text.text = caps(vm.back_text)
        self.ids.game_btn.on_release = self._on_start_pressed
        self.ids.back_btn.on_release = self._on_back_pressed

    def on_pre_enter(self, *args) -> None:
        """EN: Re-attach controls when entering the screen.
        RU: РџРѕРІС‚РѕСЂРЅРѕ РїРѕРґРєР»СЋС‡РёС‚СЊ СѓРїСЂР°РІР»РµРЅРёРµ РїСЂРё РІС…РѕРґРµ РЅР° СЌРєСЂР°РЅ.
        """
        self._reset_to_first_start_state()
        self._rating_session = RatingSession()
        apply_game_layout(self)
        self.apply_hud_layout()
        self.touch_controls_hide()
        if hasattr(self, "_game_control") and hasattr(self, "_gameplay_surface"):
            self._game_control.attach(self._gameplay_surface)

    def on_pre_leave(self, *args) -> None:
        """EN: Stop gameplay runtime before leaving the screen.
        RU: РћСЃС‚Р°РЅРѕРІРёС‚СЊ РёРіСЂРѕРІРѕР№ runtime РїРµСЂРµРґ СѓС…РѕРґРѕРј СЃ СЌРєСЂР°РЅР°.
        """
        if hasattr(self, "_gameplay_runtime"):
            self._gameplay_runtime.stop()
        self._stop_hud_sync()
        if hasattr(self, "_game_control") and hasattr(self, "_gameplay_surface"):
            self._game_control.detach(self._gameplay_surface)

    def _inject_hud_widgets(self) -> None:
        """EN: Inject score and lives widgets into the top bar.
        RU: 124142303238424c 3238343635424b 4147514230 38 3638373d3539 32 323540453d4e4e 3f303d353b4c.
        """
        self._score_label = ScoreLabel()
        self._score_label.size_hint = (None, None)
        if hasattr(self._score_label, "adaptive_size"):
            self._score_label.adaptive_size = True
        left_host = AnchorLayout(anchor_x="center", anchor_y="center", padding=(0, 0, 0, 0))
        left_host.add_widget(self._score_label)
        self.ids.lefttopbar.add_widget(left_host)
        self._score = ScoreManager(self._score_label)

        self._lives_indicator = LivesIndicator()
        self._lives_indicator.size_hint = (None, None)
        if hasattr(self._lives_indicator, "adaptive_size"):
            self._lives_indicator.adaptive_size = True
        right_host = AnchorLayout(anchor_x="center", anchor_y="center", padding=(0, 0, 0, 0))
        right_host.add_widget(self._lives_indicator)
        self.ids.righttopbar.add_widget(right_host)

        session = getattr(self, "_runtime_session", None)
        if session is None:
            session = GameSessionManager(max_attempts=3)
        self._life = LifeManager(session, self._lives_indicator)
        self._life.sync()

    def on_screen_control(self, action: str, pressed: bool) -> None:
        """EN: Dispatch on-screen control events to game control manager.
        RU: РџРµСЂРµРґР°С‚СЊ СЃРѕР±С‹С‚РёСЏ СЌРєСЂР°РЅРЅС‹С… РєРЅРѕРїРѕРє РІ РјРµРЅРµРґР¶РµСЂ СѓРїСЂР°РІР»РµРЅРёСЏ РёРіСЂРѕР№.
        """
        if not hasattr(self, "_game_control"):
            return
        self._game_control.hud_event(action, pressed)

    def is_hud_swapped(self) -> bool:
        """EN: Return whether the touch HUD layout is swapped.
        RU: Р’РµСЂРЅСѓС‚СЊ РїСЂРёР·РЅР°Рє РїРµСЂРµСЃС‚Р°РІР»РµРЅРЅРѕР№ С‚Р°С‡-СЂР°СЃРєР»Р°РґРєРё HUD.
        """
        return get_swapped()

    def _hud_action_for_slot(self, slot: str) -> str | None:
        """EN: Map HUD button slot to control action according to current layout.
        RU: РЎРѕРїРѕСЃС‚Р°РІРёС‚СЊ СЃР»РѕС‚ HUD-РєРЅРѕРїРєРё СЃ РґРµР№СЃС‚РІРёРµРј СѓРїСЂР°РІР»РµРЅРёСЏ РїРѕ С‚РµРєСѓС‰РµР№ СЂР°СЃРєР»Р°РґРєРµ.
        """
        if not self.is_hud_swapped():
            mapping = {
                "left_top": None,
                "left_bottom": "brake",
                "right_top": "right",
                "right_bottom": "left",
            }
        else:
            mapping = {
                "left_top": "left",
                "left_bottom": "right",
                "right_top": None,
                "right_bottom": "brake",
            }
        return mapping.get(slot)

    def on_hud_button(self, slot: str, pressed: bool) -> None:
        """EN: Route touch HUD slot press/release into the current control action.
        RU: РњР°СЂС€СЂСѓС‚РёР·РёСЂРѕРІР°С‚СЊ РЅР°Р¶Р°С‚РёРµ/РѕС‚РїСѓСЃРєР°РЅРёРµ СЃР»РѕС‚Р° HUD РІ С‚РµРєСѓС‰РµРµ РґРµР№СЃС‚РІРёРµ СѓРїСЂР°РІР»РµРЅРёСЏ.
        """
        action = self._hud_action_for_slot(slot)
        if action is None:
            return
        self.on_screen_control(action, pressed)

    def apply_hud_layout(self) -> None:
        """EN: Apply touch HUD icons and visibility for the current layout.
        RU: РџСЂРёРјРµРЅРёС‚СЊ РёРєРѕРЅРєРё Рё РІРёРґРёРјРѕСЃС‚СЊ С‚Р°С‡-HUD РґР»СЏ С‚РµРєСѓС‰РµР№ СЂР°СЃРєР»Р°РґРєРё.
        """
        ids = self.ids
        if not ids:
            return

        slot_to_btn = {
            "left_top": ids.get("btn_left"),
            "left_bottom": ids.get("btn_brake_left"),
            "right_top": ids.get("btn_right"),
            "right_bottom": ids.get("btn_brake_right"),
        }
        slot_to_icon = {
            "left_top": ids.get("ico_left_top"),
            "left_bottom": ids.get("ico_left_bottom"),
            "right_top": ids.get("ico_right_top"),
            "right_bottom": ids.get("ico_right_bottom"),
        }
        icon_by_action = {
            "left": "arrow-left",
            "right": "arrow-right",
            "brake": "arrow-down",
        }

        for slot in ("left_top", "left_bottom", "right_top", "right_bottom"):
            btn = slot_to_btn.get(slot)
            ico = slot_to_icon.get(slot)
            action = self._hud_action_for_slot(slot)
            if btn is None:
                continue

            if action is None:
                btn.opacity = 0
                btn.disabled = True
                btn.size_hint = (None, None)
                btn.size = (0, 0)
            else:
                btn.opacity = 1
                btn.disabled = False
                btn.size_hint = (None, None)
                if ico is not None:
                    ico.icon = icon_by_action[action]

    def _touch_controls_set_visible(self, visible: bool) -> None:
        """EN: Show/hide touch controls layer.
        RU: РџРѕРєР°Р·Р°С‚СЊ/СЃРєСЂС‹С‚СЊ СЃР»РѕР№ С‚Р°С‡-РєРЅРѕРїРѕРє.
        """
        layer = self.ids.get("touch_controls_layer")
        if not layer:
            return
        layer.opacity = 1 if visible else 0
        layer.disabled = not visible
        if visible:
            layer.size_hint = (1, 1)
            layer.pos = (0, 0)
            if layer.parent is not None:
                layer.size = layer.parent.size
        else:
            layer.size_hint = (None, None)
            layer.size = (0, 0)
        Clock.schedule_once(lambda *_: apply_game_layout(self), 0)

    def touch_controls_show(self) -> None:
        """EN: Show and enable touch controls.
        RU: РџРѕРєР°Р·Р°С‚СЊ Рё РІРєР»СЋС‡РёС‚СЊ С‚Р°С‡-РєРЅРѕРїРєРё.
        """
        self._touch_controls_set_visible(True)

    def touch_controls_hide(self) -> None:
        """EN: Hide and disable touch controls.
        RU: РЎРєСЂС‹С‚СЊ Рё РѕС‚РєР»СЋС‡РёС‚СЊ С‚Р°С‡-РєРЅРѕРїРєРё.
        """
        self._touch_controls_set_visible(False)

    def _start_hud_sync(self) -> None:
        """EN: Start periodic HUD synchronization.
        RU: 17303f43414238424c 3f3540383e34384735413a434e 41383d45403e3d38373046384e HUD.
        """
        if getattr(self, "_hud_ev", None):
            return
        self._last_score = None
        self._hud_ev = Clock.schedule_interval(self._sync_hud, 0)

    def _stop_hud_sync(self) -> None:
        """EN: Stop periodic HUD synchronization.
        RU: 1e4142303d3e3238424c 3f3540383e34384735413a434e 41383d45403e3d38373046384e HUD.
        """
        ev = getattr(self, "_hud_ev", None)
        if ev:
            ev.cancel()
        self._hud_ev = None

    def _sync_hud(self, _dt) -> None:
        """EN: Sync score and lives from the current runtime state.
        RU: 21383d45403e3d383738403e3230424c 41475142 38 3638373d38 3837 42353a434935333e 413e41423e4f3d384f runtime.
        """
        state = getattr(self, "_state", None)
        if state:
            score = int(getattr(state, "current_y_loop", 0))
            if score != self._last_score:
                self._score.set_score(score)
                if hasattr(self, "_rating_session"):
                    self._rating_session.on_score_changed(score)
                self._record_sis_max = max(int(self._record_sis_max), int(score))
                if not self._reward_used:
                    self._record_pure_max = max(int(self._record_pure_max), int(score))
                self._register_score_point_and_check_fast_cheat(int(score))
                self._last_score = score
        if hasattr(self, "_life"):
            self._life.sync()

    def _register_score_point_and_check_fast_cheat(self, score: int) -> None:
        """EN: Push (time, score) point into rolling window and detect fast-cheat by 20-score jumps.
        RU: Р”РѕР±Р°РІРёС‚СЊ С‚РѕС‡РєСѓ (time, score) РІ rolling-РѕРєРЅРѕ Рё РїСЂРѕРІРµСЂРёС‚СЊ Р±С‹СЃС‚СЂС‹Р№ С‡РёС‚ РїРѕ РїСЂС‹Р¶РєР°Рј РЅР° 20 РѕС‡РєРѕРІ.
        """

        now = perf_counter()
        self._cheat_points_window.append((now, int(score)))

        points = list(self._cheat_points_window)
        for old_t, old_score in points:
            delta_score = int(score) - int(old_score)
            if delta_score >= 20:
                delta_t = max(now - float(old_t), 1e-9)
                if (float(delta_score) / delta_t) > 0:
                    self._cheat_flag = True
                    return

    def _close_chis_segment(self) -> None:
        """EN: Close current CHIS segment and accumulate elapsed seconds.
        RU: Р—Р°РєСЂС‹С‚СЊ С‚РµРєСѓС‰РёР№ СЃРµРіРјРµРЅС‚ Р§РРЎ Рё РЅР°РєРѕРїРёС‚СЊ РїСЂРѕС€РµРґС€РёРµ СЃРµРєСѓРЅРґС‹.
        """

        if self._chis_segment_started_at > 0:
            self._chis_accum_sec += max(0.0, perf_counter() - float(self._chis_segment_started_at))
            self._chis_segment_started_at = 0.0

    def _open_chis_segment(self) -> None:
        """EN: Start a new CHIS timing segment from current monotonic time.
        RU: Р—Р°РїСѓСЃС‚РёС‚СЊ РЅРѕРІС‹Р№ СЃРµРіРјРµРЅС‚ С‚Р°Р№РјРµСЂР° Р§РРЎ РѕС‚ С‚РµРєСѓС‰РµРіРѕ РјРѕРЅРѕС‚РѕРЅРЅРѕРіРѕ РІСЂРµРјРµРЅРё.
        """

        self._chis_segment_started_at = perf_counter()

    def _finalize_chis_sec(self) -> float:
        """EN: Finalize CHIS duration (accumulated + open segment tail) in seconds.
        RU: Р¤РёРЅР°Р»РёР·РёСЂРѕРІР°С‚СЊ РґР»РёС‚РµР»СЊРЅРѕСЃС‚СЊ Р§РРЎ (РЅР°РєРѕРїР»РµРЅРёРµ + С…РІРѕСЃС‚ РѕС‚РєСЂС‹С‚РѕРіРѕ СЃРµРіРјРµРЅС‚Р°) РІ СЃРµРєСѓРЅРґР°С….
        """

        self._close_chis_segment()
        return float(max(0.0, self._chis_accum_sec))

    def _reward_click_delta(self) -> int:
        """EN: Return reward-click delta within current SIS.
        RU: Р’РµСЂРЅСѓС‚СЊ РґРµР»СЊС‚Сѓ РєР»РёРєРѕРІ reward РІ СЂР°РјРєР°С… С‚РµРєСѓС‰РµР№ РЎРРЎ.
        """

        delta = int(counters.receive_click_count) - int(self._reward_click_start)
        return max(0, int(delta))

    def _apply_cheat_reset_and_exit(self) -> None:
        """EN: On cheat, zero local/server profile_game and immediately return to start screen.
        RU: РџСЂРё С‡РёС‚Рµ РѕР±РЅСѓР»РёС‚СЊ Р»РѕРєР°Р»СЊРЅРѕ/РЅР° СЃРµСЂРІРµСЂРµ profile_game Рё РЅРµРјРµРґР»РµРЅРЅРѕ РІРµСЂРЅСѓС‚СЊ РЅР° СЃС‚Р°СЂС‚РѕРІС‹Р№ СЌРєСЂР°РЅ.
        """

        self._record_store.set_best_score(0)
        RatingStorage().save_points(0)
        self._balance_store.set_balance(0.0)
        self._snapshot_store.patch_game(record=0, rating=0, balance=0.0)
        self._cheat_flag = True
        self._session_started = False
        if hasattr(self, "_gameplay_runtime"):
            self._gameplay_runtime.stop()
        if hasattr(self, "_game_control") and hasattr(self, "_gameplay_surface"):
            self._game_control.detach(self._gameplay_surface)
        if hasattr(self, "_stop_hud_sync"):
            self._stop_hud_sync()
        self._reset_to_first_start_state()
        if self.manager:
            self.manager.back()

    def _on_runtime_loss(self) -> None:
        """EN: Update lives when the runtime registers a loss.
        RU: 1e313d3e3238424c 3638373d38 3f4038 4035333841424030463838 3f3e42354038 32 runtime.
        """
        self._time_manager.time_gameplay(stop=True)
        if hasattr(self, "_rating_session"):
            self._rating_session.on_life_lost()
        if not hasattr(self, "_life"):
            return
        if getattr(self, "_runtime_session", None) is getattr(self._life, "_session", None):
            self._life.sync()
        else:
            self._life.register_loss()

    def _hide_hud_for_play(self) -> None:
        """EN: Hide content and bottom bars while keeping the top bar visible.
        RU: РЎРєСЂС‹С‚СЊ content Рё bottom Р±Р°СЂ, РѕСЃС‚Р°РІРёРІ top bar РІРёРґРёРјС‹Рј.
        """
        set_hud_visible(self, top=True, content=False, bottom=False)
        self._game_over_flag = False

    def _show_hud_after_loss(self) -> None:
        """EN: Show all HUD bars after a loss.
        RU: РџРѕРєР°Р·Р°С‚СЊ РІСЃРµ HUD-Р±Р°СЂС‹ РїРѕСЃР»Рµ РїСЂРѕРёРіСЂС‹С€Р°.
        """
        counters.inc_gameover()
        if hasattr(self, "_rating_session"):
            self._rating_session.on_game_over(time.time())
        now_ts = time.time()
        current_score = int(getattr(getattr(self, "_state", None), "current_y_loop", 0))
        elapsed_sec = 0.0
        if self._start_pressed_at > 0:
            elapsed_sec = max(0.0, now_ts - float(self._start_pressed_at))
        print(
            f"[GameOver] score={current_score} elapsed_from_start_sec={elapsed_sec:.2f}",
            flush=True,
        )
        if hasattr(self, "_game_control"):
            self._game_control.hud_reset()
        self.touch_controls_hide()
        set_hud_visible(self, top=True, content=True, bottom=True)
        self.ids.title_lbl.text = t("game.reward_prompt")
        self.ids.game_btn_text.text = caps(t("game.btn_receive"))
        self.ids.game_btn.on_release = self.receive_reward
        self._game_over_flag = True

    def receive_reward(self) -> None:
        """EN: Open rewarded modal and continue after close.
        RU: РћС‚РєСЂС‹С‚СЊ rewarded-РјРѕРґР°Р»РєСѓ Рё РїСЂРѕРґРѕР»Р¶РёС‚СЊ РёРіСЂСѓ РїРѕСЃР»Рµ Р·Р°РєСЂС‹С‚РёСЏ.
        """
        counters.inc_receive_click()
        self._close_chis_segment()
        modal = RewardedAdModal(on_close=self._resume_after_reward)
        self._rewarded_modal = modal
        modal.open()

    def _resume_after_reward(self) -> None:
        """EN: Resume game after rewarded modal closes.
        RU: РџСЂРѕРґРѕР»Р¶РёС‚СЊ РёРіСЂСѓ РїРѕСЃР»Рµ Р·Р°РєСЂС‹С‚РёСЏ rewarded-РјРѕРґР°Р»РєРё.
        """
        if hasattr(self, "_life"):
            self._life.reset_to_full()
        self._hide_hud_for_play()
        self.touch_controls_show()
        if hasattr(self, "_gameplay_runtime"):
            self._gameplay_runtime.receive_reward()
        self._time_manager.time_gameplay(reset=True)
        self._time_manager.time_gameplay(start=True)
        self._reward_used = True
        self._open_chis_segment()

    def _reset_to_first_start_state(self) -> None:
        """
        Р’РµСЂРЅСѓС‚СЊ СЌРєСЂР°РЅ РРіСЂР° РІ СЃРѕСЃС‚РѕСЏРЅРёРµ РєР°Рє РїСЂРё РїРµСЂРІРѕРј Р·Р°РїСѓСЃРєРµ РїСЂРёР»РѕР¶РµРЅРёСЏ:
        - РєРЅРѕРїРєР° РЎС‚Р°СЂС‚
        - С‚РµРєСЃС‚ Р·Р°РіРѕР»РѕРІРєР° РѕР±С‹С‡РЅС‹Р№
        - РЅРёРєР°РєРѕР№ СЂРµРєР»Р°РјС‹/РѕРІРµСЂР»РµСЏ
        - С‚Р°С‡-РєРЅРѕРїРєРё СЃРєСЂС‹С‚С‹
        - runtime РѕСЃС‚Р°РЅРѕРІР»РµРЅ
        - HUD СЃРёРЅС…СЂРѕРЅРёР·Р°С†РёСЏ РѕСЃС‚Р°РЅРѕРІР»РµРЅР°
        - РїРѕРґРіРѕС‚РѕРІРёС‚СЊ СЃС†РµРЅСѓ (Р±РµР· Р·Р°РїСѓСЃРєР°)
        """
        reward_modal = getattr(self, "_reward_modal", None)
        if reward_modal is not None and getattr(reward_modal, "parent", None) is not None:
            reward_modal.dismiss()
        rewarded_modal = getattr(self, "_rewarded_modal", None)
        if rewarded_modal is not None and getattr(rewarded_modal, "parent", None) is not None:
            rewarded_modal.dismiss()
        reward_ev = getattr(self, "_reward_ev", None)
        if reward_ev is not None:
            reward_ev.cancel()
        if hasattr(self, "_reward_modal"):
            self._reward_modal = None
        if hasattr(self, "_rewarded_modal"):
            self._rewarded_modal = None
        if hasattr(self, "_reward_ev"):
            self._reward_ev = None

        self.ids.game_btn_text.text = caps(t("game.btn_start"))
        self.ids.game_btn.on_release = self._on_start_pressed
        self.ids.title_lbl.text = t("game.title")

        set_hud_visible(self, top=True, content=True, bottom=True)
        self.touch_controls_hide()

        self._game_over_flag = False
        if hasattr(self, "_reward_mode"):
            self._reward_mode = False

        if hasattr(self, "_gameplay_runtime"):
            self._gameplay_runtime.stop()
        if hasattr(self, "_stop_hud_sync"):
            self._stop_hud_sync()

        self._reset_hud_state()
        if hasattr(self, "_gameplay_runtime"):
            Clock.schedule_once(lambda *_: self._gameplay_runtime.prepare_scene(), 0)
        self._session_started = False
        self._receive_click_start = counters.receive_click_count
        self._reward_click_start = counters.receive_click_count
        self._sis_started_at = 0.0
        self._chis_segment_started_at = 0.0
        self._chis_accum_sec = 0.0
        self._reward_used = False
        self._record_sis_max = 0
        self._record_pure_max = 0
        self._attempts_total = int(ATTEMPTS_BASE)
        self._cheat_flag = False
        self._cheat_points_window.clear()

    def _reset_hud_state(self) -> None:
        """EN: Reset score/lives state for a fresh run.
        RU: РЎР±СЂРѕСЃРёС‚СЊ СЃС‡С‘С‚/Р¶РёР·РЅРё РґР»СЏ РЅРѕРІРѕРіРѕ Р·Р°РїСѓСЃРєР°.
        """
        if hasattr(self, "_score"):
            self._score.reset()
        if hasattr(self, "_life"):
            self._life.reset_to_full()
        self._last_score = None

    def _on_back_pressed(self) -> None:
        """EN: Stop runtime, finalize SIS metrics, and navigate back.
        RU: ?????????? runtime, ?????????????? ??????? ??? ? ????????? ?????.
        """
        if not self._session_started:
            if hasattr(self, "_gameplay_runtime"):
                self._gameplay_runtime.stop()
            if hasattr(self, "_game_control") and hasattr(self, "_gameplay_surface"):
                self._game_control.detach(self._gameplay_surface)
            self.touch_controls_hide()
            self._reset_hud_state()
            if hasattr(self, "_stop_hud_sync"):
                self._stop_hud_sync()
            self._reset_to_first_start_state()
            if self.manager:
                self.manager.back()
            return

        now = time.time()
        if hasattr(self, "_rating_session"):
            self._rating_session.on_exit_back(now)

        sis_sec = float(self._time_manager.time_game_session(stop=True) or 0.0)
        chis_sec = float(self._finalize_chis_sec() or 0.0)
        gameplay_sec = self._time_manager.time_gameplay()
        if gameplay_sec is None:
            gameplay_sec = 0.0

        reward_click_delta = self._reward_click_delta()
        self._attempts_total = int(ATTEMPTS_BASE * (1 + int(reward_click_delta)))

        best_life_score = int(getattr(getattr(self, "_rating_session", None), "best_life_score", 0) or 0)
        best_game_score = int(getattr(getattr(self, "_rating_session", None), "best_game_score", 0) or 0)

        record_sis = int(self._record_sis_max)
        record_pure = int(self._record_pure_max)
        user_id = self._resolve_user_id()
        if user_id is not None:
            finish_payload = {
                "user_id": int(user_id),
                "record_sis": int(record_sis),
                "record_pure": int(record_pure),
                "sis_sec": float(sis_sec),
                "chis_sec": float(chis_sec),
                "attempts": int(self._attempts_total),
                "reward_clicks": int(reward_click_delta),
                "best_life_score": int(best_life_score),
                "best_game_score": int(best_game_score),
                "anti_cheat_windows": self._build_anti_cheat_windows(),
            }
            ok_finish, finish_resp = auth_backend.finish_session_metrics(finish_payload)
            if ok_finish and isinstance(finish_resp, dict) and bool(finish_resp.get("cheat")):
                self._apply_cheat_reset_and_exit()
                return

        print(
            "[SIS] "
            f"sis_sec={sis_sec:.2f} chis_sec={chis_sec:.2f} gameplay_sec={gameplay_sec:.2f} "
            f"record_sis={record_sis} record_pure={record_pure} "
            f"attempts={self._attempts_total} reward_clicks={reward_click_delta} "
            f"finish_sent={'yes' if user_id is not None else 'no'}",
            flush=True,
        )

        self._session_started = False
        if hasattr(self, "_gameplay_runtime"):
            self._gameplay_runtime.stop()
        if hasattr(self, "_game_control") and hasattr(self, "_gameplay_surface"):
            self._game_control.detach(self._gameplay_surface)
        self.touch_controls_hide()
        self._reset_hud_state()
        if hasattr(self, "_stop_hud_sync"):
            self._stop_hud_sync()
        counters.dump_to_print()
        self._reset_to_first_start_state()
        if self.manager:
            self.manager.back()

    def _build_anti_cheat_windows(self) -> list[dict]:
        """EN: Build score/time windows payload for server-side fast anti-cheat checks.
        RU: РЎС„РѕСЂРјРёСЂРѕРІР°С‚СЊ payload РѕРєРѕРЅ score/time РґР»СЏ СЃРµСЂРІРµСЂРЅРѕР№ fast anti-cheat РїСЂРѕРІРµСЂРєРё.
        """

        points = list(self._cheat_points_window)
        windows: list[dict] = []
        for idx, (new_t, new_score) in enumerate(points):
            for old_t, old_score in points[:idx]:
                delta_score = int(new_score) - int(old_score)
                if delta_score < 20:
                    continue
                delta_sec = max(float(new_t) - float(old_t), 1e-9)
                windows.append({"delta_score": int(delta_score), "delta_sec": float(delta_sec)})
                if len(windows) >= 100:
                    return windows
        return windows

    def _resolve_user_id(self) -> int | None:
        """EN: Resolve active user id from cache with email fallback.
        RU: РћРїСЂРµРґРµР»РёС‚СЊ Р°РєС‚РёРІРЅС‹Р№ user_id РёР· РєРµС€Р° СЃ fallback С‡РµСЂРµР· email.
        """
        cache = get_user_cache() or {}
        raw_user_id = cache.get("user_id")
        if isinstance(raw_user_id, int):
            return raw_user_id
        if isinstance(raw_user_id, str) and raw_user_id.isdigit():
            return int(raw_user_id)

        email = (cache.get("email") or "").strip() or (UserSession().get_email() or "").strip()
        if not email:
            return None

        ok, payload = auth_backend.resolve_user_id(email)
        if not ok:
            return None
        user_id = int(payload)
        update_user_cache_fields({"user_id": user_id})
        return user_id

    def _on_start_pressed(self) -> None:
        """EN: Hide HUD and start the gameplay runtime.
        RU: РЎРєСЂС‹С‚СЊ HUD Рё Р·Р°РїСѓСЃС‚РёС‚СЊ РёРіСЂРѕРІРѕР№ runtime.
        """
        start_ts = time.time()
        self._start_pressed_at = start_ts
        self._sis_started_at = perf_counter()
        self._chis_accum_sec = 0.0
        self._open_chis_segment()
        self._reward_used = False
        self._record_sis_max = 0
        self._record_pure_max = 0
        self._attempts_total = int(ATTEMPTS_BASE)
        self._cheat_flag = False
        self._cheat_points_window.clear()
        self._reward_click_start = int(counters.receive_click_count)
        if hasattr(self, "_rating_session"):
            current_score = int(getattr(getattr(self, "_state", None), "current_y_loop", 0))
            self._rating_session.on_press_start(start_ts, current_score)
        self._time_manager.time_game_session(reset=True)
        self._time_manager.time_gameplay(reset=True)
        self._time_manager.time_game_session(start=True)
        self._time_manager.time_gameplay(start=True)
        self._session_started = True
        self._receive_click_start = counters.receive_click_count
        if hasattr(self, "_game_control") and hasattr(self, "_gameplay_surface"):
            self._game_control.attach(self._gameplay_surface)
        self._game_over_flag = False
        self._reset_hud_state()
        if hasattr(self, "_start_hud_sync"):
            self._start_hud_sync()
        self._hide_hud_for_play()
        self.touch_controls_show()
        if hasattr(self, "_gameplay_runtime"):
            self._gameplay_runtime.start()



