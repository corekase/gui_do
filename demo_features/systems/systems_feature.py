"""Systems demo window integrated into the gui_do main scene."""

from __future__ import annotations

from pathlib import Path
import tempfile

from pygame import Rect, Surface

from gui_do import (
    AccessibilityBus,
    AccessibilityNode,
    AccessibilityRole,
    AccessibilityTree,
    AppStateStore,
    AnchoredWindowSpec,
    AnimationStateMachine,
    AnimationTransitionMode,
    AsyncFieldValidator,
    AsyncFormValidator,
    ButtonControl,
    Camera2D,
    CollectionView,
    CollectionViewQuery,
    CommandHistory,
    CooperativeScheduler,
    Debouncer,
    DataCache,
    DataflowPipeline,
    DirtyRegionTracker,
    Emitter,
    FieldGraphSchema,
    FieldSchema,
    Feature,
    FormField,
    FrameTimer,
    GridLayout,
    GridPlacement,
    InteractionStateMachine,
    LabelControl,
    LocaleRegistry,
    MeasurePolicy,
    MigrationRegistry,
    MigrationStep,
    ImageControl,
    PanelControl,
    ParticleLayer,
    PipelineStage,
    RecyclePool,
    SchemaFormRuntime,
    SchemaVersion,
    SceneGraph2D,
    SceneTimeline,
    ScopeStack,
    ScopedTheme,
    SoundBankRegistry,
    SoundCue,
    SoundEventBus,
    ServiceKey,
    SettingsRegistry,
    SnapshotMigrator,
    StateMachine,
    SurfaceCompositor,
    TaskScheduler,
    Throttler,
    TextFlow,
    TextSearcher,
    TextSpan,
    ThemeManager,
    ThemeInvalidationBus,
    Timers,
    TelemetryCollector,
    TileMap,
    TileSet,
    StringTable,
    UndoContextManager,
    ValidationPolicy,
    Router,
    HierarchicalStateMachine,
    Node2D,
    VirtualizationCore,
    VirtualizedWindow,
    WindowControl,
    WorkspacePersistenceManager,
    WorkspaceState,
    create_feature_presented_window,
    TransitionEvent,
    TransitionManager,
    TransitionSpec,
    TweenManager,
)
from gui_do.features.data_driven_runtime import (
    bind_feature_runtime,
    CheckpointDomainSpec,
    CheckpointSpec,
    ContractMigrationSpec,
    ExecutionContextSpec,
    CapabilityProviderSpec,
    CapabilityRequirementSpec,
    DurableOperationBindingSpec,
    DurableOperationQueueSpec,
    EffectBindingSpec,
    EventSubscriptionSpec,
    EventPipelineSpec,
    EventPipelineStageSpec,
    FailurePolicySpec,
    FeatureOperationSpec,
    MigrationStepSpec,
    MigrationTargetSpec,
    ObservableEffectSpec,
    ProjectionNodeSpec,
    ProjectionSpec,
    ReactiveGraphSpec,
    ReactiveNodeSpec,
    ReactiveSourceSpec,
    RuntimePolicySpec,
    RoutedRuntimeSpec,
    SagaSpec,
    SagaStepSpec,
    ServiceBindingSpec,
    StoreSubscriptionSpec,
    WorkloadBudgetClassSpec,
    WorkloadBudgetSpec,
    shutdown_feature_runtime,
)
from gui_do.layout.constraint_layout import AnchorConstraint
from .systems_data_helpers import (
    add_backlog_item as add_backlog_item_helper,
    build_data_panel as build_data_panel_helper,
    cache_payload_for_backlog_item as cache_payload_for_backlog_item_helper,
    clear_backlog_cache as clear_backlog_cache_helper,
    on_backlog_filter_changed as on_backlog_filter_changed_helper,
    on_backlog_selected as on_backlog_selected_helper,
    on_backlog_view_refreshed as on_backlog_view_refreshed_helper,
    project_backlog_item as project_backlog_item_helper,
    refresh_backlog_labels as refresh_backlog_labels_helper,
    refresh_backlog_view as refresh_backlog_view_helper,
    selected_backlog_filter as selected_backlog_filter_helper,
)
from .systems_history_helpers import (
    advance_history_stage as advance_history_stage_helper,
    batch_promote_history_stage as batch_promote_history_stage_helper,
    build_history_panel as build_history_panel_helper,
    redo_history_stage as redo_history_stage_helper,
    refresh_history_labels as refresh_history_labels_helper,
    undo_history_stage as undo_history_stage_helper,
)
from .systems_infrastructure_helpers import (
    apply_runtime_contract_migration as apply_runtime_contract_migration_helper,
    advance_interaction_state as advance_interaction_state_helper,
    bind_virtual_cell as bind_virtual_cell_helper,
    build_infrastructure_panel as build_infrastructure_panel_helper,
    push_scope_demo as push_scope_demo_helper,
    record_theme_invalidation as record_theme_invalidation_helper,
    refresh_infrastructure_labels as refresh_infrastructure_labels_helper,
    refresh_virtualization_demo as refresh_virtualization_demo_helper,
    run_runtime_checkpoint as run_runtime_checkpoint_helper,
    run_runtime_saga as run_runtime_saga_helper,
    run_accessibility_demo as run_accessibility_demo_helper,
    run_audio_demo as run_audio_demo_helper,
    run_pipeline_demo as run_pipeline_demo_helper,
    run_snapshot_migration as run_snapshot_migration_helper,
    sample_telemetry as sample_telemetry_helper,
    solve_constraint_layout as solve_constraint_layout_helper,
    toggle_schema_example as toggle_schema_example_helper,
    trigger_theme_invalidation as trigger_theme_invalidation_helper,
)
from .systems_helpers import (
    place_compact_labeled_row,
    place_graphics_particle_layer,
    place_row_controls,
    place_text_preview_region,
    place_vertical_grid_sequence,
    place_vertical_label_stack,
    row_bounds,
    sync_graphics_emitter_offsets,
)
from .systems_models import _BacklogItem, _VirtualCell
from .systems_motion_helpers import (
    build_motion_panel as build_motion_panel_helper,
    cycle_motion_animation_state as cycle_motion_animation_state_helper,
    on_motion_animation_state_changed as on_motion_animation_state_changed_helper,
    play_motion_timeline as play_motion_timeline_helper,
    refresh_motion_labels as refresh_motion_labels_helper,
    run_motion_sequence as run_motion_sequence_helper,
    run_motion_tween as run_motion_tween_helper,
    set_motion_sequence_stage as set_motion_sequence_stage_helper,
    set_motion_timeline_stage as set_motion_timeline_stage_helper,
    toggle_motion_transition as toggle_motion_transition_helper,
)
from .systems_persistence_helpers import (
    apply_production_profile as apply_production_profile_helper,
    apply_review_profile as apply_review_profile_helper,
    build_persistence_panel as build_persistence_panel_helper,
    build_workspace_state as build_workspace_state_helper,
    refresh_persistence_labels as refresh_persistence_labels_helper,
    restore_workspace_state as restore_workspace_state_helper,
    save_workspace_state as save_workspace_state_helper,
)
from .systems_presenter import _SystemsPresenter
from .systems_scheduling_helpers import (
    build_scheduling_panel as build_scheduling_panel_helper,
    build_artifact_job as build_artifact_job_helper,
    on_debounced_burst_commit as on_debounced_burst_commit_helper,
    on_throttled_burst_input as on_throttled_burst_input_helper,
    on_timer_probe_complete as on_timer_probe_complete_helper,
    on_timer_probe_tick as on_timer_probe_tick_helper,
    queue_background_job as queue_background_job_helper,
    refresh_scheduling_labels as refresh_scheduling_labels_helper,
    simulate_rate_limited_input as simulate_rate_limited_input_helper,
    start_timer_probe as start_timer_probe_helper,
    start_rollout_sequence as start_rollout_sequence_helper,
)
from .systems_state_helpers import (
    add_release_blocker as add_release_blocker_helper,
    advance_active_context as advance_active_context_helper,
    advance_release_state_machine as advance_release_state_machine_helper,
    approve_release_item as approve_release_item_helper,
    build_state_panel as build_state_panel_helper,
    cycle_release_router as cycle_release_router_helper,
    on_state_context_changed as on_state_context_changed_helper,
    redo_active_context as redo_active_context_helper,
    refresh_state_labels as refresh_state_labels_helper,
    undo_active_context as undo_active_context_helper,
)
from .systems_graphics_helpers import (
    advance_graphics_demo as advance_graphics_demo_helper,
    advance_graphics_runtime as advance_graphics_runtime_helper,
    build_graphics_panel as build_graphics_panel_helper,
    build_surface_effect_source as build_surface_effect_source_helper,
    cycle_surface_effect as cycle_surface_effect_helper,
    pan_tile_camera as pan_tile_camera_helper,
    refresh_graphics_labels as refresh_graphics_labels_helper,
    refresh_surface_effect_preview as refresh_surface_effect_preview_helper,
    render_tile_map_preview as render_tile_map_preview_helper,
    reset_particle_layer as reset_particle_layer_helper,
    trigger_particle_burst as trigger_particle_burst_helper,
)
from .systems_text_helpers import (
    apply_text_locale_regex_preset as apply_text_locale_regex_preset_helper,
    apply_text_regex_preset as apply_text_regex_preset_helper,
    build_text_panel as build_text_panel_helper,
    build_text_preview_spans as build_text_preview_spans_helper,
    next_text_match as next_text_match_helper,
    on_text_locale_changed as on_text_locale_changed_helper,
    on_text_query_changed as on_text_query_changed_helper,
    rebuild_text_document as rebuild_text_document_helper,
    rebuild_text_searcher as rebuild_text_searcher_helper,
    refresh_text_labels as refresh_text_labels_helper,
    render_text_preview as render_text_preview_helper,
    render_text_preview_fallback as render_text_preview_fallback_helper,
    replace_first_text_match as replace_first_text_match_helper,
    run_text_search as run_text_search_helper,
    toggle_text_case_sensitive as toggle_text_case_sensitive_helper,
    toggle_text_regex as toggle_text_regex_helper,
    toggle_text_whole_word as toggle_text_whole_word_helper,
)
from .systems_theme_helpers import (
    build_theme_panel as build_theme_panel_helper,
    on_theme_changed as on_theme_changed_helper,
    refresh_theme_labels as refresh_theme_labels_helper,
    toggle_review_scope as toggle_review_scope_helper,
)
from .systems_validation_helpers import (
    apply_suggested_name as apply_suggested_name_helper,
    build_validation_panel as build_validation_panel_helper,
    check_pipeline_name as check_pipeline_name_helper,
    on_deployment_name_changed as on_deployment_name_changed_helper,
    on_environment_changed as on_environment_changed_helper,
    refresh_validation_labels as refresh_validation_labels_helper,
    run_local_validation_checks as run_local_validation_checks_helper,
)
from .systems_specs import (
    SYSTEMS_BUTTON_ROW_GAP,
    SYSTEMS_BUTTON_ROW_HEIGHT,
    SYSTEMS_BUTTON_ROW_SPACING,
    SYSTEMS_HISTORY_STAGES,
    SYSTEMS_LABEL_INSET_X,
    SYSTEMS_LEFT_SIDE_INSET_X,
    SYSTEMS_MOTION_ANIMATION_STATES,
    SYSTEMS_PANEL_PADDING_X,
    SYSTEMS_SURFACE_EFFECT_CYCLE,
    SYSTEMS_TAB_DEFINITIONS,
)
from gui_do.controls.data.list_view_control import ListItem


_SYSTEMS_FAILURE_TOPIC = "systems.runtime_operation.failed"
_SYSTEMS_PERSISTENCE_POLICY = "systems.persistence"
_SYSTEMS_OP_APPLY_REVIEW_PROFILE = "systems.apply_review_profile"
_SYSTEMS_OP_APPLY_PRODUCTION_PROFILE = "systems.apply_production_profile"
_SYSTEMS_OP_SAVE_WORKSPACE = "systems.save_workspace_state"
_SYSTEMS_OP_RESTORE_WORKSPACE = "systems.restore_workspace_state"
_SYSTEMS_OP_SNAPSHOT_MIGRATION = "systems.run_snapshot_migration"
_SYSTEMS_EVENT_PIPELINE_FAILURES = "systems.runtime.failures"
_SYSTEMS_EVENT_PIPELINE_BURST = "systems.runtime.burst"


class SystemsFeature(Feature):
    """Tabbed main-scene systems window with practical demo integrations."""

    TAB_DEFINITIONS = SYSTEMS_TAB_DEFINITIONS
    PANEL_PADDING_X = SYSTEMS_PANEL_PADDING_X
    LEFT_SIDE_INSET_X = SYSTEMS_LEFT_SIDE_INSET_X
    LABEL_INSET_X = SYSTEMS_LABEL_INSET_X
    BUTTON_ROW_HEIGHT = SYSTEMS_BUTTON_ROW_HEIGHT
    BUTTON_ROW_GAP = SYSTEMS_BUTTON_ROW_GAP
    BUTTON_ROW_SPACING = SYSTEMS_BUTTON_ROW_SPACING

    HOST_REQUIREMENTS = {
        "build": ("app", "root", "screen_rect"),
        "on_update": ("app",),
    }

    def __init__(self) -> None:
        super().__init__("systems_demo", scene_name="main")
        self._frame_timer = FrameTimer()
        self._runtime_spec = None
        self.runtime_scope = None
        self.operation_bus = None
        self.runtime_execution_context = None
        self.runtime_budget = None
        self.runtime_checkpoint = None
        self.runtime_saga = None
        self.runtime_reactive_graph = None
        self.runtime_migration = None
        self.runtime_policy = None
        self.runtime_effects = None
        self.runtime_event_pipelines = None
        self.runtime_durable_queue = None
        self.runtime_capabilities = None
        self.runtime_projection = None
        self.state_store = None
        self.active_tab_key = "data"
        self.demo = None
        self.window = None
        self.systems_tabs = None
        self._tab_panels: dict[str, PanelControl] = {}
        self._motion_timeline: SceneTimeline | None = None
        self._motion_tween_value = 0.0
        self._motion_timeline_stage = "Idle"
        self._motion_sequence_stage = "Idle"
        self._motion_timeline_cycles = 0
        self._motion_sequence_runs = 0
        self._motion_transition_value = 0.0
        self._motion_transition_phase = "Idle"
        self._motion_animation_state = "idle"
        self._motion_animation_value = 0.0
        self._motion_tweens = TweenManager()
        self._transition_manager = TransitionManager(self._motion_tweens)
        self._transition_manager.register(
            self,
            TransitionEvent.SHOW,
            TransitionSpec(
                attr="_motion_transition_value",
                start_value=0.0,
                end_value=1.0,
                duration_seconds=0.25,
                easing="ease_out",
            ),
        )
        self._transition_manager.register(
            self,
            TransitionEvent.HIDE,
            TransitionSpec(
                attr="_motion_transition_value",
                start_value=1.0,
                end_value=0.0,
                duration_seconds=0.25,
                easing="ease_in",
            ),
        )
        self._motion_animation_states = SYSTEMS_MOTION_ANIMATION_STATES
        self._motion_animation_state_index = 0
        self._motion_animation_state_machine = AnimationStateMachine(self._motion_tweens)
        self._motion_animation_state_machine.register_state(
            "idle",
            lambda seq: seq.then(
                target=self,
                attr="_motion_animation_value",
                end_value=0.15,
                duration_seconds=0.12,
            ),
        )
        self._motion_animation_state_machine.register_state(
            "hover",
            lambda seq: seq.then(
                target=self,
                attr="_motion_animation_value",
                end_value=0.7,
                duration_seconds=0.16,
            ),
        )
        self._motion_animation_state_machine.register_state(
            "press",
            lambda seq: seq.then(
                target=self,
                attr="_motion_animation_value",
                end_value=1.0,
                duration_seconds=0.09,
            ).then(
                target=self,
                attr="_motion_animation_value",
                end_value=0.45,
                duration_seconds=0.09,
            ),
        )
        self._motion_animation_state_machine.register_transition(
            "press",
            "idle",
            mode=AnimationTransitionMode.COMPLETE_THEN_TRANSITION,
        )
        self._motion_animation_state_machine.on_state_changed(self._on_motion_animation_state_changed)
        self._surface_effect_cycle = SYSTEMS_SURFACE_EFFECT_CYCLE
        self._surface_effect_index = 0
        self._surface_effect_source: Surface | None = None
        self._surface_effect_preview: ImageControl | None = None
        self._surface_effect_label = None

        self._backlog_items = [
            _BacklogItem("QA smoke pass", "Review", 1, "Mira"),
            _BacklogItem("Keyboard navigation audit", "Review", 2, "Jules"),
            _BacklogItem("Screenshot export", "Ready", 3, "Tao"),
            _BacklogItem("Theme preset sync", "Planned", 4, "Ari"),
        ]
        self._next_backlog_index = 0
        self._backlog_cache = DataCache(max_size=8)
        self._backlog_view = CollectionView(
            self._backlog_items,
            query=CollectionViewQuery(
                sort_key=lambda item: (item.priority, item.title),
                projector=self._project_backlog_item,
            ),
        )
        self._backlog_unsub = None
        self._selected_backlog_item: _BacklogItem | None = None
        self.data_filter_dropdown = None
        self.data_list = None
        self.data_summary_label = None
        self.data_cache_label = None
        self.data_detail_label = None

        self._deployment_name_field = FormField("deployment_name", "nightly-gui")
        self._environment_field = FormField("environment", "Staging")
        self._name_validator = AsyncFieldValidator(
            field=self._deployment_name_field,
            local_rules=[lambda value: None if str(value).strip() else "Name is required"],
            async_check=self._check_pipeline_name,
            debounce_ms=250,
        )
        self._environment_validator = AsyncFieldValidator(
            field=self._environment_field,
            local_rules=[
                lambda value: None
                if str(value) in {"Staging", "QA", "Production"}
                else "Choose a valid target environment"
            ],
        )
        self._form_validator = AsyncFormValidator([self._name_validator, self._environment_validator])
        self.validation_name_input = None
        self.validation_environment_dropdown = None
        self.validation_state_label = None
        self.validation_local_label = None
        self.validation_async_label = None

        self._history = CommandHistory()
        self._history_stages = SYSTEMS_HISTORY_STAGES
        self._history_stage_index = 0
        self.history_current_label = None
        self.history_undo_label = None
        self.history_redo_label = None

        self._theme_manager = ThemeManager()
        self._theme_manager.register_theme(
            "sunrise",
            {
                "primary": (203, 92, 44),
                "surface": (246, 234, 219),
                "text": (54, 37, 29),
            },
        )
        self._review_scope = ScopedTheme(
            {
                "primary": (194, 66, 43),
                "surface": (255, 240, 231),
                "text": (78, 44, 35),
            },
            name="review",
        )
        self._review_scope_enabled = False
        self.theme_dropdown = None
        self.theme_state_label = None
        self.theme_scope_label = None
        self.theme_resolved_label = None

        self._release_store = AppStateStore(
            {
                "pending": 4,
                "approved": 1,
                "blocked": 0,
                "status": "Review",
            }
        )
        self._release_readiness = self._release_store.select(
            lambda state: max(0, int(state.get("approved", 0)) * 25 - int(state.get("blocked", 0)) * 10)
        )
        self._state_history = CommandHistory()
        self._state_build_history = CommandHistory()
        self._state_stages = ("Draft", "Review", "Approved", "Released")
        self._state_stage_index = 0
        self._state_build_stages = ("Queued", "Running", "Passed")
        self._state_build_stage_index = 0
        self._undo_context = UndoContextManager(default_key="release")
        self._undo_context.register("release", self._state_history, make_active=True)
        self._undo_context.register("build", self._state_build_history)
        self._undo_context_key = "release"
        self._release_state_machine = StateMachine("draft")
        self._release_state_machine.add_state("review")
        self._release_state_machine.add_state("approved")
        self._release_state_machine.add_state("released")
        self._release_state_machine.add_transition("draft", "review", trigger="advance")
        self._release_state_machine.add_transition("review", "approved", trigger="advance")
        self._release_state_machine.add_transition("approved", "released", trigger="advance")
        self._release_state_machine.add_transition("released", "draft", trigger="advance")
        release_ring_machine = StateMachine("canary")
        release_ring_machine.add_state("stable")
        release_ring_machine.add_transition("canary", "stable", trigger="promote")
        release_ring_machine.add_transition("stable", "canary", trigger="reset")
        self._release_hierarchical_state_machine = HierarchicalStateMachine("planning")
        self._release_hierarchical_state_machine.add_history(
            "execution",
            release_ring_machine,
            initial="canary",
        )
        self._release_hierarchical_state_machine.add_transition("planning", "execution", trigger="start")
        self._release_hierarchical_state_machine.add_transition("execution", "planning", trigger="pause")
        self._release_hierarchical_state_machine.trigger("start")
        self._release_router = Router()
        self._release_router.register("/main", "main")
        self._release_router.register("/systems", "main")
        self._release_router.register("/showcase", "control_showcase")
        self._release_router.push("/systems", {"entry": "task_panel"})
        self._router_cycle_paths = ("/showcase", "/main", "/systems")
        self._router_cycle_index = 0
        self.state_context_dropdown = None
        self.state_store_label = None
        self.state_readiness_label = None
        self.state_context_label = None
        self.state_machine_label = None
        self.state_router_label = None

        self._pipeline = DataflowPipeline(
            [
                PipelineStage("normalize", lambda value, _token: str(value).strip().lower()),
                PipelineStage("stamp", lambda value, _token: f"{value}-signed"),
                PipelineStage("route", lambda value, _token: f"artifact://release/{value}"),
            ]
        )
        self._interaction = InteractionStateMachine.with_standard_pointer_transitions()
        self._interaction_event_index = 0
        self._schema_runtime = SchemaFormRuntime(
            FieldGraphSchema(
                [
                    FieldSchema(
                        "channel",
                        default="canary",
                        required=True,
                        validators=[
                            lambda value: None if str(value) in {"canary", "stable"} else "Channel must be canary or stable"
                        ],
                    ),
                    FieldSchema(
                        "approver",
                        default="Mira",
                        required=True,
                        validators=[
                            lambda value: None
                            if len(str(value).strip()) >= 3
                            else "Approver must have at least 3 characters"
                        ],
                    ),
                ]
            ),
            ValidationPolicy.ON_CHANGE,
        )
        self._schema_use_invalid_value = False
        self._version_v1 = SchemaVersion(1, 0)
        self._version_v2 = SchemaVersion(2, 0)
        self._version_v3 = SchemaVersion(3, 0)
        self._migration_registry = MigrationRegistry()
        self._migration_registry.register(
            MigrationStep(self._version_v1, self._version_v2, lambda data: {**data, "build_template": "modern"})
        )
        self._migration_registry.register(
            MigrationStep(self._version_v2, self._version_v3, lambda data: {**data, "checks": ["lint", "tests"]})
        )
        self._snapshot_migrator = SnapshotMigrator(self._migration_registry)
        self._theme_invalidation_ticks = 0
        self._theme_invalidation_bus = ThemeInvalidationBus(theme_manager=self._theme_manager)
        self._theme_invalidation_bus.register(self, self._record_theme_invalidation)
        self._virtual_window = VirtualizedWindow(
            viewport_height=108,
            overscan=1,
            policy=MeasurePolicy(item_height=24),
        )
        self._virtual_pool = RecyclePool(_VirtualCell, reset_fn=lambda cell: setattr(cell, "index", -1))
        self._virtual_core = VirtualizationCore(self._virtual_window, self._virtual_pool, self._bind_virtual_cell)
        self._virtual_scroll_offset = 0
        self._call_to_action_constraint = AnchorConstraint(
            left_frac=0.1,
            top=84,
            min_width=320,
            max_width=320,
        )
        self._scope_stack = ScopeStack()
        self._service_key_api_base: ServiceKey[str] = ServiceKey("api_base")
        self._service_key_channel: ServiceKey[str] = ServiceKey("release_channel")
        self._service_key_release_store: ServiceKey[AppStateStore] = ServiceKey("systems.release_store")
        self._scope_stack.root.bind(self._service_key_api_base, "https://deploy.internal")
        self._scope_stack.root.bind(self._service_key_channel, "canary")
        self._accessibility_tree = AccessibilityTree()
        self._accessibility_root_node = AccessibilityNode(
            role=AccessibilityRole.WINDOW,
            label="Systems Window",
        )
        self._accessibility_pipeline_node = AccessibilityNode(
            role=AccessibilityRole.BUTTON,
            label="Run Pipeline",
            description="Infrastructure pipeline action",
        )
        self._accessibility_tree.register(self._accessibility_root_node)
        self._accessibility_tree.register(self._accessibility_pipeline_node, parent=self._accessibility_root_node)
        self._accessibility_bus = AccessibilityBus()
        self._accessibility_cycle = 0
        self._accessibility_last_announcement = "AccessibilityBus is idle."

        self._sound_bank = SoundBankRegistry()
        self._sound_bank.register(
            "systems.notification",
            SoundCue("demo_features/data/sounds/click.ogg", volume=0.3),
        )
        self._sound_event_bus = SoundEventBus()
        self._sound_event_bus.load_bank(self._sound_bank)
        self._sound_demo_muted = False
        self._sound_last_emit_ok = False

        self._telemetry = TelemetryCollector()
        self._telemetry.enable()
        self._telemetry_sample_count = 0

        self.infrastructure_pipeline_label = None
        self.infrastructure_interaction_label = None
        self.infrastructure_schema_label = None
        self.infrastructure_migration_label = None
        self.infrastructure_theme_bus_label = None
        self.infrastructure_virtualization_label = None
        self.infrastructure_layout_label = None
        self.infrastructure_scope_label = None
        self.infrastructure_checkpoint_label = None
        self.infrastructure_saga_label = None
        self.infrastructure_runtime_label = None
        self._runtime_checkpoint_status = "Runtime checkpoint ready: click capture to persist scoped demo state."
        self._runtime_saga_status = "Runtime saga idle: start the rollout saga to orchestrate profile + persistence operations."
        self._runtime_migration_status = "Runtime migration ready: contract payload starts at v1.0 and upgrades to v2.0."
        self._runtime_contract_payload_version = "1.0"
        self._runtime_contract_payload = {
            "queue_depth": "2",
            "profile": "review",
            "region": "us-central",
        }
        self._runtime_reactive_release_score = 0

        self._task_scheduler = TaskScheduler(max_workers=1)
        self._task_job_index = 0
        self._task_last_summary = "TaskScheduler idle: no background jobs queued yet."
        self._task_last_failure = ""
        self._cooperative_scheduler = CooperativeScheduler()
        self._timers = Timers()
        self._throttle_event_count = 0
        self._throttle_last_value = 0
        self._debounce_commit_count = 0
        self._debounce_last_value = "none"
        self._rate_limiter_status = "Debouncer/Throttler idle: no burst input sampled yet."
        self._throttler = Throttler(
            interval_ms=120,
            callback=self._on_throttled_burst_input,
            timers=self._timers,
            timer_id="systems_throttled_burst",
        )
        self._debouncer = Debouncer(
            delay_ms=240,
            callback=self._on_debounced_burst_commit,
            timers=self._timers,
            timer_id="systems_debounced_commit",
        )
        self._timer_tick_count = 0
        self._timer_probe_armed = False
        self._timer_last_event = "Timers idle: no probe callbacks yet."
        self._rollout_handle = None
        self._rollout_phase = "Idle"
        self.scheduling_task_label = None
        self.scheduling_rollout_label = None
        self.scheduling_timer_label = None
        self.scheduling_rate_limiter_label = None
        self.scheduling_timeline_label = None
        self.scheduling_tween_label = None
        self.scheduling_sequence_label = None
        self.motion_intro_label = None

        self._settings_registry = SettingsRegistry()
        self._settings_registry.declare("systems", "profile", default="review", label="Release Profile")
        self._settings_registry.declare("systems", "autosave", default=True, label="Autosave Workspace")
        self._settings_registry.declare("systems", "parallel_checks", default=2, label="Parallel Checks")
        self._workspace_persistence = WorkspacePersistenceManager()
        self._workspace_persistence.register_settings("systems", self._settings_registry)
        self._workspace_state_path = Path(tempfile.gettempdir()) / "gui_do_demo" / "systems_workspace_state.json"
        self._saved_workspace_state: WorkspaceState | None = None
        self._persistence_last_status = "WorkspacePersistenceManager ready to serialize systems settings."
        self._persistence_last_report: dict[str, object] | None = None
        self.persistence_overview_label = None
        self.persistence_settings_label = None
        self.persistence_status_label = None

        preview_rect = Rect(0, 0, 520, 180)
        self._particle_layer = ParticleLayer("systems_graphics_particle_layer", preview_rect, max_particles=1024)
        self._particle_ambient_emitter = Emitter(
            x=preview_rect.width * 0.5,
            y=preview_rect.height * 0.78,
            rate=150,
            lifetime=(1.0, 1.8),
            speed=(42, 96),
            angle_range=(258, 282),
            size=(2.0, 1.0),
            colors=[(255, 214, 140), (255, 241, 188)],
            gravity=-26,
        )
        self._particle_burst_emitter = Emitter(
            x=preview_rect.width * 0.5,
            y=preview_rect.height * 0.42,
            rate=0,
            burst_count=0,
            lifetime=(0.7, 1.3),
            speed=(70, 170),
            angle_range=(0, 360),
            size=(3.0, 1.0),
            colors=[(255, 119, 87), (255, 196, 87), (87, 166, 255), (87, 224, 173)],
            gravity=120,
        )
        self.graphics_particle_label = None
        self.graphics_layer_label = None
        self.graphics_scene_graph_label = None
        self.graphics_compositor_label = None
        self.graphics_tile_map_label = None
        self.graphics_surface_effects_label = None
        self.graphics_tile_preview_canvas = None
        self._burst_emitter_panel_offset: tuple = (0.0, 0.0)
        self._ambient_emitter_panel_offset: tuple = (0.0, 0.0)
        self._graphics_scene_graph = SceneGraph2D()
        release_node = Node2D("release_stage", pos=(84.0, 56.0), scale=(1.0, 1.0))
        release_node.add_child(Node2D("approval_badge", pos=(36.0, 4.0), scale=(0.8, 0.8)))
        release_node.add_child(Node2D("timeline_anchor", pos=(18.0, 28.0), scale=(1.1, 1.0)))
        self._graphics_scene_graph.add(release_node)
        self._graphics_camera = Camera2D(Rect(0, 0, preview_rect.width, preview_rect.height), zoom=1.0)
        self._graphics_dirty_tracker = DirtyRegionTracker()
        self._graphics_compositor = SurfaceCompositor((preview_rect.width, preview_rect.height))
        self._graphics_compositor.add_layer("scene", z_index=0)
        self._graphics_compositor.add_layer("particles", z_index=10, opacity=0.92)
        self._graphics_compositor.add_layer("ui", z_index=20)
        tile_atlas = Surface((32, 16))
        tile_atlas.fill((61, 112, 74), Rect(0, 0, 16, 16))
        tile_atlas.fill((102, 132, 72), Rect(16, 0, 16, 16))
        self._graphics_tile_set = TileSet(tile_atlas, tile_w=16, tile_h=16)
        self._graphics_tile_map = TileMap(tile_w=16, tile_h=16, cols=40, rows=24, tile_set=self._graphics_tile_set)
        self._graphics_tile_map.fill(0)
        self._graphics_tile_map.fill_rect(4, 2, 10, 5, 1)
        self._graphics_tile_map.fill_rect(21, 10, 8, 7, 1)
        self._graphics_tile_camera = Rect(0, 0, preview_rect.width, preview_rect.height)
        self._graphics_runtime_step = 0
        self._reset_particle_layer()

        self._locale_registry = LocaleRegistry(default_locale="en", fallback_locale="en")
        self._locale_registry.register(
            StringTable(
                "en",
                {
                    "systems.text.title": "Release Notes",
                    "systems.text.summary": "The release candidate adds systems demos for scheduling, graphics, and persistence.",
                    "systems.text.actions": "Action items: verify smoke checks, confirm rollback path, and announce the rollout.",
                    "systems.text.hint": "Search this note for keywords like release, rollout, or checks.",
                    "systems.text.replacement": "deployment",
                },
            )
        )
        self._locale_registry.register(
            StringTable(
                "es",
                {
                    "systems.text.title": "Notas de Lanzamiento",
                    "systems.text.summary": "La version candidata agrega demos de sistemas para planificacion, graficos y persistencia.",
                    "systems.text.actions": "Tareas: verificar pruebas rapidas, confirmar reversa y anunciar el despliegue.",
                    "systems.text.hint": "Busca palabras como despliegue, planificacion o pruebas.",
                    "systems.text.replacement": "entrega",
                },
            )
        )
        self._locale_registry.register(
            StringTable(
                "fr",
                {
                    "systems.text.title": "Notes de Version",
                    "systems.text.summary": "Cette version ajoute des demos systeme pour l'ordonnancement, le rendu et la persistance.",
                    "systems.text.actions": "Actions: verifier les controles, confirmer le plan de retour, puis annoncer le deploiement.",
                    "systems.text.hint": "Recherchez des mots comme deploiement, verifications ou etapes.",
                    "systems.text.replacement": "livraison",
                },
            )
        )
        self._text_search_query = "release"
        self._text_search_cursor = 0
        self._text_last_action = "Text systems ready."
        self._text_case_sensitive = False
        self._text_whole_word = False
        self._text_use_regex = False
        self._text_searcher = TextSearcher(
            "",
            case_sensitive=self._text_case_sensitive,
            whole_word=self._text_whole_word,
            use_regex=self._text_use_regex,
        )
        self._text_flow = TextFlow(width=480, line_spacing=3)
        self._projected_release_score = 0
        self.text_mode_case_button = None
        self.text_mode_whole_word_button = None
        self.text_mode_regex_button = None
        self.text_locale_dropdown = None
        self.text_query_input = None
        self.text_search_status_label = None
        self.text_search_match_label = None
        self.text_preview_canvas = None
        self._rebuild_text_document()

    def build(self, host) -> None:
        self.window = create_feature_presented_window(
            host,
            feature=self,
            presenter_cls=_SystemsPresenter,
            spec=self._make_window_spec(host),
            window_control_cls=WindowControl,
        )

    def bind_runtime(self, host) -> None:
        self.demo = host
        runtime_spec = self._build_runtime_spec(host)
        bind_feature_runtime(
            self,
            host,
            runtime_spec=runtime_spec,
            runtime_spec_attr_name="_runtime_spec",
        )
        if callable(self._backlog_unsub) and self.runtime_scope is not None:
            self.runtime_scope.add_cleanup(self._backlog_unsub)
        if self.runtime_scope is not None:
            self.runtime_scope.add_cleanup(lambda: self._theme_invalidation_bus.unregister(self))

    def shutdown_runtime(self, host) -> None:
        shutdown_feature_runtime(
            self,
            host,
            runtime_spec=self._runtime_spec,
            runtime_spec_attr_name="_runtime_spec",
        )
        self._task_scheduler.shutdown()
        self._sound_event_bus.stop_all()
        self._backlog_unsub = None
        self.state_store = None

    def on_update(self, host) -> None:
        if self.window is None or not self.window.visible:
            return
        dt = self._frame_timer.tick()
        self._timers.update(dt)
        self._task_scheduler.update()
        self._cooperative_scheduler.update(dt)
        self._motion_tweens.update(dt)
        if self._motion_timeline is not None:
            self._motion_timeline.update(dt)
        if self.active_tab_key == "validation":
            self._form_validator.update(dt)
            self._refresh_validation_labels()
        elif self.active_tab_key == "infrastructure":
            self._refresh_infrastructure_labels()
        elif self.active_tab_key == "scheduling":
            self._refresh_scheduling_labels()
        elif self.active_tab_key == "graphics":
            self._advance_graphics_demo(dt)
        elif self.active_tab_key == "text":
            self._refresh_text_labels()

    def set_active_tab(self, key: str) -> None:
        next_key = str(key)
        self.active_tab_key = next_key
        for tab_key, panel in self._tab_panels.items():
            is_active = tab_key == next_key
            panel.visible = is_active
            panel.enabled = is_active
        if next_key == "data":
            self._refresh_backlog_view()
        elif next_key == "validation":
            self._refresh_validation_labels()
        elif next_key == "history":
            self._refresh_history_labels()
        elif next_key == "theme":
            self._refresh_theme_labels()
        elif next_key == "state":
            self._refresh_state_labels()
        elif next_key == "infrastructure":
            self._refresh_infrastructure_labels()
        elif next_key == "scheduling":
            self._refresh_scheduling_labels()
        elif next_key == "motion":
            self._refresh_motion_labels()
        elif next_key == "persistence":
            self._refresh_persistence_labels()
        elif next_key == "graphics":
            self._refresh_graphics_labels()
        elif next_key == "text":
            self._refresh_text_labels()

    def _row_bounds(
        self,
        rect: Rect,
        top: int,
        *,
        left: int | None = None,
        width: int | None = None,
        height: int | None = None,
    ) -> Rect:
        return row_bounds(self, rect, top, left=left, width=width, height=height)

    def _place_row_controls(self, panel: PanelControl, row_bounds: Rect, controls: list[object]) -> None:
        place_row_controls(self, panel, row_bounds, controls)

    def _place_vertical_grid_sequence(
        self,
        panel: PanelControl,
        bounds: Rect,
        items: list[tuple[object, int, int]],
        *,
        stretch_width: bool = True,
    ) -> None:
        place_vertical_grid_sequence(self, panel, bounds, items, stretch_width=stretch_width)

    def _place_vertical_label_stack(
        self,
        panel: PanelControl,
        bounds: Rect,
        labels: list[LabelControl],
        *,
        gap: int = 8,
    ) -> None:
        place_vertical_label_stack(self, panel, bounds, labels, gap=gap)

    def _place_compact_labeled_row(
        self,
        panel: PanelControl,
        *,
        left: int = 0,
        top: int,
        label: LabelControl,
        field: object,
        label_width: int = 120,
        gap: int = 10,
    ) -> None:
        place_compact_labeled_row(
            self,
            panel,
            left=left,
            top=top,
            label=label,
            field=field,
            label_width=label_width,
            gap=gap,
        )

    def _place_graphics_particle_layer(
        self,
        panel: PanelControl,
        *,
        left: int,
        top: int,
        width: int,
        height: int,
    ) -> None:
        place_graphics_particle_layer(
            self,
            panel,
            left=left,
            top=top,
            width=width,
            height=height,
        )

    def _sync_graphics_emitter_offsets(
        self,
        *,
        panel_rect: Rect,
        left_col_x: int,
        left_col_width: int,
        labels_top: int,
    ) -> None:
        sync_graphics_emitter_offsets(
            self,
            panel_rect=panel_rect,
            left_col_x=left_col_x,
            left_col_width=left_col_width,
            labels_top=labels_top,
        )

    def _place_text_preview_region(
        self,
        panel: PanelControl,
        *,
        top: int,
        width: int,
        height: int,
    ) -> None:
        place_text_preview_region(self, panel, top=top, width=width, height=height)

    def _add_button_rows(
        self,
        panel: PanelControl,
        rect: Rect,
        top: int,
        buttons: list[ButtonControl],
        *,
        per_row: int = 2,
        left: int | None = None,
        width: int | None = None,
    ) -> int:
        current_top = int(top)
        row_size = max(1, int(per_row))
        for start in range(0, len(buttons), row_size):
            row_bounds = self._row_bounds(rect, current_top, left=left, width=width)
            self._place_row_controls(panel, row_bounds, buttons[start:start + row_size])
            current_top = row_bounds.bottom + self.BUTTON_ROW_SPACING
        return current_top

    def _add_single_column_button_row(
        self,
        panel: PanelControl,
        rect: Rect,
        top: int,
        button: ButtonControl,
        *,
        column_index: int = 0,
        span_both_columns: bool = False,
        span_from_window_left: bool = False,
        left: int | None = None,
        width: int | None = None,
    ) -> int:
        row_bounds = self._row_bounds(rect, top, left=left, width=width)
        if span_both_columns:
            inset_x = self.LEFT_SIDE_INSET_X
            start_x = inset_x if span_from_window_left else row_bounds.left + inset_x
            button_width = max(1, row_bounds.right - start_x)
            button.rect = Rect(0, 0, button_width, row_bounds.height)
            panel.add_at(button, start_x, row_bounds.top)
            return row_bounds.bottom + self.BUTTON_ROW_SPACING
        normalized_index = max(0, min(1, int(column_index)))
        grid = GridLayout(
            row_tracks=[row_bounds.height],
            col_tracks=["1fr", "1fr"],
            gap=self.BUTTON_ROW_GAP,
            padding=0,
        )
        button.rect = Rect(0, 0, max(1, row_bounds.width // 2), row_bounds.height)
        grid.place(button, GridPlacement(row=0, col=normalized_index))
        grid.apply(row_bounds)
        panel.add_at(button, button.rect.left, button.rect.top)
        return row_bounds.bottom + self.BUTTON_ROW_SPACING

    def build_data_panel(self, rect: Rect) -> PanelControl:
        return build_data_panel_helper(self, rect)

    def build_validation_panel(self, rect: Rect) -> PanelControl:
        return build_validation_panel_helper(self, rect)

    def build_history_panel(self, rect: Rect) -> PanelControl:
        return build_history_panel_helper(self, rect)

    def build_theme_panel(self, rect: Rect) -> PanelControl:
        return build_theme_panel_helper(self, rect)

    def build_state_panel(self, rect: Rect) -> PanelControl:
        return build_state_panel_helper(self, rect)

    def build_infrastructure_panel(self, rect: Rect) -> PanelControl:
        return build_infrastructure_panel_helper(self, rect)

    def build_scheduling_panel(self, rect: Rect) -> PanelControl:
        return build_scheduling_panel_helper(self, rect)

    def build_motion_panel(self, rect: Rect) -> PanelControl:
        return build_motion_panel_helper(self, rect)

    def build_persistence_panel(self, rect: Rect) -> PanelControl:
        return build_persistence_panel_helper(self, rect)

    def build_graphics_panel(self, rect: Rect) -> PanelControl:
        return build_graphics_panel_helper(self, rect)

    def build_text_panel(self, rect: Rect) -> PanelControl:
        return build_text_panel_helper(self, rect)

    def _make_window_spec(self, host) -> AnchoredWindowSpec:
        width = max(640, int(host.screen_rect.width * 0.8))
        height = max(420, int(host.screen_rect.height * 0.8))
        return AnchoredWindowSpec(
            control_id="systems_window",
            title="Systems",
            size=(width, height),
            anchor="center",
            margin=(0, 0),
            use_frame_backdrop=True,
        )

    def _rebuild_text_document(self) -> None:
        rebuild_text_document_helper(self)

    def _rebuild_text_searcher(self) -> None:
        rebuild_text_searcher_helper(self)

    def _on_text_locale_changed(self, value: str) -> None:
        on_text_locale_changed_helper(self, value)

    def _on_text_query_changed(self, value: str) -> None:
        on_text_query_changed_helper(self, value)

    def _run_text_search(self) -> None:
        run_text_search_helper(self)

    def _toggle_text_case_sensitive(self) -> None:
        toggle_text_case_sensitive_helper(self)

    def _toggle_text_whole_word(self) -> None:
        toggle_text_whole_word_helper(self)

    def _toggle_text_regex(self) -> None:
        toggle_text_regex_helper(self)

    def _apply_text_regex_preset(self) -> None:
        apply_text_regex_preset_helper(self)

    def _apply_text_locale_regex_preset(self) -> None:
        apply_text_locale_regex_preset_helper(self)

    def _next_text_match(self) -> None:
        next_text_match_helper(self)

    def _replace_first_text_match(self) -> None:
        replace_first_text_match_helper(self)

    def _build_text_preview_spans(self, text: str, matches: list[object], active_index: int) -> list[TextSpan]:
        return build_text_preview_spans_helper(self, text, matches, active_index)

    def _render_text_preview_fallback(self, surface: Surface, text: str) -> None:
        render_text_preview_fallback_helper(self, surface, text)

    def _render_text_preview(self, matches: list[object], active_index: int) -> None:
        render_text_preview_helper(self, matches, active_index)

    def _refresh_text_labels(self) -> None:
        refresh_text_labels_helper(self)

    def _project_backlog_item(self, item: _BacklogItem) -> ListItem:
        return project_backlog_item_helper(self, item)

    def _selected_backlog_filter(self) -> str:
        return selected_backlog_filter_helper(self)

    def _refresh_backlog_view(self) -> None:
        refresh_backlog_view_helper(self)

    def _on_backlog_filter_changed(self, value: str) -> None:
        on_backlog_filter_changed_helper(self, value)

    def _on_backlog_view_refreshed(self) -> None:
        on_backlog_view_refreshed_helper(self)

    def _on_backlog_selected(self, _index: int, item: ListItem) -> None:
        on_backlog_selected_helper(self, _index, item)

    def _cache_payload_for_backlog_item(self, item: _BacklogItem) -> str:
        return cache_payload_for_backlog_item_helper(self, item)

    def _refresh_backlog_labels(self) -> None:
        refresh_backlog_labels_helper(self)

    def _add_backlog_item(self) -> None:
        add_backlog_item_helper(self)

    def _clear_backlog_cache(self) -> None:
        clear_backlog_cache_helper(self)

    def _check_pipeline_name(self, value: object) -> str | None:
        return check_pipeline_name_helper(self, value)

    def _on_deployment_name_changed(self, value: str) -> None:
        on_deployment_name_changed_helper(self, value)

    def _on_environment_changed(self, value: str) -> None:
        on_environment_changed_helper(self, value)

    def _run_local_validation_checks(self) -> None:
        run_local_validation_checks_helper(self)

    def _apply_suggested_name(self) -> None:
        apply_suggested_name_helper(self)

    def _refresh_validation_labels(self) -> None:
        refresh_validation_labels_helper(self)

    def _advance_history_stage(self) -> None:
        advance_history_stage_helper(self)

    def _batch_promote_history_stage(self) -> None:
        batch_promote_history_stage_helper(self)

    def _undo_history_stage(self) -> None:
        undo_history_stage_helper(self)

    def _redo_history_stage(self) -> None:
        redo_history_stage_helper(self)

    def _refresh_history_labels(self) -> None:
        refresh_history_labels_helper(self)

    def _on_theme_changed(self, value: str) -> None:
        on_theme_changed_helper(self, value)

    def _toggle_review_scope(self) -> None:
        toggle_review_scope_helper(self)

    def _refresh_theme_labels(self) -> None:
        refresh_theme_labels_helper(self)

    def _on_state_context_changed(self, value: str) -> None:
        on_state_context_changed_helper(self, value)

    def _approve_release_item(self) -> None:
        approve_release_item_helper(self)

    def _add_release_blocker(self) -> None:
        add_release_blocker_helper(self)

    def _advance_active_context(self) -> None:
        advance_active_context_helper(self)

    def _undo_active_context(self) -> None:
        undo_active_context_helper(self)

    def _redo_active_context(self) -> None:
        redo_active_context_helper(self)

    def _advance_release_state_machine(self) -> None:
        advance_release_state_machine_helper(self)

    def _cycle_release_router(self) -> None:
        cycle_release_router_helper(self)

    def _refresh_state_labels(self) -> None:
        refresh_state_labels_helper(self)

    def _build_runtime_spec(self, _host) -> RoutedRuntimeSpec:
        return RoutedRuntimeSpec(
            scene_name="main",
            execution_context_spec=ExecutionContextSpec(
                enabled=True,
                default_priority=2,
                default_deadline_updates=2,
                propagate_cancellation=True,
            ),
            execution_context_attr_name="runtime_execution_context",
            budget_spec=WorkloadBudgetSpec(
                classes=(
                    WorkloadBudgetClassSpec(name="event_pipeline", max_units_per_update=4, reserve_units=1),
                    WorkloadBudgetClassSpec(name="workflow", max_units_per_update=3, reserve_units=1),
                    WorkloadBudgetClassSpec(name="durable_queue", max_units_per_update=2, reserve_units=1),
                    WorkloadBudgetClassSpec(name="saga", max_units_per_update=2, reserve_units=1),
                    WorkloadBudgetClassSpec(name="reactive_graph", max_units_per_update=2, reserve_units=1),
                ),
                default_max_units_per_update=2,
            ),
            budget_attr_name="runtime_budget",
            checkpoint_spec=CheckpointSpec(
                enabled=True,
                interval_updates=180,
                max_snapshots=6,
                domains=(
                    CheckpointDomainSpec(
                        name="release_store",
                        capture=lambda _feature: dict(self._release_store.snapshot()),
                        restore=lambda payload, _feature: self._release_store.dispatch(dict(payload or {})),
                    ),
                    CheckpointDomainSpec(
                        name="runtime_contract",
                        capture=lambda _feature: {
                            "version": self._runtime_contract_payload_version,
                            "payload": dict(self._runtime_contract_payload),
                        },
                        restore=lambda payload, _feature: self._restore_runtime_contract_checkpoint(payload),
                    ),
                ),
            ),
            checkpoint_attr_name="runtime_checkpoint",
            saga_specs=(
                SagaSpec(
                    name="systems_release_rollout",
                    steps=(
                        SagaStepSpec(
                            name="stage_profile",
                            handler=lambda payload, _feature, _run: self._runtime_saga_stage_profile(payload),
                            compensate=lambda payload, _feature, _run: self._runtime_saga_compensate(payload),
                        ),
                        SagaStepSpec(
                            name="save_workspace",
                            handler=lambda payload, _feature, _run: self._runtime_saga_stage_save_workspace(payload),
                            compensate=lambda payload, _feature, _run: self._runtime_saga_compensate(payload),
                        ),
                    ),
                ),
            ),
            saga_attr_name="runtime_saga",
            reactive_graph_spec=ReactiveGraphSpec(
                sources=(
                    ReactiveSourceSpec(
                        name="release_readiness_source",
                        subscribe=lambda callback, *_args: self._release_readiness.subscribe(lambda value: callback(value)),
                        invalidates=("runtime_release_projection",),
                    ),
                ),
                nodes=(
                    ReactiveNodeSpec(
                        name="runtime_release_projection",
                        compute=lambda _feature, _runtime: int(getattr(self._release_readiness, "value", 0)),
                        target_attr_name="_runtime_reactive_release_score",
                    ),
                ),
                max_nodes_per_update=1,
            ),
            reactive_graph_attr_name="runtime_reactive_graph",
            migration_spec=ContractMigrationSpec(
                steps=(
                    MigrationStepSpec(
                        contract="systems_runtime_contract",
                        from_version="1.0",
                        to_version="2.0",
                        migrate=lambda payload, _feature: {
                            "queue_depth": int(dict(payload or {}).get("queue_depth", 0)),
                            "profile": str(dict(payload or {}).get("profile", "review")),
                            "region": str(dict(payload or {}).get("region", "us-central")),
                            "migrated": True,
                        },
                    ),
                ),
                targets=(
                    MigrationTargetSpec(
                        name="systems_runtime_contract_payload",
                        contract="systems_runtime_contract",
                        version_attr="_runtime_contract_payload_version",
                        payload_attr="_runtime_contract_payload",
                        target_version="2.0",
                    ),
                ),
                strict=True,
            ),
            migration_attr_name="runtime_migration",
            policy_specs=(
                RuntimePolicySpec(name="systems_allow_workflow", target="workflow", action="allow", priority=5),
                RuntimePolicySpec(name="systems_limit_pipeline", target="event_pipeline", action="limit", max_units=1, priority=4),
                RuntimePolicySpec(name="systems_allow_projection", target="projection", action="allow", priority=3),
                RuntimePolicySpec(name="systems_allow_queue", target="durable_queue", action="allow", priority=2),
            ),
            policy_attr_name="runtime_policy",
            effect_bindings=(
                EffectBindingSpec(
                    name="release_readiness_effect",
                    group="state",
                    factory=lambda: self._release_readiness.subscribe(lambda _value: self._refresh_state_labels()),
                ),
            ),
            effects_attr_name="runtime_effects",
            event_pipelines=(
                EventPipelineSpec(
                    name=_SYSTEMS_EVENT_PIPELINE_FAILURES,
                    handler=lambda payload, *_args: self._on_runtime_failure_pipeline(payload),
                    stages=(
                        EventPipelineStageSpec(kind="filter", predicate=lambda payload: isinstance(payload, dict)),
                        EventPipelineStageSpec(kind="map", mapper=lambda payload: dict(payload)),
                    ),
                ),
                EventPipelineSpec(
                    name=_SYSTEMS_EVENT_PIPELINE_BURST,
                    handler=lambda payload, *_args: self._on_burst_pipeline(payload),
                    stages=(
                        EventPipelineStageSpec(kind="filter", predicate=lambda payload: isinstance(payload, int)),
                        EventPipelineStageSpec(kind="throttle", interval_updates=1),
                        EventPipelineStageSpec(kind="window", window_size=3),
                    ),
                ),
            ),
            event_pipeline_attr_name="runtime_event_pipelines",
            durable_queue_spec=DurableOperationQueueSpec(
                queue_name="systems_operations",
                max_inflight=1,
                bindings=(
                    DurableOperationBindingSpec(queue_operation=_SYSTEMS_OP_APPLY_REVIEW_PROFILE, operation_name=_SYSTEMS_OP_APPLY_REVIEW_PROFILE),
                    DurableOperationBindingSpec(queue_operation=_SYSTEMS_OP_APPLY_PRODUCTION_PROFILE, operation_name=_SYSTEMS_OP_APPLY_PRODUCTION_PROFILE),
                    DurableOperationBindingSpec(queue_operation=_SYSTEMS_OP_SAVE_WORKSPACE, operation_name=_SYSTEMS_OP_SAVE_WORKSPACE),
                    DurableOperationBindingSpec(queue_operation=_SYSTEMS_OP_RESTORE_WORKSPACE, operation_name=_SYSTEMS_OP_RESTORE_WORKSPACE),
                    DurableOperationBindingSpec(queue_operation=_SYSTEMS_OP_SNAPSHOT_MIGRATION, operation_name=_SYSTEMS_OP_SNAPSHOT_MIGRATION),
                ),
            ),
            durable_queue_attr_name="runtime_durable_queue",
            capability_providers=(
                CapabilityProviderSpec(
                    capability="release_store",
                    version="1.0",
                    value_factory=lambda: self._release_store,
                ),
            ),
            capability_requirements=(
                CapabilityRequirementSpec(
                    capability="release_store",
                    min_version="1.0",
                    optional=False,
                    attr_name="state_store",
                ),
            ),
            capability_attr_name="runtime_capabilities",
            projection_spec=ProjectionSpec(
                nodes=(
                    ProjectionNodeSpec(
                        name="release_readiness_score",
                        compute=lambda: int(getattr(self._release_readiness, "value", 0)),
                        target_attr_name="_projected_release_score",
                    ),
                ),
                max_nodes_per_update=1,
            ),
            projection_attr_name="runtime_projection",
            service_bindings=(
                ServiceBindingSpec(
                    attr_name="state_store",
                    key=self._service_key_release_store,
                    factory=lambda _feature, _runtime_host, _runtime_scope: self._release_store,
                    owned=False,
                ),
            ),
            store_subscriptions=(
                StoreSubscriptionSpec(
                    state_key="status",
                    handler=lambda _value: self._refresh_state_labels(),
                    store_attr_name="state_store",
                    invoke_immediately=True,
                ),
            ),
            observable_effects=(
                ObservableEffectSpec(
                    handler=lambda _value: self._refresh_state_labels(),
                    observable_attr_name="_release_readiness",
                    invoke_immediately=True,
                ),
            ),
            operation_bus_attr_name="operation_bus",
            failure_policies=(
                FailurePolicySpec(
                    name=_SYSTEMS_PERSISTENCE_POLICY,
                    retries=1,
                    retry_delay_seconds=0.05,
                    timeout_seconds=0.75,
                    publish_topic=_SYSTEMS_FAILURE_TOPIC,
                    publish_scope=self.name,
                ),
            ),
            operations=(
                FeatureOperationSpec(name=_SYSTEMS_OP_APPLY_REVIEW_PROFILE, handler=lambda _payload: apply_review_profile_helper(self)),
                FeatureOperationSpec(name=_SYSTEMS_OP_APPLY_PRODUCTION_PROFILE, handler=lambda _payload: apply_production_profile_helper(self)),
                FeatureOperationSpec(name=_SYSTEMS_OP_SAVE_WORKSPACE, handler=lambda _payload: save_workspace_state_helper(self), failure_policy=_SYSTEMS_PERSISTENCE_POLICY),
                FeatureOperationSpec(name=_SYSTEMS_OP_RESTORE_WORKSPACE, handler=lambda _payload: restore_workspace_state_helper(self), failure_policy=_SYSTEMS_PERSISTENCE_POLICY),
                FeatureOperationSpec(name=_SYSTEMS_OP_SNAPSHOT_MIGRATION, handler=lambda _payload: run_snapshot_migration_helper(self), failure_policy=_SYSTEMS_PERSISTENCE_POLICY),
            ),
            event_subscriptions=(
                EventSubscriptionSpec(
                    attr_name="_runtime_operation_failure_subscription",
                    topic=_SYSTEMS_FAILURE_TOPIC,
                    handler=lambda payload: self._on_runtime_operation_failed(payload),
                    scope=self.name,
                ),
            ),
        )

    def _restore_runtime_contract_checkpoint(self, payload: dict | None) -> None:
        data = dict(payload or {})
        self._runtime_contract_payload_version = str(data.get("version", self._runtime_contract_payload_version))
        payload_data = data.get("payload")
        if isinstance(payload_data, dict):
            self._runtime_contract_payload = dict(payload_data)

    def _runtime_saga_stage_profile(self, payload: dict | None) -> dict:
        self._runtime_saga_status = "Runtime saga stage_profile: applying review profile"
        apply_review_profile_helper(self)
        return dict(payload or {})

    def _runtime_saga_stage_save_workspace(self, payload: dict | None):
        self._runtime_saga_status = "Runtime saga stage_save_workspace: dispatching save workspace operation"
        if self.operation_bus is not None:
            return self.operation_bus.call(_SYSTEMS_OP_SAVE_WORKSPACE)
        save_workspace_state_helper(self)
        return dict(payload or {})

    def _runtime_saga_compensate(self, _payload: dict | None) -> None:
        self._runtime_saga_status = "Runtime saga compensation: reverting to review profile"
        apply_review_profile_helper(self)

    def _dispatch_runtime_operation(self, operation_name: str) -> bool:
        if self.runtime_durable_queue is not None:
            try:
                self.runtime_durable_queue.enqueue(str(operation_name), {"source": "systems_feature"})
                return True
            except KeyError:
                pass
        if self.operation_bus is None:
            return False
        self.operation_bus.call(operation_name)
        return True

    def _publish_pipeline_event(self, pipeline_name: str, payload: object) -> None:
        pipeline = self.runtime_event_pipelines
        if pipeline is None:
            return
        try:
            pipeline.publish(str(pipeline_name), payload)
        except Exception:
            return

    def _on_runtime_failure_pipeline(self, payload) -> None:
        if not isinstance(payload, dict):
            return
        operation_name = str(payload.get("operation_name", "operation"))
        self._persistence_last_status = f"Failure pipeline observed: {operation_name}"
        if self.active_tab_key == "persistence":
            self._refresh_persistence_labels()

    def _on_burst_pipeline(self, payload) -> None:
        if not isinstance(payload, (tuple, list)):
            return
        self._scheduling_last_action = f"Burst pipeline window: {len(payload)} samples"
        if self.active_tab_key == "scheduling":
            self._refresh_scheduling_labels()

    def _on_runtime_operation_failed(self, payload) -> None:
        if not isinstance(payload, dict):
            return
        self._publish_pipeline_event(_SYSTEMS_EVENT_PIPELINE_FAILURES, payload)
        operation_name = str(payload.get("operation_name", "operation"))
        error_text = str(payload.get("error", "unknown error"))
        self._persistence_last_status = f"Runtime operation failed: {operation_name} -> {error_text}"
        if self.active_tab_key == "persistence":
            self._refresh_persistence_labels()

    def _queue_background_job(self) -> None:
        queue_background_job_helper(self)

    def _build_artifact_job(self, task_id: str, payload: dict[str, object]) -> str:
        return build_artifact_job_helper(self, task_id, payload)

    def _start_rollout_sequence(self) -> None:
        start_rollout_sequence_helper(self)

    def _refresh_scheduling_labels(self) -> None:
        refresh_scheduling_labels_helper(self)

    def _refresh_motion_labels(self) -> None:
        refresh_motion_labels_helper(self)

    def _play_motion_timeline(self) -> None:
        play_motion_timeline_helper(self)

    def _set_motion_timeline_stage(self, stage: str) -> None:
        set_motion_timeline_stage_helper(self, stage)

    def _run_motion_tween(self) -> None:
        run_motion_tween_helper(self)

    def _run_motion_sequence(self) -> None:
        run_motion_sequence_helper(self)

    def _toggle_motion_transition(self) -> None:
        toggle_motion_transition_helper(self)

    def _on_motion_animation_state_changed(self, state_name: str) -> None:
        on_motion_animation_state_changed_helper(self, state_name)

    def _cycle_motion_animation_state(self) -> None:
        cycle_motion_animation_state_helper(self)

    def _set_motion_sequence_stage(self, stage: str) -> None:
        set_motion_sequence_stage_helper(self, stage)

    def _start_timer_probe(self) -> None:
        start_timer_probe_helper(self)

    def _simulate_rate_limited_input(self) -> None:
        simulate_rate_limited_input_helper(self)

    def _on_throttled_burst_input(self, value: int) -> None:
        self._publish_pipeline_event(_SYSTEMS_EVENT_PIPELINE_BURST, int(value))
        on_throttled_burst_input_helper(self, value)

    def _on_debounced_burst_commit(self, value: str) -> None:
        self._publish_pipeline_event(_SYSTEMS_EVENT_PIPELINE_BURST, len(str(value)))
        on_debounced_burst_commit_helper(self, value)

    def _on_timer_probe_tick(self) -> None:
        on_timer_probe_tick_helper(self)

    def _on_timer_probe_complete(self) -> None:
        on_timer_probe_complete_helper(self)

    def _apply_review_profile(self) -> None:
        if self._dispatch_runtime_operation(_SYSTEMS_OP_APPLY_REVIEW_PROFILE):
            return
        apply_review_profile_helper(self)

    def _apply_production_profile(self) -> None:
        if self._dispatch_runtime_operation(_SYSTEMS_OP_APPLY_PRODUCTION_PROFILE):
            return
        apply_production_profile_helper(self)

    def _build_workspace_state(self) -> WorkspaceState:
        return build_workspace_state_helper(self)

    def _save_workspace_state(self) -> None:
        if self._dispatch_runtime_operation(_SYSTEMS_OP_SAVE_WORKSPACE):
            return
        save_workspace_state_helper(self)

    def _restore_workspace_state(self) -> None:
        if self._dispatch_runtime_operation(_SYSTEMS_OP_RESTORE_WORKSPACE):
            return
        restore_workspace_state_helper(self)

    def _refresh_persistence_labels(self) -> None:
        refresh_persistence_labels_helper(self)

    def _trigger_particle_burst(self) -> None:
        trigger_particle_burst_helper(self)

    def _build_surface_effect_source(self, size: tuple[int, int]) -> Surface:
        return build_surface_effect_source_helper(self, size)

    def _cycle_surface_effect(self) -> None:
        cycle_surface_effect_helper(self)

    def _refresh_surface_effect_preview(self) -> None:
        refresh_surface_effect_preview_helper(self)

    def _reset_particle_layer(self) -> None:
        reset_particle_layer_helper(self)

    def _advance_graphics_runtime(self) -> None:
        advance_graphics_runtime_helper(self)

    def _pan_tile_camera(self, dx: int, dy: int, *, refresh: bool = True) -> None:
        pan_tile_camera_helper(self, dx, dy, refresh=refresh)

    def _advance_graphics_demo(self, dt: float) -> None:
        advance_graphics_demo_helper(self, dt)

    def _render_tile_map_preview(self) -> None:
        render_tile_map_preview_helper(self)

    def _refresh_graphics_labels(self) -> None:
        refresh_graphics_labels_helper(self)

    def _run_pipeline_demo(self) -> None:
        run_pipeline_demo_helper(self)

    def _advance_interaction_state(self) -> None:
        advance_interaction_state_helper(self)

    def _toggle_schema_example(self) -> None:
        toggle_schema_example_helper(self)

    def _run_snapshot_migration(self) -> None:
        if self._dispatch_runtime_operation(_SYSTEMS_OP_SNAPSHOT_MIGRATION):
            return
        run_snapshot_migration_helper(self)

    def _run_runtime_checkpoint(self) -> None:
        run_runtime_checkpoint_helper(self)

    def _run_runtime_saga(self) -> None:
        run_runtime_saga_helper(self)

    def _apply_runtime_contract_migration(self) -> None:
        apply_runtime_contract_migration_helper(self)

    def _record_theme_invalidation(self) -> None:
        record_theme_invalidation_helper(self)

    def _trigger_theme_invalidation(self) -> None:
        trigger_theme_invalidation_helper(self)

    def _bind_virtual_cell(self, cell: _VirtualCell, index: int) -> None:
        bind_virtual_cell_helper(self, cell, index)

    def _refresh_virtualization_demo(self) -> None:
        refresh_virtualization_demo_helper(self)

    def _solve_constraint_layout(self) -> None:
        solve_constraint_layout_helper(self)

    def _push_scope_demo(self) -> None:
        push_scope_demo_helper(self)

    def _run_accessibility_demo(self) -> None:
        run_accessibility_demo_helper(self)

    def _run_audio_demo(self) -> None:
        run_audio_demo_helper(self)

    def _sample_telemetry(self) -> None:
        sample_telemetry_helper(self)

    def _refresh_infrastructure_labels(self) -> None:
        refresh_infrastructure_labels_helper(self)
