import unittest

import pygame
from pygame import Rect
from pygame.locals import KEYDOWN, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION

from gui.utility.events import Event
from gui.utility.event_dispatcher import EventDispatcher
from gui.utility.focus_state import FocusStateController
from gui.utility.input.input_emitter import InputEventEmitter
from gui.utility.input.drag_state_controller import DragStateController
from gui.utility.input.lock_state_controller import LockStateController
from state_model_backed_stub import StateModelBackedStub


class WidgetStub:
    def __init__(self, widget_id: str, gui=None, collide: bool = True) -> None:
        self.id = widget_id
        self.gui = gui
        self.visible = True
        self._collide = collide
        self.hit_rect = None
        self.draw_rect = Rect(0, 0, 200, 200)

    def get_collide(self, _window) -> bool:
        return self._collide

    def should_handle_outside_collision(self) -> bool:
        return False

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


class StreamGuiStub(StateModelBackedStub):
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

    def handle_widget(self, widget, event, window=None):
        area = "screen"
        if self.task_panel is not None and window is self.task_panel:
            area = "panel"
        elif window is not None:
            area = "window"
        self.handled.append((widget.id, area, event.type))
        return event.type in (MOUSEBUTTONDOWN, MOUSEBUTTONUP)

    def raise_window(self, _window):
        return None

    def lower_window(self, _window):
        return None

    def set_lock_area(self, _locking_object, _area=None):
        self.locking_object = None

    def set_mouse_pos(self, pos, _update_physical_coords=True):
        self.mouse_pos = pos


class EventDispatcherStreamStressTests(unittest.TestCase):
    def test_high_volume_screen_stream_routes_clicks_and_focuses_widget(self) -> None:
        gui = StreamGuiStub()
        screen_widget = WidgetStub("screen", gui=gui)
        gui.widgets = [screen_widget]
        dispatcher = EventDispatcher(gui)

        emitted = []
        for i in range(180):
            emitted.append(dispatcher.handle(pygame.event.Event(MOUSEMOTION, {"pos": (10, 10), "rel": (1, 0)})))
            emitted.append(dispatcher.handle(pygame.event.Event(MOUSEBUTTONDOWN, {"button": 1, "pos": (10, 10)})))
            emitted.append(dispatcher.handle(pygame.event.Event(MOUSEBUTTONUP, {"button": 1, "pos": (10, 10)})))

        widget_events = [event for event in emitted if event.type == Event.Widget]
        pass_events = [event for event in emitted if event.type == Event.Pass]

        self.assertEqual(len(widget_events), 360)
        self.assertEqual(len(pass_events), 180)
        self.assertTrue(gui.focus_updates)
        self.assertIs(gui.focus_updates[-1], screen_widget)
        self.assertTrue(all(area == "screen" for _, area, _ in gui.handled))

    def test_high_volume_overlap_stream_keeps_task_panel_priority(self) -> None:
        gui = StreamGuiStub()
        panel_widget = WidgetStub("panel", gui=gui)
        window_widget = WidgetStub("window", gui=gui)
        screen_widget = WidgetStub("screen", gui=gui)

        gui.task_panel = TaskPanelStub([panel_widget])
        window = WindowStub(gui, [window_widget])
        gui.windows = [window]
        gui.active_window = window
        gui.widgets = [screen_widget]
        dispatcher = EventDispatcher(gui)

        emitted = []
        for _ in range(220):
            emitted.append(dispatcher.handle(pygame.event.Event(MOUSEBUTTONDOWN, {"button": 1, "pos": (8, 8)})))

        self.assertTrue(all(event.type == Event.Widget for event in emitted))
        self.assertTrue(all(getattr(event, "widget_id", None) == "panel" for event in emitted))
        self.assertTrue(all(getattr(event, "task_panel", False) for event in emitted))
        self.assertTrue(gui.handled)
        self.assertTrue(all(entry[0] == "panel" and entry[1] == "panel" for entry in gui.handled))

        handled_widget_ids = {entry[0] for entry in gui.handled}
        self.assertEqual(handled_widget_ids, {"panel"})

    def test_system_events_remain_mapped_during_large_stream(self) -> None:
        gui = StreamGuiStub()
        dispatcher = EventDispatcher(gui)

        mapped = []
        for key_code in range(100, 200):
            mapped.append(dispatcher.handle(pygame.event.Event(KEYDOWN, {"key": key_code})))

        self.assertTrue(all(event.type == Event.KeyDown for event in mapped))
        self.assertEqual([event.key for event in mapped], list(range(100, 200)))


if __name__ == "__main__":
    unittest.main()
