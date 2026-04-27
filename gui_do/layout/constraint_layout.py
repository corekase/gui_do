"""ConstraintLayout — anchor-based rect derivation from parent edges."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, TYPE_CHECKING

from pygame import Rect

if TYPE_CHECKING:
    from ..core.ui_node import UiNode


@dataclass
class AnchorConstraint:
    """Describes how a node's rect is derived from its parent's rect."""

    # Fixed pixel offsets from parent edges (None = unconstrained)
    left: Optional[int] = None
    right: Optional[int] = None
    top: Optional[int] = None
    bottom: Optional[int] = None

    # Fractional placement (0.0..1.0 of parent dimension)
    left_frac: Optional[float] = None
    right_frac: Optional[float] = None
    top_frac: Optional[float] = None
    bottom_frac: Optional[float] = None

    # Size constraints (applied after edges)
    min_width: Optional[int] = None
    max_width: Optional[int] = None
    min_height: Optional[int] = None
    max_height: Optional[int] = None

    def apply(self, node_rect: Rect, parent_rect: Rect) -> Rect:
        """Return a new Rect for node given parent_rect. Does not mutate."""
        pw = parent_rect.width
        ph = parent_rect.height

        # --- Horizontal resolution ---
        if self.left is not None:
            new_left = parent_rect.left + int(self.left)
        elif self.left_frac is not None:
            new_left = parent_rect.left + int(pw * self.left_frac)
        else:
            new_left = node_rect.left

        if self.right is not None:
            new_right = parent_rect.right - int(self.right)
        elif self.right_frac is not None:
            new_right = parent_rect.right - int(pw * self.right_frac)
        else:
            new_right = node_rect.right

        if self.left is not None or self.left_frac is not None:
            if self.right is not None or self.right_frac is not None:
                new_width = new_right - new_left
            else:
                new_width = node_rect.width
        elif self.right is not None or self.right_frac is not None:
            new_width = node_rect.width
            new_left = new_right - new_width
        else:
            new_width = node_rect.width
            new_left = node_rect.left

        # --- Vertical resolution ---
        if self.top is not None:
            new_top = parent_rect.top + int(self.top)
        elif self.top_frac is not None:
            new_top = parent_rect.top + int(ph * self.top_frac)
        else:
            new_top = node_rect.top

        if self.bottom is not None:
            new_bottom = parent_rect.bottom - int(self.bottom)
        elif self.bottom_frac is not None:
            new_bottom = parent_rect.bottom - int(ph * self.bottom_frac)
        else:
            new_bottom = node_rect.bottom

        if self.top is not None or self.top_frac is not None:
            if self.bottom is not None or self.bottom_frac is not None:
                new_height = new_bottom - new_top
            else:
                new_height = node_rect.height
        elif self.bottom is not None or self.bottom_frac is not None:
            new_height = node_rect.height
            new_top = new_bottom - new_height
        else:
            new_height = node_rect.height
            new_top = node_rect.top

        # --- Size clamps ---
        if self.min_width is not None:
            new_width = max(new_width, int(self.min_width))
        if self.max_width is not None:
            new_width = min(new_width, int(self.max_width))
        if self.min_height is not None:
            new_height = max(new_height, int(self.min_height))
        if self.max_height is not None:
            new_height = min(new_height, int(self.max_height))

        return Rect(new_left, new_top, new_width, new_height)


class ConstraintLayout:
    """Applies AnchorConstraints for registered nodes relative to a parent rect."""

    def __init__(self) -> None:
        self._nodes: List["UiNode"] = []
        self._constraints: Dict[int, AnchorConstraint] = {}

    def add(self, node: "UiNode", constraint: AnchorConstraint) -> None:
        """Register a node with a constraint."""
        nid = id(node)
        if nid not in self._constraints:
            self._nodes.append(node)
        self._constraints[nid] = constraint

    def remove(self, node: "UiNode") -> bool:
        """Remove a node from the layout. Returns True if it was registered."""
        nid = id(node)
        if nid not in self._constraints:
            return False
        del self._constraints[nid]
        self._nodes = [n for n in self._nodes if n is not node]
        return True

    def has(self, node: "UiNode") -> bool:
        return id(node) in self._constraints

    def apply(self, parent_rect: Rect) -> None:
        """Recompute and mutate rect of all registered nodes."""
        for node in self._nodes:
            nid = id(node)
            constraint = self._constraints.get(nid)
            if constraint is None:
                continue
            new_rect = constraint.apply(node.rect, parent_rect)
            node.rect = new_rect

    def apply_to(self, node: "UiNode", parent_rect: Rect) -> Rect:
        """Return resolved rect for one node without mutating."""
        nid = id(node)
        constraint = self._constraints.get(nid)
        if constraint is None:
            return Rect(node.rect)
        return constraint.apply(node.rect, parent_rect)

    def node_count(self) -> int:
        return len(self._nodes)


class ConstraintBuilder:
    """Fluent builder API for constructing an AnchorConstraint and registering it."""

    def __init__(self, node: "UiNode", layout: ConstraintLayout) -> None:
        self._node = node
        self._layout = layout
        self._c = AnchorConstraint()

    def left(self, pixels: int = 0) -> "ConstraintBuilder":
        self._c.left = int(pixels)
        return self

    def right(self, pixels: int = 0) -> "ConstraintBuilder":
        self._c.right = int(pixels)
        return self

    def top(self, pixels: int = 0) -> "ConstraintBuilder":
        self._c.top = int(pixels)
        return self

    def bottom(self, pixels: int = 0) -> "ConstraintBuilder":
        self._c.bottom = int(pixels)
        return self

    def fill_width(self, left: int = 0, right: int = 0) -> "ConstraintBuilder":
        """Constrain both left and right edges."""
        self._c.left = int(left)
        self._c.right = int(right)
        return self

    def fill_height(self, top: int = 0, bottom: int = 0) -> "ConstraintBuilder":
        """Constrain both top and bottom edges."""
        self._c.top = int(top)
        self._c.bottom = int(bottom)
        return self

    def min_width(self, pixels: int) -> "ConstraintBuilder":
        self._c.min_width = int(pixels)
        return self

    def max_width(self, pixels: int) -> "ConstraintBuilder":
        self._c.max_width = int(pixels)
        return self

    def min_height(self, pixels: int) -> "ConstraintBuilder":
        self._c.min_height = int(pixels)
        return self

    def max_height(self, pixels: int) -> "ConstraintBuilder":
        self._c.max_height = int(pixels)
        return self

    def commit(self) -> AnchorConstraint:
        """Register the built constraint and return it."""
        self._layout.add(self._node, self._c)
        return self._c
