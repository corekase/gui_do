"""Tests for SplitterControl, ButtonGroupControl, and PanelControl."""
import unittest

import pygame
from pygame import Rect

from gui_do.controls.composite.splitter_control import SplitterControl
from gui_do.controls.input.button_group_control import ButtonGroupControl
from gui_do.controls.composite.panel_control import PanelControl
from gui_do.controls.chrome.window_control import WindowControl
from gui_do.events.gui_event import GuiEvent, EventType
from gui_do.events.pointer_capture import PointerCapture
from gui_do.layout.layout_axis import LayoutAxis

pygame.init()


# ===========================================================================
# SplitterControl
# ===========================================================================


class TestSplitterControlInitial(unittest.TestCase):
    def setUp(self):
        self.sp = SplitterControl("sp", Rect(0, 0, 400, 200))

    def test_default_axis_horizontal(self):
        self.assertEqual(LayoutAxis.HORIZONTAL, self.sp.axis)

    def test_is_horizontal_true(self):
        self.assertTrue(self.sp.is_horizontal)

    def test_is_horizontal_false_for_vertical(self):
        sp = SplitterControl("sp", Rect(0, 0, 200, 400), axis=LayoutAxis.VERTICAL)
        self.assertFalse(sp.is_horizontal)

    def test_default_ratio_half(self):
        self.assertAlmostEqual(0.5, self.sp.ratio, places=1)

    def test_initial_ratio_stored(self):
        sp = SplitterControl("sp", Rect(0, 0, 400, 200), ratio=0.3)
        self.assertAlmostEqual(0.3, sp.ratio, places=2)

    def test_ratio_clamped_high(self):
        sp = SplitterControl("sp", Rect(0, 0, 400, 200), ratio=1.5)
        self.assertLessEqual(sp.ratio, 1.0)

    def test_ratio_clamped_low(self):
        sp = SplitterControl("sp", Rect(0, 0, 400, 200), ratio=-0.5)
        self.assertGreaterEqual(sp.ratio, 0.0)


class TestSplitterControlPaneRects(unittest.TestCase):
    """Verify geometric correctness of pane_a_rect / pane_b_rect / divider_rect."""

    def test_horizontal_pane_a_left_of_divider(self):
        sp = SplitterControl("sp", Rect(0, 0, 400, 200), ratio=0.5)
        a = sp.pane_a_rect
        div = sp.divider_rect
        self.assertLessEqual(a.right, div.left)

    def test_horizontal_pane_b_right_of_divider(self):
        sp = SplitterControl("sp", Rect(0, 0, 400, 200), ratio=0.5)
        b = sp.pane_b_rect
        div = sp.divider_rect
        self.assertGreaterEqual(b.left, div.right)

    def test_horizontal_panes_same_height(self):
        sp = SplitterControl("sp", Rect(0, 0, 400, 200), ratio=0.5)
        self.assertEqual(sp.pane_a_rect.height, sp.pane_b_rect.height)

    def test_vertical_pane_a_above_divider(self):
        sp = SplitterControl("sp", Rect(0, 0, 200, 400), axis=LayoutAxis.VERTICAL, ratio=0.5)
        a = sp.pane_a_rect
        div = sp.divider_rect
        self.assertLessEqual(a.bottom, div.top)

    def test_vertical_pane_b_below_divider(self):
        sp = SplitterControl("sp", Rect(0, 0, 200, 400), axis=LayoutAxis.VERTICAL, ratio=0.5)
        b = sp.pane_b_rect
        div = sp.divider_rect
        self.assertGreaterEqual(b.top, div.bottom)

    def test_divider_width_matches_thickness(self):
        sp = SplitterControl("sp", Rect(0, 0, 400, 200), ratio=0.5, divider_thickness=8)
        self.assertEqual(8, sp.divider_rect.width)

    def test_vertical_divider_height_matches_thickness(self):
        sp = SplitterControl("sp", Rect(0, 0, 200, 400), axis=LayoutAxis.VERTICAL,
                              ratio=0.5, divider_thickness=8)
        self.assertEqual(8, sp.divider_rect.height)

    def test_ratio_affects_pane_a_width(self):
        sp_narrow = SplitterControl("sp", Rect(0, 0, 400, 200), ratio=0.25)
        sp_wide = SplitterControl("sp2", Rect(0, 0, 400, 200), ratio=0.75)
        self.assertLess(sp_narrow.pane_a_rect.width, sp_wide.pane_a_rect.width)


class TestSplitterControlRatioSetter(unittest.TestCase):
    def test_set_ratio(self):
        sp = SplitterControl("sp", Rect(0, 0, 400, 200), ratio=0.5)
        sp.ratio = 0.7
        self.assertAlmostEqual(0.7, sp.ratio, places=1)

    def test_set_ratio_clamped_low(self):
        sp = SplitterControl("sp", Rect(0, 0, 400, 200))
        sp.ratio = -1.0
        self.assertGreaterEqual(sp.ratio, 0.0)

    def test_set_ratio_clamped_high(self):
        sp = SplitterControl("sp", Rect(0, 0, 400, 200))
        sp.ratio = 2.0
        self.assertLessEqual(sp.ratio, 1.0)

    def test_on_ratio_changed_callback_stored(self):
        received = []
        sp = SplitterControl("sp", Rect(0, 0, 400, 200), on_ratio_changed=lambda r: received.append(r))
        # ratio_changed fires when dragging; just verify it's stored
        self.assertIsNotNone(sp._on_ratio_changed)

    def test_min_pane_size_clamped_to_at_least_four(self):
        sp = SplitterControl("sp", Rect(0, 0, 400, 200), min_pane_size=0)
        self.assertGreaterEqual(sp._min_pane_size, 4)


class TestSplitterControlAcceptsFocus(unittest.TestCase):
    def test_tab_index_zero(self):
        sp = SplitterControl("sp", Rect(0, 0, 400, 200))
        self.assertEqual(0, sp.tab_index)


# ===========================================================================
# ButtonGroupControl
# ===========================================================================


def _make_btn(control_id, group, selected=False, on_activate=None):
    ButtonGroupControl.clear_group_registry(group)
    return ButtonGroupControl(
        control_id, Rect(0, 0, 80, 28), group, control_id,
        selected=selected, on_activate=on_activate,
    )


class TestButtonGroupControlInitial(unittest.TestCase):
    def setUp(self):
        ButtonGroupControl.clear_group_registry()

    def test_first_button_becomes_selected_when_none_specified(self):
        btn = ButtonGroupControl("a", Rect(0, 0, 80, 28), "grp", "A")
        self.assertTrue(btn.pushed)

    def test_selected_true_stores_pushed(self):
        ButtonGroupControl.clear_group_registry("grp2")
        btn = ButtonGroupControl("b", Rect(0, 0, 80, 28), "grp2", "B", selected=True)
        self.assertTrue(btn.pushed)

    def test_text_stored(self):
        btn = _make_btn("btn1", "g1")
        self.assertEqual("btn1", btn.text_on)

    def test_group_stored(self):
        btn = _make_btn("btn2", "g2")
        self.assertEqual("g2", btn.group)


class TestButtonGroupControlSetOnActivate(unittest.TestCase):
    def setUp(self):
        ButtonGroupControl.clear_group_registry()

    def test_set_on_activate_callable(self):
        btn = _make_btn("x", "grp_act")
        received = []
        btn.set_on_activate(lambda: received.append(1))
        btn._invoke_activate()
        self.assertEqual([1], received)

    def test_set_on_activate_none_clears(self):
        received = []
        btn = _make_btn("x", "grp_clear", on_activate=lambda: received.append(1))
        btn.set_on_activate(None)
        btn._invoke_activate()
        self.assertEqual([], received)

    def test_set_on_activate_non_callable_raises(self):
        btn = _make_btn("x", "grp_err")
        with self.assertRaises(ValueError):
            btn.set_on_activate("bad")


class TestButtonGroupControlClearGroupRegistry(unittest.TestCase):
    def test_clear_specific_group(self):
        ButtonGroupControl.clear_group_registry("my_group")
        ButtonGroupControl("a", Rect(0, 0, 80, 28), "my_group", "A", selected=True)
        ButtonGroupControl.clear_group_registry("my_group")
        self.assertNotIn("my_group", ButtonGroupControl._selection_by_group)

    def test_clear_all_groups(self):
        ButtonGroupControl.clear_group_registry()
        self.assertEqual({}, ButtonGroupControl._selection_by_group)


class TestButtonGroupControlInvokeClick(unittest.TestCase):
    def setUp(self):
        ButtonGroupControl.clear_group_registry()

    def test_invoke_click_fires_on_activate(self):
        received = []
        btn = _make_btn("x", "grp_ic", on_activate=lambda: received.append(1))
        btn._invoke_click()
        self.assertEqual([1], received)

    def test_invoke_click_keeps_pushed_true(self):
        btn = _make_btn("x", "grp_push")
        btn._invoke_click()
        self.assertTrue(btn.pushed)

    def test_button_id_reflects_selected(self):
        ButtonGroupControl.clear_group_registry("grp_bid")
        btn = ButtonGroupControl("sel", Rect(0, 0, 80, 28), "grp_bid", "Sel", selected=True)
        self.assertEqual("sel", btn.button_id)


# ===========================================================================
# PanelControl
# ===========================================================================


class TestPanelControlInitial(unittest.TestCase):
    def test_control_id(self):
        p = PanelControl("panel", Rect(0, 0, 400, 300))
        self.assertEqual("panel", p.control_id)

    def test_rect_stored(self):
        r = Rect(10, 20, 400, 300)
        p = PanelControl("panel", r)
        self.assertEqual(r, p.rect)

    def test_draw_background_default_true(self):
        p = PanelControl("panel", Rect(0, 0, 400, 300))
        self.assertTrue(p.draw_background)

    def test_draw_background_false(self):
        p = PanelControl("panel", Rect(0, 0, 400, 300), draw_background=False)
        self.assertFalse(p.draw_background)

    def test_children_empty_initially(self):
        p = PanelControl("panel", Rect(0, 0, 400, 300))
        self.assertEqual([], p.children)

    def test_constraints_none_by_default(self):
        p = PanelControl("panel", Rect(0, 0, 400, 300))
        self.assertIsNone(p.constraints)


class TestPanelControlWindowHelpers(unittest.TestCase):
    """_is_window_like, _top_window_at, _top_visible_window helpers."""

    def _make_mock_window(self, control_id, x=0, y=0, w=200, h=150, visible=True, enabled=True):
        from gui_do.controls.base.ui_node import UiNode
        node = UiNode(control_id, Rect(x, y, w, h))
        node._visible = visible
        node._enabled = enabled
        # Patch is_window to return True
        node.is_window = lambda: True
        return node

    def test_is_window_like_true(self):
        panel = PanelControl("p", Rect(0, 0, 800, 600))
        win = self._make_mock_window("w1")
        self.assertTrue(panel._is_window_like(win))

    def test_top_window_at_finds_window(self):
        panel = PanelControl("p", Rect(0, 0, 800, 600))
        win = self._make_mock_window("w1", x=0, y=0, w=200, h=150)
        panel.children.append(win)
        result = panel._top_window_at((50, 50))
        self.assertIs(win, result)

    def test_top_window_at_returns_none_outside(self):
        panel = PanelControl("p", Rect(0, 0, 800, 600))
        win = self._make_mock_window("w1", x=0, y=0, w=100, h=100)
        panel.children.append(win)
        result = panel._top_window_at((500, 500))
        self.assertIsNone(result)

    def test_top_visible_window_returns_last_visible(self):
        panel = PanelControl("p", Rect(0, 0, 800, 600))
        win1 = self._make_mock_window("w1")
        win2 = self._make_mock_window("w2")
        panel.children.extend([win1, win2])
        result = panel._top_visible_window()
        self.assertIs(win2, result)

    def test_top_visible_window_none_when_empty(self):
        panel = PanelControl("p", Rect(0, 0, 800, 600))
        self.assertIsNone(panel._top_visible_window())

    def test_top_visible_window_skips_invisible(self):
        panel = PanelControl("p", Rect(0, 0, 800, 600))
        win1 = self._make_mock_window("w1", visible=True)
        win2 = self._make_mock_window("w2", visible=False)
        panel.children.extend([win1, win2])
        result = panel._top_visible_window()
        self.assertIs(win1, result)

    def test_next_top_visible_window_excluding(self):
        panel = PanelControl("p", Rect(0, 0, 800, 600))
        win1 = self._make_mock_window("w1")
        win2 = self._make_mock_window("w2")
        panel.children.extend([win1, win2])
        result = panel._next_top_visible_window(excluding=win2)
        self.assertIs(win1, result)


class _StubFocusManager:
    def __init__(self):
        self.cleared = False

    def clear_focus(self):
        self.cleared = True


class _StubShearController:
    def __init__(self):
        self.start_calls = []
        self.update_calls = []
        self.end_calls = 0

    def start_drag(self, mouse_pos, surface=None):
        self.start_calls.append((mouse_pos, surface))

    def update_drag(self, mouse_pos):
        self.update_calls.append(mouse_pos)

    def end_drag(self, mouse_pos=None):
        self.end_calls += 1

    def is_active(self):
        return False


class _StubApp:
    def __init__(self):
        self.surface = pygame.Surface((800, 600))
        self.pointer_capture = PointerCapture()
        self.focus = _StubFocusManager()


class TestPanelControlWindowDrag(unittest.TestCase):
    def test_titlebar_drag_uses_mouse_anchor_in_shear_mode(self):
        panel = PanelControl("panel", Rect(0, 0, 800, 600))
        window = WindowControl("win", Rect(100, 80, 260, 180), "Window")
        window.window_effects = {"shear_enabled": True}
        shear = _StubShearController()
        window.shear_controller = shear
        panel.add(window)

        app = _StubApp()

        down = GuiEvent(
            kind=EventType.MOUSE_BUTTON_DOWN,
            type=0,
            pos=(130, 90),
            button=1,
        )
        consumed = panel.on_event_capture(down, app)
        self.assertTrue(consumed)
        self.assertTrue(app.pointer_capture.is_owned_by("win"))
        self.assertEqual((130, 90), shear.start_calls[-1][0])

        # A large rel delta should not yank the window; anchored absolute mouse
        # positioning keeps it smooth and directly under the grab point.
        motion = GuiEvent(
            kind=EventType.MOUSE_MOTION,
            type=0,
            pos=(150, 110),
            rel=(500, -250),
        )
        consumed = panel.on_event_capture(motion, app)
        self.assertTrue(consumed)
        self.assertEqual((120, 100), window.rect.topleft)
        self.assertEqual((150, 110), shear.update_calls[-1])

        up = GuiEvent(
            kind=EventType.MOUSE_BUTTON_UP,
            type=0,
            pos=(150, 110),
            button=1,
        )
        consumed = panel.on_event_capture(up, app)
        self.assertTrue(consumed)
        self.assertFalse(app.pointer_capture.is_active)
        self.assertEqual(1, shear.end_calls)


class _StubFocusForDrawOrder:
    def __init__(self, focused_node=None):
        self.focused_node = focused_node


class _StubFocusVisualizerForDrawOrder:
    def draw_hint_for_window(self, surface, theme, window):
        return None


class _StubAppForDrawOrder:
    def __init__(self, focused_node=None):
        self.focus = _StubFocusForDrawOrder(focused_node=focused_node)
        self.focus_visualizer = _StubFocusVisualizerForDrawOrder()


class _OrderTrackingWindow(WindowControl):
    def __init__(self, control_id: str, order_log: list[str]):
        super().__init__(control_id, Rect(0, 0, 160, 100), control_id)
        self._order_log = order_log

    def draw(self, surface, theme):
        self._order_log.append(self.control_id)


class TestPanelControlFocusedWindowDrawOrder(unittest.TestCase):
    def test_focused_window_drawn_last_when_not_shear_dragging(self):
        panel = PanelControl("panel", Rect(0, 0, 800, 600), draw_background=False)
        draw_order: list[str] = []
        focused = _OrderTrackingWindow("focused", draw_order)
        other = _OrderTrackingWindow("other", draw_order)
        panel.children.extend([focused, other])
        app = _StubAppForDrawOrder(focused_node=focused)

        surface = pygame.Surface((800, 600))
        panel.draw_window_phase(surface, theme=None, app=app)

        self.assertEqual(["other", "focused"], draw_order)

    def test_focused_window_not_forced_last_during_active_shear_drag(self):
        panel = PanelControl("panel", Rect(0, 0, 800, 600), draw_background=False)
        draw_order: list[str] = []
        focused = _OrderTrackingWindow("focused", draw_order)
        other = _OrderTrackingWindow("other", draw_order)
        panel.children.extend([focused, other])
        app = _StubAppForDrawOrder(focused_node=focused)

        class _StubShear:
            dragging = True

        focused.shear_controller = _StubShear()
        focused.shear_active = True

        surface = pygame.Surface((800, 600))
        panel.draw_window_phase(surface, theme=None, app=app)

        self.assertEqual(["focused", "other"], draw_order)


if __name__ == "__main__":
    unittest.main()
