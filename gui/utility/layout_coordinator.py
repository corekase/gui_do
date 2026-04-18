from __future__ import annotations

from typing import Tuple, TYPE_CHECKING, Union

from pygame import Rect

from .events import GuiError

if TYPE_CHECKING:
    from .gui_manager import GuiManager


class LayoutCoordinator:
    """Owns layout/grid helper validation and forwarding."""

    def __init__(self, gui_manager: "GuiManager") -> None:
        """Create LayoutCoordinator."""
        self.gui: "GuiManager" = gui_manager

    def set_grid_properties(self, anchor: Tuple[int, int], width: int, height: int, spacing: int, use_rect: bool = True) -> None:
        """Set grid properties."""
        if width <= 0:
            raise GuiError(f'grid width must be positive, got: {width}')
        if height <= 0:
            raise GuiError(f'grid height must be positive, got: {height}')
        if spacing < 0:
            raise GuiError(f'grid spacing cannot be negative, got: {spacing}')
        if not isinstance(anchor, tuple) or len(anchor) != 2:
            raise GuiError(f'anchor must be a tuple of (x, y), got: {anchor}')
        self.gui.layout_manager.set_properties(anchor, width, height, spacing, use_rect)

    def gridded(self, x: int, y: int) -> Union[Rect, Tuple[int, int]]:
        """Gridded."""
        return self.gui.layout_manager.get_cell(x, y)
