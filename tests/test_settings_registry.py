"""Tests for SettingsRegistry and SettingDescriptor from persistence.settings_registry."""
import unittest

from gui_do.persistence.settings_registry import SettingsRegistry, SettingDescriptor


# ===========================================================================
# SettingDescriptor
# ===========================================================================


class TestSettingDescriptor(unittest.TestCase):
    def test_fields_stored(self):
        d = SettingDescriptor("audio", "volume", 1.0, "Master Volume")
        self.assertEqual("audio", d.namespace)
        self.assertEqual("volume", d.key)
        self.assertEqual(1.0, d.default)
        self.assertEqual("Master Volume", d.label)

    def test_label_defaults_empty(self):
        d = SettingDescriptor("ns", "key", 0)
        self.assertEqual("", d.label)


# ===========================================================================
# SettingsRegistry — initial state
# ===========================================================================


class TestSettingsRegistryInitial(unittest.TestCase):
    def test_no_namespaces(self):
        r = SettingsRegistry()
        self.assertEqual([], r.namespaces())

    def test_file_path_none(self):
        r = SettingsRegistry()
        self.assertIsNone(r.file_path)

    def test_no_descriptors(self):
        r = SettingsRegistry()
        self.assertEqual([], r.all_descriptors())


# ===========================================================================
# SettingsRegistry — declare
# ===========================================================================


class TestSettingsRegistryDeclare(unittest.TestCase):
    def test_declare_creates_observable(self):
        r = SettingsRegistry()
        ov = r.declare("audio", "volume", 1.0)
        self.assertEqual(1.0, ov.value)

    def test_declare_adds_namespace(self):
        r = SettingsRegistry()
        r.declare("audio", "volume", 1.0)
        self.assertIn("audio", r.namespaces())

    def test_declare_adds_key(self):
        r = SettingsRegistry()
        r.declare("audio", "volume", 1.0)
        self.assertIn("volume", r.keys("audio"))

    def test_declare_empty_namespace_raises(self):
        r = SettingsRegistry()
        with self.assertRaises(ValueError):
            r.declare("", "key", 0)

    def test_declare_empty_key_raises(self):
        r = SettingsRegistry()
        with self.assertRaises(ValueError):
            r.declare("ns", "", 0)

    def test_declare_twice_returns_same_observable(self):
        r = SettingsRegistry()
        ov1 = r.declare("ns", "k", 0)
        ov2 = r.declare("ns", "k", 99)
        self.assertIs(ov1, ov2)
        self.assertEqual(0, ov1.value)  # original value preserved


# ===========================================================================
# SettingsRegistry — get / set / get_value
# ===========================================================================


class TestSettingsRegistryGetSet(unittest.TestCase):
    def test_get_value_returns_default(self):
        r = SettingsRegistry()
        r.declare("ui", "scale", 2)
        self.assertEqual(2, r.get_value("ui", "scale"))

    def test_set_value_updates(self):
        r = SettingsRegistry()
        r.declare("ui", "scale", 2)
        r.set_value("ui", "scale", 4)
        self.assertEqual(4, r.get_value("ui", "scale"))

    def test_get_missing_raises(self):
        r = SettingsRegistry()
        with self.assertRaises(KeyError):
            r.get("ns", "key")

    def test_set_fires_subscriber(self):
        r = SettingsRegistry()
        calls = []
        ov = r.declare("ns", "k", 0)
        ov.subscribe(lambda v: calls.append(v))
        r.set_value("ns", "k", 5)
        self.assertIn(5, calls)


# ===========================================================================
# SettingsRegistry — reset
# ===========================================================================


class TestSettingsRegistryReset(unittest.TestCase):
    def test_reset_reverts_namespace(self):
        r = SettingsRegistry()
        r.declare("audio", "volume", 1.0)
        r.set_value("audio", "volume", 0.5)
        r.reset("audio")
        self.assertEqual(1.0, r.get_value("audio", "volume"))

    def test_reset_all(self):
        r = SettingsRegistry()
        r.declare("a", "x", 10)
        r.declare("b", "y", 20)
        r.set_value("a", "x", 99)
        r.set_value("b", "y", 99)
        r.reset_all()
        self.assertEqual(10, r.get_value("a", "x"))
        self.assertEqual(20, r.get_value("b", "y"))


# ===========================================================================
# SettingsRegistry — inspection
# ===========================================================================


class TestSettingsRegistryInspection(unittest.TestCase):
    def test_namespaces_sorted(self):
        r = SettingsRegistry()
        r.declare("z", "k", 0)
        r.declare("a", "k", 0)
        self.assertEqual(["a", "z"], r.namespaces())

    def test_keys_sorted(self):
        r = SettingsRegistry()
        r.declare("ns", "z", 0)
        r.declare("ns", "a", 0)
        self.assertEqual(["a", "z"], r.keys("ns"))

    def test_describe_returns_descriptor(self):
        r = SettingsRegistry()
        r.declare("audio", "volume", 1.0, label="Volume")
        d = r.describe("audio", "volume")
        self.assertIsNotNone(d)
        self.assertEqual("Volume", d.label)

    def test_describe_missing_returns_none(self):
        r = SettingsRegistry()
        self.assertIsNone(r.describe("ns", "k"))

    def test_all_descriptors_ordered(self):
        r = SettingsRegistry()
        r.declare("b", "z", 0)
        r.declare("a", "k", 0)
        descs = r.all_descriptors()
        self.assertEqual(("a", "k"), (descs[0].namespace, descs[0].key))
        self.assertEqual(("b", "z"), (descs[1].namespace, descs[1].key))


if __name__ == "__main__":
    unittest.main()
