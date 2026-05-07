"""Tests for gui_do.graphics.scene_graph_2d (S4)."""
import unittest
from unittest.mock import MagicMock

from gui_do.graphics.scene_graph_2d import Node2D, SceneGraph2D, Camera2D


# Fake pygame.Rect substitute
class FakeRect:
    def __init__(self, x, y, w, h):
        self.x, self.y, self.width, self.height = x, y, w, h


class TestCamera2D(unittest.TestCase):

    def _make_camera(self, **kw):
        rect = FakeRect(0, 0, 800, 600)
        return Camera2D(viewport_rect=rect, **kw)

    def test_defaults(self):
        cam = self._make_camera()
        self.assertAlmostEqual(cam.zoom, 1.0)
        self.assertAlmostEqual(cam.x, 0.0)
        self.assertAlmostEqual(cam.y, 0.0)

    def test_world_to_screen_identity(self):
        cam = self._make_camera()
        sx, sy = cam.world_to_screen(100.0, 200.0)
        self.assertAlmostEqual(sx, 100.0)
        self.assertAlmostEqual(sy, 200.0)

    def test_world_to_screen_with_zoom(self):
        cam = self._make_camera(zoom=2.0)
        sx, sy = cam.world_to_screen(50.0, 50.0)
        self.assertAlmostEqual(sx, 100.0)
        self.assertAlmostEqual(sy, 100.0)

    def test_world_to_screen_with_offset(self):
        cam = self._make_camera(x=10.0, y=20.0)
        sx, sy = cam.world_to_screen(10.0, 20.0)
        self.assertAlmostEqual(sx, 0.0)
        self.assertAlmostEqual(sy, 0.0)

    def test_screen_to_world_roundtrip(self):
        cam = self._make_camera(zoom=2.0, x=50.0, y=30.0)
        wx, wy = 123.4, 67.8
        sx, sy = cam.world_to_screen(wx, wy)
        wx2, wy2 = cam.screen_to_world(sx, sy)
        self.assertAlmostEqual(wx2, wx, places=5)
        self.assertAlmostEqual(wy2, wy, places=5)

    def test_pan(self):
        cam = self._make_camera()
        cam.pan(10.0, 20.0)
        self.assertAlmostEqual(cam.x, 10.0)
        self.assertAlmostEqual(cam.y, 20.0)

    def test_pan_screen(self):
        cam = self._make_camera(zoom=2.0)
        cam.pan_screen(100.0, 200.0)  # 50 world units each
        self.assertAlmostEqual(cam.x, 50.0)
        self.assertAlmostEqual(cam.y, 100.0)

    def test_set_zoom(self):
        cam = self._make_camera()
        cam.set_zoom(3.0)
        self.assertAlmostEqual(cam.zoom, 3.0)

    def test_set_zoom_clamps_minimum(self):
        cam = self._make_camera()
        cam.set_zoom(-1.0)
        self.assertGreater(cam.zoom, 0.0)

    def test_set_zoom_with_anchor(self):
        # After zoom with anchor, world point under anchor should not move
        cam = self._make_camera(zoom=1.0, x=0.0, y=0.0)
        anchor = (400.0, 300.0)
        wx_before, wy_before = cam.screen_to_world(*anchor)
        cam.set_zoom(2.0, anchor_screen=anchor)
        wx_after, wy_after = cam.screen_to_world(*anchor)
        self.assertAlmostEqual(wx_before, wx_after, places=4)
        self.assertAlmostEqual(wy_before, wy_after, places=4)


class TestNode2D(unittest.TestCase):

    def test_defaults(self):
        n = Node2D("root")
        self.assertEqual(n.name, "root")
        self.assertAlmostEqual(n.x, 0.0)
        self.assertAlmostEqual(n.y, 0.0)
        self.assertAlmostEqual(n.scale_x, 1.0)
        self.assertAlmostEqual(n.scale_y, 1.0)
        self.assertTrue(n.visible)
        self.assertIsNone(n.on_draw)
        self.assertIsNone(n.parent)
        self.assertEqual(n.children(), [])

    def test_pos_property(self):
        n = Node2D("n", pos=(3.0, 7.0))
        self.assertEqual(n.pos, (3.0, 7.0))

    def test_pos_setter_updates_xy(self):
        n = Node2D("n")
        n.pos = (5.0, 9.0)
        self.assertAlmostEqual(n.x, 5.0)
        self.assertAlmostEqual(n.y, 9.0)

    def test_scale_property(self):
        n = Node2D("n", scale=(2.0, 3.0))
        self.assertEqual(n.scale, (2.0, 3.0))

    def test_world_transform_root(self):
        n = Node2D("n", pos=(10.0, 20.0), scale=(2.0, 3.0))
        wx, wy, wsx, wsy = n.world_transform()
        self.assertAlmostEqual(wx, 10.0)
        self.assertAlmostEqual(wy, 20.0)
        self.assertAlmostEqual(wsx, 2.0)
        self.assertAlmostEqual(wsy, 3.0)

    def test_world_transform_child_inherits(self):
        parent = Node2D("parent", pos=(100.0, 0.0), scale=(2.0, 2.0))
        child = Node2D("child", pos=(5.0, 0.0))
        parent.add_child(child)
        wx, wy, wsx, wsy = child.world_transform()
        self.assertAlmostEqual(wx, 110.0)  # 100 + 5*2
        self.assertAlmostEqual(wy, 0.0)
        self.assertAlmostEqual(wsx, 2.0)
        self.assertAlmostEqual(wsy, 2.0)

    def test_world_transform_cached(self):
        n = Node2D("n", pos=(1.0, 2.0))
        t1 = n.world_transform()
        t2 = n.world_transform()
        self.assertIs(t1, t2)  # Same cached object

    def test_transform_cache_invalidated_on_pos_change(self):
        n = Node2D("n", pos=(0.0, 0.0))
        n.world_transform()
        n.pos = (10.0, 0.0)
        wx, wy, _, _ = n.world_transform()
        self.assertAlmostEqual(wx, 10.0)

    def test_transform_cache_invalidated_on_child_reparent(self):
        parent = Node2D("parent", pos=(50.0, 0.0))
        child = Node2D("child", pos=(1.0, 0.0))
        parent.add_child(child)
        parent.pos = (100.0, 0.0)
        wx, _, _, _ = child.world_transform()
        self.assertAlmostEqual(wx, 101.0)

    def test_add_child_sets_parent(self):
        parent = Node2D("p")
        child = Node2D("c")
        parent.add_child(child)
        self.assertIs(child.parent, parent)
        self.assertIn(child, parent.children())

    def test_add_child_reparents(self):
        p1 = Node2D("p1")
        p2 = Node2D("p2")
        child = Node2D("c")
        p1.add_child(child)
        p2.add_child(child)
        self.assertIs(child.parent, p2)
        self.assertNotIn(child, p1.children())

    def test_remove_child(self):
        parent = Node2D("p")
        child = Node2D("c")
        parent.add_child(child)
        result = parent.remove_child(child)
        self.assertTrue(result)
        self.assertIsNone(child.parent)
        self.assertNotIn(child, parent.children())

    def test_remove_child_returns_false_if_not_found(self):
        parent = Node2D("p")
        self.assertFalse(parent.remove_child(Node2D("x")))

    def test_find_descendant(self):
        root = Node2D("root")
        mid = Node2D("mid")
        leaf = Node2D("leaf")
        root.add_child(mid)
        mid.add_child(leaf)
        self.assertIs(root.find("leaf"), leaf)

    def test_find_returns_none_if_not_found(self):
        n = Node2D("n")
        self.assertIsNone(n.find("missing"))

    def test_draw_calls_on_draw(self):
        calls = []
        n = Node2D("n", pos=(10.0, 20.0))
        n.on_draw = lambda s, x, y, sx, sy: calls.append((x, y))

        surface = MagicMock()
        rect = FakeRect(0, 0, 800, 600)
        cam = Camera2D(viewport_rect=rect)
        n.draw(surface, cam)
        self.assertEqual(len(calls), 1)
        self.assertAlmostEqual(calls[0][0], 10.0)
        self.assertAlmostEqual(calls[0][1], 20.0)

    def test_draw_invisible_node_skipped(self):
        calls = []
        n = Node2D("n", visible=False)
        n.on_draw = lambda s, x, y, sx, sy: calls.append(1)
        surface = MagicMock()
        rect = FakeRect(0, 0, 800, 600)
        cam = Camera2D(viewport_rect=rect)
        n.draw(surface, cam)
        self.assertEqual(calls, [])

    def test_draw_on_draw_exception_does_not_propagate(self):
        def bad(s, x, y, sx, sy):
            raise RuntimeError("boom")
        n = Node2D("n")
        n.on_draw = bad
        surface = MagicMock()
        rect = FakeRect(0, 0, 800, 600)
        cam = Camera2D(viewport_rect=rect)
        n.draw(surface, cam)  # Should not raise


class TestSceneGraph2D(unittest.TestCase):

    def _cam(self):
        return Camera2D(viewport_rect=FakeRect(0, 0, 800, 600))

    def test_initially_empty(self):
        g = SceneGraph2D()
        self.assertEqual(g.root_count, 0)

    def test_add_increases_root_count(self):
        g = SceneGraph2D()
        g.add(Node2D("a"))
        self.assertEqual(g.root_count, 1)

    def test_add_idempotent(self):
        g = SceneGraph2D()
        n = Node2D("n")
        g.add(n)
        g.add(n)
        self.assertEqual(g.root_count, 1)

    def test_remove_decreases_count(self):
        g = SceneGraph2D()
        n = Node2D("n")
        g.add(n)
        self.assertTrue(g.remove(n))
        self.assertEqual(g.root_count, 0)

    def test_remove_returns_false_if_not_found(self):
        g = SceneGraph2D()
        self.assertFalse(g.remove(Node2D("x")))

    def test_clear(self):
        g = SceneGraph2D()
        for i in range(5):
            g.add(Node2D(str(i)))
        g.clear()
        self.assertEqual(g.root_count, 0)

    def test_find_root_node(self):
        g = SceneGraph2D()
        n = Node2D("hero")
        g.add(n)
        self.assertIs(g.find("hero"), n)

    def test_find_descendant(self):
        g = SceneGraph2D()
        root = Node2D("root")
        child = Node2D("child")
        root.add_child(child)
        g.add(root)
        self.assertIs(g.find("child"), child)

    def test_find_missing_returns_none(self):
        g = SceneGraph2D()
        self.assertIsNone(g.find("nope"))

    def test_draw_calls_draw_on_all_roots(self):
        g = SceneGraph2D()
        cam = self._cam()
        surface = MagicMock()
        calls = []

        for name in ("a", "b", "c"):
            n = Node2D(name)
            n.on_draw = lambda s, x, y, sx, sy, _n=name: calls.append(_n)
            g.add(n)

        g.draw(surface, cam)
        self.assertEqual(set(calls), {"a", "b", "c"})

    def test_find_all(self):
        g = SceneGraph2D()
        parent = Node2D("parent")
        child = Node2D("child")
        parent.add_child(child)
        g.add(parent)
        all_nodes = g.find_all()
        names = {n.name for n in all_nodes}
        self.assertIn("parent", names)
        self.assertIn("child", names)

    def test_find_all_visible_only(self):
        g = SceneGraph2D()
        visible = Node2D("v", visible=True)
        hidden = Node2D("h", visible=False)
        g.add(visible)
        g.add(hidden)
        result = g.find_all(visible_only=True)
        names = {n.name for n in result}
        self.assertIn("v", names)
        self.assertNotIn("h", names)


class TestSceneGraph2DExports(unittest.TestCase):

    def test_importable_from_gui_do(self):
        import gui_do
        self.assertTrue(hasattr(gui_do, "Node2D"))
        self.assertTrue(hasattr(gui_do, "SceneGraph2D"))
        self.assertTrue(hasattr(gui_do, "Camera2D"))


if __name__ == "__main__":
    unittest.main()
