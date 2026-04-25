import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
from pygame import Rect

from gui import GuiApplication, PanelControl, WindowControl


class PanelWindowOrderingActivationTests(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()
        self.surface = pygame.display.set_mode((400, 300))
        self.app = GuiApplication(self.surface)
        self.panel = self.app.add(PanelControl("root", Rect(0, 0, 400, 300)))

    def tearDown(self) -> None:
        pygame.quit()

    def test_programmatic_raise_sets_active_for_visible_enabled_window(self) -> None:
        win_a = self.panel.add(WindowControl("a", Rect(20, 20, 120, 100), "A"))
        win_b = self.panel.add(WindowControl("b", Rect(50, 40, 120, 100), "B"))

        self.panel._raise_window(win_a)

        self.assertEqual(self.panel.children[-1], win_a)
        self.assertTrue(win_a.active)
        self.assertFalse(win_b.active)

    def test_programmatic_lower_promotes_new_top_visible_enabled_window(self) -> None:
        win_a = self.panel.add(WindowControl("a", Rect(20, 20, 120, 100), "A"))
        win_b = self.panel.add(WindowControl("b", Rect(50, 40, 120, 100), "B"))

        win_b.active = True
        self.panel._lower_window(win_b)

        self.assertEqual(self.panel.children[0], win_b)
        self.assertTrue(win_a.active)
        self.assertFalse(win_b.active)

    def test_programmatic_raise_hidden_or_disabled_window_does_not_steal_active(self) -> None:
        win_a = self.panel.add(WindowControl("a", Rect(20, 20, 120, 100), "A"))
        win_b = self.panel.add(WindowControl("b", Rect(50, 40, 120, 100), "B"))
        win_a.active = True

        win_b.visible = False
        self.panel._raise_window(win_b)
        self.assertTrue(win_a.active)
        self.assertFalse(win_b.active)

        win_b.visible = True
        win_b.enabled = False
        self.panel._raise_window(win_b)
        self.assertTrue(win_a.active)
        self.assertFalse(win_b.active)


if __name__ == "__main__":
    unittest.main()
