"""Tests for Timers management APIs: timer_ids, cancel_all, reschedule."""
import unittest

from gui.core.timers import Timers


class TimerIdsTests(unittest.TestCase):

    def test_timer_ids_empty_on_fresh_instance(self) -> None:
        t = Timers()
        self.assertEqual(t.timer_ids(), [])

    def test_timer_ids_includes_repeating_timer(self) -> None:
        t = Timers()
        t.add_timer("r1", 0.5, lambda: None)
        self.assertIn("r1", t.timer_ids())

    def test_timer_ids_includes_one_shot_timer(self) -> None:
        t = Timers()
        t.add_once("once1", 1.0, lambda: None)
        self.assertIn("once1", t.timer_ids())

    def test_timer_ids_includes_both_types(self) -> None:
        t = Timers()
        t.add_timer("r", 0.1, lambda: None)
        t.add_once("o", 0.2, lambda: None)
        ids = t.timer_ids()
        self.assertIn("r", ids)
        self.assertIn("o", ids)
        self.assertEqual(len(ids), 2)

    def test_timer_ids_excludes_removed_timer(self) -> None:
        t = Timers()
        t.add_timer("r", 0.1, lambda: None)
        t.remove_timer("r")
        self.assertNotIn("r", t.timer_ids())

    def test_timer_ids_excludes_fired_one_shot(self) -> None:
        fired = []
        t = Timers()
        t.add_once("shot", 0.1, lambda: fired.append(1))
        t.update(0.2)
        self.assertNotIn("shot", t.timer_ids())


class CancelAllTests(unittest.TestCase):

    def test_cancel_all_returns_zero_when_empty(self) -> None:
        t = Timers()
        self.assertEqual(t.cancel_all(), 0)

    def test_cancel_all_returns_count_removed(self) -> None:
        t = Timers()
        t.add_timer("a", 0.1, lambda: None)
        t.add_timer("b", 0.2, lambda: None)
        t.add_once("c", 0.3, lambda: None)
        self.assertEqual(t.cancel_all(), 3)

    def test_cancel_all_clears_all_timers(self) -> None:
        t = Timers()
        t.add_timer("x", 0.1, lambda: None)
        t.add_once("y", 0.2, lambda: None)
        t.cancel_all()
        self.assertEqual(t.timer_ids(), [])

    def test_cancel_all_prevents_callbacks(self) -> None:
        fired = []
        t = Timers()
        t.add_timer("r", 0.1, lambda: fired.append("r"))
        t.add_once("o", 0.1, lambda: fired.append("o"))
        t.cancel_all()
        t.update(1.0)
        self.assertEqual(fired, [])

    def test_cancel_all_idempotent(self) -> None:
        t = Timers()
        t.add_timer("a", 0.1, lambda: None)
        t.cancel_all()
        count = t.cancel_all()
        self.assertEqual(count, 0)


class RescheduleTests(unittest.TestCase):

    def test_reschedule_returns_false_when_not_found(self) -> None:
        t = Timers()
        self.assertFalse(t.reschedule("missing", 1.0))

    def test_reschedule_returns_true_when_found(self) -> None:
        t = Timers()
        t.add_timer("r", 0.5, lambda: None)
        self.assertTrue(t.reschedule("r", 1.0))

    def test_reschedule_raises_for_non_positive_interval(self) -> None:
        t = Timers()
        t.add_timer("r", 0.5, lambda: None)
        with self.assertRaises(ValueError):
            t.reschedule("r", 0.0)
        with self.assertRaises(ValueError):
            t.reschedule("r", -1.0)

    def test_reschedule_changes_fire_rate_of_repeating_timer(self) -> None:
        fired = []
        t = Timers()
        t.add_timer("r", 0.5, lambda: fired.append(1))
        # With original 0.5s interval, 0.4s should not fire
        t.update(0.4)
        self.assertEqual(len(fired), 0)
        # Reschedule to shorter interval; 0.1s more should now cross the new threshold
        t.reschedule("r", 0.1)
        t.update(0.1)
        # elapsed was 0.4 from before; timer re-uses accumulated 0.4 against new interval 0.1
        self.assertGreater(len(fired), 0)

    def test_reschedule_works_on_one_shot_timer(self) -> None:
        fired = []
        t = Timers()
        t.add_once("o", 1.0, lambda: fired.append(1))
        t.reschedule("o", 0.1)
        t.update(0.2)
        self.assertEqual(len(fired), 1)

    def test_reschedule_preserves_timer_existence(self) -> None:
        t = Timers()
        t.add_timer("r", 0.5, lambda: None)
        t.reschedule("r", 2.0)
        self.assertTrue(t.has_timer("r"))

    def test_reschedule_lengthening_delays_callback(self) -> None:
        fired = []
        t = Timers()
        t.add_timer("r", 0.1, lambda: fired.append(1))
        t.update(0.05)  # halfway to first fire
        t.reschedule("r", 10.0)  # much longer — should not fire within a short tick
        t.update(0.5)
        self.assertEqual(len(fired), 0)


if __name__ == "__main__":
    unittest.main()
