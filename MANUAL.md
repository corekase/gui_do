# gui_do Manual

## Title and Purpose
[Back to Table of Contents](#table-of-contents)

This manual is the primary learning and reference document for gui_do. It explains the framework from first principles through production-oriented composition patterns. It is intended for new developers, active feature implementers, and maintainers who need contract-aligned, test-backed guidance for changes across runtime, UI systems, and persistence.

## Table of Contents

1. [Title and Purpose](#title-and-purpose)
2. [Table of Contents](#table-of-contents)
3. [How to Use This Manual](#how-to-use-this-manual)
4. [Conceptual Foundations (Theory)](#conceptual-foundations-theory)
5. [Quickstart Path (Practice)](#quickstart-path-practice)
6. [Architecture and Runtime Model](#architecture-and-runtime-model)
7. [Core Workflow: Build, Bind, Route, Update, Draw](#core-workflow-build-bind-route-update-draw)
8. [Main Systems Reference](#main-systems-reference)
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
9. [Integration Patterns and Composition Recipes](#integration-patterns-and-composition-recipes)
10. [End-to-End Reference Application](#end-to-end-reference-application)
11. [Testing, Diagnostics, and Reliability](#testing-diagnostics-and-reliability)
12. [Performance and Scaling Guidance](#performance-and-scaling-guidance)
13. [Migration, Versioning, and Deprecation Notes](#migration-versioning-and-deprecation-notes)
14. [FAQ and Troubleshooting](#faq-and-troubleshooting)
15. [Appendix](#appendix)
   - [A: Glossary](#a-glossary)
   - [B: Lifecycle/Event Sequence](#b-lifecycleevent-sequence)
   - [C: System Dependency Map](#c-system-dependency-map)
   - [D: API Quick Index](#d-api-quick-index)
   - [D.1: Tier Matrix](#d1-tier-matrix)
   - [D.2: Selection Heuristics](#d2-selection-heuristics)
   - [E: Architecture Templates](#e-architecture-templates)
   - [F: Specifications and Option Reference](#f-specifications-and-option-reference)

## How to Use This Manual
[Back to Table of Contents](#table-of-contents)

Use this manual in three modes: Learn, Build, and Maintain. Learn mode prioritizes concepts and runtime architecture. Build mode prioritizes system chapters, recipes, and examples. Maintain mode prioritizes contracts, tests, migration strategy, and appendices.

Reading paths:
- Beginner: sections 3 through 7, then chapters 8.1 through 8.5.
- Intermediate: sections 6 through 10, then targeted system chapters.
- Maintainer: sections 11 through 15 first, then affected system chapters.

Tri-lens markers:
- Theory: explains intent and invariants.
- Practice: explains implementation patterns and examples.
- Operations: explains diagnostics, tests, and risk control.

Contract alignment:
- Source of truth priority is code behavior, tests, docs contracts, demo usage, then prose.
- Normative docs include docs/public_api_spec.md, docs/runtime_operating_contracts.md, and docs/architecture_boundary_spec.md.

Known non-goals:
- Not a browser-style retained DOM framework.
- Not an internal API stability guarantee for submodule imports.
- Not a replacement for application domain architecture decisions.

## Conceptual Foundations (Theory)
[Back to Table of Contents](#table-of-contents)

### Data-Driven Design
[Back to Table of Contents](#table-of-contents)

gui_do separates structure description from runtime execution. You declare scenes, features, actions, windows, accessibility, and presentation policy through specs and binding entries, then run deterministic assembly and bootstrap. `HostApplicationBindingSpec` plus `build_host_application_config` yields `HostApplicationConfig`, and `bootstrap_host_application` realizes that model into a live host runtime.

This is different from imperative wiring where each shortcut, scene route, and toggle is manually threaded through multiple handlers. With data-driven declarations, one structured edit in config can drive consistent registration, scope behavior, and teardown.

### Reactive Data and Observable State
[Back to Table of Contents](#table-of-contents)

Reactive primitives (`ObservableValue`, `ObservableList`, `ObservableDict`) propagate changes to subscribers automatically. Use `reactive_batch` to collapse related updates and avoid churn. Use `ComputedValue` for derived state where deterministic projection from source observables is desired.

Subscribe in `bind_runtime` and dispose in `shutdown_runtime`. This is a lifecycle correctness rule, not just style preference.

### Feature Composition and Lifecycles
[Back to Table of Contents](#table-of-contents)

A feature is the primary composition unit. `Feature` supports general lifecycle hooks, `LogicFeature` handles logic-centric message behavior, `RoutedFeature` supports topic-based routed messaging, and `DirectFeature` supports direct draw/update/event hooks.

`HOST_REQUIREMENTS` expresses required host fields per lifecycle hook and supports early validation. The recommended package pattern is one feature package folder with package-root `__init__.py` as the public surface and internal modules split by concern.

Concise example:

```python
from gui_do import HostApplicationBindingSpec, build_host_application_config


binding = HostApplicationBindingSpec(
   display_size=(1280, 720),
   window_title="Demo",
   fonts={"default": {"file": None, "size": 14}},
   initial_scene_name="main",
)
config = build_host_application_config(binding)
```

## Quickstart Path (Practice)
[Back to Table of Contents](#table-of-contents)

Install and verify:

```bash
python -m pip install -e . --no-deps
python -m pytest -q tests/test_public_api_exports.py
```

Minimal host pattern:

```python
from gui_do import HostApplicationConfig, SceneSetupSpec, FeatureSpec, RuntimeSceneSpec, ActionSpec, bootstrap_host_application
```

Create a feature, bind one observable to one label, add an exit action, add `RuntimeSceneSpec(..., bind_escape_to_exit=True)`, bootstrap once, then call `run_entrypoint`.

## Architecture and Runtime Model
[Back to Table of Contents](#table-of-contents)

Boundary model:
- gui_do/ is framework code and must not import demo_features/.
- Consumer entrypoints should import from root package exports.

Tier model:
- Tier 1 is the default start point.
- Tier 2 to 7 cover core runtime systems.
- Tier 8+ adds lower-level or specialized capabilities.

Runtime guarantees include canonical GuiEvent normalization, scene-isolated execution, deterministic routing order, and scheduler budget clamping.

Concise example:

```python
from gui_do import GuiEvent, EventType


def is_quit(event: GuiEvent) -> bool:
   return event.kind == EventType.QUIT
```

## Core Workflow: Build, Bind, Route, Update, Draw
[Back to Table of Contents](#table-of-contents)

Phase invariants:
- build: structure creation only.
- bind_runtime: runtime wiring and subscriptions.
- route: message/event dispatch.
- update: frame-time logic and schedulers.
- draw: custom rendering.

Routed lifecycle helpers (`bind_routed_feature_lifecycle`, `shutdown_routed_feature_lifecycle`) reduce repetitive wiring for hotkeys, overlays, task-panel focus toggles, and scoped subscriptions.

Concise example:

```python
from gui_do import bind_routed_feature_lifecycle, shutdown_routed_feature_lifecycle


def bind_feature(feature, host, spec):
   bind_routed_feature_lifecycle(feature, host, spec)


def unbind_feature(feature, host, spec):
   shutdown_routed_feature_lifecycle(feature, host, spec)
```

## Main Systems Reference
[Back to Table of Contents](#table-of-contents)

### 8.1 Application Bootstrap and Host Configuration
[Back to Table of Contents](#table-of-contents)

What/why: deterministic startup via declarative config.

Mental model: bootstrap populates a plain host with app runtime members in one ordered pass.

Primary APIs: `HostApplicationConfig`, `HostApplicationBindingSpec`, `bootstrap_host_application`, `build_host_application_config`, `SceneSetupSpec`, `FeatureSpec`, `WindowSpec`, `ActionSpec`, `RuntimeSceneSpec`.

Typical flow:
1. Define scenes/features/actions/windows in config.
2. Bootstrap host.
3. Run entrypoint.

Minimal example:

```python
config = HostApplicationConfig(...)
bootstrap_host_application(host, config)
```

Advanced pattern: use scene and feature-window bundle binding specs for compact multi-scene composition.

Common mistakes: scene name mismatches, late host mutation that bypasses config contract.

Cross-links: 8.2, 8.3, 8.11.

See [Appendix F: Specifications and Option Reference](#f-specifications-and-option-reference).

### 8.2 Feature Lifecycle and Feature Types
[Back to Table of Contents](#table-of-contents)

What/why: features provide deterministic behavior boundaries.

Mental model: all build phases complete before bind_runtime phases begin.

Primary APIs: `Feature`, `DirectFeature`, `LogicFeature`, `RoutedFeature`, `FeatureMessage`, `FeatureManager`, `RoutedFeatureLifecycleSpec`.

Typical flow:
1. Implement feature class and HOST_REQUIREMENTS.
2. Build controls in build.
3. Bind runtime in bind_runtime.
4. Dispose in shutdown_runtime.

Minimal example:

```python
class MyFeature(Feature):
    ...
```

Advanced pattern: logic and presentation companions using routed helpers.

Common mistakes: subscribing in build and forgetting teardown.

Cross-links: 8.3, 8.4, 8.5.

See [Appendix F: Specifications and Option Reference](#f-specifications-and-option-reference).

### 8.3 Events, Actions, Input Mapping, and Routing
[Back to Table of Contents](#table-of-contents)

What/why: stable event/action routing under scene and window scopes.

Primary APIs: `GuiEvent`, `EventType`, `EventManager`, `ActionRegistry`, `InputMap`, `KeyChordManager`, `FocusManager`.

Typical flow:
1. Declare `ActionSpec`.
2. Bind keys/chords.
3. Route through normalized GuiEvent pipeline.

Minimal example:

```python
actions = (ActionSpec(action_id="exit", label="Exit", kind="exit"),)
```

Advanced pattern: interaction state machine and recorder/playback for deterministic regression traces.

Common mistakes: bypassing GuiEvent normalization and ignoring propagation flags.

Cross-links: 8.2, 8.7, 8.8.

See [Appendix F: Specifications and Option Reference](#f-specifications-and-option-reference).

### 8.4 State and Observables
[Back to Table of Contents](#table-of-contents)

What/why: reactive data propagation for decoupled UI updates.

Primary APIs: `ObservableValue`, `ObservableList`, `ObservableDict`, `ComputedValue`, `reactive_batch`, `AppStateStore`.

Typical flow:
1. Create observable in feature init.
2. Subscribe in bind_runtime.
3. Dispose in shutdown_runtime.

Minimal example:

```python
count = ObservableValue(0)
unsub = count.subscribe(lambda v: print(v))
```

Advanced pattern: centralized state with selectors and transactions.

Common mistakes: per-frame polling and leaking subscriptions.

Cross-links: 8.2, 8.13, 8.14.

See [Appendix F: Specifications and Option Reference](#f-specifications-and-option-reference).

### 8.5 Controls and Control Composition
[Back to Table of Contents](#table-of-contents)

What/why: reusable controls and chrome components inside feature-owned subtrees.

Primary APIs: Tier 12 and Tier 13 controls including `PanelControl`, `LabelControl`, `ButtonControl`, `CanvasControl`, `WindowPresenter`, `ErrorBoundary`, `TextInputControl`, `DataGridControl`, `TreeControl`.

Minimal example:

```python
root = host.app.add(PanelControl("root", rect), scene_name="main")
```

Advanced pattern: presenter-managed windows with feature lifecycle ownership.

Common mistakes: cross-feature control references as data bus.

Cross-links: 8.2, 8.6, 8.9.

### 8.6 Layout Systems
[Back to Table of Contents](#table-of-contents)

What/why: declarative spatial systems for resize-safe UI.

Primary APIs: `FlexLayout`, `GridLayout`, `ConstraintLayout`, `DockWorkspace`, `ResponsiveLayout`, `ConstraintLayoutEngine`, `VirtualizationCore`.

Minimal example:

```python
layout = FlexLayout(...)
```

Advanced pattern: adaptive constraint sets with virtualization.

Common mistakes: mixed ownership over same container bounds.

Cross-links: 8.5, 8.9, 12.

### 8.7 Focus and Accessibility
[Back to Table of Contents](#table-of-contents)

What/why: coherent keyboard routing and semantic accessibility tree behavior.

Primary APIs: `FocusManager`, `FocusScopeManager`, `WindowFocusManager`, `FocusRing`, `AccessibilityTree`, `AccessibilityNode`, `AccessibilityBus`.

Minimal example:

```python
tree = AccessibilityTree()
```

Advanced pattern: accessibility sequencing with modal focus scopes.

Common mistakes: hidden controls left in focus traversal.

Cross-links: 8.3, 8.8, 8.9.

### 8.8 Overlays, Dialogs, Notifications, and Command Surfaces
[Back to Table of Contents](#table-of-contents)

What/why: transient surfaces with explicit routing and dismissal contracts.

Primary APIs: `OverlayManager`, `DialogManager`, `ToastManager`, `CommandPaletteManager`, `TooltipManager`, `ShortcutHelpOverlay`, `NotificationCenter`, `PopupPlacement`.

Minimal example:

```python
host.app.toasts.show("Saved")
```

Advanced pattern: routed shortcut help overlay driven by action descriptors.

Common mistakes: overlays with no dismissal path.

Cross-links: 8.3, 8.7, 8.9.

### 8.9 Scene, Window, and Task-Panel Presentation Models
[Back to Table of Contents](#table-of-contents)

What/why: synchronize scene context, window visibility, and discoverable command surfaces.

Primary APIs: `ScenePresentationModel`, `WindowSpec`, `AnchoredWindowSpec`, `SceneTaskPanelSpec`, `TaskPanelButtonSpec`, `TaskPanelFocusToggleSpec`, `create_feature_presented_window`, `set_window_visible_state`, `ActiveTabUpdateRouter`.

Concise example:

```python
from gui_do import AnchoredWindowSpec, create_feature_presented_window


window = create_feature_presented_window(
   host,
   feature=self,
   spec=AnchoredWindowSpec("inspector", "Inspector", (380, 280), "top_right", (12, 12)),
)
```

See [Appendix F: Specifications and Option Reference](#f-specifications-and-option-reference).

### 8.10 Scheduling, Timing, Animation, and Transitions
[Back to Table of Contents](#table-of-contents)

What/why: frame-budget-safe time orchestration.

Budget contract: fraction `0.12`, floor `0.5 ms`, ceiling `4.0 ms`.

Primary APIs: `TaskScheduler`, `TweenManager`, `AnimationSequence`, `TransitionManager`, `CooperativeScheduler`, `Sleep`, `WaitForSignal`, `Debouncer`, `Throttler`, `DataflowPipeline`.

Concise example:

```python
from gui_do import Sleep


def workflow(host):
   yield Sleep(0.25)
   host.app.running = True
```

See [Appendix F: Specifications and Option Reference](#f-specifications-and-option-reference).

### 8.11 Persistence and Workspace/Session State
[Back to Table of Contents](#table-of-contents)

What/why: durable save/restore with explicit diagnostics and migration.

Restore report fields: `target_scene`, `switched_scene`, `restored_feature_states`, `restored_scene_nodes`, `applied_settings`, `skipped_settings`, `missing_settings_blocks`.

Primary APIs: `WorkspacePersistenceManager`, `SettingsRegistry`, `UndoContextManager`, `SnapshotMigrator`, `MigrationRegistry`, `MigrationStep`, `make_snapshot`, `read_version`.

Concise example:

```python
from gui_do import make_snapshot, read_version


snap = make_snapshot("1.0.0", {"scene": "main"})
version = read_version(snap)
```

See [Appendix F: Specifications and Option Reference](#f-specifications-and-option-reference).

### 8.12 Theme, Styling, and Visual Systems
[Back to Table of Contents](#table-of-contents)

What/why: centralized visual policy and cache invalidation.

Primary APIs: `ThemeManager`, `ColorTheme`, `DesignTokens`, `FontRoleRegistry`, `ScopedThemeManager`, `ThemeInvalidationBus`.

Concise example:

```python
from gui_do import ThemeManager


theme = ThemeManager()
theme.set_theme("default")
```

### 8.13 Text, Input, Forms, and Validation Systems
[Back to Table of Contents](#table-of-contents)

What/why: structured input and validation flows.

Primary APIs: `FormModel`, `FormSchema`, `ValidationPipeline`, `AsyncFormValidator`, `SchemaFormRuntime`, `TextFormatter`, `TextFlow`, `TextSearcher`, `LocaleRegistry`, and input controls from Tier 13.

See [Appendix F: Specifications and Option Reference](#f-specifications-and-option-reference).

### 8.14 Data and Dataflow Helpers
[Back to Table of Contents](#table-of-contents)

What/why: scalable data loading, transform, diff, and projection.

Primary APIs: `AsyncDataProvider`, `SortFilterProxySource`, `DataCache`, `ListDiffCalculator`, `DataflowPipeline`, `CancellationToken`, `VirtualizationCore`, `AppStateStore`.

See [Appendix F: Specifications and Option Reference](#f-specifications-and-option-reference).

### 8.15 Graphics and Audio Integration Points
[Back to Table of Contents](#table-of-contents)

What/why: high-fidelity custom rendering and semantic sound playback.

Primary APIs: `DirtyRegionTracker`, `DrawContext`, `SurfaceCompositor`, `ParticleSystem`, `SceneGraph2D`, `RenderTarget`, `SoundCue`, `SoundEventBus`.

See [Appendix F: Specifications and Option Reference](#f-specifications-and-option-reference).

### 8.16 Telemetry, Introspection, and Operational Hooks
[Back to Table of Contents](#table-of-contents)

What/why: runtime observability and inspection.

Primary APIs: `TelemetryCollector`, `configure_telemetry`, `analyze_telemetry_records`, `SceneSpatialIndex`, `PropertyRegistry`, `PropertyInspectorModel`.

Concise example:

```python
from gui_do import configure_telemetry, telemetry_collector


configure_telemetry(enabled=True)
records = telemetry_collector().records
```

## Integration Patterns and Composition Recipes
[Back to Table of Contents](#table-of-contents)

Recipe 1: Routed feature plus shortcut overlay lifecycle wiring.
Recipe 2: Presenter-backed window plus task-panel focus toggle.
Recipe 3: App state store plus snapshot migration.
Recipe 4: Dataflow pipeline plus telemetry plus error boundary.

## End-to-End Reference Application
[Back to Table of Contents](#table-of-contents)

Reference listing:

```python
# See chapter 8 recipes for complete implementation details.
# Build HostApplicationConfig, register a RoutedFeature, bind lifecycle,
# wire ShortcutOverlaySpec, enable telemetry, and expose save/load hooks.
```

What this demonstrates:
- Bootstrap with current public field names.
- Routed lifecycle with observable binding.
- Runtime scene escape policy and shortcut overlay behavior.
- Workspace save/load integration points.

Validation checklist:
1. App opens and enters initial scene.
2. Observable updates UI label.
3. F9 toggles help overlay.
4. Escape exits as configured.
5. Workspace load returns structured report.

## Testing, Diagnostics, and Reliability
[Back to Table of Contents](#table-of-contents)

Contract command:

```bash
python -m pytest -q tests/test_public_api_exports.py tests/test_public_api_docs_contracts.py tests/test_runtime_operating_contracts.py tests/test_boundary_contracts.py tests/test_gui_application_workspace_contracts.py
```

Core coverage:
- `test_public_api_exports.py`
- `test_public_api_docs_contracts.py`
- `test_runtime_operating_contracts.py`
- `test_boundary_contracts.py`
- `test_gui_application_workspace_contracts.py`

Additional contract/runtime files currently present:
- `tests/test_architecture_boundary_docs_contracts.py`
- `tests/test_core_only_bootstrap_contracts.py`
- `tests/test_demo_feature_package_contracts.py`
- `tests/test_runtime_guarantees_and_determinism.py`

Debug tools: `EventRecorder`, `EventPlayback`, `DebugOverlay`, `PropertyInspectorPanel`, telemetry analyzers.

Maintainer release runbook:
1. Run contract tests and key runtime tests.
2. Reconcile exports, docs, and manual sections.
3. Validate boundary and runtime contract suites.
4. Re-run representative telemetry scenarios.

Regression triage:
1. Reproduce.
2. Trace.
3. Localize.
4. Test-first.
5. Patch.
6. Regress-adjacent verification.

Maintainer Diff Checklist

Inventory delta checks:
1. Compare current root exports in `gui_do/__init__.py` with Appendix D and D.1 entries.
2. Check docs/ contracts for changed guarantees, policies, or boundary rules.
3. Check tests/ for new contract/runtime test modules that imply manual updates.
4. Check demo_features/ for new recommended composition patterns to document.

Content integrity checks:
1. Every changed system has updates in both chapter narrative and quick-index references.
2. Removed APIs are deleted from examples, recipes, and appendix indexes.
3. Added APIs are classified at the right abstraction level (Tier 1 first, then lower tiers).

Navigation and structure checks:
1. All newly added sections are present in TOC and resolve correctly.
2. Every major section still contains a Back to Table of Contents link.
3. Top-level chapter order remains stable unless intentional restructure is recorded.

Operational checks:
1. Re-run high-priority contract tests (command below).
2. Validate end-to-end reference listing assumptions against current runtime behavior.
3. Record unresolved ambiguities as explicit TODO notes in migration/deprecation section.

Contract test command:

```bash
python -m pytest -q tests/test_public_api_exports.py tests/test_public_api_docs_contracts.py tests/test_runtime_operating_contracts.py tests/test_boundary_contracts.py tests/test_gui_application_workspace_contracts.py
```

## Performance and Scaling Guidance
[Back to Table of Contents](#table-of-contents)

Scheduler contract: fraction `0.12`, floor `0.5 ms`, ceiling `4.0 ms`.

Use `DirtyRegionTracker` to gate costly redraw regions. Use virtualization (`VirtualizationCore`, `VirtualizedWindow`, `RecyclePool`) and diff-based updates (`ListDiffCalculator`) for large datasets. Prefer cancelable staged work (`DataflowPipeline`, `CancellationToken`) for preemptible heavy tasks.

## Migration, Versioning, and Deprecation Notes
[Back to Table of Contents](#table-of-contents)

Versioned snapshot workflow:
1. Write with `make_snapshot`.
2. Read version with `read_version`.
3. Migrate with `SnapshotMigrator` and registered `MigrationStep` edges.
4. Restore migrated state.

Deprecation policy is additive-first. No formal deprecated public APIs are cataloged in this generation.

Upgrade checklist:
1. Contract tests before and after.
2. Root-import-only consumer verification.
3. Routing and focus behavior checks.
4. Restore report inspection.
5. Telemetry baseline comparison.

## FAQ and Troubleshooting
[Back to Table of Contents](#table-of-contents)

Q: Controls or features first?
A: Features first. Controls are internal implementation details of feature boundaries.

Q: When use RoutedFeature?
A: Use it when routed message topics and declarative runtime wiring are core to behavior.

Q: Why key handlers do not fire?
A: Check focus owner, scene/window scope, and overlay capture order. Trace with recorder.

Q: Why toast clicks do not pass through?
A: Toast hit regions intentionally consume clicks by contract.

Q: How preserve restore compatibility?
A: Version snapshots and migrate before restore. Handle skipped/missing settings gracefully.

Q: How verify supported API usage?
A: Import from root package and run export/contract tests.

## Appendix
[Back to Table of Contents](#table-of-contents)

### A: Glossary
[Back to Table of Contents](#table-of-contents)

Feature, Spec, Host, Scene, Window presentation, Routed runtime, Observable, Workspace state, Contract test, and Tier are the core terms used across this manual.

### B: Lifecycle/Event Sequence
[Back to Table of Contents](#table-of-contents)

1. Bootstrap from config.
2. Build all features.
3. Bind runtime for all features.
4. Enter runtime loop.
5. Normalize events.
6. Route overlays/focus/scene.
7. Handle events.
8. Update and schedule.
9. Draw and present.
10. Transition scenes with teardown/rebuild.
11. Shutdown and persist.

### C: System Dependency Map
[Back to Table of Contents](#table-of-contents)

Bootstrap depends on specs and lifecycle. Features depend on controls and observables. Layout/focus/overlays depend on routing and visibility state. Persistence depends on state and registration. Scheduling depends on update loop. Telemetry and introspection cross-cut all systems.

### D: API Quick Index
[Back to Table of Contents](#table-of-contents)

Quick groups: Bootstrap, Features, Events/Actions, State/Observables, Controls, Layout, Overlays, Scheduling, Forms/Text, Dataflow, Graphics/Audio, Diagnostics/Introspection.

### D.1: Tier Matrix
[Back to Table of Contents](#table-of-contents)

| Tier | System |
| --- | --- |
| 1 | PRIMARY ENTRY POINTS & DATA-DRIVEN APIs |
| 2 | CORE APPLICATION & SCENE MANAGEMENT |
| 3 | ESSENTIAL DATA & STATE MANAGEMENT |
| 4 | EVENTS, ACTIONS, FOCUS & INPUT |
| 5 | SCHEDULING & ANIMATION |
| 6 | THEME & FONT MANAGEMENT |
| 7 | TELEMETRY & DIAGNOSTICS |
| 8 | LAYOUT & SPATIAL |
| 9 | OVERLAY MANAGERS & WINDOWS |
| 10 | FORMS & DATA BINDING |
| 11 | STATE & PERSISTENCE |
| 12 | PRIMARY CONTROLS (BASIC UI BUILDING BLOCKS) |
| 13 | EXTENDED CONTROLS (SPECIALIZED UI COMPONENTS) |
| 14 | TEXT & LOCALIZATION |
| 15 | DATA & COLLECTIONS |
| 16 | GRAPHICS & RENDERING |
| 17 | INTROSPECTION & INSPECTION |
| 18 | ADVANCED RUNTIME & BOOTSTRAPPING |
| 19 | INFRASTRUCTURE & INTERNALS (AVOID IN APPLICATION CODE) |
| 20 | AUDIO |
| 21 | ACCESSIBILITY |
| 22 | THEME INVALIDATION |
| 23 | UNDO CONTEXT ROUTING |
| 24 | ASYNC FORM VALIDATION |
| 25 | SCOPED SERVICE GRAPH |
| 26 | CANCELABLE DATAFLOW PIPELINE |
| 27 | TRANSACTIONAL APP STATE STORE |
| 28 | ADAPTIVE CONSTRAINT LAYOUT v2 |
| 29 | UNIFIED VIRTUALIZATION CORE |
| 30 | INTERACTION STATE MACHINE FRAMEWORK |
| 31 | SCHEMA-DRIVEN FORM RUNTIME |
| 32 | PORTABLE SNAPSHOT & MIGRATION LAYER |

### D.2: Selection Heuristics
[Back to Table of Contents](#table-of-contents)

Start with Tier 1 and descend only when needed. Use Tier 18 for advanced runtime extension. Avoid Tier 19 in app code. Import from root package only.

### E: Architecture Templates
[Back to Table of Contents](#table-of-contents)

Small single-scene app, multi-window workbench, data-heavy analysis tool, and long-running workflow templates are recommended defaults.

### F: Specifications and Option Reference
[Back to Table of Contents](#table-of-contents)

Bootstrap spec family
- Spec: `HostApplicationBindingSpec`
- Purpose: high-level declarative input for building a complete host config.
- Key options: `display_size`, `window_title`, `fonts`, `initial_scene_name`, `scene_entries`, `feature_entries`, `window_entries`, `runtime_scene_entries`, `action_entries`.
- Notes: use `build_host_application_config` to materialize normalized runtime specs.
- Cross-links: 8.1, 8.9.

Feature and lifecycle spec family
- Spec: `FeatureSpec`
- Purpose: map host attribute names to feature factories.
- Key options: `attr_name`, `factory`.
- Cross-links: 8.1, 8.2.

- Spec: `RoutedRuntimeSpec`
- Purpose: declarative routed wiring for hotkeys, overlays, subscriptions, and focus toggles.
- Key options: `scene_name`, `action_hotkeys`, `control_key_bindings`, `event_subscriptions`, `shortcut_overlays`, `task_panel_focus_toggles`, `command_palette`.
- Cross-links: 7, 8.2, 8.8.

- Spec: `RoutedFeatureLifecycleSpec`
- Purpose: feature lifecycle bundle for routed runtime setup/teardown.
- Key options: `companion_providers`, `runtime_spec`, `runtime_spec_factory`, `runtime_spec_attr_name`, `scheduler_attr_name`.
- Cross-links: 7, 8.2.

Action and input spec family
- Spec: `ActionSpec`
- Purpose: standard action declaration for exit, scene navigation, and palette actions.
- Key options: `action_id`, `label`, `kind`, `target`, `category`, `key`.
- Cross-links: 8.1, 8.3.

- Spec: `ActionHotkeySpec`
- Purpose: declarative hotkey registration for named actions.
- Key options: action name/id and key binding fields.
- Cross-links: 8.3, Integration recipes.

- Spec: `ControlKeyBindingSpec`
- Purpose: bind key behavior to specific controls.
- Key options: control identifier and key/action mapping fields.
- Cross-links: 8.3, 8.5.

Window and presentation spec family
- Spec: `WindowSpec`
- Purpose: declarative window presentation and toggle metadata.
- Key options: `key`, `feature_attribute_name`, `toggle_attribute_name`, `action_name`, `task_panel_toggle_button_id`, `task_panel_slot_index`.
- Cross-links: 8.1, 8.9.

- Spec: `AnchoredWindowSpec`
- Purpose: define anchored presenter-backed window geometry and chrome options.
- Key options: `control_id`, `title`, `size`, `anchor`, `margin`, `use_frame_backdrop`.
- Cross-links: 8.9.

- Spec: `SceneTaskPanelSpec`
- Purpose: configure per-scene task panel container behavior.
- Key options: control identifiers, size, docking/visibility policy fields.
- Cross-links: 8.9.

- Spec: `TaskPanelButtonSpec` and `TaskPanelFocusToggleSpec`
- Purpose: task panel button declaration and focus-toggle behavior for window visibility workflows.
- Key options: button identity/label/slot and focus toggle action/scene/key.
- Cross-links: 8.7, 8.9.

Overlay and command surface spec family
- Spec: `ShortcutOverlaySpec`
- Purpose: configure a feature-owned shortcut help overlay.
- Key options: `attr_name`, `action_registry_attr`, `width`, `height`, `toggle_action_name`, `toggle_key`, `toggle_scene_name`, manual shortcut/filter options.
- Cross-links: 8.8, Integration recipes.

- Spec: `SceneCommandPaletteSpec`
- Purpose: configure per-scene command palette activation.
- Key options: activation key and scene name.
- Cross-links: 8.8, 8.9.

- Spec: `NotificationSpec`
- Purpose: pre-seed notification-center records.
- Key options: `message`, `title`, `severity`.
- Cross-links: 8.8.

Persistence and migration spec family
- Spec: `SceneRootSpec`
- Purpose: define declarative scene root panels.
- Key options: `scene_name`, `control_id`, `draw_background`.
- Cross-links: 8.1, 8.11.

- Spec family: migration objects (`SchemaVersion`, `VersionedSnapshot`, `MigrationStep`, `MigrationRegistry`)
- Purpose: declare and resolve versioned snapshot migrations.
- Key options: source/target version and transform callable registration.
- Cross-links: 8.11, 13.

Accessibility and static annotation spec family
- Spec: `StaticAccessibilitySpec` and `AccessibilitySequenceSpec`
- Purpose: declare static semantic labels and accessibility ordering.
- Key options: control attribute binding and role/label fields.
- Cross-links: 8.7, 8.1.
