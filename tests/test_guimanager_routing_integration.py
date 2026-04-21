import unittest

from gui_manager_test_factory import build_routing_stub
from gui.utility.events import Event
from gui.utility.gui_manager import GuiManager
from gui.utility.scheduling.task_event import TaskEvent
from gui.utility.scheduling.task_kind import TaskKind
from gui.widgets.window import Window


class SimpleEvent:
    def __init__(self, event_type: Event, **kwargs: object) -> None:
        self.type = event_type
        self.window = None
        self.task_panel = False
        for key, value in kwargs.items():
            setattr(self, key, value)


class TaskPanelStub:
    def __init__(self) -> None:
        self.visible = True
        self.events = []

    def handle_event(self, event) -> None:
        self.events.append(event)


class GuiManagerRoutingIntegrationTests(unittest.TestCase):
    def _build_manager_stub(self):
        return build_routing_stub()

    def _build_window_stub(self):
        window = Window.__new__(Window)
        window._visible = True
        window.events = []
        window.handle_event = lambda event: window.events.append(event)
        return window

    def test_task_event_routes_to_owned_window(self) -> None:
        gui = self._build_manager_stub()
        owner = self._build_window_stub()
        gui.windows.append(owner)
        GuiManager.set_task_owner(gui, "task-1", owner)
        event = TaskEvent(TaskKind.Finished, "task-1")

        GuiManager.dispatch_event(gui, event)

        self.assertEqual(owner.events, [event])
        self.assertEqual(gui._screen_events, [])

    def test_task_panel_event_routes_to_task_panel_handler(self) -> None:
        gui = self._build_manager_stub()
        panel = TaskPanelStub()
        gui.task_panel = panel
        event = SimpleEvent(Event.Widget, task_panel=True, widget_id="w")

        GuiManager.dispatch_event(gui, event)

        self.assertEqual(panel.events, [event])
        self.assertEqual(gui._screen_events, [])

    def test_window_scoped_event_routes_to_window_handler(self) -> None:
        gui = self._build_manager_stub()
        window = self._build_window_stub()
        gui.windows.append(window)
        event = SimpleEvent(Event.Widget, window=window, widget_id="w1")

        GuiManager.dispatch_event(gui, event)

        self.assertEqual(window.events, [event])
        self.assertEqual(gui._screen_events, [])

    def test_unowned_event_falls_back_to_screen_handler(self) -> None:
        gui = self._build_manager_stub()
        event = SimpleEvent(Event.KeyDown, key=27)

        GuiManager.dispatch_event(gui, event)

        self.assertEqual(gui._screen_events, [event])

    def test_key_events_route_to_active_window(self) -> None:
        gui = self._build_manager_stub()
        active = self._build_window_stub()
        other = self._build_window_stub()
        gui.windows.extend([other, active])
        gui.active_window = active

        key_down = SimpleEvent(Event.KeyDown, key=27)
        key_up = SimpleEvent(Event.KeyUp, key=27)

        GuiManager.dispatch_event(gui, key_down)
        GuiManager.dispatch_event(gui, key_up)

        self.assertEqual(active.events, [key_down, key_up])
        self.assertEqual(other.events, [])
        self.assertEqual(gui._screen_events, [])

    def test_key_events_fall_back_to_screen_when_active_window_is_not_registered(self) -> None:
        gui = self._build_manager_stub()
        stale_active = self._build_window_stub()
        gui.active_window = stale_active
        event = SimpleEvent(Event.KeyDown, key=11)

        GuiManager.dispatch_event(gui, event)

        self.assertEqual(stale_active.events, [])
        self.assertEqual(gui._screen_events, [event])

    def test_key_events_fall_back_to_screen_when_active_window_is_hidden(self) -> None:
        gui = self._build_manager_stub()
        hidden_active = self._build_window_stub()
        hidden_active._visible = False
        gui.windows.append(hidden_active)
        gui.active_window = hidden_active
        event = SimpleEvent(Event.KeyUp, key=99)

        GuiManager.dispatch_event(gui, event)

        self.assertEqual(hidden_active.events, [])
        self.assertEqual(gui._screen_events, [event])


if __name__ == "__main__":
    unittest.main()
