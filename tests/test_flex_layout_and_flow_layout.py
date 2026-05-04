"""Tests for FlexLayout and FlowLayout.

Both are pure geometry engines — they mutate node.rect attributes.
Nodes are stubbed as SimpleNamespace(rect=Rect(...)).
"""
import unittest
from types import SimpleNamespace

from pygame import Rect

from gui_do.layout.flex_layout import (
    FlexLayout, FlexItem, FlexDirection, FlexAlign, FlexJustify,
)
from gui_do.layout.flow_layout import FlowLayout, FlowItem


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _node(w: int, h: int, x: int = 0, y: int = 0) -> SimpleNamespace:
    """A minimal node stub — just needs a mutable `rect`."""
    return SimpleNamespace(rect=Rect(x, y, w, h))


def _flex_item(w: int, h: int, **kwargs) -> FlexItem:
    return FlexItem(node=_node(w, h), **kwargs)


def _flow_item(w: int, h: int, **kwargs) -> FlowItem:
    return FlowItem(node=_node(w, h), **kwargs)


CONTAINER = Rect(0, 0, 400, 200)


# ===========================================================================
# FlexLayout — ROW direction
# ===========================================================================


class TestFlexLayoutRowBasic(unittest.TestCase):
    def _layout(self, *items, gap=0, **kw):
        layout = FlexLayout(direction=FlexDirection.ROW, gap=gap, **kw)
        layout.items = list(items)
        layout.apply(CONTAINER)
        return layout

    def test_empty_no_error(self):
        layout = FlexLayout()
        layout.apply(CONTAINER)  # should not raise

    def test_single_item_starts_at_container_x(self):
        item = _flex_item(80, 40)
        self._layout(item)
        self.assertEqual(0, item.node.rect.x)

    def test_single_item_starts_at_container_y(self):
        item = _flex_item(80, 40)
        self._layout(item)
        self.assertEqual(0, item.node.rect.y)

    def test_gap_offsets_second_item(self):
        a = _flex_item(80, 40)
        b = _flex_item(80, 40)
        self._layout(a, b, gap=8)
        self.assertEqual(88, b.node.rect.x)   # 80 + 8

    def test_basis_overrides_node_width(self):
        item = _flex_item(80, 40, basis=100)
        self._layout(item)
        self.assertEqual(100, item.node.rect.width)

    def test_grow_distributes_surplus(self):
        a = _flex_item(100, 40, grow=1)
        b = _flex_item(100, 40, grow=1)
        self._layout(a, b, gap=0)
        # 400 total, 2 items share it equally
        self.assertEqual(200, a.node.rect.width)
        self.assertEqual(200, b.node.rect.width)

    def test_grow_proportional(self):
        a = _flex_item(0, 40, grow=1, basis=0)
        b = _flex_item(0, 40, grow=3, basis=0)
        self._layout(a, b, gap=0)
        self.assertAlmostEqual(100, a.node.rect.width, delta=1)
        self.assertAlmostEqual(300, b.node.rect.width, delta=1)

    def test_max_size_caps_grow(self):
        a = _flex_item(0, 40, grow=1, basis=0, max_size=50)
        self._layout(a, gap=0)
        self.assertLessEqual(a.node.rect.width, 50)

    def test_min_size_floors_shrink(self):
        a = _flex_item(600, 40, shrink=1, min_size=100)
        self._layout(a, gap=0)
        self.assertGreaterEqual(a.node.rect.width, 100)

    def test_add_helper(self):
        layout = FlexLayout()
        n = _node(50, 50)
        item = layout.add(n, grow=1)
        self.assertIsInstance(item, FlexItem)
        self.assertIs(n, item.node)
        self.assertEqual(1, len(layout.items))

    def test_remove_helper(self):
        layout = FlexLayout()
        n = _node(50, 50)
        layout.add(n)
        removed = layout.remove(n)
        self.assertTrue(removed)
        self.assertEqual(0, len(layout.items))

    def test_remove_missing_returns_false(self):
        layout = FlexLayout()
        self.assertFalse(layout.remove(_node(10, 10)))

    def test_clear_removes_all(self):
        layout = FlexLayout()
        layout.add(_node(50, 50))
        layout.add(_node(50, 50))
        layout.clear()
        self.assertEqual(0, len(layout.items))


class TestFlexLayoutRowAlign(unittest.TestCase):
    def _apply(self, align, item):
        layout = FlexLayout(direction=FlexDirection.ROW, align=align)
        layout.items = [item]
        layout.apply(CONTAINER)

    def test_align_start_y_at_zero(self):
        item = _flex_item(80, 40)
        self._apply(FlexAlign.START, item)
        self.assertEqual(0, item.node.rect.y)

    def test_align_center(self):
        item = _flex_item(80, 40)
        self._apply(FlexAlign.CENTER, item)
        expected_y = (CONTAINER.height - 40) // 2
        self.assertEqual(expected_y, item.node.rect.y)

    def test_align_end(self):
        item = _flex_item(80, 40)
        self._apply(FlexAlign.END, item)
        expected_y = CONTAINER.height - 40
        self.assertEqual(expected_y, item.node.rect.y)

    def test_align_stretch(self):
        item = _flex_item(80, 40)
        self._apply(FlexAlign.STRETCH, item)
        self.assertEqual(CONTAINER.height, item.node.rect.height)


class TestFlexLayoutJustify(unittest.TestCase):
    def _apply_two(self, justify):
        a = _flex_item(80, 40)
        b = _flex_item(80, 40)
        layout = FlexLayout(direction=FlexDirection.ROW, justify=justify, gap=0)
        layout.items = [a, b]
        layout.apply(CONTAINER)
        return a, b

    def test_justify_start(self):
        a, b = self._apply_two(FlexJustify.START)
        self.assertEqual(0, a.node.rect.x)
        self.assertEqual(80, b.node.rect.x)

    def test_justify_end(self):
        a, b = self._apply_two(FlexJustify.END)
        # a.right should be at 320, b.right at 400
        self.assertEqual(400, b.node.rect.right)

    def test_justify_center(self):
        a, b = self._apply_two(FlexJustify.CENTER)
        # total content = 160, surplus = 240; each side gets 120
        self.assertGreater(a.node.rect.x, 0)

    def test_justify_space_between_two_items(self):
        a, b = self._apply_two(FlexJustify.SPACE_BETWEEN)
        self.assertEqual(0, a.node.rect.x)
        self.assertEqual(CONTAINER.width - 80, b.node.rect.x)


class TestFlexLayoutColumn(unittest.TestCase):
    def test_column_stacks_vertically(self):
        a = _flex_item(80, 50)
        b = _flex_item(80, 50)
        layout = FlexLayout(direction=FlexDirection.COLUMN, gap=10)
        layout.items = [a, b]
        layout.apply(CONTAINER)
        self.assertEqual(0, a.node.rect.y)
        self.assertEqual(60, b.node.rect.y)  # 50 + 10

    def test_column_grow_vertical(self):
        a = _flex_item(80, 0, grow=1, basis=0)
        b = _flex_item(80, 0, grow=1, basis=0)
        layout = FlexLayout(direction=FlexDirection.COLUMN, gap=0)
        layout.items = [a, b]
        layout.apply(CONTAINER)
        self.assertEqual(100, a.node.rect.height)
        self.assertEqual(100, b.node.rect.height)


class TestFlexLayoutPadding(unittest.TestCase):
    def test_padding_reduces_available_space(self):
        item = _flex_item(0, 40, grow=1, basis=0)
        layout = FlexLayout(direction=FlexDirection.ROW, padding=10)
        layout.items = [item]
        layout.apply(CONTAINER)
        self.assertEqual(380, item.node.rect.width)  # 400 - 2*10

    def test_padding_offsets_start_x(self):
        item = _flex_item(100, 40)
        layout = FlexLayout(direction=FlexDirection.ROW, padding=20)
        layout.items = [item]
        layout.apply(CONTAINER)
        self.assertEqual(20, item.node.rect.x)

    def test_apply_accepts_callable_rect_source(self):
        item = _flex_item(100, 40)
        layout = FlexLayout(direction=FlexDirection.ROW)
        layout.items = [item]
        layout.apply(lambda: Rect(10, 20, 200, 120))
        self.assertEqual(10, item.node.rect.x)
        self.assertEqual(20, item.node.rect.y)


# ===========================================================================
# FlowLayout
# ===========================================================================


class TestFlowLayoutRowBasic(unittest.TestCase):
    def setUp(self):
        self.layout = FlowLayout(gap_x=0, gap_y=0)

    def test_empty_apply_returns_zero(self):
        result = self.layout.apply(Rect(0, 0, 200, 200))
        self.assertEqual(0, result)

    def test_empty_rows_empty(self):
        self.layout.apply(Rect(0, 0, 200, 200))
        self.assertEqual([], self.layout.rows())

    def test_single_item_placed_at_origin(self):
        item = _flow_item(60, 30)
        self.layout.add(item)
        self.layout.apply(Rect(0, 0, 200, 200))
        self.assertEqual(0, item.node.rect.x)
        self.assertEqual(0, item.node.rect.y)

    def test_two_items_same_row(self):
        a = _flow_item(60, 30)
        b = _flow_item(60, 30)
        self.layout.add(a)
        self.layout.add(b)
        self.layout.apply(Rect(0, 0, 200, 200))
        self.assertEqual(0, a.node.rect.x)
        self.assertEqual(60, b.node.rect.x)
        self.assertEqual(1, len(self.layout.rows()))

    def test_overflow_wraps_to_second_row(self):
        a = _flow_item(120, 30)
        b = _flow_item(120, 30)
        self.layout.add(a)
        self.layout.add(b)
        self.layout.apply(Rect(0, 0, 200, 200))
        rows = self.layout.rows()
        self.assertEqual(2, len(rows))
        self.assertEqual(30, b.node.rect.y)  # second row starts at y=row_h of first

    def test_gap_x_separates_items(self):
        layout = FlowLayout(gap_x=10, gap_y=0)
        a = _flow_item(60, 30)
        b = _flow_item(60, 30)
        layout.add(a)
        layout.add(b)
        layout.apply(Rect(0, 0, 200, 200))
        self.assertEqual(70, b.node.rect.x)   # 60 + 10

    def test_gap_y_separates_rows(self):
        layout = FlowLayout(gap_x=0, gap_y=8)
        a = _flow_item(150, 30)
        b = _flow_item(150, 30)
        layout.add(a)
        layout.add(b)
        layout.apply(Rect(0, 0, 200, 200))
        self.assertEqual(38, b.node.rect.y)   # 30 + 8

    def test_total_height_returned(self):
        layout = FlowLayout(gap_x=0, gap_y=0)
        a = _flow_item(60, 30)
        layout.add(a)
        h = layout.apply(Rect(0, 0, 200, 200))
        self.assertEqual(30, h)

    def test_two_rows_total_height(self):
        layout = FlowLayout(gap_x=0, gap_y=10)
        a = _flow_item(150, 30)
        b = _flow_item(150, 30)
        layout.add(a)
        layout.add(b)
        h = layout.apply(Rect(0, 0, 200, 200))
        self.assertEqual(70, h)  # 30 + 10 + 30

    def test_apply_accepts_callable_rect_source(self):
        item = _flow_item(60, 30)
        self.layout.add(item)
        self.layout.apply(lambda: Rect(25, 15, 200, 100))
        self.assertEqual(25, item.node.rect.x)
        self.assertEqual(15, item.node.rect.y)


class TestFlowLayoutItemManagement(unittest.TestCase):
    def setUp(self):
        self.layout = FlowLayout()

    def test_add_item(self):
        item = _flow_item(60, 30)
        self.layout.add(item)
        self.assertIn(item, self.layout.items)

    def test_remove_item(self):
        item = _flow_item(60, 30)
        self.layout.add(item)
        result = self.layout.remove(item)
        self.assertTrue(result)
        self.assertNotIn(item, self.layout.items)

    def test_remove_missing_returns_false(self):
        self.assertFalse(self.layout.remove(_flow_item(10, 10)))

    def test_clear_removes_all(self):
        self.layout.add(_flow_item(60, 30))
        self.layout.add(_flow_item(60, 30))
        self.layout.clear()
        self.assertEqual([], self.layout.items)


class TestFlowLayoutAlignCenter(unittest.TestCase):
    def test_align_center_positions_shorter_item_correctly(self):
        layout = FlowLayout(gap_x=0, gap_y=0, align="center")
        tall = _flow_item(60, 60)
        short = _flow_item(60, 20)
        layout.add(tall)
        layout.add(short)
        layout.apply(Rect(0, 0, 200, 200))
        # Row height is 60; short item centered: y = (60 - 20) // 2 = 20
        self.assertEqual(20, short.node.rect.y)

    def test_align_end_positions_shorter_item_at_bottom(self):
        layout = FlowLayout(gap_x=0, gap_y=0, align="end")
        tall = _flow_item(60, 60)
        short = _flow_item(60, 20)
        layout.add(tall)
        layout.add(short)
        layout.apply(Rect(0, 0, 200, 200))
        # Row height 60; short at y = 60 - 20 = 40
        self.assertEqual(40, short.node.rect.y)


class TestFlowLayoutMinMaxConstraints(unittest.TestCase):
    def test_min_width_applied(self):
        layout = FlowLayout(gap_x=0, gap_y=0)
        item = _flow_item(20, 30, min_width=100)
        layout.add(item)
        layout.apply(Rect(0, 0, 400, 200))
        self.assertEqual(100, item.node.rect.width)

    def test_max_width_applied(self):
        layout = FlowLayout(gap_x=0, gap_y=0)
        item = _flow_item(200, 30, max_width=80)
        layout.add(item)
        layout.apply(Rect(0, 0, 400, 200))
        self.assertEqual(80, item.node.rect.width)


class TestFlowLayoutInvalidDirection(unittest.TestCase):
    def test_invalid_direction_raises(self):
        with self.assertRaises(ValueError):
            FlowLayout(direction="diagonal")

    def test_invalid_align_raises(self):
        with self.assertRaises(ValueError):
            FlowLayout(align="justify")


if __name__ == "__main__":
    unittest.main()
