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
    ShortcutHelpOverlay,
    resolve_scene_selection_callback,
    SplitterControl,
    StateMachine,
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
            "ensure_scene_task_panel",
            "TASK_PANEL_CONTROL_FONT_ROLE",
            "SCREEN_TITLE_FONT_ROLE",
            "go_to_main",
            "go_to_control_showcase",
            "set_life_window_visible",
            "set_mandel_window_visible",
            "set_systems_window_visible",
            "action_registry",
        ),
        "bind_runtime": ("app", "action_registry"),
    }

    def __init__(self) -> None:
        super().__init__("main_demo", scene_name="main")
        self._help_overlay: ShortcutHelpOverlay | None = None

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

        scene_select = resolve_scene_selection_callback(host)

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
        host.task_panel = host.ensure_scene_task_panel(
            "main",
            control_id="task_panel",
            height=50,
            hidden_peek_pixels=6,
            animation_step_px=8,
            dock_bottom=True,
            auto_hide=True,
        )

        host.app.layout.set_linear_properties(
            anchor=(16, host.screen_rect.height - 40),
            item_width=124,
            item_height=30,
            spacing=10,
            horizontal=True,
        )

        def _on_systems_toggle(pushed: bool) -> None:
            host.set_systems_window_visible(bool(pushed), from_toggle=True)

        def _on_life_toggle(pushed: bool) -> None:
            host.set_life_window_visible(bool(pushed), from_toggle=True)

        def _on_mandel_toggle(pushed: bool) -> None:
            host.set_mandel_window_visible(bool(pushed), from_toggle=True)

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
        host.systems_toggle_window = host.task_panel.add(
            ToggleControl(
                "show_systems",
                host.app.layout.linear(1),
                "System",
                "System",
                pushed=False,
                on_toggle=_on_systems_toggle,
                style="angle",
                font_role=host.TASK_PANEL_CONTROL_FONT_ROLE,
            )
        )
        host.showcase_button = host.task_panel.add(
            ButtonControl(
                "showcase",
                host.app.layout.linear(2),
                "Showcase",
                host.go_to_control_showcase,
                style="angle",
                font_role=host.TASK_PANEL_CONTROL_FONT_ROLE,
            )
        )
        host.life_toggle_window = host.task_panel.add(
            ToggleControl(
                "show_life",
                host.app.layout.linear(3),
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
                host.app.layout.linear(4),
                "Mandelbrot",
                "Mandelbrot",
                pushed=False,
                on_toggle=_on_mandel_toggle,
                style="round",
                font_role=host.TASK_PANEL_CONTROL_FONT_ROLE,
            )
        )
        host.help_button = host.task_panel.add(
            ButtonControl(
                "show_help",
                host.app.layout.linear(5),
                "Help (F9)",
                lambda: self._help_overlay.toggle() if self._help_overlay is not None else None,
                style="angle",
                font_role=host.TASK_PANEL_CONTROL_FONT_ROLE,
            )
        )

        host._main_tooltip_manager = TooltipManager(default_delay_ms=500)
        host._main_tooltip_manager.register(host.exit_button, "Exit the application")
        host._main_tooltip_manager.register(host.systems_toggle_window, "Toggle the Systems demo window")
        host._main_tooltip_manager.register(host.showcase_button, "Open the control showcase scene")
        host._main_tooltip_manager.register(host.life_toggle_window, "Toggle the Life simulation window")
        host._main_tooltip_manager.register(host.mandel_toggle_window, "Toggle the Mandelbrot fractal window")
        host._main_tooltip_manager.register(host.help_button, "Show keyboard shortcut reference (F1)")

        host.app.tile_windows()

    def bind_runtime(self, host) -> None:
        """Create the ShortcutHelpOverlay and bind F9 to toggle it."""
        overlay_rect = Rect(
            max(0, host.app.surface.get_width() // 2 - 300),
            max(0, host.app.surface.get_height() // 2 - 220),
            600,
            440,
        )
        self._help_overlay = ShortcutHelpOverlay(
            host.app.overlay,
            action_registry=host.action_registry,
            overlay_rect=overlay_rect,
        )
        host.app.actions.register_action(
            "show_help",
            lambda _event: (self._help_overlay.toggle() or True),
        )
        host.app.actions.bind_key(__import__("pygame").K_F9, "show_help", scene="main")

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
