"""Infrastructure-tab helpers for the systems demo feature."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pygame import Rect

from gui_do import ButtonControl, InteractionContext, LabelControl, LivePoliteness, PanelControl, make_snapshot

from .systems_models import _VirtualCell

if TYPE_CHECKING:
    from .systems_feature import SystemsFeature


def build_infrastructure_panel(feature: SystemsFeature, rect: Rect) -> PanelControl:
    panel = PanelControl("systems_infrastructure_panel", Rect(rect), draw_background=False)
    telemetry_button = ButtonControl(
        "systems_infra_telemetry",
        Rect(0, 0, 176, 32),
        "Record Telemetry",
        feature._sample_telemetry,
        style="round",
    )
    infrastructure_label_top = feature._add_button_rows(
        panel,
        rect,
        0,
        [
            ButtonControl(
                "systems_infra_run_pipeline",
                Rect(0, 0, 156, 32),
                "Run Pipeline",
                feature._run_pipeline_demo,
                style="round",
            ),
            ButtonControl(
                "systems_infra_pointer_event",
                Rect(0, 0, 168, 32),
                "Next Pointer Event",
                feature._advance_interaction_state,
                style="round",
            ),
            ButtonControl(
                "systems_infra_schema",
                Rect(0, 0, 172, 32),
                "Toggle Schema Input",
                feature._toggle_schema_example,
                style="round",
            ),
            ButtonControl(
                "systems_infra_migrate",
                Rect(0, 0, 168, 32),
                "Migrate Snapshot",
                feature._run_snapshot_migration,
                style="round",
            ),
            ButtonControl(
                "systems_infra_theme_bus",
                Rect(0, 0, 194, 32),
                "Trigger Theme Invalidation",
                feature._trigger_theme_invalidation,
                style="round",
            ),
            ButtonControl(
                "systems_infra_virtualize",
                Rect(0, 0, 190, 32),
                "Refresh Virtual Window",
                feature._refresh_virtualization_demo,
                style="round",
            ),
            ButtonControl(
                "systems_infra_layout",
                Rect(0, 0, 170, 32),
                "Solve Constraints",
                feature._solve_constraint_layout,
                style="round",
            ),
            ButtonControl(
                "systems_infra_scope",
                Rect(0, 0, 156, 32),
                "Push Child Scope",
                feature._push_scope_demo,
                style="round",
            ),
            ButtonControl(
                "systems_infra_accessibility",
                Rect(0, 0, 176, 32),
                "Announce Accessibility",
                feature._run_accessibility_demo,
                style="round",
            ),
            ButtonControl(
                "systems_infra_audio",
                Rect(0, 0, 170, 32),
                "Emit Audio Cue",
                feature._run_audio_demo,
                style="round",
            ),
        ],
        left=feature.PANEL_PADDING_X + feature.LEFT_SIDE_INSET_X,
        width=max(
            1,
            rect.width - (feature.PANEL_PADDING_X * 2) - (feature.LEFT_SIDE_INSET_X * 2),
        ),
    )
    infrastructure_label_top = feature._add_single_column_button_row(
        panel,
        rect,
        infrastructure_label_top,
        telemetry_button,
        column_index=0,
        span_both_columns=True,
        span_from_window_left=False,
        left=feature.PANEL_PADDING_X,
        width=max(1, rect.width - (feature.PANEL_PADDING_X * 2) - feature.LEFT_SIDE_INSET_X),
    )

    feature.infrastructure_pipeline_label = LabelControl(
        "systems_infra_pipeline_status", Rect(0, 0, rect.width, 28), "", align="left"
    )
    feature.infrastructure_interaction_label = LabelControl(
        "systems_infra_interaction_status", Rect(0, 0, rect.width, 28), "", align="left"
    )
    feature.infrastructure_schema_label = LabelControl(
        "systems_infra_schema_status", Rect(0, 0, rect.width, 28), "", align="left"
    )
    feature.infrastructure_migration_label = LabelControl(
        "systems_infra_migration_status", Rect(0, 0, rect.width, 28), "", align="left"
    )
    feature.infrastructure_theme_bus_label = LabelControl(
        "systems_infra_theme_status", Rect(0, 0, rect.width, 28), "", align="left"
    )
    feature.infrastructure_virtualization_label = LabelControl(
        "systems_infra_virtualization_status", Rect(0, 0, rect.width, 28), "", align="left"
    )
    feature.infrastructure_layout_label = LabelControl(
        "systems_infra_layout_status", Rect(0, 0, rect.width, 28), "", align="left"
    )
    feature.infrastructure_scope_label = LabelControl(
        "systems_infra_scope_status", Rect(0, 0, rect.width, 28), "", align="left"
    )
    feature.infrastructure_runtime_label = LabelControl(
        "systems_infra_runtime_status", Rect(0, 0, rect.width, 56), "", align="left"
    )
    feature._place_vertical_label_stack(
        panel,
        Rect(
            feature.LABEL_INSET_X,
            infrastructure_label_top + 8,
            max(1, rect.width - feature.LABEL_INSET_X),
            344,
        ),
        [
            feature.infrastructure_pipeline_label,
            feature.infrastructure_interaction_label,
            feature.infrastructure_schema_label,
            feature.infrastructure_migration_label,
            feature.infrastructure_theme_bus_label,
            feature.infrastructure_virtualization_label,
            feature.infrastructure_layout_label,
            feature.infrastructure_scope_label,
            feature.infrastructure_runtime_label,
        ],
        gap=8,
    )
    feature._refresh_infrastructure_labels()
    return panel


def run_pipeline_demo(feature: SystemsFeature) -> None:
    result = feature._pipeline.run(" nightly ").result
    if feature.infrastructure_pipeline_label is not None:
        feature.infrastructure_pipeline_label.text = f"DataflowPipeline output: {result}"


def advance_interaction_state(feature: SystemsFeature) -> None:
    sequence = (
        "pointer_enter",
        "pointer_down",
        "drag_start",
        "pointer_up",
        "cancel",
    )
    event_kind = sequence[feature._interaction_event_index % len(sequence)]
    feature._interaction_event_index += 1
    changed = feature._interaction.handle_event(InteractionContext(event_kind=event_kind))
    if feature.infrastructure_interaction_label is not None:
        feature.infrastructure_interaction_label.text = (
            f"InteractionStateMachine event={event_kind} changed={changed} phase={feature._interaction.phase.name.lower()}"
        )


def toggle_schema_example(feature: SystemsFeature) -> None:
    feature._schema_use_invalid_value = not feature._schema_use_invalid_value
    if feature._schema_use_invalid_value:
        feature._schema_runtime.set_value("approver", "QA")
        feature._schema_runtime.set_value("channel", "beta")
    else:
        feature._schema_runtime.set_value("approver", "Mira")
        feature._schema_runtime.set_value("channel", "canary")
    feature._schema_runtime.validate_all()
    feature._refresh_infrastructure_labels()


def run_snapshot_migration(feature: SystemsFeature) -> None:
    snapshot = make_snapshot(feature._version_v1, {"pipeline": "nightly-gui"})
    migrated = feature._snapshot_migrator.migrate(snapshot, feature._version_v3)
    if feature.infrastructure_migration_label is not None:
        feature.infrastructure_migration_label.text = (
            f"SnapshotMigrator {snapshot['schema_version']} -> {migrated['schema_version']} data keys={sorted(migrated['data'].keys())}"
        )


def record_theme_invalidation(feature: SystemsFeature) -> None:
    feature._theme_invalidation_ticks += 1


def trigger_theme_invalidation(feature: SystemsFeature) -> None:
    feature._theme_invalidation_bus.trigger_invalidation()
    feature._refresh_infrastructure_labels()


def bind_virtual_cell(_feature: SystemsFeature, cell: _VirtualCell, index: int) -> None:
    cell.index = int(index)


def refresh_virtualization_demo(feature: SystemsFeature) -> None:
    feature._virtual_scroll_offset = (feature._virtual_scroll_offset + 48) % 480
    feature._virtual_core.refresh(scroll_offset=feature._virtual_scroll_offset, item_count=120)
    feature._refresh_infrastructure_labels()


def solve_constraint_layout(feature: SystemsFeature) -> None:
    resolved = feature._call_to_action_constraint.apply(Rect(0, 0, 220, 34), Rect(0, 0, 960, 540))
    if feature.infrastructure_layout_label is not None:
        feature.infrastructure_layout_label.text = (
            f"ConstraintLayout call_to_action -> x={resolved.left} y={resolved.top} w={resolved.width} h={resolved.height}"
        )


def push_scope_demo(feature: SystemsFeature) -> None:
    with feature._scope_stack.push() as child:
        child.bind(feature._service_key_channel, "stable")
        api_base = child.get(feature._service_key_api_base)
        channel = child.get(feature._service_key_channel)
        if feature.infrastructure_scope_label is not None:
            feature.infrastructure_scope_label.text = (
                f"ServiceScope child resolved api={api_base} channel={channel}; root channel remains canary"
            )


def run_accessibility_demo(feature: SystemsFeature) -> None:
    feature._accessibility_cycle += 1
    feature._accessibility_pipeline_node.enabled = not feature._accessibility_pipeline_node.enabled
    politeness = LivePoliteness.ASSERTIVE if feature._accessibility_cycle % 3 == 0 else LivePoliteness.POLITE
    feature._accessibility_bus.announce(
        f"Release checklist update {feature._accessibility_cycle}",
        politeness=politeness,
    )
    announcements = feature._accessibility_bus.consume_announcements()
    if announcements:
        latest = announcements[-1]
        feature._accessibility_last_announcement = f"{latest.politeness.value}: {latest.message}"
    feature._refresh_infrastructure_labels()


def run_audio_demo(feature: SystemsFeature) -> None:
    event_name = "systems.notification"
    feature._sound_demo_muted = not feature._sound_demo_muted
    if feature._sound_demo_muted:
        feature._sound_event_bus.mute(event_name)
    else:
        feature._sound_event_bus.unmute(event_name)
    feature._sound_last_emit_ok = feature._sound_event_bus.emit(event_name, volume=0.25)
    feature._refresh_infrastructure_labels()


def sample_telemetry(feature: SystemsFeature) -> None:
    with feature._telemetry.span("systems", "infrastructure_sample", {"tab": feature.active_tab_key}):
        feature._accessibility_tree.snapshot()
    feature._telemetry_sample_count = len(feature._telemetry.snapshot())
    feature._refresh_infrastructure_labels()


def refresh_infrastructure_labels(feature: SystemsFeature) -> None:
    if feature.infrastructure_pipeline_label is not None and not feature.infrastructure_pipeline_label.text:
        feature.infrastructure_pipeline_label.text = "DataflowPipeline ready: normalize -> stamp -> route"
    if feature.infrastructure_interaction_label is not None and not feature.infrastructure_interaction_label.text:
        feature.infrastructure_interaction_label.text = (
            f"InteractionStateMachine phase={feature._interaction.phase.name.lower()}"
        )
    if feature.infrastructure_schema_label is not None:
        errors = [
            *feature._schema_runtime.get_errors("channel"),
            *feature._schema_runtime.get_errors("approver"),
        ]
        if errors:
            feature.infrastructure_schema_label.text = f"SchemaFormRuntime errors: {'; '.join(errors)}"
        else:
            feature.infrastructure_schema_label.text = (
                f"SchemaFormRuntime valid for channel={feature._schema_runtime.get_value('channel')} "
                f"approver={feature._schema_runtime.get_value('approver')}"
            )
    if feature.infrastructure_migration_label is not None and not feature.infrastructure_migration_label.text:
        feature.infrastructure_migration_label.text = (
            f"SnapshotMigrator path available: {feature._snapshot_migrator.can_migrate(feature._version_v1, feature._version_v3)}"
        )
    if feature.infrastructure_theme_bus_label is not None:
        feature.infrastructure_theme_bus_label.text = (
            f"ThemeInvalidationBus callbacks triggered {feature._theme_invalidation_ticks} times"
        )
    if feature.infrastructure_virtualization_label is not None:
        first, last = feature._virtual_window.visible_range()
        feature.infrastructure_virtualization_label.text = (
            f"VirtualizationCore visible range [{first}, {last}] at scroll={feature._virtual_scroll_offset}; pool={feature._virtual_pool.pool_size}"
        )
    if feature.infrastructure_layout_label is not None and not feature.infrastructure_layout_label.text:
        feature.infrastructure_layout_label.text = "ConstraintLayout ready with container-relative constraints"
    if feature.infrastructure_scope_label is not None and not feature.infrastructure_scope_label.text:
        feature.infrastructure_scope_label.text = (
            f"ScopeStack root api={feature._scope_stack.root.get(feature._service_key_api_base)} "
            f"channel={feature._scope_stack.root.get(feature._service_key_channel)}"
        )
    if feature.infrastructure_runtime_label is not None:
        policy_runtime = getattr(feature, "runtime_policy", None)
        policy_count = len(getattr(policy_runtime, "_policies", ())) if policy_runtime is not None else 0

        effects_runtime = getattr(feature, "runtime_effects", None)
        effect_group_count = len(getattr(effects_runtime, "_groups", {})) if effects_runtime is not None else 0

        pipeline_runtime = getattr(feature, "runtime_event_pipelines", None)
        pipeline_count = len(getattr(pipeline_runtime, "_pipelines", {})) if pipeline_runtime is not None else 0

        queue_runtime = getattr(feature, "runtime_durable_queue", None)
        queue_total = 0
        queue_pending = 0
        queue_running = 0
        queue_completed = 0
        queue_failed = 0
        if queue_runtime is not None and hasattr(queue_runtime, "records"):
            try:
                queue_records = tuple(queue_runtime.records())
                queue_total = len(queue_records)
                queue_pending = sum(1 for record in queue_records if str(getattr(record, "status", "")) == "pending")
                queue_running = sum(1 for record in queue_records if str(getattr(record, "status", "")) == "running")
                queue_completed = sum(1 for record in queue_records if str(getattr(record, "status", "")) == "completed")
                queue_failed = sum(1 for record in queue_records if str(getattr(record, "status", "")) == "failed")
            except Exception:
                pass

        capabilities_runtime = getattr(feature, "runtime_capabilities", None)
        capability_count = 0
        if capabilities_runtime is not None and hasattr(capabilities_runtime, "snapshot"):
            try:
                capability_count = len(capabilities_runtime.snapshot())
            except Exception:
                capability_count = 0

        projection_score = int(getattr(feature, "_projected_release_score", 0))

        feature.infrastructure_runtime_label.text = (
            " | ".join(
                (
                    f"AccessibilityTree nodes={len(feature._accessibility_tree)} last='{feature._accessibility_last_announcement}'",
                    f"SoundEventBus events={feature._sound_event_bus.registered_event_names()} muted={feature._sound_demo_muted} played={feature._sound_last_emit_ok}",
                    f"TelemetryCollector samples={feature._telemetry_sample_count}",
                    (
                        "RuntimeSystems "
                        f"policy={policy_count} effects={effect_group_count} pipelines={pipeline_count} "
                        f"queue={queue_total} (p={queue_pending} r={queue_running} c={queue_completed} f={queue_failed}) "
                        f"caps={capability_count} projection={projection_score}"
                    ),
                )
            )
        )


__all__ = [
    "advance_interaction_state",
    "bind_virtual_cell",
    "build_infrastructure_panel",
    "push_scope_demo",
    "record_theme_invalidation",
    "refresh_infrastructure_labels",
    "refresh_virtualization_demo",
    "run_accessibility_demo",
    "run_audio_demo",
    "run_pipeline_demo",
    "run_snapshot_migration",
    "sample_telemetry",
    "solve_constraint_layout",
    "toggle_schema_example",
    "trigger_theme_invalidation",
]
