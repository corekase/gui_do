"""Tests for FocusRing and FocusScopeManager."""
import unittest

from gui_do.focus.focus_ring import FocusRing
from gui_do.focus.focus_scope import FocusScope, FocusScopeManager


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class _FakeFocusManager:
    """Minimal stand-in for FocusManager that exposes _scope_stack."""

    def __init__(self):
        self._scope_stack = []


class _FakeNode:
    def __init__(self, control_id: str):
        self.control_id = control_id


# ===========================================================================
# FocusRing
# ===========================================================================


class TestFocusRingMembership(unittest.TestCase):
    def test_contains_existing(self):
        ring = FocusRing(["a", "b", "c"])
        self.assertTrue(ring.contains("b"))

    def test_contains_missing(self):
        ring = FocusRing(["a", "b"])
        self.assertFalse(ring.contains("z"))

    def test_node_ids_returns_copy(self):
        ring = FocusRing(["a", "b"])
        ids = ring.node_ids
        ids.append("extra")
        self.assertEqual(2, ring.size)

    def test_size(self):
        ring = FocusRing(["x", "y", "z"])
        self.assertEqual(3, ring.size)

    def test_first(self):
        ring = FocusRing(["a", "b", "c"])
        self.assertEqual("a", ring.first())

    def test_last(self):
        ring = FocusRing(["a", "b", "c"])
        self.assertEqual("c", ring.last())

    def test_first_empty_ring_returns_none(self):
        self.assertIsNone(FocusRing([]).first())

    def test_last_empty_ring_returns_none(self):
        self.assertIsNone(FocusRing([]).last())


class TestFocusRingTraversal(unittest.TestCase):
    def setUp(self):
        self.ring = FocusRing(["a", "b", "c"])

    def test_advance_forward(self):
        self.assertEqual("b", self.ring.advance("a", forward=True))

    def test_advance_backward(self):
        self.assertEqual("b", self.ring.advance("c", forward=False))

    def test_advance_from_none_forward_returns_first(self):
        self.assertEqual("a", self.ring.advance(None, forward=True))

    def test_advance_from_none_backward_returns_last(self):
        self.assertEqual("c", self.ring.advance(None, forward=False))

    def test_advance_unknown_id_forward_returns_first(self):
        self.assertEqual("a", self.ring.advance("z", forward=True))

    def test_advance_unknown_id_backward_returns_last(self):
        self.assertEqual("c", self.ring.advance("z", forward=False))

    def test_advance_wraps_at_end_forward(self):
        self.assertEqual("a", self.ring.advance("c", forward=True))

    def test_advance_wraps_at_start_backward(self):
        self.assertEqual("c", self.ring.advance("a", forward=False))

    def test_advance_empty_ring_returns_none(self):
        ring = FocusRing([])
        self.assertIsNone(ring.advance(None))

    def test_trap_wraps_instead_of_escaping(self):
        ring = FocusRing(["x", "y"], trap=True, wrap=False)
        self.assertEqual("x", ring.advance("y", forward=True))
        self.assertEqual("y", ring.advance("x", forward=False))

    def test_no_wrap_no_parent_returns_none_at_boundary(self):
        ring = FocusRing(["a", "b"], wrap=False)
        self.assertIsNone(ring.advance("b", forward=True))
        self.assertIsNone(ring.advance("a", forward=False))

    def test_no_wrap_delegates_to_parent(self):
        parent = FocusRing(["p", "q", "a"])
        child = FocusRing(["a", "b"], wrap=False, parent=parent)
        # advance forward past "b" in child → parent.advance("b", forward=True)
        # "b" not in parent → parent returns first = "p"
        self.assertEqual("p", child.advance("b", forward=True))

    def test_parent_delegation_backward(self):
        parent = FocusRing(["x", "a", "y"])
        child = FocusRing(["a", "b"], wrap=False, parent=parent)
        # advance backward past "a" → parent.advance("a", forward=False) → "x"
        self.assertEqual("x", child.advance("a", forward=False))

    def test_first_focusable(self):
        ring = FocusRing(["a", "b"])
        self.assertEqual("a", ring.first_focusable())

    def test_first_focusable_empty_returns_none(self):
        self.assertIsNone(FocusRing([]).first_focusable())


class TestFocusRingMutation(unittest.TestCase):
    def test_append_adds_to_end(self):
        ring = FocusRing(["a", "b"])
        ring.append("c")
        self.assertEqual(["a", "b", "c"], ring.node_ids)

    def test_append_duplicate_ignored(self):
        ring = FocusRing(["a", "b"])
        ring.append("a")
        self.assertEqual(2, ring.size)

    def test_insert_after(self):
        ring = FocusRing(["a", "c"])
        ring.insert("b", after="a")
        self.assertEqual(["a", "b", "c"], ring.node_ids)

    def test_insert_before(self):
        ring = FocusRing(["a", "c"])
        ring.insert("b", before="c")
        self.assertEqual(["a", "b", "c"], ring.node_ids)

    def test_insert_no_anchor_appends(self):
        ring = FocusRing(["a"])
        ring.insert("b")
        self.assertEqual(["a", "b"], ring.node_ids)

    def test_insert_duplicate_ignored(self):
        ring = FocusRing(["a", "b"])
        ring.insert("a", after="b")
        self.assertEqual(2, ring.size)

    def test_remove_existing(self):
        ring = FocusRing(["a", "b", "c"])
        self.assertTrue(ring.remove("b"))
        self.assertEqual(["a", "c"], ring.node_ids)

    def test_remove_missing_returns_false(self):
        ring = FocusRing(["a"])
        self.assertFalse(ring.remove("z"))

    def test_clear(self):
        ring = FocusRing(["a", "b"])
        ring.clear()
        self.assertEqual(0, ring.size)

    def test_replace(self):
        ring = FocusRing(["a", "b"])
        ring.replace(["x", "y", "z"])
        self.assertEqual(["x", "y", "z"], ring.node_ids)


# ===========================================================================
# FocusScope
# ===========================================================================


class TestFocusScope(unittest.TestCase):
    def test_scope_id_from_argument(self):
        node = _FakeNode("panel")
        scope = FocusScope(node, scope_id="my-scope")
        self.assertEqual("my-scope", scope.scope_id)

    def test_scope_id_auto_generated(self):
        node = _FakeNode("panel")
        scope = FocusScope(node)
        self.assertIn("scope:", scope.scope_id)

    def test_initially_not_active(self):
        scope = FocusScope(_FakeNode("x"))
        self.assertFalse(scope.active)

    def test_root_reference(self):
        node = _FakeNode("dialog")
        scope = FocusScope(node)
        self.assertIs(node, scope.root)


# ===========================================================================
# FocusScopeManager
# ===========================================================================


class TestFocusScopeManager(unittest.TestCase):
    def setUp(self):
        self.fm = _FakeFocusManager()
        self.mgr = FocusScopeManager(self.fm)

    def test_initial_depth_is_zero(self):
        self.assertEqual(0, self.mgr.depth)

    def test_initial_not_constrained(self):
        self.assertFalse(self.mgr.is_constrained)

    def test_active_scope_none_when_empty(self):
        self.assertIsNone(self.mgr.active_scope)

    def test_push_returns_scope(self):
        node = _FakeNode("modal")
        scope = self.mgr.push(node, scope_id="test")
        self.assertIsInstance(scope, FocusScope)

    def test_push_activates_scope(self):
        node = _FakeNode("modal")
        scope = self.mgr.push(node)
        self.assertTrue(scope.active)

    def test_push_increments_depth(self):
        self.mgr.push(_FakeNode("a"))
        self.assertEqual(1, self.mgr.depth)

    def test_push_sets_constrained(self):
        self.mgr.push(_FakeNode("a"))
        self.assertTrue(self.mgr.is_constrained)

    def test_active_scope_is_innermost(self):
        self.mgr.push(_FakeNode("outer"), scope_id="outer")
        inner = self.mgr.push(_FakeNode("inner"), scope_id="inner")
        self.assertIs(inner, self.mgr.active_scope)

    def test_push_syncs_to_focus_manager(self):
        node = _FakeNode("x")
        self.mgr.push(node)
        self.assertEqual([node], self.fm._scope_stack)

    def test_pop_removes_scope(self):
        node = _FakeNode("a")
        scope = self.mgr.push(node)
        result = self.mgr.pop(scope)
        self.assertTrue(result)
        self.assertEqual(0, self.mgr.depth)

    def test_pop_deactivates_scope(self):
        node = _FakeNode("a")
        scope = self.mgr.push(node)
        self.mgr.pop(scope)
        self.assertFalse(scope.active)

    def test_pop_missing_returns_false(self):
        unrelated = FocusScope(_FakeNode("z"))
        self.assertFalse(self.mgr.pop(unrelated))

    def test_pop_syncs_focus_manager(self):
        node = _FakeNode("a")
        scope = self.mgr.push(node)
        self.mgr.pop(scope)
        self.assertEqual([], self.fm._scope_stack)

    def test_pop_non_top_scope(self):
        outer = self.mgr.push(_FakeNode("outer"))
        inner = self.mgr.push(_FakeNode("inner"))
        self.mgr.pop(outer)   # remove non-top
        self.assertEqual(1, self.mgr.depth)
        self.assertIs(inner, self.mgr.active_scope)

    def test_pop_top_returns_innermost(self):
        self.mgr.push(_FakeNode("outer"))
        inner = self.mgr.push(_FakeNode("inner"))
        popped = self.mgr.pop_top()
        self.assertIs(inner, popped)
        self.assertEqual(1, self.mgr.depth)

    def test_pop_top_empty_returns_none(self):
        self.assertIsNone(self.mgr.pop_top())

    def test_pop_all_clears_stack(self):
        self.mgr.push(_FakeNode("a"))
        self.mgr.push(_FakeNode("b"))
        self.mgr.pop_all()
        self.assertEqual(0, self.mgr.depth)
        self.assertFalse(self.mgr.is_constrained)

    def test_pop_all_deactivates_all_scopes(self):
        s1 = self.mgr.push(_FakeNode("a"))
        s2 = self.mgr.push(_FakeNode("b"))
        self.mgr.pop_all()
        self.assertFalse(s1.active)
        self.assertFalse(s2.active)

    def test_pop_all_syncs_focus_manager(self):
        self.mgr.push(_FakeNode("a"))
        self.mgr.push(_FakeNode("b"))
        self.mgr.pop_all()
        self.assertEqual([], self.fm._scope_stack)

    def test_stacked_scopes_sync_in_order(self):
        a = _FakeNode("a")
        b = _FakeNode("b")
        self.mgr.push(a)
        self.mgr.push(b)
        self.assertEqual([a, b], self.fm._scope_stack)


if __name__ == "__main__":
    unittest.main()
