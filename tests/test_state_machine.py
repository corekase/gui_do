"""Tests for StateMachine from state.state_machine."""
import unittest

from gui_do.state.state_machine import StateMachine


# ===========================================================================
# StateMachine — initial state
# ===========================================================================


class TestStateMachineInitial(unittest.TestCase):
    def test_current_state(self):
        sm = StateMachine("idle")
        self.assertEqual("idle", sm.current.value)

    def test_empty_initial_raises(self):
        with self.assertRaises(ValueError):
            StateMachine("")

    def test_initial_in_states(self):
        sm = StateMachine("idle")
        self.assertIn("idle", sm.states)


# ===========================================================================
# StateMachine.add_state
# ===========================================================================


class TestStateMachineAddState(unittest.TestCase):
    def test_add_state(self):
        sm = StateMachine("idle")
        sm.add_state("running")
        self.assertIn("running", sm.states)

    def test_empty_name_raises(self):
        sm = StateMachine("idle")
        with self.assertRaises(ValueError):
            sm.add_state("")

    def test_on_enter_called(self):
        sm = StateMachine("idle")
        entered = []
        sm.add_state("running", on_enter=lambda: entered.append(1))
        sm.add_transition("idle", "running", trigger="start")
        sm.trigger("start")
        self.assertEqual([1], entered)

    def test_on_exit_called(self):
        sm = StateMachine("idle")
        exited = []
        sm.add_state("idle", on_exit=lambda: exited.append(1))
        sm.add_state("running")
        sm.add_transition("idle", "running", trigger="start")
        sm.trigger("start")
        self.assertEqual([1], exited)


# ===========================================================================
# StateMachine.add_transition / trigger
# ===========================================================================


class TestStateMachineTrigger(unittest.TestCase):
    def test_trigger_returns_true_on_success(self):
        sm = StateMachine("idle")
        sm.add_transition("idle", "running", trigger="start")
        self.assertTrue(sm.trigger("start"))

    def test_trigger_updates_state(self):
        sm = StateMachine("idle")
        sm.add_transition("idle", "running", trigger="start")
        sm.trigger("start")
        self.assertEqual("running", sm.current.value)

    def test_trigger_no_match_returns_false(self):
        sm = StateMachine("idle")
        self.assertFalse(sm.trigger("unknown"))

    def test_trigger_with_guard_true(self):
        sm = StateMachine("idle")
        sm.add_transition("idle", "running", trigger="start", guard=lambda: True)
        self.assertTrue(sm.trigger("start"))

    def test_trigger_with_guard_false_returns_false(self):
        sm = StateMachine("idle")
        sm.add_transition("idle", "running", trigger="start", guard=lambda: False)
        result = sm.trigger("start")
        self.assertFalse(result)
        self.assertEqual("idle", sm.current.value)

    def test_trigger_with_action(self):
        sm = StateMachine("idle")
        actions = []
        sm.add_transition("idle", "running", trigger="start", action=lambda: actions.append(1))
        sm.trigger("start")
        self.assertEqual([1], actions)

    def test_trigger_notifies_subscribers(self):
        sm = StateMachine("idle")
        sm.add_transition("idle", "running", trigger="start")
        changes = []
        sm.current.subscribe(lambda s: changes.append(s))
        sm.trigger("start")
        self.assertIn("running", changes)

    def test_empty_trigger_raises(self):
        sm = StateMachine("idle")
        with self.assertRaises(ValueError):
            sm.add_transition("idle", "running", trigger="")


# ===========================================================================
# StateMachine inspection
# ===========================================================================


class TestStateMachineInspection(unittest.TestCase):
    def test_states_includes_all(self):
        sm = StateMachine("idle")
        sm.add_state("running")
        sm.add_state("done")
        states = sm.states
        self.assertIn("idle", states)
        self.assertIn("running", states)
        self.assertIn("done", states)

    def test_can_trigger_from_current_true(self):
        sm = StateMachine("idle")
        sm.add_transition("idle", "running", trigger="start")
        self.assertTrue(sm.can_trigger("start"))

    def test_can_trigger_from_current_false(self):
        sm = StateMachine("idle")
        self.assertFalse(sm.can_trigger("unknown"))

    def test_available_triggers(self):
        sm = StateMachine("idle")
        sm.add_transition("idle", "running", trigger="start")
        sm.add_transition("idle", "paused", trigger="pause")
        triggers = sm.available_triggers()
        self.assertIn("start", triggers)
        self.assertIn("pause", triggers)


if __name__ == "__main__":
    unittest.main()
