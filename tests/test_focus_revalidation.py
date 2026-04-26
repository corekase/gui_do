"""Tests for FocusManager.revalidate_focus — focus moves away from disabled/hidden nodes."""
import unittest

import pygame
from pygame import Rect

from gui_do.app.gui_application import GuiApplication
from gui_do.controls.button_control import ButtonControl
from gui_do.controls.panel_control import PanelControl
from gui_do.controls.window_control import WindowControl
from gui_do.core.focus_manager import FocusManager
from gui_do.core.scene import Scene
from gui_do.core.ui_node import UiNode


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _node(control_id: str = "n", tab_index: int = 0) -> UiNode:
    n = UiNode(control_id, Rect(0, 0, 100, 30))
    n.set_tab_index(tab_index)
    return n


def _scene_with(*nodes) -> Scene:
    scene = Scene()
    for n in nodes:
        scene.add(n)
    return scene


# ---------------------------------------------------------------------------
# Unit tests — FocusManager.revalidate_focus
# ---------------------------------------------------------------------------

class RevalidateFocusNothingToDoTests(unittest.TestCase):

    def setUp(self) -> None:
        self.fm = FocusManager()

    def test_no_op_when_no_focus(self) -> None:
        scene = _scene_with(_node("a"))
        self.fm.revalidate_focus(scene)   # must not raise
        self.assertIsNone(self.fm.focused_node)

    def test_no_op_when_focused_node_still_valid(self) -> None:
        a = _node("a", tab_index=0)
        b = _node("b", tab_index=1)
        scene = _scene_with(a, b)
        self.fm.set_focus(a)
        self.fm.revalidate_focus(scene)
        self.assertIs(self.fm.focused_node, a)


class RevalidateFocusDisabledTests(unittest.TestCase):

    def setUp(self) -> None:
        self.fm = FocusManager()

    def test_clears_focus_when_no_other_candidates(self) -> None:
        a = _node("a", tab_index=0)
        scene = _scene_with(a)
        self.fm.set_focus(a)
        a.enabled = False
        self.fm.revalidate_focus(scene)
        self.assertIsNone(self.fm.focused_node)

    def test_moves_to_next_tab_order_candidate(self) -> None:
        a = _node("a", tab_index=0)
        b = _node("b", tab_index=1)
        c = _node("c", tab_index=2)
        scene = _scene_with(a, b, c)
        self.fm.set_focus(b)
        b.enabled = False
        self.fm.revalidate_focus(scene)
        self.assertIs(self.fm.focused_node, c)

    def test_wraps_to_first_when_no_later_candidate(self) -> None:
        a = _node("a", tab_index=0)
        b = _node("b", tab_index=1)
        scene = _scene_with(a, b)
        self.fm.set_focus(b)
        b.enabled = False
        self.fm.revalidate_focus(scene)
        self.assertIs(self.fm.focused_node, a)

    def test_moves_to_next_when_hidden(self) -> None:
        a = _node("a", tab_index=0)
        b = _node("b", tab_index=1)
        scene = _scene_with(a, b)
        self.fm.set_focus(a)
        a.visible = False
        self.fm.revalidate_focus(scene)
        self.assertIs(self.fm.focused_node, b)

    def test_clears_when_all_disabled(self) -> None:
        a = _node("a", tab_index=0)
        b = _node("b", tab_index=1)
        scene = _scene_with(a, b)
        self.fm.set_focus(a)
        a.enabled = False
        b.enabled = False
        self.fm.revalidate_focus(scene)
        self.assertIsNone(self.fm.focused_node)


class RevalidateFocusWindowScopeTests(unittest.TestCase):
    """When the focused node is inside a WindowControl, search is scoped to that window."""

    def setUp(self) -> None:
        self.fm = FocusManager()

    def _build(self):
        window = WindowControl("win", Rect(0, 0, 400, 300), "Win")
        window.active = True
        btn_a = window.add(ButtonControl("a", Rect(10, 10, 80, 30), "A"))
        btn_b = window.add(ButtonControl("b", Rect(10, 50, 80, 30), "B"))
        btn_a.set_tab_index(0)
        btn_b.set_tab_index(1)
        # A control outside the window
        outside = UiNode("outside", Rect(0, 0, 80, 30))
        outside.set_tab_index(99)
        scene = Scene()
        scene.add(window)
        scene.add(outside)
        return scene, window, btn_a, btn_b, outside

    def test_moves_within_window_not_outside(self) -> None:
        scene, _, btn_a, btn_b, outside = self._build()
        self.fm.set_focus(btn_a)
        btn_a.enabled = False
        self.fm.revalidate_focus(scene)
        self.assertIs(self.fm.focused_node, btn_b)
        self.assertIsNot(self.fm.focused_node, outside)

    def test_clears_when_all_window_buttons_disabled(self) -> None:
        scene, _, btn_a, btn_b, outside = self._build()
        self.fm.set_focus(btn_a)
        btn_a.enabled = False
        btn_b.enabled = False
        self.fm.revalidate_focus(scene)
        # No candidates inside the window → focus cleared, not jumped to outside
        self.assertIsNone(self.fm.focused_node)


# ---------------------------------------------------------------------------
# Integration — GuiApplication.update() calls revalidate_focus
# ---------------------------------------------------------------------------

class GuiApplicationUpdateRevalidatesTests(unittest.TestCase):

    def setUp(self) -> None:
        pygame.init()
        from pygame import Surface
        self.app = GuiApplication(Surface((400, 300)))
        root = self.app.add(PanelControl("root", Rect(0, 0, 400, 300)))
        self.btn_a = root.add(ButtonControl("a", Rect(10, 10, 80, 30), "A"))
        self.btn_b = root.add(ButtonControl("b", Rect(10, 50, 80, 30), "B"))
        self.btn_a.set_tab_index(0)
        self.btn_b.set_tab_index(1)

    def tearDown(self) -> None:
        pygame.quit()

    def test_update_moves_focus_from_disabled_to_next(self) -> None:
        self.app.focus.set_focus(self.btn_a)
        self.btn_a.enabled = False
        self.app.update(0.016)
        self.assertIs(self.app.focus.focused_node, self.btn_b)

    def test_update_clears_focus_when_no_candidates(self) -> None:
        self.app.focus.set_focus(self.btn_a)
        self.btn_a.enabled = False
        self.btn_b.enabled = False
        self.app.update(0.016)
        self.assertIsNone(self.app.focus.focused_node)

    def test_update_leaves_focus_alone_when_still_valid(self) -> None:
        self.app.focus.set_focus(self.btn_a)
        self.app.update(0.016)
        self.assertIs(self.app.focus.focused_node, self.btn_a)


if __name__ == "__main__":
    unittest.main()
