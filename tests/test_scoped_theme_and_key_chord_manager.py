"""Tests for ScopedTheme, ScopedThemeManager, and KeyChordManager.

ScopedTheme / ScopedThemeManager — pure Python, no pygame.
KeyChordManager — uses lightweight stubs for ActionManager and timer.
"""
import unittest
from types import SimpleNamespace

from gui_do.theme.scoped_theme import ScopedTheme, ScopedThemeManager
from gui_do.theme.theme_manager import DesignTokens
from gui_do.actions.key_chord_manager import (
    KeyChordManager,
    KeyChord,
    ChordStep,
)
from gui_do.events.gui_event import EventType


# ===========================================================================
# Helpers / stubs
# ===========================================================================


def _base_tokens(**kwargs) -> DesignTokens:
    tokens = {"primary": (10, 20, 30), "surface": (50, 60, 70)}
    tokens.update(kwargs)
    return DesignTokens("test", tokens)


class _FakeActions:
    """Minimal ActionManager stub that exposes _actions dict."""

    def __init__(self):
        self._actions: dict = {}

    def register_action(self, name, handler):
        self._actions[name] = handler


def _key_event(key: int, mod: int = 0) -> SimpleNamespace:
    return SimpleNamespace(kind=EventType.KEY_DOWN, key=key, mod=mod)


def _non_key_event() -> SimpleNamespace:
    return SimpleNamespace(kind=EventType.MOUSE_MOTION, key=None, mod=0)


def _chord(*steps) -> KeyChord:
    return KeyChord(list(steps))


# ===========================================================================
# ScopedTheme
# ===========================================================================


class TestScopedThemeInitial(unittest.TestCase):
    def test_empty_scope_name(self):
        s = ScopedTheme(name="my-scope")
        self.assertEqual("my-scope", s.name)

    def test_default_name(self):
        s = ScopedTheme()
        self.assertEqual("scoped", s.name)

    def test_parent_initially_none(self):
        s = ScopedTheme()
        self.assertIsNone(s.parent)

    def test_to_dict_empty(self):
        s = ScopedTheme()
        self.assertEqual({}, s.to_dict())


class TestScopedThemeOverrides(unittest.TestCase):
    def test_construct_with_overrides(self):
        s = ScopedTheme({"primary": (1, 2, 3)})
        self.assertEqual((1, 2, 3), s.to_dict()["primary"])

    def test_set_adds_token(self):
        s = ScopedTheme()
        s.set("accent", (100, 150, 200))
        self.assertEqual((100, 150, 200), s.to_dict()["accent"])

    def test_remove_existing_token(self):
        s = ScopedTheme({"accent": (1, 2, 3)})
        s.remove("accent")
        self.assertNotIn("accent", s.to_dict())

    def test_remove_missing_token_no_error(self):
        s = ScopedTheme()
        s.remove("nonexistent")  # should not raise

    def test_resolve_own_token(self):
        s = ScopedTheme({"primary": (9, 8, 7)})
        self.assertEqual((9, 8, 7), s.resolve("primary"))

    def test_resolve_missing_returns_fallback(self):
        s = ScopedTheme()
        self.assertIsNone(s.resolve("missing"))
        self.assertEqual((0, 0, 0), s.resolve("missing", fallback=(0, 0, 0)))

    def test_resolve_climbs_parent_chain(self):
        parent = ScopedTheme({"surface": (10, 20, 30)})
        child = ScopedTheme()
        child._parent = parent
        self.assertEqual((10, 20, 30), child.resolve("surface"))

    def test_child_overrides_parent(self):
        parent = ScopedTheme({"surface": (10, 20, 30)})
        child = ScopedTheme({"surface": (99, 88, 77)})
        child._parent = parent
        self.assertEqual((99, 88, 77), child.resolve("surface"))

    def test_copy_is_independent(self):
        s = ScopedTheme({"primary": (1, 2, 3)}, name="original")
        c = s.copy(name="copy")
        c.set("primary", (9, 9, 9))
        self.assertEqual((1, 2, 3), s.resolve("primary"))

    def test_to_dict_does_not_include_parent(self):
        parent = ScopedTheme({"surface": (1, 2, 3)})
        child = ScopedTheme({"text": (4, 5, 6)})
        child._parent = parent
        d = child.to_dict()
        self.assertNotIn("surface", d)
        self.assertIn("text", d)


# ===========================================================================
# ScopedThemeManager
# ===========================================================================


class TestScopedThemeManagerStack(unittest.TestCase):
    def setUp(self):
        self.base = _base_tokens()
        self.mgr = ScopedThemeManager(self.base)

    def test_initial_depth_zero(self):
        self.assertEqual(0, self.mgr.depth)

    def test_active_scope_none_initially(self):
        self.assertIsNone(self.mgr.active_scope)

    def test_push_increases_depth(self):
        self.mgr.push(ScopedTheme({"primary": (1, 2, 3)}))
        self.assertEqual(1, self.mgr.depth)

    def test_pop_decreases_depth(self):
        self.mgr.push(ScopedTheme())
        self.mgr.pop()
        self.assertEqual(0, self.mgr.depth)

    def test_pop_empty_returns_none(self):
        self.assertIsNone(self.mgr.pop())

    def test_active_scope_after_push(self):
        s = ScopedTheme(name="topmost")
        self.mgr.push(s)
        self.assertIs(s, self.mgr.active_scope)

    def test_push_sets_parent_to_previous_top(self):
        s1 = ScopedTheme()
        s2 = ScopedTheme()
        self.mgr.push(s1)
        self.mgr.push(s2)
        self.assertIs(s1, s2.parent)

    def test_pop_clears_parent_reference(self):
        s = ScopedTheme()
        self.mgr.push(s)
        self.mgr.pop()
        self.assertIsNone(s.parent)

    def test_first_push_parent_is_none(self):
        s = ScopedTheme()
        self.mgr.push(s)
        self.assertIsNone(s.parent)


class TestScopedThemeManagerResolve(unittest.TestCase):
    def setUp(self):
        self.base = _base_tokens(surface=(50, 60, 70))
        self.mgr = ScopedThemeManager(self.base)

    def test_resolve_falls_through_to_base(self):
        self.assertEqual((10, 20, 30), self.mgr.resolve("primary"))

    def test_resolve_scope_overrides_base(self):
        self.mgr.push(ScopedTheme({"primary": (1, 2, 3)}))
        self.assertEqual((1, 2, 3), self.mgr.resolve("primary"))

    def test_resolve_inner_scope_overrides_outer(self):
        self.mgr.push(ScopedTheme({"primary": (10, 10, 10)}))
        self.mgr.push(ScopedTheme({"primary": (99, 0, 0)}))
        self.assertEqual((99, 0, 0), self.mgr.resolve("primary"))

    def test_resolve_outer_token_not_in_inner(self):
        self.mgr.push(ScopedTheme({"primary": (1, 2, 3)}))
        # "surface" only in base
        self.assertEqual((50, 60, 70), self.mgr.resolve("surface"))

    def test_resolve_unknown_returns_fallback(self):
        self.assertEqual((0, 0, 0), self.mgr.resolve("unknown", (0, 0, 0)))

    def test_pop_restores_base_resolution(self):
        self.mgr.push(ScopedTheme({"primary": (1, 2, 3)}))
        self.mgr.pop()
        self.assertEqual((10, 20, 30), self.mgr.resolve("primary"))


class TestScopedThemeManagerContextManager(unittest.TestCase):
    def setUp(self):
        self.base = _base_tokens()
        self.mgr = ScopedThemeManager(self.base)

    def test_scope_context_pushes_on_enter(self):
        s = ScopedTheme({"primary": (5, 5, 5)})
        with self.mgr.scope(s):
            self.assertEqual(1, self.mgr.depth)
            self.assertEqual((5, 5, 5), self.mgr.resolve("primary"))

    def test_scope_context_pops_on_exit(self):
        s = ScopedTheme({"primary": (5, 5, 5)})
        with self.mgr.scope(s):
            pass
        self.assertEqual(0, self.mgr.depth)
        self.assertEqual((10, 20, 30), self.mgr.resolve("primary"))

    def test_nested_scopes_resolve_correctly(self):
        outer = ScopedTheme({"primary": (11, 11, 11)})
        inner = ScopedTheme({"primary": (22, 22, 22)})
        with self.mgr.scope(outer):
            with self.mgr.scope(inner):
                self.assertEqual((22, 22, 22), self.mgr.resolve("primary"))
            self.assertEqual((11, 11, 11), self.mgr.resolve("primary"))


# ===========================================================================
# KeyChord / ChordStep
# ===========================================================================


class TestKeyChord(unittest.TestCase):
    def test_empty_steps_raises(self):
        with self.assertRaises(ValueError):
            KeyChord([])

    def test_single_step(self):
        ch = _chord(ChordStep(key=65, mod=0))
        self.assertEqual(1, len(ch))

    def test_two_steps(self):
        ch = _chord(ChordStep(65), ChordStep(66))
        self.assertEqual(2, len(ch))

    def test_getitem(self):
        step = ChordStep(key=75, mod=4)
        ch = KeyChord([step])
        self.assertIs(step, ch[0])

    def test_frozen_steps(self):
        ch = _chord(ChordStep(65))
        with self.assertRaises(Exception):
            ch.steps = ()  # type: ignore[misc]


# ===========================================================================
# KeyChordManager
# ===========================================================================


class TestKeyChordManagerSetup(unittest.TestCase):
    def test_none_actions_raises(self):
        with self.assertRaises(ValueError):
            KeyChordManager(None)

    def test_registered_chords_initially_empty(self):
        mgr = KeyChordManager(_FakeActions())
        self.assertEqual([], mgr.registered_chords())

    def test_not_in_progress_initially(self):
        mgr = KeyChordManager(_FakeActions())
        self.assertFalse(mgr.is_in_progress)


class TestKeyChordManagerRegistration(unittest.TestCase):
    def setUp(self):
        self.actions = _FakeActions()
        self.mgr = KeyChordManager(self.actions)

    def _bind(self, *keys, action="act"):
        steps = [ChordStep(k) for k in keys]
        chord = KeyChord(steps)
        self.mgr.bind(chord, action)
        return chord

    def test_bind_registers_chord(self):
        ch = self._bind(65)
        self.assertIn(ch, self.mgr.registered_chords())

    def test_bind_replaces_duplicate(self):
        ch = self._bind(65, 66, action="old")
        self.mgr.bind(ch, "new")
        self.assertEqual(1, len(self.mgr.registered_chords()))

    def test_unbind_existing(self):
        ch = self._bind(65)
        result = self.mgr.unbind(ch)
        self.assertTrue(result)
        self.assertEqual([], self.mgr.registered_chords())

    def test_unbind_missing_returns_false(self):
        result = self.mgr.unbind(KeyChord([ChordStep(99)]))
        self.assertFalse(result)


class TestKeyChordManagerSingleStep(unittest.TestCase):
    def setUp(self):
        self.actions = _FakeActions()
        self.mgr = KeyChordManager(self.actions)
        self.fired = []
        self.actions.register_action("test.act", lambda e: self.fired.append(e) or True)

        self.chord = KeyChord([ChordStep(key=65, mod=0)])
        self.mgr.bind(self.chord, "test.act")

    def test_single_step_chord_fires_immediately(self):
        ev = _key_event(65)
        consumed = self.mgr.process_event(ev)
        self.assertTrue(consumed)
        self.assertEqual(1, len(self.fired))

    def test_non_key_event_not_consumed(self):
        consumed = self.mgr.process_event(_non_key_event())
        self.assertFalse(consumed)

    def test_wrong_key_not_consumed(self):
        ev = _key_event(90)
        consumed = self.mgr.process_event(ev)
        self.assertFalse(consumed)
        self.assertEqual(0, len(self.fired))


class TestKeyChordManagerTwoStep(unittest.TestCase):
    def setUp(self):
        self.actions = _FakeActions()
        self.mgr = KeyChordManager(self.actions)
        self.fired = []
        self.actions.register_action("test.act", lambda e: self.fired.append(e) or True)

        # Ctrl+K then Ctrl+C (mod=4 for Ctrl)
        self.chord = KeyChord([ChordStep(75, 4), ChordStep(67, 4)])
        self.mgr.bind(self.chord, "test.act")

    def test_first_step_consumed_not_fired(self):
        ev = _key_event(75, mod=4)
        consumed = self.mgr.process_event(ev)
        self.assertTrue(consumed)
        self.assertEqual(0, len(self.fired))
        self.assertTrue(self.mgr.is_in_progress)

    def test_second_step_fires_action(self):
        self.mgr.process_event(_key_event(75, mod=4))
        consumed = self.mgr.process_event(_key_event(67, mod=4))
        self.assertTrue(consumed)
        self.assertEqual(1, len(self.fired))
        self.assertFalse(self.mgr.is_in_progress)

    def test_wrong_second_step_resets(self):
        self.mgr.process_event(_key_event(75, mod=4))
        consumed = self.mgr.process_event(_key_event(90, mod=4))
        self.assertFalse(consumed)   # falls through
        self.assertFalse(self.mgr.is_in_progress)
        self.assertEqual(0, len(self.fired))

    def test_reset_clears_progress(self):
        self.mgr.process_event(_key_event(75, mod=4))
        self.assertTrue(self.mgr.is_in_progress)
        self.mgr.reset()
        self.assertFalse(self.mgr.is_in_progress)

    def test_after_reset_first_step_works_again(self):
        self.mgr.process_event(_key_event(75, mod=4))
        self.mgr.reset()
        self.mgr.process_event(_key_event(75, mod=4))
        self.mgr.process_event(_key_event(67, mod=4))
        self.assertEqual(1, len(self.fired))

    def test_mod_zero_matches_any(self):
        """A ChordStep with mod=0 matches regardless of actual modifier."""
        chord = KeyChord([ChordStep(65, 0)])
        self.mgr.bind(chord, "test.act")
        consumed = self.mgr.process_event(_key_event(65, mod=8))
        self.assertTrue(consumed)


class TestKeyChordManagerUnregisteredAction(unittest.TestCase):
    def test_unregistered_action_returns_false(self):
        actions = _FakeActions()
        mgr = KeyChordManager(actions)
        chord = KeyChord([ChordStep(65)])
        mgr.bind(chord, "ghost.action")   # no handler registered
        consumed = mgr.process_event(_key_event(65))
        self.assertFalse(consumed)


if __name__ == "__main__":
    unittest.main()
