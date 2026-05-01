"""Tests for NumericFormatter and PatternFormatter."""
import unittest

from gui_do.text.text_formatter import NumericFormatter, PatternFormatter


# ===========================================================================
# NumericFormatter
# ===========================================================================


class TestNumericFormatterFormat(unittest.TestCase):
    def test_integer_format(self):
        fmt = NumericFormatter(decimals=0)
        self.assertEqual("42", fmt.format("42"))

    def test_float_format(self):
        fmt = NumericFormatter(decimals=2)
        self.assertEqual("3.14", fmt.format("3.14159"))

    def test_format_rounds(self):
        fmt = NumericFormatter(decimals=1)
        # Python banker's rounding: 3.15 -> 3.1 (rounds to even)
        self.assertEqual("3.1", fmt.format("3.15"))

    def test_thousands_separator(self):
        fmt = NumericFormatter(decimals=0, thousands_sep=",")
        self.assertEqual("1,234", fmt.format("1234"))

    def test_thousands_large(self):
        fmt = NumericFormatter(decimals=0, thousands_sep=",")
        self.assertEqual("1,234,567", fmt.format("1234567"))

    def test_invalid_returns_raw(self):
        fmt = NumericFormatter(decimals=0)
        self.assertEqual("abc", fmt.format("abc"))

    def test_negative_integer(self):
        fmt = NumericFormatter(decimals=0)
        self.assertEqual("-5", fmt.format("-5"))


class TestNumericFormatterParse(unittest.TestCase):
    def test_parse_integer(self):
        fmt = NumericFormatter(decimals=0)
        self.assertEqual("10", fmt.parse("10"))

    def test_parse_strips_thousands_sep(self):
        fmt = NumericFormatter(decimals=0, thousands_sep=",")
        self.assertEqual("1234", fmt.parse("1,234"))

    def test_parse_float(self):
        fmt = NumericFormatter(decimals=2)
        self.assertEqual("3.14", fmt.parse("3.14"))

    def test_parse_invalid_returns_raw(self):
        fmt = NumericFormatter(decimals=0)
        self.assertEqual("xyz", fmt.parse("xyz"))


class TestNumericFormatterValidate(unittest.TestCase):
    def test_valid_integer(self):
        fmt = NumericFormatter(decimals=0)
        self.assertTrue(fmt.validate("42"))

    def test_invalid_text(self):
        fmt = NumericFormatter(decimals=0)
        self.assertFalse(fmt.validate("abc"))

    def test_below_min(self):
        fmt = NumericFormatter(decimals=0, min_value=0.0)
        self.assertFalse(fmt.validate("-1"))

    def test_above_max(self):
        fmt = NumericFormatter(decimals=0, max_value=100.0)
        self.assertFalse(fmt.validate("101"))

    def test_at_min_boundary(self):
        fmt = NumericFormatter(decimals=0, min_value=5.0)
        self.assertTrue(fmt.validate("5"))

    def test_at_max_boundary(self):
        fmt = NumericFormatter(decimals=0, max_value=10.0)
        self.assertTrue(fmt.validate("10"))

    def test_no_bounds(self):
        fmt = NumericFormatter(decimals=0)
        self.assertTrue(fmt.validate("-999999"))


class TestNumericFormatterAdjustCursor(unittest.TestCase):
    def test_cursor_moves_forward(self):
        fmt = NumericFormatter(decimals=0)
        result = fmt.adjust_cursor("123", cursor=2, inserted="4")
        self.assertEqual(3, result)

    def test_cursor_clamped(self):
        fmt = NumericFormatter(decimals=0)
        # cursor=0, inserted="2" -> 0 + len("2") = 1, capped at len("1")+len("2")=2; result=1
        result = fmt.adjust_cursor("1", cursor=0, inserted="2")
        self.assertEqual(1, result)


# ===========================================================================
# PatternFormatter
# ===========================================================================


class TestPatternFormatterInitial(unittest.TestCase):
    def test_mask_stored(self):
        pf = PatternFormatter("###-####")
        self.assertEqual("###-####", pf.mask)

    def test_slot_count(self):
        pf = PatternFormatter("(###) ###-####")
        self.assertEqual(10, pf.slot_count)

    def test_slot_count_simple(self):
        pf = PatternFormatter("###")
        self.assertEqual(3, pf.slot_count)


class TestPatternFormatterFormat(unittest.TestCase):
    def test_format_full(self):
        pf = PatternFormatter("###-####")
        self.assertEqual("123-4567", pf.format("1234567"))

    def test_format_partial_fills_with_placeholder(self):
        pf = PatternFormatter("###-####")
        result = pf.format("12")
        self.assertEqual("12_-____", result)

    def test_format_phone_number(self):
        pf = PatternFormatter("(###) ###-####")
        self.assertEqual("(555) 867-5309", pf.format("5558675309"))

    def test_format_empty_all_placeholders(self):
        pf = PatternFormatter("###")
        self.assertEqual("___", pf.format(""))


class TestPatternFormatterParse(unittest.TestCase):
    def test_parse_extracts_digits(self):
        pf = PatternFormatter("###-####")
        self.assertEqual("1234567", pf.parse("123-4567"))

    def test_parse_phone(self):
        pf = PatternFormatter("(###) ###-####")
        self.assertEqual("5558675309", pf.parse("(555) 867-5309"))

    def test_parse_empty(self):
        pf = PatternFormatter("###")
        self.assertEqual("", pf.parse("___"))


class TestPatternFormatterValidate(unittest.TestCase):
    def test_validate_full(self):
        pf = PatternFormatter("###-####")
        self.assertTrue(pf.validate("1234567"))

    def test_validate_partial_false(self):
        pf = PatternFormatter("###-####")
        self.assertFalse(pf.validate("123"))

    def test_validate_exact_count(self):
        pf = PatternFormatter("###")
        self.assertTrue(pf.validate("456"))

    def test_validate_empty_false(self):
        pf = PatternFormatter("###")
        self.assertFalse(pf.validate(""))


class TestPatternFormatterFormatPartial(unittest.TestCase):
    def test_format_partial_empty(self):
        pf = PatternFormatter("(###) ###-####")
        self.assertEqual("", pf.format_partial(""))

    def test_format_partial_three_digits(self):
        pf = PatternFormatter("(###) ###-####")
        result = pf.format_partial("555")
        self.assertIn("555", result)

    def test_format_partial_includes_literals(self):
        pf = PatternFormatter("###-####")
        # "1234" should produce "123-4" with the literal dash
        result = pf.format_partial("1234")
        self.assertEqual("123-4", result)


if __name__ == "__main__":
    unittest.main()
