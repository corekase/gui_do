from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple, Any

from ...widgets.window import Window


@dataclass
class DragState:
    """Holds drag lifecycle state for window dragging interactions."""

    dragging: bool = False
    dragging_window: Optional[Window] = None
    mouse_delta: Optional[Tuple[int, int]] = None

    @staticmethod
    def _is_window_like(window: Any) -> bool:
        """Return whether object satisfies the minimal drag-window contract."""
        if window is None:
            return False
        try:
            return isinstance(window.x, int) and isinstance(window.y, int)
        except AttributeError:
            return False

    @staticmethod
    def _validate_drag_context(window: Window, mouse_delta: Tuple[int, int]) -> None:
        """Validate drag context values before state transitions."""
        if not DragState._is_window_like(window):
            raise ValueError(f'window must satisfy drag-window contract, got: {window}')
        if not isinstance(mouse_delta, tuple) or len(mouse_delta) != 2:
            raise ValueError(f'mouse_delta must be a tuple of (x, y), got: {mouse_delta}')
        dx, dy = mouse_delta
        if not isinstance(dx, int) or not isinstance(dy, int):
            raise ValueError(f'mouse_delta values must be ints, got: {mouse_delta}')

    def has_context(self) -> bool:
        """Return whether current drag state has a complete drag context."""
        return self.dragging_window is not None and self.mouse_delta is not None

    def start_drag(self, window: Window, mouse_delta: Tuple[int, int]) -> None:
        """Enter active drag state with a validated window/delta context."""
        self._validate_drag_context(window, mouse_delta)
        self.dragging = True
        self.dragging_window = window
        self.mouse_delta = mouse_delta

    def stop_drag(self) -> None:
        """Return to idle drag state and clear all drag context."""
        self.dragging = False
        self.dragging_window = None
        self.mouse_delta = None
