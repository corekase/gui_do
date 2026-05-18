# gui_do Manual

This manual is the primary learning and reference document for `gui_do`. It teaches the framework from its data-driven entry points through the lower-level runtime systems that support scenes, features, controls, layout, persistence, and diagnostics. The document is organized so a new user can start from the public root exports and a maintainer can confirm behavior against the package contracts, runtime operating contracts, tests, and demo feature packages without treating internal implementation details as the public API.

## Table of Contents
[Back to Table of Contents](#table-of-contents)

- [Title and Purpose](#gui_do-manual)
- [Table of Contents](#table-of-contents)
- [How to Use This Manual](#how-to-use-this-manual)
- [Conceptual Foundations (Theory)](#conceptual-foundations-theory)
- [Quickstart Path (Practice)](#quickstart-path-practice)
- [Architecture and Runtime Model](#architecture-and-runtime-model)
- [Feature Organization Conventions](#feature-organization-conventions)
- [Core Workflow: Build, Bind, Route, Update, Draw](#core-workflow-build-bind-route-update-draw)
- [Main Systems Reference](#main-systems-reference)
- [8.1 Application Bootstrap and Host Configuration](#81-application-bootstrap-and-host-configuration)
- [8.2 Feature Lifecycle and Feature Types](#82-feature-lifecycle-and-feature-types)
- [8.3 Events, Actions, Input Mapping, and Routing](#83-events-actions-input-mapping-and-routing)
- [8.4 State and Observables](#84-state-and-observables)
- [8.5 Controls and Control Composition](#85-controls-and-control-composition)
- [8.6 Layout Systems](#86-layout-systems)
- [8.7 Focus and Accessibility](#87-focus-and-accessibility)
- [8.8 Overlays, Dialogs, Notifications, and Command Surfaces](#88-overlays-dialogs-notifications-and-command-surfaces)
- [8.9 Scene, Window, and Task-Panel Presentation Models](#89-scene-window-and-task-panel-presentation-models)
- [8.10 Scheduling, Timing, Animation, and Transitions](#810-scheduling-timing-animation-and-transitions)
- [8.11 Persistence and Workspace/Session State](#811-persistence-and-workspacesession-state)
- [8.12 Theme, Styling, and Visual Systems](#812-theme-styling-and-visual-systems)
- [8.13 Text, Input, Forms, and Validation Systems](#813-text-input-forms-and-validation-systems)
- [8.14 Data and Dataflow Helpers](#814-data-and-dataflow-helpers)
- [8.15 Graphics and Audio Integration Points](#815-graphics-and-audio-integration-points)
- [8.16 Telemetry, Introspection, and Operational Hooks](#816-telemetry-introspection-and-operational-hooks)
- [Integration Patterns and Composition Recipes](#integration-patterns-and-composition-recipes)
- [End-to-End Reference Application](#end-to-end-reference-application)
- [Testing, Diagnostics, and Reliability](#testing-diagnostics-and-reliability)
- [Performance and Scaling Guidance](#performance-and-scaling-guidance)
- [Migration, Versioning, and Deprecation Notes](#migration-versioning-and-deprecation-notes)
- [FAQ and Troubleshooting](#faq-and-troubleshooting)
- [Appendix](#appendix)
- [Appendix A: Glossary](#appendix-a-glossary)
- [Appendix B: Lifecycle and Event Sequence](#appendix-b-lifecycle-and-event-sequence)
- [Appendix C: System Dependency Map](#appendix-c-system-dependency-map)
- [Appendix D: API Quick Index](#appendix-d-api-quick-index)
- [Appendix D.1: Tier Matrix](#appendix-d1-tier-matrix)
- [Appendix D.2: Selection Heuristics](#appendix-d2-selection-heuristics)
- [Appendix E: Architecture Templates](#appendix-e-architecture-templates)
- [Appendix F: Specifications and Option Reference](#appendix-f-specifications-and-option-reference)

## How to Use This Manual
[Back to Table of Contents](#table-of-contents)

Read this document in one of three modes. The learning path starts with theory and then moves through the data-driven runtime surface in the same order that a real application is assembled. The build path starts from the Tier 1 entry points and the scene-level specs you actually declare in application code. The maintenance path treats the root package exports, contract documents, and tests as the normative evidence for whether the manual still matches the code.

The manual uses three recurring lenses. The control-plane lens explains the declarative objects you author, such as `HostApplicationBindingSpec`, `FeatureSpec`, `SceneSetupSpec`, `WindowSpec`, `ActionSpec`, and the growing family of routed runtime sibling specs. The runtime-plane lens explains which managers, registries, and orchestrators realize those declarations once the host application is built. The lifecycle lens explains when the framework creates structure, binds runtime resources, performs per-frame work, and tears everything down safely.

### Reading Paths

If you are new to the framework, read Section 4, Section 5, Section 6, Section 7, and then the system chapters in order. That path builds the mental model before it asks you to memorize APIs. If you already have an application in progress, start with Section 5 and Section 7, then jump directly to the system chapters you are using. If you maintain the framework or regenerate this manual, use Section 11 together with Appendix D, Appendix D.1, Appendix F, `docs/public_api_spec.md`, `docs/runtime_operating_contracts.md`, and the contract-oriented tests under `tests/`.

### Tri-Lens Markers

Throughout the manual, conceptual explanations distinguish between declaration, realization, and lifecycle ownership. When a chapter discusses specs, factory helpers, or package-root imports, treat that as control-plane guidance. When it discusses managers such as `ActionManager`, `CommandPaletteManager`, `WorkspacePersistenceManager`, or `FeatureOperationBus`, treat that as runtime-plane guidance. When it discusses `build`, `bind_runtime`, `on_update`, `draw`, and `shutdown_runtime`, treat that as lifecycle guidance. This separation matters because `gui_do` is intentionally declarative at the application-assembly boundary and imperative inside the behavior of an individual feature.

### Contract Alignment

The package root is the supported consumer import surface. The root export tiers in `gui_do/__init__.py` define what should be taught as public API, while `docs/public_api_spec.md` defines the stability policy and `docs/runtime_operating_contracts.md` defines measurable runtime guarantees such as scheduler budget clamping and workspace restore report fields. `docs/architecture_boundary_spec.md` defines the library-versus-demo import boundary. When prose in this manual and a contract document appear to differ, treat the current code and the contract documents as authoritative and update the manual accordingly.

### Learn, Build, Maintain

To learn `gui_do`, focus on the conceptual chapters and the first half of the system reference. To build with it, stay close to Tier 1 and Tier 2 exports and use the demo feature packages as evidence for package organization and spec composition. To maintain it, verify every manual claim against one of four sources: the package root exports, the contract documents, the tests, or a demo feature package that exercises the same behavior. This discipline keeps the document from drifting into historical or speculative guidance.
Reliability in `gui_do` is enforced by a mix of contract tests, behavior-focused runtime tests, and operational diagnostics. The key distinction is that contract tests protect the supported framework guarantees, while the broader runtime tests protect concrete control, scene, overlay, scheduler, persistence, and demo behavior that users are likely to depend on in practice.

### Contract Tests

The highest-priority contract command is:

```bash
python -m pytest -q tests/test_public_api_exports.py tests/test_public_api_docs_contracts.py tests/test_runtime_operating_contracts.py tests/test_boundary_contracts.py tests/test_gui_application_workspace_contracts.py
```

### Contract Tests

The highest-priority contract command is the one above. `tests/test_public_api_exports.py` verifies that the supported root export surface remains importable. `tests/test_public_api_docs_contracts.py` checks that published API documentation and contracts match the code. `tests/test_runtime_operating_contracts.py` protects runtime guarantees such as scheduler budgeting, scene isolation, normalized dispatch, and deterministic ordering. `tests/test_boundary_contracts.py` guards the framework and demo boundary. `tests/test_gui_application_workspace_contracts.py` validates application-facing workspace save and restore behavior.

### Runtime Behavior Tests

The wider suite covers the areas where application regressions usually emerge first: workspace load and save behavior, overlay, tooltip, cursor, and palette routing, layout determinism, animation and scheduler semantics, accessibility trees and specs, and control runtime behavior. Runtime-facility coverage matters here as well: service registration and cleanup, effect registration and disposal, operation retry and timeout behavior, failure publication behavior, and routed teardown guarantees should be treated as release-critical behaviors.

### Debug and Trace Tools

`EventRecorder`, `EventPlayback`, and `RecordedEvent` support reproducible input traces when an interaction bug is hard to reproduce manually. `DebugOverlay` gives live visual state inspection for geometry and rendering paths. `PropertyInspectorPanel`, `PropertyInspectorModel`, and `SceneSpatialIndex` help localize structural bugs in the live UI tree. The telemetry path, especially `analyze_telemetry_log_file()`, `analyze_telemetry_records()`, and `render_telemetry_report()`, is the first place to look when frame-time or pipeline regressions are suspected.

### Maintainer Release Runbook

1. Run the high-priority contract tests.
2. Run the broader runtime tests that cover the systems touched by the change.
3. Validate demo assumptions against the current demo configuration and feature packages.
4. Check the root export inventory against Appendix D and Appendix D.1.
5. Re-read the runtime contracts for any changed guarantees, restore fields, or performance budgets.
6. Re-check the boundary rule that `gui_do/` does not import `demo_features/` and that consumer entrypoints import from the root package.
7. Record any unresolved upgrade ambiguity in the migration section instead of leaving it implicit.

### Regression Triage Workflow

The fastest reliable triage path is reproduce, trace, localize, test first, patch, and then re-check adjacent contracts. Reproduce the issue with the smallest scene or test surface that still fails. Capture a trace or telemetry sample if routing or timing is involved. Localize the failure to one controlling abstraction instead of scanning the whole stack. Add or update the narrowest test that expresses the defect. Patch the owning slice. Then rerun adjacent contract tests so a local fix does not silently violate a broader runtime guarantee.

[Back to Table of Contents](#table-of-contents)

## Performance and Scaling Guidance
[Back to Table of Contents](#table-of-contents)

Performance work in `gui_do` is usually about bounding work, not chasing isolated micro-optimizations. The runtime contracts already define one of the most important limits: scheduler dispatch budgeting is clamped to `0.12` of dt milliseconds, with a `0.5 ms` floor and a `4.0 ms` ceiling. That gives a predictable upper bound during slow frames while still preventing starvation when frames are very fast.

`DirtyRegionTracker` is the framework's primary draw-cost gate for complex scenes. Its incremental union cache means `overlaps_dirty()` does not need to rescan the full dirty-rect set for each query, which keeps overlap checks cheap in large scenes. When a surface or region is expensive to redraw, use dirty-region gating and, when needed, offscreen render targets so unchanged regions are simply reused.

For large collections, prefer `VirtualizationCore`, `VirtualizedWindow`, and `RecyclePool` over keeping every row or cell live. For collection mutation, `ListDiffCalculator` should usually drive incremental updates instead of whole-list redraws. For high-churn allocations, `ObjectPool` is the intended pressure-relief valve. For expensive searches, form validation, or staged transforms, combine `Debouncer` or `Throttler` with `DataflowPipeline` and `CancellationToken` so the system can discard stale work instead of completing it uselessly.

The practical scaling checklist is straightforward: keep updates scene-scoped, avoid per-frame whole-collection reallocation, debounce expensive user-driven work, make background transforms preemptible, profile representative interactions instead of idle loops, and gate expensive draw regions with dirty tracking wherever possible.

[Back to Table of Contents](#table-of-contents)

## Migration, Versioning, and Deprecation Notes
[Back to Table of Contents](#table-of-contents)

The versioned snapshot path is the recommended upgrade strategy. Write snapshots with `make_snapshot(current_version, state_dict)`. On load, inspect the stored version with `read_version()`. Pass the result through `SnapshotMigrator.migrate()` so registered `MigrationStep` objects can advance the snapshot through the available migration graph. Then restore the migrated state into the runtime. `MigrationRegistry` owns the one-directional steps, and `MigrationError` is the signal that no valid migration path exists.

Deprecation should be handled additively whenever possible. Prefer adding fields or parameters and keeping older behavior available long enough for a migration path to exist. Remove legacy behavior only after a documented migration path exists and the affected examples, tests, and appendices have been updated. No formal deprecated public APIs are cataloged in this manual at generation time; when formal deprecations are introduced, this section should become the canonical record.

The practical upgrade checklist is to run the contract tests before and after the upgrade, verify root-import consumer usage, re-check action, input, and focus routing in active scenes, inspect workspace restore reports for skipped or missing settings, rerun telemetry baselines, and update examples or docs that describe routed runtime so they use current service, effect, operation, and failure-policy terminology.

[Back to Table of Contents](#table-of-contents)

## FAQ and Troubleshooting
[Back to Table of Contents](#table-of-contents)

**Should I build apps directly with controls or with features?**

Use features as the architectural unit. Controls are the implementation surface inside those boundaries. A feature gives you lifecycle phases, scene membership, runtime wiring, teardown, and a natural place for observables, services, and routed actions. Controls alone do not provide those coordination guarantees.

**When should I use `RoutedFeature` over `Feature`?**

Use `RoutedFeature` when the feature needs declarative runtime wiring such as hotkeys, overlays, subscriptions, task-panel toggles, or topic-based message dispatch. Plain `Feature` is still correct when the behavior is structurally simple and does not benefit from the routed runtime bundle.

**Why are some key handlers not firing?**

Check focus ownership first. Then check whether the action or binding is scene-scoped or window-scoped and whether the relevant window is visible. Then check whether an overlay, dialog, or palette is consuming the key first. If routing is still unclear, capture the interaction with `EventRecorder` and inspect the resulting path instead of guessing.

**Why do toast clicks not pass through?**

Toast bounds intentionally consume left-click events so underlying controls are not activated accidentally through transient notifications. If the toast itself should respond, attach explicit toast click handling instead of relying on pass-through behavior.

**How do I avoid breaking workspace restore across versions?**

Use versioned snapshots, register migration steps for every schema change, and inspect the restore report instead of assuming a full replay. `skipped_settings` and `missing_settings_blocks` are designed to surface compatibility drift without aborting the whole restore.

**How do I confirm my API usage is within the supported surface?**

Prefer explicit imports from the `gui_do` root and verify them with the contract tests. The manual treats the root package as the supported consumer surface, and Appendix D indexes that surface directly.

**Why does my feature's `bind_runtime()` appear to run before a sibling's `build()`?**

That ordering is not the intended contract. All features in a scene should complete `build()` before any of them enter `bind_runtime()`. If you see a mismatch, verify that the features are actually declared in the same scene and that the issue is not caused by late-created presentation surfaces.

**How do I add a keyboard shortcut without touching every location where that key is handled?**

Declare an action and bind it through the action or routed-runtime surface. That keeps the shortcut registered in one place and lets the action registry, input map, and optional shortcut overlay stay consistent.

[Back to Table of Contents](#table-of-contents)

## Appendix
[Back to Table of Contents](#table-of-contents)

### Appendix A: Glossary
[Back to Table of Contents](#table-of-contents)

**Feature**

A feature is the framework's lifecycle-managed behavior unit. `Feature`, `DirectFeature`, `LogicFeature`, and `RoutedFeature` share the same lifecycle idea but emphasize different execution surfaces. The key value is not inheritance variety by itself; it is the guarantee that structure, runtime wiring, event handling, update work, drawing, and teardown all happen in a deterministic framework-managed order.

**Spec**

A spec is a declarative data object that describes runtime wiring instead of performing it immediately. The spec graph is how bootstrap, scene composition, routed runtime setup, overlays, action bindings, and higher-level faculties stay inspectable and reproducible.

**Host**

The host is the plain Python object passed through bootstrap and then populated with runtime members. It is intentionally not a heavyweight inheritance root. The framework attaches the application runtime, managers, and configured members to it so features can depend on stable attributes without dict-driven plumbing.

**Scene**

A scene is the top-level interaction context. Features belong to one scene at a time. Scene transitions therefore change the active feature set, active presentation surfaces, and scene-scoped routing behavior in one coordinated move.

**Window presentation**

Window presentation is the model that determines which floating or anchored windows exist in a scene, which are visible, how their toggles are exposed, and how focus and scene chrome react to visibility changes.

**Routed runtime**

Routed runtime is the declarative bundle of hotkeys, overlays, subscriptions, effects, service hooks, operation bindings, palette bindings, and related runtime facilities that a feature can own through one spec-driven lifecycle.

**Observable**

An observable is a value or collection that notifies subscribers when it changes. In `gui_do`, observables are the primary reactive glue between feature state and UI state, and they work best when their subscriptions are owned by lifecycle-aware runtime scopes.

**Workspace state**

Workspace state is the persisted runtime context used for session restore. It includes scene choice, scene snapshots, feature state, settings blocks, metadata, and optionally dock layout so a later session can reconstruct the working surface.

**Contract test**

A contract test protects framework-level guarantees rather than incidental implementation details. These tests are the closest thing to an executable stability policy and should be treated as part of the supported surface, not as ordinary regression tests.

**Tier**

A tier is a public API grouping in `gui_do/__init__.py`. Tiers are documentation and selection signals: start at the highest-level stable surface that solves the problem, then descend only when you need finer control.

**Runtime scope**

Runtime scope is the lifecycle-owned container that tracks cleanup, subscriptions, services, and other teardown-sensitive runtime objects. It is what keeps bind and shutdown logic symmetric without manual unsubscribe and dispose lists scattered across a feature.

**Feature operation**

A feature operation is a declarative operation handler bound through runtime specs. It lets a feature expose named work with explicit context, retry, timeout, and failure-publication behavior instead of burying that logic in ad hoc callbacks.

**Failure policy**

Failure policy is the runtime rule set that governs retry, timeout, and failure publication for declaratively bound operations. It turns error handling into owned runtime behavior instead of unstructured exception branching.

[Back to Table of Contents](#table-of-contents)

### Appendix B: Lifecycle and Event Sequence
[Back to Table of Contents](#table-of-contents)

1. `bootstrap_host_application()` initializes the host from config specs.
2. Scene and feature declarations are resolved into the runtime graph.
3. All feature `build(host)` calls complete before runtime binding begins.
4. All active feature `bind_runtime(host)` calls run.
5. The runtime loop starts.
6. Raw pygame events are normalized into `GuiEvent` instances.
7. Overlay, focus, window, and scene routing is applied in the app dispatch path.
8. Feature `handle_event()` calls run in routing order.
9. Per-frame update work runs, including scheduler dispatch and timed work.
10. Feature `draw()` calls and control-tree drawing produce the frame.
11. Scene transitions shut down departing runtime, then build and bind arriving features.
12. Application exit triggers final runtime shutdown and optional workspace save behavior.

[Back to Table of Contents](#table-of-contents)

### Appendix C: System Dependency Map
[Back to Table of Contents](#table-of-contents)

Bootstrap is the top structural layer. It depends on the spec vocabulary, feature lifecycle, scene and window presentation, action and input registration, and theme and font configuration because all of those are assembled before the runtime loop becomes meaningful.

Feature lifecycle depends on the control tree, reactive state, event routing, and scene ownership rules. Layout and focus both sit downstream of the control tree and presentation model because visibility and containment determine which nodes can be measured or focused at all.

Overlays depend on event routing and focus policy because they are meaningful only when they can intercept or redirect input ahead of background surfaces. Persistence depends on registered scenes, feature state boundaries, and settings registries. Scheduling and animation depend on the per-frame update loop and scene-local runtime ownership.

Telemetry and introspection cross-cut almost everything: they do not own the main runtime path, but they inspect and measure it. Audio depends on the mixer layer and semantic event publication. Service scope is the broad dependency container that can support features or advanced runtime facilities at almost any tier.

[Back to Table of Contents](#table-of-contents)

### Appendix D: API Quick Index
[Back to Table of Contents](#table-of-contents)

This index follows the public root organization from `gui_do/__init__.py`. Names are grouped once by topic. Tiers 20-24 are imported by the root module but omitted from `__all__` at generation time; they are listed here because they are still part of the discovered root-topic layout.

#### Bootstrap and Data-Driven Specs

`Feature`, `DirectFeature`, `LogicFeature`, `RoutedFeature`, `FeatureMessage`, `FeatureManager`, `ScenePresentationModel`, `SceneSetupSpec`, `setup_standard_font_roles`, `FeatureSpec`, `WindowSpec`, `RuntimeSceneSpec`, `ActionSpec`, `StaticAccessibilitySpec`, `CursorSpec`, `SceneRootSpec`, `AnchoredWindowSpec`, `LogicBindingSpec`, `TaskPanelButtonSpec`, `TaskPanelWindowToggleGroupSpec`, `PaletteInputBindSpec`, `SceneCommandPaletteSpec`, `ActionHotkeySpec`, `ControlKeyBindingSpec`, `SceneTaskPanelSpec`, `TaskPanelSlotLayoutSpec`, `TaskPanelSceneNavButtonSpec`, `EventSubscriptionSpec`, `ServiceBindingSpec`, `ServiceConsumerSpec`, `StoreSubscriptionSpec`, `StoreSelectorSpec`, `ObservableEffectSpec`, `SignalEffectSpec`, `FailurePolicySpec`, `FeatureOperationSpec`, `ShortcutOverlaySpec`, `TaskPanelFocusToggleSpec`, `GlobalPointerActionSpec`, `FeatureDependencySpec`, `ExecutionContextSpec`, `WorkloadBudgetClassSpec`, `WorkloadBudgetSpec`, `CheckpointDomainSpec`, `CheckpointSpec`, `SagaStepSpec`, `SagaSpec`, `ReactiveSourceSpec`, `ReactiveNodeSpec`, `ReactiveGraphSpec`, `MigrationStepSpec`, `MigrationTargetSpec`, `ContractMigrationSpec`, `RuntimePolicySpec`, `EffectBindingSpec`, `EventPipelineStageSpec`, `EventPipelineSpec`, `DurableOperationBindingSpec`, `DurableOperationQueueSpec`, `DurableQueueRecord`, `CapabilityProviderSpec`, `CapabilityRequirementSpec`, `ProjectionNodeSpec`, `ProjectionSpec`, `PolicyDecision`, `WorkflowStepSpec`, `WorkflowSpec`, `RecomputeNodeSpec`, `QoSPolicySpec`, `HealthProbeSpec`, `ReplaySpec`, `ReplacePolicySpec`, `WorkflowCoordinator`, `RuntimePolicyEngine`, `EffectLifetimeOrchestrator`, `EventPipelineRuntime`, `DurableOperationQueueRuntime`, `CapabilityContractRuntime`, `ProjectionRuntime`, `RecomputeOrchestrator`, `QoSPolicyRuntime`, `FeatureHealthRuntime`, `RuntimeReplayHarness`, `FeatureHotSwapManager`, `ExecutionContextRuntime`, `WorkloadBudgetBrokerRuntime`, `CheckpointRecoveryRuntime`, `SagaCompensationRuntime`, `ReactiveDependencyGraphRuntime`, `ContractMigrationRuntime`, `RoutedRuntimeSpec`, `RoutedFeatureLifecycleSpec`, `FeatureWindowBundleBindingSpec`, `WindowToggleBindingSpec`, `SceneSetupBindingSpec`, `RuntimeSceneBindingSpec`, `SceneRootBindingSpec`, `CursorBindingSpec`, `FontRoleBindingSpec`, `ActionBindingSpec`, `PaletteBindingSpec`, `SceneBundleBindingSpec`, `HostApplicationBindingSpec`, `TabbedPresenterSpec`, `AccessibilitySequenceSpec`, `TabBuilderSpec`, `NotificationSpec`, `HostApplicationConfig`, `TelemetryConfig`, `bootstrap_host_application`, `build_notification_center`, `make_window_toggle_spec`, `make_scene_nav_action`, `make_exit_action`, `make_palette_toggle_action`, `make_static_accessibility_spec`, `build_feature_specs`, `build_feature_window_bundle_specs`, `build_window_toggle_specs`, `build_scene_setup_specs`, `build_runtime_scene_specs`, `build_scene_root_specs`, `build_cursor_specs`, `build_font_role_specs`, `build_scene_nav_actions`, `build_action_specs`, `build_scene_bundle_specs`, `build_static_accessibility_specs`, `build_host_application_config`, `FeatureOperationBus`, `FeatureOperationContext`, `FeatureOperationHandle`, `FeatureRuntimeScope`

#### Core Application and Scene Management

`GuiApplication`, `create_display`, `SceneTransitionManager`, `SceneTransitionStyle`, `apply_scene_setup_specs`

#### Reactive State and Presentation Models

`ObservableValue`, `PresentationModel`, `ComputedValue`, `InvalidationTracker`, `ChangeKind`, `CollectionChange`, `ObservableList`, `ObservableDict`, `CollectionViewQuery`, `CollectionView`, `Binding`, `BindingGroup`, `ObservableStream`, `SelectionModel`, `SelectionMode`

#### Events, Actions, Focus, and Input

`EventPhase`, `EventType`, `GuiEvent`, `ValueChangeCallback`, `ValueChangeReason`, `EventManager`, `EventBus`, `GestureRecognizer`, `EventRecorder`, `EventPlayback`, `RecordedEvent`, `InputSnapshot`, `Signal`, `SignalConnection`, `ActionManager`, `ActionContext`, `ActionMiddleware`, `ActionDescriptor`, `ActionRegistry`, `InputMap`, `InputBinding`, `KeyChordManager`, `KeyChord`, `ChordStep`, `FocusManager`, `FocusScope`, `FocusScopeManager`, `WindowFocusManager`, `FocusRing`

#### Scheduling and Animation

`TaskEvent`, `TaskScheduler`, `Timers`, `TweenManager`, `TweenHandle`, `Easing`, `AnimationSequence`, `AnimationHandle`, `TransitionManager`, `TransitionSpec`, `TransitionEvent`, `AnimationStateMachine`, `AnimationTransitionMode`, `SceneTimeline`, `Debouncer`, `Throttler`, `CooperativeScheduler`, `CoroutineHandle`, `Pause`, `Sleep`, `WaitForEvent`, `WaitForSignal`, `WaitUntil`, `WaitForAll`

#### Theme and Fonts

`FontManager`, `FontRoleRegistry`, `ColorTheme`, `ThemeManager`, `DesignTokens`, `ScopedTheme`, `ScopedThemeManager`

#### Telemetry and Diagnostics

`TelemetryCollector`, `TelemetrySample`, `configure_telemetry`, `telemetry_collector`, `analyze_telemetry_log_file`, `analyze_telemetry_records`, `load_telemetry_log_file`, `render_telemetry_report`

#### Layout and Spatial Systems

`LayoutAxis`, `ConstraintLayout`, `AnchorConstraint`, `DockPane`, `DockTabs`, `DockSplit`, `DockWorkspace`, `FlexLayout`, `FlexItem`, `FlexDirection`, `FlexAlign`, `FlexJustify`, `GridLayout`, `GridTrack`, `GridPlacement`, `LayoutAnimator`, `LayoutPass`, `MeasureContext`, `ArrangeContext`, `LayoutRoot`, `FlowLayout`, `FlowItem`, `Viewport`, `WindowLayoutHandler`

#### Overlays and Command Surfaces

`OverlayManager`, `OverlayHandle`, `Alignment`, `PlacementResult`, `PopupPlacement`, `Side`, `compute_popup_rect`, `DialogManager`, `DialogHandle`, `ToastManager`, `ToastHandle`, `ToastSeverity`, `ContextMenuManager`, `ContextMenuItem`, `ContextMenuHandle`, `CommandPaletteManager`, `CommandEntry`, `CommandPaletteHandle`, `TooltipManager`, `TooltipHandle`, `MenuBarManager`, `FileDialogManager`, `FileDialogOptions`, `FileDialogHandle`, `NotificationCenter`, `NotificationRecord`, `ResizeManager`, `CursorManager`, `CursorHandle`, `CursorShape`, `DragDropManager`, `DragPayload`, `ClipboardManager`, `TransferData`, `TransferManager`, `ShortcutHelpOverlay`, `ShortcutSection`, `ShortcutEntry`

#### Forms and Validation

`FormModel`, `FormField`, `ValidationRule`, `FieldError`, `FormSchema`, `SchemaField`, `DocumentModel`, `WizardFlow`, `WizardStep`, `WizardHandle`, `ValidationResult`, `Validator`, `RequiredValidator`, `RangeValidator`, `LengthValidator`, `PatternValidator`, `CustomValidator`, `DependentValidator`, `ValidationPipeline`, `AsyncFieldValidator`, `AsyncFormValidator`, `FieldSchema`, `FieldGraphSchema`, `ValidationPolicy`, `SchemaFormRuntime`

#### State, Persistence, and Migration

`CommandHistory`, `Command`, `CommandTransaction`, `StateMachine`, `HierarchicalStateMachine`, `Router`, `RouteEntry`, `SettingsRegistry`, `SettingDescriptor`, `WorkspaceState`, `WorkspacePersistenceManager`, `DEFAULT_WORKSPACE_STATE_PATH`, `SceneSnapshot`, `NodeSnapshot`, `SchemaVersion`, `VersionedSnapshot`, `MigrationStep`, `MigrationRegistry`, `SnapshotMigrator`, `MigrationError`, `make_snapshot`, `read_version`

#### Primary Controls

`PanelControl`, `LabelControl`, `ButtonControl`, `ToggleControl`, `SliderControl`, `ScrollbarControl`, `CanvasControl`, `CanvasEventPacket`, `CanvasViewport`, `FrameControl`, `ImageControl`, `ArrowBoxControl`, `ButtonGroupControl`, `TabControl`, `TabItem`, `DockWorkspacePanel`

#### Extended Controls and Presentation Surfaces

`TextInputControl`, `TextAreaControl`, `RichLabelControl`, `DropdownControl`, `DropdownOption`, `ListViewControl`, `ListItem`, `OverlayPanelControl`, `DataGridControl`, `GridColumn`, `GridRow`, `TreeControl`, `TreeNode`, `SplitterControl`, `SpinnerControl`, `RangeSliderControl`, `ColorPickerControl`, `ScrollViewControl`, `ProgressBarControl`, `AnimatedImageControl`, `ErrorBoundary`, `WindowControl`, `TaskPanelControl`, `WindowPresenter`, `MenuStripControl`, `MenuEntry`, `SceneMenuOptions`, `WindowMenuOptions`, `NotificationPanelControl`, `PropertyInspectorPanel`, `ToolbarControl`, `ToolbarItem`, `StatusBarControl`, `StatusSlot`, `ExpanderControl`, `DatePickerControl`, `TimePickerControl`, `BreadcrumbControl`, `BreadcrumbItem`, `SplitButtonControl`, `SplitButtonOption`, `ChipInputControl`

#### Text and Localization

`TextFormatter`, `NumericFormatter`, `PatternFormatter`, `FixedPatternFormatter`, `TextFlow`, `TextSpan`, `TextSearcher`, `TextMatch`, `StringTable`, `LocaleRegistry`

#### Data and Collections

`VirtualItemSource`, `FixedItemSource`, `SortFilterProxySource`, `AsyncDataProvider`, `LoadState`, `LoadStateKind`, `ObjectPool`, `DataCache`, `CacheStats`, `ListDiffCalculator`, `ListDiff`, `DiffInsert`, `DiffRemove`, `DiffMove`

#### Graphics and Rendering

`BuiltInGraphicsFactory`, `DirtyRegionTracker`, `DrawContext`, `DrawPhase`, `AssetRegistry`, `DebugOverlay`, `SurfaceCompositor`, `Layer`, `ShapeRenderer`, `SurfaceEffects`, `VectorPath`, `SpriteSheet`, `FrameAnimation`, `ParticleSystem`, `Emitter`, `ParticleLayer`, `TileSet`, `TileMap`, `RenderTarget`, `LiveRenderTarget`, `OffscreenRenderTarget`, `create_render_target`, `create_surface`, `Node2D`, `SceneGraph2D`, `Camera2D`

#### Introspection and Inspection

`SceneSpatialIndex`, `ui_property`, `PropertyDescriptor`, `PropertyRegistry`, `property_registry`, `PropertyInspectorModel`, `InspectedProperty`

#### Advanced Runtime and Bootstrap Extensions

`FrameTimer`, `TabPanelManager`, `WindowRelativeRect`, `resolve_scene_selection_callback`, `minimize_window_menu_entries`, `set_window_visible_state`, `toggle_window_visibility`, `create_anchored_feature_window`, `add_window_menu_strip`, `split_slot_bounds`, `place_control`, `place_control_unlabeled`, `register_placed_control`, `add_group_label`, `PlacedControl`, `make_labeled_slot_height_fn`, `apply_category_visibility`, `ControlRegistry`, `RowCellSpec`, `build_horizontal_row_specs`, `build_multi_column_grid_specs`, `build_tools_menu_entries`, `add_standard_menu_strip`, `add_menu_strip_from_spec`, `apply_accessibility_sequence`, `apply_accessibility_sequence_from_attrs`, `register_companion_logic_features`, `ensure_scene_scheduler`, `sorted_window_bindings`, `collect_window_toggle_controls`, `apply_window_toggle_accessibility`, `add_window_toggle_task_panel_controls`, `add_task_panel_window_toggle_group`, `setup_scene_command_palette_bindings`, `register_window_toggle_tooltips`, `initialize_locale_registry`, `bind_input_map_actions`, `register_descriptors`, `resolve_canvas_local_point`, `apply_runtime_scene_pristine_assets`, `bind_runtime_scene_exit_keys`, `prewarm_runtime_scenes`, `add_task_panel_button`, `add_task_panel_buttons`, `register_tooltip_specs`, `register_action_hotkeys`, `register_global_pointer_actions`, `draw_controls_prewarm`, `bind_palette_window_action_bind`, `ensure_scene_task_panel`, `create_task_panel_slot_layout`, `add_task_panel_scene_nav_button`, `add_scene_task_panel_items`, `centered_overlay_rect`, `create_shortcut_help_overlay`, `bind_feature_event_subscription`, `unbind_feature_event_subscription`, `setup_routed_runtime`, `shutdown_routed_runtime`, `bind_task_panel_focus_toggle`, `add_window_control`, `add_window_label`, `add_window_button`, `add_window_button_row`, `instantiate_features_from_specs`, `register_features_from_specs`, `register_window_presentation_specs`, `register_window_tab_builders`, `build_tab_builder_specs`, `create_tab_control_from_specs`, `compute_tabbed_window_layout`, `setup_feature_presenter_tabs_from_window_content`, `register_window_tab_builder_specs`, `setup_feature_presenter_tabs`, `register_tab_update_handlers`, `create_presented_anchored_window`, `create_presented_window_from_spec`, `create_feature_presented_window`, `configure_routed_feature_runtime`, `register_routed_feature_companions`, `bind_routed_feature_lifecycle`, `shutdown_routed_feature_lifecycle`, `ActiveTabUpdateRouter`, `TabLayoutContext`, `declare_host_actions`, `build_host_main_tab_order`, `apply_host_main_accessibility`

#### Infrastructure Internals

`UiEngine`

#### Audio

`SoundCue`, `SoundBankRegistry`, `SoundEventBus`

#### Accessibility

`AccessibilityRole`, `LivePoliteness`, `AccessibilityNode`, `AccessibilityTree`, `AccessibilityAnnouncement`, `AccessibilityBus`

#### Theme Invalidation

`ThemeInvalidationBus`

#### Undo Routing

`UndoContextManager`

#### Service Scope

`ServiceKey`, `ServiceScope`, `ScopeStack`

#### Dataflow Pipeline

`CancellationToken`, `PipelineStage`, `DataflowPipeline`, `PipelineHandle`

#### Transactional App State Store

`AppStateStore`, `StateSelector`, `StateTransaction`

#### Adaptive Constraint Layout

`ConstraintAttr`, `LayoutConstraint`, `ConstraintSet`, `AdaptivePolicy`, `resolve_adaptive_policy`

#### Virtualization

`MeasureMode`, `MeasurePolicy`, `VirtualizedWindow`, `RecyclePool`, `VirtualizationCore`

#### Interaction State Machine

`InteractionPhase`, `InteractionContext`, `InteractionTransition`, `InteractionStateMachine`

[Back to Table of Contents](#table-of-contents)

### Appendix D.1: Tier Matrix
[Back to Table of Contents](#table-of-contents)

| Tier | System | Representative names |
| --- | --- | --- |
| 1 | PRIMARY ENTRY POINTS & DATA-DRIVEN APIs | `Feature`, `HostApplicationBindingSpec`, `RoutedRuntimeSpec`, `FeatureWindowBundleBindingSpec`, `bootstrap_host_application` |
| 2 | CORE APPLICATION & SCENE MANAGEMENT | `GuiApplication`, `create_display`, `SceneTransitionManager`, `SceneTransitionStyle`, `apply_scene_setup_specs` |
| 3 | ESSENTIAL DATA & STATE MANAGEMENT | `ObservableValue`, `ComputedValue`, `CollectionView`, `BindingGroup`, `SelectionModel` |
| 4 | EVENTS, ACTIONS, FOCUS & INPUT | `GuiEvent`, `ActionRegistry`, `InputMap`, `FocusManager`, `KeyChordManager` |
| 5 | SCHEDULING & ANIMATION | `TaskScheduler`, `TweenManager`, `AnimationStateMachine`, `SceneTimeline`, `CooperativeScheduler` |
| 6 | THEME & FONT MANAGEMENT | `FontManager`, `FontRoleRegistry`, `ThemeManager`, `DesignTokens`, `ScopedThemeManager` |
| 7 | TELEMETRY & DIAGNOSTICS | `TelemetryCollector`, `configure_telemetry`, `analyze_telemetry_records`, `load_telemetry_log_file`, `render_telemetry_report` |
| 8 | LAYOUT & SPATIAL | `ConstraintLayout`, `DockWorkspace`, `FlexLayout`, `GridLayout`, `WindowLayoutHandler` |
| 9 | OVERLAY MANAGERS & WINDOWS | `OverlayManager`, `DialogManager`, `ToastManager`, `CommandPaletteManager`, `ShortcutHelpOverlay` |
| 10 | FORMS & DATA BINDING | `FormModel`, `FormSchema`, `DocumentModel`, `WizardFlow`, `ValidationPipeline` |
| 11 | STATE & PERSISTENCE | `CommandHistory`, `Router`, `SettingsRegistry`, `WorkspacePersistenceManager`, `SceneSnapshot` |
| 12 | PRIMARY CONTROLS (BASIC UI BUILDING BLOCKS) | `PanelControl`, `ButtonControl`, `CanvasControl`, `TabControl`, `DockWorkspacePanel` |
| 13 | EXTENDED CONTROLS (SPECIALIZED UI COMPONENTS) | `TextInputControl`, `ListViewControl`, `WindowControl`, `MenuStripControl`, `ChipInputControl` |
| 14 | TEXT & LOCALIZATION | `TextFormatter`, `TextFlow`, `TextSearcher`, `StringTable`, `LocaleRegistry` |
| 15 | DATA & COLLECTIONS | `VirtualItemSource`, `SortFilterProxySource`, `AsyncDataProvider`, `DataCache`, `ListDiffCalculator` |
| 16 | GRAPHICS & RENDERING | `DirtyRegionTracker`, `DrawContext`, `SurfaceCompositor`, `ParticleSystem`, `SceneGraph2D` |
| 17 | INTROSPECTION & INSPECTION | `SceneSpatialIndex`, `ui_property`, `PropertyRegistry`, `PropertyInspectorModel`, `InspectedProperty` |
| 18 | ADVANCED RUNTIME & BOOTSTRAPPING | `set_window_visible_state`, `add_standard_menu_strip`, `ensure_scene_task_panel`, `create_feature_presented_window`, `ActiveTabUpdateRouter` |
| 19 | INFRASTRUCTURE & INTERNALS (AVOID IN APPLICATION CODE) | `UiEngine` |
| 20 | AUDIO | `SoundCue`, `SoundBankRegistry`, `SoundEventBus` |
| 21 | ACCESSIBILITY | `AccessibilityRole`, `AccessibilityNode`, `AccessibilityTree`, `AccessibilityAnnouncement`, `AccessibilityBus` |
| 22 | THEME INVALIDATION | `ThemeInvalidationBus` |
| 23 | UNDO CONTEXT ROUTING | `UndoContextManager` |
| 24 | ASYNC FORM VALIDATION | `AsyncFieldValidator`, `AsyncFormValidator` |
| 25 | SCOPED SERVICE GRAPH | `ServiceKey`, `ServiceScope`, `ScopeStack` |
| 26 | CANCELABLE DATAFLOW PIPELINE | `CancellationToken`, `PipelineStage`, `DataflowPipeline`, `PipelineHandle` |
| 27 | TRANSACTIONAL APP STATE STORE | `AppStateStore`, `StateSelector`, `StateTransaction` |
| 28 | ADAPTIVE CONSTRAINT LAYOUT v2 | `ConstraintAttr`, `LayoutConstraint`, `ConstraintSet`, `AdaptivePolicy`, `resolve_adaptive_policy` |
| 29 | UNIFIED VIRTUALIZATION CORE | `MeasureMode`, `MeasurePolicy`, `VirtualizedWindow`, `RecyclePool`, `VirtualizationCore` |
| 30 | INTERACTION STATE MACHINE FRAMEWORK | `InteractionPhase`, `InteractionContext`, `InteractionTransition`, `InteractionStateMachine` |
| 31 | SCHEMA-DRIVEN FORM RUNTIME | `FieldSchema`, `FieldGraphSchema`, `ValidationPolicy`, `SchemaFormRuntime` |
| 32 | PORTABLE SNAPSHOT & MIGRATION LAYER | `SchemaVersion`, `VersionedSnapshot`, `MigrationStep`, `SnapshotMigrator`, `read_version` |

[Back to Table of Contents](#table-of-contents)

### Appendix D.2: Selection Heuristics
[Back to Table of Contents](#table-of-contents)

1. Start at Tier 1. If `HostApplicationConfig`, `bootstrap_host_application()`, the feature types, and the spec vocabulary solve the problem, stop there.
2. Descend one tier at a time only when you need finer control than the higher-level surface provides.
3. Use Tier 18 when you are extending or customizing bootstrap and routed runtime behavior rather than replacing it.
4. Use explicit imports from the `gui_do` root in application code rather than submodule imports.
5. Avoid Tier 19 in application code; it is documented as infrastructure internals.

Useful shortcuts are consistent. Need app setup: use the bootstrap surface. Need cross-feature runtime behavior: use lifecycle specs and routed runtime helpers. Need large-data UI: use virtualization and dataflow APIs before building a custom loop. Need maintainable persistence: use `WorkspacePersistenceManager` plus `SnapshotMigrator`. Need discoverable shortcuts: declare actions and expose them through `ShortcutOverlaySpec` or command-surface helpers.

[Back to Table of Contents](#table-of-contents)

### Appendix E: Architecture Templates
[Back to Table of Contents](#table-of-contents)

**Template 1: Small Single-Scene App**

Use one scene, a handful of `Feature` instances, local observable state, and a small action set. This is the right shape when the application does not need floating windows or multiple scene contexts.

**Template 2: Multi-Window Workbench**

Use multiple scenes or one workbench scene with a unified menu strip, `SceneTaskPanelSpec`, presenter-backed windows, and `TaskPanelFocusToggleSpec`. This is the reference shape for tooling-style applications.

**Template 3: Data-Heavy Analysis Tool**

Use `AsyncDataProvider`, `SortFilterProxySource`, `VirtualizationCore`, `DataflowPipeline`, dirty-region rendering, and telemetry baselines. This is the correct shape when list or grid scale would otherwise dominate runtime cost.

**Template 4: Long-Running Workflow App**

Use `CooperativeScheduler` for multi-step work, expose progress through observables, use `WizardFlow` for guided input, and persist versioned workspace state with migration support.

[Back to Table of Contents](#table-of-contents)

### Appendix F: Specifications and Option Reference
[Back to Table of Contents](#table-of-contents)

This appendix is the concise practical index for the framework's spec families. Spec-heavy sections in this manual should be read with this appendix nearby.

#### Bootstrap and Scene Composition Specs

`HostApplicationBindingSpec`: top-level bootstrap input. Key options include display size, window title, initial scene name, font config, scene bundles, feature specs, action specs, cursor specs, accessibility specs, telemetry config, and related root declarations. See chapters 8.1, 8.3, and 8.9.

`HostApplicationConfig`: built config object produced by `build_host_application_config()`. Use it as the validated bootstrap payload passed to `bootstrap_host_application()`. See chapter 8.1.

`SceneBundleBindingSpec`: bundle-oriented scene declaration. It groups scene setup, runtime scene behavior, scene navigation, and optional scene roots so one declaration can emit the needed sub-specs. See chapters 6 and 8.1.

`FeatureSpec`: declarative feature entry. Its key fields identify the feature factory, scene, and structural placement context. See chapters 5, 6, and 8.2.

`SceneSetupSpec`, `RuntimeSceneSpec`, and `SceneRootSpec`: scene-level structural and runtime declarations. Use them to separate scene structure from per-scene runtime facilities and root-node ownership. See chapters 8.1 and 8.9.

#### Action, Input, and Overlay Specs

`ActionSpec` and `ActionBindingSpec`: declare named actions, labels, categories, and kind-specific behavior such as exit or palette toggling. Use them when behavior should be named and rebindable. See chapter 8.3.

`ActionHotkeySpec` and `ControlKeyBindingSpec`: bind keys to actions or controls with scene and visibility scope. Use them instead of scattering raw key checks through features. See chapter 8.3.

`ShortcutOverlaySpec`: declares a help-overlay owner, toggle action, optional key, filtering rules, and manual shortcut sections. Use it when discoverable shortcuts are part of the runtime contract. See chapter 8.8.

`NotificationSpec`: declarative notification-center entry used during bootstrap. Use it when a notification surface should be configured structurally instead of ad hoc at runtime. See chapters 8.1 and 8.8.

#### Window and Presentation Specs

`WindowSpec` and `AnchoredWindowSpec`: declarative window shape and placement specs. `AnchoredWindowSpec` adds anchoring semantics and chrome-related placement details for presenter-backed or feature-backed windows. See chapter 8.9.

`FeatureWindowBundleBindingSpec` and `WindowToggleBindingSpec`: bind feature-owned windows to scene presentation, toggles, and related chrome. Use them when a feature should bring its window behavior with it as a single declaration. See chapter 8.9.

`SceneTaskPanelSpec`, `TaskPanelButtonSpec`, `TaskPanelSlotLayoutSpec`, `TaskPanelWindowToggleGroupSpec`, `TaskPanelSceneNavButtonSpec`, and `TaskPanelFocusToggleSpec`: task-panel composition vocabulary. These specs control panel composition, slot order, scene-nav buttons, window-toggle groups, and focus inclusion when windows are shown or hidden. See chapters 8.8 and 8.9.

`TabbedPresenterSpec` and `TabBuilderSpec`: presenter-tab declarations. Use them when one presenter-backed window should host multiple tabbed content surfaces with stable builder wiring. See chapter 8.9.

#### Routed Runtime and Higher-Level Runtime Specs

`RoutedRuntimeSpec`: the central runtime bundle for hotkeys, overlays, subscriptions, store selectors, effects, service hooks, operations, palette bindings, and presentation toggles. Use it whenever a feature's runtime wiring would otherwise be spread across manual calls. See chapters 8.2, 8.3, and 8.8.

`RoutedFeatureLifecycleSpec`: pairs routed runtime with companion logic features and teardown rules. Use it when one feature should own a broader routed runtime lifecycle. See chapter 8.2.

`EventSubscriptionSpec`, `StoreSubscriptionSpec`, `StoreSelectorSpec`, `ObservableEffectSpec`, and `SignalEffectSpec`: declarative reactive and event hooks. They define which runtime streams are observed and how feature-owned handlers are bound. See chapters 8.3 and 8.4.

`ServiceBindingSpec` and `ServiceConsumerSpec`: typed service publication and consumption declarations for runtime scopes. Use them when scene-local services should be lifecycle-owned instead of manually attached to the host. See chapters 8.2 and 8.14.

`FeatureOperationSpec` and `FailurePolicySpec`: declarative operation binding with retry, timeout, and failure-publication rules. Use them when runtime work should behave as a named operation rather than a raw callback. See chapters 8.2, 8.10, and 8.14.

`PaletteInputBindSpec`, `PaletteBindingSpec`, and `SceneCommandPaletteSpec`: command-palette declarations. They control toggle binds, action binds, palette ownership, and scene scoping. See chapter 8.8.

`GlobalPointerActionSpec`: scene-wide pointer-triggered action declaration. Use it sparingly for semantic pointer actions that should run before ordinary control dispatch. See chapter 8.3.

#### Accessibility, Cursor, and Font Specs

`StaticAccessibilitySpec` and `AccessibilitySequenceSpec`: declare accessibility metadata and explicit accessibility sequencing. Use them when semantic tree content should be registered structurally instead of assembled imperatively. See chapters 8.7 and 8.8.

`CursorSpec` and `CursorBindingSpec`: cursor declarations and bindings for scenes or surfaces. See chapters 8.1 and 8.8.

`FontRoleBindingSpec`: semantic font-role mapping used during bootstrap. It bridges the host font configuration to named roles consumed by controls and presenters. See chapters 8.1 and 8.12.

#### Persistence, Migration, and Policy Specs

`TelemetryConfig`: bootstrap-time telemetry declaration. Use it when diagnostics should be enabled structurally rather than by ad hoc runtime code. See chapters 8.1 and 8.16.

`MigrationStepSpec`, `MigrationTargetSpec`, and `ContractMigrationSpec`: declarative migration vocabulary used by the broader runtime-policy and migration surface. They describe how one contract or snapshot shape should advance. See chapters 8.11 and the migration notes section.

`RuntimePolicySpec`, `ExecutionContextSpec`, `WorkloadBudgetClassSpec`, `WorkloadBudgetSpec`, `CheckpointDomainSpec`, `CheckpointSpec`, `SagaStepSpec`, and `SagaSpec`: advanced runtime-governance specs. They define context, budgets, checkpoints, and saga-style compensation flows for complex runtime orchestration. See chapters 3, 8.2, and 8.10.

`FeatureDependencySpec`, `CapabilityProviderSpec`, `CapabilityRequirementSpec`, `ProjectionNodeSpec`, `ProjectionSpec`, `WorkflowStepSpec`, `WorkflowSpec`, `RecomputeNodeSpec`, `QoSPolicySpec`, `HealthProbeSpec`, `ReplaySpec`, and `ReplacePolicySpec`: higher-level runtime faculties used when features need declarative dependency validation, projections, workflows, recomputation, QoS, health, replay, or hot-swap policies. See chapters 3 and 8.2.

[Back to Table of Contents](#table-of-contents)

`tests/test_public_api_exports.py` verifies that the supported root export surface remains importable. `tests/test_public_api_docs_contracts.py` checks that published API documentation and contracts match the code. `tests/test_runtime_operating_contracts.py` protects the runtime guarantees around scheduler budgeting, scene isolation, normalized dispatch, and deterministic ordering. `tests/test_boundary_contracts.py` guards the framework/demo package boundary. `tests/test_gui_application_workspace_contracts.py` validates application-facing workspace save and restore behavior.

### Runtime Behavior Tests

The wider test suite covers the areas where application regressions usually emerge first: workspace load and save behavior, overlay, tooltip, cursor, and palette routing, layout determinism, animation and scheduler semantics, accessibility trees and specs, and control runtime behavior. Runtime-facility coverage also matters here: service registration and cleanup, effect registration and disposal, operation retry and timeout behavior, failure publication behavior, and routed teardown guarantees should always be treated as release-critical behaviors rather than optional conveniences.

Representative files include `tests/test_scene_snapshot_and_workspace_state.py`, `tests/test_scene_command_palette_bindings.py`, `tests/test_task_panel_f1_toggle.py`, `tests/test_cooperative_scheduler.py`, `tests/test_schema_form_runtime.py`, `tests/test_theme_invalidation_bus.py`, `tests/test_runtime_systems.py`, and `tests/test_systems_feature.py`.

### Debug and Trace Tools

`EventRecorder`, `EventPlayback`, and `RecordedEvent` exist for reproducible input traces when an interaction bug is hard to reproduce manually. `DebugOverlay` gives live visual state inspection for geometry and rendering paths. `PropertyInspectorPanel`, `PropertyInspectorModel`, and `SceneSpatialIndex` help localize structural bugs in the live UI tree. The telemetry path, especially `analyze_telemetry_log_file()`, `analyze_telemetry_records()`, and `render_telemetry_report()`, is the first place to look when frame-time or pipeline regressions are suspected.

### Maintainer Release Runbook

The release gate should be run in the same order every time.

1. Run the high-priority contract tests.
2. Run the broader runtime tests that cover the systems touched by the change.
3. Validate demo assumptions against the current demo configuration and feature packages.
4. Check the root export inventory against Appendix D and Appendix D.1.
5. Re-read the runtime contracts for any changed guarantees, restore fields, or performance budgets.
6. Re-check the boundary rule that `gui_do/` does not import `demo_features/` and that consumer entrypoints import from the root package.
7. Record any unresolved upgrade ambiguity in the migration section instead of leaving it implicit.

### Regression Triage Workflow

The fastest reliable triage path is reproduce, trace, localize, test first, patch, and then re-check adjacent contracts. Reproduce the issue with the smallest scene or test surface that still fails. Capture a trace or telemetry sample if routing or timing is involved. Localize the failure to one controlling abstraction instead of scanning the whole stack. Add or update the narrowest test that expresses the defect. Patch the owning slice. Then rerun adjacent contract tests so a local fix does not silently violate a broader runtime guarantee.

### Maintainer Diff Checklist

Inventory delta checks:

1. Compare current root exports in `gui_do/__init__.py` with Appendix D and Appendix D.1 entries.
2. Check `docs/` contracts for changed guarantees, policies, or boundary rules.
3. Check `tests/` for new contract or runtime test modules that imply manual updates.
4. Check `demo_features/` for new recommended composition patterns to document.

Content integrity checks:

1. Every changed system has updates in both chapter narrative and quick-index references.
2. Removed APIs are deleted from examples, recipes, and appendix indexes.
3. Added APIs are classified at the right abstraction level, starting with Tier 1 before lower tiers.

Navigation and structure checks:

1. All newly added sections are present in the table of contents and resolve correctly.
2. Every major section still contains a Back to Table of Contents link.
3. Top-level chapter order remains stable unless an intentional restructure is recorded in migration guidance.

Operational checks:

1. Re-run high-priority contract tests.
2. Validate end-to-end reference assumptions against current runtime behavior.
3. Record unresolved ambiguities as explicit notes in the migration or deprecation guidance.

[Back to Table of Contents](#table-of-contents)
- This manual does not treat internal modules as a supported import surface when equivalent root exports exist.
- This manual does not preserve stale API narratives for historical completeness when the current runtime no longer supports them.
- This manual does not teach bootstrap patterns that violate the `gui_do/` versus `demo_features/` boundary defined by the architecture contracts.
- This manual does not assume package-relative file path resolution; relative paths resolve from the process current working directory, which is expected to be the launching application directory.
Performance work in `gui_do` is usually about bounding work, not chasing isolated micro-optimizations. The runtime contracts already define one of the most important limits: scheduler dispatch budgeting is clamped to `0.12` of dt milliseconds, with a `0.5 ms` floor and a `4.0 ms` ceiling. That gives a predictable upper bound during slow frames while still preventing starvation when frames are very fast.

`DirtyRegionTracker` is the framework's primary draw-cost gate for complex scenes. Its incremental union cache means `overlaps_dirty()` does not need to rescan the full dirty-rect set for each query, which keeps overlap checks cheap in large scenes. When a surface or region is expensive to redraw, use dirty-region gating and, when needed, offscreen render targets so unchanged regions are simply reused.

For large collections, prefer `VirtualizationCore`, `VirtualizedWindow`, and `RecyclePool` over keeping every row or cell live. For collection mutation, `ListDiffCalculator` should usually drive incremental updates instead of whole-list redraws. For high-churn allocations, `ObjectPool` is the intended pressure-relief valve. For expensive searches, form validation, or staged transforms, combine `Debouncer` or `Throttler` with `DataflowPipeline` and `CancellationToken` so the system can discard stale work instead of completing it uselessly.

The practical scaling checklist is straightforward: keep updates scene-scoped, avoid per-frame whole-collection reallocation, debounce expensive user-driven work, make background transforms preemptible, profile representative interactions instead of idle loops, and gate expensive draw regions with dirty tracking wherever possible.

[Back to Table of Contents](#table-of-contents)

The framework is easiest to understand if you separate three concerns that are intentionally kept distinct in the codebase. First, there is the declaration layer: dataclasses such as `HostApplicationBindingSpec`, `FeatureSpec`, `SceneBundleBindingSpec`, `WindowSpec`, `MenuStripSpec`, and `RoutedRuntimeSpec` describe what the application should contain. Second, there is the runtime realization layer: managers such as `FeatureManager`, `ActionManager`, `CommandPaletteManager`, `WorkspacePersistenceManager`, and the routed runtime orchestrators turn those declarations into live behavior. Third, there is lifecycle ownership: features are built, runtime resources are bound after structure exists, per-frame work runs while the scene is active, and teardown unwinds owned resources in reverse.

That separation is not decorative. It is the design rule that keeps the demo consumer code under `demo_features/` from leaking into the framework package, keeps scene setup deterministic, and makes the newer routed runtime facilities manageable instead of turning them into ad hoc callback webs. The theory chapter exists to give you the mental model for the rest of the manual: author structure as data, keep imperative behavior inside feature methods, and let lifecycle-owned runtime scopes clean up anything that would otherwise survive too long.
The versioned snapshot path is the recommended upgrade strategy. Write snapshots with `make_snapshot(current_version, state_dict)`. On load, inspect the stored version with `read_version()`. Pass the result through `SnapshotMigrator.migrate()` so registered `MigrationStep` objects can advance the snapshot through the available migration graph. Then restore the migrated state into the runtime. `MigrationRegistry` owns the one-directional steps, and `MigrationError` is the signal that no valid migration path exists.

Deprecation should be handled additively whenever possible. Prefer adding fields or parameters and keeping older behavior available long enough for a migration path to exist. Remove legacy behavior only after a documented migration path exists and the affected examples, tests, and appendices have been updated. No formal deprecated public APIs are cataloged in this manual at generation time; when formal deprecations are introduced, this section should become the canonical record.

The practical upgrade checklist is to run the contract tests before and after the upgrade, verify root-import consumer usage, re-check action, input, and focus routing in active scenes, inspect workspace restore reports for skipped or missing settings, rerun telemetry baselines, and update examples or docs that describe routed runtime so they use current service, effect, operation, and failure-policy terminology.

[Back to Table of Contents](#table-of-contents)
In `gui_do`, application structure is authored as data before it is executed as runtime behavior. The central entry point is the pair `HostApplicationBindingSpec` and `build_host_application_config()`. A user-facing application does not construct the action registry, window presentation model, scene roots, font roles, runtime scene startup policy, and feature instances one imperative branch at a time. Instead, it builds a single declarative description that names scenes, features, windows, actions, cursors, palette behavior, and optional scene bundles. The builder then converts that description into a `HostApplicationConfig`, and `bootstrap_host_application()` applies that config to a host object. The demo does this directly in `demo_features.demo_config`, where one host-level spec drives the entire application bootstrap.

This pipeline matters because it keeps description separate from execution. `build_host_application_config()` is a deterministic build step. It expands shorthand entries such as `SceneBundleBindingSpec`, `FeatureWindowBundleBindingSpec`, `ActionBindingSpec`, `CursorBindingSpec`, and `FontRoleBindingSpec` into the normalized spec collections the runtime consumes. That means validation and cross-reference resolution happen before the event loop runs. A misdeclared feature window bundle or scene setup does not hide inside an event callback; it surfaces while the config is being assembled. The result is a clearer contract boundary: the configuration phase describes intent, and the bootstrap phase realizes that intent.

**Should I build apps directly with controls or with features?**

Use features as the architectural unit. Controls are the implementation surface inside those boundaries. A feature gives you lifecycle phases, scene membership, runtime wiring, teardown, and a natural place for observables, services, and routed actions. Controls alone do not provide those coordination guarantees.

**When should I use `RoutedFeature` over `Feature`?**

Use `RoutedFeature` when the feature needs declarative runtime wiring such as hotkeys, overlays, subscriptions, task-panel toggles, or topic-based message dispatch. Plain `Feature` is still correct when the behavior is structurally simple and does not benefit from the routed runtime bundle.

**Why are some key handlers not firing?**

Check focus ownership first. Then check whether the action or binding is scene-scoped or window-scoped and whether the relevant window is visible. Then check whether an overlay, dialog, or palette is consuming the key first. If routing is still unclear, capture the interaction with `EventRecorder` and inspect the resulting path instead of guessing.

**Why do toast clicks not pass through?**

Toast bounds intentionally consume left-click events so underlying controls are not activated accidentally through transient notifications. If the toast itself should respond, attach explicit toast click handling instead of relying on pass-through behavior.

**How do I avoid breaking workspace restore across versions?**

Use versioned snapshots, register migration steps for every schema change, and inspect the restore report instead of assuming a full replay. `skipped_settings` and `missing_settings_blocks` are designed to surface compatibility drift without aborting the whole restore.

**How do I confirm my API usage is within the supported surface?**

Prefer explicit imports from the `gui_do` root and verify them with the contract tests. The manual treats the root package as the supported consumer surface, and Appendix D indexes that surface directly.

**Why does my feature's `bind_runtime()` appear to run before a sibling's `build()`?**

That ordering is not the intended contract. All features in a scene should complete `build()` before any of them enter `bind_runtime()`. If you see a mismatch, verify that the features are actually declared in the same scene and that the issue is not caused by late-created presentation surfaces.

**How do I add a keyboard shortcut without touching every location where that key is handled?**

Declare an action and bind it through the action or routed-runtime surface. That keeps the shortcut registered in one place and lets the action registry, input map, and optional shortcut overlay stay consistent.

[Back to Table of Contents](#table-of-contents)

The testability benefit follows directly from that separation. Specs are plain data, so tests can construct `HostApplicationBindingSpec`, `RoutedRuntimeSpec`, `SceneCommandPaletteSpec`, `MenuStripSpec`, or `FeatureWindowBundleBindingSpec` without a running display. The repository leans on this heavily: contract-style tests assert export surfaces, operating contracts, and builder behavior without needing the full interactive demo to run. A `HostApplicationConfig` can be assembled and inspected before any live scene is entered, and runtime helpers such as `setup_routed_runtime()` are tested against mock features and hosts.

Named specs also act as a forward-compatible serialization boundary. Because the framework prefers dataclasses with named fields over positional argument bundles, new optional fields can be added without rewriting every call site. `MenuStripSpec` can grow explicit scene and window opt-in fields. `SceneCommandPaletteSpec` can shift from a single activation field to separate `toggle` and `action` binds. `RoutedRuntimeSpec` can add new sibling declarative faculties such as policies, projections, workflows, and replay capture without forcing a redesign of the overall runtime composition model. The spec objects remain readable and evolvable because intent is encoded in field names.

The boundary of this pattern is important. `gui_do` is data-driven about structure, ownership, and wiring. It is not data-driven about all application behavior. Once a feature is active, its `handle_event()`, `on_update()`, `draw()`, and message handlers are ordinary imperative Python. That is deliberate. Declarative configuration is best for graph shape, relationships, and setup policy; imperative methods are best for domain behavior and rendering decisions. The framework is strongest when you keep those responsibilities separate rather than trying to force all behavior into either raw callback wiring or pure data.

**Feature**

A feature is the framework's lifecycle-managed behavior unit. `Feature`, `DirectFeature`, `LogicFeature`, and `RoutedFeature` share the same lifecycle idea but emphasize different execution surfaces. The key value is not inheritance variety by itself; it is the guarantee that structure, runtime wiring, event handling, update work, drawing, and teardown all happen in a deterministic framework-managed order.

**Spec**

A spec is a declarative data object that describes runtime wiring instead of performing it immediately. The spec graph is how bootstrap, scene composition, routed runtime setup, overlays, action bindings, and higher-level faculties stay inspectable and reproducible.

**Host**

The host is the plain Python object passed through bootstrap and then populated with runtime members. It is intentionally not a heavyweight inheritance root. The framework attaches the application runtime, managers, and configured members to it so features can depend on stable attributes without dict-driven plumbing.

**Scene**

A scene is the top-level interaction context. Features belong to one scene at a time. Scene transitions therefore change the active feature set, active presentation surfaces, and scene-scoped routing behavior in one coordinated move.

**Window presentation**

Window presentation is the model that determines which floating or anchored windows exist in a scene, which are visible, how their toggles are exposed, and how focus and scene chrome react to visibility changes.

**Routed runtime**

Routed runtime is the declarative bundle of hotkeys, overlays, subscriptions, effects, service hooks, operation bindings, palette bindings, and related runtime facilities that a feature can own through one spec-driven lifecycle.

**Observable**

An observable is a value or collection that notifies subscribers when it changes. In `gui_do`, observables are the primary reactive glue between feature state and UI state, and they work best when their subscriptions are owned by lifecycle-aware runtime scopes.

**Workspace state**

Workspace state is the persisted runtime context used for session restore. It includes scene choice, scene snapshots, feature state, settings blocks, metadata, and optionally dock layout so a later session can reconstruct the working surface.

**Contract test**

A contract test protects framework-level guarantees rather than incidental implementation details. These tests are the closest thing to an executable stability policy and should be treated as part of the supported surface, not as ordinary regression tests.

**Tier**

A tier is a public API grouping in `gui_do/__init__.py`. Tiers are documentation and selection signals: start at the highest-level stable surface that solves the problem, then descend only when you need finer control.

**Runtime scope**

Runtime scope is the lifecycle-owned container that tracks cleanup, subscriptions, services, and other teardown-sensitive runtime objects. It is what keeps bind and shutdown logic symmetric without manual unsubscribe and dispose lists scattered across a feature.

**Feature operation**

A feature operation is a declarative operation handler bound through runtime specs. It lets a feature expose named work with explicit context, retry, timeout, and failure-publication behavior instead of burying that logic in ad hoc callbacks.

**Failure policy**

Failure policy is the runtime rule set that governs retry, timeout, and failure publication for declaratively bound operations. It turns error handling into owned runtime behavior instead of unstructured exception branching.

[Back to Table of Contents](#table-of-contents)
	FeatureWindowBundleBindingSpec,
	FontRoleBindingSpec,
	HostApplicationBindingSpec,
	PaletteBindingSpec,
1. `bootstrap_host_application()` initializes the host from config specs.
2. Scene and feature declarations are resolved into the runtime graph.
3. All feature `build(host)` calls complete before runtime binding begins.
4. All active feature `bind_runtime(host)` calls run.
5. The runtime loop starts.
6. Raw pygame events are normalized into `GuiEvent` instances.
7. Overlay, focus, window, and scene routing is applied in the app dispatch path.
8. Feature `handle_event()` calls run in routing order.
9. Per-frame update work runs, including scheduler dispatch and timed work.
10. Feature `draw()` calls and control-tree drawing produce the frame.
11. Scene transitions shut down departing runtime, then build and bind arriving features.
12. Application exit triggers final runtime shutdown and optional workspace save behavior.

[Back to Table of Contents](#table-of-contents)
)


config = build_host_application_config(
Bootstrap is the top structural layer. It depends on the spec vocabulary, feature lifecycle, scene and window presentation, action and input registration, and theme and font configuration because all of those are assembled before the runtime loop becomes meaningful.

Feature lifecycle depends on the control tree, reactive state, event routing, and scene ownership rules. Layout and focus both sit downstream of the control tree and presentation model because visibility and containment determine which nodes can be measured or focused at all.

Overlays depend on event routing and focus policy because they are meaningful only when they can intercept or redirect input ahead of background surfaces. Persistence depends on registered scenes, feature state boundaries, and settings registries. Scheduling and animation depend on the per-frame update loop and scene-local runtime ownership.

Telemetry and introspection cross-cut almost everything: they do not own the main runtime path, but they inspect and measure it. Audio depends on the mixer layer and semantic event publication. Service scope is the broad dependency container that can support features or advanced runtime facilities at almost any tier.

[Back to Table of Contents](#table-of-contents)
		fonts={
			"default": {"file": "demo_features/data/fonts/Gimbot.ttf", "size": 14},
			"window": "demo_features/data/fonts/Ubuntu-B.ttf",
		},
This index follows the public root organization from `gui_do/__init__.py`. Names are grouped once by topic. Tiers 20-24 are imported by the root module but omitted from `__all__` at generation time; they are listed here because they are still part of the discovered root-topic layout.

#### Bootstrap and Data-Driven Specs

`Feature`, `DirectFeature`, `LogicFeature`, `RoutedFeature`, `FeatureMessage`, `FeatureManager`, `ScenePresentationModel`, `SceneSetupSpec`, `setup_standard_font_roles`, `FeatureSpec`, `WindowSpec`, `RuntimeSceneSpec`, `ActionSpec`, `StaticAccessibilitySpec`, `CursorSpec`, `SceneRootSpec`, `AnchoredWindowSpec`, `LogicBindingSpec`, `TaskPanelButtonSpec`, `TaskPanelWindowToggleGroupSpec`, `PaletteInputBindSpec`, `SceneCommandPaletteSpec`, `ActionHotkeySpec`, `ControlKeyBindingSpec`, `SceneTaskPanelSpec`, `TaskPanelSlotLayoutSpec`, `TaskPanelSceneNavButtonSpec`, `EventSubscriptionSpec`, `ServiceBindingSpec`, `ServiceConsumerSpec`, `StoreSubscriptionSpec`, `StoreSelectorSpec`, `ObservableEffectSpec`, `SignalEffectSpec`, `FailurePolicySpec`, `FeatureOperationSpec`, `ShortcutOverlaySpec`, `TaskPanelFocusToggleSpec`, `GlobalPointerActionSpec`, `FeatureDependencySpec`, `ExecutionContextSpec`, `WorkloadBudgetClassSpec`, `WorkloadBudgetSpec`, `CheckpointDomainSpec`, `CheckpointSpec`, `SagaStepSpec`, `SagaSpec`, `ReactiveSourceSpec`, `ReactiveNodeSpec`, `ReactiveGraphSpec`, `MigrationStepSpec`, `MigrationTargetSpec`, `ContractMigrationSpec`, `RuntimePolicySpec`, `EffectBindingSpec`, `EventPipelineStageSpec`, `EventPipelineSpec`, `DurableOperationBindingSpec`, `DurableOperationQueueSpec`, `DurableQueueRecord`, `CapabilityProviderSpec`, `CapabilityRequirementSpec`, `ProjectionNodeSpec`, `ProjectionSpec`, `PolicyDecision`, `WorkflowStepSpec`, `WorkflowSpec`, `RecomputeNodeSpec`, `QoSPolicySpec`, `HealthProbeSpec`, `ReplaySpec`, `ReplacePolicySpec`, `WorkflowCoordinator`, `RuntimePolicyEngine`, `EffectLifetimeOrchestrator`, `EventPipelineRuntime`, `DurableOperationQueueRuntime`, `CapabilityContractRuntime`, `ProjectionRuntime`, `RecomputeOrchestrator`, `QoSPolicyRuntime`, `FeatureHealthRuntime`, `RuntimeReplayHarness`, `FeatureHotSwapManager`, `ExecutionContextRuntime`, `WorkloadBudgetBrokerRuntime`, `CheckpointRecoveryRuntime`, `SagaCompensationRuntime`, `ReactiveDependencyGraphRuntime`, `ContractMigrationRuntime`, `RoutedRuntimeSpec`, `RoutedFeatureLifecycleSpec`, `FeatureWindowBundleBindingSpec`, `WindowToggleBindingSpec`, `SceneSetupBindingSpec`, `RuntimeSceneBindingSpec`, `SceneRootBindingSpec`, `CursorBindingSpec`, `FontRoleBindingSpec`, `ActionBindingSpec`, `PaletteBindingSpec`, `SceneBundleBindingSpec`, `HostApplicationBindingSpec`, `TabbedPresenterSpec`, `AccessibilitySequenceSpec`, `TabBuilderSpec`, `NotificationSpec`, `HostApplicationConfig`, `TelemetryConfig`, `bootstrap_host_application`, `build_notification_center`, `make_window_toggle_spec`, `make_scene_nav_action`, `make_exit_action`, `make_palette_toggle_action`, `make_static_accessibility_spec`, `build_feature_specs`, `build_feature_window_bundle_specs`, `build_window_toggle_specs`, `build_scene_setup_specs`, `build_runtime_scene_specs`, `build_scene_root_specs`, `build_cursor_specs`, `build_font_role_specs`, `build_scene_nav_actions`, `build_action_specs`, `build_scene_bundle_specs`, `build_static_accessibility_specs`, `build_host_application_config`, `FeatureOperationBus`, `FeatureOperationContext`, `FeatureOperationHandle`, `FeatureRuntimeScope`

#### Core Application and Scene Management

`GuiApplication`, `create_display`, `SceneTransitionManager`, `SceneTransitionStyle`, `apply_scene_setup_specs`

#### Reactive State and Presentation Models

`ObservableValue`, `PresentationModel`, `ComputedValue`, `InvalidationTracker`, `ChangeKind`, `CollectionChange`, `ObservableList`, `ObservableDict`, `CollectionViewQuery`, `CollectionView`, `Binding`, `BindingGroup`, `ObservableStream`, `SelectionModel`, `SelectionMode`

#### Events, Actions, Focus, and Input

`EventPhase`, `EventType`, `GuiEvent`, `ValueChangeCallback`, `ValueChangeReason`, `EventManager`, `EventBus`, `GestureRecognizer`, `EventRecorder`, `EventPlayback`, `RecordedEvent`, `InputSnapshot`, `Signal`, `SignalConnection`, `ActionManager`, `ActionContext`, `ActionMiddleware`, `ActionDescriptor`, `ActionRegistry`, `InputMap`, `InputBinding`, `KeyChordManager`, `KeyChord`, `ChordStep`, `FocusManager`, `FocusScope`, `FocusScopeManager`, `WindowFocusManager`, `FocusRing`

#### Scheduling and Animation

`TaskEvent`, `TaskScheduler`, `Timers`, `TweenManager`, `TweenHandle`, `Easing`, `AnimationSequence`, `AnimationHandle`, `TransitionManager`, `TransitionSpec`, `TransitionEvent`, `AnimationStateMachine`, `AnimationTransitionMode`, `SceneTimeline`, `Debouncer`, `Throttler`, `CooperativeScheduler`, `CoroutineHandle`, `Pause`, `Sleep`, `WaitForEvent`, `WaitForSignal`, `WaitUntil`, `WaitForAll`

#### Theme and Fonts

`FontManager`, `FontRoleRegistry`, `ColorTheme`, `ThemeManager`, `DesignTokens`, `ScopedTheme`, `ScopedThemeManager`

#### Telemetry and Diagnostics

`TelemetryCollector`, `TelemetrySample`, `configure_telemetry`, `telemetry_collector`, `analyze_telemetry_log_file`, `analyze_telemetry_records`, `load_telemetry_log_file`, `render_telemetry_report`

#### Layout and Spatial Systems

`LayoutAxis`, `ConstraintLayout`, `AnchorConstraint`, `DockPane`, `DockTabs`, `DockSplit`, `DockWorkspace`, `FlexLayout`, `FlexItem`, `FlexDirection`, `FlexAlign`, `FlexJustify`, `GridLayout`, `GridTrack`, `GridPlacement`, `LayoutAnimator`, `LayoutPass`, `MeasureContext`, `ArrangeContext`, `LayoutRoot`, `FlowLayout`, `FlowItem`, `Viewport`, `WindowLayoutHandler`

#### Overlays and Command Surfaces

`OverlayManager`, `OverlayHandle`, `Alignment`, `PlacementResult`, `PopupPlacement`, `Side`, `compute_popup_rect`, `DialogManager`, `DialogHandle`, `ToastManager`, `ToastHandle`, `ToastSeverity`, `ContextMenuManager`, `ContextMenuItem`, `ContextMenuHandle`, `CommandPaletteManager`, `CommandEntry`, `CommandPaletteHandle`, `TooltipManager`, `TooltipHandle`, `MenuBarManager`, `FileDialogManager`, `FileDialogOptions`, `FileDialogHandle`, `NotificationCenter`, `NotificationRecord`, `ResizeManager`, `CursorManager`, `CursorHandle`, `CursorShape`, `DragDropManager`, `DragPayload`, `ClipboardManager`, `TransferData`, `TransferManager`, `ShortcutHelpOverlay`, `ShortcutSection`, `ShortcutEntry`

#### Forms and Validation

`FormModel`, `FormField`, `ValidationRule`, `FieldError`, `FormSchema`, `SchemaField`, `DocumentModel`, `WizardFlow`, `WizardStep`, `WizardHandle`, `ValidationResult`, `Validator`, `RequiredValidator`, `RangeValidator`, `LengthValidator`, `PatternValidator`, `CustomValidator`, `DependentValidator`, `ValidationPipeline`, `AsyncFieldValidator`, `AsyncFormValidator`, `FieldSchema`, `FieldGraphSchema`, `ValidationPolicy`, `SchemaFormRuntime`

#### State, Persistence, and Migration

`CommandHistory`, `Command`, `CommandTransaction`, `StateMachine`, `HierarchicalStateMachine`, `Router`, `RouteEntry`, `SettingsRegistry`, `SettingDescriptor`, `WorkspaceState`, `WorkspacePersistenceManager`, `DEFAULT_WORKSPACE_STATE_PATH`, `SceneSnapshot`, `NodeSnapshot`, `SchemaVersion`, `VersionedSnapshot`, `MigrationStep`, `MigrationRegistry`, `SnapshotMigrator`, `MigrationError`, `make_snapshot`, `read_version`

#### Primary Controls

`PanelControl`, `LabelControl`, `ButtonControl`, `ToggleControl`, `SliderControl`, `ScrollbarControl`, `CanvasControl`, `CanvasEventPacket`, `CanvasViewport`, `FrameControl`, `ImageControl`, `ArrowBoxControl`, `ButtonGroupControl`, `TabControl`, `TabItem`, `DockWorkspacePanel`

#### Extended Controls and Presentation Surfaces

`TextInputControl`, `TextAreaControl`, `RichLabelControl`, `DropdownControl`, `DropdownOption`, `ListViewControl`, `ListItem`, `OverlayPanelControl`, `DataGridControl`, `GridColumn`, `GridRow`, `TreeControl`, `TreeNode`, `SplitterControl`, `SpinnerControl`, `RangeSliderControl`, `ColorPickerControl`, `ScrollViewControl`, `ProgressBarControl`, `AnimatedImageControl`, `ErrorBoundary`, `WindowControl`, `TaskPanelControl`, `WindowPresenter`, `MenuStripControl`, `MenuEntry`, `SceneMenuOptions`, `WindowMenuOptions`, `NotificationPanelControl`, `PropertyInspectorPanel`, `ToolbarControl`, `ToolbarItem`, `StatusBarControl`, `StatusSlot`, `ExpanderControl`, `DatePickerControl`, `TimePickerControl`, `BreadcrumbControl`, `BreadcrumbItem`, `SplitButtonControl`, `SplitButtonOption`, `ChipInputControl`

#### Text and Localization

`TextFormatter`, `NumericFormatter`, `PatternFormatter`, `FixedPatternFormatter`, `TextFlow`, `TextSpan`, `TextSearcher`, `TextMatch`, `StringTable`, `LocaleRegistry`

#### Data and Collections

`VirtualItemSource`, `FixedItemSource`, `SortFilterProxySource`, `AsyncDataProvider`, `LoadState`, `LoadStateKind`, `ObjectPool`, `DataCache`, `CacheStats`, `ListDiffCalculator`, `ListDiff`, `DiffInsert`, `DiffRemove`, `DiffMove`

#### Graphics and Rendering

`BuiltInGraphicsFactory`, `DirtyRegionTracker`, `DrawContext`, `DrawPhase`, `AssetRegistry`, `DebugOverlay`, `SurfaceCompositor`, `Layer`, `ShapeRenderer`, `SurfaceEffects`, `VectorPath`, `SpriteSheet`, `FrameAnimation`, `ParticleSystem`, `Emitter`, `ParticleLayer`, `TileSet`, `TileMap`, `RenderTarget`, `LiveRenderTarget`, `OffscreenRenderTarget`, `create_render_target`, `create_surface`, `Node2D`, `SceneGraph2D`, `Camera2D`

#### Introspection and Inspection

`SceneSpatialIndex`, `ui_property`, `PropertyDescriptor`, `PropertyRegistry`, `property_registry`, `PropertyInspectorModel`, `InspectedProperty`

#### Advanced Runtime and Bootstrap Extensions

`FrameTimer`, `TabPanelManager`, `WindowRelativeRect`, `resolve_scene_selection_callback`, `minimize_window_menu_entries`, `set_window_visible_state`, `toggle_window_visibility`, `create_anchored_feature_window`, `add_window_menu_strip`, `split_slot_bounds`, `place_control`, `place_control_unlabeled`, `register_placed_control`, `add_group_label`, `PlacedControl`, `make_labeled_slot_height_fn`, `apply_category_visibility`, `ControlRegistry`, `RowCellSpec`, `build_horizontal_row_specs`, `build_multi_column_grid_specs`, `build_tools_menu_entries`, `add_standard_menu_strip`, `add_menu_strip_from_spec`, `apply_accessibility_sequence`, `apply_accessibility_sequence_from_attrs`, `register_companion_logic_features`, `ensure_scene_scheduler`, `sorted_window_bindings`, `collect_window_toggle_controls`, `apply_window_toggle_accessibility`, `add_window_toggle_task_panel_controls`, `add_task_panel_window_toggle_group`, `setup_scene_command_palette_bindings`, `register_window_toggle_tooltips`, `initialize_locale_registry`, `bind_input_map_actions`, `register_descriptors`, `resolve_canvas_local_point`, `apply_runtime_scene_pristine_assets`, `bind_runtime_scene_exit_keys`, `prewarm_runtime_scenes`, `add_task_panel_button`, `add_task_panel_buttons`, `register_tooltip_specs`, `register_action_hotkeys`, `register_global_pointer_actions`, `draw_controls_prewarm`, `bind_palette_window_action_bind`, `ensure_scene_task_panel`, `create_task_panel_slot_layout`, `add_task_panel_scene_nav_button`, `add_scene_task_panel_items`, `centered_overlay_rect`, `create_shortcut_help_overlay`, `bind_feature_event_subscription`, `unbind_feature_event_subscription`, `setup_routed_runtime`, `shutdown_routed_runtime`, `bind_task_panel_focus_toggle`, `add_window_control`, `add_window_label`, `add_window_button`, `add_window_button_row`, `instantiate_features_from_specs`, `register_features_from_specs`, `register_window_presentation_specs`, `register_window_tab_builders`, `build_tab_builder_specs`, `create_tab_control_from_specs`, `compute_tabbed_window_layout`, `setup_feature_presenter_tabs_from_window_content`, `register_window_tab_builder_specs`, `setup_feature_presenter_tabs`, `register_tab_update_handlers`, `create_presented_anchored_window`, `create_presented_window_from_spec`, `create_feature_presented_window`, `configure_routed_feature_runtime`, `register_routed_feature_companions`, `bind_routed_feature_lifecycle`, `shutdown_routed_feature_lifecycle`, `ActiveTabUpdateRouter`, `TabLayoutContext`, `declare_host_actions`, `build_host_main_tab_order`, `apply_host_main_accessibility`

#### Infrastructure Internals

`UiEngine`

#### Audio

`SoundCue`, `SoundBankRegistry`, `SoundEventBus`

#### Accessibility

`AccessibilityRole`, `LivePoliteness`, `AccessibilityNode`, `AccessibilityTree`, `AccessibilityAnnouncement`, `AccessibilityBus`

#### Theme Invalidation

`ThemeInvalidationBus`

#### Undo Routing

`UndoContextManager`

#### Service Scope

`ServiceKey`, `ServiceScope`, `ScopeStack`

#### Dataflow Pipeline

`CancellationToken`, `PipelineStage`, `DataflowPipeline`, `PipelineHandle`

#### Transactional App State Store

`AppStateStore`, `StateSelector`, `StateTransaction`

#### Adaptive Constraint Layout

`ConstraintAttr`, `LayoutConstraint`, `ConstraintSet`, `AdaptivePolicy`, `resolve_adaptive_policy`

#### Virtualization

`MeasureMode`, `MeasurePolicy`, `VirtualizedWindow`, `RecyclePool`, `VirtualizationCore`

#### Interaction State Machine

`InteractionPhase`, `InteractionContext`, `InteractionTransition`, `InteractionStateMachine`

[Back to Table of Contents](#table-of-contents)
				scene_name="main",
				pretty_name="Desktop Demo",
				transition_style=SceneTransitionStyle.SLIDE_RIGHT,
				transition_duration=0.5,
| Tier | System | Representative names |
| --- | --- | --- |
| 1 | PRIMARY ENTRY POINTS & DATA-DRIVEN APIs | `Feature`, `HostApplicationBindingSpec`, `RoutedRuntimeSpec`, `FeatureWindowBundleBindingSpec`, `bootstrap_host_application` |
| 2 | CORE APPLICATION & SCENE MANAGEMENT | `GuiApplication`, `create_display`, `SceneTransitionManager`, `SceneTransitionStyle`, `apply_scene_setup_specs` |
| 3 | ESSENTIAL DATA & STATE MANAGEMENT | `ObservableValue`, `ComputedValue`, `CollectionView`, `BindingGroup`, `SelectionModel` |
| 4 | EVENTS, ACTIONS, FOCUS & INPUT | `GuiEvent`, `ActionRegistry`, `InputMap`, `FocusManager`, `KeyChordManager` |
| 5 | SCHEDULING & ANIMATION | `TaskScheduler`, `TweenManager`, `AnimationStateMachine`, `SceneTimeline`, `CooperativeScheduler` |
| 6 | THEME & FONT MANAGEMENT | `FontManager`, `FontRoleRegistry`, `ThemeManager`, `DesignTokens`, `ScopedThemeManager` |
| 7 | TELEMETRY & DIAGNOSTICS | `TelemetryCollector`, `configure_telemetry`, `analyze_telemetry_records`, `load_telemetry_log_file`, `render_telemetry_report` |
| 8 | LAYOUT & SPATIAL | `ConstraintLayout`, `DockWorkspace`, `FlexLayout`, `GridLayout`, `WindowLayoutHandler` |
| 9 | OVERLAY MANAGERS & WINDOWS | `OverlayManager`, `DialogManager`, `ToastManager`, `CommandPaletteManager`, `ShortcutHelpOverlay` |
| 10 | FORMS & DATA BINDING | `FormModel`, `FormSchema`, `DocumentModel`, `WizardFlow`, `ValidationPipeline` |
| 11 | STATE & PERSISTENCE | `CommandHistory`, `Router`, `SettingsRegistry`, `WorkspacePersistenceManager`, `SceneSnapshot` |
| 12 | PRIMARY CONTROLS (BASIC UI BUILDING BLOCKS) | `PanelControl`, `ButtonControl`, `CanvasControl`, `TabControl`, `DockWorkspacePanel` |
| 13 | EXTENDED CONTROLS (SPECIALIZED UI COMPONENTS) | `TextInputControl`, `ListViewControl`, `WindowControl`, `MenuStripControl`, `ChipInputControl` |
| 14 | TEXT & LOCALIZATION | `TextFormatter`, `TextFlow`, `TextSearcher`, `StringTable`, `LocaleRegistry` |
| 15 | DATA & COLLECTIONS | `VirtualItemSource`, `SortFilterProxySource`, `AsyncDataProvider`, `DataCache`, `ListDiffCalculator` |
| 16 | GRAPHICS & RENDERING | `DirtyRegionTracker`, `DrawContext`, `SurfaceCompositor`, `ParticleSystem`, `SceneGraph2D` |
| 17 | INTROSPECTION & INSPECTION | `SceneSpatialIndex`, `ui_property`, `PropertyRegistry`, `PropertyInspectorModel`, `InspectedProperty` |
| 18 | ADVANCED RUNTIME & BOOTSTRAPPING | `set_window_visible_state`, `add_standard_menu_strip`, `ensure_scene_task_panel`, `create_feature_presented_window`, `ActiveTabUpdateRouter` |
| 19 | INFRASTRUCTURE & INTERNALS (AVOID IN APPLICATION CODE) | `UiEngine` |
| 20 | AUDIO | `SoundCue`, `SoundBankRegistry`, `SoundEventBus` |
| 21 | ACCESSIBILITY | `AccessibilityRole`, `AccessibilityNode`, `AccessibilityTree`, `AccessibilityAnnouncement`, `AccessibilityBus` |
| 22 | THEME INVALIDATION | `ThemeInvalidationBus` |
| 23 | UNDO CONTEXT ROUTING | `UndoContextManager` |
| 24 | ASYNC FORM VALIDATION | `AsyncFieldValidator`, `AsyncFormValidator` |
| 25 | SCOPED SERVICE GRAPH | `ServiceKey`, `ServiceScope`, `ScopeStack` |
| 26 | CANCELABLE DATAFLOW PIPELINE | `CancellationToken`, `PipelineStage`, `DataflowPipeline`, `PipelineHandle` |
| 27 | TRANSACTIONAL APP STATE STORE | `AppStateStore`, `StateSelector`, `StateTransaction` |
| 28 | ADAPTIVE CONSTRAINT LAYOUT v2 | `ConstraintAttr`, `LayoutConstraint`, `ConstraintSet`, `AdaptivePolicy`, `resolve_adaptive_policy` |
| 29 | UNIFIED VIRTUALIZATION CORE | `MeasureMode`, `MeasurePolicy`, `VirtualizedWindow`, `RecyclePool`, `VirtualizationCore` |
| 30 | INTERACTION STATE MACHINE FRAMEWORK | `InteractionPhase`, `InteractionContext`, `InteractionTransition`, `InteractionStateMachine` |
| 31 | SCHEMA-DRIVEN FORM RUNTIME | `FieldSchema`, `FieldGraphSchema`, `ValidationPolicy`, `SchemaFormRuntime` |
| 32 | PORTABLE SNAPSHOT & MIGRATION LAYER | `SchemaVersion`, `VersionedSnapshot`, `MigrationStep`, `SnapshotMigrator`, `read_version` |

[Back to Table of Contents](#table-of-contents)
		),
		feature_window_bundle_entries=(
			FeatureWindowBundleBindingSpec(
				"_systems_feature",
1. Start at Tier 1. If `HostApplicationConfig`, `bootstrap_host_application()`, the feature types, and the spec vocabulary solve the problem, stop there.
2. Descend one tier at a time only when you need finer control than the higher-level surface provides.
3. Use Tier 18 when you are extending or customizing bootstrap and routed runtime behavior rather than replacing it.
4. Use explicit imports from the `gui_do` root in application code rather than submodule imports.
5. Avoid Tier 19 in application code; it is documented as infrastructure internals.

Useful shortcuts are consistent. Need app setup: use the bootstrap surface. Need cross-feature runtime behavior: use lifecycle specs and routed runtime helpers. Need large-data UI: use virtualization and dataflow APIs before building a custom loop. Need persistence that survives schema change: use `WorkspacePersistenceManager` plus `SnapshotMigrator`. Need discoverable shortcuts: declare actions and expose them through `ShortcutOverlaySpec` or command-surface helpers.

[Back to Table of Contents](#table-of-contents)
				task_panel_label="Systems",
			),
		),
		action_entries=(
**Template 1: Small Single-Scene App**

Use one scene, a handful of `Feature` instances, local observable state, and a small action set. This is the right shape when the application does not need floating windows or multiple scene contexts.

**Template 2: Multi-Window Workbench**

Use multiple scenes or one workbench scene with a unified menu strip, `SceneTaskPanelSpec`, presenter-backed windows, and `TaskPanelFocusToggleSpec`. This is the reference shape for tooling-style applications.

**Template 3: Data-Heavy Analysis Tool**

Use `AsyncDataProvider`, `SortFilterProxySource`, `VirtualizationCore`, `DataflowPipeline`, dirty-region rendering, and telemetry baselines. This is the correct shape when list or grid scale would otherwise dominate runtime cost.

**Template 4: Long-Running Workflow App**

Use `CooperativeScheduler` for multi-step work, expose progress through observables, use `WizardFlow` for guided input, and persist versioned workspace state with migration support.

[Back to Table of Contents](#table-of-contents)
			FontRoleBindingSpec("title", 14, "window"),
		),
		palette_spec=PaletteBindingSpec(include_scene_entries=True, include_window_entries=True),
	)
This appendix is the concise practical index for the framework's spec families. Spec-heavy sections in this manual should be read with this appendix nearby.

#### Bootstrap and Scene Composition Specs

`HostApplicationBindingSpec`: top-level bootstrap input. Key options include display size, window title, initial scene name, font config, scene bundles, feature specs, action specs, cursor specs, accessibility specs, telemetry config, and related root declarations. See chapters 8.1, 8.3, and 8.9.

`HostApplicationConfig`: built config object produced by `build_host_application_config()`. Use it as the validated bootstrap payload passed to `bootstrap_host_application()`. See chapter 8.1.

`SceneBundleBindingSpec`: bundle-oriented scene declaration. It groups scene setup, runtime scene behavior, scene navigation, and optional scene roots so one declaration can emit the needed sub-specs. See chapters 6 and 8.1.

`FeatureSpec`: declarative feature entry. Its key fields identify the feature factory, scene, and structural placement context. See chapters 5, 6, and 8.2.

`SceneSetupSpec`, `RuntimeSceneSpec`, and `SceneRootSpec`: scene-level structural and runtime declarations. Use them to separate scene structure from per-scene runtime facilities and root-node ownership. See chapters 8.1 and 8.9.

#### Action, Input, and Overlay Specs

`ActionSpec` and `ActionBindingSpec`: declare named actions, labels, categories, and kind-specific behavior such as exit or palette toggling. Use them when behavior should be named and rebindable. See chapter 8.3.

`ActionHotkeySpec` and `ControlKeyBindingSpec`: bind keys to actions or controls with scene and visibility scope. Use them instead of scattering raw key checks through features. See chapter 8.3.

`ShortcutOverlaySpec`: declares a help-overlay owner, toggle action, optional key, filtering rules, and manual shortcut sections. Use it when discoverable shortcuts are part of the runtime contract. See chapter 8.8.

`NotificationSpec`: declarative notification-center entry used during bootstrap. Use it when a notification surface should be configured structurally instead of ad hoc at runtime. See chapters 8.1 and 8.8.

#### Window and Presentation Specs

`WindowSpec` and `AnchoredWindowSpec`: declarative window shape and placement specs. `AnchoredWindowSpec` adds anchoring semantics and chrome-related placement details for presenter-backed or feature-backed windows. See chapter 8.9.

`FeatureWindowBundleBindingSpec` and `WindowToggleBindingSpec`: bind feature-owned windows to scene presentation, toggles, and related chrome. Use them when a feature should bring its window behavior with it as a single declaration. See chapter 8.9.

`SceneTaskPanelSpec`, `TaskPanelButtonSpec`, `TaskPanelSlotLayoutSpec`, `TaskPanelWindowToggleGroupSpec`, `TaskPanelSceneNavButtonSpec`, and `TaskPanelFocusToggleSpec`: task-panel composition vocabulary. These specs control panel composition, slot order, scene-nav buttons, window-toggle groups, and focus inclusion when windows are shown or hidden. See chapters 8.8 and 8.9.

`TabbedPresenterSpec` and `TabBuilderSpec`: presenter-tab declarations. Use them when one presenter-backed window should host multiple tabbed content surfaces with stable builder wiring. See chapter 8.9.

#### Routed Runtime and Higher-Level Runtime Specs

`RoutedRuntimeSpec`: the central runtime bundle for hotkeys, overlays, subscriptions, store selectors, effects, service hooks, operations, palette bindings, and presentation toggles. Use it whenever a feature's runtime wiring would otherwise be spread across manual calls. See chapters 8.2, 8.3, and 8.8.

`RoutedFeatureLifecycleSpec`: pairs routed runtime with companion logic features and teardown rules. Use it when one feature should own a broader routed runtime lifecycle. See chapter 8.2.

`EventSubscriptionSpec`, `StoreSubscriptionSpec`, `StoreSelectorSpec`, `ObservableEffectSpec`, and `SignalEffectSpec`: declarative reactive and event hooks. They define which runtime streams are observed and how feature-owned handlers are bound. See chapters 8.3 and 8.4.

`ServiceBindingSpec` and `ServiceConsumerSpec`: typed service publication and consumption declarations for runtime scopes. Use them when scene-local services should be lifecycle-owned instead of manually attached to the host. See chapters 8.2 and 8.14.

`FeatureOperationSpec` and `FailurePolicySpec`: declarative operation binding with retry, timeout, and failure-publication rules. Use them when runtime work should behave as a named operation rather than a raw callback. See chapters 8.2, 8.10, and 8.14.

`PaletteInputBindSpec`, `PaletteBindingSpec`, and `SceneCommandPaletteSpec`: command-palette declarations. They control toggle binds, action binds, palette ownership, and scene scoping. See chapter 8.8.

`GlobalPointerActionSpec`: scene-wide pointer-triggered action declaration. Use it sparingly for semantic pointer actions that should run before ordinary control dispatch. See chapter 8.3.

#### Accessibility, Cursor, and Font Specs

`StaticAccessibilitySpec` and `AccessibilitySequenceSpec`: declare accessibility metadata and explicit accessibility sequencing. Use them when semantic tree content should be registered structurally instead of assembled imperatively. See chapters 8.7 and 8.8.

`CursorSpec` and `CursorBindingSpec`: cursor declarations and bindings for scenes or surfaces. See chapters 8.1 and 8.8.

`FontRoleBindingSpec`: semantic font-role mapping used during bootstrap. It bridges the host font configuration to named roles consumed by controls and presenters. See chapters 8.1 and 8.12.

#### Persistence, Migration, and Policy Specs

`TelemetryConfig`: bootstrap-time telemetry declaration. Use it when diagnostics should be enabled structurally rather than by ad hoc runtime code. See chapters 8.1 and 8.16.

`MigrationStepSpec`, `MigrationTargetSpec`, and `ContractMigrationSpec`: declarative migration vocabulary used by the broader runtime-policy and migration surface. They describe how one contract or snapshot shape should advance. See chapters 8.11 and the migration notes section.

`RuntimePolicySpec`, `ExecutionContextSpec`, `WorkloadBudgetClassSpec`, `WorkloadBudgetSpec`, `CheckpointDomainSpec`, `CheckpointSpec`, `SagaStepSpec`, and `SagaSpec`: advanced runtime-governance specs. They define context, budgets, checkpoints, and saga-style compensation flows for complex runtime orchestration. See chapters 3, 8.2, and 8.10.

`FeatureDependencySpec`, `CapabilityProviderSpec`, `CapabilityRequirementSpec`, `ProjectionNodeSpec`, `ProjectionSpec`, `WorkflowStepSpec`, `WorkflowSpec`, `RecomputeNodeSpec`, `QoSPolicySpec`, `HealthProbeSpec`, `ReplaySpec`, and `ReplacePolicySpec`: higher-level runtime faculties used when features need declarative dependency validation, projections, workflows, recomputation, QoS, health, replay, or hot-swap policies. See chapters 3 and 8.2.

[Back to Table of Contents](#table-of-contents)
[Back to Table of Contents](#table-of-contents)

### Reactive Data and Observable State

Reactive state in `gui_do` means that producers publish changes once and consumers subscribe once. The producer does not need to know every control, presenter, or sibling feature that depends on a value. That is the difference from imperative refresh code: instead of every mutation chasing its readers manually, the value itself owns notification. When a feature changes an `ObservableValue`, appends to an `ObservableList`, or updates an `ObservableDict`, every subscriber that registered interest earlier is notified through a consistent contract.

The core primitives are intentionally small. `ObservableValue` holds one value and notifies subscribers when `.value` changes. `ObservableList` and `ObservableDict` provide the same idea for mutable collections, but they emit a `CollectionChange` that describes the mutation with fields such as `kind`, `index`, `key`, `old_value`, `new_value`, and `new_index`. Those collection-level descriptors matter because advanced controls rarely care only that something changed; they care whether an item was added, replaced, moved, or cleared. A collection change contract is the minimum structure needed for efficient UI refresh strategies.

`reactive_batch()` exists for the cases where one conceptual change spans several observable writes. While the batch context is active, assignments update the stored values immediately but defer notifications until the outermost batch exits. This keeps dependent UI from rendering intermediate states and keeps computed outputs from thrashing during grouped updates. The implementation is intentionally explicit: batching is a context manager, not a hidden scheduler. You choose the atomic boundary, and the framework guarantees the observer flush happens once the batch completes successfully.

`ComputedValue` pushes the model further by allowing derived reactive state to be represented as a first-class observable. The implementation supports both explicit dependencies and auto-tracking: any `ObservableValue` whose `.value` is read while the computation runs can be registered automatically. That means a feature can model derived state as a live value instead of manually keeping a second observable in sync with callback glue. The distinction matters when you want consumers to treat derived state like any other reactive source rather than learning which values are primary and which are hand-maintained copies.

Subscription timing is where many GUI systems become unreliable, and `gui_do` is explicit about the safe phase boundaries. Structural work belongs in `build()`. Runtime subscriptions belong in `bind_runtime()`, when sibling features, app services, and control instances are already present. Cleanup belongs in `shutdown_runtime()`. If you subscribe too early, the callback may run before the controls or services it wants to touch exist. If you never unsubscribe, you retain feature instances after scene exit, keep receiving updates after shutdown, and eventually create duplicate notifications when the same scene is rebuilt.

The framework's ownership model reduces that teardown burden in two ways. First, `ObservableValue.subscribe()` auto-detects bound feature methods and passes the unsubscribe callable into `Feature._track_runtime_subscription()`. Second, the routed runtime path creates a `FeatureRuntimeScope` whose `subscribe()`, `own_connection()`, `own_cancel_handle()`, and `own_disposable()` helpers register cleanup actions into a single disposal bag. When `shutdown_routed_runtime()` runs, it disposes the runtime scope, and those owned subscriptions, signal connections, cancellable handles, and disposable services are unwound in reverse order. That automation exists so authors do not have to maintain parallel unsubscribe lists by hand every time a feature grows a new binding.

That ownership discipline is not an incidental convenience feature. It prevents an entire class of resource errors: subscription leaks, retained feature instances, post-shutdown callbacks into dead controls, duplicate notifications after scene rebuild, and partial teardown where one cleanup path runs but another is forgotten. The framework still allows manual subscription ownership when needed, but its default trajectory is toward lifecycle-owned cleanup because GUI code accumulates cross-system references very quickly once observables, signals, state stores, timers, and overlay callbacks are all in play.

Cross-feature reactive state works best when ownership is clear. One feature owns a value or a store. Other features consume it by subscription, selector, or declared runtime spec. That keeps the producer agnostic about who depends on it and keeps the consumer focused on reaction rather than polling. The anti-patterns are predictable: polling an observable in `on_update()` wastes frame time and adds latency, sharing a mutable plain Python object bypasses the notification contract entirely, and subscribing in `build()` forces structural code to know too much about runtime availability. The framework offers direct observable primitives, `AppStateStore`, selectors, and batched updates precisely so those anti-patterns are unnecessary.

```python
from gui_do import ComputedValue, ObservableList, ObservableValue, reactive_batch


count = ObservableValue(0)
label = ComputedValue(lambda: f"Count: {count.value}")
events = []

unsubscribe = label.subscribe(events.append)
count.value = 1

with reactive_batch():
	count.value = 2
	count.value = 3

items = ObservableList(["alpha"])
items.subscribe(lambda change: events.append((change.kind.value, change.new_value)))
items.append("beta")

unsubscribe()
```

[Back to Table of Contents](#table-of-contents)

### Feature Composition and Lifecycles

The feature is the unit of composition that the rest of the runtime serves. A feature is not just a widget and not just a controller. It is the object that owns a coherent slice of behavior, declares which host attributes it needs through `HOST_REQUIREMENTS`, participates in scene membership through `scene_name`, receives lifecycle callbacks in a stable order, and can exchange structured messages with other features through `FeatureMessage`. The framework's job is to coordinate many such objects without forcing them to know one another's implementation details.

The base `Feature` class defines the lifecycle surface: `build()`, `bind_runtime()`, `configure_accessibility()`, `shutdown_runtime()`, `handle_event()`, `on_update()`, `draw()`, `prewarm()`, `save_state()`, and `restore_state()`. `HOST_REQUIREMENTS` lets a feature declare what a given hook needs from the host, and `validate_host_for()` enforces that contract before execution. That is a concrete design choice: instead of relying on constructor injection or undocumented host assumptions, each lifecycle phase can describe its dependency boundary declaratively.

The subtypes exist to mark intent. `DirectFeature` is for direct screen event, update, and draw integration when the control tree would be unnecessary overhead. `LogicFeature` is for message-driven domain behavior with no requirement to build controls of its own. `RoutedFeature` extends `Feature` with topic-based message dispatch and automatically treats `bind_runtime()` as requiring an `app` so scheduler and routed runtime wiring can occur safely. The types are small, but they let the rest of the system reason about what work belongs where.

The lifecycle ordering is the practical center of the framework. `build()` is for creating stable structure: controls, presenters, labels, window layout, and static scene elements. `bind_runtime()` runs after all features have built, so this is where cross-feature logic aliases, state subscriptions, service consumption, palette bindings, and other runtime resources should be attached. `handle_event()` processes routed `GuiEvent` values when the routing layer decides the feature is eligible to receive them. `on_update()` is the frame-driven hook for lightweight incremental work, and `draw()` is for custom rendering paths that sit beside or underneath the normal control render path. `shutdown_runtime()` is the matching unwind phase for everything attached during runtime binding.

Message-based feature coordination keeps features loosely coupled. A feature can queue a `FeatureMessage` with a structured payload and let the `FeatureManager` deliver it to a named target. `LogicFeature` drains queued messages whose payload contains a `command`; `RoutedFeature` drains queued messages whose payload contains a `topic` and dispatches them through `message_handlers()`. This means coordination can be explicit without turning into direct object references everywhere. The sender does not need to know the target's internal methods, only the message contract.

Scene assignment closes the loop on lifecycle safety. A feature belongs to one scene or to the global scope. When scenes transition, the framework activates and tears down features according to scene membership. This is why cleanup must be coupled to runtime ownership rather than left to best effort. A previous scene's feature must not continue receiving store updates, event bus publications, or timer callbacks after the scene has been left. The explicit `shutdown_runtime()` phase exists to make that boundary enforceable rather than aspirational.

The repository's demo packages show the recommended growth pattern. `demo_features/main` uses `main_feature.py`, `main_specs.py`, and `main_build_helpers.py` to separate lifecycle logic, declarative scene specs, and helper construction code. `demo_features/showcase` splits its feature across focused helpers such as `showcase_basics_helpers.py`, `showcase_extended_helpers.py`, `showcase_runtime_helpers.py`, and `showcase_specs.py`. `demo_features/systems` grows even further into separate helpers for data, graphics, persistence, scheduling, state, text, theme, validation, and presenter logic. That is exactly the kind of growth that the package-root import convention is meant to support.

Common composition patterns follow naturally from these rules. A logic-plus-presentation split uses a `LogicFeature` to own computation and publishes results through observables or messages, while a `Feature` or `RoutedFeature` binds controls and reacts to those values. A presenter pattern keeps a `WindowPresenter` or presenter-like helper responsible for window-local UI construction while the feature handles runtime coordination. A background feature pattern uses scheduling or operation facilities to run long-lived work without forcing UI code to carry the retry, timeout, and progress mechanics directly.

```python
from gui_do import Feature, ObservableValue


class StatusFeature(Feature):
	HOST_REQUIREMENTS = {
		"bind_runtime": ("app",),
		"shutdown_runtime": ("app",),
	}

	def __init__(self) -> None:
		super().__init__("status", scene_name="main")
		self.status = ObservableValue("idle")

	def bind_runtime(self, host) -> None:
		self._unsubscribe = self.status.subscribe(lambda value: None)

	def shutdown_runtime(self, host) -> None:
		self._unsubscribe()
```

[Back to Table of Contents](#table-of-contents)

### Automatic Subscription Ownership and Teardown Safety

Automatic ownership exists because reactive GUI code is otherwise too easy to tear down incorrectly. Once a feature subscribes to a state store, an `ObservableValue`, a signal, a scheduler callback, and an event bus topic, the feature has acquired references from several subsystems at once. If cleanup is left to scattered ad hoc code, teardown quality degrades as the feature evolves. One callback is removed, another is forgotten, a third is only conditionally removed, and the resulting bug report appears much later as a duplicate notification or a callback into a feature that should have been dead.

`gui_do` addresses that by giving runtime-bound resources a clear owner. `Feature._track_runtime_subscription()` can collect unsubscribe callables even outside the routed runtime path, while `FeatureRuntimeScope` is the stronger ownership model for declarative routed runtime setup. The scope owns a cleanup bag and a child `ServiceScope`. Its helpers let you register a subscription, a disconnectable connection, a cancel handle, or a disposable instance in the same place where you create it. That turns cleanup from a memory exercise into a lifecycle guarantee.

The consistency benefit is larger than just memory hygiene. Automatic ownership means authors do not need to mirror every subscription site with a manually synchronized unsubscribe site. It reduces teardown drift when features gain new runtime bindings over time. It ensures a scene shutdown unwinds resources in a predictable order. It prevents retained feature instances and post-shutdown callbacks from reviving stale UI state. It also reduces partial teardown failures, because `shutdown_routed_runtime()` disposes the runtime scope as one operation instead of hoping that every individual cleanup branch was updated after the last refactor.

The anti-pattern to avoid is relying on `shutdown_runtime()` as a place for selective, incomplete cleanup while routed runtime resources continue to exist outside the feature's ownership graph. If `setup_routed_runtime()` created store selectors, projections, event pipelines, or operation infrastructure, `shutdown_runtime()` must unwind the routed runtime scope rather than merely clearing a local field or hiding a control. Otherwise the code appears to shut down while the routed resources continue to observe, publish, or schedule work.

[Back to Table of Contents](#table-of-contents)

### Higher-Level Runtime Faculties and Composition

The newer routed runtime facilities extend the same control-plane to runtime-plane pattern rather than introducing a separate architecture. `RoutedRuntimeSpec` is the umbrella declaration. It already covered logic bindings, service bindings, store subscriptions, observable effects, signal effects, operation handlers, shortcut overlays, and global pointer actions. It now also carries sibling declarative specs for higher-level runtime faculties: dependency validation with `FeatureDependencySpec`; policy admission with `RuntimePolicySpec`, `PolicyDecision`, and `RuntimePolicyEngine`; effect lifetime control with `EffectBindingSpec` and `EffectLifetimeOrchestrator`; event stream routing with `EventPipelineStageSpec`, `EventPipelineSpec`, and `EventPipelineRuntime`; durable queue recovery with `DurableOperationBindingSpec`, `DurableOperationQueueSpec`, `DurableQueueRecord`, and `DurableOperationQueueRuntime`; capability negotiation with `CapabilityProviderSpec`, `CapabilityRequirementSpec`, and `CapabilityContractRuntime`; incremental projection updates with `ProjectionNodeSpec`, `ProjectionSpec`, and `ProjectionRuntime`; workflow coordination with `WorkflowStepSpec`, `WorkflowSpec`, and `WorkflowCoordinator`; recompute ordering with `RecomputeNodeSpec` and `RecomputeOrchestrator`; quality-of-service policies with `QoSPolicySpec` and `QoSPolicyRuntime`; health monitoring with `HealthProbeSpec` and `FeatureHealthRuntime`; replay capture with `ReplaySpec` and `RuntimeReplayHarness`; and hot-swap policy with `ReplacePolicySpec` and `FeatureHotSwapManager`.

The important conceptual point is that these facilities are siblings, not isolated subsystems with unrelated lifecycle rules. `setup_routed_runtime()` calls `build_routed_runtime_systems()` after it has created the `FeatureRuntimeScope`, optional service bindings, optional operation bus, and reactive subscriptions. The returned runtime systems object is then owned by that same runtime scope. Its `on_update` hook is attached to the feature as `_routed_runtime_on_update`, and individual facilities are exposed back to the feature through attribute names such as `policy_attr_name`, `effects_attr_name`, `event_pipeline_attr_name`, `durable_queue_attr_name`, `capability_attr_name`, `projection_attr_name`, `workflow_attr_name`, `recompute_attr_name`, `qos_attr_name`, `health_attr_name`, and `replay_attr_name`. This is a control-plane/runtime-plane bridge: declaration names the facility, runtime setup realizes it, and the lifecycle owns it.

These facilities exist because some runtime problems are too cross-cutting to be solved cleanly by one-off callbacks. Dependency validation guards startup and feature interaction assumptions. Policy engines centralize admission and allow/deny reasoning instead of scattering precondition checks. Effect lifetime orchestration ensures that long-lived reactive or service effects have an owner. Event pipeline stages let features model routed event processing as an explicit pipeline instead of incidental handler ordering. Durable queues and projections let stateful runtime work survive failure and be recomputed incrementally. Workflows, recompute graphs, QoS policies, health probes, replay capture, and hot-swap managers all move operational concerns into explicit runtime structures where they can be tested and shut down deliberately.

The lifecycle placement remains stable despite the increased capability surface. The declarations live in `RoutedRuntimeSpec`. Setup happens during `bind_runtime()` through `setup_routed_runtime()`. Frame-time work happens through the `_routed_runtime_on_update` callback that `RoutedFeature.on_update()` invokes before draining queued messages. Cleanup happens through `shutdown_routed_runtime()`, which disposes the runtime scope, unwinds event subscriptions, clears facility attributes, and removes the runtime update hook. That symmetry is what prevents higher-level faculties from becoming a source of leaks or scene-crossing behavior.

The practical guidance is to treat these faculties as declarative control-plane components for operational behavior that would otherwise become fragile imperative glue. Use them when you need durable ownership, policy enforcement, deterministic recompute order, replayable diagnostics, or bounded operational behavior across frames. Do not use them as a substitute for ordinary feature methods when simple local logic will do. The framework is giving you a structured runtime control plane, not encouraging every feature to become a miniature orchestrator for its own sake.

```python
from gui_do import (
	FeatureOperationSpec,
	PaletteInputBindSpec,
	RoutedRuntimeSpec,
	SceneCommandPaletteSpec,
	ServiceBindingSpec,
	StoreSubscriptionSpec,
)


runtime_spec = RoutedRuntimeSpec(
	scene_name="main",
	service_bindings=(
		ServiceBindingSpec(attr_name="status_service", key="status", factory=lambda feature, host, scope: object()),
	),
	store_subscriptions=(
		StoreSubscriptionSpec(state_key="status", handler=lambda value: None, invoke_immediately=True),
	),
	operations=(
		FeatureOperationSpec(name="refresh", handler=lambda payload, ctx=None: payload),
	),
	command_palette=SceneCommandPaletteSpec(
		scene_name="main",
		toggle=PaletteInputBindSpec(action_name="command_palette_toggle", key=294),
		action=PaletteInputBindSpec(action_name="command_palette_action", pointer_button=2),
	),
)
```

[Back to Table of Contents](#table-of-contents)

## Quickstart Path (Practice)
[Back to Table of Contents](#table-of-contents)

The fastest reliable way to start a `gui_do` application is to imitate the repository's own demo bootstrap and keep the first version deliberately small. The practical path is: define one `HostApplicationBindingSpec`, build it into a `HostApplicationConfig` with `build_host_application_config()`, call `bootstrap_host_application()` from your entrypoint, and let the runtime construct scenes, actions, windows, roots, and presentation bindings from the spec graph. This keeps the first app close to Tier 1 instead of dropping immediately into lower-level managers.

The real demo uses exactly that approach. `gui_do_demo.py` imports `bootstrap_host_application` from the `gui_do` root and consumes `DEMO_BOOTSTRAP_CONFIG` from `demo_features.demo_config`. That config is built from one `HostApplicationBindingSpec` containing scene bundle entries, feature entries, feature-window bundle entries, actions, accessibility entries, font roles, cursors, telemetry, and command palette policy. The best beginner habit is to keep your first app equally centralized: one config file, one entrypoint, one scene, and one visible feature.

### Six-Milestone Quickstart

Milestone A is simple boot success: the app opens one scene and exits cleanly. That means you have a valid `HostApplicationBindingSpec`, a stable `initial_scene_name`, and at least one matching scene entry. Milestone B is one visible feature creating one control or root visual element. At that point you have proved the scene bootstrap, feature registration, and build lifecycle are all connected. Milestone C is one observable updating one piece of UI reactively, which proves you understand the difference between structure and runtime state.

Milestone D adds one action and one hotkey. The point is not the feature itself; it is proving you can trace input through the action registry and input scope rather than improvising event branches inside feature code. Milestone E adds one overlay or toast route, which confirms that overlay routing, focus changes, and event consumption work the way the app loop expects. Milestone F is a workspace save and load roundtrip, because persistence is where many projects discover they were relying on accidental state rather than explicit state ownership.

The beginner confidence checklist is short but strict. You should be able to explain where `build()` ends and `bind_runtime()` begins. You should be able to add or remove one feature through specs only, without touching the application loop. You should be able to trace one keypress from normalized `GuiEvent`, through action routing and scene scope, to the final handler that changes state.

```python
from gui_do import bootstrap_host_application

from demo_features.demo_config import DEMO_BOOTSTRAP_CONFIG


class DemoApp:
	def __init__(self) -> None:
		bootstrap_host_application(self, DEMO_BOOTSTRAP_CONFIG)


app = DemoApp()
# app.app.run_entrypoint(target_fps=DEMO_BOOTSTRAP_CONFIG.target_fps)
```

### Minimal Host Config Pattern

The host-level build pattern should stay close to the demo until you have a reason to generalize it. Keep the entrypoint thin, keep the config in one module, and treat the spec graph as the single source of truth for scene membership and host-level wiring. Relative asset paths, telemetry files, and other file-oriented inputs should be written as paths relative to the process current working directory, which in this repository is the project root when launched from `gui_do_demo.py`.

```python
from gui_do import (
	ActionBindingSpec,
	HostApplicationBindingSpec,
	SceneBundleBindingSpec,
	SceneTransitionStyle,
	build_host_application_config,
)


config = build_host_application_config(
	HostApplicationBindingSpec(
		display_size=(1280, 720),
		window_title="example",
		fonts={"default": {"file": "demo_features/data/fonts/Gimbot.ttf", "size": 14}},
		initial_scene_name="main",
		scene_bundle_entries=(
			SceneBundleBindingSpec(
				scene_name="main",
				pretty_name="Main",
				transition_style=SceneTransitionStyle.SLIDE_RIGHT,
				transition_duration=0.3,
				emit_nav_action_spec=True,
				nav_action_id="nav_main",
				nav_label="Go to Main",
			),
		),
		action_entries=(
			ActionBindingSpec(kind="exit", action_id="exit", label="Exit", category="File"),
		),
	)
)
```

### Quickstart Failure Modes

If a feature never appears, verify that the feature is registered in the host config and that its `scene_name` matches the scene you actually entered. If a hotkey does nothing, verify both the action descriptor and the input binding scope; scene mismatch is the common early mistake. If an overlay seems to swallow keys unexpectedly, inspect the overlay's dismissal and consumption behavior instead of patching around it in feature code. If state changes but the UI does not, the problem is usually lifecycle timing: subscribe in `bind_runtime()`, not during `build()`, and do not dispose the subscription before the scene exits.

[Back to Table of Contents](#table-of-contents)

## Architecture and Runtime Model
[Back to Table of Contents](#table-of-contents)

The repository enforces a strict boundary between framework code and consumer code. Everything under `gui_do/` is reusable framework runtime: lifecycle coordination, events, data, layout, controls, overlays, persistence, and supporting systems. Everything under `demo_features/` and the `gui_do_demo.py` entrypoint is consumer composition. The framework must not import demo code, and the entrypoint should import from the `gui_do` root rather than internal submodules. That rule is not informal; `tests/test_boundary_contracts.py` checks both directions.

The public API is deliberately tiered. Tier 1 is the recommended entry surface for new applications: feature classes, spec dataclasses, builder helpers, and bootstrap functions. Tiers 2 through 7 expose core runtime systems such as application management, observables, actions, events, scheduling, theming, and telemetry. Tier 8 and above expose progressively lower-level or more specialized systems: layout engines, overlay managers, forms, persistence tools, controls, graphics, introspection, and advanced runtime helpers. The tier number is guidance about approach order. When multiple tiers can solve the same problem, start with the lower-numbered and more declarative layer first.

The runtime operating contracts define the guarantees the architecture is supposed to preserve. Raw input is normalized into `GuiEvent` before app-level dispatch. Scene-contained runtime work is scene-isolated. Window focus candidate ordering is deterministic and sorted by `control_id`. Scheduler message dispatch time is clamped to a fraction of frame time with fixed bounds: `0.12` of dt milliseconds, a `0.5 ms` floor, and a `4.0 ms` ceiling. Workspace restore skips missing settings keys instead of aborting the whole restore. Those guarantees are useful because they turn architectural claims into measurable runtime behavior.

The app event pipeline in `GuiApplication.process_event()` makes those guarantees concrete. It normalizes raw input through `EventManager.to_gui_event()`. It terminates early for `QUIT`. It updates shared input state, reconciles logical pointer position, and preserves raw pointer data while producing logicalized pointer events. It applies pointer lock and pointer capture rules before routing. Global pointer actions run before normal scene dispatch, then toast routing, task-panel focus exit checks, overlay routing, keyboard routing, direct feature handlers, routed feature handlers, screen lifecycle handlers, scene dispatch, and finally any fallthrough handlers. At every stage, `default_prevented` and `propagation_stopped` are hard stop signals, not suggestions.

That routing order explains several user-visible behaviors. Overlay clicks are routed before focus changes when needed so an open flyout does not dismiss itself before it can receive the click. Command palette dismissal on left click is handled in the overlay path, while the separate command-palette action bind is registered as a global pointer action when declared. Pointer events originating in windows are distinguished from scene-level dispatch. Keyboard routing gives overlays first chance to handle keys such as dismissal gestures. The architecture is therefore not just a list of subsystems; it is a deliberate dispatch order designed to make mixed overlay, focus, scene, and window interactions deterministic.

The architecture also has explicit non-goals. `gui_do` does not promise OS-native widget parity across platforms. It does not replace domain-layer architecture decisions for your business logic. It does not treat star-import behavior as part of the compatibility contract. And it does not recommend internal infrastructure tiers as beginner entry points when a Tier 1 or Tier 2 surface already exists for the same job.

[Back to Table of Contents](#table-of-contents)

## Feature Organization Conventions
[Back to Table of Contents](#table-of-contents)

Each feature should live in its own folder under a feature root such as `demo_features/`. That is not just a style preference. It is the package boundary that allows a feature to grow without turning into an unstructured set of cross-imports. A small feature may begin as one file, but once it gains lifecycle hooks, presenter logic, scene specs, helper builders, data helpers, and routed runtime wiring, the cost of keeping everything together rises quickly. A dedicated package gives the feature a private growth space while preserving a stable public entry surface.

That package should be a real Python package with `__init__.py` as the supported integration surface. The repository demonstrates this consistently. `demo_features/main/__init__.py`, `demo_features/showcase/__init__.py`, and `demo_features/systems/__init__.py` exist specifically to mark the package boundary and to give the rest of the application one import surface that is independent of internal file layout. Bootstrap code and cross-feature code should depend on that package root rather than importing deep implementation files by habit.

The growth pattern inside a package should be concern-driven. `demo_features/main` splits its scene feature across `main_feature.py`, `main_specs.py`, and `main_build_helpers.py`. `demo_features/showcase` grows into several focused helpers for basics, advanced controls, extended controls, runtime helpers, and specs. `demo_features/systems` expands further into feature, presenter, models, and multiple helper modules for data, graphics, history, persistence, scheduling, state, text, theme, validation, and infrastructure. That evolution is exactly what the package convention is for: the file names make responsibilities visible, while the package boundary keeps the public integration surface narrow.

This layout also scales better once routed runtime facilities and feature-to-feature coordination are involved. A feature that publishes services, owns projections, subscribes to stores, exposes windows, and coordinates workflows benefits from having one package-local place for runtime specs, another for presenter or UI code, and another for domain helpers. Without that structure, lifecycle ownership and runtime wiring become difficult to review because unrelated concerns accumulate in the same file.

The recommended import rule is therefore simple: import a feature package from its package root whenever you are operating at bootstrap or cross-feature composition level, and keep package-internal helper imports inside that package. This keeps the application's public composition graph stable even when a package is reorganized internally.

```python
# package root surface
from demo_features.main import FEATURE_PACKAGE_INFO

# package-local implementation files stay inside the package
from demo_features.main.main_specs import MAIN_RUNTIME_SPEC
from demo_features.main.main_feature import MainFeature
```

[Back to Table of Contents](#table-of-contents)

## Core Workflow: Build, Bind, Route, Update, Draw
[Back to Table of Contents](#table-of-contents)

`gui_do` applications are easiest to reason about when you treat them as a five-phase programming model. `build` creates stable structure. `bind_runtime` attaches live dependencies. `route` moves input and messages to the right destination. `update` advances frame-based work. `draw` handles custom rendering that is not naturally expressed through existing controls. The phases are not interchangeable, and most early bugs come from crossing their boundaries carelessly.

`build()` is where a feature should instantiate controls, create scene-local roots, arrange presenter structure, and initialize local observables that do not yet depend on sibling features or runtime services. The important invariant is negative: do not attach runtime subscriptions here when they require cross-feature state, application managers, or other scene objects that may not exist yet. The `MainFeature` and `ShowcaseFeature` both illustrate this split. They create structure in `build()`, then rely on runtime helpers in `bind_runtime()` for dynamic wiring.

`bind_runtime()` is the phase for host-dependent wiring. This is where action keys, palette bindings, event subscriptions, state selectors, logic aliases, and feature-owned overlays should be attached. By the time this phase runs, sibling features have built and host resources are available. In the repository, `MainFeature.bind_runtime()` calls `setup_routed_runtime()` with `MAIN_RUNTIME_SPEC`, then registers an Escape global key. `ShowcaseFeature.bind_runtime()` similarly derives a `RoutedRuntimeSpec`, adds observable effects, and then delegates lifecycle-owned wiring to the routed runtime helper. That is the intended pattern: build structure first, then bind live behavior against completed structure.

Route is the combined input and message delivery phase. User input becomes `GuiEvent` and moves through the application event pipeline. Feature coordination uses `FeatureMessage` instead of direct references when a loose contract is preferable. `LogicFeature` is the lightweight coordination hub for command-like messages and shared domain behavior; `RoutedFeature` is the topic-driven variant that integrates naturally with routed runtime helpers. Use observable state when many consumers need to react continuously to values. Use messages when you want discrete intent transfer without turning the sender into a holder of direct consumer references.

`on_update()` is for frame-based logic, not for synthetic polling that should have been reactive. This is where scheduler-backed workloads, animation progression, and runtime-system `on_update` hooks belong. Routed runtime facilities integrate here by attaching `_routed_runtime_on_update` during setup, which `RoutedFeature.on_update()` invokes before draining queued topic messages. That means higher-level facilities such as workflow coordination, recompute orchestration, QoS policy, health monitoring, replay capture, and projections can participate in per-frame work without forcing each feature to hand-wire every subsystem call.

`draw()` is the escape hatch for rendering concerns that are not naturally expressed through the control tree. Direct features and custom render helpers live here. The key is to keep draw focused on rendering, not on late mutation of application structure. When a control or presenter can express the UI, use that first. Reach for custom drawing when you need a direct surface path, graphics primitives, or effects that do not belong inside a standard control.

`RoutedRuntimeSpec` and `RoutedFeatureLifecycleSpec` exist to reduce the amount of repeated runtime glue a feature has to write. They are most valuable when one feature needs multiple hotkeys, runtime-managed shortcut overlays, task-panel focus toggles, event subscriptions, service publication or consumption, store selectors, observable effects, signal connections, or operation handlers with failure policy. They are also the control-plane for the higher-level faculties introduced later in the manual: dependency validation, workflow coordination, recompute graphs, QoS policies, health probes, replay harnesses, hot-swap policy, policy admission, effect lifetime, event pipelines, durable queues, capability negotiation, and projections.

The lifecycle wrappers around those specs matter. `bind_routed_feature_lifecycle()` resolves a runtime spec, registers any companion providers, creates any needed scene scheduler, and calls `setup_routed_runtime()`. `shutdown_routed_feature_lifecycle()` performs the symmetric unwind, including scope disposal and attribute cleanup. The point is not convenience alone. It is ensuring that a feature whose runtime surface grows over time still has one obvious place where setup happens and one obvious place where teardown is guaranteed.

```python
from gui_do import ObservableEffectSpec, RoutedRuntimeSpec, SceneCommandPaletteSpec, PaletteInputBindSpec


runtime_spec = RoutedRuntimeSpec(
	scene_name="main",
	observable_effects=(
		ObservableEffectSpec(
			handler=lambda value: None,
			observable_attr_name="_live_value",
			invoke_immediately=True,
		),
	),
	command_palette=SceneCommandPaletteSpec(
		scene_name="main",
		toggle=PaletteInputBindSpec(action_name="command_palette_toggle", key=294),
		action=PaletteInputBindSpec(action_name="command_palette_action", pointer_button=2),
	),
)
```

[Back to Table of Contents](#table-of-contents)

## Main Systems Reference
[Back to Table of Contents](#table-of-contents)

### General Usage of gui_do Systems
[Back to Table of Contents](#table-of-contents)

The systems chapters are designed to be read as cooperating parts of one runtime rather than as unrelated API inventories. `gui_do` is modular, but the modules are held together by the same three ideas throughout the codebase: declarative control-plane specs, runtime-plane managers that realize those specs, and lifecycle-owned teardown. For every system, the practical questions are the same: what do you declare, what runtime object or manager realizes that declaration, and during which lifecycle phase does the ownership begin and end?

Three optional facilities make that pattern easy to see. The task panel exists only if you declare it with `SceneTaskPanelSpec` and then add task-panel items or an automatic window-toggle group. The unified menu strip exists only if you opt into it with `MenuStripSpec` and one of the creation helpers such as `add_menu_strip_from_spec()`, `add_standard_menu_strip()`, or `add_window_menu_strip()`. The command palette exists only when routed runtime wiring includes `SceneCommandPaletteSpec`, with overall entry behavior shaped by `PaletteBindingSpec`. The runtime operating contracts are explicit that omitted facilities remain omitted; the framework does not create them as hidden defaults.

That opt-in model means lifecycle discipline matters more than convenience wiring. Global keys, pointer buttons, scene-scoped actions, and overlay toggles for these facilities should be attached in `bind_runtime()` and unwound in `shutdown_runtime()` or the routed runtime shutdown path. `TaskPanelFocusToggleSpec`, `ActionHotkeySpec`, `ShortcutOverlaySpec`, `GlobalPointerActionSpec`, and `SceneCommandPaletteSpec` all exist so those bindings can be registered declaratively and torn down with the owning scene or feature.

Best practice is to keep optional facilities discoverable and bounded. Pair hotkeys with visible affordances such as menu items, task-panel buttons, or shortcut overlays. Use explicit opt-in and opt-out fields rather than relying on assumptions about menu or window participation. Treat focus and dismissal behavior as part of the feature contract instead of a patch-up job after the UI exists. And if a facility is scene-local, keep its bindings scene-local as well.

```python
from gui_do import (
	MenuStripSpec,
	PaletteInputBindSpec,
	SceneCommandPaletteSpec,
	SceneTaskPanelSpec,
	TaskPanelFocusToggleSpec,
)


task_panel_spec = SceneTaskPanelSpec(scene_name="main", control_id="task_panel")
focus_toggle = TaskPanelFocusToggleSpec(action_name="toggle_task_panel_focus", scene_name="main", key=282)
palette_spec = SceneCommandPaletteSpec(
	scene_name="main",
	toggle=PaletteInputBindSpec(action_name="command_palette_toggle", key=294),
	action=PaletteInputBindSpec(action_name="command_palette_action", pointer_button=2),
)
menu_spec = MenuStripSpec(control_id="main_menu", rect=(0, 0, 800, 28), scene_name="main")
```

See [Appendix F: Specifications and Option Reference](#appendix-f-specifications-and-option-reference) for the full option surfaces of the spec types used in these chapters.

### 8.1 Application Bootstrap and Host Configuration
[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Application bootstrap is the deterministic assembly phase of `gui_do`. `HostApplicationBindingSpec`, `HostApplicationConfig`, `build_host_application_config()`, and `bootstrap_host_application()` exist so a developer can describe application structure once and let the framework realize the full graph of scenes, features, actions, windows, cursors, and host-owned runtime members in a predictable order.

#### Mental model and lifecycle placement

Think of bootstrap as a config-to-runtime transformation. A host object starts as plain Python. `build_host_application_config()` normalizes the declarative binding graph into concrete spec collections. `bootstrap_host_application()` then creates and attaches the live `GuiApplication`, registers scene setup and runtime-scene policy, instantiates features, binds windows and actions, and leaves the host with a usable `app`. Feature `build()` and `bind_runtime()` happen after this host-level assembly path is in place.

#### Primary public APIs and key types

The main surface is `HostApplicationBindingSpec`, `HostApplicationConfig`, `bootstrap_host_application`, `build_host_application_config`, `FeatureSpec`, `WindowSpec`, `RuntimeSceneSpec`, `ActionSpec`, `SceneSetupSpec`, `SceneBundleBindingSpec`, `FeatureWindowBundleBindingSpec`, `CursorSpec`, `FontRoleBindingSpec`, `PaletteBindingSpec`, `TelemetryConfig`, `GuiApplication`, `create_display`, `SceneTransitionManager`, and `SceneTransitionStyle`. The related `build_*` helpers matter because they are the supported normalization path from shorthand bindings to concrete config objects.

See [Appendix F: Specifications and Option Reference](#appendix-f-specifications-and-option-reference) for the bootstrap and composition spec families.

#### Typical usage flow

1. Declare the display, window title, and initial scene in one `HostApplicationBindingSpec`.
2. Add scene setup, runtime-scene, feature, and action declarations directly or via bundle specs.
3. Normalize the config through `build_host_application_config()`.
4. Call `bootstrap_host_application(host, config)` from the entrypoint.
5. Run `host.app.run_entrypoint()` when the host is ready to enter the event loop.

#### Minimal example

```python
from gui_do import HostApplicationBindingSpec, bootstrap_host_application, build_host_application_config


class AppHost:
	pass


host = AppHost()
config = build_host_application_config(
	HostApplicationBindingSpec(
		display_size=(1280, 720),
		window_title="example",
		fonts={"default": {"file": "demo_features/data/fonts/Gimbot.ttf", "size": 14}},
		initial_scene_name="main",
	)
)
bootstrap_host_application(host, config)
```

#### Advanced pattern(s)

The repository's demo uses the more scalable bundle pattern. `SceneBundleBindingSpec` emits scene setup, runtime-scene startup behavior, navigation actions, and optional scene roots from one declaration. `FeatureWindowBundleBindingSpec` pairs feature factories with window toggle metadata. This keeps the host config compact while still letting the builder resolve cross-references in one deterministic pass.

#### Common mistakes and anti-patterns

Common bootstrap failures are structural. A feature can be registered for a scene that never exists. `initial_scene_name` can fail to match any declared scene. Host attributes can be mutated imperatively after bootstrap in ways that bypass the spec graph and make the application's source of truth harder to follow. Another frequent mistake is writing relative file paths as though they were module-relative; in this framework they resolve from the process current working directory unless already absolute.

#### Cross-links to related systems

Bootstrap hands off directly to [8.2 Feature Lifecycle and Feature Types](#82-feature-lifecycle-and-feature-types), [8.3 Events, Actions, Input Mapping, and Routing](#83-events-actions-input-mapping-and-routing), [8.9 Scene, Window, and Task-Panel Presentation Models](#89-scene-window-and-task-panel-presentation-models), and [8.11 Persistence and Workspace/Session State](#811-persistence-and-workspacesession-state).

[Back to Table of Contents](#table-of-contents)

### 8.2 Feature Lifecycle and Feature Types
[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Features are the framework's primary unit of behavior. `Feature`, `DirectFeature`, `LogicFeature`, `RoutedFeature`, `FeatureMessage`, and `FeatureManager` exist so UI composition, message coordination, scene membership, and teardown happen in a deterministic order rather than being scattered through unrelated callbacks.

#### Mental model and lifecycle placement

Each feature owns a slice of the application lifecycle. `build()` is for stable structure. `bind_runtime()` is for runtime wiring once siblings and host services exist. `handle_event()` receives routed events. `on_update()` performs per-frame logic. `draw()` handles custom rendering. `shutdown_runtime()` unwinds runtime-owned resources. `DirectFeature` is the direct-surface path. `LogicFeature` is the non-UI coordination path. `RoutedFeature` adds topic-based message dispatch and a natural fit for routed runtime helpers.

#### Primary public APIs and key types

The key public names are `Feature`, `DirectFeature`, `LogicFeature`, `RoutedFeature`, `FeatureMessage`, `FeatureManager`, `ScenePresentationModel`, `RoutedFeatureLifecycleSpec`, `bind_routed_feature_lifecycle()`, `shutdown_routed_feature_lifecycle()`, `register_routed_feature_companions()`, `setup_routed_runtime()`, and `shutdown_routed_runtime()`. `HOST_REQUIREMENTS` is the hook-specific dependency declaration protocol used by the feature classes.

See [Appendix F: Specifications and Option Reference](#appendix-f-specifications-and-option-reference) for routed runtime, operation, and higher-level runtime spec families.

#### Typical usage flow

1. Choose the feature subtype that matches the behavior.
2. Declare hook-specific host dependencies in `HOST_REQUIREMENTS`.
3. Build controls or scene-local visuals in `build()`.
4. Attach live wiring in `bind_runtime()`.
5. Handle input or messages through `handle_event()` and `on_update()`.
6. Unwind runtime-owned state in `shutdown_runtime()`.

#### Minimal example

```python
from gui_do import Feature, ObservableValue


class CounterFeature(Feature):
	HOST_REQUIREMENTS = {"bind_runtime": (), "shutdown_runtime": ()}

	def __init__(self) -> None:
		super().__init__("counter", scene_name="main")
		self.count = ObservableValue(0)
		self._unsubscribe = None

	def bind_runtime(self, host) -> None:
		self._unsubscribe = self.count.subscribe(lambda value: None)

	def shutdown_runtime(self, host) -> None:
		if callable(self._unsubscribe):
			self._unsubscribe()
			self._unsubscribe = None
```

#### Advanced pattern(s)

The most useful advanced pattern is logic-plus-presentation composition. A `LogicFeature` owns domain state or background coordination. A companion `RoutedFeature` or standard `Feature` subscribes to that state and drives controls or presenters. `RoutedFeatureLifecycleSpec` keeps companion registration and runtime setup declarative, while `bind_routed_feature_lifecycle()` and `shutdown_routed_feature_lifecycle()` preserve symmetry.

Another advanced pattern is scope-owned runtime wiring. If a feature needs service publication or consumption, store selectors, observable effects, signal bindings, operation handlers, command palette binds, task-panel focus toggles, or higher-level faculties such as policy engines and projections, route that through `setup_routed_runtime()` so the same ownership model handles setup and teardown.

#### Common mistakes and anti-patterns

Subscribing in `build()` is the most common lifecycle bug because runtime dependencies may not exist yet. Using a regular `Feature` for direct-surface animation or heavy draw work that belongs in `DirectFeature` is another mismatch. The routed-runtime anti-pattern is partial teardown: clearing one attribute manually while event subscriptions, selectors, or runtime scopes continue to live. If you used the routed lifecycle helpers, use the matching shutdown helper as well.

#### Cross-links to related systems

Lifecycle rules connect directly to [8.1 Application Bootstrap and Host Configuration](#81-application-bootstrap-and-host-configuration), [8.4 State and Observables](#84-state-and-observables), [8.10 Scheduling, Timing, Animation, and Transitions](#810-scheduling-timing-animation-and-transitions), and [8.16 Telemetry, Introspection, and Operational Hooks](#816-telemetry-introspection-and-operational-hooks).

[Back to Table of Contents](#table-of-contents)

### 8.3 Events, Actions, Input Mapping, and Routing
[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

This chapter covers the path from raw input to named behavior. `GuiEvent`, `EventType`, `EventPhase`, `EventManager`, `EventBus`, `Signal`, `ActionManager`, `ActionRegistry`, `InputMap`, `InputBinding`, `KeyChordManager`, `KeyChord`, `ChordStep`, and the focus-related routing managers exist so the application can interpret input consistently instead of duplicating routing logic across features.

#### Mental model and lifecycle placement

Raw pygame events become normalized `GuiEvent` instances first. Routing then proceeds through the application's stable dispatch order: early quit handling, shared input-state update, logical pointer reconciliation, global pointer actions, overlay and toast routing, keyboard routing, feature handlers, screen handlers, scene dispatch, and fallthrough handlers. Named actions sit above raw input so user-facing behavior can be rebound or scoped without rewriting feature event code.

#### Primary public APIs and key types

`GuiEvent` carries `kind`, `type`, `key`, `pos`, `rel`, `raw_pos`, `raw_rel`, `button`, `wheel_x`, `wheel_y`, `mod`, `text`, `control_id`, `group`, `window`, `task_panel`, `task_id`, `error`, `source_event`, `phase`, `propagation_stopped`, and `default_prevented`. The public event kinds are `PASS`, `QUIT`, `KEY_DOWN`, `KEY_UP`, `MOUSE_BUTTON_DOWN`, `MOUSE_BUTTON_UP`, `MOUSE_MOTION`, `MOUSE_WHEEL`, `TEXT_INPUT`, and `TEXT_EDITING`. On the action side, the important names are `ActionDescriptor`, `ActionRegistry`, `ActionManager`, `ActionContext`, `ActionMiddleware`, `InputMap`, `InputBinding`, `ActionSpec`, `ActionHotkeySpec`, `ControlKeyBindingSpec`, and `EventSubscriptionSpec`.

See [Appendix F: Specifications and Option Reference](#appendix-f-specifications-and-option-reference) for action, input, and overlay-related spec families.

#### Typical usage flow

1. Declare a named action through `ActionSpec` or `ActionDescriptor`.
2. Bind it through `ActionHotkeySpec`, `ControlKeyBindingSpec`, `InputMap`, or routed runtime helpers.
3. Let `GuiApplication.process_event()` normalize and route the input.
4. Respect `default_prevented` and `propagation_stopped` in custom routing extensions.
5. Keep scene and window scope explicit whenever input should not be global.

#### Minimal example

```python
from gui_do import ActionBindingSpec, ActionHotkeySpec, RoutedRuntimeSpec


actions = (
	ActionBindingSpec(kind="exit", action_id="exit", label="Exit", category="File"),
	ActionBindingSpec(kind="palette_toggle", action_id="palette_toggle", label="Toggle Command Palette"),
)

runtime_spec = RoutedRuntimeSpec(
	scene_name="main",
	action_hotkeys=(
		ActionHotkeySpec(action_name="show_help", handler=lambda event: True, key=298, scene_name="main"),
	),
)
```

#### Advanced pattern(s)

`InteractionStateMachine` is the right abstraction when an interaction has phases such as press, drag, guarded transition, and release. `EventRecorder`, `EventPlayback`, and `RecordedEvent` support deterministic test scenarios and replay debugging. `KeyChordManager` models actions that depend on sequences rather than one key. The command palette's two-bind model is another advanced routing pattern: `SceneCommandPaletteSpec` registers independent `toggle` and `action` binds, and the first `action` trigger when closed is consumed immediately after opening the palette.

#### Common mistakes and anti-patterns

Bypassing `GuiEvent` normalization and handling raw pygame events directly usually breaks consistency around pointer locking, overlay routing, and scene scoping. Another common mistake is assuming an action is global when it was registered for a specific scene or window scope. Custom routing code that ignores `propagation_stopped` or `default_prevented` is also incorrect because the app loop treats those flags as hard stops.

#### Cross-links to related systems

Routing interacts directly with [8.2 Feature Lifecycle and Feature Types](#82-feature-lifecycle-and-feature-types), [8.7 Focus and Accessibility](#87-focus-and-accessibility), [8.8 Overlays, Dialogs, Notifications, and Command Surfaces](#88-overlays-dialogs-notifications-and-command-surfaces), and [8.9 Scene, Window, and Task-Panel Presentation Models](#89-scene-window-and-task-panel-presentation-models).

[Back to Table of Contents](#table-of-contents)

### 8.4 State and Observables
[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Reactive state is the framework's preferred path for keeping UI synchronized with changing values. `ObservableValue`, `ObservableList`, `ObservableDict`, `CollectionChange`, `ComputedValue`, `reactive_batch()`, `PresentationModel`, `Binding`, `BindingGroup`, `CollectionView`, `CollectionViewQuery`, `SelectionModel`, `SelectionMode`, `AppStateStore`, `StateSelector`, and `StateTransaction` exist so features and controls can react to change without maintaining manual refresh trees.

#### Mental model and lifecycle placement

Observables are the local reactive bus. The app state store is the broader transactional bus for shared application state. Features usually create their observable state early, but they should attach subscriptions in `bind_runtime()` so controls and sibling features already exist. Teardown belongs in `shutdown_runtime()` or the owning runtime scope. Derived state belongs in `ComputedValue` or selectors rather than in hand-maintained mirrored variables.

#### Primary public APIs and key types

`ObservableValue` provides `.value`, `.subscribe()`, `set_silently()`, `force_notify()`, and `observer_count`. `ObservableList` and `ObservableDict` publish `CollectionChange` instances using `ChangeKind` values such as `ADDED`, `REMOVED`, `REPLACED`, `CLEARED`, and `MOVED`. `ComputedValue` supports explicit or auto-tracked dependencies. `reactive_batch()` and `is_batching()` define batching semantics. `AppStateStore` offers key subscriptions, selectors, transactions, snapshot, and restore. The declarative routed-runtime bridge is `StoreSubscriptionSpec`, `StoreSelectorSpec`, `ObservableEffectSpec`, and `SignalEffectSpec`.

#### Typical usage flow

1. Create owned observable or store-backed state.
2. Subscribe or select in `bind_runtime()`.
3. Use `ComputedValue`, selectors, or `CollectionView` for derived state rather than manual duplication.
4. Use `reactive_batch()` or `StateTransaction` for grouped updates.
5. Dispose the subscription owner during runtime shutdown.

#### Minimal example

```python
from gui_do import ComputedValue, ObservableValue, reactive_batch


count = ObservableValue(0)
label_text = ComputedValue(lambda: f"Count: {count.value}")
events = []
unsubscribe = label_text.subscribe(events.append)

with reactive_batch():
	count.value = 1
	count.value = 2

unsubscribe()
```

#### Advanced pattern(s)

Use `AppStateStore` when several features share one authoritative state source. `StateSelector` supports dependency-aware updates so only selectors affected by changed keys recompute. `StateTransaction` groups several patches into one atomic commit. `CollectionView` and `CollectionViewQuery` are the right tools for filtered or sorted reactive views over changing collections.

The declarative reactive path is often the cleaner scaling path. `StoreSubscriptionSpec` and `StoreSelectorSpec` register state-store listeners through routed runtime ownership. `ObservableEffectSpec` and `SignalEffectSpec` do the same for arbitrary observables and signals. That turns reactive binding into a lifecycle-owned declaration instead of another manual cleanup list.

#### Automatic Subscription Ownership and Cleanup

Automatic subscription ownership exists because reactive GUI code is otherwise easy to tear down incorrectly. In `gui_do`, a feature-bound handler subscribed to an `ObservableValue` can be associated automatically with the feature. If the feature already has a `FeatureRuntimeScope`, ownership is delegated there. If not, the feature still maintains a fallback runtime subscription list. This is a consistency model for lifecycle safety, not just a convenience trick.

The mechanism reduces manual unsubscribe bookkeeping and prevents setup and shutdown logic from drifting apart. A callback added during `bind_runtime()` does not need a developer to remember a second file or distant branch later if the runtime scope already owns it. The operational benefit is broad: it mitigates subscription leaks, retained feature instances after teardown, callbacks into dead UI, duplicate callbacks after repeated bind cycles, and partial cleanup during scene transitions.

It is still important to keep explicit lifecycle discipline. Automatic ownership complements `bind_runtime()` and `shutdown_runtime()`; it does not make those phases optional. The safe pattern is to bind in the correct phase and let the owning feature or runtime scope perform release during shutdown.

```python
# fragile manual path
unsubscribe = observable.subscribe(handler)
# if shutdown forgets to call unsubscribe(), the feature remains referenced

# lifecycle-owned path
runtime_scope.subscribe(observable, handler)
# runtime_scope.dispose() releases the callback automatically
```

#### Common mistakes and anti-patterns

Polling `.value` in `on_update()` instead of subscribing wastes frame time and introduces latency. Subscribing in `build()` before runtime dependencies exist creates timing bugs. Sharing plain Python lists or dicts across features breaks the reactive contract because nobody is notified when they change. The routed-runtime anti-pattern is declaring selectors or observable effects but never disposing the owning runtime scope.

#### Cross-links to related systems

Reactive state underpins [8.2 Feature Lifecycle and Feature Types](#82-feature-lifecycle-and-feature-types), [8.6 Layout Systems](#86-layout-systems), [8.9 Scene, Window, and Task-Panel Presentation Models](#89-scene-window-and-task-panel-presentation-models), and [8.13 Text, Input, Forms, and Validation Systems](#813-text-input-forms-and-validation-systems).

[Back to Table of Contents](#table-of-contents)

### 8.5 Controls and Control Composition
[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Controls are the reusable UI primitives that features compose into a scene-owned tree. The control tree is where hit testing, drawing, accessibility metadata, and most focus traversal live, so features do not need to solve those concerns independently. `gui_do` deliberately exposes both basic controls and a large extended-control surface because different features need different levels of specialization without abandoning the common tree model.

#### Mental model and lifecycle placement

Controls belong to containers. Containers belong to a scene root, a floating window, or an overlay surface. A feature owns the controls it creates, usually from `build()`, and then binds runtime behavior to them in `bind_runtime()`. Controls should mirror state, not act as the only source of truth for state. When a feature is torn down, its controls should disappear with the owning scene or window instead of being held alive by cross-feature references.

#### Primary public APIs and key types

The basic Tier 12 controls are `PanelControl`, `LabelControl`, `ButtonControl`, `ToggleControl`, `SliderControl`, `ScrollbarControl`, `CanvasControl`, `CanvasEventPacket`, `CanvasViewport`, `FrameControl`, `ImageControl`, `ArrowBoxControl`, `ButtonGroupControl`, `TabControl`, `TabItem`, and `DockWorkspacePanel`. The extended Tier 13 controls include `TextInputControl`, `TextAreaControl`, `RichLabelControl`, `DropdownControl`, `DropdownOption`, `ListViewControl`, `ListItem`, `OverlayPanelControl`, `DataGridControl`, `GridColumn`, `GridRow`, `TreeControl`, `TreeNode`, `SplitterControl`, `SpinnerControl`, `RangeSliderControl`, `ColorPickerControl`, `ScrollViewControl`, `ProgressBarControl`, `AnimatedImageControl`, `ErrorBoundary`, `WindowControl`, `TaskPanelControl`, `WindowPresenter`, `MenuEntry`, `MenuStripControl`, `SceneMenuOptions`, `WindowMenuOptions`, `NotificationPanelControl`, `PropertyInspectorPanel`, `ToolbarControl`, `ToolbarItem`, `StatusBarControl`, `StatusSlot`, `ExpanderControl`, `DatePickerControl`, `TimePickerControl`, `BreadcrumbControl`, `BreadcrumbItem`, `SplitButtonControl`, `SplitButtonOption`, and `ChipInputControl`.

Higher-level control-composition helpers include `ControlDefinition`, `build_specs_from_column_section()`, `RowCellSpec`, `build_horizontal_row_specs()`, and `build_multi_column_grid_specs()`. These matter when a feature wants declarative control grids rather than manual child creation one widget at a time.

#### Typical usage flow

1. Create a root container in `build()`.
2. Add child controls to that container or presenter.
3. Set focusability and accessibility metadata as part of the structural build.
4. Bind observables, callbacks, and routed runtime effects in `bind_runtime()`.
5. Keep cross-feature coordination in observables or messages rather than direct control references.

#### Minimal example

```python
from pygame import Rect

from gui_do import ButtonControl, LabelControl, PanelControl


def build(self, host):
	self.root = host.app.add(PanelControl("my_root", Rect(0, 0, 400, 300)), scene_name="main")
	self.label = self.root.add(LabelControl("status", Rect(8, 8, 200, 24), "Ready"))
	self.root.add(ButtonControl("go", Rect(8, 40, 100, 28), "Go", on_click=self._on_go))
```

#### Advanced pattern(s)

The presenter pattern is the most important advanced control-composition technique. `WindowPresenter` keeps floating-window layout and control creation inside a presenter object while the owning feature remains focused on lifecycle and routing. When a window has tabbed content, combine that with `TabbedPresenterSpec`, `TabBuilderSpec`, `build_tab_builder_specs()`, `create_tab_control_from_specs()`, `compute_tabbed_window_layout()`, and `setup_feature_presenter_tabs()`.

`CanvasControl` and `CanvasViewport` are the right choice when a subtree needs custom drawing with canvas-local coordinate handling instead of standard control visuals. `ErrorBoundary` is the right containment choice when a control subtree is experimental or likely to raise during render or event handling and you want a fallback instead of a frame-level failure.

#### Common mistakes and anti-patterns

The main anti-pattern is turning controls into the source of truth for state. A text field or toggle can display and emit state changes, but the durable state should usually live in an observable or store. Another mistake is holding direct references to controls owned by other features; that creates hidden coupling and breaks teardown assumptions. Building or restructuring controls in `on_update()` is also usually wrong because it mixes frame logic with structural lifetime.

#### Cross-links to related systems

Controls depend directly on [8.2 Feature Lifecycle and Feature Types](#82-feature-lifecycle-and-feature-types), [8.4 State and Observables](#84-state-and-observables), [8.6 Layout Systems](#86-layout-systems), [8.7 Focus and Accessibility](#87-focus-and-accessibility), and [8.9 Scene, Window, and Task-Panel Presentation Models](#89-scene-window-and-task-panel-presentation-models).

[Back to Table of Contents](#table-of-contents)

### 8.6 Layout Systems
[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Layout systems exist so features can describe spatial intent without hardcoding brittle pixel arithmetic everywhere. `gui_do` exposes several layout families because no single policy fits every region: linear panels, track-based grids, flow layouts, dock workspaces, viewport-aware arrangements, adaptive constraint policies, and virtualization-oriented measurement all serve different UI shapes.

#### Mental model and lifecycle placement

Choose the simplest layout family that matches the region. Use linear or grid composition for ordinary UI panels. Use constraint-based placement where relationships matter more than tracks. Use adaptive policies when the viewport should alter the arrangement. Use dock and virtualization systems when the UI becomes workspace-like or data-heavy. Structural layout definitions belong in `build()`, while any runtime-driven layout invalidation or breakpoint switching belongs in `bind_runtime()` or per-frame update only when it actually depends on changing runtime inputs.

#### Primary public APIs and key types

The layout surface spans `LayoutAxis`, `ConstraintLayout`, `AnchorConstraint`, `DockPane`, `DockTabs`, `DockSplit`, `DockWorkspace`, `FlexLayout`, `FlexItem`, `FlexDirection`, `FlexAlign`, `FlexJustify`, `GridLayout`, `GridTrack`, `GridPlacement`, `LayoutAnimator`, `LayoutPass`, `MeasureContext`, `ArrangeContext`, `LayoutRoot`, `FlowLayout`, `FlowItem`, `Viewport`, and `WindowLayoutHandler`. The adaptive layer adds `ConstraintAttr`, `LayoutConstraint`, `ConstraintSet`, `AdaptivePolicy`, and `resolve_adaptive_policy()`. The virtualization layer adds `MeasureMode`, `MeasurePolicy`, `VirtualizedWindow`, `RecyclePool`, and `VirtualizationCore`.

#### Typical usage flow

1. Pick a container and the layout family that fits the region.
2. Add children and declare the sizing or placement metadata.
3. Run layout after the tree exists, not before controls are attached.
4. Introduce adaptive or virtualized behavior only when the simpler layout families stop fitting.

#### Minimal example

```python
from gui_do import FlexDirection, FlexItem, FlexLayout


layout = FlexLayout(direction=FlexDirection.ROW, gap=8)
layout.add(FlexItem(control=sidebar, grow=0, basis=200))
layout.add(FlexItem(control=main_area, grow=1))
```

#### Advanced pattern(s)

The advanced responsive pattern is constraint-plus-policy composition. A `ConstraintSet` can describe one relationship graph for a wide layout and another for a narrow one, while `AdaptivePolicy` and `resolve_adaptive_policy()` choose between them based on viewport rules. `DockWorkspace` is the advanced composition model for multi-pane workbenches, and `WindowLayoutHandler` is the host-side helper for desktop-style tiling and placement. When collection-heavy controls need measurement efficiency, the virtualization core provides the identity tracking and recycle-pool path instead of forcing every scrollable view to keep every row live.

#### Common mistakes and anti-patterns

The main layout anti-pattern is mixing incompatible layout owners inside the same region without a clear boundary. Another is hardcoding fixed sizes where the UI actually needs adaptive behavior. Running layout before the children have been attached is also wrong because many layout systems depend on the control tree already existing. Finally, do not reach for virtualization or docking before you need them; simpler families are easier to reason about and test.

#### Cross-links to related systems

Layout connects most strongly to [8.5 Controls and Control Composition](#85-controls-and-control-composition), [8.7 Focus and Accessibility](#87-focus-and-accessibility), [8.9 Scene, Window, and Task-Panel Presentation Models](#89-scene-window-and-task-panel-presentation-models), and [8.15 Graphics and Audio Integration Points](#815-graphics-and-audio-integration-points).

[Back to Table of Contents](#table-of-contents)

### 8.7 Focus and Accessibility
[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Focus management keeps keyboard interaction coherent by ensuring the right node receives the right key events at the right time. Accessibility provides a semantic representation of the UI that testing tools, announcements, and assistive consumers can understand. These systems sit alongside the control tree rather than inside individual control implementations because coherent focus and semantic navigation are cross-cutting concerns.

#### Mental model and lifecycle placement

Focus state is scene- and window-aware. Controls become candidates for focus during structural build, and hidden or disabled controls should fall out of the active traversal path. Accessibility metadata is usually attached when the control or node is created, then announced or traversed at runtime. If a feature uses focus-related subscriptions or scene-level accessibility sequencing, those registrations should follow the same lifecycle rules as other runtime-owned resources.

#### Primary public APIs and key types

The focus surface includes `FocusManager`, `FocusScope`, `FocusScopeManager`, `WindowFocusManager`, and `FocusRing`. The accessibility surface includes `AccessibilityRole`, `LivePoliteness`, `AccessibilityNode`, `AccessibilityTree`, `AccessibilityAnnouncement`, and `AccessibilityBus`. At the spec layer, `AccessibilitySequenceSpec`, `StaticAccessibilitySpec`, and `TaskPanelFocusToggleSpec` are the key declarative hooks that connect accessibility and focus behavior to feature lifecycle and scene composition.

#### Typical usage flow

1. Mark controls as focusable during `build()` and give them coherent tab indices or sequence metadata.
2. Apply static accessibility metadata through `StaticAccessibilitySpec` or explicit control/node configuration.
3. Use `AccessibilitySequenceSpec` when one scene needs an explicit sequence applied from attributes.
4. Use `TaskPanelFocusToggleSpec` or related scene-specific helpers when focus participation depends on window visibility or task-panel mode.

#### Minimal example

```python
from gui_do import AccessibilityNode, AccessibilityRole, AccessibilityTree


tree = AccessibilityTree()
node = AccessibilityNode(role=AccessibilityRole.BUTTON, name="Submit")
tree.root.add_child(node)
```

#### Advanced pattern(s)

`FocusScope` and `FocusScopeManager` are the right tools when a modal or bounded subtree should temporarily trap or narrow focus traversal. `WindowFocusManager` is the coordination layer for per-window focus behavior and deterministic candidate ordering. `FocusRing` is the explicit traversal model for ordered focus candidates, including wrapping and trap behavior. On the accessibility side, `AccessibilityBus` plus `AccessibilityAnnouncement` gives the runtime a dedicated announcement channel instead of forcing semantic updates to piggyback on unrelated event routes.

#### Common mistakes and anti-patterns

Leaving hidden or disabled controls in the active focus path creates keyboard stalls and confusing traversal order. Missing semantic roles on custom canvas-driven widgets makes them effectively invisible to semantic consumers. A common lifecycle anti-pattern is registering focus or accessibility-related observers without a runtime owner; if the feature or dialog disappears while the subscription survives, you keep emitting announcements or focus adjustments against a dead subtree.

#### Cross-links to related systems

Focus and accessibility depend on [8.3 Events, Actions, Input Mapping, and Routing](#83-events-actions-input-mapping-and-routing), [8.5 Controls and Control Composition](#85-controls-and-control-composition), [8.8 Overlays, Dialogs, Notifications, and Command Surfaces](#88-overlays-dialogs-notifications-and-command-surfaces), and [8.9 Scene, Window, and Task-Panel Presentation Models](#89-scene-window-and-task-panel-presentation-models).

[Back to Table of Contents](#table-of-contents)

### 8.8 Overlays, Dialogs, Notifications, and Command Surfaces
[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Transient and modal UI needs its own routing layer. `gui_do` therefore exposes a family of managers rather than one giant overlay abstraction: `OverlayManager`, `DialogManager`, `ToastManager`, `ContextMenuManager`, `CommandPaletteManager`, `TooltipManager`, `MenuBarManager`, `FileDialogManager`, `NotificationCenter`, `ResizeManager`, `CursorManager`, `DragDropManager`, `ClipboardManager`, `TransferManager`, and `ShortcutHelpOverlay`. These systems sit above the main control tree so they can consume input before it leaks into background controls.

#### Mental model and lifecycle placement

Overlays and command surfaces are transient by design. A toast should consume pointer interaction in its own bounds and then disappear. A context menu or command palette should own focus while open and restore or release it on dismissal. A shortcut overlay or dialog should be created and toggled by runtime wiring, not by ad hoc global state. If an overlay path is configured through routed runtime specs, its setup belongs in `bind_runtime()` and its disposal belongs to the owning runtime shutdown path.

#### Primary public APIs and key types

The main overlay and command-surface names are `OverlayManager`, `OverlayHandle`, `Alignment`, `PlacementResult`, `PopupPlacement`, `Side`, `compute_popup_rect()`, `DialogManager`, `DialogHandle`, `ToastManager`, `ToastHandle`, `ToastSeverity`, `ContextMenuManager`, `ContextMenuItem`, `ContextMenuHandle`, `CommandPaletteManager`, `CommandEntry`, `CommandPaletteHandle`, `TooltipManager`, `TooltipHandle`, `MenuBarManager`, `FileDialogManager`, `FileDialogOptions`, `FileDialogHandle`, `NotificationCenter`, `NotificationRecord`, `ResizeManager`, `CursorManager`, `CursorHandle`, `CursorShape`, `DragDropManager`, `DragPayload`, `ClipboardManager`, `TransferData`, `TransferManager`, `ShortcutHelpOverlay`, `ShortcutSection`, and `ShortcutEntry`. At the spec level, `ShortcutOverlaySpec`, `NotificationSpec`, `MenuStripSpec`, `SceneCommandPaletteSpec`, and `PaletteInputBindSpec` are the key declarative bridges.

See [Appendix F: Specifications and Option Reference](#appendix-f-specifications-and-option-reference) for overlay, command-surface, cursor, and accessibility-related spec families.

#### Typical usage flow

1. Use the relevant manager for the transient surface type rather than emulating it in the scene tree.
2. Pair every overlay with a clear dismissal contract.
3. Keep any input or effect bindings that open the overlay tied to the owning feature lifecycle.
4. Prefer spec-driven command-surface setup for repeatable scenes and features.

#### Minimal example

```python
host.toasts.show("File saved", severity=ToastSeverity.SUCCESS)
```

#### Advanced pattern(s)

`ShortcutHelpOverlay` is the clearest example of lifecycle-owned overlay composition. `ShortcutOverlaySpec` lets a feature declare the owning attribute, toggle action name, toggle key, manual shortcut lines, manual section title, section filtering, and action-registry integration. `setup_routed_runtime()` can then create and register the overlay during runtime binding, and the matching shutdown path tears it down with the feature.

##### Unified Menu Strip

The unified menu-strip API is the only supported menu-strip surface. The public names are `MenuStripControl`, `MenuEntry`, `SceneMenuOptions`, `WindowMenuOptions`, `MenuStripSpec`, `add_menu_strip_from_spec()`, `add_standard_menu_strip()`, and `add_window_menu_strip()`. There is no separate regular-menu versus scene-menu narrative to preserve. One control supports both static top-level menus and optional automatic Scene and Window sections.

Static entries are expressed as `MenuEntry` values whose `items` are `ContextMenuItem` callbacks or signal-like actions. Dynamic sections are inserted independently through scene and window menu options. `MenuStripSpec` exposes `scene_menu_insert_index` and `window_menu_insert_index`, so the Scene and Window sections can appear before, after, or between static menus. Their labels are user-configurable through `scene_menu_label` and `window_menu_label`; they are not hardcoded by the runtime contract.

Scene discovery has two modes. With `scene_menu_mode="add_all"`, the strip includes discoverable scenes that satisfy runtime eligibility. With `scene_menu_mode="opt_in"`, it includes only scene names listed in `scene_menu_opt_in_scene_names`. In either mode, the current scene is excluded by default because `scene_menu_include_current_scene` defaults to `False`. The tests verify that if filtering leaves no scene targets, the Scene top-level entry still highlights like any other top-level header but does not open a flyout overlay. That is the intended UX contract: highlightable header, no redundant no-op menu.

Window menu behavior follows the current target scene context and uses the scene's window pretty names or titles. Visibility toggles keep standard callback behavior, and the public opt-out contract is explicit. `window_menu_opt_in` defaults to `True` on `WindowSpec`, `AnchoredWindowSpec`, and `FeatureWindowBundleBindingSpec`. Setting it to `False` removes the window from the Window menu, command palette, and task panel. On the scene side, `MenuStripSpec.scene_menu_opt_in` defaults to `True`; setting it to `False` opts the scene out of the Scene section when opt-in filtering is used.

Use a static-only strip when the scene does not need dynamic navigation or window visibility controls. Use a dynamic strip when scene navigation or window visibility is part of the user's workflow. Choose insertion indices to preserve the expected order of static menus relative to dynamic sections. Choose `add_all` when scene discovery should follow runtime eligibility automatically, and `opt_in` when the scene list is editorial and intentionally curated.

```python
from pygame import Rect

from gui_do import MenuStripSpec, add_menu_strip_from_spec


menu = add_menu_strip_from_spec(
	host.control_showcase_root,
	host,
	MenuStripSpec(
		control_id="control_showcase_menu_bar",
		rect=Rect(0, 0, host.control_showcase_root.rect.width, 28),
		scene_name="control_showcase",
		scenes_shown=True,
		windows_shown=False,
		scene_menu_label="Scene",
		scene_menu_insert_index=0,
		scene_menu_mode="add_all",
		scene_menu_include_current_scene=False,
		tools_exclude_labels=("Open Command Palette (F5)",),
	),
)
```

##### Command Palette and Two-Bind Input Model

The command palette now uses a two-bind model that is explicit in the public spec surface. `PaletteInputBindSpec` defines one bind with `action_name`, optional `key`, and optional `pointer_button`. `SceneCommandPaletteSpec` contains two of them: `toggle` and `action`. The `toggle` bind opens or closes the palette. The `action` bind behaves differently depending on current palette state.

The implementation in `setup_scene_command_palette_bindings()` is precise. If the palette is closed and the `action` bind fires, the handler shows the palette and immediately returns `True`. It does not also try to toggle a window at the current pointer on that same trigger. That is intentional single-event-open behavior: the first action opens the surface, and a later action can target an already visible window entry. If the palette is already open, the `action` handler resolves pointer position from `event.pos` and falls back to `app.logical_pointer_pos` when the event does not carry coordinates. It then calls `palette_manager.try_activate_window_at(pos)`. Non-window entries at that pointer are ignored silently, and the event is still consumed.

The current demo scenes use the same shape. In both `demo_features.main.main_specs` and `demo_features.showcase.showcase_specs`, the toggle bind is `F5` and the action bind is pointer button `2`, the middle mouse button. This means the palette is always reachable by keyboard, while pointer activation can toggle window entries in-place once the palette is open. Tests also verify the stay-open behavior for mouse activation of window entries: if a window entry is activated through pointer targeting, the palette should remain open even if the action path would otherwise trigger focus changes that normally dismiss overlays.

This design is better than a single ambiguous "open" action because it separates palette visibility from entry activation intent. Each bind can use a key, a pointer button, or both independently. Scenes can omit the command palette entirely by not declaring `SceneCommandPaletteSpec` in their routed runtime. And because the binding helper registers these actions through the scene's routed runtime setup, the lifecycle owns their setup and teardown instead of leaving global input bindings behind after a scene exits.

```python
from gui_do import PaletteInputBindSpec, SceneCommandPaletteSpec


palette = SceneCommandPaletteSpec(
	scene_name="main",
	toggle=PaletteInputBindSpec(action_name="command_palette_toggle", key=294),
	action=PaletteInputBindSpec(action_name="command_palette_action", pointer_button=2),
)
```

#### Common mistakes and anti-patterns

The most common overlay mistake is creating a transient surface without a dismissal contract. Another is expecting clicks on toasts or overlays to fall through to background controls. For menu strips, carrying forward a split legacy mental model for separate menu-strip APIs is now wrong; the unified strip is the supported surface. For the command palette, the main mistake is assuming the `action` bind should both open the palette and toggle a window on the same first trigger. The implementation deliberately does not do that.

#### Cross-links to related systems

Overlays and command surfaces interact directly with [8.3 Events, Actions, Input Mapping, and Routing](#83-events-actions-input-mapping-and-routing), [8.7 Focus and Accessibility](#87-focus-and-accessibility), [8.9 Scene, Window, and Task-Panel Presentation Models](#89-scene-window-and-task-panel-presentation-models), and [Appendix F: Specifications and Option Reference](#appendix-f-specifications-and-option-reference).

[Back to Table of Contents](#table-of-contents)

### 8.9 Scene, Window, and Task-Panel Presentation Models
[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Scenes define broad interaction contexts. Windows define focused work surfaces within a scene. Task panels and menu strips provide discoverable chrome for navigation and visibility control. This chapter covers the presentation layer that keeps those surfaces coordinated instead of letting every feature invent its own window and scene management rules.

#### Mental model and lifecycle placement

Scene and window presentation is structural and should therefore be established during `build()`. Visibility toggles, focus participation, and related runtime behavior are then bound in `bind_runtime()`. The mental model is that scenes own collections of windows plus optional scene chrome such as task panels and menu strips. Features should not create presentation surfaces late in `bind_runtime()` if sibling features are expected to bind against them.

#### Primary public APIs and key types

The key public names are `ScenePresentationModel`, `WindowSpec`, `AnchoredWindowSpec`, `SceneTaskPanelSpec`, `TaskPanelButtonSpec`, `TaskPanelSlotLayoutSpec`, `TaskPanelWindowToggleGroupSpec`, `TaskPanelSceneNavButtonSpec`, `TaskPanelFocusToggleSpec`, `FeatureWindowBundleBindingSpec`, `WindowToggleBindingSpec`, `WindowPresenter`, `TabbedPresenterSpec`, `TabBuilderSpec`, `ActiveTabUpdateRouter`, `TabLayoutContext`, `set_window_visible_state()`, `toggle_window_visibility()`, `create_anchored_feature_window()`, `create_feature_presented_window()`, `create_presented_window_from_spec()`, `create_presented_anchored_window()`, `ensure_scene_task_panel()`, `create_task_panel_slot_layout()`, `add_task_panel_button()`, `add_task_panel_buttons()`, `add_task_panel_scene_nav_button()`, `add_scene_task_panel_items()`, and the unified menu-strip helpers covered earlier.

See [Appendix F: Specifications and Option Reference](#appendix-f-specifications-and-option-reference) for window, task-panel, presenter, and routed presentation spec families.

#### Typical usage flow

1. Declare scenes and windows through the bootstrap spec graph.
2. Build presenter-backed windows in `build()`.
3. Use `FeatureWindowBundleBindingSpec` or `WindowToggleBindingSpec` to connect feature-owned windows to task-panel and menu-strip presentation.
4. Bind task-panel focus toggles and other presentation-time actions in `bind_runtime()`.

#### Minimal example

```python
window = create_feature_presented_window(host, spec=window_spec, feature=self, presenter=presenter)
```

#### Advanced pattern(s)

Tabbed windows are the advanced presentation pattern. `TabbedPresenterSpec`, `TabBuilderSpec`, `build_tab_builder_specs()`, and `ActiveTabUpdateRouter` let a window host multiple internal views while routing updates only to the active tab. The scene task-panel composition helpers are another advanced pattern: `SceneTaskPanelSpec` plus `TaskPanelWindowToggleGroupSpec` lets ordinary task-panel buttons and automatic window toggles coexist in one layout, with slot indices preserving visual and focus order.

For scene-local presentation actions that may fail, take time, or need retries, use the routed operation bus rather than burying that logic inside button callbacks. A task-panel or window action can still be user-facing chrome while delegating the underlying work to `FeatureOperationSpec` plus `FailurePolicySpec`.

#### Common mistakes and anti-patterns

Creating windows during `bind_runtime()` instead of `build()` leaves sibling features with nothing stable to target. Forgetting to synchronize task-panel state with window visibility leads to misleading UI chrome. Mismatching scene scope and window scope for action handlers produces commands that appear present but do nothing in the active scene.

#### Cross-links to related systems

Presentation models depend on [8.2 Feature Lifecycle and Feature Types](#82-feature-lifecycle-and-feature-types), [8.5 Controls and Control Composition](#85-controls-and-control-composition), [8.7 Focus and Accessibility](#87-focus-and-accessibility), and [8.8 Overlays, Dialogs, Notifications, and Command Surfaces](#88-overlays-dialogs-notifications-and-command-surfaces).

[Back to Table of Contents](#table-of-contents)

### 8.10 Scheduling, Timing, Animation, and Transitions
[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Frame-based applications need structured time management. `gui_do` provides simple timers, tweens, transition managers, animation sequences, animation state machines, scene timelines, rate limiting, cooperative coroutines, and a cancelable dataflow pipeline so time-based work can stay inside predictable frame budgets.

#### Mental model and lifecycle placement

Scheduling belongs to runtime, not structure. Create timers, tweens, or cooperative workflows during `bind_runtime()` or in reaction to runtime events. Advance them during the app's frame loop. The runtime operating contracts define scheduler dispatch budgeting: the message dispatch budget is clamped to `0.12` of dt milliseconds with a `0.5 ms` floor and a `4.0 ms` ceiling. That policy exists so scheduler work cannot starve rendering under slow or fast frames.

#### Primary public APIs and key types

The core scheduling surface is `TaskEvent`, `TaskScheduler`, `Timers`, `TweenManager`, `TweenHandle`, `Easing`, `AnimationSequence`, `AnimationHandle`, `TransitionManager`, `TransitionSpec`, `TransitionEvent`, `AnimationStateMachine`, `AnimationTransitionMode`, `SceneTimeline`, `Debouncer`, `Throttler`, `CooperativeScheduler`, `CoroutineHandle`, `Pause`, `Sleep`, `WaitForEvent`, `WaitForSignal`, `WaitUntil`, `WaitForAll`, and the dataflow pipeline surface `CancellationToken`, `PipelineStage`, `DataflowPipeline`, and `PipelineHandle`.

#### Typical usage flow

1. Create the timed work during runtime binding or in response to user actions.
2. Let the owning manager tick the work each frame.
3. Cancel or dispose time-based handles during scene or feature teardown.

#### Minimal example

```python
self._tween = host.tweens.to(self.panel, "alpha", 255, duration=0.2)

def workflow(host):
	yield Sleep(1.0)
	host.toasts.show("Done!")

host.scheduler.run(workflow(host))
```

#### Advanced pattern(s)

`CooperativeScheduler` is the advanced workflow path for multi-frame logic that should stay on the frame thread without blocking it. `WaitForSignal`, `WaitForEvent`, `WaitUntil`, and `WaitForAll` let a workflow pause until runtime conditions are satisfied. `AnimationStateMachine` is the advanced path for state-driven animation transitions. `SceneTimeline` is a good fit for scripted scene sequences.

Timeouts and retries are also scheduling concerns. A routed operation with `FailurePolicySpec` uses timer-backed retry and timeout semantics under the hood, which means failure policy is not separate from scheduling; it is scheduled work with lifecycle ownership.

#### Common mistakes and anti-patterns

Putting unbounded work directly in `on_update()` is the classic frame-budget failure. Blocking I/O inside a cooperative coroutine is also wrong; use a dataflow pipeline or another off-main-thread strategy for that. Forgetting to cancel tweens, timelines, or coroutine handles on scene exit is another common leak path because those timed mutations can continue targeting dead controls.

#### Cross-links to related systems

Scheduling connects directly to [8.2 Feature Lifecycle and Feature Types](#82-feature-lifecycle-and-feature-types), [8.14 Data and Dataflow Helpers](#814-data-and-dataflow-helpers), and [8.16 Telemetry, Introspection, and Operational Hooks](#816-telemetry-introspection-and-operational-hooks).

[Back to Table of Contents](#table-of-contents)

### 8.11 Persistence and Workspace/Session State
[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Persistence turns a running UI session into a recoverable workspace. `gui_do` exposes workspace capture and restore, scene snapshots, settings registries, command history, routers, state machines, undo context routing, and snapshot migration so session state can survive restarts and schema evolution.

#### Mental model and lifecycle placement

Persistence is a boundary between live runtime state and serialized state. A `WorkspaceState` stores the active scene, scene snapshot, feature states, settings blocks, metadata, and dock layout. `WorkspacePersistenceManager` captures that data from a running app and restores it later. Restore should be treated as a structured replay, not as a blind overwrite. The runtime contracts require the restore report to expose `target_scene`, `switched_scene`, `restored_feature_states`, `restored_scene_nodes`, `applied_settings`, `skipped_settings`, and `missing_settings_blocks`.

#### Primary public APIs and key types

The persistence surface includes `CommandHistory`, `Command`, `CommandTransaction`, `StateMachine`, `HierarchicalStateMachine`, `Router`, `RouteEntry`, `SettingsRegistry`, `SettingDescriptor`, `WorkspaceState`, `WorkspacePersistenceManager`, `DEFAULT_WORKSPACE_STATE_PATH`, `SceneSnapshot`, `NodeSnapshot`, `UndoContextManager`, `SchemaVersion`, `VersionedSnapshot`, `MigrationStep`, `MigrationRegistry`, `SnapshotMigrator`, `MigrationError`, `make_snapshot()`, and `read_version()`.

See [Appendix F: Specifications and Option Reference](#appendix-f-specifications-and-option-reference) for persistence, migration, and policy-related spec families.

#### Typical usage flow

1. Capture workspace state from the running application.
2. Save the resulting `WorkspaceState` to disk.
3. Load it later and restore through the workspace persistence manager or app facade.
4. Inspect the restore report instead of assuming every setting or snapshot fragment applied successfully.

#### Minimal example

```python
state = host.workspace_persistence.capture(host.app, feature_manager=host.features)
state.save("workspace.json")

loaded = WorkspaceState.load("workspace.json")
report = host.workspace_persistence.restore(loaded, host.app, feature_manager=host.features)
```

#### Advanced pattern(s)

`SnapshotMigrator` is the schema-evolution path. Register `MigrationStep` objects and let the migrator walk old snapshots forward before restore. `SettingsRegistry` plus `SettingDescriptor` gives typed settings a stable persistence boundary. `UndoContextManager` is the multi-stack path when different panels or work areas need independent undo/redo histories routed through one manager.

Persistence actions can also be modeled as routed feature operations with failure policies, especially when save or load work needs structured failure publication, retries, or UI feedback instead of inline callback error handling.

#### Common mistakes and anti-patterns

Assuming every settings key exists is incorrect; missing or unknown keys are supposed to be skipped, not treated as fatal restore failures. Restoring snapshots without version checks is another avoidable mistake; read and migrate versioned snapshots first. `DEFAULT_WORKSPACE_STATE_PATH` is convenient but should not be assumed correct for multi-instance or per-project scenarios.

#### Cross-links to related systems

Persistence connects to [8.1 Application Bootstrap and Host Configuration](#81-application-bootstrap-and-host-configuration), [8.2 Feature Lifecycle and Feature Types](#82-feature-lifecycle-and-feature-types), and [8.16 Telemetry, Introspection, and Operational Hooks](#816-telemetry-introspection-and-operational-hooks).

[Back to Table of Contents](#table-of-contents)

### 8.12 Theme, Styling, and Visual Systems
[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Theming centralizes visual policy so controls and features do not hardcode color, font, and token choices independently. The theme system provides named theme registration, active-theme observables, font role registries, scoped theme overrides, and explicit invalidation for visual caches.

#### Mental model and lifecycle placement

Theme and font registration should happen during config and bootstrap, not after the UI has already started drawing. Runtime theme changes are legitimate, but they should flow through the theme managers and invalidation bus rather than direct patching of individual controls. Treat `DesignTokens` as semantic inputs and the active theme as a reactive runtime value.

#### Primary public APIs and key types

The theme surface is `FontManager`, `FontRoleRegistry`, `ColorTheme`, `ThemeManager`, `DesignTokens`, `ScopedTheme`, `ScopedThemeManager`, and `ThemeInvalidationBus`. The bootstrap-facing spec names that matter here are `FontRoleBindingSpec`, `CursorSpec`, and `CursorBindingSpec`, plus the host-level `fonts` config consumed by bootstrap. `setup_standard_font_roles()` is the convenience path for registering a standard role set from a font config dictionary.

See [Appendix F: Specifications and Option Reference](#appendix-f-specifications-and-option-reference) for font, cursor, bootstrap, and accessibility-related spec families.

#### Typical usage flow

1. Declare fonts and font-role bindings in the host config.
2. Let controls resolve font roles by semantic name.
3. Switch themes through `ThemeManager` or a scoped theme manager when needed.
4. Invalidate cached visuals through `ThemeInvalidationBus` rather than polling for theme changes.

#### Minimal example

```python
manager = ThemeManager()
manager.register_theme("contrast", {"primary": (255, 220, 0), "text": (20, 20, 20)})
manager.switch("contrast")
```

#### Advanced pattern(s)

`ScopedTheme` and `ScopedThemeManager` are the advanced path when one subtree, sidebar, or window should override the surrounding theme. `ThemeInvalidationBus` matters when a custom control caches rendered surfaces or glyph output and must flush that cache when the active theme changes. `DesignTokens` lets features and controls ask for semantic values instead of shipping hardcoded colors or spacing literals.

#### Common mistakes and anti-patterns

Hardcoding color literals in draw code undermines theme switching immediately. Changing the active theme without invalidating visual caches leaves stale surfaces onscreen. Registering fonts lazily after the control tree already expects semantic roles can produce missing-role failures or inconsistent visuals.

#### Cross-links to related systems

Theme and styling connect directly to [8.1 Application Bootstrap and Host Configuration](#81-application-bootstrap-and-host-configuration), [8.5 Controls and Control Composition](#85-controls-and-control-composition), and [8.15 Graphics and Audio Integration Points](#815-graphics-and-audio-integration-points).

[Back to Table of Contents](#table-of-contents)

### 8.13 Text, Input, Forms, and Validation Systems
[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Text entry, structured forms, validation, and localization are common enough to deserve first-class support rather than repeated ad hoc feature code. `gui_do` therefore exposes text controls, form models, validation pipelines, document and wizard models, schema-driven form runtime, async validation, formatting helpers, text search, and locale/string-table support as public systems.

#### Mental model and lifecycle placement

Use controls such as `TextInputControl`, `TextAreaControl`, `SpinnerControl`, `DatePickerControl`, `TimePickerControl`, `ColorPickerControl`, and `ChipInputControl` for the input surface. Use `FormModel`, `FormSchema`, or `SchemaFormRuntime` for the logical form state and validation policy. Bind controls to the logical form model during `bind_runtime()`, not by treating the control widget as the only source of truth.

#### Primary public APIs and key types

The core surface includes `FormModel`, `FormField`, `ValidationRule`, `FieldError`, `FormSchema`, `SchemaField`, `DocumentModel`, `WizardFlow`, `WizardStep`, `WizardHandle`, `ValidationResult`, `Validator`, `RequiredValidator`, `RangeValidator`, `LengthValidator`, `PatternValidator`, `CustomValidator`, `DependentValidator`, `ValidationPipeline`, `AsyncFieldValidator`, `AsyncFormValidator`, `FieldSchema`, `FieldGraphSchema`, `ValidationPolicy`, `SchemaFormRuntime`, `TextFormatter`, `NumericFormatter`, `PatternFormatter`, `FixedPatternFormatter`, `TextFlow`, `TextSpan`, `TextSearcher`, `TextMatch`, `StringTable`, and `LocaleRegistry`.

See [Appendix F: Specifications and Option Reference](#appendix-f-specifications-and-option-reference) for form, validation, and schema-driven runtime spec families.

#### Typical usage flow

1. Choose the input controls for the fields you need.
2. Define the logical form structure and validation rules.
3. Bind control changes to the model in `bind_runtime()`.
4. Apply sync or async validation according to policy.
5. Surface errors through labels, notifications, or inline field state.

#### Minimal example

```python
schema = FieldGraphSchema(
	[
		FieldSchema(name="email", required=True),
		FieldSchema(name="password", required=True),
	]
)
runtime = SchemaFormRuntime(schema, policy=ValidationPolicy.ON_CHANGE)
```

#### Advanced pattern(s)

Use `AsyncFormValidator` when validation needs debouncing or stale-result suppression, such as availability checks against a remote endpoint. Use `WizardFlow` when the form is really a guided multi-step workflow instead of one screen. Use `LocaleRegistry` and `StringTable` when labels or validation text should vary by locale instead of being baked into the control tree.

#### Common mistakes and anti-patterns

Validating only on submit when users need immediate feedback is a UX mismatch. Treating `ValidationPolicy` as decorative instead of real behavior leads to inconsistent feedback timing. Async validators without cancellation or generation suppression can apply stale results after the user has already changed the field again.

#### Cross-links to related systems

Text and forms depend directly on [8.4 State and Observables](#84-state-and-observables), [8.5 Controls and Control Composition](#85-controls-and-control-composition), and [8.14 Data and Dataflow Helpers](#814-data-and-dataflow-helpers).

[Back to Table of Contents](#table-of-contents)

### 8.14 Data and Dataflow Helpers
[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Data-heavy features need more than raw lists and callbacks. `gui_do` exposes item sources, sort/filter proxies, async data providers, object pooling, caching, list diffing, transactional state, dataflow pipelines, and virtualization so large or staged datasets can be loaded, transformed, and displayed efficiently.

#### Mental model and lifecycle placement

Data should move through stages. A source or provider produces items. Optional proxies or selectors transform them. Views or virtualization consume the result. Long-running or preemptible transformations should be routed through `DataflowPipeline` or feature operations instead of buried in one callback chain. Runtime ownership still matters: cancel stale work when the user changes direction or the scene exits.

#### Primary public APIs and key types

The data surface includes `VirtualItemSource`, `FixedItemSource`, `SortFilterProxySource`, `AsyncDataProvider`, `LoadState`, `LoadStateKind`, `ObjectPool`, `DataCache`, `CacheStats`, `ListDiffCalculator`, `ListDiff`, `DiffInsert`, `DiffRemove`, `DiffMove`, `CancellationToken`, `PipelineStage`, `DataflowPipeline`, `PipelineHandle`, `AppStateStore`, `StateSelector`, `StateTransaction`, `MeasureMode`, `MeasurePolicy`, `VirtualizedWindow`, `RecyclePool`, and `VirtualizationCore`.

#### Typical usage flow

1. Choose a data source abstraction.
2. Add proxy or pipeline stages if filtering, ranking, or async transformation is needed.
3. Bind the result to a view or virtualization layer.
4. Cancel or replace stale work when the user changes the query or context.

#### Minimal example

```python
source = FixedItemSource(items)
proxy = SortFilterProxySource(source)
proxy.set_filter(lambda item: item.active)
proxy.set_sort_key(lambda item: item.name)
```

#### Advanced pattern(s)

`DataflowPipeline` is the advanced path for staged background work where each generation can be cancelled when newer input arrives. `ListDiffCalculator` is the advanced update path when a view should apply incremental inserts, removes, and moves instead of full redraws. `DataCache` and `ObjectPool` are the operational tools for hot paths that otherwise churn allocations or reload identical content repeatedly.

Use routed feature operations when a dataflow task has a meaningful lifecycle as an operation: retry, timeout, cancellation, and failure publication fit better there than in anonymous callbacks.

#### Common mistakes and anti-patterns

Redrawing or reloading entire collections when a diff or proxy would do wastes work. Forgetting to cancel stale pipeline generations can surface obsolete results. Misusing an object pool by returning objects that are still referenced elsewhere creates correctness bugs instead of performance wins.

#### Cross-links to related systems

Data helpers connect directly to [8.4 State and Observables](#84-state-and-observables), [8.5 Controls and Control Composition](#85-controls-and-control-composition), [8.10 Scheduling, Timing, Animation, and Transitions](#810-scheduling-timing-animation-and-transitions), and [8.16 Telemetry, Introspection, and Operational Hooks](#816-telemetry-introspection-and-operational-hooks).

[Back to Table of Contents](#table-of-contents)

### 8.15 Graphics and Audio Integration Points
[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

The control tree is not the only rendering path in the framework. `gui_do` also exposes graphics helpers for custom drawing, scene graphs, compositing, offscreen targets, particles, tiles, and debug overlays, plus an audio cue surface for semantic sound playback.

#### Mental model and lifecycle placement

Custom graphics usually live in `draw()` or inside canvas-oriented controls. Assets and expensive setup should happen before the frame loop starts using them. Audio cues should be published from semantic events or actions rather than low-level pointer noise so the sound surface reflects user intent instead of implementation detail.

#### Primary public APIs and key types

The graphics surface includes `BuiltInGraphicsFactory`, `DirtyRegionTracker`, `DrawContext`, `DrawPhase`, `AssetRegistry`, `DebugOverlay`, `SurfaceCompositor`, `Layer`, `ShapeRenderer`, `SurfaceEffects`, `VectorPath`, `SpriteSheet`, `FrameAnimation`, `ParticleSystem`, `Emitter`, `ParticleLayer`, `TileSet`, `TileMap`, `RenderTarget`, `LiveRenderTarget`, `OffscreenRenderTarget`, `create_render_target()`, `create_surface()`, `Node2D`, `SceneGraph2D`, and `Camera2D`. The audio surface is `SoundCue`, `SoundBankRegistry`, and `SoundEventBus`.

#### Typical usage flow

1. Load or register assets before the draw path uses them.
2. Update graphics state in `on_update()`.
3. Draw through `DrawContext`, canvas surfaces, or direct render helpers.
4. Publish audio cues from semantic actions or state transitions.

#### Minimal example

```python
self.particles.tick(dt)
self.particles.draw(screen)
host.sound_bus.publish(SoundCue("notify"))
```

#### Advanced pattern(s)

`DirtyRegionTracker` plus offscreen render targets is the advanced performance pattern for expensive canvases. `SceneGraph2D` and `Camera2D` give hierarchical 2D transforms and camera-relative composition. `SurfaceCompositor` and `Layer` are the right fit when rendering should happen in explicitly ordered layers rather than a flat control pass.

#### Common mistakes and anti-patterns

Loading assets in `draw()` creates frame hitches immediately. Redrawing a full surface when dirty-region gating could skip most work wastes time. Publishing audio from raw low-level input events rather than semantic actions usually produces noisy and misleading cues.

#### Cross-links to related systems

Graphics and audio connect most directly to [8.2 Feature Lifecycle and Feature Types](#82-feature-lifecycle-and-feature-types), [8.5 Controls and Control Composition](#85-controls-and-control-composition), [8.10 Scheduling, Timing, Animation, and Transitions](#810-scheduling-timing-animation-and-transitions), and [8.16 Telemetry, Introspection, and Operational Hooks](#816-telemetry-introspection-and-operational-hooks).

[Back to Table of Contents](#table-of-contents)

### 8.16 Telemetry, Introspection, and Operational Hooks
[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Operational visibility lets you diagnose behavior without guessing from pixels alone. The framework therefore exposes telemetry collection and analysis, property inspection, and scene spatial indexing as first-class systems.

#### Mental model and lifecycle placement

Telemetry should be configured before the scenarios you want to observe. Property inspection and spatial indexing are runtime supports for debugging and tooling, not replacements for normal control APIs. Treat them as observability layers over the running application rather than as primary user-facing abstractions.

#### Primary public APIs and key types

The telemetry surface is `TelemetryCollector`, `TelemetrySample`, `configure_telemetry()`, `telemetry_collector()`, `analyze_telemetry_log_file()`, `analyze_telemetry_records()`, `load_telemetry_log_file()`, and `render_telemetry_report()`. The introspection surface is `SceneSpatialIndex`, `ui_property`, `PropertyDescriptor`, `PropertyRegistry`, `property_registry`, `PropertyInspectorModel`, and `InspectedProperty`.

#### Typical usage flow

1. Configure telemetry before running the scenarios to measure.
2. Capture or analyze the resulting records.
3. Use property inspection or spatial queries to localize problematic UI surfaces.

#### Minimal example

```python
configure_telemetry(enabled=True)
report = analyze_telemetry_records(telemetry_collector.records)
print(render_telemetry_report(report))
```

#### Advanced pattern(s)

The strongest observability pattern is combining telemetry with structural inspection. A debug overlay can use `SceneSpatialIndex` to show which nodes overlap a region while telemetry reveals where frame time is actually going. `ui_property` and the property registry create a structured property-inspection path for custom controls instead of bespoke debug panels.

#### Common mistakes and anti-patterns

Profiling only idle frames rarely tells you anything useful about real workloads. Relying solely on visual inspection for performance issues is another trap. Forgetting to enable telemetry before the relevant scenario runs means the data simply is not there later.

#### Cross-links to related systems

Telemetry and introspection connect to [8.10 Scheduling, Timing, Animation, and Transitions](#810-scheduling-timing-animation-and-transitions), [8.11 Persistence and Workspace/Session State](#811-persistence-and-workspacesession-state), and [8.15 Graphics and Audio Integration Points](#815-graphics-and-audio-integration-points).

[Back to Table of Contents](#table-of-contents)

## Integration Patterns and Composition Recipes
[Back to Table of Contents](#table-of-contents)

The framework is strongest when systems are composed deliberately instead of introduced one at a time without a lifecycle plan. A routed feature plus actions plus a shortcut overlay is a good example: actions make behavior named and discoverable, routed runtime keeps the hotkeys and overlay lifecycle-owned, and the overlay turns the action surface into user-facing documentation. The payoff is not just less code; it is that setup, discoverability, and teardown all follow the same graph.

Presenter-backed windows plus task-panel toggles are another common composition. The presenter owns the window-local control tree. The feature owns lifecycle and runtime behavior. The task panel and menu strip expose visibility and navigation affordances. `TaskPanelFocusToggleSpec` or related routed runtime wiring keeps hidden windows out of focus traversal so the chrome and keyboard model stay aligned.

State-store plus persistence plus snapshot migration is the composition pattern for applications that expect long-lived data. Let one state store be authoritative, project slices through selectors, capture snapshots at the workspace boundary, and migrate them before restore when schema changes. This keeps restore deterministic and inspectable instead of turning persistence into a bundle of accidental object pickles.

Dataflow plus telemetry plus an error boundary is the operations-focused recipe. Let the pipeline do staged work, let telemetry measure it, and let an `ErrorBoundary` contain rendering failures in the output surface instead of taking down the whole frame. This is the pattern the systems demo is effectively exercising across multiple tabs: runtime helpers, data helpers, graphics helpers, theme helpers, and persistence helpers all stay separated but still compose through shared lifecycle rules.

[Back to Table of Contents](#table-of-contents)

## End-to-End Reference Application
[Back to Table of Contents](#table-of-contents)

The repository's demo is the reference application because it uses the public root import surface, keeps feature code under `demo_features/`, and exercises most of the framework's major systems in one place. The entrypoint in `gui_do_demo.py` is intentionally thin: it bootstraps from `DEMO_BOOTSTRAP_CONFIG` and then runs the application entrypoint on the attached `app`. That is the correct consumer pattern.

`demo_features/demo_config.py` shows how to assemble a multi-scene application with scene bundles, feature entries, feature-window bundle entries, actions, accessibility entries, font roles, cursor entries, telemetry config, and palette configuration. `demo_features/main` shows a scene-level feature with routed runtime wiring, help overlay, task panel, unified menu strip, and command palette. `demo_features/showcase` shows a control-focused scene with category tabs and scene-local command palette/menu strip usage. `demo_features/systems` is the broadest systems reference because it imports and exercises scheduling, forms, dataflow, graphics, theme, persistence, telemetry, and more in one presenter-backed window.

If you need one end-to-end template for your own project, treat the demo as a shape rather than as a monolith to copy. Keep the entrypoint thin. Put feature composition in one config module. Keep each feature in its own package. Let the config declare scenes and windows. Bind runtime behavior in the features themselves. And treat the demo's package boundary discipline as non-negotiable: the framework package does not import the consumer layer.

[Back to Table of Contents](#table-of-contents)

## Testing, Diagnostics, and Reliability
[Back to Table of Contents](#table-of-contents)

This section will be expanded with discovery-based testing and maintenance guidance, but the maintainer checklist is established here so future manual updates remain tied to the same source-of-truth workflow.

### Maintainer Diff Checklist

Inventory delta checks:

1. Compare current root exports in `gui_do/__init__.py` with Appendix D and Appendix D.1 entries.
2. Check `docs/` contracts for changed guarantees, policies, or boundary rules.
3. Check `tests/` for new contract or runtime test modules that imply manual updates.
4. Check `demo_features/` for new recommended composition patterns to document.

Content integrity checks:

1. Every changed system has updates in both chapter narrative and quick-index references.
2. Removed APIs are deleted from examples, recipes, and appendix indexes.
3. Added APIs are classified at the right abstraction level, with Tier 1 guidance leading when available.

Navigation and structure checks:

1. All newly added sections are present in the table of contents and resolve correctly.
2. Every major section still contains a Back to Table of Contents link.
3. Top-level chapter order remains stable unless an intentional restructure is justified in the migration section.

Operational checks:

1. Re-run high-priority contract tests.
2. Validate end-to-end reference assumptions against current runtime behavior.
3. Record unresolved ambiguities as explicit notes in the migration or deprecation guidance.

```bash
python -m pytest -q tests/test_public_api_exports.py tests/test_public_api_docs_contracts.py tests/test_runtime_operating_contracts.py tests/test_boundary_contracts.py tests/test_gui_application_workspace_contracts.py
```
