"""New Systems demo feature — showcases the new gui_do systems.

Demonstrates: SortFilterProxySource,
LocaleRegistry/StringTable, InputMap/InputBinding, ResponsiveLayout/Breakpoint,
TextFlow/TextSpan, EventRecorder/EventPlayback/RecordedEvent,
PropertyRegistry/PropertyDescriptor/ui_property, SceneSnapshot/NodeSnapshot,
and SceneSpatialIndex.
"""

from __future__ import annotations

try:
    from demo_features._import_bootstrap import ensure_repo_root_on_path
except ModuleNotFoundError:
    from _import_bootstrap import ensure_repo_root_on_path

ensure_repo_root_on_path()

from typing import Optional

import pygame
from pygame import Rect

from gui_do import (
    AnimatedImageControl,
    Breakpoint,
    ButtonControl,
    CanvasControl,
    CooperativeScheduler,
    CoroutineHandle,
    DataCache,
    DiffInsert,
    DiffMove,
    DiffRemove,
    DockPane,
    DockTabs,
    DockWorkspace,
    DockWorkspacePanel,
    Emitter,
    EventPlayback,
    EventRecorder,
    FixedItemSource,
    FlowItem,
    FlowLayout,
    FrameAnimation,
    FrameTimer,
    InputMap,
    LabelControl,
    ListDiff,
    ListDiffCalculator,
    ListItem,
    LocaleRegistry,
    Pause,
    ParticleLayer,
    ParticleSystem,
    ProgressBarControl,
    PropertyDescriptor,
    PropertyInspectorModel,
    PropertyInspectorPanel,
    property_registry,
    RecordedEvent,
    ResponsiveLayout,
    RoutedFeature,
    SceneSpatialIndex,
    SceneSnapshot,
    ShortcutHelpOverlay,
    Sleep,
    SortFilterProxySource,
    SpriteSheet,
    StringTable,
    TabPanelManager,
    TextFlow,
    TextInputControl,
    TextMatch,
    TextSearcher,
    TextSpan,
    TileMap,
    TileSet,
    ToggleControl,
    ui_property,
    WaitUntil,
    WindowControl,
)
from gui_do import set_window_visible_state
from gui_do.controls.chrome.window_presenter import WindowPresenter
from gui_do.features.data_driven_runtime import (
    ActiveTabUpdateRouter,
    bind_routed_feature_lifecycle,
    RoutedRuntimeSpec,
    RoutedFeatureLifecycleSpec,
    ShortcutOverlaySpec,
    TabbedPresenterSpec,
    bind_input_map_actions,
    AnchoredWindowSpec,
    build_tab_builder_specs,
    create_feature_presented_window,
    initialize_locale_registry,
    PresenterButtonSpec,
    PresenterLabelSpec,
    register_descriptors,
    register_tab_update_handlers,
    setup_feature_presenter_tabs_from_window_content,
    TabLayoutContext,
)

_TAB_H = 36

_SYSTEMS_WINDOW_SPEC = AnchoredWindowSpec(
    control_id="systems_window",
    title="System",
    size=(820, 590),
    anchor="top_left",
    margin=(24, 92),
    use_frame_backdrop=True,
)

_SYSTEMS_TAB_ENTRIES = (
    ("filter", "Filter"),
    ("locale", "Locale"),
    ("input", "Input"),
    ("event", "Event"),
    ("inspect", "Inspect"),
    ("props", "Props"),
    ("dock", "Dock"),
    ("particle", "Particle"),
    ("sprite", "Sprite"),
    ("sched", "Sched"),
    ("tilemap", "TileMap"),
    ("progress", "Progress"),
    ("flow", "Flow"),
    ("search", "Search"),
    ("listdiff", "ListDiff"),
    ("cache", "Cache"),
    ("shortcuts", "Shortcuts"),
)
_SYSTEMS_TAB_SPECS = build_tab_builder_specs(_SYSTEMS_TAB_ENTRIES)

_SYSTEMS_TABBED_PRESENTER_SPEC = TabbedPresenterSpec(
    control_id="nsdf_tab",
    selected_key="filter",
    tab_height=_TAB_H,
    tab_rows=2,
    padding=0,
    min_content_height=60,
)

_SYSTEMS_RUNTIME_SPEC = RoutedRuntimeSpec(
    scene_name="main",
    shortcut_overlays=(
        ShortcutOverlaySpec(
            attr_name="_shortcut_overlay",
            action_registry_attr="action_registry",
            width=560,
            height=400,
        ),
    ),
)

_SYSTEMS_LIFECYCLE_SPEC = RoutedFeatureLifecycleSpec(
    runtime_spec=_SYSTEMS_RUNTIME_SPEC,
    runtime_spec_attr_name="_runtime_spec",
    scheduler_attr_name="scheduler",
)

_LOCALE_TABLE_SPECS = (
    (
        "en",
        {
            "greeting": "Hello, World!",
            "description": "gui_do is a pygame UI toolkit.",
            "feature_count": "New systems added this session: 10.",
        },
    ),
    (
        "es",
        {
            "greeting": "\u00a1Hola, Mundo!",
            "description": "gui_do es un kit de herramientas de UI para pygame.",
            "feature_count": "Sistemas nuevos esta sesi\u00f3n: 10.",
        },
    ),
    (
        "fr",
        {
            "greeting": "Bonjour, le Monde!",
            "description": "gui_do est une bo\u00eete \u00e0 outils UI pour pygame.",
            "feature_count": "Nouveaux syst\u00e8mes cette session: 10.",
        },
    ),
)

_LOCALE_BUTTON_SPECS = (
    ("en", "EN"),
    ("es", "ES"),
    ("fr", "FR"),
)

_INPUT_DECLARE_SPECS = (
    ("move_up", pygame.K_UP, "Move Up"),
    ("move_down", pygame.K_DOWN, "Move Down"),
    ("move_left", pygame.K_LEFT, "Move Left"),
    ("move_right", pygame.K_RIGHT, "Move Right"),
)

_INPUT_REMAP_BINDINGS = (
    (pygame.K_w, "move_up"),
    (pygame.K_s, "move_down"),
    (pygame.K_a, "move_left"),
    (pygame.K_d, "move_right"),
)

_INPUT_DEFAULT_BINDINGS = (
    (pygame.K_UP, "move_up"),
    (pygame.K_DOWN, "move_down"),
    (pygame.K_LEFT, "move_left"),
    (pygame.K_RIGHT, "move_right"),
)

_FILTER_ITEM_LABELS = (
    "Apple",
    "Apricot",
    "Banana",
    "Blueberry",
    "Cherry",
    "Grape",
    "Lemon",
    "Mango",
    "Orange",
    "Peach",
)

_FILTER_TAB_LABEL_SPECS = (
    PresenterLabelSpec(
        "nsdf_filter_info", 20,
        "SortFilterProxySource wraps any VirtualItemSource with reactive filter + sort.",
        advance=28,
    ),
    PresenterLabelSpec("nsdf_filter_lbl", 26, "Filter:", width=60, advance=0),
)

_FILTER_INPUT_SPEC = {
    "control_id": "nsdf_filter_input",
    "x_offset": 68,
    "width": 200,
    "height": 28,
    "placeholder": "type prefix...",
    "advance": 36,
}

_FILTER_SORT_TOGGLE_SPEC = {
    "control_id": "nsdf_sort_toggle",
    "width": 130,
    "height": 28,
    "off_text": "Sort: A→Z",
    "on_text": "Sort: Z→A",
    "pushed": False,
    "style": "round",
    "advance": 38,
}

_FILTER_RESULT_TITLE_SPEC = PresenterLabelSpec(
    "nsdf_filter_result_title", 20, "Proxy output:", advance=24)

_FILTER_RESULT_LABEL_SPEC = {
    "control_id": "nsdf_filter_result_lbl",
    "min_height": 40,
    "text": "",
}

_LOCALE_TAB_LABEL_SPECS = (
    PresenterLabelSpec("nsdf_locale_lbl", 26, "Locale:", width=80, advance=0),
    PresenterLabelSpec(
        "nsdf_canvas_lbl", 20, "TextFlow rendering (word-wrapped, mixed-style):", advance=24),
)

_LOCALE_BUTTON_LAYOUT_SPEC = {
    "x_offset": 90,
    "step": 60,
    "width": 52,
    "height": 28,
    "advance": 36,
}

_LOCALE_GREETING_LABEL_SPEC = {
    "control_id": "nsdf_greeting_lbl",
    "height": 26,
    "advance": 34,
}

_LOCALE_TEXT_CANVAS_SPEC = {
    "control_id": "nsdf_text_canvas",
    "min_height": 60,
    "text_flow_horizontal_padding": 16,
    "line_spacing": 3,
}

_INPUT_TAB_HEADER_LABEL_SPECS = (
    PresenterLabelSpec("nsdf_input_title", 22, "InputMap — declared action bindings:", advance=26),
    PresenterLabelSpec("nsdf_resp_title", 22,
        "ResponsiveLayout — breakpoints based on window width:", advance=26),
)

_INPUT_BINDING_LABEL_SPEC = {
    "control_id_prefix": "nsdf_binding_",
    "height": 22,
    "advance": 23,
    "text_template": "  {label}: {key_name}",
}

_INPUT_ACTION_BUTTON_SPECS = (
    PresenterButtonSpec("nsdf_input_remap_btn", 150, 28, "Remap: W/A/S/D",
        "_remap_bindings", advance=36),
    PresenterButtonSpec("nsdf_input_reset_btn", 150, 28, "Reset to Arrows",
        "_reset_bindings", advance=44),
)

_INPUT_LAYOUT_STATUS_LABEL_SPEC = PresenterLabelSpec(
    "nsdf_layout_lbl", 22, "Active breakpoint: (updating...)")

_INPUT_BREAKPOINT_SPECS = (
    ("narrow", 0),
    ("standard", 600),
    ("wide", 900),
)

# ---------------------------------------------------------------------------
# Event tab specs
# ---------------------------------------------------------------------------

_EVENT_INFO_LABEL_SPEC = PresenterLabelSpec(
    "nsdf_evt_info", 20,
    "EventRecorder captures GuiEvents; EventPlayback replays them via a handler.",
    advance=28,
)
_EVENT_STATUS_LABEL_SPEC = PresenterLabelSpec(
    "nsdf_evt_status", 22, "Status: Idle \u2014 0 events recorded", advance=30)
_EVENT_LOG_TITLE_SPEC = PresenterLabelSpec("nsdf_evt_log_title", 20, "Event log:", advance=24)
_EVENT_LOG_LABEL_SPEC = PresenterLabelSpec("nsdf_evt_log", 40, "No events recorded yet.")
_EVENT_BUTTON_ROW_HANDLER_ATTRS = (
    ("nsdf_evt_record", "Start Rec.", "_start_recording"),
    ("nsdf_evt_stop", "Stop", "_stop_recording"),
    ("nsdf_evt_simulate", "Sim. Events", "_simulate_events"),
    ("nsdf_evt_play", "Play Back", "_start_playback"),
)
_EVENT_BUTTON_ROW_GEOMETRY = {"height": 28, "gap": 8, "width": 120, "advance": 40}

# ---------------------------------------------------------------------------
# Inspect tab specs
# ---------------------------------------------------------------------------

_INSPECT_HEADER_LABEL_SPECS = (
    PresenterLabelSpec("nsdf_prop_title", 22,
        "PropertyRegistry \u2014 registered descriptors for ButtonControl:", advance=26),
    PresenterLabelSpec("nsdf_snap_title", 22,
        "SceneSnapshot \u2014 capture & restore window rect:", advance=26),
    PresenterLabelSpec("nsdf_spatial_title", 22,
        "SceneSpatialIndex \u2014 build from scene, then hit-test:", advance=26),
)
_INSPECT_SNAPSHOT_BUTTON_SPECS = (
    PresenterButtonSpec("nsdf_snap_capture", 110, 28, "Capture",
        "_capture_snapshot", advance=0),
    PresenterButtonSpec("nsdf_snap_restore", 110, 28, "Restore",
        "_restore_snapshot", advance=36, x_offset=118),
)
_INSPECT_SNAPSHOT_LABEL_SPEC = PresenterLabelSpec(
    "nsdf_snap_label", 22, "No snapshot captured yet.", advance=30)
_INSPECT_SPATIAL_BUTTON_SPEC = PresenterButtonSpec(
    "nsdf_spatial_build", 160, 28, "Build & Query Center",
    "_build_and_query_spatial", advance=36)
_INSPECT_SPATIAL_LABEL_SPEC = PresenterLabelSpec(
    "nsdf_spatial_label", 22, "Press 'Build & Query Center' to run.")

# ---------------------------------------------------------------------------
# Props tab specs
# ---------------------------------------------------------------------------

_PROPS_HEADER_LABEL_SPECS = (
    PresenterLabelSpec("nsdf_props_title", 22,
        "PropertyInspectorPanel \u2014 inspect _DemoInspectable properties:", advance=28),
    PresenterLabelSpec("nsdf_props_hint", 20,
        "Click a property row to select it. Use refresh to re-read values.", advance=26),
)
_PROPS_SELECTED_LABEL_SPEC = PresenterLabelSpec(
    "nsdf_prop_selected", 20, "Select a property above\u2026", advance=26)
_PROPS_REFRESH_BUTTON_SPEC = PresenterButtonSpec(
    "nsdf_props_refresh", 100, 28, "Refresh", "_refresh_prop_inspector")

# ---------------------------------------------------------------------------
# Inspect descriptor display specs
# ---------------------------------------------------------------------------

_BUTTON_DESCRIPTOR_SPECS = (
    ("visible", "Visible", "bool", "Appearance"),
    ("enabled", "Enabled", "bool", "Behaviour"),
    ("text", "Label Text", "str", "Content"),
)


# ---------------------------------------------------------------------------
# Inspectable demo target
# ---------------------------------------------------------------------------

class _DemoInspectable:
    """Simple object decorated with ``@ui_property`` for PropertyInspectorPanel demo."""

    def __init__(self) -> None:
        self._opacity: float = 1.0
        self._speed: int = 50
        self._label: str = "demo"
        self._active: bool = True

    @property
    @ui_property(label="Opacity", type="float", min=0.0, max=1.0, group="Appearance")
    def opacity(self) -> float:
        return self._opacity

    @opacity.setter
    def opacity(self, v: float) -> None:
        self._opacity = float(v)

    @property
    @ui_property(label="Speed", type="int", min=0, max=200, group="Behaviour")
    def speed(self) -> int:
        return self._speed

    @speed.setter
    def speed(self, v: int) -> None:
        self._speed = int(v)

    @property
    @ui_property(label="Label", type="str", group="Content")
    def label(self) -> str:
        return self._label

    @label.setter
    def label(self, v: str) -> None:
        self._label = str(v)

    @property
    @ui_property(label="Active", type="bool", group="Behaviour")
    def active(self) -> bool:
        return self._active

    @active.setter
    def active(self, v: bool) -> None:
        self._active = bool(v)


class SystemsDemoFeature(RoutedFeature):
    """Demonstrates all 10 new gui_do systems in a tabbed window."""

    HOST_REQUIREMENTS = {
        "build": (
            "app",
            "root",
        ),
        "bind_runtime": (
            "app",
        ),
    }

    def __init__(self) -> None:
        super().__init__("systems_demo", scene_name="main")
        self.window: Optional[WindowControl] = None
        self._active_tab: str = "filter"
        self._tabs = TabPanelManager()
        self._frame_timer = FrameTimer()
        self._tab_updates = ActiveTabUpdateRouter()

        # Filter tab
        self._proxy: Optional[SortFilterProxySource] = None
        self._filter_label: Optional[LabelControl] = None

        # Locale tab
        self._locale_registry: Optional[LocaleRegistry] = None
        self._greeting_label: Optional[LabelControl] = None
        self._text_flow: Optional[TextFlow] = None
        self._text_canvas: Optional[CanvasControl] = None
        self._text_flow_dirty: bool = True

        # Input tab
        self._input_map: Optional[InputMap] = None
        self._binding_labels: list = []
        self._responsive: Optional[ResponsiveLayout] = None
        self._layout_label: Optional[LabelControl] = None

        # Event tab
        self._recorder: Optional[EventRecorder] = None
        self._playback: Optional[EventPlayback] = None
        self._event_status_label: Optional[LabelControl] = None
        self._event_log_label: Optional[LabelControl] = None
        self._recorded_events: list = []

        # Inspect tab
        self._snapshot: Optional[SceneSnapshot] = None
        self._snapshot_label: Optional[LabelControl] = None
        self._spatial_index: Optional[SceneSpatialIndex] = None
        self._spatial_label: Optional[LabelControl] = None
        self._main_scene = None

        # Props tab — PropertyInspectorPanel demo
        self._demo_inspectable = _DemoInspectable()
        self._prop_inspector_panel: Optional[PropertyInspectorPanel] = None
        self._prop_selected_label: Optional[LabelControl] = None

        # Dock tab — DockWorkspacePanel demo
        self._dock_workspace: Optional[DockWorkspace] = None
        self._dock_panel: Optional[DockWorkspacePanel] = None
        self._dock_active_label: Optional[LabelControl] = None
        self._dock_model_label: Optional[LabelControl] = None

        # Particle tab
        self._particle_system: Optional[ParticleSystem] = None
        self._particle_layer: Optional[ParticleLayer] = None
        self._particle_canvas: Optional[CanvasControl] = None
        self._particle_count_label: Optional[LabelControl] = None

        # Sprite tab
        self._sprite_anim: Optional[FrameAnimation] = None
        self._sprite_ctrl: Optional[AnimatedImageControl] = None

        # Scheduler tab
        self._scheduler: Optional[CooperativeScheduler] = None
        self._sched_handle: Optional[CoroutineHandle] = None
        self._sched_log_label: Optional[LabelControl] = None
        self._sched_step_label: Optional[LabelControl] = None
        self._sched_log: list = []

        # TileMap tab
        self._tile_map: Optional[TileMap] = None
        self._tile_canvas: Optional[CanvasControl] = None
        self._tile_dirty: bool = True

        # Progress tab
        self._progress_bar: Optional[ProgressBarControl] = None
        self._progress_indeterminate: Optional[ProgressBarControl] = None
        self._progress_label: Optional[LabelControl] = None

        # Flow tab
        self._flow_layout: Optional[FlowLayout] = None
        self._flow_result_label: Optional[LabelControl] = None
        self._flow_items: list = []

        # Search tab
        self._searcher: Optional[TextSearcher] = None
        self._search_result_label: Optional[LabelControl] = None
        self._search_input: Optional[TextInputControl] = None

        # ListDiff tab
        self._listdiff_old: list = ["Alpha", "Beta", "Gamma", "Delta"]
        self._listdiff_new: list = ["Beta", "Gamma", "Epsilon", "Delta", "Zeta"]
        self._listdiff_result_label: Optional[LabelControl] = None

        # Cache tab
        self._cache: Optional[DataCache] = None
        self._cache_stats_label: Optional[LabelControl] = None

        # Shortcuts tab
        self._shortcut_overlay: Optional[ShortcutHelpOverlay] = None
        self._shortcut_info_label: Optional[LabelControl] = None

        register_tab_update_handlers(
            self._tab_updates,
            (
                ("locale", self._update_locale_tab_frame),
                ("particle", self._update_particle_tab_frame),
                ("sprite", self._update_sprite_tab_frame),
                ("sched", self._update_sched_tab_frame),
                ("tilemap", self._update_tilemap_tab_frame),
                ("progress", self._update_progress_tab_frame),
            ),
        )

    # ------------------------------------------------------------------
    # Feature lifecycle
    # ------------------------------------------------------------------

    def build(self, host) -> None:
        self.window = create_feature_presented_window(
            host,
            feature=self,
            presenter_cls=_SystemsWindowPresenter,
            spec=_SYSTEMS_WINDOW_SPEC,
            window_control_cls=WindowControl,
        )

        self._on_tab_change("filter")

    def on_update(self, host) -> None:
        super().on_update(host)
        if self.window is None or not self.window.visible:
            return

        dt = self._frame_timer.tick()

        # Update event playback
        if self._playback is not None and self._playback.is_playing:
            self._playback.update(dt)
            self._update_event_status()

        # Update responsive layout breakpoint label
        if self._responsive is not None and self.window is not None:
            if self._responsive.update(self.window.rect.width):
                if self._layout_label is not None:
                    bp = self._responsive.active_breakpoint.value
                    self._layout_label.text = f"Active breakpoint: {bp}"

        self._tab_updates.run(self._active_tab, host, dt)

    def _update_locale_tab_frame(self, host, _dt: float) -> None:
        if (
            self._text_flow_dirty
            and self._text_canvas is not None
            and self._text_flow is not None
        ):
            self._text_flow_dirty = False
            canvas = self._text_canvas.canvas
            canvas.fill((28, 30, 40))
            self._text_flow.layout(host.app.theme)
            self._text_flow.render(canvas, 8, 8)
            self._text_canvas.invalidate()

    def _update_particle_tab_frame(self, _host, dt: float) -> None:
        if self._particle_system is None:
            return
        self._particle_system.update(dt)
        if self._particle_canvas is not None:
            surf = self._particle_canvas.canvas
            surf.fill((20, 20, 30))
            self._particle_system.draw(surf)
            self._particle_canvas.invalidate()
        if self._particle_count_label is not None:
            self._particle_count_label.text = (
                f"Live particles: {self._particle_system.active_particle_count}  "
                f"Emitters: {self._particle_system.emitter_count}"
            )

    def _update_sprite_tab_frame(self, _host, dt: float) -> None:
        if self._sprite_anim is None:
            return
        self._sprite_anim.update(dt)
        if self._sprite_ctrl is not None:
            self._sprite_ctrl.invalidate()

    def _update_sched_tab_frame(self, _host, dt: float) -> None:
        if self._scheduler is None:
            return
        self._scheduler.update(dt)
        if self._sched_step_label is not None:
            self._sched_step_label.text = (
                f"Active coroutines: {self._scheduler.coroutine_count}"
            )

    def _update_tilemap_tab_frame(self, _host, _dt: float) -> None:
        if not self._tile_dirty or self._tile_canvas is None or self._tile_map is None:
            return
        self._tile_dirty = False
        surf = self._tile_canvas.canvas
        surf.fill((20, 30, 20))
        cam = Rect(0, 0, surf.get_width(), surf.get_height())
        self._tile_map.draw(surf, cam, offset=(0, 0))
        self._tile_canvas.invalidate()

    def _update_progress_tab_frame(self, _host, dt: float) -> None:
        if self._progress_indeterminate is not None:
            self._progress_indeterminate.tick(dt)

    # ------------------------------------------------------------------
    # Tab management
    # ------------------------------------------------------------------

    def _window_event_handler(self, event_type: str, _data=None) -> None:
        if event_type == "close":
            set_window_visible_state(self.window, False)

    def _on_tab_change(self, key: str) -> None:
        self._active_tab = key
        self._tabs.activate(key)
        # Re-apply overflow clipping for flow items after the blanket show/hide above.
        # Do NOT call _flow_apply_layout here — that would reposition items using a
        # cached absolute rect and break them if the window has moved since build.
        if key == "flow" and self._flow_items:
            wo = getattr(self, "_flow_items_win_offset", None)
            if wo is not None and self.window is not None:
                ox, oy, fw, fh = wo
                clip_bottom = self.window.rect.top + oy + fh
            else:
                clip_bottom = getattr(self, "_flow_items_rect", Rect(0, 0, 0, 9999)).bottom
            for item in self._flow_items:
                item.visible = item.rect.bottom <= clip_bottom

    @staticmethod
    def _add_tab_labels_from_specs(ctx: TabLayoutContext, specs) -> list[LabelControl]:
        labels = []
        for spec in specs:
            kwargs = {}
            if spec.width is not None:
                kwargs["width"] = spec.width
            if spec.advance is not None:
                kwargs["advance"] = spec.advance
            label = ctx.add_label(spec.control_id, spec.height, spec.text, **kwargs)
            labels.append(label)
        return labels

    def _add_button_from_spec(self, ctx: TabLayoutContext, spec: PresenterButtonSpec):
        """Add a button described by a PresenterButtonSpec, resolving handler by name."""
        return ctx.add_button(
            spec.control_id, spec.width, spec.height, spec.text,
            getattr(self, spec.handler_attr),
            x_offset=spec.x_offset,
            advance=spec.advance,
            style=spec.style,
        )

    @staticmethod
    def _binding_label_text(binding) -> str:
        key_name = pygame.key.name(binding.key) if binding.key else "?"
        return str(_INPUT_BINDING_LABEL_SPEC["text_template"]).format(
            label=binding.label,
            key_name=key_name,
        )

    def _configure_input_breakpoints(self) -> None:
        self._responsive = ResponsiveLayout()
        for name, min_width in _INPUT_BREAKPOINT_SPECS:
            self._responsive.add_breakpoint(Breakpoint(str(name), min_width=int(min_width), layout=None))

    # ------------------------------------------------------------------
    # Tab: Filter — SortFilterProxySource
    # ------------------------------------------------------------------

    def _build_filter_tab(self, host, rect: Rect) -> list:
        ctx = TabLayoutContext(self.window, rect)

        fruit_items = [ListItem(name) for name in _FILTER_ITEM_LABELS]
        source = FixedItemSource(fruit_items)
        self._proxy = SortFilterProxySource(source)
        self._proxy.subscribe(self._update_filter_label)

        self._add_tab_labels_from_specs(ctx, _FILTER_TAB_LABEL_SPECS)

        ctx.add_control(
            TextInputControl(
                str(_FILTER_INPUT_SPEC["control_id"]),
                Rect(
                    ctx.x + int(_FILTER_INPUT_SPEC["x_offset"]),
                    ctx.y,
                    int(_FILTER_INPUT_SPEC["width"]),
                    int(_FILTER_INPUT_SPEC["height"]),
                ),
                placeholder=str(_FILTER_INPUT_SPEC["placeholder"]),
                on_change=self._on_filter_changed,
            )
        )
        ctx.advance(int(_FILTER_INPUT_SPEC["advance"]))

        ctx.add_control(
            ToggleControl(
                str(_FILTER_SORT_TOGGLE_SPEC["control_id"]),
                Rect(
                    ctx.x,
                    ctx.y,
                    int(_FILTER_SORT_TOGGLE_SPEC["width"]),
                    int(_FILTER_SORT_TOGGLE_SPEC["height"]),
                ),
                str(_FILTER_SORT_TOGGLE_SPEC["off_text"]),
                str(_FILTER_SORT_TOGGLE_SPEC["on_text"]),
                pushed=bool(_FILTER_SORT_TOGGLE_SPEC["pushed"]),
                on_toggle=self._on_sort_toggled,
                style=str(_FILTER_SORT_TOGGLE_SPEC["style"]),
            )
        )
        ctx.advance(int(_FILTER_SORT_TOGGLE_SPEC["advance"]))

        self._add_tab_labels_from_specs(ctx, (_FILTER_RESULT_TITLE_SPEC,))
        self._filter_label = ctx.add_label(
            str(_FILTER_RESULT_LABEL_SPEC["control_id"]),
            max(int(_FILTER_RESULT_LABEL_SPEC["min_height"]), ctx.remaining_height(margin=ctx.pad)),
            str(_FILTER_RESULT_LABEL_SPEC["text"]),
        )

        self._update_filter_label()
        return ctx.build()

    def _on_filter_changed(self, text: str) -> None:
        if not text.strip():
            self._proxy.set_filter(None)
        else:
            prefix = text.strip().lower()
            self._proxy.set_filter(lambda item: item.label.lower().startswith(prefix))

    def _on_sort_toggled(self, pushed: bool) -> None:
        if pushed:
            self._proxy.set_sort_key(lambda item: item.label, reverse=False)
        else:
            self._proxy.set_sort_key(None)

    def _update_filter_label(self) -> None:
        if self._proxy is None or self._filter_label is None:
            return
        count = self._proxy.item_count()
        names = [self._proxy.item_at(i).label for i in range(min(count, 7))]
        suffix = "..." if count > 7 else ""
        self._filter_label.text = f"Showing {count} item(s):\n" + ", ".join(names) + suffix

    # ------------------------------------------------------------------
    # Tab: Locale — LocaleRegistry + StringTable + TextFlow + TextSpan
    # ------------------------------------------------------------------

    def _build_locale_tab(self, host, rect: Rect) -> list:
        ctx = TabLayoutContext(self.window, rect)

        self._locale_registry = initialize_locale_registry(
            [StringTable(locale_id, strings) for locale_id, strings in _LOCALE_TABLE_SPECS],
            initial_locale="en",
        )

        self._add_tab_labels_from_specs(ctx, (_LOCALE_TAB_LABEL_SPECS[0],))
        for i, (locale_id, locale_name) in enumerate(_LOCALE_BUTTON_SPECS):
            ctx.add_control(
                ButtonControl(
                    f"nsdf_locale_btn_{locale_id}",
                    Rect(
                        ctx.x + int(_LOCALE_BUTTON_LAYOUT_SPEC["x_offset"]) + (i * int(_LOCALE_BUTTON_LAYOUT_SPEC["step"])),
                        ctx.y,
                        int(_LOCALE_BUTTON_LAYOUT_SPEC["width"]),
                        int(_LOCALE_BUTTON_LAYOUT_SPEC["height"]),
                    ),
                    locale_name,
                    self._make_locale_setter(locale_id),
                )
            )
        ctx.advance(int(_LOCALE_BUTTON_LAYOUT_SPEC["advance"]))

        self._greeting_label = ctx.add_label(
            str(_LOCALE_GREETING_LABEL_SPEC["control_id"]),
            int(_LOCALE_GREETING_LABEL_SPEC["height"]),
            self._locale_registry.t("greeting"),
            advance=int(_LOCALE_GREETING_LABEL_SPEC["advance"]),
        )
        self._add_tab_labels_from_specs(ctx, (_LOCALE_TAB_LABEL_SPECS[1],))

        canvas_h = max(int(_LOCALE_TEXT_CANVAS_SPEC["min_height"]), ctx.remaining_height(margin=ctx.pad))
        self._text_canvas = ctx.add_control(
            CanvasControl(str(_LOCALE_TEXT_CANVAS_SPEC["control_id"]), Rect(ctx.x, ctx.y, ctx.width, canvas_h))
        )

        self._text_flow = TextFlow(
            width=ctx.width - int(_LOCALE_TEXT_CANVAS_SPEC["text_flow_horizontal_padding"]),
            line_spacing=int(_LOCALE_TEXT_CANVAS_SPEC["line_spacing"]),
        )
        self._rebuild_text_flow()
        return ctx.build()

    def _make_locale_setter(self, locale_id: str):
        def set_locale():
            self._locale_registry.set_locale(locale_id)
            if self._greeting_label is not None:
                self._greeting_label.text = self._locale_registry.t("greeting")
            self._rebuild_text_flow()
            self._text_flow_dirty = True

        return set_locale

    def _rebuild_text_flow(self) -> None:
        if self._locale_registry is None or self._text_flow is None:
            return
        desc = self._locale_registry.t("description", fallback="")
        feat = self._locale_registry.t("feature_count", fallback="")
        self._text_flow.set_content(
            [
                TextSpan(desc, role="body"),
                TextSpan("\n", role="body"),
                TextSpan(feat, bold=True, color=(80, 200, 120), role="body"),
            ]
        )
        self._text_flow_dirty = True

    # ------------------------------------------------------------------
    # Tab: Input — InputMap + InputBinding + ResponsiveLayout + Breakpoint
    # ------------------------------------------------------------------

    def _build_input_tab(self, host, rect: Rect) -> list:
        ctx = TabLayoutContext(self.window, rect)

        self._input_map = InputMap()
        for action, key, label in _INPUT_DECLARE_SPECS:
            self._input_map.declare(action, key=key, mod=0, label=label)

        self._add_tab_labels_from_specs(ctx, (_INPUT_TAB_HEADER_LABEL_SPECS[0],))

        self._binding_labels = []
        for binding in self._input_map.bindings():
            lbl = ctx.add_label(
                f"{_INPUT_BINDING_LABEL_SPEC['control_id_prefix']}{binding.action}",
                int(_INPUT_BINDING_LABEL_SPEC["height"]),
                self._binding_label_text(binding),
                advance=int(_INPUT_BINDING_LABEL_SPEC["advance"]),
            )
            self._binding_labels.append(lbl)
        ctx.advance(6)

        for spec in _INPUT_ACTION_BUTTON_SPECS:
            self._add_button_from_spec(ctx, spec)

        self._add_tab_labels_from_specs(ctx, (_INPUT_TAB_HEADER_LABEL_SPECS[1],))
        self._layout_label = ctx.add_label(
            _INPUT_LAYOUT_STATUS_LABEL_SPEC.control_id,
            _INPUT_LAYOUT_STATUS_LABEL_SPEC.height,
            _INPUT_LAYOUT_STATUS_LABEL_SPEC.text,
        )

        self._configure_input_breakpoints()

        return ctx.build()

    def _remap_bindings(self) -> None:
        if self._input_map is None:
            return
        bind_input_map_actions(self._input_map, _INPUT_REMAP_BINDINGS, mod=0)
        self._refresh_binding_labels()

    def _reset_bindings(self) -> None:
        if self._input_map is None:
            return
        bind_input_map_actions(self._input_map, _INPUT_DEFAULT_BINDINGS, mod=0)
        self._refresh_binding_labels()

    def _refresh_binding_labels(self) -> None:
        if self._input_map is None:
            return
        for lbl, binding in zip(self._binding_labels, self._input_map.bindings()):
            lbl.text = self._binding_label_text(binding)

    # ------------------------------------------------------------------
    # Tab: Event — EventRecorder + EventPlayback + RecordedEvent
    # ------------------------------------------------------------------

    def _build_event_tab(self, host, rect: Rect) -> list:
        ctx = TabLayoutContext(self.window, rect)

        self._recorder = EventRecorder()

        self._add_tab_labels_from_specs(ctx, (_EVENT_INFO_LABEL_SPEC,))
        self._event_status_label = ctx.add_label(
            _EVENT_STATUS_LABEL_SPEC.control_id,
            _EVENT_STATUS_LABEL_SPEC.height,
            _EVENT_STATUS_LABEL_SPEC.text,
            advance=_EVENT_STATUS_LABEL_SPEC.advance,
        )

        ctx.add_button_row(
            **_EVENT_BUTTON_ROW_GEOMETRY,
            specs=tuple(
                (cid, lbl, getattr(self, attr))
                for cid, lbl, attr in _EVENT_BUTTON_ROW_HANDLER_ATTRS
            ),
        )

        self._add_tab_labels_from_specs(ctx, (_EVENT_LOG_TITLE_SPEC,))
        self._event_log_label = ctx.add_label(
            _EVENT_LOG_LABEL_SPEC.control_id,
            max(_EVENT_LOG_LABEL_SPEC.height, ctx.remaining_height(margin=ctx.pad)),
            _EVENT_LOG_LABEL_SPEC.text,
        )
        return ctx.build()

    def _start_recording(self) -> None:
        if self._recorder is None:
            return
        self._recorder.start()
        self._update_event_status()

    def _stop_recording(self) -> None:
        if self._recorder is None:
            return
        self._recorded_events = self._recorder.stop()
        self._update_event_status()
        self._update_event_log()

    def _simulate_events(self) -> None:
        """Add a handful of synthetic RecordedEvent objects for demo purposes."""
        self._recorded_events = [
            RecordedEvent(time_offset_ms=0.0, event_type="MOUSE_DOWN", pos=[100, 200], button=1),
            RecordedEvent(time_offset_ms=250.0, event_type="MOUSE_UP", pos=[100, 200], button=1),
            RecordedEvent(time_offset_ms=500.0, event_type="MOUSE_MOTION", pos=[150, 220]),
            RecordedEvent(time_offset_ms=750.0, event_type="KEY_DOWN", key=pygame.K_SPACE),
            RecordedEvent(time_offset_ms=1000.0, event_type="KEY_UP", key=pygame.K_SPACE),
        ]
        self._update_event_status()
        self._update_event_log()

    def _start_playback(self) -> None:
        if not self._recorded_events:
            if self._event_status_label is not None:
                self._event_status_label.text = "Status: No events — use Start Rec. or Sim. Events first."
            return
        self._playback = EventPlayback(
            self._recorded_events,
            handler=self._on_playback_event,
            loop=False,
            on_complete=self._on_playback_complete,
        )
        self._playback.start()
        self._update_event_status()

    def _on_playback_event(self, event: RecordedEvent) -> None:
        if self._event_log_label is not None:
            self._event_log_label.text = (
                f"Replaying: {event.event_type} @ {event.time_offset_ms:.0f}ms"
            )

    def _on_playback_complete(self) -> None:
        self._update_event_status()
        if self._event_log_label is not None:
            self._event_log_label.text = "Playback complete."

    def _update_event_status(self) -> None:
        if self._event_status_label is None or self._recorder is None:
            return
        if self._playback is not None and self._playback.is_playing:
            pct = int(self._playback.progress * 100)
            self._event_status_label.text = f"Status: Playing ({pct}%)"
        elif self._recorder.is_recording:
            self._event_status_label.text = (
                f"Status: Recording ({self._recorder.recorded_count} events so far)"
            )
        else:
            count = len(self._recorded_events)
            self._event_status_label.text = f"Status: Idle — {count} event(s) recorded"

    def _update_event_log(self) -> None:
        if self._event_log_label is None:
            return
        if not self._recorded_events:
            self._event_log_label.text = "No events recorded."
            return
        lines = [
            f"  {e.event_type} @ +{e.time_offset_ms:.0f}ms"
            for e in self._recorded_events[:8]
        ]
        suffix = f"\n  ... ({len(self._recorded_events)} total)" if len(self._recorded_events) > 8 else ""
        self._event_log_label.text = "\n".join(lines) + suffix

    # ------------------------------------------------------------------
    # Tab: Inspect — PropertyRegistry + ui_property + SceneSnapshot +
    #                NodeSnapshot + SceneSpatialIndex
    # ------------------------------------------------------------------

    def _build_inspect_tab(self, host, rect: Rect) -> list:
        ctx = TabLayoutContext(self.window, rect)

        # PropertyRegistry / PropertyDescriptor demo
        self._add_tab_labels_from_specs(ctx, (_INSPECT_HEADER_LABEL_SPECS[0],))

        # Register sample descriptors to demonstrate the API
        descs = [
            PropertyDescriptor(
                name=name,
                label=label,
                type=desc_type,
                group=group,
                owner_class=ButtonControl,
            )
            for name, label, desc_type, group in _BUTTON_DESCRIPTOR_SPECS
        ]
        register_descriptors(property_registry, ButtonControl, descs)

        for desc in property_registry.descriptors_for(ButtonControl):
            ctx.add_label(
                f"nsdf_prop_{desc.name}", 20,
                f"  [{desc.group}] {desc.label} : {desc.type}", advance=21)
        ctx.advance(8)

        # SceneSnapshot demo
        self._add_tab_labels_from_specs(ctx, (_INSPECT_HEADER_LABEL_SPECS[1],))
        for spec in _INSPECT_SNAPSHOT_BUTTON_SPECS:
            self._add_button_from_spec(ctx, spec)
        self._snapshot_label = ctx.add_label(
            _INSPECT_SNAPSHOT_LABEL_SPEC.control_id,
            _INSPECT_SNAPSHOT_LABEL_SPEC.height,
            _INSPECT_SNAPSHOT_LABEL_SPEC.text,
            advance=_INSPECT_SNAPSHOT_LABEL_SPEC.advance,
        )

        # SceneSpatialIndex demo
        self._add_tab_labels_from_specs(ctx, (_INSPECT_HEADER_LABEL_SPECS[2],))
        self._spatial_index = SceneSpatialIndex(cell_size=64)
        self._add_button_from_spec(ctx, _INSPECT_SPATIAL_BUTTON_SPEC)
        self._spatial_label = ctx.add_label(
            _INSPECT_SPATIAL_LABEL_SPEC.control_id,
            _INSPECT_SPATIAL_LABEL_SPEC.height,
            _INSPECT_SPATIAL_LABEL_SPEC.text,
        )

        return ctx.build()

    # ------------------------------------------------------------------
    # Tab: Props — PropertyInspectorPanel
    # ------------------------------------------------------------------

    def _build_props_tab(self, host, rect: Rect) -> list:
        ctx = TabLayoutContext(self.window, rect)

        self._add_tab_labels_from_specs(ctx, _PROPS_HEADER_LABEL_SPECS)

        panel_h = max(120, ctx.remaining_height(margin=60 + ctx.pad))
        self._prop_inspector_panel = ctx.add_control(
            PropertyInspectorPanel(
                "nsdf_prop_inspector",
                Rect(ctx.x, ctx.y, ctx.width, panel_h),
                PropertyInspectorModel(self._demo_inspectable),
                on_select=self._on_prop_selected,
            )
        )
        ctx.advance(panel_h + 6)

        self._prop_selected_label = ctx.add_label(
            _PROPS_SELECTED_LABEL_SPEC.control_id,
            _PROPS_SELECTED_LABEL_SPEC.height,
            _PROPS_SELECTED_LABEL_SPEC.text,
            advance=_PROPS_SELECTED_LABEL_SPEC.advance,
        )
        self._add_button_from_spec(ctx, _PROPS_REFRESH_BUTTON_SPEC)

        return ctx.build()

    def _on_prop_selected(self, prop) -> None:
        if self._prop_selected_label is None:
            return
        try:
            current = getattr(self._demo_inspectable, prop.descriptor.name, "?")
            self._prop_selected_label.text = (
                f"Selected: [{prop.descriptor.group}] {prop.descriptor.label} = {current!r}"
            )
        except Exception:
            self._prop_selected_label.text = f"Selected: {prop.descriptor.name}"

    def _refresh_prop_inspector(self) -> None:
        if self._prop_inspector_panel is not None:
            self._prop_inspector_panel.refresh()

    # ------------------------------------------------------------------
    # Tab: Dock — DockWorkspacePanel
    # ------------------------------------------------------------------

    def _build_dock_tab(self, host, rect: Rect) -> list:
        ctx = TabLayoutContext(self.window, rect)

        ctx.add_label("nsdf_dock_title", 22,
            "DockWorkspacePanel — interactive tab bar backed by DockWorkspace model:",
            advance=28)
        ctx.add_label("nsdf_dock_hint", 20,
            "Click a tab below to switch the active pane.", advance=26)

        # Build a demo DockWorkspace with tabs
        self._dock_workspace = DockWorkspace(
            DockTabs(
                "demo_tabs",
                panes=[
                    DockPane("editor", "Editor"),
                    DockPane("preview", "Preview"),
                    DockPane("console", "Console"),
                    DockPane("output", "Output"),
                ],
            )
        )

        panel_h = 36
        self._dock_panel = ctx.add_control(
            DockWorkspacePanel(
                "nsdf_dock_panel",
                Rect(ctx.x, ctx.y, ctx.width, panel_h),
                self._dock_workspace,
                on_change=self._on_dock_pane_changed,
            )
        )
        ctx.advance(panel_h + 12)

        self._dock_active_label = ctx.add_label(
            "nsdf_dock_active", 20, "Active pane: editor", advance=26)

        ctx.add_button_row(height=28, gap=8, width=120, advance=36, specs=(
            ("nsdf_dock_add", "Add Extra Pane", self._dock_add_pane),
            ("nsdf_dock_remove", "Remove Active", self._dock_remove_active),
        ))

        ctx.add_label("nsdf_dock_model_title", 20,
            "DockWorkspace.to_dict() — model serializes cleanly:", advance=24)
        self._dock_model_label = ctx.add_label(
            "nsdf_dock_model_label", 20, self._dock_model_summary())

        return ctx.build()

    def _on_dock_pane_changed(self, pane_id: str) -> None:
        if self._dock_active_label is not None:
            self._dock_active_label.text = f"Active pane: {pane_id}"
        if hasattr(self, "_dock_model_label") and self._dock_model_label is not None:
            self._dock_model_label.text = self._dock_model_summary()

    def _dock_add_pane(self) -> None:
        if self._dock_workspace is None or self._dock_panel is None:
            return
        root = self._dock_workspace.root
        if not isinstance(root, DockTabs):
            return
        idx = len(root.panes) + 1
        root.add_pane(DockPane(f"extra_{idx}", f"Extra {idx}"))
        self._dock_panel.invalidate()
        if hasattr(self, "_dock_model_label") and self._dock_model_label is not None:
            self._dock_model_label.text = self._dock_model_summary()

    def _dock_remove_active(self) -> None:
        if self._dock_workspace is None or self._dock_panel is None:
            return
        active = self._dock_panel.active_pane_id
        if active is None:
            return
        self._dock_workspace.remove_pane(active)
        self._dock_panel.invalidate()
        if self._dock_active_label is not None:
            new_active = self._dock_panel.active_pane_id
            self._dock_active_label.text = f"Active pane: {new_active or '(none)'}"
        if hasattr(self, "_dock_model_label") and self._dock_model_label is not None:
            self._dock_model_label.text = self._dock_model_summary()

    def _dock_model_summary(self) -> str:
        if self._dock_workspace is None:
            return "(no workspace)"
        d = self._dock_workspace.to_dict()
        root = d.get("root", {})
        kind = root.get("kind", "?")
        if kind == "tabs":
            pane_ids = [p["pane_id"] for p in root.get("panes", [])]
            return f"kind=tabs, panes={pane_ids}, active={root.get('active_pane_id')!r}"
        return str(d)[:100]

    def _capture_snapshot(self) -> None:
        if self.window is None:
            return
        self._snapshot = SceneSnapshot.from_nodes([self.window])
        if self._snapshot_label is not None:
            pos = self.window.rect.topleft
            self._snapshot_label.text = (
                f"Captured: window at {pos}, {len(self._snapshot)} node(s) saved"
            )

    def _restore_snapshot(self) -> None:
        if self._snapshot is None:
            if self._snapshot_label is not None:
                self._snapshot_label.text = "Nothing captured yet — press Capture first."
            return
        entry = self._snapshot.get(self.window.control_id)
        if entry is not None:
            restored_rect = Rect(entry.rect)
            self.window.rect = restored_rect
            if self._snapshot_label is not None:
                self._snapshot_label.text = (
                    f"Restored: window moved to {restored_rect.topleft}"
                )

    def _build_and_query_spatial(self) -> None:
        if self._spatial_index is None or self.window is None:
            return
        try:
            if self._main_scene is not None:
                self._spatial_index.build(self._main_scene)
                cx, cy = self.window.rect.center
                hits = self._spatial_index.query_point(cx, cy)
                if self._spatial_label is not None:
                    self._spatial_label.text = (
                        f"Index built — {len(hits)} node(s) at window center ({cx}, {cy})"
                    )
            else:
                if self._spatial_label is not None:
                    self._spatial_label.text = "Scene not yet bound (call bind_runtime first)."
        except Exception as exc:
            if self._spatial_label is not None:
                self._spatial_label.text = f"Error: {exc}"

    # ------------------------------------------------------------------
    # Tab: Particle — ParticleSystem + Emitter + ParticleLayer
    # ------------------------------------------------------------------

    def _build_particle_tab(self, host, rect: Rect) -> list:
        import pygame as _pygame
        ctx = TabLayoutContext(self.window, rect)

        ctx.add_label("nsdf_particle_info", 20,
            "ParticleSystem — live GPU-free particle simulation.  Add/burst emitters below.",
            advance=26)
        self._particle_count_label = ctx.add_label(
            "nsdf_particle_count", 22, "Live particles: 0  Emitters: 0", advance=30)

        ctx.add_button_row(height=28, gap=8, width=130, advance=38, specs=(
            ("nsdf_particle_add", "Add Emitter", self._particle_add_emitter),
            ("nsdf_particle_burst", "Burst (50)", self._particle_burst),
            ("nsdf_particle_clear", "Clear Emitters", self._particle_clear),
        ))

        canvas_h = max(60, ctx.remaining_height(margin=ctx.pad))
        self._particle_canvas = ctx.add_control(
            CanvasControl("nsdf_particle_canvas",
                Rect(ctx.x, ctx.y, ctx.width, canvas_h)))

        # Build particle layer (owns its own ParticleSystem)
        self._particle_layer = ParticleLayer(
            "nsdf_particle_layer",
            Rect(ctx.x, ctx.y, ctx.width, canvas_h),
        )
        self._particle_system = self._particle_layer.particle_system
        return ctx.build()

    def _particle_add_emitter(self) -> None:
        if self._particle_system is None or self._particle_canvas is None:
            return
        import random as _random
        canvas_rect = self._particle_canvas.rect
        cx = canvas_rect.left + _random.randint(20, max(21, canvas_rect.width - 20))
        cy = canvas_rect.top + _random.randint(20, max(21, canvas_rect.height - 20))
        emitter = Emitter(
            x=cx - canvas_rect.left,
            y=cy - canvas_rect.top,
            rate=15.0,
            lifetime=(0.8, 2.0),
            speed=(20.0, 60.0),
            colors=[(100 + _random.randint(0, 155), 60, 200)],
        )
        self._particle_system.add_emitter(emitter)

    def _particle_burst(self) -> None:
        if self._particle_system is None or self._particle_canvas is None:
            return
        canvas_rect = self._particle_canvas.rect
        cx = (canvas_rect.width) // 2
        cy = (canvas_rect.height) // 2
        emitter = Emitter(
            x=cx,
            y=cy,
            rate=0.0,
            burst_count=50,
            lifetime=(0.5, 1.5),
            speed=(40.0, 120.0),
            colors=[(220, 180, 40)],
        )
        self._particle_system.add_emitter(emitter)

    def _particle_clear(self) -> None:
        if self._particle_system is not None:
            self._particle_system.clear()

    # ------------------------------------------------------------------
    # Tab: Sprite — SpriteSheet + FrameAnimation + AnimatedImageControl
    # ------------------------------------------------------------------

    def _build_sprite_tab(self, host, rect: Rect) -> list:
        import pygame as _pygame
        ctx = TabLayoutContext(self.window, rect)

        ctx.add_label("nsdf_sprite_info", 40,
            "SpriteSheet slices an atlas into frames.  FrameAnimation drives playback.\n"
            "AnimatedImageControl renders the active frame as a scene-graph node.",
            advance=50)

        # Build a four-frame colored atlas
        FW, FH = 64, 64
        _atlas = _pygame.Surface((FW * 4, FH), flags=_pygame.SRCALPHA)
        for fi, col in enumerate([(220, 60, 60, 255), (60, 220, 60, 255), (60, 60, 220, 255), (220, 200, 40, 255)]):
            _atlas.fill(col, Rect(fi * FW, 0, FW, FH))
        sheet = SpriteSheet(_atlas, frame_w=FW, frame_h=FH)
        self._sprite_anim = FrameAnimation(sheet, frames=list(range(4)), fps=3, loop=True)
        ctrl_w, ctrl_h = min(200, ctx.width), 80
        self._sprite_ctrl = ctx.add_control(
            AnimatedImageControl(
                "nsdf_sprite_ctrl",
                Rect(ctx.x, ctx.y, ctrl_w, ctrl_h),
                animation=self._sprite_anim,
                scale=True,
            )
        )
        ctx.advance(ctrl_h + 12)

        ctx.add_label("nsdf_sprite_sheet_info", 22,
            f"SpriteSheet: {sheet.frame_count} frames  ({FW}×{FH} px each)", advance=28)

        ctx.add_button_row(height=28, gap=8, width=90, specs=(
            ("nsdf_sprite_play", "Play", lambda: self._sprite_anim.play() if self._sprite_anim else None),
            ("nsdf_sprite_pause", "Pause", lambda: self._sprite_anim.pause() if self._sprite_anim else None),
            ("nsdf_sprite_reset", "Reset", lambda: self._sprite_anim.reset() if self._sprite_anim else None),
        ))
        return ctx.build()

    # ------------------------------------------------------------------
    # Tab: Sched — CooperativeScheduler + Pause + Sleep + WaitUntil
    # ------------------------------------------------------------------

    def _build_sched_tab(self, host, rect: Rect) -> list:
        ctx = TabLayoutContext(self.window, rect)

        self._scheduler = CooperativeScheduler()

        ctx.add_label("nsdf_sched_info", 40,
            "CooperativeScheduler runs generator coroutines on the frame thread.\n"
            "Yield Pause, Sleep(s), or WaitUntil(predicate) to suspend.",
            advance=50)
        self._sched_step_label = ctx.add_label(
            "nsdf_sched_step", 22, "Active coroutines: 0", advance=30)

        log_h = max(40, ctx.remaining_height(margin=50))
        self._sched_log_label = ctx.add_label(
            "nsdf_sched_log", log_h,
            "Press a button to start a coroutine…", advance=log_h + 4)

        ctx.add_button_row(height=28, gap=8, width=140, specs=(
            ("nsdf_sched_start", "Start Sequence", self._sched_start_sequence),
            ("nsdf_sched_cancel", "Cancel All", self._sched_cancel_all),
        ))
        return ctx.build()

    def _sched_log_append(self, msg: str) -> None:
        self._sched_log.append(msg)
        if len(self._sched_log) > 8:
            self._sched_log = self._sched_log[-8:]
        if self._sched_log_label is not None:
            self._sched_log_label.text = "\n".join(self._sched_log)

    def _sched_start_sequence(self) -> None:
        if self._scheduler is None:
            return
        log = self._sched_log_append

        def demo_sequence():
            log("Step 1: starting…")
            yield Pause()
            log("Step 2: after one frame")
            yield Sleep(0.5)
            log("Step 3: after 0.5 s")
            yield Sleep(1.0)
            log("Step 4: after 1.5 s total — done!")

        self._scheduler.start(demo_sequence())

    def _sched_cancel_all(self) -> None:
        if self._scheduler is not None:
            self._scheduler.cancel_all()
            self._sched_log_append("All coroutines cancelled.")

    # ------------------------------------------------------------------
    # Tab: TileMap — TileSet + TileMap
    # ------------------------------------------------------------------

    def _build_tilemap_tab(self, host, rect: Rect) -> list:
        import pygame as _pygame
        import random as _random
        ctx = TabLayoutContext(self.window, rect)

        ctx.add_label("nsdf_tilemap_info", 40,
            "TileSet slices an atlas into tile surfaces.  TileMap renders only visible tiles.\n"
            "Camera culling is automatic via visible_range().",
            advance=50)

        TILE_W, TILE_H = 24, 24
        COLS, ROWS = 16, 10
        # Build a simple 4-tile atlas
        _atlas = _pygame.Surface((TILE_W * 4, TILE_H), flags=_pygame.SRCALPHA)
        for ti, col in enumerate([(40, 100, 40, 255), (80, 60, 30, 255), (120, 120, 120, 255), (30, 80, 160, 255)]):
            _atlas.fill(col[:3], Rect(ti * TILE_W, 0, TILE_W, TILE_H))
        tile_set = TileSet(_atlas, tile_w=TILE_W, tile_h=TILE_H)
        self._tile_map = TileMap(tile_w=TILE_W, tile_h=TILE_H, cols=COLS, rows=ROWS, tile_set=tile_set)
        self._tile_map.fill(0)
        # Border of water, interior of grass with some rocks
        for c in range(COLS):
            self._tile_map.set_tile(c, 0, 3)
            self._tile_map.set_tile(c, ROWS - 1, 3)
        for r in range(ROWS):
            self._tile_map.set_tile(0, r, 3)
            self._tile_map.set_tile(COLS - 1, r, 3)
        for _ in range(12):
            rc = _random.randint(1, COLS - 2)
            rr = _random.randint(1, ROWS - 2)
            self._tile_map.set_tile(rc, rr, 2)

        canvas_h = max(60, ctx.remaining_height(margin=60))
        self._tile_canvas = ctx.add_control(
            CanvasControl("nsdf_tile_canvas",
                Rect(ctx.x, ctx.y, ctx.width, canvas_h)))
        self._tile_dirty = True
        ctx.advance(canvas_h + 8)

        ctx.add_label("nsdf_tilemap_detail", 22,
            f"TileSet: {tile_set.tile_count} tiles  |  TileMap: {COLS}×{ROWS} ({COLS * ROWS} cells)")
        return ctx.build()

    # ------------------------------------------------------------------
    # Tab: Progress — ProgressBarControl
    # ------------------------------------------------------------------

    def _build_progress_tab(self, host, rect: Rect) -> list:
        ctx = TabLayoutContext(self.window, rect)

        ctx.add_label("nsdf_progress_info", 20,
            "ProgressBarControl — determinate (0–1) and indeterminate (marquee) modes.",
            advance=30)

        ctx.add_label("nsdf_prog_det_lbl", 18, "Determinate (value=0.72):", advance=22)
        self._progress_bar = ctx.add_control(
            ProgressBarControl(
                "nsdf_progress_bar",
                Rect(ctx.x, ctx.y, ctx.width, 18),
                value=0.72,
            )
        )
        ctx.advance(30)

        ctx.add_label("nsdf_prog_indet_lbl", 18, "Indeterminate (marquee):", advance=22)
        self._progress_indeterminate = ctx.add_control(
            ProgressBarControl(
                "nsdf_progress_indet",
                Rect(ctx.x, ctx.y, ctx.width, 18),
                indeterminate=True,
            )
        )
        ctx.advance(30)

        self._progress_label = ctx.add_label(
            "nsdf_progress_val_lbl", 22, "Adjust value:", advance=28)

        progress_specs = tuple(
            (
                f"nsdf_prog_set_{step_pct}",
                label,
                self._make_progress_setter(step_pct / 100.0),
            )
            for step_pct, label in ((0, "0%"), (25, "25%"), (50, "50%"), (75, "75%"), (100, "100%"))
        )
        ctx.add_button_row(height=26, gap=8, width=70, specs=progress_specs)
        return ctx.build()

    def _make_progress_setter(self, value: float):
        def _set():
            if self._progress_bar is not None:
                self._progress_bar.value = value
                if self._progress_label is not None:
                    self._progress_label.text = f"Value set to {value:.0%}"
        return _set

    # ------------------------------------------------------------------
    # Tab: Flow — FlowLayout + FlowItem
    # ------------------------------------------------------------------

    def _build_flow_tab(self, host, rect: Rect) -> list:
        ctx = TabLayoutContext(self.window, rect)

        ctx.add_label("nsdf_flow_info", 40,
            "FlowLayout arranges FlowItem nodes left-to-right with automatic row wrapping.\n"
            "Items here are LabelControls sized as tags.  Add/clear to see layout reflow.",
            advance=50)

        self._flow_result_label = ctx.add_label(
            "nsdf_flow_result", 22,
            "Row info will appear here after layout runs.", advance=30)

        ctx.add_button_row(height=28, gap=8, width=110, advance=36, specs=(
            ("nsdf_flow_add", "Add Item", self._flow_add_item),
            ("nsdf_flow_clear", "Clear Items", self._flow_clear_items),
            ("nsdf_flow_layout", "Apply Layout", self._flow_apply_layout),
        ))

        self._flow_layout = FlowLayout(gap_x=8, gap_y=6)
        self._flow_items_rect = Rect(ctx.x, ctx.y, ctx.width,
            max(60, ctx.remaining_height(margin=ctx.pad)))
        # Store offset relative to the window rect so layout stays correct if the window moves.
        self._flow_items_win_offset = (
            self._flow_items_rect.left - self.window.rect.left,
            self._flow_items_rect.top - self.window.rect.top,
            self._flow_items_rect.width,
            self._flow_items_rect.height,
        )

        # Pre-populate with a few example tags and run layout immediately so
        # items start at proper positions (not at 0,0).
        for tag in ("gui_do", "FlowLayout", "FlowItem", "pygame", "demo"):
            self._flow_add_item_named(tag)
        self._flow_apply_layout()
        # Add flow item labels to controls so _on_tab_change can manage visibility
        return ctx.build() + self._flow_items

    def _flow_add_item_named(self, name: str) -> None:
        if self._flow_layout is None:
            return
        lbl = self.window.add(
            LabelControl(
                f"nsdf_flow_tag_{len(self._flow_items)}",
                Rect(0, 0, max(40, len(name) * 9 + 16), 24),
                name,
                align="center",
            )
        )
        self._flow_items.append(lbl)
        self._flow_layout.add(FlowItem(node=lbl))

    def _flow_add_item(self) -> None:
        names = ["alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta", "theta", "iota", "kappa"]
        self._flow_add_item_named(names[len(self._flow_items) % len(names)])
        self._flow_apply_layout()
        # Register new item with tab panel so visibility is managed on tab switch
        new_item = self._flow_items[-1]
        self._tabs.append_to("flow", new_item)

    def _flow_clear_items(self) -> None:
        # Hide and untrack all flow items
        for item in self._flow_items:
            self._tabs.remove_from("flow", item)
        self._flow_items.clear()
        if self._flow_layout is not None:
            self._flow_layout.clear()

    def _flow_apply_layout(self) -> None:
        if self._flow_layout is None:
            return
        # Recompute bounds from the current window position so a moved window
        # doesn't cause items to render at stale absolute coordinates.
        if self.window is not None and hasattr(self, "_flow_items_win_offset"):
            ox, oy, fw, fh = self._flow_items_win_offset
            bounds = Rect(self.window.rect.left + ox, self.window.rect.top + oy, fw, fh)
        else:
            bounds = getattr(self, "_flow_items_rect", None)
        if bounds is None:
            return
        used_h = self._flow_layout.apply(bounds)
        # Hide items whose placed rect falls below the container boundary so
        # they don't render outside the window frame (no clipping in this layer).
        clip_bottom = bounds.bottom
        flow_tab_active = self._active_tab == "flow"
        for item in self._flow_items:
            fits = item.rect.bottom <= clip_bottom
            item.visible = fits and flow_tab_active
        rows = self._flow_layout.rows()
        visible_count = sum(1 for item in self._flow_items if item.rect.bottom <= clip_bottom)
        if self._flow_result_label is not None:
            clipped = len(self._flow_items) - visible_count
            clip_note = f"  ({clipped} clipped)" if clipped else ""
            self._flow_result_label.text = (
                f"{len(self._flow_items)} item(s) in {len(rows)} row(s) — used height: {used_h}px{clip_note}"
            )

    # ------------------------------------------------------------------
    # Tab: Search — TextSearcher + TextMatch
    # ------------------------------------------------------------------

    def _build_search_tab(self, host, rect: Rect) -> list:
        ctx = TabLayoutContext(self.window, rect)

        DEMO_TEXT = (
            "TextSearcher wraps Python regex to provide case-insensitive, whole-word, "
            "and full-regex search over a string.  Type a query below to find matches."
        )
        self._searcher = TextSearcher(DEMO_TEXT, case_sensitive=False)

        ctx.add_label("nsdf_search_source", 50,
            f'Search target:\n"{DEMO_TEXT[:80]}…"', advance=58)

        ctx.add_label("nsdf_search_lbl", 26, "Query:", width=60, advance=0)
        self._search_input = ctx.add_control(
            TextInputControl(
                "nsdf_search_input",
                Rect(ctx.x + 68, ctx.y, min(260, ctx.width - 68), 28),
                placeholder="enter search term…",
                on_change=self._on_search_changed,
            )
        )
        ctx.advance(36)

        self._search_result_label = ctx.add_label(
            "nsdf_search_result",
            max(40, ctx.remaining_height(margin=ctx.pad)),
            "Results appear here…",
        )
        return ctx.build()

    def _on_search_changed(self, text: str) -> None:
        if self._searcher is None or self._search_result_label is None:
            return
        q = text.strip()
        if not q:
            self._search_result_label.text = "Results appear here…"
            return
        matches = self._searcher.find_all(q)
        if not matches:
            self._search_result_label.text = f"No matches for {q!r}."
        else:
            lines = [f"  [{m.start}:{m.end}] {m.text!r}" for m in matches[:6]]
            suffix = f"\n  … ({len(matches)} total)" if len(matches) > 6 else ""
            self._search_result_label.text = f"{len(matches)} match(es):\n" + "\n".join(lines) + suffix

    # ------------------------------------------------------------------
    # Tab: ListDiff — ListDiffCalculator + ListDiff + DiffInsert/Remove/Move
    # ------------------------------------------------------------------

    def _build_listdiff_tab(self, host, rect: Rect) -> list:
        ctx = TabLayoutContext(self.window, rect)

        ctx.add_label("nsdf_listdiff_info", 20,
            "ListDiffCalculator.diff(old, new) returns DiffInsert / DiffRemove / DiffMove ops.",
            advance=28)
        ctx.add_label("nsdf_listdiff_old", 22, f"Old: {self._listdiff_old}", advance=26)
        ctx.add_label("nsdf_listdiff_new", 22, f"New: {self._listdiff_new}", advance=30)

        ctx.add_button_row(height=28, gap=8, width=130, advance=38, specs=(
            ("nsdf_listdiff_run", "Compute Diff", self._run_listdiff),
            ("nsdf_listdiff_apply", "Apply & Show", self._apply_listdiff),
        ))

        self._listdiff_result_label = ctx.add_label(
            "nsdf_listdiff_result",
            max(60, ctx.remaining_height(margin=ctx.pad)),
            "Press 'Compute Diff' to see operations.",
        )
        return ctx.build()

    def _run_listdiff(self) -> None:
        if self._listdiff_result_label is None:
            return
        diff = ListDiffCalculator.diff(self._listdiff_old, self._listdiff_new)
        lines = []
        for op in diff.removes:
            lines.append(f"  REMOVE [{op.index}] {op.item!r}")
        for op in diff.inserts:
            lines.append(f"  INSERT [{op.index}] {op.item!r}")
        for op in diff.moves:
            lines.append(f"  MOVE   [{op.from_index}→{op.to_index}] {op.item!r}")
        if diff.is_empty:
            self._listdiff_result_label.text = "Lists are identical — no operations."
        else:
            self._listdiff_result_label.text = (
                f"{len(diff.removes)} remove(s), {len(diff.inserts)} insert(s), {len(diff.moves)} move(s):\n"
                + "\n".join(lines)
            )

    def _apply_listdiff(self) -> None:
        if self._listdiff_result_label is None:
            return
        target = list(self._listdiff_old)
        diff = ListDiffCalculator.diff(self._listdiff_old, self._listdiff_new)
        ListDiffCalculator.apply_to_list(target, diff)
        self._listdiff_result_label.text = (
            f"Applied diff — result matches new: {target == self._listdiff_new}\n"
            f"Result: {target}"
        )

    # ------------------------------------------------------------------
    # Tab: Cache — DataCache + CacheStats
    # ------------------------------------------------------------------

    def _build_cache_tab(self, host, rect: Rect) -> list:
        ctx = TabLayoutContext(self.window, rect)

        self._cache = DataCache(max_size=5)
        # Pre-populate
        for k, v in [("user:1", "Alice"), ("user:2", "Bob"), ("user:3", "Carol")]:
            self._cache.put(k, v)

        ctx.add_label("nsdf_cache_info", 20,
            "DataCache — LRU cache (max_size=5) with reactive on_evicted/on_invalidated signals.",
            advance=28)
        self._cache_stats_label = ctx.add_label(
            "nsdf_cache_stats", 60, self._cache_stats_text(), advance=68)

        # Two buttons on the left + one further right, all at same y
        ctx.add_button_row(height=28, gap=8, width=110, advance=0, specs=(
            ("nsdf_cache_get", "Get user:1", self._cache_get_user1),
            ("nsdf_cache_miss", "Miss user:99", self._cache_miss),
        ))
        ctx.add_control(ButtonControl(
            "nsdf_cache_evict",
            Rect(ctx.x + 236, ctx.y, 130, 28),
            "Fill (cause evict)",
            self._cache_fill,
        ))
        ctx.advance(36)
        ctx.add_button("nsdf_cache_inval", 130, 28, "Invalidate user:2",
            self._cache_invalidate)

        return ctx.build()

    def _cache_stats_text(self) -> str:
        if self._cache is None:
            return "(no cache)"
        s = self._cache.stats()
        return (
            f"Size: {s.size}  Hits: {s.hits}  Misses: {s.misses}  "
            f"Evictions: {s.evictions}  Invalidations: {s.invalidations}\n"
            f"Hit rate: {s.hit_rate:.0%}  Total lookups: {s.total_lookups}"
        )

    def _refresh_cache_stats(self) -> None:
        if self._cache_stats_label is not None:
            self._cache_stats_label.text = self._cache_stats_text()

    def _cache_get_user1(self) -> None:
        if self._cache is not None:
            self._cache.get("user:1")
            self._refresh_cache_stats()

    def _cache_miss(self) -> None:
        if self._cache is not None:
            self._cache.get("user:99")
            self._refresh_cache_stats()

    def _cache_fill(self) -> None:
        if self._cache is not None:
            for i in range(4, 9):
                self._cache.put(f"user:{i}", f"User{i}")
            self._refresh_cache_stats()

    def _cache_invalidate(self) -> None:
        if self._cache is not None:
            self._cache.invalidate("user:2")
            self._refresh_cache_stats()

    # ------------------------------------------------------------------
    # Tab: Shortcuts — ShortcutHelpOverlay + ShortcutSection + ShortcutEntry
    # ------------------------------------------------------------------

    def _build_shortcuts_tab(self, host, rect: Rect) -> list:
        ctx = TabLayoutContext(self.window, rect)

        ctx.add_label("nsdf_shortcuts_info", 40,
            "ShortcutHelpOverlay reads ActionRegistry + KeyChordManager and renders\n"
            "a structured shortcut reference panel via the OverlayManager.",
            advance=50)
        ctx.add_button("nsdf_shortcuts_show", 150, 28, "Show Help Overlay",
            self._shortcuts_show_overlay, advance=38)
        self._shortcut_info_label = ctx.add_label(
            "nsdf_shortcuts_detail",
            max(60, ctx.remaining_height(margin=ctx.pad)),
            "Overlay not yet opened — click 'Show Help Overlay' to display it.\n"
            "ShortcutHelpOverlay.sections builds structured data from ActionRegistry.",
        )
        return ctx.build()

    def _shortcuts_show_overlay(self) -> None:
        if self._shortcut_overlay is None or self.window is None:
            return
        self._shortcut_overlay.toggle()
        sections = self._shortcut_overlay.sections
        total = sum(len(s.entries) for s in sections)
        if self._shortcut_info_label is not None:
            self._shortcut_info_label.text = (
                f"Overlay {'open' if self._shortcut_overlay.is_open else 'closed'}.\n"
                f"{len(sections)} section(s), {total} shortcut entry/entries built from ActionRegistry."
            )

    def bind_runtime(self, host) -> None:
        super().bind_runtime(host)
        bind_routed_feature_lifecycle(self, host, _SYSTEMS_LIFECYCLE_SPEC)
        self._main_scene = self._resolve_existing_main_scene(host)
        self._frame_timer.reset()

    @staticmethod
    def _resolve_existing_main_scene(host):
        app = getattr(host, "app", None)
        if app is None:
            return None
        if hasattr(app, "has_scene") and not app.has_scene("main"):
            return None
        runtime_map = getattr(app, "_scenes", None)
        if isinstance(runtime_map, dict):
            runtime = runtime_map.get("main")
            return getattr(runtime, "scene", None)
        return None


class _SystemsWindowPresenter(WindowPresenter):

    def __init__(self, feature, host):
        super().__init__(None)
        self.feature = feature
        self.host = host
        self.tab = None

    def on_create(self):
        # Tab builders use feature.window.add(...), so ensure this reference
        # exists before registering/building tab content.
        self.feature.window = self.window
        self.feature.demo = self.host
        self.tab = setup_feature_presenter_tabs_from_window_content(
            self,
            window=self.window,
            spec=_SYSTEMS_TABBED_PRESENTER_SPEC,
            tab_specs=_SYSTEMS_TAB_SPECS,
            on_change=self.feature._on_tab_change,
            tab_manager=self.feature._tabs,
            feature=self.feature,
            host=self.host,
            on_activate_callbacks=(
                ("locale", lambda: setattr(self.feature, "_text_flow_dirty", True)),
            ),
        )
        self.feature.tab = self.tab
        self.window.visible = False
