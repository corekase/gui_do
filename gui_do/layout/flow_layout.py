"""FlowLayout — auto-wrapping left-to-right (or top-to-bottom) item layout."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, TYPE_CHECKING

from pygame import Rect

from .layout_registry import LayoutRegistry
from .rect_source import RectSource, resolve_rect

if TYPE_CHECKING:
    from ..controls.base.ui_node import UiNode


@dataclass
class FlowItem:
    node: "UiNode"
    min_width: Optional[int] = None
    max_width: Optional[int] = None
    min_height: Optional[int] = None
    max_height: Optional[int] = None


@dataclass
class FlowRow:
    y_offset: int = 0
    used_width: int = 0
    used_height: int = 0
    items: List[FlowItem] = field(default_factory=list)

    def item_count(self) -> int:
        return len(self.items)


class FlowLayout:
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
        padding: int = 0,
        inset: int | tuple = 0,
        margin: int | tuple = 0,
    ) -> None:
        if direction not in (self.ROW, self.COLUMN):
            raise ValueError(f"direction must be 'row' or 'column', got {direction!r}")
        if align not in (self.ALIGN_START, self.ALIGN_CENTER, self.ALIGN_END):
            raise ValueError(f"align must be 'start', 'center', or 'end', got {align!r}")
        self._gap_x = int(gap_x)
        self._gap_y = int(gap_y)
        self._direction = direction
        self._align = align
        self._padding = int(padding)
        self._inset = self._parse_box_param(inset)
        self._margin = self._parse_box_param(margin)
        self._items: List[FlowItem] = []
        self._last_rows: List[FlowRow] = []

    @staticmethod
    def _parse_box_param(val):
        if isinstance(val, int):
            return (val, val, val, val)
        if isinstance(val, (tuple, list)) and len(val) == 4:
            return tuple(int(x) for x in val)
        return (0, 0, 0, 0)

    def add(self, item: FlowItem) -> None:
        self._items.append(item)

    def remove(self, item: FlowItem) -> bool:
        try:
            self._items.remove(item)
            return True
        except ValueError:
            return False

    def clear(self) -> None:
        self._items.clear()

    @property
    def items(self) -> List[FlowItem]:
        return list(self._items)

    def apply(self, container_rect: RectSource) -> int:
        container = resolve_rect(container_rect)
        pad = self._padding
        inset_l, inset_t, inset_r, inset_b = self._inset
        margin_l, margin_t, margin_r, margin_b = self._margin
        container = Rect(
            container.x + pad + inset_l + margin_l,
            container.y + pad + inset_t + margin_t,
            container.width - 2 * pad - inset_l - inset_r - margin_l - margin_r,
            container.height - 2 * pad - inset_t - inset_b - margin_t - margin_b,
        )
        if self._direction == self.ROW:
            return self._apply_row(container)
        return self._apply_column(container)

    def rows(self) -> List[FlowRow]:
        return list(self._last_rows)

    def _item_size(self, item: FlowItem) -> tuple[int, int]:
        w = item.node.rect.width
        h = item.node.rect.height
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
        max_w = container_rect.width
        cx = container_rect.x
        cy = container_rect.y

        self._last_rows = []
        current_row = FlowRow(y_offset=0)
        x_cursor = 0
        row_h = 0
        rows: List[FlowRow] = []

        for item in self._items:
            iw, ih = self._item_size(item)
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

        y = cy
        for row in rows:
            row.y_offset = y - cy
            row_h = row.used_height
            x = cx
            for item in row.items:
                iw, ih = self._item_size(item)
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
        max_h = container_rect.height
        cx = container_rect.x
        cy = container_rect.y

        self._last_rows = []
        current_col = FlowRow(y_offset=0)
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


LayoutRegistry.register("flow", FlowLayout)
