"""EN: Password reset screen layout wrapper.
RU: Обертка раскладки экрана восстановления пароля.
"""

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp

from uix.screens.common.bottom_bar_buttons import apply_bottom_buttons
from uix.screens.layouts.layout_constants import (
    FIELD_H,
    TITLE_FALLBACK_SIZE,
    TITLE_STYLE,
    ZONE_PADDING,
    ZONE_SPACING,
)


def apply_password_reset_layout(view) -> None:
    """EN: Apply responsive layout rules to password reset view.
    RU: Применить адаптивные правила раскладки к виду восстановления пароля.
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

        ids.topbar.size_hint_y = None
        ids.topbar.size_hint_x = 1
        ids.topbar.height = inner_h * 0.10

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
        ids.bottom_center.anchor_x = "center"
        ids.bottom_center.anchor_y = "center"

        ids.card.size_hint = (1, 1)

        ids.content_stack.size_hint_x = 1
        ids.content_stack.size_hint_y = None
        ids.content_stack.padding = (
            dp(ZONE_PADDING),
            dp(ZONE_PADDING),
            dp(ZONE_PADDING),
            dp(ZONE_PADDING + 20),
        )
        ids.content_stack.spacing = dp(ZONE_SPACING)

        styles = getattr(view.theme_cls, "font_styles", {})
        if TITLE_STYLE in styles:
            ids.title_lbl.font_style = TITLE_STYLE
        else:
            ids.title_lbl.font_size = dp(TITLE_FALLBACK_SIZE)
        ids.title_lbl.halign = "center"

        for field in (ids.email_field, ids.code_field, ids.new_password_field):
            field.size_hint_x = 1
            field.size_hint_y = None
            field.height = dp(FIELD_H)
            field.mode = "outlined"

        ids.error_lbl.theme_text_color = "Error"
        ids.error_lbl.halign = "left"
        ids.error_lbl.opacity = 0

        apply_bottom_buttons(
            bottombar=ids.bottombar,
            bottom_center=ids.bottom_center,
            btn_stack=ids.btn_stack,
            buttons=[ids.send_btn, ids.confirm_btn, ids.back_btn],
            spacing_dp=dp(ZONE_SPACING),
            width_ratio=0.5,
        )
        ids.send_btn.style = "outlined"
        ids.confirm_btn.style = "elevated"
        ids.back_btn.style = "text"

    if not getattr(view, "_layout_bound", False):
        Window.bind(size=_recalc)
        view._layout_bound = True
    Clock.schedule_once(_recalc, 0)


PASSWORD_RESET_DEBUG_IDS = [
    "main_layout",
    "topbar",
    "contentbar",
    "bottombar",
    "email_field",
    "code_field",
    "new_password_field",
    "send_btn",
    "confirm_btn",
    "back_btn",
]
