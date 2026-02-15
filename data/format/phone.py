"""EN: Utilities for phone normalization, formatting, and live input masking.
RU: Утилиты для нормализации, форматирования и маскирования ввода телефона.
"""

from __future__ import annotations

import re

from kivy.clock import Clock


def normalize_phone(value: str) -> str:
    """EN: Keep only digits and limit to 10 characters.
    RU: Оставить только цифры и ограничить длину до 10 символов.
    """
    return re.sub(r"\D", "", value or "")[:10]


def format_phone(value: str) -> str:
    """EN: Format digits to partial/full mask `(000) 000-00-00` for live typing.
    RU: Форматировать цифры в частичную/полную маску `(000) 000-00-00` для ввода в реальном времени.
    """
    digits = normalize_phone(value)
    if not digits:
        return ""
    if len(digits) <= 3:
        if len(digits) == 3:
            return f"({digits})"
        return f"({digits}"
    if len(digits) <= 6:
        return f"({digits[:3]}) {digits[3:]}"
    if len(digits) <= 8:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    return f"({digits[:3]}) {digits[3:6]}-{digits[6:8]}-{digits[8:]}"


def attach_phone_mask(text_input) -> None:
    """EN: Attach one-time phone mask behavior to a text field.
    RU: Подключить одноразовое поведение маски телефона к текстовому полю.
    """
    if getattr(text_input, "_phone_mask_attached", False):
        return

    def _digits_only(substring, from_undo=False):
        """EN: Allow only digits in the inserted substring.
        RU: Пропускать только цифры во вводимом фрагменте.
        """
        return re.sub(r"\D", "", substring)

    text_input.input_filter = _digits_only
    text_input._phone_mask_lock = False

    def digits_before_cursor(text: str, cursor_x: int) -> int:
        """EN: Count digits in text before the cursor position.
        RU: Посчитать количество цифр в тексте слева от курсора.
        """
        if cursor_x <= 0:
            return 0
        return sum(ch.isdigit() for ch in text[:cursor_x])

    def cursor_from_digits(text: str, digits_count: int) -> int:
        """EN: Return cursor position after the given count of digits.
        RU: Вернуть позицию курсора после заданного количества цифр.
        """
        if digits_count <= 0:
            return 0
        count = 0
        for i, ch in enumerate(text):
            if ch.isdigit():
                count += 1
                if count >= digits_count:
                    return i + 1
        return len(text)

    def _apply_mask(_dt: float = 0.0) -> None:
        """EN: Apply mask after input stack finishes to avoid insert_text conflicts.
        RU: Применить маску после завершения ввода, чтобы не конфликтовать с insert_text.
        """
        if getattr(text_input, "_phone_mask_lock", False):
            return
        old_text = text_input.text or ""
        old_cursor = text_input.cursor[0] if text_input.cursor else 0
        old_k = digits_before_cursor(old_text, old_cursor)
        text_input._phone_mask_lock = True
        try:
            digits = normalize_phone(text_input.text)
            masked = format_phone(digits)
            if masked != text_input.text:
                text_input.text = masked
            text_input.cursor = (cursor_from_digits(masked, old_k), 0)
        finally:
            text_input._phone_mask_lock = False

    trigger_mask = Clock.create_trigger(_apply_mask, 0)

    def _on_text(_instance, _text: str) -> None:
        """EN: Schedule mask update on text changes.
        RU: Планировать обновление маски при изменении текста.
        """
        if getattr(text_input, "_phone_mask_lock", False):
            return
        trigger_mask()

    if not getattr(text_input, "_phone_mask_backspace_patched", False):
        text_input._orig_do_backspace = text_input.do_backspace

        def _do_backspace(from_undo=False, mode="bkspc"):
            """EN: Backspace/delete that operates on digits, not mask symbols.
            RU: Backspace/delete, работающий по цифрам, а не по символам маски.
            """
            if getattr(text_input, "selection_text", ""):
                return text_input._orig_do_backspace(from_undo=from_undo, mode=mode)

            digits = normalize_phone(text_input.text)
            if not digits:
                text_input.text = ""
                return

            cur = text_input.cursor[0] if text_input.cursor else 0
            k = digits_before_cursor(text_input.text, cur)

            if mode == "bkspc":
                if k == 0:
                    text_input.text = ""
                    return
                new_digits = digits[: k - 1] + digits[k:]
                new_k = k - 1
            else:
                if k >= len(digits):
                    return
                new_digits = digits[:k] + digits[k + 1 :]
                new_k = k

            masked = format_phone(new_digits)
            text_input._phone_mask_lock = True
            try:
                text_input.text = masked
                text_input.cursor = (cursor_from_digits(masked, new_k), 0)
            finally:
                text_input._phone_mask_lock = False

        text_input.do_backspace = _do_backspace
        text_input._phone_mask_backspace_patched = True

    text_input.bind(text=_on_text)
    text_input._phone_mask_attached = True
    trigger_mask()
