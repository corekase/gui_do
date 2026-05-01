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
            "scene_presentation",
            "go_to_main",
            "go_to_control_showcase",
            "window_presentation",
            "action_registry",
        ),
        "bind_runtime": ("app", "action_registry"),
    }

    def __init__(self) -> None:
        super().__init__("main_demo", scene_name="main")
        self._help_overlay: ShortcutHelpOverlay | None = None

    def build(self, host) -> None:
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
                on_window_toggled=host.window_presentation.handle_window_toggle,
            )
        )
        host.screen_title = host.root.add(
            self._make_sized_title_label(host, "screen_title", "gui_do", 24, 36, fallback_size=(640, 96))
        )
        host.task_panel = host.scene_presentation.ensure_scene_task_panel(
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

        host.exit_button = host.task_panel.add(
            ButtonControl(
                "exit",
                host.app.layout.linear(0),
                "Exit",
                lambda: setattr(host.app, "running", False),
                style="angle",
            )
        )
        host.showcase_button = host.task_panel.add(
            ButtonControl(
                "showcase",
                host.app.layout.linear(2),
                "Showcase",
                host.go_to_control_showcase,
                style="angle",
            )
        )

        toggle_controls = []
        bindings = list(host.window_presentation.bindings())
        next_slot_index = 1
        for idx, binding in enumerate(bindings):
            if idx == 1:
                next_slot_index = 3
            toggle = host.task_panel.add(
                ToggleControl(
                    binding.task_panel_button_id or f"show_{binding.key}",
                    host.app.layout.linear(next_slot_index),
                    binding.task_panel_label or binding.key.title(),
                    binding.task_panel_label or binding.key.title(),
                    pushed=False,
                    on_toggle=lambda pushed, _key=binding.key: host.window_presentation.set_visible(
                        _key,
                        bool(pushed),
                        from_toggle=True,
                    ),
                    style=binding.task_panel_style,
                )
            )
            if binding.toggle_attr:
                setattr(host, binding.toggle_attr, toggle)
            toggle_controls.append((binding, toggle))
            next_slot_index += 1

        host.help_button = host.task_panel.add(
            ButtonControl(
                "show_help",
                host.app.layout.linear(max(5, next_slot_index)),
                "Help (F9)",
                lambda: self._help_overlay.toggle() if self._help_overlay is not None else None,
                style="angle",
            )
        )

        host._main_tooltip_manager = TooltipManager(default_delay_ms=500)
        host._main_tooltip_manager.register(host.exit_button, "Exit the application")
        host._main_tooltip_manager.register(host.showcase_button, "Open the control showcase scene")
        for binding, toggle in toggle_controls:
            label = binding.task_panel_label or binding.action_label or binding.key.title()
            host._main_tooltip_manager.register(toggle, f"Toggle the {label} window")
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
        )
        # Use the per-scene FontManager, not the global FontRoleRegistry
        scene_runtime = host.app._scenes[host.app.active_scene_name]
        scene_font_manager = scene_runtime.theme.fonts
        if scene_font_manager.has_role(label.font_role):
            font = scene_font_manager.font_instance(label.font_role, size=label.font_size)
            label.rect.size = font.text_surface_size(label.text, shadow=True)
        return label
