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

# ---------------------------------------------------------------------------
# Category visibility helpers (inlined from control_showcase_category_visibility)
# ---------------------------------------------------------------------------

BASICS_SUPPRESSED_LABEL_NAMES: frozenset[str] = frozenset({
    "button_2", "button_3",
    "toggle_2", "toggle_3",
    "button_group_a2", "button_group_a3",
    "button_group_b2", "button_group_b3",
    "button_group_c2", "button_group_c3",
})

CONTROLS_RUNTIME_SPEC = _CONTROLS_RUNTIME_SPEC

__all__ = ["BASICS_SUPPRESSED_LABEL_NAMES", "CONTROLS_RUNTIME_SPEC"]
