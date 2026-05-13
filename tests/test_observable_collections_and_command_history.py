"""Tests for ObservableList, ObservableDict, and CommandHistory."""
import unittest

from gui_do.data.observable_collections import (
    ChangeKind,
    ObservableDict,
    ObservableList,
)
from gui_do.state.command_history import (
    CommandHistory,
)


# ===========================================================================
# Helpers
# ===========================================================================


class _SetCmd:
    """Simple reversible command for testing."""

    def __init__(self, target: list, value):
        self._target = target
        self._value = value
        self._prev = None

    @property
    def description(self) -> str:
        return f"Set to {self._value}"

    def execute(self) -> None:
        self._prev = self._target[0] if self._target else None
        self._target.clear()
        self._target.append(self._value)

    def undo(self) -> None:
        self._target.clear()
        if self._prev is not None:
            self._target.append(self._prev)


# ===========================================================================
# ObservableList
# ===========================================================================


class TestObservableList(unittest.TestCase):
    def test_initial_items_accessible(self):
        lst = ObservableList([1, 2, 3])
        self.assertEqual([1, 2, 3], lst.snapshot())

    def test_len(self):
        lst = ObservableList([1, 2])
        self.assertEqual(2, len(lst))

    def test_getitem(self):
        lst = ObservableList(["a", "b"])
        self.assertEqual("b", lst[1])

    def test_contains(self):
        lst = ObservableList([10, 20])
        self.assertIn(10, lst)
        self.assertNotIn(99, lst)

    def test_iter(self):
        lst = ObservableList([1, 2, 3])
        self.assertEqual([1, 2, 3], list(lst))

    def test_index(self):
        lst = ObservableList(["a", "b", "c"])
        self.assertEqual(1, lst.index("b"))

    def test_snapshot_returns_copy(self):
        lst = ObservableList([1, 2])
        snap = lst.snapshot()
        snap.append(99)
        self.assertEqual(2, len(lst))

    def test_append_fires_added_event(self):
        changes = []
        lst = ObservableList()
        lst.subscribe(changes.append)
        lst.append("x")
        self.assertEqual(1, len(changes))
        self.assertEqual(ChangeKind.ADDED, changes[0].kind)
        self.assertEqual("x", changes[0].new_value)

    def test_insert_fires_added_event(self):
        changes = []
        lst = ObservableList([1, 3])
        lst.subscribe(changes.append)
        lst.insert(1, 2)
        self.assertEqual(ChangeKind.ADDED, changes[0].kind)
        self.assertEqual([1, 2, 3], lst.snapshot())

    def test_remove_at_fires_removed_event(self):
        changes = []
        lst = ObservableList([1, 2, 3])
        lst.subscribe(changes.append)
        removed = lst.remove_at(1)
        self.assertEqual(2, removed)
        self.assertEqual(ChangeKind.REMOVED, changes[0].kind)
        self.assertEqual(2, changes[0].old_value)

    def test_remove_by_value(self):
        lst = ObservableList([1, 2, 3])
        result = lst.remove(2)
        self.assertTrue(result)
        self.assertEqual([1, 3], lst.snapshot())

    def test_remove_missing_returns_false(self):
        lst = ObservableList([1])
        self.assertFalse(lst.remove(99))

    def test_replace_fires_replaced_event(self):
        changes = []
        lst = ObservableList([1, 2, 3])
        lst.subscribe(changes.append)
        old = lst.replace(1, 99)
        self.assertEqual(2, old)
        self.assertEqual(ChangeKind.REPLACED, changes[0].kind)
        self.assertEqual(99, changes[0].new_value)

    def test_setitem_triggers_replace(self):
        changes = []
        lst = ObservableList([1, 2, 3])
        lst.subscribe(changes.append)
        lst[0] = 10
        self.assertEqual(ChangeKind.REPLACED, changes[0].kind)

    def test_move_item(self):
        changes = []
        lst = ObservableList([1, 2, 3])
        lst.subscribe(changes.append)
        lst.move(0, 2)
        self.assertEqual(ChangeKind.MOVED, changes[0].kind)
        self.assertEqual([2, 3, 1], lst.snapshot())

    def test_move_out_of_range_raises(self):
        lst = ObservableList([1, 2])
        with self.assertRaises(IndexError):
            lst.move(0, 5)

    def test_extend_fires_one_event_per_item(self):
        changes = []
        lst = ObservableList()
        lst.subscribe(changes.append)
        lst.extend([1, 2, 3])
        self.assertEqual(3, len(changes))

    def test_clear_fires_cleared(self):
        changes = []
        lst = ObservableList([1, 2])
        lst.subscribe(changes.append)
        lst.clear()
        self.assertEqual(ChangeKind.CLEARED, changes[0].kind)
        self.assertEqual(0, len(lst))

    def test_clear_empty_list_does_not_fire(self):
        changes = []
        lst = ObservableList()
        lst.subscribe(changes.append)
        lst.clear()
        self.assertEqual([], changes)

    def test_set_all_fires_clear_then_adds(self):
        changes = []
        lst = ObservableList([1, 2])
        lst.subscribe(changes.append)
        lst.set_all([10, 20, 30])
        kinds = [c.kind for c in changes]
        self.assertIn(ChangeKind.CLEARED, kinds)
        adds = [c for c in changes if c.kind == ChangeKind.ADDED]
        self.assertEqual(3, len(adds))

    def test_sort_fires_cleared_then_added(self):
        changes = []
        lst = ObservableList([3, 1, 2])
        lst.subscribe(changes.append)
        lst.sort()
        self.assertEqual([1, 2, 3], lst.snapshot())
        self.assertEqual(ChangeKind.CLEARED, changes[0].kind)

    def test_unsubscribe_stops_notifications(self):
        changes = []
        lst = ObservableList()
        unsub = lst.subscribe(changes.append)
        unsub()
        lst.append("x")
        self.assertEqual([], changes)

    def test_non_callable_listener_raises(self):
        lst = ObservableList()
        with self.assertRaises(ValueError):
            lst.subscribe("not_callable")


# ===========================================================================
# ObservableDict
# ===========================================================================


class TestObservableDict(unittest.TestCase):
    def test_initial_keys_accessible(self):
        d = ObservableDict({"a": 1, "b": 2})
        self.assertIn("a", d)

    def test_getitem(self):
        d = ObservableDict({"x": 42})
        self.assertEqual(42, d["x"])

    def test_len(self):
        d = ObservableDict({"a": 1, "b": 2})
        self.assertEqual(2, len(d))

    def test_get_with_default(self):
        d = ObservableDict()
        self.assertEqual("default", d.get("missing", "default"))

    def test_snapshot_returns_copy(self):
        d = ObservableDict({"a": 1})
        snap = d.snapshot()
        snap["extra"] = 99
        self.assertNotIn("extra", d)

    def test_setitem_new_key_fires_added(self):
        changes = []
        d = ObservableDict()
        d.subscribe(changes.append)
        d["k"] = 1
        self.assertEqual(ChangeKind.ADDED, changes[0].kind)
        self.assertEqual("k", changes[0].key)

    def test_setitem_existing_key_fires_replaced(self):
        changes = []
        d = ObservableDict({"k": 1})
        d.subscribe(changes.append)
        d["k"] = 2
        self.assertEqual(ChangeKind.REPLACED, changes[0].kind)
        self.assertEqual(1, changes[0].old_value)
        self.assertEqual(2, changes[0].new_value)

    def test_delitem_fires_removed(self):
        changes = []
        d = ObservableDict({"k": 10})
        d.subscribe(changes.append)
        del d["k"]
        self.assertEqual(ChangeKind.REMOVED, changes[0].kind)
        self.assertEqual(10, changes[0].old_value)

    def test_pop_removes_and_returns(self):
        d = ObservableDict({"k": 7})
        val = d.pop("k")
        self.assertEqual(7, val)
        self.assertNotIn("k", d)

    def test_pop_missing_with_default(self):
        d = ObservableDict()
        self.assertEqual("def", d.pop("nope", "def"))

    def test_pop_missing_without_default_raises(self):
        d = ObservableDict()
        with self.assertRaises(KeyError):
            d.pop("nope")

    def test_update_fires_per_key(self):
        changes = []
        d = ObservableDict()
        d.subscribe(changes.append)
        d.update({"a": 1, "b": 2})
        self.assertEqual(2, len(changes))

    def test_setdefault_adds_when_absent(self):
        d = ObservableDict()
        val = d.setdefault("k", 99)
        self.assertEqual(99, val)
        self.assertEqual(99, d["k"])

    def test_setdefault_does_not_overwrite(self):
        d = ObservableDict({"k": 1})
        val = d.setdefault("k", 99)
        self.assertEqual(1, val)

    def test_clear_fires_cleared(self):
        changes = []
        d = ObservableDict({"a": 1})
        d.subscribe(changes.append)
        d.clear()
        self.assertEqual(ChangeKind.CLEARED, changes[0].kind)
        self.assertEqual(0, len(d))

    def test_iter_over_keys(self):
        d = ObservableDict({"a": 1, "b": 2})
        self.assertEqual({"a", "b"}, set(d))

    def test_unsubscribe_stops_notifications(self):
        changes = []
        d = ObservableDict()
        unsub = d.subscribe(changes.append)
        unsub()
        d["x"] = 1
        self.assertEqual([], changes)


# ===========================================================================
# CommandHistory
# ===========================================================================


class TestCommandHistory(unittest.TestCase):
    def _state(self):
        return [0]

    def test_can_undo_false_when_empty(self):
        h = CommandHistory()
        self.assertFalse(h.can_undo)

    def test_can_redo_false_when_empty(self):
        h = CommandHistory()
        self.assertFalse(h.can_redo)

    def test_push_executes_command(self):
        state = self._state()
        h = CommandHistory()
        h.push(_SetCmd(state, 42))
        self.assertEqual(42, state[0])

    def test_push_enables_undo(self):
        h = CommandHistory()
        h.push(_SetCmd(self._state(), 1))
        self.assertTrue(h.can_undo)

    def test_undo_reverses_command(self):
        state = [10]
        h = CommandHistory()
        h.push(_SetCmd(state, 99))
        h.undo()
        self.assertEqual(10, state[0])

    def test_undo_enables_redo(self):
        h = CommandHistory()
        h.push(_SetCmd(self._state(), 1))
        h.undo()
        self.assertTrue(h.can_redo)

    def test_redo_re_executes_command(self):
        state = [0]
        h = CommandHistory()
        h.push(_SetCmd(state, 5))
        h.undo()
        h.redo()
        self.assertEqual(5, state[0])

    def test_push_after_undo_clears_redo(self):
        h = CommandHistory()
        h.push(_SetCmd(self._state(), 1))
        h.undo()
        h.push(_SetCmd(self._state(), 2))
        self.assertFalse(h.can_redo)

    def test_undo_description(self):
        h = CommandHistory()
        h.push(_SetCmd(self._state(), 7))
        self.assertIn("7", h.undo_description)

    def test_redo_description(self):
        h = CommandHistory()
        h.push(_SetCmd(self._state(), 3))
        h.undo()
        self.assertIn("3", h.redo_description)

    def test_undo_returns_false_when_empty(self):
        h = CommandHistory()
        self.assertFalse(h.undo())

    def test_redo_returns_false_when_empty(self):
        h = CommandHistory()
        self.assertFalse(h.redo())

    def test_undo_stack_size(self):
        h = CommandHistory()
        h.push(_SetCmd(self._state(), 1))
        h.push(_SetCmd(self._state(), 2))
        self.assertEqual(2, h.undo_stack_size)

    def test_redo_stack_size_after_undo(self):
        h = CommandHistory()
        h.push(_SetCmd(self._state(), 1))
        h.undo()
        self.assertEqual(1, h.redo_stack_size)

    def test_clear_empties_both_stacks(self):
        h = CommandHistory()
        h.push(_SetCmd(self._state(), 1))
        h.clear()
        self.assertFalse(h.can_undo)
        self.assertFalse(h.can_redo)

    def test_subscribe_fires_on_push(self):
        events = []
        h = CommandHistory()
        h.subscribe(events.append)
        h.push(_SetCmd(self._state(), 1))
        self.assertIn("push", events)

    def test_subscribe_fires_on_undo(self):
        events = []
        h = CommandHistory()
        h.push(_SetCmd(self._state(), 1))
        h.subscribe(events.append)
        h.undo()
        self.assertIn("undo", events)

    def test_subscribe_fires_on_redo(self):
        events = []
        h = CommandHistory()
        h.push(_SetCmd(self._state(), 1))
        h.undo()
        h.subscribe(events.append)
        h.redo()
        self.assertIn("redo", events)

    def test_unsubscribe_stops_events(self):
        events = []
        h = CommandHistory()
        unsub = h.subscribe(events.append)
        unsub()
        h.push(_SetCmd(self._state(), 1))
        self.assertEqual([], events)

    def test_transaction_context_manager(self):
        state_a = [0]
        state_b = [0]
        h = CommandHistory()
        with h.transaction("Bulk"):
            h.push(_SetCmd(state_a, 10))
            h.push(_SetCmd(state_b, 20))
        self.assertEqual(10, state_a[0])
        self.assertEqual(20, state_b[0])
        self.assertEqual(1, h.undo_stack_size)

    def test_transaction_undo_reverses_all_commands(self):
        state_a = [1]
        state_b = [2]
        h = CommandHistory()
        with h.transaction("Edit"):
            h.push(_SetCmd(state_a, 10))
            h.push(_SetCmd(state_b, 20))
        h.undo()
        self.assertEqual(1, state_a[0])
        self.assertEqual(2, state_b[0])

    def test_transaction_aborted_on_exception(self):
        h = CommandHistory()
        try:
            with h.transaction("Fail") as tx:
                tx.add(_SetCmd(self._state(), 99))
                raise RuntimeError("abort")
        except RuntimeError:
            pass
        self.assertFalse(h.can_undo)

    def test_begin_transaction_while_open_raises(self):
        h = CommandHistory()
        h.begin_transaction("A")
        with self.assertRaises(RuntimeError):
            h.begin_transaction("B")
        h.abort_transaction()

    def test_end_transaction_without_open_raises(self):
        h = CommandHistory()
        with self.assertRaises(RuntimeError):
            h.end_transaction()

    def test_abort_transaction_without_open_raises(self):
        h = CommandHistory()
        with self.assertRaises(RuntimeError):
            h.abort_transaction()

    def test_max_size_limits_undo_stack(self):
        h = CommandHistory(max_size=3)
        for i in range(5):
            h.push(_SetCmd(self._state(), i))
        self.assertLessEqual(h.undo_stack_size, 3)

    def test_push_with_execute_false_does_not_run_command(self):
        state = [0]
        h = CommandHistory()
        h.push(_SetCmd(state, 99), execute=False)
        self.assertEqual(0, state[0])
        self.assertTrue(h.can_undo)


if __name__ == "__main__":
    unittest.main()
