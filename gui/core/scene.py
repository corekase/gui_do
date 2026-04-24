from typing import Callable, List, Optional
from typing import TYPE_CHECKING

from .gui_event import EventPhase, GuiEvent
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
        node.parent = None
        node.on_mount(None)
        node.invalidate()
        return node

    def remove(self, node: UiNode, *, dispose: bool = False) -> bool:
        if node not in self.nodes:
            return False
        self.nodes.remove(node)
        node.on_unmount(None)
        if dispose:
            node.dispose()
        return True

    def update(self, dt_seconds: float) -> None:
        for node in self.nodes:
            if node.visible:
                node.update(dt_seconds)

    def _is_window_like(self, node: UiNode) -> bool:
        return node.is_window()

    def _is_task_panel(self, node: UiNode) -> bool:
        return node.is_task_panel()

    # --- Query helpers ---

    def find(self, control_id: str) -> "Optional[UiNode]":
        """Return the first node in BFS order whose ``control_id`` matches, or ``None``."""
        for node in self._walk_nodes():
            if node.control_id == control_id:
                return node
        return None

    def find_all(self, predicate: "Callable[[UiNode], bool]") -> "List[UiNode]":
        """Return all nodes in BFS order that satisfy *predicate*."""
        return [node for node in self._walk_nodes() if predicate(node)]

    def node_count(self) -> int:
        """Return the total number of nodes reachable from this scene (including descendants)."""
        return len(self._walk_nodes())

    # --- Internal traversal ---

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

    def top_window_at(self, pos) -> UiNode | None:
        if not (isinstance(pos, tuple) and len(pos) == 2):
            return None
        for window in reversed(self._window_nodes()):
            if window.visible and window.enabled and window.rect.collidepoint(pos):
                return window
        return None

    @staticmethod
    def _is_descendant_of(node: UiNode, ancestor: UiNode) -> bool:
        current = node
        while current is not None:
            if current is ancestor:
                return True
            current = current.parent
        return False

    @staticmethod
    def _is_effectively_interactive(node: UiNode) -> bool:
        """Return True when node and all ancestors are visible/enabled."""
        current = node
        while current is not None:
            if not current.visible or not current.enabled:
                return False
            current = current.parent
        return True

    def _clear_active_windows(self) -> None:
        for node in self.nodes:
            node._clear_active_windows()

    def dispatch(self, event: GuiEvent, app: "GuiApplication") -> bool:
        if event.is_mouse_down(1):
            pos = event.pos
            if isinstance(pos, tuple) and len(pos) == 2:
                if not self._point_in_task_panel(pos) and not self._point_in_window(pos):
                    self._clear_active_windows()
        capture_event = event.with_phase(EventPhase.CAPTURE)
        for node in self.nodes:
            if node.visible and node.enabled and self._dispatch_node_event(node, capture_event, app):
                return True
            if capture_event.propagation_stopped:
                return True

        target_event = event.with_phase(EventPhase.TARGET)
        for node in reversed(self.nodes):
            if node.visible and node.enabled and self._dispatch_node_event(node, target_event, app):
                return True
            if target_event.propagation_stopped:
                return True

        bubble_event = event.with_phase(EventPhase.BUBBLE)
        for node in self.nodes:
            if node.visible and node.enabled and self._dispatch_node_event(node, bubble_event, app):
                return True
            if bubble_event.propagation_stopped:
                return True
        return False

    @staticmethod
    def _dispatch_node_event(node: UiNode, event: GuiEvent, app: "GuiApplication") -> bool:
        return bool(node.handle_routed_event(event, app))

    def top_focus_target_at(self, pos) -> UiNode | None:
        if not (isinstance(pos, tuple) and len(pos) == 2):
            return None
        top_window = self.top_window_at(pos)
        for node in reversed(self._walk_nodes()):
            if top_window is not None and not self._is_descendant_of(node, top_window):
                continue
            if (
                self._is_effectively_interactive(node)
                and node.accepts_mouse_focus()
                and node.hit_test(pos)
            ):
                return node
        return None

    def draw(self, surface: "pygame.Surface", theme: "ColorTheme", app: "GuiApplication" | None = None) -> None:
        for node in self.nodes:
            if not node.visible:
                continue

            draw_screen_phase = getattr(node, "draw_screen_phase", None)
            draw_window_phase = getattr(node, "draw_window_phase", None)
            if app is not None and callable(draw_screen_phase) and callable(draw_window_phase):
                draw_screen_phase(surface, theme)
                app.focus_visualizer.draw_hint_for_scene_root(surface, theme, node)
                draw_window_phase(surface, theme, app=app)
                continue

            node.draw(surface, theme)
            if app is not None:
                app.focus_visualizer.draw_hint_for_scene_root(surface, theme, node)
