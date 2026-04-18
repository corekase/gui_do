import unittest
from types import SimpleNamespace

import pygame
from pygame import Rect
from pygame.locals import MOUSEBUTTONDOWN

from gui.utility.events import InteractiveState, Orientation
from gui.widgets.canvas import Canvas
from gui.widgets.scrollbar import Scrollbar
from gui.widgets.toggle import Toggle


class ToggleWidgetTests(unittest.TestCase):
    def _build_toggle(self, pushed: bool = False):
        toggle = Toggle.__new__(Toggle)
        toggle._pushed = pushed
        toggle.state = InteractiveState.Idle
        toggle.draw_rect = Rect(0, 0, 20, 10)
        toggle.hit_rect = None
        gui = SimpleNamespace()
        gui.get_mouse_pos = lambda: (5, 5)
        gui.convert_to_window = lambda point, _window: point
        toggle.gui = gui
        return toggle

    def test_left_click_toggles_pushed_state_when_hovered(self) -> None:
        toggle = self._build_toggle(False)

        event = pygame.event.Event(MOUSEBUTTONDOWN, {"button": 1})
        activated = Toggle.handle_event(toggle, event, None)

        self.assertTrue(activated)
        self.assertTrue(toggle.pushed)

        activated = Toggle.handle_event(toggle, event, None)

        self.assertTrue(activated)
        self.assertFalse(toggle.pushed)

    def test_non_left_click_does_not_toggle(self) -> None:
        toggle = self._build_toggle(False)

        event = pygame.event.Event(MOUSEBUTTONDOWN, {"button": 3})
        activated = Toggle.handle_event(toggle, event, None)

        self.assertFalse(activated)
        self.assertFalse(toggle.pushed)


class ScrollbarWidgetTests(unittest.TestCase):
    def test_increment_and_decrement_are_clamped_to_valid_range(self) -> None:
        scrollbar = Scrollbar.__new__(Scrollbar)
        scrollbar._hit = False
        scrollbar._total_range = 10
        scrollbar._bar_size = 4
        scrollbar._inc_size = 5

        scrollbar._start_pos = 8
        Scrollbar.increment(scrollbar)
        self.assertEqual(scrollbar._start_pos, 6)
        self.assertTrue(scrollbar._hit)

        scrollbar._start_pos = 1
        Scrollbar.decrement(scrollbar)
        self.assertEqual(scrollbar._start_pos, 0)
        self.assertTrue(scrollbar._hit)

    def test_position_moves_all_scrollbar_geometry_and_arrows(self) -> None:
        arrow1 = SimpleNamespace(draw_rect=Rect(20, 20, 4, 4), position=(20, 20))
        arrow2 = SimpleNamespace(draw_rect=Rect(30, 20, 4, 4), position=(30, 20))

        scrollbar = Scrollbar.__new__(Scrollbar)
        scrollbar.draw_rect = Rect(10, 10, 20, 8)
        scrollbar.hit_rect = None
        scrollbar._overall_rect = Rect(10, 10, 40, 8)
        scrollbar._graphic_rect = Rect(12, 12, 16, 4)
        scrollbar._increment_rect = Rect(30, 10, 8, 8)
        scrollbar._decrement_rect = Rect(10, 10, 8, 8)
        scrollbar._registered = [arrow1, arrow2]

        scrollbar.position = (15, 20)

        self.assertEqual(scrollbar.draw_rect.topleft, (15, 20))
        self.assertEqual(scrollbar._overall_rect.topleft, (15, 20))
        self.assertEqual(scrollbar._graphic_rect.topleft, (17, 22))
        self.assertEqual(scrollbar._increment_rect.topleft, (35, 20))
        self.assertEqual(scrollbar._decrement_rect.topleft, (15, 20))
        self.assertEqual(arrow1.position, (25, 30))
        self.assertEqual(arrow2.position, (35, 30))

    def test_handle_area_respects_orientation(self) -> None:
        scrollbar = Scrollbar.__new__(Scrollbar)
        scrollbar._graphic_rect = Rect(100, 200, 50, 20)
        scrollbar._total_range = 100
        scrollbar._start_pos = 10
        scrollbar._bar_size = 20

        scrollbar._horizontal = Orientation.Horizontal
        area = Scrollbar._handle_area(scrollbar)
        self.assertEqual(area, Rect(105, 200, 10, 20))

        scrollbar._horizontal = Orientation.Vertical
        area = Scrollbar._handle_area(scrollbar)
        self.assertEqual(area, Rect(100, 202, 50, 4))


class CanvasFocusedTests(unittest.TestCase):
    def test_focused_uses_converted_mouse_position(self) -> None:
        canvas = Canvas.__new__(Canvas)
        canvas.draw_rect = Rect(0, 0, 10, 10)
        canvas.window = None

        gui = SimpleNamespace()
        mouse = {"pos": (5, 5)}
        gui.get_mouse_pos = lambda: mouse["pos"]
        gui.convert_to_window = lambda point, _window: point
        canvas.gui = gui

        self.assertTrue(Canvas.focused(canvas))

        mouse["pos"] = (30, 30)
        self.assertFalse(Canvas.focused(canvas))


if __name__ == "__main__":
    unittest.main()
