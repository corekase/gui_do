from __future__ import annotations

from typing import Optional, Tuple, TYPE_CHECKING

from pygame import Rect

from ..events import GuiError
from ..lock_state_model import LockState
from ..widget import Widget

if TYPE_CHECKING:
    from ..gui_manager import GuiManager


class LockStateController:
    """Encapsulates input-lock lifecycle and clamping semantics."""

    def __init__(self, gui_manager: "GuiManager") -> None:
        """Bind lock-state operations to a specific GUI manager."""
        self.gui: "GuiManager" = gui_manager

    @property
    def state(self):
        """Return the mutable lock-state model owned by the manager."""
        return self.gui._lock_state

    def _commit_lock_mutation(self, mutation) -> None:
        """Apply a mutation callback to the shared lock-state model."""
        mutation(self.state)

    def _is_registered_object(self, value: Widget) -> bool:
        """Return registration status via object registry when available."""
        registry = getattr(self.gui, 'object_registry', None)
        if registry is not None and hasattr(registry, 'is_registered_object'):
            return bool(registry.is_registered_object(value))
        return False

    def _assign_area_lock(self, locking_object: Widget) -> None:
        """Assign area lock using current lock-area rectangle."""
        area = self.state.lock_area_rect
        if area is None:
            raise GuiError('lock area must be set before assigning area lock')
        self._commit_lock_mutation(lambda state: state.apply_area_lock(locking_object, area))

    def _assign_point_lock(self, locking_object: Widget, point: Tuple[int, int]) -> None:
        """Assign point lock to a specific widget and lock anchor."""
        self._commit_lock_mutation(lambda state: state.apply_point_lock(locking_object, point))

    def _restore_physical_mouse_on_unlock(self) -> None:
        """Restore hardware pointer when releasing an active mouse lock."""
        if not self.state.mouse_locked:
            return
        if self.state.mouse_point_locked and self.state.lock_point_pos is not None:
            self.gui.pointer.set_physical_mouse_pos(self.state.lock_point_pos)
            self.gui.mouse_pos = self.state.lock_point_pos
            return
        self.gui.pointer.set_physical_mouse_pos(self.gui.mouse_pos)

    def set_area(self, locking_object: Optional[Widget], area: Optional[Rect] = None) -> None:
        """Set or clear area lock for a registered widget."""
        if area is not None:
            if not isinstance(area, Rect):
                raise GuiError('lock area must be a Rect')
            if locking_object is None:
                raise GuiError('locking_object is required when setting a lock area')
            if not isinstance(locking_object, Widget):
                raise GuiError('locking_object must be a widget')
            if not self._is_registered_object(locking_object):
                raise GuiError('locking_object must be a registered widget')
            if area.width <= 0 or area.height <= 0:
                raise GuiError('lock area dimensions must be positive')
            self._commit_lock_mutation(lambda state: setattr(state, 'lock_area_rect', area))
            self._assign_area_lock(locking_object)
        else:
            # Clearing lock restores pointer before wiping lock-state fields.
            self._restore_physical_mouse_on_unlock()
            self.clear()

    def set_point(self, locking_object: Optional[Widget], point: Optional[Tuple[int, int]] = None) -> None:
        """Set or clear point lock for a registered widget."""
        if locking_object is None:
            self.set_area(None)
            return
        if not isinstance(locking_object, Widget):
            raise GuiError('locking_object must be a widget')
        if not self._is_registered_object(locking_object):
            raise GuiError('locking_object must be a registered widget')
        if point is None:
            point = self.gui.input_providers.mouse_get_pos()
        if not isinstance(point, tuple) or len(point) != 2:
            raise GuiError(f'point must be a tuple of (x, y), got: {point}')
        self._assign_point_lock(locking_object, point)

    def resolve(self) -> Optional[Widget]:
        """Return valid locking widget, clearing stale/invalid lock state as needed."""
        locking_object = self.state.locking_object
        if locking_object is None:
            if self.state.mouse_locked or self.state.lock_area_rect is not None or self.state.lock_point_pos is not None:
                self.clear()
            return None
        if not isinstance(locking_object, Widget):
            self.clear()
            return None
        if not self._is_registered_object(locking_object):
            self.clear()
            return None
        if self.state.lock_area_rect is None and self.state.lock_point_pos is None:
            self.clear()
            return None
        return locking_object

    def clamp_position(self, position: Tuple[int, int]) -> Tuple[int, int]:
        """Clamp a position into the active lock area when area lock is enabled."""
        if not isinstance(position, tuple) or len(position) != 2:
            raise GuiError(f'position must be a tuple of (x, y), got: {position}')
        self.resolve()
        lock_area_rect = self.state.lock_area_rect
        if lock_area_rect is None:
            return position
        x, y = position
        max_x = lock_area_rect.right - 1
        max_y = lock_area_rect.bottom - 1
        if x < lock_area_rect.left:
            x = lock_area_rect.left
        elif x > max_x:
            x = max_x
        if y < lock_area_rect.top:
            y = lock_area_rect.top
        elif y > max_y:
            y = max_y
        return (x, y)

    def enforce_point_lock(self, hardware_position: Tuple[int, int]) -> None:
        """Recenter hardware pointer when point-lock recenter constraints are violated."""
        if self.state.lock_point_pos is None:
            self._commit_lock_mutation(lambda state: setattr(state, 'lock_point_recenter_pending', False))
            return
        if not isinstance(hardware_position, tuple) or len(hardware_position) != 2:
            raise GuiError(f'hardware_position must be a tuple of (x, y), got: {hardware_position}')
        in_recenter_rect = self.gui.point_lock_recenter_rect.collidepoint(hardware_position)
        if self.state.lock_point_recenter_pending:
            if in_recenter_rect:
                self._commit_lock_mutation(lambda state: setattr(state, 'lock_point_recenter_pending', False))
            return
        if not in_recenter_rect:
            self.gui.pointer.set_physical_mouse_pos(self.gui.point_lock_recenter_rect.center)
            self._commit_lock_mutation(lambda state: setattr(state, 'lock_point_recenter_pending', True))

    def clear(self) -> None:
        """Clear all active lock-state fields."""
        self._commit_lock_mutation(lambda state: state.clear_lock())
