from typing import List, Optional
from typing import TYPE_CHECKING

from pygame import Rect

from ...events.gui_event import GuiEvent
from ..base.ui_node import UiNode

if TYPE_CHECKING:
    import pygame
    from ...app.gui_application import GuiApplication
    from ...theme.color_theme import ColorTheme
    from ..layout.constraint_layout import ConstraintLayout


class PanelControl(UiNode):
    """Container control that owns child controls."""

    def __init__(self, control_id: str, rect: Rect, draw_background: bool = True, constraints: "Optional[ConstraintLayout]" = None) -> None:
        super().__init__(control_id, rect)
        self.children: List[UiNode] = []
        self.draw_background = bool(draw_background)
        self.constraints: "Optional[ConstraintLayout]" = constraints
        self._visuals = None
        self._drag_window = None
        self._drag_last_pos = None
        self._pending_capture_release_owner_id = None
        self._visual_size = None

    def _is_window_like(self, child: UiNode) -> bool:
        return child.is_window()

    def _set_window_active_state(self, window: UiNode, is_active: bool) -> None:
        window.set_active(bool(is_active))

    def _top_window_at(self, pos) -> Optional[UiNode]:
        for child in reversed(self.children):
            if child.visible and child.enabled and self._is_window_like(child) and child.rect.collidepoint(pos):
                return child
        return None

    def _set_active_window(self, window: UiNode) -> None:
        is_valid_target = (
            window in self.children and self._is_window_like(window) and window.visible and window.enabled
        )
        target = window if is_valid_target else self._next_top_visible_window(excluding=window)
        if target is None:
            self._clear_active_windows()
            return
        for candidate in self.children:
            if self._is_window_like(candidate):
                self._set_window_active_state(candidate, candidate is target)

    def _clear_active_windows(self) -> None:
        for candidate in self.children:
            if self._is_window_like(candidate):
                self._set_window_active_state(candidate, False)

    def _next_top_visible_window(self, excluding: Optional[UiNode] = None) -> Optional[UiNode]:
        for child in reversed(self.children):
            if child is excluding:
                continue
            if child.visible and child.enabled and self._is_window_like(child):
                return child
        return None

    def _top_visible_window(self) -> Optional[UiNode]:
        for child in reversed(self.children):
            if child.visible and child.enabled and self._is_window_like(child):
                return child
        return None

    def _on_window_visibility_changed(self, window: UiNode, old_visible: bool, new_visible: bool) -> None:
        if old_visible == new_visible:
            return
        if new_visible:
            self._raise_window(window)
            if window.enabled:
                self._set_active_window(window)
            else:
                self._set_window_active_state(window, False)
                next_window = self._next_top_visible_window(excluding=window)
                if next_window is None:
                    self._clear_active_windows()
                else:
                    self._set_active_window(next_window)
            return
        if self._drag_window is window:
            self._pending_capture_release_owner_id = window.control_id
            self._drag_window = None
            self._drag_last_pos = None
        self._set_window_active_state(window, False)
        next_window = self._next_top_visible_window(excluding=window)
        if next_window is None:
            self._clear_active_windows()
            return
        self._set_active_window(next_window)

    def _on_window_enabled_changed(self, window: UiNode, old_enabled: bool, new_enabled: bool) -> None:
        if old_enabled == new_enabled:
            return
        if not window.visible:
            if self._drag_window is window:
                self._pending_capture_release_owner_id = window.control_id
                self._drag_window = None
                self._drag_last_pos = None
            self._set_window_active_state(window, False)
            return
        if not new_enabled:
            was_active = bool(window.active)
            if self._drag_window is window:
                self._pending_capture_release_owner_id = window.control_id
                self._drag_window = None
                self._drag_last_pos = None
            self._set_window_active_state(window, False)
            if not was_active:
                return
            next_window = self._next_top_visible_window(excluding=window)
            if next_window is None:
                self._clear_active_windows()
            else:
                self._set_active_window(next_window)
            return
        active_window = None
        for child in reversed(self.children):
            if child.visible and child.enabled and self._is_window_like(child) and child.active:
                active_window = child
                break
        if active_window is None:
            self._set_active_window(window)

    def _raise_window(self, window: UiNode) -> None:
        if window in self.children:
            self.children.remove(window)
            self.children.append(window)
        if window.visible and window.enabled:
            self._set_active_window(window)
            return
        active_window = self._top_visible_window()
        if active_window is None:
            self._clear_active_windows()
            return
        self._set_active_window(active_window)

    def _lower_window(self, window: UiNode) -> None:
        if window not in self.children:
            return
        self.children.remove(window)
        first_window_idx = None
        for idx, child in enumerate(self.children):
            if self._is_window_like(child):
                first_window_idx = idx
                break
        if first_window_idx is None:
            self.children.append(window)
        else:
            self.children.insert(first_window_idx, window)

        active_window = self._top_visible_window()
        if active_window is None:
            self._clear_active_windows()
            return
        self._set_active_window(active_window)

    def add(self, child: UiNode) -> UiNode:
        """Attach one child control and return it."""
        return self.add_child(child)

    def add_at(self, child: UiNode, rel_x: int = 0, rel_y: int = 0) -> UiNode:
        """Attach *child* at a position relative to this panel's top-left corner.

        The child's rect dimensions are preserved; only its position is adjusted
        so that ``(0, 0)`` maps to this panel's ``rect.topleft``.  This is the
        preferred way to add children whose layout is expressed in panel-local
        coordinates rather than screen-space coordinates.

        Example::

            overlay.add_at(label, rel_x=8, rel_y=6)
        """
        offset_x = int(rel_x)
        offset_y = int(rel_y)
        # Track panel-local offsets so these children stay anchored if the panel moves.
        setattr(child, "_panel_local_offset", (offset_x, offset_y))
        child.rect.left = self.rect.left + offset_x
        child.rect.top = self.rect.top + offset_y
        return self.add(child)

    def set_rect(self, rect: Rect) -> None:
        old_rect = Rect(self.rect)
        super().set_rect(rect)
        if self.rect.topleft == old_rect.topleft:
            return
        for child in self.children:
            local_offset = getattr(child, "_panel_local_offset", None)
            if (
                isinstance(local_offset, tuple)
                and len(local_offset) == 2
                and isinstance(local_offset[0], int)
                and isinstance(local_offset[1], int)
            ):
                child.rect.left = self.rect.left + local_offset[0]
                child.rect.top = self.rect.top + local_offset[1]

    @property
    def child_count(self) -> int:
        """Return the number of direct children."""
        return len(self.children)

    def has_child(self, child: UiNode) -> bool:
        """Return True when *child* is a direct child of this panel."""
        return child in self.children

    def window_count(self) -> int:
        """Return the number of direct children that are window-type nodes."""
        return sum(1 for c in self.children if self._is_window_like(c))

    def clear_children(self, *, dispose: bool = False) -> int:
        """Remove all direct children and return the count removed.

        Calls ``remove()`` for each child so that window management hooks
        (activation, drag-cancel) run correctly. Pass ``dispose=True`` to
        also call ``dispose()`` on every removed child.
        """
        count = 0
        for child in list(self.children):
            if self.remove(child, dispose=dispose):
                count += 1
        return count

    def remove(self, child: UiNode, *, dispose: bool = False) -> bool:
        if child not in self.children:
            return False

        was_window = self._is_window_like(child)
        was_active_window = bool(was_window and child.active)

        if self._drag_window is child:
            self._pending_capture_release_owner_id = child.control_id
            self._drag_window = None
            self._drag_last_pos = None

        if was_window:
            self._set_window_active_state(child, False)

        if not self.remove_child(child, dispose=dispose):
            return False

        if was_active_window:
            next_window = self._top_visible_window()
            if next_window is None:
                self._clear_active_windows()
            else:
                self._set_active_window(next_window)
        return True

    def set_constraints(self, constraints: "Optional[ConstraintLayout]") -> None:
        self.constraints = constraints
        if constraints is not None:
            constraints.apply(self.rect)

    def _reapply_constraints(self) -> None:
        if self.constraints is not None:
            self.constraints.apply(self.rect)

    def update(self, dt_seconds: float) -> None:
        self._reapply_constraints()
        for child in self.children:
            if child.visible:
                child.update(dt_seconds)

    def on_event_capture(self, event: GuiEvent, app: "GuiApplication", theme=None) -> bool:
        # Release pointer capture if needed
        if self._pending_capture_release_owner_id is not None:
            owner_id = self._pending_capture_release_owner_id
            if app.pointer_capture.is_owned_by(owner_id):
                app.pointer_capture.end(owner_id)
            self._pending_capture_release_owner_id = None

        # Cancel drag if window is no longer valid
        if self._drag_window is not None:
            invalid_drag_window = (
                self._drag_window not in self.children
                or not self._drag_window.visible
                or not self._drag_window.enabled
            )
            if invalid_drag_window:
                if app.pointer_capture.is_owned_by(self._drag_window.control_id):
                    app.pointer_capture.end(self._drag_window.control_id)
                self._drag_window = None
                self._drag_last_pos = None

        raw = event.pos

        # --- Handle window chrome events before children ---
        # Mouse motion: dragging window
        if event.is_mouse_motion() and self._drag_window is not None:
            rel = event.rel
            if isinstance(rel, tuple) and len(rel) == 2:
                dx, dy = int(rel[0]), int(rel[1])
            elif isinstance(raw, tuple) and len(raw) == 2 and self._drag_last_pos is not None:
                dx = int(raw[0] - self._drag_last_pos[0])
                dy = int(raw[1] - self._drag_last_pos[1])
            else:
                return False
            self._drag_window.move_by(dx, dy)
            self._drag_last_pos = raw
            event.prevent_default()
            event.stop_propagation()
            return True

        # Mouse up: end drag
        if event.is_mouse_up(1) and self._drag_window is not None:
            app.pointer_capture.end(self._drag_window.control_id)
            self._drag_window = None
            self._drag_last_pos = None
            event.prevent_default()
            event.stop_propagation()
            return True

        # Mouse down: check window chrome (titlebar/lower control)
        if event.is_mouse_down(1) and isinstance(raw, tuple) and len(raw) == 2:
            # Check all windows, topmost first
            for window in reversed(self.children):
                if not self._is_window_like(window) or not window.visible or not window.enabled:
                    continue
                if window.rect.collidepoint(raw):
                    self._set_active_window(window)
                    # Lower control
                    if window.lower_control_rect().collidepoint(raw):
                        self._lower_window(window)
                        new_top = self._top_visible_window()
                        if new_top is None:
                            self._clear_active_windows()
                        else:
                            self._set_active_window(new_top)
                        event.prevent_default()
                        event.stop_propagation()
                        return True
                    # Titlebar drag
                    if window.title_bar_rect().collidepoint(raw):
                        self._raise_window(window)
                        self._drag_window = window
                        self._drag_last_pos = raw
                        app.pointer_capture.begin(window.control_id, app.surface.get_rect())
                        event.prevent_default()
                        event.stop_propagation()
                        return True
                    # If click is in window but not chrome, raise window
                    self._raise_window(window)
                    break

        # --- End window chrome handling ---

        # Fallback: dispatch to children
        return self._dispatch_children(event, app, reverse=False, theme=theme)

    def handle_event(self, event: GuiEvent, app: "GuiApplication", theme=None) -> bool:
        return self._dispatch_children(event, app, reverse=True, theme=theme)

    def on_event_bubble(self, event: GuiEvent, app: "GuiApplication", theme=None) -> bool:
        return self._dispatch_children(event, app, reverse=True, theme=theme)

    def draw(self, surface: "pygame.Surface", theme: "ColorTheme") -> None:
        self.draw_screen_phase(surface, theme)
        self.draw_window_phase(surface, theme)

    def draw_screen_phase(self, surface: "pygame.Surface", theme: "ColorTheme") -> None:
        """Draw panel background and non-window children (screen lifecycle layer)."""
        if self.draw_background:
            factory = theme.graphics_factory
            visual_size = (self.rect.width, self.rect.height)
            if self._visuals is None or self._visual_size != visual_size:
                self._visuals = factory.build_frame_visuals(self.rect)
                self._visual_size = visual_size
            selected = factory.resolve_visual_state(
                self._visuals,
                visible=self.visible,
                enabled=self.enabled,
                armed=False,
                hovered=False,
            )
            surface.blit(selected, self.rect)
        for child in self.children:
            if self._is_window_like(child):
                continue
            if child.visible:
                child.draw(surface, theme)

    def draw_window_phase(self, surface: "pygame.Surface", theme: "ColorTheme", app: "GuiApplication | None" = None) -> None:
        """Draw window children (window lifecycle layer), optionally with per-window hints."""
        for child in self.children:
            if not self._is_window_like(child):
                continue
            if not child.visible:
                continue
            child.draw(surface, theme)
            if app is not None:
                app.focus_visualizer.draw_hint_for_window(surface, theme, child)
