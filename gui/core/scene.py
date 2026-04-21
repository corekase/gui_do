import pygame

from typing import List

from .ui_node import UiNode


class Scene:
    """Top-level scene graph container."""

    def __init__(self) -> None:
        self.nodes: List[UiNode] = []

    def add(self, node: UiNode) -> UiNode:
        self.nodes.append(node)
        return node

    def update(self, dt_seconds: float) -> None:
        for node in self.nodes:
            if node.visible:
                node.update(dt_seconds)

    def _is_window_like(self, node) -> bool:
        return hasattr(node, "title_bar_rect") and hasattr(node, "lower_widget_rect") and hasattr(node, "move_by")

    def _is_task_panel(self, node) -> bool:
        return getattr(node, "control_id", None) == "task_panel"

    def _window_nodes(self) -> List[UiNode]:
        windows: List[UiNode] = []
        for node in self.nodes:
            children = getattr(node, "children", None)
            if not children:
                continue
            for child in children:
                if self._is_window_like(child):
                    windows.append(child)
        return windows

    def _point_in_task_panel(self, pos) -> bool:
        for node in self.nodes:
            if self._is_task_panel(node) and node.visible and node.enabled and node.rect.collidepoint(pos):
                return True
        return False

    def _point_in_window(self, pos) -> bool:
        for window in reversed(self._window_nodes()):
            if window.visible and window.enabled and window.rect.collidepoint(pos):
                return True
        return False

    def _clear_active_windows(self) -> None:
        for node in self.nodes:
            clear_method = getattr(node, "_clear_active_windows", None)
            if callable(clear_method):
                clear_method()

    def dispatch(self, event, app) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and getattr(event, "button", None) == 1:
            pos = getattr(event, "pos", None)
            if isinstance(pos, tuple) and len(pos) == 2:
                if not self._point_in_task_panel(pos) and not self._point_in_window(pos):
                    self._clear_active_windows()
        for node in reversed(self.nodes):
            if node.visible and node.enabled and node.handle_event(event, app):
                return True
        return False

    def draw(self, surface, theme) -> None:
        for node in self.nodes:
            if node.visible:
                node.draw(surface, theme)
