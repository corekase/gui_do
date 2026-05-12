from __future__ import annotations

from ..events.gui_event import EventType


# Frozenset for O(1) pointer-event kind membership tests in the hot event path.
POINTER_EVENT_KINDS: frozenset = frozenset((
    EventType.MOUSE_BUTTON_DOWN,
    EventType.MOUSE_BUTTON_UP,
    EventType.MOUSE_MOTION,
    EventType.MOUSE_WHEEL,
))


# Frozenset for the three event kinds that require pointer logicalization.
LOGICALIZE_KINDS: frozenset = frozenset((
    EventType.MOUSE_MOTION,
    EventType.MOUSE_BUTTON_DOWN,
    EventType.MOUSE_BUTTON_UP,
))
