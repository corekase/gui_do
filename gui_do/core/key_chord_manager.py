"""KeyChordManager — multi-key sequential chord dispatch.

A *chord* is a sequence of two or more keystroke steps, each defined by a key
code and an optional modifier mask (e.g. Ctrl+K then Ctrl+C).  The manager
intercepts ``KEY_DOWN`` events, accumulates partial-chord state, and fires
the matched action when the full sequence is completed.

Only *exact* chords are matched: every step in the chord sequence must match
key and mod within the configured timeout.  If the first key of a chord is
pressed but no subsequent step matches within ``timeout_ms`` milliseconds, the
partial state is reset and the event is re-dispatched to the fallback handler.

Chords are composed from one or more :class:`ChordStep` objects::

    from gui_do import KeyChordManager, KeyChord, ChordStep
    import pygame

    manager = KeyChordManager(actions, timers, timeout_ms=1500)

    # Ctrl+K  then  Ctrl+C
    manager.bind(
        KeyChord(
            steps=[
                ChordStep(key=pygame.K_k, mod=pygame.KMOD_CTRL),
                ChordStep(key=pygame.K_c, mod=pygame.KMOD_CTRL),
            ]
        ),
        action_name="editor.copy_line",
    )

    # In your feature/scene handle_event:
    def handle_event(self, event, host):
        if manager.process_event(event):
            return True   # chord consumed
        return False

    # Register the action handler:
    actions.register_action("editor.copy_line", lambda event: True)

:class:`KeyChordManager` does **not** extend :class:`~gui_do.ActionManager` —
it delegates to one via composition so chords can co-exist with simple key
bindings in the same ``ActionManager``.

Modifier matching uses a bitmask AND, so ``mod=KMOD_CTRL`` matches both left-
and right-Ctrl.  Pass ``mod=0`` to match any step regardless of modifiers.

Thread safety: this class is single-threaded and intended to be driven from
the main event loop.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Sequence, Tuple, TYPE_CHECKING

from .gui_event import EventType

if TYPE_CHECKING:
    pass  # GuiEvent imported at runtime to keep the module importable without pygame


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ChordStep:
    """A single keystroke in a chord sequence.

    Parameters
    ----------
    key:
        Pygame key constant (e.g. ``pygame.K_k``).
    mod:
        Bitmask of required modifiers (e.g. ``pygame.KMOD_CTRL``).  ``0``
        means no modifier is required.  The check is ``event.mod & mod == mod``
        so partial modifier overlap is allowed.
    """

    key: int
    mod: int = 0


@dataclass(frozen=True)
class KeyChord:
    """An immutable ordered sequence of :class:`ChordStep` keystroke steps.

    Parameters
    ----------
    steps:
        Two or more :class:`ChordStep` objects that define the sequence.
        Single-step chords are accepted but :class:`KeyChordManager` will
        match them on the first keypress alone.
    """

    steps: Tuple[ChordStep, ...]

    def __init__(self, steps: Sequence[ChordStep]) -> None:
        if not steps:
            raise ValueError("KeyChord must have at least one step")
        object.__setattr__(self, "steps", tuple(steps))

    def __len__(self) -> int:
        return len(self.steps)

    def __getitem__(self, index: int) -> ChordStep:
        return self.steps[index]


# ---------------------------------------------------------------------------
# KeyChordManager
# ---------------------------------------------------------------------------


class KeyChordManager:
    """Intercepts key events and dispatches multi-step keyboard chord actions.

    Parameters
    ----------
    actions:
        The :class:`~gui_do.ActionManager` that owns the action handlers.
    timers:
        The :class:`~gui_do.Timers` instance used to implement the chord
        timeout.  If ``None``, no timeout is applied.
    timeout_ms:
        Milliseconds allowed between consecutive chord steps before the
        partial chord state resets.  Defaults to ``1500``.
    """

    _TIMER_ID_PREFIX = "_key_chord_timeout_"

    def __init__(
        self,
        actions,
        timers=None,
        *,
        timeout_ms: int = 1500,
    ) -> None:
        if actions is None:
            raise ValueError("actions must not be None")
        self._actions = actions
        self._timers = timers
        self._timeout_s: float = max(0, int(timeout_ms)) / 1000.0
        # Registered chords — each entry: (chord, action_name)
        self._chords: List[Tuple[KeyChord, str]] = []
        # Current partial chord state
        self._progress: int = 0          # depth into the chord sequence so far
        self._active_matches: List[Tuple[KeyChord, str]] = []   # candidate chords

        self._timer_id = self._TIMER_ID_PREFIX + str(id(self))

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def bind(self, chord: KeyChord, action_name: str) -> None:
        """Register *chord* to trigger *action_name*.

        If the chord is already registered it is replaced.
        """
        self._chords = [(c, a) for c, a in self._chords if c != chord]
        self._chords.append((chord, action_name))

    def unbind(self, chord: KeyChord) -> bool:
        """Remove a chord registration. Returns True if it was present."""
        before = len(self._chords)
        self._chords = [(c, a) for c, a in self._chords if c != chord]
        return len(self._chords) < before

    def registered_chords(self) -> List[KeyChord]:
        """Return a list of all registered chords."""
        return [c for c, _ in self._chords]

    # ------------------------------------------------------------------
    # Event processing
    # ------------------------------------------------------------------

    def process_event(self, event) -> bool:
        """Process *event* and return True if it was consumed by a chord.

        Call this from ``handle_event`` before any other key handling.  If the
        method returns True, the event has been consumed and the registered
        action handler has been called (or partial chord state has been updated
        and the event should be suppressed to avoid double-handling).

        When a partial chord is in progress (the first step was matched), all
        subsequent ``KEY_DOWN`` events are consumed until the chord is either
        completed or the timeout resets the state.
        """
        if event.kind is not EventType.KEY_DOWN or event.key is None:
            return False

        step_progress = self._progress

        if step_progress == 0:
            # Not in a chord — check if any chord starts with this key
            candidates = self._matching_candidates(event, step=0)
            if not candidates:
                return False  # not the start of any chord

            # Advance progress
            self._active_matches = candidates
            self._progress = 1
            # Check for single-step chords that complete immediately
            complete = [(c, a) for c, a in candidates if len(c) == 1]
            if complete:
                chord, action_name = complete[0]
                self._reset()
                return self._fire(action_name, event)
            # Multi-step chord in progress — arm timeout
            self._arm_timeout()
            return True  # consume the first step

        else:
            # Already in a partial chord — check candidates for next step
            candidates = self._matching_candidates(event, step=step_progress)
            if not candidates:
                # No match — reset and do NOT consume so the key falls through
                self._reset()
                return False

            self._active_matches = candidates
            self._progress = step_progress + 1

            # Complete any chord that matches fully at current depth
            complete = [(c, a) for c, a in candidates if len(c) == self._progress]
            if complete:
                chord, action_name = complete[0]
                self._reset()
                return self._fire(action_name, event)

            # Still in progress
            self._arm_timeout()
            return True

    def reset(self) -> None:
        """Manually reset any in-progress chord state (e.g. on focus loss)."""
        self._reset()

    @property
    def is_in_progress(self) -> bool:
        """Return True when a partial chord sequence is being accumulated."""
        return self._progress > 0

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _matching_candidates(self, event, *, step: int) -> List[Tuple[KeyChord, str]]:
        """Return chords that match *event* at *step* from the current active matches."""
        pool = self._active_matches if step > 0 else self._chords
        result = []
        for chord, action_name in pool:
            if step >= len(chord):
                continue
            cs = chord[step]
            key_match = event.key == cs.key
            mod_match = (cs.mod == 0) or (event.mod & cs.mod == cs.mod)
            if key_match and mod_match:
                result.append((chord, action_name))
        return result

    def _fire(self, action_name: str, event) -> bool:
        """Invoke the action handler and return True if it consumed the event."""
        handler = self._actions._actions.get(action_name)
        if handler is None:
            return False
        try:
            return bool(handler(event))
        except Exception:
            return False

    def _arm_timeout(self) -> None:
        if self._timers is None or self._timeout_s <= 0:
            return
        self._timers.remove_timer(self._timer_id)
        self._timers.add_once(self._timer_id, self._timeout_s, self._reset)

    def _reset(self) -> None:
        if self._timers is not None:
            self._timers.remove_timer(self._timer_id)
        self._progress = 0
        self._active_matches = []
