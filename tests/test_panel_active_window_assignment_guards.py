import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
from pygame import Rect

from gui_do import GuiApplication, PanelControl, WindowControl


class PanelActiveWindowAssignmentGuardsTests(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()
        self.surface = pygame.display.set_mode((400, 300))
        self.app = GuiApplication(self.surface)
        self.panel = self.app.add(PanelControl("root", Rect(0, 0, 400, 300)))

    def tearDown(self) -> None:
        pygame.quit()

    def test_setting_active_to_hidden_window_falls_back_to_top_visible_enabled(self) -> None:
        win_a = self.panel.add(WindowControl("a", Rect(20, 20, 120, 100), "A"))
        win_b = self.panel.add(WindowControl("b", Rect(50, 40, 120, 100), "B"))

        win_b.visible = False
        self.panel._set_active_window(win_b)

        self.assertTrue(win_a.active)
        self.assertFalse(win_b.active)

    def test_setting_active_to_disabled_window_falls_back_to_top_visible_enabled(self) -> None:
        win_a = self.panel.add(WindowControl("a", Rect(20, 20, 120, 100), "A"))
        win_b = self.panel.add(WindowControl("b", Rect(50, 40, 120, 100), "B"))

        win_b.enabled = False
        self.panel._set_active_window(win_b)

        self.assertTrue(win_a.active)
        self.assertFalse(win_b.active)

    def test_setting_active_to_detached_window_clears_when_no_visible_enabled_windows(self) -> None:
        win = self.panel.add(WindowControl("a", Rect(20, 20, 120, 100), "A"))
        self.panel.remove(win)

        self.panel._set_active_window(win)

        self.assertIsNone(self.panel._top_visible_window())


if __name__ == "__main__":
    unittest.main()
