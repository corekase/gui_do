import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
from pygame import Rect

from gui import GuiApplication, PanelControl, WindowControl


class PanelDragRemoveCleanupTests(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()
        self.surface = pygame.display.set_mode((400, 300))
        self.app = GuiApplication(self.surface)
        self.panel = self.app.add(PanelControl("root", Rect(0, 0, 400, 300)))

    def tearDown(self) -> None:
        pygame.quit()

    def test_remove_dragged_window_clears_panel_drag_state_immediately(self) -> None:
        window = self.panel.add(WindowControl("win", Rect(40, 40, 200, 140), "W"))
        start = window.title_bar_rect().center

        self.app.process_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": start, "button": 1}))
        self.assertIs(self.panel._drag_window, window)
        self.assertTrue(self.app.pointer_capture.is_owned_by("win"))

        removed = self.panel.remove(window)

        self.assertTrue(removed)
        self.assertIsNone(self.panel._drag_window)
        self.assertIsNone(self.panel._drag_last_pos)

        # Next routed event clears any lingering capture ownership for removed drag window.
        self.app.process_event(pygame.event.Event(pygame.MOUSEMOTION, {"pos": (10, 10), "rel": (0, 0)}))
        self.assertFalse(self.app.pointer_capture.is_owned_by("win"))


if __name__ == "__main__":
    unittest.main()
