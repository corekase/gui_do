"""Tests for TabControl, ScrollViewControl, ArrowBoxControl, FrameControl."""
import unittest

import pygame
from pygame import Rect

from gui_do.controls.data.tab_control import TabControl, TabItem
from gui_do.controls.composite.scroll_view_control import ScrollViewControl
from gui_do.controls.display.arrow_box_control import ArrowBoxControl
from gui_do.controls.display.frame_control import FrameControl
from gui_do.controls.display.label_control import LabelControl

pygame.init()


# ---------------------------------------------------------------------------
# Helper: minimal UiNode stub for content
# ---------------------------------------------------------------------------

def _label(cid="lbl", w=200, h=24):
    return LabelControl(cid, Rect(0, 0, w, h), cid)


# ===========================================================================
# TabControl
# ===========================================================================


class TestTabControlInitial(unittest.TestCase):
    def test_empty_selected_key_none(self):
        tc = TabControl("tc", Rect(0, 0, 400, 300))
        self.assertIsNone(tc.selected_key)

    def test_first_item_selected_by_default(self):
        tc = TabControl("tc", Rect(0, 0, 400, 300), items=[
            TabItem("a", "Alpha"),
            TabItem("b", "Beta"),
        ])
        self.assertEqual("a", tc.selected_key)

    def test_selected_key_overrides_default(self):
        tc = TabControl("tc", Rect(0, 0, 400, 300), items=[
            TabItem("a", "Alpha"),
            TabItem("b", "Beta"),
        ], selected_key="b")
        self.assertEqual("b", tc.selected_key)

    def test_invalid_selected_key_falls_back_to_first(self):
        tc = TabControl("tc", Rect(0, 0, 400, 300), items=[
            TabItem("a", "Alpha"),
        ], selected_key="missing")
        self.assertEqual("a", tc.selected_key)

    def test_items_returns_copy(self):
        items = [TabItem("a", "Alpha"), TabItem("b", "Beta")]
        tc = TabControl("tc", Rect(0, 0, 400, 300), items=items)
        copy = tc.items()
        copy.clear()
        self.assertEqual(2, len(tc.items()))

    def test_tab_index_zero(self):
        tc = TabControl("tc", Rect(0, 0, 400, 300))
        self.assertEqual(0, tc.tab_index)

    def test_accepts_focus(self):
        tc = TabControl("tc", Rect(0, 0, 400, 300))
        self.assertTrue(tc.accepts_focus())


class TestTabControlSelect(unittest.TestCase):
    def setUp(self):
        self.received = []
        self.tc = TabControl(
            "tc", Rect(0, 0, 400, 300),
            items=[TabItem("a", "Alpha"), TabItem("b", "Beta"), TabItem("c", "Gamma", enabled=False)],
            on_change=lambda k: self.received.append(k),
        )

    def test_select_valid_key_returns_true(self):
        self.assertTrue(self.tc.select("b"))

    def test_select_valid_key_updates_selected(self):
        self.tc.select("b")
        self.assertEqual("b", self.tc.selected_key)

    def test_select_fires_on_change(self):
        self.tc.select("b")
        self.assertEqual(["b"], self.received)

    def test_select_same_key_no_callback(self):
        self.tc.select("a")  # already selected
        self.assertEqual([], self.received)

    def test_select_unknown_key_returns_false(self):
        self.assertFalse(self.tc.select("zzz"))

    def test_select_disabled_tab_returns_false(self):
        self.assertFalse(self.tc.select("c"))


class TestTabControlAddRemove(unittest.TestCase):
    def test_add_item_appended(self):
        tc = TabControl("tc", Rect(0, 0, 400, 300))
        tc.add_item(TabItem("x", "X"))
        self.assertEqual(1, len(tc.items()))
        self.assertEqual("x", tc.selected_key)

    def test_add_item_second_no_change_to_selected(self):
        tc = TabControl("tc", Rect(0, 0, 400, 300), items=[TabItem("a", "A")])
        tc.add_item(TabItem("b", "B"))
        self.assertEqual("a", tc.selected_key)

    def test_remove_item_returns_true(self):
        tc = TabControl("tc", Rect(0, 0, 400, 300), items=[TabItem("a", "A"), TabItem("b", "B")])
        self.assertTrue(tc.remove_item("a"))

    def test_remove_item_missing_returns_false(self):
        tc = TabControl("tc", Rect(0, 0, 400, 300), items=[TabItem("a", "A")])
        self.assertFalse(tc.remove_item("zzz"))

    def test_remove_selected_advances_to_next(self):
        received = []
        tc = TabControl("tc", Rect(0, 0, 400, 300),
                        items=[TabItem("a", "A"), TabItem("b", "B")],
                        on_change=lambda k: received.append(k))
        tc.remove_item("a")
        self.assertEqual("b", tc.selected_key)

    def test_remove_only_item_selected_none(self):
        tc = TabControl("tc", Rect(0, 0, 400, 300), items=[TabItem("a", "A")])
        tc.remove_item("a")
        self.assertIsNone(tc.selected_key)

    def test_remove_non_selected_tab_keeps_selection(self):
        tc = TabControl("tc", Rect(0, 0, 400, 300),
                        items=[TabItem("a", "A"), TabItem("b", "B")])
        tc.remove_item("b")
        self.assertEqual("a", tc.selected_key)


# ===========================================================================
# ScrollViewControl
# ===========================================================================


class TestScrollViewControlInitial(unittest.TestCase):
    def test_initial_scroll_zero(self):
        sv = ScrollViewControl("sv", Rect(0, 0, 400, 300))
        self.assertEqual(0, sv.scroll_x)
        self.assertEqual(0, sv.scroll_y)

    def test_scroll_y_enabled_by_default(self):
        sv = ScrollViewControl("sv", Rect(0, 0, 400, 300))
        self.assertTrue(sv._scroll_y_enabled)

    def test_scroll_x_disabled_by_default(self):
        sv = ScrollViewControl("sv", Rect(0, 0, 400, 300))
        self.assertFalse(sv._scroll_x_enabled)

    def test_explicit_scroll_x_enabled(self):
        sv = ScrollViewControl("sv", Rect(0, 0, 400, 300), scroll_x=True)
        self.assertTrue(sv._scroll_x_enabled)

    def test_children_empty_initially(self):
        sv = ScrollViewControl("sv", Rect(0, 0, 400, 300))
        self.assertEqual([], sv.children)

    def test_initial_content_size(self):
        sv = ScrollViewControl("sv", Rect(0, 0, 400, 300), content_width=800, content_height=600)
        self.assertEqual(800, sv._content_width)
        self.assertEqual(600, sv._content_height)


class TestScrollViewControlAdd(unittest.TestCase):
    def setUp(self):
        self.sv = ScrollViewControl("sv", Rect(0, 0, 400, 300))

    def test_add_returns_child(self):
        child = _label()
        result = self.sv.add(child, 0, 0)
        self.assertIs(child, result)

    def test_add_increments_children(self):
        self.sv.add(_label("a"), 0, 0)
        self.sv.add(_label("b"), 0, 30)
        self.assertEqual(2, len(self.sv.children))

    def test_add_expands_content_width(self):
        self.sv.add(_label(w=500, h=24), 0, 0)
        self.assertGreaterEqual(self.sv._content_width, 500)

    def test_add_expands_content_height(self):
        self.sv.add(_label(w=200, h=24), 0, 400)
        self.assertGreaterEqual(self.sv._content_height, 424)

    def test_add_sets_child_parent(self):
        child = _label()
        self.sv.add(child)
        self.assertIs(self.sv, child.parent)


class TestScrollViewControlRemove(unittest.TestCase):
    def test_remove_returns_true(self):
        sv = ScrollViewControl("sv", Rect(0, 0, 400, 300))
        child = _label()
        sv.add(child)
        self.assertTrue(sv.remove(child))

    def test_remove_removes_child(self):
        sv = ScrollViewControl("sv", Rect(0, 0, 400, 300))
        child = _label()
        sv.add(child)
        sv.remove(child)
        self.assertEqual(0, len(sv.children))

    def test_remove_clears_parent(self):
        sv = ScrollViewControl("sv", Rect(0, 0, 400, 300))
        child = _label()
        sv.add(child)
        sv.remove(child)
        self.assertIsNone(child.parent)

    def test_remove_missing_returns_false(self):
        sv = ScrollViewControl("sv", Rect(0, 0, 400, 300))
        self.assertFalse(sv.remove(_label()))


class TestScrollViewControlSetScroll(unittest.TestCase):
    def setUp(self):
        self.sv = ScrollViewControl("sv", Rect(0, 0, 400, 300),
                                    content_width=1000, content_height=800,
                                    scroll_x=True, scroll_y=True)

    def test_set_scroll_y(self):
        self.sv.set_scroll(y=100)
        self.assertEqual(100, self.sv.scroll_y)

    def test_set_scroll_x(self):
        self.sv.set_scroll(x=50)
        self.assertEqual(50, self.sv.scroll_x)

    def test_set_scroll_clamped_high(self):
        self.sv.set_scroll(y=10000)
        self.assertLessEqual(self.sv.scroll_y, self.sv._content_height)

    def test_set_scroll_clamped_low(self):
        self.sv.set_scroll(y=-100)
        self.assertEqual(0, self.sv.scroll_y)

    def test_scroll_by_y(self):
        self.sv.set_scroll(y=0)
        self.sv.scroll_by(dy=50)
        self.assertEqual(50, self.sv.scroll_y)

    def test_scroll_by_negative(self):
        self.sv.set_scroll(y=100)
        self.sv.scroll_by(dy=-50)
        self.assertEqual(50, self.sv.scroll_y)

    def test_set_content_size(self):
        self.sv.set_content_size(1200, 900)
        self.assertEqual(1200, self.sv._content_width)
        self.assertEqual(900, self.sv._content_height)


class TestScrollViewControlResize(unittest.TestCase):
    def test_resize_updates_rect(self):
        sv = ScrollViewControl("sv", Rect(0, 0, 400, 300))
        sv.resize(800, 600)
        self.assertEqual(800, sv.rect.width)
        self.assertEqual(600, sv.rect.height)

    def test_set_rect(self):
        sv = ScrollViewControl("sv", Rect(0, 0, 400, 300))
        sv.set_rect(Rect(10, 20, 500, 400))
        self.assertEqual(Rect(10, 20, 500, 400), sv.rect)

    def test_set_pos(self):
        sv = ScrollViewControl("sv", Rect(0, 0, 400, 300))
        sv.set_pos(50, 100)
        self.assertEqual(50, sv.rect.x)
        self.assertEqual(100, sv.rect.y)


# ===========================================================================
# ArrowBoxControl
# ===========================================================================


class TestArrowBoxControlInitial(unittest.TestCase):
    def test_direction_stored(self):
        ab = ArrowBoxControl("ab", Rect(0, 0, 24, 24), direction=90)
        self.assertEqual(90, ab.direction)

    def test_direction_normalised_mod360(self):
        ab = ArrowBoxControl("ab", Rect(0, 0, 24, 24), direction=450)
        self.assertEqual(90, ab.direction)

    def test_repeat_interval_stored(self):
        ab = ArrowBoxControl("ab", Rect(0, 0, 24, 24), direction=0, repeat_interval_seconds=0.2)
        self.assertAlmostEqual(0.2, ab.repeat_interval_seconds)

    def test_on_activate_none_by_default(self):
        ab = ArrowBoxControl("ab", Rect(0, 0, 24, 24), direction=0)
        self.assertIsNone(ab.on_activate)


class TestArrowBoxControlSetOnActivate(unittest.TestCase):
    def test_set_on_activate_callable(self):
        received = []
        ab = ArrowBoxControl("ab", Rect(0, 0, 24, 24), direction=0)
        ab.set_on_activate(lambda: received.append(1))
        ab._invoke()
        self.assertEqual([1], received)

    def test_set_on_activate_none_clears(self):
        received = []
        ab = ArrowBoxControl("ab", Rect(0, 0, 24, 24), direction=0,
                             on_activate=lambda: received.append(1))
        ab.set_on_activate(None)
        ab._invoke()
        self.assertEqual([], received)

    def test_set_on_activate_non_callable_raises(self):
        ab = ArrowBoxControl("ab", Rect(0, 0, 24, 24), direction=0)
        with self.assertRaises(ValueError):
            ab.set_on_activate("bad")

    def test_invoke_click_fires_on_activate(self):
        received = []
        ab = ArrowBoxControl("ab", Rect(0, 0, 24, 24), direction=0,
                             on_activate=lambda: received.append(1))
        ab._invoke_click()
        self.assertEqual([1], received)

    def test_initial_on_activate_fires(self):
        received = []
        ab = ArrowBoxControl("ab", Rect(0, 0, 24, 24), direction=180,
                             on_activate=lambda: received.append("left"))
        ab._invoke()
        self.assertEqual(["left"], received)


# ===========================================================================
# FrameControl
# ===========================================================================


class TestFrameControlInitial(unittest.TestCase):
    def test_default_border_width_one(self):
        fc = FrameControl("fc", Rect(0, 0, 200, 100))
        self.assertEqual(1, fc.border_width)

    def test_initial_border_width_stored(self):
        fc = FrameControl("fc", Rect(0, 0, 200, 100), border_width=3)
        self.assertEqual(3, fc.border_width)

    def test_border_width_clamped_to_one(self):
        fc = FrameControl("fc", Rect(0, 0, 200, 100), border_width=0)
        self.assertEqual(1, fc.border_width)

    def test_rect_stored(self):
        r = Rect(10, 20, 300, 150)
        fc = FrameControl("fc", r)
        self.assertEqual(r, fc.rect)


class TestFrameControlBorderWidthSetter(unittest.TestCase):
    def test_set_border_width(self):
        fc = FrameControl("fc", Rect(0, 0, 200, 100))
        fc.border_width = 4
        self.assertEqual(4, fc.border_width)

    def test_set_border_width_clamped_to_one(self):
        fc = FrameControl("fc", Rect(0, 0, 200, 100))
        fc.border_width = 0
        self.assertEqual(1, fc.border_width)

    def test_set_same_border_width_idempotent(self):
        fc = FrameControl("fc", Rect(0, 0, 200, 100), border_width=2)
        fc.border_width = 2   # should not raise


if __name__ == "__main__":
    unittest.main()
