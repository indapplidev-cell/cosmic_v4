"""EN: Layout application for the start screen.
RU: Применение раскладки для стартового экрана.
"""

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp

from uix.screens.common.bottom_bar_buttons import apply_bottom_buttons
from uix.screens.layouts.layout_constants import (
    BTN_H,
    TITLE_FALLBACK_SIZE,
    TITLE_STYLE,
    ZONE_SPACING,
)


def apply_start_layout(view) -> None:
    """EN: Apply responsive layout rules to the start view.
    RU: Применить адаптивные правила раскладки к стартовому виду.
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

        ids.topbar.orientation = "horizontal"
        ids.topbar.size_hint_y = None
        ids.topbar.size_hint_x = 1
        inner_h = max(win_h - pad * 2, 0)
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

        styles = getattr(view.theme_cls, "font_styles", {})
        if TITLE_STYLE in styles:
            ids.title_lbl.font_style = TITLE_STYLE
        else:
            ids.title_lbl.font_size = dp(TITLE_FALLBACK_SIZE)
        ids.title_lbl.halign = "center"
        ids.title_lbl.adaptive_height = True

        apply_bottom_buttons(
            bottombar=ids.bottombar,
            bottom_center=ids.bottom_center,
            btn_stack=ids.btn_stack,
            buttons=[ids.game_btn, ids.profile_btn, ids.settings_btn],
            btn_h_dp=dp(BTN_H),
            spacing_dp=dp(ZONE_SPACING),
            width_ratio=0.5,
        )

        ids.game_btn.style = "filled"
        ids.profile_btn.style = "outlined"
        ids.settings_btn.style = "outlined"

    if not getattr(view, "_layout_bound", False):
        Window.bind(size=_recalc)
        view._layout_bound = True
    Clock.schedule_once(_recalc, 0)


START_DEBUG_IDS = [
    "main_layout",
    "topbar",
    "lefttopbar",
    "midltopbar",
    "righttopbar",
    "contentbar",
    "content_center",
    "title_lbl",
    "bottombar",
    "bottom_center",
    "btn_stack",
]
