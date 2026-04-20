import unittest

import pygame
from pygame import Rect
from pygame.locals import KEYDOWN, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION, QUIT

from gui.utility.events import Event
from gui.utility.event_dispatcher import EventDispatcher
from gui.utility.focus_state import FocusStateController
from gui.utility.input.input_emitter import InputEventEmitter
from gui.utility.input.drag_state_controller import DragStateController
from gui.utility.input.lock_state_controller import LockStateController
from state_model_backed_stub import StateModelBackedStub


class SimpleGuiEvent:
    def __init__(self, event_type: Event, **kwargs: object) -> None:
        self.type = event_type
        for key, value in kwargs.items():
            setattr(self, key, value)


class WidgetStub:
    def __init__(self, widget_id: str) -> None:
        self.id = widget_id
        self.visible = True
        self.hit_rect = None
        self.draw_rect = Rect(50, 50, 10, 10)
        self.window = None

    def get_collide(self, _window) -> bool:
        return False

    def should_handle_outside_collision(self) -> bool:
        return False

    def build_gui_event(self, window=None):
        event_gui = window.gui if window is not None else None
        if event_gui is None:
            return None
        return event_gui.event(Event.Widget, widget_id=self.id, window=window)


class OrderingWindowStub:
    def __init__(self) -> None:
        self.visible = True
        self.widgets = []
        self.x = 10
        self.y = 10

    def get_window_rect(self):
        return Rect(0, 0, 100, 100)

    def get_title_bar_rect(self):
        return Rect(0, 0, 100, 20)

    def get_widget_rect(self):
        return Rect(80, 0, 20, 20)


class OrderingGuiStub(StateModelBackedStub):
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
        self.input_emitter = InputEventEmitter(self)
        self.drag_state = DragStateController(self)
        self.focus_state = FocusStateController(self)
        self.lock_state = LockStateController(self)

    def _resolve_locking_state(self):
        return self.locking_object

    def get_mouse_pos(self):
        return self.mouse_pos

    def _get_mouse_pos(self):
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

    def _convert_to_window(self, point, _window):
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

    def _set_mouse_pos(self, pos, _update_physical_coords=False):
        self.mouse_pos = pos


class EventDispatcherOrderingBatch3Tests(unittest.TestCase):
    def test_system_event_has_priority_even_when_dragging_active(self) -> None:
        gui = OrderingGuiStub()
        gui.dragging = True
        gui.dragging_window = OrderingWindowStub()
        gui.mouse_delta = (1, 1)
        gui.windows = [gui.dragging_window]
        dispatcher = EventDispatcher(gui)

        result = dispatcher.handle(pygame.event.Event(QUIT, {}))

        self.assertEqual(result.type, Event.Quit)
        self.assertTrue(gui.dragging)

    def test_keyboard_system_mapping_short_circuits_before_drag_reset(self) -> None:
        gui = OrderingGuiStub()
        gui.dragging = True
        gui.dragging_window = None
        gui.mouse_delta = (1, 1)
        dispatcher = EventDispatcher(gui)

        result = dispatcher.handle(pygame.event.Event(KEYDOWN, {"key": 97}))

        self.assertEqual(result.type, Event.KeyDown)
        self.assertTrue(gui.dragging)
        self.assertEqual(gui.mouse_delta, (1, 1))

    def test_screen_base_mousebuttondown_when_no_widget_hit(self) -> None:
        gui = OrderingGuiStub()
        gui.widgets = [WidgetStub("screen")]
        dispatcher = EventDispatcher(gui)

        result = dispatcher.handle(pygame.event.Event(MOUSEBUTTONDOWN, {"button": 1, "pos": (5, 5)}))

        self.assertEqual(result.type, Event.MouseButtonDown)
        self.assertEqual(result.button, 1)

    def test_screen_base_mousebuttonup_when_no_widget_hit(self) -> None:
        gui = OrderingGuiStub()
        gui.widgets = [WidgetStub("screen")]
        dispatcher = EventDispatcher(gui)

        result = dispatcher.handle(pygame.event.Event(MOUSEBUTTONUP, {"button": 1, "pos": (5, 5)}))

        self.assertEqual(result.type, Event.MouseButtonUp)
        self.assertEqual(result.button, 1)

    def test_screen_base_mousemotion_when_no_widget_hit(self) -> None:
        gui = OrderingGuiStub()
        gui.widgets = [WidgetStub("screen")]
        dispatcher = EventDispatcher(gui)

        result = dispatcher.handle(pygame.event.Event(MOUSEMOTION, {"rel": (3, -1), "pos": (5, 5)}))

        self.assertEqual(result.type, Event.MouseMotion)
        self.assertEqual(result.rel, (3, -1))


if __name__ == "__main__":
    unittest.main()
