"""Tests for FocusRing — bounded focus traversal ring."""
import unittest

from gui_do.focus.focus_ring import FocusRing


# ===========================================================================
# FocusRing — initial state
# ===========================================================================


class TestFocusRingInitial(unittest.TestCase):
    def test_node_ids_stored(self):
        r = FocusRing(["a", "b", "c"])
        self.assertEqual(["a", "b", "c"], r.node_ids)

    def test_size(self):
        r = FocusRing(["x", "y"])
        self.assertEqual(2, r.size)

    def test_contains_true(self):
        r = FocusRing(["a", "b"])
        self.assertTrue(r.contains("a"))

    def test_contains_false(self):
        r = FocusRing(["a", "b"])
        self.assertFalse(r.contains("z"))

    def test_first(self):
        r = FocusRing(["a", "b", "c"])
        self.assertEqual("a", r.first())

    def test_last(self):
        r = FocusRing(["a", "b", "c"])
        self.assertEqual("c", r.last())

    def test_empty_first_none(self):
        r = FocusRing([])
        self.assertIsNone(r.first())

    def test_empty_last_none(self):
        r = FocusRing([])
        self.assertIsNone(r.last())


# ===========================================================================
# FocusRing — advance (forward)
# ===========================================================================


class TestFocusRingAdvance(unittest.TestCase):
    def test_advance_forward(self):
        r = FocusRing(["a", "b", "c"])
        self.assertEqual("b", r.advance("a", forward=True))

    def test_advance_backward(self):
        r = FocusRing(["a", "b", "c"])
        self.assertEqual("b", r.advance("c", forward=False))

    def test_advance_wraps_forward(self):
        r = FocusRing(["a", "b", "c"], wrap=True)
        self.assertEqual("a", r.advance("c", forward=True))

    def test_advance_wraps_backward(self):
        r = FocusRing(["a", "b", "c"], wrap=True)
        self.assertEqual("c", r.advance("a", forward=False))

    def test_advance_no_wrap_returns_none(self):
        r = FocusRing(["a", "b", "c"], wrap=False)
        self.assertIsNone(r.advance("c", forward=True))

    def test_advance_none_returns_first(self):
        r = FocusRing(["a", "b", "c"])
        self.assertEqual("a", r.advance(None, forward=True))

    def test_advance_none_backward_returns_last(self):
        r = FocusRing(["a", "b", "c"])
        self.assertEqual("c", r.advance(None, forward=False))

    def test_advance_unknown_id_returns_first(self):
        r = FocusRing(["a", "b", "c"])
        self.assertEqual("a", r.advance("unknown", forward=True))

    def test_advance_empty_returns_none(self):
        r = FocusRing([])
        self.assertIsNone(r.advance("a", forward=True))


# ===========================================================================
# FocusRing — trap mode
# ===========================================================================


class TestFocusRingTrap(unittest.TestCase):
    def test_trap_wraps_forward(self):
        r = FocusRing(["a", "b", "c"], trap=True, wrap=False)
        # Even with wrap=False, trap wraps
        self.assertEqual("a", r.advance("c", forward=True))

    def test_trap_wraps_backward(self):
        r = FocusRing(["a", "b", "c"], trap=True, wrap=False)
        self.assertEqual("c", r.advance("a", forward=False))


# ===========================================================================
# FocusRing — parent delegation
# ===========================================================================


class TestFocusRingParent(unittest.TestCase):
    def test_delegates_to_parent_at_boundary(self):
        parent = FocusRing(["p1", "p2"], wrap=True)
        child = FocusRing(["c1", "c2"], wrap=False, parent=parent)
        # At end of child ring with wrap=False → delegates to parent with current_id="c2"
        # parent doesn't have "c2", so returns first
        result = child.advance("c2", forward=True)
        self.assertIsNotNone(result)


# ===========================================================================
# FocusRing — dynamic mutation
# ===========================================================================


class TestFocusRingMutation(unittest.TestCase):
    def test_append(self):
        r = FocusRing(["a", "b"])
        r.append("c")
        self.assertIn("c", r.node_ids)

    def test_append_duplicate_no_change(self):
        r = FocusRing(["a", "b"])
        r.append("a")
        self.assertEqual(2, r.size)

    def test_insert_after(self):
        r = FocusRing(["a", "b", "c"])
        r.insert("x", after="a")
        self.assertEqual(["a", "x", "b", "c"], r.node_ids)

    def test_insert_before(self):
        r = FocusRing(["a", "b", "c"])
        r.insert("x", before="b")
        self.assertEqual(["a", "x", "b", "c"], r.node_ids)

    def test_remove_existing(self):
        r = FocusRing(["a", "b", "c"])
        result = r.remove("b")
        self.assertTrue(result)
        self.assertEqual(["a", "c"], r.node_ids)

    def test_remove_missing_returns_false(self):
        r = FocusRing(["a", "b"])
        result = r.remove("z")
        self.assertFalse(result)

    def test_clear(self):
        r = FocusRing(["a", "b", "c"])
        r.clear()
        self.assertEqual(0, r.size)

    def test_replace(self):
        r = FocusRing(["a", "b"])
        r.replace(["x", "y", "z"])
        self.assertEqual(["x", "y", "z"], r.node_ids)

    def test_first_focusable(self):
        r = FocusRing(["a", "b"])
        self.assertEqual("a", r.first_focusable())


if __name__ == "__main__":
    unittest.main()
