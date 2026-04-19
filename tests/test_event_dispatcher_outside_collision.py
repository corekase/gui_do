import unittest

import pygame
from pygame import Rect
from pygame.locals import MOUSEBUTTONDOWN

from gui.utility.events import Event
from gui.utility.event_dispatcher import EventDispatcher
from gui.utility.focus_state import FocusStateController
from gui.utility.input.input_emitter import InputEventEmitter
from gui.utility.input.drag_state_controller import DragStateController
from gui.utility.input.lock_state_controller import LockStateController
from state_model_backed_stub import StateModelBackedStub


class WidgetStub:
    def __init__(self, widget_id: str, gui=None) -> None:
        self.id = widget_id
        self.gui = gui
        self.visible = True
        self.hit_rect = None
        self.draw_rect = Rect(50, 50, 10, 10)

    def get_collide(self, _window) -> bool:
        return False

    def should_handle_outside_collision(self) -> bool:
        return True

    def build_gui_event(self, window=None):
        event_gui = window.gui if window is not None else self.gui
        return event_gui.event(Event.Widget, widget_id=self.id, window=window)


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
    def __init__(self, widgets) -> None:
        self.widgets = widgets
        self.visible = True

    def get_rect(self):
        return Rect(0, 0, 200, 200)


class OutsideCollisionGuiStub(StateModelBackedStub):
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


class EventDispatcherOutsideCollisionBatch7Tests(unittest.TestCase):
    def test_window_widget_with_outside_collision_can_handle(self) -> None:
        gui = OutsideCollisionGuiStub()
        window_widget = WidgetStub("window", gui=gui)
        window = WindowStub(gui, [window_widget])
        gui.windows = [window]
        gui.active_window = window
        dispatcher = EventDispatcher(gui)

        result = dispatcher.handle(pygame.event.Event(MOUSEBUTTONDOWN, {"button": 1, "pos": (5, 5)}))

        self.assertEqual(result.type, Event.Widget)
        self.assertEqual(result.widget_id, "window")
        self.assertEqual(gui.handled, [("window", "window")])

    def test_task_panel_widget_with_outside_collision_can_handle(self) -> None:
        gui = OutsideCollisionGuiStub()
        panel_widget = WidgetStub("panel", gui=gui)
        gui.task_panel = TaskPanelStub([panel_widget])
        dispatcher = EventDispatcher(gui)

        result = dispatcher.handle(pygame.event.Event(MOUSEBUTTONDOWN, {"button": 1, "pos": (5, 5)}))

        self.assertEqual(result.type, Event.Widget)
        self.assertEqual(result.widget_id, "panel")
        self.assertTrue(getattr(result, "task_panel", False))
        self.assertEqual(gui.handled, [("panel", "panel")])

    def test_screen_widget_outside_collision_falls_back_to_base_mouse_event(self) -> None:
        gui = OutsideCollisionGuiStub()
        screen_widget = WidgetStub("screen", gui=gui)
        gui.widgets = [screen_widget]
        dispatcher = EventDispatcher(gui)

        result = dispatcher.handle(pygame.event.Event(MOUSEBUTTONDOWN, {"button": 1, "pos": (5, 5)}))

        self.assertEqual(result.type, Event.MouseButtonDown)
        self.assertEqual(result.button, 1)
        self.assertEqual(gui.handled, [])


if __name__ == "__main__":
    unittest.main()
