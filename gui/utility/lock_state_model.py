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
