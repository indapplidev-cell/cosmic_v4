"""EN: Layout application for the game screen.
RU: Применение раскладки для экрана игры.
"""

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from client.presentation.widgets.hud_layout_store import get_swapped

from client.presentation.common.bottom_bar_buttons import apply_bottom_buttons
from client.presentation.layouts.layout_constants import (
    TITLE_FALLBACK_SIZE,
    TITLE_STYLE,
    ZONE_SPACING,
)


def set_hud_visible(view, *, top: bool, content: bool, bottom: bool) -> None:
    """EN: Toggle HUD visibility for bars and collapse hidden bars so they stop taking layout space.
    RU: Переключить видимость HUD-баров и схлопнуть скрытые бары, чтобы они перестали занимать место в раскладке.
    """
    shell = getattr(view, "_shell", None)
    if shell is not None:
        shell.set_bar_visibility(top=top, content=content, bottom=bottom)

    ids = view.ids
    for bar_name, visible in (
        ("topbar", top),
        ("contentbar", content),
        ("bottombar", bottom),
    ):
        bar = ids.get(bar_name)
        if bar is None:
            continue
        bar.opacity = 1 if visible else 0
        bar.disabled = not visible


def apply_game_layout(view) -> None:
    """EN: Apply responsive layout rules to the game view and keep the gameplay area
    constrained to the shell space below the persistent top bar.
    RU: Применить адаптивные правила раскладки к экрану игры и удерживать игровую
    область в пределах shell-пространства ниже постоянного верхнего бара.
    """

    def _recalc(*_args) -> None:
        ids = view.ids
        win_w, win_h = Window.size
        pad = win_h * 0.05
        shell = getattr(view, "_shell", None)
        shell_topbar = getattr(getattr(shell, "ids", {}), "get", lambda *_args, **_kwargs: None)("topbar")
        top_inset = float(getattr(shell_topbar, "height", 0) or 0)
        gameplay_h = max(win_h - top_inset, 0)

        ids.main_layout.orientation = "vertical"
        ids.main_layout.size_hint = (1, 1)
        ids.main_layout.size = (win_w, win_h)
        ids.main_layout.padding = (pad, pad, pad, pad)
        ids.main_layout.spacing = 0

        ids.gameplay_layout.size_hint = (None, None)
        ids.gameplay_layout.pos = (0, 0)
        ids.gameplay_layout.size = (win_w, gameplay_h)
        if "game_bg_gif" in ids:
            ids.game_bg_gif.size_hint = (None, None)
            ids.game_bg_gif.size = ids.gameplay_layout.size
            ids.game_bg_gif.pos = ids.gameplay_layout.pos
            ids.game_bg_gif.opacity = 1
        if "touch_controls_layer" in ids:
            layer = ids.touch_controls_layer
            visible = (not layer.disabled) and (layer.opacity > 0)

            def _hide_btn(btn) -> None:
                btn.size_hint = (None, None)
                btn.size = (0, 0)
                btn.opacity = 0
                btn.disabled = True

            if not visible:
                layer.size_hint = (None, None)
                layer.size = (0, 0)
                layer.opacity = 0
                layer.disabled = True
                ids.steering_icon.size = (0, 0)
                ids.steering_icon.opacity = 0
                _hide_btn(ids.btn_left)
                _hide_btn(ids.btn_right)
                _hide_btn(ids.btn_brake_left)
                _hide_btn(ids.btn_brake_right)
            else:
                layer.size_hint = (None, None)
                layer.pos = (0, 0)
                layer.size = ids.gameplay_layout.size

                btn_w = max(win_w * 0.18, dp(140))
                btn_h = max(win_h * 0.08, dp(70))
                brake_btn_size = max(btn_h * 1.6, dp(120))
                steering_icon_size = brake_btn_size * 1.5
                gap = max(win_h * 0.02, dp(14))
                side = max(win_w * 0.05, dp(24))
                bottom = max(win_h * 0.10, dp(40))
                swapped = get_swapped()

                def _show_btn(btn, pos) -> None:
                    btn.size_hint = (None, None)
                    btn.size = (btn_w, btn_h)
                    btn.pos = pos
                    btn.opacity = 1
                    btn.disabled = False

                def _show_brake_btn(btn, pos) -> None:
                    btn.size_hint = (None, None)
                    btn.size = (brake_btn_size, brake_btn_size)
                    btn.pos = pos
                    btn.opacity = 1
                    btn.disabled = False

                def _show_icon_btn(btn, pos) -> None:
                    btn.size_hint = (None, None)
                    btn.size = (brake_btn_size, brake_btn_size)
                    btn.pos = pos
                    btn.opacity = 1
                    btn.disabled = False

                def _show_steering_icon(x: float) -> None:
                    ids.steering_icon.size_hint = (None, None)
                    ids.steering_icon.size = (steering_icon_size, steering_icon_size)
                    ids.steering_icon.pos = (x, bottom - (steering_icon_size - brake_btn_size) / 2)
                    ids.steering_icon.opacity = 1

                if not swapped:
                    _show_brake_btn(ids.btn_brake_left, (side, bottom))
                    _hide_btn(ids.btn_brake_right)
                    group_width = brake_btn_size * 2 + steering_icon_size + gap * 2
                    left_x = win_w - side - group_width
                    steering_x = left_x + brake_btn_size + gap
                    right_x = steering_x + steering_icon_size + gap
                    _show_icon_btn(ids.btn_left, (left_x, bottom))
                    _show_steering_icon(steering_x)
                    _show_icon_btn(ids.btn_right, (right_x, bottom))
                else:
                    _hide_btn(ids.btn_brake_left)
                    _show_brake_btn(ids.btn_brake_right, (win_w - side - brake_btn_size, bottom))
                    left_x = side
                    steering_x = left_x + brake_btn_size + gap
                    right_x = steering_x + steering_icon_size + gap
                    _show_icon_btn(ids.btn_left, (left_x, bottom))
                    _show_steering_icon(steering_x)
                    _show_icon_btn(ids.btn_right, (right_x, bottom))

        ids.content_center.anchor_x = "center"
        ids.content_center.anchor_y = "top"
        ids.content_center.size_hint = (1, 1)

        styles = getattr(view.theme_cls, "font_styles", {})
        if TITLE_STYLE in styles:
            ids.title_lbl.font_style = TITLE_STYLE
        else:
            ids.title_lbl.font_size = dp(TITLE_FALLBACK_SIZE)
        ids.title_lbl.halign = "center"
        ids.title_lbl.adaptive_height = True

        ids.bottom_center.anchor_x = "center"
        ids.bottom_center.anchor_y = "center"
        ids.bottom_center.size_hint = (1, 1)

        apply_bottom_buttons(
            bottombar=ids.bottombar,
            bottom_center=ids.bottom_center,
            btn_stack=ids.btn_stack,
            buttons=[ids.game_btn, ids.back_btn],
            spacing_dp=dp(ZONE_SPACING),
            width_ratio=0.5,
            height_ratio=0.5,
        )
        ids.game_btn.style = "filled"
        ids.back_btn.style = "outlined"

    if not getattr(view, "_layout_bound", False):
        Window.bind(size=_recalc)
        view._layout_bound = True
    Clock.schedule_once(_recalc, 0)


GAME_DEBUG_IDS = [
    "main_layout",
    "gameplay_layout",
    "touch_controls_layer",
    "topbar",
    "lefttopbar",
    "midltopbar",
    "righttopbar",
    "contentbar",
    "content_center",
    "bottombar",
    "bottom_center",
    "btn_stack",
    "btn_left",
    "btn_right",
    "btn_brake_left",
    "btn_brake_right",
    "title_lbl",
    "game_root",
]
