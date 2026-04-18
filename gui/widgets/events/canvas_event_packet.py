from __future__ import annotations

from typing import Optional, Tuple

from ...utility.events import CanvasEvent


class CanvasEventPacket:
    """Canvas input payload with normalized coordinates and event-specific fields."""

    def __init__(self) -> None:
        """Initialize the CanvasEventPacket instance."""
        self.type: Optional[CanvasEvent] = None
        self.pos: Optional[Tuple[int, int]] = None
        self.rel: Optional[Tuple[int, int]] = None
        self.button: Optional[int] = None
        self.y: Optional[int] = None
