from __future__ import annotations


def calculate_grid_layout(anchor, cols, rows, gap, label_height, label_gap):
    """Return a list of (x, y, w, h) tuples for a grid anchored at (x, y)."""
    x0, y0, cell_w, cell_h = anchor
    layout = []
    for row in range(rows):
        for col in range(cols):
            x = x0 + col * (cell_w + gap)
            y = y0 + row * (cell_h + label_height + label_gap + gap)
            layout.append((x, y, cell_w, cell_h))
    return layout
