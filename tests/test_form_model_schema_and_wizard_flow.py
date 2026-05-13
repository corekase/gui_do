"""Tests for FormField, FormModel, FormSchema, WizardStep, and WizardFlow."""
import unittest

from gui_do.forms.form_model import FieldError, FormField, FormModel
from gui_do.forms.form_schema import FormSchema, SchemaField
from gui_do.forms.wizard_flow import WizardFlow, WizardStep


# ---------------------------------------------------------------------------
# Validator helpers
# ---------------------------------------------------------------------------


def _min_len(n):
    def _rule(v):
        return None if (v and len(str(v)) >= n) else f"Must be at least {n} chars."
    return _rule


def _is_positive(v):
    try:
        return None if float(v) > 0 else "Must be positive."
    except (TypeError, ValueError):
        return "Must be a number."


# ===========================================================================
# FormField
# ===========================================================================


class TestFormField(unittest.TestCase):
    def test_name(self):
        f = FormField("email", "")
        self.assertEqual("email", f.name)

    def test_initial_not_dirty(self):
        f = FormField("x", "hello")
        self.assertFalse(f.is_dirty)

    def test_value_change_marks_dirty(self):
        f = FormField("x", "hello")
        f.value.value = "world"
        self.assertTrue(f.is_dirty)

    def test_initially_valid_with_no_validators(self):
        f = FormField("x", "")
        self.assertTrue(f.is_valid)

    def test_validate_passes_valid_value(self):
        f = FormField("x", "abc", validators=[_min_len(2)])
        ok = f.validate()
        self.assertTrue(ok)
        self.assertEqual([], f.errors)

    def test_validate_fails_invalid_value(self):
        f = FormField("x", "a", validators=[_min_len(3)])
        ok = f.validate()
        self.assertFalse(ok)
        self.assertEqual(1, len(f.errors))

    def test_first_error(self):
        f = FormField("x", "a", validators=[_min_len(3)])
        f.validate()
        self.assertIsNotNone(f.first_error)

    def test_first_error_none_when_valid(self):
        f = FormField("x", "abc", validators=[_min_len(2)])
        f.validate()
        self.assertIsNone(f.first_error)

    def test_required_field_rejects_empty_string(self):
        f = FormField("x", "", required=True)
        ok = f.validate()
        self.assertFalse(ok)
        self.assertIn("required", f.first_error.lower())

    def test_required_field_passes_nonempty(self):
        f = FormField("x", "hi", required=True)
        self.assertTrue(f.validate())

    def test_commit_clears_dirty(self):
        f = FormField("x", "a")
        f.value.value = "b"
        f.commit()
        self.assertFalse(f.is_dirty)

    def test_reset_reverts_value(self):
        f = FormField("x", "original")
        f.value.value = "changed"
        f.reset()
        self.assertEqual("original", f.value.value)

    def test_reset_clears_errors(self):
        f = FormField("x", "a", validators=[_min_len(5)])
        f.validate()
        f.reset()
        self.assertEqual([], f.errors)

    def test_reset_fires_on_errors_changed(self):
        fired = []
        f = FormField("x", "a", validators=[_min_len(5)])
        f.validate()
        f.on_errors_changed(fired.append)
        f.reset()
        self.assertEqual(1, len(fired))
        self.assertEqual([], fired[0])

    def test_add_validator(self):
        f = FormField("x", -1)
        f.add_validator(_is_positive)
        self.assertFalse(f.validate())

    def test_on_errors_changed_fires_on_validate(self):
        fired = []
        f = FormField("x", "a", validators=[_min_len(5)])
        f.on_errors_changed(fired.append)
        f.validate()
        self.assertEqual(1, len(fired))

    def test_on_errors_changed_unsubscribe(self):
        fired = []
        f = FormField("x", "a", validators=[_min_len(5)])
        unsub = f.on_errors_changed(fired.append)
        unsub()
        f.validate()
        self.assertEqual([], fired)

    def test_errors_returns_copy(self):
        f = FormField("x", "a", validators=[_min_len(5)])
        f.validate()
        errs = f.errors
        errs.clear()
        self.assertEqual(1, len(f.errors))

    def test_validator_exception_adds_generic_error(self):
        def _bad(v):
            raise RuntimeError("boom")
        f = FormField("x", "v", validators=[_bad])
        f.validate()
        self.assertFalse(f.is_valid)


# ===========================================================================
# FormModel
# ===========================================================================


class TestFormModel(unittest.TestCase):
    def test_add_field_returns_form_field(self):
        form = FormModel()
        f = form.add_field("name", "")
        self.assertIsInstance(f, FormField)

    def test_field_lookup(self):
        form = FormModel()
        form.add_field("name", "Alice")
        self.assertEqual("Alice", form.field("name").value.value)

    def test_fields_dict(self):
        form = FormModel()
        form.add_field("a", 1)
        form.add_field("b", 2)
        self.assertIn("a", form.fields)
        self.assertIn("b", form.fields)

    def test_not_dirty_initially(self):
        form = FormModel()
        form.add_field("x", "v")
        self.assertFalse(form.is_dirty)

    def test_is_dirty_when_any_field_changed(self):
        form = FormModel()
        form.add_field("x", "v")
        form.field("x").value.value = "changed"
        self.assertTrue(form.is_dirty)

    def test_is_valid_initially_no_validators(self):
        form = FormModel()
        form.add_field("x", "v")
        self.assertTrue(form.is_valid)

    def test_validate_all_returns_false_on_error(self):
        form = FormModel()
        form.add_field("x", "a", validators=[_min_len(5)])
        ok = form.validate_all()
        self.assertFalse(ok)

    def test_validate_all_returns_true_when_valid(self):
        form = FormModel()
        form.add_field("x", "hello", validators=[_min_len(3)])
        self.assertTrue(form.validate_all())

    def test_get_errors_aggregates_field_errors(self):
        form = FormModel()
        form.add_field("a", "x", validators=[_min_len(5)])
        form.add_field("b", "y", validators=[_min_len(5)])
        # validate_all uses all() which short-circuits; validate each field directly
        form.field("a").validate()
        form.field("b").validate()
        errs = form.get_errors()
        self.assertEqual(2, len(errs))
        names = {e.field_name for e in errs}
        self.assertIn("a", names)
        self.assertIn("b", names)

    def test_commit_all_clears_dirty(self):
        form = FormModel()
        form.add_field("x", "v")
        form.field("x").value.value = "changed"
        form.commit_all()
        self.assertFalse(form.is_dirty)

    def test_reset_all_reverts_fields(self):
        form = FormModel()
        form.add_field("x", "original")
        form.field("x").value.value = "changed"
        form.reset_all()
        self.assertEqual("original", form.field("x").value.value)

    def test_get_values_snapshot(self):
        form = FormModel()
        form.add_field("a", 1)
        form.add_field("b", 2)
        form.field("a").value.value = 10
        vals = form.get_values()
        self.assertEqual({"a": 10, "b": 2}, vals)

    def test_cross_validator_no_errors(self):
        form = FormModel()
        form.add_field("a", 5)
        form.add_cross_validator(lambda f: None)
        self.assertTrue(form.validate_all())

    def test_cross_validator_with_errors(self):
        form = FormModel()
        form.add_field("pw", "abc")
        form.add_field("pw2", "xyz")
        def _passwords_match(frm):
            if frm.field("pw").value.value != frm.field("pw2").value.value:
                return [FieldError("pw2", "Passwords must match.")]
            return None
        form.add_cross_validator(_passwords_match)
        ok = form.validate_all()
        self.assertFalse(ok)
        cross = form.cross_errors
        self.assertEqual(1, len(cross))
        self.assertEqual("pw2", cross[0].field_name)

    def test_cross_errors_in_get_errors(self):
        form = FormModel()
        form.add_field("x", 0)
        form.add_cross_validator(lambda _: [FieldError("x", "cross error")])
        form.validate_all()
        msgs = [e.message for e in form.get_errors()]
        self.assertIn("cross error", msgs)

    def test_reset_all_clears_cross_errors(self):
        form = FormModel()
        form.add_field("x", 0)
        form.add_cross_validator(lambda _: [FieldError("x", "e")])
        form.validate_all()
        form.reset_all()
        self.assertEqual([], form.cross_errors)


# ===========================================================================
# FormSchema
# ===========================================================================


class TestFormSchema(unittest.TestCase):
    def _schema(self):
        return FormSchema([
            SchemaField("name", "", label="Name", required=True),
            SchemaField("age", 0, label="Age", validators=[_is_positive]),
        ])

    def test_fields_property(self):
        s = self._schema()
        self.assertEqual(2, len(s.fields))

    def test_duplicate_names_raises(self):
        with self.assertRaises(ValueError):
            FormSchema([
                SchemaField("x", ""),
                SchemaField("x", ""),
            ])

    def test_build_form_creates_form_model(self):
        s = self._schema()
        form = s.build_form()
        self.assertIsInstance(form, FormModel)
        self.assertIn("name", form.fields)
        self.assertIn("age", form.fields)

    def test_build_form_applies_required(self):
        s = self._schema()
        form = s.build_form()
        name_field = form.field("name")
        name_field.validate()
        self.assertFalse(name_field.is_valid)

    def test_build_form_applies_validators(self):
        s = self._schema()
        form = s.build_form()
        form.field("age").value.value = -1
        self.assertFalse(form.field("age").validate())

    def test_defaults(self):
        s = self._schema()
        d = s.defaults()
        self.assertEqual({"name": "", "age": 0}, d)

    def test_validate_values_with_valid_data(self):
        s = self._schema()
        errors = s.validate_values({"name": "Alice", "age": 25})
        self.assertEqual([], errors)

    def test_validate_values_with_invalid_data(self):
        s = self._schema()
        errors = s.validate_values({"name": "", "age": -1})
        field_names = {e.field_name for e in errors}
        self.assertIn("name", field_names)
        self.assertIn("age", field_names)

    def test_apply_to(self):
        s = self._schema()
        form = s.build_form()
        s.apply_to(form, {"name": "Bob", "age": 30})
        self.assertEqual("Bob", form.field("name").value.value)
        self.assertEqual(30, form.field("age").value.value)

    def test_apply_to_skips_missing_keys(self):
        s = self._schema()
        form = s.build_form()
        s.apply_to(form, {"name": "Carol"})   # "age" not in values
        self.assertEqual(0, form.field("age").value.value)

    def test_extract_from(self):
        s = self._schema()
        form = s.build_form()
        form.field("name").value.value = "Dave"
        form.field("age").value.value = 40
        d = s.extract_from(form)
        self.assertEqual({"name": "Dave", "age": 40}, d)


# ===========================================================================
# WizardFlow
# ===========================================================================


class TestWizardFlow(unittest.TestCase):
    def _two_step_wizard(self, on_complete=None, on_cancel=None):
        steps = [
            WizardStep(title="Step 1", fields=["name"]),
            WizardStep(title="Step 2", fields=["age"]),
        ]
        return WizardFlow(
            steps,
            on_complete=on_complete or (lambda d: None),
            on_cancel=on_cancel,
        )

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def test_empty_steps_raises(self):
        with self.assertRaises(ValueError):
            WizardFlow([], on_complete=lambda d: None)

    def test_initial_step_index_is_zero(self):
        wiz = self._two_step_wizard()
        self.assertEqual(0, wiz.step_index)

    def test_step_count(self):
        wiz = self._two_step_wizard()
        self.assertEqual(2, wiz.step_count)

    def test_current_step_title(self):
        wiz = self._two_step_wizard()
        self.assertEqual("Step 1", wiz.current_step.title)

    def test_initial_progress_is_zero(self):
        wiz = self._two_step_wizard()
        self.assertAlmostEqual(0.0, wiz.progress.value)

    # ------------------------------------------------------------------
    # Navigation — advance
    # ------------------------------------------------------------------

    def test_advance_without_validator_succeeds(self):
        wiz = self._two_step_wizard()
        ok, errors = wiz.advance({"name": "Alice"})
        self.assertTrue(ok)
        self.assertEqual([], errors)

    def test_advance_moves_to_next_step(self):
        wiz = self._two_step_wizard()
        wiz.advance({"name": "Alice"})
        self.assertEqual(1, wiz.step_index)

    def test_advance_updates_progress(self):
        wiz = self._two_step_wizard()
        wiz.advance({"name": "Alice"})
        self.assertGreater(wiz.progress.value, 0.0)

    def test_advance_collects_data(self):
        wiz = self._two_step_wizard()
        wiz.advance({"name": "Alice"})
        self.assertEqual("Alice", wiz.collected_data.get("name"))

    def test_advance_validation_failure(self):
        steps = [WizardStep(title="S1", on_validate=lambda d: ["Name required"] if not d.get("name") else [])]
        wiz = WizardFlow(steps, on_complete=lambda d: None)
        ok, errors = wiz.advance({})
        self.assertFalse(ok)
        self.assertIn("Name required", errors)
        self.assertEqual(0, wiz.step_index)

    def test_last_step_advance_calls_on_complete(self):
        completed = []
        wiz = self._two_step_wizard(on_complete=completed.append)
        wiz.advance({"name": "Alice"})
        wiz.advance({"age": 30})
        self.assertEqual(1, len(completed))
        self.assertEqual("Alice", completed[0]["name"])
        self.assertEqual(30, completed[0]["age"])

    def test_last_step_advance_sets_progress_to_one(self):
        wiz = self._two_step_wizard()
        wiz.advance({})
        wiz.advance({})
        self.assertAlmostEqual(1.0, wiz.progress.value)

    def test_step_data_recorded(self):
        wiz = self._two_step_wizard()
        wiz.advance({"name": "Alice"})
        self.assertEqual({"name": "Alice"}, wiz.step_data(0))

    def test_step_data_none_before_visit(self):
        wiz = self._two_step_wizard()
        self.assertIsNone(wiz.step_data(1))

    # ------------------------------------------------------------------
    # Navigation — back
    # ------------------------------------------------------------------

    def test_back_from_step_zero_returns_false(self):
        wiz = self._two_step_wizard()
        self.assertFalse(wiz.back())

    def test_back_decrements_step(self):
        wiz = self._two_step_wizard()
        wiz.advance({})
        wiz.back()
        self.assertEqual(0, wiz.step_index)

    def test_back_returns_true(self):
        wiz = self._two_step_wizard()
        wiz.advance({})
        self.assertTrue(wiz.back())

    # ------------------------------------------------------------------
    # Cancel
    # ------------------------------------------------------------------

    def test_cancel_fires_on_cancel(self):
        fired = []
        wiz = self._two_step_wizard(on_cancel=lambda: fired.append(True))
        wiz.cancel()
        self.assertEqual([True], fired)

    def test_cancel_sets_is_cancelled(self):
        wiz = self._two_step_wizard()
        wiz.cancel()
        self.assertTrue(wiz.is_cancelled)

    # ------------------------------------------------------------------
    # WizardHandle
    # ------------------------------------------------------------------

    def test_handle_cancel_delegates(self):
        fired = []
        wiz = self._two_step_wizard(on_cancel=lambda: fired.append(True))
        h = wiz.handle()
        h.cancel()
        self.assertTrue(h.is_cancelled)
        self.assertEqual([True], fired)

    def test_handle_flow_reference(self):
        wiz = self._two_step_wizard()
        h = wiz.handle()
        self.assertIs(wiz, h.flow)

    # ------------------------------------------------------------------
    # Callbacks — on_enter / on_leave
    # ------------------------------------------------------------------

    def test_on_enter_called_for_first_step(self):
        entered = []
        s0 = WizardStep(title="S0", on_enter=lambda d: entered.append(0))
        WizardFlow([s0], on_complete=lambda d: None)
        self.assertEqual([0], entered)

    def test_on_enter_called_on_advance(self):
        entered = []
        s0 = WizardStep(title="S0")
        s1 = WizardStep(title="S1", on_enter=lambda d: entered.append(1))
        wiz = WizardFlow([s0, s1], on_complete=lambda d: None)
        wiz.advance({})
        self.assertEqual([1], entered)

    def test_on_leave_called_on_advance(self):
        left = []
        s0 = WizardStep(title="S0", on_leave=lambda d, dir: left.append(dir))
        s1 = WizardStep(title="S1")
        wiz = WizardFlow([s0, s1], on_complete=lambda d: None)
        wiz.advance({})
        self.assertEqual(["forward"], left)

    def test_progress_observable(self):
        wiz = self._two_step_wizard()
        values = []
        wiz.progress.subscribe(values.append)
        wiz.advance({})
        self.assertTrue(any(v > 0 for v in values))


if __name__ == "__main__":
    unittest.main()
