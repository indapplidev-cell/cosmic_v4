"""EN: Shared bottom bar button sizing helpers.
RU: Общие утилиты размеров кнопок нижней панели.
"""

from kivy.clock import Clock


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
    btn_h_dp: float,
    spacing_dp: float,
    width_ratio: float = 0.8,
    height_ratio: float | None = None,
) -> None:
    """EN: Apply standard bottom bar button stack sizing.
    RU: Применить стандартные размеры стека кнопок нижней панели.
    """
    bottom_center.anchor_x = "center"
    bottom_center.anchor_y = "center"

    def _apply(*_args) -> None:
        btn_stack.size_hint = (None, None)
        btn_stack.orientation = "vertical"
        btn_stack.spacing = spacing_dp
        btn_stack.width = bottombar.width * width_ratio
        if height_ratio is None:
            btn_stack.height = (len(buttons) * btn_h_dp) + (max(len(buttons) - 1, 0) * spacing_dp)
        else:
            btn_stack.height = bottombar.height * height_ratio

        for btn in buttons:
            disable_button_adaptive(btn)
            btn.size_hint_x = 1
            btn.size_hint_y = None
            btn.height = btn_h_dp

    if not getattr(btn_stack, "_stack_bound", False):
        bottombar.bind(size=_apply)
        btn_stack._stack_bound = True
    Clock.schedule_once(_apply, 0)
