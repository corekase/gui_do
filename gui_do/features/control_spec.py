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
            Defaults to ``True``.
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
    focusable: bool = True
    accessibility_role: str | None = None
    accessibility_label: str | None = None


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
        desired_h = max(1, int(slot_height_for(defn.control_height)))
        slot_rect = Rect(stack.add_slot_or_overflow(desired_h, overflow_gap=max(0, int(overflow_gap))))
        bottom_y = int(slot_rect.bottom)
        specs.append(
            ControlPlacementSpec(
                name=defn.name,
                label_text=defn.label_text,
                control=defn.control_factory(),
                control_rect=slot_rect,
                focusable=bool(defn.focusable),
                accessibility_role=defn.accessibility_role,
                accessibility_label=defn.accessibility_label,
                column_index=int(defn.column_index),
                row_index=int(defn.row_index),
            )
        )
    return tuple(specs), bottom_y
