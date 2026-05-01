"""Tests for _anchor_adjusted_lock_rect (thumb drag lock rect geometry)."""
import unittest
import pygame
from pygame import Rect

from gui_do.controls.base._thumb_drag_lock import _anchor_adjusted_lock_rect

pygame.init()


class TestAnchorAdjustedLockRect(unittest.TestCase):
    """Pure geometry tests for _anchor_adjusted_lock_rect."""

    def test_y_axis_basic(self):
        track = Rect(10, 0, 20, 200)
        handle = Rect(10, 0, 20, 40)
        anchor = 20
        lock = _anchor_adjusted_lock_rect("y", track, handle, anchor, (20, 20))
        # x should be midpoint of track
        self.assertEqual(track.x + track.width // 2, lock.x)
        # min_py = track.y + anchor = 0 + 20 = 20
        self.assertEqual(20, lock.y)
        # max_py = track.bottom - handle.height + anchor = 200 - 40 + 20 = 180
        self.assertEqual(161, lock.height)  # (180 - 20) + 1

    def test_x_axis_basic(self):
        track = Rect(0, 10, 200, 20)
        handle = Rect(0, 10, 40, 20)
        anchor = 20
        lock = _anchor_adjusted_lock_rect("x", track, handle, anchor, (20, 20))
        # min_px = track.x + anchor = 0 + 20 = 20
        self.assertEqual(20, lock.x)
        # max_px = track.right - handle.width + anchor = 200 - 40 + 20 = 180
        self.assertEqual(161, lock.width)  # (180 - 20) + 1

    def test_y_axis_zero_anchor(self):
        track = Rect(0, 0, 20, 100)
        handle = Rect(0, 0, 20, 20)
        lock = _anchor_adjusted_lock_rect("y", track, handle, 0, (10, 0))
        self.assertEqual(0, lock.y)
        self.assertEqual(81, lock.height)  # (80 - 0) + 1

    def test_clamped_when_handle_larger_than_track(self):
        # When handle >= track, max < min → should clamp max = min
        track = Rect(0, 0, 20, 30)
        handle = Rect(0, 0, 20, 50)  # larger than track
        lock = _anchor_adjusted_lock_rect("y", track, handle, 0, (10, 0))
        # max_py = 30 - 50 + 0 = -20, which < min_py 0; so max_py = min_py = 0
        self.assertEqual(0, lock.y)
        self.assertEqual(1, lock.height)

    def test_x_axis_zero_range(self):
        track = Rect(0, 0, 50, 20)
        handle = Rect(0, 0, 50, 20)  # fills track exactly
        lock = _anchor_adjusted_lock_rect("x", track, handle, 0, (0, 10))
        self.assertEqual(0, lock.x)
        self.assertEqual(1, lock.width)

    def test_y_lock_width_is_one(self):
        track = Rect(10, 0, 20, 200)
        handle = Rect(10, 0, 20, 40)
        lock = _anchor_adjusted_lock_rect("y", track, handle, 0, (0, 0))
        self.assertEqual(1, lock.width)

    def test_x_lock_height_is_one(self):
        track = Rect(0, 10, 200, 20)
        handle = Rect(0, 10, 40, 20)
        lock = _anchor_adjusted_lock_rect("x", track, handle, 0, (0, 0))
        self.assertEqual(1, lock.height)


if __name__ == "__main__":
    unittest.main()
