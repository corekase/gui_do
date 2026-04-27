from collections import deque
from typing import Callable, List, Optional
from typing import TYPE_CHECKING

from pygame import Rect

from .gui_event import EventPhase, GuiEvent

if TYPE_CHECKING:
    import pygame
    from ..app.gui_application import GuiApplication
    from ..theme.color_theme import ColorTheme


class UiNode:
    """Base node for all controls in the package."""

    def __init__(self, control_id: str, rect: Rect) -> None:
        self.control_id = control_id
        self.rect = Rect(rect)
        self._enabled = True
        self._visible = True
        self._focused = False
        self.parent: Optional["UiNode"] = None
        self.children: list["UiNode"] = []
        self.accessibility_role = "widget"
        self.accessibility_label: Optional[str] = None
        self.tab_index = -1
        self._disposed = False
        self._dirty = True

    @property
    def visible(self) -> bool:
        return self._visible

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        previous = self._enabled
        self._enabled = bool(value)
        if previous != self._enabled:
            self._on_enabled_changed(previous, self._enabled)

    @visible.setter
    def visible(self, value: bool) -> None:
        previous = self._visible
        self._visible = bool(value)
        if previous != self._visible:
            self._on_visibility_changed(previous, self._visible)

    def _on_visibility_changed(self, _old_visible: bool, _new_visible: bool) -> None:
        """Hook for controls that need side effects when visibility changes."""
        self.invalidate()

    def _on_enabled_changed(self, _old_enabled: bool, _new_enabled: bool) -> None:
        """Hook for controls that need side effects when enabled-state changes."""
        self.invalidate()

    @property
    def focused(self) -> bool:
        return self._focused

    def accepts_focus(self) -> bool:
        return self.tab_index >= 0

    def accepts_mouse_focus(self) -> bool:
        """Return whether this node should become focused from mouse clicks.

        Keyboard focus traversal still uses :meth:`accepts_focus`.
        """
        return self.accepts_focus()

    def set_accessibility(self, *, role: str | None = None, label: str | None = None) -> None:
        if role is not None:
            self.accessibility_role = str(role)
        if label is not None:
            self.accessibility_label = str(label)

    def set_tab_index(self, index: int) -> None:
        self.tab_index = int(index)

    def _set_focused(self, value: bool) -> None:
        is_focused = bool(value)
        if self._focused == is_focused:
            return
        self._focused = is_focused
        self.on_focus_changed(is_focused)
        self.invalidate()

    def on_focus_changed(self, _is_focused: bool) -> None:
        """Hook for controls that react to focus changes."""

    def hit_test(self, pos) -> bool:
        return isinstance(pos, tuple) and len(pos) == 2 and self.rect.collidepoint(pos)

    # --- Visibility / enabled helpers ---

    def show(self) -> None:
        """Make this node visible. Equivalent to ``node.visible = True``."""
        self.visible = True

    def hide(self) -> None:
        """Make this node invisible. Equivalent to ``node.visible = False``."""
        self.visible = False

    def enable(self) -> None:
        """Enable this node. Equivalent to ``node.enabled = True``."""
        self.enabled = True

    def disable(self) -> None:
        """Disable this node. Equivalent to ``node.enabled = False``."""
        self.enabled = False

    # --- Geometry helpers ---

    def set_pos(self, x: int, y: int) -> None:
        """Move this node's top-left corner to (x, y) and invalidate."""
        self.rect.x = int(x)
        self.rect.y = int(y)
        self.invalidate()

    def resize(self, width: int, height: int) -> None:
        """Resize this node to (width, height) without changing position, then invalidate."""
        self.rect.width = int(width)
        self.rect.height = int(height)
        self.invalidate()

    def set_rect(self, rect: "Rect") -> None:
        """Replace this node's rect entirely and invalidate."""
        self.rect = Rect(rect)
        self.invalidate()

    # --- Tree traversal helpers ---

    def ancestors(self) -> "Generator[UiNode, None, None]":
        """Yield each ancestor node starting from the immediate parent up to the root."""
        current = self.parent
        while current is not None:
            yield current
            current = current.parent

    def find_descendant(self, control_id: str) -> "Optional[UiNode]":
        """Return the first descendant (BFS) whose ``control_id`` matches, or ``None``."""
        queue: deque[UiNode] = deque(self.children)
        while queue:
            candidate = queue.popleft()
            if candidate.control_id == control_id:
                return candidate
            queue.extend(candidate.children)
        return None

    def find_descendants(self, predicate: "Callable[[UiNode], bool]") -> "List[UiNode]":
        """Return all descendants (BFS) that satisfy *predicate*."""
        result: List[UiNode] = []
        queue: deque[UiNode] = deque(self.children)
        while queue:
            candidate = queue.popleft()
            if predicate(candidate):
                result.append(candidate)
            queue.extend(candidate.children)
        return result

    def find_descendants_of_type(self, node_type: type) -> "List[UiNode]":
        """Return all descendants (BFS) that are instances of *node_type*."""
        return self.find_descendants(lambda n: isinstance(n, node_type))

    def is_root(self) -> bool:
        """Return True when this node has no parent (is a scene root node)."""
        return self.parent is None

    def depth(self) -> int:
        """Return tree depth, where a root node has depth 0."""
        d = 0
        current = self.parent
        while current is not None:
            d += 1
            current = current.parent
        return d

    def sibling_index(self) -> int:
        """Return position of this node among its parent's children, or 0 for root nodes."""
        if self.parent is None:
            return 0
        try:
            return self.parent.children.index(self)
        except ValueError:
            return 0

    def siblings(self) -> "Generator[UiNode, None, None]":
        """Yield all sibling nodes (nodes sharing the same parent, excluding self)."""
        if self.parent is None:
            return
        for child in self.parent.children:
            if child is not self:
                yield child

    def root(self) -> "UiNode":
        """Return the root ancestor of this node (or self if already a root node)."""
        current: UiNode = self
        while current.parent is not None:
            current = current.parent
        return current

    # --- Lifecycle ---

    def on_mount(self, _parent: "UiNode | None") -> None:
        """Hook called when node is attached to a parent or scene."""

    def on_unmount(self, _parent: "UiNode | None") -> None:
        """Hook called when node is detached from a parent or scene."""

    def dispose(self) -> None:
        self._disposed = True
        for child in list(self.children):
            child.dispose()

    @property
    def disposed(self) -> bool:
        return self._disposed

    def invalidate(self) -> None:
        self._dirty = True
        if self.parent is not None:
            self.parent.invalidate()

    def clear_dirty(self) -> None:
        self._dirty = False
        for child in self.children:
            child.clear_dirty()

    @property
    def dirty(self) -> bool:
        return self._dirty

    def is_window(self) -> bool:
        return False

    def is_task_panel(self) -> bool:
        return False

    def set_active(self, _value: bool) -> None:
        """Hook for controls that support active-state semantics."""

    def _clear_active_windows(self) -> None:
        """Hook for container nodes that manage active window state."""

    def update(self, _dt_seconds: float) -> None:
        """Per-frame state update."""

    def handle_event(self, _event: GuiEvent, _app: "GuiApplication") -> bool:
        """Handle one normalized GuiEvent and return whether consumed."""
        return False

    def on_event_capture(self, _event: GuiEvent, _app: "GuiApplication") -> bool:
        """Capture-phase event hook."""
        return False

    def on_event_bubble(self, _event: GuiEvent, _app: "GuiApplication") -> bool:
        """Bubble-phase event hook."""
        return False

    def handle_routed_event(self, event: GuiEvent, app: "GuiApplication") -> bool:
        if event.phase is EventPhase.CAPTURE:
            return bool(self.on_event_capture(event, app))
        if event.phase is EventPhase.BUBBLE:
            return bool(self.on_event_bubble(event, app))
        return bool(self.handle_event(event, app))

    def reconcile_hover(self, _wants_hover: bool) -> None:
        """Update hover state during focus traversal. No-op for nodes without hover visuals."""

    def begin_focus_activation_visual(self) -> None:
        """No-op base. Controls with activation visuals override this."""

    def end_focus_activation_visual(self) -> None:
        """No-op base. Controls with activation visuals override this."""

    def _invoke_click(self) -> None:
        """No-op base. Activatable controls override this."""

    def should_arm_focus_activation_for_event(self, _event: "GuiEvent") -> bool:
        """No-op base. Returns False. Activatable controls override this."""
        return False

    def draw_screen_phase(self, surface: "pygame.Surface", theme: "ColorTheme") -> None:
        """Screen-phase draw. Default calls draw(). PanelControl overrides for split-phase rendering."""
        self.draw(surface, theme)

    def draw_window_phase(self, _surface: "pygame.Surface", _theme: "ColorTheme", app: "GuiApplication | None" = None) -> None:
        """Window-phase draw. No-op for most nodes; PanelControl renders window children here."""

    def draw(self, _surface: "pygame.Surface", _theme: "ColorTheme") -> None:
        """Draw control onto target surface."""
