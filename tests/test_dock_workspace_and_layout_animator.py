"""Tests for DockWorkspace (pure data model) and LayoutAnimator (instant path)."""
import unittest
from types import SimpleNamespace

import pygame
from pygame import Rect

from gui_do.layout.dock_workspace import (
    DockPane, DockSplit, DockTabs, DockWorkspace,
)
from gui_do.layout.layout_animator import LayoutAnimator
from gui_do.layout.constraint_layout import AnchorConstraint, ConstraintLayout
from gui_do.scheduling.tween_manager import TweenManager

pygame.init()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _node(w: int, h: int, x: int = 0, y: int = 0) -> SimpleNamespace:
    """Minimal UiNode stub with rect and invalidate()."""
    n = SimpleNamespace(rect=Rect(x, y, w, h))
    n.invalidate = lambda: None
    return n


# ===========================================================================
# DockPane
# ===========================================================================


class TestDockPane(unittest.TestCase):
    def test_to_dict_kind(self):
        pane = DockPane(pane_id="p1", title="Panel A")
        d = pane.to_dict()
        self.assertEqual("pane", d["kind"])

    def test_to_dict_fields(self):
        pane = DockPane(pane_id="p1", title="Panel A", payload={"x": 1})
        d = pane.to_dict()
        self.assertEqual("p1", d["pane_id"])
        self.assertEqual("Panel A", d["title"])
        self.assertEqual({"x": 1}, d["payload"])

    def test_to_dict_payload_is_copy(self):
        pane = DockPane(pane_id="p1", payload={"a": 1})
        d = pane.to_dict()
        d["payload"]["a"] = 99
        self.assertEqual(1, pane.payload["a"])


# ===========================================================================
# DockTabs
# ===========================================================================


class TestDockTabs(unittest.TestCase):
    def test_active_pane_id_auto_set_from_first_pane(self):
        pane = DockPane(pane_id="p1")
        tabs = DockTabs(tabs_id="t1", panes=[pane])
        self.assertEqual("p1", tabs.active_pane_id)

    def test_active_pane_id_none_when_no_panes(self):
        tabs = DockTabs(tabs_id="t1")
        self.assertIsNone(tabs.active_pane_id)

    def test_add_pane_appends(self):
        tabs = DockTabs(tabs_id="t1")
        pane = DockPane(pane_id="p1")
        tabs.add_pane(pane)
        self.assertIn(pane, tabs.panes)

    def test_add_pane_sets_active_if_none(self):
        tabs = DockTabs(tabs_id="t1")
        pane = DockPane(pane_id="p1")
        tabs.add_pane(pane)
        self.assertEqual("p1", tabs.active_pane_id)

    def test_add_pane_does_not_change_active_if_already_set(self):
        pane1 = DockPane(pane_id="p1")
        pane2 = DockPane(pane_id="p2")
        tabs = DockTabs(tabs_id="t1", panes=[pane1])
        tabs.add_pane(pane2)
        self.assertEqual("p1", tabs.active_pane_id)

    def test_remove_pane_returns_true(self):
        pane = DockPane(pane_id="p1")
        tabs = DockTabs(tabs_id="t1", panes=[pane, DockPane(pane_id="p2")])
        self.assertTrue(tabs.remove_pane("p1"))

    def test_remove_pane_removes_from_list(self):
        pane = DockPane(pane_id="p1")
        tabs = DockTabs(tabs_id="t1", panes=[pane, DockPane(pane_id="p2")])
        tabs.remove_pane("p1")
        ids = [p.pane_id for p in tabs.panes]
        self.assertNotIn("p1", ids)

    def test_remove_pane_missing_returns_false(self):
        tabs = DockTabs(tabs_id="t1")
        self.assertFalse(tabs.remove_pane("nope"))

    def test_remove_active_pane_changes_active(self):
        p1 = DockPane(pane_id="p1")
        p2 = DockPane(pane_id="p2")
        tabs = DockTabs(tabs_id="t1", panes=[p1, p2])
        tabs.remove_pane("p1")
        self.assertEqual("p2", tabs.active_pane_id)

    def test_remove_all_panes_active_becomes_none(self):
        tabs = DockTabs(tabs_id="t1", panes=[DockPane(pane_id="p1")])
        tabs.remove_pane("p1")
        self.assertIsNone(tabs.active_pane_id)

    def test_to_dict_kind(self):
        tabs = DockTabs(tabs_id="t1")
        self.assertEqual("tabs", tabs.to_dict()["kind"])

    def test_to_dict_includes_panes(self):
        tabs = DockTabs(tabs_id="t1", panes=[DockPane(pane_id="p1")])
        d = tabs.to_dict()
        self.assertEqual(1, len(d["panes"]))
        self.assertEqual("p1", d["panes"][0]["pane_id"])


# ===========================================================================
# DockSplit
# ===========================================================================


class TestDockSplit(unittest.TestCase):
    def test_bad_axis_raises(self):
        with self.assertRaises(ValueError):
            DockSplit(axis="diagonal")

    def test_auto_ratios_equal(self):
        a = DockPane(pane_id="a")
        b = DockPane(pane_id="b")
        split = DockSplit(axis="horizontal", children=[a, b])
        self.assertEqual([0.5, 0.5], split.ratios)

    def test_children_ratios_mismatch_raises(self):
        a = DockPane(pane_id="a")
        b = DockPane(pane_id="b")
        with self.assertRaises(ValueError):
            DockSplit(axis="horizontal", children=[a, b], ratios=[1.0])

    def test_to_dict_kind(self):
        split = DockSplit(axis="vertical")
        self.assertEqual("split", split.to_dict()["kind"])

    def test_to_dict_axis(self):
        split = DockSplit(axis="horizontal")
        self.assertEqual("horizontal", split.to_dict()["axis"])


# ===========================================================================
# DockWorkspace
# ===========================================================================


class TestDockWorkspaceEmpty(unittest.TestCase):
    def test_empty_workspace(self):
        ws = DockWorkspace()
        self.assertIsNone(ws.root)

    def test_pane_ids_empty(self):
        ws = DockWorkspace()
        self.assertEqual([], ws.pane_ids())

    def test_find_pane_none(self):
        ws = DockWorkspace()
        self.assertIsNone(ws.find_pane("p1"))

    def test_to_dict_root_none(self):
        ws = DockWorkspace()
        self.assertIsNone(ws.to_dict()["root"])

    def test_from_dict_empty(self):
        ws = DockWorkspace.from_dict({"root": None})
        self.assertIsNone(ws.root)


class TestDockWorkspaceWithPane(unittest.TestCase):
    def setUp(self):
        self.pane = DockPane(pane_id="main", title="Main")
        self.ws = DockWorkspace(root=self.pane)

    def test_pane_ids_returns_sorted(self):
        self.assertEqual(["main"], self.ws.pane_ids())

    def test_find_pane_found(self):
        found = self.ws.find_pane("main")
        self.assertIs(self.pane, found)

    def test_find_pane_missing(self):
        self.assertIsNone(self.ws.find_pane("other"))

    def test_remove_pane_root_becomes_none(self):
        self.ws.remove_pane("main")
        self.assertIsNone(self.ws.root)

    def test_remove_pane_returns_true(self):
        self.assertTrue(self.ws.remove_pane("main"))

    def test_remove_missing_pane_returns_false(self):
        self.assertFalse(self.ws.remove_pane("nope"))


class TestDockWorkspaceWithTabs(unittest.TestCase):
    def _make(self):
        p1 = DockPane(pane_id="p1")
        p2 = DockPane(pane_id="p2")
        tabs = DockTabs(tabs_id="t1", panes=[p1, p2])
        ws = DockWorkspace(root=tabs)
        return ws, p1, p2

    def test_pane_ids(self):
        ws, _, _ = self._make()
        self.assertEqual(["p1", "p2"], ws.pane_ids())

    def test_find_pane_in_tabs(self):
        ws, p1, _ = self._make()
        self.assertIs(p1, ws.find_pane("p1"))

    def test_remove_pane_collapses_single_pane_to_root(self):
        ws, _, _ = self._make()
        ws.remove_pane("p1")
        # Only p2 remains; DockTabs with 1 pane collapses to the pane itself
        self.assertIsInstance(ws.root, DockPane)
        self.assertEqual("p2", ws.root.pane_id)


class TestDockWorkspaceWithSplit(unittest.TestCase):
    def _make(self):
        p1 = DockPane(pane_id="left")
        p2 = DockPane(pane_id="right")
        split = DockSplit(axis="horizontal", children=[p1, p2], ratios=[0.4, 0.6])
        ws = DockWorkspace(root=split)
        return ws, p1, p2

    def test_pane_ids_from_split(self):
        ws, _, _ = self._make()
        self.assertEqual(["left", "right"], ws.pane_ids())

    def test_remove_pane_from_split_collapses(self):
        ws, _, _ = self._make()
        ws.remove_pane("left")
        self.assertIsInstance(ws.root, DockPane)
        self.assertEqual("right", ws.root.pane_id)

    def test_remove_pane_ratios_renormalized(self):
        p1 = DockPane(pane_id="a")
        p2 = DockPane(pane_id="b")
        p3 = DockPane(pane_id="c")
        split = DockSplit(axis="vertical", children=[p1, p2, p3], ratios=[0.3, 0.3, 0.4])
        ws = DockWorkspace(root=split)
        ws.remove_pane("a")
        # Remaining ratios should sum to 1.0
        total = sum(ws.root.ratios)
        self.assertAlmostEqual(1.0, total, places=5)


class TestDockWorkspaceRoundtrip(unittest.TestCase):
    def _roundtrip(self, ws):
        return DockWorkspace.from_dict(ws.to_dict())

    def test_pane_roundtrip(self):
        ws = DockWorkspace(root=DockPane(pane_id="p1", title="Panel", payload={"k": "v"}))
        ws2 = self._roundtrip(ws)
        self.assertEqual("p1", ws2.root.pane_id)
        self.assertEqual("Panel", ws2.root.title)
        self.assertEqual({"k": "v"}, ws2.root.payload)

    def test_tabs_roundtrip(self):
        panes = [DockPane(pane_id="p1"), DockPane(pane_id="p2")]
        ws = DockWorkspace(root=DockTabs(tabs_id="t1", panes=panes))
        ws2 = self._roundtrip(ws)
        self.assertIsInstance(ws2.root, DockTabs)
        self.assertEqual(["p1", "p2"], ws2.pane_ids())

    def test_split_roundtrip(self):
        p1 = DockPane(pane_id="left")
        p2 = DockPane(pane_id="right")
        split = DockSplit(axis="horizontal", children=[p1, p2], ratios=[0.4, 0.6])
        ws = DockWorkspace(root=split)
        ws2 = self._roundtrip(ws)
        self.assertIsInstance(ws2.root, DockSplit)
        self.assertEqual("horizontal", ws2.root.axis)
        self.assertAlmostEqual(0.4, ws2.root.ratios[0])
        self.assertAlmostEqual(0.6, ws2.root.ratios[1])

    def test_from_dict_unknown_kind_raises(self):
        with self.assertRaises(ValueError):
            DockWorkspace.from_dict({"root": {"kind": "unknown"}})


# ===========================================================================
# LayoutAnimator — instant path (duration=0)
# ===========================================================================


class TestLayoutAnimatorInstant(unittest.TestCase):
    """With duration=0 the animator applies rects immediately without tweening."""

    def _make_animator(self):
        tweens = TweenManager()
        return LayoutAnimator(tweens, duration=0.0)

    def test_apply_targets_moves_node(self):
        animator = self._make_animator()
        n = _node(50, 50, x=10, y=10)
        animator.apply_targets([(n, Rect(100, 200, 50, 50))])
        self.assertEqual(100, n.rect.x)
        self.assertEqual(200, n.rect.y)

    def test_apply_targets_resizes_node(self):
        animator = self._make_animator()
        n = _node(50, 50)
        animator.apply_targets([(n, Rect(0, 0, 200, 100))])
        self.assertEqual(200, n.rect.width)
        self.assertEqual(100, n.rect.height)

    def test_apply_targets_multiple_nodes(self):
        animator = self._make_animator()
        a = _node(50, 50)
        b = _node(50, 50)
        animator.apply_targets([(a, Rect(0, 0, 100, 100)), (b, Rect(200, 0, 100, 100))])
        self.assertEqual(0, a.rect.x)
        self.assertEqual(200, b.rect.x)

    def test_apply_targets_empty_is_no_op(self):
        animator = self._make_animator()
        animator.apply_targets([])   # should not raise

    def test_apply_constraint_moves_node(self):
        animator = self._make_animator()
        layout = ConstraintLayout()
        n = _node(0, 0, x=0, y=0)
        layout.add(n, AnchorConstraint(left=30, right=0, top=10, bottom=0))
        parent = Rect(0, 0, 400, 300)
        animator.apply_constraint(layout, parent)
        self.assertEqual(30, n.rect.left)
        self.assertEqual(10, n.rect.top)

    def test_cancel_clears_handles(self):
        tweens = TweenManager()
        animator = LayoutAnimator(tweens, duration=0.5)
        n = _node(50, 50, x=0, y=0)
        # With duration=0.5 tweens are registered (not instant)
        animator.apply_targets([(n, Rect(100, 0, 50, 50))])
        # cancel should clear them
        animator.cancel()
        self.assertFalse(animator.is_animating)

    def test_is_animating_false_when_no_tweens(self):
        animator = self._make_animator()
        self.assertFalse(animator.is_animating)

    def test_duration_stored(self):
        tweens = TweenManager()
        animator = LayoutAnimator(tweens, duration=0.5)
        self.assertAlmostEqual(0.5, animator._duration)

    def test_negative_duration_clamped_to_zero(self):
        tweens = TweenManager()
        animator = LayoutAnimator(tweens, duration=-1.0)
        self.assertEqual(0.0, animator._duration)


if __name__ == "__main__":
    unittest.main()
