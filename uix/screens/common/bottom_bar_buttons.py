"""EN: Shared bottom bar button sizing helpers.
RU: Общие утилиты размеров кнопок нижней панели.
"""

from kivy.clock import Clock
from kivy.metrics import dp


def disable_button_adaptive(btn) -> None:
    """EN: Disable adaptive sizing for MDButton.
    RU: Отключить адаптивный размер для MDButton.
    """
    if hasattr(btn, "adaptive_width"):
        btn.adaptive_width = False
    if hasattr(btn, "adaptive_size"):
        btn.adaptive_size = False
    if hasattr(btn, "theme_width"):
        btn.theme_width = "Custom"


def apply_bottom_buttons(
    *,
    bottombar,
    bottom_center,
    btn_stack,
    buttons: list,
    spacing_dp: float | None = None,
    width_ratio: float = 0.8,
    height_ratio: float | None = 0.90,
) -> None:
    """EN: Apply adaptive button stack sizing from BottomBar dimensions.
    RU: Применить адаптивные размеры стека кнопок от размеров BottomBar.

    EN: The stack height is derived from BottomBar height. Button height is
    clamped with min/max limits, then spacing and vertical padding are reduced
    when needed to guarantee the stack fits inside BottomBar.
    RU: Высота стека берется из высоты BottomBar. Высота кнопок ограничивается
    min/max пределами, затем при нехватке места уменьшаются spacing и
    вертикальные отступы, чтобы стек гарантированно помещался в BottomBar.
    """
    bottom_center.anchor_x = "center"
    bottom_center.anchor_y = "center"

    def _apply(*_args) -> None:
        n = max(len(buttons), 1)
        min_btn_h = dp(32)
        max_btn_h = dp(96)
        stack_ratio = 0.90 if height_ratio is None else height_ratio

        stack_h = max(0.0, bottombar.height * stack_ratio)
        pad_y = max(0.0, stack_h * 0.08)
        spacing = max(0.0, stack_h * 0.06) if spacing_dp is None else max(0.0, spacing_dp)
        slots = max(n - 1, 0)

        available = max(stack_h - (2 * pad_y) - (spacing * slots), 0.0)
        btn_h = available / n
        btn_h = max(min_btn_h, min(max_btn_h, btn_h))

        total_h = (btn_h * n) + (spacing * slots) + (2 * pad_y)
        if total_h > stack_h and slots > 0:
            overflow = total_h - stack_h
            spacing = max(0.0, spacing - (overflow / slots))
            total_h = (btn_h * n) + (spacing * slots) + (2 * pad_y)
        if total_h > stack_h:
            overflow = total_h - stack_h
            pad_y = max(0.0, pad_y - (overflow / 2.0))
            total_h = (btn_h * n) + (spacing * slots) + (2 * pad_y)
        if total_h > stack_h:
            fit_available = max(stack_h - (2 * pad_y) - (spacing * slots), 0.0)
            btn_h = fit_available / n

        btn_stack.size_hint = (None, None)
        btn_stack.orientation = "vertical"
        btn_stack.spacing = spacing
        btn_stack.width = bottombar.width * width_ratio
        btn_stack.height = stack_h
        btn_stack.padding = (0, pad_y, 0, pad_y)
        btn_stack.pos_hint = {"center_x": 0.5, "center_y": 0.5}

        for btn in buttons:
            disable_button_adaptive(btn)
            btn.size_hint_x = 1
            btn.size_hint_y = None
            btn.height = btn_h

    if not getattr(btn_stack, "_stack_bound", False):
        bottombar.bind(size=_apply, height=_apply)
        btn_stack._stack_bound = True
    Clock.schedule_once(_apply, 0)
