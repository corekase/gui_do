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


def column_stack_from_anchor(*, anchor: Rect, content_bottom: int, preferred_width: int, item_gap_y: int) -> tuple[ColumnStack, int, int, int]:
    col_x = int(anchor.left)
    col_w = min(int(preferred_width), int(anchor.width))
    col_y = int(anchor.top)
    col_h = max(1, int(content_bottom) - col_y)
    stack = ColumnStack(bounds=Rect(col_x, col_y, col_w, col_h), item_gap_y=item_gap_y)
    return stack, col_x, col_w, col_y
