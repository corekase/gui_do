from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from pygame import Rect

from ..intermediates.widget import Widget


@dataclass
class LockState:
    """Holds lock lifecycle state for input and cursor enforcement."""

    locking_object: Optional[Widget] = None
    mouse_locked: bool = False
    mouse_point_locked: bool = False
    lock_area_rect: Optional[Rect] = None
    lock_point_pos: Optional[Tuple[int, int]] = None
    lock_point_recenter_pending: bool = False
    lock_point_tolerance_rect: Optional[Rect] = None

    @staticmethod
    def _validate_lock_owner(locking_object: Widget) -> None:
        """Validate lock owner type for lock-state transitions."""
        if not isinstance(locking_object, Widget):
            raise ValueError(f'locking_object must be a Widget, got: {locking_object}')

    @staticmethod
    def _validate_area(area: Rect) -> None:
        """Validate lock area shape for area-lock transitions."""
        if not isinstance(area, Rect):
            raise ValueError(f'area must be a Rect, got: {area}')
        if area.width <= 0 or area.height <= 0:
            raise ValueError(f'area dimensions must be positive, got: {area}')

    @staticmethod
    def _validate_point(point: Tuple[int, int], label: str = 'point') -> None:
        """Validate tuple[int, int] point values for lock transitions."""
        if not isinstance(point, tuple) or len(point) != 2:
            raise ValueError(f'{label} must be a tuple of (x, y), got: {point}')
        x, y = point
        if not isinstance(x, int) or not isinstance(y, int):
            raise ValueError(f'{label} values must be ints, got: {point}')

    def has_active_lock(self) -> bool:
        """Return whether lock state currently describes an active lock."""
        return self.locking_object is not None and self.mouse_locked

    def apply_area_lock(self, locking_object: Widget, area: Rect) -> None:
        """Apply area lock."""
        self._validate_lock_owner(locking_object)
        self._validate_area(area)
        self.locking_object = locking_object
        self.mouse_locked = True
        self.mouse_point_locked = False
        self.lock_area_rect = area
        self.lock_point_pos = None
        self.lock_point_recenter_pending = False
        self.lock_point_tolerance_rect = None

    def apply_point_lock(self, locking_object: Widget, point: Tuple[int, int]) -> None:
        """Apply point lock."""
        self._validate_lock_owner(locking_object)
        self._validate_point(point)
        self.locking_object = locking_object
        self.mouse_locked = True
        self.mouse_point_locked = True
        self.lock_area_rect = None
        self.lock_point_pos = point
        self.lock_point_recenter_pending = False
        self.lock_point_tolerance_rect = None

    def clear_lock(self) -> None:
        """Clear lock."""
        self.locking_object = None
        self.mouse_locked = False
        self.mouse_point_locked = False
        self.lock_area_rect = None
        self.lock_point_pos = None
        self.lock_point_recenter_pending = False
        self.lock_point_tolerance_rect = None

    def set_recenter_pending(self, pending: bool) -> None:
        """Set point-lock recenter pending flag with strict bool validation."""
        if not isinstance(pending, bool):
            raise ValueError(f'pending must be a bool, got: {pending}')
        self.lock_point_recenter_pending = pending
