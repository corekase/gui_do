from __future__ import annotations

from dataclasses import dataclass
from pygame.event import Event as PygameEvent
from pygame.locals import MOUSEBUTTONDOWN, MOUSEBUTTONUP
from typing import Optional, Tuple

from .event_fields import event_button, event_key, event_pos, event_rel, event_wheel_delta


_NORMALIZED_EVENT_CACHE_ATTR = '_gui_do_normalized_event'


@dataclass(frozen=True)
class NormalizedInputEvent:
    """Normalized view of one raw pygame event payload."""

    type: int
    button: Optional[int]
    key: Optional[int]
    pos: Optional[Tuple[int, int]]
    rel: Tuple[int, int]
    wheel_delta: int

    @property
    def is_left_down(self) -> bool:
        """Return whether this event is a left-button down event."""
        return self.type == MOUSEBUTTONDOWN and self.button == 1

    @property
    def is_left_up(self) -> bool:
        """Return whether this event is a left-button up event."""
        return self.type == MOUSEBUTTONUP and self.button == 1


def normalize_input_event(event: PygameEvent) -> NormalizedInputEvent:
    """Normalize raw event fields into a stable typed structure."""
    cached = getattr(event, _NORMALIZED_EVENT_CACHE_ATTR, None)
    if isinstance(cached, NormalizedInputEvent):
        return cached
    normalized = NormalizedInputEvent(
        type=event.type,
        button=event_button(event),
        key=event_key(event),
        pos=event_pos(event),
        rel=event_rel(event),
        wheel_delta=event_wheel_delta(event),
    )
    try:
        setattr(event, _NORMALIZED_EVENT_CACHE_ATTR, normalized)
    except Exception:
        # Some event implementations may disallow custom attributes.
        pass
    return normalized
