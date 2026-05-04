"""Tests for gui_do.events.interaction_state_machine."""
from __future__ import annotations

import unittest

from gui_do.events.interaction_state_machine import (
    InteractionContext,
    InteractionPhase,
    InteractionStateMachine,
    InteractionTransition,
)


def _ctx(event_kind: str, **kwargs) -> InteractionContext:
    return InteractionContext(event_kind=event_kind, **kwargs)


class TestInteractionPhase(unittest.TestCase):
    def test_all_phases_unique(self):
        phases = list(InteractionPhase)
        self.assertEqual(len(phases), len(set(phases)))

    def test_idle_is_default_phase(self):
        ism = InteractionStateMachine()
        self.assertEqual(ism.phase, InteractionPhase.IDLE)


class TestInteractionContext(unittest.TestCase):
    def test_defaults(self):
        ctx = InteractionContext()
        self.assertEqual(ctx.event_kind, "")
        self.assertEqual(ctx.pos, (0, 0))
        self.assertEqual(ctx.button, 0)
        self.assertEqual(ctx.modifiers, 0)
        self.assertEqual(ctx.delta, (0, 0))

    def test_custom_values(self):
        ctx = InteractionContext(event_kind="click", pos=(5, 10), button=1)
        self.assertEqual(ctx.event_kind, "click")
        self.assertEqual(ctx.pos, (5, 10))
        self.assertEqual(ctx.button, 1)


class TestInteractionStateMachine(unittest.TestCase):
    def _basic_machine(self) -> InteractionStateMachine:
        ism = InteractionStateMachine()
        ism.add_transition(InteractionTransition(
            InteractionPhase.IDLE, "enter", InteractionPhase.HOVER
        ))
        ism.add_transition(InteractionTransition(
            InteractionPhase.HOVER, "leave", InteractionPhase.IDLE
        ))
        return ism

    def test_initial_phase_is_idle(self):
        self.assertEqual(InteractionStateMachine().phase, InteractionPhase.IDLE)

    def test_custom_initial_phase(self):
        ism = InteractionStateMachine(initial_phase=InteractionPhase.HOVER)
        self.assertEqual(ism.phase, InteractionPhase.HOVER)

    def test_transition_fires(self):
        ism = self._basic_machine()
        result = ism.handle_event(_ctx("enter"))
        self.assertTrue(result)
        self.assertEqual(ism.phase, InteractionPhase.HOVER)

    def test_unmatched_event_returns_false(self):
        ism = self._basic_machine()
        result = ism.handle_event(_ctx("unknown"))
        self.assertFalse(result)
        self.assertEqual(ism.phase, InteractionPhase.IDLE)

    def test_wrong_phase_blocks_transition(self):
        ism = self._basic_machine()
        # "leave" only valid from HOVER, not IDLE
        result = ism.handle_event(_ctx("leave"))
        self.assertFalse(result)
        self.assertEqual(ism.phase, InteractionPhase.IDLE)

    def test_guard_can_block(self):
        ism = InteractionStateMachine()
        ism.add_transition(InteractionTransition(
            InteractionPhase.IDLE,
            "enter",
            InteractionPhase.HOVER,
            guard=lambda ctx: ctx.button == 0,
        ))
        result = ism.handle_event(_ctx("enter", button=1))
        self.assertFalse(result)
        self.assertEqual(ism.phase, InteractionPhase.IDLE)

    def test_guard_allows_transition(self):
        ism = InteractionStateMachine()
        ism.add_transition(InteractionTransition(
            InteractionPhase.IDLE,
            "enter",
            InteractionPhase.HOVER,
            guard=lambda ctx: ctx.button == 0,
        ))
        result = ism.handle_event(_ctx("enter", button=0))
        self.assertTrue(result)
        self.assertEqual(ism.phase, InteractionPhase.HOVER)

    def test_action_called_on_transition(self):
        called = []
        ism = InteractionStateMachine()
        ism.add_transition(InteractionTransition(
            InteractionPhase.IDLE,
            "enter",
            InteractionPhase.HOVER,
            action=lambda ctx: called.append(ctx.event_kind),
        ))
        ism.handle_event(_ctx("enter"))
        self.assertEqual(called, ["enter"])

    def test_phase_change_callback(self):
        changes = []
        ism = self._basic_machine()
        ism.on_phase_change(lambda old, new: changes.append((old, new)))
        ism.handle_event(_ctx("enter"))
        self.assertEqual(changes, [(InteractionPhase.IDLE, InteractionPhase.HOVER)])

    def test_unsubscribe_phase_change(self):
        changes = []
        ism = self._basic_machine()
        unsub = ism.on_phase_change(lambda old, new: changes.append((old, new)))
        unsub()
        ism.handle_event(_ctx("enter"))
        self.assertEqual(changes, [])

    def test_reset(self):
        ism = self._basic_machine()
        ism.handle_event(_ctx("enter"))
        ism.reset()
        self.assertEqual(ism.phase, InteractionPhase.IDLE)

    def test_reset_to_custom_phase(self):
        ism = self._basic_machine()
        ism.reset(InteractionPhase.CANCELLED)
        self.assertEqual(ism.phase, InteractionPhase.CANCELLED)

    def test_wildcard_transition(self):
        ism = InteractionStateMachine()
        # Wildcard cancel from any phase
        ism.add_transition(InteractionTransition(
            None, "cancel", InteractionPhase.CANCELLED  # type: ignore[arg-type]
        ))
        ism.handle_event(_ctx("cancel"))
        self.assertEqual(ism.phase, InteractionPhase.CANCELLED)

    def test_standard_pointer_machine(self):
        ism = InteractionStateMachine.with_standard_pointer_transitions()
        self.assertEqual(ism.phase, InteractionPhase.IDLE)

        ism.handle_event(_ctx("pointer_enter"))
        self.assertEqual(ism.phase, InteractionPhase.HOVER)

        ism.handle_event(_ctx("pointer_down"))
        self.assertEqual(ism.phase, InteractionPhase.PRESSED)

        ism.handle_event(_ctx("drag_start"))
        self.assertEqual(ism.phase, InteractionPhase.DRAGGING)

        ism.handle_event(_ctx("pointer_up"))
        self.assertEqual(ism.phase, InteractionPhase.IDLE)

    def test_standard_cancel_from_any_phase(self):
        ism = InteractionStateMachine.with_standard_pointer_transitions()
        ism.handle_event(_ctx("pointer_enter"))
        ism.handle_event(_ctx("cancel"))
        self.assertEqual(ism.phase, InteractionPhase.CANCELLED)


if __name__ == "__main__":
    unittest.main()
