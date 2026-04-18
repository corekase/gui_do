from typing import Callable, Optional

from ..events import BaseEvent


def _noop() -> None:
    pass


def _noop_event(_: BaseEvent) -> None:
    pass


class ScreenLifecycle:
    """Owns screen-level lifecycle callbacks and event handler."""

    def __init__(self) -> None:
        self.preamble: Callable[[], None] = _noop
        self.event_handler: Callable[[BaseEvent], None] = _noop_event
        self.postamble: Callable[[], None] = _noop

    def set_lifecycle(
        self,
        preamble: Optional[Callable[[], None]],
        event_handler: Optional[Callable[[BaseEvent], None]],
        postamble: Optional[Callable[[], None]],
    ) -> None:
        self.preamble = preamble if preamble is not None else _noop
        self.event_handler = event_handler if event_handler is not None else _noop_event
        self.postamble = postamble if postamble is not None else _noop

    def run_preamble(self) -> None:
        self.preamble()

    def run_postamble(self) -> None:
        self.postamble()

    def handle_event(self, event: BaseEvent) -> None:
        self.event_handler(event)
