"""InputSnapshot — immutable per-frame input state assembled once for all consumers.

An :class:`InputSnapshot` is built once at the start of each frame from the
current pygame state plus the normalized events processed in that tick.  It is
then passed read-only to every system that needs input state: gesture
recognizers, tooltip managers, drag-drop, key-chord managers, and controls.

This eliminates the fragmented per-system mouse/key-state bookkeeping that
previously spread across ``GuiManager``, ``InputRouter``, ``FocusManager``,
and individual controls.

Usage::

    from gui_do import InputSnapshot

    # Build once per frame before event dispatch:
    snapshot = InputSnapshot.build(events=normalized_events_this_frame,
                                   previous=last_frame_snapshot)

    # Consumers read from it:
    if snapshot.is_button_just_pressed(1):
        start_drag()

    if snapshot.is_key_down(pygame.K_SHIFT):
        extend_selection()

    hovered_id = snapshot.hover_chain[0] if snapshot.hover_chain else None

    wheel = snapshot.accumulated_wheel_delta  # sum for the frame
"""
from __future__ import annotations

from typing import FrozenSet, Optional, Sequence, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from .gui_event import GuiEvent


class InputSnapshot:
    """Immutable snapshot of pointer and keyboard input state for one frame.

    Parameters
    ----------
    pointer_pos:
        Current logical pointer position (x, y).
    pointer_delta:
        Pointer movement since last frame (dx, dy).
    buttons_held:
        Frozenset of mouse button numbers currently held down (1-based).
    buttons_just_pressed:
        Frozenset of buttons that transitioned down this frame.
    buttons_just_released:
        Frozenset of buttons that transitioned up this frame.
    modifiers:
        Current pygame modifier bitmask (``pygame.key.get_mods()`` value).
    keys_just_pressed:
        Frozenset of pygame keysym constants pressed this frame.
    keys_just_released:
        Frozenset of pygame keysym constants released this frame.
    accumulated_wheel_delta:
        Sum of all wheel-scroll deltas (positive = up/forward) for the frame.
    hover_chain:
        Ordered sequence of ``control_id`` strings from outermost to innermost
        node under the pointer (populated by the hit-test phase, empty if not
        yet resolved).
    """

    __slots__ = (
        "pointer_pos",
        "pointer_delta",
        "buttons_held",
        "buttons_just_pressed",
        "buttons_just_released",
        "modifiers",
        "keys_just_pressed",
        "keys_just_released",
        "accumulated_wheel_delta",
        "hover_chain",
    )

    def __init__(
        self,
        *,
        pointer_pos: Tuple[int, int] = (0, 0),
        pointer_delta: Tuple[int, int] = (0, 0),
        buttons_held: FrozenSet[int] = frozenset(),
        buttons_just_pressed: FrozenSet[int] = frozenset(),
        buttons_just_released: FrozenSet[int] = frozenset(),
        modifiers: int = 0,
        keys_just_pressed: FrozenSet[int] = frozenset(),
        keys_just_released: FrozenSet[int] = frozenset(),
        accumulated_wheel_delta: float = 0.0,
        hover_chain: Tuple[str, ...] = (),
    ) -> None:
        self.pointer_pos: Tuple[int, int] = pointer_pos
        self.pointer_delta: Tuple[int, int] = pointer_delta
        self.buttons_held: FrozenSet[int] = buttons_held
        self.buttons_just_pressed: FrozenSet[int] = buttons_just_pressed
        self.buttons_just_released: FrozenSet[int] = buttons_just_released
        self.modifiers: int = modifiers
        self.keys_just_pressed: FrozenSet[int] = keys_just_pressed
        self.keys_just_released: FrozenSet[int] = keys_just_released
        self.accumulated_wheel_delta: float = accumulated_wheel_delta
        self.hover_chain: Tuple[str, ...] = hover_chain

    # ------------------------------------------------------------------
    # Convenience queries
    # ------------------------------------------------------------------

    def is_button_held(self, button: int) -> bool:
        """True if *button* (1=left, 2=middle, 3=right) is currently held."""
        return button in self.buttons_held

    def is_button_just_pressed(self, button: int) -> bool:
        """True if *button* transitioned down this frame."""
        return button in self.buttons_just_pressed

    def is_button_just_released(self, button: int) -> bool:
        """True if *button* transitioned up this frame."""
        return button in self.buttons_just_released

    def is_key_down(self, key: int) -> bool:
        """True if modifier flag *key* is set (use ``pygame.KMOD_*`` constants)."""
        return bool(self.modifiers & key)

    def is_key_just_pressed(self, keysym: int) -> bool:
        """True if pygame keysym *keysym* was pressed this frame."""
        return keysym in self.keys_just_pressed

    def is_key_just_released(self, keysym: int) -> bool:
        """True if pygame keysym *keysym* was released this frame."""
        return keysym in self.keys_just_released

    @property
    def topmost_hovered_id(self) -> Optional[str]:
        """Return the innermost hovered ``control_id``, or ``None``."""
        return self.hover_chain[-1] if self.hover_chain else None

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @classmethod
    def build(
        cls,
        events: "Sequence[GuiEvent]",
        previous: "Optional[InputSnapshot]" = None,
    ) -> "InputSnapshot":
        """Build a snapshot from a sequence of :class:`~gui_do.GuiEvent` objects.

        ``previous`` is used to derive ``buttons_held`` across frames and to
        compute ``pointer_delta`` relative to the last known position.
        """
        from .gui_event import EventType

        prev_pos = previous.pointer_pos if previous is not None else (0, 0)
        prev_held = previous.buttons_held if previous is not None else frozenset()

        pointer_pos: Tuple[int, int] = prev_pos
        pointer_delta: Tuple[int, int] = (0, 0)
        held = set(prev_held)
        just_pressed: set[int] = set()
        just_released: set[int] = set()
        modifiers: int = 0
        keys_pressed: set[int] = set()
        keys_released: set[int] = set()
        wheel_delta: float = 0.0

        for ev in events:
            kind = ev.kind
            if kind == EventType.MOUSE_MOTION:
                pos = ev.pos
                if isinstance(pos, tuple) and len(pos) == 2:
                    pointer_pos = (int(pos[0]), int(pos[1]))
                rel = getattr(ev, "rel", None)
                if isinstance(rel, tuple) and len(rel) == 2:
                    pointer_delta = (
                        pointer_delta[0] + int(rel[0]),
                        pointer_delta[1] + int(rel[1]),
                    )
            elif kind == EventType.MOUSE_BUTTON_DOWN:
                pos = ev.pos
                if isinstance(pos, tuple) and len(pos) == 2:
                    pointer_pos = (int(pos[0]), int(pos[1]))
                btn = getattr(ev, "button", None)
                if isinstance(btn, int):
                    held.add(btn)
                    just_pressed.add(btn)
                mod = getattr(ev, "mod", 0)
                if isinstance(mod, int):
                    modifiers = mod
            elif kind == EventType.MOUSE_BUTTON_UP:
                pos = ev.pos
                if isinstance(pos, tuple) and len(pos) == 2:
                    pointer_pos = (int(pos[0]), int(pos[1]))
                btn = getattr(ev, "button", None)
                if isinstance(btn, int):
                    held.discard(btn)
                    just_released.add(btn)
                mod = getattr(ev, "mod", 0)
                if isinstance(mod, int):
                    modifiers = mod
            elif kind == EventType.MOUSE_WHEEL:
                delta = getattr(ev, "wheel_delta", None)
                if delta is None:
                    delta = getattr(ev, "y", 0)
                wheel_delta += float(delta) if delta is not None else 0.0
            elif kind in (EventType.KEY_DOWN, EventType.KEY_UP):
                mod = getattr(ev, "mod", 0)
                if isinstance(mod, int):
                    modifiers = mod
                key = getattr(ev, "key", None)
                if isinstance(key, int):
                    if kind == EventType.KEY_DOWN:
                        keys_pressed.add(key)
                    else:
                        keys_released.add(key)

        return cls(
            pointer_pos=pointer_pos,
            pointer_delta=pointer_delta,
            buttons_held=frozenset(held),
            buttons_just_pressed=frozenset(just_pressed),
            buttons_just_released=frozenset(just_released),
            modifiers=modifiers,
            keys_just_pressed=frozenset(keys_pressed),
            keys_just_released=frozenset(keys_released),
            accumulated_wheel_delta=wheel_delta,
        )

    @classmethod
    def empty(cls) -> "InputSnapshot":
        """Return a zero-state snapshot (no buttons, no pointer movement)."""
        return cls()

    def with_hover_chain(self, chain: Tuple[str, ...]) -> "InputSnapshot":
        """Return a copy of this snapshot with a different *hover_chain*."""
        return InputSnapshot(
            pointer_pos=self.pointer_pos,
            pointer_delta=self.pointer_delta,
            buttons_held=self.buttons_held,
            buttons_just_pressed=self.buttons_just_pressed,
            buttons_just_released=self.buttons_just_released,
            modifiers=self.modifiers,
            keys_just_pressed=self.keys_just_pressed,
            keys_just_released=self.keys_just_released,
            accumulated_wheel_delta=self.accumulated_wheel_delta,
            hover_chain=chain,
        )
