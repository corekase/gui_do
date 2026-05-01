import unittest

import pygame

from gui_do_demo import GuiDoDemo


class _StubActions:
    def __init__(self):
        self.bound_keys = []

    def bind_key(self, key, action_name: str, *, scene: str):
        self.bound_keys.append((key, str(action_name), str(scene)))


class _StubApp:
    def __init__(self):
        self.actions = _StubActions()
        self.pristine_calls = []
        self.prewarm_calls = []

    def set_pristine(self, asset_path: str, *, scene_name: str):
        self.pristine_calls.append((str(asset_path), str(scene_name)))

    def prewarm_scene(self, scene_name: str):
        self.prewarm_calls.append(str(scene_name))


class TestDemoRuntimeSceneSpecs(unittest.TestCase):
    def _make_demo(self):
        demo = GuiDoDemo.__new__(GuiDoDemo)
        demo.app = _StubApp()
        return demo

    def test_runtime_scene_specs_apply_pristine_assets(self):
        demo = self._make_demo()

        demo._apply_runtime_scene_pristine_assets()

        self.assertEqual(
            [
                ("demo_features/data/images/backdrop.jpg", "main"),
                ("demo_features/data/images/backdrop.jpg", "control_showcase"),
            ],
            demo.app.pristine_calls,
        )

    def test_runtime_scene_specs_bind_escape_to_exit(self):
        demo = self._make_demo()

        demo._bind_runtime_scene_exit_keys()

        self.assertEqual(
            [
                (pygame.K_ESCAPE, "exit", "main"),
                (pygame.K_ESCAPE, "exit", "control_showcase"),
            ],
            demo.app.actions.bound_keys,
        )

    def test_runtime_scene_specs_prewarm_targets(self):
        demo = self._make_demo()

        demo._prewarm_runtime_scenes()

        self.assertEqual(["control_showcase"], demo.app.prewarm_calls)


if __name__ == "__main__":
    unittest.main()
