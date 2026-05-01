"""Tests for ErrorContext, format_error_message, logical_error, io_error."""
import unittest

from gui_do.app.error_handling import (
    ErrorContext,
    format_error_message,
    logical_error,
    io_error,
)


# ===========================================================================
# ErrorContext dataclass
# ===========================================================================


class TestErrorContextDefaults(unittest.TestCase):
    def test_required_fields_stored(self):
        ctx = ErrorContext(
            kind="logical",
            subsystem="test",
            operation="op",
            reason="bad",
            source="here",
        )
        self.assertEqual("logical", ctx.kind)
        self.assertEqual("test", ctx.subsystem)
        self.assertEqual("op", ctx.operation)
        self.assertEqual("bad", ctx.reason)
        self.assertEqual("here", ctx.source)

    def test_optional_defaults_none(self):
        ctx = ErrorContext(kind="k", subsystem="s", operation="o", reason="r", source="src")
        self.assertIsNone(ctx.path)
        self.assertIsNone(ctx.details)
        self.assertIsNone(ctx.cause)

    def test_is_frozen(self):
        ctx = ErrorContext(kind="k", subsystem="s", operation="o", reason="r", source="src")
        with self.assertRaises(Exception):
            ctx.kind = "changed"  # type: ignore[misc]

    def test_optional_fields_stored(self):
        cause = ValueError("original")
        ctx = ErrorContext(
            kind="io",
            subsystem="disk",
            operation="read",
            reason="not found",
            source="loader",
            path="/tmp/x",
            details={"key": "value"},
            cause=cause,
        )
        self.assertEqual("/tmp/x", ctx.path)
        self.assertEqual({"key": "value"}, ctx.details)
        self.assertIs(cause, ctx.cause)


# ===========================================================================
# format_error_message
# ===========================================================================


class TestFormatErrorMessage(unittest.TestCase):
    def test_basic_message_contains_reason(self):
        ctx = ErrorContext(kind="logical", subsystem="s", operation="o", reason="bad input", source="here")
        msg = format_error_message(ctx)
        self.assertIn("bad input", msg)

    def test_message_contains_kind(self):
        ctx = ErrorContext(kind="logical", subsystem="s", operation="o", reason="r", source="here")
        msg = format_error_message(ctx)
        self.assertIn("kind=logical", msg)

    def test_message_contains_subsystem(self):
        ctx = ErrorContext(kind="k", subsystem="mysub", operation="o", reason="r", source="here")
        msg = format_error_message(ctx)
        self.assertIn("subsystem=mysub", msg)

    def test_message_contains_path_when_set(self):
        ctx = ErrorContext(kind="io", subsystem="s", operation="o", reason="r", source="here", path="/some/path")
        msg = format_error_message(ctx)
        self.assertIn("/some/path", msg)

    def test_message_omits_path_when_none(self):
        ctx = ErrorContext(kind="io", subsystem="s", operation="o", reason="r", source="here")
        msg = format_error_message(ctx)
        self.assertNotIn("path=", msg)

    def test_message_contains_details(self):
        ctx = ErrorContext(kind="k", subsystem="s", operation="o", reason="r", source="here",
                           details={"count": 3})
        msg = format_error_message(ctx)
        self.assertIn("count", msg)

    def test_message_contains_cause_type(self):
        cause = FileNotFoundError("missing")
        ctx = ErrorContext(kind="io", subsystem="s", operation="o", reason="r", source="here", cause=cause)
        msg = format_error_message(ctx)
        self.assertIn("FileNotFoundError", msg)


# ===========================================================================
# logical_error factory
# ===========================================================================


class TestLogicalError(unittest.TestCase):
    def test_returns_exception(self):
        exc = logical_error("bad value", subsystem="foo", operation="bar", source="test")
        self.assertIsInstance(exc, Exception)

    def test_default_exc_type_is_value_error(self):
        exc = logical_error("bad value", subsystem="foo", operation="bar", source="test")
        self.assertIsInstance(exc, ValueError)

    def test_custom_exc_type(self):
        exc = logical_error("bad", subsystem="s", operation="o", exc_type=TypeError, source="test")
        self.assertIsInstance(exc, TypeError)

    def test_message_contains_reason(self):
        exc = logical_error("my reason", subsystem="s", operation="o", source="test")
        self.assertIn("my reason", str(exc))


# ===========================================================================
# io_error factory
# ===========================================================================


class TestIoError(unittest.TestCase):
    def test_returns_exception(self):
        cause = OSError("disk full")
        exc = io_error("write failed", subsystem="disk", operation="write", cause=cause, source="test")
        self.assertIsInstance(exc, Exception)

    def test_default_exc_type_is_runtime_error(self):
        cause = OSError("disk full")
        exc = io_error("write failed", subsystem="disk", operation="write", cause=cause, source="test")
        self.assertIsInstance(exc, RuntimeError)

    def test_custom_exc_type(self):
        cause = OSError("fail")
        exc = io_error("fail", subsystem="s", operation="o", cause=cause, exc_type=PermissionError, source="test")
        self.assertIsInstance(exc, PermissionError)

    def test_message_contains_reason(self):
        cause = OSError("x")
        exc = io_error("my io reason", subsystem="s", operation="o", cause=cause, source="test")
        self.assertIn("my io reason", str(exc))

    def test_message_contains_path(self):
        cause = OSError("x")
        exc = io_error("fail", subsystem="s", operation="o", cause=cause, path="/my/path", source="test")
        self.assertIn("/my/path", str(exc))


if __name__ == "__main__":
    unittest.main()
