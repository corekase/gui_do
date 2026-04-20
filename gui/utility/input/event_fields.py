from __future__ import annotations

from pygame.event import Event as PygameEvent
from typing import Optional, Tuple


def event_button(event: PygameEvent) -> Optional[int]:
    """Return mouse button value when present and integer-typed."""
    value = getattr(event, 'button', None)
    return value if isinstance(value, int) else None


def event_key(event: PygameEvent) -> Optional[int]:
    """Return key value when present and integer-typed."""
    value = getattr(event, 'key', None)
    return value if isinstance(value, int) else None


def event_pos(event: PygameEvent) -> Optional[Tuple[int, int]]:
    """Return normalized event screen position when available."""
    value = getattr(event, 'pos', None)
    if not isinstance(value, tuple) or len(value) != 2:
        return None
    x, y = value
    if not isinstance(x, int) or not isinstance(y, int):
        return None
    return (x, y)


def event_rel(event: PygameEvent) -> Tuple[int, int]:
    """Return normalized relative motion delta."""
    value = getattr(event, 'rel', (0, 0))
    if not isinstance(value, tuple) or len(value) != 2:
        return (0, 0)
    dx, dy = value
    if not isinstance(dx, int) or not isinstance(dy, int):
        return (0, 0)
    return (dx, dy)


def event_wheel_delta(event: PygameEvent) -> int:
    """Return normalized wheel delta, defaulting to zero."""
    value = getattr(event, 'y', 0)
    if isinstance(value, bool):
        return 0
    if isinstance(value, int):
        return value
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
