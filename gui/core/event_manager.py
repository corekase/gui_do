from __future__ import annotations

from typing import Optional, Tuple

from .gui_event import GuiEvent


class EventManager:
    """Converts raw events into canonical GuiEvent objects."""

    def to_gui_event(self, event, pointer_pos: Optional[Tuple[int, int]] = None) -> GuiEvent:
        if isinstance(event, GuiEvent):
            return event
        return GuiEvent.from_pygame(event, pointer_pos=pointer_pos)
