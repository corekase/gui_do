"""Tests for gui_do.forms.schema_form_runtime."""
from __future__ import annotations

import unittest

from gui_do.forms.schema_form_runtime import (
    FieldGraphSchema,
    FieldSchema,
    SchemaFormRuntime,
    ValidationPolicy,
)


def _min_length(n):
    def _v(v):
        if len(str(v)) < n:
            return f"Must be at least {n} characters"
        return None
    return _v


class TestFieldSchema(unittest.TestCase):
    def test_defaults(self):
        fs = FieldSchema(name="email")
        self.assertEqual(fs.field_type, str)
        self.assertEqual(fs.default, "")
        self.assertFalse(fs.required)
        self.assertEqual(fs.validators, [])
        self.assertEqual(fs.depends_on, [])
        self.assertIsNone(fs.visible_when)


class TestFieldGraphSchema(unittest.TestCase):
    def test_unique_names(self):
        with self.assertRaises(ValueError):
            FieldGraphSchema([FieldSchema("x"), FieldSchema("x")])

    def test_unknown_dependency_raises(self):
        with self.assertRaises(ValueError):
            FieldGraphSchema([FieldSchema("a", depends_on=["nonexistent"])])

    def test_valid_dependency(self):
        schema = FieldGraphSchema([
            FieldSchema("parent"),
            FieldSchema("child", depends_on=["parent"]),
        ])
        self.assertEqual(len(schema), 2)

    def test_fields_returns_copy(self):
        schema = FieldGraphSchema([FieldSchema("a")])
        fields = schema.fields
        fields.clear()
        self.assertEqual(len(schema), 1)


class TestSchemaFormRuntime(unittest.TestCase):
    def _make_runtime(self, policy=ValidationPolicy.ON_CHANGE):
        schema = FieldGraphSchema([
            FieldSchema("username", required=True, validators=[_min_length(3)]),
            FieldSchema("email", required=False),
        ])
        return SchemaFormRuntime(schema, policy)

    def test_initial_values(self):
        rt = self._make_runtime()
        self.assertEqual(rt.get_value("username"), "")
        self.assertEqual(rt.get_value("email"), "")

    def test_set_value(self):
        rt = self._make_runtime()
        rt.set_value("username", "Alice")
        self.assertEqual(rt.get_value("username"), "Alice")

    def test_on_change_validation(self):
        rt = self._make_runtime(ValidationPolicy.ON_CHANGE)
        rt.set_value("username", "ab")  # too short
        self.assertGreater(len(rt.get_errors("username")), 0)

    def test_valid_after_correction(self):
        rt = self._make_runtime(ValidationPolicy.ON_CHANGE)
        rt.set_value("username", "ab")
        rt.set_value("username", "Alice")
        self.assertEqual(rt.get_errors("username"), [])

    def test_required_field_error(self):
        rt = self._make_runtime(ValidationPolicy.ON_CHANGE)
        rt.set_value("username", "")
        errors = rt.get_errors("username")
        self.assertTrue(any("required" in e.lower() for e in errors))

    def test_on_blur_policy_defers_validation(self):
        rt = self._make_runtime(ValidationPolicy.ON_BLUR)
        rt.set_value("username", "ab")
        # No errors yet — not blurred
        self.assertEqual(rt.get_errors("username"), [])
        rt.blur("username")
        self.assertGreater(len(rt.get_errors("username")), 0)

    def test_on_submit_defers_until_validate_all(self):
        rt = self._make_runtime(ValidationPolicy.ON_SUBMIT)
        rt.set_value("username", "")
        self.assertEqual(rt.get_errors("username"), [])
        rt.validate_all()
        self.assertGreater(len(rt.get_errors("username")), 0)

    def test_is_valid(self):
        rt = self._make_runtime()
        rt.set_value("username", "Alice")
        self.assertTrue(rt.is_valid())

    def test_not_valid_with_errors(self):
        rt = self._make_runtime()
        rt.set_value("username", "")
        self.assertFalse(rt.is_valid())

    def test_validate_all_returns_bool(self):
        rt = self._make_runtime()
        rt.set_value("username", "Alice")
        self.assertTrue(rt.validate_all())

    def test_field_names(self):
        rt = self._make_runtime()
        names = rt.field_names()
        self.assertIn("username", names)
        self.assertIn("email", names)

    def test_on_change_callback(self):
        rt = self._make_runtime()
        changes = []
        rt.on_change(lambda name, val: changes.append((name, val)))
        rt.set_value("email", "test@example.com")
        self.assertIn(("email", "test@example.com"), changes)

    def test_unsubscribe_change_callback(self):
        rt = self._make_runtime()
        changes = []
        unsub = rt.on_change(lambda n, v: changes.append(v))
        unsub()
        rt.set_value("email", "x")
        self.assertEqual(changes, [])

    def test_visible_when_controls_visibility(self):
        schema = FieldGraphSchema([
            FieldSchema("has_email", default=False),
            FieldSchema(
                "email",
                depends_on=["has_email"],
                visible_when=lambda vals: vals.get("has_email") is True,
            ),
        ])
        rt = SchemaFormRuntime(schema)
        self.assertFalse(rt.is_visible("email"))
        rt.set_value("has_email", True)
        self.assertTrue(rt.is_visible("email"))

    def test_invisible_field_does_not_affect_validity(self):
        schema = FieldGraphSchema([
            FieldSchema("toggle", default=False),
            FieldSchema(
                "secret",
                required=True,
                depends_on=["toggle"],
                visible_when=lambda vals: vals.get("toggle") is True,
            ),
        ])
        rt = SchemaFormRuntime(schema, ValidationPolicy.ON_SUBMIT)
        rt.validate_all()
        # "secret" is not visible → shouldn't make form invalid
        self.assertTrue(rt.is_valid())

    def test_values_snapshot(self):
        rt = self._make_runtime()
        rt.set_value("email", "a@b.com")
        snap = rt.values_snapshot()
        self.assertEqual(snap["email"], "a@b.com")

    def test_restore_values(self):
        rt = self._make_runtime()
        rt.restore_values({"username": "Bob", "email": "bob@x.com"})
        self.assertEqual(rt.get_value("username"), "Bob")
        self.assertEqual(rt.get_value("email"), "bob@x.com")


if __name__ == "__main__":
    unittest.main()
