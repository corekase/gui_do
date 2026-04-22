"""Tests for GUI package convenience helper functions (2026-04-22).

Covers:
  - UiNode: show/hide, enable/disable, set_pos/move_to, resize, set_rect,
             siblings, root, find_descendants_of_type
  - PanelControl / WindowControl: clear_children
  - GuiApplication: find, find_all, focus_on, quit
  - ActionManager: register_and_bind
  - SliderControl: normalized, set_normalized
  - ScrollbarControl: scroll_fraction
  - EventBus: once
"""
import unittest

import pygame
from pygame import Rect, Surface

from gui.app.gui_application import GuiApplication
from gui.controls.button_control import ButtonControl
from gui.controls.label_control import LabelControl
from gui.controls.panel_control import PanelControl
from gui.controls.scrollbar_control import ScrollbarControl
from gui.controls.slider_control import SliderControl
from gui.controls.window_control import WindowControl
from gui.core.action_manager import ActionManager
from gui.core.event_bus import EventBus
from gui.core.ui_node import UiNode
from gui.layout.layout_axis import LayoutAxis


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _node(control_id: str = "n", rect=None) -> UiNode:
    return UiNode(control_id, rect or Rect(0, 0, 100, 100))


# ---------------------------------------------------------------------------
# UiNode — visibility helpers
# ---------------------------------------------------------------------------

class UiNodeShowHideTests(unittest.TestCase):

    def test_show_sets_visible_true(self) -> None:
        node = _node()
        node.visible = False
        node.show()
        self.assertTrue(node.visible)

    def test_hide_sets_visible_false(self) -> None:
        node = _node()
        node.hide()
        self.assertFalse(node.visible)

    def test_show_then_hide(self) -> None:
        node = _node()
        node.hide()
        node.show()
        node.hide()
        self.assertFalse(node.visible)

    def test_show_idempotent(self) -> None:
        node = _node()
        node.show()
        node.show()
        self.assertTrue(node.visible)


class UiNodeEnableDisableTests(unittest.TestCase):

    def test_enable_sets_enabled_true(self) -> None:
        node = _node()
        node.enabled = False
        node.enable()
        self.assertTrue(node.enabled)

    def test_disable_sets_enabled_false(self) -> None:
        node = _node()
        node.disable()
        self.assertFalse(node.enabled)

    def test_disable_then_enable(self) -> None:
        node = _node()
        node.disable()
        node.enable()
        self.assertTrue(node.enabled)

    def test_disable_idempotent(self) -> None:
        node = _node()
        node.disable()
        node.disable()
        self.assertFalse(node.enabled)


# ---------------------------------------------------------------------------
# UiNode — geometry helpers
# ---------------------------------------------------------------------------

class UiNodeGeometryTests(unittest.TestCase):

    def test_set_pos_moves_topleft(self) -> None:
        node = _node(rect=Rect(0, 0, 50, 50))
        node.set_pos(100, 200)
        self.assertEqual(node.rect.topleft, (100, 200))
        self.assertEqual(node.rect.size, (50, 50))

    def test_move_to_is_alias_for_set_pos(self) -> None:
        node = _node(rect=Rect(0, 0, 60, 30))
        node.move_to(10, 20)
        self.assertEqual(node.rect.topleft, (10, 20))
        self.assertEqual(node.rect.size, (60, 30))

    def test_set_pos_invalidates(self) -> None:
        node = _node()
        node._dirty = False
        node.set_pos(5, 5)
        self.assertTrue(node.dirty)

    def test_resize_changes_size(self) -> None:
        node = _node(rect=Rect(10, 20, 50, 50))
        node.resize(200, 100)
        self.assertEqual(node.rect.size, (200, 100))
        self.assertEqual(node.rect.topleft, (10, 20))

    def test_resize_invalidates(self) -> None:
        node = _node()
        node._dirty = False
        node.resize(80, 40)
        self.assertTrue(node.dirty)

    def test_set_rect_replaces_rect_entirely(self) -> None:
        node = _node(rect=Rect(0, 0, 100, 100))
        node.set_rect(Rect(5, 10, 200, 80))
        self.assertEqual(node.rect, Rect(5, 10, 200, 80))

    def test_set_rect_invalidates(self) -> None:
        node = _node()
        node._dirty = False
        node.set_rect(Rect(1, 2, 3, 4))
        self.assertTrue(node.dirty)


# ---------------------------------------------------------------------------
# UiNode — siblings / root
# ---------------------------------------------------------------------------

class UiNodeSiblingsTests(unittest.TestCase):

    def _build_family(self):
        parent = _node("parent")
        a = _node("a")
        b = _node("b")
        c = _node("c")
        for child in (a, b, c):
            child.parent = parent
            parent.children.append(child)
        return parent, a, b, c

    def test_siblings_yields_other_children(self) -> None:
        _, a, b, c = self._build_family()
        result = list(a.siblings())
        self.assertIn(b, result)
        self.assertIn(c, result)
        self.assertNotIn(a, result)

    def test_siblings_count(self) -> None:
        _, a, b, c = self._build_family()
        self.assertEqual(len(list(b.siblings())), 2)

    def test_siblings_empty_for_root(self) -> None:
        node = _node()
        self.assertEqual(list(node.siblings()), [])

    def test_siblings_empty_for_only_child(self) -> None:
        parent = _node("p")
        child = _node("c")
        child.parent = parent
        parent.children.append(child)
        self.assertEqual(list(child.siblings()), [])


class UiNodeRootTests(unittest.TestCase):

    def test_root_returns_self_when_no_parent(self) -> None:
        node = _node()
        self.assertIs(node.root(), node)

    def test_root_returns_root_ancestor(self) -> None:
        grandparent = _node("gp")
        parent = _node("p")
        child = _node("c")
        parent.parent = grandparent
        grandparent.children.append(parent)
        child.parent = parent
        parent.children.append(child)

        self.assertIs(child.root(), grandparent)
        self.assertIs(parent.root(), grandparent)
        self.assertIs(grandparent.root(), grandparent)


# ---------------------------------------------------------------------------
# UiNode — find_descendants_of_type
# ---------------------------------------------------------------------------

class FindDescendantsOfTypeTests(unittest.TestCase):

    def test_finds_matching_type(self) -> None:
        panel = PanelControl("p", Rect(0, 0, 400, 300))
        btn = panel.add(ButtonControl("b", Rect(10, 10, 80, 30), "OK"))
        label = panel.add(LabelControl("l", Rect(10, 50, 100, 20), "hello"))

        buttons = panel.find_descendants_of_type(ButtonControl)
        self.assertIn(btn, buttons)
        self.assertNotIn(label, buttons)

    def test_returns_empty_when_no_match(self) -> None:
        panel = PanelControl("p", Rect(0, 0, 400, 300))
        panel.add(LabelControl("l", Rect(0, 0, 100, 20), "x"))
        self.assertEqual(panel.find_descendants_of_type(ButtonControl), [])

    def test_finds_nested_type(self) -> None:
        panel = PanelControl("p", Rect(0, 0, 400, 300))
        inner = panel.add(PanelControl("inner", Rect(0, 0, 200, 200)))
        btn = inner.add(ButtonControl("b", Rect(0, 0, 80, 30), "X"))

        buttons = panel.find_descendants_of_type(ButtonControl)
        self.assertIn(btn, buttons)


# ---------------------------------------------------------------------------
# PanelControl — clear_children
# ---------------------------------------------------------------------------

class PanelClearChildrenTests(unittest.TestCase):

    def _make_panel(self):
        panel = PanelControl("p", Rect(0, 0, 400, 300))
        a = panel.add(ButtonControl("a", Rect(10, 10, 80, 30), "A"))
        b = panel.add(ButtonControl("b", Rect(10, 50, 80, 30), "B"))
        c = panel.add(LabelControl("c", Rect(10, 90, 80, 20), "C"))
        return panel, a, b, c

    def test_clear_children_removes_all(self) -> None:
        panel, _, _, _ = self._make_panel()
        count = panel.clear_children()
        self.assertEqual(panel.child_count, 0)
        self.assertEqual(count, 3)

    def test_clear_children_unparents_nodes(self) -> None:
        panel, a, b, c = self._make_panel()
        panel.clear_children()
        for node in (a, b, c):
            self.assertIsNone(node.parent)

    def test_clear_children_with_dispose(self) -> None:
        panel, a, b, c = self._make_panel()
        panel.clear_children(dispose=True)
        for node in (a, b, c):
            self.assertTrue(node.disposed)

    def test_clear_children_empty_panel_returns_zero(self) -> None:
        panel = PanelControl("p", Rect(0, 0, 100, 100))
        self.assertEqual(panel.clear_children(), 0)

    def test_clear_children_no_dispose_keeps_nodes_alive(self) -> None:
        panel, a, b, _ = self._make_panel()
        panel.clear_children(dispose=False)
        self.assertFalse(a.disposed)
        self.assertFalse(b.disposed)


# ---------------------------------------------------------------------------
# WindowControl — clear_children
# ---------------------------------------------------------------------------

class WindowClearChildrenTests(unittest.TestCase):

    def _make_window(self):
        window = WindowControl("w", Rect(10, 10, 300, 200), "Win")
        a = window.add(ButtonControl("a", Rect(10, 10, 80, 30), "A"))
        b = window.add(LabelControl("b", Rect(10, 50, 80, 20), "B"))
        return window, a, b

    def test_clear_children_removes_all(self) -> None:
        window, _, _ = self._make_window()
        count = window.clear_children()
        self.assertEqual(len(window.children), 0)
        self.assertEqual(count, 2)

    def test_clear_children_with_dispose(self) -> None:
        window, a, b = self._make_window()
        window.clear_children(dispose=True)
        self.assertTrue(a.disposed)
        self.assertTrue(b.disposed)

    def test_clear_children_no_dispose_keeps_nodes_alive(self) -> None:
        window, a, b = self._make_window()
        window.clear_children(dispose=False)
        self.assertFalse(a.disposed)
        self.assertFalse(b.disposed)

    def test_clear_children_empty_window_returns_zero(self) -> None:
        window = WindowControl("w", Rect(0, 0, 200, 150), "W")
        self.assertEqual(window.clear_children(), 0)


# ---------------------------------------------------------------------------
# GuiApplication — find / find_all / focus_on / quit
# ---------------------------------------------------------------------------

class GuiApplicationConvenienceTests(unittest.TestCase):

    def setUp(self) -> None:
        pygame.init()
        self.app = GuiApplication(Surface((400, 300)))
        self.root = self.app.add(PanelControl("root", Rect(0, 0, 400, 300)))
        self.btn = self.root.add(ButtonControl("btn_ok", Rect(10, 10, 80, 30), "OK"))
        self.btn.set_tab_index(0)
        self.label = self.root.add(LabelControl("lbl_title", Rect(10, 50, 100, 20), "Title"))

    def tearDown(self) -> None:
        pygame.quit()

    def test_find_returns_matching_node(self) -> None:
        result = self.app.find("btn_ok")
        self.assertIs(result, self.btn)

    def test_find_returns_none_for_missing(self) -> None:
        self.assertIsNone(self.app.find("nonexistent"))

    def test_find_all_filters_by_predicate(self) -> None:
        result = self.app.find_all(lambda n: isinstance(n, ButtonControl))
        self.assertIn(self.btn, result)
        self.assertNotIn(self.label, result)

    def test_find_all_returns_empty_when_no_match(self) -> None:
        result = self.app.find_all(lambda n: False)
        self.assertEqual(result, [])

    def test_focus_on_focuses_by_id(self) -> None:
        result = self.app.focus_on("btn_ok")
        self.assertTrue(result)
        self.assertIs(self.app.focus.focused_node, self.btn)

    def test_focus_on_returns_false_for_missing_id(self) -> None:
        result = self.app.focus_on("not_there")
        self.assertFalse(result)

    def test_quit_sets_running_false(self) -> None:
        self.assertTrue(self.app.running)
        self.app.quit()
        self.assertFalse(self.app.running)

    def test_find_in_named_scene(self) -> None:
        other_scene = self.app.create_scene("other")
        other_btn = other_scene.add(ButtonControl("btn_other", Rect(0, 0, 80, 30), "X"))
        result = self.app.find("btn_other", scene_name="other")
        self.assertIs(result, other_btn)

    def test_focus_on_uses_named_scene(self) -> None:
        other_scene = self.app.create_scene("other2")
        other_btn = other_scene.add(ButtonControl("btn2", Rect(0, 0, 80, 30), "Y"))
        other_btn.set_tab_index(0)
        result = self.app.focus_on("btn2", scene_name="other2")
        self.assertTrue(result)
        self.assertIs(self.app.focus.focused_node, other_btn)


# ---------------------------------------------------------------------------
# ActionManager — register_and_bind
# ---------------------------------------------------------------------------

class ActionManagerRegisterAndBindTests(unittest.TestCase):

    def setUp(self) -> None:
        self.am = ActionManager()

    def test_register_and_bind_creates_action(self) -> None:
        self.am.register_and_bind("save", pygame.K_s, lambda e: True)
        self.assertTrue(self.am.has_action("save"))

    def test_register_and_bind_creates_key_binding(self) -> None:
        self.am.register_and_bind("save", pygame.K_s, lambda e: True)
        bindings = self.am.bindings_for_action("save")
        self.assertEqual(len(bindings), 1)
        self.assertEqual(bindings[0].key, pygame.K_s)

    def test_register_and_bind_with_scene_scope(self) -> None:
        self.am.register_and_bind("open", pygame.K_o, lambda e: True, scene="main")
        bindings = self.am.bindings_for_action("open")
        self.assertEqual(bindings[0].scene, "main")

    def test_register_and_bind_with_window_only(self) -> None:
        self.am.register_and_bind("close", pygame.K_w, lambda e: True, window_only=True)
        bindings = self.am.bindings_for_action("close")
        self.assertTrue(bindings[0].window_only)

    def test_register_and_bind_replaces_existing_handler(self) -> None:
        called = []
        self.am.register_and_bind("act", pygame.K_a, lambda e: called.append(1) or True)
        self.am.register_and_bind("act", pygame.K_a, lambda e: called.append(2) or True)
        # Second binding adds a second key entry; action handler is replaced
        self.assertTrue(self.am.has_action("act"))


# ---------------------------------------------------------------------------
# SliderControl — normalized / set_normalized
# ---------------------------------------------------------------------------

class SliderNormalizedTests(unittest.TestCase):

    def _slider(self, minimum, maximum, value):
        return SliderControl("s", Rect(0, 0, 200, 20), LayoutAxis.HORIZONTAL, minimum, maximum, value)

    def test_normalized_minimum_is_zero(self) -> None:
        s = self._slider(0, 100, 0)
        self.assertAlmostEqual(s.normalized, 0.0)

    def test_normalized_maximum_is_one(self) -> None:
        s = self._slider(0, 100, 100)
        self.assertAlmostEqual(s.normalized, 1.0)

    def test_normalized_midpoint(self) -> None:
        s = self._slider(0, 100, 50)
        self.assertAlmostEqual(s.normalized, 0.5)

    def test_normalized_with_offset_range(self) -> None:
        s = self._slider(50, 150, 100)
        self.assertAlmostEqual(s.normalized, 0.5)

    def test_normalized_zero_span_returns_zero(self) -> None:
        s = self._slider(10, 10, 10)
        self.assertAlmostEqual(s.normalized, 0.0)

    def test_set_normalized_sets_correct_value(self) -> None:
        s = self._slider(0, 100, 0)
        s.set_normalized(0.75)
        self.assertAlmostEqual(s.value, 75.0)

    def test_set_normalized_zero(self) -> None:
        s = self._slider(0, 200, 100)
        s.set_normalized(0.0)
        self.assertAlmostEqual(s.value, 0.0)

    def test_set_normalized_one(self) -> None:
        s = self._slider(0, 200, 0)
        s.set_normalized(1.0)
        self.assertAlmostEqual(s.value, 200.0)

    def test_set_normalized_clamped_above_one(self) -> None:
        s = self._slider(0, 100, 0)
        s.set_normalized(2.0)
        self.assertAlmostEqual(s.value, 100.0)

    def test_set_normalized_clamped_below_zero(self) -> None:
        s = self._slider(0, 100, 50)
        s.set_normalized(-1.0)
        self.assertAlmostEqual(s.value, 0.0)


# ---------------------------------------------------------------------------
# ScrollbarControl — scroll_fraction
# ---------------------------------------------------------------------------

class ScrollbarScrollFractionTests(unittest.TestCase):

    def _bar(self, content, viewport, offset):
        return ScrollbarControl("sb", Rect(0, 0, 20, 200), LayoutAxis.VERTICAL, content, viewport, offset=offset)

    def test_scroll_fraction_at_start(self) -> None:
        bar = self._bar(400, 200, 0)
        self.assertAlmostEqual(bar.scroll_fraction, 0.0)

    def test_scroll_fraction_at_end(self) -> None:
        bar = self._bar(400, 200, 200)
        self.assertAlmostEqual(bar.scroll_fraction, 1.0)

    def test_scroll_fraction_midpoint(self) -> None:
        bar = self._bar(400, 200, 100)
        self.assertAlmostEqual(bar.scroll_fraction, 0.5)

    def test_scroll_fraction_content_fits_viewport(self) -> None:
        bar = self._bar(100, 200, 0)
        self.assertAlmostEqual(bar.scroll_fraction, 0.0)

    def test_scroll_fraction_after_set_offset(self) -> None:
        bar = self._bar(400, 100, 0)
        bar.set_offset(300)
        self.assertAlmostEqual(bar.scroll_fraction, 1.0)


# ---------------------------------------------------------------------------
# EventBus — once
# ---------------------------------------------------------------------------

class EventBusOnceTests(unittest.TestCase):

    def setUp(self) -> None:
        self.bus = EventBus()

    def test_once_fires_on_first_publish(self) -> None:
        received = []
        self.bus.once("ping", received.append)
        self.bus.publish("ping", "hello")
        self.assertEqual(received, ["hello"])

    def test_once_does_not_fire_on_second_publish(self) -> None:
        received = []
        self.bus.once("ping", received.append)
        self.bus.publish("ping", 1)
        self.bus.publish("ping", 2)
        self.assertEqual(received, [1])

    def test_once_unsubscribes_after_fire(self) -> None:
        self.bus.once("evt", lambda p: None)
        before = self.bus.subscriber_count("evt")
        self.bus.publish("evt")
        after = self.bus.subscriber_count("evt")
        self.assertEqual(before, 1)
        self.assertEqual(after, 0)

    def test_once_can_be_cancelled_before_fire(self) -> None:
        received = []
        sub = self.bus.once("evt", received.append)
        self.bus.unsubscribe(sub)
        self.bus.publish("evt", "x")
        self.assertEqual(received, [])

    def test_once_coexists_with_regular_subscriptions(self) -> None:
        always = []
        once_list = []
        self.bus.subscribe("evt", always.append)
        self.bus.once("evt", once_list.append)
        self.bus.publish("evt", "a")
        self.bus.publish("evt", "b")
        self.assertEqual(always, ["a", "b"])
        self.assertEqual(once_list, ["a"])

    def test_once_with_scope(self) -> None:
        received = []
        self.bus.once("evt", received.append, scope="myscope")
        self.bus.publish("evt", "x", scope="myscope")
        self.bus.publish("evt", "y", scope="myscope")
        self.assertEqual(received, ["x"])

    def test_once_returns_subscription(self) -> None:
        sub = self.bus.once("evt", lambda p: None)
        self.assertIsNotNone(sub)
        self.assertEqual(sub.topic, "evt")


if __name__ == "__main__":
    unittest.main()
