import unittest

from gui_do.features.feature_lifecycle import SceneSetupSpec, apply_scene_setup_specs


class _StubApp:
    def __init__(self):
        self.created_scenes = []
        self.tiling_configs = []
        self.tiling_enabled = []
        self.switched_to = None

    def create_scene(self, name: str, *, pretty_name=None):
        self.created_scenes.append((str(name), pretty_name))

    def configure_window_tiling(
        self,
        *,
        gap=None,
        padding=None,
        avoid_task_panel=None,
        center_on_failure=None,
        relayout=True,
        scene_name=None,
    ):
        self.tiling_configs.append(
            {
                "scene_name": scene_name,
                "gap": gap,
                "padding": padding,
                "avoid_task_panel": avoid_task_panel,
                "center_on_failure": center_on_failure,
                "relayout": relayout,
            }
        )

    def set_window_tiling_enabled(self, enabled: bool, relayout: bool = True, scene_name=None):
        self.tiling_enabled.append(
            {
                "scene_name": scene_name,
                "enabled": bool(enabled),
                "relayout": bool(relayout),
            }
        )

    def switch_scene(self, scene_name: str):
        self.switched_to = str(scene_name)


class _StubTransitions:
    def __init__(self):
        self.styles = []

    def set_style(self, scene_name: str, style, *, duration=None):
        self.styles.append((str(scene_name), style, duration))


class TestSceneSetupSpecs(unittest.TestCase):
    def test_apply_scene_setup_specs_creates_scenes_and_applies_defaults(self):
        app = _StubApp()
        transitions = _StubTransitions()

        specs = (
            SceneSetupSpec(
                name="main",
                pretty_name="Main",
                transition_style="slide-right",
                transition_duration=0.4,
                make_initial=True,
            ),
            SceneSetupSpec(
                name="secondary",
                pretty_name="Secondary",
                transition_style="slide-left",
                transition_duration=0.6,
                tiling_enabled=False,
                tiling_gap=8,
                tiling_padding=10,
                tiling_avoid_task_panel=False,
                tiling_center_on_failure=False,
            ),
        )

        initial = apply_scene_setup_specs(app, specs, scene_transitions=transitions)

        self.assertEqual("main", initial)
        self.assertEqual("main", app.switched_to)
        self.assertEqual(
            [("main", "Main"), ("secondary", "Secondary")],
            app.created_scenes,
        )
        self.assertEqual(2, len(app.tiling_configs))
        self.assertEqual(2, len(app.tiling_enabled))
        self.assertEqual(
            [
                ("main", "slide-right", 0.4),
                ("secondary", "slide-left", 0.6),
            ],
            transitions.styles,
        )

    def test_first_scene_becomes_initial_when_not_explicit(self):
        app = _StubApp()

        specs = (
            SceneSetupSpec(name="first"),
            SceneSetupSpec(name="second"),
        )

        initial = apply_scene_setup_specs(app, specs)

        self.assertEqual("first", initial)
        self.assertEqual("first", app.switched_to)


if __name__ == "__main__":
    unittest.main()
