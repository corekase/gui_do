import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
from pygame import Rect

from gui import ButtonControl, GuiApplication, PanelControl, WindowControl


class ButtonControlRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()
        self.surface = pygame.display.set_mode((240, 160))
        self.app = GuiApplication(self.surface)
        self.root = self.app.add(PanelControl("root", Rect(0, 0, 240, 160)))

    def tearDown(self) -> None:
        pygame.quit()

    def test_keyboard_activation_when_focused(self) -> None:
        fired = []
        control = self.root.add(ButtonControl("btn", Rect(20, 20, 80, 30), "B", on_click=lambda: fired.append(True)))
        control.set_tab_index(0)
        self.app.focus.set_focus(control)

        consumed_return = self.app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RETURN}))
        consumed_space = self.app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_SPACE}))

        self.assertTrue(consumed_return)
        self.assertTrue(consumed_space)
        self.assertEqual(len(fired), 2)
        self.assertFalse(control.pressed)

    def test_keyboard_activation_ignored_when_disabled(self) -> None:
        fired = []
        control = self.root.add(ButtonControl("btn", Rect(20, 20, 80, 30), "B", on_click=lambda: fired.append(True)))
        control.set_tab_index(0)
        self.app.focus.set_focus(control)
        control.enabled = False

        consumed = self.app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RETURN}))

        self.assertFalse(consumed)
        self.assertEqual(fired, [])
        self.assertFalse(control.pressed)

    def test_space_does_not_activate_any_button_when_no_focus(self) -> None:
        fired = []
        win = self.root.add(WindowControl("w", Rect(10, 10, 220, 130), "Win"))
        first = win.add(ButtonControl("b1", Rect(20, 30, 80, 30), "1", on_click=lambda: fired.append("first")))
        second = win.add(ButtonControl("b2", Rect(20, 70, 80, 30), "2", on_click=lambda: fired.append("second")))
        first.set_tab_index(0)
        second.set_tab_index(1)
        win.active = True

        self.assertIsNone(self.app.focus.focused_node)
        consumed = self.app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_SPACE}))

        self.assertTrue(consumed)
        self.assertIsNone(self.app.focus.focused_node)
        self.assertEqual(fired, [])


if __name__ == "__main__":
    unittest.main()
