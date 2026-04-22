from typing import Callable, Generator, List, Optional
from typing import TYPE_CHECKING

from pygame import Rect

from .gui_event import EventPhase, GuiEvent

if TYPE_CHECKING:
    import pygame
    from ..app.gui_application import GuiApplication
    from ..theme.color_theme import ColorTheme


class UiNode:
    """Base node for all controls in the rebased package."""

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

    # --- Tree traversal helpers ---

    def ancestors(self) -> "Generator[UiNode, None, None]":
        """Yield each ancestor node starting from the immediate parent up to the root."""
        current = self.parent
        while current is not None:
            yield current
            current = current.parent

    def find_descendant(self, control_id: str) -> "Optional[UiNode]":
        """Return the first descendant (BFS) whose ``control_id`` matches, or ``None``."""
        queue: List[UiNode] = list(self.children)
        while queue:
            candidate = queue.pop(0)
            if candidate.control_id == control_id:
                return candidate
            queue.extend(candidate.children)
        return None

    def find_descendants(self, predicate: "Callable[[UiNode], bool]") -> "List[UiNode]":
        """Return all descendants (BFS) that satisfy *predicate*."""
        result: List[UiNode] = []
        queue: List[UiNode] = list(self.children)
        while queue:
            candidate = queue.pop(0)
            if predicate(candidate):
                result.append(candidate)
            queue.extend(candidate.children)
        return result

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

    def draw(self, _surface: "pygame.Surface", _theme: "ColorTheme") -> None:
        """Draw control onto target surface."""
