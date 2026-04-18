from gui.utility.gui_utils.drag_state_model import DragState
from gui.utility.gui_utils.lock_state_model import LockState


class StateModelBackedStub:
    """Test helper that exposes manager-style state fields through strict model objects."""

    def _init_state_models(self) -> None:
        self._drag_state = DragState()
        self._lock_state = LockState()

    @property
    def dragging(self):
        return self._drag_state.dragging

    @dragging.setter
    def dragging(self, value):
        self._drag_state.dragging = value

    @property
    def dragging_window(self):
        return self._drag_state.dragging_window

    @dragging_window.setter
    def dragging_window(self, value):
        self._drag_state.dragging_window = value

    @property
    def mouse_delta(self):
        return self._drag_state.mouse_delta

    @mouse_delta.setter
    def mouse_delta(self, value):
        self._drag_state.mouse_delta = value

    @property
    def locking_object(self):
        return self._lock_state.locking_object

    @locking_object.setter
    def locking_object(self, value):
        self._lock_state.locking_object = value

    @property
    def mouse_locked(self):
        return self._lock_state.mouse_locked

    @mouse_locked.setter
    def mouse_locked(self, value):
        self._lock_state.mouse_locked = value

    @property
    def mouse_point_locked(self):
        return self._lock_state.mouse_point_locked

    @mouse_point_locked.setter
    def mouse_point_locked(self, value):
        self._lock_state.mouse_point_locked = value

    @property
    def lock_area_rect(self):
        return self._lock_state.lock_area_rect

    @lock_area_rect.setter
    def lock_area_rect(self, value):
        self._lock_state.lock_area_rect = value

    @property
    def lock_point_pos(self):
        return self._lock_state.lock_point_pos

    @lock_point_pos.setter
    def lock_point_pos(self, value):
        self._lock_state.lock_point_pos = value

    @property
    def lock_point_recenter_pending(self):
        return self._lock_state.lock_point_recenter_pending

    @lock_point_recenter_pending.setter
    def lock_point_recenter_pending(self, value):
        self._lock_state.lock_point_recenter_pending = value

    @property
    def lock_point_tolerance_rect(self):
        return self._lock_state.lock_point_tolerance_rect

    @lock_point_tolerance_rect.setter
    def lock_point_tolerance_rect(self, value):
        self._lock_state.lock_point_tolerance_rect = value
