from __future__ import annotations

from kivy.graphics import InstructionGroup

from client.gameplay.runtime import gameplay_runtime as gameplay_runtime_module
from client.gameplay.runtime.gameplay_runtime import GameplayRuntime
from client.gameplay.widgets.gameplay_surface import GameplaySurface


def test_gameplay_surface_exposes_separate_actor_layer_in_canvas_after():
    surface = GameplaySurface()

    assert isinstance(surface.actor_canvas, InstructionGroup)
    assert surface.actor_canvas is not surface.canvas
    assert any(instruction is surface.actor_canvas for instruction in surface.canvas.after.children)


def test_runtime_uses_surface_canvas_for_road_and_actor_canvas_for_ship(monkeypatch):
    captured = {}

    class RendererSpy:
        def __init__(self, canvas, config, projector):
            captured['renderer_canvas'] = canvas
            captured['renderer_config'] = config
            captured['renderer_projector'] = projector

        def render(self, snapshot, size):
            return None

    class ShipEngineSpy:
        def __init__(self, canvas, config):
            captured['ship_canvas'] = canvas
            captured['ship_config'] = config

        def update(self, size):
            return None

        def reset_to_start(self, state):
            return None

    monkeypatch.setattr(gameplay_runtime_module, 'GameplayRenderer', RendererSpy)
    monkeypatch.setattr(gameplay_runtime_module, 'ShipEngine', ShipEngineSpy)

    surface = GameplaySurface()
    runtime = GameplayRuntime(surface)

    assert captured['renderer_canvas'] is surface.canvas
    assert captured['ship_canvas'] is surface.actor_canvas
    assert captured['ship_canvas'] is not captured['renderer_canvas']
    assert runtime._gameplay_renderer is not None
    assert runtime._ship_engine is not None
