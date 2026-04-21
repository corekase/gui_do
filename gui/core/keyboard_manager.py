from __future__ import annotations

from typing import Callable, Optional

import pygame

from .gui_event import EventType


class KeyboardManager:
    """Routes key events through focused window-first keyboard dispatch."""

    KEY_EVENT_TYPES = {
        pygame.KEYDOWN,
        pygame.KEYUP,
        pygame.TEXTINPUT,
        pygame.TEXTEDITING,
    }

    @classmethod
    def is_key_event(cls, event) -> bool:
        event_kind = getattr(event, "kind", None)
        if event_kind in (EventType.KEY_DOWN, EventType.KEY_UP, EventType.TEXT_INPUT, EventType.TEXT_EDITING):
            return True
        return getattr(event, "type", None) in cls.KEY_EVENT_TYPES

    @staticmethod
    def _is_window_like(node: object) -> bool:
        return hasattr(node, "title_bar_rect") and hasattr(node, "lower_widget_rect") and hasattr(node, "move_by")

    def _window_nodes(self, scene) -> list[object]:
        windows: list[object] = []
        stack = list(getattr(scene, "nodes", []))
        while stack:
            node = stack.pop(0)
            children = getattr(node, "children", None)
            if isinstance(children, list) and children:
                stack.extend(children)
            if self._is_window_like(node):
                windows.append(node)
        return windows

    def _active_window(self, scene) -> Optional[object]:
        windows = self._window_nodes(scene)
        for window in reversed(windows):
            if bool(getattr(window, "active", False)) and bool(getattr(window, "visible", False)) and bool(getattr(window, "enabled", False)):
                return window
        return None

    def route_key_event(self, scene, event, app, screen_event_handler: Optional[Callable[[object], bool]] = None) -> bool:
        active_window = self._active_window(scene)
        if active_window is not None and active_window.handle_event(event, app):
            return True
        if screen_event_handler is not None:
            return bool(screen_event_handler(event))
        return False
