from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Tuple, Union, TYPE_CHECKING

from pygame import Rect

from .rect_source import LayoutRect, RectSource, resolve_rect

if TYPE_CHECKING:
    from ..controls.base.ui_node import UiNode
    from .constraint_layout import ConstraintLayout, ConstraintBuilder


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


@dataclass
class _ColumnFlowConfig:
    bounds: Rect = field(default_factory=lambda: Rect(0, 0, 1, 1))
    overall_rows: int = 5
    overall_columns: int = 2
    column_spacing: int = 8
    row_spacing: int = 8


class LayoutManager:
    """Grid, linear, and anchor layout helpers for controls."""

    def __init__(self) -> None:
        self._linear = _LinearConfig()
        self._linear_cursor = 0
        self._grid = _GridConfig()
        self._grid_cursor = 0
        self._anchor_bounds = Rect(0, 0, 1, 1)
        self._column_flow = _ColumnFlowConfig()
        self._column_flow_x_counter = 0
        self._column_flow_y_counter = 0
        self._column_flow_rows_per_band = 5
        self._column_flow_cols_per_band = 2
        self._column_flow_cell_w = 1
        self._column_flow_cell_h = 1

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

    def set_anchor_bounds(self, bounds: RectSource) -> None:
        self._anchor_bounds = resolve_rect(bounds)

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
        parent_rect: RectSource,
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
        return c.apply(node.rect, resolve_rect(parent_rect))

    def anchor(self, node: "UiNode", layout: "ConstraintLayout") -> "ConstraintBuilder":
        """Start a fluent constraint builder for node within layout."""
        from .constraint_layout import ConstraintBuilder
        return ConstraintBuilder(node, layout)

    def set_column_flow_properties(
        self,
        *,
        bounds: RectSource,
        overall_rows: int,
        overall_columns: int,
        column_spacing: int = 8,
        row_spacing: int = 8,
    ) -> None:
        """Configure boundary-aware column flow layout.

        The layout area is split into a conceptual grid where
        ``x_columns = width / overall_rows`` and
        ``y_columns = height / overall_columns``.
        """
        rows = max(1, int(overall_rows))
        cols = max(1, int(overall_columns))
        gap_x = max(0, int(column_spacing))
        gap_y = max(0, int(row_spacing))
        box = resolve_rect(bounds)
        self._column_flow = _ColumnFlowConfig(
            bounds=box,
            overall_rows=rows,
            overall_columns=cols,
            column_spacing=gap_x,
            row_spacing=gap_y,
        )
        self._column_flow_x_counter = 0
        self._column_flow_y_counter = 0
        self._column_flow_rows_per_band = rows
        self._column_flow_cols_per_band = cols

        total_gap_x = gap_x * max(0, rows - 1)
        total_gap_y = gap_y * max(0, cols - 1)
        self._column_flow_cell_w = max(1, (box.width - total_gap_x) // rows)
        self._column_flow_cell_h = max(1, (box.height - total_gap_y) // cols)

    def column_flow_anchor(self, column_span: int = 1) -> Rect:
        """Return the current anchor rect and advance the x counter.

        Wrapping behavior:
        - If the next column would exceed the configured row count, move to the
          next row band and reset x counter.
        - The returned rect height equals one flow cell height.
        """
        span = max(1, int(column_span))
        if self._column_flow_x_counter + span > self._column_flow_rows_per_band:
            self._column_flow_x_counter = 0
            self._column_flow_y_counter += 1

        box = self._column_flow.bounds
        x = box.left + (self._column_flow_x_counter * (self._column_flow_cell_w + self._column_flow.column_spacing))
        y = box.top + (self._column_flow_y_counter * (self._column_flow_cell_h + self._column_flow.row_spacing))
        w = (self._column_flow_cell_w * span) + (self._column_flow.column_spacing * (span - 1))
        h = self._column_flow_cell_h

        self._column_flow_x_counter += span
        return Rect(x, y, w, h)

    def column_flow_anchors(self, count: int, column_span: int = 1) -> tuple[Rect, ...]:
        """Return multiple sequential column-flow anchors in one call."""
        total = max(0, int(count))
        span = max(1, int(column_span))
        return tuple(self.column_flow_anchor(span) for _ in range(total))

    @classmethod
    def column_flow_anchors_for(
        cls,
        bounds: RectSource,
        count: int,
        *,
        overall_rows: int,
        overall_columns: int,
        column_spacing: int = 8,
        row_spacing: int = 8,
        column_span: int = 1,
    ) -> "tuple[Rect, ...]":
        """Create a temporary layout, configure column flow, and return anchors.

        One-shot alternative to the create-configure-query pattern::

            # Before:
            flow = LayoutManager()
            flow.set_column_flow_properties(bounds=b, overall_rows=7, ...)
            anchors = flow.column_flow_anchors(8)

            # After:
            anchors = LayoutManager.column_flow_anchors_for(b, 8, overall_rows=7, ...)
        """
        mgr = cls()
        mgr.set_column_flow_properties(
            bounds=resolve_rect(bounds),
            overall_rows=int(overall_rows),
            overall_columns=int(overall_columns),
            column_spacing=int(column_spacing),
            row_spacing=int(row_spacing),
        )
        return mgr.column_flow_anchors(int(count), int(column_span))

    @staticmethod
    def as_layout_rect(source: RectSource) -> LayoutRect:
        """Wrap a rect source into a lazy provider for nested composition."""
        return LayoutRect.from_source(source)

    def column_flow_next_row(self) -> None:
        """Advance to a new row band and reset horizontal column cursor."""
        self._column_flow_x_counter = 0
        self._column_flow_y_counter += 1

    @property
    def x_columns_counter(self) -> int:
        """Current horizontal column counter for column-flow layout."""
        return self._column_flow_x_counter

    @property
    def y_columns_counter(self) -> int:
        """Current vertical band counter for column-flow layout."""
        return self._column_flow_y_counter
