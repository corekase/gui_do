"""Tests for popup_placement — Side, Alignment, PlacementResult, compute_popup_rect."""
import unittest
import pygame
from pygame import Rect

from gui_do.overlays.popup_placement import (
    Side,
    Alignment,
    PlacementResult,
    PopupPlacement,
    compute_popup_rect,
)

pygame.init()


# ===========================================================================
# Side enum
# ===========================================================================


class TestSide(unittest.TestCase):
    def test_values(self):
        self.assertEqual("top", Side.TOP.value)
        self.assertEqual("bottom", Side.BOTTOM.value)
        self.assertEqual("left", Side.LEFT.value)
        self.assertEqual("right", Side.RIGHT.value)


# ===========================================================================
# Alignment enum
# ===========================================================================


class TestAlignment(unittest.TestCase):
    def test_values(self):
        self.assertEqual("start", Alignment.START.value)
        self.assertEqual("center", Alignment.CENTER.value)
        self.assertEqual("end", Alignment.END.value)


# ===========================================================================
# PlacementResult dataclass
# ===========================================================================


class TestPlacementResult(unittest.TestCase):
    def test_fields_stored(self):
        r = PlacementResult(rect=Rect(0, 0, 100, 50), actual_side=Side.BOTTOM)
        self.assertEqual(Rect(0, 0, 100, 50), r.rect)
        self.assertEqual(Side.BOTTOM, r.actual_side)

    def test_flags_default_false(self):
        r = PlacementResult(rect=Rect(0, 0, 100, 50), actual_side=Side.TOP)
        self.assertFalse(r.was_flipped)
        self.assertFalse(r.was_nudged)

    def test_custom_flags(self):
        r = PlacementResult(rect=Rect(0, 0, 100, 50), actual_side=Side.LEFT, was_flipped=True, was_nudged=True)
        self.assertTrue(r.was_flipped)
        self.assertTrue(r.was_nudged)


# ===========================================================================
# PopupPlacement defaults
# ===========================================================================


class TestPopupPlacementDefaults(unittest.TestCase):
    def test_default_side(self):
        p = PopupPlacement()
        self.assertEqual(Side.BOTTOM, p.preferred_side)

    def test_default_alignment(self):
        p = PopupPlacement()
        self.assertEqual(Alignment.START, p.alignment)

    def test_default_offset(self):
        p = PopupPlacement()
        self.assertEqual(0, p.offset)

    def test_default_flip_axes(self):
        p = PopupPlacement()
        self.assertTrue(p.flip_axes)


# ===========================================================================
# compute_popup_rect — basic placement
# ===========================================================================


class TestComputePopupRectBasic(unittest.TestCase):
    def test_below_anchor(self):
        screen = Rect(0, 0, 800, 600)
        anchor = Rect(100, 100, 100, 30)
        result = compute_popup_rect(
            anchor=anchor,
            popup_size=(100, 50),
            screen_bounds=screen,
            preferred_side=Side.BOTTOM,
        )
        self.assertIsInstance(result, PlacementResult)
        self.assertEqual(Side.BOTTOM, result.actual_side)
        # Popup top should be below anchor bottom
        self.assertGreaterEqual(result.rect.top, anchor.bottom)

    def test_above_anchor(self):
        screen = Rect(0, 0, 800, 600)
        anchor = Rect(100, 300, 100, 30)
        result = compute_popup_rect(
            anchor=anchor,
            popup_size=(100, 50),
            screen_bounds=screen,
            preferred_side=Side.TOP,
        )
        self.assertEqual(Side.TOP, result.actual_side)
        # Popup bottom should be above anchor top
        self.assertLessEqual(result.rect.bottom, anchor.top)

    def test_right_of_anchor(self):
        screen = Rect(0, 0, 800, 600)
        anchor = Rect(100, 100, 100, 30)
        result = compute_popup_rect(
            anchor=anchor,
            popup_size=(100, 50),
            screen_bounds=screen,
            preferred_side=Side.RIGHT,
        )
        self.assertEqual(Side.RIGHT, result.actual_side)
        self.assertGreaterEqual(result.rect.left, anchor.right)

    def test_left_of_anchor(self):
        screen = Rect(0, 0, 800, 600)
        anchor = Rect(300, 100, 100, 30)
        result = compute_popup_rect(
            anchor=anchor,
            popup_size=(100, 50),
            screen_bounds=screen,
            preferred_side=Side.LEFT,
        )
        self.assertEqual(Side.LEFT, result.actual_side)
        self.assertLessEqual(result.rect.right, anchor.left)

    def test_result_inside_screen_bounds(self):
        screen = Rect(0, 0, 800, 600)
        anchor = Rect(100, 100, 100, 30)
        result = compute_popup_rect(
            anchor=anchor,
            popup_size=(200, 100),
            screen_bounds=screen,
            preferred_side=Side.BOTTOM,
        )
        self.assertGreaterEqual(result.rect.left, screen.left)
        self.assertGreaterEqual(result.rect.top, screen.top)

    def test_flips_when_overflow_bottom(self):
        # Anchor near bottom — bottom popup would overflow, should flip to top
        screen = Rect(0, 0, 800, 600)
        anchor = Rect(100, 560, 100, 30)
        result = compute_popup_rect(
            anchor=anchor,
            popup_size=(100, 100),
            screen_bounds=screen,
            preferred_side=Side.BOTTOM,
            flip_axes=True,
        )
        self.assertTrue(result.was_flipped or result.rect.bottom <= screen.bottom)

    def test_offset_applied(self):
        screen = Rect(0, 0, 800, 600)
        anchor = Rect(100, 100, 100, 30)
        result_no_offset = compute_popup_rect(
            anchor=anchor, popup_size=(100, 50), screen_bounds=screen, preferred_side=Side.BOTTOM, offset=0
        )
        result_offset = compute_popup_rect(
            anchor=anchor, popup_size=(100, 50), screen_bounds=screen, preferred_side=Side.BOTTOM, offset=10
        )
        self.assertGreater(result_offset.rect.top, result_no_offset.rect.top)

    def test_popup_placement_compute_delegates(self):
        screen = Rect(0, 0, 800, 600)
        anchor = Rect(100, 100, 100, 30)
        p = PopupPlacement(preferred_side=Side.BOTTOM)
        result = p.compute(anchor_rect=anchor, popup_size=(100, 50), screen_bounds=screen)
        self.assertIsInstance(result, PlacementResult)
        self.assertEqual(Side.BOTTOM, result.actual_side)


if __name__ == "__main__":
    unittest.main()
