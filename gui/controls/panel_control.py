from typing import List, Optional
from typing import TYPE_CHECKING

from pygame import Rect

from ..core.gui_event import GuiEvent
from ..core.ui_node import UiNode

if TYPE_CHECKING:
    import pygame
    from ..app.gui_application import GuiApplication
    from ..theme.color_theme import ColorTheme


class PanelControl(UiNode):
    """Container control that owns child controls."""

    def __init__(self, control_id: str, rect: Rect, draw_background: bool = True) -> None:
        super().__init__(control_id, rect)
        self.children: List[UiNode] = []
        self.draw_background = bool(draw_background)
        self._visuals = None
        self._drag_window = None
        self._drag_last_pos = None
        self._visual_size = None

    def _is_window_like(self, child: UiNode) -> bool:
        return child.is_window()

    def _window_children(self) -> List[UiNode]:
        windows: List[UiNode] = []
        for child in self.children:
            if child.visible and child.enabled and self._is_window_like(child):
                windows.append(child)
        return windows

    def _all_window_children(self) -> List[UiNode]:
        windows: List[UiNode] = []
        for child in self.children:
            if self._is_window_like(child):
                windows.append(child)
        return windows

    def _set_window_active_state(self, window: UiNode, is_active: bool) -> None:
        window.set_active(bool(is_active))

    def _top_window_at(self, pos) -> Optional[UiNode]:
        for child in reversed(self.children):
            if child.visible and child.enabled and self._is_window_like(child) and child.rect.collidepoint(pos):
                return child
        return None

    def _set_active_window(self, window: UiNode) -> None:
        for candidate in self._all_window_children():
            self._set_window_active_state(candidate, candidate is window)

    def _clear_active_windows(self) -> None:
        for candidate in self._all_window_children():
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
            self._set_active_window(window)
            return
        self._set_window_active_state(window, False)
        next_window = self._next_top_visible_window(excluding=window)
        if next_window is None:
            self._clear_active_windows()
            return
        self._set_active_window(next_window)

    def _raise_window(self, window: UiNode) -> None:
        if window in self.children:
            self.children.remove(window)
            self.children.append(window)

    def _lower_window(self, window: UiNode) -> None:
        if window not in self.children:
            return
        self.children.remove(window)
        window_indices = [idx for idx, child in enumerate(self.children) if self._is_window_like(child)]
        if not window_indices:
            self.children.append(window)
            return
        self.children.insert(window_indices[0], window)

    def add(self, child: UiNode) -> UiNode:
        """Attach one child control and return it."""
        child.parent = self
        self.children.append(child)
        if hasattr(child, "on_mount"):
            child.on_mount(self)
        if hasattr(child, "invalidate"):
            child.invalidate()
        return child

    def remove(self, child: UiNode, *, dispose: bool = False) -> bool:
        if child not in self.children:
            return False
        self.children.remove(child)
        child.parent = None
        if hasattr(child, "on_unmount"):
            child.on_unmount(self)
        if dispose:
            if hasattr(child, "dispose"):
                child.dispose()
        if hasattr(self, "invalidate"):
            self.invalidate()
        return True

    def update(self, dt_seconds: float) -> None:
        for child in self.children:
            if child.visible:
                child.update(dt_seconds)

    def handle_event(self, event: GuiEvent, app: "GuiApplication") -> bool:
        raw = event.pos

        if event.is_mouse_motion() and self._drag_window is not None:
            rel = event.rel
            if isinstance(rel, tuple) and len(rel) == 2:
                dx, dy = int(rel[0]), int(rel[1])
            elif isinstance(raw, tuple) and len(raw) == 2 and self._drag_last_pos is not None:
                dx = int(raw[0] - self._drag_last_pos[0])
                dy = int(raw[1] - self._drag_last_pos[1])
            else:
                dx, dy = 0, 0
            self._drag_window.move_by(dx, dy)
            if isinstance(raw, tuple) and len(raw) == 2:
                self._drag_last_pos = raw
            return True

        if event.is_mouse_up(1) and self._drag_window is not None:
            app.pointer_capture.end(self._drag_window.control_id)
            self._drag_window = None
            self._drag_last_pos = None
            return True

        if event.is_mouse_down(1) and isinstance(raw, tuple) and len(raw) == 2:
            window = self._top_window_at(raw)
            if window is not None:
                self._set_active_window(window)
                if window.lower_widget_rect().collidepoint(raw):
                    self._lower_window(window)
                    new_top = self._top_visible_window()
                    if new_top is None:
                        self._clear_active_windows()
                    else:
                        self._set_active_window(new_top)
                    return True
                self._raise_window(window)
                if window.title_bar_rect().collidepoint(raw):
                    self._drag_window = window
                    self._drag_last_pos = raw
                    app.pointer_capture.begin(window.control_id, app.surface.get_rect())
                    return True

        for child in reversed(self.children):
            if child.visible and child.enabled and child.handle_event(event, app):
                return True
        return False

    def draw(self, surface: "pygame.Surface", theme: "ColorTheme") -> None:
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
            if child.visible:
                child.draw(surface, theme)
