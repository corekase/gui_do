import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
from pygame import Rect

from gui import GuiApplication, PanelControl, ToggleControl


class ToggleControlRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()
        self.surface = pygame.display.set_mode((240, 160))
        self.app = GuiApplication(self.surface)
        self.root = self.app.add(PanelControl("root", Rect(0, 0, 240, 160)))

    def tearDown(self) -> None:
        pygame.quit()

    def test_keyboard_activation_toggles_state_and_invokes_callback(self) -> None:
        states = []
        toggle = self.root.add(ToggleControl("tog", Rect(20, 20, 80, 30), "On", "Off", pushed=False, on_toggle=lambda state: states.append(state)))
        toggle.set_tab_index(0)
        self.app.focus.set_focus(toggle)

        consumed_return = self.app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RETURN}))
        consumed_space = self.app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_SPACE}))

        self.assertTrue(consumed_return)
        self.assertTrue(consumed_space)
        self.assertFalse(toggle.pushed)
        self.assertEqual(states, [True, False])

    def test_keyboard_activation_ignored_when_disabled(self) -> None:
        states = []
        toggle = self.root.add(ToggleControl("tog", Rect(20, 20, 80, 30), "On", "Off", pushed=False, on_toggle=lambda state: states.append(state)))
        toggle.set_tab_index(0)
        self.app.focus.set_focus(toggle)
        toggle.enabled = False

        consumed = self.app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RETURN}))

        self.assertFalse(consumed)
        self.assertFalse(toggle.pushed)
        self.assertEqual(states, [])


if __name__ == "__main__":
    unittest.main()
