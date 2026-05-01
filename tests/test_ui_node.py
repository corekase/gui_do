"""Tests for UiNode (base node) tree traversal, geometry, and state helpers."""
import unittest
import pygame
from pygame import Rect

from gui_do.controls.base.ui_node import UiNode

pygame.init()


def _node(control_id="node", rect=None):
    return UiNode(control_id, rect or Rect(0, 0, 50, 50))


# ===========================================================================
# UiNode — initial state
# ===========================================================================


class TestUiNodeInitial(unittest.TestCase):
    def test_control_id_stored(self):
        n = _node("my_button")
        self.assertEqual("my_button", n.control_id)

    def test_rect_stored(self):
        n = UiNode("x", Rect(10, 20, 100, 50))
        self.assertEqual(Rect(10, 20, 100, 50), n.rect)

    def test_visible_true_by_default(self):
        n = _node()
        self.assertTrue(n.visible)

    def test_enabled_true_by_default(self):
        n = _node()
        self.assertTrue(n.enabled)

    def test_parent_none(self):
        n = _node()
        self.assertIsNone(n.parent)

    def test_children_empty(self):
        n = _node()
        self.assertEqual([], n.children)

    def test_tab_index_minus_one(self):
        n = _node()
        self.assertEqual(-1, n.tab_index)

    def test_accessibility_role_default(self):
        n = _node()
        self.assertEqual("control", n.accessibility_role)

    def test_is_root_true(self):
        n = _node()
        self.assertTrue(n.is_root())

    def test_depth_zero(self):
        n = _node()
        self.assertEqual(0, n.depth())


# ===========================================================================
# UiNode — visibility / enabled
# ===========================================================================


class TestUiNodeVisibility(unittest.TestCase):
    def test_hide(self):
        n = _node()
        n.hide()
        self.assertFalse(n.visible)

    def test_show(self):
        n = _node()
        n.hide()
        n.show()
        self.assertTrue(n.visible)

    def test_disable(self):
        n = _node()
        n.disable()
        self.assertFalse(n.enabled)

    def test_enable(self):
        n = _node()
        n.disable()
        n.enable()
        self.assertTrue(n.enabled)


# ===========================================================================
# UiNode — geometry
# ===========================================================================


class TestUiNodeGeometry(unittest.TestCase):
    def test_set_pos(self):
        n = _node()
        n.set_pos(100, 200)
        self.assertEqual(100, n.rect.x)
        self.assertEqual(200, n.rect.y)

    def test_resize(self):
        n = _node()
        n.resize(300, 150)
        self.assertEqual(300, n.rect.width)
        self.assertEqual(150, n.rect.height)

    def test_set_rect(self):
        n = _node()
        new_rect = Rect(5, 10, 200, 100)
        n.set_rect(new_rect)
        self.assertEqual(new_rect, n.rect)

    def test_hit_test_inside(self):
        n = UiNode("x", Rect(0, 0, 100, 100))
        self.assertTrue(n.hit_test((50, 50)))

    def test_hit_test_outside(self):
        n = UiNode("x", Rect(0, 0, 100, 100))
        self.assertFalse(n.hit_test((150, 50)))


# ===========================================================================
# UiNode — accessibility
# ===========================================================================


class TestUiNodeAccessibility(unittest.TestCase):
    def test_set_accessibility_role(self):
        n = _node()
        n.set_accessibility(role="button")
        self.assertEqual("button", n.accessibility_role)

    def test_set_accessibility_label(self):
        n = _node()
        n.set_accessibility(label="Save file")
        self.assertEqual("Save file", n.accessibility_label)

    def test_set_tab_index(self):
        n = _node()
        n.set_tab_index(3)
        self.assertEqual(3, n.tab_index)


# ===========================================================================
# UiNode — tree traversal
# ===========================================================================


class TestUiNodeTreeTraversal(unittest.TestCase):
    def test_add_child(self):
        parent = _node("parent")
        child = _node("child")
        parent.add_child(child)
        self.assertIn(child, parent.children)
        self.assertIs(parent, child.parent)

    def test_depth_one_level(self):
        parent = _node("parent")
        child = _node("child")
        parent.add_child(child)
        self.assertEqual(1, child.depth())

    def test_is_root_false_when_has_parent(self):
        parent = _node("parent")
        child = _node("child")
        parent.add_child(child)
        self.assertFalse(child.is_root())

    def test_ancestors_yields_parent(self):
        parent = _node("parent")
        child = _node("child")
        parent.add_child(child)
        ancs = list(child.ancestors())
        self.assertEqual([parent], ancs)

    def test_find_descendant_direct(self):
        parent = _node("parent")
        child = _node("target")
        parent.add_child(child)
        found = parent.find_descendant("target")
        self.assertIs(child, found)

    def test_find_descendant_missing(self):
        parent = _node("parent")
        result = parent.find_descendant("nonexistent")
        self.assertIsNone(result)

    def test_find_descendants_predicate(self):
        parent = _node("parent")
        a = _node("a")
        b = _node("b")
        parent.add_child(a)
        parent.add_child(b)
        result = parent.find_descendants(lambda n: n.control_id == "a")
        self.assertEqual([a], result)

    def test_find_descendants_of_type(self):
        parent = _node("parent")
        child = _node("child")
        parent.add_child(child)
        result = parent.find_descendants_of_type(UiNode)
        self.assertIn(child, result)

    def test_sibling_index(self):
        parent = _node("parent")
        a = _node("a")
        b = _node("b")
        parent.add_child(a)
        parent.add_child(b)
        self.assertEqual(0, a.sibling_index())
        self.assertEqual(1, b.sibling_index())

    def test_sibling_index_root(self):
        n = _node("root")
        self.assertEqual(0, n.sibling_index())


if __name__ == "__main__":
    unittest.main()
