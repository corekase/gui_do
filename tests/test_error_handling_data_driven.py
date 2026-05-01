"""Tests for error_handling module and data_driven_runtime dataclasses."""
import unittest

from gui_do.app.error_handling import (
    ErrorContext,
    format_error_message,
    discover_error_source,
    logical_error,
    io_error,
)
from gui_do.features.data_driven_runtime import (
    FeatureSpec,
    WindowSpec,
    RuntimeSceneSpec,
    ActionSpec,
    StaticAccessibilitySpec,
)


# ===========================================================================
# ErrorContext dataclass
# ===========================================================================


class TestErrorContext(unittest.TestCase):
    def _make(self, **kwargs):
        defaults = dict(
            kind="logical", subsystem="ui", operation="load",
            reason="test reason", source="test_module:fn:1"
        )
        defaults.update(kwargs)
        return ErrorContext(**defaults)

    def test_kind_stored(self):
        ctx = self._make(kind="io")
        self.assertEqual("io", ctx.kind)

    def test_subsystem_stored(self):
        ctx = self._make(subsystem="rendering")
        self.assertEqual("rendering", ctx.subsystem)

    def test_operation_stored(self):
        ctx = self._make(operation="draw")
        self.assertEqual("draw", ctx.operation)

    def test_reason_stored(self):
        ctx = self._make(reason="file not found")
        self.assertEqual("file not found", ctx.reason)

    def test_source_stored(self):
        ctx = self._make(source="main.py:run:42")
        self.assertEqual("main.py:run:42", ctx.source)

    def test_path_none_by_default(self):
        ctx = self._make()
        self.assertIsNone(ctx.path)

    def test_path_stored(self):
        ctx = self._make(path="/some/file.txt")
        self.assertEqual("/some/file.txt", ctx.path)

    def test_details_none_by_default(self):
        ctx = self._make()
        self.assertIsNone(ctx.details)

    def test_cause_none_by_default(self):
        ctx = self._make()
        self.assertIsNone(ctx.cause)

    def test_cause_stored(self):
        exc = ValueError("boom")
        ctx = self._make(cause=exc)
        self.assertIs(exc, ctx.cause)

    def test_frozen(self):
        ctx = self._make()
        with self.assertRaises((AttributeError, TypeError)):
            ctx.kind = "changed"


# ===========================================================================
# format_error_message
# ===========================================================================


class TestFormatErrorMessage(unittest.TestCase):
    def _make(self, **kwargs):
        defaults = dict(
            kind="logical", subsystem="ui", operation="load",
            reason="bad thing", source="caller.py:fn:10"
        )
        defaults.update(kwargs)
        return ErrorContext(**defaults)

    def test_contains_reason(self):
        msg = format_error_message(self._make(reason="missing widget"))
        self.assertIn("missing widget", msg)

    def test_contains_kind(self):
        msg = format_error_message(self._make(kind="io"))
        self.assertIn("io", msg)

    def test_contains_subsystem(self):
        msg = format_error_message(self._make(subsystem="render"))
        self.assertIn("render", msg)

    def test_contains_operation(self):
        msg = format_error_message(self._make(operation="flush"))
        self.assertIn("flush", msg)

    def test_contains_source(self):
        msg = format_error_message(self._make(source="mymodule.py:foo:7"))
        self.assertIn("mymodule.py:foo:7", msg)

    def test_contains_path_when_present(self):
        msg = format_error_message(self._make(path="/data/file.json"))
        self.assertIn("/data/file.json", msg)

    def test_no_path_when_absent(self):
        msg = format_error_message(self._make())
        self.assertNotIn("path=", msg)

    def test_contains_details_when_present(self):
        msg = format_error_message(self._make(details={"size": 99}))
        self.assertIn("size", msg)
        self.assertIn("99", msg)

    def test_contains_cause_when_present(self):
        exc = RuntimeError("disk full")
        msg = format_error_message(self._make(cause=exc))
        self.assertIn("RuntimeError", msg)
        self.assertIn("disk full", msg)


# ===========================================================================
# discover_error_source
# ===========================================================================


class TestDiscoverErrorSource(unittest.TestCase):
    def test_returns_string(self):
        result = discover_error_source()
        self.assertIsInstance(result, str)

    def test_contains_colon_separated_parts(self):
        result = discover_error_source()
        # Should be module:function:lineno
        self.assertGreaterEqual(result.count(":"), 1)

    def test_points_to_caller_not_gui_do(self):
        result = discover_error_source()
        # Should NOT point into gui_do internals
        self.assertNotIn("gui_do.", result.split(":")[0])


# ===========================================================================
# logical_error / io_error factory helpers
# ===========================================================================


class TestLogicalError(unittest.TestCase):
    def test_returns_exception(self):
        exc = logical_error("bad state", subsystem="ui", operation="validate",
                            source="test:fn:1")
        self.assertIsInstance(exc, Exception)

    def test_default_exc_type_is_value_error(self):
        exc = logical_error("bad state", subsystem="ui", operation="validate",
                            source="test:fn:1")
        self.assertIsInstance(exc, ValueError)

    def test_custom_exc_type(self):
        exc = logical_error("bad state", subsystem="ui", operation="validate",
                            source="test:fn:1", exc_type=RuntimeError)
        self.assertIsInstance(exc, RuntimeError)

    def test_message_contains_reason(self):
        exc = logical_error("missing key", subsystem="data", operation="lookup",
                            source="test:fn:1")
        self.assertIn("missing key", str(exc))


class TestIoError(unittest.TestCase):
    def test_returns_exception(self):
        cause = OSError("file not found")
        exc = io_error("cannot read", subsystem="persistence", operation="load",
                       cause=cause, source="test:fn:1")
        self.assertIsInstance(exc, Exception)

    def test_default_exc_type_is_runtime_error(self):
        cause = OSError("no file")
        exc = io_error("load failed", subsystem="io", operation="read",
                       cause=cause, source="test:fn:1")
        self.assertIsInstance(exc, RuntimeError)

    def test_message_contains_reason(self):
        cause = OSError("permission denied")
        exc = io_error("blocked", subsystem="fs", operation="write",
                       cause=cause, source="test:fn:1")
        self.assertIn("blocked", str(exc))

    def test_message_contains_path(self):
        cause = OSError("no such file")
        exc = io_error("missing", subsystem="fs", operation="read",
                       cause=cause, path="/data/file.bin", source="test:fn:1")
        self.assertIn("/data/file.bin", str(exc))


# ===========================================================================
# data_driven_runtime dataclasses
# ===========================================================================


class TestFeatureSpec(unittest.TestCase):
    def test_attr_name_stored(self):
        fs = FeatureSpec(attr_name="my_feature", factory=list)
        self.assertEqual("my_feature", fs.attr_name)

    def test_factory_stored(self):
        fs = FeatureSpec(attr_name="x", factory=dict)
        self.assertIs(dict, fs.factory)

    def test_frozen(self):
        fs = FeatureSpec(attr_name="x", factory=list)
        with self.assertRaises((AttributeError, TypeError)):
            fs.attr_name = "y"


class TestRuntimeSceneSpec(unittest.TestCase):
    def test_scene_name_stored(self):
        spec = RuntimeSceneSpec(scene_name="main")
        self.assertEqual("main", spec.scene_name)

    def test_pristine_asset_none_default(self):
        spec = RuntimeSceneSpec(scene_name="main")
        self.assertIsNone(spec.pristine_asset)

    def test_bind_escape_false_default(self):
        spec = RuntimeSceneSpec(scene_name="main")
        self.assertFalse(spec.bind_escape_to_exit)

    def test_prewarm_false_default(self):
        spec = RuntimeSceneSpec(scene_name="main")
        self.assertFalse(spec.prewarm)

    def test_frozen(self):
        spec = RuntimeSceneSpec(scene_name="main")
        with self.assertRaises((AttributeError, TypeError)):
            spec.scene_name = "other"


class TestActionSpec(unittest.TestCase):
    def test_action_id_stored(self):
        spec = ActionSpec(action_id="quit", label="Quit", kind="exit")
        self.assertEqual("quit", spec.action_id)

    def test_label_stored(self):
        spec = ActionSpec(action_id="quit", label="Exit App", kind="exit")
        self.assertEqual("Exit App", spec.label)

    def test_target_none_default(self):
        spec = ActionSpec(action_id="quit", label="Q", kind="exit")
        self.assertIsNone(spec.target)

    def test_category_none_default(self):
        spec = ActionSpec(action_id="quit", label="Q", kind="exit")
        self.assertIsNone(spec.category)


if __name__ == "__main__":
    unittest.main()
