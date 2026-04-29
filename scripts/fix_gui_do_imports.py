#!/usr/bin/env python3
"""Rewrite relative imports after gui_do directory restructuring.

Run from the repository root (where gui_do/ lives):
    python scripts/fix_gui_do_imports.py

The script:
  1. Walks all .py files under gui_do/
  2. For each file, uses its known old package location to resolve old relative imports
  3. Translates each import to the new module path
  4. Rewrites the file in-place
"""
from __future__ import annotations

import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Module remap: old subpackage path → new subpackage path
# Both are dot-separated paths relative to the gui_do root.
# ---------------------------------------------------------------------------
MODULE_REMAP: dict[str, str] = {
    # app/ (from loop/ and core/)
    "loop.ui_engine":                                   "app.ui_engine",
    "core.scene":                                       "app.scene",
    "core.renderer":                                    "app.renderer",
    "core.error_handling":                              "app.error_handling",
    "core.first_frame_profiler":                        "app.first_frame_profiler",

    # controls/base/ (from controls/ and core/)
    "core.ui_node":                                     "controls.base.ui_node",
    "controls._axis_drag_control_base":                 "controls.base._axis_drag_control_base",
    "controls._focus_activatable_control_base":         "controls.base._focus_activatable_control_base",
    "controls._hover_press_control_base":               "controls.base._hover_press_control_base",
    "controls._text_button_control_base":               "controls.base._text_button_control_base",
    "controls._text_edit_focus_base":                   "controls.base._text_edit_focus_base",
    "controls._thumb_drag_lock":                        "controls.base._thumb_drag_lock",
    "controls._virtualized_scroll_list_base":           "controls.base._virtualized_scroll_list_base",

    # controls/display/
    "controls.label_control":                           "controls.display.label_control",
    "controls.rich_label_control":                      "controls.display.rich_label_control",
    "controls.image_control":                           "controls.display.image_control",
    "controls.frame_control":                           "controls.display.frame_control",
    "controls.arrow_box_control":                       "controls.display.arrow_box_control",

    # controls/input/
    "controls.button_control":                          "controls.input.button_control",
    "controls.toggle_control":                          "controls.input.toggle_control",
    "controls.button_group_control":                    "controls.input.button_group_control",
    "controls.text_input_control":                      "controls.input.text_input_control",
    "controls.text_area_control":                       "controls.input.text_area_control",
    "controls.color_picker_control":                    "controls.input.color_picker_control",
    "controls.spinner_control":                         "controls.input.spinner_control",
    "controls.range_slider_control":                    "controls.input.range_slider_control",
    "controls.slider_control":                          "controls.input.slider_control",
    "controls.scrollbar_control":                       "controls.input.scrollbar_control",
    "controls.dropdown_control":                        "controls.input.dropdown_control",

    # controls/data/
    "controls.list_view_control":                       "controls.data.list_view_control",
    "controls.data_grid_control":                       "controls.data.data_grid_control",
    "controls.tree_control":                            "controls.data.tree_control",
    "controls.tab_control":                             "controls.data.tab_control",

    # controls/canvas/
    "controls.canvas_control":                          "controls.canvas.canvas_control",
    "core.canvas_viewport":                             "controls.canvas.canvas_viewport",

    # controls/composite/
    "controls.panel_control":                           "controls.composite.panel_control",
    "controls.scroll_view_control":                     "controls.composite.scroll_view_control",
    "controls.splitter_control":                        "controls.composite.splitter_control",
    "controls.overlay_panel_control":                   "controls.composite.overlay_panel_control",
    "controls.dock_workspace_panel":                    "controls.composite.dock_workspace_panel",
    "core.error_boundary":                              "controls.composite.error_boundary",

    # controls/chrome/
    "controls.window_control":                          "controls.chrome.window_control",
    "controls.task_panel_control":                      "controls.chrome.task_panel_control",
    "controls.menu_bar_control":                        "controls.chrome.menu_bar_control",
    "controls.notification_panel_control":              "controls.chrome.notification_panel_control",
    "controls.property_inspector_panel":                "controls.chrome.property_inspector_panel",

    # events/
    "core.gui_event":                                   "events.gui_event",
    "core.event_manager":                               "events.event_manager",
    "core.event_bus":                                   "events.event_bus",
    "core.event_recorder":                              "events.event_recorder",
    "core.gesture_recognizer":                          "events.gesture_recognizer",
    "core.input_state":                                 "events.input_state",
    "core.pointer_capture":                             "events.pointer_capture",
    "core.keyboard_manager":                            "events.keyboard_manager",
    "core.value_change_callback":                       "events.value_change_callback",
    "core.value_change_reason":                         "events.value_change_reason",

    # actions/
    "core.action_manager":                              "actions.action_manager",
    "core.action_registry":                             "actions.action_registry",
    "core.key_chord_manager":                           "actions.key_chord_manager",
    "core.input_map":                                   "actions.input_map",

    # focus/
    "core.focus_manager":                               "focus.focus_manager",
    "core.focus_scope":                                 "focus.focus_scope",
    "core.focus_hint_constants":                        "focus.focus_hint_constants",
    "core.focus_visualizer":                            "focus.focus_visualizer",

    # data/
    "core.presentation_model":                          "data.presentation_model",
    "core.observable_collections":                      "data.observable_collections",
    "core.collection_view":                             "data.collection_view",
    "core.binding":                                     "data.binding",
    "core.selection_model":                             "data.selection_model",
    "core.virtual_item_source":                         "data.virtual_item_source",
    "core.sort_filter_proxy":                           "data.sort_filter_proxy",
    "core.async_data_provider":                         "data.async_data_provider",
    "core.invalidation":                                "data.invalidation",

    # forms/
    "core.form_model":                                  "forms.form_model",
    "core.form_schema":                                 "forms.form_schema",
    "core.document_model":                              "forms.document_model",

    # state/
    "core.command_history":                             "state.command_history",
    "core.state_machine":                               "state.state_machine",
    "core.router":                                      "state.router",

    # scheduling/
    "core.task_scheduler":                              "scheduling.task_scheduler",
    "core.timers":                                      "scheduling.timers",
    "core.tween_manager":                               "scheduling.tween_manager",
    "core.animation_sequence":                          "scheduling.animation_sequence",
    "core.transition_manager":                          "scheduling.transition_manager",
    "core.rate_limiter":                                "scheduling.rate_limiter",

    # overlays/
    "core.overlay_manager":                             "overlays.overlay_manager",
    "core.toast_manager":                               "overlays.toast_manager",
    "core.dialog_manager":                              "overlays.dialog_manager",
    "core.context_menu_manager":                        "overlays.context_menu_manager",
    "core.tooltip_manager":                             "overlays.tooltip_manager",
    "core.command_palette_manager":                     "overlays.command_palette_manager",
    "core.file_dialog_manager":                         "overlays.file_dialog_manager",
    "core.drag_drop_manager":                           "overlays.drag_drop_manager",
    "core.transfer_data":                               "overlays.transfer_data",
    "core.clipboard":                                   "overlays.clipboard",
    "core.notification_center":                         "overlays.notification_center",
    "core.menu_bar_manager":                            "overlays.menu_bar_manager",
    "core.menu_overlay_panel_base":                     "overlays.menu_overlay_panel_base",
    "core.resize_manager":                              "overlays.resize_manager",
    "core.cursor_manager":                              "overlays.cursor_manager",

    # persistence/
    "core.settings_registry":                           "persistence.settings_registry",
    "core.workspace_persistence":                       "persistence.workspace_persistence",
    "core.scene_snapshot":                              "persistence.scene_snapshot",
    "core.scene_transition_manager":                    "persistence.scene_transition_manager",

    # text/
    "core.text_flow":                                   "text.text_flow",
    "core.text_formatter":                              "text.text_formatter",
    "core.localization":                                "text.localization",

    # introspection/
    "core.property_registry":                           "introspection.property_registry",
    "core.property_inspector":                          "introspection.property_inspector",
    "core.spatial_index":                               "introspection.spatial_index",

    # features/
    "core.feature_lifecycle":                           "features.feature_lifecycle",

    # theme/ (fonts join theme)
    "core.font_manager":                                "theme.font_manager",
    "core.font_role_registry":                          "theme.font_role_registry",

    # telemetry/
    "core.telemetry":                                   "telemetry.telemetry",
    "core.telemetry_analyzer":                          "telemetry.telemetry_analyzer",
}

# Inverse: new subpackage path → old subpackage path (for moved files only)
NEW_TO_OLD: dict[str, str] = {v: k for k, v in MODULE_REMAP.items()}


# ---------------------------------------------------------------------------
# Import resolution helpers
# ---------------------------------------------------------------------------

def resolve_relative(pkg: str, dots: int, module: str) -> str:
    """Resolve a relative import to an absolute subpackage path.

    pkg:    dot-separated package path of the importing file
            (e.g. "controls.base" for a regular file, or "graphics" for
             graphics/__init__.py — the package the init file *defines*)
    dots:   number of leading dots in the import statement
    module: module path after the dots (may be empty string)

    Returns absolute subpackage path relative to gui_do root.
    """
    parts = pkg.split(".") if pkg else []
    up = dots - 1  # 1 dot = stay in same pkg, 2 dots = parent, ...
    if up > 0:
        parts = parts[:-up] if up < len(parts) else []
    if module:
        parts = parts + module.split(".")
    return ".".join(parts)


def make_relative(from_pkg: str, to_abs: str) -> str:
    """Compute the new relative import string.

    from_pkg: package of the importing file (new location)
    to_abs:   absolute module path of the imported module (new location)
    """
    from_parts = from_pkg.split(".") if from_pkg else []
    to_parts = to_abs.split(".")
    common = 0
    for a, b in zip(from_parts, to_parts):
        if a == b:
            common += 1
        else:
            break
    up = len(from_parts) - common
    dots = "." * (up + 1)
    down = ".".join(to_parts[common:])
    return dots + down if down else dots


def get_module_info(py_file: Path, root: Path) -> tuple[str, str, str, str]:
    """Return (new_pkg, new_resolve_pkg, old_pkg, old_resolve_pkg) for a .py file.

    *_pkg:          the module's own subpackage path (dot-separated, no extension)
    *_resolve_pkg:  the package used for resolving relative imports:
                    - for __init__.py: same as *_pkg (the file IS the package)
                    - for regular files: the parent package
    """
    rel = py_file.relative_to(root)
    is_init = rel.name == "__init__.py"

    if is_init:
        dir_parts = list(rel.parent.parts)
        # Guard: root __init__.py has parent "."
        dir_parts = [p for p in dir_parts if p != "."]
        new_pkg = ".".join(dir_parts)            # e.g. "graphics" or ""
        new_resolve_pkg = new_pkg               # init resolves relative to itself
    else:
        dir_parts = list(rel.parent.parts)
        dir_parts = [p for p in dir_parts if p != "."]
        module_parts = dir_parts + [rel.stem]
        new_pkg = ".".join(module_parts)         # e.g. "controls.composite.panel_control"
        new_resolve_pkg = ".".join(dir_parts)    # e.g. "controls.composite"

    # Determine old location
    old_pkg = NEW_TO_OLD.get(new_pkg, new_pkg)

    if is_init:
        old_resolve_pkg = old_pkg
    else:
        old_parts = old_pkg.split(".") if old_pkg else []
        old_resolve_pkg = ".".join(old_parts[:-1])  # parent package

    return new_pkg, new_resolve_pkg, old_pkg, old_resolve_pkg


# ---------------------------------------------------------------------------
# Import rewriting
# ---------------------------------------------------------------------------

# Matches: from <dots><module_path> import
# group 1: "from "
# group 2: leading dots  e.g. ".."
# group 3: module path after dots (may be empty)  e.g. "core.event_manager"
# group 4: " import" (rest of line handled by Python)
_IMPORT_RE = re.compile(
    r"^(from\s+)(\.+)([\w.]*?)(\s+import\b)",
    re.MULTILINE,
)


def fix_imports_in(content: str, old_resolve_pkg: str, new_resolve_pkg: str) -> str:
    """Rewrite all relative imports in *content*.

    old_resolve_pkg: the package path used to resolve the original relative imports
    new_resolve_pkg: the package path used to build the new relative imports
    """
    def replacer(m: re.Match) -> str:
        from_kw   = m.group(1)
        dots_str  = m.group(2)
        module_str = m.group(3)
        import_kw = m.group(4)

        dots = len(dots_str)

        # Resolve using the OLD package
        old_abs = resolve_relative(old_resolve_pkg, dots, module_str)

        # Translate to new location
        new_abs = MODULE_REMAP.get(old_abs, old_abs)

        # Build new relative from the NEW package
        new_rel = make_relative(new_resolve_pkg, new_abs)

        return from_kw + new_rel + import_kw

    return _IMPORT_RE.sub(replacer, content)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    root = Path("gui_do")
    if not root.is_dir():
        raise SystemExit("Run this script from the repository root (where gui_do/ lives).")

    changed = 0
    unchanged = 0

    for py_file in sorted(root.rglob("*.py")):
        new_pkg, new_resolve_pkg, old_pkg, old_resolve_pkg = get_module_info(py_file, root)

        content = py_file.read_text(encoding="utf-8")
        if not re.search(r"^from\s+\.", content, re.MULTILINE):
            unchanged += 1
            continue

        new_content = fix_imports_in(content, old_resolve_pkg, new_resolve_pkg)

        if new_content != content:
            py_file.write_text(new_content, encoding="utf-8")
            print(f"  updated: {py_file}")
            changed += 1
        else:
            unchanged += 1

    print(f"\nDone: {changed} files updated, {unchanged} unchanged.")


if __name__ == "__main__":
    main()
