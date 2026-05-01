"""Tests for PopupPlacement and NotificationCenter."""
import unittest

import pygame
pygame.init()

from pygame import Rect
from gui_do.overlays.popup_placement import (
    Alignment, PlacementResult, PopupPlacement, Side, compute_popup_rect
)
from gui_do.overlays.notification_center import NotificationCenter, NotificationRecord
from gui_do.overlays.toast_manager import ToastSeverity


# ===========================================================================
# Side / Alignment enums
# ===========================================================================


class TestSideEnum(unittest.TestCase):
    def test_members(self):
        self.assertEqual("top", Side.TOP.value)
        self.assertEqual("bottom", Side.BOTTOM.value)
        self.assertEqual("left", Side.LEFT.value)
        self.assertEqual("right", Side.RIGHT.value)


class TestAlignmentEnum(unittest.TestCase):
    def test_members(self):
        self.assertEqual("start", Alignment.START.value)
        self.assertEqual("center", Alignment.CENTER.value)
        self.assertEqual("end", Alignment.END.value)


# ===========================================================================
# compute_popup_rect — basic placement
# ===========================================================================


class TestComputePopupRect(unittest.TestCase):
    """Tests that popup is placed correctly relative to anchor on preferred side."""

    def _screen(self):
        return Rect(0, 0, 800, 600)

    def _anchor(self):
        return Rect(100, 100, 80, 30)  # button at (100,100), 80x30

    def test_place_below(self):
        result = compute_popup_rect(
            anchor=self._anchor(),
            popup_size=(200, 100),
            screen_bounds=self._screen(),
            preferred_side=Side.BOTTOM,
        )
        self.assertEqual(Side.BOTTOM, result.actual_side)
        # Popup top should be at anchor bottom
        self.assertEqual(130, result.rect.top)

    def test_place_above(self):
        result = compute_popup_rect(
            anchor=self._anchor(),
            popup_size=(200, 100),
            screen_bounds=self._screen(),
            preferred_side=Side.TOP,
        )
        self.assertEqual(Side.TOP, result.actual_side)
        # Popup bottom should be at anchor top
        self.assertEqual(100, result.rect.bottom)

    def test_place_right(self):
        result = compute_popup_rect(
            anchor=self._anchor(),
            popup_size=(150, 80),
            screen_bounds=self._screen(),
            preferred_side=Side.RIGHT,
        )
        self.assertEqual(Side.RIGHT, result.actual_side)
        self.assertEqual(180, result.rect.left)  # anchor right = 100+80 = 180

    def test_place_left(self):
        result = compute_popup_rect(
            anchor=self._anchor(),
            popup_size=(100, 80),
            screen_bounds=self._screen(),
            preferred_side=Side.LEFT,
        )
        self.assertEqual(Side.LEFT, result.actual_side)
        self.assertEqual(100, result.rect.right)  # anchor left = 100

    def test_offset_applied_below(self):
        result = compute_popup_rect(
            anchor=self._anchor(),
            popup_size=(100, 50),
            screen_bounds=self._screen(),
            preferred_side=Side.BOTTOM,
            offset=8,
        )
        self.assertEqual(138, result.rect.top)  # 130 + 8 offset

    def test_popup_stays_in_screen(self):
        # Anchor near bottom edge — flip or nudge should keep popup in screen
        anchor = Rect(100, 550, 80, 30)
        result = compute_popup_rect(
            anchor=anchor,
            popup_size=(200, 100),
            screen_bounds=self._screen(),
            preferred_side=Side.BOTTOM,
        )
        self.assertGreaterEqual(result.rect.top, 0)
        self.assertLessEqual(result.rect.bottom, 600 + result.rect.height)

    def test_was_not_flipped_when_fits(self):
        result = compute_popup_rect(
            anchor=self._anchor(),
            popup_size=(100, 50),
            screen_bounds=self._screen(),
            preferred_side=Side.BOTTOM,
        )
        self.assertFalse(result.was_flipped)

    def test_placement_result_type(self):
        result = compute_popup_rect(
            anchor=self._anchor(),
            popup_size=(100, 50),
            screen_bounds=self._screen(),
        )
        self.assertIsInstance(result, PlacementResult)


# ===========================================================================
# PopupPlacement descriptor
# ===========================================================================


class TestPopupPlacement(unittest.TestCase):
    def test_defaults(self):
        pp = PopupPlacement()
        self.assertEqual(Side.BOTTOM, pp.preferred_side)
        self.assertEqual(Alignment.START, pp.alignment)
        self.assertEqual(0, pp.offset)

    def test_compute_delegates(self):
        pp = PopupPlacement(preferred_side=Side.TOP)
        result = pp.compute(
            anchor_rect=Rect(100, 100, 80, 30),
            popup_size=(200, 80),
            screen_bounds=Rect(0, 0, 800, 600),
        )
        self.assertIsInstance(result, PlacementResult)
        self.assertEqual(Side.TOP, result.actual_side)


# ===========================================================================
# NotificationCenter — initial state
# ===========================================================================


class TestNotificationCenterInitial(unittest.TestCase):
    def test_empty_records(self):
        nc = NotificationCenter()
        self.assertEqual([], nc.all_records)

    def test_unread_count_zero(self):
        nc = NotificationCenter()
        self.assertEqual(0, nc.unread_count.value)


# ===========================================================================
# NotificationCenter — add / mark_read / clear
# ===========================================================================


class TestNotificationCenterAdd(unittest.TestCase):
    def test_add_inserts_record(self):
        nc = NotificationCenter()
        r = NotificationRecord(message="Hello")
        nc.add(r)
        self.assertEqual(1, len(nc.all_records))

    def test_unread_count_increments(self):
        nc = NotificationCenter()
        nc.add(NotificationRecord(message="A"))
        nc.add(NotificationRecord(message="B"))
        self.assertEqual(2, nc.unread_count.value)

    def test_records_newest_first(self):
        nc = NotificationCenter()
        nc.add(NotificationRecord(message="first"))
        nc.add(NotificationRecord(message="second"))
        self.assertEqual("second", nc.all_records[0].message)

    def test_max_records_respected(self):
        nc = NotificationCenter(max_records=2)
        nc.add(NotificationRecord(message="a"))
        nc.add(NotificationRecord(message="b"))
        nc.add(NotificationRecord(message="c"))
        self.assertEqual(2, len(nc.all_records))

    def test_mark_all_read(self):
        nc = NotificationCenter()
        nc.add(NotificationRecord(message="A"))
        nc.add(NotificationRecord(message="B"))
        nc.mark_all_read()
        self.assertEqual(0, nc.unread_count.value)
        self.assertTrue(all(r.read for r in nc.all_records))

    def test_mark_read_single(self):
        nc = NotificationCenter()
        r = NotificationRecord(message="X")
        nc.add(r)
        nc.mark_read(r)
        self.assertEqual(0, nc.unread_count.value)

    def test_clear(self):
        nc = NotificationCenter()
        nc.add(NotificationRecord(message="Y"))
        nc.clear()
        self.assertEqual([], nc.all_records)
        self.assertEqual(0, nc.unread_count.value)

    def test_records_observable_updates(self):
        nc = NotificationCenter()
        r = NotificationRecord(message="Z")
        nc.add(r)
        self.assertIn(r, nc.records.value)


if __name__ == "__main__":
    unittest.main()
