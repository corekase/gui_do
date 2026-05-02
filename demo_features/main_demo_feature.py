"""Main scene feature extracted from the gui_do demo entrypoint."""

from __future__ import annotations

try:
    from demo_features._import_bootstrap import ensure_repo_root_on_path
except ModuleNotFoundError:
    from _import_bootstrap import ensure_repo_root_on_path

ensure_repo_root_on_path()

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
from gui_do.features.data_driven_runtime import (
    TaskPanelButtonSpec,
    add_task_panel_button,
    add_task_panel_buttons,
    add_standard_scene_menu_strip,
    add_window_toggle_task_panel_controls,
    register_tooltip_specs,
    register_window_toggle_tooltips,
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

        host.desktop_menu_bar = add_standard_scene_menu_strip(
            host.root,
            host,
            control_id="desktop_menu_bar",
            rect=Rect(0, 0, host.screen_rect.width, 28),
            scene_name="main",
            scenes_shown=True,
            windows_shown=True,
            on_window_toggled=host.window_presentation.handle_window_toggle,
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

        add_task_panel_buttons(
            host,
            host.task_panel,
            host.app.layout,
            (
                TaskPanelButtonSpec(
                    attr_name="exit_button",
                    control_id="exit",
                    slot_index=0,
                    label="Exit",
                    on_click=lambda: setattr(host.app, "running", False),
                    style="angle",
                ),
                TaskPanelButtonSpec(
                    attr_name="showcase_button",
                    control_id="showcase",
                    slot_index=2,
                    label="Showcase",
                    on_click=host.go_to_control_showcase,
                    style="angle",
                ),
            ),
        )

        toggle_controls, max_slot_index = add_window_toggle_task_panel_controls(
            host,
            host.task_panel,
            host.app.layout,
            host.window_presentation,
        )

        host.help_button = add_task_panel_button(
            host.task_panel,
            host.app.layout,
            control_id="show_help",
            slot_index=max(5, max_slot_index + 1),
            label="Help (F9)",
            on_click=lambda: self._help_overlay.toggle() if self._help_overlay is not None else None,
            style="angle",
        )

        host._main_tooltip_manager = TooltipManager(default_delay_ms=500)
        register_tooltip_specs(
            host._main_tooltip_manager,
            (
                (host.exit_button, "Exit the application"),
                (host.showcase_button, "Open the control showcase scene"),
            ),
        )
        register_window_toggle_tooltips(host._main_tooltip_manager, toggle_controls)
        register_tooltip_specs(
            host._main_tooltip_manager,
            ((host.help_button, "Show keyboard shortcut reference (F1)"),),
        )

        host.app.tile_windows()

    def bind_runtime(self, host) -> None:
        """Create runtime overlays and bind explicit scene-owned hotkeys."""
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

        def _toggle_task_panel_focus(_event):
            overlay = getattr(host.app, "overlay", None)
            has_overlay = getattr(overlay, "has_overlay", None)
            if callable(has_overlay) and has_overlay("__command_palette__"):
                return True
            task_panel_focus = getattr(host.app, "task_panel_focus", None)
            return bool(task_panel_focus is not None and task_panel_focus.toggle(host.app.scene, host.app))

        host.app.actions.register_action("toggle_task_panel_focus", _toggle_task_panel_focus)
        host.app.actions.bind_key(__import__("pygame").K_F1, "toggle_task_panel_focus", scene="main")

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
