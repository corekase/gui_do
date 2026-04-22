import os
import unittest
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from gui.core.gui_event import EventType
from gui_do_demo import GuiDoDemo


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
        demo.neighbours = GuiDoDemo.neighbours
        demo.life_cells = set()
        demo.life_origin = [0.0, 0.0]
        demo.life_cell_size = 12
        demo._life_zoom_slider_last_value = 5
        demo.life_zoom_slider = SimpleNamespace(value=5.0)
        demo.life_zoom_label = SimpleNamespace(text="Zoom 12")
        demo.life_canvas = _LifeCanvasStub([])
        demo.app = SimpleNamespace(theme=SimpleNamespace(medium=(0, 0, 0)))
        demo.life_toggle = SimpleNamespace(pushed=False)
        return demo

    def test_life_preamble_applies_external_slider_value_change(self) -> None:
        demo = self._make_demo_stub()
        demo.life_zoom_slider.value = 7.0

        demo._life_window_preamble()

        self.assertEqual(demo._life_zoom_slider_last_value, 7)
        self.assertEqual(demo.life_cell_size, 16)

    def test_slider_callback_applies_zoom_change(self) -> None:
        demo = self._make_demo_stub()

        demo._on_life_zoom_slider_changed(6.0)

        self.assertEqual(demo._life_zoom_slider_last_value, 6)
        self.assertEqual(demo.life_cell_size, 14)
        self.assertEqual(demo.life_zoom_label.text, "Zoom 14")

    def test_life_reset_sets_zoom_label_to_default(self) -> None:
        demo = self._make_demo_stub()
        demo.life_zoom_label.text = "Zoom 18"

        demo._life_reset()

        self.assertEqual(demo.life_zoom_label.text, "Zoom 12")

    def test_update_life_uses_local_packet_position_when_available(self) -> None:
        demo = self._make_demo_stub()
        demo.life_cell_size = 10
        demo.life_canvas = _LifeCanvasStub([
            _Packet(local_pos=(15, 15), pos=(200, 200), button=1),
        ])

        demo._update_life()

        self.assertIn((1, 1), demo.life_cells)


if __name__ == "__main__":
    unittest.main()
