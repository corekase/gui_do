"""Tests for ScopedTheme and ScopedThemeManager from theme.scoped_theme."""
import unittest

from gui_do.theme.scoped_theme import ScopedTheme, ScopedThemeManager


class _MockTokens:
    """Minimal DesignTokens mock."""
    def __init__(self, data):
        self._data = data

    def get(self, token, fallback):
        return self._data.get(token, fallback)


# ===========================================================================
# ScopedTheme — initial state
# ===========================================================================


class TestScopedThemeInitial(unittest.TestCase):
    def test_name_default(self):
        s = ScopedTheme()
        self.assertEqual("scoped", s.name)

    def test_custom_name(self):
        s = ScopedTheme(name="dark-panel")
        self.assertEqual("dark-panel", s.name)

    def test_parent_none_initial(self):
        s = ScopedTheme()
        self.assertIsNone(s.parent)

    def test_overrides_stored(self):
        s = ScopedTheme({"surface": (10, 20, 30)})
        self.assertEqual({"surface": (10, 20, 30)}, s.to_dict())


# ===========================================================================
# ScopedTheme.set / remove / resolve
# ===========================================================================


class TestScopedThemeSet(unittest.TestCase):
    def test_set_adds_token(self):
        s = ScopedTheme()
        s.set("primary", (100, 150, 200))
        self.assertEqual((100, 150, 200), s.resolve("primary"))

    def test_remove_token(self):
        s = ScopedTheme({"key": (1, 2, 3)})
        s.remove("key")
        self.assertIsNone(s.resolve("key"))

    def test_remove_missing_no_error(self):
        s = ScopedTheme()
        s.remove("nonexistent")  # should not raise

    def test_resolve_missing_returns_fallback(self):
        s = ScopedTheme()
        result = s.resolve("missing", fallback=(50, 60, 70))
        self.assertEqual((50, 60, 70), result)

    def test_resolve_climbs_parent_chain(self):
        parent = ScopedTheme({"surface": (10, 20, 30)})
        child = ScopedTheme()
        child._parent = parent
        # child doesn't have "surface", should find it in parent
        self.assertEqual((10, 20, 30), child.resolve("surface"))

    def test_to_dict_returns_copy(self):
        s = ScopedTheme({"a": (1, 2, 3)})
        d = s.to_dict()
        d["a"] = (0, 0, 0)
        self.assertEqual((1, 2, 3), s.resolve("a"))

    def test_copy(self):
        s = ScopedTheme({"a": (1, 2, 3)}, name="orig")
        c = s.copy(name="dupe")
        self.assertEqual("dupe", c.name)
        self.assertEqual({"a": (1, 2, 3)}, c.to_dict())


# ===========================================================================
# ScopedThemeManager
# ===========================================================================


class TestScopedThemeManagerInitial(unittest.TestCase):
    def test_active_scope_none(self):
        mgr = ScopedThemeManager(_MockTokens({}))
        self.assertIsNone(mgr.active_scope)

    def test_depth_zero(self):
        mgr = ScopedThemeManager(_MockTokens({}))
        self.assertEqual(0, mgr.depth)


class TestScopedThemeManagerPushPop(unittest.TestCase):
    def test_push_sets_active(self):
        mgr = ScopedThemeManager(_MockTokens({}))
        s = ScopedTheme(name="test")
        mgr.push(s)
        self.assertIs(s, mgr.active_scope)

    def test_push_increments_depth(self):
        mgr = ScopedThemeManager(_MockTokens({}))
        mgr.push(ScopedTheme())
        self.assertEqual(1, mgr.depth)

    def test_pop_returns_scope(self):
        mgr = ScopedThemeManager(_MockTokens({}))
        s = ScopedTheme()
        mgr.push(s)
        result = mgr.pop()
        self.assertIs(s, result)

    def test_pop_empty_returns_none(self):
        mgr = ScopedThemeManager(_MockTokens({}))
        self.assertIsNone(mgr.pop())

    def test_push_two_sets_parent(self):
        mgr = ScopedThemeManager(_MockTokens({}))
        outer = ScopedTheme(name="outer")
        inner = ScopedTheme(name="inner")
        mgr.push(outer)
        mgr.push(inner)
        self.assertIs(outer, inner.parent)


class TestScopedThemeManagerResolve(unittest.TestCase):
    def test_resolve_from_active_scope(self):
        base = _MockTokens({"surface": (50, 50, 50)})
        mgr = ScopedThemeManager(base)
        s = ScopedTheme({"surface": (10, 20, 30)})
        mgr.push(s)
        self.assertEqual((10, 20, 30), mgr.resolve("surface"))

    def test_resolve_falls_through_to_base(self):
        base = _MockTokens({"primary": (200, 100, 50)})
        mgr = ScopedThemeManager(base)
        mgr.push(ScopedTheme())  # empty scope
        self.assertEqual((200, 100, 50), mgr.resolve("primary"))

    def test_resolve_no_scope_uses_base(self):
        base = _MockTokens({"text": (0, 0, 0)})
        mgr = ScopedThemeManager(base)
        self.assertEqual((0, 0, 0), mgr.resolve("text"))

    def test_resolve_missing_returns_fallback(self):
        base = _MockTokens({})
        mgr = ScopedThemeManager(base)
        self.assertEqual((99, 99, 99), mgr.resolve("missing", (99, 99, 99)))

    def test_context_manager_pushes_pops(self):
        base = _MockTokens({})
        mgr = ScopedThemeManager(base)
        s = ScopedTheme({"k": (1, 2, 3)})
        with mgr.scope(s):
            self.assertEqual(1, mgr.depth)
            self.assertEqual((1, 2, 3), mgr.resolve("k"))
        self.assertEqual(0, mgr.depth)


if __name__ == "__main__":
    unittest.main()
