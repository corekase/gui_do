from __future__ import annotations

from typing import Optional, TYPE_CHECKING

import pygame

from .focus_hint_constants import FOCUS_TRAVERSAL_HINT_TIMEOUT_SECONDS

if TYPE_CHECKING:
    from .focus_visualizer import FocusVisualizer


class FocusManager:
    """Tracks keyboard focus independently from window activation.

    Optionally displays a visual focus indicator via an attached FocusVisualizer.
    """

    def __init__(self, visualizer: Optional["FocusVisualizer"] = None) -> None:
        self._focused_node = None
        self._visualizer = visualizer
        self._armed_focus_target = None
        self._armed_focus_elapsed_seconds = 0.0
        self._scope_focus_memory = {"__screen__": None}

    @property
    def focused_node(self):
        return self._focused_node

    @property
    def focused_control_id(self) -> Optional[str]:
        """Return the ``control_id`` of the currently focused node, or ``None``."""
        if self._focused_node is None:
            return None
        return self._focused_node.control_id

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
            scope_key = self._scope_key_for_window(self._find_ancestor_window(node))
            self._scope_focus_memory[scope_key] = node
        # Trigger visual focus indicator
        if self._visualizer is not None:
            if node is not None:
                self._visualizer.set_focus_hint(node, show_hint=show_hint)
            else:
                self._visualizer.clear_focus_hint()

    @staticmethod
    def _scope_key_for_window(window) -> object:
        return "__screen__" if window is None else window

    def _remembered_focus_for_scope(self, *, window, candidates):
        scope_key = self._scope_key_for_window(window)
        remembered = self._scope_focus_memory.get(scope_key)
        if remembered is None:
            return None
        if remembered in candidates:
            return remembered
        self._scope_focus_memory[scope_key] = None
        return None

    @staticmethod
    def _is_screen_scope_target_occluded_by_window(node, scene) -> bool:
        """Return True when a screen-scope node is covered by any visible enabled window."""
        if scene is None:
            return False
        owner_window = FocusManager._find_ancestor_window(node)
        if owner_window is not None:
            return False
        windows_provider = getattr(scene, "_window_nodes", None)
        if windows_provider is None:
            return False
        for window in windows_provider():
            if not (window.visible and window.enabled):
                continue
            if window.rect.colliderect(node.rect):
                return True
        return False

    def _preferred_scope_entry_target(self, *, scene, window, candidates):
        """Pick the initial focus target when entering a scope.

        Prefers remembered targets when they are usable and visually reachable.
        For screen scope, falls back to the first non-occluded candidate so the
        focus hint can be seen after scope re-entry.
        """
        remembered = self._remembered_focus_for_scope(window=window, candidates=candidates)
        if remembered is not None:
            if window is not None or not self._is_screen_scope_target_occluded_by_window(remembered, scene):
                return remembered

        if window is None:
            for candidate in candidates:
                if not self._is_screen_scope_target_occluded_by_window(candidate, scene):
                    return candidate

        return candidates[0]

    def set_focus_by_id(self, scene, control_id: str) -> bool:
        """Find the first focusable node with *control_id* in *scene* and focus it.

        Returns ``True`` when a matching focusable node was found and focused,
        ``False`` otherwise (missing, hidden, disabled, or non-focusable).
        """
        for node in scene._walk_nodes():
            if node.control_id != control_id:
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
        if not self._is_focus_window_context_valid(target):
            self.clear_focus()
            return False
        if self._try_activate_focused_button(event, app, target):
            return True
        return bool(target.handle_event(event, app))

    def update(self, dt_seconds: float) -> None:
        """Advance focus-driven cosmetic states."""
        if self._armed_focus_target is None:
            return
        if dt_seconds <= 0.0:
            return

        self._armed_focus_elapsed_seconds += float(dt_seconds)
        if self._armed_focus_elapsed_seconds < FOCUS_TRAVERSAL_HINT_TIMEOUT_SECONDS:
            return

        target = self._armed_focus_target
        self._armed_focus_target = None
        self._armed_focus_elapsed_seconds = 0.0
        if hasattr(target, "end_focus_activation_visual"):
            target.end_focus_activation_visual()

    def _try_activate_focused_button(self, event, app, target) -> bool:
        """Handle focused keyboard activation for push buttons in one place.

        Activation still occurs exactly once here. The armed state is visual-only and
        held for the shared focus-hint timeout.
        """
        if not (event.is_key_down(pygame.K_RETURN) or event.is_key_down(pygame.K_SPACE)):
            return False
        if not hasattr(target, "begin_focus_activation_visual"):
            return False
        if not hasattr(target, "_invoke_click"):
            return False

        if getattr(app, "focus_visualizer", None) is not None:
            app.focus_visualizer.refresh_focus_hint(target)
        self._begin_focus_activation_visual(target)
        target._invoke_click()
        return True

    def _begin_focus_activation_visual(self, target) -> None:
        if self._armed_focus_target is not None and self._armed_focus_target is not target:
            previous = self._armed_focus_target
            if hasattr(previous, "end_focus_activation_visual"):
                previous.end_focus_activation_visual()
        self._armed_focus_target = target
        self._armed_focus_elapsed_seconds = 0.0
        target.begin_focus_activation_visual()

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
            if not self._is_focus_window_context_valid(node):
                continue
            if window is not None and not self._is_descendant(node, window):
                continue
            ordered.append(node)
        ordered.sort(key=lambda node: (node.tab_index, node.control_id))
        return ordered

    def cycle_focus(self, scene, *, forward: bool = True, window=None, pointer_pos=None) -> bool:
        focused = self._focused_node
        if focused is not None and not self._is_focus_window_context_valid(focused):
            self.clear_focus()

        self._reconcile_hover_state(scene, pointer_pos=pointer_pos, window=window)

        candidates = self._focusable_nodes(scene, window=window)
        if not candidates:
            self.clear_focus()
            return False

        focused = self._focused_node
        hint_active = self._visualizer is not None and self._visualizer.has_active_hint()

        # When the graphical hint is not active, establish/refresh the current focus context.
        # This consumes the cycle key without advancing focus, so the next cycle event can move.
        if not hint_active:
            if focused is None or focused not in candidates:
                target = self._preferred_scope_entry_target(scene=scene, window=window, candidates=candidates)
                self.set_focus(target, show_hint=True)
                return True
            if self._visualizer is not None:
                self._visualizer.refresh_focus_hint(focused)
            return True

        # Hint is active: cycle to the next/previous focus target.
        if focused is None or focused not in candidates:
            target = self._preferred_scope_entry_target(scene=scene, window=window, candidates=candidates)
            self.set_focus(target, show_hint=True)
            return True

        current_index = candidates.index(focused)
        offset = 1 if forward else -1
        next_index = (current_index + offset) % len(candidates)
        next_node = candidates[next_index]
        if next_node is focused:
            if self._visualizer is not None:
                self._visualizer.refresh_focus_hint(next_node)
            return True
        self.set_focus(next_node, show_hint=True)
        return True

    def _reconcile_hover_state(self, scene, *, pointer_pos, window=None) -> None:
        """Normalize hover flags against the latest pointer position during traversal."""
        if not (isinstance(pointer_pos, tuple) and len(pointer_pos) == 2):
            return
        x = int(pointer_pos[0])
        y = int(pointer_pos[1])
        probe = (x, y)

        for node in scene._walk_nodes():
            if window is not None and not self._is_descendant(node, window):
                continue

            wants_hover = bool(node.visible and node.enabled and node.rect.collidepoint(probe))

            if hasattr(node, "hovered"):
                current = bool(getattr(node, "hovered"))
                if current != wants_hover:
                    setattr(node, "hovered", wants_hover)
                    node.invalidate()

            if hasattr(node, "_hovered"):
                current_private = bool(getattr(node, "_hovered"))
                if current_private != wants_hover:
                    setattr(node, "_hovered", wants_hover)
                    node.invalidate()

    def revalidate_focus(self, scene) -> None:
        """If the focused node is no longer focusable, move to the nearest valid node or clear.

        Searches within the same enclosing window as the previously focused node first.
        Focus is moved without showing the keyboard hint (it is an automatic transition).
        """
        focused = self._focused_node
        if focused is None:
            return
        if not self._is_focus_window_context_valid(focused):
            self.clear_focus()
            return
        if focused.visible and focused.enabled and focused.accepts_focus():
            return  # still valid, nothing to do

        window = self._find_ancestor_window(focused)
        candidates = self._focusable_nodes(scene, window=window)

        if not candidates:
            self.clear_focus()
            return

        focused_tab = focused.tab_index
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
            if current.is_window():
                return current
            current = current.parent
        return None

    def _is_focus_window_context_valid(self, node) -> bool:
        """Return whether *node* is eligible for focus given ancestor window state."""
        window = self._find_ancestor_window(node)
        if window is None:
            return True
        return bool(window.visible and window.enabled and window.active)

    @property
    def has_focus(self) -> bool:
        return self._focused_node is not None

    def focusable_count(self, scene, *, window=None) -> int:
        """Return the number of focusable nodes in *scene*, optionally scoped to *window*."""
        return len(self._focusable_nodes(scene, window=window))
