from typing import List
from typing import TYPE_CHECKING

from .gui_event import GuiEvent
from .ui_node import UiNode

if TYPE_CHECKING:
    import pygame
    from ..app.gui_application import GuiApplication
    from ..theme.color_theme import ColorTheme


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

    def _is_window_like(self, node: UiNode) -> bool:
        return node.is_window()

    def _is_task_panel(self, node: UiNode) -> bool:
        return node.is_task_panel()

    def _walk_nodes(self) -> List[UiNode]:
        stack = list(self.nodes)
        ordered: List[UiNode] = []
        while stack:
            node = stack.pop(0)
            ordered.append(node)
            stack.extend(node.children)
        return ordered

    def _window_nodes(self) -> List[UiNode]:
        return [node for node in self._walk_nodes() if self._is_window_like(node)]

    def active_window(self) -> UiNode | None:
        for window in reversed(self._window_nodes()):
            if window.active and window.visible and window.enabled:
                return window
        return None

    def _point_in_task_panel(self, pos) -> bool:
        for node in self._walk_nodes():
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
            node._clear_active_windows()

    def dispatch(self, event: GuiEvent, app: "GuiApplication") -> bool:
        if event.is_mouse_down(1):
            pos = event.pos
            if isinstance(pos, tuple) and len(pos) == 2:
                if not self._point_in_task_panel(pos) and not self._point_in_window(pos):
                    self._clear_active_windows()
        for node in reversed(self.nodes):
            if node.visible and node.enabled and node.handle_event(event, app):
                return True
        return False

    def draw(self, surface: "pygame.Surface", theme: "ColorTheme") -> None:
        for node in self.nodes:
            if node.visible:
                node.draw(surface, theme)
