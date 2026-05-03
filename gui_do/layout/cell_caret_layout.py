"""Cell-caret layout helper for sequential placement across a cell grid."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence, Tuple

from pygame import Rect


@dataclass(frozen=True)
class CellCaretState:
    """Current logical caret position within the grid."""

    col: int
    row: int
    x: int
    y: int


class CellCaretLayout:
    """Places variable-size items in cells, advancing caret and overflowing by cell."""

    def __init__(
        self,
        *,
        bounds: Rect,
        cell_width: int,
        cell_height: int,
        columns: int,
        cell_sizes: Sequence[Tuple[int, int]] | None = None,
        cell_gap_x: int = 0,
        cell_gap_y: int = 0,
        item_gap_x: int = 0,
        item_gap_y: int = 0,
        flow_axis: str = "vertical",
        origin_col: int = 0,
        origin_row: int = 0,
    ) -> None:
        self.bounds = Rect(bounds)
        self.cell_width = max(1, int(cell_width))
        self.cell_height = max(1, int(cell_height))
        self.columns = max(1, int(columns))
        self.cell_gap_x = max(0, int(cell_gap_x))
        self.cell_gap_y = max(0, int(cell_gap_y))
        self.item_gap_x = max(0, int(item_gap_x))
        self.item_gap_y = max(0, int(item_gap_y))
        self._variable_mode = bool(cell_sizes)

        axis = str(flow_axis).lower().strip()
        if axis not in ("vertical", "horizontal"):
            raise ValueError("flow_axis must be 'vertical' or 'horizontal'")
        self.flow_axis = axis

        self._col = max(0, int(origin_col))
        self._row = max(0, int(origin_row))
        self._caret_x = 0
        self._caret_y = 0
        self._overflow_next_y: int | None = None

        self._cell_rects: list[Rect] = []
        self._cell_rows: list[list[int]] = []
        self._cell_index = 0
        if self._variable_mode:
            self._build_variable_cell_rects(cell_sizes)
            if not self._cell_rects:
                raise ValueError("cell_sizes must contain at least one cell size")
            self.move_to_cell(self._col, self._row)

    @property
    def state(self) -> CellCaretState:
        return CellCaretState(self._col, self._row, self._caret_x, self._caret_y)

    def move_to_cell(self, col: int, row: int = 0, *, reset_caret: bool = True) -> None:
        self._col = max(0, int(col))
        self._row = max(0, int(row))
        if self._variable_mode:
            if self._row >= len(self._cell_rows):
                raise IndexError("row index exceeds available variable-size cell rows")
            row_cells = self._cell_rows[self._row]
            if self._col >= len(row_cells):
                raise IndexError("col index exceeds available variable-size cells in row")
            self._cell_index = row_cells[self._col]
        if reset_caret:
            self._caret_x = 0
            self._caret_y = 0

    def cell_rect(self, col: int | None = None, row: int | None = None) -> Rect:
        """Return the absolute rect for a specific or current cell."""
        if self._variable_mode:
            if col is None and row is None:
                return Rect(self._cell_rects[self._cell_index])
            target_col = self._col if col is None else max(0, int(col))
            target_row = self._row if row is None else max(0, int(row))
            if target_row >= len(self._cell_rows):
                raise IndexError("row index exceeds available variable-size cell rows")
            row_cells = self._cell_rows[target_row]
            if target_col >= len(row_cells):
                raise IndexError("col index exceeds available variable-size cells in row")
            return Rect(self._cell_rects[row_cells[target_col]])

        target_col = self._col if col is None else max(0, int(col))
        target_row = self._row if row is None else max(0, int(row))
        x = self.bounds.left + (target_col * (self.cell_width + self.cell_gap_x))
        y = self.bounds.top + (target_row * (self.cell_height + self.cell_gap_y))
        return Rect(x, y, self.cell_width, self.cell_height)

    def cell_content_rect(
        self,
        *,
        col: int | None = None,
        row: int | None = None,
        padding: int | Tuple[int, int] | Tuple[int, int, int, int] = 0,
    ) -> Rect:
        """Return an inset content rect for a cell, suitable for nested layout managers."""
        left, top, right, bottom = self._normalize_padding(padding)
        cell = self.cell_rect(col, row)
        return Rect(
            cell.left + left,
            cell.top + top,
            max(1, cell.width - left - right),
            max(1, cell.height - top - bottom),
        )

    def bind_layout_manager(
        self,
        layout_manager,
        *,
        col: int | None = None,
        row: int | None = None,
        padding: int | Tuple[int, int] | Tuple[int, int, int, int] = 0,
    ) -> Rect:
        """Bind a layout manager's anchor bounds to a cell content rect and return that rect."""
        content = self.cell_content_rect(col=col, row=row, padding=padding)
        set_anchor_bounds = getattr(layout_manager, "set_anchor_bounds", None)
        if callable(set_anchor_bounds):
            set_anchor_bounds(content)
        return content

    def add(self, width: int, height: int) -> Rect:
        """Place an item at the active caret, overflowing to the next cell when needed."""
        item_w = max(1, int(width))
        item_h = max(1, int(height))

        current_cell = self._current_cell_rect()
        if item_w > current_cell.width or item_h > current_cell.height:
            raise ValueError("Item dimensions exceed cell dimensions")

        while not self._fits_in_current_cell(item_w, item_h):
            self._advance_to_next_cell()

        cell_rect = self._current_cell_rect()
        placed = Rect(
            cell_rect.left + self._caret_x,
            cell_rect.top + self._caret_y,
            item_w,
            item_h,
        )

        self._advance_caret_from_placement(placed)
        return placed

    def add_slot(self, height: int, *, width: int | None = None) -> Rect:
        """Place a full-width slot (or explicit width) in the current cell flow."""
        current = self._current_cell_rect()
        slot_w = current.width if width is None else max(1, int(width))
        return self.add(slot_w, max(1, int(height)))

    def add_slot_or_overflow(
        self,
        height: int,
        *,
        width: int | None = None,
        overflow_gap: int = 0,
    ) -> Rect:
        """Place a slot, falling back to virtual overflow placement when cell space is exhausted.

        The returned rect always preserves the requested slot height, so controls keep
        their intended internal rendering geometry even when a column's visual budget is
        tight and cannot fit additional cells.
        """
        desired_h = max(1, int(height))
        try:
            placed = self.add_slot(desired_h, width=width)
            self._overflow_next_y = int(placed.bottom + max(0, int(overflow_gap)))
            return placed
        except (OverflowError, ValueError):
            cell = self._current_cell_rect()
            slot_w = cell.width if width is None else max(1, int(width))
            start_y = cell.top if self._overflow_next_y is None else int(self._overflow_next_y)
            placed = Rect(cell.left, start_y, slot_w, desired_h)
            self._overflow_next_y = int(placed.bottom + max(0, int(overflow_gap)))
            return placed

    def add_labeled_slot(
        self,
        control_height: int,
        *,
        label_height: int,
        label_gap: int,
        width: int | None = None,
        include_label: bool = True,
    ) -> tuple[Rect | None, Rect]:
        """Place a slot and split it into label/control rects."""
        slot_h = self.labeled_slot_height(
            control_height,
            label_height=label_height,
            label_gap=label_gap,
            include_label=include_label,
        )
        slot_rect = self.add_slot(slot_h, width=width)
        if not include_label:
            return None, Rect(slot_rect)
        label_h = max(0, int(label_height))
        gap = max(0, int(label_gap))
        label_rect = Rect(slot_rect.left, slot_rect.top, slot_rect.width, label_h)
        control_rect = Rect(
            slot_rect.left,
            slot_rect.top + label_h + gap,
            slot_rect.width,
            max(1, slot_rect.height - label_h - gap),
        )
        return label_rect, control_rect

    @staticmethod
    def labeled_slot_height(
        control_height: int,
        *,
        label_height: int,
        label_gap: int,
        include_label: bool = True,
    ) -> int:
        """Compute total slot height for a control with optional label area."""
        base = max(1, int(control_height))
        if not include_label:
            return base
        return base + max(0, int(label_height)) + max(0, int(label_gap))

    @staticmethod
    def split_columns(
        bounds: Rect,
        *,
        count: int,
        gap: int = 0,
        min_width: int = 1,
        max_width: int | None = None,
        align: str = "left",
    ) -> list[Rect]:
        """Split a bounds rect into equal-width columns."""
        cols = max(1, int(count))
        col_gap = max(0, int(gap))
        minimum = max(1, int(min_width))
        usable_w = max(1, int(bounds.width) - col_gap * (cols - 1))
        col_w = max(minimum, usable_w // cols)
        if max_width is not None:
            col_w = min(col_w, max(1, int(max_width)))

        total_w = (col_w * cols) + (col_gap * (cols - 1))
        mode = str(align).lower().strip()
        if mode not in {"left", "center", "right"}:
            raise ValueError("align must be 'left', 'center', or 'right'")
        if mode == "center":
            start_x = bounds.left + max(0, (bounds.width - total_w) // 2)
        elif mode == "right":
            start_x = bounds.left + max(0, bounds.width - total_w)
        else:
            start_x = bounds.left

        return [
            Rect(start_x + idx * (col_w + col_gap), bounds.top, col_w, bounds.height)
            for idx in range(cols)
        ]

    @classmethod
    def column_stack_from_anchor(
        cls,
        *,
        anchor: Rect,
        content_bottom: int,
        preferred_width: int,
        item_gap_y: int,
    ) -> tuple["CellCaretLayout", int, int, int]:
        """Create a single-column stack aligned to a flow anchor and return stack + geometry."""
        col_x = int(anchor.left)
        col_w = min(int(preferred_width), int(anchor.width))
        col_y = int(anchor.top)
        col_h = max(1, int(content_bottom) - col_y)
        stack = cls(
            bounds=Rect(col_x, col_y, col_w, col_h),
            cell_width=col_w,
            cell_height=col_h,
            columns=1,
            item_gap_y=max(0, int(item_gap_y)),
        )
        return stack, col_x, col_w, col_y

    def _advance_caret_from_placement(self, placed: Rect) -> None:
        cell_rect = self._current_cell_rect()
        local_right = int(placed.right - cell_rect.left)
        local_bottom = int(placed.bottom - cell_rect.top)
        if self.flow_axis == "horizontal":
            self._caret_x = local_right + self.item_gap_x
            return
        self._caret_y = local_bottom + self.item_gap_y

    def _fits_in_current_cell(self, item_w: int, item_h: int) -> bool:
        cell_rect = self._current_cell_rect()
        if cell_rect.width <= 0 or cell_rect.height <= 0:
            return False
        if self._caret_x + item_w > cell_rect.width:
            return False
        if self._caret_y + item_h > cell_rect.height:
            return False
        if cell_rect.left + self._caret_x + item_w > self.bounds.right:
            return False
        if cell_rect.top + self._caret_y + item_h > self.bounds.bottom:
            return False
        return True

    def _advance_to_next_cell(self) -> None:
        if self._variable_mode:
            self._cell_index += 1
            if self._cell_index >= len(self._cell_rects):
                raise OverflowError("No remaining cell space in CellCaretLayout")
            self._sync_col_row_from_index()
            self._caret_x = 0
            self._caret_y = 0
            return

        self._col += 1
        if self._col >= self.columns:
            self._col = 0
            self._row += 1

        self._caret_x = 0
        self._caret_y = 0

        cell_rect = self._current_cell_rect()
        if cell_rect.left >= self.bounds.right or cell_rect.top >= self.bounds.bottom:
            raise OverflowError("No remaining cell space in CellCaretLayout")

    def _current_cell_rect(self) -> Rect:
        if self._variable_mode:
            return Rect(self._cell_rects[self._cell_index])
        return self.cell_rect(self._col, self._row)

    def _build_variable_cell_rects(self, cell_sizes: Sequence[Tuple[int, int]] | None) -> None:
        assert cell_sizes is not None
        x = self.bounds.left
        y = self.bounds.top
        row_height = 0
        current_row: list[int] = []

        for raw_w, raw_h in cell_sizes:
            cell_w = max(1, int(raw_w))
            cell_h = max(1, int(raw_h))
            if current_row and (x + cell_w > self.bounds.right):
                self._cell_rows.append(current_row)
                current_row = []
                x = self.bounds.left
                y += row_height + self.cell_gap_y
                row_height = 0

            rect = Rect(x, y, cell_w, cell_h)
            self._cell_rects.append(rect)
            current_row.append(len(self._cell_rects) - 1)
            x += cell_w + self.cell_gap_x
            row_height = max(row_height, cell_h)

        if current_row:
            self._cell_rows.append(current_row)

    def _sync_col_row_from_index(self) -> None:
        for row_idx, row in enumerate(self._cell_rows):
            for col_idx, index in enumerate(row):
                if index == self._cell_index:
                    self._row = row_idx
                    self._col = col_idx
                    return
        raise IndexError("Cell index out of range for variable-size layout rows")

    @staticmethod
    def _normalize_padding(
        padding: int | Tuple[int, int] | Tuple[int, int, int, int]
    ) -> Tuple[int, int, int, int]:
        if isinstance(padding, int):
            value = max(0, int(padding))
            return value, value, value, value
        values = tuple(int(v) for v in padding)
        if len(values) == 2:
            px = max(0, values[0])
            py = max(0, values[1])
            return px, py, px, py
        if len(values) == 4:
            return tuple(max(0, v) for v in values)
        raise ValueError("padding must be an int, 2-tuple, or 4-tuple")
