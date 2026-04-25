"""Tests for UiNode positional helpers: is_root, depth, sibling_index."""
import unittest

from pygame import Rect

from gui.core.ui_node import UiNode


def _node(control_id: str = "n") -> UiNode:
    return UiNode(control_id, Rect(0, 0, 10, 10))


def _attach(parent: UiNode, child: UiNode) -> None:
    child.parent = parent
    parent.children.append(child)


class IsRootTests(unittest.TestCase):

    def test_fresh_node_is_root(self) -> None:
        n = _node()
        self.assertTrue(n.is_root())

    def test_child_node_is_not_root(self) -> None:
        parent = _node("parent")
        child = _node("child")
        _attach(parent, child)
        self.assertFalse(child.is_root())

    def test_parent_itself_is_root(self) -> None:
        parent = _node("parent")
        child = _node("child")
        _attach(parent, child)
        self.assertTrue(parent.is_root())

    def test_grandchild_is_not_root(self) -> None:
        root = _node("root")
        mid = _node("mid")
        leaf = _node("leaf")
        _attach(root, mid)
        _attach(mid, leaf)
        self.assertFalse(leaf.is_root())


class DepthTests(unittest.TestCase):

    def test_root_has_depth_zero(self) -> None:
        n = _node()
        self.assertEqual(n.depth(), 0)

    def test_direct_child_has_depth_one(self) -> None:
        parent = _node("parent")
        child = _node("child")
        _attach(parent, child)
        self.assertEqual(child.depth(), 1)

    def test_grandchild_has_depth_two(self) -> None:
        root = _node("root")
        mid = _node("mid")
        leaf = _node("leaf")
        _attach(root, mid)
        _attach(mid, leaf)
        self.assertEqual(leaf.depth(), 2)

    def test_parent_depth_unchanged_after_adding_child(self) -> None:
        parent = _node("parent")
        child = _node("child")
        _attach(parent, child)
        self.assertEqual(parent.depth(), 0)

    def test_depth_four_levels(self) -> None:
        nodes = [_node(f"n{i}") for i in range(5)]
        for i in range(4):
            _attach(nodes[i], nodes[i + 1])
        self.assertEqual(nodes[4].depth(), 4)


class SiblingIndexTests(unittest.TestCase):

    def test_root_sibling_index_is_zero(self) -> None:
        n = _node()
        self.assertEqual(n.sibling_index(), 0)

    def test_only_child_is_index_zero(self) -> None:
        parent = _node("parent")
        child = _node("child")
        _attach(parent, child)
        self.assertEqual(child.sibling_index(), 0)

    def test_second_child_is_index_one(self) -> None:
        parent = _node("parent")
        c0 = _node("c0")
        c1 = _node("c1")
        _attach(parent, c0)
        _attach(parent, c1)
        self.assertEqual(c0.sibling_index(), 0)
        self.assertEqual(c1.sibling_index(), 1)

    def test_third_child_is_index_two(self) -> None:
        parent = _node("parent")
        c0, c1, c2 = _node("c0"), _node("c1"), _node("c2")
        for c in (c0, c1, c2):
            _attach(parent, c)
        self.assertEqual(c2.sibling_index(), 2)

    def test_sibling_index_at_different_depths(self) -> None:
        root = _node("root")
        mid = _node("mid")
        leaf_a = _node("leaf_a")
        leaf_b = _node("leaf_b")
        _attach(root, mid)
        _attach(mid, leaf_a)
        _attach(mid, leaf_b)
        self.assertEqual(leaf_a.sibling_index(), 0)
        self.assertEqual(leaf_b.sibling_index(), 1)


if __name__ == "__main__":
    unittest.main()
