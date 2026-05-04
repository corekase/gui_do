"""Tests for reactive_batch — deferred ObservableValue notification batching."""
import unittest

import gui_do
from gui_do import reactive_batch
from gui_do.data.presentation_model import ObservableValue
from gui_do.data.observable_collections import ObservableList


class TestReactiveBatchContextManager(unittest.TestCase):
    def test_no_batch_notifies_immediately(self):
        a = ObservableValue(0)
        calls = []
        a.subscribe(calls.append)
        a.value = 1
        self.assertEqual(calls, [1])

    def test_batch_defers_until_exit(self):
        a = ObservableValue(0)
        calls = []
        a.subscribe(calls.append)
        with reactive_batch():
            a.value = 1
            self.assertEqual(calls, [], "Observer must not fire inside batch")
        self.assertEqual(calls, [1])

    def test_batch_deduplcates_repeated_assignment(self):
        a = ObservableValue(0)
        calls = []
        a.subscribe(calls.append)
        with reactive_batch():
            a.value = 1
            a.value = 2
            a.value = 3
        # Observer fires once with final value
        self.assertEqual(calls, [3])

    def test_multiple_observables_notify_once_each(self):
        a = ObservableValue(0)
        b = ObservableValue(0)
        a_calls = []
        b_calls = []
        a.subscribe(a_calls.append)
        b.subscribe(b_calls.append)
        with reactive_batch():
            a.value = 10
            b.value = 20
        self.assertEqual(a_calls, [10])
        self.assertEqual(b_calls, [20])

    def test_nested_batch_defers_to_outermost_exit(self):
        a = ObservableValue(0)
        calls = []
        a.subscribe(calls.append)
        with reactive_batch():
            with reactive_batch():
                a.value = 5
                self.assertEqual(calls, [])
            # Still inside outermost batch
            self.assertEqual(calls, [])
        self.assertEqual(calls, [5])

    def test_exception_discards_pending_notifications(self):
        a = ObservableValue(0)
        calls = []
        a.subscribe(calls.append)
        try:
            with reactive_batch():
                a.value = 99
                raise RuntimeError("test error")
        except RuntimeError:
            pass
        # Notification should be discarded (state may be inconsistent)
        self.assertEqual(calls, [])

    def test_no_notification_when_value_unchanged_inside_batch(self):
        a = ObservableValue(42)
        calls = []
        a.subscribe(calls.append)
        with reactive_batch():
            a.value = 42  # no change
        self.assertEqual(calls, [])

    def test_is_batching_reflects_context(self):
        from gui_do.data.reactive_batch import is_batching
        self.assertFalse(is_batching())
        with reactive_batch():
            self.assertTrue(is_batching())
        self.assertFalse(is_batching())

    def test_batch_is_exported_from_gui_do(self):
        self.assertTrue(callable(gui_do.reactive_batch))

    def test_reentrant_observer_notification_handled_safely(self):
        """Observer mutation during flush is queued and flushed in same pass."""
        a = ObservableValue(0)
        b = ObservableValue(0)
        b_calls = []
        b.subscribe(b_calls.append)

        def on_a_change(v):
            b.value = v + 100

        a.subscribe(on_a_change)

        with reactive_batch():
            a.value = 1
        # b should have been updated during flush re-entrancy
        self.assertEqual(b_calls, [101])


class TestObservableListBatchReplace(unittest.TestCase):
    def test_batch_replace_fires_one_cleared_event(self):
        lst = ObservableList([1, 2, 3])
        from gui_do.data.observable_collections import ChangeKind
        events = []
        lst.subscribe(events.append)
        lst.batch_replace([10, 20, 30])
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].kind, ChangeKind.CLEARED)

    def test_batch_replace_updates_contents(self):
        lst = ObservableList([1, 2, 3])
        lst.batch_replace([10, 20])
        self.assertEqual(list(lst), [10, 20])

    def test_batch_replace_empty_list(self):
        lst = ObservableList([1, 2])
        events = []
        lst.subscribe(events.append)
        lst.batch_replace([])
        self.assertEqual(list(lst), [])
        self.assertEqual(len(events), 1)
