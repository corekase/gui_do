import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
from pygame import Rect, Surface

from gui.controls.canvas_control import CanvasControl
from gui.core.gui_event import EventType, GuiEvent


def _motion(pos):
    return GuiEvent(kind=EventType.MOUSE_MOTION, type=0, pos=pos, rel=(0, 0))


class _FakeFactory:
    def build_frame_visuals(self, rect: Rect):
        idle = Surface((rect.width, rect.height), pygame.SRCALPHA)
        idle.fill((10, 10, 10, 255))
        hover = idle.copy()
        armed = idle.copy()
        disabled = idle.copy()
        hidden = Surface((rect.width, rect.height), pygame.SRCALPHA)
        return type("Visuals", (), {"idle": idle, "hover": hover, "armed": armed, "disabled": disabled, "hidden": hidden})

    @staticmethod
    def resolve_visual_state(visuals, *, visible: bool, enabled: bool, armed: bool, hovered: bool):
        del armed, hovered
        if not visible:
            return visuals.hidden
        if not enabled:
            return visuals.disabled
        return visuals.idle


class CanvasControlRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()
        pygame.display.set_mode((80, 80))

    def tearDown(self) -> None:
        pygame.quit()

    def test_read_event_exposes_local_position(self) -> None:
        control = CanvasControl("c", Rect(20, 30, 20, 20), max_events=4)

        handled = control.handle_event(_motion((26, 37)), None)
        packet = control.read_event()

        self.assertTrue(handled)
        self.assertIsNotNone(packet)
        self.assertEqual(packet.pos, (26, 37))
        self.assertEqual(packet.local_pos, (6, 7))

    def test_canvas_surface_resizes_with_rect_and_preserves_existing_pixels(self) -> None:
        control = CanvasControl("c", Rect(0, 0, 10, 10), max_events=4)
        control.canvas.fill((255, 0, 0, 255), Rect(0, 0, 1, 1))

        control.rect.size = (30, 20)
        control.handle_event(_motion((1, 1)), None)

        self.assertEqual(control.canvas.get_size(), (30, 20))
        self.assertEqual(tuple(control.canvas.get_at((0, 0))[:3]), (255, 0, 0))

    def test_draw_path_resizes_canvas_when_event_path_not_hit(self) -> None:
        control = CanvasControl("c", Rect(0, 0, 10, 10), max_events=4)
        control.rect.size = (18, 16)
        target = Surface((40, 40), pygame.SRCALPHA)
        theme = type("Theme", (), {"graphics_factory": _FakeFactory()})()

        control.draw(target, theme)

        self.assertEqual(control.canvas.get_size(), (18, 16))


if __name__ == "__main__":
    unittest.main()
