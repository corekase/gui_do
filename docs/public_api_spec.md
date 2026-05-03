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
- Overlay and modal managers (dialog, toast, tooltip, context menu, command palette)
- Forms, validation, state machines, routing, persistence
- Controls (core and extended)
- Graphics, rendering, introspection, and advanced runtime helper APIs

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
