"""Tests for the 8 generalized systems added in session 2026-04-30.

Covers:
  1. Smart Popup Placement (popup_placement.py)
  2. Control measure() / preferred_size() intrinsic sizing
  3. Auto-tracking reactive computation graph (ComputedValue)
  4. Widget value-state serialization (capture_state / restore_state)
  5. Action Middleware Pipeline (ActionMiddleware / ActionContext)
  6. Cascading Theme Scope Resolution (UiNode.attach_scoped_theme / nearest_scoped_theme)
  7. Spatial Arrow-Key Navigation (FocusScopeManager.move_focus_in_direction)
  8. Local Coordinate Transform Chain (UiNode.local_to_screen / screen_to_local)
"""
from __future__ import annotations

import unittest
from pygame import Rect


# -------------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------------

def _make_node(control_id: str, rect, tab_index: int = -1):
    from gui_do.controls.base.ui_node import UiNode
    node = UiNode(control_id, Rect(rect))
    node.tab_index = tab_index
    return node


# =========================================================================
# 1. Smart Popup Placement
# =========================================================================


class TestPopupPlacement(unittest.TestCase):

    def test_imports(self):
        from gui_do import Alignment, PlacementResult, PopupPlacement, Side, compute_popup_rect
        self.assertTrue(callable(compute_popup_rect))

    def test_basic_bottom_placement_fits(self):
        from gui_do import compute_popup_rect, Side
        anchor = Rect(100, 100, 80, 30)
        popup_size = (80, 40)
        viewport = Rect(0, 0, 800, 600)
        result = compute_popup_rect(anchor, popup_size, viewport, preferred_side=Side.BOTTOM)
        self.assertFalse(result.was_flipped)
        self.assertEqual(result.actual_side, Side.BOTTOM)
        self.assertEqual(result.rect.top, anchor.bottom)
        self.assertEqual(result.rect.width, popup_size[0])
        self.assertEqual(result.rect.height, popup_size[1])

    def test_bottom_flips_to_top_when_clipped(self):
        from gui_do import compute_popup_rect, Side
        anchor = Rect(100, 560, 80, 30)
        popup_size = (80, 80)
        viewport = Rect(0, 0, 800, 600)
        result = compute_popup_rect(anchor, popup_size, viewport, preferred_side=Side.BOTTOM)
        self.assertTrue(result.was_flipped)
        self.assertEqual(result.actual_side, Side.TOP)
        self.assertEqual(result.rect.bottom, anchor.top)

    def test_top_placement_fits(self):
        from gui_do import compute_popup_rect, Side
        anchor = Rect(200, 200, 60, 30)
        popup_size = (60, 50)
        viewport = Rect(0, 0, 800, 600)
        result = compute_popup_rect(anchor, popup_size, viewport, preferred_side=Side.TOP)
        self.assertFalse(result.was_flipped)
        self.assertEqual(result.rect.bottom, anchor.top)

    def test_left_placement(self):
        from gui_do import compute_popup_rect, Side
        anchor = Rect(200, 200, 60, 30)
        popup_size = (80, 50)
        viewport = Rect(0, 0, 800, 600)
        result = compute_popup_rect(anchor, popup_size, viewport, preferred_side=Side.LEFT)
        self.assertEqual(result.actual_side, Side.LEFT)
        self.assertEqual(result.rect.right, anchor.left)

    def test_right_placement(self):
        from gui_do import compute_popup_rect, Side
        anchor = Rect(200, 200, 60, 30)
        popup_size = (80, 50)
        viewport = Rect(0, 0, 800, 600)
        result = compute_popup_rect(anchor, popup_size, viewport, preferred_side=Side.RIGHT)
        self.assertEqual(result.actual_side, Side.RIGHT)
        self.assertEqual(result.rect.left, anchor.right)

    def test_nudge_keeps_rect_inside_viewport(self):
        from gui_do import compute_popup_rect, Side
        anchor = Rect(10, 10, 20, 20)
        popup_size = (100, 50)
        viewport = Rect(0, 0, 800, 600)
        result = compute_popup_rect(anchor, popup_size, viewport, preferred_side=Side.BOTTOM)
        self.assertGreaterEqual(result.rect.left, viewport.left)
        self.assertGreaterEqual(result.rect.top, viewport.top)
        self.assertLessEqual(result.rect.right, viewport.right)
        self.assertLessEqual(result.rect.bottom, viewport.bottom)

    def test_placement_result_fields(self):
        from gui_do import PlacementResult, Side
        pr = PlacementResult(Rect(0, 0, 10, 10), Side.TOP, False, False)
        self.assertIsInstance(pr.rect, Rect)
        self.assertEqual(pr.actual_side, Side.TOP)
        self.assertFalse(pr.was_flipped)
        self.assertFalse(pr.was_nudged)

    def test_popup_placement_descriptor(self):
        from gui_do import PopupPlacement, Side, Alignment
        pp = PopupPlacement(preferred_side=Side.LEFT, alignment=Alignment.CENTER, offset=4)
        anchor = Rect(300, 200, 100, 40)
        popup_size = (80, 50)
        viewport = Rect(0, 0, 800, 600)
        result = pp.compute(anchor, popup_size, viewport)
        self.assertIsNotNone(result)

    def test_alignment_center(self):
        from gui_do import compute_popup_rect, Side, Alignment
        anchor = Rect(300, 100, 100, 30)
        popup_size = (100, 50)
        viewport = Rect(0, 0, 800, 600)
        result = compute_popup_rect(
            anchor, popup_size, viewport,
            preferred_side=Side.BOTTOM, alignment=Alignment.CENTER,
        )
        self.assertEqual(result.rect.centerx, anchor.centerx)

    def test_alignment_start(self):
        from gui_do import compute_popup_rect, Side, Alignment
        anchor = Rect(300, 100, 100, 30)
        popup_size = (100, 50)
        viewport = Rect(0, 0, 800, 600)
        result = compute_popup_rect(
            anchor, popup_size, viewport,
            preferred_side=Side.BOTTOM, alignment=Alignment.START,
        )
        self.assertEqual(result.rect.left, anchor.left)

    def test_alignment_end(self):
        from gui_do import compute_popup_rect, Side, Alignment
        anchor = Rect(300, 100, 100, 30)
        popup_size = (100, 50)
        viewport = Rect(0, 0, 800, 600)
        result = compute_popup_rect(
            anchor, popup_size, viewport,
            preferred_side=Side.BOTTOM, alignment=Alignment.END,
        )
        self.assertEqual(result.rect.right, anchor.right)

    def test_side_enum_has_four_values(self):
        from gui_do import Side
        self.assertEqual(len(Side), 4)

    def test_alignment_enum_has_three_values(self):
        from gui_do import Alignment
        self.assertEqual(len(Alignment), 3)


# =========================================================================
# 2. Control measure() / preferred_size()
# =========================================================================


class TestIntrinsicSizing(unittest.TestCase):

    def test_ui_node_default_preferred_size(self):
        node = _make_node("n", (0, 0, 120, 40))
        self.assertEqual(node.preferred_size(), (120, 40))

    def test_ui_node_measure_alias(self):
        node = _make_node("n", (0, 0, 100, 50))
        self.assertEqual(node.measure(), node.preferred_size())

    def test_ui_node_preferred_size_ignores_available(self):
        node = _make_node("n", (0, 0, 80, 30))
        self.assertEqual(node.preferred_size(200, 300), (80, 30))

    def test_label_preferred_size_before_render(self):
        from gui_do.controls.display.label_control import LabelControl
        lbl = LabelControl("lbl", Rect(0, 0, 100, 30), text="Hi")
        w, h = lbl.preferred_size()
        self.assertEqual((w, h), (100, 30))

    def test_text_input_preferred_size_uses_available_width(self):
        from gui_do.controls.input.text_input_control import TextInputControl
        ti = TextInputControl("ti", Rect(0, 0, 150, 32))
        w, h = ti.preferred_size(available_width=200)
        self.assertEqual(w, 200)
        self.assertEqual(h, 32)

    def test_text_input_preferred_size_falls_back_to_rect_width(self):
        from gui_do.controls.input.text_input_control import TextInputControl
        ti = TextInputControl("ti", Rect(0, 0, 150, 32))
        w, h = ti.preferred_size()
        self.assertEqual(w, 150)

    def test_list_view_preferred_size_clamps_to_available_height(self):
        from gui_do.controls.data.list_view_control import ListViewControl
        lv = ListViewControl("lv", Rect(0, 0, 200, 400), items=["a", "b", "c"])
        w, h = lv.preferred_size(available_width=200, available_height=100)
        self.assertEqual(w, 200)
        self.assertLessEqual(h, 100)

    def test_measure_protocol_returns_tuple_of_two_ints(self):
        node = _make_node("n", (0, 0, 50, 50))
        result = node.measure(available_width=100, available_height=200)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)


# =========================================================================
# 3. Auto-tracking reactive computation graph
# =========================================================================


class TestAutoTrackingComputedValue(unittest.TestCase):

    def test_auto_discovers_deps(self):
        from gui_do import ObservableValue, ComputedValue
        a = ObservableValue(10)
        b = ObservableValue(5)
        c = ComputedValue(lambda: a.value + b.value)
        self.assertEqual(c.value, 15)

    def test_updates_when_dep_changes(self):
        from gui_do import ObservableValue, ComputedValue
        x = ObservableValue(3)
        doubled = ComputedValue(lambda: x.value * 2)
        self.assertEqual(doubled.value, 6)
        x.value = 10
        self.assertEqual(doubled.value, 20)

    def test_explicit_deps_still_work(self):
        from gui_do import ObservableValue, ComputedValue
        a = ObservableValue(4)
        b = ObservableValue(6)
        c = ComputedValue(lambda: a.value + b.value, deps=[a, b])
        self.assertEqual(c.value, 10)
        a.value = 1
        self.assertEqual(c.value, 7)

    def test_no_deps_returns_constant(self):
        from gui_do import ComputedValue
        c = ComputedValue(lambda: 42)
        self.assertEqual(c.value, 42)

    def test_chained_computed_values(self):
        from gui_do import ObservableValue, ComputedValue
        x = ObservableValue(2)
        y = ComputedValue(lambda: x.value * 3)
        z = ComputedValue(lambda: y.value + 1)
        self.assertEqual(z.value, 7)
        x.value = 5
        self.assertEqual(z.value, 16)

    def test_dispose_stops_updates(self):
        from gui_do import ObservableValue, ComputedValue
        x = ObservableValue(1)
        calls = []
        c = ComputedValue(lambda: x.value + 0)
        c.subscribe(lambda new_val: calls.append(new_val))
        c.dispose()
        x.value = 99
        self.assertEqual(calls, [])

    def test_conditional_dependency_tracking(self):
        from gui_do import ObservableValue, ComputedValue
        flag = ObservableValue(True)
        a = ObservableValue(10)
        b = ObservableValue(20)
        c = ComputedValue(lambda: a.value if flag.value else b.value)
        self.assertEqual(c.value, 10)
        flag.value = False
        self.assertEqual(c.value, 20)
        b.value = 99
        self.assertEqual(c.value, 99)


# =========================================================================
# 4. Widget value-state serialization
# =========================================================================


class TestCaptureRestoreState(unittest.TestCase):

    def test_ui_node_default_capture_empty(self):
        node = _make_node("n", (0, 0, 100, 100))
        self.assertEqual(node.capture_state(), {})

    def test_ui_node_default_restore_noop(self):
        node = _make_node("n", (0, 0, 100, 100))
        node.restore_state({"anything": 1})

    def test_slider_round_trip(self):
        from gui_do.controls.input.slider_control import SliderControl
        from gui_do.layout.layout_axis import LayoutAxis
        sl = SliderControl("sl", Rect(0, 0, 200, 30), LayoutAxis.HORIZONTAL, minimum=0.0, maximum=100.0, value=50.0)
        sl._set_value(75.0)
        state = sl.capture_state()
        sl._set_value(0.0)
        sl.restore_state(state)
        self.assertAlmostEqual(sl.value, 75.0)

    def test_toggle_round_trip(self):
        from gui_do.controls.input.toggle_control import ToggleControl
        tg = ToggleControl("tg", Rect(0, 0, 60, 30), text_on="On", pushed=False)
        tg.pushed = True
        state = tg.capture_state()
        tg.pushed = False
        tg.restore_state(state)
        self.assertTrue(tg.pushed)

    def test_scrollbar_round_trip(self):
        from gui_do.controls.input.scrollbar_control import ScrollbarControl
        from gui_do.layout.layout_axis import LayoutAxis
        sb = ScrollbarControl("sb", Rect(0, 0, 20, 200), LayoutAxis.VERTICAL, content_size=1000, viewport_size=200)
        sb._set_offset(300)
        state = sb.capture_state()
        sb._set_offset(0)
        sb.restore_state(state)
        self.assertEqual(sb.offset, 300)

    def test_text_input_round_trip(self):
        from gui_do.controls.input.text_input_control import TextInputControl
        ti = TextInputControl("ti", Rect(0, 0, 200, 30))
        ti.set_value_with_cursor("hello world", 5)
        state = ti.capture_state()
        ti.set_value_with_cursor("", 0)
        ti.restore_state(state)
        self.assertEqual(ti.value, "hello world")
        self.assertEqual(ti._cursor_pos, 5)

    def test_list_view_selection_round_trip(self):
        from gui_do.controls.data.list_view_control import ListViewControl
        # Use enough items that scroll_offset=10 is within valid range
        items = [f"item{i}" for i in range(30)]
        lv = ListViewControl("lv", Rect(0, 0, 200, 100), items=items)
        lv._selected_indices = [1, 3]
        lv._selected_set = {1, 3}
        # Set a valid small scroll offset that won't get clamped to zero
        lv._scroll_offset = 10
        state = lv.capture_state()
        lv._selected_indices = []
        lv._selected_set = set()
        lv._scroll_offset = 0
        lv.restore_state(state)
        self.assertEqual(lv._selected_indices, [1, 3])
        self.assertEqual(lv._scroll_offset, 10)

    def test_list_view_restore_clamps_invalid_indices(self):
        from gui_do.controls.data.list_view_control import ListViewControl
        lv = ListViewControl("lv", Rect(0, 0, 200, 300), items=["a", "b"])
        lv.restore_state({"selected_indices": [0, 1, 5, 99]})
        self.assertEqual(sorted(lv._selected_indices), [0, 1])

    def test_tab_control_round_trip(self):
        from gui_do.controls.data.tab_control import TabControl, TabItem
        tc = TabControl("tc", Rect(0, 0, 400, 300), items=[
            TabItem("a", "Alpha"), TabItem("b", "Beta"),
        ])
        tc.select("b")
        state = tc.capture_state()
        tc.select("a")
        tc.restore_state(state)
        self.assertEqual(tc.selected_key, "b")

    def test_subtree_capture_restore(self):
        from gui_do.controls.input.slider_control import SliderControl
        from gui_do.controls.input.toggle_control import ToggleControl
        from gui_do.layout.layout_axis import LayoutAxis
        root = _make_node("root", (0, 0, 800, 600))
        sl = SliderControl("sl", Rect(0, 0, 200, 30), LayoutAxis.HORIZONTAL, minimum=0, maximum=100, value=0)
        tg = ToggleControl("tg", Rect(0, 0, 60, 30), text_on="On", pushed=False)
        sl.parent = root
        tg.parent = root
        root.children = [sl, tg]
        sl._set_value(42.0)
        tg.pushed = True
        state = root.capture_subtree_state()
        sl._set_value(0.0)
        tg.pushed = False
        root.restore_subtree_state(state)
        self.assertAlmostEqual(sl.value, 42.0)
        self.assertTrue(tg.pushed)


# =========================================================================
# 5. Action Middleware Pipeline
# =========================================================================


class TestActionMiddleware(unittest.TestCase):

    def test_action_context_fields(self):
        from gui_do import ActionContext
        ctx = ActionContext(action_name="foo.bar")
        self.assertEqual(ctx.action_name, "foo.bar")
        self.assertIsNone(ctx.event)
        self.assertIsInstance(ctx.extras, dict)

    def test_middleware_is_called(self):
        from gui_do.actions.action_manager import ActionManager
        from gui_do import ActionContext
        mgr = ActionManager()
        log = []
        handler_calls = []
        mgr.register_action("ping", lambda e: handler_calls.append(1) or True)

        def mw(ctx: ActionContext, next_fn):
            log.append(f"before:{ctx.action_name}")
            result = next_fn(ctx)
            log.append(f"after:{ctx.action_name}:{result}")
            return result

        mgr.add_middleware(mw)
        mgr._dispatch("ping", mgr._actions["ping"], None)
        self.assertIn("before:ping", log)
        self.assertIn("after:ping:True", log)

    def test_middleware_can_block_action(self):
        from gui_do.actions.action_manager import ActionManager
        from gui_do import ActionContext
        mgr = ActionManager()
        handler_calls = []
        mgr.register_action("edit.save", lambda e: handler_calls.append(1) or True)

        def blocking_mw(ctx: ActionContext, next_fn):
            return False

        mgr.add_middleware(blocking_mw)
        result = mgr._dispatch("edit.save", mgr._actions["edit.save"], None)
        self.assertFalse(result)
        self.assertEqual(handler_calls, [])

    def test_middleware_lifo_order(self):
        from gui_do.actions.action_manager import ActionManager
        from gui_do import ActionContext
        mgr = ActionManager()
        mgr.register_action("x", lambda e: True)
        order = []

        def mw1(ctx, next_fn):
            order.append(1)
            return next_fn(ctx)

        def mw2(ctx, next_fn):
            order.append(2)
            return next_fn(ctx)

        mgr.add_middleware(mw1)
        mgr.add_middleware(mw2)
        mgr._dispatch("x", mgr._actions["x"], None)
        self.assertEqual(order, [2, 1])

    def test_remove_middleware(self):
        from gui_do.actions.action_manager import ActionManager
        mgr = ActionManager()
        mgr.register_action("x", lambda e: True)
        log = []

        def mw(ctx, next_fn):
            log.append("mw")
            return next_fn(ctx)

        mgr.add_middleware(mw)
        self.assertEqual(mgr.middleware_count(), 1)
        removed = mgr.remove_middleware(mw)
        self.assertTrue(removed)
        self.assertEqual(mgr.middleware_count(), 0)
        mgr._dispatch("x", mgr._actions["x"], None)
        self.assertEqual(log, [])

    def test_clear_middlewares(self):
        from gui_do.actions.action_manager import ActionManager
        mgr = ActionManager()
        mgr.add_middleware(lambda ctx, n: n(ctx))
        mgr.add_middleware(lambda ctx, n: n(ctx))
        mgr.clear_middlewares()
        self.assertEqual(mgr.middleware_count(), 0)

    def test_extras_dict_shared_across_chain(self):
        from gui_do.actions.action_manager import ActionManager
        from gui_do import ActionContext
        mgr = ActionManager()
        mgr.register_action("y", lambda e: True)
        captured_extras = {}

        def mw_setter(ctx: ActionContext, next_fn):
            ctx.extras["key"] = "value"
            return next_fn(ctx)

        def mw_reader(ctx: ActionContext, next_fn):
            # This runs after mw_setter (mw_setter is added last → runs first in LIFO)
            captured_extras.update(ctx.extras)
            return next_fn(ctx)

        # mw_reader is added first → runs second (LIFO: mw_setter runs first)
        mgr.add_middleware(mw_reader)
        mgr.add_middleware(mw_setter)  # added last → runs first in LIFO
        mgr._dispatch("y", mgr._actions["y"], None)
        self.assertEqual(captured_extras.get("key"), "value")

    def test_build_middleware_chain_empty(self):
        from gui_do.actions.action_middleware import build_middleware_chain, ActionContext
        calls = []
        terminal = lambda ctx: calls.append("terminal") or True
        chain = build_middleware_chain([], terminal)
        ctx = ActionContext(action_name="x")
        result = chain(ctx)
        self.assertTrue(result)
        self.assertEqual(calls, ["terminal"])


# =========================================================================
# 6. Cascading Theme Scope Resolution
# =========================================================================


class TestScopedThemeResolution(unittest.TestCase):

    def _make_scope(self, overrides):
        from gui_do import ScopedTheme
        return ScopedTheme(overrides)

    def test_nearest_scoped_theme_none_by_default(self):
        node = _make_node("n", (0, 0, 100, 100))
        self.assertIsNone(node.nearest_scoped_theme())

    def test_attach_returns_scope_from_nearest(self):
        node = _make_node("n", (0, 0, 100, 100))
        scope = self._make_scope({"surface": (10, 20, 30)})
        node.attach_scoped_theme(scope)
        self.assertIs(node.nearest_scoped_theme(), scope)

    def test_detach_removes_scope(self):
        node = _make_node("n", (0, 0, 100, 100))
        scope = self._make_scope({"surface": (10, 20, 30)})
        node.attach_scoped_theme(scope)
        node.detach_scoped_theme()
        self.assertIsNone(node.nearest_scoped_theme())

    def test_scope_inherits_from_ancestor(self):
        parent = _make_node("parent", (0, 0, 800, 600))
        child = _make_node("child", (10, 10, 100, 50))
        child.parent = parent
        scope = self._make_scope({"surface": (10, 20, 30)})
        parent.attach_scoped_theme(scope)
        self.assertIs(child.nearest_scoped_theme(), scope)

    def test_inner_scope_takes_precedence(self):
        root = _make_node("root", (0, 0, 800, 600))
        middle = _make_node("middle", (10, 10, 400, 400))
        leaf = _make_node("leaf", (10, 10, 100, 50))
        middle.parent = root
        leaf.parent = middle
        outer = self._make_scope({"surface": (100, 0, 0)})
        inner = self._make_scope({"surface": (0, 200, 0)})
        root.attach_scoped_theme(outer)
        middle.attach_scoped_theme(inner)
        self.assertIs(leaf.nearest_scoped_theme(), inner)

    def test_scope_resolve_token(self):
        scope = self._make_scope({"primary": (255, 0, 128)})
        self.assertEqual(scope.resolve("primary"), (255, 0, 128))

    def test_scope_resolve_missing_token_returns_fallback(self):
        scope = self._make_scope({})
        result = scope.resolve("nonexistent", fallback=(0, 0, 0))
        self.assertEqual(result, (0, 0, 0))

    def test_resolve_theme_passthrough(self):
        node = _make_node("n", (0, 0, 100, 100))
        sentinel = object()
        result = node.resolve_theme(sentinel)  # type: ignore[arg-type]
        self.assertIs(result, sentinel)


# =========================================================================
# 7. Spatial Arrow-Key Navigation
# =========================================================================


class TestSpatialNavigation(unittest.TestCase):

    def _make_focus_manager(self):
        from gui_do.focus.focus_manager import FocusManager
        return FocusManager()

    def _setup_grid(self):
        root = _make_node("root", (0, 0, 300, 300))
        positions = {
            "tl": (0, 0, 100, 100),   "tc": (100, 0, 100, 100),   "tr": (200, 0, 100, 100),
            "ml": (0, 100, 100, 100), "mc": (100, 100, 100, 100), "mr": (200, 100, 100, 100),
            "bl": (0, 200, 100, 100), "bc": (100, 200, 100, 100), "br": (200, 200, 100, 100),
        }
        nodes = {}
        for cid, rect in positions.items():
            n = _make_node(cid, rect, tab_index=0)
            n.parent = root
            root.children.append(n)
            nodes[cid] = n
        return root, nodes

    def test_move_focus_right(self):
        from gui_do.focus.focus_scope import FocusScopeManager
        fm = self._make_focus_manager()
        root, nodes = self._setup_grid()
        fm.set_focus(nodes["ml"])
        scope_mgr = FocusScopeManager(fm)
        moved = scope_mgr.move_focus_in_direction("right", root)
        self.assertTrue(moved)
        self.assertIs(fm.focused_node, nodes["mc"])

    def test_move_focus_left(self):
        from gui_do.focus.focus_scope import FocusScopeManager
        fm = self._make_focus_manager()
        root, nodes = self._setup_grid()
        fm.set_focus(nodes["mc"])
        scope_mgr = FocusScopeManager(fm)
        scope_mgr.move_focus_in_direction("left", root)
        self.assertIs(fm.focused_node, nodes["ml"])

    def test_move_focus_down(self):
        from gui_do.focus.focus_scope import FocusScopeManager
        fm = self._make_focus_manager()
        root, nodes = self._setup_grid()
        fm.set_focus(nodes["tc"])
        scope_mgr = FocusScopeManager(fm)
        scope_mgr.move_focus_in_direction("down", root)
        self.assertIs(fm.focused_node, nodes["mc"])

    def test_move_focus_up(self):
        from gui_do.focus.focus_scope import FocusScopeManager
        fm = self._make_focus_manager()
        root, nodes = self._setup_grid()
        fm.set_focus(nodes["mc"])
        scope_mgr = FocusScopeManager(fm)
        scope_mgr.move_focus_in_direction("up", root)
        self.assertIs(fm.focused_node, nodes["tc"])

    def test_no_move_at_edge(self):
        from gui_do.focus.focus_scope import FocusScopeManager
        fm = self._make_focus_manager()
        root, nodes = self._setup_grid()
        fm.set_focus(nodes["tl"])
        scope_mgr = FocusScopeManager(fm)
        moved = scope_mgr.move_focus_in_direction("left", root)
        self.assertFalse(moved)
        self.assertIs(fm.focused_node, nodes["tl"])

    def test_invalid_direction_returns_false(self):
        from gui_do.focus.focus_scope import FocusScopeManager
        fm = self._make_focus_manager()
        root, nodes = self._setup_grid()
        fm.set_focus(nodes["mc"])
        scope_mgr = FocusScopeManager(fm)
        self.assertFalse(scope_mgr.move_focus_in_direction("diagonal", root))

    def test_no_move_when_no_focus(self):
        from gui_do.focus.focus_scope import FocusScopeManager
        fm = self._make_focus_manager()
        root, nodes = self._setup_grid()
        scope_mgr = FocusScopeManager(fm)
        self.assertFalse(scope_mgr.move_focus_in_direction("right", root))


# =========================================================================
# 8. Local Coordinate Transform Chain
# =========================================================================


class TestCoordinateTransforms(unittest.TestCase):

    def test_local_to_screen_no_parent(self):
        node = _make_node("n", (50, 100, 80, 40))
        sx, sy = node.local_to_screen((10, 5))
        self.assertEqual(sx, 60)
        self.assertEqual(sy, 105)

    def test_local_to_screen_with_parent(self):
        parent = _make_node("p", (100, 200, 400, 400))
        child = _make_node("c", (10, 20, 80, 40))
        child.parent = parent
        parent._local_offset = (0, 0)
        sx, sy = child.local_to_screen((5, 3))
        # child local (5,3) → child.rect.left=10, child.rect.top=20 → (15,23)
        # + parent._local_offset(0,0) + parent.rect (100,200) → (115,223)
        self.assertEqual(sx, 115)
        self.assertEqual(sy, 223)

    def test_local_to_screen_with_scroll_offset(self):
        parent = _make_node("p", (0, 0, 400, 400))
        child = _make_node("c", (0, 0, 100, 50))
        child.parent = parent
        parent._local_offset = (-50, -100)
        sx, sy = child.local_to_screen((0, 0))
        self.assertEqual(sx, -50)
        self.assertEqual(sy, -100)

    def test_screen_to_local_inverse(self):
        parent = _make_node("p", (200, 150, 400, 300))
        child = _make_node("c", (10, 10, 80, 40))
        child.parent = parent
        parent._local_offset = (0, 0)
        screen_pos = child.local_to_screen((5, 7))
        local_pos = child.screen_to_local(screen_pos)
        self.assertEqual(local_pos, (5, 7))

    def test_screen_to_local_origin_is_zero(self):
        node = _make_node("n", (120, 80, 200, 100))
        origin_screen = node.local_to_screen((0, 0))
        lx, ly = node.screen_to_local(origin_screen)
        self.assertEqual((lx, ly), (0, 0))

    def test_set_local_offset(self):
        node = _make_node("n", (0, 0, 100, 100))
        node.set_local_offset(15, -30)
        self.assertEqual(node._local_offset, (15, -30))

    def test_default_local_offset_is_zero(self):
        node = _make_node("n", (0, 0, 100, 100))
        self.assertEqual(node._local_offset, (0, 0))

    def test_deep_parent_chain(self):
        grand = _make_node("grand", (100, 100, 600, 600))
        parent = _make_node("parent", (50, 50, 400, 400))
        child = _make_node("child", (20, 20, 100, 100))
        parent.parent = grand
        child.parent = parent
        grand._local_offset = (0, 0)
        parent._local_offset = (0, 0)
        # child at (20,20), parent._local_offset=(0,0), parent.rect=(50,50)
        # grand._local_offset=(0,0), grand.rect=(100,100) → (170, 170)
        sx, sy = child.local_to_screen((0, 0))
        self.assertEqual(sx, 170)
        self.assertEqual(sy, 170)
        lx, ly = child.screen_to_local((sx, sy))
        self.assertEqual((lx, ly), (0, 0))


if __name__ == "__main__":
    unittest.main()
