"""Main scene feature extracted from the gui_do demo entrypoint."""

from __future__ import annotations

from pygame import Rect

from gui_do import (
    ArrowBoxControl,
    ArrangeContext,
    ButtonControl,
    ButtonGroupControl,
    CanvasViewport,
    ColorPickerControl,
    ContextMenuItem,
    DataGridControl,
    DropdownControl,
    DropdownOption,
    Feature,
    FixedItemSource,
    FrameControl,
    GridColumn,
    GridRow,
    ImageControl,
    LabelControl,
    LayoutAxis,
    LayoutRoot,
    MeasureContext,
    MenuBarManager,
    NotificationCenter,
    NotificationPanelControl,
    NotificationRecord,
    NumericFormatter,
    OverlayPanelControl,
    PanelControl,
    PatternFormatter,
    RichLabelControl,
    ScrollbarControl,
    ScrollViewControl,
    ScopedTheme,
    ScopedThemeManager,
    SelectionMode,
    SelectionModel,
    SplitterControl,
    TaskPanelControl,
    ToastSeverity,
    ToggleControl,
    TooltipManager,
)


class MainDemoFeature(Feature):
    """Build the demo's main scene surface and dock controls."""

    HOST_REQUIREMENTS = {
        "build": (
            "app",
            "screen_rect",
            "font_roles",
            "TASK_PANEL_CONTROL_FONT_ROLE",
            "SCREEN_TITLE_FONT_ROLE",
            "go_to_main",
            "go_to_control_showcase",
            "set_life_window_visible",
            "set_mandel_window_visible",
            "set_system_window_visible",
            "_open_file_dialog_from_main",
            "_save_file_dialog_from_main",
            "_open_notifications_panel_from_main",
            "_publish_system_test_event_from_main",
        )
    }

    def __init__(self) -> None:
        super().__init__("main_demo", scene_name="main")

    def build(self, host) -> None:
        self._register_screen_font_roles(host)

        host.root = host.app.add(
            PanelControl("main_root", Rect(0, 0, host.screen_rect.width, host.screen_rect.height), draw_background=False),
            scene_name="main",
        )

        menu_manager = MenuBarManager()
        menu_manager.register_menu(
            "File",
            [
                ContextMenuItem("Open...", action=host._open_file_dialog_from_main),
                ContextMenuItem("Save As...", action=host._save_file_dialog_from_main),
                ContextMenuItem("", separator=True),
                ContextMenuItem("Exit", action=lambda: setattr(host.app, "running", False)),
            ],
        )
        menu_manager.register_menu(
            "Scenes",
            [
                ContextMenuItem("Main", action=host.go_to_main),
                ContextMenuItem("Control Showcase", action=host.go_to_control_showcase),
            ],
        )
        menu_manager.register_menu(
            "Windows",
            [
                ContextMenuItem("Life", action=lambda: host.set_life_window_visible(True)),
                ContextMenuItem("Mandelbrot", action=lambda: host.set_mandel_window_visible(True)),
                ContextMenuItem("System", action=lambda: host.set_system_window_visible(True)),
            ],
        )
        menu_manager.register_menu(
            "Tools",
            [
                ContextMenuItem("Notifications", action=host._open_notifications_panel_from_main),
                ContextMenuItem("Publish Test Event", action=host._publish_system_test_event_from_main),
            ],
        )
        host.desktop_menu_bar = host.root.add(
            menu_manager.build("desktop_menu_bar", Rect(0, 0, host.screen_rect.width, 28), host.app)
        )
        host.screen_title = host.root.add(
            self._make_sized_title_label(host, "screen_title", "gui_do", 24, 36, fallback_size=(640, 96))
        )
        host.task_panel = host.app.add(
            TaskPanelControl(
                "task_panel",
                Rect(0, host.screen_rect.height - 50, host.screen_rect.width, 50),
                auto_hide=True,
                hidden_peek_pixels=6,
                animation_step_px=8,
                dock_bottom=True,
            ),
            scene_name="main",
        )

        host.app.layout.set_linear_properties(
            anchor=(16, host.screen_rect.height - 40),
            item_width=124,
            item_height=30,
            spacing=10,
            horizontal=True,
        )

        def _on_life_toggle(pushed: bool) -> None:
            host.set_life_window_visible(bool(pushed), from_toggle=True)

        def _on_mandel_toggle(pushed: bool) -> None:
            host.set_mandel_window_visible(bool(pushed), from_toggle=True)

        def _on_system_toggle(pushed: bool) -> None:
            host.set_system_window_visible(bool(pushed), from_toggle=True)

        host.exit_button = host.task_panel.add(
            ButtonControl(
                "exit",
                host.app.layout.linear(0),
                "Exit",
                lambda: setattr(host.app, "running", False),
                style="angle",
                font_role=host.TASK_PANEL_CONTROL_FONT_ROLE,
            )
        )
        host.showcase_button = host.task_panel.add(
            ButtonControl(
                "showcase",
                host.app.layout.linear(1),
                "Showcase",
                host.go_to_control_showcase,
                style="angle",
                font_role=host.TASK_PANEL_CONTROL_FONT_ROLE,
            )
        )
        host.life_toggle_window = host.task_panel.add(
            ToggleControl(
                "show_life",
                host.app.layout.linear(2),
                "Life",
                "Life",
                pushed=False,
                on_toggle=_on_life_toggle,
                style="round",
                font_role=host.TASK_PANEL_CONTROL_FONT_ROLE,
            )
        )
        host.mandel_toggle_window = host.task_panel.add(
            ToggleControl(
                "show_mandel",
                host.app.layout.linear(3),
                "Mandelbrot",
                "Mandelbrot",
                pushed=False,
                on_toggle=_on_mandel_toggle,
                style="round",
                font_role=host.TASK_PANEL_CONTROL_FONT_ROLE,
            )
        )
        host.system_toggle_window = host.task_panel.add(
            ToggleControl(
                "show_system",
                host.app.layout.linear(4),
                "System",
                "System",
                pushed=False,
                on_toggle=_on_system_toggle,
                style="round",
                font_role=host.TASK_PANEL_CONTROL_FONT_ROLE,
            )
        )
        host.inbox_button = host.task_panel.add(
            ButtonControl(
                "show_notifications",
                host.app.layout.linear(5),
                "Inbox",
                host._open_notifications_panel_from_main,
                style="angle",
                font_role=host.TASK_PANEL_CONTROL_FONT_ROLE,
            )
        )

        right_margin = 16
        right_gap = 10
        system_w = host.system_toggle_window.rect.width
        inbox_w = host.inbox_button.rect.width
        y = host.task_panel.rect.top + 10
        inbox_x = host.task_panel.rect.right - right_margin - inbox_w
        system_x = inbox_x - right_gap - system_w
        host.system_toggle_window.rect.topleft = (system_x, y)
        host.inbox_button.rect.topleft = (inbox_x, y)

        host._main_tooltip_manager = TooltipManager(default_delay_ms=500)
        host._main_tooltip_manager.register(host.exit_button, "Exit the application")
        host._main_tooltip_manager.register(host.showcase_button, "Open the control showcase scene")
        host._main_tooltip_manager.register(host.life_toggle_window, "Toggle the Life simulation window")
        host._main_tooltip_manager.register(host.mandel_toggle_window, "Toggle the Mandelbrot fractal window")
        host._main_tooltip_manager.register(host.system_toggle_window, "Toggle the system utilities window")
        host._main_tooltip_manager.register(host.inbox_button, "Open the notification inbox panel")

        self._build_main_scene_controls_dock(host)
        host.app.tile_windows()

    def _register_screen_font_roles(self, host) -> None:
        for scene_name in ("main", "control_showcase"):
            host.font_roles.apply(host.app, scene_name=scene_name)

    def _make_sized_title_label(
        self,
        host,
        control_id: str,
        text: str,
        left: int,
        top: int,
        *,
        fallback_size: tuple[int, int],
    ) -> LabelControl:
        label = host.app.style_label(
            LabelControl(control_id, Rect(left, top, int(fallback_size[0]), int(fallback_size[1])), text),
            size=64,
            role=host.SCREEN_TITLE_FONT_ROLE,
        )
        if host.app.theme.fonts.has_role(label.font_role):
            font = host.app.theme.fonts.font_instance(label.font_role, size=label.font_size)
            label.rect.size = font.text_surface_size(label.text, shadow=True)
        return label

    def _build_main_scene_controls_dock(self, host) -> None:
        dock_width = 560
        dock_margin_right = 24
        dock_top = 112
        dock_left = host.screen_rect.right - dock_margin_right - dock_width
        dock_bottom = host.task_panel.rect.top - 18
        dock_height = max(320, dock_bottom - dock_top)
        header_h = 28
        scroll_margin = 12
        notification_panel_h = 188
        notification_label_h = 20
        notification_gap = 8
        preview_gap = 14
        overlay_h = 88

        host.main_controls_dock = host.root.add(
            PanelControl(
                "main_controls_dock",
                Rect(dock_left, dock_top, dock_width, dock_height),
                draw_background=True,
            )
        )

        dock_title = LabelControl(
            "main_controls_dock_title",
            Rect(dock_left + scroll_margin, dock_top + 10, dock_width - (scroll_margin * 2), header_h),
            "Main Scene Control Dock",
            align="left",
        )
        dock_title.font_role = host.TASK_PANEL_CONTROL_FONT_ROLE
        host.main_controls_dock.add(dock_title)

        scroll_top = dock_top + header_h + 18
        fixed_preview_h = notification_label_h + notification_gap + notification_panel_h
        scroll_bottom = dock_top + dock_height - overlay_h - fixed_preview_h - (preview_gap * 2)
        scroll_rect = Rect(
            dock_left + scroll_margin,
            scroll_top,
            dock_width - (scroll_margin * 2),
            max(160, scroll_bottom - scroll_top),
        )
        host.main_controls_scroll = host.main_controls_dock.add(
            ScrollViewControl(
                "main_controls_scroll",
                scroll_rect,
                content_width=scroll_rect.width - 14,
                content_height=1050,
                scroll_y=True,
            )
        )
        host.main_controls_scroll.set_tab_index(-1)

        content_w = scroll_rect.width - 24
        scroll_stack = host.app.compose_scroll_stack(host.main_controls_scroll)
        y = 0

        def add_scroll_child(control, x: int, y_pos: int, *, focusable: bool = False) -> None:
            scroll_stack.add(control, x=x, y=y_pos, focusable=focusable)

        add_scroll_child(
            RichLabelControl(
                "main_controls_intro",
                Rect(0, 0, content_w, 68),
                text="This dock integrates the remaining gui_do controls directly into the main scene using concrete utility-style samples.",
                font_role=host.TASK_PANEL_CONTROL_FONT_ROLE,
            ),
            0,
            y,
        )
        y += 82

        add_scroll_child(LabelControl("main_controls_nav_label", Rect(0, 0, 180, 20), "Arrow Pad", align="left"), 0, y)
        arrow_y = y + 24
        arrow_size = 34
        arrow_gap = 8
        add_scroll_child(ArrowBoxControl("main_arrow_up", Rect(0, 0, arrow_size, arrow_size), 90), 0, arrow_y)
        add_scroll_child(ArrowBoxControl("main_arrow_down", Rect(0, 0, arrow_size, arrow_size), 270), arrow_size + arrow_gap, arrow_y)
        add_scroll_child(ArrowBoxControl("main_arrow_left", Rect(0, 0, arrow_size, arrow_size), 180), (arrow_size + arrow_gap) * 2, arrow_y)
        add_scroll_child(ArrowBoxControl("main_arrow_right", Rect(0, 0, arrow_size, arrow_size), 0), (arrow_size + arrow_gap) * 3, arrow_y)
        y = arrow_y + arrow_size + 22

        add_scroll_child(LabelControl("main_controls_group_label", Rect(0, 0, 180, 20), "View Mode", align="left"), 0, y)
        group_y = y + 24
        group_w = 104
        add_scroll_child(ButtonGroupControl("main_group_overview", Rect(0, 0, group_w, 28), "main_scene_mode", "Overview", selected=True, font_role=host.TASK_PANEL_CONTROL_FONT_ROLE), 0, group_y)
        add_scroll_child(ButtonGroupControl("main_group_logs", Rect(0, 0, group_w, 28), "main_scene_mode", "Logs", font_role=host.TASK_PANEL_CONTROL_FONT_ROLE), group_w + 8, group_y)
        add_scroll_child(ButtonGroupControl("main_group_assets", Rect(0, 0, group_w, 28), "main_scene_mode", "Assets", font_role=host.TASK_PANEL_CONTROL_FONT_ROLE), (group_w + 8) * 2, group_y)
        y = group_y + 44

        add_scroll_child(LabelControl("main_controls_dropdown_label", Rect(0, 0, 220, 20), "Scene Preset", align="left"), 0, y)
        add_scroll_child(
            DropdownControl(
                "main_scene_preset_dropdown",
                Rect(0, 0, 220, 30),
                [
                    DropdownOption("Presentation"),
                    DropdownOption("Diagnostics"),
                    DropdownOption("Quiet Mode"),
                ],
                selected_index=0,
                font_role=host.TASK_PANEL_CONTROL_FONT_ROLE,
            ),
            0,
            y + 24,
        )
        y += 68

        add_scroll_child(LabelControl("main_controls_splitter_label", Rect(0, 0, 220, 20), "Split Workspace", align="left"), 0, y)
        add_scroll_child(
            SplitterControl(
                "main_scene_splitter",
                Rect(0, 0, content_w, 48),
                axis=LayoutAxis.HORIZONTAL,
                ratio=0.62,
            ),
            0,
            y + 24,
        )
        y += 88

        add_scroll_child(LabelControl("main_controls_color_label", Rect(0, 0, 220, 20), "Accent Color", align="left"), 0, y)
        picker_y = y + 24
        add_scroll_child(
            ColorPickerControl(
                "main_scene_color_picker",
                Rect(0, 0, 220, 180),
                color=(64, 128, 255),
            ),
            0,
            picker_y,
        )
        add_scroll_child(
            ScrollbarControl(
                "main_scene_scrollbar",
                Rect(0, 0, 18, 180),
                LayoutAxis.VERTICAL,
                content_size=1000,
                viewport_size=220,
                offset=140,
                step=24,
            ),
            232,
            picker_y,
        )
        add_scroll_child(FrameControl("main_scene_preview_frame", Rect(0, 0, 120, 120), border_width=2), 276, picker_y)
        add_scroll_child(
            ImageControl(
                "main_scene_preview_image",
                Rect(0, 0, 104, 104),
                "demo_features/data/images/realize.png",
            ),
            284,
            picker_y + 8,
        )
        y = picker_y + 198

        add_scroll_child(LabelControl("main_controls_grid_label", Rect(0, 0, 220, 20), "Job Queue", align="left"), 0, y)
        add_scroll_child(
            DataGridControl(
                "main_scene_data_grid",
                Rect(0, 0, content_w, 176),
                columns=[
                    GridColumn("task", "Task", width=200),
                    GridColumn("state", "State", width=120),
                    GridColumn("owner", "Owner", width=120),
                ],
                rows=[
                    GridRow({"task": "Build main scene", "state": "Ready", "owner": "UI"}, row_id="job-1"),
                    GridRow({"task": "Tile windows", "state": "Queued", "owner": "Layout"}, row_id="job-2"),
                    GridRow({"task": "Publish toast", "state": "Done", "owner": "Events"}, row_id="job-3"),
                ],
                show_scrollbar=True,
            ),
            0,
            y + 24,
        )
        y += 216

        row_lbl_h = 20
        row_val_h = 22
        item_gap = 8
        scroll_stack.set_y(y)

        _num_fmt = NumericFormatter(decimals=2, thousands_sep=",")
        budget_input = _num_fmt.create_text_input(
            "main_budget_input",
            Rect(0, 0, 220, 30),
            raw_value="12500",
            placeholder="0.00",
            font_role=host.TASK_PANEL_CONTROL_FONT_ROLE,
        )
        scroll_stack.add_labeled_value(
            LabelControl("main_num_fmt_label", Rect(0, 0, content_w, row_lbl_h), "Budget USD (NumericFormatter)", align="left"),
            budget_input,
            x=0,
            label_gap=4,
            item_gap=item_gap,
            focusable_value=True,
        )

        _pat_fmt = PatternFormatter("###-###-####")
        phone_input = _pat_fmt.create_text_input(
            "main_phone_input",
            Rect(0, 0, 220, 30),
            raw_value="5551234567",
            placeholder="###-###-####",
            font_role=host.TASK_PANEL_CONTROL_FONT_ROLE,
        )
        scroll_stack.add_labeled_value(
            LabelControl("main_phone_label", Rect(0, 0, content_w, row_lbl_h), "Phone (PatternFormatter)", align="left"),
            phone_input,
            x=0,
            label_gap=4,
            item_gap=item_gap,
            focusable_value=True,
        )

        host._main_sel_model = SelectionModel(mode=SelectionMode.MULTI, item_count=4)
        host._main_sel_model.select(0)
        host._main_sel_model.select(2)
        scroll_stack.add_labeled_value(
            LabelControl("main_sel_label", Rect(0, 0, content_w, row_lbl_h), "Selection Model (MULTI)", align="left"),
            LabelControl(
                "main_sel_value",
                Rect(0, 0, content_w, row_val_h),
                f"Selected: {sorted(host._main_sel_model.selected_indices)}",
                align="left",
            ),
            x=0,
            label_gap=4,
            item_gap=item_gap,
        )

        host._main_asset_source = FixedItemSource(["backdrop.jpg", "cursor.png", "hand.png", "realize.png"])
        scroll_stack.add(
            LabelControl("main_src_label", Rect(0, 0, content_w, row_lbl_h), "Asset Library (FixedItemSource)", align="left"),
            x=0,
            gap_after=4,
        )
        for idx in range(host._main_asset_source.item_count()):
            scroll_stack.add(
                LabelControl(
                    f"main_src_item_{idx}",
                    Rect(0, 0, content_w - 12, row_val_h),
                    f"  {host._main_asset_source.item_at(idx)}",
                    align="left",
                ),
                x=12,
            )
        scroll_stack.advance(item_gap)

        host._main_canvas_viewport = CanvasViewport(
            content_size=(1280, 960),
            min_scale=0.1,
            max_scale=8.0,
        )
        viewport = host._main_canvas_viewport
        scroll_stack.add_labeled_value(
            LabelControl("main_vp_label", Rect(0, 0, content_w, row_lbl_h), "Canvas Viewport", align="left"),
            LabelControl(
                "main_vp_value",
                Rect(0, 0, content_w, row_val_h),
                f"Scale: {viewport.scale:.2f}  Content: {viewport.content_size[0]}x{viewport.content_size[1]}  Offset: {viewport.offset}",
                align="left",
            ),
            x=0,
            label_gap=4,
            item_gap=item_gap,
        )

        scroll_stack.add_labeled_value(
            LabelControl("main_adp_label", Rect(0, 0, content_w, row_lbl_h), "Async Data Provider", align="left"),
            LabelControl(
                "main_adp_value",
                Rect(0, 0, content_w, row_val_h),
                "State: IDLE  -  call .load(fn) to start a background fetch",
                align="left",
            ),
            x=0,
            label_gap=4,
            item_gap=item_gap,
        )

        host._main_scoped_theme_mgr = ScopedThemeManager({"color.accent": (64, 128, 255), "color.surface": (30, 30, 40)})
        host._main_scoped_theme_mgr.push(ScopedTheme({"color.accent": (255, 140, 0)}, name="dock-theme"))
        accent = host._main_scoped_theme_mgr.resolve("color.accent", (0, 0, 0))
        scroll_stack.add_labeled_value(
            LabelControl("main_theme_label", Rect(0, 0, content_w, row_lbl_h), "Scoped Theme", align="left"),
            LabelControl(
                "main_theme_value",
                Rect(0, 0, content_w, row_val_h),
                f"Depth: {host._main_scoped_theme_mgr.depth}  accent -> {accent}",
                align="left",
            ),
            x=0,
            label_gap=4,
            item_gap=item_gap,
        )

        scroll_stack.add_labeled_value(
            LabelControl("main_fscope_label", Rect(0, 0, content_w, row_lbl_h), "Focus Scope Manager", align="left"),
            LabelControl(
                "main_fscope_value",
                Rect(0, 0, content_w, row_val_h),
                "push(FocusScope(root, id)) -> Tab contained to modal subtree",
                align="left",
            ),
            x=0,
            label_gap=4,
            item_gap=item_gap,
        )

        class _DockLayout:
            def measure(self, ctx: MeasureContext) -> tuple:
                return (content_w, 200)

            def arrange(self, ctx: ArrangeContext) -> None:
                return None

        host._main_layout_root = LayoutRoot(layout=_DockLayout())
        host._main_layout_root.update(Rect(0, 0, content_w, 200))
        scroll_stack.add_labeled_value(
            LabelControl("main_layout_label", Rect(0, 0, content_w, row_lbl_h), "Layout Root (two-pass)", align="left"),
            LabelControl(
                "main_layout_value",
                Rect(0, 0, content_w, row_val_h),
                f"Preferred: {host._main_layout_root.preferred_size[0]}x{host._main_layout_root.preferred_size[1]}  dirty: {host._main_layout_root.is_dirty}",
                align="left",
            ),
            x=0,
            label_gap=4,
            item_gap=item_gap,
        )

        scroll_stack.add_labeled_value(
            LabelControl("main_trans_label", Rect(0, 0, content_w, row_lbl_h), "Transition Manager", align="left"),
            LabelControl(
                "main_trans_value",
                Rect(0, 0, content_w, row_val_h),
                "register(id, SHOW, TransitionSpec(attr, val, secs)) -> tween on state change",
                align="left",
            ),
            x=0,
            label_gap=4,
            item_gap=item_gap,
        )

        scroll_stack.add_labeled_value(
            LabelControl("main_tooltip_label", Rect(0, 0, content_w, row_lbl_h), "Tooltip Manager", align="left"),
            LabelControl(
                "main_tooltip_value",
                Rect(0, 0, content_w, row_val_h),
                "Delay: 500 ms  6 tooltips registered on task panel buttons",
                align="left",
            ),
            x=0,
            label_gap=4,
            item_gap=item_gap,
        )
        y = scroll_stack.y

        host.main_controls_scroll.set_content_size(content_w, y + 12)

        preview_top = scroll_rect.bottom + preview_gap
        host.main_controls_notifications_label = LabelControl(
            "main_controls_notifications_label",
            Rect(dock_left + scroll_margin, preview_top, dock_width - (scroll_margin * 2), notification_label_h),
            "Inbox Preview",
            align="left",
        )
        host.main_controls_notifications_label.font_role = host.TASK_PANEL_CONTROL_FONT_ROLE
        host.main_controls_dock.add(host.main_controls_notifications_label)

        host.main_scene_notification_center = NotificationCenter(host.app.events, max_records=16)
        host.main_scene_notification_center.add(NotificationRecord("Main scene controls dock ready", title="Dock", severity=ToastSeverity.SUCCESS))
        host.main_scene_notification_center.add(NotificationRecord("Window tiling available", title="Workspace", severity=ToastSeverity.INFO))
        host.main_scene_notification_center.add(NotificationRecord("Two background tasks queued", title="Scheduler", severity=ToastSeverity.WARNING))
        host.main_scene_notification_panel = NotificationPanelControl(
            "main_scene_notification_panel",
            Rect(
                dock_left + scroll_margin,
                preview_top + notification_label_h + notification_gap,
                dock_width - (scroll_margin * 2),
                notification_panel_h,
            ),
            host.main_scene_notification_center,
        )
        host.main_scene_notification_panel.set_tab_index(-1)
        host.main_controls_dock.add(host.main_scene_notification_panel)

        overlay_top = dock_top + dock_height - overlay_h - 10
        host.main_scene_overlay_panel = host.main_controls_dock.add(
            OverlayPanelControl(
                "main_scene_overlay_panel",
                Rect(dock_left + 12, overlay_top, dock_width - 24, overlay_h),
                draw_background=True,
            )
        )
        overlay_items = (
            "Overlay HUD",
            "Pinned status card",
            "Quick glance summary",
        )
        for index, text in enumerate(overlay_items):
            label = LabelControl(
                f"main_scene_overlay_label_{index}",
                Rect(0, 0, host.main_scene_overlay_panel.rect.width - 20, 18),
                text,
                align="left",
            )
            label.font_role = host.TASK_PANEL_CONTROL_FONT_ROLE
            host.main_scene_overlay_panel.add_at(label, rel_x=10, rel_y=8 + index * 22)
