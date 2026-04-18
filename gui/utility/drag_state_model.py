from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from ..widgets.window import Window as Window


@dataclass
class DragState:
    """Holds drag lifecycle state for window dragging interactions."""

    dragging: bool = False
    dragging_window: Optional[Window] = None
    mouse_delta: Optional[Tuple[int, int]] = None

    def begin_drag(self, window: Window, mouse_delta: Tuple[int, int]) -> None:
        """Begin drag."""
        self.dragging = True
        self.dragging_window = window
        self.mouse_delta = mouse_delta

    def clear_drag(self) -> None:
        """Clear drag."""
        self.dragging = False
        self.dragging_window = None
        self.mouse_delta = None
