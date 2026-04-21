from __future__ import annotations

from typing import Callable, Optional

from .gui_event import EventType


class KeyboardManager:
    """Routes key events through focused window-first keyboard dispatch."""

    @classmethod
    def is_key_event(cls, event) -> bool:
        return event.kind in (EventType.KEY_DOWN, EventType.KEY_UP, EventType.TEXT_INPUT, EventType.TEXT_EDITING)

    def route_key_event(self, scene, event, app, screen_event_handler: Optional[Callable[[object], bool]] = None) -> bool:
        active_window = scene.active_window()
        if active_window is not None:
            # Focused windows own keyboard input; do not bubble key events to screen while focused.
            active_window.handle_event(event, app)
            return True
        if screen_event_handler is not None:
            return bool(screen_event_handler(event))
        return False
