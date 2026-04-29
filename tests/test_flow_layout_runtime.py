"""Tests for FlowLayout and FlowItem."""
import unittest
from unittest.mock import MagicMock

import pygame
from pygame import Rect

from gui_do.layout.flow_layout import FlowLayout, FlowItem, FlowRow
from gui_do.controls.base.ui_node import UiNode


def _node(w: int, h: int, x: int = 0, y: int = 0) -> UiNode:
    return UiNode("n", Rect(x, y, w, h))


class TestFlowItemDataclass(unittest.TestCase):
    def test_node_stored(self) -> None:
        node = _node(50, 30)
        item = FlowItem(node=node)
        self.assertIs(item.node, node)

    def test_defaults_are_none(self) -> None:
        item = FlowItem(node=_node(10, 10))
        self.assertIsNone(item.min_width)
        self.assertIsNone(item.max_width)
        self.assertIsNone(item.min_height)
        self.assertIsNone(item.max_height)


class TestFlowRowItemCount(unittest.TestCase):
    def test_item_count_matches_entries(self) -> None:
        row = FlowRow(items=[FlowItem(node=_node(10, 10)), FlowItem(node=_node(20, 10))])
        self.assertEqual(row.item_count, 2)


class TestFlowLayoutAddRemoveClear(unittest.TestCase):
    def test_add_item(self) -> None:
        layout = FlowLayout(gap_x=4, gap_y=4)
        layout.add(FlowItem(node=_node(50, 30)))
        self.assertEqual(len(layout._items), 1)

    def test_remove_item(self) -> None:
        layout = FlowLayout(gap_x=4, gap_y=4)
        item = FlowItem(node=_node(50, 30))
        layout.add(item)
        layout.remove(item)
        self.assertEqual(len(layout._items), 0)

    def test_clear(self) -> None:
        layout = FlowLayout(gap_x=4, gap_y=4)
        layout.add(FlowItem(node=_node(50, 30)))
        layout.add(FlowItem(node=_node(50, 30)))
        layout.clear()
        self.assertEqual(len(layout._items), 0)


class TestFlowLayoutApplyRow(unittest.TestCase):
    def test_single_item_positioned_at_container_origin(self) -> None:
        layout = FlowLayout(gap_x=0, gap_y=0)
        node = _node(50, 30)
        layout.add(FlowItem(node=node))
        container = Rect(10, 20, 200, 200)
        layout.apply(container)
        self.assertEqual(node.rect.left, 10)
        self.assertEqual(node.rect.top, 20)

    def test_items_laid_out_left_to_right(self) -> None:
        layout = FlowLayout(gap_x=0, gap_y=0)
        n1 = _node(60, 30)
        n2 = _node(60, 30)
        layout.add(FlowItem(node=n1))
        layout.add(FlowItem(node=n2))
        container = Rect(0, 0, 200, 200)
        layout.apply(container)
        self.assertEqual(n1.rect.left, 0)
        self.assertEqual(n2.rect.left, 60)

    def test_wraps_when_container_too_narrow(self) -> None:
        layout = FlowLayout(gap_x=0, gap_y=0)
        n1 = _node(70, 30)
        n2 = _node(70, 30)
        layout.add(FlowItem(node=n1))
        layout.add(FlowItem(node=n2))
        container = Rect(0, 0, 100, 200)  # too narrow for both side-by-side
        layout.apply(container)
        # n2 should be on a new row
        self.assertEqual(n2.rect.top, 30)

    def test_gap_applied_between_items(self) -> None:
        layout = FlowLayout(gap_x=10, gap_y=0)
        n1 = _node(50, 30)
        n2 = _node(50, 30)
        layout.add(FlowItem(node=n1))
        layout.add(FlowItem(node=n2))
        container = Rect(0, 0, 200, 200)
        layout.apply(container)
        # n2 starts at 50 + 10 (gap)
        self.assertEqual(n2.rect.left, 60)

    def test_apply_returns_used_height(self) -> None:
        layout = FlowLayout(gap_x=0, gap_y=0)
        layout.add(FlowItem(node=_node(50, 30)))
        height = layout.apply(Rect(0, 0, 200, 200))
        self.assertIsInstance(height, int)
        self.assertGreater(height, 0)


class TestFlowLayoutRows(unittest.TestCase):
    def test_rows_returns_list_of_flow_row(self) -> None:
        layout = FlowLayout(gap_x=0, gap_y=0)
        layout.add(FlowItem(node=_node(50, 30)))
        layout.apply(Rect(0, 0, 200, 200))
        rows = layout.rows()
        self.assertIsInstance(rows, list)
        self.assertTrue(len(rows) >= 1)
        self.assertIsInstance(rows[0], FlowRow)
