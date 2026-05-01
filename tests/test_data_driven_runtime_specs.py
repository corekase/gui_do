"""Tests for pure data types in data_driven_runtime: dataclasses and ActiveTabUpdateRouter."""
import unittest

from gui_do.features.data_driven_runtime import (
    FeatureSpec,
    WindowSpec,
    RuntimeSceneSpec,
    ActionSpec,
    StaticAccessibilitySpec,
    CursorSpec,
    SceneRootSpec,
    AnchoredWindowSpec,
    LogicBindingSpec,
    TaskPanelButtonSpec,
    AccessibilitySequenceSpec,
    TabBuilderSpec,
    TelemetryConfig,
    ActiveTabUpdateRouter,
)


# ===========================================================================
# FeatureSpec
# ===========================================================================


class TestFeatureSpec(unittest.TestCase):
    def test_fields_stored(self):
        factory = lambda: None
        spec = FeatureSpec(attr_name="my_feature", factory=factory)
        self.assertEqual("my_feature", spec.attr_name)
        self.assertIs(factory, spec.factory)

    def test_frozen(self):
        spec = FeatureSpec(attr_name="x", factory=lambda: None)
        with self.assertRaises(Exception):
            spec.attr_name = "y"  # type: ignore[misc]


# ===========================================================================
# RuntimeSceneSpec
# ===========================================================================


class TestRuntimeSceneSpec(unittest.TestCase):
    def test_required_field(self):
        spec = RuntimeSceneSpec(scene_name="main")
        self.assertEqual("main", spec.scene_name)

    def test_defaults(self):
        spec = RuntimeSceneSpec(scene_name="x")
        self.assertIsNone(spec.pristine_asset)
        self.assertFalse(spec.bind_escape_to_exit)
        self.assertFalse(spec.prewarm)

    def test_custom_values(self):
        spec = RuntimeSceneSpec(
            scene_name="demo",
            pristine_asset="default.json",
            bind_escape_to_exit=True,
            prewarm=True,
        )
        self.assertEqual("default.json", spec.pristine_asset)
        self.assertTrue(spec.bind_escape_to_exit)
        self.assertTrue(spec.prewarm)


# ===========================================================================
# ActionSpec
# ===========================================================================


class TestActionSpec(unittest.TestCase):
    def test_fields_stored(self):
        spec = ActionSpec(action_id="exit", label="Exit", kind="exit")
        self.assertEqual("exit", spec.action_id)
        self.assertEqual("Exit", spec.label)
        self.assertEqual("exit", spec.kind)

    def test_optional_defaults_none(self):
        spec = ActionSpec(action_id="x", label="X", kind="exit")
        self.assertIsNone(spec.target)
        self.assertIsNone(spec.category)


# ===========================================================================
# CursorSpec
# ===========================================================================


class TestCursorSpec(unittest.TestCase):
    def test_fields_stored(self):
        spec = CursorSpec(name="pointer", path="cursors/pointer.png", hotspot=(0, 0))
        self.assertEqual("pointer", spec.name)
        self.assertEqual("cursors/pointer.png", spec.path)
        self.assertEqual((0, 0), spec.hotspot)


# ===========================================================================
# SceneRootSpec
# ===========================================================================


class TestSceneRootSpec(unittest.TestCase):
    def test_required_fields(self):
        spec = SceneRootSpec(scene_name="main", control_id="root_panel")
        self.assertEqual("main", spec.scene_name)
        self.assertEqual("root_panel", spec.control_id)

    def test_draw_background_default(self):
        spec = SceneRootSpec(scene_name="x", control_id="y")
        self.assertFalse(spec.draw_background)


# ===========================================================================
# AnchoredWindowSpec
# ===========================================================================


class TestAnchoredWindowSpec(unittest.TestCase):
    def test_fields_stored(self):
        spec = AnchoredWindowSpec(
            control_id="help_window",
            title="Help",
            size=(400, 300),
            anchor="center",
            margin=(0, 0),
        )
        self.assertEqual("help_window", spec.control_id)
        self.assertEqual("Help", spec.title)
        self.assertEqual((400, 300), spec.size)
        self.assertEqual("center", spec.anchor)
        self.assertTrue(spec.use_frame_backdrop)  # default True


# ===========================================================================
# LogicBindingSpec
# ===========================================================================


class TestLogicBindingSpec(unittest.TestCase):
    def test_fields_stored(self):
        spec = LogicBindingSpec(alias="data_provider", provider_name="my_feature")
        self.assertEqual("data_provider", spec.alias)
        self.assertEqual("my_feature", spec.provider_name)


# ===========================================================================
# TaskPanelButtonSpec
# ===========================================================================


class TestTaskPanelButtonSpec(unittest.TestCase):
    def test_fields_stored(self):
        spec = TaskPanelButtonSpec(
            attr_name="btn_attr",
            control_id="btn_1",
            slot_index=0,
            label="Click Me",
            on_click=lambda: None,
        )
        self.assertEqual("btn_attr", spec.attr_name)
        self.assertEqual("btn_1", spec.control_id)
        self.assertEqual(0, spec.slot_index)
        self.assertEqual("Click Me", spec.label)
        self.assertEqual("angle", spec.style)  # default

    def test_custom_style(self):
        spec = TaskPanelButtonSpec(
            attr_name="x",
            control_id="y",
            slot_index=1,
            label="Z",
            on_click=lambda: None,
            style="square",
        )
        self.assertEqual("square", spec.style)


# ===========================================================================
# TelemetryConfig
# ===========================================================================


class TestTelemetryConfig(unittest.TestCase):
    def test_defaults(self):
        config = TelemetryConfig()
        self.assertFalse(config.enabled)
        self.assertTrue(config.live_analysis_enabled)
        self.assertFalse(config.file_logging_enabled)

    def test_enabled_true(self):
        config = TelemetryConfig(enabled=True)
        self.assertTrue(config.enabled)


# ===========================================================================
# ActiveTabUpdateRouter
# ===========================================================================


class TestActiveTabUpdateRouter(unittest.TestCase):
    def test_run_no_handler(self):
        router = ActiveTabUpdateRouter()
        result = router.run("missing_tab")
        self.assertFalse(result)

    def test_register_and_run(self):
        router = ActiveTabUpdateRouter()
        called = []
        router.register("tab1", lambda: called.append(1))
        result = router.run("tab1")
        self.assertTrue(result)
        self.assertEqual([1], called)

    def test_run_wrong_tab(self):
        router = ActiveTabUpdateRouter()
        called = []
        router.register("tab1", lambda: called.append(1))
        result = router.run("tab2")
        self.assertFalse(result)
        self.assertEqual([], called)

    def test_unregister_returns_true(self):
        router = ActiveTabUpdateRouter()
        router.register("tab1", lambda: None)
        result = router.unregister("tab1")
        self.assertTrue(result)

    def test_unregister_missing_returns_false(self):
        router = ActiveTabUpdateRouter()
        result = router.unregister("nonexistent")
        self.assertFalse(result)

    def test_keys(self):
        router = ActiveTabUpdateRouter()
        router.register("a", lambda: None)
        router.register("b", lambda: None)
        self.assertIn("a", router.keys())
        self.assertIn("b", router.keys())

    def test_run_with_args(self):
        router = ActiveTabUpdateRouter()
        captured = []
        router.register("tab", lambda x, y: captured.append((x, y)))
        router.run("tab", 10, 20)
        self.assertEqual([(10, 20)], captured)


if __name__ == "__main__":
    unittest.main()
