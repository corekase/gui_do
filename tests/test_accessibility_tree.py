"""Tests for gui_do.accessibility.accessibility_tree (S3)."""
import unittest
from unittest.mock import MagicMock

from gui_do.accessibility.accessibility_tree import (
    AccessibilityRole,
    LivePoliteness,
    AccessibilityNode,
    AccessibilityTree,
    AccessibilityAnnouncement,
    AccessibilityBus,
)


class TestAccessibilityRole(unittest.TestCase):

    def test_enum_has_expected_values(self):
        self.assertEqual(AccessibilityRole.BUTTON.value, "button")
        self.assertEqual(AccessibilityRole.SLIDER.value, "slider")
        self.assertEqual(AccessibilityRole.DIALOG.value, "dialog")
        self.assertEqual(AccessibilityRole.NONE.value, "none")

    def test_all_roles_are_strings(self):
        for role in AccessibilityRole:
            self.assertIsInstance(role.value, str)

    def test_minimum_role_count(self):
        self.assertGreaterEqual(len(AccessibilityRole), 10)


class TestLivePoliteness(unittest.TestCase):

    def test_values(self):
        self.assertEqual(LivePoliteness.OFF.value, "off")
        self.assertEqual(LivePoliteness.POLITE.value, "polite")
        self.assertEqual(LivePoliteness.ASSERTIVE.value, "assertive")


class TestAccessibilityNode(unittest.TestCase):

    def test_defaults(self):
        node = AccessibilityNode()
        self.assertEqual(node.role, AccessibilityRole.NONE)
        self.assertEqual(node.label, "")
        self.assertIsNone(node.widget)
        self.assertIsNone(node.value_text)
        self.assertEqual(node.description, "")
        self.assertIsNone(node.labelledby)
        self.assertEqual(node.live_politeness, LivePoliteness.OFF)
        self.assertTrue(node.enabled)

    def test_construction_with_all_args(self):
        widget = object()
        label_node = AccessibilityNode(label="Zoom")
        node = AccessibilityNode(
            role=AccessibilityRole.SLIDER,
            label="My Slider",
            widget=widget,
            value_text=lambda: "50%",
            description="Adjust zoom level",
            labelledby=label_node,
            live_politeness=LivePoliteness.POLITE,
            enabled=False,
        )
        self.assertEqual(node.role, AccessibilityRole.SLIDER)
        self.assertEqual(node.label, "My Slider")
        self.assertIs(node.widget, widget)
        self.assertFalse(node.enabled)
        self.assertEqual(node.live_politeness, LivePoliteness.POLITE)

    def test_get_value_text_with_callable(self):
        node = AccessibilityNode(value_text=lambda: "75%")
        self.assertEqual(node.get_value_text(), "75%")

    def test_get_value_text_no_callable(self):
        node = AccessibilityNode()
        self.assertEqual(node.get_value_text(), "")

    def test_get_value_text_exception_returns_empty(self):
        def bad():
            raise RuntimeError("oops")
        node = AccessibilityNode(value_text=bad)
        self.assertEqual(node.get_value_text(), "")

    def test_get_effective_label_own(self):
        node = AccessibilityNode(label="Submit")
        self.assertEqual(node.get_effective_label(), "Submit")

    def test_get_effective_label_via_labelledby(self):
        label_node = AccessibilityNode(label="Username")
        input_node = AccessibilityNode(labelledby=label_node)
        self.assertEqual(input_node.get_effective_label(), "Username")

    def test_children_initially_empty(self):
        node = AccessibilityNode()
        self.assertEqual(node.children, [])

    def test_parent_initially_none(self):
        node = AccessibilityNode()
        self.assertIsNone(node.parent)

    def test_ancestors_empty_when_no_parent(self):
        node = AccessibilityNode()
        self.assertEqual(list(node.ancestors()), [])

    def test_repr(self):
        node = AccessibilityNode(role=AccessibilityRole.BUTTON, label="OK")
        r = repr(node)
        self.assertIn("button", r)
        self.assertIn("OK", r)


class TestAccessibilityTree(unittest.TestCase):

    def setUp(self):
        self.tree = AccessibilityTree()

    def test_empty_tree_len(self):
        self.assertEqual(len(self.tree), 0)

    def test_register_and_len(self):
        n = AccessibilityNode(role=AccessibilityRole.BUTTON, label="OK")
        self.tree.register(n)
        self.assertEqual(len(self.tree), 1)

    def test_register_idempotent(self):
        n = AccessibilityNode(label="X")
        self.tree.register(n)
        self.tree.register(n)
        self.assertEqual(len(self.tree), 1)

    def test_register_with_parent(self):
        parent = AccessibilityNode(role=AccessibilityRole.DIALOG, label="Dialog")
        child = AccessibilityNode(role=AccessibilityRole.BUTTON, label="Close")
        self.tree.register(parent)
        self.tree.register(child, parent=parent)
        self.assertEqual(child.parent, parent)
        self.assertIn(child, parent.children)

    def test_ancestors(self):
        root = AccessibilityNode(label="Root")
        mid = AccessibilityNode(label="Mid")
        leaf = AccessibilityNode(label="Leaf")
        self.tree.register(root)
        self.tree.register(mid, parent=root)
        self.tree.register(leaf, parent=mid)
        ancestors = list(leaf.ancestors())
        self.assertEqual(ancestors, [mid, root])

    def test_unregister(self):
        n = AccessibilityNode(label="X")
        self.tree.register(n)
        self.tree.unregister(n)
        self.assertEqual(len(self.tree), 0)

    def test_unregister_unknown_is_noop(self):
        n = AccessibilityNode(label="Ghost")
        self.tree.unregister(n)  # Should not raise

    def test_unregister_removes_from_parent(self):
        parent = AccessibilityNode(role=AccessibilityRole.TOOLBAR, label="Bar")
        child = AccessibilityNode(role=AccessibilityRole.BUTTON, label="Save")
        self.tree.register(parent)
        self.tree.register(child, parent=parent)
        self.tree.unregister(child)
        self.assertNotIn(child, parent.children)
        self.assertIsNone(child.parent)

    def test_clear(self):
        for i in range(5):
            self.tree.register(AccessibilityNode(label=str(i)))
        self.tree.clear()
        self.assertEqual(len(self.tree), 0)

    def test_find_all_by_role(self):
        self.tree.register(AccessibilityNode(role=AccessibilityRole.BUTTON, label="A"))
        self.tree.register(AccessibilityNode(role=AccessibilityRole.BUTTON, label="B"))
        self.tree.register(AccessibilityNode(role=AccessibilityRole.SLIDER, label="S"))
        buttons = self.tree.find_all(role=AccessibilityRole.BUTTON)
        self.assertEqual(len(buttons), 2)

    def test_find_all_no_filter(self):
        for _ in range(4):
            self.tree.register(AccessibilityNode())
        self.assertEqual(len(self.tree.find_all()), 4)

    def test_find_all_enabled_only(self):
        self.tree.register(AccessibilityNode(label="On", enabled=True))
        self.tree.register(AccessibilityNode(label="Off", enabled=False))
        result = self.tree.find_all(enabled_only=True)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].label, "On")

    def test_find_all_scoped(self):
        dialog = AccessibilityNode(role=AccessibilityRole.DIALOG, label="D")
        btn_in = AccessibilityNode(role=AccessibilityRole.BUTTON, label="In")
        btn_out = AccessibilityNode(role=AccessibilityRole.BUTTON, label="Out")
        self.tree.register(dialog)
        self.tree.register(btn_in, parent=dialog)
        self.tree.register(btn_out)
        scoped = self.tree.find_all(role=AccessibilityRole.BUTTON, scope=dialog)
        self.assertEqual(len(scoped), 1)
        self.assertEqual(scoped[0].label, "In")

    def test_find_by_widget(self):
        widget = object()
        n = AccessibilityNode(widget=widget, label="W")
        self.tree.register(n)
        self.assertIs(self.tree.find_by_widget(widget), n)

    def test_find_by_widget_unknown_returns_none(self):
        self.assertIsNone(self.tree.find_by_widget(object()))

    def test_find_first_by_role(self):
        self.tree.register(AccessibilityNode(role=AccessibilityRole.BUTTON, label="First"))
        self.tree.register(AccessibilityNode(role=AccessibilityRole.BUTTON, label="Second"))
        result = self.tree.find_first(role=AccessibilityRole.BUTTON)
        self.assertEqual(result.label, "First")

    def test_find_first_by_label(self):
        self.tree.register(AccessibilityNode(label="Alpha"))
        self.tree.register(AccessibilityNode(label="Beta"))
        result = self.tree.find_first(label="Beta")
        self.assertEqual(result.label, "Beta")

    def test_find_first_no_match_returns_none(self):
        self.assertIsNone(self.tree.find_first(role=AccessibilityRole.GRID))

    def test_snapshot(self):
        self.tree.register(AccessibilityNode(role=AccessibilityRole.BUTTON, label="OK", enabled=True))
        self.tree.register(AccessibilityNode(role=AccessibilityRole.SLIDER, label="Vol", enabled=False,
                                             value_text=lambda: "50%"))
        snap = self.tree.snapshot()
        self.assertEqual(len(snap), 2)
        self.assertEqual(snap[0]["role"], "button")
        self.assertEqual(snap[0]["label"], "OK")
        self.assertTrue(snap[0]["enabled"])
        self.assertEqual(snap[1]["role"], "slider")
        self.assertEqual(snap[1]["value_text"], "50%")
        self.assertFalse(snap[1]["enabled"])


class TestAccessibilityBus(unittest.TestCase):

    def setUp(self):
        self.bus = AccessibilityBus()

    def test_initially_empty(self):
        self.assertEqual(self.bus.pending_count, 0)

    def test_announce_increments_count(self):
        self.bus.announce("Hello")
        self.assertEqual(self.bus.pending_count, 1)

    def test_announce_default_politeness_is_polite(self):
        self.bus.announce("Test")
        announcements = self.bus.consume_announcements()
        self.assertEqual(announcements[0].politeness, LivePoliteness.POLITE)

    def test_announce_assertive(self):
        self.bus.announce("Alert!", politeness=LivePoliteness.ASSERTIVE)
        items = self.bus.consume_announcements()
        self.assertEqual(items[0].politeness, LivePoliteness.ASSERTIVE)

    def test_consume_clears_queue(self):
        self.bus.announce("A")
        self.bus.announce("B")
        items = self.bus.consume_announcements()
        self.assertEqual(len(items), 2)
        self.assertEqual(self.bus.pending_count, 0)

    def test_consume_returns_fifo_order(self):
        self.bus.announce("First")
        self.bus.announce("Second")
        items = self.bus.consume_announcements()
        self.assertEqual(items[0].message, "First")
        self.assertEqual(items[1].message, "Second")

    def test_subscribe_called_on_announce(self):
        received = []
        self.bus.subscribe(received.append)
        self.bus.announce("Ping")
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0].message, "Ping")

    def test_subscribe_returns_unsubscribe(self):
        received = []
        unsub = self.bus.subscribe(received.append)
        self.bus.announce("Before")
        unsub()
        self.bus.announce("After")
        self.assertEqual(len(received), 1)  # Only "Before" received

    def test_subscribe_exception_does_not_propagate(self):
        def bad(_):
            raise RuntimeError("boom")
        self.bus.subscribe(bad)
        self.bus.announce("safe")  # Should not raise

    def test_AccessibilityAnnouncement_dataclass(self):
        a = AccessibilityAnnouncement("msg", LivePoliteness.POLITE)
        self.assertEqual(a.message, "msg")
        self.assertEqual(a.politeness, LivePoliteness.POLITE)


class TestAccessibilityExports(unittest.TestCase):

    def test_importable_from_gui_do(self):
        import gui_do
        self.assertTrue(hasattr(gui_do, "AccessibilityTree"))
        self.assertTrue(hasattr(gui_do, "AccessibilityNode"))
        self.assertTrue(hasattr(gui_do, "AccessibilityRole"))
        self.assertTrue(hasattr(gui_do, "AccessibilityBus"))
        self.assertTrue(hasattr(gui_do, "AccessibilityAnnouncement"))
        self.assertTrue(hasattr(gui_do, "LivePoliteness"))


if __name__ == "__main__":
    unittest.main()
