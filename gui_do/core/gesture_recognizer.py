"""GestureRecognizer — composed pointer gesture detection from raw GuiEvents.

Recognises common composed gestures from a stream of :class:`~gui_do.GuiEvent`
objects and fires registered callbacks.  Attach one recognizer per interactive
node that needs gesture semantics (``Canvas``, ``Image``, list rows, etc.).

Supported gestures
------------------
- **double_click**: two ``MOUSE_DOWN`` events within ``double_click_ms``
  milliseconds and ``double_click_slop`` pixels of each other.
- **long_press**: ``MOUSE_DOWN`` held for at least ``long_press_ms``
  milliseconds without significant movement (> ``long_press_slop`` pixels).
- **swipe**: ``MOUSE_UP`` ending a drag whose displacement exceeds
  ``swipe_min_px`` pixels.  Fires with the detected direction string:
  ``"left"``, ``"right"``, ``"up"``, or ``"down"``.

All thresholds are configurable at construction time.

Usage::

    gr = GestureRecognizer(
        on_double_click=lambda pos: zoom_in(pos),
        on_long_press=lambda pos: show_context_menu(pos),
        on_swipe=lambda direction, velocity: handle_swipe(direction, velocity),
    )

    # In the node's update():
    gr.update(dt_seconds)

    # In the node's handle_event():
    gr.process_event(event)

The recognizer is portable — it uses only :class:`~gui_do.GuiEvent` fields and
a ``dt_seconds`` accumulator.  No OS-level pointer APIs are used.
"""
from __future__ import annotations

import math
from typing import Callable, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from .gui_event import GuiEvent


# Default thresholds (all portable, frame-rate independent)
_DEFAULT_DOUBLE_CLICK_MS = 400
_DEFAULT_DOUBLE_CLICK_SLOP_PX = 8
_DEFAULT_LONG_PRESS_MS = 600
_DEFAULT_LONG_PRESS_SLOP_PX = 10
_DEFAULT_SWIPE_MIN_PX = 40


SwipeCallback = Callable[[str, float], None]   # (direction, velocity_px_per_s)
GestureCallback = Callable[[Tuple[int, int]], None]   # (pos,)


class GestureRecognizer:
    """Frame-driven gesture recognizer for double-click, long-press, and swipe.

    Parameters
    ----------
    on_double_click:
        Fired with the click position when a double-click is detected.
    on_long_press:
        Fired with the press position when a long-press is detected.
    on_swipe:
        Fired with ``(direction, velocity_px_per_s)`` on swipe completion.
        *direction* is one of ``"left"``, ``"right"``, ``"up"``, ``"down"``.
    double_click_ms:
        Maximum interval between two clicks to count as a double-click.
    double_click_slop:
        Maximum pixel distance between two clicks to count as a double-click.
    long_press_ms:
        Minimum hold duration (ms) to fire a long-press.
    long_press_slop:
        Maximum movement (pixels) allowed during a long-press hold.
    swipe_min_px:
        Minimum displacement (pixels) required for a swipe to fire.
    button:
        Mouse button to monitor (1 = left, 3 = right).
    """

    def __init__(
        self,
        *,
        on_double_click: Optional[GestureCallback] = None,
        on_long_press: Optional[GestureCallback] = None,
        on_swipe: Optional[SwipeCallback] = None,
        double_click_ms: int = _DEFAULT_DOUBLE_CLICK_MS,
        double_click_slop: int = _DEFAULT_DOUBLE_CLICK_SLOP_PX,
        long_press_ms: int = _DEFAULT_LONG_PRESS_MS,
        long_press_slop: int = _DEFAULT_LONG_PRESS_SLOP_PX,
        swipe_min_px: int = _DEFAULT_SWIPE_MIN_PX,
        button: int = 1,
    ) -> None:
        self._on_double_click = on_double_click
        self._on_long_press = on_long_press
        self._on_swipe = on_swipe

        self._double_click_interval_s = max(1, int(double_click_ms)) / 1000.0
        self._double_click_slop = max(0, int(double_click_slop))
        self._long_press_threshold_s = max(1, int(long_press_ms)) / 1000.0
        self._long_press_slop = max(0, int(long_press_slop))
        self._swipe_min_px = max(1, int(swipe_min_px))
        self._button = int(button)

        # Double-click state
        self._last_click_time_s: float = -999.0
        self._last_click_pos: Optional[Tuple[int, int]] = None

        # Long-press state
        self._press_active: bool = False
        self._press_pos: Optional[Tuple[int, int]] = None
        self._press_elapsed_s: float = 0.0
        self._long_press_fired: bool = False

        # Swipe state (reuses press pos as start)
        self._swipe_start_pos: Optional[Tuple[int, int]] = None
        self._swipe_start_time_s: float = 0.0
        self._total_elapsed_s: float = 0.0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update(self, dt_seconds: float) -> None:
        """Advance time accumulators. Call once per frame from the owning node's ``update()``."""
        self._total_elapsed_s += dt_seconds
        if self._press_active and not self._long_press_fired:
            self._press_elapsed_s += dt_seconds
            if self._press_elapsed_s >= self._long_press_threshold_s:
                self._long_press_fired = True
                if self._on_long_press is not None and self._press_pos is not None:
                    self._on_long_press(self._press_pos)

    def process_event(self, event: "GuiEvent") -> None:
        """Feed a :class:`~gui_do.GuiEvent` into the recognizer.

        Call from the owning node's ``handle_event()`` or ``on_event()``.
        """
        from .gui_event import EventType
        kind = getattr(event, "kind", None)

        if kind == EventType.MOUSE_DOWN and getattr(event, "button", None) == self._button:
            self._on_mouse_down(event)
        elif kind == EventType.MOUSE_UP and getattr(event, "button", None) == self._button:
            self._on_mouse_up(event)
        elif kind == EventType.MOUSE_MOTION:
            self._on_mouse_motion(event)

    def reset(self) -> None:
        """Clear all pending gesture state."""
        self._last_click_time_s = -999.0
        self._last_click_pos = None
        self._press_active = False
        self._press_pos = None
        self._press_elapsed_s = 0.0
        self._long_press_fired = False
        self._swipe_start_pos = None

    # ------------------------------------------------------------------
    # Internal event handlers
    # ------------------------------------------------------------------

    def _on_mouse_down(self, event: "GuiEvent") -> None:
        pos = self._event_pos(event)
        if pos is None:
            return
        now = self._total_elapsed_s
        # Double-click detection
        if (
            self._last_click_pos is not None
            and now - self._last_click_time_s <= self._double_click_interval_s
            and self._dist(pos, self._last_click_pos) <= self._double_click_slop
        ):
            # Double-click confirmed
            self._last_click_pos = None
            self._last_click_time_s = -999.0
            if self._on_double_click is not None:
                self._on_double_click(pos)
        else:
            self._last_click_time_s = now
            self._last_click_pos = pos

        # Begin press / swipe tracking
        self._press_active = True
        self._press_pos = pos
        self._press_elapsed_s = 0.0
        self._long_press_fired = False
        self._swipe_start_pos = pos
        self._swipe_start_time_s = now

    def _on_mouse_up(self, event: "GuiEvent") -> None:
        if not self._press_active:
            return
        pos = self._event_pos(event)
        self._press_active = False
        # Swipe detection
        if (
            self._on_swipe is not None
            and not self._long_press_fired
            and self._swipe_start_pos is not None
            and pos is not None
        ):
            dx = pos[0] - self._swipe_start_pos[0]
            dy = pos[1] - self._swipe_start_pos[1]
            dist = self._dist(pos, self._swipe_start_pos)
            if dist >= self._swipe_min_px:
                elapsed = self._total_elapsed_s - self._swipe_start_time_s
                velocity = dist / max(elapsed, 1e-6)
                direction = self._classify_swipe(dx, dy)
                self._on_swipe(direction, velocity)
        self._swipe_start_pos = None
        self._press_pos = None
        self._long_press_fired = False

    def _on_mouse_motion(self, event: "GuiEvent") -> None:
        if not self._press_active or self._long_press_fired:
            return
        pos = self._event_pos(event)
        if pos is not None and self._press_pos is not None:
            if self._dist(pos, self._press_pos) > self._long_press_slop:
                # Movement cancelled long-press; reset press timer
                self._press_elapsed_s = 0.0

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _event_pos(event: "GuiEvent") -> Optional[Tuple[int, int]]:
        pos = getattr(event, "pos", None)
        if isinstance(pos, tuple) and len(pos) == 2:
            return (int(pos[0]), int(pos[1]))
        return None

    @staticmethod
    def _dist(a: Tuple[int, int], b: Tuple[int, int]) -> float:
        return math.hypot(a[0] - b[0], a[1] - b[1])

    @staticmethod
    def _classify_swipe(dx: int, dy: int) -> str:
        if abs(dx) >= abs(dy):
            return "right" if dx > 0 else "left"
        return "down" if dy > 0 else "up"
