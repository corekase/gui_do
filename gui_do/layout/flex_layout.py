"""FlexLayout — row/column flow layout with grow, shrink, gap, and alignment."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from pygame import Rect

if TYPE_CHECKING:
    from ..core.ui_node import UiNode


class FlexDirection(Enum):
    """Primary axis direction for a :class:`FlexLayout`."""

    ROW = "row"
    COLUMN = "column"


class FlexAlign(Enum):
    """Cross-axis alignment of children within a flex container."""

    START = "start"
    CENTER = "center"
    END = "end"
    STRETCH = "stretch"


class FlexJustify(Enum):
    """Main-axis distribution of children within a flex container."""

    START = "start"
    CENTER = "center"
    END = "end"
    SPACE_BETWEEN = "space_between"
    SPACE_AROUND = "space_around"


@dataclass
class FlexItem:
    """Describes how one child node participates in a flex layout.

    Attributes:
        node: The :class:`~gui_do.UiNode` to position.
        grow: Flex-grow factor — how much surplus space this item absorbs.
            ``0`` means the item does not grow.
        shrink: Flex-shrink factor — how much the item shrinks when space is
            tight.  ``0`` means the item does not shrink below its basis.
        basis: Base size along the main axis in pixels.  ``None`` uses the
            node's current rect dimension.
        min_size: Minimum main-axis size in pixels.  ``None`` = unconstrained.
        max_size: Maximum main-axis size in pixels.  ``None`` = unconstrained.
        align_self: Override the container's *align* for this item only.
            ``None`` inherits the container's *align* setting.
    """

    node: "UiNode"
    grow: float = 0.0
    shrink: float = 1.0
    basis: Optional[int] = None
    min_size: Optional[int] = None
    max_size: Optional[int] = None
    align_self: Optional[FlexAlign] = None


class FlexLayout:
    """Row or column flex layout engine.

    :meth:`apply` computes and mutates child rects in place given a
    *container_rect*.  It does **not** call ``invalidate()`` on children;
    callers should do that after applying layout.

    Usage::

        layout = FlexLayout(
            direction=FlexDirection.ROW,
            gap=8,
            align=FlexAlign.CENTER,
            justify=FlexJustify.START,
        )
        layout.items = [
            FlexItem(label, grow=0, basis=120),
            FlexItem(text_input, grow=1),
            FlexItem(button, grow=0, basis=80),
        ]
        layout.apply(container_rect)
        for item in layout.items:
            item.node.invalidate()

    Re-applying on resize::

        def on_resize(new_rect):
            layout.apply(new_rect)
            for item in layout.items:
                item.node.invalidate()
    """

    def __init__(
        self,
        *,
        direction: FlexDirection = FlexDirection.ROW,
        gap: int = 0,
        align: FlexAlign = FlexAlign.START,
        justify: FlexJustify = FlexJustify.START,
        padding: int = 0,
        items: Optional[List[FlexItem]] = None,
    ) -> None:
        self.direction: FlexDirection = FlexDirection(direction) if isinstance(direction, str) else direction
        self.gap: int = max(0, int(gap))
        self.align: FlexAlign = FlexAlign(align) if isinstance(align, str) else align
        self.justify: FlexJustify = FlexJustify(justify) if isinstance(justify, str) else justify
        self.padding: int = max(0, int(padding))
        self.items: List[FlexItem] = list(items) if items else []

    # ------------------------------------------------------------------
    # Layout computation
    # ------------------------------------------------------------------

    def apply(self, container_rect: Rect) -> None:
        """Compute and mutate child rects so they fill *container_rect*.

        The *container_rect* is treated as the available space.  ``padding``
        is subtracted from each side before distributing space.
        """
        if not self.items:
            return

        pad = self.padding
        cx = container_rect.x + pad
        cy = container_rect.y + pad
        cw = container_rect.width - pad * 2
        ch = container_rect.height - pad * 2

        is_row = self.direction is FlexDirection.ROW
        main_size = cw if is_row else ch
        cross_size = ch if is_row else cw

        # Resolve bases
        bases = []
        for item in self.items:
            if item.basis is not None:
                b = int(item.basis)
            else:
                b = item.node.rect.width if is_row else item.node.rect.height
            if item.min_size is not None:
                b = max(b, int(item.min_size))
            if item.max_size is not None:
                b = min(b, int(item.max_size))
            bases.append(b)

        # Total gap space
        n = len(self.items)
        total_gap = self.gap * (n - 1)
        available = main_size - total_gap

        # Compute initial sizes from bases, then grow/shrink
        sizes = list(bases)
        total_used = sum(sizes)
        surplus = available - total_used

        if surplus > 0:
            total_grow = sum(item.grow for item in self.items)
            if total_grow > 0:
                for i, item in enumerate(self.items):
                    if item.grow > 0:
                        extra = int(surplus * item.grow / total_grow)
                        new_s = sizes[i] + extra
                        if item.max_size is not None:
                            new_s = min(new_s, int(item.max_size))
                        sizes[i] = new_s
        elif surplus < 0:
            deficit = -surplus
            total_shrink = sum(item.shrink * bases[i] for i, item in enumerate(self.items))
            if total_shrink > 0:
                for i, item in enumerate(self.items):
                    if item.shrink > 0:
                        scaled_shrink = item.shrink * bases[i] / total_shrink
                        reduction = int(deficit * scaled_shrink)
                        new_s = max(0, sizes[i] - reduction)
                        if item.min_size is not None:
                            new_s = max(new_s, int(item.min_size))
                        sizes[i] = new_s

        # Distribute justify offsets
        total_actual = sum(sizes) + total_gap
        justify_offset = 0
        between_extra = 0
        around_extra = 0
        if self.justify is FlexJustify.CENTER:
            justify_offset = (available - total_actual + total_gap) // 2
        elif self.justify is FlexJustify.END:
            justify_offset = available - total_actual + total_gap
        elif self.justify is FlexJustify.SPACE_BETWEEN and n > 1:
            between_extra = max(0, (available - sum(sizes))) // (n - 1)
        elif self.justify is FlexJustify.SPACE_AROUND and n > 0:
            around_extra = max(0, (available - sum(sizes))) // n
            justify_offset = around_extra // 2

        # Assign rects
        pos = (cx if is_row else cy) + justify_offset
        for i, (item, main) in enumerate(zip(self.items, sizes)):
            eff_align = item.align_self if item.align_self is not None else self.align
            # Cross dimension
            node_cross = item.node.rect.height if is_row else item.node.rect.width
            if eff_align is FlexAlign.STRETCH:
                cross = cross_size
                cross_pos = cy if is_row else cx
            elif eff_align is FlexAlign.CENTER:
                cross = node_cross
                cross_pos = (cy if is_row else cx) + (cross_size - cross) // 2
            elif eff_align is FlexAlign.END:
                cross = node_cross
                cross_pos = (cy if is_row else cx) + cross_size - cross
            else:  # START
                cross = node_cross
                cross_pos = cy if is_row else cx

            if is_row:
                item.node.rect = Rect(int(pos), int(cross_pos), int(main), int(cross))
            else:
                item.node.rect = Rect(int(cross_pos), int(pos), int(cross), int(main))

            pos += main + self.gap
            if self.justify is FlexJustify.SPACE_BETWEEN and i < n - 1:
                pos += between_extra
            if self.justify is FlexJustify.SPACE_AROUND:
                pos += around_extra

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    def add(self, node: "UiNode", **kwargs) -> "FlexItem":
        """Append a new :class:`FlexItem` for *node* and return it."""
        item = FlexItem(node, **kwargs)
        self.items.append(item)
        return item

    def remove(self, node: "UiNode") -> bool:
        """Remove the :class:`FlexItem` wrapping *node*.  Returns True if found."""
        for i, item in enumerate(self.items):
            if item.node is node:
                self.items.pop(i)
                return True
        return False

    def clear(self) -> None:
        """Remove all items."""
        self.items.clear()
