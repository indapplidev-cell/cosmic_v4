"""EN: Layout application for the profile screen.
RU: Применение раскладки для экрана профиля.
"""

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp

from uix.screens.common.bottom_bar_buttons import apply_bottom_buttons
from uix.screens.layouts.layout_constants import BTN_H, ZONE_SPACING


def apply_profile_layout(view) -> None:
    """EN: Apply responsive layout rules to the profile view.
    RU: Применить адаптивные правила раскладки к виду профиля.
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
        ids.topbar.size_hint_y = None
        ids.topbar.size_hint_x = 1
        ids.topbar.height = inner_h * 0.10
        ids.topbar.size = (ids.main_layout.width - pad * 2, ids.topbar.height)

        ids.contentbar.size_hint_y = None
        ids.contentbar.size_hint_x = 1
        ids.contentbar.height = inner_h * 0.50

        ids.bottombar.size_hint_y = None
        ids.bottombar.size_hint_x = 1
        ids.bottombar.height = inner_h * 0.40

        ids.lefttopbar.size_hint = (None, 1)
        ids.lefttopbar.width = ids.topbar.width * 0.20

        ids.midltopbar.size_hint = (None, 1)
        ids.midltopbar.width = ids.topbar.width * 0.60

        ids.righttopbar.size_hint = (None, 1)
        ids.righttopbar.width = ids.topbar.width * 0.20

        ids.content_center.anchor_x = "center"
        ids.content_center.anchor_y = "center"
        ids.content_center.size_hint = (1, 1)

        ids.profile_card.size_hint = (1, 1)
        ids.profile_card.size = ids.content_center.size
        if "profile_left_col" in ids:
            ids.profile_left_col.size_hint_y = 1
        if "profile_right_col" in ids:
            ids.profile_right_col.size_hint_y = 1

        ids.bottom_center.anchor_x = "center"
        ids.bottom_center.anchor_y = "center"
        ids.bottom_center.size_hint = (1, 1)

        apply_bottom_buttons(
            bottombar=ids.bottombar,
            bottom_center=ids.bottom_center,
            btn_stack=ids.btn_stack,
            buttons=[ids.payout_btn, ids.login_btn, ids.back_btn],
            btn_h_dp=dp(BTN_H),
            spacing_dp=dp(ZONE_SPACING),
            width_ratio=0.5,
        )
        ids.payout_btn.style = "elevated"
        ids.login_btn.style = "outlined"
        ids.back_btn.style = "outlined"

    if not getattr(view, "_layout_bound", False):
        Window.bind(size=_recalc)
        view._layout_bound = True
    Clock.schedule_once(_recalc, 0)


PROFILE_DEBUG_IDS = [
    "main_layout",
    "topbar",
    "lefttopbar",
    "midltopbar",
    "righttopbar",
    "contentbar",
    "content_center",
    "bottombar",
    "bottom_center",
    "btn_stack",
    "payout_btn",
    "login_btn",
    "back_btn",
    "profile_card",
    "profile_left_col",
    "profile_right_col",
    "card_record",
    "card_rating",
    "card_balance",
    "card_login",
    "card_phone",
    "card_tg",
]
