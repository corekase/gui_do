import unittest

import pygame

from gui_do.data.presentation_model import (
    ComputedValue,
    ObservableValue,
    PresentationModel,
)
from gui_do.data.binding import Binding, BindingGroup
from gui_do.data.invalidation import InvalidationTracker


# ---------------------------------------------------------------------------
# ObservableValue
# ---------------------------------------------------------------------------


class TestObservableValue(unittest.TestCase):
    def test_initial_value(self):
        ov = ObservableValue(42)
        self.assertEqual(42, ov.value)

    def test_set_value_notifies_observer(self):
        ov = ObservableValue(0)
        received = []
        ov.subscribe(received.append)
        ov.value = 7
        self.assertEqual([7], received)

    def test_set_same_value_does_not_notify(self):
        ov = ObservableValue(0)
        received = []
        ov.subscribe(received.append)
        ov.value = 0
        self.assertEqual([], received)

    def test_multiple_observers_all_notified(self):
        ov = ObservableValue(0)
        a, b = [], []
        ov.subscribe(a.append)
        ov.subscribe(b.append)
        ov.value = 1
        self.assertEqual([1], a)
        self.assertEqual([1], b)

    def test_unsubscribe_stops_notification(self):
        ov = ObservableValue(0)
        received = []
        unsub = ov.subscribe(received.append)
        unsub()
        ov.value = 1
        self.assertEqual([], received)

    def test_observer_count(self):
        ov = ObservableValue(0)
        self.assertEqual(0, ov.observer_count)
        unsub = ov.subscribe(lambda v: None)
        self.assertEqual(1, ov.observer_count)
        unsub()
        self.assertEqual(0, ov.observer_count)

    def test_set_silently_does_not_notify(self):
        ov = ObservableValue(0)
        received = []
        ov.subscribe(received.append)
        ov.set_silently(99)
        self.assertEqual([], received)
        self.assertEqual(99, ov.value)

    def test_force_notify_fires_even_when_unchanged(self):
        ov = ObservableValue(5)
        received = []
        ov.subscribe(received.append)
        ov.force_notify()
        self.assertEqual([5], received)


# ---------------------------------------------------------------------------
# ComputedValue
# ---------------------------------------------------------------------------


class TestComputedValue(unittest.TestCase):
    def test_initial_value_computed_lazily(self):
        a = ObservableValue(3)
        b = ObservableValue(4)
        cv = ComputedValue(lambda: a.value + b.value)
        self.assertEqual(7, cv.value)

    def test_value_updates_when_dep_changes(self):
        a = ObservableValue(1)
        cv = ComputedValue(lambda: a.value * 2)
        _ = cv.value  # prime
        a.value = 5
        self.assertEqual(10, cv.value)

    def test_subscriber_notified_on_dep_change(self):
        a = ObservableValue(1)
        cv = ComputedValue(lambda: a.value + 10)
        _ = cv.value  # prime auto-tracking so dependency is registered
        received = []
        cv.subscribe(received.append)
        a.value = 5
        self.assertEqual([15], received)

    def test_explicit_deps_registered(self):
        a = ObservableValue(2)
        b = ObservableValue(3)
        cv = ComputedValue(lambda: a.value * b.value, deps=[a, b])
        received = []
        cv.subscribe(received.append)
        b.value = 10
        self.assertEqual([20], received)

    def test_auto_tracked_deps_discovered(self):
        a = ObservableValue(1)
        b = ObservableValue(2)
        cv = ComputedValue(lambda: a.value + b.value)
        _ = cv.value  # triggers auto-tracking
        received = []
        cv.subscribe(received.append)
        a.value = 10
        self.assertEqual([12], received)

    def test_unsubscribe_stops_notification(self):
        a = ObservableValue(0)
        cv = ComputedValue(lambda: a.value)
        received = []
        unsub = cv.subscribe(received.append)
        _ = cv.value
        unsub()
        a.value = 99
        self.assertEqual([], received)

    def test_cached_value_not_recomputed_when_not_dirty(self):
        calls = []

        def compute():
            calls.append(True)
            return 42

        a = ObservableValue(0)
        cv = ComputedValue(compute, deps=[a])
        _ = cv.value  # first compute
        _ = cv.value  # should use cache
        self.assertEqual(1, len(calls))


# ---------------------------------------------------------------------------
# PresentationModel
# ---------------------------------------------------------------------------


class TestPresentationModel(unittest.TestCase):
    def test_bind_registers_observer_and_receives_changes(self):
        class _MyModel(PresentationModel):
            def __init__(self):
                super().__init__()
                self.name = ObservableValue("Alice")

        model = _MyModel()
        received = []
        model.bind(model.name, received.append)
        model.name.value = "Bob"
        self.assertEqual(["Bob"], received)

    def test_dispose_unsubscribes_all_bindings(self):
        class _MyModel(PresentationModel):
            def __init__(self):
                super().__init__()
                self.x = ObservableValue(0)

        model = _MyModel()
        received = []
        model.bind(model.x, received.append)
        model.dispose()
        model.x.value = 999
        self.assertEqual([], received)


# ---------------------------------------------------------------------------
# Binding / BindingGroup
# ---------------------------------------------------------------------------


class _FakeControl:
    """Minimal control stub: has a settable attribute and a change callback."""

    def __init__(self):
        self.value = None
        self.on_change = None


class TestBinding(unittest.TestCase):
    def test_one_way_initial_value_applied(self):
        src = ObservableValue(10)
        ctrl = _FakeControl()
        Binding(src, ctrl, "value", mode="one_way")
        self.assertEqual(10, ctrl.value)

    def test_one_way_model_change_updates_control(self):
        src = ObservableValue(0)
        ctrl = _FakeControl()
        Binding(src, ctrl, "value", mode="one_way")
        src.value = 42
        self.assertEqual(42, ctrl.value)

    def test_one_way_control_change_does_not_update_model(self):
        src = ObservableValue(0)
        ctrl = _FakeControl()
        Binding(src, ctrl, "value", mode="one_way")
        ctrl.value = 99  # direct mutation — not via binding
        self.assertEqual(0, src.value)

    def test_two_way_model_change_updates_control(self):
        src = ObservableValue(1)
        ctrl = _FakeControl()
        Binding(src, ctrl, "value", mode="two_way", control_change_signal="on_change")
        src.value = 7
        self.assertEqual(7, ctrl.value)

    def test_two_way_control_change_updates_model(self):
        src = ObservableValue(0)
        ctrl = _FakeControl()
        Binding(src, ctrl, "value", mode="two_way", control_change_signal="on_change")
        ctrl.on_change(5)  # simulate control firing its change callback
        self.assertEqual(5, src.value)

    def test_two_way_no_infinite_loop(self):
        src = ObservableValue(0)
        ctrl = _FakeControl()
        Binding(src, ctrl, "value", mode="two_way", control_change_signal="on_change")
        # If loop guard fails this would recurse infinitely
        src.value = 3
        self.assertEqual(3, ctrl.value)
        self.assertEqual(3, src.value)

    def test_to_control_converter_applied(self):
        src = ObservableValue(0.5)
        ctrl = _FakeControl()
        Binding(src, ctrl, "value", mode="one_way", to_control=lambda v: round(v * 100))
        src.value = 0.75
        self.assertEqual(75, ctrl.value)

    def test_to_source_converter_applied(self):
        src = ObservableValue(0)
        ctrl = _FakeControl()
        Binding(src, ctrl, "value", mode="two_way",
                control_change_signal="on_change",
                to_source=lambda v: v * 2)
        ctrl.on_change(5)
        self.assertEqual(10, src.value)

    def test_dispose_stops_model_to_control_updates(self):
        src = ObservableValue(0)
        ctrl = _FakeControl()
        b = Binding(src, ctrl, "value", mode="one_way")
        b.dispose()
        src.value = 99
        self.assertEqual(0, ctrl.value)

    def test_dispose_restores_previous_control_callback(self):
        src = ObservableValue(0)
        ctrl = _FakeControl()
        prev_calls = []
        ctrl.on_change = prev_calls.append
        b = Binding(src, ctrl, "value", mode="two_way", control_change_signal="on_change")
        b.dispose()
        # Original callback restored
        ctrl.on_change(42)
        self.assertEqual([42], prev_calls)

    def test_disposed_property(self):
        src = ObservableValue(0)
        ctrl = _FakeControl()
        b = Binding(src, ctrl, "value")
        self.assertFalse(b.disposed)
        b.dispose()
        self.assertTrue(b.disposed)

    def test_invalid_mode_raises(self):
        src = ObservableValue(0)
        ctrl = _FakeControl()
        with self.assertRaises(ValueError):
            Binding(src, ctrl, "value", mode="bad_mode")

    def test_two_way_without_signal_raises(self):
        src = ObservableValue(0)
        ctrl = _FakeControl()
        with self.assertRaises(ValueError):
            Binding(src, ctrl, "value", mode="two_way")

    def test_sync_to_control_forces_resync(self):
        src = ObservableValue(5)
        ctrl = _FakeControl()
        b = Binding(src, ctrl, "value", mode="one_way")
        ctrl.value = 999  # manual overwrite
        b.sync_to_control()
        self.assertEqual(5, ctrl.value)


class TestBindingGroup(unittest.TestCase):
    def test_add_returns_binding(self):
        src = ObservableValue(0)
        ctrl = _FakeControl()
        group = BindingGroup()
        b = Binding(src, ctrl, "value")
        result = group.add(b)
        self.assertIs(b, result)

    def test_len_reflects_count(self):
        group = BindingGroup()
        src = ObservableValue(0)
        ctrl = _FakeControl()
        group.add(Binding(src, ctrl, "value"))
        group.add(Binding(src, ctrl, "value"))
        self.assertEqual(2, len(group))

    def test_dispose_stops_all_bindings(self):
        src = ObservableValue(0)
        ctrl1 = _FakeControl()
        ctrl2 = _FakeControl()
        group = BindingGroup()
        group.add(Binding(src, ctrl1, "value"))
        group.add(Binding(src, ctrl2, "value"))
        group.dispose()
        src.value = 99
        self.assertEqual(0, ctrl1.value)
        self.assertEqual(0, ctrl2.value)

    def test_dispose_clears_group(self):
        group = BindingGroup()
        src = ObservableValue(0)
        ctrl = _FakeControl()
        group.add(Binding(src, ctrl, "value"))
        group.dispose()
        self.assertEqual(0, len(group))

    def test_sync_all_to_control(self):
        src = ObservableValue(7)
        ctrl = _FakeControl()
        group = BindingGroup()
        group.add(Binding(src, ctrl, "value", mode="one_way"))
        ctrl.value = 0  # manual overwrite
        group.sync_all_to_control()
        self.assertEqual(7, ctrl.value)


# ---------------------------------------------------------------------------
# InvalidationTracker
# ---------------------------------------------------------------------------


class TestInvalidationTracker(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    def test_initially_full_redraw(self):
        tracker = InvalidationTracker()
        full, rects = tracker.begin_frame()
        self.assertTrue(full)
        self.assertEqual([], rects)

    def test_invalidate_all_sets_full_redraw(self):
        tracker = InvalidationTracker()
        tracker.end_frame()  # clear initial state
        tracker.invalidate_all()
        full, _ = tracker.begin_frame()
        self.assertTrue(full)

    def test_invalidate_rect_tracks_dirty_region(self):
        tracker = InvalidationTracker()
        tracker.set_screen_size((800, 600))
        tracker.end_frame()
        tracker.invalidate_rect(pygame.Rect(10, 10, 50, 50))
        full, rects = tracker.begin_frame()
        self.assertFalse(full)
        self.assertEqual(1, len(rects))

    def test_invalidate_rect_covering_full_screen_promotes_to_full_redraw(self):
        tracker = InvalidationTracker()
        tracker.set_screen_size((800, 600))
        tracker.end_frame()
        tracker.invalidate_rect(pygame.Rect(0, 0, 800, 600))
        full, _ = tracker.begin_frame()
        self.assertTrue(full)

    def test_end_frame_clears_dirty_state(self):
        tracker = InvalidationTracker()
        tracker.set_screen_size((800, 600))
        tracker.end_frame()
        tracker.invalidate_rect(pygame.Rect(0, 0, 10, 10))
        tracker.end_frame()
        full, rects = tracker.begin_frame()
        self.assertFalse(full)
        self.assertEqual([], rects)

    def test_merge_dirty_rects_unions_overlapping(self):
        tracker = InvalidationTracker()
        tracker.set_screen_size((800, 600))
        tracker.end_frame()
        tracker.invalidate_rect(pygame.Rect(0, 0, 50, 50))
        tracker.invalidate_rect(pygame.Rect(25, 25, 50, 50))
        merged = tracker.merge_dirty_rects()
        self.assertEqual(1, len(merged))

    def test_merge_dirty_rects_keeps_non_overlapping_separate(self):
        tracker = InvalidationTracker()
        tracker.set_screen_size((800, 600))
        tracker.end_frame()
        tracker.invalidate_rect(pygame.Rect(0, 0, 10, 10))
        tracker.invalidate_rect(pygame.Rect(500, 500, 10, 10))
        merged = tracker.merge_dirty_rects()
        self.assertEqual(2, len(merged))

    def test_merge_dirty_rects_empty_returns_empty(self):
        tracker = InvalidationTracker()
        self.assertEqual([], tracker.merge_dirty_rects())

    def test_multiple_rects_accumulated(self):
        tracker = InvalidationTracker()
        tracker.set_screen_size((800, 600))
        tracker.end_frame()
        tracker.invalidate_rect(pygame.Rect(0, 0, 10, 10))
        tracker.invalidate_rect(pygame.Rect(100, 100, 10, 10))
        tracker.invalidate_rect(pygame.Rect(200, 200, 10, 10))
        _, rects = tracker.begin_frame()
        self.assertEqual(3, len(rects))


if __name__ == "__main__":
    unittest.main()
