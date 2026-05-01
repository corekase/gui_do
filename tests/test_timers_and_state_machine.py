import unittest

from gui_do.scheduling.timers import Timers
from gui_do.state.state_machine import StateMachine


# ---------------------------------------------------------------------------
# Timers
# ---------------------------------------------------------------------------


class TestTimers(unittest.TestCase):
    def test_add_timer_registers_and_fires_on_interval(self):
        t = Timers()
        calls = []
        t.add_timer("repeat", 0.1, lambda: calls.append(True))

        t.update(0.1)

        self.assertEqual(1, len(calls))

    def test_repeating_timer_fires_multiple_times(self):
        t = Timers()
        calls = []
        t.add_timer("repeat", 0.1, lambda: calls.append(True))

        t.update(0.35)

        self.assertEqual(3, len(calls))

    def test_add_once_fires_exactly_once_then_removes(self):
        t = Timers()
        calls = []
        t.add_once("once", 0.1, lambda: calls.append(True))

        t.update(0.15)
        t.update(0.15)

        self.assertEqual(1, len(calls))
        self.assertFalse(t.has_timer("once"))

    def test_has_timer_reflects_registration(self):
        t = Timers()
        self.assertFalse(t.has_timer("x"))
        t.add_timer("x", 1.0, lambda: None)
        self.assertTrue(t.has_timer("x"))

    def test_remove_timer_deregisters_timer(self):
        t = Timers()
        calls = []
        t.add_timer("r", 0.1, lambda: calls.append(True))
        t.remove_timer("r")
        t.update(0.5)

        self.assertEqual([], calls)
        self.assertFalse(t.has_timer("r"))

    def test_remove_timer_on_unknown_id_is_noop(self):
        t = Timers()
        t.remove_timer("no_such")  # should not raise

    def test_cancel_all_removes_all_timers(self):
        t = Timers()
        t.add_timer("a", 0.1, lambda: None)
        t.add_timer("b", 0.2, lambda: None)

        count = t.cancel_all()

        self.assertEqual(2, count)
        self.assertEqual([], t.timer_ids())

    def test_timer_ids_returns_all_registered_ids(self):
        t = Timers()
        t.add_timer("x", 1.0, lambda: None)
        t.add_once("y", 0.5, lambda: None)

        ids = t.timer_ids()
        self.assertIn("x", ids)
        self.assertIn("y", ids)

    def test_reschedule_changes_interval(self):
        t = Timers()
        calls = []
        t.add_timer("r", 1.0, lambda: calls.append(True))

        t.reschedule("r", 0.1)
        t.update(0.1)

        self.assertEqual(1, len(calls))

    def test_reschedule_unknown_id_returns_false(self):
        t = Timers()
        result = t.reschedule("missing", 1.0)
        self.assertFalse(result)

    def test_reschedule_known_id_returns_true(self):
        t = Timers()
        t.add_timer("r", 1.0, lambda: None)
        self.assertTrue(t.reschedule("r", 0.5))

    def test_add_timer_invalid_interval_raises(self):
        t = Timers()
        with self.assertRaises(ValueError):
            t.add_timer("bad", 0, lambda: None)

    def test_add_once_invalid_delay_raises(self):
        t = Timers()
        with self.assertRaises(ValueError):
            t.add_once("bad", -1, lambda: None)

    def test_update_with_zero_dt_does_not_fire(self):
        t = Timers()
        calls = []
        t.add_timer("r", 0.1, lambda: calls.append(True))
        t.update(0.0)
        self.assertEqual([], calls)

    def test_timer_not_yet_elapsed_does_not_fire(self):
        t = Timers()
        calls = []
        t.add_timer("r", 1.0, lambda: calls.append(True))
        t.update(0.5)
        self.assertEqual([], calls)


# ---------------------------------------------------------------------------
# StateMachine
# ---------------------------------------------------------------------------


class TestStateMachine(unittest.TestCase):
    def _make(self):
        sm = StateMachine("idle")
        sm.add_state("running")
        sm.add_state("done")
        sm.add_transition("idle", "running", trigger="start")
        sm.add_transition("running", "done", trigger="finish")
        return sm

    def test_initial_state_set_correctly(self):
        sm = StateMachine("idle")
        self.assertEqual("idle", sm.current.value)

    def test_trigger_valid_transition_returns_true(self):
        sm = self._make()
        result = sm.trigger("start")
        self.assertTrue(result)
        self.assertEqual("running", sm.current.value)

    def test_trigger_invalid_transition_returns_false(self):
        sm = self._make()
        result = sm.trigger("finish")
        self.assertFalse(result)
        self.assertEqual("idle", sm.current.value)

    def test_trigger_fires_observable_value_change(self):
        sm = self._make()
        states = []
        sm.current.subscribe(states.append)

        sm.trigger("start")

        self.assertIn("running", states)

    def test_on_enter_callback_fires_on_transition(self):
        sm = StateMachine("idle")
        entered = []
        sm.add_state("active", on_enter=lambda: entered.append("active"))
        sm.add_transition("idle", "active", trigger="go")

        sm.trigger("go")

        self.assertEqual(["active"], entered)

    def test_on_exit_callback_fires_on_transition(self):
        sm = StateMachine("idle")
        exited = []
        sm.add_state("idle", on_exit=lambda: exited.append("idle"))
        sm.add_state("active")
        sm.add_transition("idle", "active", trigger="go")

        sm.trigger("go")

        self.assertEqual(["idle"], exited)

    def test_guard_false_prevents_transition(self):
        sm = StateMachine("idle")
        sm.add_state("active")
        sm.add_transition("idle", "active", trigger="go", guard=lambda: False)

        result = sm.trigger("go")

        self.assertFalse(result)
        self.assertEqual("idle", sm.current.value)

    def test_guard_true_allows_transition(self):
        sm = StateMachine("idle")
        sm.add_state("active")
        sm.add_transition("idle", "active", trigger="go", guard=lambda: True)

        result = sm.trigger("go")

        self.assertTrue(result)
        self.assertEqual("active", sm.current.value)

    def test_action_called_during_transition(self):
        sm = StateMachine("idle")
        actions = []
        sm.add_state("active")
        sm.add_transition("idle", "active", trigger="go", action=lambda: actions.append("action"))

        sm.trigger("go")

        self.assertEqual(["action"], actions)

    def test_can_trigger_reflects_current_state(self):
        sm = self._make()
        self.assertTrue(sm.can_trigger("start"))
        self.assertFalse(sm.can_trigger("finish"))

    def test_can_trigger_false_when_guard_blocks(self):
        sm = StateMachine("idle")
        sm.add_state("active")
        sm.add_transition("idle", "active", trigger="go", guard=lambda: False)
        self.assertFalse(sm.can_trigger("go"))

    def test_available_triggers_lists_valid_triggers(self):
        sm = self._make()
        triggers = sm.available_triggers()
        self.assertIn("start", triggers)
        self.assertNotIn("finish", triggers)

    def test_states_property_includes_all_declared_states(self):
        sm = self._make()
        self.assertIn("idle", sm.states)
        self.assertIn("running", sm.states)
        self.assertIn("done", sm.states)

    def test_transition_count_reflects_declarations(self):
        sm = self._make()
        self.assertEqual(2, sm.transition_count())

    def test_empty_initial_state_raises(self):
        with self.assertRaises(ValueError):
            StateMachine("")

    def test_add_on_enter_adds_additional_entry_callback(self):
        sm = StateMachine("idle")
        calls = []
        sm.add_state("active")
        sm.add_on_enter("active", lambda: calls.append(1))
        sm.add_on_enter("active", lambda: calls.append(2))
        sm.add_transition("idle", "active", trigger="go")

        sm.trigger("go")

        self.assertEqual([1, 2], calls)

    def test_sequential_transitions_change_state_correctly(self):
        sm = self._make()
        sm.trigger("start")
        sm.trigger("finish")
        self.assertEqual("done", sm.current.value)


if __name__ == "__main__":
    unittest.main()
