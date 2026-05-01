"""Tests for layout_pass (MeasureContext, ArrangeContext, LayoutRoot) and LayoutManager."""
import unittest

import pygame
from pygame import Rect

from gui_do.layout.layout_pass import MeasureContext, ArrangeContext, LayoutRoot
from gui_do.layout.layout_manager import LayoutManager
from gui_do.layout.layout_axis import LayoutAxis

pygame.init()


# ===========================================================================
# MeasureContext
# ===========================================================================


class TestMeasureContext(unittest.TestCase):
    def test_width_stored(self):
        ctx = MeasureContext(400, 300)
        self.assertEqual(400, ctx.available_width)

    def test_height_stored(self):
        ctx = MeasureContext(400, 300)
        self.assertEqual(300, ctx.available_height)

    def test_available_size_tuple(self):
        ctx = MeasureContext(200, 150)
        self.assertEqual((200, 150), ctx.available_size)

    def test_unconstrained_minus_one(self):
        ctx = MeasureContext(-1, -1)
        self.assertEqual(-1, ctx.available_width)
        self.assertEqual(-1, ctx.available_height)


# ===========================================================================
# ArrangeContext
# ===========================================================================


class TestArrangeContext(unittest.TestCase):
    def test_rect_stored(self):
        r = Rect(10, 20, 300, 200)
        ctx = ArrangeContext(r)
        self.assertEqual(r, ctx.rect)

    def test_rect_is_copy(self):
        r = Rect(10, 20, 300, 200)
        ctx = ArrangeContext(r)
        r.x = 999
        self.assertEqual(10, ctx.rect.x)


# ===========================================================================
# LayoutRoot
# ===========================================================================


class _SimpleLayout:
    """Minimal layout that always returns (100, 50) as preferred size."""
    def __init__(self):
        self.arranged = []
        self.measured = []

    def measure(self, ctx):
        self.measured.append((ctx.available_width, ctx.available_height))
        return (100, 50)

    def arrange(self, ctx):
        self.arranged.append(Rect(ctx.rect))


class TestLayoutRoot(unittest.TestCase):
    def test_is_dirty_initially(self):
        layout = _SimpleLayout()
        root = LayoutRoot(layout)
        self.assertTrue(root.is_dirty)

    def test_update_runs_measure_and_arrange(self):
        layout = _SimpleLayout()
        root = LayoutRoot(layout)
        result = root.update(Rect(0, 0, 400, 300))
        self.assertTrue(result)
        self.assertEqual(1, len(layout.measured))
        self.assertEqual(1, len(layout.arranged))

    def test_update_clears_dirty(self):
        layout = _SimpleLayout()
        root = LayoutRoot(layout)
        root.update(Rect(0, 0, 400, 300))
        self.assertFalse(root.is_dirty)

    def test_second_update_skipped_if_same_rect(self):
        layout = _SimpleLayout()
        root = LayoutRoot(layout)
        root.update(Rect(0, 0, 400, 300))
        result2 = root.update(Rect(0, 0, 400, 300))
        self.assertFalse(result2)
        self.assertEqual(1, len(layout.measured))

    def test_mark_dirty_forces_rerun(self):
        layout = _SimpleLayout()
        root = LayoutRoot(layout)
        root.update(Rect(0, 0, 400, 300))
        root.mark_dirty()
        result = root.update(Rect(0, 0, 400, 300))
        self.assertTrue(result)
        self.assertEqual(2, len(layout.measured))

    def test_preferred_size_from_measure(self):
        layout = _SimpleLayout()
        root = LayoutRoot(layout)
        root.update(Rect(0, 0, 400, 300))
        self.assertEqual((100, 50), root.preferred_size)

    def test_different_rect_triggers_rerun(self):
        layout = _SimpleLayout()
        root = LayoutRoot(layout)
        root.update(Rect(0, 0, 400, 300))
        result = root.update(Rect(0, 0, 800, 600))
        self.assertTrue(result)

    def test_preferred_size_zero_initially(self):
        layout = _SimpleLayout()
        root = LayoutRoot(layout)
        self.assertEqual((0, 0), root.preferred_size)


# ===========================================================================
# LayoutManager — linear
# ===========================================================================


class TestLayoutManagerLinear(unittest.TestCase):
    def test_first_item_at_anchor(self):
        lm = LayoutManager()
        lm.set_linear_properties(anchor=(10, 20), item_width=100, item_height=40, spacing=8)
        r = lm.linear(0)
        self.assertEqual(Rect(10, 20, 100, 40), r)

    def test_second_item_offset(self):
        lm = LayoutManager()
        lm.set_linear_properties(anchor=(0, 0), item_width=100, item_height=40, spacing=8)
        r = lm.linear(1)
        self.assertEqual(Rect(108, 0, 100, 40), r)

    def test_vertical_layout(self):
        lm = LayoutManager()
        lm.set_linear_properties(anchor=(0, 0), item_width=100, item_height=40,
                                  spacing=8, horizontal=False)
        r = lm.linear(1)
        self.assertEqual(Rect(0, 48, 100, 40), r)

    def test_next_linear_increments(self):
        lm = LayoutManager()
        lm.set_linear_properties(anchor=(0, 0), item_width=100, item_height=40, spacing=8)
        r0 = lm.next_linear()
        r1 = lm.next_linear()
        self.assertEqual(Rect(0, 0, 100, 40), r0)
        self.assertEqual(Rect(108, 0, 100, 40), r1)

    def test_use_rect_false_returns_tuple(self):
        lm = LayoutManager()
        lm.set_linear_properties(anchor=(5, 10), item_width=50, item_height=30,
                                  spacing=4, use_rect=False)
        result = lm.linear(0)
        self.assertIsInstance(result, tuple)
        self.assertEqual((5, 10), result)

    def test_reset_on_set_linear_properties(self):
        lm = LayoutManager()
        lm.set_linear_properties(anchor=(0, 0), item_width=100, item_height=40, spacing=8)
        lm.next_linear()
        lm.set_linear_properties(anchor=(0, 0), item_width=100, item_height=40, spacing=8)
        r = lm.next_linear()
        self.assertEqual(Rect(0, 0, 100, 40), r)

    def test_wrap_count(self):
        lm = LayoutManager()
        lm.set_linear_properties(anchor=(0, 0), item_width=50, item_height=30,
                                  spacing=5, wrap_count=3)
        r3 = lm.linear(3)  # starts second row
        self.assertEqual(0, r3.x)
        self.assertEqual(35, r3.y)  # (30 + 5) * 1


class TestLayoutManagerGridded(unittest.TestCase):
    def test_grid_item_at_0_0(self):
        lm = LayoutManager()
        lm.set_grid_properties(anchor=(0, 0), item_width=100, item_height=40,
                               column_spacing=8, row_spacing=8)
        r = lm.gridded(0, 0)
        self.assertEqual(Rect(0, 0, 100, 40), r)

    def test_grid_item_at_1_0(self):
        lm = LayoutManager()
        lm.set_grid_properties(anchor=(0, 0), item_width=100, item_height=40,
                               column_spacing=8, row_spacing=8)
        r = lm.gridded(1, 0)
        self.assertEqual(Rect(108, 0, 100, 40), r)

    def test_grid_item_at_0_1(self):
        lm = LayoutManager()
        lm.set_grid_properties(anchor=(0, 0), item_width=100, item_height=40,
                               column_spacing=8, row_spacing=8)
        r = lm.gridded(0, 1)
        self.assertEqual(Rect(0, 48, 100, 40), r)

    def test_grid_col_span(self):
        lm = LayoutManager()
        lm.set_grid_properties(anchor=(0, 0), item_width=100, item_height=40,
                               column_spacing=8, row_spacing=8)
        r = lm.gridded(0, 0, column_span=2)
        # width = 100*2 + 8*(2-1) = 208
        self.assertEqual(208, r.width)

    def test_next_gridded(self):
        lm = LayoutManager()
        lm.set_grid_properties(anchor=(0, 0), item_width=100, item_height=40,
                               column_spacing=8, row_spacing=8)
        r0 = lm.next_gridded(3)  # 3 columns
        r1 = lm.next_gridded(3)
        r3 = lm.next_gridded(3)  # after 3 items (index 2), still same row
        r3_actual = lm.gridded(0, 1)  # index 3 starts row 1
        # next_gridded starts at 0, so after 3 calls we're at index 3
        self.assertEqual(Rect(0, 0, 100, 40), r0)
        self.assertEqual(Rect(108, 0, 100, 40), r1)


class TestLayoutManagerAnchored(unittest.TestCase):
    def test_anchored_center(self):
        lm = LayoutManager()
        lm.set_anchor_bounds(Rect(0, 0, 200, 100))
        r = lm.anchored((80, 40), anchor="center")
        self.assertEqual(60, r.x)   # (200-80)//2
        self.assertEqual(30, r.y)   # (100-40)//2

    def test_anchored_top_left(self):
        lm = LayoutManager()
        lm.set_anchor_bounds(Rect(10, 20, 200, 100))
        r = lm.anchored((50, 30), anchor="top_left")
        self.assertEqual(10, r.x)
        self.assertEqual(20, r.y)

    def test_anchored_bottom_right(self):
        lm = LayoutManager()
        lm.set_anchor_bounds(Rect(0, 0, 200, 100))
        r = lm.anchored((50, 30), anchor="bottom_right")
        self.assertEqual(150, r.x)
        self.assertEqual(70, r.y)

    def test_anchored_with_margin(self):
        lm = LayoutManager()
        lm.set_anchor_bounds(Rect(0, 0, 200, 100))
        r = lm.anchored((40, 20), anchor="top_left", margin=(5, 10))
        self.assertEqual(5, r.x)
        self.assertEqual(10, r.y)


if __name__ == "__main__":
    unittest.main()
