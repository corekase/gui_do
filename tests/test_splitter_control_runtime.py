"""Tests for SplitterControl — draggable two-pane divider."""
import unittest
from unittest.mock import MagicMock

import pygame
from pygame import Rect

from gui_do.controls.splitter_control import SplitterControl
from gui_do.layout.layout_axis import LayoutAxis


def _splitter(**kwargs) -> SplitterControl:
    return SplitterControl("split", Rect(0, 0, 400, 300), **kwargs)


class TestSplitterDefaults(unittest.TestCase):
    def test_default_axis_horizontal(self) -> None:
        s = _splitter()
        self.assertEqual(s.axis, LayoutAxis.HORIZONTAL)
        self.assertTrue(s.is_horizontal)

    def test_default_ratio(self) -> None:
        s = _splitter()
        self.assertAlmostEqual(s.ratio, 0.5)

    def test_vertical_axis(self) -> None:
        s = _splitter(axis=LayoutAxis.VERTICAL)
        self.assertFalse(s.is_horizontal)


class TestSplitterPaneRects(unittest.TestCase):
    def test_pane_a_rect_horizontal(self) -> None:
        s = _splitter(ratio=0.5)
        a = s.pane_a_rect
        b = s.pane_b_rect
        dr = s.divider_rect
        self.assertEqual(a.x, s.rect.x)
        # A right edge == divider left edge
        self.assertEqual(a.right, dr.x)
        # B left edge == divider right edge
        self.assertEqual(b.x, dr.right)
        self.assertEqual(b.right, s.rect.right)

    def test_pane_a_rect_vertical(self) -> None:
        s = _splitter(axis=LayoutAxis.VERTICAL, ratio=0.4)
        a = s.pane_a_rect
        b = s.pane_b_rect
        dr = s.divider_rect
        self.assertEqual(a.y, s.rect.y)
        self.assertEqual(a.bottom, dr.y)
        self.assertEqual(b.y, dr.bottom)
        self.assertEqual(b.bottom, s.rect.bottom)

    def test_rects_cover_full_area(self) -> None:
        s = _splitter(ratio=0.5)
        a = s.pane_a_rect
        b = s.pane_b_rect
        dr = s.divider_rect
        total = a.width + dr.width + b.width
        self.assertEqual(total, s.rect.width)

    def test_divider_rect_horizontal(self) -> None:
        s = _splitter(ratio=0.5)
        dr = s.divider_rect
        self.assertEqual(dr.y, s.rect.y)
        self.assertEqual(dr.height, s.rect.height)

    def test_divider_rect_vertical(self) -> None:
        s = _splitter(axis=LayoutAxis.VERTICAL, ratio=0.5)
        dr = s.divider_rect
        self.assertEqual(dr.x, s.rect.x)
        self.assertEqual(dr.width, s.rect.width)


class TestSplitterRatioClamping(unittest.TestCase):
    def test_ratio_clamped_below_zero(self) -> None:
        s = _splitter()
        s.ratio = -1.0
        self.assertGreater(s.ratio, 0.0)

    def test_ratio_clamped_above_one(self) -> None:
        s = _splitter()
        s.ratio = 2.0
        self.assertLess(s.ratio, 1.0)

    def test_min_pane_size_enforced(self) -> None:
        s = _splitter(min_pane_size=80)
        s.ratio = 0.0
        a = s.pane_a_rect
        self.assertGreaterEqual(a.width, 80)
        s.ratio = 1.0
        b = s.pane_b_rect
        self.assertGreaterEqual(b.width, 80)


class TestSplitterAcceptsFocus(unittest.TestCase):
    def test_accepts_focus_when_enabled(self) -> None:
        s = _splitter()
        self.assertTrue(s.accepts_focus())

    def test_not_accepts_focus_when_disabled(self) -> None:
        s = _splitter()
        s.enabled = False
        self.assertFalse(s.accepts_focus())


class TestSplitterEventHandling(unittest.TestCase):
    def _evt(self, kind, **kwargs):
        evt = MagicMock()
        evt.kind = kind
        for k, v in kwargs.items():
            setattr(evt, k, v)
        return evt

    def _app(self):
        app = MagicMock()
        app.capture_pointer = MagicMock()
        app.release_pointer = MagicMock()
        return app

    def test_mouse_down_on_divider_starts_drag(self) -> None:
        from gui_do.core.gui_event import EventType
        s = _splitter(ratio=0.5)
        dr = s.divider_rect
        pos = dr.center
        evt = self._evt(EventType.MOUSE_BUTTON_DOWN, button=1, pos=pos)
        s.handle_event(evt, self._app())
        self.assertTrue(s._dragging)

    def test_mouse_down_outside_divider_no_drag(self) -> None:
        from gui_do.core.gui_event import EventType
        s = _splitter(ratio=0.5)
        # Click far left of divider
        pos = (5, s.rect.centery)
        evt = self._evt(EventType.MOUSE_BUTTON_DOWN, button=1, pos=pos)
        consumed = s.handle_event(evt, self._app())
        self.assertFalse(s._dragging)
        self.assertFalse(consumed)

    def test_drag_motion_changes_ratio(self) -> None:
        from gui_do.core.gui_event import EventType
        s = _splitter(ratio=0.5)
        dr = s.divider_rect
        app = self._app()
        # Start drag
        evt_down = self._evt(EventType.MOUSE_BUTTON_DOWN, button=1, pos=dr.center)
        s.handle_event(evt_down, app)
        # Drag right
        new_pos = (dr.centerx + 60, dr.centery)
        evt_motion = self._evt(EventType.MOUSE_MOTION, pos=new_pos)
        s.handle_event(evt_motion, app)
        self.assertGreater(s.ratio, 0.5)

    def test_drag_end_on_mouse_up(self) -> None:
        from gui_do.core.gui_event import EventType
        s = _splitter(ratio=0.5)
        dr = s.divider_rect
        app = self._app()
        evt_down = self._evt(EventType.MOUSE_BUTTON_DOWN, button=1, pos=dr.center)
        s.handle_event(evt_down, app)
        evt_up = self._evt(EventType.MOUSE_BUTTON_UP, button=1, pos=dr.center)
        s.handle_event(evt_up, app)
        self.assertFalse(s._dragging)

    def test_on_ratio_changed_callback_fired(self) -> None:
        from gui_do.core.gui_event import EventType
        ratios = []
        s = _splitter(ratio=0.5, on_ratio_changed=ratios.append)
        dr = s.divider_rect
        app = self._app()
        evt_down = self._evt(EventType.MOUSE_BUTTON_DOWN, button=1, pos=dr.center)
        s.handle_event(evt_down, app)
        new_pos = (dr.centerx + 40, dr.centery)
        evt_motion = self._evt(EventType.MOUSE_MOTION, pos=new_pos)
        s.handle_event(evt_motion, app)
        self.assertTrue(len(ratios) > 0)

    def test_keyboard_left_decreases_ratio(self) -> None:
        from gui_do.core.gui_event import EventType
        s = _splitter(ratio=0.5)
        s._focused = True
        initial = s.ratio
        evt = self._evt(EventType.KEY_DOWN, key=pygame.K_LEFT, mod=0)
        s.handle_event(evt, self._app())
        self.assertLess(s.ratio, initial)

    def test_keyboard_right_increases_ratio(self) -> None:
        from gui_do.core.gui_event import EventType
        s = _splitter(ratio=0.5)
        s._focused = True
        initial = s.ratio
        evt = self._evt(EventType.KEY_DOWN, key=pygame.K_RIGHT, mod=0)
        s.handle_event(evt, self._app())
        self.assertGreater(s.ratio, initial)

    def test_vertical_keyboard_up_decreases_ratio(self) -> None:
        from gui_do.core.gui_event import EventType
        s = _splitter(axis=LayoutAxis.VERTICAL, ratio=0.5)
        s._focused = True
        initial = s.ratio
        evt = self._evt(EventType.KEY_DOWN, key=pygame.K_UP, mod=0)
        s.handle_event(evt, self._app())
        self.assertLess(s.ratio, initial)

    def test_disabled_splitter_ignores_events(self) -> None:
        from gui_do.core.gui_event import EventType
        s = _splitter(ratio=0.5)
        s.enabled = False
        dr = s.divider_rect
        evt = self._evt(EventType.MOUSE_BUTTON_DOWN, button=1, pos=dr.center)
        consumed = s.handle_event(evt, self._app())
        self.assertFalse(consumed)
        self.assertFalse(s._dragging)


class TestSplitterUpdateNoop(unittest.TestCase):
    def test_update_does_not_raise(self) -> None:
        s = _splitter()
        s.update(0.016)


if __name__ == "__main__":
    unittest.main()
