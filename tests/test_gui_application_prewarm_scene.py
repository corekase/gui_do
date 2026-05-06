import unittest
from types import MethodType

import pygame

from gui_do.app.gui_application import GuiApplication


class _StubFeatures:
    def __init__(self):
        self.calls = []

    def prewarm_features(self, host, surface, theme, *, scene_name=None, force=False):
        self.calls.append(
            {
                "host": host,
                "surface": surface,
                "theme": theme,
                "scene_name": scene_name,
                "force": force,
            }
        )
        return 7


class TestGuiApplicationPrewarmScene(unittest.TestCase):
    def test_prewarm_scene_primes_pristine_for_target_scene(self):
        app = GuiApplication.__new__(GuiApplication)
        app.surface = pygame.Surface((128, 72))
        app._active_scene_name = "main"
        app.features = _StubFeatures()

        runtime_theme = object()
        pristine_calls = []
        scene_calls = {"update": 0, "draw": 0}

        class _RuntimeScene:
            def update(self, dt_seconds):
                _ = dt_seconds
                scene_calls["update"] += 1

            def draw(self, surface, theme):
                _ = surface
                _ = theme
                scene_calls["draw"] += 1

        def _scene_runtime(self, name):
            self._requested_scene = name
            return type("_Runtime", (), {"theme": runtime_theme, "scene": _RuntimeScene()})()

        def _restore_pristine(self, scene_name=None, surface=None):
            pristine_calls.append({"scene_name": scene_name, "surface": surface})
            return True

        app._scene_runtime = MethodType(_scene_runtime, app)
        app.restore_pristine = MethodType(_restore_pristine, app)

        warmed = app.prewarm_scene("control_showcase", force=True, host="host_ctx")

        self.assertEqual(7, warmed)
        self.assertEqual("control_showcase", app._requested_scene)
        self.assertEqual(1, len(pristine_calls))
        self.assertEqual("control_showcase", pristine_calls[0]["scene_name"])
        self.assertEqual((128, 72), pristine_calls[0]["surface"].get_size())
        self.assertEqual(1, scene_calls["update"])
        self.assertEqual(1, scene_calls["draw"])

        self.assertEqual(1, len(app.features.calls))
        call = app.features.calls[0]
        self.assertEqual("host_ctx", call["host"])
        self.assertEqual(runtime_theme, call["theme"])
        self.assertEqual("control_showcase", call["scene_name"])
        self.assertTrue(call["force"])

    def test_prewarm_scene_draws_hidden_windows_once(self):
        app = GuiApplication.__new__(GuiApplication)
        app.surface = pygame.Surface((96, 64))
        app._active_scene_name = "main"
        app.features = _StubFeatures()

        runtime_theme = object()

        class _StubWindow:
            def __init__(self, *, visible: bool):
                self.visible = bool(visible)
                self.draw_calls = 0

            def draw(self, surface, theme):
                _ = surface
                _ = theme
                self.draw_calls += 1

        hidden_window = _StubWindow(visible=False)
        visible_window = _StubWindow(visible=True)
        scene_calls = {"draw": 0}

        class _RuntimeScene:
            def update(self, _dt_seconds):
                return None

            def draw(self, _surface, _theme):
                scene_calls["draw"] += 1

            def _window_query_nodes(self):
                return ([hidden_window, visible_window], [])

        def _scene_runtime(self, _name):
            return type("_Runtime", (), {"theme": runtime_theme, "scene": _RuntimeScene()})()

        def _restore_pristine(self, scene_name=None, surface=None):
            _ = scene_name
            _ = surface
            return True

        app._scene_runtime = MethodType(_scene_runtime, app)
        app.restore_pristine = MethodType(_restore_pristine, app)

        app.prewarm_scene("main")

        self.assertEqual(1, scene_calls["draw"])
        self.assertEqual(1, hidden_window.draw_calls)
        self.assertEqual(0, visible_window.draw_calls)


if __name__ == "__main__":
    unittest.main()
