import unittest

import pygame
from pygame import Rect
from pygame.locals import MOUSEBUTTONDOWN, MOUSEMOTION

from gui.utility.constants import Event
from gui.utility.event_dispatcher import EventDispatcher
from gui.utility.focus_state import FocusStateController
from gui.utility.input_emitter import InputEventEmitter
from gui.utility.input_state import DragStateController, LockStateController
from state_model_backed_stub import StateModelBackedStub


class SimpleGuiEvent:
    def __init__(self, event_type: Event, **kwargs: object) -> None:
        self.type = event_type
        for key, value in kwargs.items():
            setattr(self, key, value)


class WindowStub:
    def __init__(self) -> None:
        self.x = 10
        self.y = 10
        self.visible = True
        self.widgets = []

    @property
    def position(self):
        return (self.x, self.y)

    @position.setter
    def position(self, value):
        self.x, self.y = value

    def get_window_rect(self):
        return Rect(0, 0, 100, 100)

    def get_title_bar_rect(self):
        return Rect(0, 0, 100, 20)

    def get_widget_rect(self):
        return Rect(80, 0, 20, 20)


class GuardGuiStub(StateModelBackedStub):
    def __init__(self) -> None:
        self._init_state_models()
        self.dragging = False
        self.dragging_window = None
        self.mouse_delta = None
        self.locking_object = None
        self.task_panel = None
        self.active_window = None
        self.windows = []
        self.widgets = []
        self.mouse_locked = False
        self.mouse_pos = (5, 5)
        self.lock_area_rect = None
        self.lock_point_pos = None
        self.lock_point_recenter_pending = False
        self.lock_point_tolerance_rect = None
        self.lock_clear_calls = 0
        self.input_emitter = InputEventEmitter(self)
        self.drag_state = DragStateController(self)
        self.focus_state = FocusStateController(self)
        self.lock_state = LockStateController(self)
        self.lock_state.resolve = lambda: self.locking_object

    def _resolve_locking_state(self):
        return self.locking_object

    def get_mouse_pos(self):
        return self.mouse_pos

    def lock_area(self, pos):
        return pos

    def enforce_point_lock(self, _pos):
        return None

    def event(self, event_type: Event, **kwargs: object):
        return SimpleGuiEvent(event_type, **kwargs)

    def update_focus(self, _widget):
        return None

    def update_active_window(self):
        self.focus_state.update_active_window()

    def convert_to_window(self, point, _window):
        return point

    def handle_widget(self, _widget, _event, _window=None):
        return True

    def raise_window(self, _window):
        return None

    def lower_window(self, _window):
        return None

    def set_lock_area(self, _locking_object, _area=None):
        self.locking_object = None
        self.lock_clear_calls += 1

    def set_mouse_pos(self, pos, _update_physical_coords=True):
        self.mouse_pos = pos


class EventDispatcherGuardEdgeTests(unittest.TestCase):
    def test_unregistered_locking_object_is_cleared_and_passed(self) -> None:
        gui = GuardGuiStub()

        class LockWidget:
            id = "lock"
            window = None

        gui.locking_object = LockWidget()
        dispatcher = EventDispatcher(gui)

        event = dispatcher.handle(pygame.event.Event(MOUSEBUTTONDOWN, {"button": 1, "pos": (5, 5)}))

        self.assertEqual(event.type, Event.Pass)
        self.assertEqual(gui.lock_clear_calls, 1)
        self.assertIsNone(gui.locking_object)

    def test_dragging_with_missing_drag_window_resets_drag_state(self) -> None:
        gui = GuardGuiStub()
        gui.dragging = True
        gui.dragging_window = None
        gui.mouse_delta = (1, 1)
        dispatcher = EventDispatcher(gui)

        event = dispatcher.handle(pygame.event.Event(MOUSEMOTION, {"rel": (1, 1), "pos": (6, 6)}))

        self.assertEqual(event.type, Event.Pass)
        self.assertFalse(gui.dragging)
        self.assertIsNone(gui.dragging_window)
        self.assertIsNone(gui.mouse_delta)

    def test_dragging_with_window_not_registered_resets_drag_state(self) -> None:
        gui = GuardGuiStub()
        gui.dragging = True
        gui.dragging_window = WindowStub()
        gui.mouse_delta = (2, 3)
        gui.windows = []
        dispatcher = EventDispatcher(gui)

        event = dispatcher.handle(pygame.event.Event(MOUSEMOTION, {"rel": (2, 1), "pos": (8, 8)}))

        self.assertEqual(event.type, Event.Pass)
        self.assertFalse(gui.dragging)
        self.assertIsNone(gui.dragging_window)
        self.assertIsNone(gui.mouse_delta)


if __name__ == "__main__":
    unittest.main()
