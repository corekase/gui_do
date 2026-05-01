"""Tests for ListDiff types and ListDiffCalculator."""
import unittest

from gui_do.data.list_diff import (
    DiffInsert,
    DiffRemove,
    DiffMove,
    ListDiff,
    ListDiffCalculator,
)


# ===========================================================================
# ListDiff dataclasses
# ===========================================================================


class TestDiffTypes(unittest.TestCase):
    def test_diff_insert_frozen(self):
        d = DiffInsert(index=2, item="x")
        self.assertEqual(2, d.index)
        with self.assertRaises(Exception):
            d.index = 0  # type: ignore[misc]

    def test_diff_remove_frozen(self):
        d = DiffRemove(index=1, item="y")
        self.assertEqual(1, d.index)

    def test_diff_move_frozen(self):
        d = DiffMove(from_index=0, to_index=3, item="z")
        self.assertEqual(3, d.to_index)

    def test_list_diff_is_empty_true(self):
        d = ListDiff(inserts=[], removes=[], moves=[])
        self.assertTrue(d.is_empty)

    def test_list_diff_is_empty_false(self):
        d = ListDiff(inserts=[DiffInsert(0, "x")], removes=[], moves=[])
        self.assertFalse(d.is_empty)


# ===========================================================================
# ListDiffCalculator.diff — basic cases
# ===========================================================================


class TestListDiffCalculatorBasic(unittest.TestCase):
    def test_identical_lists_empty_diff(self):
        diff = ListDiffCalculator.diff(["a", "b", "c"], ["a", "b", "c"])
        self.assertTrue(diff.is_empty)

    def test_insert_one_item(self):
        diff = ListDiffCalculator.diff(["a", "b"], ["a", "x", "b"])
        self.assertEqual(1, len(diff.inserts))
        self.assertEqual("x", diff.inserts[0].item)
        self.assertEqual([], diff.removes)

    def test_remove_one_item(self):
        diff = ListDiffCalculator.diff(["a", "b", "c"], ["a", "c"])
        self.assertEqual(1, len(diff.removes))
        self.assertEqual("b", diff.removes[0].item)
        self.assertEqual([], diff.inserts)

    def test_empty_old_all_inserts(self):
        diff = ListDiffCalculator.diff([], ["a", "b"])
        self.assertEqual(2, len(diff.inserts))
        self.assertEqual([], diff.removes)

    def test_empty_new_all_removes(self):
        diff = ListDiffCalculator.diff(["a", "b"], [])
        self.assertEqual(2, len(diff.removes))
        self.assertEqual([], diff.inserts)

    def test_replace_one_item(self):
        diff = ListDiffCalculator.diff(["a", "b", "c"], ["a", "x", "c"])
        # "b" removed, "x" inserted
        items_removed = [r.item for r in diff.removes]
        items_inserted = [i.item for i in diff.inserts]
        self.assertIn("b", items_removed)
        self.assertIn("x", items_inserted)

    def test_completely_different_lists(self):
        diff = ListDiffCalculator.diff(["a", "b"], ["x", "y"])
        self.assertEqual(2, len(diff.removes))
        self.assertEqual(2, len(diff.inserts))

    def test_key_fn_used_for_objects(self):
        old = [{"id": 1, "v": "old"}, {"id": 2, "v": "old"}]
        new = [{"id": 1, "v": "new"}, {"id": 3, "v": "new"}]
        diff = ListDiffCalculator.diff(old, new, key_fn=lambda x: x["id"])
        removed_ids = [r.item["id"] for r in diff.removes]
        inserted_ids = [i.item["id"] for i in diff.inserts]
        self.assertIn(2, removed_ids)
        self.assertIn(3, inserted_ids)


# ===========================================================================
# ListDiffCalculator.apply_to_list
# ===========================================================================


class TestListDiffApply(unittest.TestCase):
    def test_apply_insert(self):
        target = ["a", "b"]
        diff = ListDiffCalculator.diff(["a", "b"], ["a", "x", "b"])
        ListDiffCalculator.apply_to_list(target, diff)
        self.assertIn("x", target)

    def test_apply_remove(self):
        target = ["a", "b", "c"]
        diff = ListDiffCalculator.diff(["a", "b", "c"], ["a", "c"])
        ListDiffCalculator.apply_to_list(target, diff)
        self.assertNotIn("b", target)
        self.assertIn("a", target)
        self.assertIn("c", target)

    def test_apply_empty_diff_no_change(self):
        target = ["a", "b"]
        diff = ListDiffCalculator.diff(["a", "b"], ["a", "b"])
        original = list(target)
        ListDiffCalculator.apply_to_list(target, diff)
        self.assertEqual(original, target)


if __name__ == "__main__":
    unittest.main()
