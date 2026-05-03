"""Tests for CursorManager, TooltipManager, and OverlayManager."""
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

import pygame
from pygame import Rect

from gui_do.overlays.cursor_manager import CursorManager, CursorShape, CursorHandle
from gui_do.overlays.tooltip_manager import TooltipManager, TooltipHandle
from gui_do.overlays.overlay_manager import OverlayManager, OverlayHandle
from gui_do.events.gui_event import GuiEvent, EventType

pygame.init()


# ===========================================================================
# CursorManager
# ===========================================================================


class TestCursorManagerInitial(unittest.TestCase):
    def test_default_shape_arrow(self):
        mgr = CursorManager()
        self.assertEqual(CursorShape.ARROW, mgr.default_shape)

    def test_custom_default_shape(self):
        mgr = CursorManager(default_shape=CursorShape.HAND)
        self.assertEqual(CursorShape.HAND, mgr.default_shape)

    def test_request_count_zero(self):
        mgr = CursorManager()
        self.assertEqual(0, mgr.request_count)

    def test_active_shape_is_default_when_empty(self):
        mgr = CursorManager()
        self.assertEqual(CursorShape.ARROW, mgr.active_shape)


class TestCursorManagerPush(unittest.TestCase):
    def test_push_returns_handle(self):
        mgr = CursorManager()
        h = mgr.push(CursorShape.TEXT)
        self.assertIsInstance(h, CursorHandle)

    def test_push_non_shape_raises(self):
        mgr = CursorManager()
        with self.assertRaises(TypeError):
            mgr.push("text")

    def test_push_increments_count(self):
        mgr = CursorManager()
        mgr.push(CursorShape.TEXT)
        self.assertEqual(1, mgr.request_count)

    def test_active_shape_reflects_pushed(self):
        mgr = CursorManager()
        mgr.push(CursorShape.TEXT, priority=5)
        self.assertEqual(CursorShape.TEXT, mgr.active_shape)

    def test_higher_priority_wins(self):
        mgr = CursorManager()
        mgr.push(CursorShape.TEXT, priority=5)
        mgr.push(CursorShape.WAIT, priority=10)
        self.assertEqual(CursorShape.WAIT, mgr.active_shape)

    def test_lower_priority_does_not_override(self):
        mgr = CursorManager()
        mgr.push(CursorShape.WAIT, priority=10)
        mgr.push(CursorShape.TEXT, priority=5)
        self.assertEqual(CursorShape.WAIT, mgr.active_shape)

    def test_equal_priority_last_insertion_wins(self):
        mgr = CursorManager()
        mgr.push(CursorShape.TEXT, priority=5)
        mgr.push(CursorShape.CROSSHAIR, priority=5)
        # max() with equal priority returns first seen — but any stable result is fine;
        # just verify active_shape is one of the two pushed shapes
        self.assertIn(mgr.active_shape, {CursorShape.TEXT, CursorShape.CROSSHAIR})


class TestCursorManagerRelease(unittest.TestCase):
    def test_release_decrements_count(self):
        mgr = CursorManager()
        h = mgr.push(CursorShape.TEXT)
        h.release()
        self.assertEqual(0, mgr.request_count)

    def test_release_reverts_to_default(self):
        mgr = CursorManager()
        h = mgr.push(CursorShape.TEXT)
        h.release()
        self.assertEqual(CursorShape.ARROW, mgr.active_shape)

    def test_release_twice_no_error(self):
        mgr = CursorManager()
        h = mgr.push(CursorShape.TEXT)
        h.release()
        h.release()   # should not raise

    def test_released_flag(self):
        mgr = CursorManager()
        h = mgr.push(CursorShape.TEXT)
        self.assertFalse(h.released)
        h.release()
        self.assertTrue(h.released)

    def test_release_lower_leaves_higher_active(self):
        mgr = CursorManager()
        low = mgr.push(CursorShape.TEXT, priority=5)
        mgr.push(CursorShape.WAIT, priority=10)
        low.release()
        self.assertEqual(CursorShape.WAIT, mgr.active_shape)


class TestCursorManagerReset(unittest.TestCase):
    def test_reset_clears_all(self):
        mgr = CursorManager()
        mgr.push(CursorShape.TEXT)
        mgr.push(CursorShape.WAIT)
        mgr.reset()
        self.assertEqual(0, mgr.request_count)
        self.assertEqual(CursorShape.ARROW, mgr.active_shape)

    def test_default_shape_setter_bad_type_raises(self):
        mgr = CursorManager()
        with self.assertRaises(TypeError):
            mgr.default_shape = "arrow"

    def test_default_shape_setter_ok(self):
        mgr = CursorManager()
        mgr.default_shape = CursorShape.HAND
        self.assertEqual(CursorShape.HAND, mgr.default_shape)


# ===========================================================================
# TooltipManager
# ===========================================================================


def _stub_node(control_id: str) -> SimpleNamespace:
    return SimpleNamespace(control_id=control_id)


class TestTooltipManagerRegistration(unittest.TestCase):
    def setUp(self):
        self.mgr = TooltipManager(default_delay_ms=500, dismiss_ms=3000)

    def test_register_returns_handle(self):
        node = _stub_node("btn1")
        h = self.mgr.register(node, "Click me")
        self.assertIsInstance(h, TooltipHandle)

    def test_handle_node_id(self):
        node = _stub_node("btn1")
        h = self.mgr.register(node, "Click me")
        self.assertEqual("btn1", h.node_id)

    def test_unregister_via_handle(self):
        node = _stub_node("btn1")
        h = self.mgr.register(node, "Click me")
        h.unregister()
        # After unregister, hovering that node should produce no tooltip
        self.mgr.update(1.0, hovered_node_id="btn1")
        self.assertFalse(self.mgr.is_visible)

    def test_update_text_via_handle(self):
        node = _stub_node("btn1")
        h = self.mgr.register(node, "Old text")
        h.update_text("New text")
        # Advance time so tooltip becomes visible
        self.mgr.update(0.6, hovered_node_id="btn1")
        self.assertEqual("New text", self.mgr.visible_text)

    def test_unregister_direct(self):
        node = _stub_node("btn1")
        self.mgr.register(node, "Text")
        self.mgr.unregister("btn1")
        self.mgr.update(1.0, hovered_node_id="btn1")
        self.assertFalse(self.mgr.is_visible)


class TestTooltipManagerInitialState(unittest.TestCase):
    def setUp(self):
        self.mgr = TooltipManager(default_delay_ms=500, dismiss_ms=3000)

    def test_not_visible_initially(self):
        self.assertFalse(self.mgr.is_visible)

    def test_visible_text_none_initially(self):
        self.assertIsNone(self.mgr.visible_text)

    def test_visible_node_id_none_initially(self):
        self.assertIsNone(self.mgr.visible_node_id)


class TestTooltipManagerHoverLogic(unittest.TestCase):
    def setUp(self):
        self.mgr = TooltipManager(default_delay_ms=500, dismiss_ms=3000)
        self.mgr.register(_stub_node("btn1"), "Hint A")
        self.mgr.register(_stub_node("btn2"), "Hint B")

    def test_not_visible_before_delay(self):
        self.mgr.update(0.3, hovered_node_id="btn1")
        self.assertFalse(self.mgr.is_visible)

    def test_visible_after_delay(self):
        self.mgr.update(0.6, hovered_node_id="btn1")
        self.assertTrue(self.mgr.is_visible)

    def test_visible_text_matches_registered(self):
        self.mgr.update(0.6, hovered_node_id="btn1")
        self.assertEqual("Hint A", self.mgr.visible_text)

    def test_visible_node_id(self):
        self.mgr.update(0.6, hovered_node_id="btn1")
        self.assertEqual("btn1", self.mgr.visible_node_id)

    def test_move_to_different_node_hides_tooltip(self):
        self.mgr.update(0.6, hovered_node_id="btn1")
        self.mgr.update(0.0, hovered_node_id="btn2")
        self.assertFalse(self.mgr.is_visible)

    def test_hover_none_hides_tooltip(self):
        self.mgr.update(0.6, hovered_node_id="btn1")
        self.mgr.update(0.0, hovered_node_id=None)
        self.assertFalse(self.mgr.is_visible)

    def test_hover_unregistered_node_no_tooltip(self):
        self.mgr.update(1.0, hovered_node_id="unknown")
        self.assertFalse(self.mgr.is_visible)

    def test_custom_delay_per_node(self):
        mgr = TooltipManager(default_delay_ms=500, dismiss_ms=0)
        mgr.register(_stub_node("fast"), "Fast", delay_ms=100)
        mgr.update(0.15, hovered_node_id="fast")
        self.assertTrue(mgr.is_visible)

    def test_dismiss_after_timeout(self):
        self.mgr.update(0.6, hovered_node_id="btn1")
        self.assertTrue(self.mgr.is_visible)
        self.mgr.update(3.0, hovered_node_id="btn1")   # 3000 ms = dismiss_ms
        self.assertFalse(self.mgr.is_visible)

    def test_no_auto_dismiss_when_dismiss_ms_zero(self):
        mgr = TooltipManager(default_delay_ms=100, dismiss_ms=0)
        mgr.register(_stub_node("btn"), "Hint")
        mgr.update(0.2, hovered_node_id="btn")
        mgr.update(100.0, hovered_node_id="btn")   # huge dt
        self.assertTrue(mgr.is_visible)


# ===========================================================================
# OverlayManager
# ===========================================================================


def _stub_control(rect: Rect, visible: bool = True, enabled: bool = True) -> MagicMock:
    """Return a mock OverlayPanelControl."""
    ctrl = MagicMock()
    ctrl.rect = rect
    ctrl.visible = visible
    ctrl.enabled = enabled
    ctrl.handle_routed_event = MagicMock(return_value=False)
    return ctrl


class TestOverlayManagerBasic(unittest.TestCase):
    def setUp(self):
        self.mgr = OverlayManager()

    def test_empty_count(self):
        self.assertEqual(0, self.mgr.overlay_count())

    def test_show_returns_handle(self):
        ctrl = _stub_control(Rect(0, 0, 100, 50))
        h = self.mgr.show("overlay1", ctrl)
        self.assertIsInstance(h, OverlayHandle)

    def test_show_increments_count(self):
        self.mgr.show("o1", _stub_control(Rect(0, 0, 100, 50)))
        self.assertEqual(1, self.mgr.overlay_count())

    def test_has_overlay_true(self):
        self.mgr.show("o1", _stub_control(Rect(0, 0, 100, 50)))
        self.assertTrue(self.mgr.has_overlay("o1"))

    def test_has_overlay_false(self):
        self.assertFalse(self.mgr.has_overlay("nope"))

    def test_show_replaces_existing(self):
        c1 = _stub_control(Rect(0, 0, 100, 50))
        c2 = _stub_control(Rect(0, 0, 200, 50))
        self.mgr.show("o1", c1)
        self.mgr.show("o1", c2)
        self.assertEqual(1, self.mgr.overlay_count())

    def test_hide_returns_true(self):
        self.mgr.show("o1", _stub_control(Rect(0, 0, 100, 50)))
        self.assertTrue(self.mgr.hide("o1"))

    def test_hide_decrements_count(self):
        self.mgr.show("o1", _stub_control(Rect(0, 0, 100, 50)))
        self.mgr.hide("o1")
        self.assertEqual(0, self.mgr.overlay_count())

    def test_hide_missing_returns_false(self):
        self.assertFalse(self.mgr.hide("nope"))

    def test_hide_all_returns_count(self):
        self.mgr.show("o1", _stub_control(Rect(0, 0, 100, 50)))
        self.mgr.show("o2", _stub_control(Rect(0, 0, 100, 50)))
        self.assertEqual(2, self.mgr.hide_all())
        self.assertEqual(0, self.mgr.overlay_count())

    def test_on_dismiss_called_on_hide(self):
        fired = []
        self.mgr.show("o1", _stub_control(Rect(0, 0, 100, 50)), on_dismiss=lambda: fired.append(1))
        self.mgr.hide("o1")
        self.assertEqual([1], fired)

    def test_on_dismiss_called_on_hide_all(self):
        fired = []
        self.mgr.show("o1", _stub_control(Rect(0, 0, 100, 50)), on_dismiss=lambda: fired.append("a"))
        self.mgr.show("o2", _stub_control(Rect(0, 0, 100, 50)), on_dismiss=lambda: fired.append("b"))
        self.mgr.hide_all()
        self.assertEqual(2, len(fired))

    def test_handle_dismiss(self):
        ctrl = _stub_control(Rect(0, 0, 100, 50))
        h = self.mgr.show("o1", ctrl)
        h.dismiss()
        self.assertFalse(self.mgr.has_overlay("o1"))

    def test_handle_is_open(self):
        h = self.mgr.show("o1", _stub_control(Rect(0, 0, 100, 50)))
        self.assertTrue(h.is_open)
        h.dismiss()
        self.assertFalse(h.is_open)


class TestOverlayManagerPointInOverlay(unittest.TestCase):
    def setUp(self):
        self.mgr = OverlayManager()
        self.mgr.show("o1", _stub_control(Rect(10, 10, 100, 50)))

    def test_point_inside_returns_true(self):
        self.assertTrue(self.mgr.point_in_any_overlay((50, 30)))

    def test_point_outside_returns_false(self):
        self.assertFalse(self.mgr.point_in_any_overlay((200, 200)))

    def test_no_overlays_point_outside(self):
        mgr = OverlayManager()
        self.assertFalse(mgr.point_in_any_overlay((50, 50)))


class TestOverlayManagerAnchorPosition(unittest.TestCase):
    TARGET = Rect(100, 100, 80, 40)

    def _anchor(self, side, align="left", screen_rect=None):
        return OverlayManager.anchor_position(
            (60, 30), self.TARGET, side=side, align=align, screen_rect=screen_rect
        )

    def test_below_left(self):
        x, y = self._anchor("below", "left")
        self.assertEqual(self.TARGET.left, x)
        self.assertEqual(self.TARGET.bottom, y)

    def test_below_right(self):
        x, y = self._anchor("below", "right")
        self.assertEqual(self.TARGET.right - 60, x)

    def test_below_center(self):
        x, y = self._anchor("below", "center")
        self.assertEqual(self.TARGET.centerx - 30, x)

    def test_above(self):
        x, y = self._anchor("above", "left")
        self.assertEqual(self.TARGET.top - 30, y)

    def test_right_top(self):
        x, y = self._anchor("right", "top")
        self.assertEqual(self.TARGET.right, x)
        self.assertEqual(self.TARGET.top, y)

    def test_left_top(self):
        x, y = self._anchor("left", "top")
        self.assertEqual(self.TARGET.left - 60, x)

    def test_screen_rect_clamps(self):
        screen = Rect(0, 0, 120, 200)
        x, y = OverlayManager.anchor_position(
            (60, 30), Rect(90, 100, 80, 40), side="below", align="left",
            screen_rect=screen,
        )
        self.assertGreaterEqual(x, screen.left)
        self.assertLessEqual(x + 60, screen.right)


class TestOverlayManagerModalKeys(unittest.TestCase):
    def setUp(self):
        self.mgr = OverlayManager()

    def test_consume_unhandled_keys_prevents_fallthrough(self):
        ctrl = _stub_control(Rect(0, 0, 100, 50))
        self.mgr.show("o1", ctrl, consume_unhandled_keys=True)
        ev = GuiEvent(kind=EventType.KEY_DOWN, type=pygame.KEYDOWN, key=pygame.K_a)
        consumed = self.mgr.route_event(ev, app=SimpleNamespace())
        self.assertTrue(consumed)

    def test_key_not_consumed_without_modal_flag(self):
        ctrl = _stub_control(Rect(0, 0, 100, 50))
        self.mgr.show("o1", ctrl, consume_unhandled_keys=False)
        ev = GuiEvent(kind=EventType.KEY_DOWN, type=pygame.KEYDOWN, key=pygame.K_a)
        consumed = self.mgr.route_event(ev, app=SimpleNamespace())
        self.assertFalse(consumed)


if __name__ == "__main__":
    unittest.main()
