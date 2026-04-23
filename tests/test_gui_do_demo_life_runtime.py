import os
import unittest
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from gui.core.gui_event import EventType
from gui_do_demo import GuiDoDemo
from demo_parts.life_demo_part import LifeSimulationFeature, LifeSimulationLogicPart
from shared.part_lifecycle import PartManager


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
        demo._part_manager = PartManager(demo.app)
        life_logic_part = LifeSimulationLogicPart()
        demo._part_manager.register(life_logic_part, host=demo)
        # Create the life part and configure it
        life_part = LifeSimulationFeature()
        life_part.life_cells = set()
        life_part.life_origin = [0.0, 0.0]
        life_part.life_cell_size = 12
        life_part.life_zoom_slider_last_value = 5
        demo._part_manager.register(life_part, host=demo)
        life_part.bind_logic_part("life_simulation_logic", alias=life_part.LOGIC_ALIAS)
        demo._life_feature = life_part
        # Set up UI elements on demo
        demo.life_zoom_slider = SimpleNamespace(value=5.0)
        demo.life_zoom_label = SimpleNamespace(text="Zoom 12")
        demo.life_canvas = _LifeCanvasStub([])
        demo.life_toggle = SimpleNamespace(pushed=False)
        life_part.zoom_slider = demo.life_zoom_slider
        life_part.zoom_label = demo.life_zoom_label
        life_part.canvas = demo.life_canvas
        life_part.toggle = demo.life_toggle
        # Set the demo reference on the part so it can access UI elements
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

        demo._life_feature.on_life_zoom_slider_changed(6.0)

        self.assertEqual(demo._life_feature.life_zoom_slider_last_value, 6)
        self.assertEqual(demo._life_feature.life_cell_size, 14)
        self.assertEqual(demo.life_zoom_label.text, "Zoom 14")

    def test_life_reset_sets_zoom_label_to_default(self) -> None:
        demo = self._make_demo_stub()
        demo.life_zoom_label.text = "Zoom 18"

        demo._life_feature.life_reset()

        self.assertEqual(demo.life_zoom_label.text, "Zoom 12")

    def test_update_life_uses_local_packet_position_when_available(self) -> None:
        demo = self._make_demo_stub()
        demo._life_feature.life_cell_size = 10
        demo.life_canvas = _LifeCanvasStub([
            _Packet(local_pos=(15, 15), pos=(200, 200), button=1),
        ])
        demo._life_feature.canvas = demo.life_canvas

        demo._life_feature.update_life()
        demo._part_manager.update_parts(demo)

        self.assertIn((1, 1), demo._life_feature.life_cells)

    def test_life_reset_and_next_are_processed_by_logic_part(self) -> None:
        demo = self._make_demo_stub()

        demo._life_feature.life_reset()
        demo._part_manager.update_parts(demo)

        expected_seed = {(0, 0), (1, 0), (-1, 0), (0, -1), (1, -2)}
        self.assertEqual(demo._life_feature.life_cells, expected_seed)

        demo.life_toggle.pushed = True
        demo._life_feature.update_life()
        demo._part_manager.update_parts(demo)

        self.assertNotEqual(demo._life_feature.life_cells, expected_seed)


if __name__ == "__main__":
    unittest.main()
