"""Tests for OverlayManager (Feature 2)."""
import unittest
from unittest.mock import MagicMock, call

import pygame
from pygame import Rect

from gui_do.core.overlay_manager import OverlayManager, OverlayHandle
from gui_do.controls.overlay_panel_control import OverlayPanelControl
from gui_do.core.gui_event import EventType, GuiEvent


def _panel(x=50, y=50, w=100, h=80) -> OverlayPanelControl:
    p = OverlayPanelControl("ov", Rect(x, y, w, h))
    p.visible = True
    p.enabled = True
    return p


def _make_app():
    app = MagicMock()
    app.focus = MagicMock()
    return app


def _key_esc() -> GuiEvent:
    return GuiEvent(kind=EventType.KEY_DOWN, type=0, key=pygame.K_ESCAPE, mod=0)


def _mouse_down(x, y) -> GuiEvent:
    return GuiEvent(kind=EventType.MOUSE_BUTTON_DOWN, type=0, pos=(x, y), button=1)


class TestShowRegistersOverlay(unittest.TestCase):
    def test_show_registers_overlay(self) -> None:
        mgr = OverlayManager()
        panel = _panel()
        handle = mgr.show("a", panel)
        self.assertIsInstance(handle, OverlayHandle)
        self.assertTrue(mgr.has_overlay("a"))


class TestHideRemovesOverlay(unittest.TestCase):
    def test_hide_removes_overlay(self) -> None:
        mgr = OverlayManager()
        mgr.show("a", _panel())
        result = mgr.hide("a")
        self.assertTrue(result)
        self.assertFalse(mgr.has_overlay("a"))


class TestHideUnknownReturnsFalse(unittest.TestCase):
    def test_hide_unknown_returns_false(self) -> None:
        mgr = OverlayManager()
        self.assertFalse(mgr.hide("x"))


class TestHideAllClearsAll(unittest.TestCase):
    def test_hide_all_clears_all(self) -> None:
        mgr = OverlayManager()
        for i in range(3):
            mgr.show(str(i), _panel())
        count = mgr.hide_all()
        self.assertEqual(count, 3)
        self.assertEqual(mgr.overlay_count(), 0)


class TestOnDismissCalledOnHide(unittest.TestCase):
    def test_on_dismiss_called_on_hide(self) -> None:
        dismissed = []
        mgr = OverlayManager()
        mgr.show("a", _panel(), on_dismiss=lambda: dismissed.append(1))
        mgr.hide("a")
        self.assertEqual(dismissed, [1])


class TestHandleIsOpenProperty(unittest.TestCase):
    def test_handle_is_open_property(self) -> None:
        mgr = OverlayManager()
        handle = mgr.show("a", _panel())
        self.assertTrue(handle.is_open)
        handle.dismiss()
        self.assertFalse(handle.is_open)


class TestEscapeDismissesTopOverlay(unittest.TestCase):
    def test_escape_key_dismisses_topmost_overlay(self) -> None:
        mgr = OverlayManager()
        mgr.show("a", _panel(), dismiss_on_escape=True)
        consumed = mgr.route_event(_key_esc(), _make_app())
        self.assertTrue(consumed)
        self.assertFalse(mgr.has_overlay("a"))


class TestEscapeNotConsumedIfNoEscapeDismissible(unittest.TestCase):
    def test_escape_not_consumed_if_no_dismiss_on_escape_overlay(self) -> None:
        mgr = OverlayManager()
        mgr.show("a", _panel(), dismiss_on_escape=False)
        consumed = mgr.route_event(_key_esc(), _make_app())
        self.assertFalse(consumed)


class TestOutsideClickDismissesButDoesNotConsume(unittest.TestCase):
    def test_outside_click_dismisses_overlay_but_does_not_consume(self) -> None:
        mgr = OverlayManager()
        mgr.show("a", _panel(50, 50, 100, 80), dismiss_on_outside_click=True)
        # Click outside the overlay rect
        consumed = mgr.route_event(_mouse_down(5, 5), _make_app())
        self.assertFalse(consumed)
        self.assertFalse(mgr.has_overlay("a"))


class TestInsideClickConsumed(unittest.TestCase):
    def test_inside_click_consumed_by_overlay(self) -> None:
        mgr = OverlayManager()
        panel = _panel(50, 50, 100, 80)
        # Make panel consume the event
        panel.handle_routed_event = MagicMock(return_value=True)
        mgr.show("a", panel, dismiss_on_outside_click=True)
        consumed = mgr.route_event(_mouse_down(75, 75), _make_app())
        self.assertTrue(consumed)
        self.assertTrue(mgr.has_overlay("a"))  # not dismissed by inside click


class TestPointInAnyOverlay(unittest.TestCase):
    def test_point_in_any_overlay(self) -> None:
        mgr = OverlayManager()
        mgr.show("a", _panel(50, 50, 100, 80))
        self.assertTrue(mgr.point_in_any_overlay((75, 75)))
        self.assertFalse(mgr.point_in_any_overlay((5, 5)))


class TestShowSameIdReplaces(unittest.TestCase):
    def test_show_same_id_replaces_existing(self) -> None:
        mgr = OverlayManager()
        mgr.show("a", _panel())
        mgr.show("a", _panel())  # replaces
        self.assertEqual(mgr.overlay_count(), 1)


class TestAnchorPositionBelowLeft(unittest.TestCase):
    def test_anchor_position_below_left(self) -> None:
        target = Rect(100, 100, 80, 30)
        pos = OverlayManager.anchor_position((60, 40), target, side="below", align="left")
        self.assertEqual(pos, (100, 130))


class TestAnchorPositionClampsToScreen(unittest.TestCase):
    def test_anchor_position_clamps_to_screen(self) -> None:
        screen = Rect(0, 0, 200, 200)
        target = Rect(170, 100, 80, 30)
        pos = OverlayManager.anchor_position((60, 40), target, side="below", align="left", screen_rect=screen)
        self.assertLessEqual(pos[0] + 60, 200)


class TestIsOverlayOnOverlayPanelControl(unittest.TestCase):
    def test_is_overlay_returns_true_for_overlay_panel(self) -> None:
        panel = _panel()
        self.assertTrue(panel.is_overlay())

    def test_is_overlay_returns_false_for_base_node(self) -> None:
        from gui_do.core.ui_node import UiNode
        node = UiNode("n", Rect(0, 0, 10, 10))
        self.assertFalse(node.is_overlay())


if __name__ == "__main__":
    unittest.main()
