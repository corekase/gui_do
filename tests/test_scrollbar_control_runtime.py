import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
from pygame import Rect

from gui import GuiApplication, LayoutAxis, PanelControl, ScrollbarControl, WindowControl
from gui.core.focus_hint_constants import FOCUS_TRAVERSAL_HINT_TIMEOUT_SECONDS


class ScrollbarControlRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()
        self.surface = pygame.display.set_mode((280, 180))
        self.app = GuiApplication(self.surface)
        self.root = self.app.add(PanelControl("root", Rect(0, 0, 280, 180)))

    def tearDown(self) -> None:
        pygame.quit()

    def test_horizontal_keyboard_step_page_and_bounds(self) -> None:
        bar = self.root.add(
            ScrollbarControl(
                "sb",
                Rect(20, 20, 180, 24),
                LayoutAxis.HORIZONTAL,
                content_size=1000,
                viewport_size=200,
                offset=100,
                step=10,
            )
        )
        bar.set_tab_index(0)
        self.app.focus.set_focus(bar)

        consumed_left = self.app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_LEFT}))
        consumed_right = self.app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RIGHT}))
        consumed_page_down = self.app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_PAGEDOWN}))
        consumed_page_up = self.app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_PAGEUP}))

        self.assertTrue(consumed_left)
        self.assertTrue(consumed_right)
        self.assertTrue(consumed_page_down)
        self.assertTrue(consumed_page_up)
        self.assertGreaterEqual(bar.offset, 0)
        self.assertLessEqual(bar.offset, bar._max_offset())

    def test_vertical_keyboard_direction_and_home_end(self) -> None:
        bar = self.root.add(
            ScrollbarControl(
                "sv",
                Rect(20, 20, 24, 140),
                LayoutAxis.VERTICAL,
                content_size=1000,
                viewport_size=200,
                offset=100,
                step=10,
            )
        )
        bar.set_tab_index(0)
        self.app.focus.set_focus(bar)

        self.app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_DOWN}))
        down_offset = bar.offset
        self.app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_UP}))
        up_offset = bar.offset
        self.app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_HOME}))
        home_offset = bar.offset
        self.app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_END}))

        self.assertGreater(down_offset, 100)
        self.assertLess(up_offset, down_offset)
        self.assertEqual(home_offset, 0)
        self.assertEqual(bar.offset, bar._max_offset())

    def test_keyboard_ignored_when_disabled(self) -> None:
        bar = self.root.add(
            ScrollbarControl(
                "sb",
                Rect(20, 20, 180, 24),
                LayoutAxis.HORIZONTAL,
                content_size=1000,
                viewport_size=200,
                offset=100,
                step=10,
            )
        )
        bar.set_tab_index(0)
        self.app.focus.set_focus(bar)
        bar.enabled = False

        consumed = self.app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RIGHT}))

        self.assertFalse(consumed)
        self.assertEqual(bar.offset, 100)

    def test_keyboard_ignored_when_not_focused(self) -> None:
        bar = self.root.add(
            ScrollbarControl(
                "sb",
                Rect(20, 20, 180, 24),
                LayoutAxis.HORIZONTAL,
                content_size=1000,
                viewport_size=200,
                offset=100,
                step=10,
            )
        )
        bar.set_tab_index(0)

        consumed = self.app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RIGHT}))

        self.assertFalse(consumed)
        self.assertEqual(bar.offset, 100)

    def test_focus_keyboard_activation_sets_handle_armed_until_shared_timeout(self) -> None:
        bar = self.root.add(
            ScrollbarControl(
                "sb",
                Rect(20, 20, 180, 24),
                LayoutAxis.HORIZONTAL,
                content_size=1000,
                viewport_size=200,
                offset=100,
                step=10,
            )
        )
        bar.set_tab_index(0)
        self.app.focus.set_focus(bar)

        consumed = self.app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RETURN}))

        self.assertTrue(consumed)
        self.assertEqual(bar.offset, 100)
        self.assertTrue(bar._focus_activation_armed)
        self.assertFalse(bar.dragging)

        self.app.update(FOCUS_TRAVERSAL_HINT_TIMEOUT_SECONDS - 0.01)
        self.assertTrue(bar._focus_activation_armed)

        self.app.update(0.02)
        self.assertFalse(bar._focus_activation_armed)

    def test_less_more_and_home_end_keyboard_signals_arm_handle_visual(self) -> None:
        bar = self.root.add(
            ScrollbarControl(
                "sb",
                Rect(20, 20, 180, 24),
                LayoutAxis.HORIZONTAL,
                content_size=1000,
                viewport_size=200,
                offset=100,
                step=10,
            )
        )
        bar.set_tab_index(0)
        self.app.focus.set_focus(bar)

        consumed_more = self.app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RIGHT}))
        self.assertTrue(consumed_more)
        self.assertTrue(bar._focus_activation_armed)

        self.app.update(FOCUS_TRAVERSAL_HINT_TIMEOUT_SECONDS + 0.01)
        self.assertFalse(bar._focus_activation_armed)

        consumed_home = self.app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_HOME}))
        consumed_end = self.app.process_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_END}))
        self.assertTrue(consumed_home)
        self.assertTrue(consumed_end)
        self.assertTrue(bar._focus_activation_armed)

    def test_screen_scrollbar_drag_ends_when_pointer_enters_window(self) -> None:
        bar = self.root.add(
            ScrollbarControl(
                "sb",
                Rect(20, 20, 180, 24),
                LayoutAxis.HORIZONTAL,
                content_size=1000,
                viewport_size=200,
                offset=100,
                step=10,
            )
        )
        window = self.root.add(WindowControl("win", Rect(120, 60, 120, 80), "Window"))

        self.app.process_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": bar.handle_rect().center, "button": 1}))

        self.assertTrue(bar.dragging)
        self.assertTrue(self.app.pointer_capture.is_owned_by("sb"))

        self.app.process_event(pygame.event.Event(pygame.MOUSEMOTION, {"pos": window.rect.center, "rel": (20, 20), "buttons": (1, 0, 0)}))

        self.assertFalse(bar.dragging)
        self.assertFalse(self.app.pointer_capture.is_owned_by("sb"))

    def test_window_scrollbar_drag_does_not_end_from_window_entry_rule(self) -> None:
        window = self.root.add(WindowControl("win", Rect(20, 20, 220, 120), "Window"))
        bar = window.add(
            ScrollbarControl(
                "sb",
                Rect(40, 60, 140, 24),
                LayoutAxis.HORIZONTAL,
                content_size=1000,
                viewport_size=200,
                offset=100,
                step=10,
            )
        )

        self.app.process_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": bar.handle_rect().center, "button": 1}))

        self.assertTrue(bar.dragging)
        self.assertTrue(self.app.pointer_capture.is_owned_by("sb"))

        consumed = self.app.process_event(pygame.event.Event(pygame.MOUSEMOTION, {"pos": (bar.rect.centerx + 10, bar.rect.centery), "rel": (10, 0), "buttons": (1, 0, 0)}))

        self.assertTrue(consumed)
        self.assertTrue(bar.dragging)
        self.assertTrue(self.app.pointer_capture.is_owned_by("sb"))


if __name__ == "__main__":
    unittest.main()
