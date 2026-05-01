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
from demo_features.feature_abstractions import (
    bind_input_map_actions,
    create_presented_anchored_window,
    initialize_locale_registry,
    register_descriptors,
    register_window_tab_builders,
)

_TAB_H = 36

_SYSTEMS_TAB_SPECS = (
    ("filter", "Filter", "_build_filter_tab"),
    ("locale", "Locale", "_build_locale_tab"),
    ("input", "Input", "_build_input_tab"),
    ("event", "Event", "_build_event_tab"),
    ("inspect", "Inspect", "_build_inspect_tab"),
    ("props", "Props", "_build_props_tab"),
    ("dock", "Dock", "_build_dock_tab"),
    ("particle", "Particle", "_build_particle_tab"),
    ("sprite", "Sprite", "_build_sprite_tab"),
    ("sched", "Sched", "_build_sched_tab"),
    ("tilemap", "TileMap", "_build_tilemap_tab"),
    ("progress", "Progress", "_build_progress_tab"),
    ("flow", "Flow", "_build_flow_tab"),
    ("search", "Search", "_build_search_tab"),
    ("listdiff", "ListDiff", "_build_listdiff_tab"),
    ("cache", "Cache", "_build_cache_tab"),
    ("shortcuts", "Shortcuts", "_build_shortcuts_tab"),
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
        presenter = _SystemsWindowPresenter(self, host)
        self.window = create_presented_anchored_window(
            host,
            control_id="systems_window",
            title="System",
            size=(820, 590),
            anchor="top_left",
            margin=(24, 92),
            presenter=presenter,
            window_control_cls=WindowControl,
            use_frame_backdrop=True,
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

        info_lbl = self._add_tab_label(
            controls,
            "nsdf_filter_info",
            Rect(x, y, rect.width - pad * 2, 20),
            "SortFilterProxySource wraps any VirtualItemSource with reactive filter + sort.",
        )
        y += 28

        filter_lbl = self._add_tab_label(
            controls,
            "nsdf_filter_lbl",
            Rect(x, y, 60, 26),
            "Filter:",
        )

        filter_input = self._add_tab_control(
            controls,
            TextInputControl(
                "nsdf_filter_input",
                Rect(x + 68, y, 200, 28),
                placeholder="type prefix...",
                on_change=self._on_filter_changed,
            )
        )
        y += 36

        sort_toggle = self._add_tab_control(
            controls,
            ToggleControl(
                "nsdf_sort_toggle",
                Rect(x, y, 130, 28),
                "Sort: A→Z",
                "Sort: Z→A",
                pushed=False,
                on_toggle=self._on_sort_toggled,
                style="round",
            )
        )
        y += 38

        result_title = self._add_tab_label(
            controls,
            "nsdf_filter_result_title",
            Rect(x, y, rect.width - pad * 2, 20),
            "Proxy output:",
        )
        y += 24

        self._filter_label = self._add_tab_label(
            controls,
            "nsdf_filter_result_lbl",
            Rect(x, y, rect.width - pad * 2, max(40, rect.bottom - y - pad)),
            "",
        )
        _ = (info_lbl, filter_lbl, filter_input, sort_toggle, result_title)

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

        self._locale_registry = initialize_locale_registry(
            [StringTable(locale_id, strings) for locale_id, strings in _LOCALE_TABLE_SPECS],
            initial_locale="en",
        )

        locale_lbl = self._add_tab_label(
            controls,
            "nsdf_locale_lbl",
            Rect(x, y, 80, 26),
            "Locale:",
        )

        for i, (locale_id, locale_name) in enumerate(_LOCALE_BUTTON_SPECS):
            _ = self._add_tab_button(
                controls,
                f"nsdf_locale_btn_{locale_id}",
                Rect(x + 90 + i * 60, y, 52, 28),
                locale_name,
                self._make_locale_setter(locale_id),
            )
        y += 36

        self._greeting_label = self._add_tab_label(
            controls,
            "nsdf_greeting_lbl",
            Rect(x, y, rect.width - pad * 2, 26),
            self._locale_registry.t("greeting"),
        )
        y += 34

        canvas_lbl = self._add_tab_label(
            controls,
            "nsdf_canvas_lbl",
            Rect(x, y, rect.width - pad * 2, 20),
            "TextFlow rendering (word-wrapped, mixed-style):",
        )
        y += 24

        canvas_h = max(60, rect.bottom - y - pad)
        self._text_canvas = self._add_tab_control(
            controls,
            CanvasControl("nsdf_text_canvas", Rect(x, y, rect.width - pad * 2, canvas_h)),
        )
        _ = (locale_lbl, canvas_lbl)

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
        for action, key, label in _INPUT_DECLARE_SPECS:
            self._input_map.declare(action, key=key, mod=0, label=label)

        title_lbl = self._add_tab_label(
            controls,
            "nsdf_input_title",
            Rect(x, y, rect.width - pad * 2, 22),
            "InputMap — declared action bindings:",
        )
        y += 26

        self._binding_labels = []
        for binding in self._input_map.bindings():
            key_name = pygame.key.name(binding.key) if binding.key else "?"
            text = f"  {binding.label}: {key_name}"
            lbl = self._add_tab_label(
                controls,
                f"nsdf_binding_{binding.action}",
                Rect(x, y, rect.width - pad * 2, 22),
                text,
            )
            self._binding_labels.append(lbl)
            y += 23

        y += 6
        remap_btn = self._add_tab_button(
            controls,
            "nsdf_input_remap_btn",
            Rect(x, y, 150, 28),
            "Remap: W/A/S/D",
            self._remap_bindings,
        )
        y += 36

        reset_btn = self._add_tab_button(
            controls,
            "nsdf_input_reset_btn",
            Rect(x, y, 150, 28),
            "Reset to Arrows",
            self._reset_bindings,
        )
        y += 44

        resp_title = self._add_tab_label(
            controls,
            "nsdf_resp_title",
            Rect(x, y, rect.width - pad * 2, 22),
            "ResponsiveLayout — breakpoints based on window width:",
        )
        y += 26

        self._layout_label = self._add_tab_label(
            controls,
            "nsdf_layout_lbl",
            Rect(x, y, rect.width - pad * 2, 22),
            "Active breakpoint: (updating...)",
        )
        _ = (title_lbl, remap_btn, reset_btn, resp_title)

        self._responsive = ResponsiveLayout()
        self._responsive.add_breakpoint(Breakpoint("narrow", min_width=0, layout=None))
        self._responsive.add_breakpoint(Breakpoint("standard", min_width=600, layout=None))
        self._responsive.add_breakpoint(Breakpoint("wide", min_width=900, layout=None))

        return controls

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
            key_name = pygame.key.name(binding.key) if binding.key else "?"
            lbl.text = f"  {binding.label}: {key_name}"

    def _add_tab_control(self, controls: list, control):
        """Add a control to the window and tab-control collection in one call."""
        added = self.window.add(control)
        controls.append(added)
        return added

    def _add_tab_label(self, controls: list, control_id: str, rect: Rect, text: str):
        """Convenience wrapper for left-aligned tab labels."""
        return self._add_tab_control(
            controls,
            LabelControl(str(control_id), Rect(rect), str(text), align="left"),
        )

    def _add_tab_button(self, controls: list, control_id: str, rect: Rect, text: str, on_click, *, style=None):
        """Convenience wrapper for tab buttons with optional style."""
        kwargs = {}
        if style is not None:
            kwargs["style"] = style
        return self._add_tab_control(
            controls,
            ButtonControl(str(control_id), Rect(rect), str(text), on_click, **kwargs),
        )

    def _add_tab_button_row(
        self,
        controls: list,
        *,
        x: int,
        y: int,
        width: int,
        height: int,
        gap: int,
        specs,
    ):
        """Add a horizontal row of tab buttons from (id, label, callback[, style]) specs."""
        buttons = []
        left = int(x)
        for spec in specs:
            if len(spec) == 3:
                control_id, label, on_click = spec
                style = None
            elif len(spec) == 4:
                control_id, label, on_click, style = spec
            else:
                raise ValueError("Button row spec must have 3 or 4 values")
            button = self._add_tab_button(
                controls,
                str(control_id),
                Rect(left, int(y), int(width), int(height)),
                str(label),
                on_click,
                style=style,
            )
            buttons.append(button)
            left += int(width) + int(gap)
        return tuple(buttons)

    # ------------------------------------------------------------------
    # Tab: Event — EventRecorder + EventPlayback + RecordedEvent
    # ------------------------------------------------------------------

    def _build_event_tab(self, host, rect: Rect) -> list:
        controls = []
        pad = 8
        x, y = rect.left + pad, rect.top + pad

        self._recorder = EventRecorder()

        info_lbl = self._add_tab_label(
            controls,
            "nsdf_evt_info",
            Rect(x, y, rect.width - pad * 2, 20),
            "EventRecorder captures GuiEvents; EventPlayback replays them via a handler.",
        )
        y += 28

        self._event_status_label = self._add_tab_label(
            controls,
            "nsdf_evt_status",
            Rect(x, y, rect.width - pad * 2, 22),
            "Status: Idle — 0 events recorded",
        )
        y += 30

        record_btn, stop_btn, sim_btn, play_btn = self._add_tab_button_row(
            controls,
            x=x,
            y=y,
            width=120,
            height=28,
            gap=8,
            specs=(
                ("nsdf_evt_record", "Start Rec.", self._start_recording),
                ("nsdf_evt_stop", "Stop", self._stop_recording),
                ("nsdf_evt_simulate", "Sim. Events", self._simulate_events),
                ("nsdf_evt_play", "Play Back", self._start_playback),
            ),
        )
        _ = (record_btn, stop_btn, sim_btn, play_btn)
        y += 40

        log_title = self._add_tab_label(
            controls,
            "nsdf_evt_log_title",
            Rect(x, y, rect.width - pad * 2, 20),
            "Event log:",
        )
        y += 24

        log_h = max(40, rect.bottom - y - pad)
        self._event_log_label = self._add_tab_label(
            controls,
            "nsdf_evt_log",
            Rect(x, y, rect.width - pad * 2, log_h),
            "No events recorded yet.",
        )
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
        prop_title = self._add_tab_label(
            controls,
            "nsdf_prop_title",
            Rect(x, y, rect.width - pad * 2, 22),
            "PropertyRegistry — registered descriptors for ButtonControl:",
        )
        y += 26

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
            lbl = self._add_tab_label(
                controls,
                f"nsdf_prop_{desc.name}",
                Rect(x, y, rect.width - pad * 2, 20),
                f"  [{desc.group}] {desc.label} : {desc.type}",
            )
            y += 21

        y += 8

        # SceneSnapshot demo
        snap_title = self._add_tab_label(
            controls,
            "nsdf_snap_title",
            Rect(x, y, rect.width - pad * 2, 22),
            "SceneSnapshot — capture & restore window rect:",
        )
        y += 26

        capture_btn = self._add_tab_button(
            controls,
            "nsdf_snap_capture",
            Rect(x, y, 110, 28),
            "Capture",
            self._capture_snapshot,
        )
        restore_btn = self._add_tab_button(
            controls,
            "nsdf_snap_restore",
            Rect(x + 118, y, 110, 28),
            "Restore",
            self._restore_snapshot,
        )
        _ = (capture_btn, restore_btn)
        y += 36

        self._snapshot_label = self._add_tab_label(
            controls,
            "nsdf_snap_label",
            Rect(x, y, rect.width - pad * 2, 22),
            "No snapshot captured yet.",
        )
        y += 30

        # SceneSpatialIndex demo
        spatial_title = self._add_tab_label(
            controls,
            "nsdf_spatial_title",
            Rect(x, y, rect.width - pad * 2, 22),
            "SceneSpatialIndex — build from scene, then hit-test:",
        )
        y += 26

        self._spatial_index = SceneSpatialIndex(cell_size=64)

        build_btn = self._add_tab_button(
            controls,
            "nsdf_spatial_build",
            Rect(x, y, 160, 28),
            "Build & Query Center",
            self._build_and_query_spatial,
        )
        _ = build_btn
        y += 36

        self._spatial_label = self._add_tab_label(
            controls,
            "nsdf_spatial_label",
            Rect(x, y, rect.width - pad * 2, 22),
            "Press 'Build & Query Center' to run.",
        )

        return controls

    # ------------------------------------------------------------------
    # Tab: Props — PropertyInspectorPanel
    # ------------------------------------------------------------------

    def _build_props_tab(self, host, rect: Rect) -> list:
        controls = []
        pad = 8
        x, y = rect.left + pad, rect.top + pad

        title = self._add_tab_label(
            controls,
            "nsdf_props_title",
            Rect(x, y, rect.width - pad * 2, 22),
            "PropertyInspectorPanel — inspect _DemoInspectable properties:",
        )
        y += 28

        hint = self._add_tab_label(
            controls,
            "nsdf_props_hint",
            Rect(x, y, rect.width - pad * 2, 20),
            "Click a property row to select it. Use refresh to re-read values.",
        )
        y += 26

        panel_h = max(120, rect.bottom - y - 60 - pad)
        self._prop_inspector_panel = self._add_tab_control(
            controls,
            PropertyInspectorPanel(
                "nsdf_prop_inspector",
                Rect(x, y, rect.width - pad * 2, panel_h),
                PropertyInspectorModel(self._demo_inspectable),
                on_select=self._on_prop_selected,
            )
        )
        y += panel_h + 6

        self._prop_selected_label = self._add_tab_label(
            controls,
            "nsdf_prop_selected",
            Rect(x, y, rect.width - pad * 2, 20),
            "Select a property above…",
        )
        y += 26

        refresh_btn = self._add_tab_button(
            controls,
            "nsdf_props_refresh",
            Rect(x, y, 100, 28),
            "Refresh",
            self._refresh_prop_inspector,
        )
        _ = (title, hint, refresh_btn)

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

        title = self._add_tab_label(
            controls,
            "nsdf_dock_title",
            Rect(x, y, rect.width - pad * 2, 22),
            "DockWorkspacePanel — interactive tab bar backed by DockWorkspace model:",
        )
        y += 28

        hint = self._add_tab_label(
            controls,
            "nsdf_dock_hint",
            Rect(x, y, rect.width - pad * 2, 20),
            "Click a tab below to switch the active pane.",
        )
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
        self._dock_panel = self._add_tab_control(
            controls,
            DockWorkspacePanel(
                "nsdf_dock_panel",
                Rect(x, y, rect.width - pad * 2, panel_h),
                self._dock_workspace,
                on_change=self._on_dock_pane_changed,
            )
        )
        y += panel_h + 12

        self._dock_active_label = self._add_tab_label(
            controls,
            "nsdf_dock_active",
            Rect(x, y, rect.width - pad * 2, 20),
            "Active pane: editor",
        )
        y += 26

        # Buttons: add/remove pane
        add_btn, remove_btn = self._add_tab_button_row(
            controls,
            x=x,
            y=y,
            width=120,
            height=28,
            gap=8,
            specs=(
                ("nsdf_dock_add", "Add Extra Pane", self._dock_add_pane),
                ("nsdf_dock_remove", "Remove Active", self._dock_remove_active),
            ),
        )
        _ = (add_btn, remove_btn)
        y += 36

        # Show serialized model
        model_title = self._add_tab_label(
            controls,
            "nsdf_dock_model_title",
            Rect(x, y, rect.width - pad * 2, 20),
            "DockWorkspace.to_dict() — model serializes cleanly:",
        )
        y += 24

        self._dock_model_label = self._add_tab_label(
            controls,
            "nsdf_dock_model_label",
            Rect(x, y, rect.width - pad * 2, 20),
            self._dock_model_summary(),
        )
        _ = (title, hint, model_title)

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

        info = self._add_tab_label(
            controls,
            "nsdf_particle_info",
            Rect(x, y, rect.width - pad * 2, 20),
            "ParticleSystem — live GPU-free particle simulation.  Add/burst emitters below.",
        )
        y += 26

        self._particle_count_label = self._add_tab_label(
            controls,
            "nsdf_particle_count",
            Rect(x, y, rect.width - pad * 2, 22),
            "Live particles: 0  Emitters: 0",
        )
        y += 30

        add_btn, burst_btn, clear_btn = self._add_tab_button_row(
            controls,
            x=x,
            y=y,
            width=130,
            height=28,
            gap=8,
            specs=(
                ("nsdf_particle_add", "Add Emitter", self._particle_add_emitter),
                ("nsdf_particle_burst", "Burst (50)", self._particle_burst),
                ("nsdf_particle_clear", "Clear Emitters", self._particle_clear),
            ),
        )
        _ = (info, add_btn, burst_btn, clear_btn)
        y += 38

        canvas_h = max(60, rect.bottom - y - pad)
        self._particle_canvas = self._add_tab_control(
            controls,
            CanvasControl("nsdf_particle_canvas", Rect(x, y, rect.width - pad * 2, canvas_h)),
        )

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

        info = self._add_tab_label(
            controls,
            "nsdf_sprite_info",
            Rect(x, y, rect.width - pad * 2, 40),
            "SpriteSheet slices an atlas into frames.  FrameAnimation drives playback.\n"
            "AnimatedImageControl renders the active frame as a scene-graph node.",
        )
        y += 50

        # Build a four-frame colored atlas
        FW, FH = 64, 64
        _atlas = _pygame.Surface((FW * 4, FH), flags=_pygame.SRCALPHA)
        for fi, col in enumerate([(220, 60, 60, 255), (60, 220, 60, 255), (60, 60, 220, 255), (220, 200, 40, 255)]):
            _atlas.fill(col, Rect(fi * FW, 0, FW, FH))
        sheet = SpriteSheet(_atlas, frame_w=FW, frame_h=FH)
        self._sprite_anim = FrameAnimation(sheet, frames=list(range(4)), fps=3, loop=True)
        ctrl_w, ctrl_h = min(200, rect.width - pad * 2), 80
        self._sprite_ctrl = self._add_tab_control(
            controls,
            AnimatedImageControl(
                "nsdf_sprite_ctrl",
                Rect(x, y, ctrl_w, ctrl_h),
                animation=self._sprite_anim,
                scale=True,
            )
        )
        y += ctrl_h + 12

        sheet_info = self._add_tab_label(
            controls,
            "nsdf_sprite_sheet_info",
            Rect(x, y, rect.width - pad * 2, 22),
            f"SpriteSheet: {sheet.frame_count} frames  ({FW}×{FH} px each)",
        )
        y += 28

        play_btn, pause_btn, reset_btn = self._add_tab_button_row(
            controls,
            x=x,
            y=y,
            width=90,
            height=28,
            gap=8,
            specs=(
                ("nsdf_sprite_play", "Play", lambda: self._sprite_anim.play() if self._sprite_anim else None),
                ("nsdf_sprite_pause", "Pause", lambda: self._sprite_anim.pause() if self._sprite_anim else None),
                ("nsdf_sprite_reset", "Reset", lambda: self._sprite_anim.reset() if self._sprite_anim else None),
            ),
        )
        _ = (info, sheet_info, play_btn, pause_btn, reset_btn)
        return controls

    # ------------------------------------------------------------------
    # Tab: Sched — CooperativeScheduler + Pause + Sleep + WaitUntil
    # ------------------------------------------------------------------

    def _build_sched_tab(self, host, rect: Rect) -> list:
        controls = []
        pad = 8
        x, y = rect.left + pad, rect.top + pad

        self._scheduler = CooperativeScheduler()

        info = self._add_tab_label(
            controls,
            "nsdf_sched_info",
            Rect(x, y, rect.width - pad * 2, 40),
            "CooperativeScheduler runs generator coroutines on the frame thread.\n"
            "Yield Pause, Sleep(s), or WaitUntil(predicate) to suspend.",
        )
        y += 50

        self._sched_step_label = self._add_tab_label(
            controls,
            "nsdf_sched_step",
            Rect(x, y, rect.width - pad * 2, 22),
            "Active coroutines: 0",
        )
        y += 30

        self._sched_log_label = self._add_tab_label(
            controls,
            "nsdf_sched_log",
            Rect(x, y, rect.width - pad * 2, max(40, rect.bottom - y - 50)),
            "Press a button to start a coroutine…",
        )
        log_bottom = y + max(40, rect.bottom - y - 50)

        btn_y = log_bottom + 4
        start_btn, cancel_btn = self._add_tab_button_row(
            controls,
            x=x,
            y=btn_y,
            width=140,
            height=28,
            gap=8,
            specs=(
                ("nsdf_sched_start", "Start Sequence", self._sched_start_sequence),
                ("nsdf_sched_cancel", "Cancel All", self._sched_cancel_all),
            ),
        )
        _ = (info, start_btn, cancel_btn)
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

        info = self._add_tab_label(
            controls,
            "nsdf_tilemap_info",
            Rect(x, y, rect.width - pad * 2, 40),
            "TileSet slices an atlas into tile surfaces.  TileMap renders only visible tiles.\n"
            "Camera culling is automatic via visible_range().",
        )
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
        self._tile_canvas = self._add_tab_control(
            controls,
            CanvasControl("nsdf_tile_canvas", Rect(x, y, rect.width - pad * 2, canvas_h)),
        )
        self._tile_dirty = True
        y += canvas_h + 8

        tile_info = self._add_tab_label(
            controls,
            "nsdf_tilemap_detail",
            Rect(x, y, rect.width - pad * 2, 22),
            f"TileSet: {tile_set.tile_count} tiles  |  TileMap: {COLS}×{ROWS} ({COLS * ROWS} cells)",
        )
        _ = (info, tile_info)
        return controls

    # ------------------------------------------------------------------
    # Tab: Progress — ProgressBarControl
    # ------------------------------------------------------------------

    def _build_progress_tab(self, host, rect: Rect) -> list:
        controls = []
        pad = 8
        x, y = rect.left + pad, rect.top + pad

        info = self._add_tab_label(
            controls,
            "nsdf_progress_info",
            Rect(x, y, rect.width - pad * 2, 20),
            "ProgressBarControl — determinate (0–1) and indeterminate (marquee) modes.",
        )
        y += 30

        det_lbl = self._add_tab_label(
            controls,
            "nsdf_prog_det_lbl",
            Rect(x, y, rect.width - pad * 2, 18),
            "Determinate (value=0.72):",
        )
        y += 22

        self._progress_bar = self._add_tab_control(
            controls,
            ProgressBarControl(
                "nsdf_progress_bar",
                Rect(x, y, rect.width - pad * 2, 18),
                value=0.72,
            )
        )
        y += 30

        indet_lbl = self._add_tab_label(
            controls,
            "nsdf_prog_indet_lbl",
            Rect(x, y, rect.width - pad * 2, 18),
            "Indeterminate (marquee):",
        )
        y += 22

        self._progress_indeterminate = self._add_tab_control(
            controls,
            ProgressBarControl(
                "nsdf_progress_indet",
                Rect(x, y, rect.width - pad * 2, 18),
                indeterminate=True,
            )
        )
        y += 30

        self._progress_label = self._add_tab_label(
            controls,
            "nsdf_progress_val_lbl",
            Rect(x, y, rect.width - pad * 2, 22),
            "Adjust value:",
        )
        y += 28

        progress_specs = tuple(
            (
                f"nsdf_prog_set_{step_pct}",
                label,
                self._make_progress_setter(step_pct / 100.0),
            )
            for step_pct, label in ((0, "0%"), (25, "25%"), (50, "50%"), (75, "75%"), (100, "100%"))
        )
        _ = self._add_tab_button_row(
            controls,
            x=x,
            y=y,
            width=70,
            height=26,
            gap=8,
            specs=progress_specs,
        )
        _ = (info, det_lbl, indet_lbl)
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

        info = self._add_tab_label(
            controls,
            "nsdf_flow_info",
            Rect(x, y, rect.width - pad * 2, 40),
            "FlowLayout arranges FlowItem nodes left-to-right with automatic row wrapping.\n"
            "Items here are LabelControls sized as tags.  Add/clear to see layout reflow.",
        )
        y += 50

        self._flow_result_label = self._add_tab_label(
            controls,
            "nsdf_flow_result",
            Rect(x, y, rect.width - pad * 2, 22),
            "Row info will appear here after layout runs.",
        )
        y += 30

        add_btn, clear_btn, layout_btn = self._add_tab_button_row(
            controls,
            x=x,
            y=y,
            width=110,
            height=28,
            gap=8,
            specs=(
                ("nsdf_flow_add", "Add Item", self._flow_add_item),
                ("nsdf_flow_clear", "Clear Items", self._flow_clear_items),
                ("nsdf_flow_layout", "Apply Layout", self._flow_apply_layout),
            ),
        )
        _ = (info, add_btn, clear_btn, layout_btn)
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

        info = self._add_tab_label(
            controls,
            "nsdf_search_source",
            Rect(x, y, rect.width - pad * 2, 50),
            f'Search target:\n"{DEMO_TEXT[:80]}…"',
        )
        y += 58

        query_lbl = self._add_tab_label(
            controls,
            "nsdf_search_lbl",
            Rect(x, y, 60, 26),
            "Query:",
        )

        self._search_input = self._add_tab_control(
            controls,
            TextInputControl(
                "nsdf_search_input",
                Rect(x + 68, y, min(260, rect.width - pad * 2 - 68), 28),
                placeholder="enter search term…",
                on_change=self._on_search_changed,
            )
        )
        y += 36

        self._search_result_label = self._add_tab_label(
            controls,
            "nsdf_search_result",
            Rect(x, y, rect.width - pad * 2, max(40, rect.bottom - y - pad)),
            "Results appear here…",
        )
        _ = (info, query_lbl)
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

        info = self._add_tab_label(
            controls,
            "nsdf_listdiff_info",
            Rect(x, y, rect.width - pad * 2, 20),
            "ListDiffCalculator.diff(old, new) returns DiffInsert / DiffRemove / DiffMove ops.",
        )
        y += 28

        old_lbl = self._add_tab_label(
            controls,
            "nsdf_listdiff_old",
            Rect(x, y, rect.width - pad * 2, 22),
            f"Old: {self._listdiff_old}",
        )
        y += 26

        new_lbl = self._add_tab_label(
            controls,
            "nsdf_listdiff_new",
            Rect(x, y, rect.width - pad * 2, 22),
            f"New: {self._listdiff_new}",
        )
        y += 30

        run_btn, apply_btn = self._add_tab_button_row(
            controls,
            x=x,
            y=y,
            width=130,
            height=28,
            gap=8,
            specs=(
                ("nsdf_listdiff_run", "Compute Diff", self._run_listdiff),
                ("nsdf_listdiff_apply", "Apply & Show", self._apply_listdiff),
            ),
        )
        _ = (info, old_lbl, new_lbl, run_btn, apply_btn)
        y += 38

        self._listdiff_result_label = self._add_tab_label(
            controls,
            "nsdf_listdiff_result",
            Rect(x, y, rect.width - pad * 2, max(60, rect.bottom - y - pad)),
            "Press 'Compute Diff' to see operations.",
        )
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

        info = self._add_tab_label(
            controls,
            "nsdf_cache_info",
            Rect(x, y, rect.width - pad * 2, 20),
            "DataCache — LRU cache (max_size=5) with reactive on_evicted/on_invalidated signals.",
        )
        y += 28

        self._cache_stats_label = self._add_tab_label(
            controls,
            "nsdf_cache_stats",
            Rect(x, y, rect.width - pad * 2, 60),
            self._cache_stats_text(),
        )
        y += 68

        get_btn, miss_btn = self._add_tab_button_row(
            controls,
            x=x,
            y=y,
            width=110,
            height=28,
            gap=8,
            specs=(
                ("nsdf_cache_get", "Get user:1", self._cache_get_user1),
                ("nsdf_cache_miss", "Miss user:99", self._cache_miss),
            ),
        )
        evict_btn = self._add_tab_button(
            controls,
            "nsdf_cache_evict",
            Rect(x + 236, y, 130, 28),
            "Fill (cause evict)",
            self._cache_fill,
        )
        inval_btn = self._add_tab_button(
            controls,
            "nsdf_cache_inval",
            Rect(x, y + 36, 130, 28),
            "Invalidate user:2",
            self._cache_invalidate,
        )
        _ = (info, get_btn, miss_btn, evict_btn, inval_btn)
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

        info = self._add_tab_label(
            controls,
            "nsdf_shortcuts_info",
            Rect(x, y, rect.width - pad * 2, 40),
            "ShortcutHelpOverlay reads ActionRegistry + KeyChordManager and renders\n"
            "a structured shortcut reference panel via the OverlayManager.",
        )
        y += 50

        show_btn = self._add_tab_button(
            controls,
            "nsdf_shortcuts_show",
            Rect(x, y, 150, 28),
            "Show Help Overlay",
            self._shortcuts_show_overlay,
        )
        y += 38

        self._shortcut_info_label = self._add_tab_label(
            controls,
            "nsdf_shortcuts_detail",
            Rect(x, y, rect.width - pad * 2, max(60, rect.bottom - y - pad)),
            "Overlay not yet opened — click 'Show Help Overlay' to display it.\n"
            "ShortcutHelpOverlay.sections builds structured data from ActionRegistry.",
        )
        _ = (info, show_btn)
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
        # Tab builders use feature.window.add(...), so ensure this reference
        # exists before registering/building tab content.
        self.feature.window = self.window
        self.feature.demo = self.host
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
            items=[TabItem(tab_key, tab_label) for tab_key, tab_label, _builder_attr in _SYSTEMS_TAB_SPECS],
            selected_key="filter",
            on_change=self.feature._on_tab_change,
        )
        self.add_control(self.tab)
        self.feature.tab = self.tab
        register_window_tab_builders(
            self.feature._tabs,
            self.feature,
            self.host,
            body_content_rect,
            [(tab_key, builder_attr) for tab_key, _tab_label, builder_attr in _SYSTEMS_TAB_SPECS],
        )
        self.feature._tabs.on_activate("locale", lambda: setattr(self.feature, "_text_flow_dirty", True))
        self.window.visible = False
