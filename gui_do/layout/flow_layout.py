"""FlowLayout — auto-wrapping left-to-right (or top-to-bottom) item layout.

Complements :class:`~gui_do.FlexLayout` (single axis, no wrap) and
:class:`~gui_do.GridLayout` (rigid tracks) with the common use-case of
flowing N items into rows (or columns) with automatic wrapping.

This is a pure geometry engine — it computes and mutates child ``rect``
attributes.  It does **not** call ``invalidate()``; callers should do that
after :meth:`apply`.

Usage::

    from gui_do import FlowLayout, FlowItem
    from pygame import Rect

    layout = FlowLayout(gap_x=8, gap_y=8)

    for btn in buttons:
        layout.add(FlowItem(node=btn))

    used_height = layout.apply(container_rect)

    # Or access per-row info:
    for row in layout.rows():
        print(row.item_count, row.used_width, row.used_height)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, TYPE_CHECKING

from pygame import Rect

from .rect_source import RectSource, resolve_rect

if TYPE_CHECKING:
    from ..controls.base.ui_node import UiNode


# ---------------------------------------------------------------------------
# FlowItem
# ---------------------------------------------------------------------------


@dataclass
class FlowItem:
    """Describes how one child node participates in a :class:`FlowLayout`.

    Parameters
    ----------
    node:
        The :class:`~gui_do.UiNode` to position.
    min_width:
        Minimum width override.  ``None`` uses the node's current rect width.
    max_width:
        Maximum width cap.  ``None`` means unconstrained.
    min_height:
        Minimum height override.  ``None`` uses the node's current rect height.
    max_height:
        Maximum height cap.  ``None`` means unconstrained.
    """

    node: "UiNode"
    min_width: Optional[int] = None
    max_width: Optional[int] = None
    min_height: Optional[int] = None
    max_height: Optional[int] = None


# ---------------------------------------------------------------------------
# FlowRow (result descriptor)
# ---------------------------------------------------------------------------


@dataclass
class FlowRow:
    """Describes one row of items after a :class:`FlowLayout` is applied.

    Attributes
    ----------
    items:
        The :class:`FlowItem` objects placed in this row.
    used_width:
        Total pixel width consumed by items + gaps in this row.
    used_height:
        Height of the tallest item in this row.
    y_offset:
        Top-edge Y coordinate of this row relative to the container rect.
    """

    items: List[FlowItem] = field(default_factory=list)
    used_width: int = 0
    used_height: int = 0
    y_offset: int = 0

    @property
    def item_count(self) -> int:
        return len(self.items)


# ---------------------------------------------------------------------------
# FlowLayout
# ---------------------------------------------------------------------------


class FlowLayout:
    """Auto-wrapping flow layout engine.

    Items are placed left-to-right (``direction="row"``) or top-to-bottom
    (``direction="column"``), wrapping when the container's cross-axis
    dimension is exceeded.

    Parameters
    ----------
    gap_x:
        Horizontal gap between items in pixels.
    gap_y:
        Vertical gap between rows in pixels.
    direction:
        ``"row"`` (default) — items flow horizontally, wrap vertically.
        ``"column"`` — items flow vertically, wrap horizontally.
    align:
        Cross-axis item alignment within a row/column.
        ``"start"`` (default), ``"center"``, or ``"end"``.
    """

    ROW = "row"
    COLUMN = "column"

    ALIGN_START = "start"
    ALIGN_CENTER = "center"
    ALIGN_END = "end"

    def __init__(
        self,
        gap_x: int = 4,
        gap_y: int = 4,
        *,
        direction: str = ROW,
        align: str = ALIGN_START,
    ) -> None:
        if direction not in (self.ROW, self.COLUMN):
            raise ValueError(f"direction must be 'row' or 'column', got {direction!r}")
        if align not in (self.ALIGN_START, self.ALIGN_CENTER, self.ALIGN_END):
            raise ValueError(f"align must be 'start', 'center', or 'end', got {align!r}")
        self._gap_x = int(gap_x)
        self._gap_y = int(gap_y)
        self._direction = direction
        self._align = align
        self._items: List[FlowItem] = []
        self._last_rows: List[FlowRow] = []

    # ------------------------------------------------------------------
    # Item management
    # ------------------------------------------------------------------

    def add(self, item: FlowItem) -> None:
        """Append an item to the flow."""
        self._items.append(item)

    def remove(self, item: FlowItem) -> bool:
        """Remove *item* from the flow.  Returns ``True`` if found."""
        try:
            self._items.remove(item)
            return True
        except ValueError:
            return False

    def clear(self) -> None:
        """Remove all items."""
        self._items.clear()

    @property
    def items(self) -> List[FlowItem]:
        return list(self._items)

    # ------------------------------------------------------------------
    # Apply
    # ------------------------------------------------------------------

    def apply(self, container_rect: RectSource) -> int:
        """Compute and set child rects within *container_rect*.

        Returns
        -------
        int
            Total used height (``direction="row"``) or width
            (``direction="column"``) of all placed rows/columns.
        """
        container = resolve_rect(container_rect)
        if self._direction == self.ROW:
            return self._apply_row(container)
        else:
            return self._apply_column(container)

    def rows(self) -> List[FlowRow]:
        """Return row descriptors from the last :meth:`apply` call."""
        return list(self._last_rows)

    # ------------------------------------------------------------------
    # Internal: row direction
    # ------------------------------------------------------------------

    def _item_size(self, item: FlowItem) -> tuple:
        """Return (w, h) for *item* after applying min/max constraints."""
        node = item.node
        w = node.rect.width
        h = node.rect.height
        if item.min_width is not None:
            w = max(w, item.min_width)
        if item.max_width is not None:
            w = min(w, item.max_width)
        if item.min_height is not None:
            h = max(h, item.min_height)
        if item.max_height is not None:
            h = min(h, item.max_height)
        return w, h

    def _apply_row(self, container_rect: Rect) -> int:
        """Left-to-right flow with row wrapping."""
        max_w = container_rect.width
        cx = container_rect.x
        cy = container_rect.y

        self._last_rows = []
        current_row: FlowRow = FlowRow(y_offset=0)
        x_cursor = 0
        row_h = 0

        rows: List[FlowRow] = []
        # Build rows
        for item in self._items:
            iw, ih = self._item_size(item)
            # Check if this item fits in the current row
            if current_row.items and x_cursor + iw > max_w:
                current_row.used_width = x_cursor - self._gap_x
                current_row.used_height = row_h
                rows.append(current_row)
                current_row = FlowRow(y_offset=0)
                x_cursor = 0
                row_h = 0
            current_row.items.append(item)
            x_cursor += iw + self._gap_x
            row_h = max(row_h, ih)

        if current_row.items:
            current_row.used_width = x_cursor - self._gap_x
            current_row.used_height = row_h
            rows.append(current_row)

        # Assign positions
        y = cy
        for row in rows:
            row.y_offset = y - cy
            row_h = row.used_height
            x = cx
            for item in row.items:
                iw, ih = self._item_size(item)
                # Cross-axis alignment
                if self._align == self.ALIGN_CENTER:
                    item_y = y + (row_h - ih) // 2
                elif self._align == self.ALIGN_END:
                    item_y = y + row_h - ih
                else:
                    item_y = y
                item.node.rect = Rect(x, item_y, iw, ih)
                x += iw + self._gap_x
            y += row_h + self._gap_y

        self._last_rows = rows
        total_h = (y - cy - self._gap_y) if rows else 0
        return max(0, total_h)

    def _apply_column(self, container_rect: Rect) -> int:
        """Top-to-bottom flow with column wrapping."""
        max_h = container_rect.height
        cx = container_rect.x
        cy = container_rect.y

        self._last_rows = []
        current_col: FlowRow = FlowRow(y_offset=0)
        y_cursor = 0
        col_w = 0

        cols: List[FlowRow] = []
        for item in self._items:
            iw, ih = self._item_size(item)
            if current_col.items and y_cursor + ih > max_h:
                current_col.used_width = col_w
                current_col.used_height = y_cursor - self._gap_y
                cols.append(current_col)
                current_col = FlowRow(y_offset=0)
                y_cursor = 0
                col_w = 0
            current_col.items.append(item)
            y_cursor += ih + self._gap_y
            col_w = max(col_w, iw)

        if current_col.items:
            current_col.used_width = col_w
            current_col.used_height = y_cursor - self._gap_y
            cols.append(current_col)

        x = cx
        for col in cols:
            col.y_offset = x - cx
            col_w = col.used_width
            y = cy
            for item in col.items:
                iw, ih = self._item_size(item)
                if self._align == self.ALIGN_CENTER:
                    item_x = x + (col_w - iw) // 2
                elif self._align == self.ALIGN_END:
                    item_x = x + col_w - iw
                else:
                    item_x = x
                item.node.rect = Rect(item_x, y, iw, ih)
                y += ih + self._gap_y
            x += col_w + self._gap_x

        self._last_rows = cols
        total_w = (x - cx - self._gap_x) if cols else 0
        return max(0, total_w)
