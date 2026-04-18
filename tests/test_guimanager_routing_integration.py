import unittest

from gui_manager_test_factory import build_routing_stub
from gui.utility.constants import Event
from gui.utility.guimanager import GuiManager
from gui.widgets.window import Window


class SimpleEvent:
    def __init__(self, event_type: Event, **kwargs: object) -> None:
        self.type = event_type
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
        window.visible = True
        window.events = []
        window.handle_event = lambda event: window.events.append(event)
        return window

    def test_task_event_routes_to_owned_window(self) -> None:
        gui = self._build_manager_stub()
        owner = self._build_window_stub()
        gui.windows.append(owner)
        gui._task_owner_by_id["task-1"] = owner
        event = SimpleEvent(Event.Task, id="task-1")

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


if __name__ == "__main__":
    unittest.main()
