import unittest

import pygame
from pygame import Rect
from pygame.locals import MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION

from gui.utility.constants import Event
from gui.utility.event_dispatcher import EventDispatcher
from gui.utility.focus_state import FocusStateController
from gui.utility.input_emitter import InputEventEmitter
from gui.utility.input_state import DragStateController, LockStateController


class SimpleGuiEvent:
    def __init__(self, event_type: Event, **kwargs: object) -> None:
        self.type = event_type
        for key, value in kwargs.items():
            setattr(self, key, value)


class WindowStub:
    def __init__(self, x: int, y: int, title_rect: Rect, widget_rect: Rect) -> None:
        self.x = x
        self.y = y
        self.visible = True
        self._title_rect = title_rect
        self._widget_rect = widget_rect
        self._window_rect = Rect(x, y - 20, 200, 120)

    @property
    def position(self):
        return (self.x, self.y)

    @position.setter
    def position(self, value):
        self.x, self.y = value

    def get_window_rect(self) -> Rect:
        return self._window_rect

    def get_title_bar_rect(self) -> Rect:
        return self._title_rect

    def get_widget_rect(self) -> Rect:
        return self._widget_rect


class DragGuiStub:
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
        self.lowered = []
        self.set_mouse_pos_calls = []
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

    def event(self, event_type: Event, **kwargs: object):
        return SimpleGuiEvent(event_type, **kwargs)

    def update_focus(self, _widget):
        return None

    def convert_to_window(self, point, _window):
        return point

    def handle_widget(self, _widget, _event, _window=None):
        return False

    def raise_window(self, _window):
        return None

    def lower_window(self, window):
        self.lowered.append(window)

    def set_lock_area(self, _locking_object, _area=None):
        self.locking_object = None

    def set_mouse_pos(self, pos, update_physical_coords=True):
        self.mouse_pos = pos
        self.set_mouse_pos_calls.append((pos, update_physical_coords))


class EventDispatcherDraggingTests(unittest.TestCase):
    def test_drag_start_lowers_window_when_widget_control_hit(self) -> None:
        gui = DragGuiStub()
        window = WindowStub(
            x=100,
            y=120,
            title_rect=Rect(90, 100, 120, 20),
            widget_rect=Rect(95, 102, 20, 16),
        )
        gui.active_window = window
        gui.windows = [window]

        dispatcher = EventDispatcher(gui)
        raw = pygame.event.Event(MOUSEBUTTONDOWN, {"button": 1, "pos": (100, 105)})

        dispatcher.router._check_window_drag_start(raw)

        self.assertEqual(gui.lowered, [window])
        self.assertFalse(gui.dragging)

    def test_drag_start_enters_drag_mode_on_titlebar(self) -> None:
        gui = DragGuiStub()
        gui.mouse_pos = (20, 30)
        window = WindowStub(
            x=100,
            y=120,
            title_rect=Rect(90, 100, 120, 20),
            widget_rect=Rect(500, 500, 20, 16),
        )
        gui.active_window = window
        gui.windows = [window]

        dispatcher = EventDispatcher(gui)
        raw = pygame.event.Event(MOUSEBUTTONDOWN, {"button": 1, "pos": (100, 105)})

        dispatcher.router._check_window_drag_start(raw)

        self.assertTrue(gui.dragging)
        self.assertIs(gui.dragging_window, window)
        self.assertEqual(gui.mouse_delta, (80, 90))

    def test_window_drag_motion_updates_position_and_mouse(self) -> None:
        gui = DragGuiStub()
        window = WindowStub(
            x=10,
            y=15,
            title_rect=Rect(0, 0, 0, 0),
            widget_rect=Rect(0, 0, 0, 0),
        )
        gui.dragging = True
        gui.dragging_window = window
        gui.mouse_delta = (2, 3)
        gui.windows = [window]

        dispatcher = EventDispatcher(gui)
        raw = pygame.event.Event(MOUSEMOTION, {"rel": (5, -2)})

        result = dispatcher.emitter.emit_action(dispatcher.router._handle_window_dragging(raw))

        self.assertEqual(result.type, Event.Pass)
        self.assertEqual(window.position, (15, 13))
        self.assertEqual(gui.set_mouse_pos_calls[-1], ((13, 10), False))

    def test_window_drag_mouseup_releases_drag_state(self) -> None:
        gui = DragGuiStub()
        window = WindowStub(
            x=30,
            y=40,
            title_rect=Rect(0, 0, 0, 0),
            widget_rect=Rect(0, 0, 0, 0),
        )
        gui.dragging = True
        gui.dragging_window = window
        gui.mouse_delta = (3, 4)
        gui.windows = [window]

        dispatcher = EventDispatcher(gui)
        raw = pygame.event.Event(MOUSEBUTTONUP, {"button": 1})

        result = dispatcher.emitter.emit_action(dispatcher.router._handle_window_dragging(raw))

        self.assertEqual(result.type, Event.Pass)
        self.assertFalse(gui.dragging)
        self.assertIsNone(gui.dragging_window)
        self.assertIsNone(gui.mouse_delta)
        self.assertEqual(gui.set_mouse_pos_calls[-1], ((27, 36), True))


if __name__ == "__main__":
    unittest.main()
