from __future__ import annotations

from pygame import Rect
from typing import Tuple, Union

Geometry = Union[Rect, Tuple[int, int]]


class GridLayout:
    """Fixed-cell grid layout strategy."""

    def __init__(self) -> None:
        self._anchor: Tuple[int, int] = (0, 0)
        self._cell_width: int = 0
        self._cell_height: int = 0
        self._spacing: int = 0
        self._use_rect: bool = True

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

    def get_cell(self, x: int, y: int) -> Geometry:
        base_x, base_y = self._anchor
        x_pos = base_x + (x * self._cell_width) + (x * self._spacing)
        y_pos = base_y + (y * self._cell_height) + (y * self._spacing)
        if self._use_rect:
            return Rect(x_pos, y_pos, self._cell_width, self._cell_height)
        return (x_pos, y_pos)


class LinearLayout:
    """One-dimensional stack layout with optional wrapping."""

    def __init__(self) -> None:
        self._anchor: Tuple[int, int] = (0, 0)
        self._item_width: int = 0
        self._item_height: int = 0
        self._spacing: int = 0
        self._horizontal: bool = True
        self._wrap_count: int = 0
        self._use_rect: bool = True

    def set_properties(
        self,
        anchor: Tuple[int, int],
        item_width: int,
        item_height: int,
        spacing: int,
        horizontal: bool = True,
        wrap_count: int = 0,
        use_rect: bool = True,
    ) -> None:
        if item_width <= 0:
            raise ValueError(f'linear item_width must be positive, got {item_width}')
        if item_height <= 0:
            raise ValueError(f'linear item_height must be positive, got {item_height}')
        if spacing < 0:
            raise ValueError(f'linear spacing cannot be negative, got {spacing}')
        if not isinstance(horizontal, bool):
            raise ValueError(f'linear horizontal must be bool, got {horizontal}')
        if not isinstance(wrap_count, int) or wrap_count < 0:
            raise ValueError(f'linear wrap_count must be an int >= 0, got {wrap_count}')
        if not isinstance(anchor, tuple) or len(anchor) != 2:
            raise ValueError(f'anchor must be a tuple of (x, y), got {anchor}')
        self._anchor = anchor
        self._item_width = item_width
        self._item_height = item_height
        self._spacing = spacing
        self._horizontal = horizontal
        self._wrap_count = wrap_count
        self._use_rect = use_rect

    def get_item(self, index: int) -> Geometry:
        if not isinstance(index, int) or index < 0:
            raise ValueError(f'linear index must be an int >= 0, got {index}')
        base_x, base_y = self._anchor
        if self._wrap_count > 0:
            major = index % self._wrap_count
            minor = index // self._wrap_count
        else:
            major = index
            minor = 0
        if self._horizontal:
            x_pos = base_x + (major * (self._item_width + self._spacing))
            y_pos = base_y + (minor * (self._item_height + self._spacing))
        else:
            x_pos = base_x + (minor * (self._item_width + self._spacing))
            y_pos = base_y + (major * (self._item_height + self._spacing))
        if self._use_rect:
            return Rect(x_pos, y_pos, self._item_width, self._item_height)
        return (x_pos, y_pos)


class AnchorLayout:
    """Bounds-based anchor positioning for one-off placements."""

    _VALID_ANCHORS = {
        'top_left',
        'top_center',
        'top_right',
        'center_left',
        'center',
        'center_right',
        'bottom_left',
        'bottom_center',
        'bottom_right',
    }

    def __init__(self) -> None:
        self._bounds: Rect = Rect(0, 0, 0, 0)

    def set_bounds(self, bounds: Rect) -> None:
        if not isinstance(bounds, Rect):
            raise ValueError(f'anchor bounds must be a Rect, got {bounds}')
        self._bounds = Rect(bounds)

    def place(
        self,
        size: Tuple[int, int],
        anchor: str = 'center',
        margin: Tuple[int, int] = (0, 0),
        use_rect: bool = True,
    ) -> Geometry:
        if not isinstance(size, tuple) or len(size) != 2 or size[0] <= 0 or size[1] <= 0:
            raise ValueError(f'anchor size must be a tuple of positive ints (w, h), got {size}')
        if not isinstance(anchor, str) or anchor not in self._VALID_ANCHORS:
            raise ValueError(f'anchor must be one of {sorted(self._VALID_ANCHORS)}, got {anchor}')
        if not isinstance(margin, tuple) or len(margin) != 2:
            raise ValueError(f'margin must be a tuple of (x, y), got {margin}')
        margin_x, margin_y = margin
        if not isinstance(margin_x, int) or not isinstance(margin_y, int):
            raise ValueError(f'margin values must be ints, got {margin}')

        width, height = size
        placement = Rect(0, 0, width, height)
        bounds = self._bounds

        if anchor in ('top_left', 'center_left', 'bottom_left'):
            placement.x = bounds.left + margin_x
        elif anchor in ('top_center', 'center', 'bottom_center'):
            placement.centerx = bounds.centerx + margin_x
        else:
            placement.right = bounds.right - margin_x

        if anchor in ('top_left', 'top_center', 'top_right'):
            placement.y = bounds.top + margin_y
        elif anchor in ('center_left', 'center', 'center_right'):
            placement.centery = bounds.centery + margin_y
        else:
            placement.bottom = bounds.bottom - margin_y

        if use_rect:
            return placement
        return placement.topleft

class LayoutManager:
    """Layout system exposing grid, linear, and anchor placement helpers."""

    def __init__(self) -> None:
        self.grid: GridLayout = GridLayout()
        self.linear: LinearLayout = LinearLayout()
        self.anchor: AnchorLayout = AnchorLayout()
        self._active_linear_index: int = 0

    def set_linear_properties(
        self,
        anchor: Tuple[int, int],
        item_width: int,
        item_height: int,
        spacing: int,
        horizontal: bool = True,
        wrap_count: int = 0,
        use_rect: bool = True,
    ) -> None:
        """Configure linear stack layout used by ``linear`` and ``next_linear``."""
        self.linear.set_properties(anchor, item_width, item_height, spacing, horizontal, wrap_count, use_rect)
        self._active_linear_index = 0

    def linear_item(self, index: int) -> Geometry:
        """Return geometry for one linear slot by index."""
        return self.linear.get_item(index)

    def next_linear_item(self) -> Geometry:
        """Return geometry for the next linear slot and advance cursor."""
        geometry = self.linear.get_item(self._active_linear_index)
        self._active_linear_index += 1
        return geometry

    def reset_linear_cursor(self) -> None:
        """Reset cursor used by ``next_linear_item``."""
        self._active_linear_index = 0

    def set_anchor_bounds(self, bounds: Rect) -> None:
        """Configure anchor layout bounds."""
        self.anchor.set_bounds(bounds)

    def anchored(
        self,
        size: Tuple[int, int],
        anchor: str = 'center',
        margin: Tuple[int, int] = (0, 0),
        use_rect: bool = True,
    ) -> Geometry:
        """Return anchored geometry for a target size inside configured bounds."""
        return self.anchor.place(size, anchor, margin, use_rect)
