from __future__ import annotations

from pygame import Rect
from typing import Tuple, Union

class LayoutManager:
    """Compute grid-based widget placement for GUI factory helpers.

    Layout coordinates are derived from a top-left anchor, fixed cell size,
    and optional inter-cell spacing. Callers can request either full `Rect`
    geometry or point coordinates for custom sizing logic.
    """

    def __init__(self) -> None:
        """Initialize with an empty grid definition.

        Call `set_properties` before meaningful cell lookups.
        """
        self._anchor: Tuple[int, int] = (0, 0)
        self._cell_width: int = 0
        self._cell_height: int = 0
        self._spacing: int = 0
        self._use_rect: bool = True

    def get_cell(self, x: int, y: int) -> Union[Rect, Tuple[int, int]]:
        """Return the computed geometry or origin for a grid cell index."""
        # Convert grid indices into absolute pixel-space coordinates.
        base_x, base_y = self._anchor
        x_pos = base_x + (x * self._cell_width) + (x * self._spacing)
        y_pos = base_y + (y * self._cell_height) + (y * self._spacing)
        # Return either a full cell rectangle or the cell origin as configured.
        if self._use_rect:
            return Rect(x_pos, y_pos, self._cell_width, self._cell_height)
        return (x_pos, y_pos)

    def set_properties(self, anchor: Tuple[int, int], width: int, height: int, spacing: int, use_rect: bool = True) -> None:
        """Validate and store grid layout parameters.

        Args:
            anchor: Base `(x, y)` position for cell `(0, 0)`.
            width: Positive cell width in pixels.
            height: Positive cell height in pixels.
            spacing: Non-negative spacing between adjacent cells.
            use_rect: Whether `get_cell` should return `Rect` objects.
        """
        # Reject invalid dimensions early so layout math stays well-defined.
        if width <= 0:
            raise ValueError(f'grid width must be positive, got {width}')
        if height <= 0:
            raise ValueError(f'grid height must be positive, got {height}')
        if spacing < 0:
            raise ValueError(f'grid spacing cannot be negative, got {spacing}')
        # Keep anchor validation explicit to avoid silent tuple-shape misuse.
        if not isinstance(anchor, tuple) or len(anchor) != 2:
            raise ValueError(f'anchor must be a tuple of (x, y), got {anchor}')
        # Persist the validated grid contract for subsequent cell lookups.
        self._anchor = anchor
        self._cell_width = width
        self._cell_height = height
        self._spacing = spacing
        self._use_rect = use_rect
