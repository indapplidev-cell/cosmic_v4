"""EN: Layout application for the game screen.
RU: Применение раскладки для экрана игры.
"""

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from manager.game_control.hud_layout_store import get_swapped

from uix.screens.common.bottom_bar_buttons import apply_bottom_buttons
from uix.screens.layouts.layout_constants import (
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
    """EN: Apply responsive layout rules to the game view.
    RU: Применить адаптивные правила раскладки к виду игры.
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

        ids.gameplay_layout.size_hint = (1, 1)
        ids.gameplay_layout.pos = (0, 0)
        ids.gameplay_layout.size = (win_w, win_h)
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
                _hide_btn(ids.btn_left)
                _hide_btn(ids.btn_right)
                _hide_btn(ids.btn_brake_left)
                _hide_btn(ids.btn_brake_right)
            else:
                layer.size_hint = (None, None)
                layer.pos = (0, 0)
                layer.size = (win_w, win_h)

                btn_w = max(win_w * 0.18, dp(140))
                btn_h = max(win_h * 0.08, dp(70))
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

                if not swapped:
                    _show_btn(ids.btn_brake_left, (side, bottom))
                    _hide_btn(ids.btn_brake_right)
                    _show_btn(ids.btn_right, (win_w - side - btn_w, bottom))
                    _show_btn(ids.btn_left, (win_w - side - btn_w, bottom + btn_h + gap))
                else:
                    _hide_btn(ids.btn_brake_left)
                    _show_btn(ids.btn_brake_right, (win_w - side - btn_w, bottom))
                    _show_btn(ids.btn_left, (side, bottom))
                    _show_btn(ids.btn_right, (side, bottom + btn_h + gap))

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
