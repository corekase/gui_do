"""Main scene feature extracted from the gui_do demo entrypoint."""

from __future__ import annotations

from pygame import Rect

from gui_do import (
    ArrowBoxControl,
    ArrangeContext,
    Binding,
    BindingGroup,
    ButtonControl,
    ButtonGroupControl,
    CanvasViewport,
    ColorPickerControl,
    CommandHistory,
    DataGridControl,
    DropdownControl,
    DropdownOption,
    ErrorBoundary,
    Feature,
    FixedItemSource,
    FixedPatternFormatter,
    FrameControl,
    GridColumn,
    GridRow,
    ImageControl,
    LabelControl,
    LayoutAxis,
    LayoutRoot,
    MeasureContext,
    MenuEntry,
    SceneMenuStripControl,
    NotificationCenter,
    NotificationPanelControl,
    NotificationRecord,
    NumericFormatter,
    ObservableDict,
    ObservableList,
    ObservableValue,
    OverlayPanelControl,
    PanelControl,
    PatternFormatter,
    RichLabelControl,
    Router,
    ScrollbarControl,
    ScrollViewControl,
    ScopedTheme,
    ScopedThemeManager,
    SelectionMode,
    SelectionModel,
    SettingsRegistry,
    SplitterControl,
    StateMachine,
    TaskPanelControl,
    ThemeManager,
    ToastSeverity,
    ToggleControl,
    TooltipManager,
    CollectionView,
    CollectionViewQuery,
    ContextMenuManager,
    ContextMenuItem,
    DocumentModel,
    FormSchema,
    InvalidationTracker,
    PresentationModel,
    SchemaField,
    TransferData,
    TransferManager,


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
            "action_registry",
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

        def _extra_entries() -> list[MenuEntry]:
            tools_items = host.action_registry.context_menu_items(category="Tools")
            if not tools_items:
                return []
            return [MenuEntry("Tools", tools_items)]

        scene_select = getattr(
            getattr(host, "scene_transitions", None),
            "go",
            getattr(host.app, "switch_scene", lambda _scene: None),
        )

        host.desktop_menu_bar = host.root.add(
            SceneMenuStripControl(
                "desktop_menu_bar",
                Rect(0, 0, host.screen_rect.width, 28),
                host.app,
                scene_name="main",
                scenes_shown=True,
                windows_shown=True,
                extra_entries_provider=_extra_entries,
                on_scene_selected=scene_select,
            )
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

        def _open_notifications_panel() -> None:
            system_feature = getattr(host, "_system_feature", None)
            if system_feature is not None:
                system_feature.show_notifications_panel()

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
                _open_notifications_panel,
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
