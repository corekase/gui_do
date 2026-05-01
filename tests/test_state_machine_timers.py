"""Tests for StateMachine and Timers."""
import unittest

from gui_do.state.state_machine import StateMachine
from gui_do.scheduling.timers import Timers


# ===========================================================================
# StateMachine — initial state
# ===========================================================================


class TestStateMachineInitial(unittest.TestCase):
    def test_initial_state_set(self):
        sm = StateMachine("idle")
        self.assertEqual("idle", sm.current.value)

    def test_empty_initial_state_raises(self):
        with self.assertRaises(ValueError):
            StateMachine("")

    def test_whitespace_initial_state_raises(self):
        with self.assertRaises(ValueError):
            StateMachine("   ")

    def test_states_contains_initial(self):
        sm = StateMachine("idle")
        self.assertIn("idle", sm._states)


class TestStateMachineAddState(unittest.TestCase):
    def test_add_state_registers(self):
        sm = StateMachine("idle")
        sm.add_state("running")
        self.assertIn("running", sm._states)

    def test_empty_state_name_raises(self):
        sm = StateMachine("idle")
        with self.assertRaises(ValueError):
            sm.add_state("")


class TestStateMachineAddTransition(unittest.TestCase):
    def test_add_transition(self):
        sm = StateMachine("idle")
        sm.add_transition("idle", "running", trigger="start")
        self.assertIn(("idle", "start"), sm._transitions)

    def test_both_states_auto_added(self):
        sm = StateMachine("idle")
        sm.add_transition("idle", "running", trigger="start")
        self.assertIn("running", sm._states)

    def test_empty_trigger_raises(self):
        sm = StateMachine("idle")
        with self.assertRaises(ValueError):
            sm.add_transition("idle", "running", trigger="")


class TestStateMachineTrigger(unittest.TestCase):
    def _make(self):
        sm = StateMachine("idle")
        sm.add_transition("idle", "running", trigger="start")
        sm.add_transition("running", "done", trigger="finish")
        return sm

    def test_trigger_returns_true_on_match(self):
        sm = self._make()
        self.assertTrue(sm.trigger("start"))

    def test_trigger_changes_state(self):
        sm = self._make()
        sm.trigger("start")
        self.assertEqual("running", sm.current.value)

    def test_trigger_returns_false_no_match(self):
        sm = self._make()
        self.assertFalse(sm.trigger("finish"))  # not valid from "idle"

    def test_trigger_unknown_event(self):
        sm = self._make()
        self.assertFalse(sm.trigger("unknown"))

    def test_trigger_fires_on_enter(self):
        entered = []
        sm = StateMachine("idle")
        sm.add_state("running", on_enter=lambda: entered.append("running"))
        sm.add_transition("idle", "running", trigger="start")
        sm.trigger("start")
        self.assertEqual(["running"], entered)

    def test_trigger_fires_on_exit(self):
        exited = []
        sm = StateMachine("idle")
        sm.add_state("idle", on_exit=lambda: exited.append("idle"))
        sm.add_transition("idle", "running", trigger="start")
        sm.trigger("start")
        self.assertEqual(["idle"], exited)

    def test_trigger_fires_action(self):
        actions = []
        sm = StateMachine("idle")
        sm.add_transition("idle", "running", trigger="start",
                          action=lambda: actions.append("start"))
        sm.trigger("start")
        self.assertEqual(["start"], actions)

    def test_trigger_guard_blocks_when_false(self):
        sm = StateMachine("idle")
        sm.add_transition("idle", "running", trigger="start", guard=lambda: False)
        result = sm.trigger("start")
        self.assertFalse(result)
        self.assertEqual("idle", sm.current.value)

    def test_trigger_guard_allows_when_true(self):
        sm = StateMachine("idle")
        sm.add_transition("idle", "running", trigger="start", guard=lambda: True)
        sm.trigger("start")
        self.assertEqual("running", sm.current.value)


class TestStateMachineCanTrigger(unittest.TestCase):
    def test_can_trigger_true(self):
        sm = StateMachine("idle")
        sm.add_transition("idle", "running", trigger="start")
        self.assertTrue(sm.can_trigger("start"))

    def test_can_trigger_false_no_transition(self):
        sm = StateMachine("idle")
        self.assertFalse(sm.can_trigger("start"))

    def test_can_trigger_false_guard_blocks(self):
        sm = StateMachine("idle")
        sm.add_transition("idle", "running", trigger="start", guard=lambda: False)
        self.assertFalse(sm.can_trigger("start"))


class TestStateMachineObservable(unittest.TestCase):
    def test_subscriber_notified_on_change(self):
        received = []
        sm = StateMachine("idle")
        sm.add_transition("idle", "running", trigger="start")
        sm.current.subscribe(lambda s: received.append(s))
        sm.trigger("start")
        self.assertIn("running", received)


# ===========================================================================
# Timers
# ===========================================================================


class TestTimersInitial(unittest.TestCase):
    def test_no_timers_initially(self):
        t = Timers()
        self.assertEqual([], t.timer_ids())

    def test_has_timer_false_initially(self):
        t = Timers()
        self.assertFalse(t.has_timer("foo"))


class TestTimersAddTimer(unittest.TestCase):
    def test_add_timer_registers(self):
        t = Timers()
        t.add_timer("t1", 1.0, lambda: None)
        self.assertTrue(t.has_timer("t1"))

    def test_add_timer_zero_interval_raises(self):
        t = Timers()
        with self.assertRaises(ValueError):
            t.add_timer("t1", 0.0, lambda: None)

    def test_add_timer_negative_interval_raises(self):
        t = Timers()
        with self.assertRaises(ValueError):
            t.add_timer("t1", -1.0, lambda: None)

    def test_add_timer_non_callable_raises(self):
        t = Timers()
        with self.assertRaises(ValueError):
            t.add_timer("t1", 1.0, "not callable")


class TestTimersAddOnce(unittest.TestCase):
    def test_add_once_registers(self):
        t = Timers()
        t.add_once("once1", 0.5, lambda: None)
        self.assertTrue(t.has_timer("once1"))

    def test_add_once_fires_and_removes(self):
        fired = []
        t = Timers()
        t.add_once("once1", 0.1, lambda: fired.append(1))
        t.update(0.2)
        self.assertEqual([1], fired)
        self.assertFalse(t.has_timer("once1"))

    def test_add_once_zero_delay_raises(self):
        t = Timers()
        with self.assertRaises(ValueError):
            t.add_once("t1", 0.0, lambda: None)


class TestTimersRemoveTimer(unittest.TestCase):
    def test_remove_timer(self):
        t = Timers()
        t.add_timer("t1", 1.0, lambda: None)
        t.remove_timer("t1")
        self.assertFalse(t.has_timer("t1"))

    def test_remove_missing_timer_no_error(self):
        t = Timers()
        t.remove_timer("nonexistent")  # should not raise


class TestTimersCancelAll(unittest.TestCase):
    def test_cancel_all_clears(self):
        t = Timers()
        t.add_timer("a", 1.0, lambda: None)
        t.add_timer("b", 2.0, lambda: None)
        count = t.cancel_all()
        self.assertEqual(2, count)
        self.assertEqual([], t.timer_ids())


class TestTimersUpdate(unittest.TestCase):
    def test_repeating_timer_fires(self):
        fired = []
        t = Timers()
        t.add_timer("t1", 0.5, lambda: fired.append(1))
        t.update(0.6)
        self.assertEqual(1, len(fired))

    def test_repeating_timer_fires_multiple(self):
        fired = []
        t = Timers()
        t.add_timer("t1", 0.3, lambda: fired.append(1))
        t.update(1.0)
        self.assertGreaterEqual(len(fired), 3)

    def test_repeating_timer_not_fired_yet(self):
        fired = []
        t = Timers()
        t.add_timer("t1", 1.0, lambda: fired.append(1))
        t.update(0.5)
        self.assertEqual([], fired)

    def test_no_update_when_no_timers(self):
        t = Timers()
        t.update(1.0)  # Should not raise


class TestTimersReschedule(unittest.TestCase):
    def test_reschedule_updates_interval(self):
        t = Timers()
        t.add_timer("t1", 1.0, lambda: None)
        result = t.reschedule("t1", 2.0)
        self.assertTrue(result)
        self.assertAlmostEqual(2.0, t._timers["t1"].interval_seconds)

    def test_reschedule_missing_returns_false(self):
        t = Timers()
        result = t.reschedule("missing", 1.0)
        self.assertFalse(result)

    def test_reschedule_zero_raises(self):
        t = Timers()
        with self.assertRaises(ValueError):
            t.reschedule("t1", 0.0)


if __name__ == "__main__":
    unittest.main()
