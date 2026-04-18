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
    def __init__(self, widget_id: str) -> None:
        self.id = widget_id
        self.visible = True
        self.hit_rect = None
        self.draw_rect = Rect(0, 0, 200, 200)

    def get_collide(self, _window) -> bool:
        return True

    def should_handle_outside_collision(self) -> bool:
        return False

    def build_gui_event(self, window=None):
        return window.gui.event(Event.Widget, widget_id=self.id, window=window)


class WindowStub:
    def __init__(self, gui, window_id: str, widgets) -> None:
        self.gui = gui
        self.id = window_id
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


class WindowMutationGuiStub(StateModelBackedStub):
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
        self.raised = []
        self.remove_on_raise = None
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
        self.handled.append((widget.id, getattr(window, "id", None)))
        return True

    def raise_window(self, window):
        self.raised.append(getattr(window, "id", None))
        if self.remove_on_raise is not None and self.remove_on_raise in self.windows:
            self.windows.remove(self.remove_on_raise)

    def lower_window(self, _window):
        return None

    def set_lock_area(self, _locking_object, _area=None):
        self.locking_object = None

    def set_mouse_pos(self, pos, _update_physical_coords=True):
        self.mouse_pos = pos


class EventDispatcherWindowMutationBatch9Tests(unittest.TestCase):
    def test_removed_window_during_raise_is_skipped_and_next_window_handles(self) -> None:
        gui = WindowMutationGuiStub()
        window_a = WindowStub(gui, "a", [WidgetStub("wa")])
        window_b = WindowStub(gui, "b", [WidgetStub("wb")])
        gui.windows = [window_a, window_b]
        gui.active_window = window_b
        gui.remove_on_raise = window_b

        dispatcher = EventDispatcher(gui)
        result = dispatcher.handle(pygame.event.Event(MOUSEBUTTONDOWN, {"button": 1, "pos": (5, 5)}))

        self.assertEqual(result.type, Event.Widget)
        self.assertEqual(result.widget_id, "wa")
        self.assertEqual(gui.raised, ["b"])
        self.assertEqual(gui.handled, [("wa", "a")])

    def test_removed_only_window_during_raise_falls_back_to_base_mouse_event(self) -> None:
        gui = WindowMutationGuiStub()
        window_a = WindowStub(gui, "a", [WidgetStub("wa")])
        gui.windows = [window_a]
        gui.active_window = window_a
        gui.remove_on_raise = window_a

        dispatcher = EventDispatcher(gui)
        result = dispatcher.handle(pygame.event.Event(MOUSEBUTTONDOWN, {"button": 1, "pos": (5, 5)}))

        self.assertEqual(result.type, Event.MouseButtonDown)
        self.assertEqual(result.button, 1)
        self.assertEqual(gui.raised, ["a"])
        self.assertEqual(gui.handled, [])


if __name__ == "__main__":
    unittest.main()
