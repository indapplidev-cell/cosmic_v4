# -*- coding: utf-8 -*-
"""
GIF background widget for the Game screen.

EN: Plays an animated GIF stretched to the full screen.
RU: Проигрывает анимированный GIF, растянутый на весь экран.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List

from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.graphics.texture import Texture
from kivy.logger import Logger
from kivy.properties import BooleanProperty, StringProperty
from kivy.resources import resource_add_path, resource_find
from kivy.uix.widget import Widget

from PIL import Image


class GifBackground(Widget):
    """
    Draws GIF frames as textures on canvas.

    EN: Avoids CoreImage/reload to prevent error spam and recursion.
    RU: Рисует GIF через Texture без CoreImage/reload, чтобы убрать спам и рекурсию.
    """

    source = StringProperty("")
    loop = BooleanProperty(True)
    reverse = BooleanProperty(False)

    def __init__(self, **kwargs):
        """
        Initialize widget and its canvas rectangle.

        EN: Binds size/pos and source loading.
        RU: Привязывает размер/позицию и загрузку по source.
        """
        super().__init__(**kwargs)
        self._frames: List[Texture] = []
        self._durations: List[float] = []
        self._idx: int = 0
        self._ev = None

        with self.canvas.before:
            self._color = Color(1, 1, 1, 1)
            self._rect = Rectangle(pos=self.pos, size=self.size)

        self.bind(pos=self._sync_rect, size=self._sync_rect)
        self.bind(source=self._on_source)

    def _sync_rect(self, *_):
        self._rect.pos = self.pos
        self._rect.size = self.size

    def _cancel(self) -> None:
        if self._ev is not None:
            self._ev.cancel()
            self._ev = None

    def on_parent(self, *_):
        """
        Stop animation if widget is removed.

        EN: Cancels scheduled frame updates when detached.
        RU: Останавливает таймер кадров при удалении со сцены.
        """
        if self.parent is None:
            self._cancel()

    def _on_source(self, *_):
        self._load_gif(self.source)

    def on_reverse(self, *_args) -> None:
        if not self._frames:
            return
        self._cancel()
        self._frames.reverse()
        self._durations.reverse()
        self._idx = 0
        self._rect.texture = self._frames[0]
        self._schedule_next()

    def _load_gif(self, src: str) -> None:
        self._cancel()
        self._frames.clear()
        self._durations.clear()
        self._idx = 0

        if not src:
            self._rect.texture = None
            return

        root = Path(__file__).resolve().parents[2]
        resource_add_path(str(root))
        resource_add_path(str(root / "assets"))
        resource_add_path(str(root / "assets" / "img"))

        absolute_path = str(root / "assets" / "img" / "outerspace-55.gif")
        Logger.info("GifBackground: absolute_path=%s exists=%s", absolute_path, os.path.exists(absolute_path))

        resolved = None
        p = Path(src)
        if p.is_absolute() and p.is_file():
            resolved = str(p)
        if not resolved:
            resolved = resource_find(src) or resource_find("assets/img/outerspace-55.gif")
        if not resolved and os.path.exists(absolute_path):
            resolved = absolute_path

        if not resolved:
            Logger.warning("GifBackground: file not found: %s", src)
            self._rect.texture = None
            return

        p = Path(resolved)
        if not p.is_file():
            Logger.warning("GifBackground: file not found: %s", p)
            self._rect.texture = None
            return

        try:
            im = Image.open(str(p))
        except Exception as exc:
            Logger.exception("GifBackground: open failed: %s", exc)
            self._rect.texture = None
            return

        try:
            while True:
                frame = im.convert("RGBA")
                width, height = frame.size

                tex = Texture.create(size=(width, height), colorfmt="rgba")
                tex.blit_buffer(frame.tobytes(), colorfmt="rgba", bufferfmt="ubyte")
                tex.flip_vertical()

                self._frames.append(tex)

                dur_ms = int(im.info.get("duration", 50))
                self._durations.append(max(0.01, dur_ms / 1000.0))

                im.seek(im.tell() + 1)
        except EOFError:
            pass
        except Exception as exc:
            Logger.exception("GifBackground: decode failed: %s", exc)
            self._rect.texture = None
            return

        if not self._frames:
            Logger.warning("GifBackground: no frames decoded")
            self._rect.texture = None
            return

        Logger.info("GifBackground: loaded %s frames from %s", len(self._frames), p.name)
        self._rect.texture = self._frames[0]
        self._schedule_next()

    def _schedule_next(self) -> None:
        if not self._frames:
            return
        dt = self._durations[self._idx]
        self._ev = Clock.schedule_once(self._next_frame, dt)

    def _next_frame(self, _dt) -> None:
        if not self._frames:
            return

        self._idx += 1
        if self._idx >= len(self._frames):
            if self.loop:
                self._idx = 0
            else:
                return

        self._rect.texture = self._frames[self._idx]
        self._schedule_next()
