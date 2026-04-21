from __future__ import annotations

from typing import Optional


class FocusManager:
    """Tracks keyboard focus independently from window activation."""

    def __init__(self) -> None:
        self._focused_node = None

    @property
    def focused_node(self):
        return self._focused_node

    def clear_focus(self) -> None:
        self.set_focus(None)

    def set_focus(self, node) -> None:
        previous = self._focused_node
        if previous is node:
            return
        if previous is not None:
            previous._set_focused(False)
        self._focused_node = node
        if node is not None:
            node._set_focused(True)

    def route_key_event(self, event, app) -> bool:
        target = self._focused_node
        if target is None:
            return False
        if not target.visible or not target.enabled:
            self.clear_focus()
            return False
        return bool(target.handle_event(event, app))
