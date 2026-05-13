"""Persistence-tab helpers for the systems demo feature."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pygame import Rect

from gui_do import ButtonControl, LabelControl, PanelControl, WorkspacePersistenceManager, WorkspaceState

if TYPE_CHECKING:
    from .systems_feature import SystemsFeature


def build_persistence_panel(feature: SystemsFeature, rect: Rect) -> PanelControl:
    panel = PanelControl("systems_persistence_panel", Rect(rect), draw_background=False)
    persistence_label_top = feature._add_button_rows(
        panel,
        rect,
        0,
        [
            ButtonControl(
                "systems_persistence_review_profile",
                Rect(0, 0, 150, 32),
                "Apply Review Profile",
                feature._apply_review_profile,
                style="round",
            ),
            ButtonControl(
                "systems_persistence_prod_profile",
                Rect(0, 0, 184, 32),
                "Apply Production Profile",
                feature._apply_production_profile,
                style="round",
            ),
            ButtonControl(
                "systems_persistence_save",
                Rect(0, 0, 148, 32),
                "Save Workspace",
                feature._save_workspace_state,
                style="round",
            ),
            ButtonControl(
                "systems_persistence_restore",
                Rect(0, 0, 164, 32),
                "Restore Workspace",
                feature._restore_workspace_state,
                style="round",
            ),
        ],
        left=feature.PANEL_PADDING_X + feature.LEFT_SIDE_INSET_X,
        width=max(
            1,
            rect.width - (feature.PANEL_PADDING_X * 2) - (feature.LEFT_SIDE_INSET_X * 2),
        ),
    )
    feature.persistence_overview_label = LabelControl(
        "systems_persistence_overview",
        Rect(0, 0, rect.width, 28),
        "",
        align="left",
    )
    feature.persistence_settings_label = LabelControl(
        "systems_persistence_settings",
        Rect(0, 0, rect.width, 28),
        "",
        align="left",
    )
    feature.persistence_status_label = LabelControl(
        "systems_persistence_status",
        Rect(0, 0, rect.width, 56),
        "",
        align="left",
    )
    feature._place_vertical_label_stack(
        panel,
        Rect(
            feature.LABEL_INSET_X,
            persistence_label_top + 8,
            max(1, rect.width - feature.LABEL_INSET_X),
            128,
        ),
        [
            feature.persistence_overview_label,
            feature.persistence_settings_label,
            feature.persistence_status_label,
        ],
        gap=8,
    )
    feature._refresh_persistence_labels()
    return panel


def apply_review_profile(feature: SystemsFeature) -> None:
    feature._settings_registry.set_value("systems", "profile", "review")
    feature._settings_registry.set_value("systems", "autosave", True)
    feature._settings_registry.set_value("systems", "parallel_checks", 2)
    feature._persistence_last_status = "SettingsRegistry switched to the review workspace profile."
    feature._refresh_persistence_labels()


def apply_production_profile(feature: SystemsFeature) -> None:
    feature._settings_registry.set_value("systems", "profile", "production")
    feature._settings_registry.set_value("systems", "autosave", False)
    feature._settings_registry.set_value("systems", "parallel_checks", 4)
    feature._persistence_last_status = "SettingsRegistry switched to the production workspace profile."
    feature._refresh_persistence_labels()


def build_workspace_state(feature: SystemsFeature) -> WorkspaceState:
    return WorkspaceState(
        active_scene_name=feature.scene_name,
        scene_snapshot={},
        settings_blocks={
            block_name: WorkspacePersistenceManager._registry_values(feature._settings_registry)
            for block_name in feature._workspace_persistence.registered_blocks()
        },
        metadata={
            "profile": feature._settings_registry.get_value("systems", "profile"),
            "autosave": feature._settings_registry.get_value("systems", "autosave"),
        },
    )


def save_workspace_state(feature: SystemsFeature) -> None:
    state = feature._build_workspace_state()
    state.save(feature._workspace_state_path)
    feature._saved_workspace_state = state
    feature._persistence_last_report = None
    feature._persistence_last_status = f"WorkspaceState saved to {feature._workspace_state_path}"
    feature._refresh_persistence_labels()


def restore_workspace_state(feature: SystemsFeature) -> None:
    state = feature._saved_workspace_state
    if state is None and feature._workspace_state_path.exists():
        state = WorkspaceState.load(feature._workspace_state_path)
    if state is None:
        feature._persistence_last_status = "No workspace snapshot saved yet."
        feature._refresh_persistence_labels()
        return
    feature._saved_workspace_state = state
    if feature.demo is None:
        feature._persistence_last_status = "Systems demo host is not available for restore."
        feature._refresh_persistence_labels()
        return
    feature._persistence_last_report = feature._workspace_persistence.restore(state, feature.demo.app)
    feature._persistence_last_status = "WorkspacePersistenceManager restored the saved settings block into the live demo."
    feature._refresh_persistence_labels()


def refresh_persistence_labels(feature: SystemsFeature) -> None:
    profile = feature._settings_registry.get_value("systems", "profile")
    autosave = feature._settings_registry.get_value("systems", "autosave")
    checks = feature._settings_registry.get_value("systems", "parallel_checks")
    if feature.persistence_overview_label is not None:
        feature.persistence_overview_label.text = (
            f"WorkspacePersistenceManager blocks={feature._workspace_persistence.registered_blocks()} file={feature._workspace_state_path.name}"
        )
    if feature.persistence_settings_label is not None:
        feature.persistence_settings_label.text = (
            f"SettingsRegistry systems/profile={profile} autosave={autosave} parallel_checks={checks}"
        )
    if feature.persistence_status_label is not None:
        if feature._persistence_last_report is None:
            feature.persistence_status_label.text = feature._persistence_last_status
        else:
            applied = feature._persistence_last_report.get("applied_settings", 0)
            skipped = feature._persistence_last_report.get("skipped_settings", 0)
            feature.persistence_status_label.text = (
                f"{feature._persistence_last_status} applied={applied} skipped={skipped}"
            )


__all__ = [
    "apply_production_profile",
    "apply_review_profile",
    "build_persistence_panel",
    "build_workspace_state",
    "refresh_persistence_labels",
    "restore_workspace_state",
    "save_workspace_state",
]
