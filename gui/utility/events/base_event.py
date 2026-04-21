from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from .event import Event

if TYPE_CHECKING:
    from ...widgets.window import Window


class BaseEvent:
    """Base event type for all framework-dispatched events."""

    def __init__(self, event_type: Event) -> None:
        """Create BaseEvent."""
        self.type: Event = event_type
        self.window: Optional["Window"] = None
        self.task_panel: bool = False
