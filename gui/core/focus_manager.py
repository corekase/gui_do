from __future__ import annotations

from typing import Iterable, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .focus_visualizer import FocusVisualizer


class FocusManager:
    """Tracks keyboard focus independently from window activation.

    Optionally displays a visual focus indicator via an attached FocusVisualizer.
    """

    def __init__(self, visualizer: Optional["FocusVisualizer"] = None) -> None:
        self._focused_node = None
        self._visualizer = visualizer

    @property
    def focused_node(self):
        return self._focused_node

    @property
    def focused_control_id(self) -> Optional[str]:
        """Return the ``control_id`` of the currently focused node, or ``None``."""
        if self._focused_node is None:
            return None
        return getattr(self._focused_node, "control_id", None)

    def clear_focus(self) -> None:
        self.set_focus(None)

    def set_focus(self, node, show_hint: bool = True) -> None:
        previous = self._focused_node
        if previous is node:
            return
        if previous is not None:
            previous._set_focused(False)
        self._focused_node = node
        if node is not None:
            node._set_focused(True)
        # Trigger visual focus indicator
        if self._visualizer is not None:
            if node is not None:
                self._visualizer.set_focus_hint(node, show_hint=show_hint)
            else:
                self._visualizer.clear_focus_hint()

    def set_focus_by_id(self, scene, control_id: str) -> bool:
        """Find the first focusable node with *control_id* in *scene* and focus it.

        Returns ``True`` when a matching focusable node was found and focused,
        ``False`` otherwise (missing, hidden, disabled, or non-focusable).
        """
        for node in scene._walk_nodes():
            if getattr(node, "control_id", None) != control_id:
                continue
            if not node.visible or not node.enabled or not node.accepts_focus():
                return False
            self.set_focus(node)
            return True
        return False

    def route_key_event(self, event, app) -> bool:
        target = self._focused_node
        if target is None:
            return False
        if target not in app.scene._walk_nodes():
            self.clear_focus()
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
        if focused is None:
            # Keep focus unset for reverse traversal until focus is explicitly established.
            if not forward:
                return False
            self.set_focus(candidates[0])
            return True
        if focused not in candidates:
            next_index = 0 if forward else (len(candidates) - 1)
            self.set_focus(candidates[next_index])
            return True

        current_index = candidates.index(focused)
        offset = 1 if forward else -1
        next_index = (current_index + offset) % len(candidates)
        self.set_focus(candidates[next_index])
        return True

    def revalidate_focus(self, scene) -> None:
        """If the focused node is no longer focusable, move to the nearest valid node or clear.

        Searches within the same enclosing window as the previously focused node first.
        Focus is moved without showing the keyboard hint (it is an automatic transition).
        """
        focused = self._focused_node
        if focused is None:
            return
        if focused.visible and focused.enabled and focused.accepts_focus():
            return  # still valid, nothing to do

        window = self._find_ancestor_window(focused)
        candidates = self._focusable_nodes(scene, window=window)

        if not candidates:
            self.clear_focus()
            return

        focused_tab = getattr(focused, "tab_index", -1)
        for candidate in candidates:
            if candidate.tab_index >= focused_tab:
                self.set_focus(candidate, show_hint=False)
                return
        self.set_focus(candidates[0], show_hint=False)

    @staticmethod
    def _find_ancestor_window(node) -> "object | None":
        """Walk ancestors to find the nearest enclosing WindowControl, or None."""
        current = node.parent
        while current is not None:
            if hasattr(current, "titlebar_height"):
                return current
            current = current.parent
        return None

    @property
    def has_focus(self) -> bool:
        return self._focused_node is not None

    def focusable_count(self, scene, *, window=None) -> int:
        """Return the number of focusable nodes in *scene*, optionally scoped to *window*."""
        return len(self._focusable_nodes(scene, window=window))
