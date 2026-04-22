"""Tests for Scene.find / find_all / node_count and UiNode tree traversal helpers."""
import unittest

from pygame import Rect

from gui.core.scene import Scene
from gui.core.ui_node import UiNode


def _node(control_id: str, rect=None) -> UiNode:
    return UiNode(control_id, rect or Rect(0, 0, 10, 10))


class SceneFindTests(unittest.TestCase):
    """Scene.find, Scene.find_all, Scene.node_count."""

    def setUp(self) -> None:
        self.scene = Scene()
        self.root_a = _node("a")
        self.root_b = _node("b")
        # a has two children; child_a2 has a grandchild
        self.child_a1 = _node("a1")
        self.child_a2 = _node("a2")
        self.grandchild = _node("gc")
        self.child_a1.children.append(self.grandchild)
        self.grandchild.parent = self.child_a1
        self.root_a.children.extend([self.child_a1, self.child_a2])
        self.child_a1.parent = self.root_a
        self.child_a2.parent = self.root_a
        self.scene.add(self.root_a)
        self.scene.add(self.root_b)

    # --- find ---

    def test_find_returns_direct_root_node(self) -> None:
        self.assertIs(self.scene.find("a"), self.root_a)
        self.assertIs(self.scene.find("b"), self.root_b)

    def test_find_returns_child_node(self) -> None:
        self.assertIs(self.scene.find("a1"), self.child_a1)
        self.assertIs(self.scene.find("a2"), self.child_a2)

    def test_find_returns_grandchild_node(self) -> None:
        self.assertIs(self.scene.find("gc"), self.grandchild)

    def test_find_returns_none_for_missing_id(self) -> None:
        self.assertIsNone(self.scene.find("nonexistent"))

    def test_find_empty_scene_returns_none(self) -> None:
        self.assertIsNone(Scene().find("x"))

    # --- find_all ---

    def test_find_all_matches_predicate(self) -> None:
        result = self.scene.find_all(lambda n: n.control_id.startswith("a"))
        ids = {n.control_id for n in result}
        self.assertEqual(ids, {"a", "a1", "a2"})

    def test_find_all_returns_empty_list_when_no_match(self) -> None:
        result = self.scene.find_all(lambda n: n.control_id == "zzz")
        self.assertEqual(result, [])

    def test_find_all_returns_all_nodes_for_always_true(self) -> None:
        result = self.scene.find_all(lambda n: True)
        # a, a1, gc (grandchild of a1), a2, b
        self.assertEqual(len(result), 5)

    def test_find_all_order_is_bfs(self) -> None:
        result = self.scene.find_all(lambda n: True)
        ids = [n.control_id for n in result]
        # BFS: a, b, a1, a2, gc
        self.assertEqual(ids, ["a", "b", "a1", "a2", "gc"])

    # --- node_count ---

    def test_node_count_includes_root_and_descendants(self) -> None:
        self.assertEqual(self.scene.node_count(), 5)

    def test_node_count_empty_scene(self) -> None:
        self.assertEqual(Scene().node_count(), 0)

    def test_node_count_scene_with_flat_roots_only(self) -> None:
        s = Scene()
        s.add(_node("x"))
        s.add(_node("y"))
        self.assertEqual(s.node_count(), 2)


class UiNodeAncestorsTests(unittest.TestCase):
    """UiNode.ancestors() generator."""

    def _chain(self, ids):
        nodes = [_node(i) for i in ids]
        for parent, child in zip(nodes, nodes[1:]):
            child.parent = parent
            parent.children.append(child)
        return nodes

    def test_ancestors_yields_parent_chain_in_order(self) -> None:
        root, mid, leaf = self._chain(["root", "mid", "leaf"])
        result = list(leaf.ancestors())
        self.assertEqual([n.control_id for n in result], ["mid", "root"])

    def test_ancestors_stops_at_none_parent(self) -> None:
        root, child = self._chain(["root", "child"])
        result = list(child.ancestors())
        self.assertEqual(result, [root])

    def test_ancestors_empty_when_no_parent(self) -> None:
        node = _node("solo")
        self.assertEqual(list(node.ancestors()), [])

    def test_ancestors_single_depth(self) -> None:
        parent = _node("p")
        child = _node("c")
        child.parent = parent
        result = list(child.ancestors())
        self.assertEqual(result, [parent])


class UiNodeFindDescendantTests(unittest.TestCase):
    """UiNode.find_descendant(id) and UiNode.find_descendants(predicate)."""

    def setUp(self) -> None:
        self.root = _node("root")
        self.a = _node("a")
        self.b = _node("b")
        self.c = _node("c")
        self.d = _node("d")
        # root -> a, b; a -> c; c -> d
        self.root.children = [self.a, self.b]
        self.a.parent = self.root
        self.b.parent = self.root
        self.a.children = [self.c]
        self.c.parent = self.a
        self.c.children = [self.d]
        self.d.parent = self.c

    # --- find_descendant ---

    def test_find_descendant_returns_direct_child(self) -> None:
        self.assertIs(self.root.find_descendant("a"), self.a)
        self.assertIs(self.root.find_descendant("b"), self.b)

    def test_find_descendant_returns_deep_descendant(self) -> None:
        self.assertIs(self.root.find_descendant("d"), self.d)

    def test_find_descendant_returns_none_for_missing_id(self) -> None:
        self.assertIsNone(self.root.find_descendant("zzz"))

    def test_find_descendant_does_not_match_self(self) -> None:
        self.assertIsNone(self.root.find_descendant("root"))

    def test_find_descendant_from_leaf_returns_none(self) -> None:
        self.assertIsNone(self.d.find_descendant("a"))

    def test_find_descendant_from_mid_node(self) -> None:
        self.assertIs(self.a.find_descendant("d"), self.d)
        self.assertIsNone(self.a.find_descendant("b"))

    # --- find_descendants ---

    def test_find_descendants_returns_all_matching(self) -> None:
        results = self.root.find_descendants(lambda n: n.control_id in ("a", "d"))
        ids = {n.control_id for n in results}
        self.assertEqual(ids, {"a", "d"})

    def test_find_descendants_returns_empty_when_no_match(self) -> None:
        self.assertEqual(self.root.find_descendants(lambda n: False), [])

    def test_find_descendants_returns_all_for_always_true(self) -> None:
        results = self.root.find_descendants(lambda n: True)
        ids = {n.control_id for n in results}
        self.assertEqual(ids, {"a", "b", "c", "d"})

    def test_find_descendants_order_is_bfs(self) -> None:
        results = self.root.find_descendants(lambda n: True)
        ids = [n.control_id for n in results]
        # BFS from root's children: a, b, c, d
        self.assertEqual(ids, ["a", "b", "c", "d"])

    def test_find_descendants_does_not_include_self(self) -> None:
        results = self.root.find_descendants(lambda n: True)
        self.assertNotIn(self.root, results)


if __name__ == "__main__":
    unittest.main()
