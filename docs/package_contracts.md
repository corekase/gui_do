# Package Contracts

This file contains machine-validated package contract content used by parity
and docs contract tests. It is intentionally separate from README so project
merges do not require preserving README sections for test/tooling behavior.

## Public API

```python
from gui_do import (
    GuiApplication,
    UiEngine,
    PanelControl,
    LabelControl,
    ButtonControl,
    ArrowBoxControl,
    ButtonGroupControl,
    CanvasControl,
    CanvasEventPacket,
    FrameControl,
    ImageControl,
    SliderControl,
    ScrollbarControl,
    TaskPanelControl,
    ToggleControl,
    WindowControl,
    LayoutAxis,
    LayoutManager,
    WindowTilingManager,
    ActionManager,
    EventManager,
    EventBus,
    FocusManager,
    FontManager,
    EventPhase,
    EventType,
    GuiEvent,
    ValueChangeCallback,
    ValueChangeReason,
    InvalidationTracker,
    ObservableValue,
    PresentationModel,
    TaskEvent,
    TaskScheduler,
    Timers,
    TelemetryCollector,
    TelemetrySample,
    configure_telemetry,
    telemetry_collector,
    analyze_telemetry_records,
    analyze_telemetry_log_file,
    load_telemetry_log_file,
    render_telemetry_report,
    BuiltInGraphicsFactory,
    ColorTheme,
    Feature,
    DirectFeature,
    LogicFeature,
    RoutedFeature,
    FeatureMessage,
    FeatureManager,
    TweenManager,
    TweenHandle,
    Easing,
    TextInputControl,
    ConstraintLayout,
    AnchorConstraint,
    OverlayManager,
    OverlayHandle,
    OverlayPanelControl,
    ListViewControl,
    ListItem,
    DropdownControl,
    DropdownOption,
    ToastManager,
    ToastHandle,
    ToastSeverity,
    DialogManager,
    DialogHandle,
    DragDropManager,
    DragPayload,
    FormModel,
    FormField,
    ValidationRule,
    FieldError,
    CommandHistory,
    Command,
    CommandTransaction,
    DataGridControl,
    GridColumn,
    GridRow,
    ContextMenuManager,
    ContextMenuItem,
    ContextMenuHandle,
    SplitterControl,
)

# Consumer-side contracts are intentionally outside the gui_do library boundary:
from demo_features.mandelbrot_demo_feature import MandelStatusEvent
```

## Demo/Package Boundary

- `gui_do/` contains reusable framework/runtime functionality.
- Consumer/demo code lives outside `gui_do/` (in this repository currently under `demo_features/` and `*_demo.py`).
- Boundary scope for demo entrypoints is `*_demo.py`.
- Active demo entrypoints should consume the framework through `from gui_do import ...`, without aliases, and with a single `from gui_do import (...)` block.

## Architecture Docs

- `docs/public_api_spec.md`: supported exports and strict API contracts.
- `docs/event_system_spec.md`: normalized event model and routing semantics.
- `docs/architecture_boundary_spec.md`: package boundary rules and enforcement tests.

## Run Boundary Contract Tests

```bash
python -m unittest tests.test_boundary_contracts tests.test_public_api_exports tests.test_mandel_event_schema_exports tests.test_public_api_docs_contracts tests.test_architecture_boundary_docs_contracts tests.test_contract_command_parity tests.test_package_contracts_public_api tests.test_package_contracts_docs tests.test_contract_docs_helpers tests.test_core_only_bootstrap_contracts tests.test_contract_catalog_consistency -v
python -m pytest -q tests/test_boundary_contracts.py
python -m pytest -q tests/test_boundary_contracts.py tests/test_public_api_exports.py tests/test_mandel_event_schema_exports.py tests/test_public_api_docs_contracts.py tests/test_architecture_boundary_docs_contracts.py tests/test_contract_command_parity.py tests/test_package_contracts_public_api.py tests/test_package_contracts_docs.py tests/test_contract_docs_helpers.py tests/test_core_only_bootstrap_contracts.py tests/test_contract_catalog_consistency.py
```
