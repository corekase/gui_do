from __future__ import annotations

from pygame import Rect


class ColumnStack:
    def __init__(self, *, bounds: Rect, item_gap_y: int) -> None:
        self.bounds = Rect(bounds)
        self.item_gap_y = max(0, int(item_gap_y))
        self._cursor_y = int(self.bounds.top)

    def add_slot_or_overflow(self, height: int, overflow_gap: int = 0) -> Rect:
        _ = overflow_gap
        slot_h = max(1, int(height))
        y = self._cursor_y
        if y > self.bounds.top:
            y += self.item_gap_y
        rect = Rect(self.bounds.left, y, self.bounds.width, slot_h)
        self._cursor_y = rect.bottom
        return rect


def labeled_slot_height(control_height: int, *, label_height: int, label_gap: int, include_label: bool = True) -> int:
    base = max(1, int(control_height))
    if not include_label:
        return base
    return base + max(0, int(label_height)) + max(0, int(label_gap))


def split_columns(bounds: Rect, *, count: int, gap: int = 0, min_width: int = 1) -> list[Rect]:
    cols = max(1, int(count))
    col_gap = max(0, int(gap))
    minimum = max(1, int(min_width))
    usable_w = max(1, int(bounds.width) - col_gap * (cols - 1))
    col_w = max(minimum, usable_w // cols)
    return [
        Rect(bounds.left + idx * (col_w + col_gap), bounds.top, col_w, bounds.height)
        for idx in range(cols)
    ]

# --- Generalized, compact layout helpers for demo features ---
from typing import List, Tuple, Optional

class RowBoundsCalculator:
    @staticmethod
    def calculate(num_rows: int, height: int, padding: int = 0) -> List[Tuple[int, int]]:
        """Returns (y_start, y_end) for each row, evenly spaced."""
        row_height = (height - (num_rows - 1) * padding) // num_rows
        return [
            (i * (row_height + padding), i * (row_height + padding) + row_height)
            for i in range(num_rows)
        ]

class VerticalGridSequencePlacer:
    def __init__(self, cols: int, cell_size: Tuple[int, int], padding: int = 0):
        self.cols = cols
        self.cell_size = cell_size
        self.padding = padding
        self._count = 0
    def next(self) -> Tuple[int, int]:
        row = self._count // self.cols
        col = self._count % self.cols
        x = col * (self.cell_size[0] + self.padding)
        y = row * (self.cell_size[1] + self.padding)
        self._count += 1
        return x, y

class ControlStackLayout:
    @staticmethod
    def stack(count: int, start: int = 0, spacing: int = 8) -> List[int]:
        """Returns y positions for stacking controls vertically."""
        return [start + i * spacing for i in range(count)]


def column_flow_anchors_for(
    bounds: Rect,
    count: int,
    *,
    overall_rows: int,
    overall_columns: int,
    column_spacing: int = 8,
    row_spacing: int = 8,
    column_span: int = 1,
) -> tuple[Rect, ...]:
    """Return sequential column-flow anchors for a bounded conceptual grid.

    This mirrors the one-shot legacy behavior while keeping the implementation
    in the modern geometry helpers module.
    """
    total = max(0, int(count))
    rows = max(1, int(overall_rows))
    cols = max(1, int(overall_columns))
    gap_x = max(0, int(column_spacing))
    gap_y = max(0, int(row_spacing))
    span = max(1, int(column_span))

    box = Rect(bounds)
    total_gap_x = gap_x * max(0, rows - 1)
    total_gap_y = gap_y * max(0, cols - 1)
    cell_w = max(1, (box.width - total_gap_x) // rows)
    cell_h = max(1, (box.height - total_gap_y) // cols)

    x_counter = 0
    y_counter = 0
    anchors: list[Rect] = []
    for _ in range(total):
        if x_counter + span > rows:
            x_counter = 0
            y_counter += 1
        x = box.left + (x_counter * (cell_w + gap_x))
        y = box.top + (y_counter * (cell_h + gap_y))
        w = (cell_w * span) + (gap_x * (span - 1))
        anchors.append(Rect(x, y, w, cell_h))
        x_counter += span
    return tuple(anchors)


def column_stack_from_anchor(*, anchor: Rect, content_bottom: int, preferred_width: int, item_gap_y: int) -> tuple[ColumnStack, int, int, int]:
    col_x = int(anchor.left)
    col_w = min(int(preferred_width), int(anchor.width))
    col_y = int(anchor.top)
    col_h = max(1, int(content_bottom) - col_y)
    stack = ColumnStack(bounds=Rect(col_x, col_y, col_w, col_h), item_gap_y=item_gap_y)
    return stack, col_x, col_w, col_y


def inset_rect(rect, *, padding_x: int = 0, padding_y: int = 0) -> Rect:
    """Return rect inset by symmetric horizontal/vertical padding."""
    px = max(0, int(padding_x))
    py = max(0, int(padding_y))
    width = max(1, int(rect.width) - (px * 2))
    height = max(1, int(rect.height) - (py * 2))
    return Rect(int(rect.left) + px, int(rect.top) + py, width, height)


def centered_horizontal_strip_layout(
    *,
    left: int,
    width: int,
    y: int,
    item_count: int,
    item_height: int,
    spacing: int,
) -> list[Rect]:
    """Return equally-sized horizontal item rects centered inside a strip width."""
    count = max(1, int(item_count))
    strip_width = max(1, int(width))
    gap = max(0, int(spacing))
    slot_width = max(1, (strip_width - (gap * (count - 1))) // count)
    used_width = (slot_width * count) + (gap * (count - 1))
    strip_left = int(left) + max(0, (strip_width - used_width) // 2)

    rects = []
    for index in range(count):
        x = strip_left + (index * (slot_width + gap))
        rects.append(Rect(x, int(y), slot_width, int(item_height)))
    return rects


def split_slot_bounds(slots) -> tuple[int, int]:
    """Return the left edge of first slot and right edge of last slot."""
    if not slots:
        return 0, 0
    first = slots[0]
    last = slots[-1]
    return int(first.left), int(last.right)


def partition_rects(
    padded_rect,
    *,
    rows: int = 1,
    cols: int = 1,
    count: int = None,
    gap: int = 0,
    padding: int = 0,
    bottom_padding: int = 0,
    right_padding: int = 0,
    controls_and_status_height: int = 0,
) -> list[Rect]:
    """Partition a rect into a row-major grid of sub-rectangles."""
    x0 = getattr(padded_rect, "left", padded_rect[0]) + padding
    y0 = getattr(padded_rect, "top", padded_rect[1]) + padding
    width = getattr(padded_rect, "width", padded_rect[2]) - (padding * 2) - right_padding
    height = getattr(padded_rect, "height", padded_rect[3]) - (padding * 2) - bottom_padding - controls_and_status_height

    if rows < 1:
        rows = 1
    if cols < 1:
        cols = 1

    total_gap_x = gap * (cols - 1)
    total_gap_y = gap * (rows - 1)
    cell_w = max(1, (width - total_gap_x) // cols)
    cell_h = max(1, (height - total_gap_y) // rows)

    extra_ws = [1 if i < (width - total_gap_x) % cols else 0 for i in range(cols)]
    extra_hs = [1 if i < (height - total_gap_y) % rows else 0 for i in range(rows)]

    out = []
    yy = y0
    for r in range(rows):
        xx = x0
        h = cell_h + extra_hs[r]
        for c in range(cols):
            w = cell_w + extra_ws[c]
            out.append(Rect(xx, yy, w, h))
            xx += w + gap
            if count is not None and len(out) >= int(count):
                return out
        yy += h + gap
    return out
