"""Compatibility re-export shim: all abstractions now live in gui_do.features.data_driven_runtime."""

from __future__ import annotations

try:
    from demo_features._import_bootstrap import ensure_repo_root_on_path
except ModuleNotFoundError:
    from _import_bootstrap import ensure_repo_root_on_path

ensure_repo_root_on_path()

from gui_do.features.data_driven_runtime import (
    build_tools_menu_entries,
    add_standard_scene_menu_strip,
    apply_accessibility_sequence,
    register_companion_logic_features,
    ensure_scene_scheduler,
    sorted_window_bindings,
    collect_window_toggle_controls,
    apply_window_toggle_accessibility,
    add_window_toggle_task_panel_controls,
    register_window_toggle_tooltips,
    initialize_locale_registry,
    bind_input_map_actions,
    register_descriptors,
    resolve_canvas_local_point,
    apply_runtime_scene_pristine_assets,
    bind_runtime_scene_exit_keys,
    prewarm_runtime_scenes,
    add_task_panel_button,
    register_tooltip_specs,
    instantiate_features_from_specs,
    register_features_from_specs,
    register_window_presentation_specs,
    register_window_tab_builders,
    create_presented_anchored_window,
    FeatureSpec,
    WindowSpec,
    RuntimeSceneSpec,
    ActionSpec,
    StaticAccessibilitySpec,
    CursorSpec,
    SceneRootSpec,
    TelemetryConfig,
    HostApplicationConfig,
    bootstrap_host_application,
)
