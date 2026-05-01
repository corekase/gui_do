"""Tests for ValidationResult, built-in Validators, and ValidationPipeline."""
import unittest

from gui_do.data.validator import (
    ValidationResult,
    RequiredValidator,
    RangeValidator,
    LengthValidator,
    PatternValidator,
    CustomValidator,
    DependentValidator,
    ValidationPipeline,
)


# ===========================================================================
# ValidationResult
# ===========================================================================


class TestValidationResult(unittest.TestCase):
    def test_passed_factory(self):
        r = ValidationResult.passed()
        self.assertTrue(r.ok)
        self.assertEqual([], r.errors)

    def test_failed_factory(self):
        r = ValidationResult.failed("Required", "Too short")
        self.assertFalse(r.ok)
        self.assertEqual(["Required", "Too short"], r.errors)

    def test_bool_true_when_ok(self):
        self.assertTrue(bool(ValidationResult.passed()))

    def test_bool_false_when_failed(self):
        self.assertFalse(bool(ValidationResult.failed("oops")))


# ===========================================================================
# RequiredValidator
# ===========================================================================


class TestRequiredValidator(unittest.TestCase):
    def test_none_rejected(self):
        v = RequiredValidator()
        self.assertIsNotNone(v.check(None))

    def test_empty_string_rejected(self):
        v = RequiredValidator()
        self.assertIsNotNone(v.check(""))

    def test_non_empty_string_accepted(self):
        v = RequiredValidator()
        self.assertIsNone(v.check("hello"))

    def test_empty_list_rejected(self):
        v = RequiredValidator()
        self.assertIsNotNone(v.check([]))

    def test_non_empty_list_accepted(self):
        v = RequiredValidator()
        self.assertIsNone(v.check([1]))

    def test_custom_message(self):
        v = RequiredValidator("Name required")
        self.assertEqual("Name required", v.check(""))


# ===========================================================================
# RangeValidator
# ===========================================================================


class TestRangeValidator(unittest.TestCase):
    def test_within_range_ok(self):
        v = RangeValidator(0, 100)
        self.assertIsNone(v.check(50))

    def test_below_min_rejected(self):
        v = RangeValidator(min_value=0)
        self.assertIsNotNone(v.check(-1))

    def test_above_max_rejected(self):
        v = RangeValidator(max_value=10)
        self.assertIsNotNone(v.check(11))

    def test_at_bounds_accepted(self):
        v = RangeValidator(0, 10)
        self.assertIsNone(v.check(0))
        self.assertIsNone(v.check(10))

    def test_non_numeric_rejected(self):
        v = RangeValidator(0, 100)
        self.assertIsNotNone(v.check("abc"))

    def test_custom_message(self):
        v = RangeValidator(0, 10, message="Out of range")
        msg = v.check(99)
        self.assertEqual("Out of range", msg)


# ===========================================================================
# LengthValidator
# ===========================================================================


class TestLengthValidator(unittest.TestCase):
    def test_within_length_ok(self):
        v = LengthValidator(2, 10)
        self.assertIsNone(v.check("hello"))

    def test_too_short_rejected(self):
        v = LengthValidator(min_length=3)
        self.assertIsNotNone(v.check("ab"))

    def test_too_long_rejected(self):
        v = LengthValidator(max_length=5)
        self.assertIsNotNone(v.check("toolongstring"))

    def test_at_min_length_ok(self):
        v = LengthValidator(min_length=3)
        self.assertIsNone(v.check("abc"))

    def test_no_len_attribute_rejected(self):
        v = LengthValidator(min_length=1)
        self.assertIsNotNone(v.check(42))


# ===========================================================================
# PatternValidator
# ===========================================================================


class TestPatternValidator(unittest.TestCase):
    def test_matching_pattern_ok(self):
        v = PatternValidator(r"\d{3}-\d{4}")
        self.assertIsNone(v.check("555-1234"))

    def test_non_matching_rejected(self):
        v = PatternValidator(r"\d+")
        self.assertIsNotNone(v.check("abc"))

    def test_partial_match_with_search(self):
        v = PatternValidator(r"\d+", full_match=False)
        self.assertIsNone(v.check("abc123"))

    def test_custom_message(self):
        v = PatternValidator(r"\d+", message="Digits only")
        self.assertEqual("Digits only", v.check("abc"))


# ===========================================================================
# CustomValidator
# ===========================================================================


class TestCustomValidator(unittest.TestCase):
    def test_passes_when_fn_returns_none(self):
        v = CustomValidator(lambda x: None)
        self.assertIsNone(v.check("anything"))

    def test_fails_when_fn_returns_string(self):
        v = CustomValidator(lambda x: "bad" if x < 0 else None)
        self.assertEqual("bad", v.check(-1))
        self.assertIsNone(v.check(1))

    def test_non_callable_raises(self):
        with self.assertRaises(TypeError):
            CustomValidator("not_callable")  # type: ignore


# ===========================================================================
# DependentValidator
# ===========================================================================


class TestDependentValidator(unittest.TestCase):
    def test_check_with_context(self):
        v = DependentValidator(lambda val, ctx: "taken" if ctx.get("exists") else None)
        self.assertIsNone(v.check_with_context("alice", {"exists": False}))
        self.assertEqual("taken", v.check_with_context("alice", {"exists": True}))

    def test_check_without_context_uses_empty_dict(self):
        v = DependentValidator(lambda val, ctx: None)
        self.assertIsNone(v.check("x"))


# ===========================================================================
# ValidationPipeline
# ===========================================================================


class TestValidationPipeline(unittest.TestCase):
    def test_all_pass_returns_ok(self):
        p = ValidationPipeline([RequiredValidator(), LengthValidator(min_length=1)])
        self.assertTrue(p.validate("hello").ok)

    def test_first_error_stops_pipeline(self):
        p = ValidationPipeline([RequiredValidator(), RangeValidator(0, 10)])
        result = p.validate("")
        self.assertFalse(result.ok)
        self.assertEqual(1, len(result.errors))

    def test_collect_all_errors(self):
        p = ValidationPipeline(
            [
                RangeValidator(max_value=0),
                LengthValidator(max_length=0),
            ],
            stop_on_first_error=False,
        )
        result = p.validate(5)  # fails range; fails length (len(5) raises → error)
        self.assertFalse(result.ok)

    def test_add_fluent(self):
        p = ValidationPipeline()
        p2 = p.add(RequiredValidator())
        self.assertIs(p, p2)

    def test_is_valid_shorthand(self):
        p = ValidationPipeline([RequiredValidator()])
        self.assertTrue(p.is_valid("x"))
        self.assertFalse(p.is_valid(""))

    def test_empty_pipeline_passes_anything(self):
        p = ValidationPipeline()
        self.assertTrue(p.validate(None).ok)

    def test_context_forwarded_to_dependent(self):
        p = ValidationPipeline([
            DependentValidator(lambda v, ctx: "bad" if ctx.get("flag") else None)
        ])
        self.assertFalse(p.validate("x", context={"flag": True}).ok)
        self.assertTrue(p.validate("x", context={"flag": False}).ok)


if __name__ == "__main__":
    unittest.main()
