"""Tests for SceneSnapshot/NodeSnapshot and WorkspaceState/WorkspacePersistenceManager."""
import json
import tempfile
import unittest
from pathlib import Path

from gui_do.persistence.scene_snapshot import NodeSnapshot, SceneSnapshot
from gui_do.persistence.workspace_persistence import (
    WorkspacePersistenceManager,
    WorkspaceState,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class _Rect:
    def __init__(self, x, y, w, h):
        self.x = int(x)
        self.y = int(y)
        self.width = int(w)
        self.height = int(h)


class _Node:
    def __init__(self, control_id, *, x=0, y=0, w=100, h=50, visible=True, enabled=True):
        self.control_id = control_id
        self.rect = _Rect(x, y, w, h)
        self.visible = visible
        self.enabled = enabled
        self._invalidated = 0

    def invalidate(self):
        self._invalidated += 1


class _Scene:
    def __init__(self, *nodes):
        self._nodes = list(nodes)

    def _walk_nodes(self):
        return iter(self._nodes)


class _SettingsReg:
    """Minimal registry compatible with WorkspacePersistenceManager._registry_values."""

    def __init__(self, data):
        # data: {namespace: {key: value}}
        self._data = {ns: dict(vals) for ns, vals in data.items()}

    def namespaces(self):
        return list(self._data.keys())

    def keys(self, namespace):
        return list(self._data.get(namespace, {}).keys())

    def get_value(self, namespace, key):
        return self._data[namespace][key]

    def set_value(self, namespace, key, value):
        if namespace not in self._data or key not in self._data[namespace]:
            raise KeyError((namespace, key))
        self._data[namespace][key] = value


# ===========================================================================
# NodeSnapshot
# ===========================================================================


class TestNodeSnapshot(unittest.TestCase):
    def test_defaults(self):
        ns = NodeSnapshot(control_id="x", rect=[0, 0, 10, 20])
        self.assertTrue(ns.visible)
        self.assertTrue(ns.enabled)
        self.assertEqual({}, ns.extra)

    def test_fields(self):
        ns = NodeSnapshot(control_id="btn", rect=[5, 10, 80, 30], visible=False, enabled=False)
        self.assertEqual("btn", ns.control_id)
        self.assertEqual([5, 10, 80, 30], ns.rect)
        self.assertFalse(ns.visible)
        self.assertFalse(ns.enabled)

    def test_extra_default_is_not_shared(self):
        a = NodeSnapshot("a", [0, 0, 1, 1])
        b = NodeSnapshot("b", [0, 0, 1, 1])
        a.extra["k"] = "v"
        self.assertNotIn("k", b.extra)


# ===========================================================================
# SceneSnapshot — capture
# ===========================================================================


class TestSceneSnapshotCapture(unittest.TestCase):
    def test_capture_from_scene(self):
        node = _Node("panel", x=10, y=20, w=200, h=100)
        scene = _Scene(node)
        snap = SceneSnapshot.capture(scene)
        self.assertIn("panel", snap)
        ns = snap.get("panel")
        self.assertEqual([10, 20, 200, 100], ns.rect)

    def test_capture_preserves_visibility(self):
        node = _Node("btn", visible=False, enabled=False)
        snap = SceneSnapshot.capture(_Scene(node))
        ns = snap.get("btn")
        self.assertFalse(ns.visible)
        self.assertFalse(ns.enabled)

    def test_capture_none_scene_returns_empty(self):
        snap = SceneSnapshot.capture(None)
        self.assertEqual(0, len(snap))

    def test_capture_skips_nodes_without_control_id(self):
        class _Anon:
            rect = _Rect(0, 0, 10, 10)
            visible = True
            enabled = True
        snap = SceneSnapshot.capture(_Scene(_Anon()))
        self.assertEqual(0, len(snap))

    def test_capture_with_include_ids_filters(self):
        a = _Node("a")
        b = _Node("b")
        snap = SceneSnapshot.capture(_Scene(a, b), include_ids={"a"})
        self.assertIn("a", snap)
        self.assertNotIn("b", snap)

    def test_capture_multiple_nodes(self):
        nodes = [_Node(f"n{i}") for i in range(5)]
        snap = SceneSnapshot.capture(_Scene(*nodes))
        self.assertEqual(5, len(snap))

    def test_from_nodes(self):
        a = _Node("a", x=1, y=2, w=3, h=4)
        b = _Node("b", x=5, y=6, w=7, h=8)
        snap = SceneSnapshot.from_nodes([a, b])
        self.assertEqual([1, 2, 3, 4], snap.get("a").rect)
        self.assertEqual([5, 6, 7, 8], snap.get("b").rect)


# ===========================================================================
# SceneSnapshot — restore
# ===========================================================================


class TestSceneSnapshotRestore(unittest.TestCase):
    def test_restore_updates_rect(self):
        node = _Node("p", x=0, y=0, w=10, h=10)
        snap = SceneSnapshot.capture(_Scene(node))
        # Move node away
        node.rect.x, node.rect.y = 999, 999
        snap.restore(_Scene(node))
        self.assertEqual(0, node.rect.x)
        self.assertEqual(0, node.rect.y)

    def test_restore_updates_visibility(self):
        node = _Node("p", visible=True, enabled=True)
        snap = SceneSnapshot.from_nodes([node])
        node.visible = False
        node.enabled = False
        snap.restore(_Scene(node))
        self.assertTrue(node.visible)
        self.assertTrue(node.enabled)

    def test_restore_calls_invalidate(self):
        node = _Node("p")
        snap = SceneSnapshot.from_nodes([node])
        snap.restore(_Scene(node))
        self.assertEqual(1, node._invalidated)

    def test_restore_returns_count(self):
        nodes = [_Node(f"n{i}") for i in range(3)]
        snap = SceneSnapshot.from_nodes(nodes)
        count = snap.restore(_Scene(*nodes))
        self.assertEqual(3, count)

    def test_restore_skips_unmatched_nodes(self):
        a = _Node("a")
        snap = SceneSnapshot.from_nodes([a])
        b = _Node("b")
        snap.restore(_Scene(b))
        self.assertEqual(0, b._invalidated)

    def test_restore_none_scene_returns_zero(self):
        snap = SceneSnapshot.from_nodes([_Node("a")])
        self.assertEqual(0, snap.restore(None))

    def test_restore_empty_snapshot_returns_zero(self):
        node = _Node("a")
        self.assertEqual(0, SceneSnapshot().restore(_Scene(node)))


# ===========================================================================
# SceneSnapshot — serialisation
# ===========================================================================


class TestSceneSnapshotSerialisation(unittest.TestCase):
    def _snap_with_node(self):
        node = _Node("btn", x=5, y=10, w=80, h=25, visible=False, enabled=True)
        return SceneSnapshot.from_nodes([node])

    def test_to_dict_structure(self):
        snap = self._snap_with_node()
        d = snap.to_dict()
        self.assertIn("btn", d)
        self.assertEqual([5, 10, 80, 25], d["btn"]["rect"])
        self.assertFalse(d["btn"]["visible"])

    def test_from_dict_round_trips(self):
        snap = self._snap_with_node()
        snap2 = SceneSnapshot.from_dict(snap.to_dict())
        ns = snap2.get("btn")
        self.assertIsNotNone(ns)
        self.assertEqual([5, 10, 80, 25], ns.rect)
        self.assertFalse(ns.visible)

    def test_save_and_load(self):
        snap = self._snap_with_node()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "snap.json"
            snap.save(path)
            self.assertTrue(path.exists())
            snap2 = SceneSnapshot.load(path)
            self.assertIn("btn", snap2)

    def test_load_missing_file_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            snap = SceneSnapshot.load(Path(tmp) / "missing.json")
            self.assertEqual(0, len(snap))

    def test_node_ids_sorted(self):
        nodes = [_Node("z"), _Node("a"), _Node("m")]
        snap = SceneSnapshot.from_nodes(nodes)
        self.assertEqual(["a", "m", "z"], snap.node_ids)

    def test_contains(self):
        snap = SceneSnapshot.from_nodes([_Node("x")])
        self.assertIn("x", snap)
        self.assertNotIn("y", snap)

    def test_get_returns_none_for_missing(self):
        snap = SceneSnapshot()
        self.assertIsNone(snap.get("nope"))


# ===========================================================================
# WorkspaceState serialisation
# ===========================================================================


class TestWorkspaceState(unittest.TestCase):
    def _make_state(self):
        return WorkspaceState(
            active_scene_name="main",
            scene_snapshot={"n1": {"control_id": "n1", "rect": [0, 0, 1, 1], "visible": True, "enabled": True, "extra": {}}},
            feature_states={"feat": {"active": True}},
            settings_blocks={"ui": {"theme": {"color": "dark"}}},
            metadata={"author": "test"},
        )

    def test_to_dict_keys(self):
        d = self._make_state().to_dict()
        self.assertIn("version", d)
        self.assertIn("active_scene_name", d)
        self.assertIn("scene_snapshot", d)
        self.assertIn("feature_states", d)
        self.assertIn("settings_blocks", d)
        self.assertIn("metadata", d)

    def test_to_dict_values(self):
        d = self._make_state().to_dict()
        self.assertEqual("main", d["active_scene_name"])
        self.assertEqual({"active": True}, d["feature_states"]["feat"])

    def test_from_dict_round_trips(self):
        original = self._make_state()
        restored = WorkspaceState.from_dict(original.to_dict())
        self.assertEqual("main", restored.active_scene_name)
        self.assertIn("n1", restored.scene_snapshot)
        self.assertEqual({"active": True}, restored.feature_states["feat"])

    def test_from_dict_defaults_on_missing_keys(self):
        state = WorkspaceState.from_dict({})
        self.assertEqual("default", state.active_scene_name)
        self.assertEqual(1, state.version)
        self.assertEqual({}, state.feature_states)

    def test_from_dict_skips_non_dict_feature_states(self):
        state = WorkspaceState.from_dict({"feature_states": {"good": {"x": 1}, "bad": "nope"}})
        self.assertIn("good", state.feature_states)
        self.assertNotIn("bad", state.feature_states)

    def test_save_writes_json_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.json"
            self._make_state().save(path)
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual("main", data["active_scene_name"])

    def test_load_restores_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.json"
            self._make_state().save(path)
            loaded = WorkspaceState.load(path)
            self.assertEqual("main", loaded.active_scene_name)

    def test_load_missing_file_returns_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = WorkspaceState.load(Path(tmp) / "ghost.json")
            self.assertEqual("default", state.active_scene_name)

    def test_save_creates_parent_dirs(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "deep" / "dir" / "state.json"
            self._make_state().save(path)
            self.assertTrue(path.exists())


# ===========================================================================
# WorkspacePersistenceManager — registration API
# ===========================================================================


class TestWorkspacePersistenceManagerRegistration(unittest.TestCase):
    def test_register_adds_block(self):
        m = WorkspacePersistenceManager()
        m.register_settings("ui", _SettingsReg({}))
        self.assertIn("ui", m.registered_blocks())

    def test_registered_blocks_sorted(self):
        m = WorkspacePersistenceManager()
        m.register_settings("zebra", _SettingsReg({}))
        m.register_settings("alpha", _SettingsReg({}))
        self.assertEqual(["alpha", "zebra"], m.registered_blocks())

    def test_register_empty_name_raises(self):
        m = WorkspacePersistenceManager()
        with self.assertRaises(ValueError):
            m.register_settings("", _SettingsReg({}))

    def test_unregister_removes_block(self):
        m = WorkspacePersistenceManager()
        m.register_settings("ui", _SettingsReg({}))
        result = m.unregister_settings("ui")
        self.assertTrue(result)
        self.assertNotIn("ui", m.registered_blocks())

    def test_unregister_missing_returns_false(self):
        m = WorkspacePersistenceManager()
        self.assertFalse(m.unregister_settings("nonexistent"))

    def test_capture_registry_values(self):
        m = WorkspacePersistenceManager()
        reg = _SettingsReg({"theme": {"color": "blue", "font_size": 14}})
        m.register_settings("appearance", reg)

        class _FakeApp:
            active_scene_name = "home"
            scene = _Scene()

        state = m.capture(_FakeApp())
        self.assertIn("appearance", state.settings_blocks)
        self.assertEqual("blue", state.settings_blocks["appearance"]["theme"]["color"])

    def test_restore_applies_settings(self):
        m = WorkspacePersistenceManager()
        reg = _SettingsReg({"theme": {"color": "blue"}})
        m.register_settings("appearance", reg)

        class _FakeApp:
            active_scene_name = "home"
            scene = _Scene()
            def switch_scene(self, name): pass

        state = WorkspaceState(
            settings_blocks={"appearance": {"theme": {"color": "red"}}}
        )
        m.restore(state, _FakeApp())
        self.assertEqual("red", reg.get_value("theme", "color"))

    def test_restore_reports_missing_blocks(self):
        m = WorkspacePersistenceManager()

        class _FakeApp:
            active_scene_name = "x"
            scene = _Scene()
            def switch_scene(self, name): pass

        state = WorkspaceState(settings_blocks={"phantom": {"ns": {"k": "v"}}})
        report = m.restore(state, _FakeApp())
        self.assertIn("phantom", report["missing_settings_blocks"])


if __name__ == "__main__":
    unittest.main()
