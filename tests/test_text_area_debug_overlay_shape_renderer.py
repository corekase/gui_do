"""Tests for TextAreaControl, DebugOverlay, and ShapeRenderer."""
import unittest

import pygame
from pygame import Rect

from gui_do.controls.input.text_area_control import TextAreaControl
from gui_do.graphics.debug_overlay import DebugOverlay
from gui_do.graphics.shape_renderer import ShapeRenderer

pygame.init()
pygame.display.set_mode((1, 1))  # needed for Surface.convert_alpha in other tests


# ===========================================================================
# TextAreaControl
# ===========================================================================


class TestTextAreaControlInitial(unittest.TestCase):
    def test_value_stored(self):
        ta = TextAreaControl("ta", Rect(0, 0, 400, 200), value="Hello")
        self.assertEqual("Hello", ta.value)

    def test_empty_value_default(self):
        ta = TextAreaControl("ta", Rect(0, 0, 400, 200))
        self.assertEqual("", ta.value)

    def test_placeholder_stored(self):
        ta = TextAreaControl("ta", Rect(0, 0, 400, 200), placeholder="Enter text")
        self.assertEqual("Enter text", ta._placeholder)

    def test_read_only_false_by_default(self):
        ta = TextAreaControl("ta", Rect(0, 0, 400, 200))
        self.assertFalse(ta.read_only)

    def test_read_only_true_stored(self):
        ta = TextAreaControl("ta", Rect(0, 0, 400, 200), read_only=True)
        self.assertTrue(ta.read_only)

    def test_max_length_none_by_default(self):
        ta = TextAreaControl("ta", Rect(0, 0, 400, 200))
        self.assertIsNone(ta._max_length)

    def test_cursor_pos_at_end_of_value(self):
        ta = TextAreaControl("ta", Rect(0, 0, 400, 200), value="abc")
        self.assertEqual(3, ta.cursor_pos)

    def test_tab_index_zero(self):
        ta = TextAreaControl("ta", Rect(0, 0, 400, 200))
        self.assertEqual(0, ta.tab_index)

    def test_accepts_focus(self):
        ta = TextAreaControl("ta", Rect(0, 0, 400, 200))
        self.assertTrue(ta.accepts_focus())

    def test_accepts_mouse_focus(self):
        ta = TextAreaControl("ta", Rect(0, 0, 400, 200))
        self.assertTrue(ta.accepts_mouse_focus())


class TestTextAreaControlSetValue(unittest.TestCase):
    def test_set_value(self):
        ta = TextAreaControl("ta", Rect(0, 0, 400, 200))
        ta.set_value("world")
        self.assertEqual("world", ta.value)

    def test_set_value_no_callback(self):
        received = []
        ta = TextAreaControl("ta", Rect(0, 0, 400, 200),
                             on_change=lambda v: received.append(v))
        ta.set_value("test")
        self.assertEqual([], received)

    def test_set_value_moves_cursor_to_end(self):
        ta = TextAreaControl("ta", Rect(0, 0, 400, 200))
        ta.set_value("abcde")
        self.assertEqual(5, ta.cursor_pos)

    def test_set_value_respects_max_length(self):
        ta = TextAreaControl("ta", Rect(0, 0, 400, 200), max_length=4)
        ta.set_value("hello")
        self.assertEqual("hell", ta.value)

    def test_value_setter(self):
        ta = TextAreaControl("ta", Rect(0, 0, 400, 200))
        ta.value = "via setter"
        self.assertEqual("via setter", ta.value)

    def test_read_only_setter(self):
        ta = TextAreaControl("ta", Rect(0, 0, 400, 200))
        ta.read_only = True
        self.assertTrue(ta.read_only)


class TestTextAreaControlSelectAll(unittest.TestCase):
    def test_select_all_sets_anchors(self):
        ta = TextAreaControl("ta", Rect(0, 0, 400, 200), value="hello")
        ta.select_all()
        self.assertEqual(0, ta._sel_anchor)
        self.assertEqual(5, ta._sel_active)

    def test_selection_range_no_selection(self):
        ta = TextAreaControl("ta", Rect(0, 0, 400, 200), value="hello")
        start, end = ta.selection_range
        self.assertEqual(start, end)

    def test_selection_range_with_selection(self):
        ta = TextAreaControl("ta", Rect(0, 0, 400, 200), value="hello")
        ta.select_all()
        start, end = ta.selection_range
        self.assertEqual(0, start)
        self.assertEqual(5, end)


# ===========================================================================
# DebugOverlay
# ===========================================================================


class TestDebugOverlayInitial(unittest.TestCase):
    def test_disabled_by_default(self):
        db = DebugOverlay()
        self.assertFalse(db.enabled)

    def test_show_rects_default_true(self):
        db = DebugOverlay()
        self.assertTrue(db.show_rects)

    def test_show_fps_default_true(self):
        db = DebugOverlay()
        self.assertTrue(db.show_fps)

    def test_show_event_log_default_true(self):
        db = DebugOverlay()
        self.assertTrue(db.show_event_log)

    def test_show_roles_default_false(self):
        db = DebugOverlay()
        self.assertFalse(db.show_roles)

    def test_event_log_empty_initially(self):
        db = DebugOverlay()
        self.assertEqual(0, len(db._event_log))


class TestDebugOverlayToggle(unittest.TestCase):
    def test_toggle_enables(self):
        db = DebugOverlay()
        result = db.toggle()
        self.assertTrue(result)
        self.assertTrue(db.enabled)

    def test_toggle_disables(self):
        db = DebugOverlay()
        db.enabled = True
        result = db.toggle()
        self.assertFalse(result)
        self.assertFalse(db.enabled)


class TestDebugOverlayEventLog(unittest.TestCase):
    def test_log_event_appends(self):
        db = DebugOverlay()
        db.log_event("MOUSE_MOTION")
        self.assertEqual(1, len(db._event_log))
        self.assertEqual("MOUSE_MOTION", db._event_log[0])

    def test_log_event_multiple(self):
        db = DebugOverlay()
        db.log_event("A")
        db.log_event("B")
        db.log_event("C")
        self.assertEqual(3, len(db._event_log))

    def test_log_event_respects_max(self):
        db = DebugOverlay(max_event_log=2)
        db.log_event("A")
        db.log_event("B")
        db.log_event("C")  # A is evicted
        self.assertEqual(2, len(db._event_log))
        self.assertNotIn("A", db._event_log)

    def test_clear_event_log(self):
        db = DebugOverlay()
        db.log_event("X")
        db.log_event("Y")
        db.clear_event_log()
        self.assertEqual(0, len(db._event_log))


class TestDebugOverlayFeedDirty(unittest.TestCase):
    def test_feed_dirty_rects(self):
        db = DebugOverlay()
        rects = [Rect(0, 0, 100, 100), Rect(50, 50, 80, 80)]
        db.feed_dirty_rects(rects)
        self.assertEqual(2, len(db._dirty_flash))

    def test_feed_dirty_rects_copies(self):
        db = DebugOverlay()
        r = Rect(0, 0, 100, 100)
        db.feed_dirty_rects([r])
        r.x = 999
        self.assertEqual(0, db._dirty_flash[0].x)  # copy, not reference


# ===========================================================================
# ShapeRenderer — static method smoke tests
# (We just verify the methods run without error on a valid surface)
# ===========================================================================


class TestShapeRenderer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1))
        cls.surf = pygame.Surface((200, 200))

    def test_rounded_rect_filled(self):
        ShapeRenderer.rounded_rect(self.surf, (255, 0, 0), Rect(10, 10, 80, 40), radius=8)

    def test_rounded_rect_outline(self):
        ShapeRenderer.rounded_rect(self.surf, (0, 255, 0), Rect(10, 10, 80, 40), radius=4, width=2)

    def test_rounded_rect_zero_radius(self):
        ShapeRenderer.rounded_rect(self.surf, (0, 0, 255), Rect(10, 10, 80, 40), radius=0)

    def test_pill(self):
        ShapeRenderer.pill(self.surf, (200, 100, 50), Rect(10, 10, 100, 30))

    def test_gradient_rect_vertical(self):
        ShapeRenderer.gradient_rect(self.surf, Rect(0, 0, 50, 50), (0, 0, 0), (255, 255, 255))

    def test_gradient_rect_horizontal(self):
        ShapeRenderer.gradient_rect(self.surf, Rect(0, 0, 50, 50),
                                    (0, 0, 0), (255, 255, 255), horizontal=True)

    def test_gradient_rect_empty(self):
        # Should silently skip
        ShapeRenderer.gradient_rect(self.surf, Rect(0, 0, 0, 0), (0, 0, 0), (255, 255, 255))

    def test_drop_shadow(self):
        ShapeRenderer.drop_shadow(self.surf, Rect(20, 20, 80, 60))

    def test_check_mark(self):
        ShapeRenderer.check_mark(self.surf, Rect(4, 4, 16, 16), (80, 200, 80))

    def test_cross_mark(self):
        ShapeRenderer.cross_mark(self.surf, Rect(4, 4, 16, 16), (200, 80, 80))

    def test_chevron_right(self):
        ShapeRenderer.chevron(self.surf, Rect(10, 10, 20, 20), "right", (255, 255, 0))

    def test_chevron_left(self):
        ShapeRenderer.chevron(self.surf, Rect(10, 10, 20, 20), "left", (255, 255, 0))

    def test_chevron_up(self):
        ShapeRenderer.chevron(self.surf, Rect(10, 10, 20, 20), "up", (255, 255, 0))

    def test_chevron_down(self):
        ShapeRenderer.chevron(self.surf, Rect(10, 10, 20, 20), "down", (255, 255, 0))

    def test_separator_horizontal(self):
        ShapeRenderer.separator(self.surf, Rect(0, 50, 200, 1), (180, 180, 180))

    def test_separator_vertical(self):
        ShapeRenderer.separator(self.surf, Rect(50, 0, 1, 200), (180, 180, 180), horizontal=False)

    def test_progress_arc_full(self):
        ShapeRenderer.progress_arc(self.surf, (100, 100), 30, 1.0, (0, 200, 255))

    def test_progress_arc_empty(self):
        ShapeRenderer.progress_arc(self.surf, (100, 100), 30, 0.0, (0, 200, 255))

    def test_dotted_border(self):
        ShapeRenderer.dotted_border(self.surf, Rect(5, 5, 100, 60), (200, 200, 200))


if __name__ == "__main__":
    unittest.main()
