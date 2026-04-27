"""Desktop-style system tools window for exercising new gui_do systems."""

from __future__ import annotations

from datetime import datetime

from pygame import Rect

from gui_do import (
    ButtonControl,
    ContextMenuItem,
    FileDialogManager,
    FileDialogOptions,
    FlexAlign,
    FlexDirection,
    FlexItem,
    FlexJustify,
    FlexLayout,
    LabelControl,
    MenuBarControl,
    MenuEntry,
    NotificationCenter,
    NotificationPanelControl,
    NotificationRecord,
    RoutedFeature,
    TextAreaControl,
    ToastSeverity,
    TreeControl,
    TreeNode,
)


class SystemWindowDemoFeature(RoutedFeature):
    """Main-scene desktop utility window used to shake out new functionality."""

    HOST_REQUIREMENTS = {
        "build": ("app", "root"),
        "configure_accessibility": ("app",),
    }

    LOG_LIMIT = 16

    def __init__(self) -> None:
        super().__init__("system_window_demo", scene_name="main")
        self.window = None
        self.menu_bar = None
        self.tree = None
        self.log_area = None
        self.status_label = None
        self.notification_center = None
        self.file_dialogs = None
        self._toolbar_buttons: list[ButtonControl] = []
        self._host = None

    def build(self, host) -> None:
        self._host = host
        ui = host.app.read_feature_ui_types()
        self.register_font_roles(
            host,
            {
                "window_title": {"size": 14, "file_path": "demo_features/data/fonts/Gimbot.ttf", "system_name": "arial", "bold": True},
                "control": {"size": 15, "file_path": "demo_features/data/fonts/Ubuntu-B.ttf", "system_name": "arial"},
                "status": {"size": 14, "file_path": "demo_features/data/fonts/Ubuntu-B.ttf", "system_name": "arial"},
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
        if self.tree is not None:
            self.tree.set_tab_index(next_index)
            next_index += 1
        return next_index

    def shutdown_runtime(self, _host) -> None:
        if self.notification_center is not None:
            self.notification_center.unsubscribe_all()

    def _build_window(self, host, *, window_control_cls, button_control_cls) -> None:
        rect = host.app.layout.anchored((760, 620), anchor="top_left", margin=(24, 92), use_rect=True)
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
        menu_h = 28

        self.menu_bar = self.window.add(
            MenuBarControl(
                "system_window_menu",
                Rect(content.left + pad, content.top + pad, content.width - (pad * 2), menu_h),
                self._menu_entries(),
            )
        )

        toolbar_rect = Rect(content.left + pad, self.menu_bar.rect.bottom + 8, content.width - (pad * 2), 30)
        open_btn = self.window.add(
            button_control_cls("system_open_btn", Rect(0, 0, 120, 30), "Open File", self.open_file_dialog, font_role=self.font_role("control"))
        )
        save_btn = self.window.add(
            button_control_cls("system_save_btn", Rect(0, 0, 120, 30), "Save As", self.save_file_dialog, font_role=self.font_role("control"))
        )
        inbox_btn = self.window.add(
            button_control_cls("system_inbox_btn", Rect(0, 0, 140, 30), "Notifications", self.show_notifications_panel, font_role=self.font_role("control"))
        )
        ping_btn = self.window.add(
            button_control_cls("system_ping_btn", Rect(0, 0, 120, 30), "Publish Test", self.publish_test_notification, font_role=self.font_role("control"))
        )
        self._toolbar_buttons = [open_btn, save_btn, inbox_btn, ping_btn]
        toolbar_layout = FlexLayout(
            direction=FlexDirection.ROW,
            gap=8,
            align=FlexAlign.STRETCH,
            justify=FlexJustify.START,
            items=[
                FlexItem(open_btn, grow=1, basis=120),
                FlexItem(save_btn, grow=1, basis=120),
                FlexItem(inbox_btn, grow=1, basis=140),
                FlexItem(ping_btn, grow=1, basis=120),
            ],
        )
        toolbar_layout.apply(toolbar_rect)

        body_top = toolbar_rect.bottom + 8
        status_h = 22
        body_bottom = content.bottom - pad - status_h - 6
        body_h = max(120, body_bottom - body_top)
        left_w = int((content.width - (pad * 2)) * 0.38)
        right_w = max(120, (content.width - (pad * 2)) - left_w - 8)

        self.tree = self.window.add(
            TreeControl(
                "system_tree",
                Rect(content.left + pad, body_top, left_w, body_h),
                nodes=self._tree_nodes(),
                on_select=self._on_tree_select,
            )
        )
        self.log_area = self.window.add(
            TextAreaControl(
                "system_log",
                Rect(self.tree.rect.right + 8, body_top, right_w, body_h),
                value="System window ready.\nUse menu, tree, dialogs, and notifications.",
                font_role=self.font_role("control"),
            )
        )
        self.status_label = host.app.style_label(
            self.window.add(
                LabelControl(
                    "system_status",
                    Rect(content.left + pad, body_bottom + 6, content.width - (pad * 2), status_h),
                    "Status: idle",
                    align="left",
                )
            ),
            size=14,
            role=self.font_role("status"),
        )

    def _window_event_handler(self, event) -> bool:
        host = self._host
        if host is None or self.menu_bar is None:
            return False
        return self.menu_bar.handle_event(event, host.app)

    def _menu_entries(self) -> list[MenuEntry]:
        return [
            MenuEntry(
                "File",
                [
                    ContextMenuItem("Open...", action=self.open_file_dialog),
                    ContextMenuItem("Save As...", action=self.save_file_dialog),
                    ContextMenuItem("", separator=True),
                    ContextMenuItem("Minimize", action=self.minimize_window),
                ],
            ),
            MenuEntry(
                "View",
                [
                    ContextMenuItem("Notifications", action=self.show_notifications_panel),
                    ContextMenuItem("Publish Test", action=self.publish_test_notification),
                ],
            ),
            MenuEntry(
                "Scenes",
                [
                    ContextMenuItem("Main", action=self.go_main_scene),
                    ContextMenuItem("Controls Showcase", action=self.go_showcase_scene),
                ],
            ),
        ]

    def _tree_nodes(self) -> list[TreeNode]:
        return [
            TreeNode(
                "Desktop",
                expanded=True,
                children=[
                    TreeNode("Open File Dialog", data={"action": "open"}),
                    TreeNode("Save File Dialog", data={"action": "save"}),
                    TreeNode("Show Notifications", data={"action": "notifications"}),
                    TreeNode("Publish Test Event", data={"action": "publish"}),
                ],
            ),
            TreeNode(
                "Scenes",
                expanded=True,
                children=[
                    TreeNode("Go to Main", data={"action": "main"}),
                    TreeNode("Go to Showcase", data={"action": "showcase"}),
                ],
            ),
        ]

    def _on_tree_select(self, node: TreeNode, _row_index: int) -> None:
        data = node.data if isinstance(node.data, dict) else {}
        action = str(data.get("action", ""))
        if action == "open":
            self.open_file_dialog()
        elif action == "save":
            self.save_file_dialog()
        elif action == "notifications":
            self.show_notifications_panel()
        elif action == "publish":
            self.publish_test_notification()
        elif action == "main":
            self.go_main_scene()
        elif action == "showcase":
            self.go_showcase_scene()

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
        lines.append(str(message))
        self.log_area.set_value("\n".join(lines[-self.LOG_LIMIT :]))

    def _set_status(self, text: str) -> None:
        if self.status_label is not None:
            self.status_label.text = str(text)
