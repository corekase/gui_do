"""Tests for StringTable, LocaleRegistry, TextMatch, and TextSearcher."""
import unittest

from gui_do.text.localization import LocaleRegistry, StringTable
from gui_do.text.text_searcher import TextMatch, TextSearcher


# ===========================================================================
# StringTable
# ===========================================================================


class TestStringTable(unittest.TestCase):
    def test_locale_id_stored(self):
        t = StringTable("en", {"key": "value"})
        self.assertEqual("en", t.locale_id)

    def test_get_returns_value(self):
        t = StringTable("en", {"a.b": "Hello"})
        self.assertEqual("Hello", t.get("a.b"))

    def test_get_missing_returns_fallback(self):
        t = StringTable("en", {})
        self.assertEqual("default", t.get("nope", "default"))

    def test_has_true(self):
        t = StringTable("en", {"x": "y"})
        self.assertTrue(t.has("x"))

    def test_has_false(self):
        t = StringTable("en", {})
        self.assertFalse(t.has("nope"))

    def test_keys_sorted(self):
        t = StringTable("en", {"b": "B", "a": "A"})
        self.assertEqual(["a", "b"], t.keys())

    def test_len(self):
        t = StringTable("en", {"a": "1", "b": "2"})
        self.assertEqual(2, len(t))

    def test_empty_locale_id_raises(self):
        with self.assertRaises(ValueError):
            StringTable("", {"a": "b"})

    def test_non_dict_entries_raises(self):
        with self.assertRaises(TypeError):
            StringTable("en", "not_a_dict")


# ===========================================================================
# LocaleRegistry — initial state
# ===========================================================================


class TestLocaleRegistryInitial(unittest.TestCase):
    def test_default_locale(self):
        r = LocaleRegistry(default_locale="fr")
        self.assertEqual("fr", r.active_locale)

    def test_no_registered_locales(self):
        r = LocaleRegistry()
        self.assertEqual([], r.registered_locales)

    def test_t_returns_fallback_when_unregistered(self):
        r = LocaleRegistry()
        self.assertEqual("default", r.t("any.key", fallback="default"))


# ===========================================================================
# LocaleRegistry — register / set_locale
# ===========================================================================


class TestLocaleRegistryRegister(unittest.TestCase):
    def setUp(self):
        self.r = LocaleRegistry(default_locale="en")
        self.r.register(StringTable("en", {
            "app.title": "My App",
            "btn.ok": "OK",
        }))
        self.r.register(StringTable("es", {
            "app.title": "Mi App",
        }))

    def test_registered_locales_sorted(self):
        self.assertEqual(["en", "es"], self.r.registered_locales)

    def test_t_returns_active_locale_string(self):
        self.assertEqual("My App", self.r.t("app.title"))

    def test_t_missing_key_returns_fallback(self):
        self.assertEqual("", self.r.t("nope"))

    def test_t_custom_fallback(self):
        self.assertEqual("N/A", self.r.t("nope", fallback="N/A"))

    def test_set_locale_switches(self):
        self.r.set_locale("es")
        self.assertEqual("Mi App", self.r.t("app.title"))

    def test_t_with_explicit_locale(self):
        self.assertEqual("Mi App", self.r.t("app.title", locale="es"))

    def test_has_returns_true(self):
        self.assertTrue(self.r.has("btn.ok"))

    def test_has_returns_false_for_missing(self):
        self.assertFalse(self.r.has("missing_key"))


# ===========================================================================
# LocaleRegistry — fallback locale
# ===========================================================================


class TestLocaleRegistryFallback(unittest.TestCase):
    def test_falls_back_to_fallback_locale(self):
        r = LocaleRegistry(default_locale="es", fallback_locale="en")
        r.register(StringTable("en", {"shared.key": "English"}))
        r.register(StringTable("es", {}))
        # "es" doesn't have "shared.key" — should fall back to "en"
        self.assertEqual("English", r.t("shared.key"))

    def test_non_string_table_raises(self):
        r = LocaleRegistry()
        with self.assertRaises(TypeError):
            r.register("not_a_table")


# ===========================================================================
# TextMatch
# ===========================================================================


class TestTextMatch(unittest.TestCase):
    def test_fields_stored(self):
        m = TextMatch(start=0, end=5, text="hello")
        self.assertEqual(0, m.start)
        self.assertEqual(5, m.end)
        self.assertEqual("hello", m.text)

    def test_frozen(self):
        m = TextMatch(start=0, end=5, text="hello")
        with self.assertRaises((AttributeError, TypeError)):
            m.start = 1


# ===========================================================================
# TextSearcher
# ===========================================================================


class TestTextSearcher(unittest.TestCase):
    def test_find_all_case_insensitive(self):
        s = TextSearcher("Hello World hello", case_sensitive=False)
        matches = s.find_all("hello")
        self.assertEqual(2, len(matches))

    def test_find_all_case_sensitive(self):
        s = TextSearcher("Hello World hello", case_sensitive=True)
        matches = s.find_all("hello")
        self.assertEqual(1, len(matches))

    def test_find_all_no_match(self):
        s = TextSearcher("Hello World")
        matches = s.find_all("xyz")
        self.assertEqual([], matches)

    def test_find_all_returns_text_match(self):
        s = TextSearcher("abcabc")
        matches = s.find_all("abc")
        self.assertIsInstance(matches[0], TextMatch)
        self.assertEqual("abc", matches[0].text)

    def test_find_next_from_pos(self):
        s = TextSearcher("hello world hello")
        m = s.find_next("hello", from_pos=1)
        self.assertIsNotNone(m)
        self.assertGreater(m.start, 0)

    def test_replace_all(self):
        s = TextSearcher("cat and cat")
        new_text = s.replace_all("cat", "dog")
        self.assertEqual("dog and dog", new_text)

    def test_whole_word_match(self):
        s = TextSearcher("cat concatenate cat", whole_word=True)
        matches = s.find_all("cat")
        # "concatenate" should NOT match; only standalone "cat"
        self.assertEqual(2, len(matches))

    def test_regex_mode(self):
        s = TextSearcher("abc123def456", use_regex=True)
        matches = s.find_all(r"\d+")
        self.assertEqual(2, len(matches))

    def test_update_text(self):
        s = TextSearcher("hello world")
        s.text = "goodbye world"
        matches = s.find_all("hello")
        self.assertEqual([], matches)


if __name__ == "__main__":
    unittest.main()
