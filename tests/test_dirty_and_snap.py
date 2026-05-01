"""Tests for DirtyRegionTracker, InvalidationTracker, SnapGrid, ValueChangeReason, LayoutAxis."""
import unittest
import pygame

pygame.init()


from gui_do.graphics.dirty_region import DirtyRegionTracker
from gui_do.data.invalidation import InvalidationTracker
from gui_do.layout.snap_grid import SnapGrid
from gui_do.events.value_change_reason import ValueChangeReason
from gui_do.layout.layout_axis import LayoutAxis


# ===========================================================================
# ValueChangeReason enum
# ===========================================================================


class TestValueChangeReason(unittest.TestCase):
    def test_members(self):
        self.assertIn("KEYBOARD", ValueChangeReason.__members__)
        self.assertIn("PROGRAMMATIC", ValueChangeReason.__members__)
        self.assertIn("MOUSE_DRAG", ValueChangeReason.__members__)
        self.assertIn("WHEEL", ValueChangeReason.__members__)

    def test_str_subclass(self):
        self.assertEqual("keyboard", ValueChangeReason.KEYBOARD)

    def test_unique_values(self):
        vals = [v.value for v in ValueChangeReason]
        self.assertEqual(len(vals), len(set(vals)))


# ===========================================================================
# LayoutAxis enum
# ===========================================================================


class TestLayoutAxis(unittest.TestCase):
    def test_horizontal_value(self):
        self.assertEqual("horizontal", LayoutAxis.HORIZONTAL.value)

    def test_vertical_value(self):
        self.assertEqual("vertical", LayoutAxis.VERTICAL.value)

    def test_two_members(self):
        self.assertEqual(2, len(list(LayoutAxis)))


# ===========================================================================
# SnapGrid — snap_point / snap_rect / nearest_cell
# ===========================================================================


class TestSnapGrid(unittest.TestCase):
    def test_snap_point_to_grid(self):
        grid = SnapGrid(16, 16)
        self.assertEqual((16, 16), grid.snap_point(14, 14))

    def test_snap_point_already_on_grid(self):
        grid = SnapGrid(16, 16)
        self.assertEqual((0, 0), grid.snap_point(0, 0))

    def test_snap_point_with_offset(self):
        grid = SnapGrid(10, 10, offset_x=5, offset_y=5)
        sx, sy = grid.snap_point(13, 13)
        self.assertEqual(15, sx)
        self.assertEqual(15, sy)

    def test_snap_rect_preserves_size(self):
        grid = SnapGrid(16, 16)
        rect = pygame.Rect(14, 14, 50, 30)
        snapped = grid.snap_rect(rect)
        self.assertEqual(50, snapped.width)
        self.assertEqual(30, snapped.height)

    def test_nearest_cell_origin(self):
        grid = SnapGrid(16, 16)
        self.assertEqual((0, 0), grid.nearest_cell(0, 0))

    def test_nearest_cell_positive(self):
        grid = SnapGrid(16, 16)
        col, row = grid.nearest_cell(32, 48)
        self.assertEqual(2, col)
        self.assertEqual(3, row)

    def test_cell_w_minimum_one(self):
        grid = SnapGrid(0, 0)
        self.assertEqual(1, grid.cell_w)
        self.assertEqual(1, grid.cell_h)


# ===========================================================================
# DirtyRegionTracker
# ===========================================================================


class TestDirtyRegionTrackerInitial(unittest.TestCase):
    def test_not_dirty_initially(self):
        t = DirtyRegionTracker()
        self.assertFalse(t.has_dirty)

    def test_no_dirty_regions_initially(self):
        t = DirtyRegionTracker()
        self.assertEqual([], t.consume_dirty_regions())


class TestDirtyRegionTrackerMarkDirty(unittest.TestCase):
    def test_mark_dirty_sets_has_dirty(self):
        t = DirtyRegionTracker()
        t.mark_dirty(pygame.Rect(0, 0, 10, 10))
        self.assertTrue(t.has_dirty)

    def test_zero_size_rect_ignored(self):
        t = DirtyRegionTracker()
        t.mark_dirty(pygame.Rect(0, 0, 0, 10))
        self.assertFalse(t.has_dirty)

    def test_consume_returns_rects_and_clears(self):
        t = DirtyRegionTracker()
        t.mark_dirty(pygame.Rect(0, 0, 10, 10))
        rects = t.consume_dirty_regions()
        self.assertEqual(1, len(rects))
        self.assertFalse(t.has_dirty)

    def test_mark_all_dirty(self):
        t = DirtyRegionTracker()
        screen = pygame.Rect(0, 0, 800, 600)
        t.mark_all_dirty(screen)
        self.assertTrue(t.has_dirty)
        rects = t.consume_dirty_regions()
        self.assertEqual(1, len(rects))
        self.assertEqual(800, rects[0].width)

    def test_dirty_union_returns_none_when_clean(self):
        t = DirtyRegionTracker()
        self.assertIsNone(t.dirty_union())

    def test_dirty_union_merges_rects(self):
        t = DirtyRegionTracker()
        t.mark_dirty(pygame.Rect(0, 0, 10, 10))
        t.mark_dirty(pygame.Rect(5, 5, 10, 10))
        union = t.dirty_union()
        self.assertIsNotNone(union)
        self.assertGreater(union.width, 0)

    def test_mark_after_all_dirty_ignored(self):
        t = DirtyRegionTracker()
        t.mark_all_dirty(pygame.Rect(0, 0, 100, 100))
        t.mark_dirty(pygame.Rect(10, 10, 5, 5))  # should be ignored
        rects = t.consume_dirty_regions()
        self.assertEqual(1, len(rects))  # only the full-screen one


# ===========================================================================
# InvalidationTracker
# ===========================================================================


class TestInvalidationTrackerInitial(unittest.TestCase):
    def test_full_redraw_initially(self):
        t = InvalidationTracker()
        is_full, rects = t.begin_frame()
        self.assertTrue(is_full)

    def test_end_frame_clears_full_redraw(self):
        t = InvalidationTracker()
        t.end_frame()
        is_full, rects = t.begin_frame()
        self.assertFalse(is_full)

    def test_invalidate_all_marks_full(self):
        t = InvalidationTracker()
        t.end_frame()
        t.invalidate_all()
        is_full, _ = t.begin_frame()
        self.assertTrue(is_full)

    def test_invalidate_rect_accumulates(self):
        t = InvalidationTracker()
        t.end_frame()  # clear initial full_redraw
        t.invalidate_rect(pygame.Rect(0, 0, 10, 10))
        is_full, rects = t.begin_frame()
        self.assertFalse(is_full)

    def test_merge_dirty_rects_empty(self):
        t = InvalidationTracker()
        self.assertEqual([], t.merge_dirty_rects())


if __name__ == "__main__":
    unittest.main()
