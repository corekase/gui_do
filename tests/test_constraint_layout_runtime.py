"""Tests for ConstraintLayout (Feature 4)."""
import unittest

from pygame import Rect

from gui_do.layout.constraint_layout import AnchorConstraint, ConstraintLayout, ConstraintBuilder
from gui_do.core.ui_node import UiNode
from gui_do.controls.panel_control import PanelControl


def _node(x=0, y=0, w=50, h=30) -> UiNode:
    return UiNode("n", Rect(x, y, w, h))


def _parent() -> Rect:
    return Rect(0, 0, 400, 300)


class TestLeftOffsetPositionsNode(unittest.TestCase):
    def test_left_offset_positions_node_from_parent_left(self) -> None:
        c = AnchorConstraint(left=8)
        result = c.apply(Rect(0, 0, 50, 30), _parent())
        self.assertEqual(result.x, 8)


class TestRightOffsetPositionsNode(unittest.TestCase):
    def test_right_offset_positions_node_from_parent_right(self) -> None:
        c = AnchorConstraint(right=8)
        result = c.apply(Rect(0, 0, 50, 30), _parent())
        self.assertEqual(result.right, _parent().right - 8)


class TestFillWidthSetsBothEdges(unittest.TestCase):
    def test_fill_width_sets_both_edges(self) -> None:
        c = AnchorConstraint(left=4, right=4)
        result = c.apply(Rect(0, 0, 50, 30), _parent())
        self.assertEqual(result.x, 4)
        self.assertEqual(result.width, 400 - 8)


class TestTopBottomFillHeight(unittest.TestCase):
    def test_top_bottom_fill_height(self) -> None:
        c = AnchorConstraint(top=10, bottom=10)
        result = c.apply(Rect(0, 0, 50, 30), _parent())
        self.assertEqual(result.y, 10)
        self.assertEqual(result.height, 300 - 20)


class TestFractionalLeftPlacement(unittest.TestCase):
    def test_fractional_left_placement(self) -> None:
        c = AnchorConstraint(left_frac=0.25)
        result = c.apply(Rect(0, 0, 50, 30), _parent())
        self.assertEqual(result.x, int(400 * 0.25))


class TestMinWidthClamps(unittest.TestCase):
    def test_min_width_clamps_narrower_result(self) -> None:
        # left=0 right=0 → width=400 normally; then min enforced if it's smaller
        c = AnchorConstraint(left=190, right=190, min_width=50)
        result = c.apply(Rect(0, 0, 50, 30), _parent())
        self.assertGreaterEqual(result.width, 50)


class TestMaxWidthClamps(unittest.TestCase):
    def test_max_width_clamps_wider_result(self) -> None:
        c = AnchorConstraint(left=0, right=0, max_width=100)
        result = c.apply(Rect(0, 0, 50, 30), _parent())
        self.assertLessEqual(result.width, 100)


class TestApplyMutatesNodeRect(unittest.TestCase):
    def test_apply_mutates_node_rect(self) -> None:
        layout = ConstraintLayout()
        node = _node(0, 0, 50, 30)
        layout.add(node, AnchorConstraint(left=20))
        layout.apply(_parent())
        self.assertEqual(node.rect.x, 20)


class TestApplyToReturnsRectWithoutMutation(unittest.TestCase):
    def test_apply_to_returns_rect_without_mutation(self) -> None:
        layout = ConstraintLayout()
        node = _node(0, 0, 50, 30)
        layout.add(node, AnchorConstraint(left=20))
        result = layout.apply_to(node, _parent())
        self.assertEqual(result.x, 20)
        self.assertEqual(node.rect.x, 0)  # unchanged


class TestBuilderFillWidthRegistersConstraint(unittest.TestCase):
    def test_builder_fill_width_registers_constraint(self) -> None:
        layout = ConstraintLayout()
        node = _node()
        builder = ConstraintBuilder(node, layout)
        c = builder.fill_width(left=8, right=8).commit()
        self.assertEqual(c.left, 8)
        self.assertEqual(c.right, 8)
        self.assertTrue(layout.has(node))


class TestPanelControlAppliesConstraintsOnUpdate(unittest.TestCase):
    def test_panel_control_applies_constraints_on_update(self) -> None:
        from gui_do.layout.constraint_layout import ConstraintLayout, AnchorConstraint
        layout = ConstraintLayout()
        inner = UiNode("inner", Rect(0, 0, 50, 30))
        layout.add(inner, AnchorConstraint(left=15))
        panel = PanelControl("p", Rect(0, 0, 400, 300), constraints=layout)
        panel.update(0.016)
        self.assertEqual(inner.rect.x, 15)


class TestMultipleNodesAllUpdated(unittest.TestCase):
    def test_multiple_nodes_all_updated(self) -> None:
        layout = ConstraintLayout()
        nodes = [_node() for _ in range(3)]
        for i, n in enumerate(nodes):
            layout.add(n, AnchorConstraint(top=i * 10))
        layout.apply(_parent())
        for i, n in enumerate(nodes):
            self.assertEqual(n.rect.y, i * 10)


if __name__ == "__main__":
    unittest.main()
