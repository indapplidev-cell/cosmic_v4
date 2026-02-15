"""EN: Utilities to force-refresh MDTextField hints after language switch.
RU: Утилиты для принудительного обновления хинтов MDTextField после смены языка.
"""

from __future__ import annotations

from typing import Optional

from kivy.uix.widget import Widget


def refresh_all_mdtextfield_hints(root: Widget) -> None:
    """EN: Sync all MDTextField hints in subtree to inner TextInput.
    RU: Синхронизировать хинты всех MDTextField в поддереве с внутренним TextInput.
    """
    if root is None:
        return

    for widget in root.walk(restrict=True):
        if widget.__class__.__name__ == "MDTextField":
            _sync_one_textfield(widget)


def _sync_one_textfield(field) -> None:
    """EN: Sync one MDTextField hint from MDTextFieldHintText to inner input.
    RU: Синхронизировать хинт одного MDTextField из MDTextFieldHintText во внутренний input.
    """
    hint = _extract_hint_text(field)
    if hint is None:
        return

    if hasattr(field, "hint_text"):
        try:
            field.hint_text = hint
        except Exception:
            pass

    text_input = _find_inner_textinput(field)
    if text_input is not None and hasattr(text_input, "hint_text"):
        try:
            text_input.hint_text = hint
        except Exception:
            pass

        for method_name in ("_refresh_hint_text", "refresh_hint_text", "texture_update"):
            if hasattr(text_input, method_name):
                try:
                    getattr(text_input, method_name)()
                except Exception:
                    pass

        try:
            text_input.canvas.ask_update()
        except Exception:
            pass

    try:
        field.do_layout()
    except Exception:
        pass
    try:
        field.canvas.ask_update()
    except Exception:
        pass


def _extract_hint_text(field) -> Optional[str]:
    """EN: Extract current hint text from MDTextFieldHintText child.
    RU: Получить текущий текст хинта из дочернего MDTextFieldHintText.
    """
    for widget in field.walk(restrict=True):
        if widget.__class__.__name__ == "MDTextFieldHintText":
            text = getattr(widget, "text", None)
            if isinstance(text, str):
                return text
    return None


def _find_inner_textinput(field):
    """EN: Locate inner TextInput used by MDTextField for hint rendering.
    RU: Найти внутренний TextInput, который MDTextField использует для рендера хинта.
    """
    for attr_name in ("_text_input", "text_input", "_input", "input"):
        text_input = getattr(field, attr_name, None)
        if text_input is not None and hasattr(text_input, "hint_text"):
            return text_input

    ids = getattr(field, "ids", None)
    if isinstance(ids, dict):
        for key in ("text_input", "input", "textfield", "textinput"):
            text_input = ids.get(key)
            if text_input is not None and hasattr(text_input, "hint_text"):
                return text_input

    for widget in field.walk(restrict=True):
        if widget.__class__.__name__.endswith("TextInput") and hasattr(widget, "hint_text"):
            return widget

    return None
