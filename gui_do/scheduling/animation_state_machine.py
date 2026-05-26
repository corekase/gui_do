"""AnimationStateMachine — state-driven animation controller.

Connects control state transitions (hover, press, show, hide …) to
:class:`~gui_do.TweenManager`-driven :class:`~gui_do.AnimationSequence`
chains without requiring each control to manage tween cancellation and
sequence selection manually.

Usage::

    from gui_do import AnimationStateMachine, AnimationTransitionMode, Easing

    asm = AnimationStateMachine(app.tweens)

    # Register states — each is a builder callback that configures an
    # AnimationSequence:
    def _idle_seq(seq):
        seq.then(target=button, attr="alpha", end_value=0.85, duration_seconds=0.15)

    def _hover_seq(seq):
        seq.then(target=button, attr="alpha", end_value=1.0, duration_seconds=0.1)

    def _press_seq(seq):
        (seq
         .then(target=button, attr="rect.width",
               end_value=button.rect.width - 4, duration_seconds=0.06)
         .then(target=button, attr="rect.width",
               end_value=button.rect.width, duration_seconds=0.06))

    asm.register_state("idle",  _idle_seq)
    asm.register_state("hover", _hover_seq)
    asm.register_state("press", _press_seq)

    # Register transitions (optional — default is INTERRUPT):
    asm.register_transition("hover", "idle",
                            mode=AnimationTransitionMode.COMPLETE_THEN_TRANSITION)
    asm.register_transition("press", "idle",
                            mode=AnimationTransitionMode.COMPLETE_THEN_TRANSITION)

    # Drive state changes from control event handlers:
    asm.set_state("hover")   # cancels idle sequence, starts hover sequence
    asm.set_state("press")
    asm.set_state("idle")

    # Observe state changes:
    asm.on_state_changed(lambda name: print("animation state →", name))

    # No update() needed — TweenManager drives tweens each frame automatically.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Callable, Optional, TYPE_CHECKING, Dict, List

if TYPE_CHECKING:
    from ..scheduling.tween_manager import TweenManager
    from ..scheduling.animation_sequence import AnimationSequence


class AnimationTransitionMode(Enum):
    """Controls how an in-progress animation is handled on state change."""

    INTERRUPT = "interrupt"
    """Cancel the current animation immediately and start the new one."""

    COMPLETE_THEN_TRANSITION = "complete_then_transition"
    """Let the current animation finish, then start the new one."""

    REVERSE_THEN_TRANSITION = "reverse_then_transition"
    """Play the current animation backwards to completion, then transition."""


SequenceBuilder = Callable[["AnimationSequence"], None]
StateChangedCallback = Callable[[str], None]


class AnimationStateMachine:
    """State machine that maps named states to :class:`~gui_do.AnimationSequence` builders.

    Parameters
    ----------
    tweens:
        The active scene's :class:`~gui_do.TweenManager`.
    initial_state:
        Optional initial state name.  The corresponding sequence is started
        immediately if supplied.
    """

    def __init__(
        self,
        tweens: "TweenManager",
        *,
        initial_state: Optional[str] = None,
    ) -> None:
        self._tweens = tweens
        self._states: Dict[str, SequenceBuilder] = {}
        self._transitions: Dict[str, Dict[str, AnimationTransitionMode]] = {}
        self._current_state: Optional[str] = None
        self._pending_state: Optional[str] = None
        self._current_handle: Optional[Any] = None   # AnimationHandle
        self._state_changed_cbs: List[StateChangedCallback] = []

        if initial_state is not None:
            self.register_state(initial_state, lambda seq: None)
            self._current_state = initial_state

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register_state(self, name: str, builder: SequenceBuilder) -> None:
        """Register a named animation state with a sequence *builder* callable.

        The *builder* receives an :class:`~gui_do.AnimationSequence` instance
        and should call chained methods (``.then``, ``.parallel``, ``.wait``)
        to configure the animation.  It must not call ``.start()``.
        """
        self._states[name] = builder

    def register_transition(
        self,
        from_state: str,
        to_state: str,
        *,
        mode: AnimationTransitionMode = AnimationTransitionMode.INTERRUPT,
    ) -> None:
        """Override the default transition mode for a specific state pair.

        Parameters
        ----------
        from_state:
            The currently active state.  Use ``"*"`` to match any state.
        to_state:
            The requested new state.
        mode:
            How to handle the in-progress animation.  Default is
            :attr:`~AnimationTransitionMode.INTERRUPT`.
        """
        self._transitions.setdefault(from_state, {})[to_state] = mode

    def on_state_changed(self, callback: StateChangedCallback) -> Callable[[], None]:
        """Register *callback* to be called after each state change.

        Returns an unsub callable.
        """
        self._state_changed_cbs.append(callback)

        def _unsub() -> None:
            try:
                self._state_changed_cbs.remove(callback)
            except ValueError:
                pass

        return _unsub

    # ------------------------------------------------------------------
    # State transitions
    # ------------------------------------------------------------------

    def set_state(self, name: str) -> None:
        """Request a transition to state *name*.

        Raises ``KeyError`` if the state was not registered.  The transition
        mode (INTERRUPT, COMPLETE_THEN_TRANSITION, or REVERSE_THEN_TRANSITION)
        is resolved from registered overrides, falling back to INTERRUPT.
        """
        if name not in self._states:
            raise KeyError(f"AnimationStateMachine: unknown state {name!r}")
        if name == self._current_state:
            return

        mode = self._resolve_mode(self._current_state, name)

        if mode == AnimationTransitionMode.INTERRUPT or self._current_handle is None:
            self._start_state(name)
        elif mode == AnimationTransitionMode.COMPLETE_THEN_TRANSITION:
            # Queue — will be processed when the current sequence fires _on_done
            self._pending_state = name
        elif mode == AnimationTransitionMode.REVERSE_THEN_TRANSITION:
            # Cancel and queue; full reverse is not implemented — falls back to INTERRUPT
            self._pending_state = name
            self._start_state(name)

    def reset(self) -> None:
        """Cancel the current animation and clear state."""
        if self._current_handle is not None:
            self._current_handle.cancel()
            self._current_handle = None
        self._current_state = None
        self._pending_state = None

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    @property
    def current_state(self) -> Optional[str]:
        """The currently active animation state name, or ``None``."""
        return self._current_state

    def is_transitioning(self) -> bool:
        """Return True if a sequence is currently running."""
        return self._current_handle is not None and not self._current_handle.cancelled

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _resolve_mode(
        self,
        from_state: Optional[str],
        to_state: str,
    ) -> AnimationTransitionMode:
        if from_state is None:
            return AnimationTransitionMode.INTERRUPT
        # Check exact pair first
        mode = self._transitions.get(from_state, {}).get(to_state)
        if mode is not None:
            return mode
        # Wildcard source
        mode = self._transitions.get("*", {}).get(to_state)
        if mode is not None:
            return mode
        return AnimationTransitionMode.INTERRUPT

    def _start_state(self, name: str) -> None:
        from ..scheduling.animation_sequence import AnimationSequence

        # Cancel previous
        if self._current_handle is not None:
            self._current_handle.cancel()
            self._current_handle = None

        self._current_state = name
        self._pending_state = None

        builder = self._states[name]
        seq = AnimationSequence(self._tweens)
        builder(seq)

        # Wire done callback to process any pending transition
        seq.on_done(self._on_sequence_done)
        self._current_handle = seq.start()

        for cb in list(self._state_changed_cbs):
            cb(name)

    def _on_sequence_done(self) -> None:
        self._current_handle = None
        if self._pending_state is not None:
            self._start_state(self._pending_state)
