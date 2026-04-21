import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
from pygame import Rect

from gui import GuiApplication, PanelControl, WindowControl


class PanelWindowActivationSequencesTests(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()
        self.surface = pygame.display.set_mode((500, 360))
        self.app = GuiApplication(self.surface)
        self.panel = self.app.add(PanelControl("root", Rect(0, 0, 500, 360)))

    def tearDown(self) -> None:
        pygame.quit()

    def test_interleaved_order_and_state_transitions_keep_valid_active_window(self) -> None:
        win_a = self.panel.add(WindowControl("a", Rect(20, 20, 120, 100), "A"))
        win_b = self.panel.add(WindowControl("b", Rect(60, 40, 120, 100), "B"))
        win_c = self.panel.add(WindowControl("c", Rect(100, 60, 120, 100), "C"))

        win_c.active = True
        self.assertTrue(win_c.active)

        self.panel._lower_window(win_c)
        self.assertTrue(win_b.active)
        self.assertFalse(win_c.active)

        win_b.enabled = False
        self.assertTrue(win_a.active)
        self.assertFalse(win_b.active)

        self.panel._raise_window(win_c)
        self.assertTrue(win_c.active)
        self.assertFalse(win_a.active)

        win_c.visible = False
        self.assertTrue(win_a.active)
        self.assertFalse(win_c.active)

        win_b.enabled = True
        self.assertTrue(win_a.active)
        self.assertFalse(win_b.active)

    def test_sequence_ending_with_no_visible_enabled_windows_clears_active_state(self) -> None:
        win_a = self.panel.add(WindowControl("a", Rect(20, 20, 120, 100), "A"))
        win_b = self.panel.add(WindowControl("b", Rect(60, 40, 120, 100), "B"))

        win_b.active = True
        self.assertTrue(win_b.active)

        win_b.visible = False
        self.assertTrue(win_a.active)

        win_a.enabled = False
        self.assertFalse(win_a.active)
        self.assertFalse(win_b.active)
        self.assertIsNone(self.panel._top_visible_window())


if __name__ == "__main__":
    unittest.main()
