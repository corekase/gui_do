"""Helper functions for systems feature layout and placement concerns."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pygame import Rect

from gui_do import CanvasControl, LabelControl, PanelControl
from gui_do.features import panel_layout_helpers as panel_layout
from .systems_specs import (
    SYSTEMS_COMPACT_LABEL_WIDTH,
    SYSTEMS_COMPACT_ROW_GAP,
    SYSTEMS_GRAPHICS_EMITTER_PADDING,
    SYSTEMS_LABEL_STACK_GAP,
    SYSTEMS_TEXT_PREVIEW_MAX_EVENTS,
    SYSTEMS_TEXT_PREVIEW_MIN_WIDTH,
)

if TYPE_CHECKING:
    from .systems_feature import SystemsFeature


def row_bounds(
    feature: SystemsFeature,
    rect: Rect,
    top: int,
    *,
    left: int | None = None,
    width: int | None = None,
    height: int | None = None,
) -> Rect:
    return panel_layout.row_bounds(
        rect,
        top,
        default_left=feature.PANEL_PADDING_X,
        default_height=feature.BUTTON_ROW_HEIGHT,
        edge_padding=feature.PANEL_PADDING_X,
        left=left,
        width=width,
        height=height,
    )


def place_row_controls(
    feature: SystemsFeature,
    panel: PanelControl,
    row_bounds_value: Rect,
    controls: list[object],
) -> None:
    panel_layout.place_row_controls(panel, row_bounds_value, controls, gap=feature.BUTTON_ROW_GAP)


def place_vertical_grid_sequence(
    feature: SystemsFeature,
    panel: PanelControl,
    bounds: Rect,
    items: list[tuple[object, int, int]],
    *,
    stretch_width: bool = True,
) -> None:
    """Place controls in one column with per-item spacer rows."""
    panel_layout.place_vertical_grid_sequence(
        panel,
        bounds,
        items,
        stretch_width=stretch_width,
    )


def place_vertical_label_stack(
    feature: SystemsFeature,
    panel: PanelControl,
    bounds: Rect,
    labels: list[LabelControl],
    *,
    gap: int = SYSTEMS_LABEL_STACK_GAP,
) -> None:
    """Stack status labels vertically with consistent spacing."""
    panel_layout.place_vertical_label_stack(panel, bounds, labels, gap=gap)


def place_compact_labeled_row(
    feature: SystemsFeature,
    panel: PanelControl,
    *,
    left: int = 0,
    top: int,
    label: LabelControl,
    field: object,
    label_width: int = SYSTEMS_COMPACT_LABEL_WIDTH,
    gap: int = SYSTEMS_COMPACT_ROW_GAP,
) -> None:
    """Place a fixed-width label and field in a compact single row."""
    panel_layout.place_compact_labeled_row(
        panel,
        left=int(left),
        top=int(top),
        label=label,
        field=field,
        label_width=int(label_width),
        gap=int(gap),
    )


def place_graphics_particle_layer(
    feature: SystemsFeature,
    panel: PanelControl,
    *,
    left: int,
    top: int,
    width: int,
    height: int,
) -> None:
    feature._particle_layer.rect = Rect(0, 0, int(width), int(height))
    place_vertical_grid_sequence(
        feature,
        panel,
        Rect(int(left), int(top), max(1, int(width)), max(1, int(height))),
        [(feature._particle_layer, int(height), 0)],
    )


def sync_graphics_emitter_offsets(
    feature: SystemsFeature,
    *,
    panel_rect: Rect,
    left_col_x: int,
    left_col_width: int,
    labels_top: int,
) -> None:
    # Emitters align to the horizontal midpoint of the Burst/Reset row and
    # sit just above the stacked status labels.
    burst_dx = left_col_x + left_col_width / 2
    emitter_padding = SYSTEMS_GRAPHICS_EMITTER_PADDING
    burst_dy = labels_top - emitter_padding
    feature._burst_emitter_panel_offset = (burst_dx, burst_dy)
    feature._ambient_emitter_panel_offset = (burst_dx, burst_dy)
    feature._particle_burst_emitter.x = panel_rect.left + burst_dx
    feature._particle_burst_emitter.y = panel_rect.top + burst_dy
    feature._particle_ambient_emitter.x = panel_rect.left + burst_dx
    feature._particle_ambient_emitter.y = panel_rect.top + burst_dy


def place_text_preview_region(
    feature: SystemsFeature,
    panel: PanelControl,
    *,
    top: int,
    width: int,
    height: int,
) -> None:
    feature.text_preview_canvas = CanvasControl(
        "systems_text_preview",
        Rect(0, 0, max(SYSTEMS_TEXT_PREVIEW_MIN_WIDTH, int(width)), max(1, int(height))),
        max_events=SYSTEMS_TEXT_PREVIEW_MAX_EVENTS,
    )
    place_vertical_grid_sequence(
        feature,
        panel,
        Rect(feature.PANEL_PADDING_X, int(top), max(1, int(width)), max(1, int(height))),
        [(feature.text_preview_canvas, int(height), 0)],
    )


__all__ = [
    "place_compact_labeled_row",
    "place_graphics_particle_layer",
    "place_row_controls",
    "place_text_preview_region",
    "place_vertical_grid_sequence",
    "place_vertical_label_stack",
    "row_bounds",
    "sync_graphics_emitter_offsets",
]
