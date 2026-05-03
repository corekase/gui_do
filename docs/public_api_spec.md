# Public API Specification

## Scope

This document defines the supported public surface of the `gui_do` package and the strict contracts expected by runtime components.

Terminology in this document aligns with README and architecture docs:

- `strict contracts`: no compatibility/fallback behavior in core dispatch and rendering paths.
- `scene isolation`: only the active scene executes scene-contained runtime updates.
- `demo boundary`: demo-only schemas stay outside the gui_do root import contract.

## Design Principle: Data-Driven & Lifecycle First

**As of May 2026, gui_do's public API is organized around a core principle:**

> Applications should be built using **declarative specs and feature lifecycles**, not imperative GUI construction.

This design makes `bootstrap_host_application` with `HostApplicationConfig` the **primary entrypoint**. Traditional GUI controls and low-level managers are **secondary** and **discouraged for direct use**—instead, integrate them through the Feature system.

## API Organization

The public API is organized into **tiers** by purpose and abstraction level:

### Tier 1: PRIMARY ENTRY POINTS (use these to build apps)

**These are the recommended way to start:**

- `bootstrap_host_application(host, config)` — main bootstrapping function
- `HostApplicationConfig` — declarative application configuration
- Spec classes for declarative app definition:
  - `FeatureSpec` — declare a feature to instantiate
  - `WindowSpec` — declare a feature window with toggles and tabs
  - `RuntimeSceneSpec` — declare a runtime scene's startup behavior
  - `ActionSpec` — declare a host-level action
  - `StaticAccessibilitySpec` — declare accessibility annotations
  - `CursorSpec` — declare a cursor asset
  - `SceneRootSpec` — declare a scene root panel
  - `AnchoredWindowSpec` — declare a presenter-backed window
  - `LogicBindingSpec` — declare a routed-feature alias
  - `TaskPanelButtonSpec` — declare a task-panel button
  - `AccessibilitySequenceSpec` — declare accessibility sequence specs
  - `TabBuilderSpec` — declare tab key/label and builder
- Spec builder helpers:
  - `make_window_toggle_spec(...)` — create `WindowSpec`
  - `make_scene_nav_action(...)` — create `ActionSpec` for scene navigation
  - `make_exit_action(...)` — create `ActionSpec` for exit
  - `make_palette_open_action(...)` — create `ActionSpec` for command palette
  - `make_static_accessibility_spec(...)` — create `StaticAccessibilitySpec`
- Feature system (core to lifecycle model):
  - `Feature` — base feature interface
  - `DirectFeature` — feature with no container window
  - `LogicFeature` — feature for event handlers and state
  - `RoutedFeature` — feature with message routing
  - `FeatureMessage` — message passed between features
  - `FeatureManager` — runtime manager for features
  - `SceneSetupSpec` — declare a scene at bootstrap
  - `ScenePresentationModel` — access scene state and bindings
- Configuration & setup:
  - `setup_standard_font_roles(...)` — register standard font styles
  - `TelemetryConfig` — telemetry configuration for the app

### Tier 2: CORE APPLICATION & SCENE MANAGEMENT

**Central managers and containers required for runtime:**

- `GuiApplication` — the main application container (created by `bootstrap_host_application`)
- `create_display(size)` — create the pygame display surface
- `SceneTransitionManager` — manage scene transitions (created by bootstrap)
- `SceneTransitionStyle` — enum for transition animations
- `apply_scene_setup_specs(...)` — apply scene specs at runtime

### Tier 3: DATA & STATE

**Reactive programming and observation patterns:**

- `ObservableValue[T]` — observable scalar value
- `PresentationModel` — base for observable objects
- `ComputedValue[T]` — computed/derived observable value
- `InvalidationTracker` — track invalidated controls
- Observable collections:
  - `ObservableList[T]`
  - `ObservableDict[K, V]`
  - `ChangeKind` — kind of collection change (insert/remove/update/reset)
  - `CollectionChange[T]` — description of a change event
- Data binding:
  - `Binding` — two-way data binding
  - `BindingGroup` — manage multiple bindings
  - `CollectionView` — filtered/sorted view of a collection
  - `SelectionModel` — manage selected items
- Advanced data:
  - `ObservableStream` — stream of values with subscription
  - `ObjectPool` — object pooling for reuse
  - `DataCache` — cache with stats tracking
  - `AsyncDataProvider[T]` with `LoadState` enum — async data loading

### Tier 4: EVENTS, ACTIONS, & INPUT

**Core event and input infrastructure:**

- Event types:
  - `GuiEvent` — base GUI event
  - `EventType` — event kind enum
  - `EventPhase` — event propagation phase (bubble, capture, target)
  - `ValueChangeCallback` — callback signature for value changes
  - `ValueChangeReason` — reason for a value change
- Event routing:
  - `EventManager` — manages scene event delivery
  - `EventBus` — publish/subscribe event distribution
  - `GestureRecognizer` — recognize multi-touch/keyboard gestures
  - `EventRecorder`/`EventPlayback`/`RecordedEvent` — record and replay events
- Actions:
  - `ActionManager` — manage application actions
  - `ActionRegistry` — register actions by ID
  - `ActionDescriptor` — metadata for an action
  - `ActionContext` — context passed to action handlers
  - `ActionMiddleware` — intercept/modify action handling
  - `InputMap` — map input (keyboard, etc.) to actions
  - `InputBinding` — single input -> action binding
  - `KeyChordManager`/`KeyChord`/`ChordStep` — multi-key chord recognition
- Focus:
  - `FocusManager` — manage focused control
  - `FocusScope` — define a focus boundary
  - `FocusScopeManager` — manage focus scopes
  - `WindowFocusManager` — manage focus across windows
  - `FocusRing` — visual focus indicator
- Metadata:
  - `InputSnapshot` — snapshot of input state at a moment
  - `Signal`/`SignalConnection` — signal/slot pub-sub

### Tier 5: SCHEDULING & ANIMATION

**Time-based updates, animations, and async operations:**

- Task scheduling:
  - `TaskScheduler` — schedule deferred tasks
  - `TaskEvent` — event from a scheduled task
  - `Timers` — frame-synchronized timers
- Tweening & animation:
  - `TweenManager` — manage tweens (value interpolations)
  - `TweenHandle` — handle to active tween
  - `Easing` — easing function enum
  - `AnimationSequence`/`AnimationHandle` — multi-step animations
  - `TransitionManager` — manage state transitions with animations
  - `TransitionSpec`/`TransitionEvent` — transition specification
  - `AnimationStateMachine` — state machine with animated transitions
  - `AnimationTransitionMode` — immediate, smooth, or per-property
  - `SceneTimeline` — timeline of events in a scene
- Coroutines:
  - `CooperativeScheduler` — run user coroutines
  - `CoroutineHandle` — handle to active coroutine
  - `Pause`, `Sleep`, `WaitForEvent`, `WaitForSignal`, `WaitUntil`, `WaitForAll` — coroutine primitives
- Rate limiting:
  - `Debouncer` — delay rapid-fire events
  - `Throttler` — limit event frequency

### Tier 6: THEME & FONTS

**Visual theming and typography:**

- Font management:
  - `FontManager` — render text with styled fonts
  - `FontRoleRegistry` — define named font roles (e.g. "title", "body")
  - `TextFormatter`/`NumericFormatter`/`PatternFormatter` — format text for display
- Theming:
  - `ColorTheme` — named color palette
  - `ThemeManager` — manage active theme
  - `DesignTokens` — access token values
  - `ScopedTheme`/`ScopedThemeManager` — apply theme to a subtree
- Localization:
  - `StringTable` — table of localized strings
  - `LocaleRegistry` — manage available locales
- Text:
  - `TextFlow` — text layout with styled spans
  - `TextSpan` — styled text segment
  - `TextSearcher`/`TextMatch` — search text with context

### Tier 7: TELEMETRY & DIAGNOSTICS

**Performance monitoring and insights:**

- Telemetry:
  - `TelemetryCollector` — collect metrics
  - `TelemetrySample` — single measurement
  - `configure_telemetry(...)` — configure telemetry behavior
  - `telemetry_collector` — global collector instance
- Analysis:
  - `analyze_telemetry_records(...)` — analyze in-memory records
  - `analyze_telemetry_log_file(...)` — analyze from disk
  - `load_telemetry_log_file(...)` — load log file
  - `render_telemetry_report(...)` — generate report

### Tier 8: LAYOUT ENGINES

**Layout algorithms and spatial organization:**

- Basic layout:
  - `LayoutAxis` — axis enum (horizontal/vertical)
  - `LayoutManager` — compose layouts
  - `WindowTilingManager` — tile windows in a workspace
- Constraint-based:
  - `ConstraintLayout` — anchor controls with constraints
  - `AnchorConstraint` — position relative to anchor
- Docking:
  - `DockPane`, `DockTabs`, `DockSplit`, `DockWorkspace` — dock layout containers
  - `DockWorkspacePanel` — control in dock workspace
- Flex layout:
  - `FlexLayout`, `FlexItem` — CSS flexbox-like layout
  - `FlexDirection`, `FlexAlign`, `FlexJustify` — flex properties
- Grid:
  - `GridLayout`, `GridTrack`, `GridPlacement` — CSS grid-like layout
  - `CellCaretLayout`/`CellCaretState` — cell-based navigation
  - `SnapGrid` — snap to alignment guides
- Other:
  - `FlowLayout`, `FlowItem` — flow text-like layout
  - `ResponsiveLayout` — layout that adapts to breakpoints
  - `Breakpoint` — responsive design breakpoint
  - `LayoutAnimator` — animate layout changes
  - `LayoutPass`, `MeasureContext`, `ArrangeContext`, `LayoutRoot` — measurement/arrangement pipeline
  - `Viewport` — scrollable viewport

### Tier 9: OVERLAY & MODAL MANAGERS

**Modal dialogs, floating panels, and context menus:**

- Core overlay:
  - `OverlayManager` — manage floating content
  - `OverlayHandle` — handle to active overlay
  - `PopupPlacement` — placement algorithm
  - `Alignment`, `Side`, `PlacementResult` — placement enums
  - `compute_popup_rect(...)` — compute placement rect
- Specific managers:
  - `DialogManager` — modal dialogs
  - `DialogHandle` — dialog instance
  - `ToastManager`/`ToastHandle`/`ToastSeverity` — brief notifications
  - `CommandPaletteManager` — command/action palette overlay
  - `CommandEntry`/`CommandPaletteHandle` — palette entries
  - `ContextMenuManager` — context menus
  - `ContextMenuItem`/`ContextMenuHandle` — menu items
  - `TooltipManager`/`TooltipHandle` — hover tooltips
  - `MenuBarManager` — application menu bar
  - `FileDialogManager` — file open/save dialogs
  - `FileDialogOptions`/`FileDialogHandle` — dialog options
  - `NotificationCenter`/`NotificationRecord` — notification inbox
  - `ResizeManager` — constraint-based resize handles
  - `DragDropManager`/`DragPayload` — drag and drop operations
  - `ClipboardManager` — system clipboard access
  - `TransferManager`/`TransferData` — inter-app drag/drop data
  - `ShortcutHelpOverlay` — keyboard shortcut reference

### Tier 10: FORMS & STRUCTURED DATA

**Form models, validation, and document editing:**

- Forms:
  - `FormModel` — form with typed fields
  - `FormField` — single form field
  - `ValidationRule` — validation rule
  - `FieldError` — validation error
  - `FormSchema` — form structure definition
  - `SchemaField` — field in schema
- Documents:
  - `DocumentModel` — rich document editing
  - `CommandHistory` — undo/redo support
  - `Command`/`CommandTransaction` — commands in history
- Wizards:
  - `WizardFlow`/`WizardStep`/`WizardHandle` — multi-step wizard UI
- Validation:
  - `Validator` — base validator
  - `RequiredValidator`/`RangeValidator`/`LengthValidator` — built-in validators
  - `PatternValidator` — regex validation
  - `CustomValidator`/`DependentValidator` — user-defined validators
  - `ValidationPipeline` — chain validators
  - `ValidationResult` — validation outcome

### Tier 11: STATE & PERSISTENCE

**Application state, routing, and persistent storage:**

- State machines:
  - `StateMachine` — finite state machine
  - `HierarchicalStateMachine` — composite/nested states
- Navigation:
  - `Router` — navigation routing
  - `RouteEntry` — route definition
- Settings:
  - `SettingsRegistry` — application settings
  - `SettingDescriptor` — setting metadata
- Persistence:
  - `WorkspacePersistenceManager` — save/load workspace state
  - `WorkspaceState` — workspace snapshot
  - `DEFAULT_WORKSPACE_STATE_PATH` — default save location
  - `SceneSnapshot`/`NodeSnapshot` — control tree snapshots

### Tier 12–13: CONTROLS (GUI BUILDING BLOCKS)

**IMPORTANT: These are listed for completeness but are SECONDARY APIs.**

**Recommendation:** Compose controls via **features and specs**, not by directly instantiating controls.

#### Primary Controls (Tier 12)
- Basic containers:
  - `PanelControl` — layout container
  - `DockWorkspacePanel` — panel in dock workspace
- Display:
  - `LabelControl` — text label
  - `FrameControl` — visual frame/border
  - `ImageControl` — image display
  - `CanvasControl` — raw drawing surface
- Input:
  - `ButtonControl` — clickable button
  - `ToggleControl` — checkbox/toggle switch
  - `SliderControl` — value slider
  - `ScrollbarControl` — scroll bar
  - `ArrowBoxControl` — small directional button
  - `ButtonGroupControl` — button group
- Data:
  - `TabControl`/`TabItem` — tabbed interface

#### Extended Controls (Tier 13)
- Text entry:
  - `TextInputControl` — single-line text entry
  - `TextAreaControl` — multi-line text entry
  - `RichLabelControl` — text with inline formatting
- Complex selection:
  - `DropdownControl`/`DropdownOption` — dropdown selection
  - `ListViewControl`/`ListItem` — list selection
  - `DataGridControl`/`GridColumn`/`GridRow` — data table
  - `TreeControl`/`TreeNode` — hierarchical tree
- Layout utilities:
  - `OverlayPanelControl` — control in an overlay
  - `SplitterControl` — resizable split pane
  - `ScrollViewControl` — scrollable content area
- Input variants:
  - `SpinnerControl` — number spinner
  - `RangeSliderControl` — range value slider
  - `ColorPickerControl` — color selection
  - `ProgressBarControl` — progress indication
- Specialized:
  - `AnimatedImageControl` — image animation playback
  - `ErrorBoundary` — error handling boundary
  - `PropertyInspectorPanel` — property editor
- Chrome/framing:
  - `WindowControl` — window frame
  - `TaskPanelControl` — task panel
  - `MenuBarControl`/`MenuEntry` — application menu
  - `SceneMenuStripControl` — scene-level menu
  - `NotificationPanelControl` — notification display

### Tier 14: INTROSPECTION & INSPECTION

**Runtime property inspection and debugging:**

- Property system:
  - `ui_property` — decorator to expose properties
  - `PropertyDescriptor` — property metadata
  - `PropertyRegistry`/`property_registry` — global registry
- Inspection:
  - `PropertyInspectorModel` — model for property inspection
  - `InspectedProperty` — inspected property data
- Spatial:
  - `SceneSpatialIndex` — spatial query on scene

### Tier 15: GRAPHICS & RENDERING

**Graphics, asset management, and visual effects:**

- Rendering:
  - `DrawContext` — drawing context (pygame Surface)
  - `DrawPhase` — render phase
- Assets:
  - `AssetRegistry` — manage graphics assets
  - `BuiltInGraphicsFactory` — built-in graphics (default implementation)
- Effects & visualization:
  - `DirtyRegionTracker` — track invalidated regions
  - `DebugOverlay` — debug visualization
  - `SurfaceCompositor`/`Layer` — compose surfaces into layers
  - `ShapeRenderer` — draw geometric shapes
  - `SurfaceEffects` — visual effects (blur, etc.)
  - `VectorPath` — vector drawing primitives
  - `SpriteSheet`/`FrameAnimation` — sprite animation
  - `ParticleSystem`/`Emitter`/`ParticleLayer` — particle effects
  - `TileSet`/`TileMap` — tilemap rendering

### Tier 16: DATA STRUCTURES & UTILITIES

**Advanced data structures and utility libraries:**

- Collections:
  - `VirtualItemSource`/`FixedItemSource` — item source abstractions
  - `SortFilterProxySource` — filtered/sorted view source
  - `ListDiffCalculator`/`ListDiff` — compute collection diffs
  - `DiffInsert`/`DiffRemove`/`DiffMove` — diff operations
- Utilities:
  - `CursorManager` — cursor management
  - `CursorHandle` — cursor handle
  - `CursorShape` — cursor shape enum

### Tier 17: ADVANCED RUNTIME (INTERNAL BOOTSTRAP HELPERS)

**Advanced feature wiring, presentation setup, and internal helpers.**

**Recommendation:** Use `bootstrap_host_application` instead of these—only use these for extending bootstrap behavior.

- Window/feature presentation:
  - `create_anchored_feature_window(...)` — create feature window
  - `create_presented_anchored_window(...)` — with presentation
  - `create_presented_window_from_spec(...)` — from spec
  - `create_feature_presented_window(...)` — feature presenter
  - `FrameTimer` — frame-rate timer
  - `TabPanelManager` — manage tab panels
  - `WindowRelativeRect` — window-relative positioning
  - `ScenePresentationModel` — scene state/bindings (part of lifecycle)
- Layout helpers (for manual feature window layout):
  - `place_control(...)`/`place_control_unlabeled(...)` — position controls
  - `register_placed_control(...)` — register placed control
  - `add_group_label(...)`/`PlacedControl` — labeled groups
  - `centered_horizontal_strip_layout(...)` — common layout patterns
  - `split_slot_bounds(...)`/`partition_rects(...)`/`inset_rect(...)`
- Scene setup:
  - `apply_scene_setup_specs(...)` — apply scene specs
  - `bind_runtime_scene_exit_keys(...)` — bind ESC key
  - `apply_runtime_scene_pristine_assets(...)` — load pristine assets
  - `prewarm_runtime_scenes(...)` — preload scenes
- Accessibility:
  - `apply_accessibility_sequence(...)` — set tab order
  - `apply_accessibility_sequence_from_attrs(...)` — from object attributes
- Feature wiring:
  - `instantiate_features_from_specs(...)` — create features
  - `register_features_from_specs(...)` — register them
  - `register_companion_logic_features(...)` — register logic features
  - `bind_feature_logic_aliases(...)` — alias feature names
  - `setup_routed_feature_runtime(...)` — route messages
- Window/action setup:
  - `register_window_presentation_specs(...)` — window bindings
  - `register_window_tab_builders(...)` — tab builders
  - `setup_feature_presenter_tabs(...)` — presenter tabs
  - `collect_window_toggle_controls(...)` — gather toggles
  - `apply_window_toggle_accessibility(...)` — toggles a11y
  - `add_window_toggle_task_panel_controls(...)` — task panel buttons
  - `register_window_toggle_tooltips(...)` — tooltips
  - Various `add_window_*` helpers for manual window building
- Menu & palette:
  - `build_tools_menu_entries(...)` — menu building
  - `add_standard_scene_menu_strip(...)` — standard menu
  - `add_window_scene_menu_strip(...)` — window menu
- Other:
  - `ActiveTabUpdateRouter` — route tab updates
  - `TabLayoutContext` — tab layout context
  - `ensure_scene_scheduler(...)` — get/create scene scheduler
  - `bind_input_map_actions(...)` — bind input to actions
  - Plus many more `register_*` and `*_from_*` helpers

### Tier 18: INFRASTRUCTURE (AVOID IN APPLICATION CODE)

**Low-level infrastructure internal to the framework:**

- `UiEngine` — the core render engine (users access via `GuiApplication.render` etc.)

## Import Contract

- Supported consumer imports use explicit named imports from `gui_do`.
- Star-import behavior is not part of the public contract.
- The import list documented in this spec and in `__all__` is authoritative.

## Strict Contracts

- `strict contracts`: no compatibility/fallback behavior in core dispatch and rendering paths.
- `scene isolation`: only the active scene executes scene-contained runtime updates.
- All controls follow the disabled/hidden guard pattern at the top of `handle_event`.
- All visual state changes call `invalidate()` to trigger re-render.

## Enforcement

Automated tests enforce the public API contract:

- `tests/test_public_api_exports.py` — validates `__all__` completeness
- `tests/test_core_only_bootstrap_contracts.py` — validates bootstrap-only requirements
- `tests/test_boundary_contracts.py` — validates gui_do/demo_features boundary
- `tests/test_runtime_operating_contracts.py` — validates runtime invariants

Run command:

```bash
python -m pytest -q tests/test_public_api_exports.py tests/test_core_only_bootstrap_contracts.py tests/test_boundary_contracts.py tests/test_runtime_operating_contracts.py
```

## Migration Guide: Toward Data-Driven APIs

If you have existing code that directly instantiates controls and managers:

1. **Identify your scene structure** — what scenes and features does your app need?
2. **Define declarative specs** — use `SceneSetupSpec`, `FeatureSpec`, `WindowSpec`, `ActionSpec`
3. **Create a `HostApplicationConfig`** — gather all specs and configuration
4. **Call `bootstrap_host_application`** — let it wire everything up
5. **Implement Features** — put your logic in `Feature` subclasses

This approach is more maintainable, testable, and follows the intended design.

- `GuiApplication`
- `create_display`
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
- `DockPane`
- `DockTabs`
- `DockSplit`
- `DockWorkspace`
- `DockWorkspacePanel`
- `ActionManager`
- `ActionContext`
- `ActionMiddleware`
- `ActionDescriptor`
- `ActionRegistry`
- `EventManager`
- `EventBus`
- `FocusManager`
- `FontManager`
- `FontRoleRegistry`
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
- `FrameTimer`
- `TabPanelManager`
- `WindowRelativeRect`
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
- `FormSchema`
- `SchemaField`
- `CommandHistory`
- `Command`
- `CommandTransaction`
- `DocumentModel`
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
- `WorkspaceState`
- `WorkspacePersistenceManager`
- `DEFAULT_WORKSPACE_STATE_PATH`
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
- `SceneMenuStripControl`
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
- `TransferData`
- `TransferManager`
- `AnimationSequence`
- `AnimationHandle`
- `ScrollViewControl`
- `SpinnerControl`
- `RangeSliderControl`
- `ColorPickerControl`
- `CommandPaletteManager`
- `CommandEntry`
- `CommandPaletteHandle`
- `ChangeKind`
- `CollectionChange`
- `ObservableList`
- `ObservableDict`
- `CollectionViewQuery`
- `CollectionView`
- `Binding`
- `BindingGroup`
- `GestureRecognizer`
- `LayoutAnimator`
- `Debouncer`
- `Throttler`
- `GridLayout`
- `GridTrack`
- `GridPlacement`
- `KeyChordManager`
- `KeyChord`
- `ChordStep`
- `ErrorBoundary`
- `TooltipManager`
- `TooltipHandle`
- `FocusScope`
- `FocusScopeManager`
- `WindowFocusManager`
- `SelectionModel`
- `SelectionMode`
- `TextFormatter`
- `NumericFormatter`
- `PatternFormatter`
- `FixedPatternFormatter`
- `VirtualItemSource`
- `FixedItemSource`
- `CanvasViewport`
- `TransitionManager`
- `TransitionSpec`
- `TransitionEvent`
- `ScopedTheme`
- `ScopedThemeManager`
- `AsyncDataProvider`
- `LoadState`
- `LoadStateKind`
- `LayoutPass`
- `MeasureContext`
- `ArrangeContext`
- `LayoutRoot`
- `CursorManager`
- `CursorHandle`
- `CursorShape`
- `SortFilterProxySource`
- `StringTable`
- `LocaleRegistry`
- `InputMap`
- `InputBinding`
- `SceneSpatialIndex`
- `TextFlow`
- `TextSpan`
- `ResponsiveLayout`
- `Breakpoint`
- `EventRecorder`
- `EventPlayback`
- `RecordedEvent`
- `ui_property`
- `PropertyDescriptor`
- `PropertyRegistry`
- `PropertyInspectorModel`
- `InspectedProperty`
- `PropertyInspectorPanel`
- `property_registry`
- `SceneSnapshot`
- `NodeSnapshot`
- `DirtyRegionTracker`
- `DrawContext`
- `DrawPhase`
- `AssetRegistry`
- `DebugOverlay`
- `InputSnapshot`
- `Signal`
- `SignalConnection`
- `ValidationResult`
- `Validator`
- `RequiredValidator`
- `RangeValidator`
- `LengthValidator`
- `PatternValidator`
- `CustomValidator`
- `DependentValidator`
- `ValidationPipeline`
- `Viewport`
- `HierarchicalStateMachine`
- `FocusRing`
- `ObservableStream`
- `SurfaceCompositor`
- `Layer`
- `ShapeRenderer`
- `SurfaceEffects`
- `AnimationStateMachine`
- `AnimationTransitionMode`
- `ObjectPool`
- `VectorPath`
- `SnapGrid`
- `AlignmentGuide`
- `SnapComposer`
- `SnapTarget`
- `WizardFlow`
- `WizardStep`
- `WizardHandle`
- `SceneTimeline`
- `Alignment`
- `PlacementResult`
- `PopupPlacement`
- `Side`
- `compute_popup_rect`
- `ParticleSystem`
- `Emitter`
- `ParticleLayer`
- `SpriteSheet`
- `FrameAnimation`
- `AnimatedImageControl`
- `CooperativeScheduler`
- `CoroutineHandle`
- `Pause`
- `Sleep`
- `WaitForEvent`
- `WaitForSignal`
- `WaitUntil`
- `WaitForAll`
- `TileSet`
- `TileMap`
- `ProgressBarControl`
- `FlowLayout`
- `FlowItem`
- `TextSearcher`
- `TextMatch`
- `ListDiffCalculator`
- `ListDiff`
- `DiffInsert`
- `DiffRemove`
- `DiffMove`
- `DataCache`
- `CacheStats`
- `ShortcutHelpOverlay`
- `ShortcutSection`
- `ShortcutEntry`
- `setup_standard_font_roles`
- `set_window_visible_state`
- `toggle_window_visibility`
This root-import export set is treated as an exact, locked public surface and is regression-tested.

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
- No Mandelbrot/demo symbols (`MandelStatusEvent`, `MANDEL_*`) are exported from the `gui_do` root import contract.

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
