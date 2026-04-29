"""Tests for TextSearcher and TextMatch."""
import unittest

from gui_do.text.text_searcher import TextSearcher, TextMatch


class TestTextMatchDataclass(unittest.TestCase):
    def test_fields_stored(self) -> None:
        m = TextMatch(start=0, end=5, text="Hello")
        self.assertEqual(m.start, 0)
        self.assertEqual(m.end, 5)
        self.assertEqual(m.text, "Hello")

    def test_frozen_raises_on_assignment(self) -> None:
        m = TextMatch(0, 5, "Hello")
        with self.assertRaises((AttributeError, TypeError)):
            m.start = 1  # type: ignore[misc]


class TestFindAllCaseInsensitive(unittest.TestCase):
    def test_finds_both_occurrences(self) -> None:
        s = TextSearcher("Hello World hello", case_sensitive=False)
        matches = s.find_all("hello")
        self.assertEqual(len(matches), 2)
        self.assertEqual(matches[0].start, 0)
        self.assertEqual(matches[1].start, 12)

    def test_returns_empty_when_no_match(self) -> None:
        s = TextSearcher("foo bar", case_sensitive=False)
        self.assertEqual(s.find_all("xyz"), [])


class TestFindAllCaseSensitive(unittest.TestCase):
    def test_finds_exact_case_only(self) -> None:
        s = TextSearcher("Hello hello HELLO", case_sensitive=True)
        matches = s.find_all("hello")
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].start, 6)


class TestFindNext(unittest.TestCase):
    def test_finds_from_pos_zero(self) -> None:
        s = TextSearcher("abc abc", case_sensitive=False)
        m = s.find_next("abc", from_pos=0)
        self.assertIsNotNone(m)
        self.assertEqual(m.start, 0)

    def test_finds_next_after_first(self) -> None:
        s = TextSearcher("abc abc", case_sensitive=False)
        m = s.find_next("abc", from_pos=1)
        self.assertIsNotNone(m)
        self.assertEqual(m.start, 4)

    def test_returns_none_when_no_more(self) -> None:
        s = TextSearcher("abc", case_sensitive=False)
        self.assertIsNone(s.find_next("abc", from_pos=3))


class TestFindPrev(unittest.TestCase):
    def test_finds_previous_occurrence(self) -> None:
        # "abc abc abc": positions 0-2, 4-6, 8-10
        # find_prev returns last match whose end <= from_pos
        # from_pos=8: last abc ending at 7 (start=4) qualifies; abc at 8 ends at 11 > 8
        s = TextSearcher("abc abc abc", case_sensitive=False)
        m = s.find_prev("abc", from_pos=8)
        self.assertIsNotNone(m)
        self.assertEqual(m.start, 4)

    def test_returns_none_before_beginning(self) -> None:
        s = TextSearcher("abc", case_sensitive=False)
        self.assertIsNone(s.find_prev("abc", from_pos=0))


class TestWholeWord(unittest.TestCase):
    def test_whole_word_excludes_substrings(self) -> None:
        s = TextSearcher("foobar foo barfoo", whole_word=True)
        matches = s.find_all("foo")
        # Only standalone 'foo' at index 7
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].start, 7)


class TestRegexMode(unittest.TestCase):
    def test_regex_pattern_matches(self) -> None:
        s = TextSearcher("abc 123 def 456", use_regex=True)
        matches = s.find_all(r"\d+")
        self.assertEqual(len(matches), 2)
        self.assertEqual(matches[0].text, "123")
        self.assertEqual(matches[1].text, "456")

    def test_invalid_regex_returns_empty(self) -> None:
        s = TextSearcher("abc", use_regex=True)
        # Implementation catches re.error and returns empty list
        result = s.find_all("[invalid")
        self.assertEqual(result, [])


class TestReplace(unittest.TestCase):
    def test_replace_returns_new_string(self) -> None:
        s = TextSearcher("Hello World", case_sensitive=False)
        m = s.find_next("World", from_pos=0)
        result = s.replace(m, "Python")
        self.assertEqual(result, "Hello Python")

    def test_replace_all(self) -> None:
        s = TextSearcher("foo foo foo", case_sensitive=False)
        result = s.replace_all("foo", "bar")
        self.assertEqual(result, "bar bar bar")


class TestTextPropertySettable(unittest.TestCase):
    def test_update_text_changes_search_target(self) -> None:
        s = TextSearcher("alpha beta")
        matches = s.find_all("gamma")
        self.assertEqual(matches, [])
        s.text = "gamma delta"
        matches = s.find_all("gamma")
        self.assertEqual(len(matches), 1)


class TestHighlightSpans(unittest.TestCase):
    def test_returns_one_span_per_match(self) -> None:
        s = TextSearcher("hello world hello")
        matches = s.find_all("hello")
        spans = s.highlight_spans(matches, style="highlight")
        self.assertEqual(len(spans), 2)
        self.assertTrue(all("start" in sp for sp in spans))
