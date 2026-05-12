from __future__ import annotations

from typing import Optional, Tuple

from .gui_event import GuiEvent


class InputState:
    """Normalized pointer state for one frame."""

    def __init__(self) -> None:
        self.pointer_pos: Tuple[int, int] = (0, 0)

    def update_from_event(self, event: object) -> None:
        """Apply event to input state."""
        raw_pos = event.pos
        if isinstance(raw_pos, tuple) and len(raw_pos) == 2:
            self.pointer_pos = raw_pos


class EventManager:
    """Converts raw events into canonical GuiEvent objects."""

    def to_gui_event(self, event, pointer_pos: Optional[Tuple[int, int]] = None) -> GuiEvent:
        if isinstance(event, GuiEvent):
            return event
        return GuiEvent.from_pygame(event, pointer_pos=pointer_pos)
