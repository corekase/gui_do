"""Generic data-driven control placement spec building utilities.

:class:`ControlDefinition` is the canonical declarative descriptor for one
control in a column section.  Pass a sequence of them together with an active
:class:`~gui_do.CellCaretLayout` stack to :func:`build_specs_from_column_section`
and receive back a tuple of :class:`~gui_do.ControlPlacementSpec` objects ready
for :func:`~gui_do.features.feature_lifecycle.place_control_specs`.

Typical usage::

    from gui_do import ControlDefinition, build_specs_from_column_section

    defs = (
        ControlDefinition(
            name="spinner",
            label_text="Spinner",
            control_height=30,
            row_index=100,
            control_factory=lambda: SpinnerControl("ctrl_spinner", Rect(0, 0, col_w, 30), ...),
            column_index=5,
        ),
        ControlDefinition(
            name="range_slider",
            label_text="Range Slider",
            control_height=24,
            row_index=101,
            control_factory=lambda: RangeSliderControl(...),
            column_index=5,
        ),
    )

    specs, bottom_y = build_specs_from_column_section(
        defs,
        stack=stack,
        slot_height_for=slot_h,
        overflow_gap=row_gap,
    )

See also :mod:`gui_do.features.data_driven_runtime` for :class:`NotificationSpec`
and :func:`build_notification_center`.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

from pygame import Rect

from .feature_lifecycle import ControlPlacementSpec
from ..layout.cell_caret_layout import CellCaretLayout


@dataclass(frozen=True)
class ControlDefinition:
    """Declarative descriptor for a single control in a stacked column section.

    All sizing and identity fields are encoded here; the actual control object
    is produced lazily by :attr:`control_factory` so that construction only
    happens once placement geometry is known.

    Attributes:
        name: Unique placement name (used as key in ``placed_controls``).
        label_text: Human-readable label drawn above the control.
        control_height: Preferred intrinsic height of the control in pixels
            (before label overhead is added by the layout).
        row_index: Sort key used by category-visibility logic and relayout
            routines.  Controls within a column should have unique, ordered
            row indices.
        control_factory: Zero-argument callable that returns the live control
            instance.  Called exactly once per :func:`build_specs_from_column_section`
            invocation—never cached.
        column_index: Column bucket used by category-visibility logic.
            Defaults to ``0``.
        focusable: Whether the control participates in keyboard focus traversal.
            ``None`` (default) defers to automatic inference from the control's
            own focus capability.
        accessibility_role: ARIA-style role string passed to
            ``control.set_accessibility``.  ``None`` skips the call.
        accessibility_label: Accessible name passed alongside
            :attr:`accessibility_role`.  ``None`` skips the call.
    """

    name: str
    label_text: str
    control_height: int
    row_index: int
    control_factory: Callable[[], Any]
    column_index: int = 0
    focusable: bool | None = None
    accessibility_role: str | None = None
    accessibility_label: str | None = None
    labeled: bool = True


def build_specs_from_column_section(
    definitions: Sequence[ControlDefinition],
    *,
    stack: CellCaretLayout,
    slot_height_for: Callable[[int], int],
    overflow_gap: int = 0,
) -> tuple[tuple[ControlPlacementSpec, ...], int]:
    """Build placement specs for a sequence of :class:`ControlDefinition` objects.

    Each definition drives one slot in *stack* via
    :meth:`~gui_do.CellCaretLayout.add_slot_or_overflow`.  The resulting
    :class:`~gui_do.ControlPlacementSpec` carries the final rect, accessibility
    metadata, and column/row indices ready for
    :func:`~gui_do.features.feature_lifecycle.place_control_specs`.

    Args:
        definitions: Ordered sequence of :class:`ControlDefinition` objects.
        stack: Active :class:`~gui_do.CellCaretLayout` that owns the column's
            vertical caret.  The stack is mutated in-place as slots are claimed.
        slot_height_for: Callable mapping a raw control height to the full
            labeled-slot height (typically
            :meth:`~gui_do.CellCaretLayout.labeled_slot_height` wrapped in a
            local closure).
        overflow_gap: Vertical gap in pixels to insert before an overflow slot
            (forwarded directly to :meth:`~gui_do.CellCaretLayout.add_slot_or_overflow`).

    Returns:
        A ``(specs, bottom_y)`` pair where *specs* is an immutable tuple of
        :class:`~gui_do.ControlPlacementSpec` objects and *bottom_y* is the
        pixel coordinate of the bottom edge of the last placed slot (or the
        stack's top if *definitions* is empty).
    """
    specs: list[ControlPlacementSpec] = []
    bottom_y: int = int(stack.bounds.top)
    for defn in definitions:
        if getattr(defn, "labeled", True):
            desired_h = max(1, int(slot_height_for(defn.control_height)))
        else:
            desired_h = max(1, int(defn.control_height))
        slot_rect = Rect(stack.add_slot_or_overflow(desired_h, overflow_gap=max(0, int(overflow_gap))))
        bottom_y = int(slot_rect.bottom)
        specs.append(
            ControlPlacementSpec(
                name=defn.name,
                label_text=defn.label_text,
                control=defn.control_factory(),
                control_rect=slot_rect,
                focusable=defn.focusable,
                labeled=getattr(defn, "labeled", True),
                accessibility_role=defn.accessibility_role,
                accessibility_label=defn.accessibility_label,
                column_index=int(defn.column_index),
                row_index=int(defn.row_index),
            )
        )
    return tuple(specs), bottom_y


# ---------------------------------------------------------------------------
# RowCellSpec + build_horizontal_row_specs
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RowCellSpec:
    """Declarative descriptor for a single cell within a multi-cell horizontal row.

    Passed to :func:`build_horizontal_row_specs` as part of a sequence
    describing all cells in one layout row.

    Attributes:
        name: Unique placement name.
        label_text: Human-readable label drawn above the cell.
        control_height: Preferred intrinsic height of the control (before label
            overhead is added by the slot-height calculation).
        row_index: Category/visibility sort key for
            :func:`~gui_do.features.feature_lifecycle.apply_category_visibility`.
        cell_factory: Callable ``(width: int, height: int) -> control`` that
            builds the live control for this cell.  Height is the intrinsic
            control height *after* label overhead has been subtracted.
        focusable: Whether the cell participates in keyboard focus traversal.
            ``None`` (default) defers to automatic inference from the control's
            own focus capability.
        natural_width: If set, the cell occupies exactly this many pixels wide
            and ignores any automatic column split.  All cells in a row must
            have ``natural_width`` set for natural-width mode to activate.
        target_width: If set and smaller than the column width, the slot is
            narrowed to this width.  Use ``target_align`` to control placement.
        target_align: One of ``"left"``, ``"center"`` (default), or ``"right"``.
            Applies only when ``target_width`` is set.
        accessibility_role: ARIA-style role string.  ``None`` skips the call.
        accessibility_label: Accessible name.  ``None`` skips the call.
    """

    name: str
    label_text: str
    control_height: int
    row_index: int
    cell_factory: Callable[[int, int], Any]
    focusable: bool | None = None
    natural_width: int | None = None
    target_width: int | None = None
    target_align: str = "center"
    accessibility_role: str | None = None
    accessibility_label: str | None = None


def build_horizontal_row_specs(
    cells: Sequence[RowCellSpec],
    *,
    stack: CellCaretLayout,
    label_height: int,
    label_gap: int,
    col_gap: int = 8,
    overflow_gap: int = 8,
    min_col_width: int = 60,
) -> tuple[ControlPlacementSpec, ...]:
    """Build :class:`ControlPlacementSpec` objects for all cells in one horizontal row.

    Computes a single row slot in *stack* whose height fits the tallest cell,
    then distributes the cells horizontally within that slot.  Each cell gets
    its own :class:`ControlPlacementSpec` with the cell's ``row_index`` so
    per-row category visibility works correctly.

    Args:
        cells: Ordered sequence of :class:`RowCellSpec` objects.
        stack: Active :class:`~gui_do.CellCaretLayout` that owns the vertical
            caret.  The stack is mutated in-place as the row slot is claimed.
        label_height: Height in pixels reserved above the control for a label.
        label_gap: Gap in pixels between the label bottom and the control top.
        col_gap: Horizontal gap between columns.
        overflow_gap: Gap before the slot when *stack* overflows.
        min_col_width: Minimum column width passed to
            :meth:`~gui_do.CellCaretLayout.split_columns`.

    Returns:
        An immutable tuple of :class:`ControlPlacementSpec` objects, one per cell.
    """
    if not cells:
        return ()

    label_h = int(label_height)
    label_g = int(label_gap)
    gap_x = int(col_gap)

    def _slot_h(control_h: int) -> int:
        return CellCaretLayout.labeled_slot_height(
            max(1, int(control_h)), label_height=label_h, label_gap=label_g
        )

    row_control_h = max(int(c.control_height) for c in cells)
    row_slot_rect = Rect(
        stack.add_slot_or_overflow(
            _slot_h(row_control_h), overflow_gap=max(0, int(overflow_gap))
        )
    )

    # Determine column rects — natural-width mode or equal-split mode
    natural_widths = [c.natural_width for c in cells]
    if all(w is not None for w in natural_widths):
        x = row_slot_rect.left
        col_rects: list[Rect] = []
        for w in natural_widths:
            col_rects.append(Rect(x, row_slot_rect.top, int(w), row_slot_rect.height))
            x += int(w) + gap_x
    else:
        col_rects = CellCaretLayout.split_columns(
            row_slot_rect,
            count=len(cells),
            gap=gap_x,
            min_width=max(1, int(min_col_width)),
        )

    specs: list[ControlPlacementSpec] = []
    for col_i, cell in enumerate(cells):
        col_rect = Rect(col_rects[col_i])
        desired_slot_h = _slot_h(int(cell.control_height))
        slot_rect = Rect(
            col_rect.left,
            col_rect.top,
            col_rect.width,
            min(col_rect.height, desired_slot_h),
        )

        target_w = cell.target_width
        if isinstance(target_w, int) and 1 <= target_w < slot_rect.width:
            align = str(cell.target_align).lower()
            if align == "right":
                slot_rect = Rect(
                    slot_rect.left + slot_rect.width - target_w,
                    slot_rect.top, target_w, slot_rect.height,
                )
            elif align == "left":
                slot_rect = Rect(slot_rect.left, slot_rect.top, target_w, slot_rect.height)
            else:
                slot_rect = Rect(
                    slot_rect.left + (slot_rect.width - target_w) // 2,
                    slot_rect.top, target_w, slot_rect.height,
                )

        control_h = max(1, slot_rect.height - label_h - label_g)
        control = cell.cell_factory(slot_rect.width, control_h)
        specs.append(
            ControlPlacementSpec(
                name=cell.name,
                control=control,
                control_rect=slot_rect,
                focusable=cell.focusable,
                labeled=True,
                label_text=cell.label_text,
                accessibility_role=cell.accessibility_role,
                accessibility_label=cell.accessibility_label,
                column_index=col_i,
                row_index=int(cell.row_index),
            )
        )

    return tuple(specs)


# ---------------------------------------------------------------------------
# build_multi_column_grid_specs
# ---------------------------------------------------------------------------


def build_multi_column_grid_specs(
    definitions: Sequence[ControlDefinition],
    *,
    bounds: Rect,
    num_cols: int,
    content_bottom: int,
    row_gap: int,
    slot_height_for: Callable[[int], int],
    min_col_width: int = 100,
) -> tuple[tuple[ControlPlacementSpec, ...], int]:
    """Place *definitions* in reading order across *num_cols* columns.

    Distributes definitions round-robin (left-to-right, top-to-bottom) across
    *num_cols* independent columns built on :class:`~gui_do.CellCaretLayout`
    stacks.  Returns specs interleaved in row-major order so keyboard focus
    traversal goes left-to-right across the page.

    Args:
        definitions: Ordered sequence of :class:`ControlDefinition` objects.
        bounds: Bounding rect for the entire multi-column area.
        num_cols: Number of columns to distribute definitions across.
        content_bottom: Pixel coordinate of the maximum content bottom edge.
        row_gap: Vertical gap between slots.
        slot_height_for: Callable mapping intrinsic control height to labeled
            slot height (see :func:`~gui_do.make_labeled_slot_height_fn`).
        min_col_width: Minimum column width passed to
            :meth:`~gui_do.CellCaretLayout.split_columns`.

    Returns:
        A ``(specs, max_bottom_y)`` pair where *specs* is an immutable tuple of
        :class:`ControlPlacementSpec` objects and *max_bottom_y* is the pixel
        coordinate of the bottom edge of the tallest column.
    """
    if not definitions or num_cols < 1:
        return (), int(bounds.top)

    col_rects = CellCaretLayout.split_columns(
        bounds, count=num_cols, gap=row_gap, min_width=max(1, int(min_col_width))
    )
    n = min(num_cols, len(col_rects))

    col_defs: list[list[ControlDefinition]] = [[] for _ in range(n)]
    for i, defn in enumerate(definitions):
        col_defs[i % n].append(defn)

    col_specs: list[tuple] = []
    max_bottom = int(bounds.top)
    for idx, col_rect in enumerate(col_rects[:n]):
        stack, _, _, _ = CellCaretLayout.column_stack_from_anchor(
            anchor=col_rect,
            content_bottom=content_bottom,
            preferred_width=col_rect.width,
            item_gap_y=row_gap,
        )
        specs, bottom = build_specs_from_column_section(
            col_defs[idx],
            stack=stack,
            slot_height_for=slot_height_for,
            overflow_gap=row_gap,
        )
        col_specs.append(specs)
        max_bottom = max(max_bottom, bottom)

    # Interleave in row-major order for left-to-right focus traversal
    all_specs: list[ControlPlacementSpec] = []
    max_len = max((len(s) for s in col_specs), default=0)
    for row_i in range(max_len):
        for col_i in range(n):
            if row_i < len(col_specs[col_i]):
                all_specs.append(col_specs[col_i][row_i])

    return tuple(all_specs), max_bottom
