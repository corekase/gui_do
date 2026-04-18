from dataclasses import dataclass
from typing import Optional, Tuple

from pygame import Rect

from .widget import Widget


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

    def apply_area_lock(self, locking_object: Widget, area: Rect) -> None:
        self.locking_object = locking_object
        self.mouse_locked = True
        self.mouse_point_locked = False
        self.lock_area_rect = area
        self.lock_point_pos = None
        self.lock_point_recenter_pending = False
        self.lock_point_tolerance_rect = None

    def apply_point_lock(self, locking_object: Widget, point: Tuple[int, int]) -> None:
        self.locking_object = locking_object
        self.mouse_locked = True
        self.mouse_point_locked = True
        self.lock_area_rect = None
        self.lock_point_pos = point
        self.lock_point_recenter_pending = False
        self.lock_point_tolerance_rect = None

    def clear_lock(self) -> None:
        self.locking_object = None
        self.mouse_locked = False
        self.mouse_point_locked = False
        self.lock_area_rect = None
        self.lock_point_pos = None
        self.lock_point_recenter_pending = False
        self.lock_point_tolerance_rect = None
