"""New Systems demo feature — showcases the 10 new gui_do systems.

Demonstrates: CursorManager/CursorShape, SortFilterProxySource,
LocaleRegistry/StringTable, InputMap/InputBinding, ResponsiveLayout/Breakpoint,
TextFlow/TextSpan, EventRecorder/EventPlayback/RecordedEvent,
PropertyRegistry/PropertyDescriptor/ui_property, SceneSnapshot/NodeSnapshot,
and SceneSpatialIndex.
"""

from __future__ import annotations

import time
from typing import Optional

import pygame
from pygame import Rect

from gui_do import (
    Breakpoint,
    ButtonControl,
    CanvasControl,
    CursorHandle,
    CursorManager,
    CursorShape,
    EventPlayback,
    EventRecorder,
    FixedItemSource,
    InputMap,
    LabelControl,
    ListItem,
    LocaleRegistry,
    PropertyDescriptor,
    PropertyRegistry,
    property_registry,
    RecordedEvent,
    ResponsiveLayout,
    RoutedFeature,
    SceneSpatialIndex,
    SceneSnapshot,
    SortFilterProxySource,
    StringTable,
    TabControl,
    TabItem,
    TextFlow,
    TextInputControl,
    TextSpan,
    ToggleControl,
    WindowControl,
)

_TAB_H = 36


class NewSystemsDemoFeature(RoutedFeature):
    """Demonstrates all 10 new gui_do systems in a tabbed window."""

    HOST_REQUIREMENTS = {
        "build": (
            "app",
            "root",
            "task_panel",
            "TASK_PANEL_CONTROL_FONT_ROLE",
            "set_new_systems_window_visible",
        ),
    }

    def __init__(self) -> None:
        super().__init__("new_systems_demo", scene_name="main")
        self.window: Optional[WindowControl] = None
        self._active_tab: str = "cursor"
        self._tab_panels: dict = {}

        # Cursor tab
        self._cursor_mgr = CursorManager()
        self._cursor_handle: Optional[CursorHandle] = None
        self._cursor_label: Optional[LabelControl] = None

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
        self._last_update_time: float = 0.0

        # Inspect tab
        self._snapshot: Optional[SceneSnapshot] = None
        self._snapshot_label: Optional[LabelControl] = None
        self._spatial_index: Optional[SceneSpatialIndex] = None
        self._spatial_label: Optional[LabelControl] = None
        self._main_scene = None

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

        rect = host.app.layout.anchored(
            (820, 560), anchor="top_left", margin=(24, 92), use_rect=True
        )
        self.window = host.root.add(
            WindowControl(
                "new_systems_window",
                rect,
                "New Systems Demo",
                title_font_role=self.font_role("window_title"),
                event_handler=self._window_event_handler,
                use_frame_backdrop=True,
            )
        )

        content = self.window.content_rect()
        pad = 10
        body_top = content.top + pad
        body_bottom = content.bottom - pad
        body_h = body_bottom - body_top
        body_content_top = body_top + _TAB_H
        body_content_h = max(60, body_bottom - body_content_top)
        body_rect = Rect(content.left + pad, body_top, content.width - pad * 2, body_h)
        body_content_rect = Rect(
            content.left + pad, body_content_top, content.width - pad * 2, body_content_h
        )

        self._tab = self.window.add(
            TabControl(
                "nsdf_tab",
                body_rect,
                items=[
                    TabItem("cursor", "Cursor"),
                    TabItem("filter", "Filter"),
                    TabItem("locale", "Locale"),
                    TabItem("input", "Input"),
                    TabItem("event", "Event"),
                    TabItem("inspect", "Inspect"),
                ],
                selected_key="cursor",
                on_change=self._on_tab_change,
                font_role=self.font_role("control"),
            )
        )

        self._tab_panels["cursor"] = self._build_cursor_tab(host, Rect(body_content_rect))
        self._tab_panels["filter"] = self._build_filter_tab(host, Rect(body_content_rect))
        self._tab_panels["locale"] = self._build_locale_tab(host, Rect(body_content_rect))
        self._tab_panels["input"] = self._build_input_tab(host, Rect(body_content_rect))
        self._tab_panels["event"] = self._build_event_tab(host, Rect(body_content_rect))
        self._tab_panels["inspect"] = self._build_inspect_tab(host, Rect(body_content_rect))

        self._on_tab_change("cursor")

        # Add toggle button to the task panel
        def _on_new_systems_toggle(pushed: bool) -> None:
            host.set_new_systems_window_visible(bool(pushed), from_toggle=True)

        host.new_systems_toggle_window = host.task_panel.add(
            ToggleControl(
                "show_new_systems",
                host.app.layout.linear(5),
                "New Sys",
                "New Sys",
                pushed=False,
                on_toggle=_on_new_systems_toggle,
                style="round",
                font_role=host.TASK_PANEL_CONTROL_FONT_ROLE,
            )
        )

    def bind_runtime(self, host) -> None:
        self._main_scene = host.app.create_scene("main")
        self._last_update_time = time.perf_counter()

    def on_update(self, host) -> None:
        super().on_update(host)
        if self.window is None or not self.window.visible:
            return

        now = time.perf_counter()
        dt = now - self._last_update_time
        self._last_update_time = now

        # Update cursor manager when cursor tab is active
        if self._active_tab == "cursor":
            self._cursor_mgr.update()

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

    def shutdown_runtime(self, host) -> None:
        if self._cursor_handle is not None:
            self._cursor_handle.release()
            self._cursor_handle = None
        self._cursor_mgr.reset()

    # ------------------------------------------------------------------
    # Tab management
    # ------------------------------------------------------------------

    def _window_event_handler(self, event_type: str, _data=None) -> None:
        if event_type == "close":
            self.window.visible = False

    def _on_tab_change(self, key: str) -> None:
        self._active_tab = key
        for tab_key, controls in self._tab_panels.items():
            visible = tab_key == key
            for ctrl in controls:
                ctrl.visible = visible
        # Release cursor when leaving cursor tab
        if key != "cursor" and self._cursor_handle is not None:
            self._cursor_handle.release()
            self._cursor_handle = None
        if key == "locale":
            self._text_flow_dirty = True

    # ------------------------------------------------------------------
    # Tab: Cursor — CursorManager + CursorShape
    # ------------------------------------------------------------------

    def _build_cursor_tab(self, host, rect: Rect) -> list:
        controls = []
        pad = 8
        x, y = rect.left + pad, rect.top + pad

        self._cursor_label = self.window.add(
            LabelControl(
                "nsdf_cursor_shape_label",
                Rect(x, y, rect.width - pad * 2, 24),
                "Active cursor: (none — click a shape button)",
                align="left",
            )
        )
        self._cursor_label.font_role = self.font_role("label")
        controls.append(self._cursor_label)
        y += 34

        info_lbl = self.window.add(
            LabelControl(
                "nsdf_cursor_info",
                Rect(x, y, rect.width - pad * 2, 20),
                "CursorManager.push() stacks cursor requests by priority. release() restores the previous shape.",
                align="left",
            )
        )
        info_lbl.font_role = self.font_role("label")
        controls.append(info_lbl)
        y += 30

        btn_w, btn_h, btn_gap = 120, 28, 8
        shapes = [
            (CursorShape.ARROW, "ARROW"),
            (CursorShape.HAND, "HAND"),
            (CursorShape.TEXT, "TEXT"),
            (CursorShape.CROSSHAIR, "CROSSHAIR"),
            (CursorShape.RESIZE_H, "RESIZE_H"),
            (CursorShape.RESIZE_V, "RESIZE_V"),
            (CursorShape.FORBIDDEN, "FORBIDDEN"),
            (CursorShape.WAIT, "WAIT"),
        ]
        avail_w = rect.width - pad * 2
        col_count = max(1, (avail_w + btn_gap) // (btn_w + btn_gap))
        for i, (shape, label) in enumerate(shapes):
            col = i % col_count
            row = i // col_count
            bx = x + col * (btn_w + btn_gap)
            by = y + row * (btn_h + btn_gap)
            btn = self.window.add(
                ButtonControl(
                    f"nsdf_cursor_btn_{label.lower()}",
                    Rect(bx, by, btn_w, btn_h),
                    label,
                    self._make_cursor_pusher(shape, label),
                    font_role=self.font_role("control"),
                )
            )
            controls.append(btn)

        row_count = (len(shapes) - 1) // col_count + 1
        y += row_count * (btn_h + btn_gap) + 4

        reset_btn = self.window.add(
            ButtonControl(
                "nsdf_cursor_reset_btn",
                Rect(x, y, 120, btn_h),
                "Reset Cursor",
                self._reset_cursor,
                font_role=self.font_role("control"),
            )
        )
        controls.append(reset_btn)
        return controls

    def _make_cursor_pusher(self, shape: CursorShape, label: str):
        def push():
            if self._cursor_handle is not None:
                self._cursor_handle.release()
            self._cursor_handle = self._cursor_mgr.push(shape, priority=10)
            if self._cursor_label is not None:
                self._cursor_label.text = f"Active cursor: {label}"

        return push

    def _reset_cursor(self) -> None:
        if self._cursor_handle is not None:
            self._cursor_handle.release()
            self._cursor_handle = None
        self._cursor_mgr.reset()
        if self._cursor_label is not None:
            self._cursor_label.text = "Active cursor: (none)"

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
