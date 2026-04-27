# Public API Specification (Compact)

## Scope

This document defines the supported public surface of the `gui_do` package and the strict contracts expected by runtime components.

Terminology in this document aligns with README and architecture docs:

- `strict contracts`: no compatibility/fallback behavior in core dispatch and rendering paths.
- `scene isolation`: only the active scene executes scene-contained runtime updates.
- `demo boundary`: demo-only schemas stay outside `gui_do.__all__`.

## Public Exports

The package exports the following symbols via `gui_do/__init__.py`:

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
- `FontManager`
- `EventPhase`
- `EventType`
- `GuiEvent`
- `ValueChangeCallback`
- `ValueChangeReason`
- `InvalidationTracker`
- `ObservableValue`
- `PresentationModel`
- `ComputedValue`
- `TaskEvent`
- `TaskScheduler`
- `Timers`
- `TelemetryCollector`
- `TelemetrySample`
- `configure_telemetry`
- `telemetry_collector`
- `analyze_telemetry_records`
- `analyze_telemetry_log_file`
- `load_telemetry_log_file`
- `render_telemetry_report`
- `BuiltInGraphicsFactory`
- `ColorTheme`
- `Feature`
- `DirectFeature`
- `LogicFeature`
- `RoutedFeature`
- `FeatureMessage`
- `FeatureManager`
- `TweenManager`
- `TweenHandle`
- `Easing`
- `TextInputControl`
- `ConstraintLayout`
- `AnchorConstraint`
- `OverlayManager`
- `OverlayHandle`
- `OverlayPanelControl`
- `ListViewControl`
- `ListItem`
- `DropdownControl`
- `DropdownOption`
- `ToastManager`
- `ToastHandle`
- `ToastSeverity`
- `DialogManager`
- `DialogHandle`
- `DragDropManager`
- `DragPayload`
- `FormModel`
- `FormField`
- `ValidationRule`
- `FieldError`
- `CommandHistory`
- `Command`
- `CommandTransaction`
- `DataGridControl`
- `GridColumn`
- `GridRow`
- `ContextMenuManager`
- `ContextMenuItem`
- `ContextMenuHandle`
- `SplitterControl`
- `StateMachine`
- `SettingsRegistry`
- `SettingDescriptor`
- `Router`
- `RouteEntry`
- `ThemeManager`
- `DesignTokens`
- `TextAreaControl`
- `RichLabelControl`
- `TabControl`
- `TabItem`
- `ResizeManager`
- `MenuBarControl`
- `MenuEntry`
- `MenuBarManager`
- `TreeControl`
- `TreeNode`
- `FileDialogManager`
- `FileDialogOptions`
- `FileDialogHandle`
- `FlexLayout`
- `FlexItem`
- `FlexDirection`
- `FlexAlign`
- `FlexJustify`
- `SceneTransitionManager`
- `SceneTransitionStyle`
- `NotificationCenter`
- `NotificationRecord`
- `NotificationPanelControl`
- `ClipboardManager`
- `AnimationSequence`
- `AnimationHandle`
- `ScrollViewControl`
- `SpinnerControl`
- `RangeSliderControl`
- `ColorPickerControl`
- `CommandPaletteManager`
- `CommandEntry`
- `CommandPaletteHandle`

This `gui_do.__all__` export set is treated as an exact, locked public surface and is regression-tested.

## Event Contract

All event dispatch paths use canonical `GuiEvent` objects.

Ingress normalization contract:

- Raw `pygame` events are normalized at framework ingress only.
- Runtime routing, controls, and helpers consume canonical `GuiEvent` instances.
- Pointer paths preserve both logical and raw coordinates via `pos/rel` and `raw_pos/raw_rel`.

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

Focused button activation requirement:

- When Enter/Space activates a focused `ButtonControl`, activation occurs once from the focus-key event path.
- The button enters an armed visual state for `FOCUS_TRAVERSAL_HINT_TIMEOUT_SECONDS`, then returns to idle automatically.
- This armed transition is cosmetic-only and must not trigger a second activation callback.

Raw `pygame` events are normalized only at ingress through `EventManager` and `GuiApplication.process_event`.

See `docs/event_system_spec.md` for the detailed event object shape and dispatch flow.

## Node Contract

All nodes derive from `UiNode` and follow these role hooks:

- `is_window() -> bool`
- `is_task_panel() -> bool`
- `set_active(value: bool) -> None`
- `_clear_active_windows() -> None`

Container traversal relies on explicit `children` (no duck-typed discovery).

## Theme/Rendering Contract

Control drawing requires a canonical `ColorTheme` with a bound `graphics_factory` and a role-based `FontManager` (`theme.fonts`).

Font roles are explicit contracts at runtime; controls render against configured role names instead of runtime global font switching behavior.

No fallback render paths are part of the public contract.

## Contract Policy

The package is strict by design:

- No fallback layers.
- No duck-typed fallback pathways in core dispatch and control rendering.
- No optional graphics-factory rendering behavior.

In addition, runtime behavior is intentionally deterministic under load (for example scheduler fairness guards are configured in app runtime setup rather than implicit best-effort behavior).

New APIs must preserve these strict-contract principles.

## Demo-Specific Modules

Demo-only contracts are intentionally outside the `gui_do` package boundary.

- Mandelbrot demo event schema is defined in `demo_features/mandelbrot_demo_feature.py`.
- `demo_features.mandelbrot_demo_feature.__all__` export surface/order is treated as a locked contract for demo schema consumers.
- No Mandelbrot/demo symbols (`MandelStatusEvent`, `MANDEL_*`) are exported from `gui_do.__all__`.

Boundary rules and enforcement details are specified in `docs/architecture_boundary_spec.md`.

Enforced contract tests:

- `tests/test_boundary_contracts.py`
- `tests/test_public_api_exports.py`
- `tests/test_mandel_event_schema_exports.py`
- `tests/test_public_api_docs_contracts.py`
- `tests/test_architecture_boundary_docs_contracts.py`
- `tests/test_contract_command_parity.py`
- `tests/test_package_contracts_public_api.py`
- `tests/test_package_contracts_docs.py`
- `tests/test_contract_docs_helpers.py`
- `tests/test_core_only_bootstrap_contracts.py`
- `tests/test_contract_catalog_consistency.py`
