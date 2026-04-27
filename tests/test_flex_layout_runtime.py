"""Tests for FlexLayout, FlexItem, FlexDirection, FlexAlign, FlexJustify."""
import unittest
from unittest.mock import MagicMock
from pygame import Rect

from gui_do.layout.flex_layout import (
    FlexLayout,
    FlexItem,
    FlexDirection,
    FlexAlign,
    FlexJustify,
)


def _node(rect: Rect) -> MagicMock:
    """Create a mock UiNode with a mutable rect attribute."""
    node = MagicMock()
    node.rect = rect
    return node


class TestFlexLayoutRow(unittest.TestCase):

    def test_row_distributes_basis_widths(self):
        a = _node(Rect(0, 0, 100, 30))
        b = _node(Rect(0, 0, 200, 30))
        layout = FlexLayout(direction=FlexDirection.ROW, gap=0)
        layout.items = [FlexItem(a, grow=0, basis=100), FlexItem(b, grow=0, basis=200)]
        layout.apply(Rect(0, 0, 400, 50))
        self.assertEqual(a.rect.x, 0)
        self.assertEqual(a.rect.width, 100)
        self.assertEqual(b.rect.x, 100)
        self.assertEqual(b.rect.width, 200)

    def test_row_gap_shifts_items(self):
        a = _node(Rect(0, 0, 50, 30))
        b = _node(Rect(0, 0, 50, 30))
        layout = FlexLayout(direction=FlexDirection.ROW, gap=10)
        layout.items = [FlexItem(a, grow=0, basis=50), FlexItem(b, grow=0, basis=50)]
        layout.apply(Rect(0, 0, 200, 50))
        self.assertEqual(a.rect.x, 0)
        self.assertEqual(b.rect.x, 60)

    def test_row_grow_fills_surplus(self):
        a = _node(Rect(0, 0, 50, 30))
        b = _node(Rect(0, 0, 50, 30))
        layout = FlexLayout(direction=FlexDirection.ROW)
        layout.items = [FlexItem(a, grow=0, basis=50), FlexItem(b, grow=1, basis=50)]
        layout.apply(Rect(0, 0, 300, 50))
        # b should absorb the 200px surplus
        self.assertEqual(a.rect.width, 50)
        self.assertGreater(b.rect.width, 50)
        self.assertLessEqual(b.rect.x + b.rect.width, 300)

    def test_row_equal_grow_shares_surplus(self):
        a = _node(Rect(0, 0, 0, 30))
        b = _node(Rect(0, 0, 0, 30))
        layout = FlexLayout(direction=FlexDirection.ROW)
        layout.items = [FlexItem(a, grow=1, basis=0), FlexItem(b, grow=1, basis=0)]
        layout.apply(Rect(0, 0, 200, 50))
        self.assertEqual(a.rect.width, 100)
        self.assertEqual(b.rect.width, 100)

    def test_row_max_size_caps_grow(self):
        a = _node(Rect(0, 0, 0, 30))
        layout = FlexLayout(direction=FlexDirection.ROW)
        layout.items = [FlexItem(a, grow=1, basis=0, max_size=80)]
        layout.apply(Rect(0, 0, 300, 50))
        self.assertLessEqual(a.rect.width, 80)

    def test_row_min_size_respected_on_shrink(self):
        a = _node(Rect(0, 0, 200, 30))
        layout = FlexLayout(direction=FlexDirection.ROW)
        layout.items = [FlexItem(a, grow=0, shrink=1, basis=200, min_size=100)]
        layout.apply(Rect(0, 0, 50, 50))
        self.assertGreaterEqual(a.rect.width, 100)

    def test_row_padding_reduces_available_space(self):
        a = _node(Rect(0, 0, 0, 30))
        layout = FlexLayout(direction=FlexDirection.ROW, padding=20)
        layout.items = [FlexItem(a, grow=1, basis=0)]
        layout.apply(Rect(0, 0, 200, 50))
        # padding of 20 on each side: 200 - 40 = 160
        self.assertEqual(a.rect.width, 160)
        self.assertEqual(a.rect.x, 20)


class TestFlexLayoutColumn(unittest.TestCase):

    def test_column_stacks_vertically(self):
        a = _node(Rect(0, 0, 100, 40))
        b = _node(Rect(0, 0, 100, 60))
        layout = FlexLayout(direction=FlexDirection.COLUMN, gap=0)
        layout.items = [FlexItem(a, grow=0, basis=40), FlexItem(b, grow=0, basis=60)]
        layout.apply(Rect(0, 0, 100, 200))
        self.assertEqual(a.rect.y, 0)
        self.assertEqual(a.rect.height, 40)
        self.assertEqual(b.rect.y, 40)
        self.assertEqual(b.rect.height, 60)

    def test_column_gap_applied(self):
        a = _node(Rect(0, 0, 100, 40))
        b = _node(Rect(0, 0, 100, 40))
        layout = FlexLayout(direction=FlexDirection.COLUMN, gap=8)
        layout.items = [FlexItem(a, grow=0, basis=40), FlexItem(b, grow=0, basis=40)]
        layout.apply(Rect(0, 0, 100, 200))
        self.assertEqual(b.rect.y, 40 + 8)

    def test_column_grow_fills_height(self):
        a = _node(Rect(0, 0, 100, 0))
        layout = FlexLayout(direction=FlexDirection.COLUMN)
        layout.items = [FlexItem(a, grow=1, basis=0)]
        layout.apply(Rect(0, 0, 100, 200))
        self.assertEqual(a.rect.height, 200)


class TestFlexLayoutAlign(unittest.TestCase):

    def test_align_center_centers_cross_axis(self):
        a = _node(Rect(0, 0, 60, 20))
        layout = FlexLayout(direction=FlexDirection.ROW, align=FlexAlign.CENTER)
        layout.items = [FlexItem(a, grow=0, basis=60)]
        layout.apply(Rect(0, 0, 200, 60))
        # Cross axis centering: y = (60 - 20) // 2 = 20
        self.assertEqual(a.rect.y, 20)

    def test_align_stretch_fills_cross_axis(self):
        a = _node(Rect(0, 0, 60, 20))
        layout = FlexLayout(direction=FlexDirection.ROW, align=FlexAlign.STRETCH)
        layout.items = [FlexItem(a, grow=0, basis=60)]
        layout.apply(Rect(0, 0, 200, 60))
        self.assertEqual(a.rect.height, 60)

    def test_align_self_overrides_container_align(self):
        a = _node(Rect(0, 0, 60, 20))
        b = _node(Rect(0, 0, 60, 20))
        layout = FlexLayout(direction=FlexDirection.ROW, align=FlexAlign.START)
        layout.items = [
            FlexItem(a, grow=0, basis=60),
            FlexItem(b, grow=0, basis=60, align_self=FlexAlign.END),
        ]
        layout.apply(Rect(0, 0, 200, 60))
        self.assertEqual(a.rect.y, 0)  # start
        self.assertEqual(b.rect.y, 40)  # end: 60 - 20 = 40


class TestFlexLayoutJustify(unittest.TestCase):

    def test_justify_center_centers_content(self):
        a = _node(Rect(0, 0, 50, 30))
        layout = FlexLayout(direction=FlexDirection.ROW, justify=FlexJustify.CENTER)
        layout.items = [FlexItem(a, grow=0, basis=50)]
        layout.apply(Rect(0, 0, 200, 50))
        # (200 - 50) / 2 = 75
        self.assertAlmostEqual(a.rect.x, 75, delta=1)

    def test_justify_end_aligns_to_end(self):
        a = _node(Rect(0, 0, 50, 30))
        layout = FlexLayout(direction=FlexDirection.ROW, justify=FlexJustify.END)
        layout.items = [FlexItem(a, grow=0, basis=50)]
        layout.apply(Rect(0, 0, 200, 50))
        # 200 - 50 = 150
        self.assertAlmostEqual(a.rect.x, 150, delta=1)

    def test_justify_space_between_two_items(self):
        a = _node(Rect(0, 0, 50, 30))
        b = _node(Rect(0, 0, 50, 30))
        layout = FlexLayout(direction=FlexDirection.ROW, justify=FlexJustify.SPACE_BETWEEN)
        layout.items = [FlexItem(a, grow=0, basis=50), FlexItem(b, grow=0, basis=50)]
        layout.apply(Rect(0, 0, 200, 50))
        self.assertEqual(a.rect.x, 0)
        self.assertAlmostEqual(b.rect.x, 150, delta=1)


class TestFlexLayoutHelpers(unittest.TestCase):

    def test_add_returns_flex_item(self):
        layout = FlexLayout()
        node = _node(Rect(0, 0, 50, 30))
        item = layout.add(node, grow=1)
        self.assertIsInstance(item, FlexItem)
        self.assertIn(item, layout.items)

    def test_remove_returns_true_when_found(self):
        layout = FlexLayout()
        node = _node(Rect(0, 0, 50, 30))
        layout.add(node)
        result = layout.remove(node)
        self.assertTrue(result)
        self.assertEqual(len(layout.items), 0)

    def test_remove_returns_false_when_not_found(self):
        layout = FlexLayout()
        node = _node(Rect(0, 0, 50, 30))
        self.assertFalse(layout.remove(node))

    def test_clear_removes_all(self):
        layout = FlexLayout()
        layout.add(_node(Rect(0, 0, 50, 30)))
        layout.add(_node(Rect(0, 0, 50, 30)))
        layout.clear()
        self.assertEqual(len(layout.items), 0)

    def test_empty_items_apply_is_noop(self):
        layout = FlexLayout()
        layout.apply(Rect(0, 0, 200, 50))  # should not raise


if __name__ == "__main__":
    unittest.main()
