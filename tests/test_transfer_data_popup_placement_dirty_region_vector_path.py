"""Tests for TransferData/TransferManager, PopupPlacement/compute_popup_rect,
DirtyRegionTracker, and VectorPath geometry.

All tests are pure computation — no pygame display is required.
"""
import math
import unittest

import pygame
from pygame import Rect

from gui_do.overlays.transfer_data import TransferData, TransferManager
from gui_do.overlays.popup_placement import (
    Alignment,
    PlacementResult,
    PopupPlacement,
    Side,
    compute_popup_rect,
)
from gui_do.graphics.dirty_region import DirtyRegionTracker
from gui_do.graphics.vector_path import VectorPath


# ===========================================================================
# TransferData
# ===========================================================================


class TestTransferData(unittest.TestCase):
    def test_empty_has_no_formats(self):
        td = TransferData()
        self.assertEqual([], td.format_names())

    def test_set_and_get(self):
        td = TransferData()
        td.set("text/plain", "hello")
        self.assertEqual("hello", td.get("text/plain"))

    def test_get_missing_returns_default(self):
        td = TransferData()
        self.assertIsNone(td.get("text/html"))

    def test_get_missing_custom_default(self):
        td = TransferData()
        self.assertEqual(42, td.get("x-foo", 42))

    def test_has_format_true(self):
        td = TransferData()
        td.set("image/png", b"bytes")
        self.assertTrue(td.has_format("image/png"))

    def test_has_format_false(self):
        td = TransferData()
        self.assertFalse(td.has_format("image/png"))

    def test_format_names_sorted(self):
        td = TransferData()
        td.set("z-format", 1)
        td.set("a-format", 2)
        td.set("m-format", 3)
        self.assertEqual(["a-format", "m-format", "z-format"], td.format_names())

    def test_overwrite_value(self):
        td = TransferData()
        td.set("text/plain", "first")
        td.set("text/plain", "second")
        self.assertEqual("second", td.get("text/plain"))

    def test_preferred_format_default(self):
        td = TransferData()
        self.assertEqual("text/plain", td.preferred_format)

    def test_preferred_format_custom(self):
        td = TransferData(preferred_format="application/json")
        self.assertEqual("application/json", td.preferred_format)

    def test_multiple_formats(self):
        td = TransferData()
        td.set("text/plain", "hi")
        td.set("text/html", "<b>hi</b>")
        self.assertEqual(2, len(td.format_names()))


# ===========================================================================
# TransferManager
# ===========================================================================


class TestTransferManager(unittest.TestCase):
    def setUp(self):
        self.mgr = TransferManager()

    def _td(self, text="hello"):
        td = TransferData()
        td.set("text/plain", text)
        return td

    def test_clipboard_initially_none(self):
        self.assertIsNone(self.mgr.get_clipboard())

    def test_set_and_get_clipboard(self):
        td = self._td()
        self.mgr.set_clipboard(td)
        self.assertIs(td, self.mgr.get_clipboard())

    def test_clear_clipboard(self):
        self.mgr.set_clipboard(self._td())
        self.mgr.clear_clipboard()
        self.assertIsNone(self.mgr.get_clipboard())

    def test_drag_initially_none(self):
        self.assertIsNone(self.mgr.current_drag())

    def test_begin_drag(self):
        td = self._td()
        self.mgr.begin_drag(td)
        self.assertIs(td, self.mgr.current_drag())

    def test_end_drag_returns_data_and_clears(self):
        td = self._td()
        self.mgr.begin_drag(td)
        result = self.mgr.end_drag()
        self.assertIs(td, result)
        self.assertIsNone(self.mgr.current_drag())

    def test_end_drag_no_drag_returns_none(self):
        self.assertIsNone(self.mgr.end_drag())

    def test_copy_drag_to_clipboard(self):
        td = self._td()
        self.mgr.begin_drag(td)
        result = self.mgr.copy_drag_to_clipboard()
        self.assertTrue(result)
        self.assertIs(td, self.mgr.get_clipboard())
        # drag still active
        self.assertIs(td, self.mgr.current_drag())

    def test_copy_drag_to_clipboard_no_drag_returns_false(self):
        self.assertFalse(self.mgr.copy_drag_to_clipboard())


# ===========================================================================
# PopupPlacement / compute_popup_rect
# ===========================================================================

SCREEN = Rect(0, 0, 800, 600)
ANCHOR = Rect(100, 100, 80, 30)   # button at (100,100), 80×30


class TestComputePopupRect(unittest.TestCase):
    def test_below_start_alignment(self):
        result = compute_popup_rect(
            ANCHOR, (200, 120), SCREEN,
            preferred_side=Side.BOTTOM, alignment=Alignment.START, offset=4
        )
        self.assertEqual(Side.BOTTOM, result.actual_side)
        self.assertFalse(result.was_flipped)
        # top of popup = anchor bottom + offset
        self.assertEqual(ANCHOR.bottom + 4, result.rect.top)
        # left aligned with anchor
        self.assertEqual(ANCHOR.left, result.rect.left)

    def test_above_start_alignment(self):
        result = compute_popup_rect(
            ANCHOR, (200, 60), SCREEN,
            preferred_side=Side.TOP, alignment=Alignment.START, offset=2
        )
        self.assertEqual(Side.TOP, result.actual_side)
        # bottom of popup = anchor top - offset
        self.assertEqual(ANCHOR.top - 2 - 60, result.rect.top)

    def test_right_start_alignment(self):
        result = compute_popup_rect(
            ANCHOR, (100, 80), SCREEN,
            preferred_side=Side.RIGHT, alignment=Alignment.START, offset=0
        )
        self.assertEqual(Side.RIGHT, result.actual_side)
        self.assertEqual(ANCHOR.right, result.rect.left)
        self.assertEqual(ANCHOR.top, result.rect.top)

    def test_left_start_alignment(self):
        result = compute_popup_rect(
            ANCHOR, (100, 80), SCREEN,
            preferred_side=Side.LEFT, alignment=Alignment.START, offset=0
        )
        self.assertEqual(Side.LEFT, result.actual_side)
        self.assertEqual(ANCHOR.left - 100, result.rect.left)

    def test_center_alignment_horizontal(self):
        result = compute_popup_rect(
            ANCHOR, (200, 60), SCREEN,
            preferred_side=Side.BOTTOM, alignment=Alignment.CENTER
        )
        expected_cx = ANCHOR.centerx
        actual_cx = result.rect.left + 100  # half of 200
        self.assertEqual(expected_cx, actual_cx)

    def test_end_alignment_horizontal(self):
        # popup narrower than anchor so it fits without nudging
        result = compute_popup_rect(
            ANCHOR, (60, 60), SCREEN,
            preferred_side=Side.BOTTOM, alignment=Alignment.END
        )
        # popup right == anchor right (100+80=180; popup left=120, right=180)
        self.assertEqual(ANCHOR.right, result.rect.right)

    def test_flips_to_top_when_bottom_overflows(self):
        # Anchor near screen bottom — popup below won't fit
        anchor_near_bottom = Rect(100, 550, 80, 30)
        result = compute_popup_rect(
            anchor_near_bottom, (200, 80), SCREEN,
            preferred_side=Side.BOTTOM, flip_axes=True
        )
        self.assertTrue(result.was_flipped)
        self.assertEqual(Side.TOP, result.actual_side)

    def test_no_flip_when_flip_axes_false(self):
        anchor_near_bottom = Rect(100, 550, 80, 30)
        result = compute_popup_rect(
            anchor_near_bottom, (200, 80), SCREEN,
            preferred_side=Side.BOTTOM, flip_axes=False
        )
        self.assertFalse(result.was_flipped)
        self.assertEqual(Side.BOTTOM, result.actual_side)

    def test_nudges_when_overflows_right(self):
        anchor_near_right = Rect(750, 100, 40, 30)
        result = compute_popup_rect(
            anchor_near_right, (200, 60), SCREEN,
            preferred_side=Side.BOTTOM, alignment=Alignment.START, flip_axes=False
        )
        self.assertTrue(result.was_nudged)
        self.assertLessEqual(result.rect.right, SCREEN.right)

    def test_no_nudge_when_fits_perfectly(self):
        result = compute_popup_rect(
            ANCHOR, (80, 40), SCREEN,
            preferred_side=Side.BOTTOM, alignment=Alignment.START
        )
        self.assertFalse(result.was_nudged)

    def test_offset_applied(self):
        result = compute_popup_rect(
            ANCHOR, (80, 40), SCREEN,
            preferred_side=Side.BOTTOM, offset=10
        )
        self.assertEqual(ANCHOR.bottom + 10, result.rect.top)

    def test_result_has_correct_popup_size(self):
        result = compute_popup_rect(ANCHOR, (150, 90), SCREEN)
        self.assertEqual(150, result.rect.width)
        self.assertEqual(90, result.rect.height)

    def test_popup_placement_descriptor_delegates_to_compute(self):
        pp = PopupPlacement(preferred_side=Side.BOTTOM, alignment=Alignment.START, offset=4)
        result = pp.compute(ANCHOR, (100, 60), SCREEN)
        self.assertIsInstance(result, PlacementResult)
        self.assertEqual(Side.BOTTOM, result.actual_side)

    def test_placement_result_fields(self):
        result = compute_popup_rect(ANCHOR, (80, 40), SCREEN, preferred_side=Side.TOP)
        self.assertIsInstance(result.rect, Rect)
        self.assertIsInstance(result.was_flipped, bool)
        self.assertIsInstance(result.was_nudged, bool)


# ===========================================================================
# DirtyRegionTracker
# ===========================================================================


class TestDirtyRegionTracker(unittest.TestCase):
    def setUp(self):
        self.tracker = DirtyRegionTracker()

    def test_initially_not_dirty(self):
        self.assertFalse(self.tracker.has_dirty)

    def test_mark_dirty_sets_has_dirty(self):
        self.tracker.mark_dirty(Rect(10, 10, 50, 50))
        self.assertTrue(self.tracker.has_dirty)

    def test_consume_clears_dirty_state(self):
        self.tracker.mark_dirty(Rect(10, 10, 50, 50))
        self.tracker.consume_dirty_regions()
        self.assertFalse(self.tracker.has_dirty)

    def test_consume_returns_accumulated_rects(self):
        r1 = Rect(0, 0, 10, 10)
        r2 = Rect(20, 20, 10, 10)
        self.tracker.mark_dirty(r1)
        self.tracker.mark_dirty(r2)
        result = self.tracker.consume_dirty_regions()
        self.assertEqual(2, len(result))

    def test_zero_size_rect_ignored(self):
        self.tracker.mark_dirty(Rect(10, 10, 0, 50))
        self.tracker.mark_dirty(Rect(10, 10, 50, 0))
        self.assertFalse(self.tracker.has_dirty)

    def test_mark_all_dirty_overrides_partials(self):
        self.tracker.mark_dirty(Rect(0, 0, 50, 50))
        screen = Rect(0, 0, 800, 600)
        self.tracker.mark_all_dirty(screen)
        result = self.tracker.consume_dirty_regions()
        self.assertEqual(1, len(result))
        self.assertEqual(screen, result[0])

    def test_mark_dirty_after_mark_all_ignored(self):
        screen = Rect(0, 0, 800, 600)
        self.tracker.mark_all_dirty(screen)
        self.tracker.mark_dirty(Rect(5, 5, 10, 10))
        result = self.tracker.consume_dirty_regions()
        # Should be only the full-screen rect
        self.assertEqual(1, len(result))

    def test_dirty_union_none_when_clean(self):
        self.assertIsNone(self.tracker.dirty_union())

    def test_dirty_union_single_rect(self):
        r = Rect(10, 10, 30, 30)
        self.tracker.mark_dirty(r)
        union = self.tracker.dirty_union()
        self.assertEqual(r, union)

    def test_dirty_union_two_rects(self):
        self.tracker.mark_dirty(Rect(0, 0, 20, 20))
        self.tracker.mark_dirty(Rect(30, 30, 20, 20))
        union = self.tracker.dirty_union()
        self.assertIsNotNone(union)
        self.assertGreater(union.width, 20)

    def test_dirty_union_does_not_consume(self):
        self.tracker.mark_dirty(Rect(0, 0, 10, 10))
        self.tracker.dirty_union()
        self.assertTrue(self.tracker.has_dirty)

    def test_overlaps_dirty_true(self):
        self.tracker.mark_dirty(Rect(10, 10, 40, 40))
        self.assertTrue(self.tracker.overlaps_dirty(Rect(20, 20, 10, 10)))

    def test_overlaps_dirty_false(self):
        self.tracker.mark_dirty(Rect(10, 10, 20, 20))
        self.assertFalse(self.tracker.overlaps_dirty(Rect(100, 100, 10, 10)))

    def test_overlaps_dirty_false_when_clean(self):
        self.assertFalse(self.tracker.overlaps_dirty(Rect(0, 0, 800, 600)))

    def test_overlaps_dirty_full_dirty_is_always_true(self):
        self.tracker.mark_all_dirty(Rect(0, 0, 800, 600))
        self.assertTrue(self.tracker.overlaps_dirty(Rect(700, 500, 10, 10)))

    def test_rects_union_empty_returns_none(self):
        self.assertIsNone(DirtyRegionTracker.rects_union([]))

    def test_rects_union_single(self):
        r = Rect(5, 5, 10, 10)
        self.assertEqual(r, DirtyRegionTracker.rects_union([r]))

    def test_rects_union_multiple(self):
        result = DirtyRegionTracker.rects_union([Rect(0, 0, 10, 10), Rect(20, 20, 10, 10)])
        self.assertEqual(0, result.x)
        self.assertEqual(30, result.right)


# ===========================================================================
# VectorPath geometry (no rendering surface needed)
# ===========================================================================


class TestVectorPathSegments(unittest.TestCase):
    def test_empty_path_has_no_segments(self):
        path = VectorPath()
        self.assertEqual(0, len(path._segments))

    def test_move_to_adds_segment(self):
        path = VectorPath()
        path.move_to(10, 20)
        self.assertEqual(1, len(path._segments))
        self.assertEqual("M", path._segments[0][0])

    def test_line_to_adds_segment(self):
        path = VectorPath()
        path.move_to(0, 0).line_to(50, 0)
        self.assertEqual(2, len(path._segments))

    def test_close_adds_segment(self):
        path = VectorPath()
        path.move_to(0, 0).line_to(10, 0).close()
        self.assertEqual("Z", path._segments[-1][0])

    def test_quadratic_to_adds_segment(self):
        path = VectorPath()
        path.move_to(0, 0).quadratic_to(50, 0, 100, 0)
        self.assertEqual("Q", path._segments[-1][0])

    def test_cubic_to_adds_segment(self):
        path = VectorPath()
        path.move_to(0, 0).cubic_to(10, 0, 90, 0, 100, 0)
        self.assertEqual("C", path._segments[-1][0])

    def test_arc_adds_segment(self):
        path = VectorPath()
        path.arc(50, 50, 20, 0, 90)
        self.assertEqual("A", path._segments[-1][0])

    def test_rect_adds_multiple_segments(self):
        path = VectorPath()
        before = len(path._segments)
        path.rect(Rect(0, 0, 100, 50))
        self.assertGreater(len(path._segments), before)

    def test_chaining_returns_self(self):
        path = VectorPath()
        result = path.move_to(0, 0).line_to(10, 10)
        self.assertIs(path, result)


class TestVectorPathBoundingRect(unittest.TestCase):
    def test_empty_path_bounding_rect(self):
        bb = VectorPath().bounding_rect()
        # zero area
        self.assertEqual(0, bb.width * bb.height)

    def test_simple_line_bounding_rect(self):
        path = VectorPath()
        path.move_to(10, 20).line_to(110, 80)
        bb = path.bounding_rect()
        self.assertEqual(10, bb.left)
        self.assertEqual(20, bb.top)
        self.assertGreaterEqual(bb.right, 110)
        self.assertGreaterEqual(bb.bottom, 80)

    def test_rect_path_bounding_rect(self):
        r = Rect(5, 10, 100, 50)
        path = VectorPath()
        path.rect(r)
        bb = path.bounding_rect()
        self.assertEqual(r.left, bb.left)
        self.assertEqual(r.top, bb.top)

    def test_arc_bounding_rect_nonzero(self):
        path = VectorPath()
        path.arc(100, 100, 40, 0, 180)
        bb = path.bounding_rect()
        self.assertGreater(bb.width, 0)
        self.assertGreater(bb.height, 0)


class TestVectorPathContainsPoint(unittest.TestCase):
    def test_point_inside_rect_path(self):
        path = VectorPath()
        path.rect(Rect(0, 0, 100, 100))
        self.assertTrue(path.contains_point(50, 50))

    def test_point_outside_rect_path(self):
        path = VectorPath()
        path.rect(Rect(0, 0, 100, 100))
        self.assertFalse(path.contains_point(200, 200))


class TestVectorPathTransform(unittest.TestCase):
    def test_translate_moves_move_segment(self):
        path = VectorPath()
        path.move_to(10, 20)
        translated = path.transform(translate=(5, 10))
        self.assertIsNot(path, translated)
        seg = translated._segments[0]
        self.assertAlmostEqual(15.0, seg[1])
        self.assertAlmostEqual(30.0, seg[2])

    def test_scale_multiplies_coords(self):
        path = VectorPath()
        path.move_to(10, 5)
        scaled = path.transform(scale=2.0)
        seg = scaled._segments[0]
        self.assertAlmostEqual(20.0, seg[1])
        self.assertAlmostEqual(10.0, seg[2])

    def test_identity_transform_preserves_segments(self):
        path = VectorPath()
        path.move_to(3, 4).line_to(7, 8)
        ident = path.transform()
        self.assertEqual(len(path._segments), len(ident._segments))

    def test_rotate_90_swaps_axes(self):
        path = VectorPath()
        path.move_to(1, 0)
        rotated = path.transform(rotate_degrees=90)
        seg = rotated._segments[0]
        self.assertAlmostEqual(0.0, seg[1], places=5)
        self.assertAlmostEqual(1.0, seg[2], places=5)

    def test_close_segment_preserved_in_transform(self):
        path = VectorPath()
        path.move_to(0, 0).line_to(10, 0).close()
        xf = path.transform(translate=(1, 1))
        kinds = [s[0] for s in xf._segments]
        self.assertIn("Z", kinds)

    def test_original_unchanged_after_transform(self):
        path = VectorPath()
        path.move_to(5, 5)
        _ = path.transform(translate=(100, 100))
        self.assertAlmostEqual(5.0, path._segments[0][1])


if __name__ == "__main__":
    unittest.main()
