"""History-tab helpers for the systems demo feature."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pygame import Rect

from gui_do import ButtonControl, LabelControl, PanelControl

from .systems_commands import _StatusChangeCommand

if TYPE_CHECKING:
    from .systems_feature import SystemsFeature


def build_history_panel(feature: SystemsFeature, rect: Rect) -> PanelControl:
    panel = PanelControl("systems_history_panel", Rect(rect), draw_background=False)
    advance_button = ButtonControl(
        "systems_history_advance",
        Rect(0, 0, 140, 32),
        "Advance Stage",
        feature._advance_history_stage,
        style="round",
    )
    batch_button = ButtonControl(
        "systems_history_batch",
        Rect(0, 0, 160, 32),
        "Batch Promote",
        feature._batch_promote_history_stage,
        style="round",
    )
    undo_button = ButtonControl(
        "systems_history_undo",
        Rect(0, 0, 96, 32),
        "Undo",
        feature._undo_history_stage,
        style="round",
    )
    redo_button = ButtonControl(
        "systems_history_redo",
        Rect(0, 0, 96, 32),
        "Redo",
        feature._redo_history_stage,
        style="round",
    )
    label_top = feature._add_button_rows(
        panel,
        rect,
        0,
        [advance_button, batch_button, undo_button, redo_button],
        left=feature.PANEL_PADDING_X + feature.LEFT_SIDE_INSET_X,
        width=max(
            1,
            rect.width - (feature.PANEL_PADDING_X * 2) - (feature.LEFT_SIDE_INSET_X * 2),
        ),
    )

    feature.history_current_label = LabelControl(
        "systems_history_current",
        Rect(0, 0, rect.width, 28),
        "",
        align="left",
    )
    feature.history_undo_label = LabelControl(
        "systems_history_undo_label",
        Rect(0, 0, rect.width, 28),
        "",
        align="left",
    )
    feature.history_redo_label = LabelControl(
        "systems_history_redo_label",
        Rect(0, 0, rect.width, 28),
        "",
        align="left",
    )
    feature._place_vertical_label_stack(
        panel,
        Rect(feature.LABEL_INSET_X, label_top + 8, max(1, rect.width - feature.LABEL_INSET_X), 100),
        [
            feature.history_current_label,
            feature.history_undo_label,
            feature.history_redo_label,
        ],
        gap=8,
    )
    feature._refresh_history_labels()
    return panel


def advance_history_stage(feature: SystemsFeature) -> None:
    current = feature._history_stage_index
    if current >= len(feature._history_stages) - 1:
        return
    next_index = current + 1
    description = f"Promote to {feature._history_stages[next_index]}"
    feature._history.push(_StatusChangeCommand(feature, next_index, description))
    feature._refresh_history_labels()


def batch_promote_history_stage(feature: SystemsFeature) -> None:
    current = feature._history_stage_index
    if current >= len(feature._history_stages) - 1:
        return
    with feature._history.transaction("Prepare release bundle"):
        mid_index = min(current + 1, len(feature._history_stages) - 1)
        feature._history.push(
            _StatusChangeCommand(feature, mid_index, f"Promote to {feature._history_stages[mid_index]}")
        )
        final_index = min(mid_index + 1, len(feature._history_stages) - 1)
        if final_index != mid_index:
            feature._history.push(
                _StatusChangeCommand(feature, final_index, f"Promote to {feature._history_stages[final_index]}")
            )
    feature._refresh_history_labels()


def undo_history_stage(feature: SystemsFeature) -> None:
    feature._history.undo()
    feature._refresh_history_labels()


def redo_history_stage(feature: SystemsFeature) -> None:
    feature._history.redo()
    feature._refresh_history_labels()


def refresh_history_labels(feature: SystemsFeature) -> None:
    if feature.history_current_label is not None:
        feature.history_current_label.text = (
            f"CommandHistory current milestone: {feature._history_stages[feature._history_stage_index]}"
        )
    if feature.history_undo_label is not None:
        undo_desc = feature._history.undo_description or "Nothing to undo"
        feature.history_undo_label.text = f"Undo: {undo_desc}"
    if feature.history_redo_label is not None:
        redo_desc = feature._history.redo_description or "Nothing to redo"
        feature.history_redo_label.text = f"Redo: {redo_desc}"


__all__ = [
    "advance_history_stage",
    "batch_promote_history_stage",
    "build_history_panel",
    "redo_history_stage",
    "refresh_history_labels",
    "undo_history_stage",
]
