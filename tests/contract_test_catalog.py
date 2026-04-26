"""Canonical contract-test catalog shared by docs/parity regression tests."""

DEMO_CONTRACTS_ENABLED = True

CORE_CONTRACT_TEST_MODULES = (
    "tests.test_boundary_contracts",
    "tests.test_public_api_exports",
    "tests.test_public_api_docs_contracts",
    "tests.test_architecture_boundary_docs_contracts",
    "tests.test_contract_command_parity",
    "tests.test_package_contracts_public_api",
    "tests.test_package_contracts_docs",
    "tests.test_contract_docs_helpers",
    "tests.test_core_only_bootstrap_contracts",
    "tests.test_contract_catalog_consistency",
)

DEMO_CONTRACT_TEST_MODULES = (
    "tests.test_mandel_event_schema_exports",
)

CONTRACT_TEST_MODULES = (
    (
        "tests.test_boundary_contracts",
        "tests.test_public_api_exports",
        "tests.test_mandel_event_schema_exports",
        "tests.test_public_api_docs_contracts",
        "tests.test_architecture_boundary_docs_contracts",
        "tests.test_contract_command_parity",
        "tests.test_package_contracts_public_api",
        "tests.test_package_contracts_docs",
        "tests.test_contract_docs_helpers",
        "tests.test_core_only_bootstrap_contracts",
        "tests.test_contract_catalog_consistency",
    )
    if DEMO_CONTRACTS_ENABLED
    else CORE_CONTRACT_TEST_MODULES
)

CONTRACT_TEST_FILE_PATHS = tuple(module.replace(".", "/") + ".py" for module in CONTRACT_TEST_MODULES)

CONTRACT_UNITTEST_COMMAND = "python -m unittest " + " ".join(CONTRACT_TEST_MODULES) + " -v"
CONTRACT_PYTEST_COMMAND = "python -m pytest -q " + " ".join(CONTRACT_TEST_FILE_PATHS)

ARCHITECTURE_DOC_PATHS = (
    "docs/public_api_spec.md",
    "docs/event_system_spec.md",
    "docs/architecture_boundary_spec.md",
)

BOUNDARY_RELATED_DOC_PATHS = (
    "docs/public_api_spec.md",
    "docs/event_system_spec.md",
)

BOUNDARY_ASSET_PATHS = (
    "demo_features/mandelbrot_demo_feature.py",
) if DEMO_CONTRACTS_ENABLED else ()

ACTIVE_DEMO_ENTRYPOINT_GLOB = "*_demo.py"
ACTIVE_DEMO_ENTRYPOINTS = (
    "gui_do_demo.py",
) if DEMO_CONTRACTS_ENABLED else ()

BOUNDARY_RULE_REQUIRED_PHRASES = (
    (
        "from gui_do import ...",
        "without aliases",
        "single from gui_do import (...) block",
        "Rebase migration is complete",
        "no previous-track baggage",
    )
    if not DEMO_CONTRACTS_ENABLED
    else (
        ACTIVE_DEMO_ENTRYPOINT_GLOB,
        "from gui_do import ...",
        "without aliases",
        "single from gui_do import (...) block",
        "Rebase migration is complete",
        "no previous-track baggage",
    )
)

BOUNDARY_ENFORCEMENT_TEST_IDS = (
    (
        "tests/test_boundary_contracts.py::test_gui_package_does_not_depend_on_demo_features",
        "tests/test_boundary_contracts.py::test_demo_features_do_not_import_gui_do_internals",
    )
    if not DEMO_CONTRACTS_ENABLED
    else (
        "tests/test_boundary_contracts.py::test_gui_package_does_not_depend_on_demo_features",
        "tests/test_boundary_contracts.py::test_demo_features_do_not_import_gui_do_internals",
        "tests/test_boundary_contracts.py::test_demo_entrypoints_use_public_gui_api_only",
        "tests/test_boundary_contracts.py::test_demo_entrypoints_do_not_import_gui_submodules_via_import_statement",
        "tests/test_boundary_contracts.py::test_demo_entrypoints_import_only_named_public_gui_exports",
        "tests/test_boundary_contracts.py::test_demo_entrypoints_gui_root_import_names_follow_canonical_order",
        "tests/test_boundary_contracts.py::test_demo_entrypoints_do_not_alias_gui_root_imports",
        "tests/test_boundary_contracts.py::test_demo_entrypoints_use_single_gui_root_import_block",
        "tests/test_boundary_contracts.py::test_active_demo_entrypoints_match_expected_contract_set",
    )
)

BOUNDARY_PYTEST_COMMAND = "python -m pytest -q tests/test_boundary_contracts.py"
BOUNDARY_WORKFLOW_STEP_NAME = "Run boundary contract tests"

BOUNDARY_COMMAND_SEQUENCE = (
    CONTRACT_UNITTEST_COMMAND,
    BOUNDARY_PYTEST_COMMAND,
    CONTRACT_PYTEST_COMMAND,
)

DEMO_FEATURES_EXPORT_ORDER = (
    "MANDEL_STATUS_TOPIC",
    "MANDEL_STATUS_SCOPE",
    "MANDEL_KIND_IDLE",
    "MANDEL_KIND_CLEARED",
    "MANDEL_KIND_RUNNING_ITERATIVE",
    "MANDEL_KIND_RUNNING_RECURSIVE",
    "MANDEL_KIND_RUNNING_ONE_SPLIT",
    "MANDEL_KIND_RUNNING_FOUR_SPLIT",
    "MANDEL_KIND_FAILED",
    "MANDEL_KIND_COMPLETE",
    "MANDEL_KIND_STATUS",
    "MandelStatusEvent",
) if DEMO_CONTRACTS_ENABLED else ()

PUBLIC_API_EXPORT_ORDER = (
    "GuiApplication",
    "UiEngine",
    "PanelControl",
    "LabelControl",
    "ButtonControl",
    "ArrowBoxControl",
    "ButtonGroupControl",
    "CanvasControl",
    "CanvasEventPacket",
    "FrameControl",
    "ImageControl",
    "SliderControl",
    "ScrollbarControl",
    "TaskPanelControl",
    "ToggleControl",
    "WindowControl",
    "LayoutAxis",
    "LayoutManager",
    "WindowTilingManager",
    "ActionManager",
    "EventManager",
    "EventBus",
    "FocusManager",
    "FontManager",
    "EventPhase",
    "EventType",
    "GuiEvent",
    "ValueChangeCallback",
    "ValueChangeReason",
    "InvalidationTracker",
    "ObservableValue",
    "PresentationModel",
    "TaskEvent",
    "TaskScheduler",
    "Timers",
    "TelemetryCollector",
    "TelemetrySample",
    "configure_telemetry",
    "telemetry_collector",
    "analyze_telemetry_records",
    "analyze_telemetry_log_file",
    "load_telemetry_log_file",
    "render_telemetry_report",
    "BuiltInGraphicsFactory",
    "ColorTheme",
    "Feature",
    "DirectFeature",
    "LogicFeature",
    "RoutedFeature",
    "FeatureMessage",
    "FeatureManager",
)

PUBLIC_API_REQUIRED_REFERENCES = (
    "docs/architecture_boundary_spec.md",
    "demo_features/mandelbrot_demo_feature.py",
) if DEMO_CONTRACTS_ENABLED else ()

PUBLIC_API_REQUIRED_PHRASES = (
    "demo_features.mandelbrot_demo_feature.__all__ export surface/order is treated as a locked contract",
) if DEMO_CONTRACTS_ENABLED else ()

PACKAGE_PUBLIC_API_REQUIRED_GUI_IMPORTS = (
    "GuiApplication",
    "UiEngine",
    "ColorTheme",
)

PACKAGE_PUBLIC_API_GUI_IMPORT_ORDER = (
    "GuiApplication",
    "UiEngine",
    "PanelControl",
    "LabelControl",
    "ButtonControl",
    "ArrowBoxControl",
    "ButtonGroupControl",
    "CanvasControl",
    "CanvasEventPacket",
    "FrameControl",
    "ImageControl",
    "SliderControl",
    "ScrollbarControl",
    "TaskPanelControl",
    "ToggleControl",
    "WindowControl",
    "LayoutAxis",
    "LayoutManager",
    "WindowTilingManager",
    "ActionManager",
    "EventManager",
    "EventBus",
    "FocusManager",
    "FontManager",
    "EventPhase",
    "EventType",
    "GuiEvent",
    "ValueChangeCallback",
    "ValueChangeReason",
    "InvalidationTracker",
    "ObservableValue",
    "PresentationModel",
    "TaskEvent",
    "TaskScheduler",
    "Timers",
    "TelemetryCollector",
    "TelemetrySample",
    "configure_telemetry",
    "telemetry_collector",
    "analyze_telemetry_records",
    "analyze_telemetry_log_file",
    "load_telemetry_log_file",
    "render_telemetry_report",
    "BuiltInGraphicsFactory",
    "ColorTheme",
)

PACKAGE_PUBLIC_API_REQUIRED_DEMO_IMPORTS = (
    "from demo_features.mandelbrot_demo_feature import MandelStatusEvent",
) if DEMO_CONTRACTS_ENABLED else ()

PACKAGE_PUBLIC_API_REQUIRED_PHRASES = (
    "Demo-only contracts are intentionally outside gui_do package",
)

PACKAGE_BOUNDARY_REQUIRED_PHRASES = (
    (
        "gui_do/",
        "from gui_do import ...",
        "without aliases",
        "single from gui_do import (...) block",
    )
    if not DEMO_CONTRACTS_ENABLED
    else (
        "gui_do/",
        "demo_features/",
        "*_demo.py",
        "from gui_do import ...",
        "without aliases",
        "single from gui_do import (...) block",
    )
)
