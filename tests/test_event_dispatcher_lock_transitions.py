import unittest

import pygame
from pygame import Rect
from pygame.locals import MOUSEBUTTONDOWN

from gui.utility.events import Event
from gui.utility.event_dispatcher import EventDispatcher
from gui.utility.focus_state import FocusStateController
from gui.utility.input_emitter import InputEventEmitter
from gui.utility.input_state import DragStateController, LockStateController


class LockWidgetStub:
    def __init__(self, widget_id: str) -> None:
        self.id = widget_id
        self.window = None
        self.visible = True
        self.hit_rect = None
        self.draw_rect = Rect(0, 0, 100, 100)

    def build_gui_event(self, window=None):
        event_gui = window.gui if window is not None else None
        if event_gui is None:
            return None
        return event_gui.event(Event.Widget, widget_id=self.id, window=window)


class LockTransitionGuiStub:
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
        self.mouse_pos = (5, 5)
        self.lock_area_rect = None
        self.lock_point_pos = None
        self.lock_point_recenter_pending = False
        self.lock_point_tolerance_rect = None
        self.lock_clear_calls = 0
        self.handled = []
        self.remove_locked_on_handle = False
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

    def event(self, event_type: Event, **kwargs):
        event = type("GuiEvent", (), {})()
        event.type = event_type
        for key, value in kwargs.items():
            setattr(event, key, value)
        return event

    def update_focus(self, _widget):
        return None

    def update_active_window(self):
        self.focus_state.update_active_window()

    def convert_to_window(self, point, _window):
        return point

    def handle_widget(self, widget, _event, _window=None):
        self.handled.append(widget.id)
        if self.remove_locked_on_handle and widget in self.widgets:
            self.widgets.remove(widget)
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


class EventDispatcherLockTransitionsBatch6Tests(unittest.TestCase):
    def test_locked_widget_removed_during_handle_then_clears_on_next_event(self) -> None:
        gui = LockTransitionGuiStub()
        lock_widget = LockWidgetStub("lock")
        gui.locking_object = lock_widget
        gui.widgets = [lock_widget]
        gui.remove_locked_on_handle = True

        dispatcher = EventDispatcher(gui)
        first = dispatcher.handle(pygame.event.Event(MOUSEBUTTONDOWN, {"button": 1, "pos": (5, 5)}))
        second = dispatcher.handle(pygame.event.Event(MOUSEBUTTONDOWN, {"button": 1, "pos": (5, 5)}))

        self.assertEqual(first.type, Event.Widget)
        self.assertEqual(first.widget_id, "lock")
        self.assertEqual(second.type, Event.Pass)
        self.assertEqual(gui.lock_clear_calls, 1)
        self.assertEqual(gui.handled, ["lock"])

    def test_locked_widget_stays_registered_across_events(self) -> None:
        gui = LockTransitionGuiStub()
        lock_widget = LockWidgetStub("lock")
        gui.locking_object = lock_widget
        gui.widgets = [lock_widget]

        dispatcher = EventDispatcher(gui)
        first = dispatcher.handle(pygame.event.Event(MOUSEBUTTONDOWN, {"button": 1, "pos": (5, 5)}))
        second = dispatcher.handle(pygame.event.Event(MOUSEBUTTONDOWN, {"button": 1, "pos": (5, 5)}))

        self.assertEqual(first.type, Event.Widget)
        self.assertEqual(second.type, Event.Widget)
        self.assertEqual(gui.lock_clear_calls, 0)
        self.assertEqual(gui.handled, ["lock", "lock"])


if __name__ == "__main__":
    unittest.main()
