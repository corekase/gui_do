import unittest

from gui_do.data.observable_collections import (
    ChangeKind,
    CollectionChange,
    ObservableDict,
    ObservableList,
)


# ---------------------------------------------------------------------------
# ObservableList
# ---------------------------------------------------------------------------


class TestObservableList(unittest.TestCase):
    def _make(self, initial=None):
        return ObservableList(initial)

    def test_initial_contents_accessible_via_snapshot(self):
        lst = self._make([1, 2, 3])
        self.assertEqual([1, 2, 3], lst.snapshot())

    def test_append_fires_added_event_with_correct_index_and_value(self):
        lst = self._make()
        changes = []
        lst.subscribe(changes.append)

        lst.append("x")

        self.assertEqual(1, len(changes))
        self.assertEqual(ChangeKind.ADDED, changes[0].kind)
        self.assertEqual(0, changes[0].index)
        self.assertEqual("x", changes[0].new_value)

    def test_insert_fires_added_event_at_correct_position(self):
        lst = self._make(["a", "c"])
        changes = []
        lst.subscribe(changes.append)

        lst.insert(1, "b")

        self.assertEqual(ChangeKind.ADDED, changes[0].kind)
        self.assertEqual(1, changes[0].index)
        self.assertEqual("b", changes[0].new_value)
        self.assertEqual(["a", "b", "c"], lst.snapshot())

    def test_remove_at_fires_removed_event_with_old_value(self):
        lst = self._make(["a", "b", "c"])
        changes = []
        lst.subscribe(changes.append)

        removed = lst.remove_at(1)

        self.assertEqual("b", removed)
        self.assertEqual(ChangeKind.REMOVED, changes[0].kind)
        self.assertEqual(1, changes[0].index)
        self.assertEqual("b", changes[0].old_value)
        self.assertEqual(["a", "c"], lst.snapshot())

    def test_remove_existing_item_returns_true_and_fires_event(self):
        lst = self._make(["a", "b"])
        changes = []
        lst.subscribe(changes.append)

        result = lst.remove("a")

        self.assertTrue(result)
        self.assertEqual(ChangeKind.REMOVED, changes[0].kind)

    def test_remove_missing_item_returns_false_and_fires_no_event(self):
        lst = self._make(["a"])
        changes = []
        lst.subscribe(changes.append)

        result = lst.remove("z")

        self.assertFalse(result)
        self.assertEqual([], changes)

    def test_setitem_fires_replaced_event(self):
        lst = self._make(["a", "b"])
        changes = []
        lst.subscribe(changes.append)

        lst[0] = "x"

        self.assertEqual(ChangeKind.REPLACED, changes[0].kind)
        self.assertEqual(0, changes[0].index)
        self.assertEqual("a", changes[0].old_value)
        self.assertEqual("x", changes[0].new_value)

    def test_move_reorders_items_and_fires_moved_event(self):
        lst = self._make(["a", "b", "c"])
        changes = []
        lst.subscribe(changes.append)

        lst.move(0, 2)

        self.assertEqual(ChangeKind.MOVED, changes[0].kind)
        self.assertEqual(["b", "c", "a"], lst.snapshot())

    def test_move_same_index_is_noop(self):
        lst = self._make(["a", "b"])
        changes = []
        lst.subscribe(changes.append)

        lst.move(0, 0)

        self.assertEqual([], changes)

    def test_clear_fires_single_cleared_event(self):
        lst = self._make([1, 2, 3])
        changes = []
        lst.subscribe(changes.append)

        lst.clear()

        self.assertEqual(1, len(changes))
        self.assertEqual(ChangeKind.CLEARED, changes[0].kind)
        self.assertEqual([], lst.snapshot())

    def test_clear_on_empty_list_fires_no_event(self):
        lst = self._make()
        changes = []
        lst.subscribe(changes.append)

        lst.clear()

        self.assertEqual([], changes)

    def test_extend_fires_one_added_event_per_item(self):
        lst = self._make()
        changes = []
        lst.subscribe(changes.append)

        lst.extend(["a", "b", "c"])

        self.assertEqual(3, len(changes))
        self.assertTrue(all(c.kind is ChangeKind.ADDED for c in changes))

    def test_unsubscribe_stops_notifications(self):
        lst = self._make()
        received = []
        unsub = lst.subscribe(received.append)

        lst.append(1)
        unsub()
        lst.append(2)

        self.assertEqual(1, len(received))

    def test_multiple_subscribers_all_notified(self):
        lst = self._make()
        a = []
        b = []
        lst.subscribe(a.append)
        lst.subscribe(b.append)

        lst.append(42)

        self.assertEqual(1, len(a))
        self.assertEqual(1, len(b))

    def test_len_and_contains_work_without_notification(self):
        lst = self._make([1, 2, 3])
        changes = []
        lst.subscribe(changes.append)

        self.assertEqual(3, len(lst))
        self.assertIn(2, lst)
        self.assertEqual([], changes)

    def test_sort_fires_cleared_then_added_events(self):
        lst = self._make([3, 1, 2])
        kinds = []
        lst.subscribe(lambda c: kinds.append(c.kind))

        lst.sort()

        self.assertEqual(ChangeKind.CLEARED, kinds[0])
        self.assertEqual([ChangeKind.ADDED] * 3, kinds[1:])
        self.assertEqual([1, 2, 3], lst.snapshot())


# ---------------------------------------------------------------------------
# ObservableDict
# ---------------------------------------------------------------------------


class TestObservableDict(unittest.TestCase):
    def _make(self, initial=None):
        return ObservableDict(initial)

    def test_initial_contents_accessible_via_snapshot(self):
        d = self._make({"a": 1, "b": 2})
        self.assertEqual({"a": 1, "b": 2}, d.snapshot())

    def test_setitem_new_key_fires_added_event(self):
        d = self._make()
        changes = []
        d.subscribe(changes.append)

        d["x"] = 10

        self.assertEqual(1, len(changes))
        self.assertEqual(ChangeKind.ADDED, changes[0].kind)
        self.assertEqual("x", changes[0].key)
        self.assertEqual(10, changes[0].new_value)

    def test_setitem_existing_key_fires_replaced_event(self):
        d = self._make({"x": 1})
        changes = []
        d.subscribe(changes.append)

        d["x"] = 99

        self.assertEqual(ChangeKind.REPLACED, changes[0].kind)
        self.assertEqual(1, changes[0].old_value)
        self.assertEqual(99, changes[0].new_value)

    def test_delitem_fires_removed_event(self):
        d = self._make({"a": 1})
        changes = []
        d.subscribe(changes.append)

        del d["a"]

        self.assertEqual(ChangeKind.REMOVED, changes[0].kind)
        self.assertEqual("a", changes[0].key)
        self.assertEqual(1, changes[0].old_value)

    def test_pop_existing_key_fires_removed_event(self):
        d = self._make({"k": 5})
        changes = []
        d.subscribe(changes.append)

        val = d.pop("k")

        self.assertEqual(5, val)
        self.assertEqual(ChangeKind.REMOVED, changes[0].kind)

    def test_pop_missing_key_with_default_returns_default_no_event(self):
        d = self._make()
        changes = []
        d.subscribe(changes.append)

        result = d.pop("missing", "default")

        self.assertEqual("default", result)
        self.assertEqual([], changes)

    def test_pop_missing_key_without_default_raises_key_error(self):
        d = self._make()
        with self.assertRaises(KeyError):
            d.pop("no_such_key")

    def test_update_fires_events_per_key(self):
        d = self._make({"a": 1})
        changes = []
        d.subscribe(changes.append)

        d.update({"a": 2, "b": 3})

        self.assertEqual(2, len(changes))
        kinds = {c.key: c.kind for c in changes}
        self.assertEqual(ChangeKind.REPLACED, kinds["a"])
        self.assertEqual(ChangeKind.ADDED, kinds["b"])

    def test_clear_fires_single_cleared_event(self):
        d = self._make({"a": 1})
        changes = []
        d.subscribe(changes.append)

        d.clear()

        self.assertEqual(1, len(changes))
        self.assertEqual(ChangeKind.CLEARED, changes[0].kind)
        self.assertEqual({}, d.snapshot())

    def test_clear_on_empty_dict_fires_no_event(self):
        d = self._make()
        changes = []
        d.subscribe(changes.append)

        d.clear()

        self.assertEqual([], changes)

    def test_setdefault_adds_missing_key_and_fires_event(self):
        d = self._make()
        changes = []
        d.subscribe(changes.append)

        val = d.setdefault("k", 42)

        self.assertEqual(42, val)
        self.assertEqual(1, len(changes))
        self.assertEqual(ChangeKind.ADDED, changes[0].kind)

    def test_setdefault_existing_key_returns_existing_value_no_event(self):
        d = self._make({"k": 7})
        changes = []
        d.subscribe(changes.append)

        val = d.setdefault("k", 99)

        self.assertEqual(7, val)
        self.assertEqual([], changes)

    def test_unsubscribe_stops_notifications(self):
        d = self._make()
        received = []
        unsub = d.subscribe(received.append)

        d["a"] = 1
        unsub()
        d["b"] = 2

        self.assertEqual(1, len(received))

    def test_contains_and_get_do_not_fire_events(self):
        d = self._make({"k": 5})
        changes = []
        d.subscribe(changes.append)

        _ = "k" in d
        _ = d.get("k", 0)

        self.assertEqual([], changes)


if __name__ == "__main__":
    unittest.main()
