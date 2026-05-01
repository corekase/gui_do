"""Tests for TextMatch and TextSearcher from text.text_searcher."""
import unittest

from gui_do.text.text_searcher import TextMatch, TextSearcher


# ===========================================================================
# TextMatch dataclass
# ===========================================================================


class TestTextMatch(unittest.TestCase):
    def test_fields_stored(self):
        m = TextMatch(start=5, end=10, text="hello")
        self.assertEqual(5, m.start)
        self.assertEqual(10, m.end)
        self.assertEqual("hello", m.text)

    def test_is_frozen(self):
        m = TextMatch(start=0, end=5, text="hi")
        with self.assertRaises(Exception):
            m.start = 1  # type: ignore[misc]


# ===========================================================================
# TextSearcher — initial state
# ===========================================================================


class TestTextSearcherInitial(unittest.TestCase):
    def test_text_stored(self):
        s = TextSearcher("hello world")
        self.assertEqual("hello world", s.text)

    def test_case_sensitive_default_false(self):
        s = TextSearcher("text")
        self.assertFalse(s.case_sensitive)

    def test_whole_word_default_false(self):
        s = TextSearcher("text")
        self.assertFalse(s.whole_word)

    def test_use_regex_default_false(self):
        s = TextSearcher("text")
        self.assertFalse(s.use_regex)

    def test_text_settable(self):
        s = TextSearcher("old")
        s.text = "new text"
        self.assertEqual("new text", s.text)


# ===========================================================================
# TextSearcher.find_all
# ===========================================================================


class TestTextSearcherFindAll(unittest.TestCase):
    def test_find_all_case_insensitive(self):
        s = TextSearcher("Hello world hello", case_sensitive=False)
        matches = s.find_all("hello")
        self.assertEqual(2, len(matches))

    def test_find_all_case_sensitive(self):
        s = TextSearcher("Hello world hello", case_sensitive=True)
        matches = s.find_all("hello")
        self.assertEqual(1, len(matches))
        self.assertEqual("hello", matches[0].text)

    def test_find_all_returns_correct_spans(self):
        s = TextSearcher("abcabc")
        matches = s.find_all("abc")
        self.assertEqual(0, matches[0].start)
        self.assertEqual(3, matches[0].end)
        self.assertEqual(3, matches[1].start)

    def test_find_all_empty_query_returns_empty(self):
        s = TextSearcher("hello")
        self.assertEqual([], s.find_all(""))

    def test_find_all_no_match_returns_empty(self):
        s = TextSearcher("hello")
        self.assertEqual([], s.find_all("xyz"))

    def test_find_all_whole_word(self):
        s = TextSearcher("cat catfish", whole_word=True)
        matches = s.find_all("cat")
        self.assertEqual(1, len(matches))
        self.assertEqual("cat", matches[0].text)

    def test_find_all_regex(self):
        s = TextSearcher("a1b2c3", use_regex=True)
        matches = s.find_all(r"\d")
        self.assertEqual(3, len(matches))


# ===========================================================================
# TextSearcher.find_next / find_prev
# ===========================================================================


class TestTextSearcherFindNext(unittest.TestCase):
    def test_find_next_from_zero(self):
        s = TextSearcher("hello hello")
        m = s.find_next("hello")
        self.assertIsNotNone(m)
        self.assertEqual(0, m.start)

    def test_find_next_with_offset(self):
        s = TextSearcher("hello hello")
        m = s.find_next("hello", from_pos=1)
        self.assertIsNotNone(m)
        self.assertEqual(6, m.start)

    def test_find_next_no_match_returns_none(self):
        s = TextSearcher("hello")
        self.assertIsNone(s.find_next("xyz"))

    def test_find_next_empty_query_returns_none(self):
        s = TextSearcher("hello")
        self.assertIsNone(s.find_next(""))


class TestTextSearcherFindPrev(unittest.TestCase):
    def test_find_prev_returns_last_before_pos(self):
        s = TextSearcher("hello hello hello")
        m = s.find_prev("hello", from_pos=12)
        self.assertIsNotNone(m)
        self.assertEqual(6, m.start)

    def test_find_prev_no_match_returns_none(self):
        s = TextSearcher("hello")
        self.assertIsNone(s.find_prev("xyz", from_pos=10))


# ===========================================================================
# TextSearcher.replace / replace_all
# ===========================================================================


class TestTextSearcherReplace(unittest.TestCase):
    def test_replace_single(self):
        s = TextSearcher("hello world")
        m = s.find_next("hello")
        result = s.replace(m, "hi")
        self.assertEqual("hi world", result)

    def test_replace_does_not_modify_text(self):
        s = TextSearcher("hello world")
        m = s.find_next("hello")
        s.replace(m, "hi")
        self.assertEqual("hello world", s.text)

    def test_replace_all_replaces_all(self):
        s = TextSearcher("hello hello hello", case_sensitive=False)
        result = s.replace_all("hello", "hi")
        self.assertEqual("hi hi hi", result)

    def test_replace_all_empty_query_returns_original(self):
        s = TextSearcher("hello")
        result = s.replace_all("", "x")
        self.assertEqual("hello", result)


if __name__ == "__main__":
    unittest.main()
