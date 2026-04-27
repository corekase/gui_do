import pygame
from pygame import Rect
from demo_features.mandelbrot_demo_feature import MandelbrotRenderFeature
from demo_features.life_demo_feature import LifeSimulationFeature
from demo_features.bouncing_shapes_demo_feature import BouncingShapesBackdropFeature
from demo_features.controls_demo_feature import ControlsShowcaseFeature
from demo_features.system_window_demo_feature import SystemWindowDemoFeature

from gui_do import (
    GuiApplication,
    PanelControl,
    LabelControl,
    ButtonControl,
    ArrowBoxControl,
    ButtonGroupControl,
    FrameControl,
    ImageControl,
    ScrollbarControl,
    TaskPanelControl,
    ToggleControl,
    LayoutAxis,
    OverlayPanelControl,
    DropdownControl,
    DropdownOption,
    ToastSeverity,
    DataGridControl,
    GridColumn,
    GridRow,
    ContextMenuItem,
    SplitterControl,
    RichLabelControl,
    MenuBarManager,
    SceneTransitionManager,
    SceneTransitionStyle,
    NotificationCenter,
    NotificationRecord,
    NotificationPanelControl,
    ScrollViewControl,
    ColorPickerControl,
)


class GuiDoDemo:
    """Interactive demo app showcasing gui_do controls and scene workflows."""

    TASK_PANEL_CONTROL_FONT_ROLE = "screen.main.task_panel.control"
    SCREEN_TITLE_FONT_ROLE = "screen.main.title"

    def __init__(self) -> None:
        """Initialize pygame, app services, scene state, and demo UI."""
        pygame.init()
        flags = pygame.FULLSCREEN | pygame.SCALED
        self.screen = pygame.display.set_mode((1920, 1080), flags=flags, vsync=1)
        pygame.display.set_caption("gui_do demo")

        self.screen_rect = self.screen.get_rect()
        self.app = GuiApplication(self.screen)
        self.app.register_cursor("normal", "demo_features/data/cursors/cursor.png", (1, 1))
        self.app.register_cursor("hand", "demo_features/data/cursors/hand.png", (12, 12))
        self.app.set_cursor("normal")
        self.app.configure_telemetry(
            enabled=False,
            live_analysis_enabled=True,
            file_logging_enabled=False,
        )
        self.app.layout.set_anchor_bounds(self.screen_rect)
        self.app.create_scene("main")
        self.app.create_scene("control_showcase")
        self.scene_transitions = SceneTransitionManager(self.app, default_style=SceneTransitionStyle.FADE, default_duration=0.22)
        self.scene_transitions.set_style("control_showcase", SceneTransitionStyle.SLIDE_LEFT, duration=0.22)
        self.scene_transitions.set_style("main", SceneTransitionStyle.SLIDE_RIGHT, duration=0.22)
        self.app.configure_window_tiling(gap=16, padding=16, avoid_task_panel=True, center_on_failure=True, relayout=False, scene_name="main")
        self.app.set_window_tiling_enabled(True, relayout=False, scene_name="main")
        self.app.configure_window_tiling(gap=16, padding=16, avoid_task_panel=True, center_on_failure=True, relayout=False, scene_name="control_showcase")
        self.app.set_window_tiling_enabled(True, relayout=False, scene_name="control_showcase")
        self.app.switch_scene("main")

        # Feature registry keeps concerns isolated behind a small lifecycle contract.
        # A single backdrop instance with scene_name=None runs in all scenes so
        # shape positions and velocities are shared and continuous across scene switches.
        self._shapes_feature = BouncingShapesBackdropFeature(
            circle_count=12,
            square_count=12,
            octagon_count=12,
            star_count=12,
        )
        self._life_feature = LifeSimulationFeature()
        self._controls_feature = ControlsShowcaseFeature()
        self._mandel_feature = MandelbrotRenderFeature()
        self._system_feature = SystemWindowDemoFeature()
        for feature in [
            self._shapes_feature,
            self._life_feature,
            self._controls_feature,
            self._mandel_feature,
            self._system_feature,
        ]:
            self.app.register_feature(feature, host=self)

        self._build_main_scene()
        self._build_control_showcase_scene()
        self.app.build_features(self)
        self.life_window = self._life_feature.window
        self.mandel_window = self._mandel_feature.window
        self.system_window = self._system_feature.window
        self.life_window.visible = False
        self.mandel_window.visible = False
        self.system_window.visible = False
        self.app.set_pristine("demo_features/data/images/backdrop.jpg", scene_name="main")
        self.app.set_pristine("demo_features/data/images/backdrop.jpg", scene_name="control_showcase")
        self.app.actions.register_action("exit", lambda _event: (setattr(self.app, "running", False) or True))
        self.app.actions.bind_key(pygame.K_ESCAPE, "exit", scene="main")
        self.app.actions.bind_key(pygame.K_ESCAPE, "exit", scene="control_showcase")
        self.app.bind_features_runtime(self)
        self.app.prewarm_scene("control_showcase")

        base_controls = [
            self.exit_button,
            self.showcase_button,
            self.life_toggle_window,
            self.mandel_toggle_window,
            self.system_toggle_window,
            self.inbox_button,
        ]
        for index, control in enumerate(base_controls):
            control.set_tab_index(index)

        self.exit_button.set_accessibility(role="button", label="Exit")
        self.showcase_button.set_accessibility(role="button", label="Showcase")
        self.life_toggle_window.set_accessibility(role="toggle", label="Show Life window")
        self.mandel_toggle_window.set_accessibility(role="toggle", label="Show Mandelbrot window")
        self.system_toggle_window.set_accessibility(role="toggle", label="Show System window")
        self.inbox_button.set_accessibility(role="button", label="Open notification panel")
        self.app.configure_features_accessibility(self, len(base_controls))

    def _register_screen_font_roles(self) -> None:
        """Register screen-owned font roles for non-part scene composition."""
        self.app.register_font_role(
            self.TASK_PANEL_CONTROL_FONT_ROLE,
            size=16,
            file_path="demo_features/data/fonts/Ubuntu-B.ttf",
            system_name="arial",
            scene_name="main",
        )
        self.app.register_font_role(
            self.TASK_PANEL_CONTROL_FONT_ROLE,
            size=16,
            file_path="demo_features/data/fonts/Ubuntu-B.ttf",
            system_name="arial",
            scene_name="control_showcase",
        )
        self.app.register_font_role(
            self.SCREEN_TITLE_FONT_ROLE,
            size=72,
            file_path="demo_features/data/fonts/Gimbot.ttf",
            system_name="arial",
            scene_name="main",
        )
        self.app.register_font_role(
            self.SCREEN_TITLE_FONT_ROLE,
            size=72,
            file_path="demo_features/data/fonts/Gimbot.ttf",
            system_name="arial",
            scene_name="control_showcase",
        )

    def _make_sized_title_label(
        self,
        control_id: str,
        text: str,
        left: int,
        top: int,
        *,
        fallback_size: tuple[int, int],
    ) -> LabelControl:
        """Create a styled title label whose rect matches the rendered text surface size."""
        label = self.app.style_label(
            LabelControl(control_id, Rect(left, top, int(fallback_size[0]), int(fallback_size[1])), text),
            size=64,
            role=self.SCREEN_TITLE_FONT_ROLE,
        )
        if self.app.theme.fonts.has_role(label.font_role):
            font = self.app.theme.fonts.font_instance(
                label.font_role,
                size=label.font_size,
            )
            label.rect.size = font.text_surface_size(label.text, shadow=True)
        return label

    # ---------------------------------------------------------------------
    # Scene construction and widget composition.
    # ---------------------------------------------------------------------
    def _build_main_scene(self) -> None:
        """Build root scene container, windows, and bottom task panel controls."""
        self._register_screen_font_roles()
        self.root = self.app.add(
            PanelControl("main_root", Rect(0, 0, self.screen_rect.width, self.screen_rect.height), draw_background=False),
            scene_name="main",
        )
        menu_manager = MenuBarManager()
        menu_manager.register_menu(
            "File",
            [
                ContextMenuItem("Open...", action=self._open_file_dialog_from_main),
                ContextMenuItem("Save As...", action=self._save_file_dialog_from_main),
                ContextMenuItem("", separator=True),
                ContextMenuItem("Exit", action=lambda: setattr(self.app, "running", False)),
            ],
        )
        menu_manager.register_menu(
            "Scenes",
            [
                ContextMenuItem("Main", action=self.go_to_main),
                ContextMenuItem("Control Showcase", action=self.go_to_control_showcase),
            ],
        )
        menu_manager.register_menu(
            "Windows",
            [
                ContextMenuItem("Life", action=lambda: self.set_life_window_visible(True)),
                ContextMenuItem("Mandelbrot", action=lambda: self.set_mandel_window_visible(True)),
                ContextMenuItem("System", action=lambda: self.set_system_window_visible(True)),
            ],
        )
        menu_manager.register_menu(
            "Tools",
            [
                ContextMenuItem("Notifications", action=self._open_notifications_panel_from_main),
                ContextMenuItem("Publish Test Event", action=self._publish_system_test_event_from_main),
            ],
        )
        self.desktop_menu_bar = self.root.add(
            menu_manager.build("desktop_menu_bar", Rect(0, 0, self.screen_rect.width, 28), self.app)
        )
        self.screen_title = self.root.add(
            self._make_sized_title_label("screen_title", "gui_do", 24, 36, fallback_size=(640, 96))
        )
        self.task_panel = self.app.add(
            TaskPanelControl(
                "task_panel",
                Rect(0, self.screen_rect.height - 50, self.screen_rect.width, 50),
                auto_hide=True,
                hidden_peek_pixels=6,
                animation_step_px=8,
                dock_bottom=True,
            ),
            scene_name="main",
        )
        self.app.layout.set_linear_properties(
            anchor=(16, self.screen_rect.height - 40),
            item_width=124,
            item_height=30,
            spacing=10,
            horizontal=True,
        )

        def _on_life_toggle(pushed: bool) -> None:
            self.set_life_window_visible(bool(pushed), from_toggle=True)

        def _on_mandel_toggle(pushed: bool) -> None:
            self.set_mandel_window_visible(bool(pushed), from_toggle=True)

        def _on_system_toggle(pushed: bool) -> None:
            self.set_system_window_visible(bool(pushed), from_toggle=True)

        self.exit_button = self.task_panel.add(
            ButtonControl(
                "exit",
                self.app.layout.linear(0),
                "Exit",
                lambda: setattr(self.app, "running", False),
                style="angle",
                font_role=self.TASK_PANEL_CONTROL_FONT_ROLE,
            )
        )
        self.showcase_button = self.task_panel.add(
            ButtonControl(
                "showcase",
                self.app.layout.linear(1),
                "Showcase",
                self.go_to_control_showcase,
                style="angle",
                font_role=self.TASK_PANEL_CONTROL_FONT_ROLE,
            )
        )
        self.life_toggle_window = self.task_panel.add(
            ToggleControl(
                "show_life",
                self.app.layout.linear(2),
                "Life",
                "Life",
                pushed=False,
                on_toggle=_on_life_toggle,
                style="round",
                font_role=self.TASK_PANEL_CONTROL_FONT_ROLE,
            )
        )
        self.mandel_toggle_window = self.task_panel.add(
            ToggleControl(
                "show_mandel",
                self.app.layout.linear(3),
                "Mandelbrot",
                "Mandelbrot",
                pushed=False,
                on_toggle=_on_mandel_toggle,
                style="round",
                font_role=self.TASK_PANEL_CONTROL_FONT_ROLE,
            )
        )
        self.system_toggle_window = self.task_panel.add(
            ToggleControl(
                "show_system",
                self.app.layout.linear(4),
                "System",
                "System",
                pushed=False,
                on_toggle=_on_system_toggle,
                style="round",
                font_role=self.TASK_PANEL_CONTROL_FONT_ROLE,
            )
        )
        self.inbox_button = self.task_panel.add(
            ButtonControl(
                "show_notifications",
                self.app.layout.linear(5),
                "Inbox",
                self._open_notifications_panel_from_main,
                style="angle",
                font_role=self.TASK_PANEL_CONTROL_FONT_ROLE,
            )
        )

        right_margin = 16
        right_gap = 10
        system_w = self.system_toggle_window.rect.width
        inbox_w = self.inbox_button.rect.width
        y = self.task_panel.rect.top + 10
        inbox_x = self.task_panel.rect.right - right_margin - inbox_w
        system_x = inbox_x - right_gap - system_w
        self.system_toggle_window.rect.topleft = (system_x, y)
        self.inbox_button.rect.topleft = (inbox_x, y)
        self._build_main_scene_controls_dock()
        self.app.tile_windows()

    def _build_main_scene_controls_dock(self) -> None:
        dock_width = 560
        dock_margin_right = 24
        dock_top = 112
        dock_left = self.screen_rect.right - dock_margin_right - dock_width
        dock_bottom = self.task_panel.rect.top - 18
        dock_height = max(320, dock_bottom - dock_top)
        header_h = 28
        scroll_margin = 12
        notification_panel_h = 188
        notification_label_h = 20
        notification_gap = 8
        preview_gap = 14
        overlay_h = 88

        self.main_controls_dock = self.root.add(
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
        dock_title.font_role = self.TASK_PANEL_CONTROL_FONT_ROLE
        self.main_controls_dock.add(dock_title)

        scroll_top = dock_top + header_h + 18
        fixed_preview_h = notification_label_h + notification_gap + notification_panel_h
        scroll_bottom = dock_top + dock_height - overlay_h - fixed_preview_h - (preview_gap * 2)
        scroll_rect = Rect(
            dock_left + scroll_margin,
            scroll_top,
            dock_width - (scroll_margin * 2),
            max(160, scroll_bottom - scroll_top),
        )
        self.main_controls_scroll = self.main_controls_dock.add(
            ScrollViewControl(
                "main_controls_scroll",
                scroll_rect,
                content_width=scroll_rect.width - 14,
                content_height=1050,
                scroll_y=True,
            )
        )
        self.main_controls_scroll.set_tab_index(-1)

        content_w = scroll_rect.width - 24
        y = 0

        def add_scroll_child(control, x: int, y_pos: int, *, focusable: bool = False) -> None:
            if not focusable:
                control.set_tab_index(-1)
            self.main_controls_scroll.add(control, content_x=x, content_y=y_pos)

        add_scroll_child(
            RichLabelControl(
                "main_controls_intro",
                Rect(0, 0, content_w, 68),
                text="This dock integrates the remaining gui_do controls directly into the main scene using concrete utility-style samples.",
                font_role=self.TASK_PANEL_CONTROL_FONT_ROLE,
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
        add_scroll_child(ButtonGroupControl("main_group_overview", Rect(0, 0, group_w, 28), "main_scene_mode", "Overview", selected=True, font_role=self.TASK_PANEL_CONTROL_FONT_ROLE), 0, group_y)
        add_scroll_child(ButtonGroupControl("main_group_logs", Rect(0, 0, group_w, 28), "main_scene_mode", "Logs", font_role=self.TASK_PANEL_CONTROL_FONT_ROLE), group_w + 8, group_y)
        add_scroll_child(ButtonGroupControl("main_group_assets", Rect(0, 0, group_w, 28), "main_scene_mode", "Assets", font_role=self.TASK_PANEL_CONTROL_FONT_ROLE), (group_w + 8) * 2, group_y)
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
                font_role=self.TASK_PANEL_CONTROL_FONT_ROLE,
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

        self.main_controls_scroll.set_content_size(content_w, y + 12)

        preview_top = scroll_rect.bottom + preview_gap
        self.main_controls_notifications_label = LabelControl(
            "main_controls_notifications_label",
            Rect(dock_left + scroll_margin, preview_top, dock_width - (scroll_margin * 2), notification_label_h),
            "Inbox Preview",
            align="left",
        )
        self.main_controls_notifications_label.font_role = self.TASK_PANEL_CONTROL_FONT_ROLE
        self.main_controls_dock.add(self.main_controls_notifications_label)

        self.main_scene_notification_center = NotificationCenter(self.app.events, max_records=16)
        self.main_scene_notification_center.add(NotificationRecord("Main scene controls dock ready", title="Dock", severity=ToastSeverity.SUCCESS))
        self.main_scene_notification_center.add(NotificationRecord("Window tiling available", title="Workspace", severity=ToastSeverity.INFO))
        self.main_scene_notification_center.add(NotificationRecord("Two background tasks queued", title="Scheduler", severity=ToastSeverity.WARNING))
        self.main_scene_notification_panel = NotificationPanelControl(
            "main_scene_notification_panel",
            Rect(
                dock_left + scroll_margin,
                preview_top + notification_label_h + notification_gap,
                dock_width - (scroll_margin * 2),
                notification_panel_h,
            ),
            self.main_scene_notification_center,
        )
        self.main_scene_notification_panel.set_tab_index(-1)
        self.main_controls_dock.add(self.main_scene_notification_panel)

        overlay_top = dock_top + dock_height - overlay_h - 10
        self.main_scene_overlay_panel = self.main_controls_dock.add(
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
                Rect(0, 0, self.main_scene_overlay_panel.rect.width - 20, 18),
                text,
                align="left",
            )
            label.font_role = self.TASK_PANEL_CONTROL_FONT_ROLE
            self.main_scene_overlay_panel.add_at(label, rel_x=10, rel_y=8 + index * 22)

    def _build_control_showcase_scene(self) -> None:
        """Build the control showcase scene and provide a way back to main."""
        self.control_showcase_root = self.app.add(
            PanelControl(
                "control_showcase_root",
                Rect(0, 0, self.screen_rect.width, self.screen_rect.height),
                draw_background=False,
            ),
            scene_name="control_showcase",
        )

    def run(self) -> None:
        """Run demo engine and perform shutdown cleanup on exit."""
        self.app.run(target_fps=120)
        pygame.quit()

    def go_to_control_showcase(self) -> None:
        self.scene_transitions.go("control_showcase")

    def go_to_main(self) -> None:
        self.scene_transitions.go("main")

    def set_life_window_visible(self, visible: bool, *, from_toggle: bool = False) -> None:
        show = bool(visible)
        self.life_window.visible = show
        if not from_toggle and self.life_toggle_window is not None:
            self.life_toggle_window.pushed = show
        self.app.tile_windows(newly_visible=[self.life_window] if show else None)

    def set_mandel_window_visible(self, visible: bool, *, from_toggle: bool = False) -> None:
        show = bool(visible)
        self.mandel_window.visible = show
        if not from_toggle and self.mandel_toggle_window is not None:
            self.mandel_toggle_window.pushed = show
        self.app.tile_windows(newly_visible=[self.mandel_window] if show else None)

    def set_system_window_visible(self, visible: bool, *, from_toggle: bool = False) -> None:
        show = bool(visible)
        self.system_window.visible = show
        if not from_toggle and self.system_toggle_window is not None:
            self.system_toggle_window.pushed = show
        self.app.tile_windows(newly_visible=[self.system_window] if show else None)

    def _open_file_dialog_from_main(self) -> None:
        if self._system_feature is not None:
            self._system_feature.open_file_dialog()

    def _save_file_dialog_from_main(self) -> None:
        if self._system_feature is not None:
            self._system_feature.save_file_dialog()

    def _open_notifications_panel_from_main(self) -> None:
        if self._system_feature is not None:
            self._system_feature.show_notifications_panel()

    def _publish_system_test_event_from_main(self) -> None:
        if self._system_feature is not None:
            self._system_feature.publish_test_notification()


def main() -> None:
    """Entrypoint for running the gui_do demo as a script."""
    GuiDoDemo().run()


if __name__ == "__main__":
    main()
