from __future__ import annotations

from typing import Optional, Tuple, TYPE_CHECKING

from pygame import Rect

from ..intermediates.widget import Widget

if TYPE_CHECKING:
    from ..gui_manager import GuiManager


class LockFlowCoordinator:
    """Owns manager-level lock API flow and lock-state delegation."""

    def __init__(self, gui_manager: "GuiManager") -> None:
        """Create LockFlowCoordinator."""
        self.gui: "GuiManager" = gui_manager

    def set_lock_area(self, locking_object: Optional[Widget], area: Optional[Rect] = None) -> None:
        """Set lock area."""
        self.gui.lock_state.set_area(locking_object, area)

    def set_lock_point(self, locking_object: Optional[Widget], point: Optional[Tuple[int, int]] = None) -> None:
        """Set lock point."""
        if locking_object is None:
            self.gui.set_lock_area(None)
            return
        self.gui.lock_state.set_point(locking_object, point)

    def enforce_point_lock(self, hardware_position: Tuple[int, int]) -> None:
        """Enforce point lock."""
        self.gui.lock_state.enforce_point_lock(hardware_position)

    def lock_area(self, position: Tuple[int, int]) -> Tuple[int, int]:
        """Lock area."""
        return self.gui.lock_state.clamp_position(position)
