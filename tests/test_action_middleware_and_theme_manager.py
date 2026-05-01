"""Tests for ActionContext/build_middleware_chain/ActionManager middleware pipeline
and DesignTokens/ThemeManager.

All modules are pure Python — no pygame required.
"""
import unittest
from types import SimpleNamespace

from gui_do.actions.action_middleware import ActionContext, build_middleware_chain
from gui_do.actions.action_manager import ActionManager, KeyBinding
from gui_do.theme.theme_manager import DesignTokens, ThemeManager
from gui_do.events.gui_event import EventType


# ===========================================================================
# Helpers
# ===========================================================================


def _key_event(key=65):
    return SimpleNamespace(kind=EventType.KEY_DOWN, key=key, mod=0)


def _fake_app(scene_name="main", active_window=False):
    scene = SimpleNamespace(active_window=lambda: active_window)
    return SimpleNamespace(active_scene_name=scene_name, scene=scene)


# ===========================================================================
# ActionContext
# ===========================================================================


class TestActionContext(unittest.TestCase):
    def test_fields_set_correctly(self):
        ev = _key_event()
        ctx = ActionContext(action_name="file.open", event=ev)
        self.assertEqual("file.open", ctx.action_name)
        self.assertIs(ev, ctx.event)

    def test_extras_default_empty(self):
        ctx = ActionContext(action_name="edit.copy")
        self.assertEqual({}, ctx.extras)

    def test_extras_mutable(self):
        ctx = ActionContext(action_name="edit.paste")
        ctx.extras["key"] = "value"
        self.assertEqual("value", ctx.extras["key"])

    def test_none_event_allowed(self):
        ctx = ActionContext(action_name="view.zoom", event=None)
        self.assertIsNone(ctx.event)


# ===========================================================================
# build_middleware_chain
# ===========================================================================


class TestBuildMiddlewareChain(unittest.TestCase):
    def _make_ctx(self, name="act"):
        return ActionContext(action_name=name)

    def test_empty_middlewares_calls_terminal(self):
        fired = []
        terminal = lambda ctx: fired.append(ctx) or True
        chain = build_middleware_chain([], terminal)
        ctx = self._make_ctx()
        result = chain(ctx)
        self.assertTrue(result)
        self.assertEqual([ctx], fired)

    def test_single_middleware_wraps_terminal(self):
        log = []
        def mw(ctx, nxt):
            log.append("before")
            result = nxt(ctx)
            log.append("after")
            return result

        terminal = lambda ctx: True
        chain = build_middleware_chain([mw], terminal)
        chain(self._make_ctx())
        self.assertEqual(["before", "after"], log)

    def test_two_middlewares_lifo_order(self):
        """Last-added middleware runs first (LIFO)."""
        log = []
        def mw_a(ctx, nxt): log.append("A"); return nxt(ctx)
        def mw_b(ctx, nxt): log.append("B"); return nxt(ctx)

        # mw_b added last → should run first
        chain = build_middleware_chain([mw_a, mw_b], lambda ctx: True)
        chain(self._make_ctx())
        self.assertEqual(["B", "A"], log)

    def test_middleware_can_block(self):
        terminal_called = []
        terminal = lambda ctx: terminal_called.append(True) or True
        blocking_mw = lambda ctx, nxt: False   # never calls nxt

        chain = build_middleware_chain([blocking_mw], terminal)
        result = chain(self._make_ctx())
        self.assertFalse(result)
        self.assertEqual([], terminal_called)

    def test_middleware_can_mutate_extras(self):
        received = []
        def mw(ctx, nxt):
            ctx.extras["added"] = 42
            return nxt(ctx)

        terminal = lambda ctx: received.append(ctx.extras.get("added")) or True
        chain = build_middleware_chain([mw], terminal)
        chain(self._make_ctx())
        self.assertEqual([42], received)

    def test_middleware_return_value_propagates(self):
        mw = lambda ctx, nxt: False
        chain = build_middleware_chain([mw], lambda ctx: True)
        self.assertFalse(chain(self._make_ctx()))

    def test_terminal_false_propagates(self):
        mw = lambda ctx, nxt: nxt(ctx)
        chain = build_middleware_chain([mw], lambda ctx: False)
        self.assertFalse(chain(self._make_ctx()))


# ===========================================================================
# ActionManager middleware integration
# ===========================================================================


class TestActionManagerMiddleware(unittest.TestCase):
    def setUp(self):
        self.mgr = ActionManager()
        self.fired = []
        self.mgr.register_action("test.act", lambda e: self.fired.append(e) or True)

    def _bind_and_trigger(self, key=65):
        self.mgr.bind_key(key, "test.act")
        app = _fake_app()
        return self.mgr.trigger_from_event(_key_event(key), app)

    def test_no_middleware_fires_handler(self):
        result = self._bind_and_trigger()
        self.assertTrue(result)
        self.assertEqual(1, len(self.fired))

    def test_add_middleware_increases_count(self):
        mw = lambda ctx, nxt: nxt(ctx)
        self.mgr.add_middleware(mw)
        self.assertEqual(1, self.mgr.middleware_count())

    def test_remove_middleware_decreases_count(self):
        mw = lambda ctx, nxt: nxt(ctx)
        self.mgr.add_middleware(mw)
        removed = self.mgr.remove_middleware(mw)
        self.assertTrue(removed)
        self.assertEqual(0, self.mgr.middleware_count())

    def test_remove_missing_middleware_returns_false(self):
        self.assertFalse(self.mgr.remove_middleware(lambda ctx, nxt: nxt(ctx)))

    def test_clear_middlewares(self):
        self.mgr.add_middleware(lambda ctx, nxt: nxt(ctx))
        self.mgr.add_middleware(lambda ctx, nxt: nxt(ctx))
        self.mgr.clear_middlewares()
        self.assertEqual(0, self.mgr.middleware_count())

    def test_middleware_sees_action_name(self):
        seen = []
        def mw(ctx, nxt):
            seen.append(ctx.action_name)
            return nxt(ctx)
        self.mgr.add_middleware(mw)
        self._bind_and_trigger()
        self.assertEqual(["test.act"], seen)

    def test_blocking_middleware_prevents_handler(self):
        self.mgr.add_middleware(lambda ctx, nxt: False)
        result = self._bind_and_trigger()
        self.assertFalse(result)
        self.assertEqual(0, len(self.fired))

    def test_lifo_order(self):
        log = []
        self.mgr.add_middleware(lambda ctx, nxt: (log.append("A"), nxt(ctx))[1])
        self.mgr.add_middleware(lambda ctx, nxt: (log.append("B"), nxt(ctx))[1])
        self._bind_and_trigger()
        self.assertEqual(["B", "A"], log)


# ===========================================================================
# ActionManager key bindings
# ===========================================================================


class TestActionManagerBindings(unittest.TestCase):
    def setUp(self):
        self.mgr = ActionManager()
        self.mgr.register_action("file.save", lambda e: True)
        self.mgr.register_action("file.open", lambda e: True)

    def test_bind_key_registers(self):
        self.mgr.bind_key(65, "file.save")
        self.assertEqual(1, self.mgr.binding_count())

    def test_unbind_key_removes(self):
        self.mgr.bind_key(65, "file.save")
        removed = self.mgr.unbind_key(65, "file.save")
        self.assertTrue(removed)
        self.assertEqual(0, self.mgr.binding_count())

    def test_unbind_missing_key_returns_false(self):
        self.assertFalse(self.mgr.unbind_key(65, "file.save"))

    def test_clear_bindings(self):
        self.mgr.bind_key(65, "file.save")
        self.mgr.bind_key(66, "file.open")
        self.mgr.clear_bindings()
        self.assertEqual(0, self.mgr.binding_count())

    def test_bindings_for_action(self):
        self.mgr.bind_key(83, "file.save")
        bindings = self.mgr.bindings_for_action("file.save")
        self.assertEqual(1, len(bindings))
        self.assertEqual(83, bindings[0].key)

    def test_bindings_for_unbound_action(self):
        self.assertEqual([], self.mgr.bindings_for_action("file.save"))

    def test_duplicate_bind_ignored(self):
        self.mgr.bind_key(65, "file.save")
        self.mgr.bind_key(65, "file.save")
        self.assertEqual(1, self.mgr.binding_count())

    def test_same_key_two_actions(self):
        self.mgr.bind_key(65, "file.save")
        self.mgr.bind_key(65, "file.open")
        self.assertEqual(2, self.mgr.binding_count())

    def test_trigger_fires_handler(self):
        fired = []
        self.mgr.register_action("x.act", lambda e: fired.append(True) or True)
        self.mgr.bind_key(90, "x.act")
        self.mgr.trigger_from_event(_key_event(90), _fake_app())
        self.assertEqual([True], fired)

    def test_trigger_non_key_event_returns_false(self):
        ev = SimpleNamespace(kind=EventType.MOUSE_MOTION, key=None)
        self.assertFalse(self.mgr.trigger_from_event(ev, _fake_app()))


# ===========================================================================
# DesignTokens
# ===========================================================================


class TestDesignTokens(unittest.TestCase):
    def setUp(self):
        self.dt = DesignTokens("test", {"primary": (10, 20, 30), "surface": (50, 60, 70)})

    def test_name(self):
        self.assertEqual("test", self.dt.name)

    def test_get_existing(self):
        self.assertEqual((10, 20, 30), self.dt.get("primary"))

    def test_get_missing_returns_fallback(self):
        self.assertEqual((0, 0, 0), self.dt.get("missing", (0, 0, 0)))

    def test_get_default_fallback(self):
        result = self.dt.get("missing")
        self.assertEqual(3, len(result))

    def test_set_new_token(self):
        self.dt.set("accent", (100, 150, 200))
        self.assertEqual((100, 150, 200), self.dt.get("accent"))

    def test_set_overrides_existing(self):
        self.dt.set("primary", (1, 2, 3))
        self.assertEqual((1, 2, 3), self.dt.get("primary"))

    def test_token_names_sorted(self):
        names = self.dt.token_names()
        self.assertEqual(sorted(names), names)

    def test_to_dict_copy(self):
        d = self.dt.to_dict()
        d["primary"] = (99, 99, 99)
        # original unchanged
        self.assertEqual((10, 20, 30), self.dt.get("primary"))

    def test_copy_independent(self):
        c = self.dt.copy("copy")
        c.set("primary", (0, 0, 0))
        self.assertEqual((10, 20, 30), self.dt.get("primary"))

    def test_from_dict(self):
        dt = DesignTokens.from_dict("d", {"text": (200, 200, 200)})
        self.assertEqual((200, 200, 200), dt.get("text"))

    def test_from_dict_skips_invalid(self):
        dt = DesignTokens.from_dict("d", {"bad": "xyz", "ok": (1, 2, 3)})
        self.assertEqual((1, 2, 3), dt.get("ok"))


# ===========================================================================
# ThemeManager
# ===========================================================================


class TestThemeManagerBuiltIns(unittest.TestCase):
    def setUp(self):
        self.mgr = ThemeManager()

    def test_dark_and_light_registered(self):
        names = self.mgr.theme_names()
        self.assertIn("dark", names)
        self.assertIn("light", names)

    def test_default_active_theme_is_dark(self):
        self.assertEqual("dark", self.mgr.active_theme.value)

    def test_token_resolves_from_active(self):
        color = self.mgr.token("primary")
        self.assertIsInstance(color, tuple)
        self.assertEqual(3, len(color))

    def test_has_theme_true(self):
        self.assertTrue(self.mgr.has_theme("dark"))
        self.assertTrue(self.mgr.has_theme("light"))

    def test_has_theme_false(self):
        self.assertFalse(self.mgr.has_theme("unknown"))


class TestThemeManagerSwitch(unittest.TestCase):
    def setUp(self):
        self.mgr = ThemeManager()

    def test_switch_to_light(self):
        result = self.mgr.switch("light")
        self.assertTrue(result)
        self.assertEqual("light", self.mgr.active_theme.value)

    def test_switch_updates_active_tokens(self):
        self.mgr.switch("dark")
        dark_primary = self.mgr.token("primary")
        self.mgr.switch("light")
        light_primary = self.mgr.token("primary")
        self.assertNotEqual(dark_primary, light_primary)

    def test_switch_unknown_returns_false(self):
        self.assertFalse(self.mgr.switch("nonexistent"))

    def test_switch_unknown_leaves_active_unchanged(self):
        self.mgr.switch("nonexistent")
        self.assertEqual("dark", self.mgr.active_theme.value)

    def test_switch_fires_subscriber(self):
        events = []
        self.mgr.active_theme.subscribe(events.append)
        self.mgr.switch("light")
        self.assertEqual(1, len(events))

    def test_active_tokens_updates_on_switch(self):
        tokens_seen = []
        self.mgr.active_tokens.subscribe(tokens_seen.append)
        self.mgr.switch("light")
        self.assertEqual(1, len(tokens_seen))
        self.assertIsInstance(tokens_seen[0], DesignTokens)


class TestThemeManagerRegistration(unittest.TestCase):
    def setUp(self):
        self.mgr = ThemeManager()

    def test_register_custom_theme(self):
        self.mgr.register_theme("custom", {"primary": (1, 2, 3)})
        self.assertTrue(self.mgr.has_theme("custom"))

    def test_register_then_switch(self):
        self.mgr.register_theme("custom", {"primary": (1, 2, 3)})
        self.mgr.switch("custom")
        self.assertEqual((1, 2, 3), self.mgr.token("primary"))

    def test_register_replaces_existing(self):
        self.mgr.register_theme("custom", {"primary": (1, 2, 3)})
        self.mgr.register_theme("custom", {"primary": (9, 8, 7)})
        self.mgr.switch("custom")
        self.assertEqual((9, 8, 7), self.mgr.token("primary"))

    def test_register_empty_name_raises(self):
        with self.assertRaises(ValueError):
            self.mgr.register_theme("", {"primary": (0, 0, 0)})

    def test_get_theme_returns_design_tokens(self):
        tokens = self.mgr.get_theme("dark")
        self.assertIsInstance(tokens, DesignTokens)

    def test_get_theme_unknown_returns_none(self):
        self.assertIsNone(self.mgr.get_theme("ghost"))

    def test_register_design_tokens_directly(self):
        dt = DesignTokens("mydt", {"surface": (11, 22, 33)})
        self.mgr.register_theme("mydt", dt)
        self.mgr.switch("mydt")
        self.assertEqual((11, 22, 33), self.mgr.token("surface"))

    def test_token_fallback_on_unknown_name(self):
        fallback = (7, 8, 9)
        result = self.mgr.token("completely_unknown", fallback)
        self.assertEqual(fallback, result)


if __name__ == "__main__":
    unittest.main()
