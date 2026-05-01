"""Tests for validator classes and ValidationPipeline."""
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
    def test_passed(self):
        r = ValidationResult.passed()
        self.assertTrue(r.ok)
        self.assertEqual([], r.errors)

    def test_failed(self):
        r = ValidationResult.failed("error1", "error2")
        self.assertFalse(r.ok)
        self.assertEqual(["error1", "error2"], r.errors)

    def test_bool_true(self):
        self.assertTrue(bool(ValidationResult.passed()))

    def test_bool_false(self):
        self.assertFalse(bool(ValidationResult.failed("error")))


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

    def test_empty_list_rejected(self):
        v = RequiredValidator()
        self.assertIsNotNone(v.check([]))

    def test_nonempty_string_accepted(self):
        v = RequiredValidator()
        self.assertIsNone(v.check("hello"))

    def test_custom_message(self):
        v = RequiredValidator("custom error")
        self.assertEqual("custom error", v.check(None))

    def test_callable(self):
        v = RequiredValidator()
        result = v("value")
        self.assertIsNone(result)


# ===========================================================================
# RangeValidator
# ===========================================================================


class TestRangeValidator(unittest.TestCase):
    def test_within_range(self):
        v = RangeValidator(0, 100)
        self.assertIsNone(v.check(50))

    def test_below_min(self):
        v = RangeValidator(0, 100)
        self.assertIsNotNone(v.check(-1))

    def test_above_max(self):
        v = RangeValidator(0, 100)
        self.assertIsNotNone(v.check(101))

    def test_at_min_boundary(self):
        v = RangeValidator(0, 100)
        self.assertIsNone(v.check(0))

    def test_at_max_boundary(self):
        v = RangeValidator(0, 100)
        self.assertIsNone(v.check(100))

    def test_no_bounds(self):
        v = RangeValidator()
        self.assertIsNone(v.check(99999))

    def test_non_numeric_rejected(self):
        v = RangeValidator(0, 100)
        self.assertIsNotNone(v.check("abc"))

    def test_custom_message(self):
        v = RangeValidator(0, 10, message="out of range")
        self.assertEqual("out of range", v.check(20))


# ===========================================================================
# LengthValidator
# ===========================================================================


class TestLengthValidator(unittest.TestCase):
    def test_valid_length(self):
        v = LengthValidator(2, 10)
        self.assertIsNone(v.check("hello"))

    def test_too_short(self):
        v = LengthValidator(min_length=3)
        self.assertIsNotNone(v.check("ab"))

    def test_too_long(self):
        v = LengthValidator(max_length=5)
        self.assertIsNotNone(v.check("toolong"))

    def test_no_bounds_accepts_anything(self):
        v = LengthValidator()
        self.assertIsNone(v.check("a" * 1000))

    def test_no_len_rejected(self):
        v = LengthValidator(min_length=1)
        self.assertIsNotNone(v.check(42))


# ===========================================================================
# PatternValidator
# ===========================================================================


class TestPatternValidator(unittest.TestCase):
    def test_valid_match(self):
        v = PatternValidator(r"\d{3}-\d{4}")
        self.assertIsNone(v.check("555-1234"))

    def test_invalid_match(self):
        v = PatternValidator(r"\d{3}-\d{4}")
        self.assertIsNotNone(v.check("abc-1234"))

    def test_partial_match_with_search(self):
        v = PatternValidator(r"\d+", full_match=False)
        self.assertIsNone(v.check("abc123"))

    def test_custom_error_message(self):
        v = PatternValidator(r"\d+", message="digits only")
        self.assertEqual("digits only", v.check("abc"))


# ===========================================================================
# CustomValidator
# ===========================================================================


class TestCustomValidator(unittest.TestCase):
    def test_accepts_valid(self):
        v = CustomValidator(lambda x: None if x > 0 else "must be positive")
        self.assertIsNone(v.check(5))

    def test_rejects_invalid(self):
        v = CustomValidator(lambda x: None if x > 0 else "must be positive")
        self.assertEqual("must be positive", v.check(-1))

    def test_noncallable_raises(self):
        with self.assertRaises(TypeError):
            CustomValidator("not callable")


# ===========================================================================
# DependentValidator
# ===========================================================================


class TestDependentValidator(unittest.TestCase):
    def test_check_passes_context(self):
        v = DependentValidator(lambda value, ctx: None if ctx.get("ok") else "fail")
        self.assertIsNone(v.check_with_context("x", {"ok": True}))
        self.assertEqual("fail", v.check_with_context("x", {}))


# ===========================================================================
# ValidationPipeline
# ===========================================================================


class TestValidationPipeline(unittest.TestCase):
    def test_all_pass(self):
        p = ValidationPipeline([RequiredValidator(), RangeValidator(0, 100)])
        result = p.validate(50)
        self.assertTrue(result.ok)

    def test_stops_on_first_error(self):
        p = ValidationPipeline([
            RequiredValidator("req"),
            RangeValidator(0, 10, message="range"),
        ])
        result = p.validate(None)
        self.assertFalse(result.ok)
        self.assertEqual(["req"], result.errors)

    def test_collect_all_errors(self):
        p = ValidationPipeline([
            RequiredValidator("req"),
            LengthValidator(max_length=3, message="too long"),
        ], stop_on_first_error=False)
        result = p.validate(None)
        # None fails RequiredValidator; then LengthValidator raises on len(None)
        self.assertFalse(result.ok)
        self.assertGreaterEqual(len(result.errors), 1)

    def test_add_validator_fluent(self):
        p = ValidationPipeline()
        p.add(RequiredValidator()).add(LengthValidator(min_length=3))
        self.assertEqual(2, len(p.validators))

    def test_is_valid_true(self):
        p = ValidationPipeline([RequiredValidator()])
        self.assertTrue(p.is_valid("hello"))

    def test_is_valid_false(self):
        p = ValidationPipeline([RequiredValidator()])
        self.assertFalse(p.is_valid(""))

    def test_empty_pipeline_passes_anything(self):
        p = ValidationPipeline()
        self.assertTrue(p.validate(None).ok)


if __name__ == "__main__":
    unittest.main()
