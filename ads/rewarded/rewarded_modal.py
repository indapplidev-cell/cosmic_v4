"""EN: Rewarded ad modal overlay.
RU: Модальное оверлей-окно rewarded-рекламы.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from kivy.clock import Clock
from kivy.lang import Builder
from kivy.uix.modalview import ModalView

KV_PATH = Path(__file__).with_name("rewarded_modal.kv")
Builder.load_file(str(KV_PATH))


class RewardedAdModal(ModalView):
    """EN: Modal with delayed close button for rewarded flow.
    RU: Модальное окно с отложенным крестиком для rewarded-сценария.
    """

    def __init__(self, on_close: Callable[[], None] | None = None, **kwargs) -> None:
        """EN: Initialize modal and optional close callback.
        RU: Инициализировать модалку и необязательный callback закрытия.
        """
        super().__init__(**kwargs)
        self.size_hint = (0.8, 0.8)
        self.auto_dismiss = False
        self._on_close = on_close
        self._close_ev = None

    def on_open(self) -> None:
        """EN: Hide close button first, then enable it after delay.
        RU: Сначала скрыть крестик, затем включить его после задержки.
        """
        close_btn = self.ids.close_btn
        close_btn.opacity = 0
        close_btn.disabled = True
        if self._close_ev:
            self._close_ev.cancel()
        self._close_ev = Clock.schedule_once(self._enable_close, 5)

    def _enable_close(self, _dt) -> None:
        """EN: Show and enable close button.
        RU: Показать и включить кнопку закрытия.
        """
        close_btn = self.ids.close_btn
        close_btn.opacity = 1
        close_btn.disabled = False
        self._close_ev = None

    def _on_close_pressed(self) -> None:
        """EN: Close modal and call callback if provided.
        RU: Закрыть модалку и вызвать callback, если он задан.
        """
        self.dismiss()
        if self._on_close:
            self._on_close()
