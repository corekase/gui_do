"""New Systems demo feature — showcases the new gui_do systems.

Demonstrates: SortFilterProxySource,
LocaleRegistry/StringTable, InputMap/InputBinding, ResponsiveLayout/Breakpoint,
TextFlow/TextSpan, EventRecorder/EventPlayback/RecordedEvent,
PropertyRegistry/PropertyDescriptor/ui_property, SceneSnapshot/NodeSnapshot,
and SceneSpatialIndex.
"""

from __future__ import annotations

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
    create_anchored_feature_window,
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
    TabControl,
    TabItem,
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

_TAB_H = 36


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
            "ensure_scene_task_panel",
            "TASK_PANEL_CONTROL_FONT_ROLE",
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

    # ------------------------------------------------------------------
    # Feature lifecycle
    # ------------------------------------------------------------------

    def build(self, host) -> None:
        self.use_font_roles(
            {
                "window_title": "system.window_title",
                "control": "system.control",
                "label": "system.label",
            }
        )
        self.window = create_anchored_feature_window(
            host,
            window_control_cls=WindowControl,
            control_id="systems_window",
            title="System",
            size=(820, 590),
            anchor="top_left",
            margin=(24, 92),
            title_font_role=self.font_role("window_title"),
            use_frame_backdrop=True,
        )
        presenter = _SystemsWindowPresenter(self, host)
        self.window.set_presenter(presenter)

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

        # Draw TextFlow to canvas if dirty
        if (
            self._text_flow_dirty
            and self._text_canvas is not None
            and self._text_flow is not None
            and self._active_tab == "locale"
        ):
            self._text_flow_dirty = False
            canvas = self._text_canvas.canvas
            canvas.fill((28, 30, 40))
            self._text_flow.layout(host.app.theme)
            self._text_flow.render(canvas, 8, 8)
            self._text_canvas.invalidate()

        # Particle tab — update system and redraw canvas
        if self._active_tab == "particle" and self._particle_system is not None:
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

        # Sprite tab — animate
        if self._active_tab == "sprite" and self._sprite_anim is not None:
            self._sprite_anim.update(dt)
            if self._sprite_ctrl is not None:
                self._sprite_ctrl.invalidate()

        # Scheduler tab — tick
        if self._active_tab == "sched" and self._scheduler is not None:
            self._scheduler.update(dt)
            if self._sched_step_label is not None:
                self._sched_step_label.text = (
                    f"Active coroutines: {self._scheduler.coroutine_count}"
                )

        # TileMap tab — draw once when dirty
        if self._tile_dirty and self._active_tab == "tilemap" and self._tile_canvas is not None and self._tile_map is not None:
            self._tile_dirty = False
            surf = self._tile_canvas.canvas
            surf.fill((20, 30, 20))
            cam = Rect(0, 0, surf.get_width(), surf.get_height())
            self._tile_map.draw(surf, cam, offset=(0, 0))
            self._tile_canvas.invalidate()

        # Progress tab — tick indeterminate bar
        if self._active_tab == "progress" and self._progress_indeterminate is not None:
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
    # ------------------------------------------------------------------
    # Tab: Filter — SortFilterProxySource
    # ------------------------------------------------------------------

    def _build_filter_tab(self, host, rect: Rect) -> list:
        controls = []
        pad = 8
        x, y = rect.left + pad, rect.top + pad

        fruit_items = [
            ListItem("Apple"),
            ListItem("Apricot"),
            ListItem("Banana"),
            ListItem("Blueberry"),
            ListItem("Cherry"),
            ListItem("Grape"),
            ListItem("Lemon"),
            ListItem("Mango"),
            ListItem("Orange"),
            ListItem("Peach"),
        ]
        source = FixedItemSource(fruit_items)
        self._proxy = SortFilterProxySource(source)
        self._proxy.subscribe(self._update_filter_label)

        info_lbl = self.window.add(
            LabelControl(
                "nsdf_filter_info",
                Rect(x, y, rect.width - pad * 2, 20),
                "SortFilterProxySource wraps any VirtualItemSource with reactive filter + sort.",
                align="left",
            )
        )
        info_lbl.font_role = self.font_role("label")
        controls.append(info_lbl)
        y += 28

        filter_lbl = self.window.add(
            LabelControl("nsdf_filter_lbl", Rect(x, y, 60, 26), "Filter:", align="left")
        )
        filter_lbl.font_role = self.font_role("label")
        controls.append(filter_lbl)

        filter_input = self.window.add(
            TextInputControl(
                "nsdf_filter_input",
                Rect(x + 68, y, 200, 28),
                placeholder="type prefix...",
                on_change=self._on_filter_changed,
                font_role=self.font_role("control"),
            )
        )
        controls.append(filter_input)
        y += 36

        sort_toggle = self.window.add(
            ToggleControl(
                "nsdf_sort_toggle",
                Rect(x, y, 130, 28),
                "Sort: A→Z",
                "Sort: Z→A",
                pushed=False,
                on_toggle=self._on_sort_toggled,
                style="round",
                font_role=self.font_role("control"),
            )
        )
        controls.append(sort_toggle)
        y += 38

        result_title = self.window.add(
            LabelControl(
                "nsdf_filter_result_title",
                Rect(x, y, rect.width - pad * 2, 20),
                "Proxy output:",
                align="left",
            )
        )
        result_title.font_role = self.font_role("label")
        controls.append(result_title)
        y += 24

        self._filter_label = self.window.add(
            LabelControl(
                "nsdf_filter_result_lbl",
                Rect(x, y, rect.width - pad * 2, max(40, rect.bottom - y - pad)),
                "",
                align="left",
            )
        )
        self._filter_label.font_role = self.font_role("label")
        controls.append(self._filter_label)

        self._update_filter_label()
        return controls

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
        controls = []
        pad = 8
        x, y = rect.left + pad, rect.top + pad

        en = StringTable(
            "en",
            {
                "greeting": "Hello, World!",
                "description": "gui_do is a pygame UI toolkit.",
                "feature_count": "New systems added this session: 10.",
            },
        )
        es = StringTable(
            "es",
            {
                "greeting": "\u00a1Hola, Mundo!",
                "description": "gui_do es un kit de herramientas de UI para pygame.",
                "feature_count": "Sistemas nuevos esta sesi\u00f3n: 10.",
            },
        )
        fr = StringTable(
            "fr",
            {
                "greeting": "Bonjour, le Monde!",
                "description": "gui_do est une bo\u00eete \u00e0 outils UI pour pygame.",
                "feature_count": "Nouveaux syst\u00e8mes cette session: 10.",
            },
        )
        self._locale_registry = LocaleRegistry()
        self._locale_registry.register(en)
        self._locale_registry.register(es)
        self._locale_registry.register(fr)
        self._locale_registry.set_locale("en")

        locale_lbl = self.window.add(
            LabelControl(
                "nsdf_locale_lbl", Rect(x, y, 80, 26), "Locale:", align="left"
            )
        )
        locale_lbl.font_role = self.font_role("label")
        controls.append(locale_lbl)

        for i, (locale_id, locale_name) in enumerate(
            [("en", "EN"), ("es", "ES"), ("fr", "FR")]
        ):
            btn = self.window.add(
                ButtonControl(
                    f"nsdf_locale_btn_{locale_id}",
                    Rect(x + 90 + i * 60, y, 52, 28),
                    locale_name,
                    self._make_locale_setter(locale_id),
                    font_role=self.font_role("control"),
                )
            )
            controls.append(btn)
        y += 36

        self._greeting_label = self.window.add(
            LabelControl(
                "nsdf_greeting_lbl",
                Rect(x, y, rect.width - pad * 2, 26),
                self._locale_registry.t("greeting"),
                align="left",
            )
        )
        self._greeting_label.font_role = self.font_role("label")
        controls.append(self._greeting_label)
        y += 34

        canvas_lbl = self.window.add(
            LabelControl(
                "nsdf_canvas_lbl",
                Rect(x, y, rect.width - pad * 2, 20),
                "TextFlow rendering (word-wrapped, mixed-style):",
                align="left",
            )
        )
        canvas_lbl.font_role = self.font_role("label")
        controls.append(canvas_lbl)
        y += 24

        canvas_h = max(60, rect.bottom - y - pad)
        self._text_canvas = self.window.add(
            CanvasControl("nsdf_text_canvas", Rect(x, y, rect.width - pad * 2, canvas_h))
        )
        controls.append(self._text_canvas)

        self._text_flow = TextFlow(width=rect.width - pad * 2 - 16, line_spacing=3)
        self._rebuild_text_flow()
        return controls

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
        controls = []
        pad = 8
        x, y = rect.left + pad, rect.top + pad

        self._input_map = InputMap()
        self._input_map.declare("move_up", key=pygame.K_UP, mod=0, label="Move Up")
        self._input_map.declare("move_down", key=pygame.K_DOWN, mod=0, label="Move Down")
        self._input_map.declare("move_left", key=pygame.K_LEFT, mod=0, label="Move Left")
        self._input_map.declare("move_right", key=pygame.K_RIGHT, mod=0, label="Move Right")

        title_lbl = self.window.add(
            LabelControl(
                "nsdf_input_title",
                Rect(x, y, rect.width - pad * 2, 22),
                "InputMap — declared action bindings:",
                align="left",
            )
        )
        title_lbl.font_role = self.font_role("label")
        controls.append(title_lbl)
        y += 26

        self._binding_labels = []
        for binding in self._input_map.bindings():
            key_name = pygame.key.name(binding.key) if binding.key else "?"
            text = f"  {binding.label}: {key_name}"
            lbl = self.window.add(
                LabelControl(
                    f"nsdf_binding_{binding.action}",
                    Rect(x, y, rect.width - pad * 2, 22),
                    text,
                    align="left",
                )
            )
            lbl.font_role = self.font_role("label")
            controls.append(lbl)
            self._binding_labels.append(lbl)
            y += 23

        y += 6
        remap_btn = self.window.add(
            ButtonControl(
                "nsdf_input_remap_btn",
                Rect(x, y, 150, 28),
                "Remap: W/A/S/D",
                self._remap_bindings,
                font_role=self.font_role("control"),
            )
        )
        controls.append(remap_btn)
        y += 36

        reset_btn = self.window.add(
            ButtonControl(
                "nsdf_input_reset_btn",
                Rect(x, y, 150, 28),
                "Reset to Arrows",
                self._reset_bindings,
                font_role=self.font_role("control"),
            )
        )
        controls.append(reset_btn)
        y += 44

        resp_title = self.window.add(
            LabelControl(
                "nsdf_resp_title",
                Rect(x, y, rect.width - pad * 2, 22),
                "ResponsiveLayout — breakpoints based on window width:",
                align="left",
            )
        )
        resp_title.font_role = self.font_role("label")
        controls.append(resp_title)
        y += 26

        self._layout_label = self.window.add(
            LabelControl(
                "nsdf_layout_lbl",
                Rect(x, y, rect.width - pad * 2, 22),
                "Active breakpoint: (updating...)",
                align="left",
            )
        )
        self._layout_label.font_role = self.font_role("label")
        controls.append(self._layout_label)

        self._responsive = ResponsiveLayout()
        self._responsive.add_breakpoint(Breakpoint("narrow", min_width=0, layout=None))
        self._responsive.add_breakpoint(Breakpoint("standard", min_width=600, layout=None))
        self._responsive.add_breakpoint(Breakpoint("wide", min_width=900, layout=None))

        return controls

    def _remap_bindings(self) -> None:
        if self._input_map is None:
            return
        wasd = [
            (pygame.K_w, "move_up"),
            (pygame.K_s, "move_down"),
            (pygame.K_a, "move_left"),
            (pygame.K_d, "move_right"),
        ]
        for key, action in wasd:
            self._input_map.bind(action, key=key, mod=0)
        self._refresh_binding_labels()

    def _reset_bindings(self) -> None:
        if self._input_map is None:
            return
        defaults = [
            (pygame.K_UP, "move_up"),
            (pygame.K_DOWN, "move_down"),
            (pygame.K_LEFT, "move_left"),
            (pygame.K_RIGHT, "move_right"),
        ]
        for key, action in defaults:
            self._input_map.bind(action, key=key, mod=0)
        self._refresh_binding_labels()

    def _refresh_binding_labels(self) -> None:
        if self._input_map is None:
            return
        for lbl, binding in zip(self._binding_labels, self._input_map.bindings()):
            key_name = pygame.key.name(binding.key) if binding.key else "?"
            lbl.text = f"  {binding.label}: {key_name}"

    # ------------------------------------------------------------------
    # Tab: Event — EventRecorder + EventPlayback + RecordedEvent
    # ------------------------------------------------------------------

    def _build_event_tab(self, host, rect: Rect) -> list:
        controls = []
        pad = 8
        x, y = rect.left + pad, rect.top + pad

        self._recorder = EventRecorder()

        info_lbl = self.window.add(
            LabelControl(
                "nsdf_evt_info",
                Rect(x, y, rect.width - pad * 2, 20),
                "EventRecorder captures GuiEvents; EventPlayback replays them via a handler.",
                align="left",
            )
        )
        info_lbl.font_role = self.font_role("label")
        controls.append(info_lbl)
        y += 28

        self._event_status_label = self.window.add(
            LabelControl(
                "nsdf_evt_status",
                Rect(x, y, rect.width - pad * 2, 22),
                "Status: Idle — 0 events recorded",
                align="left",
            )
        )
        self._event_status_label.font_role = self.font_role("label")
        controls.append(self._event_status_label)
        y += 30

        btn_w, btn_gap = 120, 8
        record_btn = self.window.add(
            ButtonControl(
                "nsdf_evt_record",
                Rect(x, y, btn_w, 28),
                "Start Rec.",
                self._start_recording,
                font_role=self.font_role("control"),
            )
        )
        stop_btn = self.window.add(
            ButtonControl(
                "nsdf_evt_stop",
                Rect(x + btn_w + btn_gap, y, btn_w, 28),
                "Stop",
                self._stop_recording,
                font_role=self.font_role("control"),
            )
        )
        sim_btn = self.window.add(
            ButtonControl(
                "nsdf_evt_simulate",
                Rect(x + (btn_w + btn_gap) * 2, y, btn_w, 28),
                "Sim. Events",
                self._simulate_events,
                font_role=self.font_role("control"),
            )
        )
        play_btn = self.window.add(
            ButtonControl(
                "nsdf_evt_play",
                Rect(x + (btn_w + btn_gap) * 3, y, btn_w, 28),
                "Play Back",
                self._start_playback,
                font_role=self.font_role("control"),
            )
        )
        controls.extend([record_btn, stop_btn, sim_btn, play_btn])
        y += 40

        log_title = self.window.add(
            LabelControl(
                "nsdf_evt_log_title",
                Rect(x, y, rect.width - pad * 2, 20),
                "Event log:",
                align="left",
            )
        )
        log_title.font_role = self.font_role("label")
        controls.append(log_title)
        y += 24

        log_h = max(40, rect.bottom - y - pad)
        self._event_log_label = self.window.add(
            LabelControl(
                "nsdf_evt_log",
                Rect(x, y, rect.width - pad * 2, log_h),
                "No events recorded yet.",
                align="left",
            )
        )
        self._event_log_label.font_role = self.font_role("label")
        controls.append(self._event_log_label)
        return controls

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
        controls = []
        pad = 8
        x, y = rect.left + pad, rect.top + pad

        # PropertyRegistry / PropertyDescriptor demo
        prop_title = self.window.add(
            LabelControl(
                "nsdf_prop_title",
                Rect(x, y, rect.width - pad * 2, 22),
                "PropertyRegistry — registered descriptors for ButtonControl:",
                align="left",
            )
        )
        prop_title.font_role = self.font_role("label")
        controls.append(prop_title)
        y += 26

        # Register sample descriptors to demonstrate the API
        descs = [
            PropertyDescriptor(
                name="visible", label="Visible", type="bool",
                group="Appearance", owner_class=ButtonControl,
            ),
            PropertyDescriptor(
                name="enabled", label="Enabled", type="bool",
                group="Behaviour", owner_class=ButtonControl,
            ),
            PropertyDescriptor(
                name="text", label="Label Text", type="str",
                group="Content", owner_class=ButtonControl,
            ),
        ]
        for desc in descs:
            property_registry.register(ButtonControl, desc)

        for desc in property_registry.descriptors_for(ButtonControl):
            lbl = self.window.add(
                LabelControl(
                    f"nsdf_prop_{desc.name}",
                    Rect(x, y, rect.width - pad * 2, 20),
                    f"  [{desc.group}] {desc.label} : {desc.type}",
                    align="left",
                )
            )
            lbl.font_role = self.font_role("label")
            controls.append(lbl)
            y += 21

        y += 8

        # SceneSnapshot demo
        snap_title = self.window.add(
            LabelControl(
                "nsdf_snap_title",
                Rect(x, y, rect.width - pad * 2, 22),
                "SceneSnapshot — capture & restore window rect:",
                align="left",
            )
        )
        snap_title.font_role = self.font_role("label")
        controls.append(snap_title)
        y += 26

        capture_btn = self.window.add(
            ButtonControl(
                "nsdf_snap_capture",
                Rect(x, y, 110, 28),
                "Capture",
                self._capture_snapshot,
                font_role=self.font_role("control"),
            )
        )
        restore_btn = self.window.add(
            ButtonControl(
                "nsdf_snap_restore",
                Rect(x + 118, y, 110, 28),
                "Restore",
                self._restore_snapshot,
                font_role=self.font_role("control"),
            )
        )
        controls.extend([capture_btn, restore_btn])
        y += 36

        self._snapshot_label = self.window.add(
            LabelControl(
                "nsdf_snap_label",
                Rect(x, y, rect.width - pad * 2, 22),
                "No snapshot captured yet.",
                align="left",
            )
        )
        self._snapshot_label.font_role = self.font_role("label")
        controls.append(self._snapshot_label)
        y += 30

        # SceneSpatialIndex demo
        spatial_title = self.window.add(
            LabelControl(
                "nsdf_spatial_title",
                Rect(x, y, rect.width - pad * 2, 22),
                "SceneSpatialIndex — build from scene, then hit-test:",
                align="left",
            )
        )
        spatial_title.font_role = self.font_role("label")
        controls.append(spatial_title)
        y += 26

        self._spatial_index = SceneSpatialIndex(cell_size=64)

        build_btn = self.window.add(
            ButtonControl(
                "nsdf_spatial_build",
                Rect(x, y, 160, 28),
                "Build & Query Center",
                self._build_and_query_spatial,
                font_role=self.font_role("control"),
            )
        )
        controls.append(build_btn)
        y += 36

        self._spatial_label = self.window.add(
            LabelControl(
                "nsdf_spatial_label",
                Rect(x, y, rect.width - pad * 2, 22),
                "Press 'Build & Query Center' to run.",
                align="left",
            )
        )
        self._spatial_label.font_role = self.font_role("label")
        controls.append(self._spatial_label)

        return controls

    # ------------------------------------------------------------------
    # Tab: Props — PropertyInspectorPanel
    # ------------------------------------------------------------------

    def _build_props_tab(self, host, rect: Rect) -> list:
        controls = []
        pad = 8
        x, y = rect.left + pad, rect.top + pad

        title = self.window.add(
            LabelControl(
                "nsdf_props_title",
                Rect(x, y, rect.width - pad * 2, 22),
                "PropertyInspectorPanel — inspect _DemoInspectable properties:",
                align="left",
            )
        )
        title.font_role = self.font_role("label")
        controls.append(title)
        y += 28

        hint = self.window.add(
            LabelControl(
                "nsdf_props_hint",
                Rect(x, y, rect.width - pad * 2, 20),
                "Click a property row to select it. Use refresh to re-read values.",
                align="left",
            )
        )
        hint.font_role = self.font_role("label")
        controls.append(hint)
        y += 26

        panel_h = max(120, rect.bottom - y - 60 - pad)
        self._prop_inspector_panel = self.window.add(
            PropertyInspectorPanel(
                "nsdf_prop_inspector",
                Rect(x, y, rect.width - pad * 2, panel_h),
                PropertyInspectorModel(self._demo_inspectable),
                on_select=self._on_prop_selected,
                font_role=self.font_role("label"),
            )
        )
        controls.append(self._prop_inspector_panel)
        y += panel_h + 6

        self._prop_selected_label = self.window.add(
            LabelControl(
                "nsdf_prop_selected",
                Rect(x, y, rect.width - pad * 2, 20),
                "Select a property above…",
                align="left",
            )
        )
        self._prop_selected_label.font_role = self.font_role("label")
        controls.append(self._prop_selected_label)
        y += 26

        refresh_btn = self.window.add(
            ButtonControl(
                "nsdf_props_refresh",
                Rect(x, y, 100, 28),
                "Refresh",
                self._refresh_prop_inspector,
                font_role=self.font_role("control"),
            )
        )
        controls.append(refresh_btn)

        return controls

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
        controls = []
        pad = 8
        x, y = rect.left + pad, rect.top + pad

        title = self.window.add(
            LabelControl(
                "nsdf_dock_title",
                Rect(x, y, rect.width - pad * 2, 22),
                "DockWorkspacePanel — interactive tab bar backed by DockWorkspace model:",
                align="left",
            )
        )
        title.font_role = self.font_role("label")
        controls.append(title)
        y += 28

        hint = self.window.add(
            LabelControl(
                "nsdf_dock_hint",
                Rect(x, y, rect.width - pad * 2, 20),
                "Click a tab below to switch the active pane.",
                align="left",
            )
        )
        hint.font_role = self.font_role("label")
        controls.append(hint)
        y += 26

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
        self._dock_panel = self.window.add(
            DockWorkspacePanel(
                "nsdf_dock_panel",
                Rect(x, y, rect.width - pad * 2, panel_h),
                self._dock_workspace,
                on_change=self._on_dock_pane_changed,
                font_role=self.font_role("control"),
            )
        )
        controls.append(self._dock_panel)
        y += panel_h + 12

        self._dock_active_label = self.window.add(
            LabelControl(
                "nsdf_dock_active",
                Rect(x, y, rect.width - pad * 2, 20),
                "Active pane: editor",
                align="left",
            )
        )
        self._dock_active_label.font_role = self.font_role("label")
        controls.append(self._dock_active_label)
        y += 26

        # Buttons: add/remove pane
        add_btn = self.window.add(
            ButtonControl(
                "nsdf_dock_add",
                Rect(x, y, 120, 28),
                "Add Extra Pane",
                self._dock_add_pane,
                font_role=self.font_role("control"),
            )
        )
        remove_btn = self.window.add(
            ButtonControl(
                "nsdf_dock_remove",
                Rect(x + 128, y, 120, 28),
                "Remove Active",
                self._dock_remove_active,
                font_role=self.font_role("control"),
            )
        )
        controls.extend([add_btn, remove_btn])
        y += 36

        # Show serialized model
        model_title = self.window.add(
            LabelControl(
                "nsdf_dock_model_title",
                Rect(x, y, rect.width - pad * 2, 20),
                "DockWorkspace.to_dict() — model serializes cleanly:",
                align="left",
            )
        )
        model_title.font_role = self.font_role("label")
        controls.append(model_title)
        y += 24

        self._dock_model_label = self.window.add(
            LabelControl(
                "nsdf_dock_model_label",
                Rect(x, y, rect.width - pad * 2, 20),
                self._dock_model_summary(),
                align="left",
            )
        )
        self._dock_model_label.font_role = self.font_role("label")
        controls.append(self._dock_model_label)

        return controls

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
            self.window.rect = Rect(entry.rect)
            if self._snapshot_label is not None:
                self._snapshot_label.text = (
                    f"Restored: window moved to {entry.rect.topleft}"
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
        controls = []
        pad = 8
        x, y = rect.left + pad, rect.top + pad

        info = self.window.add(
            LabelControl(
                "nsdf_particle_info",
                Rect(x, y, rect.width - pad * 2, 20),
                "ParticleSystem — live GPU-free particle simulation.  Add/burst emitters below.",
                align="left",
            )
        )
        info.font_role = self.font_role("label")
        controls.append(info)
        y += 26

        self._particle_count_label = self.window.add(
            LabelControl(
                "nsdf_particle_count",
                Rect(x, y, rect.width - pad * 2, 22),
                "Live particles: 0  Emitters: 0",
                align="left",
            )
        )
        self._particle_count_label.font_role = self.font_role("label")
        controls.append(self._particle_count_label)
        y += 30

        btn_gap = 8
        add_btn = self.window.add(
            ButtonControl(
                "nsdf_particle_add",
                Rect(x, y, 130, 28),
                "Add Emitter",
                self._particle_add_emitter,
                font_role=self.font_role("control"),
            )
        )
        burst_btn = self.window.add(
            ButtonControl(
                "nsdf_particle_burst",
                Rect(x + 138, y, 130, 28),
                "Burst (50)",
                self._particle_burst,
                font_role=self.font_role("control"),
            )
        )
        clear_btn = self.window.add(
            ButtonControl(
                "nsdf_particle_clear",
                Rect(x + 276, y, 130, 28),
                "Clear Emitters",
                self._particle_clear,
                font_role=self.font_role("control"),
            )
        )
        controls.extend([add_btn, burst_btn, clear_btn])
        y += 38

        canvas_h = max(60, rect.bottom - y - pad)
        self._particle_canvas = self.window.add(
            CanvasControl("nsdf_particle_canvas", Rect(x, y, rect.width - pad * 2, canvas_h))
        )
        controls.append(self._particle_canvas)

        # Build particle layer (owns its own ParticleSystem)
        self._particle_layer = ParticleLayer(
            "nsdf_particle_layer",
            Rect(x, y, rect.width - pad * 2, canvas_h),
        )
        self._particle_system = self._particle_layer.particle_system
        return controls

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
        controls = []
        pad = 8
        x, y = rect.left + pad, rect.top + pad

        info = self.window.add(
            LabelControl(
                "nsdf_sprite_info",
                Rect(x, y, rect.width - pad * 2, 40),
                "SpriteSheet slices an atlas into frames.  FrameAnimation drives playback.\n"
                "AnimatedImageControl renders the active frame as a scene-graph node.",
                align="left",
            )
        )
        info.font_role = self.font_role("label")
        controls.append(info)
        y += 50

        # Build a four-frame colored atlas
        FW, FH = 64, 64
        _atlas = _pygame.Surface((FW * 4, FH), flags=_pygame.SRCALPHA)
        for fi, col in enumerate([(220, 60, 60, 255), (60, 220, 60, 255), (60, 60, 220, 255), (220, 200, 40, 255)]):
            _atlas.fill(col, Rect(fi * FW, 0, FW, FH))
        sheet = SpriteSheet(_atlas, frame_w=FW, frame_h=FH)
        self._sprite_anim = FrameAnimation(sheet, frames=list(range(4)), fps=3, loop=True)
        ctrl_w, ctrl_h = min(200, rect.width - pad * 2), 80
        self._sprite_ctrl = self.window.add(
            AnimatedImageControl(
                "nsdf_sprite_ctrl",
                Rect(x, y, ctrl_w, ctrl_h),
                animation=self._sprite_anim,
                scale=True,
            )
        )
        controls.append(self._sprite_ctrl)
        y += ctrl_h + 12

        sheet_info = self.window.add(
            LabelControl(
                "nsdf_sprite_sheet_info",
                Rect(x, y, rect.width - pad * 2, 22),
                f"SpriteSheet: {sheet.frame_count} frames  ({FW}×{FH} px each)",
                align="left",
            )
        )
        sheet_info.font_role = self.font_role("label")
        controls.append(sheet_info)
        y += 28

        play_btn = self.window.add(
            ButtonControl(
                "nsdf_sprite_play",
                Rect(x, y, 90, 28),
                "Play",
                lambda: self._sprite_anim.play() if self._sprite_anim else None,
                font_role=self.font_role("control"),
            )
        )
        pause_btn = self.window.add(
            ButtonControl(
                "nsdf_sprite_pause",
                Rect(x + 98, y, 90, 28),
                "Pause",
                lambda: self._sprite_anim.pause() if self._sprite_anim else None,
                font_role=self.font_role("control"),
            )
        )
        reset_btn = self.window.add(
            ButtonControl(
                "nsdf_sprite_reset",
                Rect(x + 196, y, 90, 28),
                "Reset",
                lambda: self._sprite_anim.reset() if self._sprite_anim else None,
                font_role=self.font_role("control"),
            )
        )
        controls.extend([play_btn, pause_btn, reset_btn])
        return controls

    # ------------------------------------------------------------------
    # Tab: Sched — CooperativeScheduler + Pause + Sleep + WaitUntil
    # ------------------------------------------------------------------

    def _build_sched_tab(self, host, rect: Rect) -> list:
        controls = []
        pad = 8
        x, y = rect.left + pad, rect.top + pad

        self._scheduler = CooperativeScheduler()

        info = self.window.add(
            LabelControl(
                "nsdf_sched_info",
                Rect(x, y, rect.width - pad * 2, 40),
                "CooperativeScheduler runs generator coroutines on the frame thread.\n"
                "Yield Pause, Sleep(s), or WaitUntil(predicate) to suspend.",
                align="left",
            )
        )
        info.font_role = self.font_role("label")
        controls.append(info)
        y += 50

        self._sched_step_label = self.window.add(
            LabelControl(
                "nsdf_sched_step",
                Rect(x, y, rect.width - pad * 2, 22),
                "Active coroutines: 0",
                align="left",
            )
        )
        self._sched_step_label.font_role = self.font_role("label")
        controls.append(self._sched_step_label)
        y += 30

        self._sched_log_label = self.window.add(
            LabelControl(
                "nsdf_sched_log",
                Rect(x, y, rect.width - pad * 2, max(40, rect.bottom - y - 50)),
                "Press a button to start a coroutine…",
                align="left",
            )
        )
        self._sched_log_label.font_role = self.font_role("label")
        controls.append(self._sched_log_label)
        log_bottom = y + max(40, rect.bottom - y - 50)

        btn_y = log_bottom + 4
        start_btn = self.window.add(
            ButtonControl(
                "nsdf_sched_start",
                Rect(x, btn_y, 140, 28),
                "Start Sequence",
                self._sched_start_sequence,
                font_role=self.font_role("control"),
            )
        )
        cancel_btn = self.window.add(
            ButtonControl(
                "nsdf_sched_cancel",
                Rect(x + 148, btn_y, 140, 28),
                "Cancel All",
                self._sched_cancel_all,
                font_role=self.font_role("control"),
            )
        )
        controls.extend([start_btn, cancel_btn])
        return controls

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
        controls = []
        pad = 8
        x, y = rect.left + pad, rect.top + pad

        info = self.window.add(
            LabelControl(
                "nsdf_tilemap_info",
                Rect(x, y, rect.width - pad * 2, 40),
                "TileSet slices an atlas into tile surfaces.  TileMap renders only visible tiles.\n"
                "Camera culling is automatic via visible_range().",
                align="left",
            )
        )
        info.font_role = self.font_role("label")
        controls.append(info)
        y += 50

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

        canvas_h = max(60, rect.bottom - y - 60)
        self._tile_canvas = self.window.add(
            CanvasControl("nsdf_tile_canvas", Rect(x, y, rect.width - pad * 2, canvas_h))
        )
        controls.append(self._tile_canvas)
        self._tile_dirty = True
        y += canvas_h + 8

        tile_info = self.window.add(
            LabelControl(
                "nsdf_tilemap_detail",
                Rect(x, y, rect.width - pad * 2, 22),
                f"TileSet: {tile_set.tile_count} tiles  |  TileMap: {COLS}×{ROWS} ({COLS * ROWS} cells)",
                align="left",
            )
        )
        tile_info.font_role = self.font_role("label")
        controls.append(tile_info)
        return controls

    # ------------------------------------------------------------------
    # Tab: Progress — ProgressBarControl
    # ------------------------------------------------------------------

    def _build_progress_tab(self, host, rect: Rect) -> list:
        controls = []
        pad = 8
        x, y = rect.left + pad, rect.top + pad

        info = self.window.add(
            LabelControl(
                "nsdf_progress_info",
                Rect(x, y, rect.width - pad * 2, 20),
                "ProgressBarControl — determinate (0–1) and indeterminate (marquee) modes.",
                align="left",
            )
        )
        info.font_role = self.font_role("label")
        controls.append(info)
        y += 30

        det_lbl = self.window.add(
            LabelControl("nsdf_prog_det_lbl", Rect(x, y, rect.width - pad * 2, 18), "Determinate (value=0.72):", align="left")
        )
        det_lbl.font_role = self.font_role("label")
        controls.append(det_lbl)
        y += 22

        self._progress_bar = self.window.add(
            ProgressBarControl(
                "nsdf_progress_bar",
                Rect(x, y, rect.width - pad * 2, 18),
                value=0.72,
            )
        )
        controls.append(self._progress_bar)
        y += 30

        indet_lbl = self.window.add(
            LabelControl("nsdf_prog_indet_lbl", Rect(x, y, rect.width - pad * 2, 18), "Indeterminate (marquee):", align="left")
        )
        indet_lbl.font_role = self.font_role("label")
        controls.append(indet_lbl)
        y += 22

        self._progress_indeterminate = self.window.add(
            ProgressBarControl(
                "nsdf_progress_indet",
                Rect(x, y, rect.width - pad * 2, 18),
                indeterminate=True,
            )
        )
        controls.append(self._progress_indeterminate)
        y += 30

        self._progress_label = self.window.add(
            LabelControl(
                "nsdf_progress_val_lbl",
                Rect(x, y, rect.width - pad * 2, 22),
                "Adjust value:",
                align="left",
            )
        )
        self._progress_label.font_role = self.font_role("label")
        controls.append(self._progress_label)
        y += 28

        btn_gap = 8
        for step_pct, label in [(0, "0%"), (25, "25%"), (50, "50%"), (75, "75%"), (100, "100%")]:
            btn = self.window.add(
                ButtonControl(
                    f"nsdf_prog_set_{step_pct}",
                    Rect(x, y, 70, 26),
                    label,
                    self._make_progress_setter(step_pct / 100.0),
                    font_role=self.font_role("control"),
                )
            )
            controls.append(btn)
            x += 78
        x = rect.left + pad
        return controls

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
        controls = []
        pad = 8
        x, y = rect.left + pad, rect.top + pad

        info = self.window.add(
            LabelControl(
                "nsdf_flow_info",
                Rect(x, y, rect.width - pad * 2, 40),
                "FlowLayout arranges FlowItem nodes left-to-right with automatic row wrapping.\n"
                "Items here are LabelControls sized as tags.  Add/clear to see layout reflow.",
                align="left",
            )
        )
        info.font_role = self.font_role("label")
        controls.append(info)
        y += 50

        self._flow_result_label = self.window.add(
            LabelControl(
                "nsdf_flow_result",
                Rect(x, y, rect.width - pad * 2, 22),
                "Row info will appear here after layout runs.",
                align="left",
            )
        )
        self._flow_result_label.font_role = self.font_role("label")
        controls.append(self._flow_result_label)
        y += 30

        add_btn = self.window.add(
            ButtonControl(
                "nsdf_flow_add",
                Rect(x, y, 110, 28),
                "Add Item",
                self._flow_add_item,
                font_role=self.font_role("control"),
            )
        )
        clear_btn = self.window.add(
            ButtonControl(
                "nsdf_flow_clear",
                Rect(x + 118, y, 110, 28),
                "Clear Items",
                self._flow_clear_items,
                font_role=self.font_role("control"),
            )
        )
        layout_btn = self.window.add(
            ButtonControl(
                "nsdf_flow_layout",
                Rect(x + 236, y, 110, 28),
                "Apply Layout",
                self._flow_apply_layout,
                font_role=self.font_role("control"),
            )
        )
        controls.extend([add_btn, clear_btn, layout_btn])
        y += 36

        self._flow_layout = FlowLayout(gap_x=8, gap_y=6)
        self._flow_items_rect = Rect(x, y, rect.width - pad * 2, max(60, rect.bottom - y - pad))
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
        controls.extend(self._flow_items)
        return controls

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
        lbl.font_role = self.font_role("label")
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
        controls = []
        pad = 8
        x, y = rect.left + pad, rect.top + pad

        DEMO_TEXT = (
            "TextSearcher wraps Python regex to provide case-insensitive, whole-word, "
            "and full-regex search over a string.  Type a query below to find matches."
        )
        self._searcher = TextSearcher(DEMO_TEXT, case_sensitive=False)

        info = self.window.add(
            LabelControl(
                "nsdf_search_source",
                Rect(x, y, rect.width - pad * 2, 50),
                f'Search target:\n"{DEMO_TEXT[:80]}…"',
                align="left",
            )
        )
        info.font_role = self.font_role("label")
        controls.append(info)
        y += 58

        query_lbl = self.window.add(
            LabelControl("nsdf_search_lbl", Rect(x, y, 60, 26), "Query:", align="left")
        )
        query_lbl.font_role = self.font_role("label")
        controls.append(query_lbl)

        self._search_input = self.window.add(
            TextInputControl(
                "nsdf_search_input",
                Rect(x + 68, y, min(260, rect.width - pad * 2 - 68), 28),
                placeholder="enter search term…",
                on_change=self._on_search_changed,
                font_role=self.font_role("control"),
            )
        )
        controls.append(self._search_input)
        y += 36

        self._search_result_label = self.window.add(
            LabelControl(
                "nsdf_search_result",
                Rect(x, y, rect.width - pad * 2, max(40, rect.bottom - y - pad)),
                "Results appear here…",
                align="left",
            )
        )
        self._search_result_label.font_role = self.font_role("label")
        controls.append(self._search_result_label)
        return controls

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
        controls = []
        pad = 8
        x, y = rect.left + pad, rect.top + pad

        info = self.window.add(
            LabelControl(
                "nsdf_listdiff_info",
                Rect(x, y, rect.width - pad * 2, 20),
                "ListDiffCalculator.diff(old, new) returns DiffInsert / DiffRemove / DiffMove ops.",
                align="left",
            )
        )
        info.font_role = self.font_role("label")
        controls.append(info)
        y += 28

        old_lbl = self.window.add(
            LabelControl(
                "nsdf_listdiff_old",
                Rect(x, y, rect.width - pad * 2, 22),
                f"Old: {self._listdiff_old}",
                align="left",
            )
        )
        old_lbl.font_role = self.font_role("label")
        controls.append(old_lbl)
        y += 26

        new_lbl = self.window.add(
            LabelControl(
                "nsdf_listdiff_new",
                Rect(x, y, rect.width - pad * 2, 22),
                f"New: {self._listdiff_new}",
                align="left",
            )
        )
        new_lbl.font_role = self.font_role("label")
        controls.append(new_lbl)
        y += 30

        run_btn = self.window.add(
            ButtonControl(
                "nsdf_listdiff_run",
                Rect(x, y, 130, 28),
                "Compute Diff",
                self._run_listdiff,
                font_role=self.font_role("control"),
            )
        )
        apply_btn = self.window.add(
            ButtonControl(
                "nsdf_listdiff_apply",
                Rect(x + 138, y, 130, 28),
                "Apply & Show",
                self._apply_listdiff,
                font_role=self.font_role("control"),
            )
        )
        controls.extend([run_btn, apply_btn])
        y += 38

        self._listdiff_result_label = self.window.add(
            LabelControl(
                "nsdf_listdiff_result",
                Rect(x, y, rect.width - pad * 2, max(60, rect.bottom - y - pad)),
                "Press 'Compute Diff' to see operations.",
                align="left",
            )
        )
        self._listdiff_result_label.font_role = self.font_role("label")
        controls.append(self._listdiff_result_label)
        return controls

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
        controls = []
        pad = 8
        x, y = rect.left + pad, rect.top + pad

        self._cache = DataCache(max_size=5)
        # Pre-populate
        for k, v in [("user:1", "Alice"), ("user:2", "Bob"), ("user:3", "Carol")]:
            self._cache.put(k, v)

        info = self.window.add(
            LabelControl(
                "nsdf_cache_info",
                Rect(x, y, rect.width - pad * 2, 20),
                "DataCache — LRU cache (max_size=5) with reactive on_evicted/on_invalidated signals.",
                align="left",
            )
        )
        info.font_role = self.font_role("label")
        controls.append(info)
        y += 28

        self._cache_stats_label = self.window.add(
            LabelControl(
                "nsdf_cache_stats",
                Rect(x, y, rect.width - pad * 2, 60),
                self._cache_stats_text(),
                align="left",
            )
        )
        self._cache_stats_label.font_role = self.font_role("label")
        controls.append(self._cache_stats_label)
        y += 68

        btn_gap = 8
        get_btn = self.window.add(
            ButtonControl(
                "nsdf_cache_get",
                Rect(x, y, 110, 28),
                "Get user:1",
                self._cache_get_user1,
                font_role=self.font_role("control"),
            )
        )
        miss_btn = self.window.add(
            ButtonControl(
                "nsdf_cache_miss",
                Rect(x + 118, y, 110, 28),
                "Miss user:99",
                self._cache_miss,
                font_role=self.font_role("control"),
            )
        )
        evict_btn = self.window.add(
            ButtonControl(
                "nsdf_cache_evict",
                Rect(x + 236, y, 130, 28),
                "Fill (cause evict)",
                self._cache_fill,
                font_role=self.font_role("control"),
            )
        )
        inval_btn = self.window.add(
            ButtonControl(
                "nsdf_cache_inval",
                Rect(x, y + 36, 130, 28),
                "Invalidate user:2",
                self._cache_invalidate,
                font_role=self.font_role("control"),
            )
        )
        controls.extend([get_btn, miss_btn, evict_btn, inval_btn])
        return controls

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
        controls = []
        pad = 8
        x, y = rect.left + pad, rect.top + pad

        info = self.window.add(
            LabelControl(
                "nsdf_shortcuts_info",
                Rect(x, y, rect.width - pad * 2, 40),
                "ShortcutHelpOverlay reads ActionRegistry + KeyChordManager and renders\n"
                "a structured shortcut reference panel via the OverlayManager.",
                align="left",
            )
        )
        info.font_role = self.font_role("label")
        controls.append(info)
        y += 50

        show_btn = self.window.add(
            ButtonControl(
                "nsdf_shortcuts_show",
                Rect(x, y, 150, 28),
                "Show Help Overlay",
                self._shortcuts_show_overlay,
                font_role=self.font_role("control"),
            )
        )
        controls.append(show_btn)
        y += 38

        self._shortcut_info_label = self.window.add(
            LabelControl(
                "nsdf_shortcuts_detail",
                Rect(x, y, rect.width - pad * 2, max(60, rect.bottom - y - pad)),
                "Overlay not yet opened — click 'Show Help Overlay' to display it.\n"
                "ShortcutHelpOverlay.sections builds structured data from ActionRegistry.",
                align="left",
            )
        )
        self._shortcut_info_label.font_role = self.font_role("label")
        controls.append(self._shortcut_info_label)
        return controls

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
        self._main_scene = host.app.create_scene("main")
        self._frame_timer.reset()
        # Build ShortcutHelpOverlay once overlay manager is available
        action_registry = getattr(host, "action_registry", None)
        overlay_rect = Rect(
            max(0, host.app.surface.get_width() // 2 - 280),
            max(0, host.app.surface.get_height() // 2 - 200),
            560,
            400,
        )
        self._shortcut_overlay = ShortcutHelpOverlay(
            host.app.overlay,
            action_registry=action_registry,
            overlay_rect=overlay_rect,
        )


class _SystemsWindowPresenter(WindowPresenter):

    def __init__(self, feature, host):
        super().__init__(None)
        self.feature = feature
        self.host = host
        self.tab = None

    def on_create(self):
        content = self.window.content_rect()
        pad = 0
        body_top = content.top + pad
        body_bottom = content.bottom - pad
        body_h = body_bottom - body_top
        body_content_top = body_top + 36 * 2  # _TAB_H * 2
        body_content_h = max(60, body_bottom - body_content_top)
        body_rect = Rect(content.left + pad, body_top, content.width - pad * 2, body_h)
        body_content_rect = Rect(
            content.left + pad, body_content_top, content.width - pad * 2, body_content_h
        )
        self.tab = TabControl(
            "nsdf_tab",
            body_rect,
            items=[
                TabItem("filter", "Filter"),
                TabItem("locale", "Locale"),
                TabItem("input", "Input"),
                TabItem("event", "Event"),
                TabItem("inspect", "Inspect"),
                TabItem("props", "Props"),
                TabItem("dock", "Dock"),
                TabItem("particle", "Particle"),
                TabItem("sprite", "Sprite"),
                TabItem("sched", "Sched"),
                TabItem("tilemap", "TileMap"),
                TabItem("progress", "Progress"),
                TabItem("flow", "Flow"),
                TabItem("search", "Search"),
                TabItem("listdiff", "ListDiff"),
                TabItem("cache", "Cache"),
                TabItem("shortcuts", "Shortcuts"),
            ],
            selected_key="filter",
            on_change=self.feature._on_tab_change,
            font_role=self.feature.font_role("control"),
        )
        self.add_control(self.tab)
        self.feature.tab = self.tab
        self.feature._tabs.register("filter", self.feature._build_filter_tab(self.host, Rect(body_content_rect)))
        self.feature._tabs.register("locale", self.feature._build_locale_tab(self.host, Rect(body_content_rect)))
        self.feature._tabs.register("input", self.feature._build_input_tab(self.host, Rect(body_content_rect)))
        self.feature._tabs.register("event", self.feature._build_event_tab(self.host, Rect(body_content_rect)))
        self.feature._tabs.register("inspect", self.feature._build_inspect_tab(self.host, Rect(body_content_rect)))
        self.feature._tabs.register("props", self.feature._build_props_tab(self.host, Rect(body_content_rect)))
        self.feature._tabs.register("dock", self.feature._build_dock_tab(self.host, Rect(body_content_rect)))
        self.feature._tabs.register("particle", self.feature._build_particle_tab(self.host, Rect(body_content_rect)))
        self.feature._tabs.register("sprite", self.feature._build_sprite_tab(self.host, Rect(body_content_rect)))
        self.feature._tabs.register("sched", self.feature._build_sched_tab(self.host, Rect(body_content_rect)))
        self.feature._tabs.register("tilemap", self.feature._build_tilemap_tab(self.host, Rect(body_content_rect)))
        self.feature._tabs.register("progress", self.feature._build_progress_tab(self.host, Rect(body_content_rect)))
        self.feature._tabs.register("flow", self.feature._build_flow_tab(self.host, Rect(body_content_rect)))
        self.feature._tabs.register("search", self.feature._build_search_tab(self.host, Rect(body_content_rect)))
        self.feature._tabs.register("listdiff", self.feature._build_listdiff_tab(self.host, Rect(body_content_rect)))
        self.feature._tabs.register("cache", self.feature._build_cache_tab(self.host, Rect(body_content_rect)))
        self.feature._tabs.register("shortcuts", self.feature._build_shortcuts_tab(self.host, Rect(body_content_rect)))
        self.feature._tabs.on_activate("locale", lambda: setattr(self.feature, "_text_flow_dirty", True))
        self.feature.window = self.window
        self.feature.demo = self.host
        self.window.visible = False
