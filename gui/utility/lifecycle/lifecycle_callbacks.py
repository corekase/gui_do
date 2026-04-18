from __future__ import annotations

from typing import Callable

from ..events import BaseEvent


def _noop() -> None:
    """Internal helper for noop."""
    pass


def _noop_event(_: BaseEvent) -> None:
    """Internal helper for noop event."""
    pass


class LifecycleCallbacks:
    """Holds preamble/event/postamble callbacks with noop defaults."""

    def __init__(
        self,
        preamble: Callable[[], None] = _noop,
        event_handler: Callable[[BaseEvent], None] = _noop_event,
        postamble: Callable[[], None] = _noop,
    ) -> None:
        """Initialize the LifecycleCallbacks instance."""
        self.preamble: Callable[[], None] = preamble
        self.event_handler: Callable[[BaseEvent], None] = event_handler
        self.postamble: Callable[[], None] = postamble

    @classmethod
    def from_optionals(
        cls,
        preamble: object | None,
        event_handler: object | None,
        postamble: object | None,
    ) -> "LifecycleCallbacks":
        """Run from optionals and return the resulting value.

        This method encapsulates the main behavior for this operation."""
        resolved_preamble = preamble if callable(preamble) else _noop
        resolved_event_handler = event_handler if callable(event_handler) else _noop_event
        resolved_postamble = postamble if callable(postamble) else _noop
        return cls(
            resolved_preamble,
            resolved_event_handler,
            resolved_postamble,
        )
