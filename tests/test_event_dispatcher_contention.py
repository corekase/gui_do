import unittest

import pygame
from pygame import Rect
from pygame.locals import MOUSEBUTTONDOWN

from gui.utility.constants import Event
from gui.utility.event_dispatcher import EventDispatcher
from gui.utility.focus_state import FocusStateController
from gui.utility.input_emitter import InputEventEmitter
from gui.utility.input_state import DragStateController, LockStateController


class WidgetStub:
    def __init__(self, widget_id: str) -> None:
        self.id = widget_id
        self.visible = True
        self.hit_rect = None
        self.draw_rect = Rect(0, 0, 100, 100)
        self.window = None

    def get_collide(self, _window) -> bool:
        return True

    def should_handle_outside_collision(self) -> bool:
        return False

    def build_gui_event(self, window=None):
        return window.gui.event(Event.Widget, widget_id=self.id, window=window)


class WindowStub:
    def __init__(self, gui, widgets) -> None:
        self.gui = gui
        self.widgets = widgets
        self.visible = True
        self.x = 0
        self.y = 0

    def get_window_rect(self):
        return Rect(0, 0, 100, 100)

    def get_title_bar_rect(self):
        return Rect(0, 0, 100, 16)

    def get_widget_rect(self):
        return Rect(80, 0, 20, 16)


class TaskPanelStub:
    def __init__(self, widgets) -> None:
        self.widgets = widgets
        self.visible = True

    def get_rect(self):
        return Rect(0, 0, 100, 100)


class ContentionGuiStub:
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
        self.handled = []
        self.lock_cleared = 0
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

    def handle_widget(self, widget, _event, window=None):
        area = "screen"
        if self.task_panel is not None and window is self.task_panel:
            area = "panel"
        elif window is not None:
            area = "window"
        if widget is self.locking_object:
            area = "lock"
        self.handled.append((widget.id, area))
        return True

    def raise_window(self, _window):
        return None

    def lower_window(self, _window):
        return None

    def set_lock_area(self, _locking_object, _area=None):
        self.locking_object = None
        self.lock_cleared += 1

    def set_mouse_pos(self, pos, _update_physical_coords=True):
        self.mouse_pos = pos


class EventDispatcherContentionBatch2Tests(unittest.TestCase):
    def test_registered_locking_object_overrides_panel_window_and_screen(self) -> None:
        gui = ContentionGuiStub()
        lock_widget = WidgetStub("lock")
        panel_widget = WidgetStub("panel")
        window_widget = WidgetStub("window")
        screen_widget = WidgetStub("screen")

        gui.locking_object = lock_widget
        gui.widgets = [screen_widget, lock_widget]
        gui.task_panel = TaskPanelStub([panel_widget])
        window = WindowStub(gui, [window_widget])
        gui.windows = [window]
        gui.active_window = window

        dispatcher = EventDispatcher(gui)
        event = dispatcher.handle(pygame.event.Event(MOUSEBUTTONDOWN, {"button": 1, "pos": (5, 5)}))

        self.assertEqual(event.type, Event.Widget)
        self.assertEqual(event.widget_id, "lock")
        self.assertEqual(gui.handled, [("lock", "lock")])

    def test_unregistered_locking_object_is_cleared_then_panel_handles(self) -> None:
        gui = ContentionGuiStub()
        lock_widget = WidgetStub("lock")
        panel_widget = WidgetStub("panel")
        window_widget = WidgetStub("window")

        gui.locking_object = lock_widget
        gui.widgets = []
        gui.task_panel = TaskPanelStub([panel_widget])
        window = WindowStub(gui, [window_widget])
        gui.windows = [window]
        gui.active_window = window

        dispatcher = EventDispatcher(gui)
        first = dispatcher.handle(pygame.event.Event(MOUSEBUTTONDOWN, {"button": 1, "pos": (5, 5)}))
        second = dispatcher.handle(pygame.event.Event(MOUSEBUTTONDOWN, {"button": 1, "pos": (5, 5)}))

        self.assertEqual(gui.lock_cleared, 1)
        self.assertEqual(first.type, Event.Pass)
        self.assertEqual(second.type, Event.Widget)
        self.assertEqual(second.widget_id, "panel")
        self.assertEqual(gui.handled, [("panel", "panel")])

    def test_without_lock_or_panel_window_handles_before_screen(self) -> None:
        gui = ContentionGuiStub()
        window_widget = WidgetStub("window")
        screen_widget = WidgetStub("screen")

        gui.widgets = [screen_widget]
        window = WindowStub(gui, [window_widget])
        gui.windows = [window]
        gui.active_window = window

        dispatcher = EventDispatcher(gui)
        event = dispatcher.handle(pygame.event.Event(MOUSEBUTTONDOWN, {"button": 1, "pos": (5, 5)}))

        self.assertEqual(event.type, Event.Widget)
        self.assertEqual(event.widget_id, "window")
        self.assertEqual(gui.handled, [("window", "window")])


if __name__ == "__main__":
    unittest.main()
