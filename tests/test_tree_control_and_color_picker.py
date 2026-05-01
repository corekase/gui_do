"""Tests for TreeControl/TreeNode and ColorPickerControl."""
import unittest

import pygame
from pygame import Rect

from gui_do.controls.data.tree_control import (
    TreeControl, TreeNode, _flatten, _FlatRow
)
from gui_do.controls.input.color_picker_control import ColorPickerControl

pygame.init()


# ===========================================================================
# TreeNode
# ===========================================================================


class TestTreeNode(unittest.TestCase):
    def test_is_leaf_no_children(self):
        n = TreeNode("leaf")
        self.assertTrue(n.is_leaf)

    def test_is_leaf_with_children(self):
        n = TreeNode("parent", children=[TreeNode("child")])
        self.assertFalse(n.is_leaf)

    def test_expanded_default_false(self):
        n = TreeNode("n")
        self.assertFalse(n.expanded)

    def test_enabled_default_true(self):
        n = TreeNode("n")
        self.assertTrue(n.enabled)

    def test_data_default_none(self):
        n = TreeNode("n")
        self.assertIsNone(n.data)

    def test_label_stored(self):
        n = TreeNode("hello")
        self.assertEqual("hello", n.label)


# ===========================================================================
# _flatten helper
# ===========================================================================


class TestFlattenHelper(unittest.TestCase):
    def test_empty_nodes(self):
        self.assertEqual([], _flatten([]))

    def test_flat_list_all_depth_zero(self):
        nodes = [TreeNode("A"), TreeNode("B")]
        rows = _flatten(nodes)
        self.assertEqual(2, len(rows))
        self.assertEqual(0, rows[0].depth)
        self.assertEqual(0, rows[1].depth)

    def test_collapsed_children_not_in_rows(self):
        parent = TreeNode("P", children=[TreeNode("C1"), TreeNode("C2")], expanded=False)
        rows = _flatten([parent])
        self.assertEqual(1, len(rows))

    def test_expanded_children_included(self):
        parent = TreeNode("P", children=[TreeNode("C1"), TreeNode("C2")], expanded=True)
        rows = _flatten([parent])
        self.assertEqual(3, len(rows))  # parent + 2 children

    def test_child_depth_is_one(self):
        parent = TreeNode("P", children=[TreeNode("C")], expanded=True)
        rows = _flatten([parent])
        self.assertEqual(1, rows[1].depth)

    def test_nested_expanded_counts(self):
        grandchild = TreeNode("GC")
        child = TreeNode("C", children=[grandchild], expanded=True)
        parent = TreeNode("P", children=[child], expanded=True)
        rows = _flatten([parent])
        self.assertEqual(3, len(rows))

    def test_grandchild_depth_is_two(self):
        grandchild = TreeNode("GC")
        child = TreeNode("C", children=[grandchild], expanded=True)
        parent = TreeNode("P", children=[child], expanded=True)
        rows = _flatten([parent])
        self.assertEqual(2, rows[2].depth)


# ===========================================================================
# TreeControl — initial state
# ===========================================================================


class TestTreeControlInitial(unittest.TestCase):
    def test_empty_nodes(self):
        tc = TreeControl("tc", Rect(0, 0, 300, 400))
        self.assertEqual([], tc.nodes)

    def test_with_nodes(self):
        nodes = [TreeNode("A"), TreeNode("B")]
        tc = TreeControl("tc", Rect(0, 0, 300, 400), nodes)
        self.assertEqual(2, len(tc.nodes))

    def test_selected_node_none_initially(self):
        tc = TreeControl("tc", Rect(0, 0, 300, 400), [TreeNode("A")])
        self.assertIsNone(tc.selected_node)

    def test_tab_index_zero(self):
        tc = TreeControl("tc", Rect(0, 0, 300, 400))
        self.assertEqual(0, tc.tab_index)

    def test_nodes_returns_copy(self):
        nodes = [TreeNode("A")]
        tc = TreeControl("tc", Rect(0, 0, 300, 400), nodes)
        copy = tc.nodes
        copy.clear()
        self.assertEqual(1, len(tc.nodes))


class TestTreeControlSetNodes(unittest.TestCase):
    def test_set_nodes_replaces(self):
        tc = TreeControl("tc", Rect(0, 0, 300, 400), [TreeNode("old")])
        tc.set_nodes([TreeNode("new1"), TreeNode("new2")])
        self.assertEqual(2, len(tc.nodes))

    def test_set_nodes_clears_selection(self):
        tc = TreeControl("tc", Rect(0, 0, 300, 400), [TreeNode("A")])
        node = tc._nodes[0]
        tc.select(node)
        tc.set_nodes([TreeNode("B")])
        self.assertIsNone(tc.selected_node)


class TestTreeControlExpandCollapse(unittest.TestCase):
    def setUp(self):
        self.child1 = TreeNode("C1")
        self.child2 = TreeNode("C2")
        self.parent = TreeNode("P", children=[self.child1, self.child2])
        self.tc = TreeControl("tc", Rect(0, 0, 300, 400), [self.parent])

    def test_expand_shows_children_in_rows(self):
        self.tc.expand(self.parent)
        self.assertTrue(self.parent.expanded)
        self.assertEqual(3, len(self.tc._rows))  # parent + 2 children

    def test_collapse_hides_children_in_rows(self):
        self.tc.expand(self.parent)
        self.tc.collapse(self.parent)
        self.assertFalse(self.parent.expanded)
        self.assertEqual(1, len(self.tc._rows))

    def test_toggle_expands_collapsed(self):
        self.tc.toggle(self.parent)
        self.assertTrue(self.parent.expanded)

    def test_toggle_collapses_expanded(self):
        self.tc.expand(self.parent)
        self.tc.toggle(self.parent)
        self.assertFalse(self.parent.expanded)

    def test_expand_leaf_no_effect(self):
        leaf = TreeNode("leaf")
        tc = TreeControl("tc", Rect(0, 0, 300, 400), [leaf])
        tc.expand(leaf)
        self.assertFalse(leaf.expanded)

    def test_expand_fires_on_expand_callback(self):
        received = []
        self.tc._on_expand = lambda node, expanded: received.append((node.label, expanded))
        self.tc.expand(self.parent)
        self.assertEqual([("P", True)], received)

    def test_collapse_fires_on_expand_callback(self):
        received = []
        self.tc._on_expand = lambda node, expanded: received.append((node.label, expanded))
        self.parent.expanded = True
        self.tc.collapse(self.parent)
        self.assertEqual([("P", False)], received)


class TestTreeControlExpandAll(unittest.TestCase):
    def test_expand_all(self):
        child = TreeNode("C")
        parent = TreeNode("P", children=[child])
        tc = TreeControl("tc", Rect(0, 0, 300, 400), [parent])
        tc.expand_all()
        self.assertTrue(parent.expanded)
        self.assertEqual(2, len(tc._rows))

    def test_collapse_all(self):
        child = TreeNode("C")
        parent = TreeNode("P", children=[child], expanded=True)
        tc = TreeControl("tc", Rect(0, 0, 300, 400), [parent])
        tc.collapse_all()
        self.assertFalse(parent.expanded)
        self.assertEqual(1, len(tc._rows))


class TestTreeControlSelect(unittest.TestCase):
    def test_select_node(self):
        node = TreeNode("A")
        tc = TreeControl("tc", Rect(0, 0, 300, 400), [node])
        tc.select(node)
        self.assertIs(node, tc.selected_node)

    def test_select_none_clears(self):
        node = TreeNode("A")
        tc = TreeControl("tc", Rect(0, 0, 300, 400), [node])
        tc.select(node)
        tc.select(None)
        self.assertIsNone(tc.selected_node)


# ===========================================================================
# ColorPickerControl
# ===========================================================================


class TestColorPickerControlInitial(unittest.TestCase):
    def test_initial_color_stored(self):
        cp = ColorPickerControl("cp", Rect(0, 0, 220, 200), color=(255, 128, 0))
        r, g, b = cp.color
        self.assertEqual(255, r)
        self.assertGreater(g, 0)  # orange has green component
        self.assertEqual(0, b)    # orange has no blue

    def test_default_color_red(self):
        cp = ColorPickerControl("cp", Rect(0, 0, 220, 200))
        self.assertEqual((255, 0, 0), cp.color)

    def test_tab_index_zero(self):
        cp = ColorPickerControl("cp", Rect(0, 0, 220, 200))
        self.assertEqual(0, cp.tab_index)

    def test_on_change_stored(self):
        handler = lambda rgb: None
        cp = ColorPickerControl("cp", Rect(0, 0, 220, 200), on_change=handler)
        self.assertIs(handler, cp.on_change)

    def test_hex_text_initialized(self):
        cp = ColorPickerControl("cp", Rect(0, 0, 220, 200), color=(255, 0, 0))
        self.assertEqual("#ff0000", cp._hex_text)

    def test_hex_editing_false_initially(self):
        cp = ColorPickerControl("cp", Rect(0, 0, 220, 200))
        self.assertFalse(cp._hex_editing)


class TestColorPickerControlColorSetter(unittest.TestCase):
    def test_set_color_updates(self):
        cp = ColorPickerControl("cp", Rect(0, 0, 220, 200))
        cp.color = (0, 255, 0)
        self.assertEqual((0, 255, 0), cp.color)

    def test_set_color_updates_hex_text(self):
        cp = ColorPickerControl("cp", Rect(0, 0, 220, 200))
        cp.color = (0, 255, 0)
        self.assertEqual("#00ff00", cp._hex_text)

    def test_set_color_clamped(self):
        cp = ColorPickerControl("cp", Rect(0, 0, 220, 200))
        cp.color = (300, -10, 128)
        r, g, b = cp.color
        self.assertLessEqual(r, 255)
        self.assertGreaterEqual(g, 0)


class TestColorPickerControlHexHelpers(unittest.TestCase):
    def test_rgb_to_hex_black(self):
        self.assertEqual("#000000", ColorPickerControl._rgb_to_hex(0, 0, 0))

    def test_rgb_to_hex_white(self):
        self.assertEqual("#ffffff", ColorPickerControl._rgb_to_hex(255, 255, 255))

    def test_rgb_to_hex_red(self):
        self.assertEqual("#ff0000", ColorPickerControl._rgb_to_hex(255, 0, 0))


class TestColorPickerControlCommitHex(unittest.TestCase):
    def test_commit_valid_hex(self):
        cp = ColorPickerControl("cp", Rect(0, 0, 220, 200))
        cp._hex_text = "#0000ff"
        cp._hex_editing = True
        cp._commit_hex()
        r, g, b = cp.color
        self.assertEqual(0, r)
        self.assertEqual(0, g)
        self.assertEqual(255, b)
        self.assertFalse(cp._hex_editing)

    def test_commit_invalid_hex_sets_error(self):
        cp = ColorPickerControl("cp", Rect(0, 0, 220, 200))
        cp._hex_text = "#xyz"
        cp._hex_editing = True
        cp._commit_hex()
        self.assertTrue(cp._hex_error)

    def test_commit_hex_fires_on_change(self):
        received = []
        cp = ColorPickerControl("cp", Rect(0, 0, 220, 200),
                                on_change=lambda rgb: received.append(rgb))
        cp._hex_text = "#00ff00"
        cp._hex_editing = True
        cp._commit_hex()
        self.assertEqual(1, len(received))

    def test_accepts_focus(self):
        cp = ColorPickerControl("cp", Rect(0, 0, 220, 200))
        cp.visible = True
        cp.enabled = True
        self.assertTrue(cp.accepts_focus())


if __name__ == "__main__":
    unittest.main()
