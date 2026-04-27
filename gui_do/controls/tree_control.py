"""TreeControl — virtualized hierarchical tree view with expand/collapse."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional, TYPE_CHECKING

import pygame
from pygame import Rect

from ..core.gui_event import EventType, GuiEvent
from ..core.ui_node import UiNode

if TYPE_CHECKING:
    from ..app.gui_application import GuiApplication
    from ..theme.color_theme import ColorTheme


SelectCallback = Optional[Callable[["TreeNode", int], None]]
ExpandCallback = Optional[Callable[["TreeNode", bool], None]]

_INDENT_WIDTH = 18
_ROW_HEIGHT = 26
_ARROW_SIZE = 8
_SCROLLBAR_WIDTH = 12
_FONT_SIZE = 17


@dataclass
class TreeNode:
    """One node in a tree hierarchy.

    *children* contains child nodes (empty list for leaves).
    *expanded* controls whether children are visible.
    *data* is an optional application payload attached to the node.
    """

    label: str
    children: List["TreeNode"] = field(default_factory=list)
    expanded: bool = False
    enabled: bool = True
    data: Any = None
    icon: Optional[str] = None  # reserved for future icon rendering

    @property
    def is_leaf(self) -> bool:
        return len(self.children) == 0


class _FlatRow:
    """Internal flattened representation used for virtualised rendering."""

    __slots__ = ("node", "depth", "index")

    def __init__(self, node: "TreeNode", depth: int, index: int) -> None:
        self.node = node
        self.depth = depth
        self.index = index


def _flatten(nodes: List[TreeNode], depth: int = 0) -> List[_FlatRow]:
    rows: List[_FlatRow] = []
    for node in nodes:
        rows.append(_FlatRow(node, depth, len(rows)))
        if node.expanded and node.children:
            rows.extend(_flatten(node.children, depth + 1))
    return rows


class TreeControl(UiNode):
    """Hierarchical tree view control with virtualised rendering.

    Usage::

        root_nodes = [
            TreeNode("Folder A", children=[
                TreeNode("File 1"),
                TreeNode("File 2"),
            ], expanded=True),
            TreeNode("Folder B", children=[
                TreeNode("File 3"),
            ]),
        ]
        tree = TreeControl("tree", Rect(10, 10, 300, 400), root_nodes)
        tree.on_select = lambda node, row: print("selected", node.label)
        app.add(tree)
    """

    def __init__(
        self,
        control_id: str,
        rect: Rect,
        nodes: Optional[List[TreeNode]] = None,
        *,
        row_height: int = _ROW_HEIGHT,
        indent_width: int = _INDENT_WIDTH,
        on_select: SelectCallback = None,
        on_expand: ExpandCallback = None,
        show_root: bool = True,
        show_scrollbar: bool = True,
        font_role: str = "body",
    ) -> None:
        super().__init__(control_id, rect)
        self._nodes: List[TreeNode] = list(nodes) if nodes else []
        self._row_height: int = max(8, int(row_height))
        self._indent_width: int = max(4, int(indent_width))
        self._on_select: SelectCallback = on_select
        self._on_expand: ExpandCallback = on_expand
        self._show_root: bool = bool(show_root)
        self._show_scrollbar: bool = bool(show_scrollbar)
        self._font_role: str = font_role
        self._selected_node: Optional[TreeNode] = None
        self._scroll_offset: int = 0  # pixels
        self._rows: List[_FlatRow] = []
        self._rebuild_rows()
        self.tab_index = 0

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def nodes(self) -> List[TreeNode]:
        return list(self._nodes)

    @property
    def selected_node(self) -> Optional[TreeNode]:
        return self._selected_node

    @property
    def scroll_offset(self) -> int:
        return self._scroll_offset

    # ------------------------------------------------------------------
    # Mutation API
    # ------------------------------------------------------------------

    def set_nodes(self, nodes: List[TreeNode]) -> None:
        """Replace the root node list."""
        self._nodes = list(nodes)
        self._selected_node = None
        self._scroll_offset = 0
        self._rebuild_rows()
        self.invalidate()

    def expand(self, node: TreeNode) -> None:
        """Expand *node* and rebuild the flat row cache."""
        if not node.is_leaf:
            node.expanded = True
            self._rebuild_rows()
            self.invalidate()
            if self._on_expand:
                try:
                    self._on_expand(node, True)
                except Exception:
                    pass

    def collapse(self, node: TreeNode) -> None:
        """Collapse *node* and rebuild the flat row cache."""
        node.expanded = False
        self._rebuild_rows()
        self.invalidate()
        if self._on_expand:
            try:
                self._on_expand(node, False)
            except Exception:
                pass

    def toggle(self, node: TreeNode) -> None:
        """Toggle expand/collapse for *node*."""
        if node.expanded:
            self.collapse(node)
        else:
            self.expand(node)

    def select(self, node: Optional[TreeNode]) -> None:
        """Programmatically select a node (None clears selection)."""
        self._selected_node = node
        self.invalidate()

    def expand_all(self) -> None:
        """Recursively expand all nodes."""
        self._set_all_expanded(self._nodes, True)
        self._rebuild_rows()
        self.invalidate()

    def collapse_all(self) -> None:
        """Recursively collapse all nodes."""
        self._set_all_expanded(self._nodes, False)
        self._rebuild_rows()
        self.invalidate()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _set_all_expanded(self, nodes: List[TreeNode], value: bool) -> None:
        for node in nodes:
            node.expanded = value
            self._set_all_expanded(node.children, value)

    def _rebuild_rows(self) -> None:
        self._rows = _flatten(self._nodes)
        # Reassign indices to match position in flat list
        for i, row in enumerate(self._rows):
            row.index = i

    def _total_height(self) -> int:
        return len(self._rows) * self._row_height

    def _visible_rect(self) -> Rect:
        """Return the content area (excluding scrollbar if shown)."""
        sb_w = _SCROLLBAR_WIDTH if self._show_scrollbar and self._total_height() > self.rect.height else 0
        return Rect(self.rect.x, self.rect.y, self.rect.width - sb_w, self.rect.height)

    def _max_scroll(self) -> int:
        return max(0, self._total_height() - self.rect.height)

    def _clamp_scroll(self) -> None:
        self._scroll_offset = max(0, min(self._scroll_offset, self._max_scroll()))

    def _row_at(self, pos: tuple) -> int:
        """Return the flat row index at pixel position, or -1."""
        vr = self._visible_rect()
        if not vr.collidepoint(pos):
            return -1
        rel_y = pos[1] - vr.y + self._scroll_offset
        idx = rel_y // self._row_height
        if 0 <= idx < len(self._rows):
            return idx
        return -1

    def _arrow_rect(self, row_rect: Rect, depth: int) -> Rect:
        """Return the rect of the expand/collapse arrow for a row."""
        ax = row_rect.x + depth * self._indent_width
        ay = row_rect.y + (row_rect.height - _ARROW_SIZE) // 2
        return Rect(ax, ay, _ARROW_SIZE, _ARROW_SIZE)

    # ------------------------------------------------------------------
    # UiNode overrides
    # ------------------------------------------------------------------

    def handle_event(self, event: GuiEvent, app: "GuiApplication") -> bool:
        if not self.visible or not self.enabled:
            return False

        vr = self._visible_rect()

        # Mouse wheel scrolling
        if event.kind == EventType.MOUSE_WHEEL and vr.collidepoint(event.pos):
            self._scroll_offset -= event.wheel_delta * self._row_height
            self._clamp_scroll()
            self.invalidate()
            return True

        if event.kind == EventType.MOUSE_BUTTON_DOWN and event.button == 1:
            row_idx = self._row_at(event.pos)
            if row_idx < 0:
                return vr.collidepoint(event.pos)
            row = self._rows[row_idx]
            node = row.node
            if not node.enabled:
                return True
            # Check if click is on the arrow
            row_y = vr.y + row_idx * self._row_height - self._scroll_offset
            rr = Rect(vr.x, row_y, vr.width, self._row_height)
            ar = self._arrow_rect(rr, row.depth)
            if not node.is_leaf and ar.collidepoint(event.pos):
                self.toggle(node)
            else:
                # Single-click on node label selects and also toggles expand
                if not node.is_leaf:
                    self.toggle(node)
                old = self._selected_node
                self._selected_node = node
                if node is not old:
                    self.invalidate()
                    if self._on_select:
                        try:
                            self._on_select(node, row_idx)
                        except Exception:
                            pass
            return True

        if event.kind == EventType.KEY_DOWN and self._selected_node is not None:
            key = event.key
            sel_idx = next((i for i, r in enumerate(self._rows) if r.node is self._selected_node), -1)
            if key == pygame.K_DOWN and sel_idx < len(self._rows) - 1:
                new_row = self._rows[sel_idx + 1]
                self._selected_node = new_row.node
                self._scroll_to_row(sel_idx + 1, vr)
                self.invalidate()
                if self._on_select:
                    try:
                        self._on_select(new_row.node, sel_idx + 1)
                    except Exception:
                        pass
                return True
            if key == pygame.K_UP and sel_idx > 0:
                new_row = self._rows[sel_idx - 1]
                self._selected_node = new_row.node
                self._scroll_to_row(sel_idx - 1, vr)
                self.invalidate()
                if self._on_select:
                    try:
                        self._on_select(new_row.node, sel_idx - 1)
                    except Exception:
                        pass
                return True
            if key == pygame.K_RIGHT and sel_idx >= 0:
                node = self._rows[sel_idx].node
                if not node.is_leaf and not node.expanded:
                    self.expand(node)
                return True
            if key == pygame.K_LEFT and sel_idx >= 0:
                node = self._rows[sel_idx].node
                if not node.is_leaf and node.expanded:
                    self.collapse(node)
                return True

        return False

    def _scroll_to_row(self, row_idx: int, vr: Rect) -> None:
        row_y = row_idx * self._row_height
        if row_y < self._scroll_offset:
            self._scroll_offset = row_y
        elif row_y + self._row_height > self._scroll_offset + vr.height:
            self._scroll_offset = row_y + self._row_height - vr.height
        self._clamp_scroll()

    def draw(self, surface: "pygame.Surface", theme: "ColorTheme") -> None:
        if not self.visible:
            return

        def _c(name: str, fallback: tuple) -> tuple:
            v = getattr(theme, name, fallback)
            return v.value if hasattr(v, "value") else v

        bg = _c("background", (30, 30, 38))
        text_col = _c("text", (220, 220, 220))
        disabled_col = tuple(max(0, min(255, c // 2)) for c in text_col)
        sel_col = _c("highlight", (0, 100, 200))
        arrow_col = _c("medium", (150, 150, 160))

        try:
            font = pygame.font.SysFont(None, _FONT_SIZE)
        except Exception:
            font = None

        vr = self._visible_rect()
        pygame.draw.rect(surface, bg, self.rect)

        # Clip rendering to visible area
        old_clip = surface.get_clip()
        surface.set_clip(vr.clip(old_clip) if old_clip else vr)

        try:
            for i, row in enumerate(self._rows):
                row_y = vr.y + i * self._row_height - self._scroll_offset
                if row_y + self._row_height < vr.y:
                    continue
                if row_y > vr.bottom:
                    break
                rr = Rect(vr.x, row_y, vr.width, self._row_height)
                node = row.node
                depth = row.depth
                # Row background
                if node is self._selected_node:
                    pygame.draw.rect(surface, sel_col, rr)
                # Arrow for non-leaf nodes
                if not node.is_leaf:
                    ar = self._arrow_rect(rr, depth)
                    if node.expanded:
                        # Draw down-pointing arrow
                        pygame.draw.polygon(surface, arrow_col, [
                            (ar.left, ar.top),
                            (ar.right, ar.top),
                            (ar.centerx, ar.bottom),
                        ])
                    else:
                        # Draw right-pointing arrow
                        pygame.draw.polygon(surface, arrow_col, [
                            (ar.left, ar.top),
                            (ar.right, ar.centery),
                            (ar.left, ar.bottom),
                        ])
                # Label
                text_x = vr.x + depth * self._indent_width + self._indent_width + 2
                col = disabled_col if not node.enabled else text_col
                if font:
                    txt = font.render(node.label, True, col)
                    surface.blit(txt, (text_x, row_y + (self._row_height - txt.get_height()) // 2))
        finally:
            surface.set_clip(old_clip)

        # Scrollbar
        total = self._total_height()
        if self._show_scrollbar and total > self.rect.height:
            sb_x = self.rect.right - _SCROLLBAR_WIDTH
            sb_rect = Rect(sb_x, self.rect.y, _SCROLLBAR_WIDTH, self.rect.height)
            pygame.draw.rect(surface, _c("surface", (50, 50, 60)), sb_rect)
            handle_h = max(20, int(self.rect.height * self.rect.height / total))
            handle_y = self.rect.y + int((self._scroll_offset / max(1, total - self.rect.height)) * (self.rect.height - handle_h))
            pygame.draw.rect(surface, _c("medium", (110, 110, 120)), Rect(sb_x + 2, handle_y, _SCROLLBAR_WIDTH - 4, handle_h))
