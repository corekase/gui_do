from __future__ import annotations

from .event import Event


class BaseEvent:
    """Base event type for all framework-dispatched events."""

    def __init__(self, event_type: Event) -> None:
        """Initialize the BaseEvent instance."""
        self.type: Event = event_type
