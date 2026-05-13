"""Systems demo window integrated into the gui_do main scene."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tempfile

from pygame import Rect, Surface

from gui_do import (
    AppStateStore,
    AnchoredWindowSpec,
    AsyncFieldValidator,
    AsyncFormValidator,
    ArrowBoxControl,
    ButtonControl,
    ConstraintAttr,
    ConstraintLayoutEngine,
    ConstraintSet,
    Camera2D,
    CanvasControl,
    CellCaretLayout,
    CollectionView,
    CollectionViewQuery,
    CommandHistory,
    CooperativeScheduler,
    DataCache,
    DataflowPipeline,
    DirtyRegionTracker,
    DropdownControl,
    DropdownOption,
    Emitter,
    FieldGraphSchema,
    FieldSchema,
    Feature,
    FormField,
    FrameTimer,
    InteractionContext,
    InteractionStateMachine,
    LayoutConstraint,
    LabelControl,
    ListViewControl,
    MeasurePolicy,
    MigrationRegistry,
    MigrationStep,
    PanelControl,
    ParticleLayer,
    PipelineStage,
    RecyclePool,
    SchemaFormRuntime,
    SchemaVersion,
    SceneGraph2D,
    ScopeStack,
    ScopedTheme,
    ScopedThemeManager,
    ServiceKey,
    SettingsRegistry,
    Sleep,
    SnapshotMigrator,
    StateMachine,
    StateTransaction,
    SurfaceCompositor,
    TabControl,
    TabItem,
    TaskScheduler,
    TextInputControl,
    ThemeManager,
    ThemeInvalidationBus,
    TileMap,
    TileSet,
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
)
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

        data_panel = feature.build_data_panel(panel_rect)
        validation_panel = feature.build_validation_panel(panel_rect)
        history_panel = feature.build_history_panel(panel_rect)
        theme_panel = feature.build_theme_panel(panel_rect)
        state_panel = feature.build_state_panel(panel_rect)
        infrastructure_panel = feature.build_infrastructure_panel(panel_rect)
        scheduling_panel = feature.build_scheduling_panel(panel_rect)
        persistence_panel = feature.build_persistence_panel(panel_rect)
        graphics_panel = feature.build_graphics_panel(panel_rect)
        for panel in (
            data_panel,
            validation_panel,
            history_panel,
            theme_panel,
            state_panel,
            infrastructure_panel,
            scheduling_panel,
            persistence_panel,
            graphics_panel,
        ):
            self.add_control(panel)

        feature._tab_panels = {
            "data": data_panel,
            "validation": validation_panel,
            "history": history_panel,
            "theme": theme_panel,
            "state": state_panel,
            "infrastructure": infrastructure_panel,
            "scheduling": scheduling_panel,
            "persistence": persistence_panel,
            "graphics": graphics_panel,
        }
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
        ("persistence", "Persistence"),
        ("graphics", "Graphics"),
    )
    PANEL_PADDING_X = 16
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
        self._constraint_engine = ConstraintLayoutEngine()
        self._constraint_engine.set_initial_rect("call_to_action", Rect(0, 0, 220, 34))
        self._scope_stack = ScopeStack()
        self._service_key_api_base: ServiceKey[str] = ServiceKey("api_base")
        self._service_key_channel: ServiceKey[str] = ServiceKey("release_channel")
        self._scope_stack.root.bind(self._service_key_api_base, "https://deploy.internal")
        self._scope_stack.root.bind(self._service_key_channel, "canary")

        self.infrastructure_pipeline_label = None
        self.infrastructure_interaction_label = None
        self.infrastructure_schema_label = None
        self.infrastructure_migration_label = None
        self.infrastructure_theme_bus_label = None
        self.infrastructure_virtualization_label = None
        self.infrastructure_layout_label = None
        self.infrastructure_scope_label = None

        self._task_scheduler = TaskScheduler(max_workers=1)
        self._task_job_index = 0
        self._task_last_summary = "TaskScheduler idle: no background jobs queued yet."
        self._task_last_failure = ""
        self._cooperative_scheduler = CooperativeScheduler()
        self._rollout_handle = None
        self._rollout_phase = "Idle"
        self.scheduling_task_label = None
        self.scheduling_rollout_label = None

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
        self._task_scheduler.update()
        self._cooperative_scheduler.update(dt)
        if self.active_tab_key == "validation":
            self._form_validator.update(dt)
            self._refresh_validation_labels()
        elif self.active_tab_key == "scheduling":
            self._refresh_scheduling_labels()
        elif self.active_tab_key == "graphics":
            self._advance_graphics_demo(dt)

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
        elif next_key == "persistence":
            self._refresh_persistence_labels()
        elif next_key == "graphics":
            self._refresh_graphics_labels()

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
        slots = CellCaretLayout.split_columns(
            row_bounds,
            count=len(controls),
            gap=self.BUTTON_ROW_GAP,
            min_width=1,
        )
        for control, slot in zip(controls, slots):
            control.rect = Rect(0, 0, slot.width, slot.height)
            panel.add_at(control, slot.left, slot.top)

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

    def build_data_panel(self, rect: Rect) -> PanelControl:
        panel = PanelControl("systems_data_panel", Rect(rect), draw_background=False)
        left_w = max(280, int(rect.width * 0.58))
        right_x = left_w + 20
        right_w = max(180, rect.width - right_x - self.PANEL_PADDING_X)
        action_button_w = 120
        action_button_gap = 8
        action_button_right_pad = 12

        panel.add_at(LabelControl("systems_data_filter_label", Rect(0, 0, 72, 28), "Status", align="left"), 0, 0)
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
        panel.add_at(self.data_filter_dropdown, 80, 0)

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
        panel.add_at(self.data_list, 0, 44)

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
        panel.add_at(self.data_summary_label, right_x, 52)
        panel.add_at(self.data_cache_label, right_x, 88)
        panel.add_at(self.data_detail_label, right_x, 132)

        self._backlog_unsub = self.data_list.bind_collection_view(
            self._backlog_view,
            on_refresh=self._on_backlog_view_refreshed,
        )
        self._refresh_backlog_view()
        return panel

    def build_validation_panel(self, rect: Rect) -> PanelControl:
        panel = PanelControl("systems_validation_panel", Rect(rect), draw_background=False)
        panel.add_at(LabelControl("systems_validation_name_label", Rect(0, 0, 180, 28), "Pipeline Name", align="left"), 0, 0)
        self.validation_name_input = TextInputControl(
            "systems_validation_name",
            Rect(0, 0, min(320, rect.width - 16), 32),
            value=self._deployment_name_field.value.value,
            placeholder="nightly-gui",
            on_change=self._on_deployment_name_changed,
        )
        panel.add_at(self.validation_name_input, 0, 30)

        panel.add_at(LabelControl("systems_validation_env_label", Rect(0, 0, 180, 28), "Target Environment", align="left"), 0, 82)
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
        panel.add_at(self.validation_environment_dropdown, 0, 112)

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
            "Use Suggested Name",
            self._apply_suggested_name,
            style="round",
        )
        self._add_button_rows(panel, rect, 156, [run_checks, suggested])

        self.validation_state_label = LabelControl(
            "systems_validation_state",
            Rect(0, 0, rect.width, 28),
            "Form state pending.",
            align="left",
        )
        self.validation_local_label = LabelControl(
            "systems_validation_local",
            Rect(0, 0, rect.width, 28),
            "Local checks pending.",
            align="left",
        )
        self.validation_async_label = LabelControl(
            "systems_validation_async",
            Rect(0, 0, rect.width, 28),
            "Async availability check pending.",
            align="left",
        )
        panel.add_at(self.validation_state_label, 0, 216)
        panel.add_at(self.validation_local_label, 0, 252)
        panel.add_at(self.validation_async_label, 0, 288)
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
        panel.add_at(self.history_current_label, 0, label_top + 8)
        panel.add_at(self.history_undo_label, 0, label_top + 44)
        panel.add_at(self.history_redo_label, 0, label_top + 80)
        self._refresh_history_labels()
        return panel

    def build_theme_panel(self, rect: Rect) -> PanelControl:
        panel = PanelControl("systems_theme_panel", Rect(rect), draw_background=False)
        panel.add_at(LabelControl("systems_theme_select_label", Rect(0, 0, 128, 28), "Theme", align="left"), 0, 0)
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
        self._place_row_controls(
            panel,
            self._row_bounds(rect, 30),
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
        panel.add_at(self.theme_state_label, 0, 92)
        panel.add_at(self.theme_scope_label, 0, 128)
        panel.add_at(self.theme_resolved_label, 0, 164)
        self._refresh_theme_labels()
        return panel

    def build_state_panel(self, rect: Rect) -> PanelControl:
        panel = PanelControl("systems_state_panel", Rect(rect), draw_background=False)
        panel.add_at(LabelControl("systems_state_context_title", Rect(0, 0, 120, 28), "Undo Context", align="left"), 0, 0)
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
        panel.add_at(self.state_context_dropdown, 130, 0)

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
                ButtonControl(
                    "systems_state_route_cycle",
                    Rect(0, 0, 170, 32),
                    "Cycle Route Stack",
                    self._cycle_release_router,
                    style="round",
                ),
            ],
        )

        self.state_store_label = LabelControl("systems_state_store", Rect(0, 0, rect.width, 28), "", align="left")
        self.state_readiness_label = LabelControl("systems_state_readiness", Rect(0, 0, rect.width, 28), "", align="left")
        self.state_context_label = LabelControl("systems_state_context_status", Rect(0, 0, rect.width, 28), "", align="left")
        self.state_machine_label = LabelControl("systems_state_machine_status", Rect(0, 0, rect.width, 28), "", align="left")
        self.state_router_label = LabelControl("systems_state_router_status", Rect(0, 0, rect.width, 28), "", align="left")
        panel.add_at(self.state_store_label, 0, state_label_top + 8)
        panel.add_at(self.state_readiness_label, 0, state_label_top + 44)
        panel.add_at(self.state_context_label, 0, state_label_top + 80)
        panel.add_at(self.state_machine_label, 0, state_label_top + 116)
        panel.add_at(self.state_router_label, 0, state_label_top + 152)
        self._refresh_state_labels()
        return panel

    def build_infrastructure_panel(self, rect: Rect) -> PanelControl:
        panel = PanelControl("systems_infrastructure_panel", Rect(rect), draw_background=False)
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
            ],
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
        panel.add_at(self.infrastructure_pipeline_label, 0, infrastructure_label_top + 8)
        panel.add_at(self.infrastructure_interaction_label, 0, infrastructure_label_top + 44)
        panel.add_at(self.infrastructure_schema_label, 0, infrastructure_label_top + 80)
        panel.add_at(self.infrastructure_migration_label, 0, infrastructure_label_top + 116)
        panel.add_at(self.infrastructure_theme_bus_label, 0, infrastructure_label_top + 152)
        panel.add_at(self.infrastructure_virtualization_label, 0, infrastructure_label_top + 188)
        panel.add_at(self.infrastructure_layout_label, 0, infrastructure_label_top + 224)
        panel.add_at(self.infrastructure_scope_label, 0, infrastructure_label_top + 260)
        self._refresh_infrastructure_labels()
        return panel

    def build_scheduling_panel(self, rect: Rect) -> PanelControl:
        panel = PanelControl("systems_scheduling_panel", Rect(rect), draw_background=False)
        self._add_button_rows(
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
            ],
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
        panel.add_at(self.scheduling_task_label, 0, 56)
        panel.add_at(self.scheduling_rollout_label, 0, 92)
        self._refresh_scheduling_labels()
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
        panel.add_at(self.persistence_overview_label, 0, persistence_label_top + 8)
        panel.add_at(self.persistence_settings_label, 0, persistence_label_top + 44)
        panel.add_at(self.persistence_status_label, 0, persistence_label_top + 80)
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
        self._particle_layer.rect = Rect(0, 0, preview_width, 180)
        self._graphics_compositor.resize((preview_width, 180))
        self._graphics_camera.viewport_rect = Rect(0, 0, preview_width, 180)
        self._graphics_tile_camera.size = (tile_preview_width, tile_preview_h)

        # Left column particle stack.
        particle_layer_top = buttons_top + 32 + self.BUTTON_ROW_SPACING
        panel.add_at(self._particle_layer, left_col_x, particle_layer_top)
        # Store panel-local offsets for the emitters so they can be re-synced
        # to screen space each frame (emitters are plain dataclasses and won't
        # move automatically when the window is dragged).
        # Emitters align to the horizontal midpoint of the Burst/Reset button row.
        _burst_dx = left_col_x + left_col_width / 2
        labels_top = particle_layer_top + 180 + 12
        emitter_padding = 12
        _burst_dy = labels_top - emitter_padding
        _ambient_dy = _burst_dy
        self._burst_emitter_panel_offset = (_burst_dx, _burst_dy)
        _ambient_dx = _burst_dx
        self._ambient_emitter_panel_offset = (_ambient_dx, _ambient_dy)
        # Set initial positions (panel.rect matches rect at build time).
        self._particle_burst_emitter.x = rect.left + _burst_dx
        self._particle_burst_emitter.y = rect.top + _burst_dy
        self._particle_ambient_emitter.x = rect.left + _ambient_dx
        self._particle_ambient_emitter.y = rect.top + _ambient_dy
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

        panel.add_at(self.graphics_particle_label, left_col_x, labels_top)
        panel.add_at(self.graphics_layer_label, left_col_x, labels_top + 36)
        panel.add_at(self.graphics_scene_graph_label, left_col_x, labels_top + 72)
        panel.add_at(self.graphics_compositor_label, left_col_x, labels_top + 108)

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
        panel.add_at(tile_preview_label, tile_preview_x, right_label_top)
        panel.add_at(nav_cluster_label, nav_cluster_x, right_label_top)
        panel.add_at(self.graphics_tile_preview_canvas, tile_preview_x, tile_preview_top)
        panel.add_at(nav_cluster, nav_cluster_x, nav_cluster_y)
        panel.add_at(self.graphics_tile_map_label, tile_preview_x, tile_preview_top + tile_preview_h + 12)
        nav_cluster.add_at(
            ArrowBoxControl(
                "systems_graphics_nav_left",
                Rect(0, 0, 44, 44),
                180,
                on_activate=lambda: self._pan_tile_camera(-24, 0),
            ),
            2,
            2,
        )
        nav_cluster.add_at(
            ArrowBoxControl(
                "systems_graphics_nav_up",
                Rect(0, 0, 44, 44),
                90,
                on_activate=lambda: self._pan_tile_camera(0, -24),
            ),
            50,
            2,
        )
        nav_cluster.add_at(
            ArrowBoxControl(
                "systems_graphics_nav_down",
                Rect(0, 0, 44, 44),
                270,
                on_activate=lambda: self._pan_tile_camera(0, 24),
            ),
            2,
            50,
        )
        nav_cluster.add_at(
            ArrowBoxControl(
                "systems_graphics_nav_right",
                Rect(0, 0, 44, 44),
                0,
                on_activate=lambda: self._pan_tile_camera(24, 0),
            ),
            50,
            50,
        )

        self._render_tile_map_preview()
        self._refresh_graphics_labels()
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
        constraints = ConstraintSet()
        constraints.add(LayoutConstraint("call_to_action", ConstraintAttr.LEFT, 0.1, is_fraction=True))
        constraints.add(LayoutConstraint("call_to_action", ConstraintAttr.TOP, 84))
        constraints.add(LayoutConstraint("call_to_action", ConstraintAttr.WIDTH, 320))
        solved = self._constraint_engine.solve(constraints, Rect(0, 0, 960, 540))
        resolved = solved["call_to_action"]
        if self.infrastructure_layout_label is not None:
            self.infrastructure_layout_label.text = (
                f"ConstraintLayoutEngine call_to_action -> x={resolved.left} y={resolved.top} w={resolved.width} h={resolved.height}"
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
            self.infrastructure_layout_label.text = "ConstraintLayoutEngine ready with container-relative constraints"
        if self.infrastructure_scope_label is not None and not self.infrastructure_scope_label.text:
            self.infrastructure_scope_label.text = (
                f"ScopeStack root api={self._scope_stack.root.get(self._service_key_api_base)} "
                f"channel={self._scope_stack.root.get(self._service_key_channel)}"
            )
