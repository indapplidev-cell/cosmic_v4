# -*- coding: utf-8 -*-
"""Thin gameplay surface wrapper around the road renderer and ship engine."""

from kivy.graphics import InstructionGroup
from kivy.uix.widget import Widget


class GameplaySurface(Widget):
    """Kivy widget that delegates frame rendering to a snapshot-driven renderer."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._snapshot_provider = None
        self._gameplay_renderer = None
        self._ship_engine = None
        self._actor_layer = InstructionGroup()
        self.canvas.after.add(self._actor_layer)

    @property
    def actor_canvas(self):
        return self._actor_layer

    def bind_engines(self, snapshot_provider, gameplay_renderer, ship_engine):
        self._snapshot_provider = snapshot_provider
        self._gameplay_renderer = gameplay_renderer
        self._ship_engine = ship_engine

    def render(self):
        if self.width < 2 or self.height < 2:
            return
        if bool(getattr(self, 'disabled', False)) or self.opacity <= 0:
            return
        if not self._snapshot_provider or not self._gameplay_renderer or not self._ship_engine:
            return
        snapshot = self._snapshot_provider()
        self._gameplay_renderer.render(snapshot, self.size)
        self._ship_engine.update(self.size)
