import unittest

import pygame
from pygame import Rect
from pygame.locals import MOUSEBUTTONDOWN

from gui.utility.event_dispatcher import EventDispatcher
from gui.utility.input_emitter import InputEventEmitter
from gui.utility.input_state import DragStateController, LockStateController


class WindowStub:
    def __init__(self, x: int, y: int, title_rect: Rect, widget_rect: Rect) -> None:
        self.x = x
        self.y = y
        self.visible = True
        self._title_rect = title_rect
        self._widget_rect = widget_rect
        self.widgets = []

    def get_window_rect(self) -> Rect:
        return Rect(self.x, self.y - 20, 200, 120)

    def get_title_bar_rect(self) -> Rect:
        return self._title_rect

    def get_widget_rect(self) -> Rect:
        return self._widget_rect


class DragStartGuiStub:
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
        self.lock_area_calls = []
        self.input_emitter = InputEventEmitter(self)
        self.drag_state = DragStateController(self)
        self.lock_state = LockStateController(self)

    def _resolve_locking_state(self):
        return self.locking_object

    def get_mouse_pos(self):
        return self.mouse_pos

    def lock_area(self, pos):
        self.lock_area_calls.append(pos)
        return pos

    def enforce_point_lock(self, _pos):
        return None

    def event(self, _event_type, **_kwargs):
        return type("GuiEvent", (), {})()

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
        if window in self.windows:
            self.windows.remove(window)

    def set_lock_area(self, _locking_object, _area=None):
        self.locking_object = None

    def set_mouse_pos(self, pos, _update_physical_coords=True):
        self.mouse_pos = pos


class EventDispatcherDragStartEdgesBatch11Tests(unittest.TestCase):
    def test_drag_start_no_active_window_is_noop(self) -> None:
        gui = DragStartGuiStub()
        dispatcher = EventDispatcher(gui)

        dispatcher.router._check_window_drag_start(pygame.event.Event(MOUSEBUTTONDOWN, {"button": 1, "pos": (10, 10)}))

        self.assertFalse(gui.dragging)
        self.assertIsNone(gui.dragging_window)
        self.assertIsNone(gui.mouse_delta)
        self.assertEqual(gui.lowered, [])

    def test_drag_start_uses_mouse_pos_when_event_pos_missing(self) -> None:
        gui = DragStartGuiStub()
        gui.mouse_pos = (25, 35)
        window = WindowStub(
            x=100,
            y=120,
            title_rect=Rect(0, 0, 200, 50),
            widget_rect=Rect(500, 500, 20, 20),
        )
        gui.active_window = window
        gui.windows = [window]
        dispatcher = EventDispatcher(gui)

        dispatcher.router._check_window_drag_start(pygame.event.Event(MOUSEBUTTONDOWN, {"button": 1}))

        self.assertTrue(gui.dragging)
        self.assertIs(gui.dragging_window, window)
        self.assertEqual(gui.mouse_delta, (75, 85))
        self.assertEqual(gui.lock_area_calls, [gui.mouse_pos, gui.mouse_pos])

    def test_drag_start_lowering_last_window_clears_active_window(self) -> None:
        gui = DragStartGuiStub()
        gui.mouse_pos = (10, 10)
        window = WindowStub(
            x=50,
            y=60,
            title_rect=Rect(0, 0, 200, 50),
            widget_rect=Rect(0, 0, 200, 50),
        )
        gui.active_window = window
        gui.windows = [window]
        dispatcher = EventDispatcher(gui)

        dispatcher.router._check_window_drag_start(pygame.event.Event(MOUSEBUTTONDOWN, {"button": 1, "pos": (10, 10)}))

        self.assertEqual(gui.lowered, [window])
        self.assertEqual(gui.windows, [])
        self.assertIsNone(gui.active_window)
        self.assertFalse(gui.dragging)


if __name__ == "__main__":
    unittest.main()
