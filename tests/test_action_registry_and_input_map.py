import unittest

from gui_do.actions.action_registry import ActionDescriptor, ActionRegistry
from gui_do.actions.input_map import InputBinding, InputMap


# ---------------------------------------------------------------------------
# ActionDescriptor
# ---------------------------------------------------------------------------


class TestActionDescriptor(unittest.TestCase):
    def _make(self, **kwargs):
        defaults = dict(
            action_id="test.action",
            label="Test",
            callback=lambda ctx, ev: True,
        )
        defaults.update(kwargs)
        return ActionDescriptor(**defaults)

    def test_is_enabled_static_true(self):
        d = self._make(enabled=True)
        self.assertTrue(d.is_enabled())

    def test_is_enabled_static_false(self):
        d = self._make(enabled=False)
        self.assertFalse(d.is_enabled())

    def test_is_enabled_callable_predicate(self):
        d = self._make(enabled=lambda ctx: ctx > 0)
        self.assertTrue(d.is_enabled(context=1))
        self.assertFalse(d.is_enabled(context=0))

    def test_is_checked_static(self):
        d = self._make(checked=True)
        self.assertTrue(d.is_checked())

    def test_is_checked_callable(self):
        d = self._make(checked=lambda ctx: ctx == "on")
        self.assertTrue(d.is_checked(context="on"))
        self.assertFalse(d.is_checked(context="off"))

    def test_invoke_calls_callback_when_enabled(self):
        called = []
        d = self._make(callback=lambda ctx, ev: called.append((ctx, ev)) or True)
        result = d.invoke(context="c", event="e")
        self.assertTrue(result)
        self.assertEqual([("c", "e")], called)

    def test_invoke_returns_false_when_disabled(self):
        called = []
        d = self._make(enabled=False, callback=lambda ctx, ev: called.append(True) or True)
        result = d.invoke()
        self.assertFalse(result)
        self.assertEqual([], called)


# ---------------------------------------------------------------------------
# ActionRegistry
# ---------------------------------------------------------------------------


class TestActionRegistry(unittest.TestCase):
    def _make_registry(self):
        return ActionRegistry()

    def _make_descriptor(self, action_id="a.b", label="Foo"):
        return ActionDescriptor(
            action_id=action_id,
            label=label,
            callback=lambda ctx, ev: True,
        )

    def test_register_and_has(self):
        reg = self._make_registry()
        reg.register(self._make_descriptor("x.y"))
        self.assertTrue(reg.has("x.y"))

    def test_has_returns_false_for_unknown(self):
        reg = self._make_registry()
        self.assertFalse(reg.has("no.such"))

    def test_get_returns_registered_descriptor(self):
        reg = self._make_registry()
        d = self._make_descriptor("a.b")
        reg.register(d)
        self.assertIs(d, reg.get("a.b"))

    def test_get_raises_for_unknown(self):
        reg = self._make_registry()
        with self.assertRaises(KeyError):
            reg.get("missing")

    def test_declare_creates_and_returns_descriptor(self):
        reg = self._make_registry()
        d = reg.declare("do.thing", "Do Thing", lambda ctx, ev: True)
        self.assertIsInstance(d, ActionDescriptor)
        self.assertTrue(reg.has("do.thing"))
        self.assertEqual("Do Thing", d.label)

    def test_register_many(self):
        reg = self._make_registry()
        descs = [self._make_descriptor(f"a.{i}") for i in range(3)]
        reg.register_many(descs)
        self.assertEqual(3, len(reg.descriptors()))

    def test_unregister_removes_action(self):
        reg = self._make_registry()
        reg.register(self._make_descriptor("r.x"))
        result = reg.unregister("r.x")
        self.assertTrue(result)
        self.assertFalse(reg.has("r.x"))

    def test_unregister_returns_false_for_unknown(self):
        reg = self._make_registry()
        self.assertFalse(reg.unregister("no.such"))

    def test_clear_removes_all(self):
        reg = self._make_registry()
        reg.register(self._make_descriptor("a.1"))
        reg.register(self._make_descriptor("a.2"))
        reg.clear()
        self.assertEqual([], reg.descriptors())

    def test_action_ids_sorted(self):
        reg = self._make_registry()
        reg.register(self._make_descriptor("z.z"))
        reg.register(self._make_descriptor("a.a"))
        reg.register(self._make_descriptor("m.m"))
        self.assertEqual(["a.a", "m.m", "z.z"], reg.action_ids())

    def test_invoke_calls_descriptor(self):
        reg = self._make_registry()
        called = []
        reg.register(ActionDescriptor(
            action_id="q.q",
            label="Q",
            callback=lambda ctx, ev: called.append(True) or True,
        ))
        reg.invoke("q.q")
        self.assertEqual([True], called)

    def test_invoke_disabled_action_returns_false(self):
        reg = self._make_registry()
        reg.register(ActionDescriptor(
            action_id="d.d",
            label="D",
            callback=lambda ctx, ev: True,
            enabled=False,
        ))
        self.assertFalse(reg.invoke("d.d"))

    def test_register_empty_id_raises(self):
        reg = self._make_registry()
        with self.assertRaises(ValueError):
            reg.register(ActionDescriptor(
                action_id="",
                label="Bad",
                callback=lambda ctx, ev: True,
            ))

    def test_register_non_callable_raises(self):
        reg = self._make_registry()
        with self.assertRaises(ValueError):
            reg.register(ActionDescriptor(
                action_id="x.x",
                label="X",
                callback="not_callable",  # type: ignore[arg-type]
            ))


# ---------------------------------------------------------------------------
# InputMap
# ---------------------------------------------------------------------------


class TestInputMap(unittest.TestCase):
    def test_declare_creates_binding(self):
        imap = InputMap()
        imap.declare("edit.copy", key=67, mod=64, label="Copy")
        b = imap.binding_for("edit.copy")
        self.assertIsNotNone(b)
        self.assertEqual(67, b.key)
        self.assertEqual(64, b.mod)
        self.assertTrue(b.is_default)

    def test_declare_empty_action_raises(self):
        imap = InputMap()
        with self.assertRaises(ValueError):
            imap.declare("", key=67)

    def test_declare_does_not_overwrite_existing(self):
        imap = InputMap()
        imap.declare("edit.copy", key=67)
        imap.declare("edit.copy", key=99)  # should be ignored
        self.assertEqual(67, imap.binding_for("edit.copy").key)

    def test_bind_overrides_declared(self):
        imap = InputMap()
        imap.declare("edit.copy", key=67, mod=64)
        imap.bind("edit.copy", key=67, mod=72)
        b = imap.binding_for("edit.copy")
        self.assertEqual(72, b.mod)
        self.assertFalse(b.is_default)

    def test_bind_creates_new_action(self):
        imap = InputMap()
        imap.bind("new.action", key=100)
        self.assertIsNotNone(imap.binding_for("new.action"))

    def test_bind_preserves_label(self):
        imap = InputMap()
        imap.declare("a.b", key=10, label="Alpha")
        imap.bind("a.b", key=20)
        self.assertEqual("Alpha", imap.binding_for("a.b").label)

    def test_unbind_removes_binding(self):
        imap = InputMap()
        imap.declare("a.b", key=10)
        result = imap.unbind("a.b")
        self.assertTrue(result)
        self.assertIsNone(imap.binding_for("a.b"))

    def test_unbind_unknown_returns_false(self):
        imap = InputMap()
        self.assertFalse(imap.unbind("no.such"))

    def test_reset_to_default_marks_is_default(self):
        imap = InputMap()
        imap.declare("a.b", key=10)
        imap.bind("a.b", key=20)
        result = imap.reset_to_default("a.b")
        self.assertTrue(result)
        self.assertTrue(imap.binding_for("a.b").is_default)

    def test_reset_to_default_already_default_returns_false(self):
        imap = InputMap()
        imap.declare("a.b", key=10)
        self.assertFalse(imap.reset_to_default("a.b"))

    def test_reset_to_default_unknown_returns_false(self):
        imap = InputMap()
        self.assertFalse(imap.reset_to_default("no.such"))

    def test_bindings_returns_all(self):
        imap = InputMap()
        imap.declare("a.b", key=1)
        imap.declare("c.d", key=2)
        self.assertEqual(2, len(imap.bindings()))

    def test_actions_returns_sorted(self):
        imap = InputMap()
        imap.declare("z.z", key=1)
        imap.declare("a.a", key=2)
        self.assertEqual(["a.a", "z.z"], imap.actions())

    def test_len(self):
        imap = InputMap()
        imap.declare("a.b", key=1)
        imap.declare("c.d", key=2)
        self.assertEqual(2, len(imap))

    def test_binding_for_unknown_returns_none(self):
        imap = InputMap()
        self.assertIsNone(imap.binding_for("no.such"))


if __name__ == "__main__":
    unittest.main()
