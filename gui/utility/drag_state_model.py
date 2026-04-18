from dataclasses import dataclass
from typing import Optional, Tuple

from ..widgets.window import Window as gWindow


@dataclass
class DragState:
    """Holds drag lifecycle state for window dragging interactions."""

    dragging: bool = False
    dragging_window: Optional[gWindow] = None
    mouse_delta: Optional[Tuple[int, int]] = None
