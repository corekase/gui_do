import unittest

import pygame
from pygame import Rect
from pygame.locals import MOUSEBUTTONDOWN

from gui.utility.constants import Event
from gui.utility.event_dispatcher import EventDispatcher


class WidgetStub:
    def __init__(self, widget_id: str, collide: bool = True) -> None:
        self.id = widget_id
        self.visible = True
        self._collide = collide
        self.hit_rect = None
        self.draw_rect = Rect(0, 0, 10, 10)

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
        return Rect(0, 0, 100, 100)

    def get_title_bar_rect(self):
        return Rect(0, 0, 100, 12)

    def get_widget_rect(self):
        return Rect(80, 0, 20, 12)


class TaskPanelStub:
    def __init__(self, widgets) -> None:
        self.widgets = widgets
        self.visible = True

    def get_rect(self):
        return Rect(0, 0, 100, 100)


class PriorityGuiStub:
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
        self.handled_widgets = []

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

    def convert_to_window(self, point, _window):
        return point

    def handle_widget(self, widget, _event, window=None):
        self.handled_widgets.append((widget.id, window))
        return True

    def raise_window(self, _window):
        return None

    def lower_window(self, _window):
        return None

    def set_lock_area(self, _locking_object, _area=None):
        self.locking_object = None

    def set_mouse_pos(self, pos, _update_physical_coords=True):
        self.mouse_pos = pos


class IntegrationHitTestingPriorityTests(unittest.TestCase):
    def test_task_panel_widgets_take_priority_over_window_widgets(self) -> None:
        gui = PriorityGuiStub()
        panel_widget = WidgetStub("panel")
        window_widget = WidgetStub("window")

        task_panel = TaskPanelStub([panel_widget])
        window = WindowStub(gui, [window_widget])

        gui.task_panel = task_panel
        gui.windows = [window]
        gui.active_window = window

        dispatcher = EventDispatcher(gui)
        raw = pygame.event.Event(MOUSEBUTTONDOWN, {"button": 1, "pos": (5, 5)})

        result = dispatcher.handle(raw)

        self.assertEqual(result.type, Event.Widget)
        self.assertEqual(result.widget_id, "panel")
        self.assertTrue(getattr(result, "task_panel", False))
        self.assertEqual(gui.handled_widgets, [("panel", task_panel)])

    def test_window_widgets_take_priority_over_screen_widgets(self) -> None:
        gui = PriorityGuiStub()
        window_widget = WidgetStub("window")
        screen_widget = WidgetStub("screen")

        window = WindowStub(gui, [window_widget])
        gui.windows = [window]
        gui.widgets = [screen_widget]

        dispatcher = EventDispatcher(gui)
        raw = pygame.event.Event(MOUSEBUTTONDOWN, {"button": 1, "pos": (5, 5)})

        result = dispatcher.handle(raw)

        self.assertEqual(result.type, Event.Widget)
        self.assertEqual(result.widget_id, "window")
        self.assertEqual(gui.handled_widgets, [("window", window)])


if __name__ == "__main__":
    unittest.main()
