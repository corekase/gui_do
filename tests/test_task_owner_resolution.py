import unittest
from types import SimpleNamespace

from gui_manager_test_factory import build_gui_manager_stub
from gui.utility.constants import Event, GuiError
from gui.utility.guimanager import GuiManager


class GuiManagerTaskOwnerResolutionTests(unittest.TestCase):
    def _build_manager_stub(self):
        return build_gui_manager_stub()

    def test_set_task_owner_rejects_unhashable_task_id(self) -> None:
        gui = self._build_manager_stub()
        window = SimpleNamespace(visible=True)
        gui.windows.append(window)

        with self.assertRaises(GuiError):
            GuiManager.set_task_owner(gui, [], window)  # type: ignore[arg-type]

    def test_set_task_owner_rejects_unregistered_window(self) -> None:
        gui = self._build_manager_stub()
        window = SimpleNamespace(visible=True)

        with self.assertRaises(GuiError):
            GuiManager.set_task_owner(gui, "task-1", window)

    def test_set_task_owner_none_removes_existing_owner(self) -> None:
        gui = self._build_manager_stub()
        window = SimpleNamespace(visible=True)
        gui.windows.append(window)

        GuiManager.set_task_owner(gui, "task-1", window)
        self.assertIs(gui.event_delivery._task_owner_by_id["task-1"], window)

        GuiManager.set_task_owner(gui, "task-1", None)
        self.assertNotIn("task-1", gui.event_delivery._task_owner_by_id)

    def test_set_task_owners_assigns_multiple_ids(self) -> None:
        gui = self._build_manager_stub()
        window = SimpleNamespace(visible=True)
        gui.windows.append(window)

        GuiManager.set_task_owners(gui, window, "a", "b", "c")

        self.assertIs(gui.event_delivery._task_owner_by_id["a"], window)
        self.assertIs(gui.event_delivery._task_owner_by_id["b"], window)
        self.assertIs(gui.event_delivery._task_owner_by_id["c"], window)

    def test_clear_task_owners_for_window_removes_only_matching_owner(self) -> None:
        gui = self._build_manager_stub()
        w1 = SimpleNamespace(visible=True)
        w2 = SimpleNamespace(visible=True)
        gui.windows.extend([w1, w2])
        gui.event_delivery._task_owner_by_id = {
            "task-a": w1,
            "task-b": w2,
            "task-c": w1,
        }

        GuiManager.clear_task_owners_for_window(gui, w1)

        self.assertNotIn("task-a", gui.event_delivery._task_owner_by_id)
        self.assertNotIn("task-c", gui.event_delivery._task_owner_by_id)
        self.assertIn("task-b", gui.event_delivery._task_owner_by_id)
        self.assertIs(gui.event_delivery._task_owner_by_id["task-b"], w2)

    def test_resolve_task_event_owner_returns_none_for_non_task_event(self) -> None:
        gui = self._build_manager_stub()
        event = SimpleNamespace(type=Event.KeyDown, id="task-1")

        owner = gui.event_delivery.resolve_task_event_owner(event)

        self.assertIsNone(owner)

    def test_resolve_task_event_owner_returns_none_for_unhashable_id(self) -> None:
        gui = self._build_manager_stub()
        event = SimpleNamespace(type=Event.Task, id=[])

        owner = gui.event_delivery.resolve_task_event_owner(event)

        self.assertIsNone(owner)

    def test_resolve_task_event_owner_returns_none_for_hidden_or_missing_owner(self) -> None:
        gui = self._build_manager_stub()
        hidden = SimpleNamespace(visible=False)
        visible = SimpleNamespace(visible=True)
        gui.windows.append(visible)
        gui.event_delivery._task_owner_by_id["hidden-task"] = hidden
        gui.event_delivery._task_owner_by_id["visible-task"] = visible

        hidden_event = SimpleNamespace(type=Event.Task, id="hidden-task")
        missing_event = SimpleNamespace(type=Event.Task, id="missing")

        owner_hidden = gui.event_delivery.resolve_task_event_owner(hidden_event)
        owner_missing = gui.event_delivery.resolve_task_event_owner(missing_event)

        self.assertIsNone(owner_hidden)
        self.assertIsNone(owner_missing)

    def test_resolve_task_event_owner_returns_registered_visible_owner(self) -> None:
        gui = self._build_manager_stub()
        owner = SimpleNamespace(visible=True)
        gui.windows.append(owner)
        gui.event_delivery._task_owner_by_id["task-ok"] = owner
        event = SimpleNamespace(type=Event.Task, id="task-ok")

        resolved = gui.event_delivery.resolve_task_event_owner(event)

        self.assertIs(resolved, owner)


if __name__ == "__main__":
    unittest.main()
