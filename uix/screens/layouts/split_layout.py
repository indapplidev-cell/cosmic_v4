"""EN: Shared equal split layout for left/divider/right screens.
RU: Общая раскладка равного сплита для левой/разделителя/правой зон.
"""

from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp

from .layout_constants import DIVIDER_W, ZONE_LEFT_RATIO, ZONE_RIGHT_RATIO


def apply_equal_split_layout(
    view,
    *,
    card_id: str,
    grid_id: str,
    left_id: str,
    divider_id: str,
    right_id: str,
    fullscreen: bool = True,
) -> None:
    """EN: Apply shared equal split geometry and divider rendering.
    RU: Применить общую геометрию равного сплита и отрисовку разделителя.
    """

    def _draw_divider() -> None:
        divider = view.ids[divider_id]
        divider.canvas.before.clear()
        with divider.canvas.before:
            Color(0.3, 0.3, 0.3, 1)
            Rectangle(pos=divider.pos, size=divider.size)

    def _apply(*_args) -> None:
        ids = view.ids
        card = ids[card_id]
        grid = ids[grid_id]
        left_col = ids[left_id]
        divider = ids[divider_id]
        right_col = ids[right_id]

        if fullscreen:
            card.size_hint = (1, 1)
            card.radius = [0, 0, 0, 0]
            card.elevation = 0
            card.padding = (0, 0, 0, 0)
            card.size = Window.size

        grid.cols = 3
        grid.rows = 1
        grid.spacing = 0
        grid.size_hint = (1, 1)
        grid.size = card.size

        divider.size_hint_x = None
        divider.width = dp(DIVIDER_W)
        divider.size_hint_y = 1

        free_w = grid.width - divider.width
        left_w = free_w * ZONE_LEFT_RATIO
        right_w = free_w * ZONE_RIGHT_RATIO

        left_col.size_hint_x = None
        left_col.width = left_w
        left_col.size_hint_y = 1

        right_col.size_hint_x = None
        right_col.width = right_w
        right_col.size_hint_y = 1

        _draw_divider()

    if not getattr(view, "_layout_bound", False):
        Window.bind(size=_apply)
        view._layout_bound = True

    if not getattr(view, "_divider_bound", False):
        view.ids[divider_id].bind(pos=lambda *_: _draw_divider(), size=lambda *_: _draw_divider())
        view._divider_bound = True

    _apply()
