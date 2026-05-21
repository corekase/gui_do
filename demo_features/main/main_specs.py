"""Shared specs for the main scene demo feature package."""

from __future__ import annotations

import pygame

from gui_do.features.data_driven_runtime import (
    ActionHotkeySpec,
    AutoSizedStyledLabelSpec,
    MenuStripSpec,
    PaletteInputBindSpec,
    RoutedRuntimeSpec,
    SceneCommandPaletteSpec,
    SceneTaskPanelSpec,
    ShortcutOverlaySpec,
    TaskPanelButtonSpec,
    TaskPanelSceneNavButtonSpec,
    TaskPanelSlotLayoutSpec,
    TaskPanelWindowToggleGroupSpec,
    TaskPanelFocusToggleSpec,
    TooltipBindingSpec,
    WindowTitlebarControlsSpec,
)


def _toggle_automatic_layout_action(feature, host, _event) -> bool:
    _ = host
    return bool(feature.toggle_automatic_layout())


def _tile_windows_now_action(feature, host, _event) -> bool:
    _ = host
    return bool(feature.layout_windows_now())


MAIN_RUNTIME_SPEC = RoutedRuntimeSpec(
    scene_name="main",
    action_hotkeys=(
        ActionHotkeySpec(
            action_name="toggle_automatic_layout",
            handler=_toggle_automatic_layout_action,
            key=pygame.K_F2,
            scene_name="main",
            global_key=True,
        ),
        ActionHotkeySpec(
            action_name="tile_now",
            handler=_tile_windows_now_action,
            key=pygame.K_F3,
            scene_name="main",
            global_key=True,
        ),
    ),
    shortcut_overlays=(
        ShortcutOverlaySpec(
            attr_name="_help_overlay",
            action_registry_attr="action_registry",
            width=760,
            height=340,
            toggle_action_name="show_help",
            toggle_key=pygame.K_F9,
            toggle_scene_name="main",
            toggle_global_key=True,
            manual_shortcut_lines=(
                "F1: Raise/Lower Task Panel",
                "F5: Toggle Command Palette",
                "F9: Display this help",
                "F2: Toggle Automatic Layout",
                "F3: Tile all windows now",
                "Mouse Wheel Click: Toggle Window Entry In Palette",
                "Tab/Shift-Tab: cycle controls",
                "Control-Tab/Shift-Control-Tab: cycle windows",
                "Enter/Space: activate control",
                "Arrow Keys: control selected control",
            ),
            manual_section_title="Keyboard",
            prepend_manual_shortcuts=True,
            manual_shortcuts_only=True,
            exclude_section_titles=("General", "Files", "Scenes", "Windows"),
            exclude_entry_labels=(
                "Open Command Palette",
                "Exit",
                "Go to main scene",
                "Show System Window",
                "Show Life Window",
            ),
        ),
    ),
    task_panel_focus_toggles=(
        TaskPanelFocusToggleSpec(
            action_name="toggle_task_panel_focus",
            scene_name="main",
            key=pygame.K_F1,
        ),
    ),
    command_palette=SceneCommandPaletteSpec(
        scene_name="main",
        toggle=PaletteInputBindSpec(
            action_name="command_palette_toggle",
            key=pygame.K_F5,
        ),
        action=PaletteInputBindSpec(
            action_name="command_palette_action",
            pointer_button=2,
        ),
    ),
)

MAIN_MENU_BAR_HEIGHT = 28


def build_main_menu_strip_spec(screen_width: int, on_window_toggled) -> MenuStripSpec:
    _ = screen_width
    return MenuStripSpec(
        control_id="desktop_menu_bar",
        scene_name="main",
        scenes_shown=True,
        windows_shown=True,
        scene_menu_label="Scene",
        window_menu_label="Window",
        scene_menu_insert_index=0,
        window_menu_insert_index=1,
        scene_menu_mode="add_all",
        scene_menu_include_current_scene=False,
        on_window_toggled=on_window_toggled,
    )


MAIN_TITLE_SPEC = AutoSizedStyledLabelSpec(
    control_id="screen_title",
    text="gui_do",
    left=24,
    top=36,
    fallback_size=(640, 96),
    style_size=64,
)

MAIN_TASK_PANEL_SPEC = SceneTaskPanelSpec(
    scene_name="main",
    control_id="task_panel",
    height=50,
    hidden_peek_pixels=6,
    animation_step_px=8,
    dock_bottom=True,
    auto_hide=True,
)

MAIN_TASK_PANEL_LAYOUT_SPEC = TaskPanelSlotLayoutSpec(
    left=16,
    top_offset=10,
    item_width=124,
    item_height=30,
    spacing=10,
    horizontal=True,
)

def build_main_task_panel_button_specs(host):
    return (
        TaskPanelButtonSpec(
            attr_name="exit_button",
            control_id="exit",
            label="Exit",
            on_click=host.app.quit,
            style="angle",
        ),
    )

MAIN_TASK_PANEL_SCENE_NAV_SPECS = (
    TaskPanelSceneNavButtonSpec(
        attr_name="showcase_button",
        control_id="showcase",
        label="Showcase",
        target_scene="control_showcase",
        accessibility_label="Open control showcase scene",
        tab_index=-1,
    ),
)

MAIN_TASK_PANEL_WINDOW_TOGGLE_GROUP_SPEC = TaskPanelWindowToggleGroupSpec(start_index=1)

MAIN_OPT_OUT_TEST_WINDOW_TITLEBAR_CONTROLS = WindowTitlebarControlsSpec(
    include_window_hide_image_button=False,
)

MAIN_TOOLTIP_BINDINGS = (
    TooltipBindingSpec("exit_button", "Exit the application"),
    TooltipBindingSpec("showcase_button", "Open the control showcase scene"),
    TooltipBindingSpec("help_button", "Show keyboard shortcut reference (F9)"),
)

__all__ = [
    "MAIN_MENU_BAR_HEIGHT",
    "MAIN_RUNTIME_SPEC",
    "MAIN_TASK_PANEL_LAYOUT_SPEC",
    "MAIN_TASK_PANEL_SCENE_NAV_SPECS",
    "MAIN_TASK_PANEL_SPEC",
    "MAIN_TASK_PANEL_WINDOW_TOGGLE_GROUP_SPEC",
    "MAIN_OPT_OUT_TEST_WINDOW_TITLEBAR_CONTROLS",
    "MAIN_TITLE_SPEC",
    "MAIN_TOOLTIP_BINDINGS",
    "build_main_menu_strip_spec",
    "build_main_task_panel_button_specs",
]
