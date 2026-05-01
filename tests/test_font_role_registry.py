"""Tests for FontRoleDef and FontRoleRegistry."""
import unittest

from gui_do.theme.font_role_registry import FontRoleDef, FontRoleRegistry


# ===========================================================================
# FontRoleDef
# ===========================================================================


class TestFontRoleDef(unittest.TestCase):
    def test_fields_stored(self):
        d = FontRoleDef(role_name="body", size=16)
        self.assertEqual("body", d.role_name)
        self.assertEqual(16, d.size)

    def test_defaults(self):
        d = FontRoleDef(role_name="x", size=12)
        self.assertIsNone(d.file_path)
        self.assertIsNone(d.system_name)
        self.assertFalse(d.bold)
        self.assertFalse(d.italic)

    def test_frozen(self):
        d = FontRoleDef(role_name="x", size=12)
        with self.assertRaises(Exception):
            d.size = 99


# ===========================================================================
# FontRoleRegistry — initial state
# ===========================================================================


class TestFontRoleRegistryInitial(unittest.TestCase):
    def test_empty_initially(self):
        r = FontRoleRegistry()
        self.assertEqual(0, len(r))

    def test_defined_names_empty(self):
        r = FontRoleRegistry()
        self.assertEqual((), r.defined_names())

    def test_has_role_false(self):
        r = FontRoleRegistry()
        self.assertFalse(r.has_role("body"))

    def test_not_contains(self):
        r = FontRoleRegistry()
        self.assertNotIn("title", r)


# ===========================================================================
# FontRoleRegistry — define
# ===========================================================================


class TestFontRoleRegistryDefine(unittest.TestCase):
    def test_define_adds_role(self):
        r = FontRoleRegistry()
        r.define("body", size=16)
        self.assertEqual(1, len(r))

    def test_has_role_after_define(self):
        r = FontRoleRegistry()
        r.define("body", size=16)
        self.assertTrue(r.has_role("body"))

    def test_contains_after_define(self):
        r = FontRoleRegistry()
        r.define("title", size=14)
        self.assertIn("title", r)

    def test_define_returns_self(self):
        r = FontRoleRegistry()
        result = r.define("body", size=16)
        self.assertIs(r, result)

    def test_define_chaining(self):
        r = FontRoleRegistry()
        r.define("body", size=16).define("title", size=14)
        self.assertEqual(2, len(r))

    def test_defined_names_order(self):
        r = FontRoleRegistry()
        r.define("body", size=16).define("title", size=14).define("caption", size=11)
        self.assertEqual(("body", "title", "caption"), r.defined_names())

    def test_empty_name_raises(self):
        r = FontRoleRegistry()
        with self.assertRaises(ValueError):
            r.define("", size=16)

    def test_whitespace_name_raises(self):
        r = FontRoleRegistry()
        with self.assertRaises(ValueError):
            r.define("   ", size=16)

    def test_redefine_replaces_no_duplicate_in_order(self):
        r = FontRoleRegistry()
        r.define("body", size=16)
        r.define("body", size=20)
        self.assertEqual(1, len(r))
        self.assertEqual(("body",), r.defined_names())


# ===========================================================================
# FontRoleRegistry — lookup
# ===========================================================================


class TestFontRoleRegistryLookup(unittest.TestCase):
    def test_role_returns_name(self):
        r = FontRoleRegistry()
        r.define("body", size=16)
        self.assertEqual("body", r.role("body"))

    def test_role_unknown_raises(self):
        r = FontRoleRegistry()
        with self.assertRaises(KeyError):
            r.role("nonexistent")

    def test_getitem(self):
        r = FontRoleRegistry()
        r.define("title", size=14)
        self.assertEqual("title", r["title"])

    def test_getitem_unknown_raises(self):
        r = FontRoleRegistry()
        with self.assertRaises(KeyError):
            _ = r["nonexistent"]

    def test_font_instance_raises(self):
        r = FontRoleRegistry()
        with self.assertRaises(NotImplementedError):
            r.font_instance("body")


if __name__ == "__main__":
    unittest.main()
