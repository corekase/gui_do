"""Tests for gui_do.persistence.snapshot_migration."""
from __future__ import annotations

import unittest

from gui_do.persistence.snapshot_migration import (
    MigrationError,
    MigrationRegistry,
    MigrationStep,
    SchemaVersion,
    SnapshotMigrator,
    make_snapshot,
    read_version,
)


V1 = SchemaVersion(1, 0)
V1_1 = SchemaVersion(1, 1)
V2 = SchemaVersion(2, 0)
V3 = SchemaVersion(3, 0)


class TestSchemaVersion(unittest.TestCase):
    def test_str(self):
        self.assertEqual(str(V1), "1.0")
        self.assertEqual(str(SchemaVersion(2, 5)), "2.5")

    def test_ordering(self):
        self.assertLess(V1, V2)
        self.assertGreater(V3, V2)
        self.assertEqual(SchemaVersion(1, 0), V1)

    def test_parse(self):
        self.assertEqual(SchemaVersion.parse("1.0"), V1)
        self.assertEqual(SchemaVersion.parse("2.3"), SchemaVersion(2, 3))

    def test_parse_invalid(self):
        with self.assertRaises(ValueError):
            SchemaVersion.parse("not.a.version.string.with.too.many.dots.xyz")

    def test_hashable(self):
        s = {V1, V2, V1}
        self.assertEqual(len(s), 2)

    def test_minor_ordering(self):
        self.assertLess(V1, V1_1)


class TestMakeSnapshot(unittest.TestCase):
    def test_schema_version_field(self):
        snap = make_snapshot(V1, {"x": 1})
        self.assertEqual(snap["schema_version"], "1.0")

    def test_data_is_copied(self):
        data = {"list": [1, 2, 3]}
        snap = make_snapshot(V1, data)
        data["list"].append(4)
        self.assertEqual(snap["data"]["list"], [1, 2, 3])

    def test_read_version(self):
        snap = make_snapshot(V2, {})
        self.assertEqual(read_version(snap), V2)


class TestMigrationStep(unittest.TestCase):
    def test_basic_construction(self):
        step = MigrationStep(V1, V2, lambda d: {**d, "v": 2})
        self.assertEqual(step.from_version, V1)
        self.assertEqual(step.to_version, V2)

    def test_invalid_direction_raises(self):
        with self.assertRaises(ValueError):
            MigrationStep(V2, V1, lambda d: d)

    def test_equal_versions_raises(self):
        with self.assertRaises(ValueError):
            MigrationStep(V1, V1, lambda d: d)


class TestMigrationRegistry(unittest.TestCase):
    def _step(self, frm, to, tag=None):
        return MigrationStep(frm, to, lambda d, t=tag: {**d, "migrated_to": str(to)})

    def test_find_direct_path(self):
        reg = MigrationRegistry()
        reg.register(self._step(V1, V2))
        path = reg.find_path(V1, V2)
        self.assertIsNotNone(path)
        self.assertEqual(len(path), 1)

    def test_find_multi_hop_path(self):
        reg = MigrationRegistry()
        reg.register(self._step(V1, V1_1))
        reg.register(self._step(V1_1, V2))
        reg.register(self._step(V2, V3))
        path = reg.find_path(V1, V3)
        self.assertIsNotNone(path)
        self.assertEqual(len(path), 3)

    def test_no_path_returns_none(self):
        reg = MigrationRegistry()
        self.assertIsNone(reg.find_path(V1, V2))

    def test_same_version_returns_empty_path(self):
        reg = MigrationRegistry()
        path = reg.find_path(V1, V1)
        self.assertEqual(path, [])

    def test_steps_returns_copy(self):
        reg = MigrationRegistry()
        reg.register(self._step(V1, V2))
        steps = reg.steps
        steps.clear()
        self.assertEqual(len(reg.steps), 1)


class TestSnapshotMigrator(unittest.TestCase):
    def _make_migrator(self) -> SnapshotMigrator:
        reg = MigrationRegistry()
        reg.register(MigrationStep(V1, V2, lambda d: {**d, "schema": 2}))
        reg.register(MigrationStep(V2, V3, lambda d: {**d, "schema": 3}))
        return SnapshotMigrator(reg)

    def test_migrate_direct(self):
        migrator = self._make_migrator()
        snap = make_snapshot(V1, {"payload": "hello"})
        result = migrator.migrate(snap, V2)
        self.assertEqual(read_version(result), V2)
        self.assertEqual(result["data"]["schema"], 2)

    def test_migrate_multi_hop(self):
        migrator = self._make_migrator()
        snap = make_snapshot(V1, {"payload": "hello"})
        result = migrator.migrate(snap, V3)
        self.assertEqual(read_version(result), V3)
        self.assertEqual(result["data"]["schema"], 3)

    def test_migrate_same_version(self):
        migrator = self._make_migrator()
        snap = make_snapshot(V2, {"x": 1})
        result = migrator.migrate(snap, V2)
        self.assertEqual(result["data"]["x"], 1)

    def test_no_path_raises(self):
        migrator = self._make_migrator()
        snap = make_snapshot(V3, {})
        with self.assertRaises(MigrationError):
            migrator.migrate(snap, V1)  # downgrade not registered

    def test_original_not_mutated(self):
        migrator = self._make_migrator()
        snap = make_snapshot(V1, {"x": 1})
        migrator.migrate(snap, V2)
        self.assertEqual(snap["schema_version"], "1.0")

    def test_can_migrate_true(self):
        migrator = self._make_migrator()
        self.assertTrue(migrator.can_migrate(V1, V3))

    def test_can_migrate_false(self):
        migrator = self._make_migrator()
        self.assertFalse(migrator.can_migrate(V3, V1))


if __name__ == "__main__":
    unittest.main()
