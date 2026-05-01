import unittest

from gui_do.data.list_diff import DiffInsert, DiffMove, DiffRemove, ListDiff, ListDiffCalculator


class TestListDiffCalculator(unittest.TestCase):
    def test_identical_lists_produce_empty_diff(self):
        diff = ListDiffCalculator.diff(["a", "b", "c"], ["a", "b", "c"])

        self.assertTrue(diff.is_empty)
        self.assertEqual([], diff.inserts)
        self.assertEqual([], diff.removes)
        self.assertEqual([], diff.moves)

    def test_empty_old_list_produces_all_inserts(self):
        diff = ListDiffCalculator.diff([], ["x", "y"])

        self.assertEqual(2, len(diff.inserts))
        self.assertEqual([], diff.removes)

    def test_empty_new_list_produces_all_removes(self):
        diff = ListDiffCalculator.diff(["x", "y"], [])

        self.assertEqual(2, len(diff.removes))
        self.assertEqual([], diff.inserts)

    def test_single_removal_detected(self):
        diff = ListDiffCalculator.diff(["a", "b", "c", "d"], ["b", "c", "d"])

        remove_items = [r.item for r in diff.removes]
        self.assertIn("a", remove_items)

    def test_single_insertion_detected(self):
        diff = ListDiffCalculator.diff(["a", "b", "c"], ["a", "b", "c", "d"])

        insert_items = [i.item for i in diff.inserts]
        self.assertIn("d", insert_items)

    def test_replace_one_item_detected_as_remove_and_insert(self):
        diff = ListDiffCalculator.diff(["a", "b", "c"], ["a", "x", "c"])

        self.assertEqual(["b"], [r.item for r in diff.removes])
        self.assertEqual(["x"], [i.item for i in diff.inserts])

    def test_key_fn_used_for_object_comparison(self):
        old = [{"id": 1, "v": "a"}, {"id": 2, "v": "b"}]
        new = [{"id": 2, "v": "b"}, {"id": 3, "v": "c"}]

        diff = ListDiffCalculator.diff(old, new, key_fn=lambda x: x["id"])

        remove_ids = [r.item["id"] for r in diff.removes]
        insert_ids = [i.item["id"] for i in diff.inserts]
        self.assertIn(1, remove_ids)
        self.assertIn(3, insert_ids)

    def test_apply_to_list_remove(self):
        target = ["a", "b", "c"]
        diff = ListDiffCalculator.diff(target, ["b", "c"])
        ListDiffCalculator.apply_to_list(target, diff)

        self.assertEqual(["b", "c"], target)

    def test_apply_to_list_insert(self):
        target = ["a", "c"]
        diff = ListDiffCalculator.diff(target, ["a", "b", "c"])
        ListDiffCalculator.apply_to_list(target, diff)

        self.assertIn("b", target)

    def test_apply_to_list_produces_target_list(self):
        old = ["a", "b", "c", "d"]
        new = ["b", "c", "e", "d"]
        target = list(old)

        diff = ListDiffCalculator.diff(old, new)
        ListDiffCalculator.apply_to_list(target, diff)

        # "a" removed, "e" inserted
        self.assertNotIn("a", target)
        self.assertIn("e", target)
        self.assertIn("b", target)
        self.assertIn("c", target)
        self.assertIn("d", target)

    def test_is_empty_true_for_blank_diff(self):
        diff = ListDiff(inserts=[], removes=[], moves=[])
        self.assertTrue(diff.is_empty)

    def test_is_empty_false_when_any_operation_exists(self):
        diff = ListDiff(inserts=[DiffInsert(index=0, item="x")], removes=[], moves=[])
        self.assertFalse(diff.is_empty)

    def test_both_lists_empty_produces_empty_diff(self):
        diff = ListDiffCalculator.diff([], [])
        self.assertTrue(diff.is_empty)


if __name__ == "__main__":
    unittest.main()
