"""EN: View for the game screen.
RU: Представление экрана игры.
"""

from pathlib import Path
import time

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
from manager.score.score_manager import ScoreManager
from manager.score.score_widget import ScoreLabel
from manager.time.time_manager import TimeManager
from data.gameplay.rating.rating_math import calculate_rating_points
from data.gameplay.rating.rating_session import RatingSession
from data.gameplay.rating_storage import RatingStorage
from data.gameplay.record_store import RecordStore
from ads.payment.balance_store import BalanceStore
from ads.payment.payment_math import calc_balance
from manager.gameover.gameover_counters import counters
from manager.lang.lang_manager import t
from uix.debug.debug_borders import apply_debug_borders_to_ids
from uix.screens.common.button_text_style import apply_button_text_style, caps
from ads.rewarded.rewarded_modal import RewardedAdModal

from .game_controller import GameScreenController
from .game_layout import GAME_DEBUG_IDS, apply_game_layout, set_hud_visible
from .game_vm import GameScreenVM

KV_PATH = Path(__file__).with_name("game.kv")
Builder.load_file(str(KV_PATH))


class GameScreenView(MDScreen):
    """EN: Game screen view that wires layout, VM, and controller.
    RU: Представление игры, связывающее раскладку, VM и контроллер.
    """

    def __init__(self, **kwargs):
        """EN: Initialize game view state.
        RU: Инициализировать состояние экрана игры.
        """
        super().__init__(**kwargs)
        self._record_store = RecordStore()
        self._balance_store = BalanceStore()
        self._game_over_flag = False
        self._time_manager = TimeManager()
        self._session_started = False
        self._receive_click_start = 0

    def on_kv_post(self, base_widget) -> None:
        """EN: Apply layout after KV is ready.
        RU: Применить раскладку после загрузки KV.
        """
        apply_game_layout(self)
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
            self._game_control.attach(surface)
            self._start_hud_sync()
    def configure(self, vm: GameScreenVM, controller: GameScreenController) -> None:
        """EN: Configure texts and bind callbacks.
        RU: Настроить тексты и привязать колбэки.
        """
        self.ids.title_lbl.text = vm.title
        self.ids.game_btn_text.text = caps(vm.game_text)
        self.ids.back_btn_text.text = caps(vm.back_text)
        self.ids.game_btn.on_release = self._on_start_pressed
        self.ids.back_btn.on_release = self._on_back_pressed

    def on_pre_enter(self, *args) -> None:
        """EN: Re-attach controls when entering the screen.
        RU: Повторно подключить управление при входе на экран.
        """
        self._reset_to_first_start_state()
        self._rating_session = RatingSession()
        self.touch_controls_hide()
        if hasattr(self, "_game_control") and hasattr(self, "_gameplay_surface"):
            self._game_control.attach(self._gameplay_surface)

    def on_pre_leave(self, *args) -> None:
        """EN: Stop gameplay runtime before leaving the screen.
        RU: Остановить игровой runtime перед уходом с экрана.
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
        RU: Передать события экранных кнопок в менеджер управления игрой.
        """
        if not hasattr(self, "_game_control"):
            return
        self._game_control.hud_event(action, pressed)

    def _touch_controls_set_visible(self, visible: bool) -> None:
        """EN: Show/hide touch controls layer.
        RU: Показать/скрыть слой тач-кнопок.
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

    def touch_controls_show(self) -> None:
        """EN: Show and enable touch controls.
        RU: Показать и включить тач-кнопки.
        """
        self._touch_controls_set_visible(True)

    def touch_controls_hide(self) -> None:
        """EN: Hide and disable touch controls.
        RU: Скрыть и отключить тач-кнопки.
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
                self._last_score = score
        if hasattr(self, "_life"):
            self._life.sync()

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
        RU: Скрыть content и bottom бар, оставив top bar видимым.
        """
        set_hud_visible(self, top=True, content=False, bottom=False)
        self._game_over_flag = False

    def _show_hud_after_loss(self) -> None:
        """EN: Show all HUD bars after a loss.
        RU: Показать все HUD-бары после проигрыша.
        """
        counters.inc_gameover()
        if hasattr(self, "_rating_session"):
            self._rating_session.on_game_over(time.time())
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
        RU: Открыть rewarded-модалку и продолжить игру после закрытия.
        """
        counters.inc_receive_click()
        modal = RewardedAdModal(on_close=self._resume_after_reward)
        self._rewarded_modal = modal
        modal.open()

    def _resume_after_reward(self) -> None:
        """EN: Resume game after rewarded modal closes.
        RU: Продолжить игру после закрытия rewarded-модалки.
        """
        if hasattr(self, "_life"):
            self._life.reset_to_full()
        self._hide_hud_for_play()
        self.touch_controls_show()
        if hasattr(self, "_gameplay_runtime"):
            self._gameplay_runtime.receive_reward()
        self._time_manager.time_gameplay(reset=True)
        self._time_manager.time_gameplay(start=True)

    def _reset_to_first_start_state(self) -> None:
        """
        Вернуть экран Игра в состояние как при первом запуске приложения:
        - кнопка Старт
        - текст заголовка обычный
        - никакой рекламы/оверлея
        - тач-кнопки скрыты
        - runtime остановлен
        - HUD синхронизация остановлена
        - подготовить сцену (без запуска)
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

    def _reset_hud_state(self) -> None:
        """EN: Reset score/lives state for a fresh run.
        RU: Сбросить счёт/жизни для нового запуска.
        """
        if hasattr(self, "_score"):
            self._score.reset()
        if hasattr(self, "_life"):
            self._life.reset_to_full()
        self._last_score = None

    def _on_back_pressed(self) -> None:
        """EN: Stop runtime, reset HUD, and navigate back.
        RU: Остановить runtime, сбросить HUD и вернуться назад.
        """
        if hasattr(self, "_rating_session"):
            self._rating_session.on_exit_back(time.time())
            gameplay_sec = self._rating_session.gameplay_duration_sec or None
            rating_points = calculate_rating_points(
                self._rating_session.best_life_score,
                self._rating_session.best_game_score,
                self._rating_session.valid_starts,
                gameplay_sec,
            )
            RatingStorage().save_points(rating_points)
            print(
                "[Rating] "
                f"points={rating_points} "
                f"best_life={self._rating_session.best_life_score} "
                f"best_game={self._rating_session.best_game_score} "
                f"valid_starts={self._rating_session.valid_starts} "
                f"gameplay_sec={self._rating_session.gameplay_duration_sec}",
                flush=True,
            )
        session_sec = self._time_manager.time_game_session(stop=True)
        if self._session_started:
            time_sec = float(session_sec or 0.0)
            receive_click_delta = counters.receive_click_count - int(self._receive_click_start)
            if receive_click_delta < 0:
                receive_click_delta = 0

            delta = calc_balance(time_sec, receive_click_delta)
            self._balance_store.add(delta)

            # чтобы не было двойного начисления при повторном back
            self._session_started = False
        gameplay_sec = self._time_manager.time_gameplay()
        if gameplay_sec is None:
            gameplay_sec = 0.0
        print(
            f"[Time] game_session_sec={session_sec or 0.0:.2f} gameplay_sec={gameplay_sec:.2f}",
            flush=True,
        )
        if self._game_over_flag:
            current_score = int(getattr(getattr(self, "_state", None), "current_y_loop", 0))
            best_score = self._record_store.commit_if_higher(current_score)
            print(f"[Record] best_score={best_score}", flush=True)
            self._game_over_flag = False
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

    def _on_start_pressed(self) -> None:
        """EN: Hide HUD and start the gameplay runtime.
        RU: Скрыть HUD и запустить игровой runtime.
        """
        if hasattr(self, "_rating_session"):
            current_score = int(getattr(getattr(self, "_state", None), "current_y_loop", 0))
            self._rating_session.on_press_start(time.time(), current_score)
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
