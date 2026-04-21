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

        removed = self.panel.remove(window)

        self.assertTrue(removed)
        self.assertIsNone(self.panel._drag_window)
        self.assertIsNone(self.panel._drag_last_pos)


if __name__ == "__main__":
    unittest.main()
