"""Tests for the conformance + API completeness pass:
GuiEvent.is_quit, CanvasEventPacket button helpers, set_on_* callback setters,
LabelControl align, WindowControl.close, PanelControl container queries,
UiEngine.current_fps, ButtonGroupControl.clear_group_registry."""
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

import pygame
from pygame import Rect

from gui_do.core.gui_event import EventType, GuiEvent
from gui_do.controls.canvas_control import CanvasControl, CanvasEventPacket
from gui_do.controls.button_control import ButtonControl
from gui_do.controls.toggle_control import ToggleControl
from gui_do.controls.arrow_box_control import ArrowBoxControl
from gui_do.controls.label_control import LabelControl
from gui_do.controls.window_control import WindowControl
from gui_do.controls.panel_control import PanelControl
from gui_do.controls.button_group_control import ButtonGroupControl
from gui_do.core.ui_node import UiNode
from gui_do.loop.ui_engine import UiEngine


def _rect() -> Rect:
    return Rect(0, 0, 100, 20)


def _make_gui_event(kind: EventType, **kwargs) -> GuiEvent:
    return GuiEvent(kind=kind, type=0, **kwargs)


# ---------------------------------------------------------------------------
# GuiEvent.is_quit
# ---------------------------------------------------------------------------

class GuiEventIsQuitTests(unittest.TestCase):

    def test_is_quit_true_for_quit_kind(self) -> None:
        ev = _make_gui_event(EventType.QUIT)
        self.assertTrue(ev.is_quit())

    def test_is_quit_false_for_key_down(self) -> None:
        ev = _make_gui_event(EventType.KEY_DOWN, key=pygame.K_q)
        self.assertFalse(ev.is_quit())

    def test_is_quit_false_for_mouse_down(self) -> None:
        ev = _make_gui_event(EventType.MOUSE_BUTTON_DOWN, button=1)
        self.assertFalse(ev.is_quit())


# ---------------------------------------------------------------------------
# CanvasEventPacket button helpers
# ---------------------------------------------------------------------------

class CanvasEventPacketButtonHelpersTests(unittest.TestCase):

    def _pkt(self, kind: EventType, button: int = None) -> CanvasEventPacket:
        return CanvasEventPacket(kind=kind, button=button)

    def test_is_left_down_true(self) -> None:
        self.assertTrue(self._pkt(EventType.MOUSE_BUTTON_DOWN, 1).is_left_down())

    def test_is_left_down_false_wrong_button(self) -> None:
        self.assertFalse(self._pkt(EventType.MOUSE_BUTTON_DOWN, 3).is_left_down())

    def test_is_left_up_true(self) -> None:
        self.assertTrue(self._pkt(EventType.MOUSE_BUTTON_UP, 1).is_left_up())

    def test_is_left_up_false_wrong_button(self) -> None:
        self.assertFalse(self._pkt(EventType.MOUSE_BUTTON_UP, 3).is_left_up())

    def test_is_right_down_true(self) -> None:
        self.assertTrue(self._pkt(EventType.MOUSE_BUTTON_DOWN, 3).is_right_down())

    def test_is_right_down_false_left(self) -> None:
        self.assertFalse(self._pkt(EventType.MOUSE_BUTTON_DOWN, 1).is_right_down())

    def test_is_right_up_true(self) -> None:
        self.assertTrue(self._pkt(EventType.MOUSE_BUTTON_UP, 3).is_right_up())

    def test_is_middle_down_true(self) -> None:
        self.assertTrue(self._pkt(EventType.MOUSE_BUTTON_DOWN, 2).is_middle_down())

    def test_is_middle_up_true(self) -> None:
        self.assertTrue(self._pkt(EventType.MOUSE_BUTTON_UP, 2).is_middle_up())

    def test_is_middle_down_false_for_up(self) -> None:
        self.assertFalse(self._pkt(EventType.MOUSE_BUTTON_UP, 2).is_middle_down())


# ---------------------------------------------------------------------------
# set_on_click / set_on_toggle / set_on_activate setters
# ---------------------------------------------------------------------------

class ButtonSetOnClickTests(unittest.TestCase):

    def test_set_on_click_replaces_callback(self) -> None:
        fired = []
        btn = ButtonControl("b", _rect(), "OK")
        btn.set_on_click(lambda: fired.append(1))
        btn._invoke_click()
        self.assertEqual(fired, [1])

    def test_set_on_click_none_removes_callback(self) -> None:
        fired = []
        btn = ButtonControl("b", _rect(), "OK", on_click=lambda: fired.append(1))
        btn.set_on_click(None)
        btn._invoke_click()
        self.assertEqual(fired, [])

    def test_set_on_click_rejects_non_callable(self) -> None:
        btn = ButtonControl("b", _rect(), "OK")
        with self.assertRaises(ValueError):
            btn.set_on_click("not_a_function")


class ToggleSetOnToggleTests(unittest.TestCase):

    def test_set_on_toggle_replaces_callback(self) -> None:
        states = []
        tog = ToggleControl("t", _rect(), "on")
        tog.set_on_toggle(lambda pushed: states.append(pushed))
        tog._commit_toggle()
        self.assertEqual(states, [True])

    def test_set_on_toggle_none_removes_callback(self) -> None:
        states = []
        tog = ToggleControl("t", _rect(), "on", on_toggle=lambda p: states.append(p))
        tog.set_on_toggle(None)
        tog._commit_toggle()
        self.assertEqual(states, [])

    def test_set_on_toggle_rejects_non_callable(self) -> None:
        tog = ToggleControl("t", _rect(), "on")
        with self.assertRaises(ValueError):
            tog.set_on_toggle(42)


class ArrowBoxSetOnActivateTests(unittest.TestCase):

    def test_set_on_activate_replaces_callback(self) -> None:
        fired = []
        arrow = ArrowBoxControl("a", _rect(), 0)
        arrow.set_on_activate(lambda: fired.append(1))
        arrow._invoke()
        self.assertEqual(fired, [1])

    def test_set_on_activate_none_removes_callback(self) -> None:
        fired = []
        arrow = ArrowBoxControl("a", _rect(), 0, on_activate=lambda: fired.append(1))
        arrow.set_on_activate(None)
        arrow._invoke()
        self.assertEqual(fired, [])

    def test_set_on_activate_rejects_non_callable(self) -> None:
        arrow = ArrowBoxControl("a", _rect(), 0)
        with self.assertRaises(ValueError):
            arrow.set_on_activate("bad")


# ---------------------------------------------------------------------------
# LabelControl align
# ---------------------------------------------------------------------------

class LabelAlignTests(unittest.TestCase):

    def test_default_align_is_left(self) -> None:
        lbl = LabelControl("l", _rect(), "hello")
        self.assertEqual(lbl.align, "left")

    def test_align_center_accepted(self) -> None:
        lbl = LabelControl("l", _rect(), "hello", align="center")
        self.assertEqual(lbl.align, "center")

    def test_align_right_accepted(self) -> None:
        lbl = LabelControl("l", _rect(), "hello", align="right")
        self.assertEqual(lbl.align, "right")

    def test_invalid_align_raises(self) -> None:
        with self.assertRaises(ValueError):
            LabelControl("l", _rect(), "hello", align="justify")

    def test_align_setter_updates_value(self) -> None:
        lbl = LabelControl("l", _rect(), "hello")
        lbl.align = "right"
        self.assertEqual(lbl.align, "right")

    def test_align_setter_rejects_invalid(self) -> None:
        lbl = LabelControl("l", _rect(), "hello")
        with self.assertRaises(ValueError):
            lbl.align = "top"

    def test_align_setter_invalidates_node(self) -> None:
        lbl = LabelControl("l", _rect(), "hello")
        lbl._dirty = False
        lbl.align = "center"
        self.assertTrue(lbl._dirty)

    def test_align_setter_no_invalidate_if_same(self) -> None:
        lbl = LabelControl("l", _rect(), "hello")
        lbl._dirty = False
        lbl.align = "left"  # same as default
        self.assertFalse(lbl._dirty)


# ---------------------------------------------------------------------------
# WindowControl.close
# ---------------------------------------------------------------------------

class WindowCloseTests(unittest.TestCase):

    def test_close_sets_visible_false(self) -> None:
        win = WindowControl("w", Rect(0, 0, 200, 150), "Test")
        win._visible = True
        win.close()
        self.assertFalse(win.visible)

    def test_close_on_already_hidden_is_safe(self) -> None:
        win = WindowControl("w", Rect(0, 0, 200, 150), "Test")
        win._visible = False
        win.close()  # must not raise
        self.assertFalse(win.visible)


# ---------------------------------------------------------------------------
# PanelControl container queries
# ---------------------------------------------------------------------------

class PanelContainerQueryTests(unittest.TestCase):

    def _panel(self) -> PanelControl:
        return PanelControl("p", Rect(0, 0, 400, 300))

    def _child(self, cid: str = "c") -> UiNode:
        return UiNode(cid, Rect(0, 0, 50, 50))

    def test_child_count_zero_initially(self) -> None:
        self.assertEqual(self._panel().child_count, 0)

    def test_child_count_after_add(self) -> None:
        p = self._panel()
        p.add(self._child("c1"))
        p.add(self._child("c2"))
        self.assertEqual(p.child_count, 2)

    def test_child_count_after_remove(self) -> None:
        p = self._panel()
        c = self._child()
        p.add(c)
        p.remove(c)
        self.assertEqual(p.child_count, 0)

    def test_has_child_true_for_added(self) -> None:
        p = self._panel()
        c = self._child()
        p.add(c)
        self.assertTrue(p.has_child(c))

    def test_has_child_false_for_stranger(self) -> None:
        p = self._panel()
        self.assertFalse(p.has_child(self._child()))

    def test_has_child_false_after_remove(self) -> None:
        p = self._panel()
        c = self._child()
        p.add(c)
        p.remove(c)
        self.assertFalse(p.has_child(c))

    def test_window_count_zero_for_plain_children(self) -> None:
        p = self._panel()
        p.add(self._child())
        self.assertEqual(p.window_count(), 0)

    def test_window_count_counts_window_children(self) -> None:
        p = self._panel()
        win = WindowControl("w", Rect(0, 0, 100, 80), "W")
        p.add(win)
        p.add(self._child("plain"))
        self.assertEqual(p.window_count(), 1)


# ---------------------------------------------------------------------------
# UiEngine.current_fps
# ---------------------------------------------------------------------------

class UiEngineCurrentFpsTests(unittest.TestCase):

    def test_current_fps_returns_float(self) -> None:
        app = SimpleNamespace(running=False)
        engine = UiEngine(app, target_fps=60)
        self.assertIsInstance(engine.current_fps, float)

    def test_current_fps_zero_before_first_tick(self) -> None:
        app = SimpleNamespace(running=False)
        engine = UiEngine(app, target_fps=60)
        self.assertEqual(engine.current_fps, 0.0)


# ---------------------------------------------------------------------------
# ButtonGroupControl.clear_group_registry
# ---------------------------------------------------------------------------

class ButtonGroupClearRegistryTests(unittest.TestCase):

    def setUp(self) -> None:
        ButtonGroupControl.clear_group_registry()

    def tearDown(self) -> None:
        ButtonGroupControl.clear_group_registry()

    def test_clear_all_removes_all_groups(self) -> None:
        bg = ButtonGroupControl("b1", _rect(), "alpha", "A", selected=True)
        self.assertIn("alpha", ButtonGroupControl._selection_by_group)
        ButtonGroupControl.clear_group_registry()
        self.assertNotIn("alpha", ButtonGroupControl._selection_by_group)

    def test_clear_specific_group_leaves_others(self) -> None:
        ButtonGroupControl("b1", _rect(), "g1", "A", selected=True)
        ButtonGroupControl("b2", _rect(), "g2", "B", selected=True)
        ButtonGroupControl.clear_group_registry(group="g1")
        self.assertNotIn("g1", ButtonGroupControl._selection_by_group)
        self.assertIn("g2", ButtonGroupControl._selection_by_group)

    def test_clear_missing_group_is_idempotent(self) -> None:
        ButtonGroupControl.clear_group_registry(group="nonexistent")  # must not raise


if __name__ == "__main__":
    unittest.main()
