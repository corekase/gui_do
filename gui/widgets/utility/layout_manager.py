from pygame import Rect

class LayoutManager:
    def __init__(self):
        self.anchor = (0, 0)
        self.cell_width = 0
        self.cell_height = 0
        self.spacing = 0
        self.use_rect = True

    def set_properties(self, anchor, width, height, spacing, use_rect=True):
        self.anchor = anchor
        self.cell_width = width
        self.cell_height = height
        self.spacing = spacing
        self.use_rect = use_rect

    def get_cell(self, x, y):
        base_x, base_y = self.anchor
        x_pos = base_x + (x * self.cell_width) + (x * self.spacing)
        y_pos = base_y + (y * self.cell_height) + (y * self.spacing)
        if self.use_rect:
            return Rect(x_pos, y_pos, self.cell_width, self.cell_height)
        return (x_pos, y_pos)
