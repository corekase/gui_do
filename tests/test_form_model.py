"""Tests for FormField and FormModel — reactive form validation."""
import unittest

from gui_do.forms.form_model import FieldError, FormField, FormModel


# ===========================================================================
# FieldError
# ===========================================================================


class TestFieldError(unittest.TestCase):
    def test_fields_stored(self):
        e = FieldError(field_name="email", message="Invalid email.")
        self.assertEqual("email", e.field_name)
        self.assertEqual("Invalid email.", e.message)


# ===========================================================================
# FormField — initial state
# ===========================================================================


class TestFormFieldInitial(unittest.TestCase):
    def test_name_stored(self):
        f = FormField("age", 0)
        self.assertEqual("age", f.name)

    def test_initial_value(self):
        f = FormField("name", "Alice")
        self.assertEqual("Alice", f.value.value)

    def test_not_dirty_initially(self):
        f = FormField("x", 10)
        self.assertFalse(f.is_dirty)

    def test_valid_initially(self):
        f = FormField("x", 10)
        self.assertTrue(f.is_valid)

    def test_no_errors_initially(self):
        f = FormField("x", 10)
        self.assertEqual([], f.errors)

    def test_first_error_none_initially(self):
        f = FormField("x", 10)
        self.assertIsNone(f.first_error)


# ===========================================================================
# FormField — dirty tracking
# ===========================================================================


class TestFormFieldDirty(unittest.TestCase):
    def test_becomes_dirty_on_value_change(self):
        f = FormField("n", 0)
        f.value.value = 5
        self.assertTrue(f.is_dirty)

    def test_commit_clears_dirty(self):
        f = FormField("n", 0)
        f.value.value = 5
        f.commit()
        self.assertFalse(f.is_dirty)

    def test_reset_reverts_value(self):
        f = FormField("n", 0)
        f.value.value = 5
        f.reset()
        self.assertEqual(0, f.value.value)
        self.assertFalse(f.is_dirty)


# ===========================================================================
# FormField — validation
# ===========================================================================


class TestFormFieldValidation(unittest.TestCase):
    def test_validator_on_valid_value(self):
        f = FormField("n", 5, validators=[lambda v: None if v > 0 else "Must be positive"])
        self.assertTrue(f.validate())
        self.assertEqual([], f.errors)

    def test_validator_on_invalid_value(self):
        f = FormField("n", -1, validators=[lambda v: None if v > 0 else "Must be positive"])
        self.assertFalse(f.validate())
        self.assertEqual(["Must be positive"], f.errors)

    def test_first_error_set(self):
        f = FormField("n", -1, validators=[lambda v: "Bad"])
        f.validate()
        self.assertEqual("Bad", f.first_error)

    def test_required_field_empty_fails(self):
        f = FormField("name", "", required=True)
        self.assertFalse(f.validate())
        self.assertGreater(len(f.errors), 0)

    def test_required_field_nonempty_passes(self):
        f = FormField("name", "Alice", required=True)
        self.assertTrue(f.validate())

    def test_add_validator_after_init(self):
        f = FormField("n", 0)
        f.add_validator(lambda v: "Error" if v == 0 else None)
        f.validate()
        self.assertEqual(["Error"], f.errors)

    def test_errors_changed_callback(self):
        calls = []
        f = FormField("n", -1, validators=[lambda v: "Bad" if v < 0 else None])
        f.on_errors_changed(lambda errs: calls.append(list(errs)))
        f.validate()
        self.assertEqual([["Bad"]], calls)

    def test_errors_changed_unsubscribe(self):
        calls = []
        f = FormField("n", -1, validators=[lambda v: "Bad" if v < 0 else None])
        unsub = f.on_errors_changed(lambda errs: calls.append(errs))
        unsub()
        f.validate()
        self.assertEqual([], calls)

    def test_reset_clears_errors(self):
        f = FormField("n", -1, validators=[lambda v: "Bad" if v < 0 else None])
        f.validate()
        f.reset()
        self.assertEqual([], f.errors)


# ===========================================================================
# FormModel — construction
# ===========================================================================


class TestFormModelInitial(unittest.TestCase):
    def test_no_fields_initially(self):
        m = FormModel()
        self.assertEqual({}, m.fields)

    def test_is_valid_empty(self):
        m = FormModel()
        self.assertTrue(m.is_valid)

    def test_is_dirty_empty(self):
        m = FormModel()
        self.assertFalse(m.is_dirty)


# ===========================================================================
# FormModel — add_field / field
# ===========================================================================


class TestFormModelAddField(unittest.TestCase):
    def test_add_field_returns_form_field(self):
        m = FormModel()
        f = m.add_field("name", "")
        self.assertIsInstance(f, FormField)

    def test_field_accessor(self):
        m = FormModel()
        m.add_field("age", 25)
        self.assertEqual(25, m.field("age").value.value)

    def test_fields_dict_has_all(self):
        m = FormModel()
        m.add_field("a", 1)
        m.add_field("b", 2)
        self.assertIn("a", m.fields)
        self.assertIn("b", m.fields)


# ===========================================================================
# FormModel — validate_all / commit_all / reset_all
# ===========================================================================


class TestFormModelValidation(unittest.TestCase):
    def test_validate_all_passes_when_all_fields_valid(self):
        m = FormModel()
        m.add_field("n", 5, validators=[lambda v: None if v > 0 else "Error"])
        self.assertTrue(m.validate_all())

    def test_validate_all_fails_when_field_invalid(self):
        m = FormModel()
        m.add_field("n", -1, validators=[lambda v: "Error" if v < 0 else None])
        self.assertFalse(m.validate_all())
        self.assertFalse(m.is_valid)

    def test_commit_all_clears_dirty(self):
        m = FormModel()
        f = m.add_field("x", 0)
        f.value.value = 99
        m.commit_all()
        self.assertFalse(m.is_dirty)

    def test_reset_all_reverts_fields(self):
        m = FormModel()
        f = m.add_field("x", 0)
        f.value.value = 99
        m.reset_all()
        self.assertEqual(0, f.value.value)

    def test_cross_validator_fires(self):
        m = FormModel()
        m.add_field("start", 5)
        m.add_field("end", 3)

        def cross(form):
            s = form.field("start").value.value
            e = form.field("end").value.value
            if s >= e:
                return [FieldError("end", "End must be after start.")]
            return None

        m.add_cross_validator(cross)
        self.assertFalse(m.validate_all())
        self.assertEqual(1, len(m.cross_errors))

    def test_get_values_snapshot(self):
        m = FormModel()
        m.add_field("a", 1)
        m.add_field("b", "hello")
        snap = m.get_values()
        self.assertEqual({"a": 1, "b": "hello"}, snap)

    def test_get_errors_combines_field_and_cross(self):
        m = FormModel()
        m.add_field("n", -1, validators=[lambda v: "Bad" if v < 0 else None])
        m.validate_all()
        errs = m.get_errors()
        self.assertTrue(any(e.message == "Bad" for e in errs))


if __name__ == "__main__":
    unittest.main()
