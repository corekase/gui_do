from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple, Union, TYPE_CHECKING

from pygame import Rect

if TYPE_CHECKING:
    from ..core.ui_node import UiNode
    from .constraint_layout import ConstraintLayout, AnchorConstraint, ConstraintBuilder


Geometry = Union[Rect, Tuple[int, int]]


@dataclass
class _LinearConfig:
    anchor: Tuple[int, int] = (0, 0)
    width: int = 100
    height: int = 40
    spacing: int = 8
    horizontal: bool = True
    wrap_count: int = 0
    use_rect: bool = True


@dataclass
class _GridConfig:
    anchor: Tuple[int, int] = (0, 0)
    width: int = 100
    height: int = 40
    column_spacing: int = 8
    row_spacing: int = 8
    use_rect: bool = True


class LayoutManager:
    """Grid, linear, and anchor layout helpers for controls."""

    def __init__(self) -> None:
        self._linear = _LinearConfig()
        self._linear_cursor = 0
        self._grid = _GridConfig()
        self._grid_cursor = 0
        self._anchor_bounds = Rect(0, 0, 1, 1)

    def set_linear_properties(
        self,
        anchor: Tuple[int, int],
        item_width: int,
        item_height: int,
        spacing: int,
        horizontal: bool = True,
        wrap_count: int = 0,
        use_rect: bool = True,
    ) -> None:
        self._linear = _LinearConfig(anchor, int(item_width), int(item_height), int(spacing), bool(horizontal), int(wrap_count), bool(use_rect))
        self._linear_cursor = 0

    def linear(self, index: int) -> Geometry:
        x = int(index)
        y = 0
        if self._linear.wrap_count > 0:
            y = x // self._linear.wrap_count
            x = x % self._linear.wrap_count
        if not self._linear.horizontal:
            x, y = y, x
        px = self._linear.anchor[0] + (x * (self._linear.width + self._linear.spacing))
        py = self._linear.anchor[1] + (y * (self._linear.height + self._linear.spacing))
        if self._linear.use_rect:
            return Rect(px, py, self._linear.width, self._linear.height)
        return (px, py)

    def next_linear(self) -> Geometry:
        geo = self.linear(self._linear_cursor)
        self._linear_cursor += 1
        return geo

    def set_grid_properties(
        self,
        *,
        anchor: Tuple[int, int],
        item_width: int,
        item_height: int,
        column_spacing: int,
        row_spacing: int,
        use_rect: bool = True,
    ) -> None:
        self._grid = _GridConfig(
            anchor=(int(anchor[0]), int(anchor[1])),
            width=int(item_width),
            height=int(item_height),
            column_spacing=int(column_spacing),
            row_spacing=int(row_spacing),
            use_rect=bool(use_rect),
        )
        self._grid_cursor = 0

    def gridded(self, column: int, row: int, column_span: int = 1, row_span: int = 1) -> Geometry:
        col = int(column)
        row_idx = int(row)
        col_span = max(1, int(column_span))
        row_span_count = max(1, int(row_span))
        px = self._grid.anchor[0] + (col * (self._grid.width + self._grid.column_spacing))
        py = self._grid.anchor[1] + (row_idx * (self._grid.height + self._grid.row_spacing))
        width = (self._grid.width * col_span) + (self._grid.column_spacing * (col_span - 1))
        height = (self._grid.height * row_span_count) + (self._grid.row_spacing * (row_span_count - 1))
        if self._grid.use_rect:
            return Rect(px, py, width, height)
        return (px, py)

    def next_gridded(self, columns: int) -> Geometry:
        col_count = max(1, int(columns))
        index = self._grid_cursor
        self._grid_cursor += 1
        row = index // col_count
        col = index % col_count
        return self.gridded(col, row)

    def set_anchor_bounds(self, bounds: Rect) -> None:
        self._anchor_bounds = Rect(bounds)

    def anchored(
        self,
        size: Tuple[int, int],
        anchor: str = "center",
        margin: Tuple[int, int] = (0, 0),
        use_rect: bool = True,
    ) -> Geometry:
        width, height = int(size[0]), int(size[1])
        rect = Rect(0, 0, width, height)
        bounds = self._anchor_bounds
        dx, dy = int(margin[0]), int(margin[1])
        if anchor == "top_left":
            rect.topleft = (bounds.left + dx, bounds.top + dy)
        elif anchor == "top_center":
            rect.midtop = (bounds.centerx + dx, bounds.top + dy)
        elif anchor == "top_right":
            rect.topright = (bounds.right - dx, bounds.top + dy)
        elif anchor == "center_left":
            rect.midleft = (bounds.left + dx, bounds.centery + dy)
        elif anchor == "center_right":
            rect.midright = (bounds.right - dx, bounds.centery + dy)
        elif anchor == "bottom_left":
            rect.bottomleft = (bounds.left + dx, bounds.bottom - dy)
        elif anchor == "bottom_center":
            rect.midbottom = (bounds.centerx + dx, bounds.bottom - dy)
        elif anchor == "bottom_right":
            rect.bottomright = (bounds.right - dx, bounds.bottom - dy)
        else:
            rect.center = bounds.center
            rect.x += dx
            rect.y += dy
        if use_rect:
            return rect
        return rect.topleft

    def constrain(
        self,
        node: "UiNode",
        parent_rect: Rect,
        *,
        left: Optional[int] = None,
        right: Optional[int] = None,
        top: Optional[int] = None,
        bottom: Optional[int] = None,
        min_width: Optional[int] = None,
        max_width: Optional[int] = None,
        min_height: Optional[int] = None,
        max_height: Optional[int] = None,
    ) -> Rect:
        """One-shot: resolve and return constrained rect for node."""
        from .constraint_layout import AnchorConstraint
        c = AnchorConstraint(
            left=left, right=right, top=top, bottom=bottom,
            min_width=min_width, max_width=max_width,
            min_height=min_height, max_height=max_height,
        )
        return c.apply(node.rect, parent_rect)

    def anchor(self, node: "UiNode", layout: "ConstraintLayout") -> "ConstraintBuilder":
        """Start a fluent constraint builder for node within layout."""
        from .constraint_layout import ConstraintBuilder
        return ConstraintBuilder(node, layout)
