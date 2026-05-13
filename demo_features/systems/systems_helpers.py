"""Helper functions for systems feature layout and placement concerns."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pygame import Rect

from gui_do import CanvasControl, FlexLayout, GridLayout, GridPlacement, LabelControl, PanelControl
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
    row_left = feature.PANEL_PADDING_X if left is None else int(left)
    row_height = feature.BUTTON_ROW_HEIGHT if height is None else max(1, int(height))
    if width is None:
        right_padding = feature.PANEL_PADDING_X if left is None else feature.PANEL_PADDING_X
        row_width = rect.width - row_left - right_padding
    else:
        row_width = int(width)
    return Rect(row_left, int(top), max(1, row_width), row_height)


def place_row_controls(
    feature: SystemsFeature,
    panel: PanelControl,
    row_bounds_value: Rect,
    controls: list[object],
) -> None:
    if not controls:
        return
    layout = FlexLayout(direction="row", gap=feature.BUTTON_ROW_GAP, padding=0)
    for control in controls:
        control.rect = Rect(0, 0, max(1, row_bounds_value.width), row_bounds_value.height)
        layout.add(control, grow=1)
    layout.apply(row_bounds_value)
    for control in controls:
        panel.add_at(control, control.rect.left, control.rect.top)


def place_vertical_grid_sequence(
    feature: SystemsFeature,
    panel: PanelControl,
    bounds: Rect,
    items: list[tuple[object, int, int]],
    *,
    stretch_width: bool = True,
) -> None:
    """Place controls in one column with per-item spacer rows using GridLayout."""
    if not items:
        return
    row_tracks: list[int] = []
    placements: list[tuple[int, object, int]] = []
    for control, row_height, after_gap in items:
        target_height = max(1, int(row_height))
        row_index = len(row_tracks)
        row_tracks.append(target_height)
        placements.append((row_index, control, target_height))
        gap_height = max(0, int(after_gap))
        if gap_height > 0:
            row_tracks.append(gap_height)

    layout = GridLayout(row_tracks=row_tracks, col_tracks=["1fr"], gap=0, padding=0)
    for row_index, control, target_height in placements:
        target_width = max(1, bounds.width) if stretch_width else max(1, int(control.rect.width))
        control.rect = Rect(0, 0, target_width, target_height)
        layout.place(control, GridPlacement(row=row_index, col=0))
    layout.apply(bounds)
    for _row_index, control, _target_height in placements:
        panel.add_at(control, control.rect.left, control.rect.top)


def place_vertical_label_stack(
    feature: SystemsFeature,
    panel: PanelControl,
    bounds: Rect,
    labels: list[LabelControl],
    *,
    gap: int = SYSTEMS_LABEL_STACK_GAP,
) -> None:
    """Stack status labels vertically with FlexLayout for consistent spacing."""
    if not labels:
        return
    layout = FlexLayout(direction="column", gap=max(0, int(gap)), padding=0)
    for label in labels:
        target_height = max(1, int(label.rect.height))
        label.rect = Rect(0, 0, max(1, bounds.width), target_height)
        layout.add(label, grow=0, basis=target_height)
    layout.apply(bounds)
    for label in labels:
        panel.add_at(label, label.rect.left, label.rect.top)


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
    row_height = max(1, max(int(label.rect.height), int(field.rect.height)))
    left_width = max(1, int(label_width))
    col_gap = max(0, int(gap))
    field_width = max(1, int(field.rect.width))
    row_bounds_value = Rect(int(left), int(top), left_width + col_gap + field_width, row_height)
    layout = GridLayout(
        row_tracks=[row_height],
        col_tracks=[left_width, field_width],
        gap=col_gap,
        padding=0,
    )
    label.rect = Rect(0, 0, left_width, row_height)
    field.rect = Rect(0, 0, field_width, row_height)
    layout.place(label, GridPlacement(row=0, col=0))
    layout.place(field, GridPlacement(row=0, col=1))
    layout.apply(row_bounds_value)
    panel.add_at(label, label.rect.left, label.rect.top)
    panel.add_at(field, field.rect.left, field.rect.top)


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
