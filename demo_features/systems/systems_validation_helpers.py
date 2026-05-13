"""Validation-tab helpers for the systems demo feature."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pygame import Rect

from gui_do import (
    ButtonControl,
    DropdownControl,
    DropdownOption,
    GridLayout,
    GridPlacement,
    LabelControl,
    PanelControl,
    TextInputControl,
)

if TYPE_CHECKING:
    from .systems_feature import SystemsFeature


def build_validation_panel(feature: SystemsFeature, rect: Rect) -> PanelControl:
    panel = PanelControl("systems_validation_panel", Rect(rect), draw_background=False)
    name_label = LabelControl("systems_validation_name_label", Rect(0, 0, 180, 28), "Pipeline Name", align="left")
    feature.validation_name_input = TextInputControl(
        "systems_validation_name",
        Rect(0, 0, min(320, rect.width - 16), 32),
        value=feature._deployment_name_field.value.value,
        placeholder="nightly-gui",
        on_change=feature._on_deployment_name_changed,
    )
    env_label = LabelControl("systems_validation_env_label", Rect(0, 0, 180, 28), "Target Environment", align="left")
    feature.validation_environment_dropdown = DropdownControl(
        "systems_validation_environment",
        Rect(0, 0, 220, 32),
        options=[
            DropdownOption("Staging", "Staging"),
            DropdownOption("QA", "QA"),
            DropdownOption("Production", "Production"),
        ],
        selected_index=0,
        on_change=lambda value, _index: feature._on_environment_changed(value),
    )
    run_checks = ButtonControl(
        "systems_validation_run_checks",
        Rect(0, 0, 148, 32),
        "Run Local Checks",
        feature._run_local_validation_checks,
        style="round",
    )
    suggested = ButtonControl(
        "systems_validation_use_suggested",
        Rect(0, 0, 160, 32),
        "Use Suggested Names",
        feature._apply_suggested_name,
        style="round",
    )

    grid_inset_x = feature.PANEL_PADDING_X
    grid_gap = 10
    grid_width = max(1, int(rect.width) - (grid_inset_x * 2))
    col_width = max(1, (grid_width - grid_gap) // 2)
    row_tracks = [28, 32, 32]
    grid_height = sum(row_tracks) + (grid_gap * (len(row_tracks) - 1))
    grid_bounds = Rect(grid_inset_x, 0, grid_width, grid_height)

    name_label.rect = Rect(0, 0, col_width, 28)
    env_label.rect = Rect(0, 0, col_width, 28)
    feature.validation_name_input.rect = Rect(0, 0, max(180, min(320, col_width)), 32)
    feature.validation_environment_dropdown.rect = Rect(0, 0, max(160, min(220, col_width)), 32)
    run_checks.rect = Rect(0, 0, min(148, col_width), 32)
    suggested.rect = Rect(0, 0, min(160, col_width), 32)

    layout = GridLayout(
        row_tracks=row_tracks,
        col_tracks=[col_width, col_width],
        gap=grid_gap,
        padding=0,
    )
    layout.place(name_label, GridPlacement(row=0, col=0))
    layout.place(env_label, GridPlacement(row=0, col=1))
    layout.place(feature.validation_name_input, GridPlacement(row=1, col=0))
    layout.place(feature.validation_environment_dropdown, GridPlacement(row=1, col=1))
    layout.place(run_checks, GridPlacement(row=2, col=0))
    layout.place(suggested, GridPlacement(row=2, col=1))
    layout.apply(grid_bounds)
    for control in (
        name_label,
        env_label,
        feature.validation_name_input,
        feature.validation_environment_dropdown,
        run_checks,
        suggested,
    ):
        panel.add_at(control, control.rect.left, control.rect.top)

    feature.validation_state_label = LabelControl(
        "systems_validation_state",
        Rect(0, 0, grid_width, 28),
        "Form state pending.",
        align="left",
    )
    feature.validation_local_label = LabelControl(
        "systems_validation_local",
        Rect(0, 0, grid_width, 28),
        "Local checks pending.",
        align="left",
    )
    feature.validation_async_label = LabelControl(
        "systems_validation_async",
        Rect(0, 0, grid_width, 28),
        "Async availability check pending.",
        align="left",
    )
    status_top = grid_bounds.bottom + 8
    status_bounds = Rect(
        grid_inset_x,
        status_top,
        grid_width,
        max(1, int(rect.height) - status_top),
    )
    feature._place_vertical_label_stack(
        panel,
        status_bounds,
        [
            feature.validation_state_label,
            feature.validation_local_label,
            feature.validation_async_label,
        ],
        gap=8,
    )
    feature._refresh_validation_labels()
    return panel


def check_pipeline_name(_feature: SystemsFeature, value: object) -> str | None:
    reserved = {"admin", "root", "prod"}
    normalized = str(value).strip().lower()
    if normalized in reserved:
        return "Reserved pipeline name"
    return None


def on_deployment_name_changed(feature: SystemsFeature, value: str) -> None:
    feature._deployment_name_field.value.value = str(value)
    feature._refresh_validation_labels()


def on_environment_changed(feature: SystemsFeature, value: str) -> None:
    feature._environment_field.value.value = str(value)
    feature._refresh_validation_labels()


def run_local_validation_checks(feature: SystemsFeature) -> None:
    feature._form_validator.validate_all_local()
    feature._refresh_validation_labels()


def apply_suggested_name(feature: SystemsFeature) -> None:
    suggested = "staging-gui-release"
    if feature.validation_name_input is not None:
        feature.validation_name_input.set_value(suggested)
    feature._deployment_name_field.value.value = suggested
    feature._refresh_validation_labels()


def refresh_validation_labels(feature: SystemsFeature) -> None:
    if feature.validation_state_label is not None:
        environment = feature._environment_field.value.value
        if feature._form_validator.is_valid:
            feature.validation_state_label.text = f"AsyncFormValidator: ready to route build to {environment}."
        else:
            feature.validation_state_label.text = "AsyncFormValidator: deployment form still needs attention."
    if feature.validation_local_label is not None:
        local_error = feature._name_validator.local_error.value or feature._environment_validator.local_error.value
        feature.validation_local_label.text = (
            f"Local validation: {local_error}" if local_error is not None else "Local validation: passed"
        )
    if feature.validation_async_label is not None:
        if feature._name_validator.is_validating.value:
            feature.validation_async_label.text = "Async validation: checking pipeline name availability..."
        else:
            async_error = feature._name_validator.async_error.value
            feature.validation_async_label.text = (
                f"Async validation: {async_error}" if async_error is not None else "Async validation: pipeline name available"
            )


__all__ = [
    "apply_suggested_name",
    "build_validation_panel",
    "check_pipeline_name",
    "on_deployment_name_changed",
    "on_environment_changed",
    "refresh_validation_labels",
    "run_local_validation_checks",
]
