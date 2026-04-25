"""Tests for FocusManager.focused_control_id and set_focus_by_id."""
import unittest

from pygame import Rect

from gui.core.focus_manager import FocusManager
from gui.core.scene import Scene
from gui.core.ui_node import UiNode


def _node(control_id: str, tab_index: int = 0, visible: bool = True, enabled: bool = True) -> UiNode:
    n = UiNode(control_id, Rect(0, 0, 50, 20))
    n.set_tab_index(tab_index)
    n._visible = visible
    n._enabled = enabled
    return n


class _HoverNode(UiNode):
    def __init__(self, control_id: str, rect: Rect, tab_index: int) -> None:
        super().__init__(control_id, rect)
        self.set_tab_index(tab_index)
        self.hovered = False

    def reconcile_hover(self, wants_hover: bool) -> None:
        self.hovered = wants_hover


class FocusedControlIdTests(unittest.TestCase):

    def setUp(self) -> None:
        self.fm = FocusManager()

    def test_focused_control_id_none_when_no_focus(self) -> None:
        self.assertIsNone(self.fm.focused_control_id)

    def test_focused_control_id_returns_id_of_focused_node(self) -> None:
        node = _node("btn_ok")
        # Directly set focus (bypassing _set_focused contract for unit simplicity)
        self.fm._focused_node = node
        self.assertEqual(self.fm.focused_control_id, "btn_ok")

    def test_focused_control_id_none_after_clear_focus(self) -> None:
        node = _node("x")
        node._focused = False  # satisfy _set_focused no-op guard
        self.fm.set_focus(node)
        self.fm.clear_focus()
        self.assertIsNone(self.fm.focused_control_id)

    def test_focused_control_id_updates_after_focus_change(self) -> None:
        a = _node("a")
        b = _node("b")
        a._focused = False
        b._focused = False
        self.fm.set_focus(a)
        self.assertEqual(self.fm.focused_control_id, "a")
        self.fm.set_focus(b)
        self.assertEqual(self.fm.focused_control_id, "b")


class SetFocusByIdTests(unittest.TestCase):

    def _scene_with(self, *nodes) -> Scene:
        scene = Scene()
        for node in nodes:
            scene.add(node)
        return scene

    def setUp(self) -> None:
        self.fm = FocusManager()

    def test_set_focus_by_id_returns_true_and_focuses_matching_node(self) -> None:
        node = _node("btn_save")
        scene = self._scene_with(node)

        result = self.fm.set_focus_by_id(scene, "btn_save")

        self.assertTrue(result)
        self.assertIs(self.fm.focused_node, node)

    def test_set_focus_by_id_returns_false_for_missing_id(self) -> None:
        scene = self._scene_with(_node("btn_cancel"))
        result = self.fm.set_focus_by_id(scene, "nonexistent")
        self.assertFalse(result)
        self.assertIsNone(self.fm.focused_node)

    def test_set_focus_by_id_returns_false_for_hidden_node(self) -> None:
        node = _node("btn_hidden", visible=False)
        scene = self._scene_with(node)
        result = self.fm.set_focus_by_id(scene, "btn_hidden")
        self.assertFalse(result)
        self.assertIsNone(self.fm.focused_node)

    def test_set_focus_by_id_returns_false_for_disabled_node(self) -> None:
        node = _node("btn_disabled", enabled=False)
        scene = self._scene_with(node)
        result = self.fm.set_focus_by_id(scene, "btn_disabled")
        self.assertFalse(result)
        self.assertIsNone(self.fm.focused_node)

    def test_set_focus_by_id_returns_false_for_non_focusable_node(self) -> None:
        node = _node("lbl", tab_index=-1)  # tab_index < 0 → non-focusable
        scene = self._scene_with(node)
        result = self.fm.set_focus_by_id(scene, "lbl")
        self.assertFalse(result)
        self.assertIsNone(self.fm.focused_node)

    def test_set_focus_by_id_focuses_descendant_node(self) -> None:
        parent = _node("panel", tab_index=-1)
        child = _node("inner_btn")
        parent.children.append(child)
        child.parent = parent
        scene = self._scene_with(parent)

        result = self.fm.set_focus_by_id(scene, "inner_btn")

        self.assertTrue(result)
        self.assertIs(self.fm.focused_node, child)

    def test_set_focus_by_id_updates_focused_control_id(self) -> None:
        node = _node("slider_1")
        scene = self._scene_with(node)
        self.fm.set_focus_by_id(scene, "slider_1")
        self.assertEqual(self.fm.focused_control_id, "slider_1")

    def test_set_focus_by_id_clears_previous_focus_when_switching(self) -> None:
        a = _node("a")
        b = _node("b")
        scene = self._scene_with(a, b)

        self.fm.set_focus_by_id(scene, "a")
        self.assertEqual(self.fm.focused_control_id, "a")

        self.fm.set_focus_by_id(scene, "b")
        self.assertEqual(self.fm.focused_control_id, "b")
        self.assertFalse(a.focused)

    def test_set_focus_by_id_on_empty_scene_returns_false(self) -> None:
        scene = Scene()
        result = self.fm.set_focus_by_id(scene, "anything")
        self.assertFalse(result)

    def test_set_focus_by_id_first_match_wins_when_duplicate_ids(self) -> None:
        first = _node("dup")
        second = _node("dup")
        scene = self._scene_with(first, second)

        result = self.fm.set_focus_by_id(scene, "dup")

        self.assertTrue(result)
        self.assertIs(self.fm.focused_node, first)


class FocusTraversalHoverReconciliationTests(unittest.TestCase):

    def test_cycle_focus_reconciles_stale_hover_to_idle_when_pointer_moved_off(self) -> None:
        fm = FocusManager()
        scene = Scene()
        first = scene.add(_HoverNode("first", Rect(10, 10, 80, 20), tab_index=0))
        scene.add(_HoverNode("second", Rect(10, 40, 80, 20), tab_index=1))

        first.hovered = True

        consumed = fm.cycle_focus(scene, pointer_pos=(300, 200))

        self.assertTrue(consumed)
        self.assertFalse(first.hovered)


if __name__ == "__main__":
    unittest.main()
