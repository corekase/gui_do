# Public API Specification

## Scope

This document defines the supported public surface of the `gui_do` package and the strict contracts expected by runtime components.

The runtime behavior is intentionally deterministic under load.

## API Model

The `gui_do` root package is the supported consumer surface.
Exports are organized in tiers in `gui_do/__init__.py` from high-level bootstrap APIs down to advanced helpers.

### Tier 1: Primary Entry Points

Recommended for new applications:

- `bootstrap_host_application`
- `HostApplicationConfig`
- Data-driven specs such as `FeatureSpec`, `WindowSpec`, `RuntimeSceneSpec`, `ActionSpec`, `TabBuilderSpec`
- Feature lifecycle abstractions: `Feature`, `DirectFeature`, `LogicFeature`, `RoutedFeature`, `FeatureManager`

### Tier 2-7: Runtime Systems

Core runtime groups exposed at the root include:

- App/scene: `GuiApplication`, `create_display`, `SceneTransitionManager`
- Events/actions/input: `GuiEvent`, `EventType`, `EventPhase`, `EventManager`, `ActionManager`, `InputMap`
- Data/state: `ObservableValue`, `PresentationModel`, `CollectionView`, `Binding`
- Scheduling/animation: `TaskScheduler`, `Timers`, `TweenManager`, `TransitionManager`
- Theme/fonts/text: `ThemeManager`, `ColorTheme`, `FontManager`, `TextFlow`, `LocaleRegistry`
- Diagnostics:
  - `TelemetryCollector`
  - `TelemetrySample`
  - `configure_telemetry`
  - `telemetry_collector`

### Tier 8+

Additional root exports cover:

- Layout engines (constraint/flex/grid/dock/flow/snap/viewport)
- Overlay and modal managers (dialog, toast, tooltip, context menu, command palette); the command palette activation key is registered per-scene via `SceneCommandPaletteSpec`
- Forms, validation, state machines, routing, persistence
- Controls (core and extended)
- Graphics, rendering, introspection, and advanced runtime helper APIs

## Per-Scene Optional Facilities

`gui_do` provides three built-in facilities that any scene may optionally declare.  All three are per-scene, have no default items, and are enabled purely by what specs are declared.  The spec-driven approach is the expected and preferred pattern for user code.

If user specs do not declare a facility, that facility is not created at runtime and does not participate in layout, focus, input routing, or window movement constraints.

### Unified Window Visibility Management

All three facilities participate in a unified window visibility management system. When multiple facilities are present in a scene, they share synchronized state and consistently respect the `window_management_opt_in` opt-out flag on window specifications.

The three components are completely independent and optional:
- **Task Panel** (via `SceneTaskPanelSpec`): Optional window toggle button group
- **Scene Menu Strip** (via `MenuStripSpec`): Optional Windows submenu
- **Command Palette** (via `SceneCommandPaletteSpec`): Optional window entry list

When all three are present, they show the same set of windows. Setting `window_management_opt_in=False` on any window spec (WindowSpec, AnchoredWindowSpec, or FeatureWindowBundleBindingSpec) excludes that window from all three management systems. By default, windows are included (`window_management_opt_in=True`). This opt-out pattern ensures that whichever components are present in a scene will all show the same set of manageable windows.

Scenes can freely omit any combination of these facilities—the unified state automatically adapts to show only windows from the facilities that are actually present.

### Task Panel

Declare with `SceneTaskPanelSpec` passed to `ensure_scene_task_panel`.  No default items — every button must be added explicitly.  The optional **window toggle group** is declared with `TaskPanelWindowToggleGroupSpec(start_index=N)`, passed to `add_task_panel_window_toggle_group`, which automatically creates one toggle button per registered window with `window_management_opt_in=True`.  Other controls may coexist before, after, or within the group's slot range.

Key types: `SceneTaskPanelSpec`, `TaskPanelButtonSpec`, `TaskPanelFocusToggleSpec`, `TaskPanelWindowToggleGroupSpec`, `RightAnchoredTaskPanelButtonSpec`.
Key helpers: `ensure_scene_task_panel`, `add_task_panel_buttons`, `add_task_panel_window_toggle_group`, `add_window_toggle_task_panel_controls`, `register_window_toggle_tooltips`.

### Scene Menu Strip

Declare with `MenuStripSpec` and passed to `add_menu_strip_from_spec()`, `add_standard_menu_strip()`, or `add_window_menu_strip()`. No default menu entries. Two optional sections: `scenes_shown=True` (Scene navigation menu) and `windows_shown=True` (Windows visibility toggles menu). The Windows section automatically filters by `window_management_opt_in` when `host.window_presentation` is available, showing only opted-in windows. When both menu strip and task panel are present with `window_presentation` available, their window lists remain synchronized through the shared `window_presentation` model. When `window_presentation` is not available, all windows in the scene are shown.

Key types: `MenuStripSpec`, `MenuStripControl`, `WindowMenuOptions`, `SceneMenuOptions`.
Key helpers: `add_menu_strip_from_spec`, `add_standard_menu_strip`, `add_window_menu_strip`.

### Command Palette

Declare with `SceneCommandPaletteSpec(key=..., scene_name=...)` in `RoutedRuntimeSpec.command_palette`.  `setup_routed_runtime` registers the activation key as a **global key** — tested before focus dispatch, active-window handlers, and screen-event handlers.  This guarantees the palette is always reachable.  Each scene declares its own key; having a command palette is optional per-scene. The palette's window entries list respects `window_management_opt_in` on each window and shows only opted-in windows.

Built-in palette entry groups are configured via `PaletteBindingSpec` in `HostApplicationBindingSpec`:

- `include_scene_entries` — optional Scene auto-populate group
- `include_window_entries` — optional Window auto-populate group
- `custom_entries_provider` — user-defined callable returning `CommandEntry` values
- `group_order` — places Scene/Window groups before, after, or between custom entries

When `connect_window_presentation=True`, built-in Window entries are ordered by `task_panel_slot_index` (matching task panel toggle order), not by control id.

Key types: `SceneCommandPaletteSpec`, `PaletteBindingSpec`, `CommandEntry`.
Key helpers: `setup_scene_command_palette_key`, `setup_routed_runtime` (auto-wires when `command_palette` is set).
Key `ActionManager` methods: `bind_global_key`, `unbind_global_key`, `trigger_global_key_from_event`.

## Import Contract

- Supported consumer imports use explicit named imports from `gui_do`.
- Star-import behavior is not part of the public contract.

## Strict Contracts

- strict contracts: no compatibility/fallback behavior in core dispatch and rendering paths.
- Scene-scoped runtime work executes only for the active scene.
- `GuiEvent` is the canonical app dispatch event object.
- Workspace restore and scheduler budget behavior are governed by runtime operating contracts.

## Enforcement

Automated tests that enforce this spec include:

- `tests/test_public_api_exports.py`
- `tests/test_public_api_docs_contracts.py`
- `tests/test_runtime_operating_contracts.py`
- `tests/test_boundary_contracts.py`

Run command:

```bash
python -m pytest -q tests/test_public_api_exports.py tests/test_public_api_docs_contracts.py tests/test_runtime_operating_contracts.py tests/test_boundary_contracts.py
```
