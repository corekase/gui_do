import unittest

import pygame
from pygame import Rect
from pygame.locals import MOUSEBUTTONDOWN

from gui.utility.events import Event
from gui.utility.event_dispatcher import EventDispatcher
from gui.utility.focus_state import FocusStateController
from gui.utility.input_emitter import InputEventEmitter
from gui.utility.input.drag_state_controller import DragStateController
from gui.utility.input.lock_state_controller import LockStateController
from state_model_backed_stub import StateModelBackedStub


class WidgetStub:
    def __init__(self, widget_id: str, collide: bool) -> None:
        self.id = widget_id
        self.visible = True
        self.hit_rect = None
        self.draw_rect = Rect(0, 0, 200, 200)
        self._collide = collide

    def get_collide(self, _window) -> bool:
        return self._collide

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
        return Rect(0, 0, 200, 200)

    def get_title_bar_rect(self):
        return Rect(0, 0, 200, 20)

    def get_widget_rect(self):
        return Rect(180, 0, 20, 20)


class TaskPanelStub:
    def __init__(self, widgets, visible: bool = True) -> None:
        self.widgets = widgets
        self.visible = visible

    def get_rect(self):
        return Rect(0, 0, 200, 200)


class FocusGuiStub(StateModelBackedStub):
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
        self.focus_updates = []
        self.handled = []
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

    def update_focus(self, widget):
        self.focus_updates.append(widget)

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
        self.handled.append((widget.id, area))
        return True

    def raise_window(self, _window):
        return None

    def lower_window(self, _window):
        return None

    def set_lock_area(self, _locking_object, _area=None):
        self.locking_object = None

    def set_mouse_pos(self, pos, _update_physical_coords=True):
        self.mouse_pos = pos


class EventDispatcherFocusTransitionsBatch4Tests(unittest.TestCase):
    def test_task_panel_collision_with_no_widget_hit_short_circuits_to_pass(self) -> None:
        gui = FocusGuiStub()
        gui.task_panel = TaskPanelStub([WidgetStub("panel", collide=False)], visible=True)
        window = WindowStub(gui, [WidgetStub("window", collide=True)])
        gui.windows = [window]
        gui.active_window = window
        gui.widgets = [WidgetStub("screen", collide=True)]

        dispatcher = EventDispatcher(gui)
        result = dispatcher.handle(pygame.event.Event(MOUSEBUTTONDOWN, {"button": 1, "pos": (5, 5)}))

        self.assertEqual(result.type, Event.Pass)
        self.assertEqual(gui.handled, [])
        self.assertEqual(gui.focus_updates[-1], None)

    def test_invisible_task_panel_allows_window_widget_routing(self) -> None:
        gui = FocusGuiStub()
        gui.task_panel = TaskPanelStub([WidgetStub("panel", collide=True)], visible=False)
        window_widget = WidgetStub("window", collide=True)
        window = WindowStub(gui, [window_widget])
        gui.windows = [window]
        gui.active_window = window

        dispatcher = EventDispatcher(gui)
        result = dispatcher.handle(pygame.event.Event(MOUSEBUTTONDOWN, {"button": 1, "pos": (5, 5)}))

        self.assertEqual(result.type, Event.Widget)
        self.assertEqual(result.widget_id, "window")
        self.assertEqual(gui.handled, [("window", "window")])

    def test_window_collision_without_widget_hit_does_not_fall_through_to_screen(self) -> None:
        gui = FocusGuiStub()
        window = WindowStub(gui, [WidgetStub("window", collide=False)])
        gui.windows = [window]
        gui.active_window = window
        gui.widgets = [WidgetStub("screen", collide=True)]

        dispatcher = EventDispatcher(gui)
        result = dispatcher.handle(pygame.event.Event(MOUSEBUTTONDOWN, {"button": 1, "pos": (5, 5)}))

        self.assertEqual(result.type, Event.Pass)
        self.assertEqual(gui.handled, [])
        self.assertEqual(gui.focus_updates[-1], None)


if __name__ == "__main__":
    unittest.main()
