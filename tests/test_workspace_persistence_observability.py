import unittest

from gui_do.persistence.workspace_persistence import WorkspacePersistenceManager, WorkspaceState


class _RectLike:
    def __init__(self, x: int, y: int, w: int, h: int):
        self.x = int(x)
        self.y = int(y)
        self.width = int(w)
        self.height = int(h)


class _StubNode:
    def __init__(self, control_id: str):
        self.control_id = str(control_id)
        self.rect = _RectLike(10, 20, 30, 40)
        self.visible = True
        self.enabled = True
        self.invalidated = 0

    def invalidate(self):
        self.invalidated += 1


class _StubScene:
    def __init__(self):
        self._node = _StubNode("root")

    def _walk_nodes(self):
        return [self._node]


class _StubApp:
    def __init__(self):
        self.active_scene_name = "default"
        self.scene = _StubScene()
        self.switched_to = []

    def switch_scene(self, name: str) -> None:
        self.active_scene_name = str(name)
        self.switched_to.append(str(name))


class _StubFeatureManager:
    def __init__(self):
        self.restored_states = None

    def restore_feature_states(self, state):
        self.restored_states = dict(state)


class _StubSettingsRegistry:
    def __init__(self):
        self._values = {
            "ui": {"theme": "light", "density": "comfortable"},
        }

    def set_value(self, namespace: str, key: str, value):
        if namespace not in self._values or key not in self._values[namespace]:
            raise KeyError((namespace, key))
        self._values[namespace][key] = value


class TestWorkspacePersistenceObservability(unittest.TestCase):
    def test_restore_tracks_scene_features_snapshot_and_settings(self):
        manager = WorkspacePersistenceManager()
        manager.register_settings("settings", _StubSettingsRegistry())
        app = _StubApp()
        feature_manager = _StubFeatureManager()
        state = WorkspaceState(
            active_scene_name="systems",
            scene_snapshot={
                "root": {
                    "control_id": "root",
                    "rect": [100, 200, 300, 400],
                    "visible": False,
                    "enabled": False,
                    "extra": {},
                }
            },
            feature_states={"systems": {"visible": True}},
            settings_blocks={
                "settings": {
                    "ui": {
                        "theme": "dark",
                        "density": "compact",
                        "unknown": "ignored",
                    }
                }
            },
        )

        report = manager.restore(state, app, feature_manager=feature_manager)

        self.assertEqual("systems", app.active_scene_name)
        self.assertEqual(["systems"], app.switched_to)
        self.assertEqual({"systems": {"visible": True}}, feature_manager.restored_states)

        node = app.scene._node
        self.assertEqual((100, 200, 300, 400), (node.rect.x, node.rect.y, node.rect.width, node.rect.height))
        self.assertFalse(node.visible)
        self.assertFalse(node.enabled)
        self.assertEqual(1, node.invalidated)

        self.assertEqual("systems", report["target_scene"])
        self.assertTrue(report["switched_scene"])
        self.assertTrue(report["restored_feature_states"])
        self.assertEqual(1, report["restored_scene_nodes"])
        self.assertEqual(2, report["applied_settings"])
        self.assertEqual(1, report["skipped_settings"])
        self.assertEqual([], report["missing_settings_blocks"])

    def test_restore_tracks_missing_blocks_and_malformed_payloads(self):
        manager = WorkspacePersistenceManager()
        app = _StubApp()
        state = WorkspaceState(
            settings_blocks={
                "missing": {"ui": {"theme": "dark"}},
                "invalid_block": ["not", "a", "dict"],
            }
        )

        report = manager.restore(state, app, feature_manager=None)

        self.assertFalse(report["switched_scene"])
        self.assertFalse(report["restored_feature_states"])
        self.assertEqual(0, report["restored_scene_nodes"])
        self.assertEqual(0, report["applied_settings"])
        self.assertEqual(0, report["skipped_settings"])
        self.assertEqual(["invalid_block", "missing"], sorted(report["missing_settings_blocks"]))


if __name__ == "__main__":
    unittest.main()
