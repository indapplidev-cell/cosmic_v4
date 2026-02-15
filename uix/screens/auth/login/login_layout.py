"""EN: Login screen layout wrapper.
RU: Обертка раскладки экрана входа.
"""

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp

from uix.screens.common.bottom_bar_buttons import apply_bottom_buttons
from uix.screens.layouts.layout_constants import (
    BTN_H,
    FIELD_H,
    TITLE_FALLBACK_SIZE,
    TITLE_STYLE,
    ZONE_PADDING,
    ZONE_SPACING,
)


def apply_login_layout(view) -> None:
    """EN: Apply responsive layout rules to the login view.
    RU: Применить адаптивные правила раскладки к виду входа.
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

        ids.bottom_center.anchor_x = "center"
        ids.bottom_center.anchor_y = "center"
        ids.bottom_center.size_hint = (1, 1)

        ids.card.size_hint = (1, 1)
        if hasattr(ids.card, "adaptive_height"):
            ids.card.adaptive_height = False
        if hasattr(ids.card, "adaptive_width"):
            ids.card.adaptive_width = False

        ids.content_stack.size_hint = (1, 1)
        ids.content_stack.padding = (
            dp(ZONE_PADDING),
            dp(ZONE_PADDING),
            dp(ZONE_PADDING),
            dp(ZONE_PADDING),
        )
        ids.content_stack.spacing = dp(ZONE_SPACING)

        styles = getattr(view.theme_cls, "font_styles", {})
        if TITLE_STYLE in styles:
            ids.title_lbl.font_style = TITLE_STYLE
        else:
            ids.title_lbl.font_size = dp(TITLE_FALLBACK_SIZE)
        ids.title_lbl.halign = "center"
        ids.title_lbl.adaptive_height = True

        for field_id in (ids.email_field, ids.password_field):
            field_id.size_hint_x = 1
            field_id.size_hint_y = None
            field_id.height = dp(FIELD_H)
            field_id.mode = "outlined"

        ids.error_lbl.theme_text_color = "Error"
        ids.error_lbl.halign = "left"
        ids.error_lbl.adaptive_height = True
        ids.error_lbl.opacity = 0

        apply_bottom_buttons(
            bottombar=ids.bottombar,
            bottom_center=ids.bottom_center,
            btn_stack=ids.btn_stack,
            buttons=[ids.login_btn, ids.register_btn, ids.forgot_btn],
            btn_h_dp=dp(BTN_H),
            spacing_dp=dp(ZONE_SPACING),
            width_ratio=0.5,
        )
        ids.login_btn.style = "elevated"
        ids.register_btn.style = "outlined"
        ids.forgot_btn.style = "text"

    if not getattr(view, "_layout_bound", False):
        Window.bind(size=_recalc)
        view._layout_bound = True
    Clock.schedule_once(_recalc, 0)


LOGIN_DEBUG_IDS = [
    "main_layout",
    "topbar",
    "lefttopbar",
    "midltopbar",
    "righttopbar",
    "contentbar",
    "content_center",
    "card",
    "bottombar",
    "bottom_center",
    "btn_stack",
    "email_field",
    "password_field",
    "login_btn",
    "register_btn",
    "forgot_btn",
]
