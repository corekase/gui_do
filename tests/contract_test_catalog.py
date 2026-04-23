"""Canonical contract-test catalog shared by docs/parity regression tests."""

CONTRACT_TEST_MODULES = (
    "tests.test_boundary_contracts",
    "tests.test_public_api_exports",
    "tests.test_mandel_event_schema_exports",
    "tests.test_public_api_docs_contracts",
    "tests.test_architecture_boundary_docs_contracts",
    "tests.test_contract_command_parity",
    "tests.test_readme_public_api_contracts",
    "tests.test_readme_docs_contracts",
    "tests.test_contract_docs_helpers",
    "tests.test_contract_catalog_consistency",
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
    "demo_parts/mandelbrot_demo_part.py",
)

ACTIVE_DEMO_ENTRYPOINT_GLOB = "*_demo.py"
ACTIVE_DEMO_ENTRYPOINTS = (
    "gui_do_demo.py",
)

BOUNDARY_RULE_REQUIRED_PHRASES = (
    ACTIVE_DEMO_ENTRYPOINT_GLOB,
    "from gui import ...",
    "without aliases",
    "single from gui import (...) block",
    "Rebase migration is complete",
    "no previous-track baggage",
)

BOUNDARY_ENFORCEMENT_TEST_IDS = (
    "tests/test_boundary_contracts.py::test_gui_package_does_not_depend_on_demo_parts",
    "tests/test_boundary_contracts.py::test_demo_parts_does_not_depend_on_gui",
    "tests/test_boundary_contracts.py::test_demo_entrypoints_use_public_gui_api_only",
    "tests/test_boundary_contracts.py::test_demo_entrypoints_do_not_import_gui_submodules_via_import_statement",
    "tests/test_boundary_contracts.py::test_demo_entrypoints_import_only_named_public_gui_exports",
    "tests/test_boundary_contracts.py::test_demo_entrypoints_gui_root_import_names_follow_canonical_order",
    "tests/test_boundary_contracts.py::test_demo_entrypoints_do_not_alias_gui_root_imports",
    "tests/test_boundary_contracts.py::test_demo_entrypoints_use_single_gui_root_import_block",
    "tests/test_boundary_contracts.py::test_active_demo_entrypoints_match_expected_contract_set",
)

BOUNDARY_PYTEST_COMMAND = "python -m pytest -q tests/test_boundary_contracts.py"
BOUNDARY_WORKFLOW_STEP_NAME = "Run boundary contract tests"

BOUNDARY_COMMAND_SEQUENCE = (
    CONTRACT_UNITTEST_COMMAND,
    BOUNDARY_PYTEST_COMMAND,
    CONTRACT_PYTEST_COMMAND,
)

DEMO_PARTS_EXPORT_ORDER = (
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
)

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
    "VALUE_CHANGE_CALLBACK_MODES",
    "ValueChangeCallbackMode",
    "ValueChangeCallback",
    "ensure_reason_callback",
    "normalize_value_change_callback_mode",
    "ValueChangeReason",
    "InvalidationTracker",
    "ObservableValue",
    "PresentationModel",
    "TaskEvent",
    "TaskScheduler",
    "Timers",
    "BuiltInGraphicsFactory",
    "ColorTheme",
)

PUBLIC_API_REQUIRED_REFERENCES = (
    "docs/architecture_boundary_spec.md",
    "demo_parts/mandelbrot_demo_part.py",
)

PUBLIC_API_REQUIRED_PHRASES = (
    "demo_parts.mandelbrot_demo_part.__all__ export surface/order is treated as a locked contract",
)

README_PUBLIC_API_REQUIRED_GUI_IMPORTS = (
    "GuiApplication",
    "UiEngine",
    "ColorTheme",
)

README_PUBLIC_API_GUI_IMPORT_ORDER = (
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
    "VALUE_CHANGE_CALLBACK_MODES",
    "ValueChangeCallbackMode",
    "ValueChangeCallback",
    "ensure_reason_callback",
    "normalize_value_change_callback_mode",
    "ValueChangeReason",
    "InvalidationTracker",
    "ObservableValue",
    "PresentationModel",
    "TaskEvent",
    "TaskScheduler",
    "Timers",
    "BuiltInGraphicsFactory",
    "ColorTheme",
)

README_PUBLIC_API_REQUIRED_DEMO_IMPORTS = (
    "from demo_parts.mandelbrot_demo_part import MandelStatusEvent",
)

README_PUBLIC_API_REQUIRED_PHRASES = (
    "Demo-only contracts are intentionally outside gui package",
)

README_BOUNDARY_REQUIRED_PHRASES = (
    "gui/",
    "demo_parts/",
    "*_demo.py",
    "from gui import ...",
    "without aliases",
    "single from gui import (...) block",
)
