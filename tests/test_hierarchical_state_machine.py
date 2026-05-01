"""Tests for HierarchicalStateMachine — composite, history, and parallel states."""
import unittest

from gui_do.state.hierarchical_state_machine import HierarchicalStateMachine
from gui_do.state.state_machine import StateMachine


# ===========================================================================
# Baseline — flat StateMachine API still works in HierarchicalStateMachine
# ===========================================================================


class TestHierarchicalFlatApi(unittest.TestCase):
    def test_initial_state(self):
        hsm = HierarchicalStateMachine("idle")
        self.assertEqual("idle", hsm.current.value)

    def test_add_state_and_trigger(self):
        hsm = HierarchicalStateMachine("idle")
        hsm.add_state("active")
        hsm.add_transition("idle", "active", trigger="start")
        self.assertTrue(hsm.trigger("start"))
        self.assertEqual("active", hsm.current.value)

    def test_no_match_returns_false(self):
        hsm = HierarchicalStateMachine("idle")
        self.assertFalse(hsm.trigger("unknown"))


# ===========================================================================
# Composite state
# ===========================================================================


class TestCompositeState(unittest.TestCase):
    def _build(self):
        """outer: idle -> active (composite) -> idle"""
        inner = StateMachine("sub_a")
        inner.add_state("sub_b")
        inner.add_transition("sub_a", "sub_b", trigger="next")

        outer = HierarchicalStateMachine("idle")
        outer.add_composite("active", inner, initial="sub_a")
        outer.add_transition("idle", "active", trigger="go")
        outer.add_transition("active", "idle", trigger="back")
        return outer, inner

    def test_sub_machine_registered(self):
        outer, inner = self._build()
        self.assertIs(inner, outer.sub_machine("active"))

    def test_entering_composite_resets_to_initial(self):
        outer, inner = self._build()
        # Advance inner manually first, then re-enter
        outer.trigger("go")
        inner.trigger("next")
        self.assertEqual("sub_b", outer.sub_current("active"))
        outer.trigger("back")
        outer.trigger("go")
        # Should reset to sub_a (non-history)
        self.assertEqual("sub_a", outer.sub_current("active"))

    def test_sub_current_returns_sub_state(self):
        outer, inner = self._build()
        outer.trigger("go")
        self.assertEqual("sub_a", outer.sub_current("active"))

    def test_sub_trigger_fires_in_sub_machine(self):
        outer, inner = self._build()
        outer.trigger("go")
        result = outer.sub_trigger("active", "next")
        self.assertTrue(result)
        self.assertEqual("sub_b", outer.sub_current("active"))

    def test_sub_current_unknown_state_returns_none(self):
        outer, _ = self._build()
        self.assertIsNone(outer.sub_current("nonexistent"))

    def test_sub_trigger_unknown_state_returns_false(self):
        outer, _ = self._build()
        self.assertFalse(outer.sub_trigger("nonexistent", "next"))


# ===========================================================================
# History state
# ===========================================================================


class TestHistoryState(unittest.TestCase):
    def _build(self):
        inner = StateMachine("page1")
        inner.add_state("page2")
        inner.add_transition("page1", "page2", trigger="next")

        outer = HierarchicalStateMachine("home")
        outer.add_history("wizard", inner, initial="page1")
        outer.add_transition("home", "wizard", trigger="open")
        outer.add_transition("wizard", "home", trigger="close")
        return outer, inner

    def test_initial_entry_uses_initial(self):
        outer, _ = self._build()
        outer.trigger("open")
        self.assertEqual("page1", outer.sub_current("wizard"))

    def test_history_resumed_on_re_entry(self):
        outer, _ = self._build()
        outer.trigger("open")
        outer.sub_trigger("wizard", "next")   # advance to page2
        outer.trigger("close")                # exit (saves page2 in history)
        outer.trigger("open")                 # re-enter
        self.assertEqual("page2", outer.sub_current("wizard"))


# ===========================================================================
# Parallel regions
# ===========================================================================


class TestParallelRegions(unittest.TestCase):
    def test_parallel_regions_registered(self):
        r1 = StateMachine("r1_idle")
        r2 = StateMachine("r2_idle")
        outer = HierarchicalStateMachine("idle")
        outer.add_parallel("running", [r1, r2])
        self.assertEqual(2, len(outer.parallel_regions("running")))

    def test_parallel_regions_unknown_returns_empty(self):
        outer = HierarchicalStateMachine("idle")
        self.assertEqual([], outer.parallel_regions("nonexistent"))

    def test_trigger_parallel_fires_all(self):
        r1 = StateMachine("a")
        r1.add_state("b")
        r1.add_transition("a", "b", trigger="ev")
        r2 = StateMachine("x")
        r2.add_state("y")
        r2.add_transition("x", "y", trigger="ev")

        outer = HierarchicalStateMachine("idle")
        outer.add_state("running")
        outer.add_parallel("running", [r1, r2])
        outer.add_transition("idle", "running", trigger="go")
        outer.trigger("go")

        results = outer.trigger_parallel("running", "ev")
        self.assertEqual([True, True], results)
        self.assertEqual("b", r1.current.value)
        self.assertEqual("y", r2.current.value)


if __name__ == "__main__":
    unittest.main()
