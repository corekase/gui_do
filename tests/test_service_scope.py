"""Tests for gui_do.app.service_scope — ServiceKey, ServiceScope, ScopeStack."""
from __future__ import annotations

import unittest

from gui_do.app.service_scope import ServiceKey, ServiceScope, ScopeStack


class TestServiceKey(unittest.TestCase):
    def test_equality_by_name(self):
        k1: ServiceKey[int] = ServiceKey("foo")
        k2: ServiceKey[str] = ServiceKey("foo")
        self.assertEqual(k1, k2)

    def test_inequality(self):
        self.assertNotEqual(ServiceKey("a"), ServiceKey("b"))

    def test_hash_consistent_with_eq(self):
        k1: ServiceKey[int] = ServiceKey("x")
        k2: ServiceKey[int] = ServiceKey("x")
        self.assertEqual(hash(k1), hash(k2))

    def test_usable_as_dict_key(self):
        k: ServiceKey[str] = ServiceKey("svc")
        d = {k: "hello"}
        self.assertEqual(d[ServiceKey("svc")], "hello")

    def test_repr(self):
        self.assertEqual(repr(ServiceKey("svc")), "ServiceKey('svc')")

    def test_empty_name_raises(self):
        with self.assertRaises(ValueError):
            ServiceKey("")


class TestServiceScope(unittest.TestCase):
    KEY: ServiceKey[str] = ServiceKey("name")

    def test_bind_and_get(self):
        scope = ServiceScope()
        scope.bind(self.KEY, "Alice")
        self.assertEqual(scope.get(self.KEY), "Alice")

    def test_get_missing_raises(self):
        scope = ServiceScope()
        with self.assertRaises(KeyError):
            scope.get(self.KEY)

    def test_get_optional_returns_none_when_missing(self):
        scope = ServiceScope()
        self.assertIsNone(scope.get_optional(self.KEY))

    def test_get_optional_returns_value(self):
        scope = ServiceScope()
        scope.bind(self.KEY, "Bob")
        self.assertEqual(scope.get_optional(self.KEY), "Bob")

    def test_child_inherits_parent_binding(self):
        parent = ServiceScope()
        parent.bind(self.KEY, "parent-val")
        child = parent.child()
        self.assertEqual(child.get(self.KEY), "parent-val")

    def test_child_can_shadow_parent(self):
        parent = ServiceScope()
        parent.bind(self.KEY, "parent-val")
        child = parent.child()
        child.bind(self.KEY, "child-val")
        self.assertEqual(child.get(self.KEY), "child-val")
        self.assertEqual(parent.get(self.KEY), "parent-val")

    def test_dispose_calls_owned_dispose(self):
        called = []

        class Svc:
            def dispose(self):
                called.append(True)

        scope = ServiceScope()
        svc_key: ServiceKey["Svc"] = ServiceKey("svc")
        scope.bind(svc_key, Svc())
        scope.dispose()
        self.assertEqual(called, [True])

    def test_dispose_not_owned_skips_dispose(self):
        called = []

        class Svc:
            def dispose(self):
                called.append(True)

        scope = ServiceScope()
        svc_key: ServiceKey["Svc"] = ServiceKey("svc2")
        scope.bind(svc_key, Svc(), owned=False)
        scope.dispose()
        self.assertEqual(called, [])

    def test_dispose_multiple_lifo_order(self):
        order = []

        class Svc:
            def __init__(self, label):
                self.label = label

            def dispose(self):
                order.append(self.label)

        scope = ServiceScope()
        k1: ServiceKey = ServiceKey("a")
        k2: ServiceKey = ServiceKey("b")
        scope.bind(k1, Svc("first"))
        scope.bind(k2, Svc("second"))
        scope.dispose()
        self.assertEqual(order, ["second", "first"])

    def test_dispose_clears_bindings(self):
        scope = ServiceScope()
        scope.bind(self.KEY, "val")
        scope.dispose()
        with self.assertRaises(KeyError):
            scope.get(self.KEY)

    def test_bind_non_disposable_instance(self):
        scope = ServiceScope()
        k: ServiceKey[int] = ServiceKey("num")
        scope.bind(k, 42)
        self.assertEqual(scope.get(k), 42)


class TestScopeStack(unittest.TestCase):
    def test_root_is_accessible(self):
        stack = ScopeStack()
        self.assertIsNotNone(stack.root)
        self.assertIs(stack.current, stack.root)

    def test_push_creates_child_scope(self):
        stack = ScopeStack()
        key: ServiceKey[str] = ServiceKey("k")
        stack.root.bind(key, "root-val")
        with stack.push() as child:
            self.assertIs(stack.current, child)
            self.assertEqual(child.get(key), "root-val")

    def test_pop_restores_parent(self):
        stack = ScopeStack()
        with stack.push():
            pass
        self.assertIs(stack.current, stack.root)

    def test_pop_disposes_child(self):
        called = []

        class Svc:
            def dispose(self):
                called.append(True)

        stack = ScopeStack()
        key: ServiceKey = ServiceKey("svc")
        with stack.push() as child:
            child.bind(key, Svc())
        self.assertEqual(called, [True])

    def test_nested_push(self):
        stack = ScopeStack()
        key: ServiceKey[int] = ServiceKey("n")
        stack.root.bind(key, 0)
        with stack.push() as l1:
            l1.bind(key, 1)
            with stack.push() as l2:
                l2.bind(key, 2)
                self.assertEqual(stack.current.get(key), 2)
            self.assertEqual(stack.current.get(key), 1)
        self.assertEqual(stack.current.get(key), 0)

    def test_cannot_pop_root(self):
        stack = ScopeStack()
        with self.assertRaises(RuntimeError):
            stack._pop_raw()


if __name__ == "__main__":
    unittest.main()
