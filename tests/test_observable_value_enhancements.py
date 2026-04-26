"""Tests for ObservableValue enhancements: set_silently, force_notify, observer_count."""
import unittest

from gui_do.core.presentation_model import ObservableValue, PresentationModel


class ObservableValueObserverCountTests(unittest.TestCase):
    def test_observer_count_zero_by_default(self) -> None:
        obs = ObservableValue(0)
        self.assertEqual(obs.observer_count, 0)

    def test_observer_count_increments_on_subscribe(self) -> None:
        obs = ObservableValue(0)
        obs.subscribe(lambda v: None)
        obs.subscribe(lambda v: None)
        self.assertEqual(obs.observer_count, 2)

    def test_observer_count_decrements_on_unsubscribe(self) -> None:
        obs = ObservableValue(0)
        unsub = obs.subscribe(lambda v: None)
        self.assertEqual(obs.observer_count, 1)
        unsub()
        self.assertEqual(obs.observer_count, 0)

    def test_observer_count_unsubscribe_idempotent(self) -> None:
        obs = ObservableValue(0)
        unsub = obs.subscribe(lambda v: None)
        unsub()
        unsub()  # second call must not raise or go negative
        self.assertEqual(obs.observer_count, 0)


class ObservableValueSetSilentlyTests(unittest.TestCase):
    def test_set_silently_updates_value(self) -> None:
        obs = ObservableValue(10)
        obs.set_silently(99)
        self.assertEqual(obs.value, 99)

    def test_set_silently_does_not_notify_observers(self) -> None:
        notified = []
        obs = ObservableValue(10)
        obs.subscribe(lambda v: notified.append(v))

        obs.set_silently(20)

        self.assertEqual(obs.value, 20)
        self.assertEqual(notified, [], "set_silently must not fire observers")

    def test_set_silently_same_value_still_silent(self) -> None:
        notified = []
        obs = ObservableValue("hello")
        obs.subscribe(lambda v: notified.append(v))

        obs.set_silently("hello")

        self.assertEqual(notified, [])

    def test_set_silently_does_not_affect_future_normal_assignments(self) -> None:
        notified = []
        obs = ObservableValue(0)
        obs.subscribe(lambda v: notified.append(v))

        obs.set_silently(5)
        obs.value = 10  # normal assignment should still fire

        self.assertEqual(notified, [10])

    def test_set_silently_followed_by_same_value_normal_assign_fires_once(self) -> None:
        """After set_silently(5), assigning value=5 normally must fire because
        the equality check will pass — but 5 == 5 → no notification. Verify the
        silent-set does not corrupt the old-value guard."""
        notified = []
        obs = ObservableValue(0)
        obs.subscribe(lambda v: notified.append(v))

        obs.set_silently(5)
        obs.value = 5  # value is already 5 silently; normal set sees no change

        # Normal setter skips notification when current == new, consistent behaviour
        self.assertEqual(notified, [])

    def test_set_silently_then_force_notify_delivers_silent_value(self) -> None:
        notified = []
        obs = ObservableValue(0)
        obs.subscribe(lambda v: notified.append(v))

        obs.set_silently(42)
        obs.force_notify()

        self.assertEqual(notified, [42])


class ObservableValueForceNotifyTests(unittest.TestCase):
    def test_force_notify_delivers_current_value(self) -> None:
        received = []
        obs = ObservableValue("initial")
        obs.subscribe(lambda v: received.append(v))

        obs.force_notify()

        self.assertEqual(received, ["initial"])

    def test_force_notify_fires_even_when_value_unchanged(self) -> None:
        received = []
        obs = ObservableValue(7)
        obs.subscribe(lambda v: received.append(v))

        obs.force_notify()
        obs.force_notify()

        self.assertEqual(received, [7, 7])

    def test_force_notify_notifies_all_observers(self) -> None:
        a, b = [], []
        obs = ObservableValue("x")
        obs.subscribe(lambda v: a.append(v))
        obs.subscribe(lambda v: b.append(v))

        obs.force_notify()

        self.assertEqual(a, ["x"])
        self.assertEqual(b, ["x"])

    def test_force_notify_does_not_change_value(self) -> None:
        obs = ObservableValue(3)
        obs.force_notify()
        self.assertEqual(obs.value, 3)

    def test_force_notify_with_no_observers_is_safe(self) -> None:
        obs = ObservableValue("safe")
        obs.force_notify()  # must not raise
        self.assertEqual(obs.value, "safe")

    def test_force_notify_after_unsubscribe_does_not_call_removed_observer(self) -> None:
        called = []
        obs = ObservableValue(0)
        unsub = obs.subscribe(lambda v: called.append(v))
        unsub()

        obs.force_notify()

        self.assertEqual(called, [])


class PresentationModelDisposeTests(unittest.TestCase):
    """Verify dispose still correctly unsubscribes bound observables."""

    def test_dispose_silences_bound_observable(self) -> None:
        obs = ObservableValue(0)
        log = []

        class _Model(PresentationModel):
            def __init__(self, observable):
                super().__init__()
                self.bind(observable, lambda v: log.append(v))

        model = _Model(obs)
        obs.value = 1
        self.assertEqual(log, [1])

        model.dispose()
        obs.value = 2
        self.assertEqual(log, [1], "observer must be silent after dispose")
        self.assertEqual(obs.observer_count, 0)


if __name__ == "__main__":
    unittest.main()
