"""Tests for FocusManager query APIs: has_focus, focusable_count."""
import unittest

from pygame import Rect

from gui.core.focus_manager import FocusManager
from gui.core.scene import Scene
from gui.core.ui_node import UiNode


def _node(control_id: str = "n", tab_index: int = 0) -> UiNode:
    n = UiNode(control_id, Rect(0, 0, 100, 100))
    n.tab_index = tab_index
    return n


def _hidden_node(control_id: str = "hidden") -> UiNode:
    n = _node(control_id)
    n._visible = False
    return n


def _disabled_node(control_id: str = "disabled") -> UiNode:
    n = _node(control_id)
    n._enabled = False
    return n


def _non_focusable(control_id: str = "nf") -> UiNode:
    n = UiNode(control_id, Rect(0, 0, 100, 100))
    n.tab_index = -1
    return n


def _scene_with(*nodes) -> Scene:
    s = Scene()
    for node in nodes:
        s.add(node)
    return s


class HasFocusTests(unittest.TestCase):

    def test_has_focus_false_initially(self) -> None:
        fm = FocusManager()
        self.assertFalse(fm.has_focus)

    def test_has_focus_true_after_set_focus(self) -> None:
        fm = FocusManager()
        n = _node("a")
        fm.set_focus(n)
        self.assertTrue(fm.has_focus)

    def test_has_focus_false_after_clear_focus(self) -> None:
        fm = FocusManager()
        n = _node("a")
        fm.set_focus(n)
        fm.clear_focus()
        self.assertFalse(fm.has_focus)

    def test_has_focus_false_after_set_focus_none(self) -> None:
        fm = FocusManager()
        n = _node("a")
        fm.set_focus(n)
        fm.set_focus(None)
        self.assertFalse(fm.has_focus)

    def test_has_focus_true_after_switching_focus(self) -> None:
        fm = FocusManager()
        a, b = _node("a"), _node("b")
        fm.set_focus(a)
        fm.set_focus(b)
        self.assertTrue(fm.has_focus)


class FocusableCountTests(unittest.TestCase):

    def test_focusable_count_zero_for_empty_scene(self) -> None:
        fm = FocusManager()
        s = _scene_with()
        self.assertEqual(fm.focusable_count(s), 0)

    def test_focusable_count_counts_focusable_nodes(self) -> None:
        fm = FocusManager()
        s = _scene_with(_node("a"), _node("b"), _node("c"))
        self.assertEqual(fm.focusable_count(s), 3)

    def test_focusable_count_excludes_non_focusable(self) -> None:
        fm = FocusManager()
        s = _scene_with(_node("a"), _non_focusable("nf"))
        self.assertEqual(fm.focusable_count(s), 1)

    def test_focusable_count_excludes_hidden(self) -> None:
        fm = FocusManager()
        s = _scene_with(_node("a"), _hidden_node("h"))
        self.assertEqual(fm.focusable_count(s), 1)

    def test_focusable_count_excludes_disabled(self) -> None:
        fm = FocusManager()
        s = _scene_with(_node("a"), _disabled_node("d"))
        self.assertEqual(fm.focusable_count(s), 1)

    def test_focusable_count_scoped_to_window(self) -> None:
        fm = FocusManager()
        # Build two containers; window_a has two children, window_b has one
        window_a = _non_focusable("win_a")
        window_b = _non_focusable("win_b")
        child_a1 = _node("ca1")
        child_a2 = _node("ca2")
        child_b1 = _node("cb1")
        child_a1.parent = window_a
        child_a2.parent = window_a
        window_a.children = [child_a1, child_a2]
        child_b1.parent = window_b
        window_b.children = [child_b1]

        s = _scene_with(window_a, window_b)
        self.assertEqual(fm.focusable_count(s, window=window_a), 2)
        self.assertEqual(fm.focusable_count(s, window=window_b), 1)

    def test_focusable_count_zero_when_all_non_focusable(self) -> None:
        fm = FocusManager()
        s = _scene_with(_non_focusable("a"), _non_focusable("b"))
        self.assertEqual(fm.focusable_count(s), 0)


if __name__ == "__main__":
    unittest.main()
