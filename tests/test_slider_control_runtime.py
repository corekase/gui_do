import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
from pygame import Rect

from gui import GuiApplication, LayoutAxis, PanelControl, SliderControl


class SliderControlRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()
        self.surface = pygame.display.set_mode((260, 180))
        self.app = GuiApplication(self.surface)
        self.root = self.app.add(PanelControl("root", Rect(0, 0, 260, 180)))

    def tearDown(self) -> None:
        pygame.quit()

    def test_horizontal_keyboard_nudges_and_home_end(self) -> None:
        slider = self.root.add(SliderControl("s", Rect(20, 20, 160, 24), LayoutAxis.HORIZONTAL, 0.0, 100.0, 50.0))
        slider.set_tab_index(0)
        self.app.focus.set_focus(slider)

        consumed_left = self.app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_LEFT}))
        consumed_right = self.app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RIGHT}))
        consumed_home = self.app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_HOME}))
        consumed_end = self.app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_END}))

        self.assertTrue(consumed_left)
        self.assertTrue(consumed_right)
        self.assertTrue(consumed_home)
        self.assertTrue(consumed_end)
        self.assertEqual(slider.value, 100.0)

    def test_vertical_keyboard_nudges_with_axis_direction(self) -> None:
        slider = self.root.add(SliderControl("v", Rect(30, 20, 24, 120), LayoutAxis.VERTICAL, 0.0, 10.0, 5.0))
        slider.set_tab_index(0)
        self.app.focus.set_focus(slider)

        self.app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_UP}))
        value_after_up = slider.value
        self.app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_DOWN}))

        self.assertGreater(value_after_up, 5.0)
        self.assertAlmostEqual(slider.value, 5.0)

    def test_keyboard_ignored_when_disabled(self) -> None:
        slider = self.root.add(SliderControl("s", Rect(20, 20, 160, 24), LayoutAxis.HORIZONTAL, 0.0, 100.0, 50.0))
        slider.set_tab_index(0)
        self.app.focus.set_focus(slider)
        slider.enabled = False

        consumed = self.app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RIGHT}))

        self.assertFalse(consumed)
        self.assertEqual(slider.value, 50.0)


if __name__ == "__main__":
    unittest.main()
