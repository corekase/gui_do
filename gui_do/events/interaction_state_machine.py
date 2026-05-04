"""InteractionStateMachine — pointer/keyboard/gesture phase tracking.

Models the full lifecycle of a user interaction (hover, press, drag, etc.)
as an explicit state machine with guard-protected transitions and action hooks.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, Dict, List, Optional, Tuple

__all__ = [
    "InteractionPhase",
    "InteractionContext",
    "InteractionTransition",
    "InteractionStateMachine",
]


# ---------------------------------------------------------------------------
# InteractionPhase
# ---------------------------------------------------------------------------


class InteractionPhase(Enum):
    """Phases of a pointer/keyboard interaction lifecycle."""

    IDLE = auto()
    HOVER = auto()
    PRESSED = auto()
    DRAGGING = auto()
    SELECTED = auto()
    CANCELLED = auto()


# ---------------------------------------------------------------------------
# InteractionContext
# ---------------------------------------------------------------------------


@dataclass
class InteractionContext:
    """Snapshot of input state accompanying an interaction event.

    All fields are optional — populate only those relevant to the event kind.
    """

    event_kind: str = ""
    pos: Tuple[int, int] = (0, 0)
    button: int = 0
    modifiers: int = 0
    delta: Tuple[int, int] = (0, 0)
    extra: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# InteractionTransition
# ---------------------------------------------------------------------------

GuardFn = Callable[["InteractionContext"], bool]
ActionFn = Callable[["InteractionContext"], None]


@dataclass
class InteractionTransition:
    """Describes a legal transition in an :class:`InteractionStateMachine`.

    Parameters
    ----------
    from_phase:
        The phase this transition originates from.
    event_kind:
        The string event identifier that triggers this transition.
    to_phase:
        The phase to move to on a successful transition.
    guard:
        Optional predicate ``(ctx) -> bool``.  If it returns ``False`` the
        transition is blocked.
    action:
        Optional callback invoked when the transition fires.
    """

    from_phase: InteractionPhase
    event_kind: str
    to_phase: InteractionPhase
    guard: Optional[GuardFn] = None
    action: Optional[ActionFn] = None


# ---------------------------------------------------------------------------
# InteractionStateMachine
# ---------------------------------------------------------------------------


class InteractionStateMachine:
    """Finite-state machine for tracking widget interaction phases.

    Usage::

        ism = InteractionStateMachine()
        ism.add_transition(InteractionTransition(
            InteractionPhase.IDLE, "pointer_enter", InteractionPhase.HOVER
        ))
        ctx = InteractionContext(event_kind="pointer_enter", pos=(10, 20))
        ism.handle_event(ctx)
        assert ism.phase == InteractionPhase.HOVER

    A global wildcard transition can be registered with ``from_phase=None``
    (matches any current phase) by calling :meth:`add_transition` with a
    transition whose ``from_phase`` is ``None``.  This is useful for
    CANCELLED transitions that should fire regardless of the current phase.
    """

    def __init__(
        self,
        initial_phase: InteractionPhase = InteractionPhase.IDLE,
    ) -> None:
        self._phase = initial_phase
        self._transitions: List[InteractionTransition] = []
        self._on_phase_change: List[Callable[[InteractionPhase, InteractionPhase], None]] = []

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------

    @property
    def phase(self) -> InteractionPhase:
        """The current interaction phase."""
        return self._phase

    # ------------------------------------------------------------------
    # Transitions
    # ------------------------------------------------------------------

    def add_transition(self, transition: InteractionTransition) -> None:
        """Register a :class:`InteractionTransition`."""
        self._transitions.append(transition)

    def handle_event(self, ctx: InteractionContext) -> bool:
        """Attempt to advance the state machine given *ctx*.

        Returns ``True`` if a transition fired, ``False`` if no matching
        transition was found or all guards rejected the event.
        """
        for t in self._transitions:
            if t.from_phase is not None and t.from_phase != self._phase:
                continue
            if t.event_kind != ctx.event_kind:
                continue
            if t.guard is not None and not t.guard(ctx):
                continue
            # Transition fires
            old_phase = self._phase
            self._phase = t.to_phase
            if t.action is not None:
                t.action(ctx)
            for cb in list(self._on_phase_change):
                cb(old_phase, self._phase)
            return True
        return False

    # ------------------------------------------------------------------
    # Phase-change observers
    # ------------------------------------------------------------------

    def on_phase_change(
        self,
        callback: Callable[[InteractionPhase, InteractionPhase], None],
    ) -> Callable[[], None]:
        """Subscribe to phase-change notifications.

        *callback* receives ``(old_phase, new_phase)``.
        Returns an unsubscribe callable.
        """
        self._on_phase_change.append(callback)

        def _unsub() -> None:
            try:
                self._on_phase_change.remove(callback)
            except ValueError:
                pass

        return _unsub

    # ------------------------------------------------------------------
    # Reset
    # ------------------------------------------------------------------

    def reset(self, phase: InteractionPhase = InteractionPhase.IDLE) -> None:
        """Reset to *phase* without firing transitions or callbacks."""
        self._phase = phase

    # ------------------------------------------------------------------
    # Helpers for common patterns
    # ------------------------------------------------------------------

    @classmethod
    def with_standard_pointer_transitions(cls) -> "InteractionStateMachine":
        """Return a pre-wired machine with standard pointer interactions.

        Transitions::

            IDLE       --pointer_enter--> HOVER
            HOVER      --pointer_leave --> IDLE
            HOVER      --pointer_down  --> PRESSED
            PRESSED    --pointer_up    --> HOVER
            PRESSED    --drag_start    --> DRAGGING
            DRAGGING   --pointer_up    --> IDLE
            *          --cancel        --> CANCELLED
            CANCELLED  --reset         --> IDLE
        """
        ism = cls()
        T = InteractionTransition
        P = InteractionPhase
        ism.add_transition(T(P.IDLE, "pointer_enter", P.HOVER))
        ism.add_transition(T(P.HOVER, "pointer_leave", P.IDLE))
        ism.add_transition(T(P.HOVER, "pointer_down", P.PRESSED))
        ism.add_transition(T(P.PRESSED, "pointer_up", P.HOVER))
        ism.add_transition(T(P.PRESSED, "drag_start", P.DRAGGING))
        ism.add_transition(T(P.DRAGGING, "pointer_up", P.IDLE))
        # Wildcard cancel (from_phase=None)
        ism.add_transition(T(None, "cancel", P.CANCELLED))  # type: ignore[arg-type]
        ism.add_transition(T(P.CANCELLED, "reset", P.IDLE))
        return ism
