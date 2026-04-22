"""Tests for InvalidationTracker query helpers and merge_dirty_regions."""
import unittest

from pygame import Rect

from gui import InvalidationTracker


class InvalidationTrackerIsDirtyTests(unittest.TestCase):

    def test_is_dirty_true_on_fresh_tracker(self) -> None:
        tracker = InvalidationTracker()
        self.assertTrue(tracker.is_dirty)

    def test_is_dirty_false_after_end_frame_with_no_pending(self) -> None:
        tracker = InvalidationTracker()
        tracker.end_frame()  # clears full-redraw flag; no rects added
        self.assertFalse(tracker.is_dirty)

    def test_is_dirty_true_after_invalidate_all(self) -> None:
        tracker = InvalidationTracker()
        tracker.end_frame()
        tracker.invalidate_all()
        self.assertTrue(tracker.is_dirty)

    def test_is_dirty_true_after_invalidate_rect(self) -> None:
        tracker = InvalidationTracker()
        tracker.end_frame()  # clear full-redraw
        tracker.invalidate_rect(Rect(0, 0, 10, 10))
        self.assertTrue(tracker.is_dirty)

    def test_is_dirty_false_after_end_frame_clears_rects(self) -> None:
        tracker = InvalidationTracker()
        tracker.end_frame()
        tracker.invalidate_rect(Rect(0, 0, 10, 10))
        tracker.end_frame()
        self.assertFalse(tracker.is_dirty)


class InvalidationTrackerDirtyRegionCountTests(unittest.TestCase):

    def test_dirty_region_count_zero_on_fresh_tracker(self) -> None:
        # fresh tracker has full-redraw set, not individual rects
        tracker = InvalidationTracker()
        self.assertEqual(tracker.dirty_region_count, 0)

    def test_dirty_region_count_zero_when_only_full_redraw_pending(self) -> None:
        tracker = InvalidationTracker()
        tracker.invalidate_all()
        self.assertEqual(tracker.dirty_region_count, 0)

    def test_dirty_region_count_increments_with_invalidate_rect(self) -> None:
        tracker = InvalidationTracker()
        tracker.end_frame()  # clear full-redraw so rects can accumulate
        tracker.invalidate_rect(Rect(0, 0, 10, 10))
        tracker.invalidate_rect(Rect(20, 20, 5, 5))
        self.assertEqual(tracker.dirty_region_count, 2)

    def test_dirty_region_count_zero_after_end_frame(self) -> None:
        tracker = InvalidationTracker()
        tracker.end_frame()
        tracker.invalidate_rect(Rect(0, 0, 10, 10))
        tracker.end_frame()
        self.assertEqual(tracker.dirty_region_count, 0)

    def test_invalidate_rect_ignored_when_full_redraw_pending(self) -> None:
        tracker = InvalidationTracker()
        # full-redraw is set from __init__; rect should be dropped
        tracker.invalidate_rect(Rect(0, 0, 10, 10))
        self.assertEqual(tracker.dirty_region_count, 0)


class InvalidationTrackerMergeDirtyRegionsTests(unittest.TestCase):

    def test_merge_returns_none_when_clean(self) -> None:
        tracker = InvalidationTracker()
        tracker.end_frame()  # clear full-redraw; no rects
        self.assertIsNone(tracker.merge_dirty_regions())

    def test_merge_returns_none_when_full_redraw_pending(self) -> None:
        tracker = InvalidationTracker()
        # fresh tracker has full-redraw set
        self.assertIsNone(tracker.merge_dirty_regions())

    def test_merge_returns_single_rect_unchanged(self) -> None:
        tracker = InvalidationTracker()
        tracker.end_frame()
        r = Rect(10, 20, 30, 40)
        tracker.invalidate_rect(r)
        merged = tracker.merge_dirty_regions()
        self.assertIsNotNone(merged)
        self.assertEqual(merged, r)

    def test_merge_returns_bounding_union_of_multiple_rects(self) -> None:
        tracker = InvalidationTracker()
        tracker.end_frame()
        tracker.invalidate_rect(Rect(0, 0, 10, 10))
        tracker.invalidate_rect(Rect(20, 30, 5, 5))
        merged = tracker.merge_dirty_regions()
        # union of [0,0,10,10] and [20,30,5,5]
        expected = Rect(0, 0, 10, 10).union(Rect(20, 30, 5, 5))
        self.assertEqual(merged, expected)

    def test_merge_does_not_clear_dirty_regions(self) -> None:
        tracker = InvalidationTracker()
        tracker.end_frame()
        tracker.invalidate_rect(Rect(0, 0, 10, 10))
        tracker.merge_dirty_regions()
        # rects still present; end_frame should still report them
        full, regions = tracker.begin_frame()
        self.assertFalse(full)
        self.assertEqual(len(regions), 1)

    def test_merge_none_after_invalidate_all_overrides_rects(self) -> None:
        tracker = InvalidationTracker()
        tracker.end_frame()
        tracker.invalidate_rect(Rect(0, 0, 10, 10))
        tracker.invalidate_all()  # promotes to full-redraw, drops rects
        self.assertIsNone(tracker.merge_dirty_regions())

    def test_merge_adjacent_rects_form_larger_bounding_rect(self) -> None:
        tracker = InvalidationTracker()
        tracker.end_frame()
        tracker.invalidate_rect(Rect(0, 0, 50, 10))
        tracker.invalidate_rect(Rect(0, 10, 50, 10))
        merged = tracker.merge_dirty_regions()
        self.assertEqual(merged, Rect(0, 0, 50, 20))


if __name__ == "__main__":
    unittest.main()
