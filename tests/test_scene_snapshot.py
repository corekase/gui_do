"""Tests for NodeSnapshot and SceneSnapshot."""
import unittest

from gui_do.persistence.scene_snapshot import NodeSnapshot, SceneSnapshot


# ===========================================================================
# NodeSnapshot
# ===========================================================================


class TestNodeSnapshot(unittest.TestCase):
    def test_fields_stored(self):
        n = NodeSnapshot(control_id="btn", rect=[10, 20, 80, 30])
        self.assertEqual("btn", n.control_id)
        self.assertEqual([10, 20, 80, 30], n.rect)

    def test_defaults(self):
        n = NodeSnapshot(control_id="x", rect=[0, 0, 0, 0])
        self.assertTrue(n.visible)
        self.assertTrue(n.enabled)
        self.assertEqual({}, n.extra)

    def test_custom_visible_enabled(self):
        n = NodeSnapshot(control_id="x", rect=[0, 0, 0, 0], visible=False, enabled=False)
        self.assertFalse(n.visible)
        self.assertFalse(n.enabled)


# ===========================================================================
# SceneSnapshot — initial state
# ===========================================================================


class TestSceneSnapshotInitial(unittest.TestCase):
    def test_empty_by_default(self):
        s = SceneSnapshot()
        self.assertEqual(0, len(s))

    def test_node_ids_empty(self):
        s = SceneSnapshot()
        self.assertEqual([], s.node_ids)

    def test_get_missing_returns_none(self):
        s = SceneSnapshot()
        self.assertIsNone(s.get("nonexistent"))

    def test_contains_false(self):
        s = SceneSnapshot()
        self.assertNotIn("btn", s)


# ===========================================================================
# SceneSnapshot — from_nodes
# ===========================================================================


class TestSceneSnapshotFromNodes(unittest.TestCase):
    def _make_node(self, cid, x, y, w, h, visible=True, enabled=True):
        class FakeRect:
            pass
        r = FakeRect()
        r.x, r.y, r.width, r.height = x, y, w, h

        class FakeNode:
            pass
        n = FakeNode()
        n.control_id = cid
        n.rect = r
        n.visible = visible
        n.enabled = enabled
        return n

    def test_captures_all_nodes(self):
        nodes = [
            self._make_node("a", 0, 0, 100, 50),
            self._make_node("b", 10, 20, 80, 40),
        ]
        s = SceneSnapshot.from_nodes(nodes)
        self.assertEqual(2, len(s))
        self.assertIn("a", s)
        self.assertIn("b", s)

    def test_captures_rect(self):
        nodes = [self._make_node("x", 5, 10, 200, 100)]
        s = SceneSnapshot.from_nodes(nodes)
        self.assertEqual([5, 10, 200, 100], s.get("x").rect)

    def test_captures_visible_false(self):
        nodes = [self._make_node("x", 0, 0, 0, 0, visible=False)]
        s = SceneSnapshot.from_nodes(nodes)
        self.assertFalse(s.get("x").visible)

    def test_skips_nodes_without_control_id(self):
        class NoId:
            rect = None
        s = SceneSnapshot.from_nodes([NoId()])
        self.assertEqual(0, len(s))

    def test_node_ids_sorted(self):
        nodes = [
            self._make_node("z", 0, 0, 0, 0),
            self._make_node("a", 0, 0, 0, 0),
        ]
        s = SceneSnapshot.from_nodes(nodes)
        self.assertEqual(["a", "z"], s.node_ids)


# ===========================================================================
# SceneSnapshot — to_dict / from_dict
# ===========================================================================


class TestSceneSnapshotSerialization(unittest.TestCase):
    def test_to_dict_roundtrip(self):
        entries = {"btn": NodeSnapshot(control_id="btn", rect=[1, 2, 3, 4])}
        s = SceneSnapshot(entries)
        d = s.to_dict()
        s2 = SceneSnapshot.from_dict(d)
        self.assertEqual(1, len(s2))
        self.assertEqual([1, 2, 3, 4], s2.get("btn").rect)

    def test_to_dict_keys_are_control_ids(self):
        entries = {"panel": NodeSnapshot(control_id="panel", rect=[0, 0, 100, 100])}
        s = SceneSnapshot(entries)
        d = s.to_dict()
        self.assertIn("panel", d)

    def test_from_dict_empty(self):
        s = SceneSnapshot.from_dict({})
        self.assertEqual(0, len(s))


# ===========================================================================
# SceneSnapshot — save / load
# ===========================================================================


class TestSceneSnapshotPersistence(unittest.TestCase):
    def test_save_and_load(self):
        import tempfile, os
        entries = {"btn": NodeSnapshot(control_id="btn", rect=[10, 20, 80, 30])}
        s = SceneSnapshot(entries)
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            s.save(path)
            loaded = SceneSnapshot.load(path)
        finally:
            os.unlink(path)
        self.assertEqual(1, len(loaded))
        self.assertEqual([10, 20, 80, 30], loaded.get("btn").rect)

    def test_load_missing_file_returns_empty(self):
        s = SceneSnapshot.load("nonexistent_file_xyz.json")
        self.assertEqual(0, len(s))


if __name__ == "__main__":
    unittest.main()
