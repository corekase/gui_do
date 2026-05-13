"""Tests for pure data types in data_driven_runtime: dataclasses and ActiveTabUpdateRouter."""
import unittest

from gui_do.features.data_driven_runtime import (
    FeatureSpec,
    RuntimeSceneSpec,
    ActionSpec,
    CursorSpec,
    SceneRootSpec,
    AnchoredWindowSpec,
    LogicBindingSpec,
    TaskPanelButtonSpec,
    TelemetryConfig,
    ActiveTabUpdateRouter,
    PresenterLabelSpec,
    PresenterButtonSpec,
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


# ===========================================================================
# PresenterLabelSpec
# ===========================================================================


class TestPresenterLabelSpec(unittest.TestCase):
    def test_required_fields(self):
        spec = PresenterLabelSpec("my_lbl", 22, "Hello world")
        self.assertEqual("my_lbl", spec.control_id)
        self.assertEqual(22, spec.height)
        self.assertEqual("Hello world", spec.text)

    def test_defaults(self):
        spec = PresenterLabelSpec("x", 20, "text")
        self.assertIsNone(spec.advance)
        self.assertIsNone(spec.width)
        self.assertEqual(0, spec.x_offset)

    def test_explicit_advance_zero(self):
        spec = PresenterLabelSpec("x", 20, "text", advance=0)
        self.assertEqual(0, spec.advance)

    def test_explicit_width_and_advance(self):
        spec = PresenterLabelSpec("lbl", 26, "Label:", width=80, advance=0)
        self.assertEqual(80, spec.width)
        self.assertEqual(0, spec.advance)

    def test_frozen(self):
        spec = PresenterLabelSpec("x", 20, "text")
        with self.assertRaises(Exception):
            spec.control_id = "y"  # type: ignore[misc]


# ===========================================================================
# PresenterButtonSpec
# ===========================================================================


class TestPresenterButtonSpec(unittest.TestCase):
    def test_required_fields(self):
        spec = PresenterButtonSpec("my_btn", 120, 28, "Click Me", "_on_click")
        self.assertEqual("my_btn", spec.control_id)
        self.assertEqual(120, spec.width)
        self.assertEqual(28, spec.height)
        self.assertEqual("Click Me", spec.text)
        self.assertEqual("_on_click", spec.handler_attr)

    def test_defaults(self):
        spec = PresenterButtonSpec("b", 100, 28, "OK", "_ok")
        self.assertIsNone(spec.advance)
        self.assertEqual(0, spec.x_offset)
        self.assertIsNone(spec.style)

    def test_explicit_advance_and_offset(self):
        spec = PresenterButtonSpec("b", 110, 28, "Restore", "_restore",
                                   advance=36, x_offset=118)
        self.assertEqual(36, spec.advance)
        self.assertEqual(118, spec.x_offset)

    def test_style(self):
        spec = PresenterButtonSpec("b", 130, 28, "Toggle", "_toggle", style="round")
        self.assertEqual("round", spec.style)

    def test_frozen(self):
        spec = PresenterButtonSpec("b", 100, 28, "OK", "_ok")
        with self.assertRaises(Exception):
            spec.control_id = "z"  # type: ignore[misc]
