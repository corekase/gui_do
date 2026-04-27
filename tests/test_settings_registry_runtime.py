import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from gui_do import SettingsRegistry, SettingDescriptor


class SettingsRegistryRuntimeTests(unittest.TestCase):

    def setUp(self) -> None:
        pygame.init()
        self.registry = SettingsRegistry()

    def tearDown(self) -> None:
        pygame.quit()

    # ------------------------------------------------------------------
    # declare / get
    # ------------------------------------------------------------------

    def test_declare_returns_observable(self) -> None:
        from gui_do import ObservableValue
        ov = self.registry.declare("audio", "volume", 1.0)
        self.assertIsInstance(ov, ObservableValue)

    def test_declared_value_equals_default(self) -> None:
        self.registry.declare("audio", "volume", 0.8)
        self.assertAlmostEqual(self.registry.get_value("audio", "volume"), 0.8)

    def test_declare_same_key_twice_returns_same_observable(self) -> None:
        ov1 = self.registry.declare("audio", "volume", 1.0)
        ov2 = self.registry.declare("audio", "volume", 0.5)
        self.assertIs(ov1, ov2)
        # Value is not overwritten on re-declare
        self.assertAlmostEqual(ov1.value, 1.0)

    def test_declare_empty_namespace_raises(self) -> None:
        with self.assertRaises(ValueError):
            self.registry.declare("", "volume", 1.0)

    def test_declare_empty_key_raises(self) -> None:
        with self.assertRaises(ValueError):
            self.registry.declare("audio", "", 1.0)

    def test_get_undeclared_raises_key_error(self) -> None:
        with self.assertRaises(KeyError):
            self.registry.get("audio", "volume")

    # ------------------------------------------------------------------
    # set_value / get_value
    # ------------------------------------------------------------------

    def test_set_value_updates_observable(self) -> None:
        self.registry.declare("audio", "volume", 1.0)
        self.registry.set_value("audio", "volume", 0.5)
        self.assertAlmostEqual(self.registry.get_value("audio", "volume"), 0.5)

    def test_set_value_fires_subscribers(self) -> None:
        received = []
        self.registry.declare("audio", "volume", 1.0)
        self.registry.get("audio", "volume").subscribe(lambda v: received.append(v))
        self.registry.set_value("audio", "volume", 0.3)
        self.assertIn(0.3, received)

    # ------------------------------------------------------------------
    # reset / reset_all
    # ------------------------------------------------------------------

    def test_reset_reverts_to_default(self) -> None:
        self.registry.declare("audio", "volume", 1.0)
        self.registry.set_value("audio", "volume", 0.2)
        self.registry.reset("audio")
        self.assertAlmostEqual(self.registry.get_value("audio", "volume"), 1.0)

    def test_reset_all_reverts_all_namespaces(self) -> None:
        self.registry.declare("audio", "volume", 1.0)
        self.registry.declare("video", "fps", 60)
        self.registry.set_value("audio", "volume", 0.2)
        self.registry.set_value("video", "fps", 30)
        self.registry.reset_all()
        self.assertAlmostEqual(self.registry.get_value("audio", "volume"), 1.0)
        self.assertEqual(self.registry.get_value("video", "fps"), 60)

    # ------------------------------------------------------------------
    # namespaces / keys / describe
    # ------------------------------------------------------------------

    def test_namespaces_returns_sorted_list(self) -> None:
        self.registry.declare("z_ns", "k", 0)
        self.registry.declare("a_ns", "k", 0)
        ns = self.registry.namespaces()
        self.assertEqual(ns, sorted(ns))
        self.assertIn("a_ns", ns)
        self.assertIn("z_ns", ns)

    def test_keys_returns_sorted_list(self) -> None:
        self.registry.declare("ns", "z_key", 0)
        self.registry.declare("ns", "a_key", 0)
        keys = self.registry.keys("ns")
        self.assertEqual(keys, sorted(keys))

    def test_describe_returns_descriptor(self) -> None:
        self.registry.declare("ns", "k", 42, label="My Setting")
        desc = self.registry.describe("ns", "k")
        self.assertIsInstance(desc, SettingDescriptor)
        self.assertEqual(desc.namespace, "ns")
        self.assertEqual(desc.key, "k")
        self.assertEqual(desc.default, 42)
        self.assertEqual(desc.label, "My Setting")

    def test_describe_unknown_returns_none(self) -> None:
        result = self.registry.describe("ns", "missing")
        self.assertIsNone(result)

    def test_all_descriptors_returns_all(self) -> None:
        self.registry.declare("ns", "a", 1, label="A")
        self.registry.declare("ns", "b", 2, label="B")
        descs = self.registry.all_descriptors()
        keys = [d.key for d in descs]
        self.assertIn("a", keys)
        self.assertIn("b", keys)

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def test_save_creates_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "settings.json"
            reg = SettingsRegistry(path)
            reg.declare("audio", "volume", 1.0)
            reg.set_value("audio", "volume", 0.7)
            result = reg.save()
            self.assertTrue(result)
            self.assertTrue(path.exists())

    def test_load_restores_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "settings.json"
            reg = SettingsRegistry(path)
            reg.declare("audio", "volume", 1.0)
            reg.set_value("audio", "volume", 0.4)
            reg.save()

            reg2 = SettingsRegistry(path)
            reg2.declare("audio", "volume", 1.0)
            reg2.load()
            self.assertAlmostEqual(reg2.get_value("audio", "volume"), 0.4)

    def test_load_missing_file_returns_false(self) -> None:
        reg = SettingsRegistry("/nonexistent/path/settings.json")
        result = reg.load()
        self.assertFalse(result)

    def test_save_no_path_returns_false(self) -> None:
        reg = SettingsRegistry()
        result = reg.save()
        self.assertFalse(result)

    def test_set_file_path(self) -> None:
        reg = SettingsRegistry()
        self.assertIsNone(reg.file_path)
        reg.set_file_path("/tmp/settings.json")
        self.assertIsNotNone(reg.file_path)

    def test_load_unknown_keys_are_ignored(self) -> None:
        import json
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "settings.json"
            path.write_text(json.dumps({"ns": {"unknown_key": 99}}), encoding="utf-8")
            reg = SettingsRegistry(path)
            reg.declare("ns", "volume", 1.0)
            result = reg.load()
            self.assertTrue(result)
            self.assertAlmostEqual(reg.get_value("ns", "volume"), 1.0)


if __name__ == "__main__":
    unittest.main()
