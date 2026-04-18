import unittest
from types import SimpleNamespace

from pygame import Rect

from gui.utility.constants import Event
from gui.utility.guimanager import GuiManager
from gui.utility.widget import Widget
from gui.widgets.window import Window


class GuiManagerRoiBatch6Tests(unittest.TestCase):
    def _build_manager_stub(self):
        gui = GuiManager.__new__(GuiManager)
        gui.windows = []
        gui.widgets = []
        gui.task_panel = None
        gui._task_owner_by_id = {}
        gui._screen_events = []
        gui._screen_event_handler = lambda event: gui._screen_events.append(event)
        gui.lock_area = lambda point: point
        return gui

    def test_dispatch_event_task_panel_hidden_falls_back_to_screen(self) -> None:
        gui = self._build_manager_stub()
        panel_events = []
        gui.task_panel = SimpleNamespace(visible=False, handle_event=lambda event: panel_events.append(event))
        event = SimpleNamespace(type=Event.Widget, task_panel=True)

        GuiManager.dispatch_event(gui, event)

        self.assertEqual(panel_events, [])
        self.assertEqual(gui._screen_events, [event])

    def test_dispatch_event_non_window_or_hidden_window_falls_back_to_screen(self) -> None:
        gui = self._build_manager_stub()

        not_window_event = SimpleNamespace(type=Event.Widget, window=object())
        GuiManager.dispatch_event(gui, not_window_event)

        hidden_window = Window.__new__(Window)
        hidden_window._visible = False
        hidden_window.events = []
        hidden_window.handle_event = lambda event: hidden_window.events.append(event)
        gui.windows.append(hidden_window)
        hidden_window_event = SimpleNamespace(type=Event.Widget, window=hidden_window)
        GuiManager.dispatch_event(gui, hidden_window_event)

        self.assertEqual(hidden_window.events, [])
        self.assertEqual(gui._screen_events, [not_window_event, hidden_window_event])

    def test_events_filters_pass_and_yields_non_pass(self) -> None:
        gui = self._build_manager_stub()
        gui._event_getter = lambda: ["a", "b", "c"]
        mapped = {
            "a": SimpleNamespace(type=Event.Pass),
            "b": SimpleNamespace(type=Event.Widget, marker="kept"),
            "c": SimpleNamespace(type=Event.Pass),
        }
        gui.handle_event = lambda raw: mapped[raw]

        events = list(GuiManager.events(gui))

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].marker, "kept")

    def test_event_injects_mouse_pos_for_mouse_events_only(self) -> None:
        gui = self._build_manager_stub()
        gui.get_mouse_pos = lambda: (7, 8)

        mouse_event = GuiManager.event(gui, Event.MouseMotion, rel=(1, 2))
        key_event = GuiManager.event(gui, Event.KeyDown, key=65)

        self.assertEqual(mouse_event.pos, (7, 8))
        self.assertIsNone(key_event.pos)

    def test_set_physical_mouse_pos_swallows_provider_failures(self) -> None:
        gui = self._build_manager_stub()

        def _boom(_pos):
            raise RuntimeError("mouse failure")

        gui._mouse_set_pos = _boom

        # Should not raise.
        GuiManager._set_physical_mouse_pos(gui, (1, 2))

    def test_lock_area_clamps_to_bounds(self) -> None:
        gui = self._build_manager_stub()
        gui._resolve_locking_state = lambda: None
        gui.lock_area_rect = Rect(10, 20, 5, 4)

        self.assertEqual(GuiManager.lock_area(gui, (0, 0)), (10, 20))
        self.assertEqual(GuiManager.lock_area(gui, (99, 99)), (14, 23))

    def test_enforce_point_lock_pending_and_recenter_paths(self) -> None:
        gui = self._build_manager_stub()
        gui.lock_point_pos = (50, 50)
        gui.point_lock_recenter_rect = Rect(20, 20, 20, 20)
        gui.lock_point_recenter_pending = True
        recenter_calls = []
        gui._set_physical_mouse_pos = lambda pos: recenter_calls.append(pos)

        GuiManager.enforce_point_lock(gui, (25, 25))
        self.assertFalse(gui.lock_point_recenter_pending)
        self.assertEqual(recenter_calls, [])

        GuiManager.enforce_point_lock(gui, (100, 100))
        self.assertTrue(gui.lock_point_recenter_pending)
        self.assertEqual(recenter_calls, [gui.point_lock_recenter_rect.center])

    def test_resolve_task_event_owner_returns_none_for_missing_task_id(self) -> None:
        gui = self._build_manager_stub()
        event = SimpleNamespace(type=Event.Task)

        owner = GuiManager._resolve_task_event_owner(gui, event)

        self.assertIsNone(owner)

    def test_describe_gui_object_window_and_fallback_type(self) -> None:
        gui = self._build_manager_stub()

        window = Window.__new__(Window)
        window.x = 1
        window.y = 2
        window.width = 30
        window.height = 40

        text = GuiManager._describe_gui_object(gui, window)
        fallback = GuiManager._describe_gui_object(gui, 123)  # type: ignore[arg-type]

        self.assertIn("Window", text)
        self.assertIn("pos=(1,2)", text)
        self.assertEqual(fallback, "int")

    def test_find_widget_id_conflict_scans_task_panel_and_windows(self) -> None:
        gui = self._build_manager_stub()

        candidate = Widget.__new__(Widget)
        candidate.id = "dup"

        panel_widget = Widget.__new__(Widget)
        panel_widget.id = "dup"
        window_widget = Widget.__new__(Widget)
        window_widget.id = "other"

        gui.task_panel = SimpleNamespace(widgets=[panel_widget])
        gui.windows = [SimpleNamespace(widgets=[window_widget])]

        conflict = GuiManager._find_widget_id_conflict(gui, "dup", candidate)
        self.assertIs(conflict, panel_widget)

        panel_widget.id = "none"
        window_widget.id = "dup"
        conflict = GuiManager._find_widget_id_conflict(gui, "dup", candidate)
        self.assertIs(conflict, window_widget)

    def test_is_registered_button_group_and_object_paths(self) -> None:
        gui = self._build_manager_stub()
        button = SimpleNamespace(surface=None)

        self.assertTrue(GuiManager._is_registered_button_group(gui, button))

        screen_widget = Widget.__new__(Widget)
        panel_widget = Widget.__new__(Widget)
        window_widget = Widget.__new__(Widget)

        gui.widgets = [screen_widget]
        gui.task_panel = SimpleNamespace(widgets=[panel_widget])
        gui.windows = [SimpleNamespace(widgets=[window_widget])]

        self.assertTrue(GuiManager._is_registered_object(gui, screen_widget))
        self.assertTrue(GuiManager._is_registered_object(gui, panel_widget))
        self.assertTrue(GuiManager._is_registered_object(gui, window_widget))

    def test_resolve_locking_state_returns_valid_locking_object(self) -> None:
        gui = self._build_manager_stub()
        widget = Widget.__new__(Widget)
        gui.locking_object = widget
        gui.mouse_locked = True
        gui.mouse_point_locked = False
        gui.lock_area_rect = Rect(0, 0, 5, 5)
        gui.lock_point_pos = None
        gui.lock_point_recenter_pending = False
        gui.lock_point_tolerance_rect = None
        gui._is_registered_object = lambda obj: obj is widget

        resolved = GuiManager._resolve_locking_state(gui)

        self.assertIs(resolved, widget)
        self.assertIs(gui.locking_object, widget)


if __name__ == "__main__":
    unittest.main()
