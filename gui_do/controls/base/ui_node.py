from typing import Callable, List, Optional
from typing import TYPE_CHECKING

from pygame import Rect

from ...events.gui_event import EventPhase, GuiEvent
from ...theme.color_theme import ColorTheme

if TYPE_CHECKING:
    from typing import Generator
    import pygame
    from ...app.gui_application import GuiApplication
    from ...theme.scoped_theme import ScopedTheme


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
        self.accessibility_role = "control"
        self.accessibility_label: Optional[str] = None
        self.tab_index = -1
        self._disposed = False
        self._dirty = True
        # Set by the scene/app during mount to enable per-rect invalidation.
        self._invalidation_tracker = None
        # Optional ScopedTheme attached to this node; resolved via resolve_theme().
        self._scoped_theme: Optional["ScopedTheme"] = None
        # Cumulative scroll/clip offset this node applies to its children.
        # Set by scroll containers when laying out children so that coordinate
        # transforms can reconstruct the full screen-to-local mapping.
        self._local_offset: tuple = (0, 0)

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

    def is_menu_bar(self) -> bool:
        return False

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
        queue = list(self.children)
        i = 0
        while i < len(queue):
            candidate = queue[i]
            i += 1
            if candidate.control_id == control_id:
                return candidate
            if candidate.children:
                queue.extend(candidate.children)
        return None

    def find_descendants(self, predicate: "Callable[[UiNode], bool]") -> "List[UiNode]":
        """Return all descendants (BFS) that satisfy *predicate*."""
        result: List[UiNode] = []
        queue = list(self.children)
        queue_extend = queue.extend
        result_append = result.append
        i = 0
        while i < len(queue):
            candidate = queue[i]
            i += 1
            if predicate(candidate):
                result_append(candidate)
            if candidate.children:
                queue_extend(candidate.children)
        return result

    def find_descendants_of_type(self, node_type: type) -> "List[UiNode]":
        """Return all descendants (BFS) that are instances of *node_type*."""
        result: List[UiNode] = []
        queue = list(self.children)
        queue_extend = queue.extend
        result_append = result.append
        i = 0
        while i < len(queue):
            candidate = queue[i]
            i += 1
            if isinstance(candidate, node_type):
                result_append(candidate)
            if candidate.children:
                queue_extend(candidate.children)
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

    def add_child(self, child: "UiNode") -> "UiNode":
        """Attach one direct child and return it.

        Container controls should prefer this base helper so child mount/
        invalidation semantics remain consistent across the hierarchy.
        """
        child.parent = self
        self.children.append(child)
        child.on_mount(self)
        child.invalidate()
        return child

    def remove_child(self, child: "UiNode", *, dispose: bool = False) -> bool:
        """Detach one direct child.

        Returns ``False`` when *child* is not a direct child.
        """
        try:
            idx = self.children.index(child)
        except ValueError:
            return False
        self.children.pop(idx)
        child.parent = None
        child.on_unmount(self)
        if dispose:
            child.dispose()
        self.invalidate()
        return True

    def clear_children(self, *, dispose: bool = False) -> int:
        """Remove all direct children and return count removed."""
        count = 0
        for child in list(self.children):
            if self.remove_child(child, dispose=dispose):
                count += 1
        return count

    @staticmethod
    def _dispatch_child_event(child: "UiNode", event: GuiEvent, app: "GuiApplication", theme=None) -> bool:
        return bool(child.handle_routed_event(event, app, theme=theme))

    def _dispatch_children(self, event: GuiEvent, app: "GuiApplication", *, reverse: bool, theme=None) -> bool:
        children = self.children

        # Get the focused node to prioritize event handling for focused controls
        # that may draw outside their rect. The focused control is handled first so
        # it gets first chance at events in its overdrawn area.
        focused_child = None
        if hasattr(app, 'focus') and app.focus is not None:
            focused_node = app.focus.focused_node
            if focused_node is not None and focused_node.parent is self:
                focused_child = focused_node

        # If there's a focused child, handle it first for event priority
        if focused_child is not None and focused_child.visible and focused_child.enabled:
            if self._dispatch_child_event(focused_child, event, app, theme=theme):
                return True
            if event.propagation_stopped:
                return True

        # Then dispatch to remaining children in normal order
        # Reverse dispatch iterates children in reverse without copying:
        # reversed() on a list returns a list_reverseiterator with no allocation.
        # Forward dispatch iterates the live list (capture-phase handlers rarely mutate children).
        iterable = reversed(children) if reverse else children
        for child in iterable:
            # Skip the focused child since we already handled it
            if child is focused_child:
                continue
            if not (child.visible and child.enabled):
                continue
            if self._dispatch_child_event(child, event, app, theme=theme):
                return True
            if event.propagation_stopped:
                return True
        return False

    def dispose(self) -> None:
        self._disposed = True
        for child in list(self.children):
            child.dispose()

    @property
    def disposed(self) -> bool:
        return self._disposed

    def invalidate(self) -> None:
        if self._dirty:
            return  # already dirty; parent chain was already walked
        self._dirty = True
        # Notify the per-frame invalidation tracker with this node's rect so
        # that the renderer can skip unaffected regions (dirty-region rendering).
        if self._invalidation_tracker is not None:
            self._invalidation_tracker.invalidate_rect(self.rect)
        if self.parent is not None:
            self.parent.invalidate()

    def set_invalidation_tracker(self, tracker) -> None:
        """Attach an :class:`~gui_do.InvalidationTracker` to this node and its subtree.

        Called automatically when a node is added to a scene that has an
        associated tracker.  Pass ``None`` to detach.
        """
        self._invalidation_tracker = tracker
        for child in self.children:
            child.set_invalidation_tracker(tracker)

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

    def is_overlay(self) -> bool:
        return False

    # ------------------------------------------------------------------
    # Drag-and-drop hooks
    # ------------------------------------------------------------------

    def on_drag_start(self, event: "GuiEvent") -> "Optional[object]":
        """Return a DragPayload to initiate drag, or None to ignore."""
        return None

    def on_drag_end(self, accepted: bool) -> None:
        """Called when a drag initiated by this node ends."""

    def accepts_drop(self, payload: "object") -> bool:
        """Return True if this node can accept the given drag payload."""
        return False

    def on_drag_enter(self, payload: "object") -> None:
        """Called when a dragged payload enters this node's bounds."""

    def on_drag_leave(self, payload: "object") -> None:
        """Called when a dragged payload leaves this node's bounds."""

    def on_drop(self, payload: "object", pos: tuple) -> bool:
        """Called when a payload is dropped onto this node. Return True if accepted."""
        return False

    def set_active(self, _value: bool) -> None:
        """Hook for controls that support active-state semantics."""

    def _clear_active_windows(self) -> None:
        """Hook for container nodes that manage active window state."""

    def update(self, _dt_seconds: float) -> None:
        """Per-frame state update."""

    def handle_event(self, _event: GuiEvent, _app: "GuiApplication", theme=None) -> bool:
        """Handle one normalized GuiEvent and return whether consumed."""
        return False

    def on_event_capture(self, _event: GuiEvent, _app: "GuiApplication", theme=None) -> bool:
        """Capture-phase event hook."""
        return False

    def on_event_bubble(self, _event: GuiEvent, _app: "GuiApplication", theme=None) -> bool:
        """Bubble-phase event hook."""
        return False

    def handle_routed_event(self, event: GuiEvent, app: "GuiApplication", theme=None) -> bool:
        # --- Ensure theme is always valid and has fonts ---
        # theme is None when called from overlay paths that pass no theme argument;
        # use identity check (C-level fast path) rather than getattr.
        if theme is None:
            theme = ColorTheme()
        if event.phase is EventPhase.CAPTURE:
            return bool(self.on_event_capture(event, app, theme=theme))
        if event.phase is EventPhase.BUBBLE:
            return bool(self.on_event_bubble(event, app, theme=theme))
        return bool(self.handle_event(event, app, theme=theme))

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

    def draw_screen_phase(self, surface: "pygame.Surface", theme: "ColorTheme", app: "GuiApplication | None" = None) -> None:
        """Screen-phase draw. Default calls draw(). PanelControl overrides for split-phase rendering."""
        self.draw(surface, theme)

    def draw_window_phase(self, _surface: "pygame.Surface", _theme: "ColorTheme", app: "GuiApplication | None" = None) -> None:
        """Window-phase draw. No-op for most nodes; PanelControl renders window children here."""

    def draw(self, _surface: "pygame.Surface", _theme: "ColorTheme") -> None:
        """Draw control onto target surface."""

    # ------------------------------------------------------------------
    # Intrinsic sizing — measure() protocol
    # ------------------------------------------------------------------

    def preferred_size(
        self,
        available_width: int = -1,
        available_height: int = -1,
    ) -> "tuple[int, int]":
        """Return the node's natural ``(width, height)`` given constraints.

        Parameters
        ----------
        available_width:
            Maximum horizontal space offered by the parent, or ``-1`` for
            unconstrained.
        available_height:
            Maximum vertical space offered by the parent, or ``-1`` for
            unconstrained.

        Returns
        -------
        (int, int)
            Preferred width and height in pixels.  The default implementation
            returns the current ``rect`` size so every control behaves
            correctly without an override.  Controls with dynamic content
            (labels, text inputs, list views …) should override this to
            reflect their natural content size.
        """
        return (self.rect.width, self.rect.height)

    def measure(
        self,
        available_width: int = -1,
        available_height: int = -1,
    ) -> "tuple[int, int]":
        """Alias for :meth:`preferred_size` matching the :class:`~gui_do.LayoutPass` protocol."""
        return self.preferred_size(available_width, available_height)

    # ------------------------------------------------------------------
    # Value-state serialization contract
    # ------------------------------------------------------------------

    def capture_state(self) -> dict:
        """Return a JSON-safe snapshot of this node's interactive value state.

        The default implementation returns an empty dict (stateless node).
        Controls with user-mutable state (text inputs, sliders, scroll views,
        toggles, list selections …) override this to include their current
        values so that callers can persist, restore, or undo the state.

        The returned dict should use only JSON-safe types (str, int, float,
        bool, list, dict, None).  Keys are control-specific; callers must
        treat the dict as opaque and round-trip it through
        :meth:`restore_state` unchanged.

        Returns
        -------
        dict
            Snapshot of interactive state.  Empty dict for stateless nodes.
        """
        return {}

    def restore_state(self, state: dict) -> None:
        """Restore interactive value state from a previously captured snapshot.

        The default implementation is a no-op.  Stateful controls override
        this to apply all keys from *state* (as produced by
        :meth:`capture_state`).  Unknown keys should be silently ignored so
        that old snapshots remain forward-compatible when new state fields are
        added.

        Parameters
        ----------
        state:
            Dict previously returned by :meth:`capture_state` on a compatible
            node.  May be an empty dict (callers should handle this).
        """

    def capture_subtree_state(self) -> dict:
        """Capture state for this node and all descendants into a nested dict.

        Returns a dict keyed by ``control_id`` containing only nodes with
        non-empty :meth:`capture_state` output, so stateless nodes contribute
        no keys.

        Returns
        -------
        dict
            ``{control_id: state_dict}`` for this node and its descendants.
        """
        result: dict = {}
        own = self.capture_state()
        if own:
            result[self.control_id] = own
        for child in self.children:
            result.update(child.capture_subtree_state())
        return result

    def restore_subtree_state(self, state: dict) -> None:
        """Restore state for this node and all descendants from a nested dict.

        *state* should be a dict as returned by :meth:`capture_subtree_state`.
        Controls whose ``control_id`` is not present in *state* are left
        unchanged (forward-compatible restoration).

        Parameters
        ----------
        state:
            ``{control_id: state_dict}`` mapping.
        """
        if not state:
            return
        own = state.get(self.control_id)
        if own is not None:
            self.restore_state(own)
        for child in self.children:
            child.restore_subtree_state(state)

    # ------------------------------------------------------------------
    # Cascading theme scope resolution
    # ------------------------------------------------------------------

    def attach_scoped_theme(self, scoped_theme: "ScopedTheme") -> None:
        """Attach a :class:`~gui_do.ScopedTheme` to this node.

        All descendants that call :meth:`resolve_theme` will receive this
        scope as the innermost override context until a closer ancestor
        overrides it again, or until :meth:`detach_scoped_theme` is called.

        Parameters
        ----------
        scoped_theme:
            The scope to attach.  Pass ``None`` to clear the attachment.
        """
        self._scoped_theme = scoped_theme
        self.invalidate()

    def detach_scoped_theme(self) -> None:
        """Remove any :class:`~gui_do.ScopedTheme` attached to this node."""
        self._scoped_theme = None
        self.invalidate()

    def resolve_theme(
        self,
        base_theme: "ColorTheme",
    ) -> "ColorTheme":
        """Return the most-specific :class:`~gui_do.ColorTheme`-compatible theme
        for this node, climbing the parent chain for :class:`~gui_do.ScopedTheme`
        overrides.

        The resolution order is:

        1. Nearest ancestor (including self) that has a ``_scoped_theme`` set.
        2. The global *base_theme* when no scope is found.

        Since :class:`~gui_do.ScopedTheme` is not a drop-in replacement for
        :class:`~gui_do.ColorTheme`, this method returns the *base_theme*
        object itself when no scope overrides are attached.  Individual draw
        methods can use :meth:`nearest_scoped_theme` to obtain the raw scope
        and resolve individual tokens from it.

        Parameters
        ----------
        base_theme:
            The application-level :class:`~gui_do.ColorTheme` used as the
            final fallback.

        Returns
        -------
        ColorTheme
            The *base_theme* (callers use :meth:`nearest_scoped_theme` for
            token-level overrides).
        """
        return base_theme

    def nearest_scoped_theme(self) -> "Optional[ScopedTheme]":
        """Return the nearest :class:`~gui_do.ScopedTheme` in the ancestor chain.

        Walks from this node upward through ``parent`` links and returns the
        first ``_scoped_theme`` that is not ``None``.  Returns ``None`` when
        no ancestor (including self) has a scoped theme attached.

        Draw methods call this to obtain token overrides::

            scope = self.nearest_scoped_theme()
            surface_color = scope.resolve("surface") if scope else theme.surface
        """
        current: Optional["UiNode"] = self
        while current is not None:
            if current._scoped_theme is not None:  # noqa: SLF001
                return current._scoped_theme
            current = current.parent
        return None

    # ------------------------------------------------------------------
    # Local coordinate transform chain
    # ------------------------------------------------------------------

    def set_local_offset(self, dx: int, dy: int) -> None:
        """Record the scroll/clip offset this node applies to its children.

        Scroll containers call this during layout so that
        :meth:`local_to_screen` and :meth:`screen_to_local` can reconstruct
        the full transform chain from any descendant up to the screen.

        Parameters
        ----------
        dx, dy:
            The horizontal and vertical scroll offset (in pixels) that this
            node applies when positioning its children.  Positive values mean
            children are shifted right / down; negative mean they are clipped
            to the left / top.
        """
        self._local_offset = (int(dx), int(dy))

    def local_to_screen(self, local_pos: tuple) -> tuple:
        """Convert a position in this node's local coordinate space to screen
        coordinates.

        Walks the parent chain accumulating each ancestor's
        ``_local_offset`` so that the position is correctly mapped even
        through nested scroll containers.

        Parameters
        ----------
        local_pos:
            ``(x, y)`` in this node's local coordinate system (i.e. relative
            to ``self.rect.topleft`` before any scrolling is applied).

        Returns
        -------
        tuple[int, int]
            The corresponding ``(screen_x, screen_y)`` position.
        """
        x, y = int(local_pos[0]), int(local_pos[1])
        # Start at this node's own rect origin.
        x += self.rect.left
        y += self.rect.top
        # Walk ancestors, each parent's _local_offset represents how much
        # this node was shifted inside the parent's content area.
        current: Optional["UiNode"] = self.parent
        while current is not None:
            ox, oy = current._local_offset  # noqa: SLF001
            x += ox
            y += oy
            x += current.rect.left
            y += current.rect.top
            current = current.parent
        return (x, y)

    def screen_to_local(self, screen_pos: tuple) -> tuple:
        """Convert a screen-space position to this node's local coordinate space.

        Inverse of :meth:`local_to_screen`.  Useful for hit testing against
        content that has been scrolled within a viewport.

        Parameters
        ----------
        screen_pos:
            ``(screen_x, screen_y)`` in screen/window coordinates.

        Returns
        -------
        tuple[int, int]
            The corresponding ``(local_x, local_y)`` in this node's coordinate
            system.
        """
        screen_x, screen_y = int(screen_pos[0]), int(screen_pos[1])
        origin_x, origin_y = self.local_to_screen((0, 0))
        return (screen_x - origin_x, screen_y - origin_y)
