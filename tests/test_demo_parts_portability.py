import os
import unittest
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from demo_parts.life_demo_part import LifeSimulationFeature
from demo_parts.mandelbrot_demo_part import MANDEL_KIND_STATUS
from demo_parts.mandelbrot_demo_part import MandelbrotRenderFeature


class _Packet:
    def __init__(self, *, local_pos=None, pos=None, button=1) -> None:
        self.local_pos = local_pos
        self.pos = pos
        self.button = button

    def is_mouse_down(self, button=None) -> bool:
        return button is None or button == self.button


class _CanvasStub:
    def __init__(self, events) -> None:
        self.rect = pygame.Rect(20, 30, 100, 100)
        self.canvas = pygame.Surface((100, 100), pygame.SRCALPHA)
        self._events = list(events)

    def read_event(self):
        if not self._events:
            return None
        return self._events.pop(0)


class _A11yControl:
    def __init__(self) -> None:
        self.tab_index = None
        self.role = None
        self.label = None

    def set_tab_index(self, value):
        self.tab_index = value

    def set_accessibility(self, *, role, label):
        self.role = role
        self.label = label


class DemoPartsPortabilityTests(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()
        pygame.display.set_mode((16, 16))

    def tearDown(self) -> None:
        pygame.quit()

    def test_life_update_life_works_without_demo_part_wrappers(self) -> None:
        part = LifeSimulationFeature()
        host = SimpleNamespace(app=SimpleNamespace(theme=SimpleNamespace(medium=(0, 0, 0))))
        part.demo = host
        part.canvas = _CanvasStub([_Packet(local_pos=(10, 10), button=1)])
        part.toggle = SimpleNamespace(pushed=False)
        part.zoom_slider = SimpleNamespace(value=5.0)
        part.zoom_label = SimpleNamespace(text="")
        part.life_origin = [0.0, 0.0]
        part.life_cell_size = 10

        part.update_life()

        self.assertIn((1, 1), part.life_cells)

    def test_life_accessibility_uses_part_owned_controls(self) -> None:
        part = LifeSimulationFeature()
        part.reset_button = _A11yControl()
        part.toggle = _A11yControl()
        part.zoom_slider = _A11yControl()

        next_index = part.configure_accessibility(SimpleNamespace(), 3)

        self.assertEqual(next_index, 6)
        self.assertEqual(part.reset_button.tab_index, 3)
        self.assertEqual(part.toggle.tab_index, 4)
        self.assertEqual(part.zoom_slider.tab_index, 5)

    def test_mandel_publish_event_updates_internal_status_without_model(self) -> None:
        part = MandelbrotRenderFeature()
        host = SimpleNamespace(app=SimpleNamespace())
        part.demo = host
        part.status_label = SimpleNamespace(text="")

        part.publish_event(MANDEL_KIND_STATUS, "portable status")

        self.assertEqual(part.status_text, "portable status")
        self.assertEqual(part.status_label.text, "portable status")

    def test_mandel_status_event_from_bus_updates_internal_status_without_model(self) -> None:
        part = MandelbrotRenderFeature()
        host = SimpleNamespace(app=SimpleNamespace())
        part.demo = host
        part.status_label = SimpleNamespace(text="")

        part.on_status_event(host, {"kind": MANDEL_KIND_STATUS, "detail": "bus status"})

        self.assertEqual(part.status_text, "bus status")
        self.assertEqual(part.status_label.text, "bus status")


if __name__ == "__main__":
    unittest.main()
