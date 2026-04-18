import unittest
from types import SimpleNamespace
from unittest.mock import patch

from gui.utility.constants import GuiError
from gui.utility import guimanager as gm


class OldPanelStub:
    def __init__(self, widgets=None, visible=True) -> None:
        self.widgets = [] if widgets is None else widgets
        self.visible = visible
        self.dispose_calls = 0

    def dispose(self) -> None:
        self.dispose_calls += 1


class NewPanelStub:
    def __init__(self) -> None:
        self.widgets = []
        self.visible = True
        self.surface = object()
        self.set_visible_calls = []

    def set_visible(self, visible: bool) -> None:
        self.set_visible_calls.append(visible)
        self.visible = visible


class TaskPanelConfigurationTests(unittest.TestCase):
    def _build_manager_stub(self):
        gui = gm.GuiManager.__new__(gm.GuiManager)
        gui.task_panel = None
        gui._task_panel_capture = True
        return gui

    def test_configure_task_panel_rejects_invalid_auto_hide_type(self) -> None:
        gui = self._build_manager_stub()

        with self.assertRaises(GuiError):
            gm.GuiManager.configure_task_panel(gui, auto_hide="yes")  # type: ignore[arg-type]

    def test_configure_task_panel_is_atomic_when_new_panel_creation_fails(self) -> None:
        gui = self._build_manager_stub()
        old_panel = OldPanelStub(widgets=[SimpleNamespace(window=None, surface=None)], visible=True)
        gui.task_panel = old_panel

        with patch.object(gm, "_ManagedTaskPanel", side_effect=GuiError("panel create failed")):
            with self.assertRaises(GuiError):
                gm.GuiManager.configure_task_panel(gui, height=40)

        self.assertIs(gui.task_panel, old_panel)
        self.assertEqual(old_panel.dispose_calls, 0)

    def test_configure_task_panel_reuses_widgets_and_visibility_on_success(self) -> None:
        gui = self._build_manager_stub()
        w1 = SimpleNamespace(window=None, surface=None)
        w2 = SimpleNamespace(window=None, surface=None)
        old_panel = OldPanelStub(widgets=[w1, w2], visible=False)
        gui.task_panel = old_panel

        created_panels = []

        def create_panel(*_args, **_kwargs):
            panel = NewPanelStub()
            created_panels.append(panel)
            return panel

        with patch.object(gm, "_ManagedTaskPanel", side_effect=create_panel):
            gm.GuiManager.configure_task_panel(gui, height=40)

        self.assertEqual(old_panel.dispose_calls, 1)
        self.assertEqual(len(created_panels), 1)
        new_panel = created_panels[0]
        self.assertIs(gui.task_panel, new_panel)
        self.assertEqual(new_panel.widgets, [w1, w2])
        self.assertEqual(new_panel.set_visible_calls, [False])
        self.assertFalse(gui._task_panel_capture)
        self.assertIs(w1.window, new_panel)
        self.assertIs(w2.window, new_panel)
        self.assertIs(w1.surface, new_panel.surface)
        self.assertIs(w2.surface, new_panel.surface)


if __name__ == "__main__":
    unittest.main()
