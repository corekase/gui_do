"""HierarchicalStateMachine — composite, history, and parallel state machine.

Extends the flat :class:`~gui_do.StateMachine` with:

- **CompositeState** — a state that is itself a sub-machine.  Entering a
  composite state activates its initial sub-state; the composite exits when
  an outer transition fires.
- **HistoryState** — a variant of ``CompositeState`` that remembers the last
  active sub-state and resumes it on re-entry instead of the initial state.
- **ParallelRegion** — runs two or more independent sub-machines
  simultaneously (orthogonal regions), each tracking its own current state.

Usage::

    from gui_do import HierarchicalStateMachine, CompositeState, HistoryState

    # ----- Composite state -----
    inner = HierarchicalStateMachine("idle_a")
    inner.add_transition("idle_a", "busy_a", trigger="work")

    outer = HierarchicalStateMachine("outer_idle")
    outer.add_composite("active", inner, initial="idle_a")
    outer.add_transition("outer_idle", "active", trigger="activate")
    outer.add_transition("active", "outer_idle", trigger="deactivate")

    outer.trigger("activate")
    print(outer.current.value)          # "active"
    print(outer.sub_current("active"))  # "idle_a"

    # ----- History state -----
    hist = HierarchicalStateMachine("page1")
    hist_inner = HierarchicalStateMachine("page1")
    hist_inner.add_state("page2")
    hist_inner.add_transition("page1", "page2", trigger="next")

    outer2 = HierarchicalStateMachine("home")
    outer2.add_history("wizard", hist_inner, initial="page1")
    outer2.add_transition("home", "wizard", trigger="open")

    outer2.trigger("open")
    outer2.sub_trigger("wizard", "next")   # advance inner
    outer2.trigger_to("home")             # exit wizard (history recorded)
    outer2.trigger("open")
    print(outer2.sub_current("wizard"))   # "page2"  ← history resumed
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, FrozenSet, List, Optional, Set, Tuple

from ..data.presentation_model import ObservableValue
from .state_machine import StateMachine, _TransitionRecord


# ---------------------------------------------------------------------------
# HierarchicalStateMachine
# ---------------------------------------------------------------------------


class HierarchicalStateMachine(StateMachine):
    """A :class:`~gui_do.StateMachine` that supports composite and history sub-states.

    All flat :class:`~gui_do.StateMachine` APIs remain unchanged.  Additional
    APIs allow embedding sub-machines inside named composite states.
    """

    def __init__(self, initial_state: str) -> None:
        super().__init__(initial_state)
        # state_name -> sub-machine
        self._composites: Dict[str, StateMachine] = {}
        # state_name -> initial sub-state name (for non-history composites)
        self._composite_initial: Dict[str, str] = {}
        # state_name -> True if this composite uses history semantics
        self._history_flags: Set[str] = set()
        # state_name -> last active sub-state (for history composites)
        self._history_state: Dict[str, str] = {}
        # state_name -> parallel region list
        self._parallel_regions: Dict[str, List[StateMachine]] = {}

    # ------------------------------------------------------------------
    # Composite state registration
    # ------------------------------------------------------------------

    def add_composite(
        self,
        state_name: str,
        sub_machine: StateMachine,
        *,
        initial: str,
    ) -> None:
        """Register *state_name* as a composite state backed by *sub_machine*.

        When *state_name* is entered the sub-machine resets to *initial*.
        When it is exited the sub-machine state is discarded.
        """
        state_name = str(state_name).strip()
        initial = str(initial).strip()
        self._states.add(state_name)
        self._composites[state_name] = sub_machine
        self._composite_initial[state_name] = initial

        # Wire entry/exit hooks
        def _on_enter():
            sub_machine.current.value = initial

        def _on_exit():
            pass  # sub-machine state discarded on exit (non-history)

        self._on_enter.setdefault(state_name, []).insert(0, _on_enter)

    def add_history(
        self,
        state_name: str,
        sub_machine: StateMachine,
        *,
        initial: str,
    ) -> None:
        """Like :meth:`add_composite` but the last sub-state is remembered on exit
        and restored on the next entry.
        """
        state_name = str(state_name).strip()
        initial = str(initial).strip()
        self._states.add(state_name)
        self._composites[state_name] = sub_machine
        self._composite_initial[state_name] = initial
        self._history_flags.add(state_name)

        def _on_enter():
            resume = self._history_state.get(state_name, initial)
            sub_machine.current.value = resume

        def _on_exit():
            # Record current sub-state for next entry
            self._history_state[state_name] = sub_machine.current.value

        self._on_enter.setdefault(state_name, []).insert(0, _on_enter)
        self._on_exit.setdefault(state_name, []).insert(0, _on_exit)

    def add_parallel(
        self,
        state_name: str,
        regions: List[StateMachine],
    ) -> None:
        """Register *state_name* as a parallel state with independent *regions*.

        All regions are entered simultaneously and remain active until the
        outer state exits.
        """
        state_name = str(state_name).strip()
        self._states.add(state_name)
        self._parallel_regions[state_name] = list(regions)

        def _on_enter():
            pass  # regions start in their own initial states

        def _on_exit():
            pass

        self._on_enter.setdefault(state_name, []).insert(0, _on_enter)

    # ------------------------------------------------------------------
    # Sub-machine queries
    # ------------------------------------------------------------------

    def sub_machine(self, state_name: str) -> Optional[StateMachine]:
        """Return the sub-machine for a composite/history state, or ``None``."""
        return self._composites.get(str(state_name))

    def sub_current(self, state_name: str) -> Optional[str]:
        """Return the current sub-state of a composite/history state, or ``None``."""
        sub = self._composites.get(str(state_name))
        return sub.current.value if sub is not None else None

    def sub_trigger(self, state_name: str, event: str) -> bool:
        """Fire *event* in the sub-machine of *state_name*.

        Returns ``True`` if the sub-machine fired a transition (the outer
        machine's current state must be *state_name* for this to be meaningful).
        """
        sub = self._composites.get(str(state_name))
        if sub is None:
            return False
        return sub.trigger(event)

    def parallel_regions(self, state_name: str) -> List[StateMachine]:
        """Return the parallel regions for *state_name*, or an empty list."""
        return list(self._parallel_regions.get(str(state_name), []))

    def trigger_parallel(self, state_name: str, event: str) -> List[bool]:
        """Fire *event* in all parallel regions of *state_name*.

        Returns a list of bools, one per region, indicating whether each
        fired a transition.
        """
        return [r.trigger(event) for r in self._parallel_regions.get(str(state_name), [])]

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------

    def trigger_to(self, target_state: str) -> bool:
        """Directly set the current state to *target_state* (bypasses guards).

        Fires on_exit for the current state and on_enter for *target_state*.
        Useful for programmatic scene resets.  Does *not* require a declared
        transition.
        """
        target_state = str(target_state).strip()
        if target_state not in self._states:
            raise ValueError(f"Unknown state: {target_state!r}")
        current = self.current.value
        if current == target_state:
            return False
        for cb in self._on_exit.get(current, []):
            try:
                cb()
            except Exception:
                pass
        for cb in self._on_enter.get(target_state, []):
            try:
                cb()
            except Exception:
                pass
        self.current.value = target_state
        return True
