"""Main scene feature extracted from the gui_do demo entrypoint."""

from __future__ import annotations

from pygame import Rect

from gui_do import (
    Feature,
    PanelControl,
    ShortcutHelpOverlay,
    TooltipManager,
)
from gui_do.features.data_driven_runtime import (
    AutoSizedStyledLabelSpec,
    SceneMenuStripSpec,
    RightAnchoredTaskPanelButtonSpec,
    SceneTaskPanelSpec,
    add_right_anchored_task_panel_button,
    TaskPanelButtonSpec,
    TooltipBindingSpec,
    add_task_panel_buttons,
    add_scene_menu_strip_from_spec,
    add_window_toggle_task_panel_controls,
    create_auto_sized_styled_label,
    ensure_scene_task_panel,
    setup_routed_runtime,
    register_tooltip_attr_specs,
    register_window_toggle_tooltips,
)

from .main_specs import MAIN_RUNTIME_SPEC as _MAIN_RUNTIME_SPEC


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
        "bind_runtime": ("app",),
    }

    def __init__(self) -> None:
        super().__init__("main_demo", scene_name="main")
        self._help_overlay: ShortcutHelpOverlay | None = None

    def build(self, host) -> None:
        host.root = host.app.add(
            PanelControl("main_root", Rect(0, 0, host.screen_rect.width, host.screen_rect.height), draw_background=False),
            scene_name="main",
        )

        host.desktop_menu_bar = add_scene_menu_strip_from_spec(
            host.root,
            host,
            SceneMenuStripSpec(
                control_id="desktop_menu_bar",
                rect=Rect(0, 0, host.screen_rect.width, 28),
                scene_name="main",
                scenes_shown=True,
                windows_shown=True,
                on_window_toggled=host.window_presentation.handle_window_toggle,
            ),
        )
        host.screen_title = host.root.add(
            create_auto_sized_styled_label(
                host,
                AutoSizedStyledLabelSpec(
                    control_id="screen_title",
                    text="gui_do",
                    left=24,
                    top=36,
                    fallback_size=(640, 96),
                    style_size=64,
                    shadow=True,
                ),
                scene_name="main",
            )
        )
        host.task_panel = ensure_scene_task_panel(
            host,
            SceneTaskPanelSpec(
                scene_name="main",
                control_id="task_panel",
                height=50,
                hidden_peek_pixels=6,
                animation_step_px=8,
                dock_bottom=True,
                auto_hide=True,
            ),
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
                    on_click=host.app.quit,
                    style="angle",
                ),
            ),
        )

        toggle_controls_before_showcase, max_slot_before_showcase = add_window_toggle_task_panel_controls(
            host,
            host.task_panel,
            host.app.layout,
            host.window_presentation,
            max_slot_index=1,
        )

        add_task_panel_buttons(
            host,
            host.task_panel,
            host.app.layout,
            (
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

        toggle_controls_after_showcase, max_slot_after_showcase = add_window_toggle_task_panel_controls(
            host,
            host.task_panel,
            host.app.layout,
            host.window_presentation,
            min_slot_index=3,
        )
        toggle_controls = toggle_controls_before_showcase + toggle_controls_after_showcase

        slot0_rect = host.app.layout.linear(0)
        host.help_button = add_right_anchored_task_panel_button(
            host,
            host.task_panel,
            RightAnchoredTaskPanelButtonSpec(
                attr_name="help_button",
                control_id="show_help",
                label="Help (F9)",
                on_click=self._toggle_help_overlay,
                width=int(slot0_rect.width),
                height=int(slot0_rect.height),
                top_offset=int(slot0_rect.top - host.task_panel.rect.top),
                right_padding=16,
                style="angle",
            ),
        )

        host._main_tooltip_manager = TooltipManager(default_delay_ms=500)
        register_tooltip_attr_specs(
            host,
            host._main_tooltip_manager,
            (
                TooltipBindingSpec("exit_button", "Exit the application"),
                TooltipBindingSpec("showcase_button", "Open the control showcase scene"),
                TooltipBindingSpec("help_button", "Show keyboard shortcut reference (F9)"),
            ),
        )
        register_window_toggle_tooltips(host._main_tooltip_manager, toggle_controls)

        host.app.tile_windows()

    def bind_runtime(self, host) -> None:
        """Wire runtime overlays and hotkeys from the declarative runtime spec."""
        setup_routed_runtime(self, host, _MAIN_RUNTIME_SPEC)

    def _toggle_help_overlay(self) -> None:
        overlay = self._help_overlay
        if overlay is None:
            return
        overlay.toggle()
