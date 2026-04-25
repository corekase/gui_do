import os
import unittest
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from gui.core.gui_event import EventType
from gui_do_demo import GuiDoDemo
from demo_features.life_demo_feature import LifeSimulationFeature, LifeSimulationLogicFeature
from shared.feature_lifecycle import Feature, FeatureManager, FeatureMessage


class _Packet:
    def __init__(self, *, local_pos=None, pos=None, button=1) -> None:
        self.kind = EventType.MOUSE_BUTTON_DOWN
        self.local_pos = local_pos
        self.pos = pos
        self.button = button

    def is_mouse_down(self, button=None) -> bool:
        return button is None or button == self.button


class _LifeCanvasStub:
    def __init__(self, events) -> None:
        self.rect = pygame.Rect(20, 30, 120, 120)
        self.canvas = pygame.Surface((120, 120), pygame.SRCALPHA)
        self._events = list(events)

    def read_event(self):
        if not self._events:
            return None
        return self._events.pop(0)


class _LifeLogicObserverPart(Feature):
    def __init__(self, name: str = "life_observer") -> None:
        super().__init__(name, scene_name="main")
        self.last_cells = None

    def on_update(self, _host) -> None:
        while self.has_messages():
            payload = self.pop_message()
            if payload is None:
                continue
            if payload.topic != "life_logic" or payload.event != "state":
                continue
            life_cells = payload.get("life_cells")
            if isinstance(life_cells, set):
                self.last_cells = set(life_cells)


class GuiDoDemoLifeRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()
        pygame.display.set_mode((16, 16))

    def tearDown(self) -> None:
        pygame.quit()

    def _make_demo_stub(self) -> GuiDoDemo:
        demo = GuiDoDemo.__new__(GuiDoDemo)
        demo.app = SimpleNamespace(
            theme=SimpleNamespace(medium=(0, 0, 0)),
            active_scene_name="main",
        )
        demo._feature_manager = FeatureManager(demo.app)
        life_logic_part = LifeSimulationLogicFeature()
        demo._feature_manager.register(life_logic_part, host=demo)
        # Create the life Feature and configure it
        life_part = LifeSimulationFeature()
        life_part.life_cells = set()
        life_part.life_origin = [0.0, 0.0]
        life_part.life_cell_size = 12
        life_part.life_zoom_slider_last_value = 5
        demo._feature_manager.register(life_part, host=demo)
        life_part.bind_logic("life_simulation_logic", alias=life_part.LOGIC_ALIAS)
        demo._life_feature = life_part
        # Set up UI elements on demo
        demo.life_zoom_slider = SimpleNamespace(value=5.0)
        demo.life_canvas = _LifeCanvasStub([])
        demo.life_toggle = SimpleNamespace(pushed=False)
        life_part.zoom_slider = demo.life_zoom_slider
        life_part.canvas = demo.life_canvas
        life_part.toggle = demo.life_toggle
        # Set the demo reference on the Feature so it can access UI elements
        life_part.demo = demo
        return demo

    def test_life_preamble_applies_external_slider_value_change(self) -> None:
        demo = self._make_demo_stub()
        demo.life_zoom_slider.value = 7.0

        demo._life_feature.life_window_preamble()

        self.assertEqual(demo._life_feature.life_zoom_slider_last_value, 7)
        self.assertEqual(demo._life_feature.life_cell_size, 16)

    def test_slider_callback_applies_zoom_change(self) -> None:
        demo = self._make_demo_stub()

        demo._life_feature.on_life_zoom_slider_changed(6.0, None)

        self.assertEqual(demo._life_feature.life_zoom_slider_last_value, 6)
        self.assertEqual(demo._life_feature.life_cell_size, 14)
        self.assertEqual(demo.life_zoom_slider.value, 6.0)

    def test_life_reset_restores_default_zoom_state(self) -> None:
        demo = self._make_demo_stub()
        demo._life_feature.life_cell_size = 18
        demo.life_zoom_slider.value = 8.0

        demo._life_feature.life_reset()

        self.assertEqual(demo._life_feature.life_cell_size, 12)
        self.assertEqual(demo.life_zoom_slider.value, 5.0)

    def test_update_life_uses_local_packet_position_when_available(self) -> None:
        demo = self._make_demo_stub()
        demo._life_feature.life_cell_size = 10
        demo.life_canvas = _LifeCanvasStub([
            _Packet(local_pos=(15, 15), pos=(200, 200), button=1),
        ])
        demo._life_feature.canvas = demo.life_canvas

        demo._life_feature.update_life()
        demo._feature_manager.update_features(demo)

        self.assertIn((1, 1), demo._life_feature.life_cells)

    def test_life_reset_and_next_are_processed_by_logic_part(self) -> None:
        demo = self._make_demo_stub()

        demo._life_feature.life_reset()
        demo._feature_manager.update_features(demo)

        expected_seed = {(0, 0), (1, 0), (-1, 0), (0, -1), (1, -2)}
        self.assertEqual(demo._life_feature.life_cells, expected_seed)

        demo.life_toggle.pushed = True
        demo._life_feature.update_life()
        demo._feature_manager.update_features(demo)

        self.assertNotEqual(demo._life_feature.life_cells, expected_seed)

    def test_non_life_part_can_bind_and_use_life_logic_part(self) -> None:
        app = SimpleNamespace(active_scene_name="main")
        manager = FeatureManager(app)
        logic_part = LifeSimulationLogicFeature()
        observer = _LifeLogicObserverPart()
        manager.register(logic_part, host=SimpleNamespace())
        manager.register(observer, host=SimpleNamespace())

        observer.bind_logic("life_simulation_logic", alias="life")
        sent_snapshot = observer.send_logic_message({"command": "snapshot"}, alias="life")
        manager.update_features(SimpleNamespace())

        self.assertTrue(sent_snapshot)
        self.assertIsInstance(observer.last_cells, set)
        self.assertIn((0, 0), observer.last_cells)

        sent_toggle = observer.send_logic_message({"command": "toggle_cell", "cell": (0, 0)}, alias="life")
        manager.update_features(SimpleNamespace())

        self.assertTrue(sent_toggle)
        self.assertNotIn((0, 0), observer.last_cells)

    def test_update_life_message_drain_is_lifecycle_owned_when_registered(self) -> None:
        demo = self._make_demo_stub()
        demo._life_feature.life_cells = set()
        demo._life_feature.enqueue_message(
            FeatureMessage.from_payload(
                "test_sender",
                demo._life_feature.name,
                {
                    "topic": "life_logic",
                    "event": "state",
                    "life_cells": {(2, 3)},
                },
            )
        )

        demo._life_feature.update_life()

        self.assertEqual(demo._life_feature.life_cells, set())

        demo._feature_manager.update_features(demo)

        self.assertEqual(demo._life_feature.life_cells, {(2, 3)})

    def test_life_part_ignores_unrelated_topics(self) -> None:
        demo = self._make_demo_stub()
        demo._life_feature.life_cells = {(7, 7)}
        demo._life_feature.enqueue_message(
            FeatureMessage.from_payload("test_sender", demo._life_feature.name, {"topic": "other", "status": "ignore"})
        )

        demo._feature_manager.update_features(demo)

        self.assertEqual(demo._life_feature.life_cells, {(7, 7)})


if __name__ == "__main__":
    unittest.main()
