import logging
from dataclasses import dataclass
from typing import Any, Optional, Tuple, TYPE_CHECKING

from pygame import Rect

from .constants import GuiError

if TYPE_CHECKING:
    from .guimanager import GuiManager


_logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class _CursorPlacement:
    """Value object for cursor anchor, hotspot, and resulting rect."""

    anchor: Tuple[int, int]
    hotspot: Tuple[int, int]
    size: Tuple[int, int]

    def build_rect(self) -> Rect:
        return Rect(
            self.anchor[0] - self.hotspot[0],
            self.anchor[1] - self.hotspot[1],
            self.size[0],
            self.size[1],
        )


class PointerCoordinator:
    """Owns cursor state and pointer-space conversions."""

    def __init__(self, gui_manager: "GuiManager") -> None:
        self.gui: "GuiManager" = gui_manager

    def get_mouse_pos(self) -> Tuple[int, int]:
        return self.gui.lock_area(self.gui.mouse_pos)

    def set_mouse_pos(self, pos: Tuple[int, int], update_physical_coords: bool = True) -> None:
        if not isinstance(pos, tuple) or len(pos) != 2:
            raise GuiError(f'pos must be a tuple of (x, y), got: {pos}')
        self.gui.mouse_pos = self.gui.lock_area(pos)
        if update_physical_coords:
            self.set_physical_mouse_pos(self.gui.mouse_pos)

    def set_physical_mouse_pos(self, pos: Tuple[int, int]) -> None:
        try:
            self.gui.input_providers.mouse_set_pos(pos)
        except Exception as exc:
            _logger.debug('mouse_set_pos failed: %s: %s', type(exc).__name__, exc)

    def _resolve_cursor_anchor(self) -> Tuple[int, int]:
        if self.gui.cursor_rect is not None and self.gui.cursor_hotspot is not None:
            return (
                self.gui.cursor_rect.x + self.gui.cursor_hotspot[0],
                self.gui.cursor_rect.y + self.gui.cursor_hotspot[1],
            )
        if self.gui.mouse_point_locked and self.gui.lock_point_pos is not None:
            return self.gui.lock_point_pos
        return self.gui.mouse_pos

    @staticmethod
    def _build_cursor_placement(anchor: Tuple[int, int], hotspot: Tuple[int, int], size: Tuple[int, int]) -> _CursorPlacement:
        return _CursorPlacement(anchor=anchor, hotspot=hotspot, size=size)

    @staticmethod
    def _validate_point(point: Tuple[int, int], label: str) -> None:
        if not isinstance(point, tuple) or len(point) != 2:
            raise GuiError(f'{label} must be a tuple of (x, y), got: {point}')

    def _normalize_window(self, window: Optional[Any]) -> Optional[Any]:
        if window is not None and window not in self.gui.windows and window is not self.gui.task_panel:
            return None
        return window

    def set_cursor(self, name: str) -> None:
        if not isinstance(name, str) or name == '':
            raise GuiError('cursor name must be a non-empty string')
        anchor = self._resolve_cursor_anchor()
        self.gui.cursor_image, self.gui.cursor_hotspot = self.gui.bitmap_factory.get_cursor(name)
        self.gui.cursor_rect = self.gui.cursor_image.get_rect()
        placement = self._build_cursor_placement(
            anchor=anchor,
            hotspot=self.gui.cursor_hotspot,
            size=(self.gui.cursor_rect.width, self.gui.cursor_rect.height),
        )
        self.gui.cursor_rect = placement.build_rect()

    def convert_to_screen(self, point: Tuple[int, int], window: Optional[Any]) -> Tuple[int, int]:
        self._validate_point(point, 'point')
        window = self._normalize_window(window)
        if window is not None:
            x, y = point
            wx, wy = window.x, window.y
            return self.gui.lock_area((x + wx, y + wy))
        return self.gui.lock_area(point)

    def convert_to_window(self, point: Tuple[int, int], window: Optional[Any]) -> Tuple[int, int]:
        self._validate_point(point, 'point')
        window = self._normalize_window(window)
        if window is not None:
            x, y = self.gui.lock_area(point)
            wx, wy = window.x, window.y
            return (x - wx, y - wy)
        return self.gui.lock_area(point)
