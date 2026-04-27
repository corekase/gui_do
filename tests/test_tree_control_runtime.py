"""Tests for TreeControl and TreeNode."""
import unittest
from unittest.mock import MagicMock
from pygame import Rect

import pygame
pygame.init()
pygame.display.set_mode((1, 1), pygame.NOFRAME)

from gui_do.controls.tree_control import TreeControl, TreeNode, _flatten


class TestTreeNode(unittest.TestCase):

    def test_is_leaf_true_for_no_children(self):
        node = TreeNode("leaf")
        self.assertTrue(node.is_leaf)

    def test_is_leaf_false_with_children(self):
        node = TreeNode("parent", children=[TreeNode("child")])
        self.assertFalse(node.is_leaf)

    def test_flatten_single_level(self):
        nodes = [TreeNode("a"), TreeNode("b")]
        rows = _flatten(nodes)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0].depth, 0)

    def test_flatten_nested_respects_expanded(self):
        child = TreeNode("child")
        parent = TreeNode("parent", children=[child], expanded=True)
        rows = _flatten([parent])
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[1].depth, 1)
        self.assertEqual(rows[1].node, child)

    def test_flatten_collapsed_hides_children(self):
        child = TreeNode("child")
        parent = TreeNode("parent", children=[child], expanded=False)
        rows = _flatten([parent])
        self.assertEqual(len(rows), 1)


class TestTreeControlBasics(unittest.TestCase):

    def _make_tree(self):
        nodes = [
            TreeNode("A", children=[TreeNode("A1"), TreeNode("A2")], expanded=False),
            TreeNode("B"),
        ]
        return TreeControl("tree", Rect(0, 0, 300, 400), nodes)

    def test_initial_row_count_collapsed(self):
        tree = self._make_tree()
        self.assertEqual(len(tree._rows), 2)

    def test_expand_increases_rows(self):
        tree = self._make_tree()
        tree.expand(tree._nodes[0])
        self.assertEqual(len(tree._rows), 4)

    def test_collapse_restores_rows(self):
        tree = self._make_tree()
        tree.expand(tree._nodes[0])
        tree.collapse(tree._nodes[0])
        self.assertEqual(len(tree._rows), 2)

    def test_toggle_expand_collapse(self):
        tree = self._make_tree()
        tree.toggle(tree._nodes[0])
        self.assertTrue(tree._nodes[0].expanded)
        tree.toggle(tree._nodes[0])
        self.assertFalse(tree._nodes[0].expanded)

    def test_select_sets_selected_node(self):
        tree = self._make_tree()
        node = tree._nodes[1]
        tree.select(node)
        self.assertIs(tree.selected_node, node)

    def test_on_select_callback_fired(self):
        selected = []
        tree = self._make_tree()
        tree._on_select = lambda node, idx: selected.append(node)
        tree.expand(tree._nodes[0])
        # Simulate click on first child row (row index 1 after expand)
        from gui_do.core.gui_event import GuiEvent, EventType
        evt = MagicMock()
        evt.kind = EventType.MOUSE_BUTTON_DOWN
        evt.button = 1
        # Click row 1 (child A1) — its y would be row_height after the first row
        row_y = tree.rect.y + 1 * tree._row_height + tree._row_height // 2
        evt.pos = (tree.rect.x + 50, row_y)
        app = MagicMock()
        tree.handle_event(evt, app)
        # A1 should be selected (toggle expand on leaf does nothing, select fires)
        self.assertGreater(len(selected), 0)

    def test_expand_all_collapse_all(self):
        tree = self._make_tree()
        tree.expand_all()
        self.assertTrue(tree._nodes[0].expanded)
        self.assertEqual(len(tree._rows), 4)
        tree.collapse_all()
        self.assertFalse(tree._nodes[0].expanded)
        self.assertEqual(len(tree._rows), 2)

    def test_set_nodes_resets_state(self):
        tree = self._make_tree()
        tree.set_nodes([TreeNode("X")])
        self.assertIsNone(tree.selected_node)
        self.assertEqual(len(tree._rows), 1)

    def test_disabled_ignores_events(self):
        tree = self._make_tree()
        tree.enabled = False
        from gui_do.core.gui_event import EventType
        evt = MagicMock()
        evt.kind = EventType.MOUSE_BUTTON_DOWN
        evt.button = 1
        evt.pos = (10, 10)
        app = MagicMock()
        self.assertFalse(tree.handle_event(evt, app))

    def test_draw_does_not_raise(self):
        tree = self._make_tree()
        surface = pygame.Surface((300, 400))
        theme = MagicMock()
        theme.background = (30, 30, 38)
        theme.text = (220, 220, 220)
        theme.highlight = (0, 100, 200)
        theme.surface = (50, 50, 60)
        theme.medium = (150, 150, 160)
        tree.draw(surface, theme)


if __name__ == "__main__":
    unittest.main()
