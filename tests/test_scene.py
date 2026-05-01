"""Tests for Scene (scene graph container)."""
import unittest
import pygame
from pygame import Rect

from gui_do.app.scene import Scene
from gui_do.controls.base.ui_node import UiNode

pygame.init()


def _node(control_id="node", rect=None):
    return UiNode(control_id, rect or Rect(0, 0, 50, 50))


# ===========================================================================
# Scene — initial state
# ===========================================================================


class TestSceneInitial(unittest.TestCase):
    def test_nodes_empty(self):
        scene = Scene()
        self.assertEqual([], scene.nodes)


# ===========================================================================
# Scene.add
# ===========================================================================


class TestSceneAdd(unittest.TestCase):
    def test_add_appends_node(self):
        scene = Scene()
        node = _node("a")
        scene.add(node)
        self.assertIn(node, scene.nodes)

    def test_add_returns_node(self):
        scene = Scene()
        node = _node("a")
        result = scene.add(node)
        self.assertIs(node, result)

    def test_add_sets_parent_none(self):
        scene = Scene()
        node = _node("a")
        scene.add(node)
        self.assertIsNone(node.parent)

    def test_add_multiple(self):
        scene = Scene()
        a, b, c = _node("a"), _node("b"), _node("c")
        scene.add(a)
        scene.add(b)
        scene.add(c)
        self.assertEqual(3, len(scene.nodes))


# ===========================================================================
# Scene.remove
# ===========================================================================


class TestSceneRemove(unittest.TestCase):
    def test_remove_returns_true(self):
        scene = Scene()
        node = _node("a")
        scene.add(node)
        result = scene.remove(node)
        self.assertTrue(result)

    def test_remove_clears_from_nodes(self):
        scene = Scene()
        node = _node("a")
        scene.add(node)
        scene.remove(node)
        self.assertNotIn(node, scene.nodes)

    def test_remove_missing_returns_false(self):
        scene = Scene()
        node = _node("a")
        result = scene.remove(node)
        self.assertFalse(result)


# ===========================================================================
# Scene.find
# ===========================================================================


class TestSceneFind(unittest.TestCase):
    def test_find_existing(self):
        scene = Scene()
        node = _node("target")
        scene.add(node)
        found = scene.find("target")
        self.assertIs(node, found)

    def test_find_missing_returns_none(self):
        scene = Scene()
        result = scene.find("nonexistent")
        self.assertIsNone(result)

    def test_find_child_descendant(self):
        scene = Scene()
        parent_node = _node("parent")
        child_node = _node("child")
        parent_node.add_child(child_node)
        scene.add(parent_node)
        found = scene.find("child")
        self.assertIs(child_node, found)


# ===========================================================================
# Scene.find_all
# ===========================================================================


class TestSceneFindAll(unittest.TestCase):
    def test_find_all_matching(self):
        scene = Scene()
        a = _node("a")
        b = _node("b")
        scene.add(a)
        scene.add(b)
        result = scene.find_all(lambda n: n.control_id.startswith("a"))
        self.assertEqual([a], result)

    def test_find_all_empty(self):
        scene = Scene()
        result = scene.find_all(lambda n: True)
        self.assertEqual([], result)


# ===========================================================================
# Scene.contains
# ===========================================================================


class TestSceneContains(unittest.TestCase):
    def test_contains_root_node(self):
        scene = Scene()
        node = _node("root")
        scene.add(node)
        self.assertTrue(scene.contains(node))

    def test_contains_child(self):
        scene = Scene()
        parent_node = _node("parent")
        child = _node("child")
        parent_node.add_child(child)
        scene.add(parent_node)
        self.assertTrue(scene.contains(child))

    def test_not_contains_unregistered(self):
        scene = Scene()
        node = _node("x")
        self.assertFalse(scene.contains(node))


if __name__ == "__main__":
    unittest.main()
