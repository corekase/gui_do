from __future__ import annotations

import logging
from typing import Any, Optional, Tuple, TYPE_CHECKING

from .events import GuiError
from .input.cursor_placement import CursorPlacement

if TYPE_CHECKING:
    from .gui_manager import GuiManager


_logger = logging.getLogger(__name__)


class PointerCoordinator:
    """Owns cursor state and pointer-space conversions."""

    def __init__(self, gui_manager: "GuiManager") -> None:
        """Bind pointer operations to a GUI manager."""
        self.gui: "GuiManager" = gui_manager

    def get_mouse_pos(self) -> Tuple[int, int]:
        """Return logical mouse position clamped by active lock area."""
        return self.gui.lock_area(self.gui.mouse_pos)

    def set_mouse_pos(self, pos: Tuple[int, int], update_physical_coords: bool = True) -> None:
        """Set logical mouse position and optionally mirror to hardware cursor."""
        if not isinstance(pos, tuple) or len(pos) != 2:
            raise GuiError(f'pos must be a tuple of (x, y), got: {pos}')
        self.gui.mouse_pos = self.gui.lock_area(pos)
        if update_physical_coords:
            self.set_physical_mouse_pos(self.gui.mouse_pos)

    def set_physical_mouse_pos(self, pos: Tuple[int, int]) -> None:
        """Best-effort hardware cursor update with backend-error suppression."""
        try:
            self.gui.input_providers.mouse_set_pos(pos)
        except Exception as exc:
            _logger.debug('mouse_set_pos failed: %s: %s', type(exc).__name__, exc)

    def _resolve_cursor_anchor(self) -> Tuple[int, int]:
        """Resolve cursor anchor using hotspot rect, lock point, or mouse position."""
        if self.gui.cursor_rect is not None and self.gui.cursor_hotspot is not None:
            return (
                self.gui.cursor_rect.x + self.gui.cursor_hotspot[0],
                self.gui.cursor_rect.y + self.gui.cursor_hotspot[1],
            )
        if self.gui.mouse_point_locked and self.gui.lock_point_pos is not None:
            return self.gui.lock_point_pos
        return self.gui.mouse_pos

    @staticmethod
    def _build_cursor_placement(anchor: Tuple[int, int], hotspot: Tuple[int, int], size: Tuple[int, int]) -> CursorPlacement:
        """Build cursor placement metadata for rect construction."""
        return CursorPlacement(anchor=anchor, hotspot=hotspot, size=size)

    @staticmethod
    def _validate_point(point: Tuple[int, int], label: str) -> None:
        """Validate point tuple contract for coordinate-conversion APIs."""
        if not isinstance(point, tuple) or len(point) != 2:
            raise GuiError(f'{label} must be a tuple of (x, y), got: {point}')

    def _normalize_window(self, window: Optional[Any]) -> Optional[Any]:
        """Normalize window-like argument to known containers or `None`."""
        if window is not None and window not in self.gui.windows and window is not self.gui.task_panel:
            return None
        return window

    @staticmethod
    def _apply_window_offset(point: Tuple[int, int], window: Any, to_window: bool) -> Tuple[int, int]:
        """Convert coordinates between screen and container-local spaces."""
        x, y = point
        wx, wy = window.x, window.y
        if to_window:
            return (x - wx, y - wy)
        return (x + wx, y + wy)

    def set_cursor(self, name: str) -> None:
        """Activate registered cursor asset and preserve anchor position."""
        if not isinstance(name, str) or name == '':
            raise GuiError('cursor name must be a non-empty string')
        anchor = self._resolve_cursor_anchor()
        cursor_asset = self.gui.graphics_factory.get_cursor(name)
        self.gui.cursor_image = cursor_asset.image
        self.gui.cursor_hotspot = cursor_asset.hotspot
        self.gui.cursor_rect = self.gui.cursor_image.get_rect()
        placement = self._build_cursor_placement(
            anchor=anchor,
            hotspot=self.gui.cursor_hotspot,
            size=(self.gui.cursor_rect.width, self.gui.cursor_rect.height),
        )
        self.gui.cursor_rect = placement.build_rect()

    def convert_to_screen(self, point: Tuple[int, int], window: Optional[Any]) -> Tuple[int, int]:
        """Convert container-local point into locked screen coordinates."""
        self._validate_point(point, 'point')
        window = self._normalize_window(window)
        if window is not None:
            return self.gui.lock_area(self._apply_window_offset(point, window, to_window=False))
        return self.gui.lock_area(point)

    def convert_to_window(self, point: Tuple[int, int], window: Optional[Any]) -> Tuple[int, int]:
        """Convert screen point into container-local coordinates with lock clamping."""
        self._validate_point(point, 'point')
        window = self._normalize_window(window)
        if window is not None:
            locked_point = self.gui.lock_area(point)
            return self._apply_window_offset(locked_point, window, to_window=True)
        return self.gui.lock_area(point)
