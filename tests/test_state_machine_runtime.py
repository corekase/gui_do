import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from gui_do import StateMachine


class StateMachineRuntimeTests(unittest.TestCase):

    def setUp(self) -> None:
        pygame.init()

    def tearDown(self) -> None:
        pygame.quit()

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def test_initial_state_is_current(self) -> None:
        sm = StateMachine("idle")
        self.assertEqual(sm.current.value, "idle")

    def test_initial_state_in_states_set(self) -> None:
        sm = StateMachine("idle")
        self.assertIn("idle", sm.states)

    def test_empty_initial_state_raises(self) -> None:
        with self.assertRaises(ValueError):
            StateMachine("")

    def test_whitespace_initial_state_raises(self) -> None:
        with self.assertRaises(ValueError):
            StateMachine("   ")

    # ------------------------------------------------------------------
    # add_state
    # ------------------------------------------------------------------

    def test_add_state_appears_in_states(self) -> None:
        sm = StateMachine("idle")
        sm.add_state("running")
        self.assertIn("running", sm.states)

    def test_add_state_empty_name_raises(self) -> None:
        sm = StateMachine("idle")
        with self.assertRaises(ValueError):
            sm.add_state("")

    def test_add_state_on_enter_callback(self) -> None:
        entered = []
        sm = StateMachine("idle")
        sm.add_state("done", on_enter=lambda: entered.append(True))
        sm.add_transition("idle", "done", trigger="finish")
        sm.trigger("finish")
        self.assertEqual(entered, [True])

    def test_add_state_on_exit_callback(self) -> None:
        exited = []
        sm = StateMachine("idle")
        sm.add_state("idle", on_exit=lambda: exited.append(True))
        sm.add_transition("idle", "done", trigger="go")
        sm.trigger("go")
        self.assertEqual(exited, [True])

    # ------------------------------------------------------------------
    # add_transition
    # ------------------------------------------------------------------

    def test_add_transition_implicitly_adds_states(self) -> None:
        sm = StateMachine("idle")
        sm.add_transition("idle", "running", trigger="start")
        self.assertIn("running", sm.states)

    def test_add_transition_empty_args_raise(self) -> None:
        sm = StateMachine("idle")
        with self.assertRaises(ValueError):
            sm.add_transition("", "running", trigger="start")
        with self.assertRaises(ValueError):
            sm.add_transition("idle", "", trigger="start")
        with self.assertRaises(ValueError):
            sm.add_transition("idle", "running", trigger="")

    def test_transition_count(self) -> None:
        sm = StateMachine("idle")
        sm.add_transition("idle", "running", trigger="start")
        sm.add_transition("running", "idle", trigger="stop")
        self.assertEqual(sm.transition_count(), 2)

    # ------------------------------------------------------------------
    # trigger
    # ------------------------------------------------------------------

    def test_trigger_fires_transition(self) -> None:
        sm = StateMachine("idle")
        sm.add_transition("idle", "running", trigger="start")
        result = sm.trigger("start")
        self.assertTrue(result)
        self.assertEqual(sm.current.value, "running")

    def test_trigger_unknown_returns_false(self) -> None:
        sm = StateMachine("idle")
        result = sm.trigger("nope")
        self.assertFalse(result)
        self.assertEqual(sm.current.value, "idle")

    def test_trigger_wrong_state_returns_false(self) -> None:
        sm = StateMachine("idle")
        sm.add_transition("running", "idle", trigger="stop")
        result = sm.trigger("stop")
        self.assertFalse(result)
        self.assertEqual(sm.current.value, "idle")

    def test_trigger_with_guard_blocking(self) -> None:
        sm = StateMachine("idle")
        sm.add_transition("idle", "running", trigger="start", guard=lambda: False)
        result = sm.trigger("start")
        self.assertFalse(result)
        self.assertEqual(sm.current.value, "idle")

    def test_trigger_with_guard_allowing(self) -> None:
        sm = StateMachine("idle")
        sm.add_transition("idle", "running", trigger="start", guard=lambda: True)
        result = sm.trigger("start")
        self.assertTrue(result)
        self.assertEqual(sm.current.value, "running")

    def test_trigger_runs_action(self) -> None:
        actions = []
        sm = StateMachine("idle")
        sm.add_transition("idle", "done", trigger="go", action=lambda: actions.append("ran"))
        sm.trigger("go")
        self.assertEqual(actions, ["ran"])

    def test_trigger_fires_observable_subscribers(self) -> None:
        states = []
        sm = StateMachine("idle")
        sm.current.subscribe(lambda v: states.append(v))
        sm.add_transition("idle", "running", trigger="start")
        sm.trigger("start")
        self.assertIn("running", states)

    # ------------------------------------------------------------------
    # can_trigger
    # ------------------------------------------------------------------

    def test_can_trigger_true_when_valid(self) -> None:
        sm = StateMachine("idle")
        sm.add_transition("idle", "running", trigger="start")
        self.assertTrue(sm.can_trigger("start"))

    def test_can_trigger_false_when_no_transition(self) -> None:
        sm = StateMachine("idle")
        self.assertFalse(sm.can_trigger("start"))

    def test_can_trigger_false_when_guard_fails(self) -> None:
        sm = StateMachine("idle")
        sm.add_transition("idle", "running", trigger="start", guard=lambda: False)
        self.assertFalse(sm.can_trigger("start"))

    # ------------------------------------------------------------------
    # available_triggers / triggers_from
    # ------------------------------------------------------------------

    def test_available_triggers_lists_allowed(self) -> None:
        sm = StateMachine("idle")
        sm.add_transition("idle", "running", trigger="start")
        sm.add_transition("idle", "error", trigger="fail")
        triggers = sm.available_triggers()
        self.assertIn("start", triggers)
        self.assertIn("fail", triggers)

    def test_triggers_from_includes_blocked_by_guard(self) -> None:
        sm = StateMachine("idle")
        sm.add_transition("idle", "running", trigger="start", guard=lambda: False)
        self.assertIn("start", sm.triggers_from("idle"))
        self.assertNotIn("start", sm.available_triggers())

    # ------------------------------------------------------------------
    # add_on_enter / add_on_exit
    # ------------------------------------------------------------------

    def test_add_on_enter_adds_extra_callback(self) -> None:
        entered = []
        sm = StateMachine("idle")
        sm.add_transition("idle", "done", trigger="go")
        sm.add_on_enter("done", lambda: entered.append(1))
        sm.add_on_enter("done", lambda: entered.append(2))
        sm.trigger("go")
        self.assertEqual(entered, [1, 2])

    def test_add_on_exit_adds_extra_callback(self) -> None:
        exited = []
        sm = StateMachine("idle")
        sm.add_transition("idle", "done", trigger="go")
        sm.add_on_exit("idle", lambda: exited.append("x"))
        sm.trigger("go")
        self.assertEqual(exited, ["x"])

    # ------------------------------------------------------------------
    # Full cycle
    # ------------------------------------------------------------------

    def test_full_state_machine_cycle(self) -> None:
        log = []
        sm = StateMachine("idle")
        sm.add_state("running", on_enter=lambda: log.append("enter:running"), on_exit=lambda: log.append("exit:running"))
        sm.add_state("idle", on_exit=lambda: log.append("exit:idle"))
        sm.add_transition("idle", "running", trigger="start")
        sm.add_transition("running", "idle", trigger="stop")
        sm.trigger("start")
        sm.trigger("stop")
        self.assertIn("exit:idle", log)
        self.assertIn("enter:running", log)
        self.assertIn("exit:running", log)
        self.assertEqual(sm.current.value, "idle")


if __name__ == "__main__":
    unittest.main()
