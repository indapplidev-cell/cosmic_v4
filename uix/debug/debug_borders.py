"""EN: Debug borders for layout visualization.
RU: Отладочные рамки для визуализации раскладок.
"""

from __future__ import annotations

from kivy.graphics import Color, Line

DEBUG_UI_BORDERS = False


def enable_debug_borders(flag: bool) -> None:
    """EN: Enable or disable debug borders globally.
    RU: Включить или выключить отладочные рамки глобально.
    """
    global DEBUG_UI_BORDERS
    DEBUG_UI_BORDERS = flag


def apply_debug_border(widget, *, name: str | None = None) -> None:
    """EN: Apply a debug border to a widget if enabled.
    RU: Применить отладочную рамку к виджету, если включено.
    """
    if not DEBUG_UI_BORDERS or widget is None:
        return

    if getattr(widget, "_dbg_bound", False):
        _update_border(widget)
        return

    with widget.canvas.after:
        widget._dbg_color = Color(0.2, 0.8, 1.0, 1.0)
        widget._dbg_line = Line(rectangle=(*widget.pos, *widget.size), width=1)

    def _on_change(*_args) -> None:
        _update_border(widget)

    widget.bind(pos=_on_change, size=_on_change)
    widget._dbg_bound = True


def _update_border(widget) -> None:
    """EN: Update an existing debug border geometry.
    RU: Обновить геометрию существующей рамки.
    """
    line = getattr(widget, "_dbg_line", None)
    if line is not None:
        line.rectangle = (*widget.pos, *widget.size)


def apply_debug_borders_to_ids(root, ids: list[str]) -> None:
    """EN: Apply debug borders to widgets by id list.
    RU: Применить отладочные рамки к виджетам по списку id.
    """
    if root is None:
        return
    for widget_id in ids:
        widget = root.ids.get(widget_id)
        apply_debug_border(widget, name=widget_id)
