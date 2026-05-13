# Package Contracts

This file contains machine-validated package contract content used by docs and parity tests.

## Public API

Import contract notes:

- Supported usage is explicit named imports from `gui_do`.
- Star-import behavior is not part of the package contract.

Representative root-import contract (non-exhaustive):

```python
from gui_do import (
    bootstrap_host_application,
    HostApplicationConfig,
    FeatureSpec,
    WindowSpec,
    RuntimeSceneSpec,
    ActionSpec,
    GuiApplication,
    EventType,
    GuiEvent,
    EventManager,
    ActionManager,
    InputMap,
    FocusManager,
    OverlayManager,
    ThemeManager,
    TelemetryCollector,
    TelemetrySample,
    configure_telemetry,
    telemetry_collector,
    PanelControl,
    LabelControl,
    ButtonControl,
    TextInputControl,
    DropdownControl,
    ListViewControl,
    DataGridControl,
    TreeControl,
    WorkspacePersistenceManager,
    WorkspaceState,
    Router,
    RouteEntry,
    SceneTransitionManager,
    SceneTransitionStyle,
    ActiveTabUpdateRouter,
    TabLayoutContext,
)

# Consumer-side contracts are intentionally outside the gui_do library boundary:
from demo_features.mandelbrot.mandelbrot_status_event import MandelStatusEvent
```

## Demo/Package Boundary

- `gui_do/` contains reusable framework/runtime functionality.
- Consumer/demo code lives outside `gui_do/` (currently in `demo_features/` and `gui_do_demo.py`).
- Demo entrypoints should consume the framework through `from gui_do import ...`.
- Demo feature code should follow the folder-package best practice described in `docs/demo_feature_layout.md`.

## Architecture Docs

- `docs/public_api_spec.md`: supported exports and strict API contracts.
- `docs/event_system_spec.md`: normalized event model and routing semantics.
- `docs/architecture_boundary_spec.md`: package boundary rules and enforcement tests.
- `docs/runtime_operating_contracts.md`: runtime guarantees, observability, stability policy, and budget contracts.
- `docs/library_demo_separation_contract.md`: framework vs demo composition contract.

## Run Boundary Contract Tests

```bash
python -m unittest tests.test_boundary_contracts tests.test_public_api_exports tests.test_mandel_event_schema_exports tests.test_public_api_docs_contracts tests.test_architecture_boundary_docs_contracts tests.test_contract_command_parity tests.test_package_contracts_public_api tests.test_package_contracts_docs tests.test_contract_docs_helpers tests.test_core_only_bootstrap_contracts tests.test_contract_catalog_consistency tests.test_runtime_operating_contracts tests.test_gui_application_workspace_contracts -v
python -m pytest -q tests/test_boundary_contracts.py tests/test_public_api_exports.py tests/test_mandel_event_schema_exports.py tests/test_public_api_docs_contracts.py tests/test_architecture_boundary_docs_contracts.py tests/test_contract_command_parity.py tests/test_package_contracts_public_api.py tests/test_package_contracts_docs.py tests/test_contract_docs_helpers.py tests/test_core_only_bootstrap_contracts.py tests/test_contract_catalog_consistency.py tests/test_runtime_operating_contracts.py tests/test_gui_application_workspace_contracts.py
```
