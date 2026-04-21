from typing import List, Optional

import pygame
from pygame import Rect
from pygame.draw import rect as draw_rect

from ..core.ui_node import UiNode


class PanelControl(UiNode):
    """Container control that owns child controls."""

    def __init__(self, control_id: str, rect: Rect) -> None:
        super().__init__(control_id, rect)
        self.children: List[UiNode] = []
        self._visuals = None
        self._drag_window = None
        self._drag_last_pos = None

    def _is_window_like(self, child: UiNode) -> bool:
        return hasattr(child, "title_bar_rect") and hasattr(child, "lower_widget_rect") and hasattr(child, "move_by")

    def _window_children(self) -> List[UiNode]:
        windows: List[UiNode] = []
        for child in self.children:
            if child.visible and child.enabled and self._is_window_like(child):
                windows.append(child)
        return windows

    def _top_window_at(self, pos) -> Optional[UiNode]:
        for child in reversed(self.children):
            if child.visible and child.enabled and self._is_window_like(child) and child.rect.collidepoint(pos):
                return child
        return None

    def _set_active_window(self, window: UiNode) -> None:
        for candidate in self._window_children():
            candidate.active = candidate is window

    def _clear_active_windows(self) -> None:
        for candidate in self._window_children():
            candidate.active = False

    def _raise_window(self, window: UiNode) -> None:
        if window in self.children:
            self.children.remove(window)
            self.children.append(window)

    def _lower_window(self, window: UiNode) -> None:
        if window in self.children:
            self.children.remove(window)
            self.children.insert(0, window)

    def add(self, child: UiNode) -> UiNode:
        """Attach one child control and return it."""
        child.parent = self
        self.children.append(child)
        return child

    def update(self, dt_seconds: float) -> None:
        for child in self.children:
            if child.visible:
                child.update(dt_seconds)

    def handle_event(self, event, app) -> bool:
        event_type = getattr(event, "type", None)
        raw = getattr(event, "pos", None)
        button = getattr(event, "button", None)

        if event_type == pygame.MOUSEMOTION and self._drag_window is not None:
            rel = getattr(event, "rel", None)
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

        if event_type == pygame.MOUSEBUTTONUP and button == 1 and self._drag_window is not None:
            app.pointer_capture.end(self._drag_window.control_id)
            self._drag_window = None
            self._drag_last_pos = None
            return True

        if event_type == pygame.MOUSEBUTTONDOWN and button == 1 and isinstance(raw, tuple) and len(raw) == 2:
            window = self._top_window_at(raw)
            if window is None:
                self._clear_active_windows()
            else:
                self._set_active_window(window)
                if window.lower_widget_rect().collidepoint(raw):
                    self._lower_window(window)
                    new_top = self._top_window_at(raw)
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

    def draw(self, surface, theme) -> None:
        factory = getattr(theme, "graphics_factory", None)
        if factory is None:
            draw_rect(surface, theme.medium, self.rect, 0)
            draw_rect(surface, theme.dark, self.rect, 2)
        else:
            if self._visuals is None:
                self._visuals = factory.build_frame_visuals(self.rect)
            surface.blit(self._visuals.idle, self.rect)
        for child in self.children:
            if child.visible:
                child.draw(surface, theme)
