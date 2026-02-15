"""EN: Layout application for the settings screen.
RU: Применение раскладки для экрана настроек.
"""

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp

from uix.screens.common.bottom_bar_buttons import apply_bottom_buttons
from uix.screens.layouts.layout_constants import BTN_H, ZONE_SPACING


def apply_settings_layout(view) -> None:
    """EN: Apply responsive layout rules to the settings view.
    RU: Применить адаптивные правила раскладки к виду настроек.
    """

    def _recalc(*_args) -> None:
        ids = view.ids
        win_w, win_h = Window.size
        pad = win_h * 0.05

        ids.main_layout.orientation = "vertical"
        ids.main_layout.size_hint = (1, 1)
        ids.main_layout.size = (win_w, win_h)
        ids.main_layout.padding = (pad, pad, pad, pad)
        ids.main_layout.spacing = 0

        inner_h = max(win_h - pad * 2, 0)

        ids.topbar.orientation = "horizontal"
        if hasattr(ids.topbar, "adaptive_height"):
            ids.topbar.adaptive_height = False
        ids.topbar.size_hint_y = None
        ids.topbar.size_hint_x = 1
        ids.topbar.height = inner_h * 0.10
        ids.topbar.size = (ids.main_layout.width - pad * 2, ids.topbar.height)

        if hasattr(ids.contentbar, "adaptive_height"):
            ids.contentbar.adaptive_height = False
        ids.contentbar.size_hint_y = None
        ids.contentbar.size_hint_x = 1
        ids.contentbar.height = inner_h * 0.50
        ids.contentbar.size = (ids.main_layout.width - pad * 2, ids.contentbar.height)

        if hasattr(ids.bottombar, "adaptive_height"):
            ids.bottombar.adaptive_height = False
        ids.bottombar.size_hint_y = None
        ids.bottombar.size_hint_x = 1
        ids.bottombar.height = inner_h * 0.40
        ids.bottombar.size = (ids.main_layout.width - pad * 2, ids.bottombar.height)

        ids.lefttopbar.size_hint = (None, 1)
        ids.lefttopbar.width = ids.topbar.width * 0.20

        ids.midltopbar.size_hint = (None, 1)
        ids.midltopbar.width = ids.topbar.width * 0.60

        ids.righttopbar.size_hint = (None, 1)
        ids.righttopbar.width = ids.topbar.width * 0.20

        ids.content_center.anchor_x = "center"
        ids.content_center.anchor_y = "center"
        ids.content_center.size_hint = (1, 1)
        if "settings_card" in ids:
            ids.settings_card.size_hint = (1, 1)

        ids.bottom_center.anchor_x = "center"
        ids.bottom_center.anchor_y = "center"
        ids.bottom_center.size_hint = (1, 1)

        apply_bottom_buttons(
            bottombar=ids.bottombar,
            bottom_center=ids.bottom_center,
            btn_stack=ids.btn_stack,
            buttons=[ids.login_btn, ids.action_btn, ids.back_btn],
            btn_h_dp=dp(BTN_H),
            spacing_dp=dp(ZONE_SPACING),
            width_ratio=0.5,
        )
        ids.login_btn.style = "outlined"
        ids.action_btn.style = "outlined"
        ids.back_btn.style = "outlined"

    if not getattr(view, "_layout_bound", False):
        Window.bind(size=_recalc)
        view._layout_bound = True
    Clock.schedule_once(_recalc, 0)


SETTINGS_DEBUG_IDS = [
    "main_layout",
    "topbar",
    "lefttopbar",
    "midltopbar",
    "righttopbar",
    "contentbar",
    "content_center",
    "settings_card",
    "settings_left_col",
    "settings_right_col",
    "card_rules",
    "card_policy",
    "card_about",
    "card_spacer_1",
    "card_spacer_2",
    "card_spacer_3",
    "bottombar",
    "bottom_center",
    "btn_stack",
]
