"""Shared specs and top-level layout constants for the controls showcase feature."""

import pygame
from gui_do.features.data_driven_runtime import (
    RoutedRuntimeSpec,
    SceneCommandPaletteSpec,
    TaskPanelFocusToggleSpec,
)

_CONTROLS_RUNTIME_SPEC = RoutedRuntimeSpec(
    scene_name="control_showcase",
    task_panel_focus_toggles=(
        TaskPanelFocusToggleSpec(
            action_name="toggle_task_panel_focus_control_showcase",
            scene_name="control_showcase",
            key=pygame.K_F1,
        ),
    ),
    command_palette=SceneCommandPaletteSpec(
        key=pygame.K_F5,
        scene_name="control_showcase",
    ),
)
