import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
from pygame import Rect

from gui import ArrowBoxControl, GuiApplication, PanelControl


class ArrowBoxRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()
        self.surface = pygame.display.set_mode((240, 160))
        self.app = GuiApplication(self.surface)
        self.root = self.app.add(PanelControl("root", Rect(0, 0, 240, 160)))

    def tearDown(self) -> None:
        pygame.quit()

    def test_keyboard_activation_when_focused(self) -> None:
        fired = []
        control = self.root.add(ArrowBoxControl("arr", Rect(20, 20, 40, 30), 0, on_activate=lambda: fired.append(True), repeat_interval_seconds=0.05))
        control.set_tab_index(0)
        self.app.focus.set_focus(control)

        consumed_return = self.app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RETURN}))
        consumed_space = self.app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_SPACE}))

        self.assertTrue(consumed_return)
        self.assertTrue(consumed_space)
        self.assertEqual(len(fired), 2)

    def test_repeat_cancels_when_pointer_leaves_while_pressed(self) -> None:
        fired = []
        control = self.root.add(ArrowBoxControl("arr", Rect(20, 20, 40, 30), 0, on_activate=lambda: fired.append(True), repeat_interval_seconds=0.05))

        self.app.process_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": (30, 30), "button": 1}))
        self.assertEqual(len(fired), 1)
        self.assertIn(control._timer_id, self.app.timers._timers)

        self.app.process_event(
            pygame.event.Event(
                pygame.MOUSEMOTION,
                {"pos": (200, 120), "rel": (5, 0), "buttons": (1, 0, 0)},
            )
        )
        self.assertNotIn(control._timer_id, self.app.timers._timers)

        self.app.update(0.2)
        self.assertEqual(len(fired), 1)


if __name__ == "__main__":
    unittest.main()
