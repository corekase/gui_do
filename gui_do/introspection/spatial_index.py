"""SceneSpatialIndex — grid-based spatial index for scene graph hit-testing.

Maintains a uniform grid over the screen area.  Each cell stores references
to :class:`~gui_do.UiNode` instances whose bounding rects overlap that cell.
:meth:`query_point` and :meth:`query_rect` return nodes in back-to-front
order (scene graph order), enabling O(1) average-case hit-testing and range
queries for rubber-band selection, drag-drop zone detection, and tooltip
resolution.

Usage::

    from gui_do import SceneSpatialIndex

    index = SceneSpatialIndex(cell_size=64)

    # Build from the current active scene:
    index.build(app.scene)

    # Point hit-test:
    nodes = index.query_point(mx, my)

    # Rect range query (e.g. rubber-band selection):
    selected = index.query_rect(selection_rect)

    # Incremental update when one node moves:
    index.update_node(my_node)

    # Full rebuild on scene change:
    index.build(app.scene)
"""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Set, Tuple, TYPE_CHECKING

from pygame import Rect

if TYPE_CHECKING:
    pass  # UiNode imported at call time to avoid circular imports


# ---------------------------------------------------------------------------
# SceneSpatialIndex
# ---------------------------------------------------------------------------


class SceneSpatialIndex:
    """Uniform-grid spatial index for fast point and rect queries.

    Parameters
    ----------
    cell_size:
        Width and height of each grid cell in pixels (default 64).  Smaller
        values trade memory for more granular queries; larger values reduce
        rebuild cost.
    """

    def __init__(self, cell_size: int = 64) -> None:
        self._cell_size = max(1, int(cell_size))
        # cell (col, row) -> list of node control_ids (in insertion/BFS order)
        self._cells: Dict[Tuple[int, int], List[str]] = defaultdict(list)
        # control_id -> node reference
        self._nodes: Dict[str, object] = {}
        # control_id -> set of cells it occupies
        self._node_cells: Dict[str, Set[Tuple[int, int]]] = {}
        # Monotonically increasing counter — assigned to each new node as a
        # stable sort key.  Stale values after removal still give correct
        # relative ordering since removed nodes no longer appear in _nodes.
        self._insert_counter: int = 0
        # control_id -> insertion-order index; used as sort key in queries so
        # we can iterate only the candidate set instead of all nodes.
        self._order_index: Dict[str, int] = {}

    # ------------------------------------------------------------------
    # Build / rebuild
    # ------------------------------------------------------------------

    def build(self, scene: object) -> None:
        """Rebuild the index from all nodes reachable in *scene*.

        *scene* must expose a ``_walk_nodes()`` generator as
        :class:`~gui_do.Scene` does.
        """
        self.clear()
        if scene is None:
            return
        for node in scene._walk_nodes():   # noqa: SLF001
            self._insert(node)

    def clear(self) -> None:
        """Remove all entries from the index."""
        self._cells.clear()
        self._nodes.clear()
        self._node_cells.clear()
        self._insert_counter = 0
        self._order_index.clear()

    # ------------------------------------------------------------------
    # Incremental update
    # ------------------------------------------------------------------

    def update_node(self, node: object) -> None:
        """Re-insert one node after its rect has changed.

        If the node is not in the index it is added.
        """
        cid = getattr(node, "control_id", None)
        if cid is None:
            return
        # Remove old cells
        old_cells = self._node_cells.pop(cid, set())
        for cell in old_cells:
            try:
                self._cells[cell].remove(cid)
            except (KeyError, ValueError):
                pass
        # Re-insert
        self._insert(node)

    def remove_node(self, node: object) -> None:
        """Remove a single node from the index."""
        cid = getattr(node, "control_id", None)
        if cid is None:
            return
        old_cells = self._node_cells.pop(cid, set())
        for cell in old_cells:
            try:
                self._cells[cell].remove(cid)
            except (KeyError, ValueError):
                pass
        self._nodes.pop(cid, None)
        self._order_index.pop(cid, None)

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def query_point(self, x: int, y: int) -> list:
        """Return all visible, enabled nodes whose rect contains ``(x, y)``.

        Results are in back-to-front scene-graph order.
        """
        cell = self._cell_for(x, y)
        candidates = self._cells.get(cell)
        if not candidates:
            return []
        order_index = self._order_index
        results = []
        for cid in candidates:
            node = self._nodes.get(cid)
            if node is None:
                continue
            if self._node_visible(node) and self._rect(node).collidepoint(x, y):
                results.append(node)
        if len(results) > 1:
            results.sort(key=lambda n: order_index.get(getattr(n, "control_id", ""), 0))
        return results

    def query_rect(self, rect) -> list:
        """Return all visible, enabled nodes whose rects overlap *rect*.

        Results are in back-to-front scene-graph order.
        """
        r = Rect(rect)
        touched_cells = self._cells_for_rect(r)
        candidate_set: Set[str] = set()
        for cell in touched_cells:
            candidate_set.update(self._cells.get(cell, []))
        if not candidate_set:
            return []
        order_index = self._order_index
        results = []
        for cid in candidate_set:
            node = self._nodes.get(cid)
            if node is None:
                continue
            if self._node_visible(node) and self._rect(node).colliderect(r):
                results.append(node)
        if len(results) > 1:
            results.sort(key=lambda n: order_index.get(getattr(n, "control_id", ""), 0))
        return results

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _insert(self, node: object) -> None:
        cid = getattr(node, "control_id", None)
        if cid is None:
            return
        r = self._rect(node)
        cells = self._cells_for_rect(r)
        self._nodes[cid] = node
        self._node_cells[cid] = cells
        for cell in cells:
            self._cells[cell].append(cid)
        if cid not in self._order_index:
            self._order_index[cid] = self._insert_counter
            self._insert_counter += 1

    def _rect(self, node: object) -> Rect:
        r = getattr(node, "rect", None)
        if r is None:
            return Rect(0, 0, 0, 0)
        return Rect(r)

    def _node_visible(self, node: object) -> bool:
        return getattr(node, "visible", True) and getattr(node, "enabled", True)

    def _cell_for(self, x: int, y: int) -> Tuple[int, int]:
        cs = self._cell_size
        return (int(x) // cs, int(y) // cs)

    def _cells_for_rect(self, r: Rect) -> Set[Tuple[int, int]]:
        cs = self._cell_size
        col_min = r.left // cs
        col_max = max(col_min, (r.right - 1) // cs)
        row_min = r.top // cs
        row_max = max(row_min, (r.bottom - 1) // cs)
        result: Set[Tuple[int, int]] = set()
        for col in range(col_min, col_max + 1):
            for row in range(row_min, row_max + 1):
                result.add((col, row))
        return result

    # ------------------------------------------------------------------
    # Inspection
    # ------------------------------------------------------------------

    @property
    def node_count(self) -> int:
        """Number of nodes currently indexed."""
        return len(self._nodes)

    @property
    def cell_size(self) -> int:
        """Grid cell size in pixels."""
        return self._cell_size
