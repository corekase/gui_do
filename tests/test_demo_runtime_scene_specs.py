import unittest

import pygame

from gui_do import apply_runtime_scene_pristine_assets, bind_runtime_scene_exit_keys, prewarm_runtime_scenes
from demo_features.demo_config import RUNTIME_SCENE_SPECS


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
    def test_runtime_scene_specs_apply_pristine_assets(self):
        app = _StubApp()

        apply_runtime_scene_pristine_assets(app, RUNTIME_SCENE_SPECS)

        self.assertEqual(
            [
                ("demo_features/data/images/backdrop.jpg", "main"),
                ("demo_features/data/images/backdrop.jpg", "control_showcase"),
            ],
            app.pristine_calls,
        )

    def test_runtime_scene_specs_bind_escape_to_exit(self):
        app = _StubApp()

        bind_runtime_scene_exit_keys(app.actions, RUNTIME_SCENE_SPECS, key=pygame.K_ESCAPE)

        self.assertEqual(
            [
                (pygame.K_ESCAPE, "exit", "main"),
                (pygame.K_ESCAPE, "exit", "control_showcase"),
            ],
            app.actions.bound_keys,
        )

    def test_runtime_scene_specs_prewarm_targets(self):
        app = _StubApp()

        prewarm_runtime_scenes(app, RUNTIME_SCENE_SPECS)

        self.assertEqual(["control_showcase"], app.prewarm_calls)


if __name__ == "__main__":
    unittest.main()
