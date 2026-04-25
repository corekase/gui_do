import unittest

import pygame
from pygame import Rect

from gui.controls.canvas_control import CanvasControl
from gui.core.gui_event import EventType, GuiEvent


def _motion(pos):
    return GuiEvent(kind=EventType.MOUSE_MOTION, type=0, pos=pos, rel=(0, 0))


class CanvasInteractionGuardsTests(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()
        pygame.display.set_mode((16, 16))

    def tearDown(self) -> None:
        pygame.quit()

    def test_canvas_ignores_events_when_disabled(self) -> None:
        control = CanvasControl("c", Rect(0, 0, 20, 20), max_events=8)
        control.enabled = False

        handled = control.handle_event(_motion((5, 5)), None)

        self.assertFalse(handled)
        self.assertIsNone(control.read_event())

    def test_canvas_ignores_events_when_hidden(self) -> None:
        control = CanvasControl("c", Rect(0, 0, 20, 20), max_events=8)
        control.visible = False

        handled = control.handle_event(_motion((5, 5)), None)

        self.assertFalse(handled)
        self.assertIsNone(control.read_event())


if __name__ == "__main__":
    unittest.main()
