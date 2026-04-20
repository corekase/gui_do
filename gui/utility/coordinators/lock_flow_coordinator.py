from __future__ import annotations

from typing import Optional, Tuple, TYPE_CHECKING

from pygame import Rect

from ..events import GuiError
from ..intermediates.widget import Widget

if TYPE_CHECKING:
    from ..gui_manager import GuiManager


class LockFlowCoordinator:
    """Owns manager-level lock API flow and lock-state delegation."""

    def __init__(self, gui_manager: "GuiManager") -> None:
        """Create LockFlowCoordinator."""
        self.gui: "GuiManager" = gui_manager

    @property
    def state(self):
        """Return mutable lock-state model owned by manager."""
        return self.gui._lock_state

    def set_locking_object(self, value: Optional[Widget]) -> None:
        """Set current lock owner reference."""
        self.state.locking_object = value

    def set_mouse_locked(self, value: bool) -> None:
        """Set whether any mouse lock is active."""
        if not isinstance(value, bool):
            raise GuiError('mouse_locked must be a bool')
        self.state.mouse_locked = value

    def set_mouse_point_locked(self, value: bool) -> None:
        """Set whether point-lock mode is active."""
        if not isinstance(value, bool):
            raise GuiError('mouse_point_locked must be a bool')
        self.state.mouse_point_locked = value

    def set_lock_area_rect(self, value: Optional[Rect]) -> None:
        """Set active lock area rectangle."""
        if value is not None:
            if not isinstance(value, Rect):
                raise GuiError(f'lock_area_rect must be a Rect or None, got: {value}')
            if value.width <= 0 or value.height <= 0:
                raise GuiError(f'lock_area_rect dimensions must be positive, got: {value}')
        self.state.lock_area_rect = value

    def set_lock_point_pos(self, value: Optional[Tuple[int, int]]) -> None:
        """Set active lock-point position."""
        if value is not None:
            if not isinstance(value, tuple) or len(value) != 2:
                raise GuiError(f'lock_point_pos must be a tuple of (x, y) or None, got: {value}')
            px, py = value
            if not isinstance(px, int) or not isinstance(py, int):
                raise GuiError(f'lock_point_pos values must be ints, got: {value}')
        self.state.lock_point_pos = value

    def set_lock_point_recenter_pending(self, value: bool) -> None:
        """Set point-lock recenter-pending flag."""
        try:
            self.state.set_recenter_pending(value)
        except ValueError as exc:
            raise GuiError(str(exc)) from exc

    def set_lock_point_tolerance_rect(self, value: Optional[Rect]) -> None:
        """Set optional tolerance rectangle for lock-point release."""
        if value is not None:
            if not isinstance(value, Rect):
                raise GuiError(f'lock_point_tolerance_rect must be a Rect or None, got: {value}')
            if value.width <= 0 or value.height <= 0:
                raise GuiError(f'lock_point_tolerance_rect dimensions must be positive, got: {value}')
        self.state.lock_point_tolerance_rect = value

    def set_release_pointer_hint(self, value: Optional[Tuple[int, int]]) -> None:
        """Set one-shot release pointer hint."""
        try:
            self.state.set_release_pointer_hint(value)
        except ValueError as exc:
            raise GuiError(str(exc)) from exc

    def consume_release_pointer_hint(self) -> Optional[Tuple[int, int]]:
        """Consume one-shot release pointer hint."""
        return self.state.consume_release_pointer_hint()

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
