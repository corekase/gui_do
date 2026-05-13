"""Tests for layout_pass (MeasureContext, ArrangeContext, LayoutRoot)."""
import unittest

import pygame
from pygame import Rect

from gui_do.layout.layout_pass import MeasureContext, ArrangeContext, LayoutRoot

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

    def test_update_accepts_rect_provider(self):
        layout = _SimpleLayout()
        root = LayoutRoot(layout)
        result = root.update(lambda: Rect(5, 6, 120, 80))
        self.assertTrue(result)
        self.assertEqual(Rect(5, 6, 120, 80), layout.arranged[0])


if __name__ == "__main__":
    unittest.main()
