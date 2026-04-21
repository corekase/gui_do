from __future__ import annotations

from typing import Iterable


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

    @staticmethod
    def _is_descendant(node, ancestor) -> bool:
        current = node
        while current is not None:
            if current is ancestor:
                return True
            current = current.parent
        return False

    def _focusable_nodes(self, scene, *, window=None) -> list:
        ordered = []
        for node in scene._walk_nodes():
            if not node.visible or not node.enabled or not node.accepts_focus():
                continue
            if window is not None and not self._is_descendant(node, window):
                continue
            ordered.append(node)
        ordered.sort(key=lambda node: (node.tab_index, node.control_id))
        return ordered

    def cycle_focus(self, scene, *, forward: bool = True, window=None) -> bool:
        candidates = self._focusable_nodes(scene, window=window)
        if not candidates:
            self.clear_focus()
            return False

        focused = self._focused_node
        if focused not in candidates:
            next_index = 0 if forward else (len(candidates) - 1)
            self.set_focus(candidates[next_index])
            return True

        current_index = candidates.index(focused)
        offset = 1 if forward else -1
        next_index = (current_index + offset) % len(candidates)
        self.set_focus(candidates[next_index])
        return True
