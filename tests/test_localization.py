"""Tests for StringTable and LocaleRegistry from text.localization."""
import unittest

from gui_do.text.localization import StringTable, LocaleRegistry


# ===========================================================================
# StringTable
# ===========================================================================


class TestStringTableInitial(unittest.TestCase):
    def test_locale_id_stored(self):
        t = StringTable("en", {"a": "alpha"})
        self.assertEqual("en", t.locale_id)

    def test_empty_locale_raises(self):
        with self.assertRaises(ValueError):
            StringTable("", {})

    def test_non_dict_entries_raises(self):
        with self.assertRaises(TypeError):
            StringTable("en", "not a dict")  # type: ignore[arg-type]

    def test_len(self):
        t = StringTable("en", {"a": "alpha", "b": "beta"})
        self.assertEqual(2, len(t))


class TestStringTableGet(unittest.TestCase):
    def test_get_existing(self):
        t = StringTable("en", {"a.title": "Hello"})
        self.assertEqual("Hello", t.get("a.title"))

    def test_get_missing_returns_fallback(self):
        t = StringTable("en", {})
        self.assertEqual("", t.get("missing"))

    def test_get_custom_fallback(self):
        t = StringTable("en", {})
        self.assertEqual("N/A", t.get("missing", "N/A"))

    def test_has_existing(self):
        t = StringTable("en", {"x": "y"})
        self.assertTrue(t.has("x"))

    def test_has_missing(self):
        t = StringTable("en", {"x": "y"})
        self.assertFalse(t.has("not.there"))

    def test_keys_sorted(self):
        t = StringTable("en", {"b": "2", "a": "1", "c": "3"})
        self.assertEqual(["a", "b", "c"], t.keys())


# ===========================================================================
# LocaleRegistry
# ===========================================================================


class TestLocaleRegistryInitial(unittest.TestCase):
    def test_default_locale(self):
        r = LocaleRegistry(default_locale="en")
        self.assertEqual("en", r.active_locale)

    def test_registered_locales_empty(self):
        r = LocaleRegistry()
        self.assertEqual([], r.registered_locales)


class TestLocaleRegistryRegister(unittest.TestCase):
    def test_register_adds_locale(self):
        r = LocaleRegistry()
        r.register(StringTable("en", {}))
        self.assertIn("en", r.registered_locales)

    def test_register_non_table_raises(self):
        r = LocaleRegistry()
        with self.assertRaises(TypeError):
            r.register("not a table")  # type: ignore[arg-type]

    def test_register_replaces_existing(self):
        r = LocaleRegistry("en")
        r.register(StringTable("en", {"key": "old"}))
        r.register(StringTable("en", {"key": "new"}))
        self.assertEqual("new", r.t("key"))


class TestLocaleRegistrySetLocale(unittest.TestCase):
    def test_set_locale_changes_active(self):
        r = LocaleRegistry("en")
        r.register(StringTable("es", {"a": "uno"}))
        r.set_locale("es")
        self.assertEqual("es", r.active_locale)

    def test_set_locale_notifies_subscribers(self):
        r = LocaleRegistry("en")
        changes = []
        r.current_locale.subscribe(lambda v: changes.append(v))
        r.set_locale("fr")
        self.assertIn("fr", changes)


class TestLocaleRegistryT(unittest.TestCase):
    def test_lookup_existing(self):
        r = LocaleRegistry("en")
        r.register(StringTable("en", {"greeting": "Hello"}))
        self.assertEqual("Hello", r.t("greeting"))

    def test_lookup_missing_returns_fallback(self):
        r = LocaleRegistry("en")
        r.register(StringTable("en", {}))
        self.assertEqual("?", r.t("missing", fallback="?"))

    def test_lookup_falls_back_to_fallback_locale(self):
        r = LocaleRegistry("es", fallback_locale="en")
        r.register(StringTable("en", {"key": "English"}))
        r.register(StringTable("es", {}))
        # "es" table doesn't have "key" so should fall back to "en"
        self.assertEqual("English", r.t("key"))

    def test_lookup_explicit_locale_override(self):
        r = LocaleRegistry("en")
        r.register(StringTable("en", {"key": "English"}))
        r.register(StringTable("fr", {"key": "Français"}))
        self.assertEqual("Français", r.t("key", locale="fr"))

    def test_registered_locales_sorted(self):
        r = LocaleRegistry()
        r.register(StringTable("fr", {}))
        r.register(StringTable("de", {}))
        r.register(StringTable("en", {}))
        self.assertEqual(["de", "en", "fr"], r.registered_locales)


if __name__ == "__main__":
    unittest.main()
