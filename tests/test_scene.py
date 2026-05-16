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


class _OrderTrackingNode(UiNode):
    def __init__(self, control_id, order_log):
        super().__init__(control_id, Rect(0, 0, 10, 10))
        self._order_log = order_log

    def draw_screen_phase(self, surface, theme, app=None):
        self._order_log.append(f"{self.control_id}:screen")

    def draw_window_phase(self, surface, theme, app=None):
        self._order_log.append(f"{self.control_id}:window")


class _StubFocus:
    def __init__(self, focused_node):
        self.focused_node = focused_node


class _StubFocusVisualizer:
    def draw_hint_for_scene_root(self, surface, theme, node):
        return None

    def draw_window_focus_hint(self, surface, theme):
        return None


class _StubApp:
    def __init__(self, focused_node):
        self.focus = _StubFocus(focused_node)
        self.focus_visualizer = _StubFocusVisualizer()


class TestSceneDrawOrder(unittest.TestCase):
    def test_focused_descendant_not_drawn_as_scene_root(self):
        scene = Scene()
        draw_order = []
        root = _OrderTrackingNode("root", draw_order)
        focused_descendant = _OrderTrackingNode("child", draw_order)
        root.add_child(focused_descendant)
        scene.add(root)

        surface = pygame.Surface((64, 64))
        app = _StubApp(focused_descendant)

        scene.draw(surface, theme=None, app=app)

        self.assertEqual(["root:screen", "root:window"], draw_order)

    def test_focused_scene_root_drawn_last(self):
        scene = Scene()
        draw_order = []
        first = _OrderTrackingNode("first", draw_order)
        focused_root = _OrderTrackingNode("focused", draw_order)
        scene.add(first)
        scene.add(focused_root)

        surface = pygame.Surface((64, 64))
        app = _StubApp(focused_root)

        scene.draw(surface, theme=None, app=app)

        self.assertEqual(
            ["first:screen", "first:window", "focused:screen", "focused:window"],
            draw_order,
        )


if __name__ == "__main__":
    unittest.main()
