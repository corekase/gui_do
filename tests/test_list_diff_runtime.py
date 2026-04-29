"""Tests for ListDiffCalculator, ListDiff, DiffInsert, DiffRemove, DiffMove."""
import unittest

from gui_do.data.list_diff import (
    ListDiffCalculator,
    ListDiff,
    DiffInsert,
    DiffRemove,
    DiffMove,
)


class TestDiffInsertFrozen(unittest.TestCase):
    def test_fields(self) -> None:
        d = DiffInsert(index=2, item="x")
        self.assertEqual(d.index, 2)
        self.assertEqual(d.item, "x")

    def test_frozen(self) -> None:
        d = DiffInsert(0, "a")
        with self.assertRaises((AttributeError, TypeError)):
            d.index = 1  # type: ignore[misc]


class TestDiffRemoveFrozen(unittest.TestCase):
    def test_fields(self) -> None:
        d = DiffRemove(index=1, item="y")
        self.assertEqual(d.index, 1)
        self.assertEqual(d.item, "y")


class TestDiffMoveFrozen(unittest.TestCase):
    def test_fields(self) -> None:
        d = DiffMove(from_index=0, to_index=3, item="z")
        self.assertEqual(d.from_index, 0)
        self.assertEqual(d.to_index, 3)


class TestListDiffIsEmpty(unittest.TestCase):
    def test_empty_when_no_ops(self) -> None:
        diff = ListDiff(inserts=[], removes=[], moves=[])
        self.assertTrue(diff.is_empty)

    def test_not_empty_when_has_insert(self) -> None:
        diff = ListDiff(inserts=[DiffInsert(0, "x")], removes=[], moves=[])
        self.assertFalse(diff.is_empty)


class TestIdenticalLists(unittest.TestCase):
    def test_no_ops_for_identical_lists(self) -> None:
        diff = ListDiffCalculator.diff(["a", "b", "c"], ["a", "b", "c"])
        self.assertTrue(diff.is_empty)


class TestPureInsert(unittest.TestCase):
    def test_single_item_added(self) -> None:
        old = ["a", "b"]
        new = ["a", "x", "b"]
        diff = ListDiffCalculator.diff(old, new)
        self.assertEqual(len(diff.inserts), 1)
        self.assertEqual(diff.inserts[0].item, "x")
        self.assertEqual(len(diff.removes), 0)


class TestPureRemove(unittest.TestCase):
    def test_single_item_removed(self) -> None:
        old = ["a", "b", "c"]
        new = ["a", "c"]
        diff = ListDiffCalculator.diff(old, new)
        self.assertEqual(len(diff.removes), 1)
        self.assertEqual(diff.removes[0].item, "b")
        self.assertEqual(len(diff.inserts), 0)


class TestInsertAndRemove(unittest.TestCase):
    def test_replace_item(self) -> None:
        old = ["a", "b", "c", "d"]
        new = ["b", "c", "e", "d"]
        diff = ListDiffCalculator.diff(old, new)
        self.assertTrue(len(diff.removes) >= 1)
        self.assertTrue(len(diff.inserts) >= 1)
        remove_items = [r.item for r in diff.removes]
        insert_items = [i.item for i in diff.inserts]
        self.assertIn("a", remove_items)
        self.assertIn("e", insert_items)


class TestKeyFunction(unittest.TestCase):
    def test_key_fn_used_for_identity(self) -> None:
        old = [{"id": 1, "v": "a"}, {"id": 2, "v": "b"}]
        new = [{"id": 2, "v": "b"}, {"id": 3, "v": "c"}]
        diff = ListDiffCalculator.diff(old, new, key_fn=lambda x: x["id"])
        remove_keys = [r.item["id"] for r in diff.removes]
        insert_keys = [i.item["id"] for i in diff.inserts]
        self.assertIn(1, remove_keys)
        self.assertIn(3, insert_keys)


class TestEmptyToFull(unittest.TestCase):
    def test_empty_old_all_inserts(self) -> None:
        diff = ListDiffCalculator.diff([], ["a", "b", "c"])
        self.assertEqual(len(diff.inserts), 3)
        self.assertEqual(diff.removes, [])

    def test_full_to_empty_all_removes(self) -> None:
        diff = ListDiffCalculator.diff(["a", "b", "c"], [])
        self.assertEqual(len(diff.removes), 3)
        self.assertEqual(diff.inserts, [])


class TestApplyToList(unittest.TestCase):
    def test_apply_insert_then_remove(self) -> None:
        old = ["a", "b", "c"]
        new = ["a", "x", "c"]
        diff = ListDiffCalculator.diff(old, new)
        target = list(old)
        ListDiffCalculator.apply_to_list(target, diff)
        self.assertIn("x", target)
        self.assertNotIn("b", target)
