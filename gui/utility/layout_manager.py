from pygame import Rect
from typing import Tuple, Union

class LayoutManager:
    def __init__(self) -> None:
        self.anchor: Tuple[int, int] = (0, 0)
        self.cell_width: int = 0
        self.cell_height: int = 0
        self.spacing: int = 0
        self.use_rect: bool = True

    def set_properties(self, anchor: Tuple[int, int], width: int, height: int, spacing: int, use_rect: bool = True) -> None:
        self.anchor = anchor
        self.cell_width = width
        self.cell_height = height
        self.spacing = spacing
        self.use_rect = use_rect

    def get_cell(self, x: int, y: int) -> Union[Rect, Tuple[int, int]]:
        base_x, base_y = self.anchor
        x_pos = base_x + (x * self.cell_width) + (x * self.spacing)
        y_pos = base_y + (y * self.cell_height) + (y * self.spacing)
        if self.use_rect:
            return Rect(x_pos, y_pos, self.cell_width, self.cell_height)
        return (x_pos, y_pos)
