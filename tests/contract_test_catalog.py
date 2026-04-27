"""Canonical contract-test catalog shared by docs/parity regression tests."""

DEMO_CONTRACTS_ENABLED = True

DEMO_TEST_DISCOVERY_RULE = "any test file in tests/ that imports from demo_features"

LIBRARY_SEPARATION_PRINCIPLE = """
GUI_DO LIBRARY vs DEMO SEPARATION:

Complete architectural separation between the reusable gui_do framework and
demo code that uses it. The demo ships in the same repository as a working
example but is NOT part of the library distribution.

GUI_DO LIBRARY:
  - gui_do/ package: Core framework, all controls, event system, layout, theme, etc.
  - tests/: Unit tests verifying all library contracts and functionality
  - docs/: Architecture and API documentation
  - scripts/manage.py: Developer bootstrap tool — strips demo to yield clean library base
  - Wheel distribution contains only gui_do/ package
  - Sdist distribution contains gui_do/, tests/, docs/, scripts/ but NOT demo content
    - Does NOT import from demo_features (enforced by test_gui_package_does_not_depend_on_demo_features)
    - Does NOT reference consumer/demo-owned paths (all path resolution uses caller-supplied CWD-relative paths)

DEMO (ships with repo, stripped by manage.py init for application developers):
    - Consumer/demo code outside gui_do/ (currently demo_features/ and *_demo.py)
  - *_demo.py: Demo application entrypoints (discovered by glob, not hardcoded list)
  - Demo tests: any test file in tests/ that imports from demo_features (content-scan discovered)
  - Demo imports ONLY from gui_do public root (enforced by test_demo_entrypoints_use_public_gui_api_only)
  - Demo passes full CWD-relative paths to framework for all asset loading
  - Demo features do NOT import gui_do internals (enforced by test_demo_features_do_not_import_gui_do_internals)
  - NOT included in wheel distribution
  - NOT included in sdist distribution

DEVELOPER WORKFLOW (application developers using gui_do):
  - Clone or download the repository
  - Run: python scripts/manage.py init  (strips all demo content)
  - Result: clean gui_do library base ready for building their own application
  - manage.py discovers all demo artifacts dynamically (no hardcoded lists)

PACKAGING ENFORCEMENT:
  - pyproject.toml [tool.setuptools.packages.find] include = ["gui_do*"] only
    - MANIFEST.in ships package sources/docs/tests without bundling consumer/demo trees
  - No hardcoded demo paths in gui_do/ code
  - All asset loading in framework accepts caller-supplied paths
"""

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
    "tests.test_library_demo_separation_contracts",
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
    )
    if not DEMO_CONTRACTS_ENABLED
    else (
        ACTIVE_DEMO_ENTRYPOINT_GLOB,
        "from gui_do import ...",
        "without aliases",
        "single from gui_do import (...) block",
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
    "ComputedValue",
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
    "TweenManager",
    "TweenHandle",
    "Easing",
    "TextInputControl",
    "ConstraintLayout",
    "AnchorConstraint",
    "OverlayManager",
    "OverlayHandle",
    "OverlayPanelControl",
    "ListViewControl",
    "ListItem",
    "DropdownControl",
    "DropdownOption",
    "ToastManager",
    "ToastHandle",
    "ToastSeverity",
    "DialogManager",
    "DialogHandle",
    "DragDropManager",
    "DragPayload",
    "FormModel",
    "FormField",
    "ValidationRule",
    "FieldError",
    "CommandHistory",
    "Command",
    "CommandTransaction",
    "DataGridControl",
    "GridColumn",
    "GridRow",
    "ContextMenuManager",
    "ContextMenuItem",
    "ContextMenuHandle",
    "SplitterControl",
    "StateMachine",
    "SettingsRegistry",
    "SettingDescriptor",
    "Router",
    "RouteEntry",
    "ThemeManager",
    "DesignTokens",
    "TextAreaControl",
    "RichLabelControl",
    "TabControl",
    "TabItem",
    "ResizeManager",
    "MenuBarControl",
    "MenuEntry",
    "MenuBarManager",
    "TreeControl",
    "TreeNode",
    "FileDialogManager",
    "FileDialogOptions",
    "FileDialogHandle",
    "FlexLayout",
    "FlexItem",
    "FlexDirection",
    "FlexAlign",
    "FlexJustify",
    "SceneTransitionManager",
    "SceneTransitionStyle",
    "NotificationCenter",
    "NotificationRecord",
    "NotificationPanelControl",
    "ClipboardManager",
    "AnimationSequence",
    "AnimationHandle",
    "ScrollViewControl",
    "SpinnerControl",
    "RangeSliderControl",
    "ColorPickerControl",
    "CommandPaletteManager",
    "CommandEntry",
    "CommandPaletteHandle",
    "ChangeKind",
    "CollectionChange",
    "ObservableList",
    "ObservableDict",
    "Binding",
    "BindingGroup",
    "GestureRecognizer",
    "LayoutAnimator",
    "Debouncer",
    "Throttler",
    "GridLayout",
    "GridTrack",
    "GridPlacement",
    "KeyChordManager",
    "KeyChord",
    "ChordStep",
    "ErrorBoundary",
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
    "ComputedValue",
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
    "TweenManager",
    "TweenHandle",
    "Easing",
    "TextInputControl",
    "ConstraintLayout",
    "AnchorConstraint",
    "OverlayManager",
    "OverlayHandle",
    "OverlayPanelControl",
    "ListViewControl",
    "ListItem",
    "DropdownControl",
    "DropdownOption",
    "ToastManager",
    "ToastHandle",
    "ToastSeverity",
    "DialogManager",
    "DialogHandle",
    "DragDropManager",
    "DragPayload",
    "FormModel",
    "FormField",
    "ValidationRule",
    "FieldError",
    "CommandHistory",
    "Command",
    "CommandTransaction",
    "DataGridControl",
    "GridColumn",
    "GridRow",
    "ContextMenuManager",
    "ContextMenuItem",
    "ContextMenuHandle",
    "SplitterControl",
    "StateMachine",
    "SettingsRegistry",
    "SettingDescriptor",
    "Router",
    "RouteEntry",
    "ThemeManager",
    "DesignTokens",
    "TextAreaControl",
    "RichLabelControl",
    "TabControl",
    "TabItem",
    "ResizeManager",
    "MenuBarControl",
    "MenuEntry",
    "MenuBarManager",
    "TreeControl",
    "TreeNode",
    "FileDialogManager",
    "FileDialogOptions",
    "FileDialogHandle",
    "FlexLayout",
    "FlexItem",
    "FlexDirection",
    "FlexAlign",
    "FlexJustify",
    "SceneTransitionManager",
    "SceneTransitionStyle",
    "NotificationCenter",
    "NotificationRecord",
    "NotificationPanelControl",
    "ClipboardManager",
    "AnimationSequence",
    "AnimationHandle",
    "ScrollViewControl",
    "SpinnerControl",
    "RangeSliderControl",
    "ColorPickerControl",
    "CommandPaletteManager",
    "CommandEntry",
    "CommandPaletteHandle",
    "ChangeKind",
    "CollectionChange",
    "ObservableList",
    "ObservableDict",
    "Binding",
    "BindingGroup",
    "GestureRecognizer",
    "LayoutAnimator",
    "Debouncer",
    "Throttler",
    "GridLayout",
    "GridTrack",
    "GridPlacement",
    "KeyChordManager",
    "KeyChord",
    "ChordStep",
    "ErrorBoundary",
)

PACKAGE_PUBLIC_API_REQUIRED_DEMO_IMPORTS = (
    "from demo_features.mandelbrot_demo_feature import MandelStatusEvent",
) if DEMO_CONTRACTS_ENABLED else ()

PACKAGE_PUBLIC_API_REQUIRED_PHRASES = (
    "Consumer-side contracts are intentionally outside the gui_do library boundary",
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
        "outside `gui_do/`",
        "*_demo.py",
        "from gui_do import ...",
        "without aliases",
        "single from gui_do import (...) block",
    )
)
