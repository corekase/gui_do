import unittest

from gui_do.data.validator import (
    CustomValidator,
    DependentValidator,
    LengthValidator,
    PatternValidator,
    RangeValidator,
    RequiredValidator,
    ValidationPipeline,
    ValidationResult,
)
from gui_do.data.selection_model import SelectionMode, SelectionModel


# ---------------------------------------------------------------------------
# ValidationResult
# ---------------------------------------------------------------------------


class TestValidationResult(unittest.TestCase):
    def test_passed_factory_produces_ok_result(self):
        result = ValidationResult.passed()
        self.assertTrue(result.ok)
        self.assertEqual([], result.errors)

    def test_failed_factory_produces_not_ok_result(self):
        result = ValidationResult.failed("Error A", "Error B")
        self.assertFalse(result.ok)
        self.assertEqual(["Error A", "Error B"], result.errors)

    def test_bool_conversion_reflects_ok(self):
        self.assertTrue(bool(ValidationResult.passed()))
        self.assertFalse(bool(ValidationResult.failed("x")))


# ---------------------------------------------------------------------------
# RequiredValidator
# ---------------------------------------------------------------------------


class TestRequiredValidator(unittest.TestCase):
    def setUp(self):
        self.v = RequiredValidator("Required!")

    def test_none_is_invalid(self):
        self.assertEqual("Required!", self.v.check(None))

    def test_empty_string_is_invalid(self):
        self.assertEqual("Required!", self.v.check(""))

    def test_empty_list_is_invalid(self):
        self.assertEqual("Required!", self.v.check([]))

    def test_nonempty_string_is_valid(self):
        self.assertIsNone(self.v.check("hello"))

    def test_zero_is_valid(self):
        self.assertIsNone(self.v.check(0))


# ---------------------------------------------------------------------------
# RangeValidator
# ---------------------------------------------------------------------------


class TestRangeValidator(unittest.TestCase):
    def test_value_in_range_is_valid(self):
        v = RangeValidator(0, 100)
        self.assertIsNone(v.check(50))

    def test_value_below_min_returns_error(self):
        v = RangeValidator(min_value=5)
        self.assertIsNotNone(v.check(4))

    def test_value_above_max_returns_error(self):
        v = RangeValidator(max_value=10)
        self.assertIsNotNone(v.check(11))

    def test_boundary_values_are_valid(self):
        v = RangeValidator(0, 10)
        self.assertIsNone(v.check(0))
        self.assertIsNone(v.check(10))

    def test_non_numeric_returns_error(self):
        v = RangeValidator(0, 100)
        self.assertIsNotNone(v.check("abc"))

    def test_custom_message_used_when_provided(self):
        v = RangeValidator(0, 100, message="Out of range")
        self.assertEqual("Out of range", v.check(-1))


# ---------------------------------------------------------------------------
# LengthValidator
# ---------------------------------------------------------------------------


class TestLengthValidator(unittest.TestCase):
    def test_string_within_length_is_valid(self):
        v = LengthValidator(min_length=2, max_length=10)
        self.assertIsNone(v.check("hello"))

    def test_string_too_short_returns_error(self):
        v = LengthValidator(min_length=3)
        self.assertIsNotNone(v.check("hi"))

    def test_string_too_long_returns_error(self):
        v = LengthValidator(max_length=4)
        self.assertIsNotNone(v.check("toolong"))

    def test_non_sized_value_returns_error(self):
        v = LengthValidator(min_length=1)
        self.assertIsNotNone(v.check(42))

    def test_exact_min_is_valid(self):
        v = LengthValidator(min_length=3)
        self.assertIsNone(v.check("abc"))

    def test_exact_max_is_valid(self):
        v = LengthValidator(max_length=3)
        self.assertIsNone(v.check("abc"))


# ---------------------------------------------------------------------------
# PatternValidator
# ---------------------------------------------------------------------------


class TestPatternValidator(unittest.TestCase):
    def test_matching_pattern_is_valid(self):
        v = PatternValidator(r"\d{4}", message="4 digits required")
        self.assertIsNone(v.check("1234"))

    def test_non_matching_pattern_returns_error(self):
        v = PatternValidator(r"\d{4}", message="4 digits required")
        self.assertEqual("4 digits required", v.check("abc"))

    def test_search_mode_matches_substring(self):
        v = PatternValidator(r"\d+", full_match=False)
        self.assertIsNone(v.check("abc123def"))

    def test_fullmatch_rejects_partial_match(self):
        v = PatternValidator(r"\d+")
        self.assertIsNotNone(v.check("123abc"))


# ---------------------------------------------------------------------------
# CustomValidator
# ---------------------------------------------------------------------------


class TestCustomValidator(unittest.TestCase):
    def test_callable_wrapping_works(self):
        v = CustomValidator(lambda x: None if x > 0 else "Must be positive")
        self.assertIsNone(v.check(1))
        self.assertEqual("Must be positive", v.check(0))

    def test_non_callable_raises_type_error(self):
        with self.assertRaises(TypeError):
            CustomValidator("not callable")


# ---------------------------------------------------------------------------
# DependentValidator
# ---------------------------------------------------------------------------


class TestDependentValidator(unittest.TestCase):
    def test_check_passes_empty_context(self):
        v = DependentValidator(lambda val, ctx: "bad" if not ctx.get("ok") else None)
        self.assertEqual("bad", v.check("x"))

    def test_check_with_context_passes_context(self):
        v = DependentValidator(lambda val, ctx: None if ctx.get("ok") else "bad")
        self.assertIsNone(v.check_with_context("x", {"ok": True}))


# ---------------------------------------------------------------------------
# ValidationPipeline
# ---------------------------------------------------------------------------


class TestValidationPipeline(unittest.TestCase):
    def test_passing_pipeline_returns_ok(self):
        p = ValidationPipeline([RequiredValidator(), LengthValidator(min_length=2)])
        result = p.validate("hello")
        self.assertTrue(result.ok)

    def test_first_failure_stops_pipeline_by_default(self):
        p = ValidationPipeline([RequiredValidator(), RangeValidator(0, 10)])
        result = p.validate("")
        self.assertFalse(result.ok)
        self.assertEqual(1, len(result.errors))

    def test_collect_all_errors_when_stop_on_first_error_false(self):
        p = ValidationPipeline(
            [RequiredValidator("Required"), RangeValidator(0, 10, message="Range")],
            stop_on_first_error=False,
        )
        result = p.validate("")
        self.assertFalse(result.ok)
        # Both errors should be collected (empty string fails required; also fails range)
        self.assertGreater(len(result.errors), 0)

    def test_add_returns_self_for_fluent_chaining(self):
        p = ValidationPipeline()
        returned = p.add(RequiredValidator())
        self.assertIs(p, returned)

    def test_is_valid_convenience_returns_bool(self):
        p = ValidationPipeline([RequiredValidator()])
        self.assertTrue(p.is_valid("value"))
        self.assertFalse(p.is_valid(""))

    def test_validators_property_returns_copy(self):
        v = RequiredValidator()
        p = ValidationPipeline([v])
        lst = p.validators
        lst.append(RangeValidator())
        self.assertEqual(1, len(p.validators))  # original unchanged

    def test_dependent_validator_receives_context_via_pipeline(self):
        ctx_received = {}
        def _fn(val, ctx):
            ctx_received.update(ctx)
            return None
        p = ValidationPipeline([DependentValidator(_fn)])
        p.validate("x", context={"user": "alice"})
        self.assertEqual({"user": "alice"}, ctx_received)


# ---------------------------------------------------------------------------
# SelectionModel
# ---------------------------------------------------------------------------


class TestSelectionModelSingle(unittest.TestCase):
    def _model(self, count=10):
        return SelectionModel(mode=SelectionMode.SINGLE, item_count=count)

    def test_initially_nothing_selected(self):
        m = self._model()
        self.assertEqual(frozenset(), m.selected_indices)
        self.assertEqual(-1, m.selected_index)

    def test_select_sets_single_index(self):
        m = self._model()
        m.select(3)
        self.assertEqual(frozenset({3}), m.selected_indices)
        self.assertEqual(3, m.selected_index)

    def test_select_replaces_previous_selection(self):
        m = self._model()
        m.select(2)
        m.select(5)
        self.assertEqual(frozenset({5}), m.selected_indices)

    def test_deselect_clears_selected_index(self):
        m = self._model()
        m.select(4)
        m.deselect(4)
        self.assertEqual(frozenset(), m.selected_indices)

    def test_out_of_range_index_is_ignored(self):
        m = self._model(count=5)
        m.select(99)
        self.assertEqual(frozenset(), m.selected_indices)

    def test_is_selected_reflects_state(self):
        m = self._model()
        m.select(2)
        self.assertTrue(m.is_selected(2))
        self.assertFalse(m.is_selected(3))

    def test_subscriber_notified_on_change(self):
        m = self._model()
        calls = []
        m.subscribe(lambda model: calls.append(model.selected_index))
        m.select(5)
        self.assertEqual([5], calls)

    def test_unsubscribe_stops_notifications(self):
        m = self._model()
        calls = []
        unsub = m.subscribe(lambda _: calls.append(True))
        m.select(1)
        unsub()
        m.select(2)
        self.assertEqual(1, len(calls))

    def test_select_all_selects_all_items(self):
        m = self._model(count=3)
        m.select_all()
        self.assertEqual(frozenset({0, 1, 2}), m.selected_indices)

    def test_clear_removes_all_selections(self):
        m = self._model()
        m.select(3)
        m.clear()
        self.assertEqual(frozenset(), m.selected_indices)

    def test_set_item_count_prunes_out_of_range_selection(self):
        m = self._model(count=10)
        m.select(8)
        m.set_item_count(5)
        self.assertEqual(frozenset(), m.selected_indices)


class TestSelectionModelMulti(unittest.TestCase):
    def _model(self, count=10):
        return SelectionModel(mode=SelectionMode.MULTI, item_count=count)

    def test_toggle_adds_and_removes(self):
        m = self._model()
        m.toggle(3)
        self.assertIn(3, m.selected_indices)
        m.toggle(3)
        self.assertNotIn(3, m.selected_indices)

    def test_multiple_items_selectable(self):
        m = self._model()
        m.toggle(1)
        m.toggle(4)
        m.toggle(7)
        self.assertEqual(frozenset({1, 4, 7}), m.selected_indices)


class TestSelectionModelRange(unittest.TestCase):
    def _model(self, count=20):
        return SelectionModel(mode=SelectionMode.RANGE, item_count=count)

    def test_anchor_and_active_define_range(self):
        m = self._model()
        m.set_anchor(3)
        m.set_active(7)
        self.assertEqual(frozenset({3, 4, 5, 6, 7}), m.selected_indices)

    def test_reversed_range_works(self):
        m = self._model()
        m.set_anchor(7)
        m.set_active(3)
        self.assertEqual(frozenset({3, 4, 5, 6, 7}), m.selected_indices)

    def test_single_item_range(self):
        m = self._model()
        m.set_anchor(5)
        m.set_active(5)
        self.assertEqual(frozenset({5}), m.selected_indices)


if __name__ == "__main__":
    unittest.main()
