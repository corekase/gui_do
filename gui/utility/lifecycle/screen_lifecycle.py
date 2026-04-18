from __future__ import annotations

from typing import Callable, Optional

from ..events import BaseEvent
from .lifecycle_callbacks import LifecycleCallbacks


class ScreenLifecycle:
    """Owns screen-level lifecycle callbacks and event handler."""

    def __init__(self) -> None:
        """Create ScreenLifecycle."""
        callbacks = LifecycleCallbacks()
        self.preamble: Callable[[], None] = callbacks.preamble
        self.event_handler: Callable[[BaseEvent], None] = callbacks.event_handler
        self.postamble: Callable[[], None] = callbacks.postamble

    def set_lifecycle(
        self,
        preamble: Optional[Callable[[], None]],
        event_handler: Optional[Callable[[BaseEvent], None]],
        postamble: Optional[Callable[[], None]],
    ) -> None:
        """Set lifecycle."""
        callbacks = LifecycleCallbacks.from_optionals(preamble, event_handler, postamble)
        self.preamble = callbacks.preamble
        self.event_handler = callbacks.event_handler
        self.postamble = callbacks.postamble

    def run_preamble(self) -> None:
        """Run preamble."""
        self.preamble()

    def run_postamble(self) -> None:
        """Run postamble."""
        self.postamble()

    def handle_event(self, event: BaseEvent) -> None:
        """Handle event."""
        self.event_handler(event)
