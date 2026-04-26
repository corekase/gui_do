import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
from pygame import Rect

from gui_do import GuiApplication, PanelControl, WindowControl


class WindowActiveSetterGuardsTests(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()
        self.surface = pygame.display.set_mode((400, 300))
        self.app = GuiApplication(self.surface)
        self.panel = self.app.add(PanelControl("root", Rect(0, 0, 400, 300)))

    def tearDown(self) -> None:
        pygame.quit()

    def test_hidden_window_cannot_be_activated_directly(self) -> None:
        first = self.panel.add(WindowControl("a", Rect(20, 20, 120, 100), "A"))
        second = self.panel.add(WindowControl("b", Rect(50, 40, 120, 100), "B"))
        first.active = True

        second.visible = False
        second.active = True

        self.assertTrue(first.active)
        self.assertFalse(second.active)

    def test_disabled_window_cannot_be_activated_directly(self) -> None:
        first = self.panel.add(WindowControl("a", Rect(20, 20, 120, 100), "A"))
        second = self.panel.add(WindowControl("b", Rect(50, 40, 120, 100), "B"))
        first.active = True

        second.enabled = False
        second.active = True

        self.assertTrue(first.active)
        self.assertFalse(second.active)


if __name__ == "__main__":
    unittest.main()
