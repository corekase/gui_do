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

    def test_run_entrypoint_ignores_workspace_load_errors_and_exits_zero(self):
        app = GuiApplication.__new__(GuiApplication)
        manager = object()
        calls = {"load": 0, "run": 0, "save": 0}

        def _load_workspace(self, workspace_manager, path):
            _ = workspace_manager
            _ = path
            calls["load"] += 1
            raise RuntimeError("load failed")

        def _run(self, target_fps=60):
            _ = target_fps
            calls["run"] += 1
            return 0

        def _save_workspace(self, workspace_manager, path, *, metadata=None):
            _ = workspace_manager
            _ = path
            _ = metadata
            calls["save"] += 1

        app.load_workspace = MethodType(_load_workspace, app)
        app.run = MethodType(_run, app)
        app.save_workspace = MethodType(_save_workspace, app)

        with patch("gui_do.app.gui_application.report_nonfatal_error") as report_mock:
            with patch("gui_do.app.gui_application.pygame.quit") as quit_mock:
                with self.assertRaises(SystemExit) as ctx:
                    app.run_entrypoint(
                        target_fps=144,
                        WORKSPACE_SAVE=True,
                        workspace_manager=manager,
                        workspace_path=Path("state.json"),
                    )

        self.assertEqual(0, ctx.exception.code)
        self.assertEqual(1, calls["load"])
        self.assertEqual(1, calls["run"])
        self.assertEqual(1, calls["save"])
        report_mock.assert_not_called()
        quit_mock.assert_called_once_with()

    def test_run_entrypoint_reports_runtime_error_and_exits_one(self):
        app = GuiApplication.__new__(GuiApplication)
        manager = object()
        calls = {"load": 0, "run": 0, "save": 0}

        def _load_workspace(self, workspace_manager, path):
            _ = workspace_manager
            _ = path
            calls["load"] += 1
            return {"loaded": True}

        def _run(self, target_fps=60):
            _ = target_fps
            calls["run"] += 1
            raise ValueError("boom")

        def _save_workspace(self, workspace_manager, path, *, metadata=None):
            _ = workspace_manager
            _ = path
            _ = metadata
            calls["save"] += 1
            raise RuntimeError("save failed")

        app.load_workspace = MethodType(_load_workspace, app)
        app.run = MethodType(_run, app)
        app.save_workspace = MethodType(_save_workspace, app)

        with patch("gui_do.app.gui_application.report_nonfatal_error") as report_mock:
            with patch("gui_do.app.gui_application.pygame.quit") as quit_mock:
                with self.assertRaises(SystemExit) as ctx:
                    app.run_entrypoint(
                        target_fps=90,
                        WORKSPACE_SAVE=True,
                        workspace_manager=manager,
                        workspace_path=Path("state.json"),
                    )

        self.assertEqual(1, ctx.exception.code)
        self.assertEqual(1, calls["load"])
        self.assertEqual(1, calls["run"])
        self.assertEqual(1, calls["save"])
        report_mock.assert_called_once()
        report_kwargs = report_mock.call_args.kwargs
        self.assertEqual("run_entrypoint", report_kwargs.get("operation"))
        self.assertEqual({"target_fps": 90}, report_kwargs.get("details"))
        quit_mock.assert_called_once_with()

    def test_run_entrypoint_without_workspace_save_skips_workspace_io(self):
        app = GuiApplication.__new__(GuiApplication)
        calls = {"run": 0}

        def _load_workspace(self, workspace_manager, path):
            _ = workspace_manager
            _ = path
            raise AssertionError("load_workspace should not be called when WORKSPACE_SAVE is False")

        def _run(self, target_fps=60):
            _ = target_fps
            calls["run"] += 1
            return 0

        def _save_workspace(self, workspace_manager, path, *, metadata=None):
            _ = workspace_manager
            _ = path
            _ = metadata
            raise AssertionError("save_workspace should not be called when WORKSPACE_SAVE is False")

        app.load_workspace = MethodType(_load_workspace, app)
        app.run = MethodType(_run, app)
        app.save_workspace = MethodType(_save_workspace, app)

        with patch("gui_do.app.gui_application.pygame.quit") as quit_mock:
            with self.assertRaises(SystemExit) as ctx:
                app.run_entrypoint(target_fps=120, WORKSPACE_SAVE=False)

        self.assertEqual(0, ctx.exception.code)
        self.assertEqual(1, calls["run"])
        quit_mock.assert_called_once_with()

    def test_run_entrypoint_constructs_default_workspace_manager(self):
        app = GuiApplication.__new__(GuiApplication)
        calls = {"load": 0, "run": 0, "save": 0}
        constructed_manager = object()

        def _load_workspace(self, workspace_manager, path):
            _ = path
            calls["load"] += 1
            self._loaded_manager = workspace_manager

        def _run(self, target_fps=60):
            _ = target_fps
            calls["run"] += 1
            return 0

        def _save_workspace(self, workspace_manager, path, *, metadata=None):
            _ = path
            _ = metadata
            calls["save"] += 1
            self._saved_manager = workspace_manager

        app.load_workspace = MethodType(_load_workspace, app)
        app.run = MethodType(_run, app)
        app.save_workspace = MethodType(_save_workspace, app)

        with patch("gui_do.app.gui_application.WorkspacePersistenceManager", return_value=constructed_manager) as manager_ctor:
            with patch("gui_do.app.gui_application.pygame.quit") as quit_mock:
                with self.assertRaises(SystemExit) as ctx:
                    app.run_entrypoint(target_fps=60, WORKSPACE_SAVE=True)

        self.assertEqual(0, ctx.exception.code)
        self.assertEqual(1, calls["load"])
        self.assertEqual(1, calls["run"])
        self.assertEqual(1, calls["save"])
        self.assertIs(constructed_manager, app._loaded_manager)
        self.assertIs(constructed_manager, app._saved_manager)
        manager_ctor.assert_called_once_with()
        quit_mock.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
