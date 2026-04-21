# Public API Specification (Compact)

## Scope

This document defines the supported public surface of the rebased `gui` package and the strict contracts expected by runtime components.

## Public Exports

The package exports the following symbols via `gui/__init__.py`:

- `GuiApplication`
- `UiEngine`
- `PanelControl`
- `LabelControl`
- `ButtonControl`
- `ArrowBoxControl`
- `ButtonGroupControl`
- `CanvasControl`
- `CanvasEventPacket`
- `FrameControl`
- `ImageControl`
- `SliderControl`
- `ScrollbarControl`
- `TaskPanelControl`
- `ToggleControl`
- `WindowControl`
- `LayoutAxis`
- `LayoutManager`
- `WindowTilingManager`
- `ActionManager`
- `EventManager`
- `EventBus`
- `FocusManager`
- `EventPhase`
- `EventType`
- `GuiEvent`
- `InvalidationTracker`
- `ObservableValue`
- `PresentationModel`
- `TaskEvent`
- `TaskScheduler`
- `Timers`
- `BuiltInGraphicsFactory`
- `ColorTheme`

This `gui.__all__` export set is treated as an exact, locked public surface and is regression-tested.

## Event Contract

All event dispatch paths use canonical `GuiEvent` objects.

Required event consumption patterns:

- Semantic checks:
  - `event.is_key_down(...)`
  - `event.is_mouse_down(...)`
  - `event.is_mouse_up(...)`
  - `event.is_mouse_motion()`
  - `event.is_mouse_wheel()`
- Routed controls:
  - `event.with_phase(...)`
  - `event.stop_propagation()`
  - `event.prevent_default()`
- Position and motion data:
  - `event.pos`
  - `event.rel`
  - `event.raw_pos`
  - `event.raw_rel`
  - `event.wheel_delta`

Raw `pygame` events are normalized only at ingress through `EventManager` and `GuiApplication.process_event`.

## Node Contract

All nodes derive from `UiNode` and follow these role hooks:

- `is_window() -> bool`
- `is_task_panel() -> bool`
- `set_active(value: bool) -> None`
- `_clear_active_windows() -> None`

Container traversal relies on explicit `children` (no duck-typed discovery).

## Theme/Rendering Contract

Control drawing requires a canonical `ColorTheme` with a bound `graphics_factory`.

No fallback render paths are part of the public contract.

## Compatibility Policy

The rebased package is strict by design:

- No compatibility shims.
- No duck-typed fallback pathways in core dispatch and control rendering.
- No optional graphics-factory rendering behavior.

New APIs must preserve these strict-contract principles.

## Demo-Specific Modules

Demo-only contracts are intentionally outside the `gui` package boundary.

- Mandelbrot demo event schema is defined in `demo_parts/mandel_events.py`.
- No Mandelbrot/demo symbols (`MandelStatusEvent`, `MANDEL_*`) are exported from `gui.__all__`.

Boundary rules and enforcement details are specified in `docs/architecture_boundary_spec.md`.

Enforced contract tests:

- `tests/test_boundary_contracts.py`
- `tests/test_public_api_exports.py`
- `tests/test_mandel_event_schema_exports.py`
- `tests/test_public_api_docs_contracts.py`
- `tests/test_architecture_boundary_docs_contracts.py`
- `tests/test_contract_command_parity.py`
- `tests/test_readme_docs_contracts.py`
- `tests/test_contract_docs_helpers.py`
- `tests/test_contract_catalog_consistency.py`
