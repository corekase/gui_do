"""Desktop-style system tools window with tabbed workspace panels."""

from __future__ import annotations

import json
from datetime import datetime

from pygame import Rect

from gui_do import (
    AnimationHandle,
    AnimationSequence,
    ButtonControl,
    ClipboardManager,
    CommandEntry,
    CommandPaletteManager,
    ComputedValue,
    ContextMenuItem,
    FileDialogManager,
    FileDialogOptions,
    FlexAlign,
    FlexDirection,
    FlexItem,
    FlexJustify,
    FlexLayout,
    LabelControl,
    LayoutAxis,
    ListItem,
    ListViewControl,
    MenuBarControl,
    MenuEntry,
    NotificationCenter,
    NotificationPanelControl,
    NotificationRecord,
    ObservableValue,
    RangeSliderControl,
    RoutedFeature,
    SliderControl,
    SpinnerControl,
    TabControl,
    TabItem,
    TextAreaControl,
    TextInputControl,
    ToastSeverity,
    TreeControl,
    TreeNode,
)

_TAB_H = 32   # matches tab_control._TAB_H


class _AnimTarget:
    """Simple attribute container for tweening demonstration."""

    def __init__(self) -> None:
        self.value: float = 0.0
        self.value_b: float = 0.0



class SystemWindowDemoFeature(RoutedFeature):
    """Main-scene desktop utility window used to exercise new functionality."""

    HOST_REQUIREMENTS = {
        "build": ("app", "root"),
        "configure_accessibility": ("app",),
        "on_update": ("app",),
    }

    LOG_LIMIT = 20

    def __init__(self) -> None:
        super().__init__("system_window_demo", scene_name="main")

        self.window = None
        self.menu_bar = None
        self.status_label = None
        self.notification_center = None
        self.file_dialogs = None
        self._toolbar_buttons: list[ButtonControl] = []
        self._host = None

        # Tab navigation
        self._body_tab: TabControl | None = None
        self._tab_panels: dict[str, list] = {}  # tab key → list of direct window children

        # Files tab
        self.tree: TreeControl | None = None
        self.log_area: TextAreaControl | None = None

        # Animate tab
        self._anim_target = _AnimTarget()
        self._anim_handle: AnimationHandle | None = None
        self._anim_value_label: LabelControl | None = None
        self._anim_status_label: LabelControl | None = None
        self._anim_duration_spinner: SpinnerControl | None = None
        self._anim_range: RangeSliderControl | None = None

        # State tab
        self._dep_a: ObservableValue | None = None
        self._dep_b: ObservableValue | None = None
        self._comp_sum: ComputedValue | None = None
        self._comp_product: ComputedValue | None = None
        self._reactive_sum_label: LabelControl | None = None
        self._reactive_product_label: LabelControl | None = None
        self._slider_a: SliderControl | None = None
        self._slider_b: SliderControl | None = None
        self._saved_app_state: dict = {}
        self._state_status_label: LabelControl | None = None
        self._clip_input: TextInputControl | None = None
        self._clip_status_label: LabelControl | None = None

        # Features tab
        self._features_list: ListViewControl | None = None
        self._features_saved: dict = {}
        self._features_log: TextAreaControl | None = None

        # Palette tab
        self._palette_mgr: CommandPaletteManager | None = None
        self._palette_cmd_input: TextInputControl | None = None
        self._palette_commands_list: ListViewControl | None = None
        self._palette_log: TextAreaControl | None = None

    def build(self, host) -> None:
        self._host = host
        ui = host.app.read_feature_ui_types()
        self.register_font_roles(
            host,
            {
                "window_title": {"size": 14, "file_path": "demo_features/data/fonts/Gimbot.ttf", "system_name": "arial", "bold": True},
                "control": {"size": 15, "file_path": "demo_features/data/fonts/Ubuntu-B.ttf", "system_name": "arial"},
                "label": {"size": 13, "file_path": "demo_features/data/fonts/Ubuntu-B.ttf", "system_name": "arial"},
                "status": {"size": 13, "file_path": "demo_features/data/fonts/Ubuntu-B.ttf", "system_name": "arial"},
            },
            scene_name="main",
        )
        self.notification_center = NotificationCenter(host.app.events, max_records=200)
        self.notification_center.subscribe("demo.system.status", severity=ToastSeverity.INFO, title="System")
        self.file_dialogs = FileDialogManager(host.app)
        self._build_window(host, window_control_cls=ui.window_control_cls, button_control_cls=ui.button_control_cls)

    def configure_accessibility(self, _host, tab_index_start: int) -> int:
        next_index = int(tab_index_start)
        for button in self._toolbar_buttons:
            button.set_tab_index(next_index)
            next_index += 1
        if self._body_tab is not None:
            self._body_tab.set_tab_index(next_index)
            next_index += 1
        if self.tree is not None:
            self.tree.set_tab_index(next_index)
            next_index += 1
        return next_index

    def on_update(self, host) -> None:
        super().on_update(host)
        if self._anim_value_label is not None:
            self._anim_value_label.text = f"A: {self._anim_target.value:.1f}  B: {self._anim_target.value_b:.1f}"

    def shutdown_runtime(self, _host) -> None:
        if self._anim_handle is not None:
            self._anim_handle.cancel()
            self._anim_handle = None
        if self._comp_sum is not None:
            self._comp_sum.dispose()
        if self._comp_product is not None:
            self._comp_product.dispose()
        if self.notification_center is not None:
            self.notification_center.unsubscribe_all()

    def _build_window(self, host, *, window_control_cls, button_control_cls) -> None:
        rect = host.app.layout.anchored((900, 680), anchor="top_left", margin=(24, 92), use_rect=True)
        self.window = host.root.add(
            window_control_cls(
                "system_window",
                rect,
                "System Workspace",
                title_font_role=self.font_role("window_title"),
                event_handler=self._window_event_handler,
                use_frame_backdrop=True,
            )
        )
        content = self.window.content_rect()
        pad = 10

        # Menu bar
        menu_h = 28
        self.menu_bar = self.window.add(
            MenuBarControl(
                "system_window_menu",
                Rect(content.left + pad, content.top + pad, content.width - (pad * 2), menu_h),
                self._menu_entries(),
            )
        )

        # Toolbar
        toolbar_rect = Rect(content.left + pad, self.menu_bar.rect.bottom + 8, content.width - (pad * 2), 30)
        open_btn = self.window.add(button_control_cls("system_open_btn", Rect(0, 0, 100, 30), "Open File", self.open_file_dialog, font_role=self.font_role("control")))
        save_btn = self.window.add(button_control_cls("system_save_btn", Rect(0, 0, 100, 30), "Save As", self.save_file_dialog, font_role=self.font_role("control")))
        inbox_btn = self.window.add(button_control_cls("system_inbox_btn", Rect(0, 0, 130, 30), "Notifications", self.show_notifications_panel, font_role=self.font_role("control")))
        ping_btn = self.window.add(button_control_cls("system_ping_btn", Rect(0, 0, 110, 30), "Publish Test", self.publish_test_notification, font_role=self.font_role("control")))
        self._toolbar_buttons = [open_btn, save_btn, inbox_btn, ping_btn]
        FlexLayout(
            direction=FlexDirection.ROW, gap=8, align=FlexAlign.STRETCH, justify=FlexJustify.START,
            items=[
                FlexItem(open_btn, grow=1, basis=100),
                FlexItem(save_btn, grow=1, basis=100),
                FlexItem(inbox_btn, grow=1, basis=130),
                FlexItem(ping_btn, grow=1, basis=110),
            ],
        ).apply(toolbar_rect)

        # Status bar
        status_h = 22
        body_bottom = content.bottom - pad - status_h - 6
        body_top = toolbar_rect.bottom + 8
        self.status_label = host.app.style_label(
            self.window.add(
                LabelControl("system_status", Rect(content.left + pad, body_bottom + 6, content.width - (pad * 2), status_h), "Status: idle", align="left")
            ),
            size=13, role=self.font_role("status"),
        )

        # Tab navigation
        body_content_top = body_top + _TAB_H
        body_content_h = max(60, body_bottom - body_content_top)
        body_content_rect = Rect(content.left + pad, body_content_top, content.width - (pad * 2), body_content_h)

        self._body_tab = self.window.add(
            TabControl(
                "system_body_tab",
                Rect(content.left + pad, body_top, content.width - (pad * 2), body_bottom - body_top),
                items=[
                    TabItem("files", "Files"),
                    TabItem("animate", "Animate"),
                    TabItem("state", "State"),
                    TabItem("features", "Features"),
                    TabItem("palette", "Palette"),
                ],
                selected_key="files",
                on_change=self._on_tab_change,
                font_role=self.font_role("control"),
            )
        )

        # Content controls — added directly to the window so move_by propagates
        # Each builder returns a list of the controls it added.
        self._tab_panels["files"] = self._build_tab_files(host, Rect(body_content_rect))
        self._tab_panels["animate"] = self._build_tab_animate(host, Rect(body_content_rect))
        self._tab_panels["state"] = self._build_tab_state(host, Rect(body_content_rect))
        self._tab_panels["features"] = self._build_tab_features(host, Rect(body_content_rect))
        self._tab_panels["palette"] = self._build_tab_palette(host, Rect(body_content_rect))

        self._on_tab_change("files")

    def _on_tab_change(self, key: str) -> None:
        for tab_key, controls in self._tab_panels.items():
            visible = (tab_key == key)
            for ctrl in controls:
                ctrl.visible = visible
        if key == "features":
            self._refresh_features_list()

    # ------------------------------------------------------------------
    # Tab 1: Files
    # ------------------------------------------------------------------

    def _build_tab_files(self, host, rect: Rect) -> list:
        controls = []
        p = rect
        pad = 8
        left_w = int(p.width * 0.38)
        right_w = max(100, p.width - left_w - 8)

        self.tree = self.window.add(
            TreeControl(
                "system_tree",
                Rect(p.left + pad, p.top + pad, left_w - pad, p.height - pad * 2),
                nodes=self._tree_nodes(),
                on_select=self._on_tree_select,
            )
        )
        controls.append(self.tree)
        self.log_area = self.window.add(
            TextAreaControl(
                "system_log",
                Rect(p.left + pad + left_w, p.top + pad, right_w - pad, p.height - pad * 2),
                value="System workspace ready.\nUse menu, toolbar, tree, and dialogs above.",
                font_role=self.font_role("control"),
            )
        )
        controls.append(self.log_area)
        return controls

    # ------------------------------------------------------------------
    # Tab 2: Animate
    # ------------------------------------------------------------------

    def _build_tab_animate(self, host, rect: Rect) -> list:
        controls = []

        def wa(ctrl):
            self.window.add(ctrl)
            controls.append(ctrl)
            return ctrl

        p = rect
        lpad = 8
        x = p.left + lpad
        y = p.top + lpad

        self._anim_value_label = wa(host.app.style_label(
            LabelControl("sys_anim_val", Rect(x, y, p.width - lpad * 2, 26), "A: 0.0  B: 0.0", align="left"),
            size=15, role=self.font_role("control"),
        ))
        y += 32

        wa(host.app.style_label(
            LabelControl("sys_anim_dur_lbl", Rect(x, y, 84, 22), "Duration (s):", align="left"),
            size=13, role=self.font_role("label"),
        ))
        self._anim_duration_spinner = wa(
            SpinnerControl(
                "sys_anim_dur", Rect(x + 90, y, 100, 26),
                value=1.5, min_value=0.1, max_value=10.0, step=0.1, decimals=1,
                on_change=lambda v, _r: None,
            )
        )
        y += 34

        wa(host.app.style_label(
            LabelControl("sys_anim_rng_lbl", Rect(x, y, 84, 22), "Value range:", align="left"),
            size=13, role=self.font_role("label"),
        ))
        self._anim_range = wa(
            RangeSliderControl(
                "sys_anim_range", Rect(x + 90, y, max(160, p.width - lpad * 2 - 94), 24),
                min_value=0, max_value=100, low_value=0, high_value=100,
                on_change=lambda lo, hi, _r: None,
            )
        )
        y += 34

        btn_w = 130
        gap = 8
        wa(ButtonControl("sys_anim_seq", Rect(x, y, btn_w, 30), "Run Sequence", self._run_anim_sequence, font_role=self.font_role("control")))
        wa(ButtonControl("sys_anim_par", Rect(x + btn_w + gap, y, btn_w, 30), "Run Parallel", self._run_anim_parallel, font_role=self.font_role("control")))
        wa(ButtonControl("sys_anim_bns", Rect(x + (btn_w + gap) * 2, y, btn_w, 30), "Bounce", self._run_anim_bounce, font_role=self.font_role("control")))
        wa(ButtonControl("sys_anim_cancel", Rect(x + (btn_w + gap) * 3, y, 90, 30), "Cancel", self._cancel_anim, font_role=self.font_role("control")))
        y += 38

        self._anim_status_label = wa(host.app.style_label(
            LabelControl("sys_anim_status", Rect(x, y, p.width - lpad * 2, 22), "No animation running.", align="left"),
            size=13, role=self.font_role("status"),
        ))
        return controls

    def _anim_duration(self) -> float:
        return float(self._anim_duration_spinner.value) if self._anim_duration_spinner else 1.5

    def _anim_low(self) -> float:
        return float(self._anim_range.low_value) if self._anim_range else 0.0

    def _anim_high(self) -> float:
        return float(self._anim_range.high_value) if self._anim_range else 100.0

    def _cancel_anim(self) -> None:
        if self._anim_handle is not None:
            self._anim_handle.cancel()
            self._anim_handle = None
        self._set_anim_status("Cancelled.")

    def _run_anim_sequence(self) -> None:
        host = self._host
        if host is None:
            return
        self._cancel_anim()
        lo, hi, dur = self._anim_low(), self._anim_high(), self._anim_duration()
        self._anim_target.value = lo
        self._anim_target.value_b = lo
        seq = AnimationSequence(host.app.tweens)
        seq.then(target=self._anim_target, attr="value", end_value=hi, duration_seconds=dur)
        seq.wait(0.1)
        seq.then(target=self._anim_target, attr="value", end_value=lo, duration_seconds=dur)
        seq.on_done(lambda: self._set_anim_status("Sequence done."))
        self._anim_handle = seq.start()
        self._set_anim_status(f"Sequence: {lo:.0f}→{hi:.0f}→{lo:.0f} ({dur:.1f}s each)")

    def _run_anim_parallel(self) -> None:
        host = self._host
        if host is None:
            return
        self._cancel_anim()
        lo, hi, dur = self._anim_low(), self._anim_high(), self._anim_duration()
        self._anim_target.value = lo
        self._anim_target.value_b = hi
        seq = AnimationSequence(host.app.tweens)
        seq.parallel([
            dict(target=self._anim_target, attr="value", end_value=hi, duration_seconds=dur),
            dict(target=self._anim_target, attr="value_b", end_value=lo, duration_seconds=dur),
        ])
        seq.on_done(lambda: self._set_anim_status("Parallel done."))
        self._anim_handle = seq.start()
        self._set_anim_status(f"Parallel: A {lo:.0f}→{hi:.0f}, B {hi:.0f}→{lo:.0f} ({dur:.1f}s)")

    def _run_anim_bounce(self) -> None:
        host = self._host
        if host is None:
            return
        self._cancel_anim()
        lo, hi = self._anim_low(), self._anim_high()
        step_dur = max(0.1, self._anim_duration() / 4)
        self._anim_target.value = lo
        seq = AnimationSequence(host.app.tweens)
        for _ in range(4):
            seq.then(target=self._anim_target, attr="value", end_value=hi, duration_seconds=step_dur)
            seq.then(target=self._anim_target, attr="value", end_value=lo, duration_seconds=step_dur)
        seq.on_done(lambda: self._set_anim_status("Bounce done."))
        self._anim_handle = seq.start()
        self._set_anim_status(f"Bounce: {lo:.0f}↔{hi:.0f} ×4 ({step_dur:.2f}s steps)")

    def _set_anim_status(self, text: str) -> None:
        if self._anim_status_label is not None:
            self._anim_status_label.text = str(text)

    # ------------------------------------------------------------------
    # Tab 3: State (App State + Reactive ComputedValue + Clipboard)
    # ------------------------------------------------------------------

    def _build_tab_state(self, host, rect: Rect) -> list:
        controls = []

        def wa(ctrl):
            self.window.add(ctrl)
            controls.append(ctrl)
            return ctrl

        p = rect
        lpad = 8
        col_w = max(200, p.width // 2 - lpad * 2)
        lbl_h = 18
        ctrl_h = 26
        row_gap = 6
        section_gap = 14

        # --- Column A: App State + Clipboard ---
        ax = p.left + lpad
        ay = p.top + lpad

        wa(host.app.style_label(
            LabelControl("sys_st_appstate_hdr", Rect(ax, ay, col_w, lbl_h), "App State", align="left"),
            size=14, role=self.font_role("control"),
        ))
        ay += lbl_h + row_gap

        wa(ButtonControl("sys_st_save_all", Rect(ax, ay, 110, ctrl_h), "Save All State", self._save_app_state, font_role=self.font_role("control")))
        wa(ButtonControl("sys_st_load_all", Rect(ax + 116, ay, 110, ctrl_h), "Load All State", self._load_app_state, font_role=self.font_role("control")))
        ay += ctrl_h + row_gap

        wa(ButtonControl("sys_st_export", Rect(ax, ay, 110, ctrl_h), "Export JSON", self._export_state_json, font_role=self.font_role("control")))
        ay += ctrl_h + row_gap

        self._state_status_label = wa(host.app.style_label(
            LabelControl("sys_st_status", Rect(ax, ay, col_w, lbl_h), "No state saved.", align="left"),
            size=12, role=self.font_role("status"),
        ))
        ay += lbl_h + section_gap

        wa(host.app.style_label(
            LabelControl("sys_clip_hdr", Rect(ax, ay, col_w, lbl_h), "Clipboard", align="left"),
            size=14, role=self.font_role("control"),
        ))
        ay += lbl_h + row_gap

        self._clip_input = wa(
            TextInputControl("sys_clip_input", Rect(ax, ay, col_w, ctrl_h), placeholder="Type to copy…", font_role=self.font_role("control"))
        )
        ay += ctrl_h + row_gap

        wa(ButtonControl("sys_clip_copy", Rect(ax, ay, 90, ctrl_h), "Copy", self._clipboard_copy, font_role=self.font_role("control")))
        wa(ButtonControl("sys_clip_paste", Rect(ax + 96, ay, 90, ctrl_h), "Paste", self._clipboard_paste, font_role=self.font_role("control")))
        ay += ctrl_h + row_gap

        self._clip_status_label = wa(host.app.style_label(
            LabelControl("sys_clip_status", Rect(ax, ay, col_w, lbl_h), "Clipboard ready.", align="left"),
            size=12, role=self.font_role("status"),
        ))

        # --- Column B: Reactive ComputedValue Demo ---
        bx = ax + col_w + section_gap
        by = p.top + lpad

        wa(host.app.style_label(
            LabelControl("sys_rx_hdr", Rect(bx, by, col_w, lbl_h), "Reactive (ComputedValue)", align="left"),
            size=14, role=self.font_role("control"),
        ))
        by += lbl_h + row_gap

        self._dep_a = ObservableValue(40.0)
        self._dep_b = ObservableValue(60.0)
        self._comp_sum = ComputedValue(
            lambda: self._dep_a.value + self._dep_b.value,
            deps=[self._dep_a, self._dep_b],
        )
        self._comp_product = ComputedValue(
            lambda: (self._dep_a.value * self._dep_b.value) / 100.0,
            deps=[self._dep_a, self._dep_b],
        )

        wa(host.app.style_label(
            LabelControl("sys_rx_a_lbl", Rect(bx, by, 28, lbl_h), "A:", align="left"),
            size=13, role=self.font_role("label"),
        ))
        self._slider_a = wa(
            SliderControl("sys_rx_sla", Rect(bx + 32, by, col_w - 32, 20), LayoutAxis.HORIZONTAL, 0.0, 100.0, 40.0,
                          on_change=lambda v, _r: self._on_dep_a_change(v))
        )
        by += 26

        wa(host.app.style_label(
            LabelControl("sys_rx_b_lbl", Rect(bx, by, 28, lbl_h), "B:", align="left"),
            size=13, role=self.font_role("label"),
        ))
        self._slider_b = wa(
            SliderControl("sys_rx_slb", Rect(bx + 32, by, col_w - 32, 20), LayoutAxis.HORIZONTAL, 0.0, 100.0, 60.0,
                          on_change=lambda v, _r: self._on_dep_b_change(v))
        )
        by += 30

        self._reactive_sum_label = wa(host.app.style_label(
            LabelControl("sys_rx_sum", Rect(bx, by, col_w, lbl_h + 2), f"Sum: {self._comp_sum.value:.1f}", align="left"),
            size=13, role=self.font_role("label"),
        ))
        by += lbl_h + 4

        self._reactive_product_label = wa(host.app.style_label(
            LabelControl("sys_rx_prod", Rect(bx, by, col_w, lbl_h + 2), f"Product / 100: {self._comp_product.value:.2f}", align="left"),
            size=13, role=self.font_role("label"),
        ))

        self._comp_sum.subscribe(lambda v: self._update_sum_label(v))
        self._comp_product.subscribe(lambda v: self._update_product_label(v))

        return controls

    def _on_dep_a_change(self, v: float) -> None:
        if self._dep_a is not None:
            self._dep_a.value = v

    def _on_dep_b_change(self, v: float) -> None:
        if self._dep_b is not None:
            self._dep_b.value = v

    def _update_sum_label(self, v: float) -> None:
        if self._reactive_sum_label is not None:
            self._reactive_sum_label.text = f"Sum: {v:.1f}"

    def _update_product_label(self, v: float) -> None:
        if self._reactive_product_label is not None:
            self._reactive_product_label.text = f"Product / 100: {v:.2f}"

    def _save_app_state(self) -> None:
        host = self._host
        if host is None:
            return
        self._saved_app_state = host.app.features.save_feature_states()
        count = len(self._saved_app_state)
        self._set_state_status(f"Saved {count} feature state(s).")
        self._append_log(f"App state saved ({count} features)")

    def _load_app_state(self) -> None:
        host = self._host
        if host is None:
            return
        if not self._saved_app_state:
            self._set_state_status("No saved state — save first.")
            return
        host.app.features.restore_feature_states(self._saved_app_state)
        self._set_state_status(f"Restored {len(self._saved_app_state)} feature state(s).")
        self._append_log("App state restored")

    def _export_state_json(self) -> None:
        host = self._host
        if host is None:
            return
        try:
            states = host.app.features.save_feature_states()
            text = json.dumps(states, indent=2, default=str)
            if self.log_area is not None:
                self.log_area.set_value(text)
            if self._body_tab is not None:
                self._body_tab.select("files")
            self._on_tab_change("files")
            self._set_state_status(f"Exported {len(states)} feature states to Files log.")
        except Exception as exc:
            self._set_state_status(f"Export failed: {exc}")

    def _set_state_status(self, text: str) -> None:
        if self._state_status_label is not None:
            self._state_status_label.text = str(text)

    def _clipboard_copy(self) -> None:
        if self._clip_input is None:
            return
        text = self._clip_input.value
        ok = ClipboardManager.copy(text)
        if self._clip_status_label is not None:
            self._clip_status_label.text = f"Copied: '{text[:40]}'" if ok else "Copy unavailable."

    def _clipboard_paste(self) -> None:
        text = ClipboardManager.paste()
        if self._clip_input is not None:
            self._clip_input.set_value(text)
        if self._clip_status_label is not None:
            self._clip_status_label.text = f"Pasted: '{text[:40]}'" if text else "Clipboard empty."

    # ------------------------------------------------------------------
    # Tab 4: Features
    # ------------------------------------------------------------------

    def _build_tab_features(self, host, rect: Rect) -> list:
        controls = []

        def wa(ctrl):
            self.window.add(ctrl)
            controls.append(ctrl)
            return ctrl

        p = rect
        lpad = 8
        lbl_h = 18
        ctrl_h = 26
        row_gap = 6
        list_h = max(80, p.height // 2 - 60)
        log_h = max(60, p.height - list_h - 90)
        x = p.left + lpad
        y = p.top + lpad

        wa(host.app.style_label(
            LabelControl("sys_feat_hdr", Rect(x, y, p.width - lpad * 2, lbl_h), "Feature State Management", align="left"),
            size=14, role=self.font_role("control"),
        ))
        y += lbl_h + row_gap

        list_w = max(180, p.width // 2 - lpad)
        self._features_list = wa(
            ListViewControl(
                "sys_feat_list",
                Rect(x, y, list_w, list_h),
                items=[],
                row_height=26,
                font_role=self.font_role("control"),
            )
        )

        btn_x = x + list_w + lpad
        btn_y = y
        btn_w = min(150, p.width - list_w - lpad * 3)
        wa(ButtonControl("sys_feat_save_all", Rect(btn_x, btn_y, btn_w, ctrl_h), "Save All", self._feat_save_all, font_role=self.font_role("control")))
        btn_y += ctrl_h + row_gap
        wa(ButtonControl("sys_feat_rest_all", Rect(btn_x, btn_y, btn_w, ctrl_h), "Restore All", self._feat_restore_all, font_role=self.font_role("control")))
        btn_y += ctrl_h + row_gap + 4
        wa(ButtonControl("sys_feat_save_sel", Rect(btn_x, btn_y, btn_w, ctrl_h), "Save Selected", self._feat_save_selected, font_role=self.font_role("control")))
        btn_y += ctrl_h + row_gap
        wa(ButtonControl("sys_feat_rest_sel", Rect(btn_x, btn_y, btn_w, ctrl_h), "Restore Selected", self._feat_restore_selected, font_role=self.font_role("control")))

        y += list_h + row_gap
        self._features_log = wa(
            TextAreaControl(
                "sys_feat_log",
                Rect(x, y, p.width - lpad * 2, log_h),
                value="Feature state log.",
                font_role=self.font_role("control"),
            )
        )
        return controls

    def _refresh_features_list(self) -> None:
        host = self._host
        if host is None or self._features_list is None:
            return
        names = sorted(host.app.features.names())
        self._features_list.set_items([ListItem(label=name, value=name) for name in names])

    def _feat_save_all(self) -> None:
        host = self._host
        if host is None:
            return
        self._features_saved = host.app.features.save_feature_states()
        self._feat_log(f"Saved all ({len(self._features_saved)}) feature states")

    def _feat_restore_all(self) -> None:
        host = self._host
        if host is None:
            return
        if not self._features_saved:
            self._feat_log("Nothing saved — use Save All first")
            return
        host.app.features.restore_feature_states(self._features_saved)
        self._feat_log(f"Restored all ({len(self._features_saved)}) feature states")

    def _feat_save_selected(self) -> None:
        host = self._host
        if host is None or self._features_list is None:
            return
        sel = self._features_list.selected_value()
        if sel is None:
            self._feat_log("Select a feature first")
            return
        name = str(sel)
        feature = host.app.features.get(name)
        if feature is None:
            self._feat_log(f"Feature '{name}' not found")
            return
        try:
            self._features_saved[name] = feature.save_state()
            self._feat_log(f"Saved '{name}': {len(self._features_saved[name])} key(s)")
        except Exception as exc:
            self._feat_log(f"Save failed for '{name}': {exc}")

    def _feat_restore_selected(self) -> None:
        host = self._host
        if host is None or self._features_list is None:
            return
        sel = self._features_list.selected_value()
        if sel is None:
            self._feat_log("Select a feature first")
            return
        name = str(sel)
        if name not in self._features_saved:
            self._feat_log(f"No saved state for '{name}'")
            return
        feature = host.app.features.get(name)
        if feature is None:
            self._feat_log(f"Feature '{name}' not found")
            return
        try:
            feature.restore_state(self._features_saved[name])
            self._feat_log(f"Restored '{name}'")
        except Exception as exc:
            self._feat_log(f"Restore failed for '{name}': {exc}")

    def _feat_log(self, message: str) -> None:
        if self._features_log is None:
            return
        lines = self._features_log.value.splitlines()
        if lines == ["Feature state log."]:
            lines = []
        ts = datetime.now().strftime("%H:%M:%S")
        lines.append(f"[{ts}] {message}")
        self._features_log.set_value("\n".join(lines[-self.LOG_LIMIT:]))

    # ------------------------------------------------------------------
    # Tab 5: Palette
    # ------------------------------------------------------------------

    def _build_tab_palette(self, host, rect: Rect) -> list:
        controls = []

        def wa(ctrl):
            self.window.add(ctrl)
            controls.append(ctrl)
            return ctrl

        p = rect
        lpad = 8
        lbl_h = 18
        ctrl_h = 26
        row_gap = 6
        x = p.left + lpad
        y = p.top + lpad

        self._palette_mgr = CommandPaletteManager(host.app.overlay)
        self._register_default_palette_commands()

        wa(host.app.style_label(
            LabelControl("sys_pal_hdr", Rect(x, y, p.width - lpad * 2, lbl_h), "Command Palette", align="left"),
            size=14, role=self.font_role("control"),
        ))
        y += lbl_h + row_gap

        wa(ButtonControl("sys_pal_open", Rect(x, y, 140, ctrl_h), "Open Palette", self._open_palette, font_role=self.font_role("control")))
        y += ctrl_h + row_gap + 4

        wa(host.app.style_label(
            LabelControl("sys_pal_reg_lbl", Rect(x, y, 120, lbl_h), "Register command:", align="left"),
            size=13, role=self.font_role("label"),
        ))
        y += lbl_h + 2

        reg_input_w = min(280, p.width // 2 - lpad)
        self._palette_cmd_input = wa(
            TextInputControl("sys_pal_cmd_in", Rect(x, y, reg_input_w, ctrl_h), placeholder="Command title…", font_role=self.font_role("control"))
        )
        wa(ButtonControl("sys_pal_reg", Rect(x + reg_input_w + 8, y, 100, ctrl_h), "Register", self._register_palette_cmd, font_role=self.font_role("control")))
        y += ctrl_h + row_gap

        wa(host.app.style_label(
            LabelControl("sys_pal_cmds_lbl", Rect(x, y, 130, lbl_h), "Registered commands:", align="left"),
            size=13, role=self.font_role("label"),
        ))
        y += lbl_h + 2

        list_h = max(80, p.height - (y - p.top) - lpad * 2)
        list_w = min(320, p.width // 2 - lpad)
        self._palette_commands_list = wa(
            ListViewControl(
                "sys_pal_cmds_list",
                Rect(x, y, list_w, list_h),
                items=self._palette_command_items(),
                row_height=26,
                font_role=self.font_role("control"),
            )
        )
        self._palette_log = wa(
            TextAreaControl(
                "sys_pal_log",
                Rect(x + list_w + lpad, y, max(80, p.width - list_w - lpad * 3), list_h),
                value="Palette activity log.",
                font_role=self.font_role("control"),
            )
        )
        return controls

    def _register_default_palette_commands(self) -> None:
        if self._palette_mgr is None:
            return
        for cmd in [
            CommandEntry("nav_main", "Go to Main Scene", self.go_main_scene, category="Navigation"),
            CommandEntry("nav_showcase", "Go to Controls Showcase", self.go_showcase_scene, category="Navigation"),
            CommandEntry("anim_sequence", "Run Animation Sequence", self._run_anim_sequence, category="Animate"),
            CommandEntry("anim_bounce", "Run Bounce Animation", self._run_anim_bounce, category="Animate"),
            CommandEntry("anim_cancel", "Cancel Animation", self._cancel_anim, category="Animate"),
            CommandEntry("files_open", "Open File Dialog", self.open_file_dialog, category="File"),
            CommandEntry("files_save", "Save File Dialog", self.save_file_dialog, category="File"),
            CommandEntry("notif_ping", "Publish Test Notification", self.publish_test_notification, category="Notifications"),
            CommandEntry("state_save", "Save All Feature States", self._save_app_state, category="State"),
            CommandEntry("state_load", "Load All Feature States", self._load_app_state, category="State"),
        ]:
            self._palette_mgr.register(cmd)

    def _open_palette(self) -> None:
        host = self._host
        if host is None or self._palette_mgr is None:
            return
        self._palette_mgr.show(host.app)
        self._pal_log("Palette opened")

    def _register_palette_cmd(self) -> None:
        if self._palette_cmd_input is None or self._palette_mgr is None:
            return
        title = self._palette_cmd_input.value.strip()
        if not title:
            self._pal_log("Enter a command title first")
            return
        entry_id = "user_" + title.lower().replace(" ", "_")
        self._palette_mgr.register(CommandEntry(
            entry_id, title,
            action=lambda t=title: self._pal_log(f"Command '{t}' executed"),
            category="User",
        ))
        self._pal_log(f"Registered: '{title}'")
        self._palette_cmd_input.set_value("")
        if self._palette_commands_list is not None:
            self._palette_commands_list.set_items(self._palette_command_items())

    def _palette_command_items(self) -> list:
        if self._palette_mgr is None:
            return []
        return [
            ListItem(label=f"[{e.category}] {e.title}" if e.category else e.title, value=e.entry_id)
            for e in self._palette_mgr._entries.values()
        ]

    def _pal_log(self, message: str) -> None:
        if self._palette_log is None:
            return
        lines = self._palette_log.value.splitlines()
        if lines == ["Palette activity log."]:
            lines = []
        ts = datetime.now().strftime("%H:%M:%S")
        lines.append(f"[{ts}] {message}")
        self._palette_log.set_value("\n".join(lines[-self.LOG_LIMIT:]))

    # ------------------------------------------------------------------
    # Menu + tree (shared by Files tab)
    # ------------------------------------------------------------------

    def _window_event_handler(self, event) -> bool:
        host = self._host
        if host is None or self.menu_bar is None:
            return False
        return self.menu_bar.handle_event(event, host.app)

    def _menu_entries(self) -> list[MenuEntry]:
        return [
            MenuEntry("File", [
                ContextMenuItem("Open...", action=self.open_file_dialog),
                ContextMenuItem("Save As...", action=self.save_file_dialog),
                ContextMenuItem("", separator=True),
                ContextMenuItem("Export State JSON", action=self._export_state_json),
                ContextMenuItem("", separator=True),
                ContextMenuItem("Minimize", action=self.minimize_window),
            ]),
            MenuEntry("View", [
                ContextMenuItem("Notifications", action=self.show_notifications_panel),
                ContextMenuItem("Publish Test", action=self.publish_test_notification),
            ]),
            MenuEntry("State", [
                ContextMenuItem("Save All Feature States", action=self._save_app_state),
                ContextMenuItem("Load All Feature States", action=self._load_app_state),
            ]),
            MenuEntry("Palette", [
                ContextMenuItem("Open Command Palette", action=self._open_palette),
            ]),
            MenuEntry("Scenes", [
                ContextMenuItem("Main", action=self.go_main_scene),
                ContextMenuItem("Controls Showcase", action=self.go_showcase_scene),
            ]),
        ]

    def _tree_nodes(self) -> list[TreeNode]:
        return [
            TreeNode("Desktop", expanded=True, children=[
                TreeNode("Open File Dialog", data={"action": "open"}),
                TreeNode("Save File Dialog", data={"action": "save"}),
                TreeNode("Show Notifications", data={"action": "notifications"}),
                TreeNode("Publish Test Event", data={"action": "publish"}),
            ]),
            TreeNode("State", expanded=True, children=[
                TreeNode("Save All States", data={"action": "save_state"}),
                TreeNode("Load All States", data={"action": "load_state"}),
                TreeNode("Export State JSON", data={"action": "export_state"}),
            ]),
            TreeNode("Animation", expanded=False, children=[
                TreeNode("Run Sequence", data={"action": "anim_seq"}),
                TreeNode("Run Bounce", data={"action": "anim_bounce"}),
                TreeNode("Cancel", data={"action": "anim_cancel"}),
            ]),
            TreeNode("Palette", expanded=False, children=[
                TreeNode("Open Command Palette", data={"action": "palette"}),
            ]),
            TreeNode("Scenes", expanded=True, children=[
                TreeNode("Go to Main", data={"action": "main"}),
                TreeNode("Go to Showcase", data={"action": "showcase"}),
            ]),
        ]

    def _on_tree_select(self, node: TreeNode, _row_index: int) -> None:
        data = node.data if isinstance(node.data, dict) else {}
        action = str(data.get("action", ""))
        dispatch = {
            "open": self.open_file_dialog,
            "save": self.save_file_dialog,
            "notifications": self.show_notifications_panel,
            "publish": self.publish_test_notification,
            "save_state": self._save_app_state,
            "load_state": self._load_app_state,
            "export_state": self._export_state_json,
            "anim_seq": self._run_anim_sequence,
            "anim_bounce": self._run_anim_bounce,
            "anim_cancel": self._cancel_anim,
            "palette": self._open_palette,
            "main": self.go_main_scene,
            "showcase": self.go_showcase_scene,
        }
        fn = dispatch.get(action)
        if fn is not None:
            fn()

    def minimize_window(self) -> None:
        if self.window is None:
            return
        self.window.visible = False
        host = self._host
        if host is not None and hasattr(host, "set_system_window_visible"):
            host.set_system_window_visible(False)
        self._set_status("Status: minimized")

    def open_file_dialog(self) -> None:
        if self.file_dialogs is None:
            return
        opts = FileDialogOptions(
            title="Open File",
            filters=[("Python", [".py"]), ("Text", [".txt"]), ("All", ["*"])],
        )
        self.file_dialogs.show_open(opts, on_close=self._on_open_result)

    def save_file_dialog(self) -> None:
        if self.file_dialogs is None:
            return
        opts = FileDialogOptions(
            title="Save File",
            filters=[("Text", [".txt"]), ("All", ["*"])],
            allow_new_file=True,
        )
        self.file_dialogs.show_save(opts, on_close=self._on_save_result)

    def show_notifications_panel(self) -> None:
        host = self._host
        if host is None or self.notification_center is None:
            return
        screen = host.app.surface.get_rect()
        panel_rect = Rect(screen.right - 420, 80, 390, min(540, screen.height - 120))
        panel = NotificationPanelControl("system_notification_panel", panel_rect, self.notification_center)
        host.app.overlay.show(
            "system_notification_panel",
            panel,
            dismiss_on_outside_click=True,
            dismiss_on_escape=True,
        )
        self._set_status("Status: notification panel opened")

    def publish_test_notification(self) -> None:
        if self.notification_center is None:
            return
        message = f"Test event at {datetime.now().strftime('%H:%M:%S')}"
        self.notification_center.add(
            NotificationRecord(
                message=message,
                title="System",
                severity=ToastSeverity.SUCCESS,
                topic="demo.system.status",
            )
        )
        self._append_log(f"Notification: {message}")
        self._set_status("Status: test notification published")

    def go_main_scene(self) -> None:
        host = self._host
        if host is None:
            return
        if hasattr(host, "go_to_main"):
            host.go_to_main()
        else:
            host.app.switch_scene("main")

    def go_showcase_scene(self) -> None:
        host = self._host
        if host is None:
            return
        if hasattr(host, "go_to_control_showcase"):
            host.go_to_control_showcase()
        else:
            host.app.switch_scene("control_showcase")

    def _on_open_result(self, paths: list[str]) -> None:
        if paths:
            self._append_log("Open: " + ", ".join(paths))
            self._set_status(f"Status: opened {len(paths)} file(s)")
            if self.notification_center is not None:
                self.notification_center.add(
                    NotificationRecord(message=", ".join(paths), title="Open Result", severity=ToastSeverity.INFO)
                )
            return
        self._append_log("Open cancelled")
        self._set_status("Status: open cancelled")

    def _on_save_result(self, paths: list[str]) -> None:
        if paths:
            self._append_log("Save: " + ", ".join(paths))
            self._set_status(f"Status: save target selected ({len(paths)})")
            if self.notification_center is not None:
                self.notification_center.add(
                    NotificationRecord(message=", ".join(paths), title="Save Result", severity=ToastSeverity.INFO)
                )
            return
        self._append_log("Save cancelled")
        self._set_status("Status: save cancelled")

    def _append_log(self, message: str) -> None:
        if self.log_area is None:
            return
        lines = self.log_area.value.splitlines()
        if lines and lines[0].startswith("System workspace ready"):
            lines = []
        lines.append(str(message))
        self.log_area.set_value("\n".join(lines[-self.LOG_LIMIT:]))

    def _set_status(self, text: str) -> None:
        if self.status_label is not None:
            self.status_label.text = str(text)
