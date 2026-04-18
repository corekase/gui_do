from __future__ import annotations

from typing import Callable, Optional

from ..events import BaseEvent
from .lifecycle_callbacks import LifecycleCallbacks


class ScreenLifecycle:
    """Owns screen-level lifecycle callbacks and event handler."""

    def __init__(self) -> None:
        """Initialize the ScreenLifecycle instance."""
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
        """Run set lifecycle and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        callbacks = LifecycleCallbacks.from_optionals(preamble, event_handler, postamble)
        self.preamble = callbacks.preamble
        self.event_handler = callbacks.event_handler
        self.postamble = callbacks.postamble

    def run_preamble(self) -> None:
        """Run run preamble and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        self.preamble()

    def run_postamble(self) -> None:
        """Run run postamble and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        self.postamble()

    def handle_event(self, event: BaseEvent) -> None:
        """Run handle event and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        self.event_handler(event)
