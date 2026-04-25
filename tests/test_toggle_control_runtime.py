import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
from pygame import Rect

from gui import GuiApplication, PanelControl, ToggleControl, WindowControl
from gui.core.focus_hint_constants import FOCUS_TRAVERSAL_HINT_TIMEOUT_SECONDS


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

    def test_keyboard_activation_sets_cosmetic_focus_armed_until_shared_timeout(self) -> None:
        states = []
        toggle = self.root.add(ToggleControl("tog", Rect(20, 20, 80, 30), "On", "Off", pushed=False, on_toggle=lambda s: states.append(s)))
        toggle.set_tab_index(0)
        self.app.focus.set_focus(toggle)

        consumed = self.app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RETURN}))

        self.assertTrue(consumed)
        self.assertEqual(states, [True])
        self.assertTrue(toggle._focus_activation_armed)

        self.app.update(FOCUS_TRAVERSAL_HINT_TIMEOUT_SECONDS - 0.01)
        self.assertTrue(toggle._focus_activation_armed)

        self.app.update(0.02)
        self.assertFalse(toggle._focus_activation_armed)

    def test_keyboard_activation_fires_toggle_and_hint_remains_active(self) -> None:
        states = []
        toggle = self.root.add(ToggleControl("tog", Rect(20, 20, 80, 30), "On", "Off", pushed=False, on_toggle=lambda state: states.append(state)))
        toggle.set_tab_index(0)

        self.app.focus.set_focus(toggle, via_keyboard=True)
        self.assertTrue(self.app.focus_visualizer.has_active_hint())
        consumed = self.app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RETURN}))

        self.assertTrue(consumed)
        self.assertTrue(toggle.pushed)
        self.assertEqual(states, [True])
        # Hint remains active (toggle still focused).
        self.assertTrue(self.app.focus_visualizer.has_active_hint())

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

    def test_space_ignored_when_no_focus_even_with_active_window(self) -> None:
        states = []
        win = self.root.add(WindowControl("w", Rect(10, 10, 220, 130), "Life"))
        toggle = win.add(ToggleControl("life_toggle", Rect(20, 20, 100, 30), "Start", "Stop", pushed=False, on_toggle=lambda state: states.append(state)))
        toggle.set_tab_index(0)
        win.active = True

        self.assertIsNone(self.app.focus.focused_node)
        consumed = self.app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_SPACE}))

        self.assertTrue(consumed)
        self.assertFalse(toggle.pushed)
        self.assertEqual(states, [])
        self.assertIsNone(self.app.focus.focused_node)

    def test_hover_resets_when_reenabled_after_pointer_moves_away_while_disabled(self) -> None:
        toggle = self.root.add(ToggleControl("tog", Rect(20, 20, 80, 30), "On", "Off", pushed=False))

        self.app.process_event(pygame.event.Event(pygame.MOUSEMOTION, {"pos": (30, 30), "rel": (0, 0), "buttons": (0, 0, 0)}))
        self.assertTrue(toggle.hovered)

        toggle.enabled = False
        self.app.process_event(pygame.event.Event(pygame.MOUSEMOTION, {"pos": (200, 120), "rel": (0, 0), "buttons": (0, 0, 0)}))
        toggle.enabled = True

        self.assertFalse(toggle.hovered)


if __name__ == "__main__":
    unittest.main()
