from __future__ import annotations

from typing import Tuple, TYPE_CHECKING, Union

from pygame import Rect

from ..events import GuiError

if TYPE_CHECKING:
    from ..gui_manager import GuiManager
    from ..intermediates.widget import Widget
    from ...widgets.window import Window


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
        self.gui.layout_manager.grid.set_properties(anchor, width, height, spacing, use_rect)

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
        """Set linear layout properties."""
        if item_width <= 0:
            raise GuiError(f'linear item_width must be positive, got: {item_width}')
        if item_height <= 0:
            raise GuiError(f'linear item_height must be positive, got: {item_height}')
        if spacing < 0:
            raise GuiError(f'linear spacing cannot be negative, got: {spacing}')
        if not isinstance(horizontal, bool):
            raise GuiError(f'linear horizontal must be bool, got: {horizontal}')
        if not isinstance(wrap_count, int) or wrap_count < 0:
            raise GuiError(f'linear wrap_count must be an int >= 0, got: {wrap_count}')
        if not isinstance(anchor, tuple) or len(anchor) != 2:
            raise GuiError(f'anchor must be a tuple of (x, y), got: {anchor}')
        self.gui.layout_manager.set_linear_properties(
            anchor,
            item_width,
            item_height,
            spacing,
            horizontal,
            wrap_count,
            use_rect,
        )

    def set_anchor_bounds(self, bounds: Rect) -> None:
        """Set anchor layout bounds."""
        if not isinstance(bounds, Rect):
            raise GuiError(f'anchor bounds must be a Rect, got: {bounds}')
        self.gui.layout_manager.set_anchor_bounds(bounds)

    def place_gui_object(self, gui_object: Union["Widget", "Window"], geometry: Union[Rect, Tuple[int, int]]) -> None:
        """Place a GUI object from layout geometry."""
        if not hasattr(gui_object, 'position'):
            raise GuiError(f'gui_object must expose a position property, got: {gui_object}')
        if isinstance(geometry, Rect):
            gui_object.position = geometry.topleft
            return
        if isinstance(geometry, tuple) and len(geometry) == 2:
            gui_object.position = geometry
            return
        raise GuiError(f'geometry must be a Rect or (x, y) tuple, got: {geometry}')
