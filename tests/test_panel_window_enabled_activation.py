import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
from pygame import Rect

from gui import GuiApplication, PanelControl, WindowControl


class PanelWindowEnabledActivationTests(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()
        self.surface = pygame.display.set_mode((400, 300))
        self.app = GuiApplication(self.surface)
        self.panel = self.app.add(PanelControl("root", Rect(0, 0, 400, 300)))

    def tearDown(self) -> None:
        pygame.quit()

    def test_disabling_active_window_promotes_next_top_visible_window(self) -> None:
        win_a = self.panel.add(WindowControl("a", Rect(20, 20, 120, 100), "A"))
        win_b = self.panel.add(WindowControl("b", Rect(50, 40, 120, 100), "B"))

        win_b.active = True
        self.assertTrue(win_b.active)

        win_b.enabled = False

        self.assertFalse(win_b.active)
        self.assertTrue(win_a.active)

    def test_disabling_last_active_window_clears_active_state(self) -> None:
        win = self.panel.add(WindowControl("a", Rect(20, 20, 120, 100), "A"))
        win.active = True

        win.enabled = False

        self.assertFalse(win.active)
        self.assertIsNone(self.panel._top_visible_window())

    def test_reenabling_visible_window_activates_when_no_active_window_exists(self) -> None:
        win = self.panel.add(WindowControl("a", Rect(20, 20, 120, 100), "A"))

        win.enabled = False
        self.assertFalse(win.active)

        win.enabled = True

        self.assertTrue(win.active)


if __name__ == "__main__":
    unittest.main()
