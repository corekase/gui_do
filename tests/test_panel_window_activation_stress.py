import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
from pygame import Rect

from gui import GuiApplication, PanelControl, WindowControl


class PanelWindowActivationStressTests(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()
        self.surface = pygame.display.set_mode((500, 360))
        self.app = GuiApplication(self.surface)
        self.panel = self.app.add(PanelControl("root", Rect(0, 0, 500, 360)))

    def tearDown(self) -> None:
        pygame.quit()

    @staticmethod
    def _active_windows(*windows: WindowControl) -> list[WindowControl]:
        return [window for window in windows if window.active]

    def _assert_activation_invariants(self, *windows: WindowControl) -> None:
        active_windows = self._active_windows(*windows)
        self.assertLessEqual(len(active_windows), 1)
        if active_windows:
            active = active_windows[0]
            self.assertTrue(active.visible)
            self.assertTrue(active.enabled)

    def test_deterministic_transition_script_preserves_activation_invariants(self) -> None:
        win_a = self.panel.add(WindowControl("a", Rect(20, 20, 120, 100), "A"))
        win_b = self.panel.add(WindowControl("b", Rect(60, 40, 120, 100), "B"))
        win_c = self.panel.add(WindowControl("c", Rect(100, 60, 120, 100), "C"))

        win_c.active = True
        self.assertTrue(win_c.active)
        self._assert_activation_invariants(win_a, win_b, win_c)

        self.panel._lower_window(win_c)
        self.assertTrue(win_b.active)
        self._assert_activation_invariants(win_a, win_b, win_c)

        win_b.enabled = False
        self.assertTrue(win_a.active)
        self._assert_activation_invariants(win_a, win_b, win_c)

        self.panel._raise_window(win_c)
        self.assertTrue(win_c.active)
        self._assert_activation_invariants(win_a, win_b, win_c)

        win_c.visible = False
        self.assertTrue(win_a.active)
        self._assert_activation_invariants(win_a, win_b, win_c)

        self.panel._raise_window(win_b)
        self.assertTrue(win_a.active)
        self._assert_activation_invariants(win_a, win_b, win_c)

        win_b.enabled = True
        self.assertTrue(win_a.active)
        self._assert_activation_invariants(win_a, win_b, win_c)

        removed_a = self.panel.remove(win_a)
        self.assertTrue(removed_a)
        self.assertFalse(win_a.active)
        self.assertTrue(win_b.active)
        self._assert_activation_invariants(win_b, win_c)

        win_c.visible = True
        self.assertTrue(win_c.active)
        self._assert_activation_invariants(win_b, win_c)

        win_c.enabled = False
        self.assertTrue(win_b.active)
        self._assert_activation_invariants(win_b, win_c)

        win_b.enabled = False
        self.assertFalse(win_b.active)
        self.assertFalse(win_c.active)
        self.assertIsNone(self.panel._top_visible_window())

        win_c.enabled = True
        self.assertTrue(win_c.active)
        self._assert_activation_invariants(win_b, win_c)

        removed_c = self.panel.remove(win_c)
        self.assertTrue(removed_c)
        self.assertFalse(win_c.active)
        self.assertIsNone(self.panel._top_visible_window())


if __name__ == "__main__":
    unittest.main()
