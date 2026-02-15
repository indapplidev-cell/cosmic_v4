from __future__ import annotations

from kivy.clock import Clock
from kivy.uix.widget import Widget


def refresh_all_hint_texts(root: Widget) -> None:
    """
    KivyMD 2.0.1: обновляет MDTextFieldHintText в пустых полях без фокуса.
    Делаем 2 прохода (сразу и через dt), чтобы поймать момент после layout/отрисовки.
    """
    if not root:
        return

    def _pass(_dt):
        for w in root.walk(restrict=True):
            if w.__class__.__name__ == "MDTextFieldHintText":
                _refresh_one_hint(w)

    Clock.schedule_once(_pass, 0)
    Clock.schedule_once(_pass, 0.05)


def _refresh_one_hint(hint) -> None:
    # 1) форс-диспетч свойства text (ключевой момент)
    try:
        hint.property("text").dispatch(hint)
    except Exception:
        pass

    # 2) форс-текстуру и канвас
    try:
        hint.texture_update()
    except Exception:
        pass
    try:
        hint.canvas.ask_update()
    except Exception:
        pass

    # 3) подняться до MDTextField и форснуть его layout/канвас
    field = hint.parent
    # MDTextFieldHintText обычно лежит внутри MDTextField (иногда через промежуточные контейнеры)
    for _ in range(5):
        if field is None:
            break
        if field.__class__.__name__ == "MDTextField":
            break
        field = field.parent

    if field is not None and field.__class__.__name__ == "MDTextField":
        try:
            field.do_layout()
        except Exception:
            pass
        try:
            field.canvas.ask_update()
        except Exception:
            pass
