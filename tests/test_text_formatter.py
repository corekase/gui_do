"""Tests for NumericFormatter and PatternFormatter from text.text_formatter."""
import unittest

from gui_do.text.text_formatter import NumericFormatter, PatternFormatter


# ===========================================================================
# NumericFormatter
# ===========================================================================


class TestNumericFormatterDefaults(unittest.TestCase):
    def test_format_integer(self):
        f = NumericFormatter(decimals=0)
        self.assertEqual("42", f.format("42"))

    def test_format_float(self):
        f = NumericFormatter(decimals=2)
        self.assertEqual("3.14", f.format("3.14"))

    def test_format_invalid_returns_raw(self):
        f = NumericFormatter(decimals=0)
        self.assertEqual("abc", f.format("abc"))

    def test_format_thousands_sep(self):
        f = NumericFormatter(decimals=0, thousands_sep=",")
        result = f.format("1000000")
        self.assertIn(",", result)
        self.assertEqual("1,000,000", result)

    def test_parse_removes_sep(self):
        f = NumericFormatter(decimals=0, thousands_sep=",")
        self.assertEqual("1000", f.parse("1,000"))

    def test_parse_float(self):
        f = NumericFormatter(decimals=2)
        self.assertEqual("3.14", f.parse("3.14"))

    def test_validate_valid(self):
        f = NumericFormatter(decimals=0)
        self.assertTrue(f.validate("42"))

    def test_validate_invalid_text(self):
        f = NumericFormatter(decimals=0)
        self.assertFalse(f.validate("abc"))

    def test_validate_min_bound(self):
        f = NumericFormatter(decimals=0, min_value=10.0)
        self.assertFalse(f.validate("5"))
        self.assertTrue(f.validate("10"))

    def test_validate_max_bound(self):
        f = NumericFormatter(decimals=0, max_value=100.0)
        self.assertFalse(f.validate("200"))
        self.assertTrue(f.validate("50"))

    def test_adjust_cursor(self):
        f = NumericFormatter(decimals=0)
        result = f.adjust_cursor("12", cursor=2, inserted="3")
        self.assertEqual(3, result)


# ===========================================================================
# PatternFormatter
# ===========================================================================


class TestPatternFormatterInitial(unittest.TestCase):
    def test_mask_stored(self):
        f = PatternFormatter("(###) ###-####")
        self.assertEqual("(###) ###-####", f.mask)

    def test_slot_count(self):
        f = PatternFormatter("(###) ###-####")
        self.assertEqual(10, f.slot_count)

    def test_slot_count_simple(self):
        f = PatternFormatter("##-##")
        self.assertEqual(4, f.slot_count)


class TestPatternFormatterFormat(unittest.TestCase):
    def test_format_full_digits(self):
        f = PatternFormatter("(###) ###-####")
        result = f.format("1234567890")
        self.assertEqual("(123) 456-7890", result)

    def test_format_partial_pads_with_fill(self):
        f = PatternFormatter("###", fill_char="_")
        result = f.format("1")
        self.assertEqual("1__", result)

    def test_format_empty_all_fill(self):
        f = PatternFormatter("##", fill_char="?")
        result = f.format("")
        self.assertEqual("??", result)

    def test_parse_extracts_digits(self):
        f = PatternFormatter("(###) ###-####")
        result = f.parse("(123) 456-7890")
        self.assertEqual("1234567890", result)

    def test_parse_empty(self):
        f = PatternFormatter("###")
        self.assertEqual("", f.parse("___"))


class TestPatternFormatterValidate(unittest.TestCase):
    def test_validate_full(self):
        f = PatternFormatter("###")
        self.assertTrue(f.validate("123"))

    def test_validate_partial_returns_false(self):
        f = PatternFormatter("###")
        self.assertFalse(f.validate("12"))

    def test_validate_empty_returns_false(self):
        f = PatternFormatter("###")
        self.assertFalse(f.validate(""))

    def test_validate_more_digits_allowed(self):
        f = PatternFormatter("###")
        self.assertTrue(f.validate("1234"))


class TestPatternFormatterFormatPartial(unittest.TestCase):
    def test_format_partial_one_digit(self):
        f = PatternFormatter("(###) ###")
        result = f.format_partial("1")
        self.assertEqual("1", result)

    def test_format_partial_empty_returns_empty(self):
        f = PatternFormatter("(###) ###")
        result = f.format_partial("")
        self.assertEqual("", result)


if __name__ == "__main__":
    unittest.main()
