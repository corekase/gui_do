import unittest

from pygame import Rect

from gui.utility.event_dispatcher import EventDispatcher
from gui.utility.focus_state import FocusStateController
from gui.utility.input_emitter import InputEventEmitter
from gui.utility.input_state import DragStateController, LockStateController


class WindowStub:
    def __init__(self, x: int, y: int, w: int, h: int, visible: bool = True) -> None:
        self.visible = visible
        self._rect = Rect(x, y, w, h)
        self.widgets = []

    def get_window_rect(self):
        return self._rect


class ActiveWindowGuiStub:
    def __init__(self) -> None:
        self.dragging = False
        self.dragging_window = None
        self.mouse_delta = None
        self.locking_object = None
        self.task_panel = None
        self.active_window = None
        self.windows = []
        self.widgets = []
        self.mouse_locked = False
        self.mouse_pos = (0, 0)
        self.lock_area_rect = None
        self.lock_point_pos = None
        self.lock_point_recenter_pending = False
        self.lock_point_tolerance_rect = None
        self.input_emitter = InputEventEmitter(self)
        self.drag_state = DragStateController(self)
        self.focus_state = FocusStateController(self)
        self.lock_state = LockStateController(self)

    def _resolve_locking_state(self):
        return self.locking_object

    def get_mouse_pos(self):
        return self.mouse_pos

    def lock_area(self, pos):
        return pos

    def enforce_point_lock(self, _pos):
        return None

    def event(self, _event_type, **_kwargs):
        return None

    def update_focus(self, _widget):
        return None

    def update_active_window(self):
        self.focus_state.update_active_window()

    def convert_to_window(self, point, _window):
        return point

    def handle_widget(self, _widget, _event, _window=None):
        return False

    def raise_window(self, _window):
        return None

    def lower_window(self, _window):
        return None

    def set_lock_area(self, _locking_object, _area=None):
        self.locking_object = None

    def set_mouse_pos(self, pos, _update_physical_coords=True):
        self.mouse_pos = pos


class EventDispatcherActiveWindowRefreshBatch5Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.gui = ActiveWindowGuiStub()
        self.dispatcher = EventDispatcher(self.gui)

    def test_update_active_window_chooses_topmost_visible_colliding_window(self) -> None:
        back = WindowStub(0, 0, 100, 100, visible=True)
        front = WindowStub(0, 0, 100, 100, visible=True)
        self.gui.windows = [back, front]
        self.gui.mouse_pos = (10, 10)

        self.dispatcher.router._update_active_window()

        self.assertIs(self.gui.active_window, front)

    def test_update_active_window_skips_invisible_colliding_window(self) -> None:
        visible = WindowStub(0, 0, 100, 100, visible=True)
        hidden_top = WindowStub(0, 0, 100, 100, visible=False)
        self.gui.windows = [visible, hidden_top]
        self.gui.mouse_pos = (5, 5)

        self.dispatcher.router._update_active_window()

        self.assertIs(self.gui.active_window, visible)

    def test_update_active_window_clears_when_mouse_not_over_any_window(self) -> None:
        old_active = WindowStub(0, 0, 100, 100, visible=True)
        other = WindowStub(200, 200, 50, 50, visible=True)
        self.gui.windows = [other]
        self.gui.active_window = old_active
        self.gui.mouse_pos = (10, 10)

        self.dispatcher.router._update_active_window()

        self.assertIsNone(self.gui.active_window)


if __name__ == "__main__":
    unittest.main()
