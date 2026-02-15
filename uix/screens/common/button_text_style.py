"""EN: Shared helpers for button text styling.
RU: Общие помощники для стилизации текста кнопок.
"""

from __future__ import annotations

from kivy.metrics import dp

BTN_TEXT_STYLE_STEP_UP = "Subtitle1"
BTN_TEXT_FALLBACK_DP = 16

WHITE = (1, 1, 1, 1)


def caps(text: str) -> str:
    """EN: Convert text to uppercase safely.
    RU: Безопасно преобразовать текст в верхний регистр.
    """
    return (text or "").upper()


def apply_button_text_style(view, btn_text_widgets: list) -> None:
    """EN: Center button text and apply white color plus a small size step up.
    RU: Центрировать текст кнопок и применить белый цвет плюс небольшой шаг размера.
    """
    styles = getattr(getattr(view, "theme_cls", None), "font_styles", {}) or {}

    def _bind_text_size(widget) -> None:
        """EN: Keep text_size in sync for vertical alignment.
        RU: Синхронизировать text_size для корректного вертикального выравнивания.
        """
        widget.text_size = widget.size

    for widget in btn_text_widgets:
        if widget is None:
            continue

        widget.size_hint = (1, 1)
        widget.pos_hint = {"center_x": 0.5, "center_y": 0.5}
        widget.halign = "center"
        widget.valign = "middle"
        widget.bind(size=lambda inst, *_: _bind_text_size(inst))
        _bind_text_size(widget)

        if hasattr(widget, "theme_text_color"):
            widget.theme_text_color = "Custom"
        if hasattr(widget, "text_color"):
            widget.text_color = WHITE

        if BTN_TEXT_STYLE_STEP_UP in styles and hasattr(widget, "font_style"):
            widget.font_style = BTN_TEXT_STYLE_STEP_UP
        else:
            widget.font_size = dp(BTN_TEXT_FALLBACK_DP)
