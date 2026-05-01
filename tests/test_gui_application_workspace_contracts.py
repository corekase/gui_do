import unittest
from pathlib import Path
from types import MethodType
from unittest.mock import patch

from gui_do.app.gui_application import GuiApplication


class _StubFeatures:
    pass


class _StubWorkspaceManager:
    def __init__(self, report):
        self._report = dict(report)
        self.calls = []

    def restore(self, state, app, *, feature_manager=None):
        self.calls.append(
            {
                "state": state,
                "app": app,
                "feature_manager": feature_manager,
            }
        )
        return dict(self._report)


class TestGuiApplicationWorkspaceContracts(unittest.TestCase):
    def test_restore_workspace_returns_manager_report(self):
        app = GuiApplication.__new__(GuiApplication)
        app.features = _StubFeatures()
        manager = _StubWorkspaceManager({"restored_scene_nodes": 3, "applied_settings": 2})
        state = object()

        report = app.restore_workspace(manager, state)

        self.assertEqual({"restored_scene_nodes": 3, "applied_settings": 2}, report)
        self.assertEqual(1, len(manager.calls))
        self.assertIs(state, manager.calls[0]["state"])
        self.assertIs(app, manager.calls[0]["app"])
        self.assertIs(app.features, manager.calls[0]["feature_manager"])

    def test_load_workspace_returns_restore_report(self):
        app = GuiApplication.__new__(GuiApplication)
        manager = object()
        sentinel_state = object()
        expected_report = {"switched_scene": True, "restored_scene_nodes": 1}

        def _restore_workspace(self, workspace_manager, state):
            self._captured_workspace_manager = workspace_manager
            self._captured_state = state
            return dict(expected_report)

        app.restore_workspace = MethodType(_restore_workspace, app)

        with patch("gui_do.persistence.workspace_persistence.WorkspaceState.load", return_value=sentinel_state) as load_mock:
            report = app.load_workspace(manager, Path("workspace.json"))

        load_mock.assert_called_once_with(Path("workspace.json"))
        self.assertIs(manager, app._captured_workspace_manager)
        self.assertIs(sentinel_state, app._captured_state)
        self.assertEqual(expected_report, report)


if __name__ == "__main__":
    unittest.main()
