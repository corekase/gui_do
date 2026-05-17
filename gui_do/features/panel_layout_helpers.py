"""General panel layout helper primitives for feature UIs.

This module centralizes common placement patterns so feature packages only pass
feature-specific sizing values and controls.
"""

from __future__ import annotations

from pygame import Rect

from gui_do import FlexLayout, GridLayout, GridPlacement


def row_bounds(
    rect: Rect,
    top: int,
    *,
    default_left: int,
    default_height: int,
    edge_padding: int,
    left: int | None = None,
    width: int | None = None,
    height: int | None = None,
) -> Rect:
    row_left = int(default_left) if left is None else int(left)
    row_height = max(1, int(default_height)) if height is None else max(1, int(height))
    if width is None:
        row_width = int(rect.width) - row_left - int(edge_padding)
    else:
        row_width = int(width)
    return Rect(row_left, int(top), max(1, row_width), row_height)


def place_row_controls(panel, row_bounds_value: Rect, controls: list[object], *, gap: int) -> None:
    if not controls:
        return
    layout = FlexLayout(direction="row", gap=max(0, int(gap)), padding=0)
    for control in controls:
        control.rect = Rect(0, 0, max(1, row_bounds_value.width), row_bounds_value.height)
        layout.add(control, grow=1)
    layout.apply(row_bounds_value)
    for control in controls:
        panel.add_at(control, control.rect.left, control.rect.top)


def place_vertical_grid_sequence(
    panel,
    bounds: Rect,
    items: list[tuple[object, int, int]],
    *,
    stretch_width: bool = True,
) -> None:
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


def place_vertical_label_stack(panel, bounds: Rect, labels: list[object], *, gap: int) -> None:
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
    panel,
    *,
    left: int,
    top: int,
    label,
    field,
    label_width: int,
    gap: int,
) -> None:
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


__all__ = [
    "place_compact_labeled_row",
    "place_row_controls",
    "place_vertical_grid_sequence",
    "place_vertical_label_stack",
    "row_bounds",
]
