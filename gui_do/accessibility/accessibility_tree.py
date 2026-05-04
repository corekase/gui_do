"""accessibility_tree — semantic accessibility node tree.

Provides a pure-Python overlay on the widget tree that:
- Assigns formal WCAG-inspired :class:`AccessibilityRole` values to nodes.
- Maintains parent–child relationships (``labelledby``, ``owns``) between nodes.
- Exposes a :class:`AccessibilityBus` for live-region announcements.
- Enables programmatic tree traversal by role (for testing and inspection).

No OS-level accessibility APIs are used.  The tree is a design-time and
runtime semantic model only.  A future bridge layer could translate it to
platform AT-SPI / UIAutomation but that is out of scope here.

Usage::

    from gui_do import (
        AccessibilityTree, AccessibilityNode, AccessibilityRole,
        AccessibilityBus, LivePoliteness,
    )

    tree = AccessibilityTree()
    bus = AccessibilityBus()

    # Register nodes at scene build time:
    zoom_node = AccessibilityNode(
        role=AccessibilityRole.SLIDER,
        label="Zoom level",
        value_text=lambda: f"{slider.value:.0f}%",
        widget=slider,
    )
    tree.register(zoom_node)

    ok_btn = AccessibilityNode(
        role=AccessibilityRole.BUTTON,
        label="OK",
        widget=ok_button,
    )
    tree.register(ok_btn)

    # Live announcements from any feature:
    bus.announce("File saved", politeness=LivePoliteness.POLITE)
    bus.announce("Unsaved changes discarded", politeness=LivePoliteness.ASSERTIVE)

    # Traversal by role:
    buttons = tree.find_all(role=AccessibilityRole.BUTTON)
    dialogs = tree.find_all(role=AccessibilityRole.DIALOG)

    # Scoped search:
    inputs = tree.find_all(role=AccessibilityRole.TEXT_INPUT, scope=dialog_node)

    # Deregister when a control is removed from the scene:
    tree.unregister(zoom_node)

    # Snapshot of current state for test assertions:
    snapshot = tree.snapshot()
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import (
    Callable,
    Dict,
    FrozenSet,
    Iterator,
    List,
    Optional,
    Sequence,
    Set,
    Tuple,
    TYPE_CHECKING,
)

if TYPE_CHECKING:
    pass  # widget type is intentionally untyped here for portability


# ---------------------------------------------------------------------------
# AccessibilityRole
# ---------------------------------------------------------------------------


class AccessibilityRole(Enum):
    """WCAG-inspired semantic role vocabulary for GUI nodes.

    Keep this minimal.  Richer ARIA roles can extend it later without
    breaking existing consumers.
    """

    NONE = "none"
    BUTTON = "button"
    TOGGLE = "toggle"
    SLIDER = "slider"
    SCROLLBAR = "scrollbar"
    TEXT_INPUT = "text_input"
    TEXT_AREA = "text_area"
    LABEL = "label"
    HEADING = "heading"
    IMAGE = "image"
    LIST = "list"
    LIST_ITEM = "list_item"
    TREE = "tree"
    TREE_ITEM = "tree_item"
    GRID = "grid"
    GRID_CELL = "grid_cell"
    TAB = "tab"
    TAB_PANEL = "tab_panel"
    DIALOG = "dialog"
    ALERT_DIALOG = "alert_dialog"
    LANDMARK = "landmark"
    NAVIGATION = "navigation"
    TOOLBAR = "toolbar"
    MENU = "menu"
    MENU_ITEM = "menu_item"
    LIVE_REGION = "live_region"
    PROGRESS_BAR = "progress_bar"
    CANVAS = "canvas"
    WINDOW = "window"


# ---------------------------------------------------------------------------
# LivePoliteness
# ---------------------------------------------------------------------------


class LivePoliteness(Enum):
    """Urgency of a live-region announcement.

    - ``OFF`` — updates are not announced.
    - ``POLITE`` — announced at the next idle opportunity.
    - ``ASSERTIVE`` — announced immediately, interrupting current speech.
    """

    OFF = "off"
    POLITE = "polite"
    ASSERTIVE = "assertive"


# ---------------------------------------------------------------------------
# AccessibilityNode
# ---------------------------------------------------------------------------


class AccessibilityNode:
    """Semantic descriptor for a single interactive or informational UI node.

    Parameters
    ----------
    role:
        The node's :class:`AccessibilityRole`.
    label:
        Human-readable accessible label (e.g. control tooltip or visible text).
    widget:
        The underlying control object.  May be ``None`` for virtual / group
        nodes that have no direct widget counterpart.
    value_text:
        Optional callable returning the current value as a string (e.g.
        ``lambda: f"{slider.value:.0f}%"``).  Called on demand — not cached.
    description:
        Extended description or hint beyond the primary label.
    labelledby:
        Node whose :attr:`label` acts as the accessible name for *this* node
        (analogous to ARIA ``aria-labelledby``).
    live_politeness:
        For nodes that represent live regions, the announcement urgency.
    enabled:
        Whether the node is currently interactive.
    """

    def __init__(
        self,
        *,
        role: AccessibilityRole = AccessibilityRole.NONE,
        label: str = "",
        widget: object = None,
        value_text: Optional[Callable[[], str]] = None,
        description: str = "",
        labelledby: Optional["AccessibilityNode"] = None,
        live_politeness: LivePoliteness = LivePoliteness.OFF,
        enabled: bool = True,
    ) -> None:
        self.role = role
        self.label = str(label)
        self.widget = widget
        self.value_text = value_text
        self.description = str(description)
        self.labelledby = labelledby
        self.live_politeness = live_politeness
        self.enabled = bool(enabled)

        # Tree linkage (set by AccessibilityTree)
        self._children: List["AccessibilityNode"] = []
        self._parent: Optional["AccessibilityNode"] = None

    # ------------------------------------------------------------------
    # Tree traversal
    # ------------------------------------------------------------------

    @property
    def children(self) -> List["AccessibilityNode"]:
        return list(self._children)

    @property
    def parent(self) -> Optional["AccessibilityNode"]:
        return self._parent

    def ancestors(self) -> Iterator["AccessibilityNode"]:
        """Yield ancestor nodes from parent up to root."""
        node = self._parent
        while node is not None:
            yield node
            node = node._parent

    # ------------------------------------------------------------------
    # Value
    # ------------------------------------------------------------------

    def get_value_text(self) -> str:
        """Return the current value string, or ``""`` if no value_text is set."""
        if self.value_text is None:
            return ""
        try:
            return str(self.value_text())
        except Exception:
            return ""

    # ------------------------------------------------------------------
    # Effective label
    # ------------------------------------------------------------------

    def get_effective_label(self) -> str:
        """Return the accessible name: own label, or labelledby node's label."""
        if self.labelledby is not None:
            return self.labelledby.label
        return self.label

    def __repr__(self) -> str:
        return (
            f"AccessibilityNode(role={self.role.value!r}, label={self.label!r})"
        )


# ---------------------------------------------------------------------------
# AccessibilityTree
# ---------------------------------------------------------------------------


class AccessibilityTree:
    """Registry and traversal engine for :class:`AccessibilityNode` objects.

    Nodes are stored in insertion order.  Traversal via :meth:`find_all`
    iterates in depth-first insertion order.

    Thread model: main (render) thread only.
    """

    def __init__(self) -> None:
        # Flat ordered list of all registered nodes
        self._nodes: List[AccessibilityNode] = []
        # Map widget id -> node for fast widget-based lookup
        self._by_widget: Dict[int, AccessibilityNode] = {}

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(
        self,
        node: AccessibilityNode,
        *,
        parent: Optional[AccessibilityNode] = None,
    ) -> None:
        """Register *node* in the tree, optionally as a child of *parent*.

        If *parent* is ``None`` the node is registered at the tree root.
        """
        if node in self._nodes:
            return  # idempotent
        self._nodes.append(node)
        if node.widget is not None:
            self._by_widget[id(node.widget)] = node
        if parent is not None and node not in parent._children:
            parent._children.append(node)
            node._parent = parent

    def unregister(self, node: AccessibilityNode) -> None:
        """Remove *node* from the tree (does not remove its children)."""
        try:
            self._nodes.remove(node)
        except ValueError:
            return
        if node.widget is not None:
            self._by_widget.pop(id(node.widget), None)
        if node._parent is not None:
            try:
                node._parent._children.remove(node)
            except ValueError:
                pass
            node._parent = None

    def clear(self) -> None:
        """Remove all nodes from the tree."""
        for node in self._nodes:
            node._parent = None
            node._children.clear()
        self._nodes.clear()
        self._by_widget.clear()

    # ------------------------------------------------------------------
    # Lookup
    # ------------------------------------------------------------------

    def find_all(
        self,
        *,
        role: Optional[AccessibilityRole] = None,
        scope: Optional[AccessibilityNode] = None,
        enabled_only: bool = False,
    ) -> List[AccessibilityNode]:
        """Return all nodes matching the given filters.

        Parameters
        ----------
        role:
            When provided, only return nodes with this :class:`AccessibilityRole`.
        scope:
            When provided, only return nodes that are descendants of *scope*
            (scope is not included itself).
        enabled_only:
            When ``True``, exclude nodes whose :attr:`~AccessibilityNode.enabled`
            is ``False``.
        """
        if scope is not None:
            candidates = list(self._iter_descendants(scope))
        else:
            candidates = self._nodes

        results: List[AccessibilityNode] = []
        for node in candidates:
            if role is not None and node.role != role:
                continue
            if enabled_only and not node.enabled:
                continue
            results.append(node)
        return results

    def find_by_widget(self, widget: object) -> Optional[AccessibilityNode]:
        """Return the node associated with *widget*, or ``None``."""
        return self._by_widget.get(id(widget))

    def find_first(
        self,
        *,
        role: Optional[AccessibilityRole] = None,
        label: Optional[str] = None,
    ) -> Optional[AccessibilityNode]:
        """Return the first matching node, or ``None``."""
        for node in self._nodes:
            if role is not None and node.role != role:
                continue
            if label is not None and node.label != label:
                continue
            return node
        return None

    def _iter_descendants(
        self, root: AccessibilityNode
    ) -> Iterator[AccessibilityNode]:
        """Depth-first iteration of all descendants of *root* (root excluded)."""
        stack = list(root._children)
        while stack:
            node = stack.pop(0)
            yield node
            stack = list(node._children) + stack

    # ------------------------------------------------------------------
    # Snapshot
    # ------------------------------------------------------------------

    def snapshot(self) -> List[dict]:
        """Return a serialisable snapshot of all nodes (for test assertions).

        Each entry is a dict with ``role``, ``label``, ``enabled``,
        ``value_text``, and ``child_count`` keys.
        """
        return [
            {
                "role": n.role.value,
                "label": n.label,
                "enabled": n.enabled,
                "value_text": n.get_value_text(),
                "child_count": len(n._children),
            }
            for n in self._nodes
        ]

    def __len__(self) -> int:
        return len(self._nodes)


# ---------------------------------------------------------------------------
# AccessibilityBus — live-region announcements
# ---------------------------------------------------------------------------


@dataclass
class AccessibilityAnnouncement:
    """A single live-region announcement record."""

    message: str
    politeness: LivePoliteness


class AccessibilityBus:
    """Collects and dispatches live-region announcements.

    Announcements are stored in a FIFO queue and consumed by
    :meth:`consume_announcements`.  Integrations (e.g. a screen-reader bridge
    or a debug overlay) consume and act on them once per frame.

    Usage::

        bus = AccessibilityBus()
        bus.announce("File saved", politeness=LivePoliteness.POLITE)

        # In the frame loop or bridge layer:
        for announcement in bus.consume_announcements():
            screen_reader.speak(announcement.message, urgency=announcement.politeness)
    """

    def __init__(self) -> None:
        self._queue: List[AccessibilityAnnouncement] = []
        self._subscribers: List[Callable[[AccessibilityAnnouncement], None]] = []

    def announce(
        self,
        message: str,
        *,
        politeness: LivePoliteness = LivePoliteness.POLITE,
    ) -> None:
        """Queue an announcement with the given *politeness* level.

        Immediate subscribers (if any) are also notified synchronously.
        """
        announcement = AccessibilityAnnouncement(
            message=str(message),
            politeness=politeness,
        )
        self._queue.append(announcement)
        for sub in tuple(self._subscribers):
            try:
                sub(announcement)
            except Exception:
                pass

    def consume_announcements(self) -> List[AccessibilityAnnouncement]:
        """Return and clear all pending announcements (FIFO order)."""
        result = list(self._queue)
        self._queue.clear()
        return result

    def subscribe(
        self, callback: Callable[[AccessibilityAnnouncement], None]
    ) -> Callable[[], None]:
        """Register *callback* to be called synchronously on each announcement.

        Returns an unsubscribe callable.
        """
        self._subscribers.append(callback)

        def _unsub() -> None:
            try:
                self._subscribers.remove(callback)
            except ValueError:
                pass

        return _unsub

    @property
    def pending_count(self) -> int:
        """Number of unconsumed announcements in the queue."""
        return len(self._queue)
