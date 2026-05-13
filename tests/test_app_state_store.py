"""Tests for gui_do.state.app_state_store."""
from __future__ import annotations

import unittest

from gui_do.state.app_state_store import (
    AppStateStore,
    StateTransaction,
)


class TestAppStateStore(unittest.TestCase):
    def test_empty_initial_state(self):
        store = AppStateStore()
        self.assertEqual(store.snapshot(), {})

    def test_initial_state_set(self):
        store = AppStateStore({"x": 1, "y": 2})
        self.assertEqual(store.get("x"), 1)
        self.assertEqual(store.get("y"), 2)

    def test_dispatch_updates_value(self):
        store = AppStateStore({"a": 0})
        store.dispatch({"a": 10})
        self.assertEqual(store.get("a"), 10)

    def test_dispatch_adds_new_key(self):
        store = AppStateStore()
        store.dispatch({"new": "hello"})
        self.assertEqual(store.get("new"), "hello")

    def test_get_missing_returns_default(self):
        store = AppStateStore()
        self.assertIsNone(store.get("missing"))
        self.assertEqual(store.get("missing", 42), 42)

    def test_snapshot_is_deep_copy(self):
        store = AppStateStore({"list": [1, 2, 3]})
        snap = store.snapshot()
        snap["list"].append(4)
        self.assertEqual(store.get("list"), [1, 2, 3])

    def test_restore_replaces_state(self):
        store = AppStateStore({"a": 1})
        store.restore({"b": 2})
        self.assertIsNone(store.get("a"))
        self.assertEqual(store.get("b"), 2)

    def test_key_subscriber_called_on_change(self):
        store = AppStateStore({"val": 0})
        received = []
        store.subscribe("val", received.append)
        store.dispatch({"val": 99})
        self.assertEqual(received, [99])

    def test_key_subscriber_not_called_without_change(self):
        store = AppStateStore({"val": 5})
        received = []
        store.subscribe("val", received.append)
        store.dispatch({"val": 5})  # same value
        self.assertEqual(received, [])

    def test_unsubscribe_stops_notifications(self):
        store = AppStateStore({"x": 0})
        received = []
        unsub = store.subscribe("x", received.append)
        unsub()
        store.dispatch({"x": 1})
        self.assertEqual(received, [])

    def test_restore_fires_key_subscribers(self):
        store = AppStateStore({"z": 0})
        received = []
        store.subscribe("z", received.append)
        store.restore({"z": 7})
        self.assertEqual(received, [7])


class TestStateSelector(unittest.TestCase):
    def test_initial_value_computed(self):
        store = AppStateStore({"count": 3})
        sel = store.select(lambda s: s.get("count", 0) * 2)
        self.assertEqual(sel.value, 6)

    def test_selector_updates_on_dispatch(self):
        store = AppStateStore({"n": 1})
        sel = store.select(lambda s: s.get("n", 0))
        store.dispatch({"n": 5})
        self.assertEqual(sel.value, 5)

    def test_selector_subscriber_fires_on_change(self):
        store = AppStateStore({"n": 1})
        sel = store.select(lambda s: s.get("n", 0))
        received = []
        sel.subscribe(received.append)
        store.dispatch({"n": 10})
        self.assertEqual(received, [10])

    def test_selector_subscriber_not_fired_on_same_derived(self):
        store = AppStateStore({"a": 1, "b": 2})
        # selector projects sum, so changing unrelated keys shouldn't fire
        # if sum stays the same — but let's test "same value" case:
        store.dispatch({"a": 1, "b": 2})  # no change
        sel = store.select(lambda s: s.get("a", 0))
        received = []
        sel.subscribe(received.append)
        store.dispatch({"b": 99})  # doesn't affect "a"
        self.assertEqual(received, [])

    def test_selector_unsubscribe(self):
        store = AppStateStore({"v": 0})
        sel = store.select(lambda s: s.get("v", 0))
        received = []
        unsub = sel.subscribe(received.append)
        unsub()
        store.dispatch({"v": 42})
        self.assertEqual(received, [])

    def test_multiple_selectors_independent(self):
        store = AppStateStore({"x": 1, "y": 10})
        sel_x = store.select(lambda s: s.get("x", 0))
        sel_y = store.select(lambda s: s.get("y", 0))
        store.dispatch({"x": 2})
        self.assertEqual(sel_x.value, 2)
        self.assertEqual(sel_y.value, 10)


class TestStateTransaction(unittest.TestCase):
    def test_patches_applied_atomically(self):
        store = AppStateStore({"a": 0, "b": 0})
        received = []
        store.subscribe("a", lambda v: received.append(("a", v)))
        store.subscribe("b", lambda v: received.append(("b", v)))

        with StateTransaction(store):
            store.dispatch({"a": 1})
            store.dispatch({"b": 2})

        # Both changes applied; subscribers fired after commit
        self.assertEqual(store.get("a"), 1)
        self.assertEqual(store.get("b"), 2)
        self.assertIn(("a", 1), received)
        self.assertIn(("b", 2), received)

    def test_exception_rolls_back(self):
        store = AppStateStore({"x": 0})
        try:
            with StateTransaction(store):
                store.dispatch({"x": 99})
                raise RuntimeError("oops")
        except RuntimeError:
            pass
        self.assertEqual(store.get("x"), 0)

    def test_no_partial_notification_during_transaction(self):
        store = AppStateStore({"a": 0})
        notify_count = [0]
        store.subscribe("a", lambda _: notify_count.__setitem__(0, notify_count[0] + 1))
        with StateTransaction(store):
            store.dispatch({"a": 1})
            store.dispatch({"a": 2})
            # Still inside tx — no notification yet
            self.assertEqual(notify_count[0], 0)
        # After commit — last value wins
        self.assertEqual(store.get("a"), 2)
        self.assertEqual(notify_count[0], 1)

    def test_nested_transaction_raises(self):
        store = AppStateStore()
        with self.assertRaises(RuntimeError):
            with StateTransaction(store):
                with StateTransaction(store):
                    pass


if __name__ == "__main__":
    unittest.main()
