"""Tests for FormModel + Validation Engine."""
import unittest

from gui_do.core.form_model import FormModel, FormField, ValidationRule, FieldError
from gui_do.core.presentation_model import ObservableValue


class TestFormFieldDefaults(unittest.TestCase):
    def test_initial_not_dirty(self) -> None:
        f: FormField[str] = FormField("name", "Alice")
        self.assertFalse(f.is_dirty)

    def test_initial_value_accessible_via_observable(self) -> None:
        f: FormField[int] = FormField("age", 30)
        self.assertEqual(f.value.value, 30)

    def test_initial_no_errors(self) -> None:
        f: FormField[str] = FormField("x", "")
        self.assertEqual(f.errors, [])
        self.assertTrue(f.is_valid)


class TestFormFieldDirtyTracking(unittest.TestCase):
    def test_becomes_dirty_after_value_change(self) -> None:
        f: FormField[str] = FormField("name", "Alice")
        f.value.value = "Bob"
        self.assertTrue(f.is_dirty)

    def test_commit_clears_dirty(self) -> None:
        f: FormField[str] = FormField("name", "Alice")
        f.value.value = "Bob"
        f.commit()
        self.assertFalse(f.is_dirty)

    def test_reset_reverts_value(self) -> None:
        f: FormField[str] = FormField("name", "Alice")
        f.value.value = "Bob"
        f.reset()
        self.assertEqual(f.value.value, "Alice")
        self.assertFalse(f.is_dirty)


class TestFormFieldValidation(unittest.TestCase):
    def test_required_field_empty_string_fails(self) -> None:
        f: FormField[str] = FormField("name", "", required=True)
        ok = f.validate()
        self.assertFalse(ok)
        self.assertFalse(f.is_valid)
        self.assertTrue(len(f.errors) > 0)

    def test_required_field_non_empty_passes(self) -> None:
        f: FormField[str] = FormField("name", "Alice", required=True)
        ok = f.validate()
        self.assertTrue(ok)
        self.assertTrue(f.is_valid)

    def test_custom_validator_error(self) -> None:
        def must_be_positive(v: int) -> str | None:
            return None if v > 0 else "Must be positive"

        f: FormField[int] = FormField("count", -1, validators=[must_be_positive])
        ok = f.validate()
        self.assertFalse(ok)
        self.assertIn("Must be positive", f.errors)

    def test_custom_validator_passes(self) -> None:
        def must_be_positive(v: int) -> str | None:
            return None if v > 0 else "Must be positive"

        f: FormField[int] = FormField("count", 5, validators=[must_be_positive])
        ok = f.validate()
        self.assertTrue(ok)
        self.assertEqual(f.errors, [])

    def test_first_error_returns_first(self) -> None:
        def e1(v): return "error1"
        def e2(v): return "error2"
        f: FormField[str] = FormField("x", "val", validators=[e1, e2])
        f.validate()
        self.assertEqual(f.first_error, "error1")

    def test_reset_clears_errors(self) -> None:
        f: FormField[str] = FormField("name", "", required=True)
        f.validate()
        self.assertFalse(f.is_valid)
        f.reset()
        self.assertEqual(f.errors, [])

    def test_validator_exception_treated_as_error(self) -> None:
        def bad_rule(v):
            raise RuntimeError("oops")

        f: FormField[str] = FormField("x", "val", validators=[bad_rule])
        ok = f.validate()
        self.assertFalse(ok)


class TestFormFieldErrorsChangedCallback(unittest.TestCase):
    def test_callback_fired_on_error_state_change(self) -> None:
        f: FormField[str] = FormField("name", "", required=True)
        calls = []
        f.on_errors_changed(calls.append)
        f.validate()
        self.assertEqual(len(calls), 1)

    def test_unsubscribe_stops_callbacks(self) -> None:
        f: FormField[str] = FormField("name", "", required=True)
        calls = []
        unsub = f.on_errors_changed(calls.append)
        unsub()
        f.validate()
        self.assertEqual(len(calls), 0)


class TestFormModelAddField(unittest.TestCase):
    def test_add_field_returns_form_field(self) -> None:
        fm = FormModel()
        f = fm.add_field("username", "")
        self.assertIsInstance(f, FormField)

    def test_field_retrieval_by_name(self) -> None:
        fm = FormModel()
        fm.add_field("email", "user@example.com")
        f = fm.field("email")
        self.assertEqual(f.value.value, "user@example.com")

    def test_fields_property_returns_all(self) -> None:
        fm = FormModel()
        fm.add_field("a", 1)
        fm.add_field("b", 2)
        self.assertIn("a", fm.fields)
        self.assertIn("b", fm.fields)


class TestFormModelAggregateState(unittest.TestCase):
    def test_is_dirty_when_any_field_dirty(self) -> None:
        fm = FormModel()
        name = fm.add_field("name", "Alice")
        fm.add_field("age", 30)
        name.value.value = "Bob"
        self.assertTrue(fm.is_dirty)

    def test_not_dirty_initially(self) -> None:
        fm = FormModel()
        fm.add_field("name", "Alice")
        self.assertFalse(fm.is_dirty)

    def test_validate_all_runs_all_validators(self) -> None:
        fm = FormModel()
        fm.add_field("name", "", required=True)
        fm.add_field("age", -1, validators=[lambda v: None if v >= 0 else "Negative"])
        ok = fm.validate_all()
        self.assertFalse(ok)
        self.assertFalse(fm.is_valid)

    def test_validate_all_passes_when_all_valid(self) -> None:
        fm = FormModel()
        fm.add_field("name", "Alice", required=True)
        fm.add_field("age", 25)
        ok = fm.validate_all()
        self.assertTrue(ok)
        self.assertTrue(fm.is_valid)

    def test_commit_all_clears_dirty(self) -> None:
        fm = FormModel()
        name = fm.add_field("name", "Alice")
        name.value.value = "Bob"
        fm.commit_all()
        self.assertFalse(fm.is_dirty)

    def test_reset_all_reverts_all_fields(self) -> None:
        fm = FormModel()
        name = fm.add_field("name", "Alice")
        name.value.value = "Bob"
        fm.reset_all()
        self.assertEqual(name.value.value, "Alice")
        self.assertFalse(fm.is_dirty)

    def test_get_values_returns_snapshot(self) -> None:
        fm = FormModel()
        fm.add_field("x", 10)
        fm.add_field("y", 20)
        vals = fm.get_values()
        self.assertEqual(vals, {"x": 10, "y": 20})

    def test_get_errors_collects_field_errors(self) -> None:
        fm = FormModel()
        fm.add_field("name", "", required=True)
        fm.validate_all()
        errors = fm.get_errors()
        self.assertTrue(any(e.field_name == "name" for e in errors))


class TestFormModelCrossValidation(unittest.TestCase):
    def test_cross_validator_fires(self) -> None:
        fm = FormModel()
        pwd = fm.add_field("password", "abc")
        confirm = fm.add_field("confirm", "xyz")

        def passwords_match(form: FormModel):
            if form.field("password").value.value != form.field("confirm").value.value:
                return [FieldError("confirm", "Passwords do not match")]
            return None

        fm.add_cross_validator(passwords_match)
        ok = fm.validate_all()
        self.assertFalse(ok)
        self.assertFalse(fm.is_valid)
        cross = fm.cross_errors
        self.assertTrue(any(e.field_name == "confirm" for e in cross))

    def test_cross_validator_passes_when_fields_match(self) -> None:
        fm = FormModel()
        fm.add_field("password", "secret")
        fm.add_field("confirm", "secret")

        def passwords_match(form: FormModel):
            if form.field("password").value.value != form.field("confirm").value.value:
                return [FieldError("confirm", "Mismatch")]
            return None

        fm.add_cross_validator(passwords_match)
        ok = fm.validate_all()
        self.assertTrue(ok)

    def test_cross_validator_exception_is_swallowed(self) -> None:
        fm = FormModel()
        fm.add_field("x", 1)

        def bad_rule(form):
            raise RuntimeError("boom")

        fm.add_cross_validator(bad_rule)
        # Should not raise
        fm.validate_all()

    def test_reset_all_clears_cross_errors(self) -> None:
        fm = FormModel()
        fm.add_field("a", "x")
        fm.add_cross_validator(lambda f: [FieldError("a", "cross")])
        fm.validate_all()
        fm.reset_all()
        self.assertEqual(fm.cross_errors, [])


class TestFieldErrorDataclass(unittest.TestCase):
    def test_field_error_attributes(self) -> None:
        err = FieldError("email", "Invalid format")
        self.assertEqual(err.field_name, "email")
        self.assertEqual(err.message, "Invalid format")


class TestValidationRuleTypeAlias(unittest.TestCase):
    def test_callable_rule_is_valid(self) -> None:
        rule: ValidationRule = lambda v: None if v else "Required"
        self.assertIsNone(rule("hello"))
        self.assertEqual(rule(""), "Required")


if __name__ == "__main__":
    unittest.main()
