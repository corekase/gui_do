import json
import tempfile
import unittest
from pathlib import Path

from gui_do.text.text_searcher import TextMatch, TextSearcher
from gui_do.persistence.settings_registry import SettingsRegistry, SettingDescriptor


# ---------------------------------------------------------------------------
# TextSearcher
# ---------------------------------------------------------------------------


class TestTextSearcher(unittest.TestCase):
    def test_find_all_case_insensitive_default(self):
        s = TextSearcher("Hello hello HELLO")
        matches = s.find_all("hello")
        self.assertEqual(3, len(matches))

    def test_find_all_case_sensitive(self):
        s = TextSearcher("Hello hello HELLO", case_sensitive=True)
        matches = s.find_all("hello")
        self.assertEqual(1, len(matches))
        self.assertEqual("hello", matches[0].text)

    def test_find_all_empty_query_returns_empty(self):
        s = TextSearcher("some text")
        self.assertEqual([], s.find_all(""))

    def test_find_all_no_match_returns_empty(self):
        s = TextSearcher("abc")
        self.assertEqual([], s.find_all("xyz"))

    def test_find_all_match_positions(self):
        s = TextSearcher("abcabc")
        matches = s.find_all("abc")
        self.assertEqual([0, 3], [m.start for m in matches])
        self.assertEqual([3, 6], [m.end for m in matches])

    def test_find_all_whole_word(self):
        s = TextSearcher("cat catfish scat", whole_word=True)
        matches = s.find_all("cat")
        self.assertEqual(1, len(matches))
        self.assertEqual("cat", matches[0].text)

    def test_find_all_use_regex(self):
        s = TextSearcher("foo123bar456", use_regex=True)
        matches = s.find_all(r"\d+")
        self.assertEqual(2, len(matches))
        self.assertEqual("123", matches[0].text)
        self.assertEqual("456", matches[1].text)

    def test_find_all_invalid_regex_returns_empty(self):
        s = TextSearcher("text", use_regex=True)
        self.assertEqual([], s.find_all("[invalid"))

    def test_find_next_returns_first_match_from_pos(self):
        s = TextSearcher("aabbcc")
        m = s.find_next("bb", from_pos=0)
        self.assertIsNotNone(m)
        self.assertEqual(2, m.start)

    def test_find_next_skips_before_from_pos(self):
        s = TextSearcher("abcabc")
        m = s.find_next("abc", from_pos=1)
        self.assertIsNotNone(m)
        self.assertEqual(3, m.start)

    def test_find_next_returns_none_when_no_match(self):
        s = TextSearcher("abc")
        self.assertIsNone(s.find_next("xyz"))

    def test_find_next_empty_query_returns_none(self):
        s = TextSearcher("abc")
        self.assertIsNone(s.find_next(""))

    def test_find_prev_returns_last_match_before_pos(self):
        s = TextSearcher("abcabc")
        m = s.find_prev("abc", from_pos=5)
        self.assertIsNotNone(m)
        self.assertEqual(0, m.start)

    def test_find_prev_returns_none_when_no_match_before_pos(self):
        s = TextSearcher("abcabc")
        m = s.find_prev("abc", from_pos=0)
        self.assertIsNone(m)

    def test_replace_single_match(self):
        s = TextSearcher("Hello World")
        m = s.find_next("World")
        result = s.replace(m, "Python")
        self.assertEqual("Hello Python", result)

    def test_replace_does_not_mutate_text_attr(self):
        s = TextSearcher("Hello World")
        m = s.find_next("World")
        s.replace(m, "Python")
        self.assertEqual("Hello World", s.text)

    def test_replace_all_replaces_every_match(self):
        s = TextSearcher("cat Cat CAT")
        result = s.replace_all("cat", "dog")
        self.assertEqual("dog dog dog", result)

    def test_replace_all_empty_query_returns_original(self):
        s = TextSearcher("unchanged")
        self.assertEqual("unchanged", s.replace_all("", "x"))

    def test_replace_all_regex_mode(self):
        s = TextSearcher("a1b2c3", use_regex=True)
        result = s.replace_all(r"\d", "#")
        self.assertEqual("a#b#c#", result)

    def test_text_setter_changes_search_target(self):
        s = TextSearcher("old text")
        s.text = "new text"
        m = s.find_next("new")
        self.assertIsNotNone(m)

    def test_highlight_spans_returns_dicts(self):
        s = TextSearcher("ab ab")
        matches = s.find_all("ab")
        spans = s.highlight_spans(matches)
        self.assertEqual(2, len(spans))
        self.assertIn("start", spans[0])
        self.assertIn("end", spans[0])
        self.assertIn("style", spans[0])

    def test_highlight_spans_custom_style(self):
        s = TextSearcher("x")
        matches = s.find_all("x")
        spans = s.highlight_spans(matches, style={"color": "red"})
        self.assertEqual({"color": "red"}, spans[0]["style"])

    def test_text_match_is_frozen(self):
        m = TextMatch(0, 3, "abc")
        with self.assertRaises(Exception):
            m.start = 1  # type: ignore[misc]


# ---------------------------------------------------------------------------
# SettingsRegistry
# ---------------------------------------------------------------------------


class TestSettingsRegistry(unittest.TestCase):
    def test_declare_returns_observable_value(self):
        reg = SettingsRegistry()
        ov = reg.declare("audio", "volume", default=1.0)
        self.assertEqual(1.0, ov.value)

    def test_declare_twice_returns_same_observable(self):
        reg = SettingsRegistry()
        ov1 = reg.declare("audio", "volume", default=1.0)
        ov2 = reg.declare("audio", "volume", default=0.5)  # second call
        self.assertIs(ov1, ov2)
        self.assertEqual(1.0, ov1.value)  # original default preserved

    def test_get_returns_observable(self):
        reg = SettingsRegistry()
        reg.declare("ui", "theme", default="dark")
        ov = reg.get("ui", "theme")
        self.assertEqual("dark", ov.value)

    def test_get_raises_for_undeclared(self):
        reg = SettingsRegistry()
        with self.assertRaises(KeyError):
            reg.get("missing", "key")

    def test_get_value_returns_raw_value(self):
        reg = SettingsRegistry()
        reg.declare("ui", "scale", default=2)
        self.assertEqual(2, reg.get_value("ui", "scale"))

    def test_set_value_updates_and_fires_observer(self):
        reg = SettingsRegistry()
        ov = reg.declare("ui", "scale", default=1)
        received = []
        ov.subscribe(received.append)
        reg.set_value("ui", "scale", 3)
        self.assertEqual([3], received)
        self.assertEqual(3, reg.get_value("ui", "scale"))

    def test_reset_reverts_to_default(self):
        reg = SettingsRegistry()
        reg.declare("audio", "volume", default=1.0)
        reg.set_value("audio", "volume", 0.3)
        reg.reset("audio")
        self.assertEqual(1.0, reg.get_value("audio", "volume"))

    def test_reset_all_reverts_every_namespace(self):
        reg = SettingsRegistry()
        reg.declare("audio", "volume", default=1.0)
        reg.declare("ui", "scale", default=1)
        reg.set_value("audio", "volume", 0.0)
        reg.set_value("ui", "scale", 2)
        reg.reset_all()
        self.assertEqual(1.0, reg.get_value("audio", "volume"))
        self.assertEqual(1, reg.get_value("ui", "scale"))

    def test_namespaces_returns_sorted(self):
        reg = SettingsRegistry()
        reg.declare("z_ns", "k", default=0)
        reg.declare("a_ns", "k", default=0)
        self.assertEqual(["a_ns", "z_ns"], reg.namespaces())

    def test_keys_returns_sorted(self):
        reg = SettingsRegistry()
        reg.declare("ns", "z_key", default=0)
        reg.declare("ns", "a_key", default=0)
        self.assertEqual(["a_key", "z_key"], reg.keys("ns"))

    def test_describe_returns_descriptor(self):
        reg = SettingsRegistry()
        reg.declare("ui", "theme", default="dark", label="Theme")
        desc = reg.describe("ui", "theme")
        self.assertIsInstance(desc, SettingDescriptor)
        self.assertEqual("dark", desc.default)
        self.assertEqual("Theme", desc.label)

    def test_describe_unknown_returns_none(self):
        reg = SettingsRegistry()
        self.assertIsNone(reg.describe("no", "key"))

    def test_all_descriptors_ordered(self):
        reg = SettingsRegistry()
        reg.declare("b_ns", "key", default=0)
        reg.declare("a_ns", "key", default=0)
        descs = reg.all_descriptors()
        self.assertEqual("a_ns", descs[0].namespace)
        self.assertEqual("b_ns", descs[1].namespace)

    def test_declare_empty_namespace_raises(self):
        reg = SettingsRegistry()
        with self.assertRaises(ValueError):
            reg.declare("", "key", default=0)

    def test_declare_empty_key_raises(self):
        reg = SettingsRegistry()
        with self.assertRaises(ValueError):
            reg.declare("ns", "", default=0)

    def test_save_and_load_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "settings.json"
            reg = SettingsRegistry(path)
            reg.declare("audio", "volume", default=1.0)
            reg.set_value("audio", "volume", 0.42)
            self.assertTrue(reg.save())

            reg2 = SettingsRegistry(path)
            reg2.declare("audio", "volume", default=1.0)
            self.assertTrue(reg2.load())
            self.assertAlmostEqual(0.42, reg2.get_value("audio", "volume"))

    def test_save_without_file_path_returns_false(self):
        reg = SettingsRegistry()
        reg.declare("ns", "k", default=0)
        self.assertFalse(reg.save())

    def test_load_without_file_path_returns_false(self):
        reg = SettingsRegistry()
        self.assertFalse(reg.load())

    def test_load_ignores_unknown_keys(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "settings.json"
            path.write_text(json.dumps({"ns": {"unknown_key": 99}}), encoding="utf-8")
            reg = SettingsRegistry(path)
            reg.declare("ns", "declared", default=0)
            reg.load()  # should not raise
            self.assertEqual(0, reg.get_value("ns", "declared"))

    def test_set_file_path(self):
        reg = SettingsRegistry()
        reg.set_file_path("/tmp/x.json")
        self.assertIsNotNone(reg.file_path)


if __name__ == "__main__":
    unittest.main()
