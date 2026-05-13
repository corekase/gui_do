"""Tests for geometry helper functions in feature_lifecycle and layout_geometry."""
import unittest
import pygame
from pygame import Rect

from gui_do.features.feature_lifecycle import (
    calculate_grid_layout,
)
from gui_do.features.layout_geometry import (
    inset_rect,
    centered_horizontal_strip_layout,
    split_slot_bounds,
    partition_rects,
)

pygame.init()


# ===========================================================================
# calculate_grid_layout
# ===========================================================================


class TestCalculateGridLayout(unittest.TestCase):
    def test_single_cell(self):
        anchor = (10, 20, 100, 50)
        result = calculate_grid_layout(anchor, cols=1, rows=1, gap=0, label_height=0, label_gap=0)
        self.assertEqual([(10, 20, 100, 50)], result)

    def test_two_columns(self):
        anchor = (0, 0, 100, 50)
        result = calculate_grid_layout(anchor, cols=2, rows=1, gap=5, label_height=0, label_gap=0)
        self.assertEqual((0, 0, 100, 50), result[0])
        self.assertEqual((105, 0, 100, 50), result[1])

    def test_two_rows(self):
        anchor = (0, 0, 100, 50)
        result = calculate_grid_layout(anchor, cols=1, rows=2, gap=5, label_height=0, label_gap=0)
        self.assertEqual((0, 0, 100, 50), result[0])
        self.assertEqual((0, 55, 100, 50), result[1])

    def test_count_equals_rows_times_cols(self):
        anchor = (0, 0, 100, 50)
        result = calculate_grid_layout(anchor, cols=3, rows=2, gap=0, label_height=0, label_gap=0)
        self.assertEqual(6, len(result))

    def test_with_label_height(self):
        anchor = (0, 0, 100, 50)
        result = calculate_grid_layout(anchor, cols=1, rows=2, gap=0, label_height=20, label_gap=5)
        # row 1 y = 0, row 2 y = 50 + 20 + 5 + 0 = 75
        self.assertEqual((0, 75, 100, 50), result[1])


# ===========================================================================
# inset_rect
# ===========================================================================


class TestInsetRect(unittest.TestCase):
    def test_no_padding(self):
        rect = Rect(10, 20, 100, 50)
        result = inset_rect(rect)
        self.assertEqual(Rect(10, 20, 100, 50), result)

    def test_x_padding(self):
        rect = Rect(0, 0, 100, 50)
        result = inset_rect(rect, padding_x=10)
        self.assertEqual(Rect(10, 0, 80, 50), result)

    def test_y_padding(self):
        rect = Rect(0, 0, 100, 50)
        result = inset_rect(rect, padding_y=5)
        self.assertEqual(Rect(0, 5, 100, 40), result)

    def test_both_paddings(self):
        rect = Rect(0, 0, 100, 50)
        result = inset_rect(rect, padding_x=10, padding_y=5)
        self.assertEqual(Rect(10, 5, 80, 40), result)

    def test_minimum_size_clamped_to_one(self):
        rect = Rect(0, 0, 10, 10)
        result = inset_rect(rect, padding_x=20, padding_y=20)
        self.assertGreaterEqual(result.width, 1)
        self.assertGreaterEqual(result.height, 1)


# ===========================================================================
# centered_horizontal_strip_layout
# ===========================================================================


class TestCenteredHorizontalStripLayout(unittest.TestCase):
    def test_single_item(self):
        result = centered_horizontal_strip_layout(
            left=0, width=100, y=10, item_count=1, item_height=30, spacing=0
        )
        self.assertEqual(1, len(result))
        self.assertEqual(10, result[0].y)
        self.assertEqual(30, result[0].height)

    def test_two_items_span_full_width(self):
        result = centered_horizontal_strip_layout(
            left=0, width=100, y=0, item_count=2, item_height=30, spacing=0
        )
        self.assertEqual(2, len(result))

    def test_spacing_applied(self):
        result = centered_horizontal_strip_layout(
            left=0, width=100, y=0, item_count=2, item_height=30, spacing=10
        )
        # Both rects should not overlap
        self.assertGreater(result[1].left, result[0].right)

    def test_correct_count(self):
        result = centered_horizontal_strip_layout(
            left=0, width=200, y=5, item_count=4, item_height=20, spacing=5
        )
        self.assertEqual(4, len(result))


# ===========================================================================
# split_slot_bounds
# ===========================================================================


class TestSplitSlotBounds(unittest.TestCase):
    def test_empty_returns_zeros(self):
        self.assertEqual((0, 0), split_slot_bounds([]))

    def test_single_slot(self):
        slot = Rect(10, 0, 50, 30)
        left, right = split_slot_bounds([slot])
        self.assertEqual(10, left)
        self.assertEqual(60, right)

    def test_multiple_slots(self):
        slots = [Rect(0, 0, 50, 30), Rect(60, 0, 50, 30), Rect(120, 0, 50, 30)]
        left, right = split_slot_bounds(slots)
        self.assertEqual(0, left)
        self.assertEqual(170, right)


# ===========================================================================
# partition_rects
# ===========================================================================


class TestPartitionRects(unittest.TestCase):
    def test_single_cell(self):
        bounds = Rect(0, 0, 100, 100)
        result = partition_rects(bounds, rows=1, cols=1)
        self.assertEqual(1, len(result))
        self.assertEqual(Rect(0, 0, 100, 100), result[0])

    def test_two_columns(self):
        bounds = Rect(0, 0, 100, 50)
        result = partition_rects(bounds, rows=1, cols=2, gap=0)
        self.assertEqual(2, len(result))
        self.assertEqual(0, result[0].left)
        self.assertEqual(50, result[1].left)

    def test_two_rows(self):
        bounds = Rect(0, 0, 100, 100)
        result = partition_rects(bounds, rows=2, cols=1, gap=0)
        self.assertEqual(2, len(result))
        self.assertEqual(0, result[0].top)
        self.assertEqual(50, result[1].top)

    def test_with_padding(self):
        bounds = Rect(0, 0, 100, 100)
        result = partition_rects(bounds, rows=1, cols=1, padding=10)
        self.assertEqual(Rect(10, 10, 80, 80), result[0])

    def test_count_limits_cells(self):
        bounds = Rect(0, 0, 300, 100)
        result = partition_rects(bounds, rows=1, cols=3, count=2)
        self.assertEqual(2, len(result))

    def test_with_gap(self):
        bounds = Rect(0, 0, 100, 50)
        result = partition_rects(bounds, rows=1, cols=2, gap=10)
        self.assertGreater(result[1].left, result[0].right)

    def test_accepts_tuple_bounds(self):
        result = partition_rects((0, 0, 100, 100), rows=1, cols=1)
        self.assertEqual(1, len(result))
        self.assertEqual(0, result[0].left)


if __name__ == "__main__":
    unittest.main()
