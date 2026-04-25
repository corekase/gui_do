from __future__ import annotations

from typing import Optional, TYPE_CHECKING

import pygame

from .focus_hint_constants import FOCUS_TRAVERSAL_HINT_TIMEOUT_SECONDS



class FocusManager:
    """Tracks keyboard focus independently from window activation.

    Optionally displays a visual focus indicator via an attached FocusVisualizer.
    """

    def __init__(self) -> None:
        self._focused_node = None
        self._hint_visible = False
        self._hint_elapsed_seconds = 0.0
        self._continuous_tab_cycle = False
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

    def set_focus(self, node, *, via_keyboard: bool = False) -> None:
        previous = self._focused_node
        if previous is node:
            if node is None:
                self._hint_visible = False
                self._hint_elapsed_seconds = 0.0
                self._continuous_tab_cycle = False
            elif via_keyboard:
                self._hint_visible = True
                self._hint_elapsed_seconds = 0.0
            return
        if previous is not None:
            previous._set_focused(False)
        self._focused_node = node
        self._hint_visible = bool(node is not None and via_keyboard)
        self._hint_elapsed_seconds = 0.0
        if not via_keyboard:
            self._continuous_tab_cycle = False
        if node is not None:
            node._set_focused(True)
            scope_key = self._scope_key_for_window(self._find_ancestor_window(node))
            self._scope_focus_memory[scope_key] = node

    def show_keyboard_hint_for_current_focus(self) -> None:
        """Expose hint for existing focus due to keyboard interaction."""
        if self._focused_node is not None:
            self._hint_visible = True
            self._hint_elapsed_seconds = 0.0

    def should_draw_focus_hint(self) -> bool:
        """Return whether the visual focus hint should currently be rendered."""
        return bool(self._hint_visible and self._focused_node is not None)

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

    def _preferred_scope_entry_target(self, *, _scene, window, candidates):
        """Pick the initial focus target when entering a scope.

        For window scope: prefer remembered target, else first candidate.
        For screen scope: prefer remembered target, else first candidate.
        """
        remembered = self._remembered_focus_for_scope(window=window, candidates=candidates)
        return remembered if remembered is not None else candidates[0]

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
        # Any routed keyboard event re-arms the hint display and resets continuous-cycle
        # mode so the next Tab applies the initiation gate (show hint before cycling).
        # Modifier-only keys (Shift, Ctrl, Alt, Meta) are excluded: they are pressed
        # before combinations such as Shift+Tab and must not pre-arm _hint_visible,
        # which would cause the subsequent Tab to skip the traversal-initiation gate.
        if not self._is_modifier_key_event(event):
            self._hint_visible = True
            self._hint_elapsed_seconds = 0.0
            self._continuous_tab_cycle = False
        if self._try_activate_focused_button(event, app, target):
            return True
        self._try_arm_focused_control_for_adjustment_event(event, target)
        return bool(target.handle_event(event, app))

    def update(self, dt_seconds: float) -> None:
        """Advance focus-driven cosmetic states."""
        if dt_seconds <= 0.0:
            return

        if self._hint_visible:
            self._hint_elapsed_seconds += float(dt_seconds)
            if self._hint_elapsed_seconds >= FOCUS_TRAVERSAL_HINT_TIMEOUT_SECONDS:
                self._hint_visible = False

        if self._armed_focus_target is None:
            return

        self._armed_focus_elapsed_seconds += float(dt_seconds)
        if self._armed_focus_elapsed_seconds < FOCUS_TRAVERSAL_HINT_TIMEOUT_SECONDS:
            return

        target = self._armed_focus_target
        self._armed_focus_target = None
        self._armed_focus_elapsed_seconds = 0.0
        target.end_focus_activation_visual()

    def _try_activate_focused_button(self, event, app, target) -> bool:
        """Handle focused keyboard activation for push buttons in one place.

        Activation still occurs exactly once here. The control activation fires first,
        then the armed state (visual-only) is started and held for the shared
        focus-hint timeout.
        """
        if not (event.is_key_down(pygame.K_RETURN) or event.is_key_down(pygame.K_SPACE)):
            return False

        target._invoke_click()
        self._begin_focus_activation_visual(target)
        return True

    def _begin_focus_activation_visual(self, target) -> None:
        if self._armed_focus_target is not None and self._armed_focus_target is not target:
            previous = self._armed_focus_target
            previous.end_focus_activation_visual()
        self._armed_focus_target = target
        self._armed_focus_elapsed_seconds = 0.0
        target.begin_focus_activation_visual()

    def _try_arm_focused_control_for_adjustment_event(self, event, target) -> None:
        """Arm a focused control's activation visual for non-click adjustment keys.

        This is non-consuming: key handling still flows through to ``target.handle_event``.
        """
        if bool(target.should_arm_focus_activation_for_event(event)):
            self._begin_focus_activation_visual(target)

    @staticmethod
    def _is_modifier_key_event(event) -> bool:
        """Return True when the event's key is a bare modifier (Shift, Ctrl, Alt, Meta)."""
        key = getattr(event, "key", None)
        return key in (
            pygame.K_LSHIFT, pygame.K_RSHIFT,
            pygame.K_LCTRL, pygame.K_RCTRL,
            pygame.K_LALT, pygame.K_RALT,
            pygame.K_LGUI, pygame.K_RGUI,
        )

    @staticmethod
    def _is_descendant(node, ancestor) -> bool:
        current = node
        while current is not None:
            if current is ancestor:
                return True
            current = current.parent
        return False

    @staticmethod
    def _is_effectively_interactive(node) -> bool:
        """Return True when node and all ancestors are visible and enabled."""
        current = node
        while current is not None:
            if not current.visible or not current.enabled:
                return False
            current = current.parent
        return True

    def _focusable_nodes(self, scene, *, window=None) -> list:
        ordered = []
        for node in scene._walk_nodes():
            if not self._is_effectively_interactive(node) or not node.accepts_focus():
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

        if focused is None or focused not in candidates:
            target = self._preferred_scope_entry_target(_scene=scene, window=window, candidates=candidates)
            self.set_focus(target, via_keyboard=True)
            self._continuous_tab_cycle = False
            return True

        # Traversal initiation: with an existing focused node but no visible hint,
        # first Tab only reveals the hint. A follow-up Tab before timeout cycles.
        if not self._hint_visible:
            self.show_keyboard_hint_for_current_focus()
            return True

        current_index = candidates.index(focused)
        offset = 1 if forward else -1
        next_index = (current_index + offset) % len(candidates)
        next_node = candidates[next_index]
        self.set_focus(next_node, via_keyboard=True)
        self._continuous_tab_cycle = True
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
            node.reconcile_hover(wants_hover)

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
                self.set_focus(candidate)
                return
        self.set_focus(candidates[0])

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
