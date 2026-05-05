"""Shared specs for the main scene demo feature package."""

from __future__ import annotations

import pygame

from gui_do.features.data_driven_runtime import (
    RoutedRuntimeSpec,
    SceneCommandPaletteSpec,
    ShortcutOverlaySpec,
    TaskPanelFocusToggleSpec,
)

MAIN_RUNTIME_SPEC = RoutedRuntimeSpec(
    scene_name="main",
    shortcut_overlays=(
        ShortcutOverlaySpec(
            attr_name="_help_overlay",
            action_registry_attr="action_registry",
            width=760,
            height=340,
            toggle_action_name="show_help",
            toggle_key=pygame.K_F9,
            toggle_scene_name="main",
            manual_shortcut_lines=(
                "F1: Raise/Lower Task Panel",
                "F5: Toggle Command Palette",
                "F9: Display this help",
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
        key=pygame.K_F5,
        scene_name="main",
    ),
)

__all__ = ["MAIN_RUNTIME_SPEC"]
