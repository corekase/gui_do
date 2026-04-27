"""StateMachine — formal finite state machine with observable state."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, FrozenSet, List, Optional, Tuple

from .presentation_model import ObservableValue


@dataclass
class _TransitionRecord:
    from_state: str
    to_state: str
    trigger: str
    guard: Optional[Callable[[], bool]]
    action: Optional[Callable[[], None]]


class StateMachine:
    """Formal finite state machine with observable current state.

    Usage::

        sm = StateMachine("idle")
        sm.add_state("running", on_enter=lambda: print("running"))
        sm.add_state("done")
        sm.add_transition("idle", "running", trigger="start",
                          guard=lambda: True, action=lambda: None)
        sm.add_transition("running", "done", trigger="finish")

        sm.current.subscribe(lambda s: print("now:", s))
        sm.trigger("start")   # True; fires subscribers with "running"
        sm.trigger("start")   # False; no valid transition from "running"
    """

    def __init__(self, initial_state: str) -> None:
        initial = str(initial_state).strip()
        if not initial:
            raise ValueError("initial_state must be a non-empty string")
        self._states: set[str] = {initial}
        # Keyed by (from_state, trigger)
        self._transitions: Dict[Tuple[str, str], _TransitionRecord] = {}
        self._on_enter: Dict[str, List[Callable[[], None]]] = {}
        self._on_exit: Dict[str, List[Callable[[], None]]] = {}
        self.current: ObservableValue[str] = ObservableValue(initial)

    # ------------------------------------------------------------------
    # Declaration API
    # ------------------------------------------------------------------

    def add_state(
        self,
        name: str,
        *,
        on_enter: Optional[Callable[[], None]] = None,
        on_exit: Optional[Callable[[], None]] = None,
    ) -> None:
        """Declare a state, optionally with entry and exit callbacks."""
        name = str(name).strip()
        if not name:
            raise ValueError("state name must be a non-empty string")
        self._states.add(name)
        if on_enter is not None:
            self._on_enter.setdefault(name, []).append(on_enter)
        if on_exit is not None:
            self._on_exit.setdefault(name, []).append(on_exit)

    def add_transition(
        self,
        from_state: str,
        to_state: str,
        *,
        trigger: str,
        guard: Optional[Callable[[], bool]] = None,
        action: Optional[Callable[[], None]] = None,
    ) -> None:
        """Declare a transition.

        Both states are implicitly added if not yet declared.
        Only one transition per (from_state, trigger) pair is supported;
        later calls overwrite earlier ones.
        """
        from_state = str(from_state).strip()
        to_state = str(to_state).strip()
        trigger = str(trigger).strip()
        if not from_state or not to_state or not trigger:
            raise ValueError("from_state, to_state, and trigger must be non-empty strings")
        self._states.add(from_state)
        self._states.add(to_state)
        self._transitions[(from_state, trigger)] = _TransitionRecord(
            from_state=from_state,
            to_state=to_state,
            trigger=trigger,
            guard=guard,
            action=action,
        )

    def add_on_enter(self, state: str, callback: Callable[[], None]) -> None:
        """Add an additional entry callback for an existing state."""
        self._on_enter.setdefault(str(state), []).append(callback)

    def add_on_exit(self, state: str, callback: Callable[[], None]) -> None:
        """Add an additional exit callback for an existing state."""
        self._on_exit.setdefault(str(state), []).append(callback)

    # ------------------------------------------------------------------
    # Runtime API
    # ------------------------------------------------------------------

    def trigger(self, event: str) -> bool:
        """Fire a named trigger from the current state.

        Returns True if a transition was fired, False otherwise.
        """
        current = self.current.value
        record = self._transitions.get((current, str(event)))
        if record is None:
            return False
        if record.guard is not None and not record.guard():
            return False
        # Exit current state
        for cb in self._on_exit.get(current, []):
            try:
                cb()
            except Exception:
                pass
        # Run transition action
        if record.action is not None:
            try:
                record.action()
            except Exception:
                pass
        # Enter new state
        new_state = record.to_state
        for cb in self._on_enter.get(new_state, []):
            try:
                cb()
            except Exception:
                pass
        self.current.value = new_state
        return True

    def can_trigger(self, event: str) -> bool:
        """Return True if firing this event would cause a transition."""
        current = self.current.value
        record = self._transitions.get((current, str(event)))
        if record is None:
            return False
        if record.guard is not None and not record.guard():
            return False
        return True

    def available_triggers(self) -> List[str]:
        """Return all trigger names that would fire from the current state."""
        current = self.current.value
        return [
            trigger
            for (from_state, trigger) in self._transitions
            if from_state == current and self.can_trigger(trigger)
        ]

    def triggers_from(self, state: str) -> List[str]:
        """Return all declared triggers from a given state (regardless of guards)."""
        state = str(state)
        return [trigger for (from_state, trigger) in self._transitions if from_state == state]

    # ------------------------------------------------------------------
    # Inspection
    # ------------------------------------------------------------------

    @property
    def states(self) -> FrozenSet[str]:
        """Return the set of all declared state names."""
        return frozenset(self._states)

    def transition_count(self) -> int:
        """Return the number of declared transitions."""
        return len(self._transitions)
