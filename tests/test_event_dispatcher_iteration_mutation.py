import unittest

import pygame
from pygame import Rect
from pygame.locals import MOUSEBUTTONDOWN

from gui.utility.constants import Event
from gui.utility.event_dispatcher import EventDispatcher
from gui.utility.input_emitter import InputEventEmitter
from gui.utility.input_state import DragStateController, LockStateController


class WidgetStub:
    def __init__(self, widget_id: str, collide: bool = True) -> None:
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
        event_gui = window.gui if window is not None else None
        if event_gui is None:
            return None
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


class MutationGuiStub:
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
        self.focus_updates = []
        self._remove_target = None
        self.input_emitter = InputEventEmitter(self)
        self.drag_state = DragStateController(self)
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

    def convert_to_window(self, point, _window):
        return point

    def handle_widget(self, widget, _event, window=None):
        self.handled.append(widget.id)
        if self._remove_target is not None:
            if window is None:
                if self._remove_target in self.widgets:
                    self.widgets.remove(self._remove_target)
            elif self.task_panel is not None and window is self.task_panel:
                if self._remove_target in self.task_panel.widgets:
                    self.task_panel.widgets.remove(self._remove_target)
            else:
                if self._remove_target in window.widgets:
                    window.widgets.remove(self._remove_target)
        return False

    def raise_window(self, _window):
        return None

    def lower_window(self, _window):
        return None

    def set_lock_area(self, _locking_object, _area=None):
        self.locking_object = None

    def set_mouse_pos(self, pos, _update_physical_coords=True):
        self.mouse_pos = pos


class EventDispatcherIterationMutationBatch8Tests(unittest.TestCase):
    def test_screen_iteration_skips_widget_removed_mid_loop(self) -> None:
        gui = MutationGuiStub()
        first = WidgetStub("first")
        removed = WidgetStub("removed")
        gui.widgets = [removed, first]
        gui._remove_target = removed
        dispatcher = EventDispatcher(gui)

        result = dispatcher.handle(pygame.event.Event(MOUSEBUTTONDOWN, {"button": 1, "pos": (5, 5)}))

        self.assertEqual(result.type, Event.Pass)
        self.assertEqual(gui.handled, ["first"])

    def test_window_iteration_skips_widget_removed_mid_loop(self) -> None:
        gui = MutationGuiStub()
        first = WidgetStub("first")
        removed = WidgetStub("removed")
        window = WindowStub(gui, [removed, first])
        gui.windows = [window]
        gui.active_window = window
        gui._remove_target = removed
        dispatcher = EventDispatcher(gui)

        result = dispatcher.handle(pygame.event.Event(MOUSEBUTTONDOWN, {"button": 1, "pos": (5, 5)}))

        self.assertEqual(result.type, Event.Pass)
        self.assertEqual(gui.handled, ["first"])

    def test_task_panel_iteration_skips_widget_removed_mid_loop(self) -> None:
        gui = MutationGuiStub()
        first = WidgetStub("first")
        removed = WidgetStub("removed")
        gui.task_panel = TaskPanelStub([removed, first])
        gui._remove_target = removed
        dispatcher = EventDispatcher(gui)

        result = dispatcher.handle(pygame.event.Event(MOUSEBUTTONDOWN, {"button": 1, "pos": (5, 5)}))

        self.assertEqual(result.type, Event.Pass)
        self.assertEqual(gui.handled, ["first"])


if __name__ == "__main__":
    unittest.main()
