from __future__ import annotations

from pygame import Rect
from typing import Tuple, Union

class LayoutManager:
    def __init__(self) -> None:
        self._anchor: Tuple[int, int] = (0, 0)
        self._cell_width: int = 0
        self._cell_height: int = 0
        self._spacing: int = 0
        self._use_rect: bool = True

    def get_cell(self, x: int, y: int) -> Union[Rect, Tuple[int, int]]:
        base_x, base_y = self._anchor
        x_pos = base_x + (x * self._cell_width) + (x * self._spacing)
        y_pos = base_y + (y * self._cell_height) + (y * self._spacing)
        if self._use_rect:
            return Rect(x_pos, y_pos, self._cell_width, self._cell_height)
        return (x_pos, y_pos)

    def set_properties(self, anchor: Tuple[int, int], width: int, height: int, spacing: int, use_rect: bool = True) -> None:
        if width <= 0:
            raise ValueError(f'grid width must be positive, got {width}')
        if height <= 0:
            raise ValueError(f'grid height must be positive, got {height}')
        if spacing < 0:
            raise ValueError(f'grid spacing cannot be negative, got {spacing}')
        if not isinstance(anchor, tuple) or len(anchor) != 2:
            raise ValueError(f'anchor must be a tuple of (x, y), got {anchor}')
        self._anchor = anchor
        self._cell_width = width
        self._cell_height = height
        self._spacing = spacing
        self._use_rect = use_rect
