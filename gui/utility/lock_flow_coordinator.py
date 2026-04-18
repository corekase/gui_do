from __future__ import annotations

from typing import Optional, Tuple, TYPE_CHECKING

from pygame import Rect

from .widget import Widget

if TYPE_CHECKING:
    from .gui_manager import GuiManager


class LockFlowCoordinator:
    """Owns manager-level lock API flow and lock-state delegation."""

    def __init__(self, gui_manager: "GuiManager") -> None:
        self.gui: "GuiManager" = gui_manager

    def set_lock_area(self, locking_object: Optional[Widget], area: Optional[Rect] = None) -> None:
        self.gui.lock_state.set_area(locking_object, area)

    def set_lock_point(self, locking_object: Optional[Widget], point: Optional[Tuple[int, int]] = None) -> None:
        if locking_object is None:
            self.gui.set_lock_area(None)
            return
        self.gui.lock_state.set_point(locking_object, point)

    def enforce_point_lock(self, hardware_position: Tuple[int, int]) -> None:
        self.gui.lock_state.enforce_point_lock(hardware_position)

    def lock_area(self, position: Tuple[int, int]) -> Tuple[int, int]:
        return self.gui.lock_state.clamp_position(position)
