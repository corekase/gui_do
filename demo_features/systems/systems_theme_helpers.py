"""Theme-tab helpers for the systems demo feature."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pygame import Rect

from gui_do import ButtonControl, DropdownControl, DropdownOption, LabelControl, PanelControl, ScopedThemeManager

if TYPE_CHECKING:
    from .systems_feature import SystemsFeature


def build_theme_panel(feature: SystemsFeature, rect: Rect) -> PanelControl:
    panel = PanelControl("systems_theme_panel", Rect(rect), draw_background=False)
    theme_select_label = LabelControl(
        "systems_theme_select_label",
        Rect(0, 0, 128, 28),
        "Theme",
        align="left",
    )
    feature.theme_dropdown = DropdownControl(
        "systems_theme_picker",
        Rect(0, 0, 180, 32),
        options=[
            DropdownOption("Dark", "dark"),
            DropdownOption("Light", "light"),
            DropdownOption("Sunrise", "sunrise"),
        ],
        selected_index=0,
        on_change=lambda value, _index: feature._on_theme_changed(value),
    )
    toggle_scope = ButtonControl(
        "systems_theme_toggle_scope",
        Rect(0, 0, 164, 32),
        "Toggle Review Scope",
        feature._toggle_review_scope,
        style="round",
    )
    feature._place_vertical_grid_sequence(
        panel,
        Rect(feature.LABEL_INSET_X, 0, max(1, rect.width - feature.LABEL_INSET_X), 28),
        [
            (theme_select_label, 28, 0),
        ],
    )
    feature._place_row_controls(
        panel,
        feature._row_bounds(
            rect,
            30,
            left=feature.PANEL_PADDING_X + feature.LEFT_SIDE_INSET_X,
            width=max(
                1,
                rect.width - (feature.PANEL_PADDING_X * 2) - (feature.LEFT_SIDE_INSET_X * 2),
            ),
        ),
        [feature.theme_dropdown, toggle_scope],
    )

    feature.theme_state_label = LabelControl(
        "systems_theme_state",
        Rect(0, 0, rect.width, 28),
        "",
        align="left",
    )
    feature.theme_scope_label = LabelControl(
        "systems_theme_scope",
        Rect(0, 0, rect.width, 28),
        "",
        align="left",
    )
    feature.theme_resolved_label = LabelControl(
        "systems_theme_resolved",
        Rect(0, 0, rect.width, 28),
        "",
        align="left",
    )
    feature._place_vertical_label_stack(
        panel,
        Rect(feature.LABEL_INSET_X, 92, max(1, rect.width - feature.LABEL_INSET_X), 100),
        [
            feature.theme_state_label,
            feature.theme_scope_label,
            feature.theme_resolved_label,
        ],
        gap=8,
    )
    feature._refresh_theme_labels()
    return panel


def on_theme_changed(feature: SystemsFeature, value: str) -> None:
    feature._theme_manager.switch(str(value))
    feature._refresh_theme_labels()


def toggle_review_scope(feature: SystemsFeature) -> None:
    feature._review_scope_enabled = not feature._review_scope_enabled
    feature._refresh_theme_labels()


def refresh_theme_labels(feature: SystemsFeature) -> None:
    active_name = feature._theme_manager.active_theme.value
    scoped = ScopedThemeManager(feature._theme_manager.active_tokens.value)
    if feature._review_scope_enabled:
        scoped.push(feature._review_scope)
    global_primary = feature._theme_manager.token("primary")
    scoped_primary = scoped.resolve("primary")
    if feature.theme_state_label is not None:
        feature.theme_state_label.text = f"ThemeManager active theme: {active_name}"
    if feature.theme_scope_label is not None:
        scope_state = "enabled" if feature._review_scope_enabled else "disabled"
        feature.theme_scope_label.text = f"ScopedThemeManager review scope: {scope_state}"
    if feature.theme_resolved_label is not None:
        feature.theme_resolved_label.text = (
            f"Resolved primary token global {global_primary} | scoped {scoped_primary}"
        )


__all__ = [
    "build_theme_panel",
    "on_theme_changed",
    "refresh_theme_labels",
    "toggle_review_scope",
]
