"""Tests for Timers (frame-driven timer service), cooperative scheduler yield tokens, and TransitionSpec."""
import unittest

from gui_do.scheduling.timers import Timers
from gui_do.scheduling.cooperative_scheduler import Pause, Sleep, WaitUntil
from gui_do.scheduling.transition_manager import TransitionEvent, TransitionSpec


# ===========================================================================
# Timers — initial state
# ===========================================================================


class TestTimersInitial(unittest.TestCase):
    def test_no_timers_initially(self):
        t = Timers()
        self.assertEqual([], t.timer_ids())

    def test_has_timer_false(self):
        t = Timers()
        self.assertFalse(t.has_timer("x"))


# ===========================================================================
# Timers — add_timer (repeating)
# ===========================================================================


class TestTimersAddTimer(unittest.TestCase):
    def test_add_timer_registers(self):
        t = Timers()
        t.add_timer("a", 1.0, lambda: None)
        self.assertTrue(t.has_timer("a"))

    def test_add_timer_invalid_interval_raises(self):
        t = Timers()
        with self.assertRaises(ValueError):
            t.add_timer("a", 0.0, lambda: None)

    def test_add_timer_non_callable_raises(self):
        t = Timers()
        with self.assertRaises(ValueError):
            t.add_timer("a", 1.0, "not_callable")

    def test_timer_fires_after_interval(self):
        t = Timers()
        calls = []
        t.add_timer("tick", 0.5, lambda: calls.append(1))
        t.update(0.5)
        self.assertEqual(1, len(calls))

    def test_timer_fires_multiple_times(self):
        t = Timers()
        calls = []
        t.add_timer("tick", 0.1, lambda: calls.append(1))
        t.update(0.35)  # fires 3 times
        self.assertEqual(3, len(calls))

    def test_timer_does_not_fire_before_interval(self):
        t = Timers()
        calls = []
        t.add_timer("tick", 1.0, lambda: calls.append(1))
        t.update(0.5)
        self.assertEqual(0, len(calls))

    def test_remove_timer(self):
        t = Timers()
        t.add_timer("x", 1.0, lambda: None)
        t.remove_timer("x")
        self.assertFalse(t.has_timer("x"))

    def test_cancel_all_returns_count(self):
        t = Timers()
        t.add_timer("a", 1.0, lambda: None)
        t.add_timer("b", 2.0, lambda: None)
        count = t.cancel_all()
        self.assertEqual(2, count)
        self.assertEqual([], t.timer_ids())


# ===========================================================================
# Timers — add_once (one-shot)
# ===========================================================================


class TestTimersAddOnce(unittest.TestCase):
    def test_add_once_fires_once(self):
        t = Timers()
        calls = []
        t.add_once("once", 0.5, lambda: calls.append(1))
        t.update(0.5)
        t.update(0.5)  # should not fire again
        self.assertEqual(1, len(calls))

    def test_add_once_removed_after_fire(self):
        t = Timers()
        t.add_once("once", 0.5, lambda: None)
        t.update(1.0)
        self.assertFalse(t.has_timer("once"))

    def test_add_once_invalid_delay_raises(self):
        t = Timers()
        with self.assertRaises(ValueError):
            t.add_once("x", -1.0, lambda: None)


# ===========================================================================
# Timers — reschedule
# ===========================================================================


class TestTimersReschedule(unittest.TestCase):
    def test_reschedule_updates_interval(self):
        t = Timers()
        calls = []
        t.add_timer("a", 1.0, lambda: calls.append(1))
        t.reschedule("a", 0.1)
        t.update(0.1)
        self.assertEqual(1, len(calls))

    def test_reschedule_missing_returns_false(self):
        t = Timers()
        self.assertFalse(t.reschedule("nope", 1.0))

    def test_reschedule_invalid_interval_raises(self):
        t = Timers()
        t.add_timer("a", 1.0, lambda: None)
        with self.assertRaises(ValueError):
            t.reschedule("a", 0.0)


# ===========================================================================
# CooperativeScheduler yield tokens
# ===========================================================================


class TestPause(unittest.TestCase):
    def test_instantiates(self):
        p = Pause()
        self.assertIsInstance(p, Pause)


class TestSleep(unittest.TestCase):
    def test_seconds_stored(self):
        s = Sleep(1.5)
        self.assertEqual(1.5, s.seconds)

    def test_negative_seconds_raises(self):
        with self.assertRaises(ValueError):
            Sleep(-0.1)

    def test_zero_seconds_ok(self):
        s = Sleep(0.0)
        self.assertEqual(0.0, s.seconds)


class TestWaitUntil(unittest.TestCase):
    def test_predicate_stored(self):
        pred = lambda: True
        w = WaitUntil(pred)
        self.assertIs(pred, w.predicate)


# ===========================================================================
# TransitionEvent
# ===========================================================================


class TestTransitionEvent(unittest.TestCase):
    def test_members_exist(self):
        self.assertTrue(hasattr(TransitionEvent, "SHOW"))
        self.assertTrue(hasattr(TransitionEvent, "HIDE"))
        self.assertTrue(hasattr(TransitionEvent, "ENABLE"))
        self.assertTrue(hasattr(TransitionEvent, "DISABLE"))

    def test_unique_values(self):
        values = [e.value for e in TransitionEvent]
        self.assertEqual(len(values), len(set(values)))


# ===========================================================================
# TransitionSpec
# ===========================================================================


class TestTransitionSpec(unittest.TestCase):
    def test_required_fields(self):
        spec = TransitionSpec(attr="alpha", end_value=1.0, duration_seconds=0.3)
        self.assertEqual("alpha", spec.attr)
        self.assertEqual(1.0, spec.end_value)
        self.assertEqual(0.3, spec.duration_seconds)

    def test_start_value_default_none(self):
        spec = TransitionSpec(attr="alpha", end_value=1.0, duration_seconds=0.3)
        self.assertIsNone(spec.start_value)

    def test_custom_start_value(self):
        spec = TransitionSpec(attr="alpha", start_value=0.0, end_value=1.0, duration_seconds=0.2)
        self.assertEqual(0.0, spec.start_value)


if __name__ == "__main__":
    unittest.main()
