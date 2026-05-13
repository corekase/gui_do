"""Systems demo window integrated into the gui_do main scene."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tempfile

import pygame
from pygame import Rect, Surface

from gui_do import (
    AccessibilityBus,
    AccessibilityNode,
    AccessibilityRole,
    AccessibilityTree,
    AppStateStore,
    AnchoredWindowSpec,
    AnimationSequence,
    AnimationStateMachine,
    AnimationTransitionMode,
    AsyncFieldValidator,
    AsyncFormValidator,
    ArrowBoxControl,
    ButtonControl,
    Camera2D,
    CanvasControl,
    CollectionView,
    CollectionViewQuery,
    CommandHistory,
    CooperativeScheduler,
    Debouncer,
    DataCache,
    DataflowPipeline,
    DirtyRegionTracker,
    DropdownControl,
    DropdownOption,
    Emitter,
    FieldGraphSchema,
    FieldSchema,
    Feature,
    FlexLayout,
    FormField,
    FrameTimer,
    GridLayout,
    GridPlacement,
    InteractionContext,
    InteractionStateMachine,
    LabelControl,
    ListViewControl,
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
    ScopedThemeManager,
    SoundBankRegistry,
    SoundCue,
    SoundEventBus,
    ServiceKey,
    SettingsRegistry,
    Sleep,
    SnapshotMigrator,
    StateMachine,
    StateTransaction,
    SurfaceEffects,
    SurfaceCompositor,
    TabControl,
    TabItem,
    TaskScheduler,
    Throttler,
    TextInputControl,
    TextFlow,
    TextSearcher,
    TextSpan,
    ThemeManager,
    ThemeInvalidationBus,
    LivePoliteness,
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
    make_snapshot,
    TransitionEvent,
    TransitionManager,
    TransitionSpec,
    TweenManager,
)
from gui_do.layout.constraint_layout import AnchorConstraint
from gui_do.controls.chrome.window_presenter import WindowPresenter
from gui_do.controls.data.list_view_control import ListItem


@dataclass(frozen=True)
class _BacklogItem:
    title: str
    status: str
    priority: int
    owner: str


class _StatusChangeCommand:
    def __init__(self, feature: "SystemsFeature", new_index: int, description: str) -> None:
        self._feature = feature
        self._new_index = int(new_index)
        self._old_index = int(feature._history_stage_index)
        self._description = str(description)

    @property
    def description(self) -> str:
        return self._description

    def execute(self) -> None:
        self._feature._history_stage_index = self._new_index
        self._feature._refresh_history_labels()

    def undo(self) -> None:
        self._feature._history_stage_index = self._old_index
        self._feature._refresh_history_labels()


class _SetIndexCommand:
    def __init__(self, feature: "SystemsFeature", attr_name: str, new_index: int, description: str) -> None:
        self._feature = feature
        self._attr_name = str(attr_name)
        self._new_index = int(new_index)
        self._old_index = int(getattr(feature, attr_name))
        self._description = str(description)

    @property
    def description(self) -> str:
        return self._description

    def execute(self) -> None:
        setattr(self._feature, self._attr_name, self._new_index)
        self._feature._refresh_state_labels()

    def undo(self) -> None:
        setattr(self._feature, self._attr_name, self._old_index)
        self._feature._refresh_state_labels()


@dataclass
class _VirtualCell:
    index: int = -1


class _SystemsPresenter(WindowPresenter):
    def __init__(self, feature: "SystemsFeature", host) -> None:
        super().__init__(None)
        self.feature = feature
        self.host = host

    def on_create(self) -> None:
        feature = self.feature
        content_rect = self.window.content_rect()
        tab_height = 36
        tab_gap = 8
        tabs = TabControl(
            "systems_tabs",
            Rect(content_rect.left, content_rect.top, content_rect.width, tab_height),
            items=[TabItem(key, label) for key, label in feature.TAB_DEFINITIONS],
            selected_key=feature.active_tab_key,
            on_change=feature.set_active_tab,
            horizontal_padding=2,
        )
        tabs.set_accessibility(role="tablist", label="Systems demo categories")
        self.add_control(tabs)
        feature.systems_tabs = tabs

        panel_rect = Rect(
            content_rect.left,
            content_rect.top + tab_height + tab_gap,
            content_rect.width,
            max(1, content_rect.height - tab_height - tab_gap),
        )
        panel_builders = [
            feature.build_data_panel,
            feature.build_validation_panel,
            feature.build_history_panel,
            feature.build_theme_panel,
            feature.build_state_panel,
            feature.build_infrastructure_panel,
            feature.build_scheduling_panel,
            feature.build_motion_panel,
            feature.build_persistence_panel,
            feature.build_graphics_panel,
            feature.build_text_panel,
        ]
        panel_keys = [
            "data", "validation", "history", "theme", "state", "infrastructure", "scheduling", "motion", "persistence", "graphics", "text",
        ]
        panels = [builder(panel_rect) for builder in panel_builders]
        for panel in panels:
            self.add_control(panel)

        feature._tab_panels = dict(zip(panel_keys, panels))
        feature.window = self.window
        feature.demo = self.host
        feature.set_active_tab(feature.active_tab_key)
        self.window.visible = False


class SystemsFeature(Feature):
    """Tabbed main-scene systems window with practical demo integrations."""

    TAB_DEFINITIONS = (
        ("data", "Data"),
        ("validation", "Validation"),
        ("history", "History"),
        ("theme", "Theme"),
        ("state", "State"),
        ("infrastructure", "Infrastructure"),
        ("scheduling", "Scheduling"),
        ("motion", "Motion"),
        ("persistence", "Persistence"),
        ("graphics", "Graphics"),
        ("text", "Text"),
    )
    PANEL_PADDING_X = 16
    LEFT_SIDE_INSET_X = 10
    LABEL_INSET_X = 10
    BUTTON_ROW_HEIGHT = 32
    BUTTON_ROW_GAP = 12
    BUTTON_ROW_SPACING = 12

    HOST_REQUIREMENTS = {
        "build": ("app", "root", "screen_rect"),
        "on_update": ("app",),
    }

    def __init__(self) -> None:
        super().__init__("systems_demo", scene_name="main")
        self._frame_timer = FrameTimer()
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
        self._motion_animation_states = ("idle", "hover", "press")
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
        self._surface_effect_cycle = ("blur", "greyscale", "tint", "brightness", "vignette", "pixelate")
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
        self._history_stages = (
            "Draft",
            "Ready for Review",
            "Approved",
            "Shipped",
        )
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
        self.infrastructure_runtime_label = None

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
        row_left = self.PANEL_PADDING_X if left is None else int(left)
        row_height = self.BUTTON_ROW_HEIGHT if height is None else max(1, int(height))
        if width is None:
            right_padding = self.PANEL_PADDING_X if left is None else self.PANEL_PADDING_X
            row_width = rect.width - row_left - right_padding
        else:
            row_width = int(width)
        return Rect(row_left, int(top), max(1, row_width), row_height)

    def _place_row_controls(self, panel: PanelControl, row_bounds: Rect, controls: list[object]) -> None:
        if not controls:
            return
        layout = FlexLayout(direction="row", gap=self.BUTTON_ROW_GAP, padding=0)
        for control in controls:
            control.rect = Rect(0, 0, max(1, row_bounds.width), row_bounds.height)
            layout.add(control, grow=1)
        layout.apply(row_bounds)
        for control in controls:
            panel.add_at(control, control.rect.left, control.rect.top)

    def _place_vertical_grid_sequence(
        self,
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

    def _place_vertical_label_stack(
        self,
        panel: PanelControl,
        bounds: Rect,
        labels: list[LabelControl],
        *,
        gap: int = 8,
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
        """Place a fixed-width label and field in a compact single row."""
        row_height = max(1, max(int(label.rect.height), int(field.rect.height)))
        left_width = max(1, int(label_width))
        col_gap = max(0, int(gap))
        field_width = max(1, int(field.rect.width))
        row_bounds = Rect(int(left), int(top), left_width + col_gap + field_width, row_height)
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
        layout.apply(row_bounds)
        panel.add_at(label, label.rect.left, label.rect.top)
        panel.add_at(field, field.rect.left, field.rect.top)

    def _place_graphics_particle_layer(
        self,
        panel: PanelControl,
        *,
        left: int,
        top: int,
        width: int,
        height: int,
    ) -> None:
        self._particle_layer.rect = Rect(0, 0, int(width), int(height))
        self._place_vertical_grid_sequence(
            panel,
            Rect(int(left), int(top), max(1, int(width)), max(1, int(height))),
            [(self._particle_layer, int(height), 0)],
        )

    def _sync_graphics_emitter_offsets(
        self,
        *,
        panel_rect: Rect,
        left_col_x: int,
        left_col_width: int,
        labels_top: int,
    ) -> None:
        # Emitters align to the horizontal midpoint of the Burst/Reset row and
        # sit just above the stacked status labels.
        burst_dx = left_col_x + left_col_width / 2
        emitter_padding = 12
        burst_dy = labels_top - emitter_padding
        self._burst_emitter_panel_offset = (burst_dx, burst_dy)
        self._ambient_emitter_panel_offset = (burst_dx, burst_dy)
        self._particle_burst_emitter.x = panel_rect.left + burst_dx
        self._particle_burst_emitter.y = panel_rect.top + burst_dy
        self._particle_ambient_emitter.x = panel_rect.left + burst_dx
        self._particle_ambient_emitter.y = panel_rect.top + burst_dy

    def _place_text_preview_region(
        self,
        panel: PanelControl,
        *,
        top: int,
        width: int,
        height: int,
    ) -> None:
        self.text_preview_canvas = CanvasControl(
            "systems_text_preview",
            Rect(0, 0, max(240, int(width)), max(1, int(height))),
            max_events=24,
        )
        self._place_vertical_grid_sequence(
            panel,
            Rect(self.PANEL_PADDING_X, int(top), max(1, int(width)), max(1, int(height))),
            [(self.text_preview_canvas, int(height), 0)],
        )

    def _inset_left_side_children(self, panel: PanelControl, *, inset_x: int | None = None) -> None:
        shift_x = self.LEFT_SIDE_INSET_X if inset_x is None else int(inset_x)
        if shift_x <= 0:
            return
        center_x = panel.rect.width // 2
        for child in panel.children:
            # Only inset controls anchored to the left side; controls that span
            # across the midpoint keep their explicit layout alignment.
            if child.rect.left < center_x and child.rect.right <= center_x:
                child.rect.x += shift_x

    def _inset_text_labels(self, panel: PanelControl, *, inset_x: int | None = None) -> None:
        shift_x = self.LABEL_INSET_X if inset_x is None else int(inset_x)
        if shift_x <= 0:
            return
        for child in panel.children:
            if isinstance(child, LabelControl):
                child.rect.x += shift_x

    def _inset_children_left_of_x(
        self,
        panel: PanelControl,
        *,
        cutoff_x: int,
        inset_x: int | None = None,
    ) -> None:
        shift_x = self.LEFT_SIDE_INSET_X if inset_x is None else int(inset_x)
        if shift_x <= 0:
            return
        cutoff = int(cutoff_x)
        for child in panel.children:
            if child.rect.left < cutoff:
                child.rect.x += shift_x

    def _force_button_left_alignment(
        self,
        panel: PanelControl,
        *,
        target_button_id: str,
        reference_button_id: str,
    ) -> None:
        by_id = {child.control_id: child for child in panel.children}
        target = by_id.get(str(target_button_id))
        reference = by_id.get(str(reference_button_id))
        if target is None or reference is None:
            return
        target.rect.x = reference.rect.left

    def _force_button_right_alignment(
        self,
        panel: PanelControl,
        *,
        target_button_id: str,
        reference_button_id: str,
    ) -> None:
        by_id = {child.control_id: child for child in panel.children}
        target = by_id.get(str(target_button_id))
        reference = by_id.get(str(reference_button_id))
        if target is None or reference is None:
            return
        target.rect.width = max(1, reference.rect.right - target.rect.left)

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
        panel = PanelControl("systems_data_panel", Rect(rect), draw_background=False)
        left_w = max(280, int(rect.width * 0.58))
        right_x = left_w + 20
        right_w = max(180, rect.width - right_x - self.PANEL_PADDING_X)
        action_button_w = 120
        action_button_gap = 8
        action_button_right_pad = 12

        filter_label = LabelControl(
            "systems_data_filter_label",
            Rect(0, 0, 72, 28),
            "Status",
            align="left",
        )
        self.data_filter_dropdown = DropdownControl(
            "systems_data_filter",
            Rect(0, 0, 180, 32),
            options=[
                DropdownOption("All", "All"),
                DropdownOption("Review", "Review"),
                DropdownOption("Ready", "Ready"),
                DropdownOption("Planned", "Planned"),
            ],
            selected_index=0,
            on_change=lambda value, _index: self._on_backlog_filter_changed(value),
        )
        self._place_compact_labeled_row(
            panel,
            top=0,
            label=filter_label,
            field=self.data_filter_dropdown,
            label_width=72,
            gap=8,
        )

        add_button = ButtonControl(
            "systems_add_review_item",
            Rect(0, 0, action_button_w, 32),
            "Queue Review",
            self._add_backlog_item,
            style="round",
        )
        cache_button = ButtonControl(
            "systems_clear_cache",
            Rect(0, 0, action_button_w, 32),
            "Clear Cache",
            self._clear_backlog_cache,
            style="round",
        )
        self._add_button_rows(
            panel,
            rect,
            0,
            [add_button, cache_button],
            per_row=2,
            left=right_x,
            width=right_w,
        )

        self.data_list = ListViewControl(
            "systems_backlog_list",
            Rect(0, 0, left_w, max(120, rect.height - 52)),
            row_height=28,
            on_select=self._on_backlog_selected,
        )
        self.data_list.set_accessibility(role="listbox", label="Deployment backlog")
        self._place_vertical_grid_sequence(
            panel,
            Rect(0, 44, max(1, left_w), max(1, self.data_list.rect.height)),
            [(self.data_list, int(self.data_list.rect.height), 0)],
        )

        self.data_summary_label = LabelControl(
            "systems_data_summary",
            Rect(0, 0, right_w, 28),
            "CollectionView keeps the release backlog filtered and sorted.",
            align="left",
        )
        self.data_cache_label = LabelControl(
            "systems_data_cache",
            Rect(0, 0, right_w, 28),
            "DataCache is ready.",
            align="left",
        )
        self.data_detail_label = LabelControl(
            "systems_data_detail",
            Rect(0, 0, right_w, 84),
            "Select a backlog item to inspect its cached deployment note.",
            align="left",
        )
        self._place_vertical_label_stack(
            panel,
            Rect(right_x, 52, max(1, right_w), 164),
            [
                self.data_summary_label,
                self.data_cache_label,
                self.data_detail_label,
            ],
            gap=8,
        )

        self._backlog_unsub = self.data_list.bind_collection_view(
            self._backlog_view,
            on_refresh=self._on_backlog_view_refreshed,
        )
        self._refresh_backlog_view()
        self._inset_children_left_of_x(panel, cutoff_x=right_x)
        return panel

    def build_validation_panel(self, rect: Rect) -> PanelControl:
        panel = PanelControl("systems_validation_panel", Rect(rect), draw_background=False)
        name_label = LabelControl("systems_validation_name_label", Rect(0, 0, 180, 28), "Pipeline Name", align="left")
        self.validation_name_input = TextInputControl(
            "systems_validation_name",
            Rect(0, 0, min(320, rect.width - 16), 32),
            value=self._deployment_name_field.value.value,
            placeholder="nightly-gui",
            on_change=self._on_deployment_name_changed,
        )
        env_label = LabelControl("systems_validation_env_label", Rect(0, 0, 180, 28), "Target Environment", align="left")
        self.validation_environment_dropdown = DropdownControl(
            "systems_validation_environment",
            Rect(0, 0, 220, 32),
            options=[
                DropdownOption("Staging", "Staging"),
                DropdownOption("QA", "QA"),
                DropdownOption("Production", "Production"),
            ],
            selected_index=0,
            on_change=lambda value, _index: self._on_environment_changed(value),
        )
        run_checks = ButtonControl(
            "systems_validation_run_checks",
            Rect(0, 0, 148, 32),
            "Run Local Checks",
            self._run_local_validation_checks,
            style="round",
        )
        suggested = ButtonControl(
            "systems_validation_use_suggested",
            Rect(0, 0, 160, 32),
            "Use Suggested Names",
            self._apply_suggested_name,
            style="round",
        )

        grid_inset_x = self.PANEL_PADDING_X
        grid_gap = 10
        grid_width = max(1, int(rect.width) - (grid_inset_x * 2))
        col_width = max(1, (grid_width - grid_gap) // 2)
        row_tracks = [28, 32, 32]
        grid_height = sum(row_tracks) + (grid_gap * (len(row_tracks) - 1))
        grid_bounds = Rect(grid_inset_x, 0, grid_width, grid_height)

        name_label.rect = Rect(0, 0, col_width, 28)
        env_label.rect = Rect(0, 0, col_width, 28)
        self.validation_name_input.rect = Rect(0, 0, max(180, min(320, col_width)), 32)
        self.validation_environment_dropdown.rect = Rect(0, 0, max(160, min(220, col_width)), 32)
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
        layout.place(self.validation_name_input, GridPlacement(row=1, col=0))
        layout.place(self.validation_environment_dropdown, GridPlacement(row=1, col=1))
        layout.place(run_checks, GridPlacement(row=2, col=0))
        layout.place(suggested, GridPlacement(row=2, col=1))
        layout.apply(grid_bounds)
        for control in (
            name_label,
            env_label,
            self.validation_name_input,
            self.validation_environment_dropdown,
            run_checks,
            suggested,
        ):
            panel.add_at(control, control.rect.left, control.rect.top)

        self.validation_state_label = LabelControl(
            "systems_validation_state",
            Rect(0, 0, grid_width, 28),
            "Form state pending.",
            align="left",
        )
        self.validation_local_label = LabelControl(
            "systems_validation_local",
            Rect(0, 0, grid_width, 28),
            "Local checks pending.",
            align="left",
        )
        self.validation_async_label = LabelControl(
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
        self._place_vertical_label_stack(
            panel,
            status_bounds,
            [
                self.validation_state_label,
                self.validation_local_label,
                self.validation_async_label,
            ],
            gap=8,
        )
        self._refresh_validation_labels()
        return panel

    def build_history_panel(self, rect: Rect) -> PanelControl:
        panel = PanelControl("systems_history_panel", Rect(rect), draw_background=False)
        advance_button = ButtonControl(
            "systems_history_advance",
            Rect(0, 0, 140, 32),
            "Advance Stage",
            self._advance_history_stage,
            style="round",
        )
        batch_button = ButtonControl(
            "systems_history_batch",
            Rect(0, 0, 160, 32),
            "Batch Promote",
            self._batch_promote_history_stage,
            style="round",
        )
        undo_button = ButtonControl(
            "systems_history_undo",
            Rect(0, 0, 96, 32),
            "Undo",
            self._undo_history_stage,
            style="round",
        )
        redo_button = ButtonControl(
            "systems_history_redo",
            Rect(0, 0, 96, 32),
            "Redo",
            self._redo_history_stage,
            style="round",
        )
        label_top = self._add_button_rows(
            panel,
            rect,
            0,
            [advance_button, batch_button, undo_button, redo_button],
            left=self.PANEL_PADDING_X + self.LEFT_SIDE_INSET_X,
            width=max(
                1,
                rect.width - (self.PANEL_PADDING_X * 2) - (self.LEFT_SIDE_INSET_X * 2),
            ),
        )

        self.history_current_label = LabelControl(
            "systems_history_current",
            Rect(0, 0, rect.width, 28),
            "",
            align="left",
        )
        self.history_undo_label = LabelControl(
            "systems_history_undo_label",
            Rect(0, 0, rect.width, 28),
            "",
            align="left",
        )
        self.history_redo_label = LabelControl(
            "systems_history_redo_label",
            Rect(0, 0, rect.width, 28),
            "",
            align="left",
        )
        self._place_vertical_label_stack(
            panel,
            Rect(self.LABEL_INSET_X, label_top + 8, max(1, rect.width - self.LABEL_INSET_X), 100),
            [
                self.history_current_label,
                self.history_undo_label,
                self.history_redo_label,
            ],
            gap=8,
        )
        self._refresh_history_labels()
        return panel

    def build_theme_panel(self, rect: Rect) -> PanelControl:
        panel = PanelControl("systems_theme_panel", Rect(rect), draw_background=False)
        theme_select_label = LabelControl(
            "systems_theme_select_label",
            Rect(0, 0, 128, 28),
            "Theme",
            align="left",
        )
        self.theme_dropdown = DropdownControl(
            "systems_theme_picker",
            Rect(0, 0, 180, 32),
            options=[
                DropdownOption("Dark", "dark"),
                DropdownOption("Light", "light"),
                DropdownOption("Sunrise", "sunrise"),
            ],
            selected_index=0,
            on_change=lambda value, _index: self._on_theme_changed(value),
        )
        toggle_scope = ButtonControl(
            "systems_theme_toggle_scope",
            Rect(0, 0, 164, 32),
            "Toggle Review Scope",
            self._toggle_review_scope,
            style="round",
        )
        self._place_vertical_grid_sequence(
            panel,
            Rect(self.LABEL_INSET_X, 0, max(1, rect.width - self.LABEL_INSET_X), 28),
            [
                (theme_select_label, 28, 0),
            ],
        )
        self._place_row_controls(
            panel,
            self._row_bounds(
                rect,
                30,
                left=self.PANEL_PADDING_X + self.LEFT_SIDE_INSET_X,
                width=max(
                    1,
                    rect.width - (self.PANEL_PADDING_X * 2) - (self.LEFT_SIDE_INSET_X * 2),
                ),
            ),
            [self.theme_dropdown, toggle_scope],
        )

        self.theme_state_label = LabelControl(
            "systems_theme_state",
            Rect(0, 0, rect.width, 28),
            "",
            align="left",
        )
        self.theme_scope_label = LabelControl(
            "systems_theme_scope",
            Rect(0, 0, rect.width, 28),
            "",
            align="left",
        )
        self.theme_resolved_label = LabelControl(
            "systems_theme_resolved",
            Rect(0, 0, rect.width, 28),
            "",
            align="left",
        )
        self._place_vertical_label_stack(
            panel,
            Rect(self.LABEL_INSET_X, 92, max(1, rect.width - self.LABEL_INSET_X), 100),
            [
                self.theme_state_label,
                self.theme_scope_label,
                self.theme_resolved_label,
            ],
            gap=8,
        )
        self._refresh_theme_labels()
        return panel

    def build_state_panel(self, rect: Rect) -> PanelControl:
        panel = PanelControl("systems_state_panel", Rect(rect), draw_background=False)
        context_title = LabelControl(
            "systems_state_context_title",
            Rect(0, 0, 120, 28),
            "Undo Context",
            align="left",
        )
        self.state_context_dropdown = DropdownControl(
            "systems_state_context",
            Rect(0, 0, 180, 32),
            options=[
                DropdownOption("Release", "release"),
                DropdownOption("Build", "build"),
            ],
            selected_index=0,
            on_change=lambda value, _index: self._on_state_context_changed(value),
        )
        self._place_compact_labeled_row(
            panel,
            left=self.LABEL_INSET_X,
            top=0,
            label=context_title,
            field=self.state_context_dropdown,
            label_width=120,
            gap=10,
        )

        cycle_route_button = ButtonControl(
            "systems_state_route_cycle",
            Rect(0, 0, 170, 32),
            "Cycle Route Stack",
            self._cycle_release_router,
            style="round",
        )
        state_label_top = self._add_button_rows(
            panel,
            rect,
            44,
            [
                ButtonControl(
                    "systems_state_approve",
                    Rect(0, 0, 140, 32),
                    "Approve Item",
                    self._approve_release_item,
                    style="round",
                ),
                ButtonControl(
                    "systems_state_blocker",
                    Rect(0, 0, 140, 32),
                    "Add Blocker",
                    self._add_release_blocker,
                    style="round",
                ),
                ButtonControl(
                    "systems_state_advance_context",
                    Rect(0, 0, 190, 32),
                    "Advance Active Context",
                    self._advance_active_context,
                    style="round",
                ),
                ButtonControl(
                    "systems_state_undo_context",
                    Rect(0, 0, 96, 32),
                    "Undo",
                    self._undo_active_context,
                    style="round",
                ),
                ButtonControl(
                    "systems_state_redo_context",
                    Rect(0, 0, 96, 32),
                    "Redo",
                    self._redo_active_context,
                    style="round",
                ),
                ButtonControl(
                    "systems_state_advance_fsm",
                    Rect(0, 0, 156, 32),
                    "Advance FSM",
                    self._advance_release_state_machine,
                    style="round",
                ),
            ],
            left=self.PANEL_PADDING_X + self.LEFT_SIDE_INSET_X,
            width=max(
                1,
                rect.width - (self.PANEL_PADDING_X * 2) - (self.LEFT_SIDE_INSET_X * 2),
            ),
        )
        state_label_top = self._add_single_column_button_row(
            panel,
            rect,
            state_label_top,
            cycle_route_button,
            column_index=0,
            span_both_columns=True,
            span_from_window_left=False,
        )

        self.state_store_label = LabelControl("systems_state_store", Rect(0, 0, rect.width, 28), "", align="left")
        self.state_readiness_label = LabelControl("systems_state_readiness", Rect(0, 0, rect.width, 28), "", align="left")
        self.state_context_label = LabelControl("systems_state_context_status", Rect(0, 0, rect.width, 28), "", align="left")
        self.state_machine_label = LabelControl("systems_state_machine_status", Rect(0, 0, rect.width, 28), "", align="left")
        self.state_router_label = LabelControl("systems_state_router_status", Rect(0, 0, rect.width, 28), "", align="left")
        self._place_vertical_label_stack(
            panel,
            Rect(
                self.LABEL_INSET_X,
                state_label_top + 8,
                max(1, rect.width - self.LABEL_INSET_X),
                172,
            ),
            [
                self.state_store_label,
                self.state_readiness_label,
                self.state_context_label,
                self.state_machine_label,
                self.state_router_label,
            ],
            gap=8,
        )
        self._refresh_state_labels()
        self._force_button_left_alignment(
            panel,
            target_button_id="systems_state_route_cycle",
            reference_button_id="systems_state_redo_context",
        )
        self._force_button_right_alignment(
            panel,
            target_button_id="systems_state_route_cycle",
            reference_button_id="systems_state_advance_fsm",
        )
        return panel

    def build_infrastructure_panel(self, rect: Rect) -> PanelControl:
        panel = PanelControl("systems_infrastructure_panel", Rect(rect), draw_background=False)
        telemetry_button = ButtonControl(
            "systems_infra_telemetry",
            Rect(0, 0, 176, 32),
            "Record Telemetry",
            self._sample_telemetry,
            style="round",
        )
        infrastructure_label_top = self._add_button_rows(
            panel,
            rect,
            0,
            [
                ButtonControl(
                    "systems_infra_run_pipeline",
                    Rect(0, 0, 156, 32),
                    "Run Pipeline",
                    self._run_pipeline_demo,
                    style="round",
                ),
                ButtonControl(
                    "systems_infra_pointer_event",
                    Rect(0, 0, 168, 32),
                    "Next Pointer Event",
                    self._advance_interaction_state,
                    style="round",
                ),
                ButtonControl(
                    "systems_infra_schema",
                    Rect(0, 0, 172, 32),
                    "Toggle Schema Input",
                    self._toggle_schema_example,
                    style="round",
                ),
                ButtonControl(
                    "systems_infra_migrate",
                    Rect(0, 0, 168, 32),
                    "Migrate Snapshot",
                    self._run_snapshot_migration,
                    style="round",
                ),
                ButtonControl(
                    "systems_infra_theme_bus",
                    Rect(0, 0, 194, 32),
                    "Trigger Theme Invalidation",
                    self._trigger_theme_invalidation,
                    style="round",
                ),
                ButtonControl(
                    "systems_infra_virtualize",
                    Rect(0, 0, 190, 32),
                    "Refresh Virtual Window",
                    self._refresh_virtualization_demo,
                    style="round",
                ),
                ButtonControl(
                    "systems_infra_layout",
                    Rect(0, 0, 170, 32),
                    "Solve Constraints",
                    self._solve_constraint_layout,
                    style="round",
                ),
                ButtonControl(
                    "systems_infra_scope",
                    Rect(0, 0, 156, 32),
                    "Push Child Scope",
                    self._push_scope_demo,
                    style="round",
                ),
                ButtonControl(
                    "systems_infra_accessibility",
                    Rect(0, 0, 176, 32),
                    "Announce Accessibility",
                    self._run_accessibility_demo,
                    style="round",
                ),
                ButtonControl(
                    "systems_infra_audio",
                    Rect(0, 0, 170, 32),
                    "Emit Audio Cue",
                    self._run_audio_demo,
                    style="round",
                ),
            ],
            left=self.PANEL_PADDING_X + self.LEFT_SIDE_INSET_X,
            width=max(
                1,
                rect.width - (self.PANEL_PADDING_X * 2) - (self.LEFT_SIDE_INSET_X * 2),
            ),
        )
        infrastructure_label_top = self._add_single_column_button_row(
            panel,
            rect,
            infrastructure_label_top,
            telemetry_button,
            column_index=0,
            span_both_columns=True,
            span_from_window_left=False,
        )

        self.infrastructure_pipeline_label = LabelControl(
            "systems_infra_pipeline_status", Rect(0, 0, rect.width, 28), "", align="left"
        )
        self.infrastructure_interaction_label = LabelControl(
            "systems_infra_interaction_status", Rect(0, 0, rect.width, 28), "", align="left"
        )
        self.infrastructure_schema_label = LabelControl(
            "systems_infra_schema_status", Rect(0, 0, rect.width, 28), "", align="left"
        )
        self.infrastructure_migration_label = LabelControl(
            "systems_infra_migration_status", Rect(0, 0, rect.width, 28), "", align="left"
        )
        self.infrastructure_theme_bus_label = LabelControl(
            "systems_infra_theme_status", Rect(0, 0, rect.width, 28), "", align="left"
        )
        self.infrastructure_virtualization_label = LabelControl(
            "systems_infra_virtualization_status", Rect(0, 0, rect.width, 28), "", align="left"
        )
        self.infrastructure_layout_label = LabelControl(
            "systems_infra_layout_status", Rect(0, 0, rect.width, 28), "", align="left"
        )
        self.infrastructure_scope_label = LabelControl(
            "systems_infra_scope_status", Rect(0, 0, rect.width, 28), "", align="left"
        )
        self.infrastructure_runtime_label = LabelControl(
            "systems_infra_runtime_status", Rect(0, 0, rect.width, 56), "", align="left"
        )
        self._place_vertical_label_stack(
            panel,
            Rect(
                self.LABEL_INSET_X,
                infrastructure_label_top + 8,
                max(1, rect.width - self.LABEL_INSET_X),
                344,
            ),
            [
                self.infrastructure_pipeline_label,
                self.infrastructure_interaction_label,
                self.infrastructure_schema_label,
                self.infrastructure_migration_label,
                self.infrastructure_theme_bus_label,
                self.infrastructure_virtualization_label,
                self.infrastructure_layout_label,
                self.infrastructure_scope_label,
                self.infrastructure_runtime_label,
            ],
            gap=8,
        )
        self._refresh_infrastructure_labels()
        self._force_button_left_alignment(
            panel,
            target_button_id="systems_infra_telemetry",
            reference_button_id="systems_infra_accessibility",
        )
        self._force_button_right_alignment(
            panel,
            target_button_id="systems_infra_telemetry",
            reference_button_id="systems_infra_audio",
        )
        return panel

    def build_scheduling_panel(self, rect: Rect) -> PanelControl:
        panel = PanelControl("systems_scheduling_panel", Rect(rect), draw_background=False)
        timer_probe_button = ButtonControl(
            "systems_schedule_timers",
            Rect(0, 0, 176, 32),
            "Start Timer Probe",
            self._start_timer_probe,
            style="round",
        )
        labels_top = self._add_button_rows(
            panel,
            rect,
            0,
            [
                ButtonControl(
                    "systems_schedule_background_job",
                    Rect(0, 0, 180, 32),
                    "Queue Artifact Build",
                    self._queue_background_job,
                    style="round",
                ),
                ButtonControl(
                    "systems_schedule_rollout",
                    Rect(0, 0, 176, 32),
                    "Start Rollout Script",
                    self._start_rollout_sequence,
                    style="round",
                ),
                ButtonControl(
                    "systems_schedule_rate_limit",
                    Rect(0, 0, 192, 32),
                    "Simulate Burst Input",
                    self._simulate_rate_limited_input,
                    style="round",
                ),
            ],
            left=self.PANEL_PADDING_X + self.LEFT_SIDE_INSET_X,
            width=max(
                1,
                rect.width - (self.PANEL_PADDING_X * 2) - (self.LEFT_SIDE_INSET_X * 2),
            ),
        )
        labels_top = self._add_single_column_button_row(
            panel,
            rect,
            labels_top,
            timer_probe_button,
            column_index=0,
            span_both_columns=True,
            span_from_window_left=False,
        )
        self.scheduling_task_label = LabelControl(
            "systems_scheduling_task_status",
            Rect(0, 0, rect.width, 28),
            "",
            align="left",
        )
        self.scheduling_rollout_label = LabelControl(
            "systems_scheduling_rollout_status",
            Rect(0, 0, rect.width, 28),
            "",
            align="left",
        )
        self.scheduling_timer_label = LabelControl(
            "systems_scheduling_timer_status",
            Rect(0, 0, rect.width, 28),
            "",
            align="left",
        )
        self.scheduling_rate_limiter_label = LabelControl(
            "systems_scheduling_rate_limit_status",
            Rect(0, 0, rect.width, 28),
            "",
            align="left",
        )
        self._place_vertical_label_stack(
            panel,
            Rect(
                self.LABEL_INSET_X,
                labels_top + 8,
                max(1, rect.width - self.LABEL_INSET_X),
                136,
            ),
            [
                self.scheduling_task_label,
                self.scheduling_rollout_label,
                self.scheduling_timer_label,
                self.scheduling_rate_limiter_label,
            ],
            gap=8,
        )
        self._refresh_scheduling_labels()
        self._force_button_left_alignment(
            panel,
            target_button_id="systems_schedule_timers",
            reference_button_id="systems_schedule_background_job",
        )
        self._force_button_right_alignment(
            panel,
            target_button_id="systems_schedule_timers",
            reference_button_id="systems_schedule_rollout",
        )
        return panel

    def build_motion_panel(self, rect: Rect) -> PanelControl:
        panel = PanelControl("systems_motion_panel", Rect(rect), draw_background=False)
        if self._motion_animation_state_machine.current_state is None:
            self._motion_animation_state_machine.set_state("idle")
        self.motion_intro_label = LabelControl(
            "systems_motion_intro",
            Rect(0, 0, rect.width, 28),
            "SceneTimeline, TweenManager, and AnimationSequence demo motion workflows.",
            align="left",
        )
        self._place_vertical_grid_sequence(
            panel,
            Rect(self.LABEL_INSET_X, 0, max(1, rect.width - self.LABEL_INSET_X), 28),
            [(self.motion_intro_label, 28, 0)],
        )

        motion_buttons_top = 44
        motion_labels_anchor_top = self._add_button_rows(
            panel,
            rect,
            motion_buttons_top,
            [
                ButtonControl(
                    "systems_motion_timeline",
                    Rect(0, 0, 160, 32),
                    "Play Timeline",
                    self._play_motion_timeline,
                    style="round",
                ),
                ButtonControl(
                    "systems_motion_tween",
                    Rect(0, 0, 156, 32),
                    "Run Tween",
                    self._run_motion_tween,
                    style="round",
                ),
                ButtonControl(
                    "systems_motion_sequence",
                    Rect(0, 0, 176, 32),
                    "Run Animation Sequence",
                    self._run_motion_sequence,
                    style="round",
                ),
                ButtonControl(
                    "systems_motion_transition",
                    Rect(0, 0, 170, 32),
                    "Toggle Transition",
                    self._toggle_motion_transition,
                    style="round",
                ),
                ButtonControl(
                    "systems_motion_asm",
                    Rect(0, 0, 170, 32),
                    "Cycle Anim State",
                    self._cycle_motion_animation_state,
                    style="round",
                ),
            ],
            per_row=3,
            left=self.PANEL_PADDING_X + self.LEFT_SIDE_INSET_X,
            width=max(
                1,
                rect.width - (self.PANEL_PADDING_X * 2) - (self.LEFT_SIDE_INSET_X * 2),
            ),
        )

        motion_labels_top = motion_labels_anchor_top + 8
        self.scheduling_timeline_label = LabelControl(
            "systems_motion_timeline_status",
            Rect(0, 0, rect.width, 28),
            "",
            align="left",
        )
        self.scheduling_tween_label = LabelControl(
            "systems_motion_tween_status",
            Rect(0, 0, rect.width, 28),
            "",
            align="left",
        )
        self.scheduling_sequence_label = LabelControl(
            "systems_motion_sequence_status",
            Rect(0, 0, rect.width, 28),
            "",
            align="left",
        )
        self._place_vertical_label_stack(
            panel,
            Rect(
                self.LABEL_INSET_X,
                motion_labels_top,
                max(1, rect.width - self.LABEL_INSET_X),
                100,
            ),
            [
                self.scheduling_timeline_label,
                self.scheduling_tween_label,
                self.scheduling_sequence_label,
            ],
            gap=8,
        )
        self._refresh_motion_labels()
        self._force_button_left_alignment(
            panel,
            target_button_id="systems_motion_timeline",
            reference_button_id="systems_motion_transition",
        )
        return panel

    def build_persistence_panel(self, rect: Rect) -> PanelControl:
        panel = PanelControl("systems_persistence_panel", Rect(rect), draw_background=False)
        persistence_label_top = self._add_button_rows(
            panel,
            rect,
            0,
            [
                ButtonControl(
                    "systems_persistence_review_profile",
                    Rect(0, 0, 150, 32),
                    "Apply Review Profile",
                    self._apply_review_profile,
                    style="round",
                ),
                ButtonControl(
                    "systems_persistence_prod_profile",
                    Rect(0, 0, 184, 32),
                    "Apply Production Profile",
                    self._apply_production_profile,
                    style="round",
                ),
                ButtonControl(
                    "systems_persistence_save",
                    Rect(0, 0, 148, 32),
                    "Save Workspace",
                    self._save_workspace_state,
                    style="round",
                ),
                ButtonControl(
                    "systems_persistence_restore",
                    Rect(0, 0, 164, 32),
                    "Restore Workspace",
                    self._restore_workspace_state,
                    style="round",
                ),
            ],
            left=self.PANEL_PADDING_X + self.LEFT_SIDE_INSET_X,
            width=max(
                1,
                rect.width - (self.PANEL_PADDING_X * 2) - (self.LEFT_SIDE_INSET_X * 2),
            ),
        )
        self.persistence_overview_label = LabelControl(
            "systems_persistence_overview",
            Rect(0, 0, rect.width, 28),
            "",
            align="left",
        )
        self.persistence_settings_label = LabelControl(
            "systems_persistence_settings",
            Rect(0, 0, rect.width, 28),
            "",
            align="left",
        )
        self.persistence_status_label = LabelControl(
            "systems_persistence_status",
            Rect(0, 0, rect.width, 56),
            "",
            align="left",
        )
        self._place_vertical_label_stack(
            panel,
            Rect(
                self.LABEL_INSET_X,
                persistence_label_top + 8,
                max(1, rect.width - self.LABEL_INSET_X),
                128,
            ),
            [
                self.persistence_overview_label,
                self.persistence_settings_label,
                self.persistence_status_label,
            ],
            gap=8,
        )
        self._refresh_persistence_labels()
        return panel

    def build_graphics_panel(self, rect: Rect) -> PanelControl:
        panel = PanelControl("systems_graphics_panel", Rect(rect), draw_background=False)
        tile_preview_h = 120

        # Two columns: left (particle systems), right (tile navigation + tilemap).
        top_padding = 8
        left_col_x = self.PANEL_PADDING_X
        left_col_width = max(160, rect.width // 2 - self.PANEL_PADDING_X * 2)
        right_col_x = rect.width // 2 + self.PANEL_PADDING_X
        right_col_width = max(160, rect.width - right_col_x - self.PANEL_PADDING_X)

        nav_cluster = PanelControl(
            "systems_graphics_tile_nav_cluster",
            Rect(0, 0, 96, 96),
            draw_background=True,
        )
        # Right-column elements are left-justified as a group and keep
        # their relative placement (nav cluster left of tile preview).
        nav_gap = 12
        tile_preview_nudge_x = 12
        tile_preview_width = min(
            360,
            max(160, right_col_width - nav_cluster.rect.width - nav_gap - tile_preview_nudge_x),
        )
        tile_preview_x = right_col_x + nav_cluster.rect.width + nav_gap + tile_preview_nudge_x
        nav_cluster_x = right_col_x

        # Left column starts at top.
        buttons_top = top_padding
        self._add_button_rows(
            panel,
            rect,
            buttons_top,
            [
                ButtonControl(
                    "systems_graphics_burst",
                    Rect(0, 0, 156, 32),
                    "Burst Particles",
                    self._trigger_particle_burst,
                    style="round",
                ),
                ButtonControl(
                    "systems_graphics_reset",
                    Rect(0, 0, 170, 32),
                    "Reset Particle Layer",
                    self._reset_particle_layer,
                    style="round",
                ),
            ],
            per_row=2,
            left=left_col_x,
            width=left_col_width,
        )

        preview_width = min(520, left_col_width)
        particle_layer_height = 180
        self._graphics_compositor.resize((preview_width, 180))
        self._graphics_camera.viewport_rect = Rect(0, 0, preview_width, 180)
        self._graphics_tile_camera.size = (tile_preview_width, tile_preview_h)

        # Left column particle stack.
        particle_layer_top = buttons_top + 32 + self.BUTTON_ROW_SPACING
        self._place_graphics_particle_layer(
            panel,
            left=left_col_x,
            top=particle_layer_top,
            width=preview_width,
            height=particle_layer_height,
        )
        # Store panel-local offsets for the emitters so they can be re-synced
        # to screen space each frame (emitters are plain dataclasses and won't
        # move automatically when the window is dragged).
        labels_top = particle_layer_top + particle_layer_height + 12
        self._sync_graphics_emitter_offsets(
            panel_rect=Rect(rect),
            left_col_x=left_col_x,
            left_col_width=left_col_width,
            labels_top=labels_top,
        )
        self.graphics_particle_label = LabelControl(
            "systems_graphics_particle_status",
            Rect(0, 0, left_col_width, 28),
            "",
            align="left",
        )
        self.graphics_layer_label = LabelControl(
            "systems_graphics_layer_status",
            Rect(0, 0, left_col_width, 28),
            "",
            align="left",
        )
        self.graphics_scene_graph_label = LabelControl(
            "systems_graphics_scene_graph_status",
            Rect(0, 0, left_col_width, 28),
            "",
            align="left",
        )
        self.graphics_compositor_label = LabelControl(
            "systems_graphics_compositor_status",
            Rect(0, 0, left_col_width, 28),
            "",
            align="left",
        )
        self.graphics_tile_map_label = LabelControl(
            "systems_graphics_tile_map_status",
            Rect(0, 0, tile_preview_width, 28),
            "",
            align="left",
        )
        self.graphics_tile_preview_canvas = CanvasControl(
            "systems_graphics_tile_map_preview",
            Rect(0, 0, tile_preview_width, tile_preview_h),
            max_events=32,
        )
        self._surface_effect_source = self._build_surface_effect_source((left_col_width, 104))
        self._surface_effect_preview = ImageControl(
            "systems_graphics_surface_effect_preview",
            Rect(0, 0, left_col_width, 104),
            self._surface_effect_source,
            scale=True,
        )
        self._surface_effect_label = ButtonControl(
            "systems_graphics_surface_effect_cycle",
            Rect(0, 0, 220, 32),
            "Cycle Surface Effect",
            self._cycle_surface_effect,
            style="round",
        )
        self.graphics_surface_effects_label = LabelControl(
            "systems_graphics_surface_effects_status",
            Rect(0, 0, left_col_width, 28),
            "",
            align="left",
        )

        self._place_vertical_label_stack(
            panel,
            Rect(left_col_x, labels_top, max(1, left_col_width), 172),
            [
                self.graphics_particle_label,
                self.graphics_layer_label,
                self.graphics_scene_graph_label,
                self.graphics_compositor_label,
                self.graphics_surface_effects_label,
            ],
            gap=8,
        )
        self._place_vertical_grid_sequence(
            panel,
            Rect(left_col_x, labels_top + 180, max(1, left_col_width), 144),
            [
                (self._surface_effect_label, 32, 8),
                (self._surface_effect_preview, 104, 0),
            ],
        )

        # Right column starts at top; move controls below labels to avoid overlap.
        right_label_top = top_padding
        right_content_top = right_label_top + 26
        tile_preview_top = right_content_top
        nav_cluster_y = right_content_top

        tile_preview_label = LabelControl(
            "systems_graphics_tile_map_preview_label",
            Rect(0, 0, tile_preview_width, 22),
            "Tilemap Output",
            align="left",
        )
        nav_cluster_label = LabelControl(
            "systems_graphics_tile_nav_label",
            Rect(0, 0, nav_cluster.rect.width, 22),
            "Tile Navigation",
            align="left",
        )
        self._place_vertical_grid_sequence(
            panel,
            Rect(tile_preview_x, right_label_top, max(1, tile_preview_width), tile_preview_h + 62),
            [
                (tile_preview_label, 22, 4),
                (self.graphics_tile_preview_canvas, tile_preview_h, 12),
                (self.graphics_tile_map_label, 28, 0),
            ],
        )
        self._place_vertical_grid_sequence(
            panel,
            Rect(nav_cluster_x, right_label_top, max(1, nav_cluster.rect.width), nav_cluster.rect.height + 26),
            [
                (nav_cluster_label, 22, 4),
                (nav_cluster, nav_cluster.rect.height, 0),
            ],
        )
        nav_left = ArrowBoxControl(
            "systems_graphics_nav_left",
            Rect(0, 0, 44, 44),
            180,
            on_activate=lambda: self._pan_tile_camera(-24, 0),
        )
        nav_up = ArrowBoxControl(
            "systems_graphics_nav_up",
            Rect(0, 0, 44, 44),
            90,
            on_activate=lambda: self._pan_tile_camera(0, -24),
        )
        nav_down = ArrowBoxControl(
            "systems_graphics_nav_down",
            Rect(0, 0, 44, 44),
            270,
            on_activate=lambda: self._pan_tile_camera(0, 24),
        )
        nav_right = ArrowBoxControl(
            "systems_graphics_nav_right",
            Rect(0, 0, 44, 44),
            0,
            on_activate=lambda: self._pan_tile_camera(24, 0),
        )
        nav_grid = GridLayout(
            row_tracks=[44, 44],
            col_tracks=[44, 44],
            gap=4,
            padding=0,
        )
        nav_grid.place(nav_left, GridPlacement(row=0, col=0))
        nav_grid.place(nav_up, GridPlacement(row=0, col=1))
        nav_grid.place(nav_down, GridPlacement(row=1, col=0))
        nav_grid.place(nav_right, GridPlacement(row=1, col=1))
        nav_grid.apply(Rect(2, 2, 92, 92))
        nav_cluster.add_at(nav_left, nav_left.rect.left, nav_left.rect.top)
        nav_cluster.add_at(nav_up, nav_up.rect.left, nav_up.rect.top)
        nav_cluster.add_at(nav_down, nav_down.rect.left, nav_down.rect.top)
        nav_cluster.add_at(nav_right, nav_right.rect.left, nav_right.rect.top)

        self._render_tile_map_preview()
        self._refresh_surface_effect_preview()
        self._refresh_graphics_labels()
        self._inset_left_side_children(panel)
        return panel

    def build_text_panel(self, rect: Rect) -> PanelControl:
        panel = PanelControl("systems_text_panel", Rect(rect), draw_background=False)
        locale_label = LabelControl(
            "systems_text_locale_label",
            Rect(0, 0, 96, 28),
            "Locale",
            align="left",
        )

        locale_options = [DropdownOption(code.upper(), code) for code in self._locale_registry.registered_locales]
        selected_locale = self._locale_registry.active_locale
        selected_index = next(
            (index for index, option in enumerate(locale_options) if option.value == selected_locale),
            0,
        )
        self.text_locale_dropdown = DropdownControl(
            "systems_text_locale",
            Rect(0, 0, 160, 32),
            options=locale_options,
            selected_index=selected_index,
            on_change=lambda value, _index: self._on_text_locale_changed(value),
        )
        self._place_compact_labeled_row(
            panel,
            left=0,
            top=0,
            label=locale_label,
            field=self.text_locale_dropdown,
            label_width=96,
            gap=2,
        )

        query_label = LabelControl(
            "systems_text_query_label",
            Rect(0, 0, 72, 28),
            "Search",
            align="left",
        )
        self.text_query_input = TextInputControl(
            "systems_text_query",
            Rect(0, 0, max(180, rect.width - 386), 32),
            value=self._text_search_query,
            placeholder="release",
            on_change=self._on_text_query_changed,
        )
        self._place_compact_labeled_row(
            panel,
            left=278,
            top=0,
            label=query_label,
            field=self.text_query_input,
            label_width=72,
            gap=0,
        )

        labels_top = self._add_button_rows(
            panel,
            rect,
            44,
            [
                ButtonControl(
                    "systems_text_search",
                    Rect(0, 0, 140, 32),
                    "Run Search",
                    self._run_text_search,
                    style="round",
                ),
                ButtonControl(
                    "systems_text_next",
                    Rect(0, 0, 146, 32),
                    "Next Match",
                    self._next_text_match,
                    style="round",
                ),
                ButtonControl(
                    "systems_text_replace",
                    Rect(0, 0, 174, 32),
                    "Replace First Match",
                    self._replace_first_text_match,
                    style="round",
                ),
                ButtonControl(
                    "systems_text_mode_case",
                    Rect(0, 0, 140, 32),
                    "Case: Off",
                    self._toggle_text_case_sensitive,
                    style="round",
                ),
                ButtonControl(
                    "systems_text_mode_whole",
                    Rect(0, 0, 170, 32),
                    "Whole Word: Off",
                    self._toggle_text_whole_word,
                    style="round",
                ),
                ButtonControl(
                    "systems_text_mode_regex",
                    Rect(0, 0, 140, 32),
                    "Regex: Off",
                    self._toggle_text_regex,
                    style="round",
                ),
                ButtonControl(
                    "systems_text_regex_preset",
                    Rect(0, 0, 174, 32),
                    "Regex Preset",
                    self._apply_text_regex_preset,
                    style="round",
                ),
                ButtonControl(
                    "systems_text_locale_regex_preset",
                    Rect(0, 0, 204, 32),
                    "Locale Regex Preset",
                    self._apply_text_locale_regex_preset,
                    style="round",
                ),
            ],
            per_row=3,
            width=max(
                1,
                rect.width - (self.PANEL_PADDING_X * 2) - self.LEFT_SIDE_INSET_X,
            ),
        )

        for child in panel.children:
            if child.control_id == "systems_text_mode_case":
                self.text_mode_case_button = child
            elif child.control_id == "systems_text_mode_whole":
                self.text_mode_whole_word_button = child
            elif child.control_id == "systems_text_mode_regex":
                self.text_mode_regex_button = child

        self.text_search_status_label = LabelControl(
            "systems_text_status",
            Rect(0, 0, rect.width, 28),
            "",
            align="left",
        )
        self.text_search_match_label = LabelControl(
            "systems_text_match_status",
            Rect(0, 0, rect.width, 28),
            "",
            align="left",
        )
        preview_top = labels_top + 80
        preview_height = max(120, rect.height - preview_top - 12)
        preview_width = rect.width - self.PANEL_PADDING_X * 2
        self._place_vertical_label_stack(
            panel,
            Rect(0, labels_top + 8, max(1, rect.width), 64),
            [
                self.text_search_status_label,
                self.text_search_match_label,
            ],
            gap=8,
        )
        self._place_text_preview_region(
            panel,
            top=preview_top,
            width=preview_width,
            height=preview_height,
        )
        self._refresh_text_labels()
        self._inset_left_side_children(panel)
        self._inset_text_labels(panel)
        self._force_button_left_alignment(
            panel,
            target_button_id="systems_text_search",
            reference_button_id="systems_text_regex_preset",
        )
        self._force_button_left_alignment(
            panel,
            target_button_id="systems_text_mode_case",
            reference_button_id="systems_text_regex_preset",
        )
        return panel

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
        title = self._locale_registry.t("systems.text.title", fallback="Release Notes")
        summary = self._locale_registry.t("systems.text.summary", fallback="Systems demo summary unavailable.")
        actions = self._locale_registry.t("systems.text.actions", fallback="Action items unavailable.")
        hint = self._locale_registry.t("systems.text.hint", fallback="Search for release.")
        self._text_searcher.text = f"{title}\n{summary}\n{actions}\n{hint}"

    def _rebuild_text_searcher(self) -> None:
        source_text = self._text_searcher.text
        self._text_searcher = TextSearcher(
            source_text,
            case_sensitive=self._text_case_sensitive,
            whole_word=self._text_whole_word,
            use_regex=self._text_use_regex,
        )

    def _on_text_locale_changed(self, value: str) -> None:
        self._locale_registry.set_locale(str(value))
        self._text_search_cursor = 0
        self._text_last_action = f"Locale switched to {self._locale_registry.active_locale.upper()}."
        self._rebuild_text_document()
        self._refresh_text_labels()

    def _on_text_query_changed(self, value: str) -> None:
        self._text_search_query = str(value)

    def _run_text_search(self) -> None:
        self._text_search_cursor = 0
        self._text_last_action = "Search refreshed for current localized note."
        self._refresh_text_labels()

    def _toggle_text_case_sensitive(self) -> None:
        self._text_case_sensitive = not self._text_case_sensitive
        self._text_search_cursor = 0
        self._rebuild_text_searcher()
        self._text_last_action = (
            f"Case-sensitive mode {'enabled' if self._text_case_sensitive else 'disabled'}."
        )
        self._refresh_text_labels()

    def _toggle_text_whole_word(self) -> None:
        self._text_whole_word = not self._text_whole_word
        self._text_search_cursor = 0
        self._rebuild_text_searcher()
        self._text_last_action = (
            f"Whole-word mode {'enabled' if self._text_whole_word else 'disabled'}."
        )
        self._refresh_text_labels()

    def _toggle_text_regex(self) -> None:
        self._text_use_regex = not self._text_use_regex
        self._text_search_cursor = 0
        self._rebuild_text_searcher()
        self._text_last_action = f"Regex mode {'enabled' if self._text_use_regex else 'disabled'}."
        self._refresh_text_labels()

    def _apply_text_regex_preset(self) -> None:
        # Practical release-note token scanner: capture terms around release/deploy/check keywords.
        preset = r"\b(?:release|rollout|checks?)\w*\b"
        self._text_search_query = preset
        if self.text_query_input is not None:
            self.text_query_input.set_value(preset)
        if not self._text_use_regex:
            self._text_use_regex = True
            self._rebuild_text_searcher()
        self._text_search_cursor = 0
        self._text_last_action = "Applied regex preset for release-note keyword scanning."
        self._refresh_text_labels()

    def _apply_text_locale_regex_preset(self) -> None:
        # Locale-aware token scanner for EN/ES/FR release terminology.
        preset = r"\b(?:release|rollout|checks?|lanzamiento|despliegue|pruebas|version|deploiement)\w*\b"
        self._text_search_query = preset
        if self.text_query_input is not None:
            self.text_query_input.set_value(preset)
        if not self._text_use_regex:
            self._text_use_regex = True
            self._rebuild_text_searcher()
        self._text_search_cursor = 0
        self._text_last_action = "Applied locale regex preset for EN/ES/FR release terms."
        self._refresh_text_labels()

    def _next_text_match(self) -> None:
        query = self._text_search_query.strip()
        matches = self._text_searcher.find_all(query)
        if not matches:
            self._text_last_action = "No matches available for next navigation."
            self._refresh_text_labels()
            return
        self._text_search_cursor = (self._text_search_cursor + 1) % len(matches)
        self._text_last_action = f"Advanced to match {self._text_search_cursor + 1} of {len(matches)}."
        self._refresh_text_labels()

    def _replace_first_text_match(self) -> None:
        query = self._text_search_query.strip()
        if not query:
            self._text_last_action = "Enter a search token before replace."
            self._refresh_text_labels()
            return
        match = self._text_searcher.find_next(query, from_pos=0)
        if match is None:
            self._text_last_action = "No match found to replace."
            self._refresh_text_labels()
            return
        replacement = self._locale_registry.t("systems.text.replacement", fallback="deployment")
        self._text_searcher.text = self._text_searcher.replace(match, replacement)
        self._text_search_cursor = 0
        self._text_last_action = f"Replaced first '{query}' with '{replacement}'."
        self._refresh_text_labels()

    def _build_text_preview_spans(self, text: str, matches: list[object], active_index: int) -> list[TextSpan]:
        if not matches:
            return [TextSpan(text, color=(226, 232, 240), role="body")]
        spans: list[TextSpan] = []
        cursor = 0
        for index, match in enumerate(matches):
            start = int(match.start)
            end = int(match.end)
            if start > cursor:
                spans.append(TextSpan(text[cursor:start], color=(226, 232, 240), role="body"))
            spans.append(
                TextSpan(
                    text[start:end],
                    bold=True,
                    color=(255, 202, 122) if index == active_index else (155, 209, 255),
                    role="body",
                )
            )
            cursor = end
        if cursor < len(text):
            spans.append(TextSpan(text[cursor:], color=(226, 232, 240), role="body"))
        return spans

    def _render_text_preview_fallback(self, surface: Surface, text: str) -> None:
        font = pygame.font.Font(None, 20)
        color = (226, 232, 240)
        y = 8
        max_width = max(8, surface.get_width() - 16)
        for line in text.splitlines():
            words = line.split(" ")
            current = ""
            for word in words:
                test = word if not current else f"{current} {word}"
                if font.size(test)[0] <= max_width:
                    current = test
                else:
                    surface.blit(font.render(current, True, color), (8, y))
                    y += 22
                    current = word
            if current:
                surface.blit(font.render(current, True, color), (8, y))
                y += 22
            y += 4
            if y > surface.get_height() - 24:
                break

    def _render_text_preview(self, matches: list[object], active_index: int) -> None:
        if self.text_preview_canvas is None:
            return
        surface = self.text_preview_canvas.get_canvas_surface()
        surface.fill((27, 32, 38))
        text = self._text_searcher.text
        spans = self._build_text_preview_spans(text, matches, active_index)
        self._text_flow.width = max(1, surface.get_width() - 12)
        self._text_flow.set_content(spans)
        theme = getattr(getattr(self.demo, "app", None), "theme", None)
        if theme is not None:
            try:
                self._text_flow.layout(theme)
                self._text_flow.render(surface, 6, 6)
            except Exception:
                self._render_text_preview_fallback(surface, text)
        else:
            self._render_text_preview_fallback(surface, text)
        self.text_preview_canvas.invalidate()

    def _refresh_text_labels(self) -> None:
        query = self._text_search_query.strip()
        matches = self._text_searcher.find_all(query)
        active_index = min(self._text_search_cursor, max(0, len(matches) - 1)) if matches else -1
        if self.text_mode_case_button is not None:
            self.text_mode_case_button.text = f"Case: {'On' if self._text_case_sensitive else 'Off'}"
        if self.text_mode_whole_word_button is not None:
            self.text_mode_whole_word_button.text = f"Whole Word: {'On' if self._text_whole_word else 'Off'}"
        if self.text_mode_regex_button is not None:
            self.text_mode_regex_button.text = f"Regex: {'On' if self._text_use_regex else 'Off'}"
        if self.text_search_status_label is not None:
            locale = self._locale_registry.active_locale.upper()
            translated_title = self._locale_registry.t("systems.text.title", fallback="Release Notes")
            self.text_search_status_label.text = (
                f"LocaleRegistry active={locale} locales={self._locale_registry.registered_locales} | "
                f"StringTable title='{translated_title}' | modes(case={self._text_case_sensitive}, whole={self._text_whole_word}, regex={self._text_use_regex})"
            )
        if self.text_search_match_label is not None:
            if not query:
                self.text_search_match_label.text = "TextSearcher waiting for a search token."
            elif not matches:
                self.text_search_match_label.text = f"TextSearcher found no matches for '{query}'. {self._text_last_action}"
            else:
                current = matches[active_index]
                self.text_search_match_label.text = (
                    f"TextSearcher matches={len(matches)} current={active_index + 1} "
                    f"span=({current.start},{current.end}) | {self._text_last_action}"
                )
        self._render_text_preview(matches, active_index)

    def _project_backlog_item(self, item: _BacklogItem) -> ListItem:
        return ListItem(
            label=f"[{item.status}] P{item.priority} {item.title}",
            value=item.title,
            data=item,
        )

    def _selected_backlog_filter(self) -> str:
        selected = getattr(self.data_filter_dropdown, "selected_option", None)
        if selected is None:
            return "All"
        return str(selected.value)

    def _refresh_backlog_view(self) -> None:
        selected_filter = self._selected_backlog_filter()
        self._backlog_view.query.filters = []
        if selected_filter != "All":
            self._backlog_view.query.filters.append(lambda item, status=selected_filter: item.status == status)
        self._backlog_view.refresh()
        self._refresh_backlog_labels()

    def _on_backlog_filter_changed(self, value: str) -> None:
        _ = value
        self._selected_backlog_item = None
        self._refresh_backlog_view()

    def _on_backlog_view_refreshed(self) -> None:
        if self.data_list is None:
            return
        items = self.data_list.items
        if items:
            self.data_list.selected_index = 0
            self._on_backlog_selected(0, items[0])
            return
        self._selected_backlog_item = None
        self._refresh_backlog_labels()

    def _on_backlog_selected(self, _index: int, item: ListItem) -> None:
        data = item.data if isinstance(item.data, _BacklogItem) else None
        self._selected_backlog_item = data
        if data is not None:
            self._backlog_cache.get_or_load(data.title, lambda: self._cache_payload_for_backlog_item(data))
        self._refresh_backlog_labels()

    def _cache_payload_for_backlog_item(self, item: _BacklogItem) -> str:
        return f"{item.owner} owns the {item.title.lower()} handoff while the item is in {item.status.lower()} state."

    def _refresh_backlog_labels(self) -> None:
        if self.data_summary_label is not None:
            self.data_summary_label.text = (
                f"CollectionView showing {self._backlog_view.count()} items for {self._selected_backlog_filter().lower()} routing."
            )
        if self.data_cache_label is not None:
            stats = self._backlog_cache.stats()
            self.data_cache_label.text = (
                f"DataCache size {stats.size} | hits {stats.hits} | misses {stats.misses} | evictions {stats.evictions}"
            )
        if self.data_detail_label is not None:
            if self._selected_backlog_item is None:
                self.data_detail_label.text = "Select a backlog item to inspect its cached deployment note."
            else:
                payload = self._backlog_cache.get_or_load(
                    self._selected_backlog_item.title,
                    lambda item=self._selected_backlog_item: self._cache_payload_for_backlog_item(item),
                )
                self.data_detail_label.text = payload

    def _add_backlog_item(self) -> None:
        templates = (
            ("Localization review", "Review", 2, "Nia"),
            ("Accessibility script", "Ready", 3, "Mira"),
            ("Telemetry snapshot", "Planned", 5, "Tao"),
        )
        title, status, priority, owner = templates[self._next_backlog_index % len(templates)]
        self._next_backlog_index += 1
        item = _BacklogItem(f"{title} {self._next_backlog_index}", status, priority, owner)
        self._backlog_items.append(item)
        self._refresh_backlog_view()

    def _clear_backlog_cache(self) -> None:
        self._backlog_cache.invalidate_all()
        self._refresh_backlog_labels()

    def _check_pipeline_name(self, value: object) -> str | None:
        reserved = {"admin", "root", "prod"}
        normalized = str(value).strip().lower()
        if normalized in reserved:
            return "Reserved pipeline name"
        return None

    def _on_deployment_name_changed(self, value: str) -> None:
        self._deployment_name_field.value.value = str(value)
        self._refresh_validation_labels()

    def _on_environment_changed(self, value: str) -> None:
        self._environment_field.value.value = str(value)
        self._refresh_validation_labels()

    def _run_local_validation_checks(self) -> None:
        self._form_validator.validate_all_local()
        self._refresh_validation_labels()

    def _apply_suggested_name(self) -> None:
        suggested = "staging-gui-release"
        if self.validation_name_input is not None:
            self.validation_name_input.set_value(suggested)
        self._deployment_name_field.value.value = suggested
        self._refresh_validation_labels()

    def _refresh_validation_labels(self) -> None:
        if self.validation_state_label is not None:
            environment = self._environment_field.value.value
            if self._form_validator.is_valid:
                self.validation_state_label.text = f"AsyncFormValidator: ready to route build to {environment}."
            else:
                self.validation_state_label.text = "AsyncFormValidator: deployment form still needs attention."
        if self.validation_local_label is not None:
            local_error = self._name_validator.local_error.value or self._environment_validator.local_error.value
            self.validation_local_label.text = (
                f"Local validation: {local_error}" if local_error is not None else "Local validation: passed"
            )
        if self.validation_async_label is not None:
            if self._name_validator.is_validating.value:
                self.validation_async_label.text = "Async validation: checking pipeline name availability..."
            else:
                async_error = self._name_validator.async_error.value
                self.validation_async_label.text = (
                    f"Async validation: {async_error}" if async_error is not None else "Async validation: pipeline name available"
                )

    def _advance_history_stage(self) -> None:
        current = self._history_stage_index
        if current >= len(self._history_stages) - 1:
            return
        next_index = current + 1
        description = f"Promote to {self._history_stages[next_index]}"
        self._history.push(_StatusChangeCommand(self, next_index, description))
        self._refresh_history_labels()

    def _batch_promote_history_stage(self) -> None:
        current = self._history_stage_index
        if current >= len(self._history_stages) - 1:
            return
        with self._history.transaction("Prepare release bundle"):
            mid_index = min(current + 1, len(self._history_stages) - 1)
            self._history.push(
                _StatusChangeCommand(self, mid_index, f"Promote to {self._history_stages[mid_index]}")
            )
            final_index = min(mid_index + 1, len(self._history_stages) - 1)
            if final_index != mid_index:
                self._history.push(
                    _StatusChangeCommand(self, final_index, f"Promote to {self._history_stages[final_index]}")
                )
        self._refresh_history_labels()

    def _undo_history_stage(self) -> None:
        self._history.undo()
        self._refresh_history_labels()

    def _redo_history_stage(self) -> None:
        self._history.redo()
        self._refresh_history_labels()

    def _refresh_history_labels(self) -> None:
        if self.history_current_label is not None:
            self.history_current_label.text = (
                f"CommandHistory current milestone: {self._history_stages[self._history_stage_index]}"
            )
        if self.history_undo_label is not None:
            undo_desc = self._history.undo_description or "Nothing to undo"
            self.history_undo_label.text = f"Undo: {undo_desc}"
        if self.history_redo_label is not None:
            redo_desc = self._history.redo_description or "Nothing to redo"
            self.history_redo_label.text = f"Redo: {redo_desc}"

    def _on_theme_changed(self, value: str) -> None:
        self._theme_manager.switch(str(value))
        self._refresh_theme_labels()

    def _toggle_review_scope(self) -> None:
        self._review_scope_enabled = not self._review_scope_enabled
        self._refresh_theme_labels()

    def _refresh_theme_labels(self) -> None:
        active_name = self._theme_manager.active_theme.value
        scoped = ScopedThemeManager(self._theme_manager.active_tokens.value)
        if self._review_scope_enabled:
            scoped.push(self._review_scope)
        global_primary = self._theme_manager.token("primary")
        scoped_primary = scoped.resolve("primary")
        if self.theme_state_label is not None:
            self.theme_state_label.text = f"ThemeManager active theme: {active_name}"
        if self.theme_scope_label is not None:
            scope_state = "enabled" if self._review_scope_enabled else "disabled"
            self.theme_scope_label.text = f"ScopedThemeManager review scope: {scope_state}"
        if self.theme_resolved_label is not None:
            self.theme_resolved_label.text = (
                f"Resolved primary token global {global_primary} | scoped {scoped_primary}"
            )

    def _on_state_context_changed(self, value: str) -> None:
        key = str(value)
        if key not in {"release", "build"}:
            return
        self._undo_context.set_active(key)
        self._undo_context_key = key
        self._refresh_state_labels()

    def _approve_release_item(self) -> None:
        pending = int(self._release_store.get("pending", 0))
        approved = int(self._release_store.get("approved", 0))
        blocked = int(self._release_store.get("blocked", 0))
        if pending <= 0:
            return
        with StateTransaction(self._release_store):
            next_pending = max(0, pending - 1)
            self._release_store.dispatch(
                {
                    "pending": next_pending,
                    "approved": approved + 1,
                    "status": "Ready" if next_pending == 0 and blocked == 0 else "Review",
                }
            )
        self._refresh_state_labels()

    def _add_release_blocker(self) -> None:
        blocked = int(self._release_store.get("blocked", 0))
        self._release_store.dispatch({"blocked": blocked + 1, "status": "Blocked"})
        self._refresh_state_labels()

    def _advance_active_context(self) -> None:
        if self._undo_context_key == "release":
            current = self._state_stage_index
            if current >= len(self._state_stages) - 1:
                return
            next_index = current + 1
            self._state_history.push(
                _SetIndexCommand(
                    self,
                    "_state_stage_index",
                    next_index,
                    f"Set release milestone to {self._state_stages[next_index]}",
                )
            )
        else:
            current = self._state_build_stage_index
            if current >= len(self._state_build_stages) - 1:
                return
            next_index = current + 1
            self._state_build_history.push(
                _SetIndexCommand(
                    self,
                    "_state_build_stage_index",
                    next_index,
                    f"Set build lane to {self._state_build_stages[next_index]}",
                )
            )
        self._refresh_state_labels()

    def _undo_active_context(self) -> None:
        self._undo_context.undo()
        self._refresh_state_labels()

    def _redo_active_context(self) -> None:
        self._undo_context.redo()
        self._refresh_state_labels()

    def _advance_release_state_machine(self) -> None:
        self._release_state_machine.trigger("advance")
        if self._release_hierarchical_state_machine.current.value == "planning":
            self._release_hierarchical_state_machine.trigger("start")
        else:
            promoted = self._release_hierarchical_state_machine.sub_trigger("execution", "promote")
            if not promoted:
                self._release_hierarchical_state_machine.trigger("pause")
        self._refresh_state_labels()

    def _cycle_release_router(self) -> None:
        phase = self._router_cycle_index % 3
        next_route = self._router_cycle_paths[self._router_cycle_index % len(self._router_cycle_paths)]
        if phase == 0:
            self._release_router.push(next_route, {"source": "systems_demo"})
        elif phase == 1:
            self._release_router.replace(next_route, {"mode": "replace"})
        else:
            if not self._release_router.pop():
                self._release_router.push(next_route, {"source": "systems_demo"})
        self._router_cycle_index += 1
        self._refresh_state_labels()

    def _refresh_state_labels(self) -> None:
        pending = int(self._release_store.get("pending", 0))
        approved = int(self._release_store.get("approved", 0))
        blocked = int(self._release_store.get("blocked", 0))
        status = str(self._release_store.get("status", "Review"))
        readiness = int(self._release_readiness.value)
        active_key = self._undo_context.active_key or "none"
        if self.state_store_label is not None:
            self.state_store_label.text = (
                f"AppStateStore release queue -> pending {pending} | approved {approved} | blocked {blocked} | status {status}"
            )
        if self.state_readiness_label is not None:
            self.state_readiness_label.text = (
                f"StateSelector readiness score: {readiness} (approved contributes +25, blockers contribute -10 each)"
            )
        if self.state_context_label is not None:
            release_stage = self._state_stages[self._state_stage_index]
            build_stage = self._state_build_stages[self._state_build_stage_index]
            self.state_context_label.text = (
                f"UndoContextManager active={active_key} | release={release_stage} | build={build_stage} "
                f"| can_undo={self._undo_context.can_undo} | can_redo={self._undo_context.can_redo}"
            )
        if self.state_machine_label is not None:
            hierarchy_state = self._release_hierarchical_state_machine.current.value
            hierarchy_ring = self._release_hierarchical_state_machine.sub_current("execution")
            self.state_machine_label.text = (
                f"StateMachine stage={self._release_state_machine.current.value} | "
                f"HierarchicalStateMachine outer={hierarchy_state} ring={hierarchy_ring}"
            )
        if self.state_router_label is not None:
            current_route = self._release_router.current_route or "none"
            self.state_router_label.text = (
                f"Router route={current_route} history={len(self._release_router.history)} "
                f"can_pop={self._release_router.can_pop()}"
            )

    def _queue_background_job(self) -> None:
        self._task_job_index += 1
        task_id = f"artifact-{self._task_job_index:02d}"
        payload = {
            "lane": self._settings_registry.get_value("systems", "profile"),
            "checks": int(self._settings_registry.get_value("systems", "parallel_checks")),
        }
        self._task_scheduler.add_task(task_id, self._build_artifact_job, payload)
        self._task_last_summary = f"TaskScheduler queued {task_id} for the {payload['lane']} lane."
        self._task_last_failure = ""
        self._refresh_scheduling_labels()

    def _build_artifact_job(self, task_id: str, payload: dict[str, object]) -> str:
        lane = str(payload.get("lane", "review"))
        checks = int(payload.get("checks", 1))
        return f"{task_id} built for {lane} with {checks} parallel checks"

    def _start_rollout_sequence(self) -> None:
        if self._rollout_handle is not None and self._rollout_handle.is_running:
            return

        def _sequence():
            self._rollout_phase = "Prime canary ring"
            yield Sleep(0.05)
            self._rollout_phase = "Wait for smoke checks"
            yield Sleep(0.05)
            self._rollout_phase = "Promote stable ring"
            yield Sleep(0.05)
            self._rollout_phase = "Rollout complete"

        self._rollout_handle = self._cooperative_scheduler.start(_sequence())
        self._refresh_scheduling_labels()

    def _refresh_scheduling_labels(self) -> None:
        finished = self._task_scheduler.get_finished_tasks()
        if finished:
            latest_task = finished[-1]
            result = self._task_scheduler.pop_result(latest_task, None)
            if result is not None:
                self._task_last_summary = f"TaskScheduler finished {latest_task}: {result}"
            self._task_scheduler.clear_finished_tasks()
        failures = self._task_scheduler.get_failed_tasks()
        if failures:
            latest_task, error = failures[-1]
            self._task_last_failure = f"TaskScheduler failed {latest_task}: {error}"
            self._task_scheduler.clear_failed_tasks()
        if self.scheduling_task_label is not None:
            summary = self._task_last_failure or self._task_last_summary
            self.scheduling_task_label.text = (
                f"{summary} | pending={self._task_scheduler.pending_count()} running={self._task_scheduler.running_count()}"
            )
        if self.scheduling_rollout_label is not None:
            self.scheduling_rollout_label.text = (
                f"CooperativeScheduler phase: {self._rollout_phase} | active coroutines={self._cooperative_scheduler.coroutine_count}"
            )
        if self.scheduling_timer_label is not None:
            self.scheduling_timer_label.text = (
                f"Timers active={self._timers.timer_ids()} probe_armed={self._timer_probe_armed} last_event={self._timer_last_event}"
            )
        if self.scheduling_rate_limiter_label is not None:
            self.scheduling_rate_limiter_label.text = (
                f"{self._rate_limiter_status} | throttled_events={self._throttle_event_count} "
                f"debounced_commits={self._debounce_commit_count}"
            )
        if self.scheduling_timeline_label is not None:
            self.scheduling_timeline_label.text = (
                f"SceneTimeline stage={self._motion_timeline_stage} cycles={self._motion_timeline_cycles}"
            )
        if self.scheduling_tween_label is not None:
            self.scheduling_tween_label.text = (
                f"TweenManager value={self._motion_tween_value:.2f} active_tweens={self._motion_tweens.active_count}"
            )
        if self.scheduling_sequence_label is not None:
            self.scheduling_sequence_label.text = (
                f"AnimationSequence stage={self._motion_sequence_stage} runs={self._motion_sequence_runs} | "
                f"TransitionManager phase={self._motion_transition_phase} value={self._motion_transition_value:.2f} | "
                f"AnimationStateMachine state={self._motion_animation_state} value={self._motion_animation_value:.2f}"
            )

    def _refresh_motion_labels(self) -> None:
        self._refresh_scheduling_labels()
        if self.motion_intro_label is not None:
            self.motion_intro_label.text = (
                "SceneTimeline, TweenManager, AnimationSequence, TransitionManager, "
                "and AnimationStateMachine demo motion workflows."
            )

    def _play_motion_timeline(self) -> None:
        timeline = SceneTimeline(duration=1.6)
        timeline.at(0.0, lambda: self._set_motion_timeline_stage("Queued"))
        timeline.at(0.5, lambda: self._set_motion_timeline_stage("Running"))
        timeline.at(1.0, lambda: self._set_motion_timeline_stage("Settling"))
        timeline.on_complete(lambda: self._set_motion_timeline_stage("Complete"))
        self._motion_timeline_stage = "Queued"
        self._motion_timeline_cycles += 1
        self._motion_timeline = timeline
        self._motion_timeline.play()
        self._refresh_scheduling_labels()

    def _set_motion_timeline_stage(self, stage: str) -> None:
        self._motion_timeline_stage = str(stage)
        self._refresh_scheduling_labels()

    def _run_motion_tween(self) -> None:
        self._motion_tweens.cancel_all()
        self._motion_tween_value = 0.0
        self._motion_sequence_stage = "Tween running"
        self._motion_tweens.tween(
            self,
            "_motion_tween_value",
            1.0,
            0.8,
            on_complete=lambda: self._set_motion_sequence_stage("Tween complete"),
        )
        self._refresh_scheduling_labels()

    def _run_motion_sequence(self) -> None:
        self._motion_tweens.cancel_all()
        self._motion_tween_value = 0.0
        self._motion_sequence_runs += 1
        sequence = AnimationSequence(self._motion_tweens)
        sequence.then(
            target=self,
            attr="_motion_tween_value",
            end_value=1.0,
            duration_seconds=0.4,
        ).wait(0.1).then(
            target=self,
            attr="_motion_tween_value",
            end_value=0.25,
            duration_seconds=0.45,
        ).on_done(lambda: self._set_motion_sequence_stage("Sequence complete"))
        self._motion_sequence_stage = "Sequence running"
        sequence.start()
        self._refresh_scheduling_labels()

    def _toggle_motion_transition(self) -> None:
        if self._motion_transition_value >= 0.5:
            self._motion_transition_phase = "Hide"
            self._transition_manager.on_hide(self)
        else:
            self._motion_transition_phase = "Show"
            self._transition_manager.on_show(self)
        self._refresh_scheduling_labels()

    def _on_motion_animation_state_changed(self, state_name: str) -> None:
        self._motion_animation_state = str(state_name)
        self._refresh_scheduling_labels()

    def _cycle_motion_animation_state(self) -> None:
        self._motion_animation_state_index = (self._motion_animation_state_index + 1) % len(self._motion_animation_states)
        next_state = self._motion_animation_states[self._motion_animation_state_index]
        self._motion_animation_state_machine.set_state(next_state)
        self._refresh_scheduling_labels()

    def _set_motion_sequence_stage(self, stage: str) -> None:
        self._motion_sequence_stage = str(stage)
        self._refresh_scheduling_labels()

    def _start_timer_probe(self) -> None:
        self._timer_probe_armed = True
        if not self._timers.has_timer("systems_probe_heartbeat"):
            self._timers.add_timer("systems_probe_heartbeat", 0.4, self._on_timer_probe_tick)
        self._timers.remove_timer("systems_probe_complete")
        self._timers.add_once("systems_probe_complete", 1.2, self._on_timer_probe_complete)
        self._refresh_scheduling_labels()

    def _simulate_rate_limited_input(self) -> None:
        # Simulate rapid slider/typing updates to demonstrate trailing-edge
        # debounce commits and throttled sampling in a realistic release UI path.
        for index in range(12):
            value = index * 10
            self._throttler.call(value)
            self._debouncer.call(f"draft-{value:03d}")
        self._rate_limiter_status = "Burst queued; waiting for throttled sample and debounced commit."
        self._refresh_scheduling_labels()

    def _on_throttled_burst_input(self, value: int) -> None:
        self._throttle_event_count += 1
        self._throttle_last_value = int(value)
        self._rate_limiter_status = f"Throttler sampled value {self._throttle_last_value}"
        self._refresh_scheduling_labels()

    def _on_debounced_burst_commit(self, value: str) -> None:
        self._debounce_commit_count += 1
        self._debounce_last_value = str(value)
        self._rate_limiter_status = (
            f"Debouncer committed {self._debounce_last_value}; last throttled value {self._throttle_last_value}"
        )
        self._refresh_scheduling_labels()

    def _on_timer_probe_tick(self) -> None:
        self._timer_tick_count += 1
        self._timer_last_event = f"heartbeat #{self._timer_tick_count}"

    def _on_timer_probe_complete(self) -> None:
        self._timer_probe_armed = False
        self._timers.remove_timer("systems_probe_heartbeat")
        self._timer_last_event = f"probe completed after {self._timer_tick_count} heartbeat callbacks"

    def _apply_review_profile(self) -> None:
        self._settings_registry.set_value("systems", "profile", "review")
        self._settings_registry.set_value("systems", "autosave", True)
        self._settings_registry.set_value("systems", "parallel_checks", 2)
        self._persistence_last_status = "SettingsRegistry switched to the review workspace profile."
        self._refresh_persistence_labels()

    def _apply_production_profile(self) -> None:
        self._settings_registry.set_value("systems", "profile", "production")
        self._settings_registry.set_value("systems", "autosave", False)
        self._settings_registry.set_value("systems", "parallel_checks", 4)
        self._persistence_last_status = "SettingsRegistry switched to the production workspace profile."
        self._refresh_persistence_labels()

    def _build_workspace_state(self) -> WorkspaceState:
        # Keep the persistence demo focused on settings blocks so users can restore
        # a realistic workspace payload without mutating the live main-scene graph.
        return WorkspaceState(
            active_scene_name=self.scene_name,
            scene_snapshot={},
            settings_blocks={
                block_name: WorkspacePersistenceManager._registry_values(self._settings_registry)
                for block_name in self._workspace_persistence.registered_blocks()
            },
            metadata={
                "profile": self._settings_registry.get_value("systems", "profile"),
                "autosave": self._settings_registry.get_value("systems", "autosave"),
            },
        )

    def _save_workspace_state(self) -> None:
        state = self._build_workspace_state()
        state.save(self._workspace_state_path)
        self._saved_workspace_state = state
        self._persistence_last_report = None
        self._persistence_last_status = f"WorkspaceState saved to {self._workspace_state_path}"
        self._refresh_persistence_labels()

    def _restore_workspace_state(self) -> None:
        state = self._saved_workspace_state
        if state is None and self._workspace_state_path.exists():
            state = WorkspaceState.load(self._workspace_state_path)
        if state is None:
            self._persistence_last_status = "No workspace snapshot saved yet."
            self._refresh_persistence_labels()
            return
        self._saved_workspace_state = state
        if self.demo is None:
            self._persistence_last_status = "Systems demo host is not available for restore."
            self._refresh_persistence_labels()
            return
        self._persistence_last_report = self._workspace_persistence.restore(state, self.demo.app)
        self._persistence_last_status = "WorkspacePersistenceManager restored the saved settings block into the live demo."
        self._refresh_persistence_labels()

    def _refresh_persistence_labels(self) -> None:
        profile = self._settings_registry.get_value("systems", "profile")
        autosave = self._settings_registry.get_value("systems", "autosave")
        checks = self._settings_registry.get_value("systems", "parallel_checks")
        if self.persistence_overview_label is not None:
            self.persistence_overview_label.text = (
                f"WorkspacePersistenceManager blocks={self._workspace_persistence.registered_blocks()} file={self._workspace_state_path.name}"
            )
        if self.persistence_settings_label is not None:
            self.persistence_settings_label.text = (
                f"SettingsRegistry systems/profile={profile} autosave={autosave} parallel_checks={checks}"
            )
        if self.persistence_status_label is not None:
            if self._persistence_last_report is None:
                self.persistence_status_label.text = self._persistence_last_status
            else:
                applied = self._persistence_last_report.get("applied_settings", 0)
                skipped = self._persistence_last_report.get("skipped_settings", 0)
                self.persistence_status_label.text = (
                    f"{self._persistence_last_status} applied={applied} skipped={skipped}"
                )

    def _trigger_particle_burst(self) -> None:
        self._particle_layer.particle_system.burst(self._particle_burst_emitter, count=150)
        self._graphics_dirty_tracker.mark_dirty(Rect(0, 0, self._particle_layer.rect.width, self._particle_layer.rect.height))
        self._refresh_graphics_labels()

    def _build_surface_effect_source(self, size: tuple[int, int]) -> Surface:
        width = max(1, int(size[0]))
        height = max(1, int(size[1]))
        surface = Surface((width, height), pygame.SRCALPHA)
        for y in range(height):
            t = y / max(1, height - 1)
            base = int(34 + 78 * t)
            accent = int(92 + 100 * t)
            surface.fill((base, base + 10, accent), Rect(0, y, width, 1))
        pygame.draw.rect(surface, (255, 255, 255), Rect(8, 8, width // 2, height // 2), border_radius=10)
        pygame.draw.circle(surface, (255, 154, 87), (width - 30, 30), 18)
        pygame.draw.circle(surface, (90, 200, 166), (width - 54, height - 28), 16)
        pygame.draw.line(surface, (20, 22, 30), (12, height - 20), (width - 12, 18), 4)
        pygame.draw.rect(surface, (250, 240, 190), Rect(width // 2 - 18, height // 2 - 10, 36, 22), border_radius=8)
        return surface

    def _cycle_surface_effect(self) -> None:
        if self._surface_effect_source is None:
            return
        self._surface_effect_index = (self._surface_effect_index + 1) % len(self._surface_effect_cycle)
        self._refresh_surface_effect_preview()

    def _refresh_surface_effect_preview(self) -> None:
        if self._surface_effect_source is None:
            return
        effect = self._surface_effect_cycle[self._surface_effect_index]
        source = self._surface_effect_source
        if effect == "blur":
            preview = SurfaceEffects.blur(source, 6)
        elif effect == "greyscale":
            preview = SurfaceEffects.greyscale(source)
        elif effect == "tint":
            preview = SurfaceEffects.tint(source, (255, 168, 92), alpha=110)
        elif effect == "brightness":
            preview = SurfaceEffects.brightness(source, 1.25)
        elif effect == "vignette":
            preview = SurfaceEffects.vignette(source, 0.7)
        else:
            preview = SurfaceEffects.pixelate(source, 8)
        if self._surface_effect_preview is not None:
            self._surface_effect_preview.set_image(preview)
        if self.graphics_surface_effects_label is not None:
            self.graphics_surface_effects_label.text = (
                f"SurfaceEffects preview uses {effect} on a generated scene card; click to cycle effects."
            )

    def _reset_particle_layer(self) -> None:
        self._particle_layer.particle_system.clear()
        self._particle_layer.particle_system.add_emitter(self._particle_ambient_emitter)
        self._particle_layer.particle_system.add_emitter(self._particle_burst_emitter)
        self._graphics_dirty_tracker.mark_dirty(Rect(0, 0, self._particle_layer.rect.width, self._particle_layer.rect.height))
        self._refresh_graphics_labels()

    def _advance_graphics_runtime(self) -> None:
        self._graphics_runtime_step += 1
        phase = self._graphics_runtime_step % 4
        release_node = self._graphics_scene_graph.find("release_stage")
        if release_node is not None:
            release_node.pos = (84.0 + phase * 24.0, 56.0 + (phase % 2) * 14.0)
        self._graphics_camera.pan_screen(10.0, 0.0)
        next_zoom = 1.0 + 0.08 * phase
        self._graphics_camera.set_zoom(next_zoom, anchor_screen=(36.0, 36.0))
        self._graphics_compositor.set_layer_visible("particles", phase != 1)
        self._graphics_compositor.set_layer_opacity("ui", 0.86 if phase in {2, 3} else 1.0)
        self._pan_tile_camera(24, 12, refresh=False)
        self._graphics_dirty_tracker.mark_dirty(Rect(0, 0, self._particle_layer.rect.width, self._particle_layer.rect.height))
        self._render_tile_map_preview()
        self._refresh_graphics_labels()

    def _pan_tile_camera(self, dx: int, dy: int, *, refresh: bool = True) -> None:
        max_x = max(0, self._graphics_tile_map.pixel_width - self._graphics_tile_camera.width)
        max_y = max(0, self._graphics_tile_map.pixel_height - self._graphics_tile_camera.height)
        self._graphics_tile_camera.x = max(0, min(max_x, self._graphics_tile_camera.x + int(dx)))
        self._graphics_tile_camera.y = max(0, min(max_y, self._graphics_tile_camera.y + int(dy)))
        if refresh:
            self._render_tile_map_preview()
            self._refresh_graphics_labels()

    def _advance_graphics_demo(self, dt: float) -> None:
        # Re-sync emitter screen positions to follow window drags.
        graphics_panel = self._tab_panels.get("graphics")
        if graphics_panel is not None:
            bx, by = self._burst_emitter_panel_offset
            ax, ay = self._ambient_emitter_panel_offset
            self._particle_burst_emitter.x = graphics_panel.rect.left + bx
            self._particle_burst_emitter.y = graphics_panel.rect.top + by
            self._particle_ambient_emitter.x = graphics_panel.rect.left + ax
            self._particle_ambient_emitter.y = graphics_panel.rect.top + ay
        self._particle_layer.update_particles(dt)
        self._graphics_dirty_tracker.mark_dirty(Rect(0, 0, self._particle_layer.rect.width, self._particle_layer.rect.height))
        self._render_tile_map_preview()
        self._refresh_graphics_labels()

    def _render_tile_map_preview(self) -> None:
        canvas_control = self.graphics_tile_preview_canvas
        if canvas_control is None:
            return
        canvas_surface = canvas_control.get_canvas_surface()
        canvas_surface.fill((24, 28, 33))
        camera_rect = Rect(self._graphics_tile_camera)
        camera_rect.width = max(1, min(camera_rect.width, self._graphics_tile_map.pixel_width))
        camera_rect.height = max(1, min(camera_rect.height, self._graphics_tile_map.pixel_height))
        self._graphics_tile_map.draw(canvas_surface, camera_rect, offset=(0, 0))

        marker_world_x = camera_rect.left + camera_rect.width // 2
        marker_world_y = camera_rect.top + camera_rect.height // 2
        marker_screen_x = max(0, min(canvas_surface.get_width() - 1, marker_world_x - camera_rect.left))
        marker_screen_y = max(0, min(canvas_surface.get_height() - 1, marker_world_y - camera_rect.top))
        canvas_surface.fill((255, 240, 140), Rect(marker_screen_x - 2, marker_screen_y - 2, 5, 5))
        canvas_control.invalidate()

    def _refresh_graphics_labels(self) -> None:
        if self.graphics_particle_label is not None:
            self.graphics_particle_label.text = (
                f"ParticleSystem emitters={self._particle_layer.particle_system.emitter_count} "
                f"active_particles={self._particle_layer.particle_system.active_particle_count}"
            )
        if self.graphics_layer_label is not None:
            self.graphics_layer_label.text = (
                "ParticleLayer hosts an ambient release trail plus on-demand burst confetti preview."
            )
        if self.graphics_scene_graph_label is not None:
            release_node = self._graphics_scene_graph.find("release_stage")
            if release_node is None:
                self.graphics_scene_graph_label.text = "SceneGraph2D has no release nodes."
            else:
                world_x, world_y, _, _ = release_node.world_transform()
                screen_x, screen_y = self._graphics_camera.world_to_screen(world_x, world_y)
                visible_nodes = len(self._graphics_scene_graph.find_all(visible_only=True))
                self.graphics_scene_graph_label.text = (
                    f"SceneGraph2D/Camera2D nodes={visible_nodes} release_stage_screen=({int(screen_x)}, {int(screen_y)}) "
                    f"zoom={self._graphics_camera.zoom:.2f}"
                )
        if self.graphics_compositor_label is not None:
            dirty_union = self._graphics_dirty_tracker.dirty_union()
            dirty_text = f"{dirty_union.width}x{dirty_union.height}" if dirty_union is not None else "none"
            self.graphics_compositor_label.text = (
                f"SurfaceCompositor layers={self._graphics_compositor.layer_names()} dirty_union={dirty_text}"
            )
        if self.graphics_tile_map_label is not None:
            col_start, col_end, row_start, row_end = self._graphics_tile_map.visible_range(self._graphics_tile_camera)
            visible_tiles = max(0, col_end - col_start) * max(0, row_end - row_start)
            sample_col, sample_row = self._graphics_tile_map.world_to_tile(
                self._graphics_tile_camera.left + 24,
                self._graphics_tile_camera.top + 24,
            )
            sample_tile = self._graphics_tile_map.tile_at(sample_col, sample_row)
            self.graphics_tile_map_label.text = (
                f"TileMap camera=({self._graphics_tile_camera.left},{self._graphics_tile_camera.top}) "
                f"visible_tiles={visible_tiles} sample_tile={sample_tile}"
            )
        if self.graphics_surface_effects_label is not None and not self.graphics_surface_effects_label.text:
            self.graphics_surface_effects_label.text = (
                "SurfaceEffects preview applies image post-processing to a generated scene card."
            )

    def _run_pipeline_demo(self) -> None:
        result = self._pipeline.run(" nightly ").result
        if self.infrastructure_pipeline_label is not None:
            self.infrastructure_pipeline_label.text = f"DataflowPipeline output: {result}"

    def _advance_interaction_state(self) -> None:
        sequence = (
            "pointer_enter",
            "pointer_down",
            "drag_start",
            "pointer_up",
            "cancel",
        )
        event_kind = sequence[self._interaction_event_index % len(sequence)]
        self._interaction_event_index += 1
        changed = self._interaction.handle_event(InteractionContext(event_kind=event_kind))
        if self.infrastructure_interaction_label is not None:
            self.infrastructure_interaction_label.text = (
                f"InteractionStateMachine event={event_kind} changed={changed} phase={self._interaction.phase.name.lower()}"
            )

    def _toggle_schema_example(self) -> None:
        self._schema_use_invalid_value = not self._schema_use_invalid_value
        if self._schema_use_invalid_value:
            self._schema_runtime.set_value("approver", "QA")
            self._schema_runtime.set_value("channel", "beta")
        else:
            self._schema_runtime.set_value("approver", "Mira")
            self._schema_runtime.set_value("channel", "canary")
        self._schema_runtime.validate_all()
        self._refresh_infrastructure_labels()

    def _run_snapshot_migration(self) -> None:
        snapshot = make_snapshot(self._version_v1, {"pipeline": "nightly-gui"})
        migrated = self._snapshot_migrator.migrate(snapshot, self._version_v3)
        if self.infrastructure_migration_label is not None:
            self.infrastructure_migration_label.text = (
                f"SnapshotMigrator {snapshot['schema_version']} -> {migrated['schema_version']} data keys={sorted(migrated['data'].keys())}"
            )

    def _record_theme_invalidation(self) -> None:
        self._theme_invalidation_ticks += 1

    def _trigger_theme_invalidation(self) -> None:
        self._theme_invalidation_bus.trigger_invalidation()
        self._refresh_infrastructure_labels()

    def _bind_virtual_cell(self, cell: _VirtualCell, index: int) -> None:
        cell.index = int(index)

    def _refresh_virtualization_demo(self) -> None:
        self._virtual_scroll_offset = (self._virtual_scroll_offset + 48) % 480
        self._virtual_core.refresh(scroll_offset=self._virtual_scroll_offset, item_count=120)
        self._refresh_infrastructure_labels()

    def _solve_constraint_layout(self) -> None:
        resolved = self._call_to_action_constraint.apply(Rect(0, 0, 220, 34), Rect(0, 0, 960, 540))
        if self.infrastructure_layout_label is not None:
            self.infrastructure_layout_label.text = (
                f"ConstraintLayout call_to_action -> x={resolved.left} y={resolved.top} w={resolved.width} h={resolved.height}"
            )

    def _push_scope_demo(self) -> None:
        with self._scope_stack.push() as child:
            child.bind(self._service_key_channel, "stable")
            api_base = child.get(self._service_key_api_base)
            channel = child.get(self._service_key_channel)
            if self.infrastructure_scope_label is not None:
                self.infrastructure_scope_label.text = (
                    f"ServiceScope child resolved api={api_base} channel={channel}; root channel remains canary"
                )

    def _run_accessibility_demo(self) -> None:
        self._accessibility_cycle += 1
        self._accessibility_pipeline_node.enabled = not self._accessibility_pipeline_node.enabled
        politeness = LivePoliteness.ASSERTIVE if self._accessibility_cycle % 3 == 0 else LivePoliteness.POLITE
        self._accessibility_bus.announce(
            f"Release checklist update {self._accessibility_cycle}",
            politeness=politeness,
        )
        announcements = self._accessibility_bus.consume_announcements()
        if announcements:
            latest = announcements[-1]
            self._accessibility_last_announcement = f"{latest.politeness.value}: {latest.message}"
        self._refresh_infrastructure_labels()

    def _run_audio_demo(self) -> None:
        # Keep this sample resilient in CI/no-audio environments: emit() returns False when unavailable.
        event_name = "systems.notification"
        self._sound_demo_muted = not self._sound_demo_muted
        if self._sound_demo_muted:
            self._sound_event_bus.mute(event_name)
        else:
            self._sound_event_bus.unmute(event_name)
        self._sound_last_emit_ok = self._sound_event_bus.emit(event_name, volume=0.25)
        self._refresh_infrastructure_labels()

    def _sample_telemetry(self) -> None:
        with self._telemetry.span("systems", "infrastructure_sample", {"tab": self.active_tab_key}):
            self._accessibility_tree.snapshot()
        self._telemetry_sample_count = len(self._telemetry.snapshot())
        self._refresh_infrastructure_labels()

    def _refresh_infrastructure_labels(self) -> None:
        if self.infrastructure_pipeline_label is not None and not self.infrastructure_pipeline_label.text:
            self.infrastructure_pipeline_label.text = "DataflowPipeline ready: normalize -> stamp -> route"
        if self.infrastructure_interaction_label is not None and not self.infrastructure_interaction_label.text:
            self.infrastructure_interaction_label.text = (
                f"InteractionStateMachine phase={self._interaction.phase.name.lower()}"
            )
        if self.infrastructure_schema_label is not None:
            errors = [
                *self._schema_runtime.get_errors("channel"),
                *self._schema_runtime.get_errors("approver"),
            ]
            if errors:
                self.infrastructure_schema_label.text = f"SchemaFormRuntime errors: {'; '.join(errors)}"
            else:
                self.infrastructure_schema_label.text = (
                    f"SchemaFormRuntime valid for channel={self._schema_runtime.get_value('channel')} "
                    f"approver={self._schema_runtime.get_value('approver')}"
                )
        if self.infrastructure_migration_label is not None and not self.infrastructure_migration_label.text:
            self.infrastructure_migration_label.text = (
                f"SnapshotMigrator path available: {self._snapshot_migrator.can_migrate(self._version_v1, self._version_v3)}"
            )
        if self.infrastructure_theme_bus_label is not None:
            self.infrastructure_theme_bus_label.text = (
                f"ThemeInvalidationBus callbacks triggered {self._theme_invalidation_ticks} times"
            )
        if self.infrastructure_virtualization_label is not None:
            first, last = self._virtual_window.visible_range()
            self.infrastructure_virtualization_label.text = (
                f"VirtualizationCore visible range [{first}, {last}] at scroll={self._virtual_scroll_offset}; pool={self._virtual_pool.pool_size}"
            )
        if self.infrastructure_layout_label is not None and not self.infrastructure_layout_label.text:
            self.infrastructure_layout_label.text = "ConstraintLayout ready with container-relative constraints"
        if self.infrastructure_scope_label is not None and not self.infrastructure_scope_label.text:
            self.infrastructure_scope_label.text = (
                f"ScopeStack root api={self._scope_stack.root.get(self._service_key_api_base)} "
                f"channel={self._scope_stack.root.get(self._service_key_channel)}"
            )
        if self.infrastructure_runtime_label is not None:
            self.infrastructure_runtime_label.text = (
                " | ".join(
                    (
                        f"AccessibilityTree nodes={len(self._accessibility_tree)} last='{self._accessibility_last_announcement}'",
                        f"SoundEventBus events={self._sound_event_bus.registered_event_names()} muted={self._sound_demo_muted} played={self._sound_last_emit_ok}",
                        f"TelemetryCollector samples={self._telemetry_sample_count}",
                    )
                )
            )
