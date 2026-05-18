from typing import Callable, List, Optional
from typing import TYPE_CHECKING

from ..events.gui_event import EventPhase, GuiEvent
from ..controls.base.ui_node import UiNode
from ..theme.color_theme import ColorTheme

if TYPE_CHECKING:
    from typing import Generator
    import pygame
    from ..app.gui_application import GuiApplication


class Scene:
    """Top-level scene graph container."""

    def __init__(self) -> None:
        self.nodes: List[UiNode] = []
        self._invalidation_tracker = None
        self._window_query_dirty: bool = True
        self._cached_window_nodes: List[UiNode] = []
        self._cached_task_panel_nodes: List[UiNode] = []
        self._walk_nodes_dirty: bool = True
        self._cached_walk_nodes: List[UiNode] = []

    def _invalidate_window_query_cache(self) -> None:
        self._window_query_dirty = True
        self._cached_window_nodes = []
        self._cached_task_panel_nodes = []
        self._walk_nodes_dirty = True
        self._cached_walk_nodes = []

    def _window_query_nodes(self) -> tuple[List[UiNode], List[UiNode]]:
        if not self._window_query_dirty:
            return self._cached_window_nodes, self._cached_task_panel_nodes
        windows: List[UiNode] = []
        task_panels: List[UiNode] = []
        for node in self._walk_nodes():
            if self._is_window_like(node):
                windows.append(node)
            elif self._is_task_panel(node):
                task_panels.append(node)
        self._cached_window_nodes = windows
        self._cached_task_panel_nodes = task_panels
        self._window_query_dirty = False
        return windows, task_panels

    def set_invalidation_tracker(self, tracker) -> None:
        """Attach *tracker* to the scene and all currently registered nodes.

        Called by :class:`~gui_do.GuiApplication` when the scene becomes
        active.  Subsequent :meth:`add` calls propagate the tracker to new
        nodes automatically.
        """
        self._invalidation_tracker = tracker
        for node in self.nodes:
            node.set_invalidation_tracker(tracker)

    def add(self, node: UiNode) -> UiNode:
        self.nodes.append(node)
        node.parent = None
        if self._invalidation_tracker is not None:
            node.set_invalidation_tracker(self._invalidation_tracker)
        node.on_mount(None)
        node.invalidate()
        self._invalidate_window_query_cache()
        return node

    def remove(self, node: UiNode, *, dispose: bool = False) -> bool:
        try:
            self.nodes.remove(node)
        except ValueError:
            return False
        node.on_unmount(None)
        if dispose:
            node.dispose()
        self._invalidate_window_query_cache()
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

    def contains(self, node: UiNode) -> bool:
        """Return ``True`` when *node* is reachable from this scene graph."""
        current = node
        while current.parent is not None:
            current = current.parent
        return any(current is n for n in self.nodes)

    def node_count(self) -> int:
        """Return the total number of nodes reachable from this scene (including descendants)."""
        return sum(1 for _ in self._walk_nodes())

    # --- Internal traversal ---

    def _get_cached_bfs_walk(self) -> List[UiNode]:
        """Return cached list of all nodes in BFS order. Invalidated on add/remove.

        Provides O(1) read access to the full scene walk result, avoiding
        redundant generator iterations in per-frame revalidation loops.
        """
        if not self._walk_nodes_dirty:
            return self._cached_walk_nodes
        # List-with-index BFS avoids deque object overhead and popleft cost.
        queue: list = list(self.nodes)
        i = 0
        nodes: List[UiNode] = []
        while i < len(queue):
            node = queue[i]
            i += 1
            nodes.append(node)
            if node.children:
                queue.extend(node.children)
        self._cached_walk_nodes = nodes
        self._walk_nodes_dirty = False
        return nodes

    def _walk_nodes(self) -> "Generator[UiNode, None, None]":
        # Delegate to cached walk, yielding from the cached list.
        # Maintains generator interface for backward compatibility.
        for node in self._get_cached_bfs_walk():
            yield node

    def active_window(self) -> UiNode | None:
        windows, _task_panels = self._window_query_nodes()
        for node in reversed(windows):
            if node.active and node.visible and node.enabled:
                return node
        return None

    def _point_in_window(self, pos) -> bool:
        windows, _task_panels = self._window_query_nodes()
        for node in windows:
            if node.visible and node.enabled and node.rect.collidepoint(pos):
                return True
        return False

    def top_window_at(self, pos) -> UiNode | None:
        if not (isinstance(pos, tuple) and len(pos) == 2):
            return None
        windows, _task_panels = self._window_query_nodes()
        for node in reversed(windows):
            if node.visible and node.enabled and node.rect.collidepoint(pos):
                return node
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
        self._invalidate_window_query_cache()
        for node in self.nodes:
            node._clear_active_windows()

    def dispatch(self, event: GuiEvent, app: "GuiApplication", theme=None) -> bool:
        # Validate theme once at the scene level before any per-node dispatch.
        if getattr(theme, "fonts", None) is None:
            theme = ColorTheme()
        if event.is_mouse_down(1):
            pos = event.pos
            if isinstance(pos, tuple) and len(pos) == 2:
                # Single walk to check both task-panel and window hit; avoids two
                # separate BFS traversals (_point_in_task_panel + _point_in_window).
                hit_interactive = False
                windows, task_panels = self._window_query_nodes()
                for node in task_panels:
                    if node.visible and node.enabled and node.rect.collidepoint(pos):
                        hit_interactive = True
                        break
                if not hit_interactive:
                    for node in windows:
                        if node.visible and node.enabled and node.rect.collidepoint(pos):
                            hit_interactive = True
                            break
                if not hit_interactive:
                    self._clear_active_windows()
        capture_event = event.with_phase(EventPhase.CAPTURE)
        for node in self.nodes:
            if node.visible and node.enabled and self._dispatch_node_event(node, capture_event, app, theme=theme):
                return True
            if capture_event.propagation_stopped:
                return True

        target_event = event.with_phase(EventPhase.TARGET)
        for node in reversed(self.nodes):
            if node.visible and node.enabled and self._dispatch_node_event(node, target_event, app, theme=theme):
                return True
            if target_event.propagation_stopped:
                return True

        bubble_event = event.with_phase(EventPhase.BUBBLE)
        for node in self.nodes:
            if node.visible and node.enabled and self._dispatch_node_event(node, bubble_event, app, theme=theme):
                return True
            if bubble_event.propagation_stopped:
                return True
        return False

    @staticmethod
    def _dispatch_node_event(node: UiNode, event: GuiEvent, app: "GuiApplication", theme=None) -> bool:
        return bool(node.handle_routed_event(event, app, theme=theme))

    def top_focus_target_at(self, pos) -> UiNode | None:
        if not (isinstance(pos, tuple) and len(pos) == 2):
            return None
        _window, best = self._pointer_context_at_validated(pos)
        return best

    def _pointer_context_at_validated(self, pos, windows: List[UiNode] | None = None) -> tuple[UiNode | None, UiNode | None]:
        """Find (window_hit, best_focus_target) at pos. Accepts optional cached windows list.

        Args:
            pos: Mouse position tuple (x, y)
            windows: Optional pre-queried windows list to avoid redundant window query.
                     If None, windows are queried from scene.
        """
        if windows is None:
            windows, _task_panels = self._window_query_nodes()
        top_window = None
        for node in reversed(windows):
            if node.visible and node.enabled and node.rect.collidepoint(pos):
                top_window = node
                break
        best: UiNode | None = None
        walk_nodes = self._get_cached_bfs_walk()  # Use cached walk instead of generator
        # The previous forward scan kept the last matching node as `best`.
        # Reversed iteration with first-match break is equivalent and avoids
        # evaluating the remainder once the top-most focus target is found.
        for node in reversed(walk_nodes):
            if not (node.visible and node.enabled):
                continue
            if (
                self._is_effectively_interactive(node)
                and node.accepts_mouse_focus()
                and node.hit_test(pos)
                and (top_window is None or self._is_descendant_of(node, top_window))
            ):
                best = node
                break
        return top_window, best

    def pointer_context_at(self, pos, windows: List[UiNode] | None = None) -> tuple[bool, UiNode | None]:
        """Return ``(window_hit, focus_target)`` for one pointer position in one pass.

        Args:
            pos: Mouse position tuple (x, y)
            windows: Optional pre-queried windows list for efficiency.
        """
        if not (isinstance(pos, tuple) and len(pos) == 2):
            return (False, None)
        top_window, best = self._pointer_context_at_validated(pos, windows=windows)
        return (top_window is not None, best)

    def draw(self, surface: "pygame.Surface", theme: "ColorTheme", app: "GuiApplication | None" = None) -> None:
        # Draw all non-focused nodes first, then draw focused node last to ensure it's on top.
        focused_node = None
        if app is not None:
            focused_node = app.focus.focused_node
            if focused_node is not None and not self.contains(focused_node):
                focused_node = None
            # Scene-level reordering must only operate on scene-root nodes.
            # Descendants are rendered by their owning root/container and must
            # not be drawn again as top-level nodes.
            elif focused_node is not None and focused_node not in self.nodes:
                focused_node = None

        for node in self.nodes:
            if not node.visible:
                continue

            # Skip the focused node for now; we'll draw it last
            if node is focused_node:
                continue

            node.draw_screen_phase(surface, theme, app=app)
            if app is not None:
                app.focus_visualizer.draw_hint_for_scene_root(surface, theme, node)
            node.draw_window_phase(surface, theme, app=app)

        # Draw focused node last so it appears on top
        if focused_node is not None and focused_node.visible:
            focused_node.draw_screen_phase(surface, theme, app=app)
            if app is not None:
                app.focus_visualizer.draw_hint_for_scene_root(surface, theme, focused_node)
            focused_node.draw_window_phase(surface, theme, app=app)

        # Window focus hint (Ctrl+Tab cycling) is drawn after all windows so
        # it sits on top of window content and chrome.
        if app is not None:
            app.focus_visualizer.draw_window_focus_hint(surface, theme)
