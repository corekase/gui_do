# gui_do Manual

Purpose: This manual is the primary single-file guide for learning, building, and maintaining applications with gui_do.

## Table of Contents

- [Title and Purpose](#gui_do-manual)
- [Table of Contents](#table-of-contents)
- [How to Use This Manual](#how-to-use-this-manual)
  - [Reading Paths](#reading-paths)
  - [Tri-Lens Markers](#tri-lens-markers)
  - [What Changed Since Last Manual](#what-changed-since-last-manual)
  - [Contract Alignment](#contract-alignment)
- [Conceptual Foundations (Theory)](#conceptual-foundations-theory)
  - [Theory: Declarative Runtime Over Imperative Wiring](#theory-declarative-runtime-over-imperative-wiring)
  - [Practice: Declaring a Host Runtime](#practice-declaring-a-host-runtime)
  - [Theory: Lifecycle-Scoped Responsibilities](#theory-lifecycle-scoped-responsibilities)
  - [Practice: Build and Bind Separation](#practice-build-and-bind-separation)
  - [Theory: Deterministic Routing and Runtime Safety Rails](#theory-deterministic-routing-and-runtime-safety-rails)
  - [Practice: Stable Dispatch and Scene Scope](#practice-stable-dispatch-and-scene-scope)
  - [Known Non-Goals](#known-non-goals)
- [Quickstart Path (Practice)](#quickstart-path-practice)
  - [Step 1: Install and Verify](#step-1-install-and-verify)
  - [Step 2: Create a Minimal Host](#step-2-create-a-minimal-host)
  - [Step 3: Add a Feature with Observable State](#step-3-add-a-feature-with-observable-state)
  - [Step 4: Add Action and Runtime Scene Policy](#step-4-add-action-and-runtime-scene-policy)
  - [Step 5: Run Loop and Validation](#step-5-run-loop-and-validation)
  - [Guided Build Track (Beginner)](#guided-build-track-beginner)
  - [Quickstart Failure Modes](#quickstart-failure-modes)
- [Architecture and Runtime Model](#architecture-and-runtime-model)
  - [Boundary Model: Framework vs Consumer](#boundary-model-framework-vs-consumer)
  - [Tiered Public API Model](#tiered-public-api-model)
  - [Runtime Guarantees](#runtime-guarantees)
  - [Event Pipeline](#event-pipeline)
- [Core Workflow: Build, Bind, Route, Update, Draw](#core-workflow-build-bind-route-update-draw)
  - [Phase Reference](#phase-reference)
  - [Message and Logic Coordination](#message-and-logic-coordination)
  - [When to Use Routed Runtime Specs](#when-to-use-routed-runtime-specs)
- [Main Systems Reference](#main-systems-reference)
  - [Application Bootstrap and Host Configuration](#application-bootstrap-and-host-configuration)
  - [Feature Lifecycle and Feature Types](#feature-lifecycle-and-feature-types)
  - [Events, Actions, Input Mapping, and Routing](#events-actions-input-mapping-and-routing)
  - [State and Observables](#state-and-observables)
  - [Controls and Control Composition](#controls-and-control-composition)
  - [Layout Systems](#layout-systems)
  - [Focus and Accessibility](#focus-and-accessibility)
  - [Overlays, Dialogs, Notifications, and Command Surfaces](#overlays-dialogs-notifications-and-command-surfaces)
  - [Scene, Window, and Task-Panel Presentation Models](#scene-window-and-task-panel-presentation-models)
  - [Scheduling, Timing, Animation, and Transitions](#scheduling-timing-animation-and-transitions)
  - [Persistence and Workspace/Session State](#persistence-and-workspacesession-state)
  - [Theme, Styling, and Visual Systems](#theme-styling-and-visual-systems)
  - [Text, Input, Forms, and Validation Systems](#text-input-forms-and-validation-systems)
  - [Data and Dataflow Helpers](#data-and-dataflow-helpers)
  - [Graphics and Audio Integration Points](#graphics-and-audio-integration-points)
  - [Telemetry, Introspection, and Operational Hooks](#telemetry-introspection-and-operational-hooks)
- [Integration Patterns and Composition Recipes](#integration-patterns-and-composition-recipes)
  - [Recipe 1: Routed Feature + Actions + Shortcut Overlay](#recipe-1-routed-feature--actions--shortcut-overlay)
  - [Recipe 2: Window Presenter + Task Panel + Focus Toggle](#recipe-2-window-presenter--task-panel--focus-toggle)
  - [Recipe 3: State Store + Persistence + Snapshot Migration](#recipe-3-state-store--persistence--snapshot-migration)
  - [Recipe 4: Dataflow Pipeline + Telemetry + Error Boundary](#recipe-4-dataflow-pipeline--telemetry--error-boundary)
- [End-to-End Reference Application](#end-to-end-reference-application)
  - [Reference Listing (Single File)](#reference-listing-single-file)
  - [What This Listing Demonstrates](#what-this-listing-demonstrates)
  - [Validation Checklist](#validation-checklist)
- [Testing, Diagnostics, and Reliability](#testing-diagnostics-and-reliability)
  - [Contract Tests](#contract-tests)
  - [Runtime Behavior Tests](#runtime-behavior-tests)
  - [Debug and Trace Tools](#debug-and-trace-tools)
  - [Maintainer Release Runbook](#maintainer-release-runbook)
  - [Regression Triage Workflow](#regression-triage-workflow)
  - [Maintainer Diff Checklist](#maintainer-diff-checklist)
  - [Manual Conformance Report (2026-05-04)](#manual-conformance-report-2026-05-04)
- [Performance and Scaling Guidance](#performance-and-scaling-guidance)
  - [Scheduler Budget Contract](#scheduler-budget-contract)
  - [Virtualization and Incremental Rendering](#virtualization-and-incremental-rendering)
  - [Practical Scaling Checklist](#practical-scaling-checklist)
- [Migration, Versioning, and Deprecation Notes](#migration-versioning-and-deprecation-notes)
  - [Versioned Snapshot Strategy](#versioned-snapshot-strategy)
  - [Deprecation Handling](#deprecation-handling)
  - [Upgrade Checklist](#upgrade-checklist)
- [FAQ and Troubleshooting](#faq-and-troubleshooting)
- [Appendix](#appendix)
  - [Appendix A: Glossary](#appendix-a-glossary)
  - [Appendix B: Lifecycle and Event Routing Sequence](#appendix-b-lifecycle-and-event-routing-sequence)
  - [Appendix C: System Dependency Map](#appendix-c-system-dependency-map)
  - [Appendix D: API Quick Index by Topic](#appendix-d-api-quick-index-by-topic)
  - [Appendix D.1: Tier-to-System Reference Matrix](#appendix-d1-tier-to-system-reference-matrix)
  - [Appendix D.2: Public API Selection Heuristics](#appendix-d2-public-api-selection-heuristics)
  - [Appendix E: Architecture Templates](#appendix-e-architecture-templates)

## How to Use This Manual

[Back to Table of Contents](#table-of-contents)

This manual is designed as both a learning path and an operational reference.

Use it in three modes:

- Learn mode: read Sections 3 through 7 in order.
- Build mode: jump to Section 8 and Section 9 recipes.
- Maintain mode: jump to Sections 10 through 13 and Appendix B through D.

### Reading Paths

[Back to Table of Contents](#table-of-contents)

- Beginner path: Sections 3, 4, 5, 6, 7, then 8.1, 8.2, 8.3, 8.4.
- Intermediate path: Sections 6, 7, all of Section 8, then Section 9.
- Maintainer path: Sections 6, 8.9 through 8.16, then Sections 10 to 13.

### Tri-Lens Markers

[Back to Table of Contents](#table-of-contents)

This manual now supports three simultaneous reading lenses:

- Beginner lens: use Quickstart, Guided Build Track, and each chapter's "Typical usage flow" first.
- API lens: use each chapter's "Primary APIs" and Appendix D and D.1 for dense lookup.
- Maintainer lens: use Sections 10 to 12 plus the Maintainer Release Runbook and Regression Triage Workflow.

### What Changed Since Last Manual

[Back to Table of Contents](#table-of-contents)

Third pass update: executed the maintainer diff checklist and recorded an explicit conformance report.

Inventory results used for this build:

- Existing manual coverage: complete baseline structure plus tri-lens and end-to-end reference additions.
- New to add: maintainer diff checklist execution evidence and dated conformance report.
- Obsolete to remove: none in this pass.
- Restructure actions: testing/maintenance section expanded with audit artifact while preserving chapter order.

### Contract Alignment

[Back to Table of Contents](#table-of-contents)

Behavioral claims in this manual are aligned to current package contracts and runtime specs under docs/, especially:

- public API surface and tier model
- event normalization and routing semantics
- runtime operating guarantees and scheduler budget policy
- package/demo boundary contracts

When narrative guidance and code behavior differ, code and contract docs are normative.

## Conceptual Foundations (Theory)

[Back to Table of Contents](#table-of-contents)

### Theory: Declarative Runtime Over Imperative Wiring

[Back to Table of Contents](#table-of-contents)

gui_do favors declarative specifications over ad hoc setup logic. Instead of imperatively wiring scenes, actions, overlays, and windows in many places, you declare specs and let bootstrap construct deterministic runtime state.

Benefits:

- predictable startup ordering
- fewer hidden coupling points
- easier composition and testing
- clearer migration when APIs evolve

### Practice: Declaring a Host Runtime

[Back to Table of Contents](#table-of-contents)

```python
from gui_do import (
    FeatureSpec,
    HostApplicationConfig,
    RuntimeSceneSpec,
    SceneSetupSpec,
)

config = HostApplicationConfig(
    display_size=(1280, 720),
    window_title="My gui_do App",
    fonts={"default": {"system": "arial", "size": 16}},
    font_role_specs=(),
    cursors=(),
    scene_specs=(SceneSetupSpec(name="main", pretty_name="Main", initial=True),),
    feature_specs=(FeatureSpec(attr_name="main_feature", factory=MyFeature),),
    window_specs=(),
    runtime_scene_specs=(RuntimeSceneSpec(scene_name="main"),),
    action_specs=(),
    static_accessibility_specs=(),
    initial_scene_name="main",
)
```

Validation tip: confirm each declared scene has corresponding runtime scene policy.

### Theory: Lifecycle-Scoped Responsibilities

[Back to Table of Contents](#table-of-contents)

Feature logic is divided into explicit phases. This separation reduces hidden side effects and allows deterministic orchestration:

- build: create controls and initial owned state
- bind_runtime: connect runtime dependencies and subscriptions
- handle_event: process relevant event inputs
- on_update: execute frame/tick logic
- draw: direct rendering for custom visuals

### Practice: Build and Bind Separation

[Back to Table of Contents](#table-of-contents)

```python
class CounterFeature(Feature):
    def build(self, host):
        self.count = ObservableValue(0)
        self.label = host.app.add(LabelControl("count", Rect(10, 10, 160, 24), "Count: 0"), scene_name="main")

    def bind_runtime(self, host):
        self._sub = self.count.subscribe(lambda value: setattr(self.label, "text", f"Count: {value}"))

    def shutdown_runtime(self, host):
        if hasattr(self, "_sub"):
            self._sub.dispose()
```

Validation tip: all external subscriptions created in bind_runtime should be disposed in shutdown_runtime.

### Theory: Deterministic Routing and Runtime Safety Rails

[Back to Table of Contents](#table-of-contents)

gui_do contracts emphasize deterministic candidate order and bounded scheduling to maintain predictable behavior under load.

Examples:

- canonical GuiEvent normalization before app dispatch
- scene-scoped runtime execution
- stable candidate ordering for key/window routing
- scheduler message budget clamp to fixed floor and ceiling

### Practice: Stable Dispatch and Scene Scope

[Back to Table of Contents](#table-of-contents)

```python
from gui_do import EventManager, GuiEvent

gui_event = EventManager.to_gui_event(raw_event, pointer_pos)
if isinstance(gui_event, GuiEvent):
    host.app.process_event(gui_event)
```

Validation tip: tests should assert event conversion and scene-scoped effects rather than relying on incidental global state.

### Known Non-Goals

[Back to Table of Contents](#table-of-contents)

gui_do intentionally does not aim to:

- provide OS-native widget parity across all platforms
- replace domain-layer architecture decisions for application business logic
- expose internal infrastructure tiers as beginner entry points
- make star-import behavior part of public API compatibility

## Quickstart Path (Practice)

[Back to Table of Contents](#table-of-contents)

### Step 1: Install and Verify

[Back to Table of Contents](#table-of-contents)

```bash
python -m pip install -e . --no-deps
python -m pytest -q tests/test_public_api_exports.py
```

### Step 2: Create a Minimal Host

[Back to Table of Contents](#table-of-contents)

```python
from gui_do import HostApplicationConfig, SceneSetupSpec

config = HostApplicationConfig(
    display_size=(960, 640),
    window_title="Quickstart",
    fonts={"default": {"system": "arial", "size": 16}},
    font_role_specs=(),
    cursors=(),
    scene_specs=(SceneSetupSpec(name="main", pretty_name="Main", initial=True),),
    feature_specs=(),
    window_specs=(),
    runtime_scene_specs=(),
    action_specs=(),
    static_accessibility_specs=(),
    initial_scene_name="main",
)
```

### Step 3: Add a Feature with Observable State

[Back to Table of Contents](#table-of-contents)

```python
class MainFeature(Feature):
    def __init__(self):
        super().__init__("main_feature", scene_name="main")
        self.value = ObservableValue("Ready")
```

### Step 4: Add Action and Runtime Scene Policy

[Back to Table of Contents](#table-of-contents)

```python
from gui_do import ActionSpec, RuntimeSceneSpec

config.action_specs = (
    ActionSpec(action_id="exit", label="Exit", kind="exit", category="File"),
)
config.runtime_scene_specs = (
    RuntimeSceneSpec(scene_name="main", bind_escape_to_exit=True),
)
```

### Step 5: Run Loop and Validation

[Back to Table of Contents](#table-of-contents)

```python
class AppHost:
    def __init__(self, cfg):
        self.config = cfg
        bootstrap_host_application(self, self.config)

    def run(self):
        self.app.run_entrypoint(target_fps=120)
```

Validation checks:

- app opens to initial scene
- escape exits when configured
- feature hooks execute in expected order

### Guided Build Track (Beginner)

[Back to Table of Contents](#table-of-contents)

Milestone progression for first successful app:

1. Milestone A: app boots to a single scene with no errors.
2. Milestone B: one feature creates one visible control.
3. Milestone C: one observable updates one control reactively.
4. Milestone D: one action and one hotkey trigger expected behavior.
5. Milestone E: one overlay and one toast route without input leakage.
6. Milestone F: workspace save/load roundtrip succeeds.

Beginner confidence checklist:

- you can explain where build ends and bind_runtime begins
- you can add/remove one feature through specs only
- you can trace one keypress through routing to action execution

### Quickstart Failure Modes

[Back to Table of Contents](#table-of-contents)

Most common early failures and fixes:

- Symptom: feature never appears.
  Fix: verify feature is included in feature_specs and scene names match.
- Symptom: hotkey does nothing.
  Fix: verify action descriptor is registered and input binding scope matches active scene/window.
- Symptom: overlay blocks unexpected keys.
  Fix: check consume_unhandled_keys and dismissal settings.
- Symptom: state updates but UI does not.
  Fix: ensure subscription is created in bind_runtime and not disposed early.

## Architecture and Runtime Model

[Back to Table of Contents](#table-of-contents)

### Boundary Model: Framework vs Consumer

[Back to Table of Contents](#table-of-contents)

- gui_do/: reusable framework/runtime code
- demo_features/ and gui_do_demo.py: consumer integration layer
- boundary rule: framework package should not depend on demo package

### Tiered Public API Model

[Back to Table of Contents](#table-of-contents)

Public root exports are grouped in tiers from high-level bootstrap abstractions to specialized systems. Prefer highest-tier abstractions first:

- Tier 1: lifecycle + data-driven runtime specs and bootstrap
- Tier 2 to 7: app, data, events/actions, scheduling, theme, telemetry
- Tier 8+: layout, overlays, forms, state/persistence, controls, graphics, introspection, advanced runtime, audio, accessibility, and additional architecture systems

### Runtime Guarantees

[Back to Table of Contents](#table-of-contents)

Contractual guarantees include:

- canonical GuiEvent app-dispatch normalization
- scene-isolated runtime updates
- deterministic ordering for window/key-routing candidates
- bounded scheduler dispatch budget policy

### Event Pipeline

[Back to Table of Contents](#table-of-contents)

High-level flow:

1. normalize raw input to GuiEvent
2. process quit and global input state updates
3. update logical/raw pointer handling
4. route overlays and focused targets
5. route feature handlers, scene handlers, and fallthrough policy
6. respect stop-propagation/default-prevented flags as hard stops

## Core Workflow: Build, Bind, Route, Update, Draw

[Back to Table of Contents](#table-of-contents)

### Phase Reference

[Back to Table of Contents](#table-of-contents)

- build: instantiate controls, initialize local observables
- bind_runtime: attach host-dependent wiring (actions, event bus, subscriptions)
- route: consume messages/events through declared mappings and handlers
- update: execute frame-based logic and scheduled workloads
- draw: custom render pass where controls are insufficient

### Message and Logic Coordination

[Back to Table of Contents](#table-of-contents)

Use logic aliases and feature messaging for decoupling:

- bind feature-level aliases to logic features
- send messages by intent, not by concrete feature implementation details
- keep domain logic in LogicFeature or service scopes when possible

### When to Use Routed Runtime Specs

[Back to Table of Contents](#table-of-contents)

Use RoutedRuntimeSpec when a feature needs multiple runtime bindings together:

- action hotkeys
- control key bindings
- event subscriptions
- shortcut overlays
- task panel focus toggles

This keeps runtime wiring declarative and auditable.

## Main Systems Reference

[Back to Table of Contents](#table-of-contents)

### Application Bootstrap and Host Configuration

[Back to Table of Contents](#table-of-contents)

What and why:

- HostApplicationConfig and bootstrap_host_application create deterministic host startup and runtime wiring.

Mental model:

- specifications describe runtime intent
- bootstrap realizes the graph and host attributes

Primary APIs:

- HostApplicationConfig, HostApplicationBindingSpec
- FeatureSpec, SceneSetupSpec, RuntimeSceneSpec, ActionSpec, WindowSpec
- bootstrap_host_application, build_host_application_config and related builder helpers

Typical usage flow:

1. declare config
2. bootstrap into host
3. run entrypoint

Minimal example:

```python
host = MyHost()
host.config = build_host_application_config(binding_spec)
bootstrap_host_application(host, host.config)
```

Advanced pattern:

- compose large apps from scene/window/feature binding bundles and generated specs.

Common mistakes:

- manually mutating host graph after bootstrap in ways that bypass specs
- declaring scene-dependent features without matching scene specs

Cross-links: 8.2, 8.9, 8.11

### Feature Lifecycle and Feature Types

[Back to Table of Contents](#table-of-contents)

What and why:

- Feature abstractions isolate behavior and enable deterministic orchestration.

Mental model:

- Feature: UI-centric composition
- DirectFeature: custom rendering focus
- LogicFeature: non-visual command/message logic
- RoutedFeature: topic-based dispatch

Primary APIs:

- Feature, DirectFeature, LogicFeature, RoutedFeature
- FeatureManager, FeatureMessage, RoutedFeatureLifecycleSpec

Typical usage flow:

1. implement hooks
2. declare in FeatureSpec
3. wire runtime through bind_runtime or routed lifecycle helpers

Minimal example:

```python
class StatusFeature(Feature):
    def build(self, host):
        ...
```

Advanced pattern:

- register routed companions and lifecycle hooks with bind_routed_feature_lifecycle.

Common mistakes:

- subscribing in build rather than bind_runtime
- mixing draw-heavy logic into non-direct features

Cross-links: 7, 8.3, 8.10

### Events, Actions, Input Mapping, and Routing

[Back to Table of Contents](#table-of-contents)

What and why:

- gui_do normalizes events and routes actions in stable order to keep behavior predictable.

Mental model:

- raw events become GuiEvent
- input map resolves bindings
- actions execute via registry/manager

Primary APIs:

- GuiEvent, EventType, EventPhase, EventManager, EventBus
- ActionManager, ActionRegistry, InputMap, KeyChordManager
- InteractionStateMachine (advanced phase/transition handling)

Typical usage flow:

1. declare actions
2. map keys/chords
3. bind feature or global handlers

Minimal example:

```python
host.input_map.bind(InputBinding("save", key=pygame.K_s, ctrl=True))
host.action_manager.execute("save")
```

Advanced pattern:

- per-scene and per-window scoped action routing with deterministic candidate precedence.

Common mistakes:

- bypassing GuiEvent normalization
- assuming global routing when handlers are scene scoped

Cross-links: 6.4, 8.7, 8.8

### State and Observables

[Back to Table of Contents](#table-of-contents)

What and why:

- reactive state decouples view updates from imperative control mutation.

Mental model:

- ObservableValue and collection observables emit change signals
- bindings and computed values derive and synchronize state

Primary APIs:

- ObservableValue, ObservableList, ObservableDict, ComputedValue
- Binding, BindingGroup, ObservableStream
- AppStateStore, StateSelector, StateTransaction (transactional advanced state)

Typical usage flow:

1. store feature or app state in observables
2. subscribe and update controls
3. dispose subscriptions on shutdown

Minimal example:

```python
self.value = ObservableValue(0)
self.value.subscribe(lambda v: setattr(self.label, "text", str(v)))
```

Advanced pattern:

- transactionally update AppStateStore and derive selectors for multiple features.

Common mistakes:

- leaking subscriptions
- using controls as source-of-truth state

Cross-links: 8.13, 8.14, 9.3

### Controls and Control Composition

[Back to Table of Contents](#table-of-contents)

What and why:

- controls provide reusable UI primitives while features provide orchestration.

Mental model:

- compose controls inside feature-owned roots
- isolate interaction logic in feature methods

Primary APIs:

- core controls: PanelControl, LabelControl, ButtonControl, ToggleControl, SliderControl, ScrollbarControl
- extended controls: TextInputControl, DropdownControl, ListViewControl, DataGridControl, TreeControl
- chrome controls: WindowControl, TaskPanelControl, MenuBarControl, SceneMenuStripControl

Typical usage flow:

1. add root panel
2. add children controls
3. bind callbacks and observable synchronization

Minimal example:

```python
root = host.app.add(PanelControl("root", Rect(0, 0, 800, 600)), scene_name="main")
root.add(ButtonControl("go", Rect(10, 10, 100, 28), "Go", on_click=self.on_go))
```

Advanced pattern:

- use ErrorBoundary around experimental control trees and dynamic presenter tabs.

Common mistakes:

- direct cross-feature control references creating hidden coupling
- attempting top-level app architecture with controls alone

Cross-links: 8.6, 8.9, 9.2

### Layout Systems

[Back to Table of Contents](#table-of-contents)

What and why:

- layout systems manage spatial constraints, responsive behavior, and docking composition.

Mental model:

- choose the simplest layout family for each region
- prefer deterministic constraints and measurable layout passes

Primary APIs:

- ConstraintLayout, AdaptiveConstraintLayout (ConstraintLayoutEngine, ConstraintSet)
- FlexLayout, GridLayout, FlowLayout, DockWorkspace, WindowTilingManager
- LayoutPass, LayoutRoot, ResponsiveLayout, Viewport, SnapGrid

Typical usage flow:

1. define container strategy
2. assign child placements/constraints
3. run measure/arrange through app/layout manager

Minimal example:

```python
layout = FlexLayout(direction=FlexDirection.ROW, gap=8)
layout.add(FlexItem(control=left_panel, grow=1))
layout.add(FlexItem(control=right_panel, grow=2))
```

Advanced pattern:

- adaptive policy switching by breakpoint and viewport with resolve_adaptive_policy.

Common mistakes:

- mixing conflicting layout systems in one container without clear ownership
- hardcoding dimensions where responsive breakpoints are required

Cross-links: 8.5, 8.9, 11.2

### Focus and Accessibility

[Back to Table of Contents](#table-of-contents)

What and why:

- focus and accessibility systems keep keyboard interaction coherent and assistive semantics available.

Mental model:

- FocusManager and scopes govern keyboard target ownership
- AccessibilityTree models semantic roles and live announcements

Primary APIs:

- FocusManager, FocusScopeManager, FocusRing, WindowFocusManager
- AccessibilityTree, AccessibilityNode, AccessibilityRole, AccessibilityBus
- AccessibilitySequenceSpec and static accessibility helpers

Typical usage flow:

1. define accessible control order and semantics
2. use task panel focus toggles and scope-aware traversal
3. route accessibility navigation keys correctly

Minimal example:

```python
tree = AccessibilityTree()
tree.root.add_child(AccessibilityNode(role=AccessibilityRole.BUTTON, name="Submit"))
```

Advanced pattern:

- scene-level accessibility sequence specs plus focused-control key consumption policy.

Common mistakes:

- duplicate focus targets across hidden/visible windows
- missing semantic roles for custom draw controls

Cross-links: 6.4, 8.3, 8.9

### Overlays, Dialogs, Notifications, and Command Surfaces

[Back to Table of Contents](#table-of-contents)

What and why:

- overlay systems manage transient and modal UI surfaces without destabilizing main control routing.

Mental model:

- overlays can be dismiss-on-escape and dismiss-on-outside-click
- optional modal key capture consumes unhandled keys
- toast clicks are consumed to prevent click-through

Primary APIs:

- OverlayManager, DialogManager, ToastManager, TooltipManager
- ContextMenuManager, CommandPaletteManager, MenuBarManager
- NotificationCenter and ShortcutHelpOverlay

Typical usage flow:

1. create manager or helper spec
2. register surface and dismissal behavior
3. route events through manager before scene fallthrough

Minimal example:

```python
host.toasts.show("Saved", severity=ToastSeverity.SUCCESS)
```

Advanced pattern:

- build shortcut help overlays with manual sections, filtering, and action-registry integration.

Common mistakes:

- allowing overlays to exist without dismissal contract
- assuming toast clicks should pass to underlying controls

Cross-links: 8.3, 8.9, 9.1

### Scene, Window, and Task-Panel Presentation Models

[Back to Table of Contents](#table-of-contents)

What and why:

- scene and window presentation models coordinate visible UI contexts, toggles, and task-panel affordances.

Mental model:

- scenes define broad context
- windows define focused work surfaces
- task panels and menu strips expose discoverable commands

Primary APIs:

- ScenePresentationModel, WindowPresenter, WindowSpec, AnchoredWindowSpec
- SceneTaskPanelSpec, TaskPanelButtonSpec, TaskPanelFocusToggleSpec
- SceneMenuStrip and tabbed presenter specs/helpers

Typical usage flow:

1. declare scenes
2. declare window presentation specs
3. add task panel controls/toggles and optional tab presenter

Minimal example:

```python
window = create_feature_presented_window(host, feature, anchored_spec)
set_window_visible_state(window, True)
```

Advanced pattern:

- ActiveTabUpdateRouter with TabLayoutContext for presenter-driven tab refresh.

Common mistakes:

- mismatching scene scope and window scope for action handlers
- not synchronizing task panel buttons with presentation state

Cross-links: 8.1, 8.6, 9.2

### Scheduling, Timing, Animation, and Transitions

[Back to Table of Contents](#table-of-contents)

What and why:

- scheduling systems execute timed work, transitions, and cooperative async flows under bounded budgets.

Mental model:

- frame budget controls throughput
- animations and transitions are stateful timelines
- cooperative tasks yield via wait instructions

Primary APIs:

- TaskScheduler, Timers, TweenManager, TransitionManager
- AnimationSequence, AnimationStateMachine, SceneTimeline
- CooperativeScheduler and wait primitives

Typical usage flow:

1. schedule or register animation tasks
2. tick in update loop
3. react to completion events

Minimal example:

```python
handle = host.tweens.to(control, "alpha", 255, duration=0.25)
```

Advanced pattern:

- cooperative scheduler coroutines that wait for events/signals while preserving frame responsiveness.

Common mistakes:

- unbounded work per frame
- hidden scheduler dependencies across scenes

Cross-links: 6.3, 11.1, 11.2

### Persistence and Workspace/Session State

[Back to Table of Contents](#table-of-contents)

What and why:

- persistence systems restore user context and state predictably across runs.

Mental model:

- workspace state captures scene target, feature state, snapshots, and settings
- restore returns structured report including applied and skipped blocks

Primary APIs:

- WorkspaceState, WorkspacePersistenceManager, SceneSnapshot
- SettingsRegistry, SceneTransitionManager
- snapshot migration types: SchemaVersion, MigrationRegistry, SnapshotMigrator

Typical usage flow:

1. save workspace at checkpoint or shutdown
2. load workspace on startup
3. inspect restore report and handle missing/unknown keys safely

Minimal example:

```python
report = host.app.load_workspace(path)
if report and report.skipped_settings:
    host.toasts.show("Some settings were skipped")
```

Advanced pattern:

- maintain versioned snapshot graph and apply BFS migration steps before restore.

Common mistakes:

- assuming all settings keys exist forever
- restoring snapshots without version checks

Cross-links: 10.1, 12.1, 12.2

### Theme, Styling, and Visual Systems

[Back to Table of Contents](#table-of-contents)

What and why:

- theming systems centralize design tokens, colors, and font roles for consistency.

Mental model:

- ThemeManager resolves active theme state
- scoped themes apply local overrides safely
- invalidation bus flushes visual caches on theme switch

Primary APIs:

- ThemeManager, ColorTheme, DesignTokens, ScopedThemeManager
- FontManager, FontRoleRegistry
- ThemeInvalidationBus

Typical usage flow:

1. define base theme and font roles
2. apply scoped overrides to subtrees when needed
3. trigger invalidation-aware redraw on theme changes

Minimal example:

```python
host.theme_manager.set_theme("light")
```

Advanced pattern:

- combine scoped themes with presenter tabs to represent per-window visual identity.

Common mistakes:

- direct color literals spread across features
- changing theme without invalidating cached surfaces

Cross-links: 8.5, 8.15, 11.2

### Text, Input, Forms, and Validation Systems

[Back to Table of Contents](#table-of-contents)

What and why:

- text and form systems support structured user entry, formatting, validation, and document-like editing.

Mental model:

- controls capture input
- models/schemas represent validation and cross-field logic
- async validators handle deferred checks with debouncing

Primary APIs:

- TextInputControl, TextAreaControl, DocumentModel
- FormModel, FormField, FormSchema, SchemaField
- ValidationPipeline and validator primitives
- AsyncFormValidator and SchemaFormRuntime

Typical usage flow:

1. define form schema/model
2. bind controls to model fields
3. run sync/async validation and display field errors

Minimal example:

```python
schema = FormSchema(fields=(SchemaField("email", required=True),))
runtime = SchemaFormRuntime(FieldGraphSchema.from_form_schema(schema), ValidationPolicy.ON_CHANGE)
```

Advanced pattern:

- async cross-field validation with cancellation and stale-result suppression.

Common mistakes:

- validating only on submit when continuous feedback is needed
- ignoring validation policy for dynamic visibility dependencies

Cross-links: 8.4, 8.14, 9.3

### Data and Dataflow Helpers

[Back to Table of Contents](#table-of-contents)

What and why:

- data helpers manage virtualized, cached, sorted, filtered, and staged data workloads.

Mental model:

- data providers feed controls efficiently
- pipeline stages transform data with cancellation safety

Primary APIs:

- VirtualItemSource, SortFilterProxySource, AsyncDataProvider
- DataCache, ObjectPool, ListDiffCalculator
- DataflowPipeline, PipelineStage, CancellationToken

Typical usage flow:

1. load data through async provider
2. wrap with filter/sort proxy
3. render via list/grid/tree or custom virtualized window

Minimal example:

```python
proxy = SortFilterProxySource(source)
proxy.set_filter(lambda row: row.name.startswith("A"))
```

Advanced pattern:

- staged dataflow pipeline with cancellation tokens feeding virtualization core windows.

Common mistakes:

- full-list redraws without diff calculation
- forgetting to cancel stale async/dataflow generations

Cross-links: 8.5, 8.10, 11.2

### Graphics and Audio Integration Points

[Back to Table of Contents](#table-of-contents)

What and why:

- graphics and audio modules support high-fidelity rendering and portable cue playback for rich UI scenarios.

Mental model:

- graphics assets and rendering layers are explicit
- audio cues are event-driven and portable via mixer wrappers

Primary APIs:

- DrawContext, DirtyRegionTracker, SurfaceCompositor, AssetRegistry
- ShapeRenderer, SurfaceEffects, SpriteSheet, ParticleSystem, SceneGraph2D
- SoundCue, SoundBankRegistry, SoundEventBus

Typical usage flow:

1. prepare assets and optional offscreen targets
2. update animations/effects in on_update
3. draw in ordered layers
4. publish sound cues on semantic events

Minimal example:

```python
host.sound_bus.publish(SoundCue("notify"))
```

Advanced pattern:

- dirty-region + offscreen render target composition with scene graph cameras and particle layers.

Common mistakes:

- unbounded full-surface redraw when dirty regions suffice
- triggering audio cues from low-level pointer noise instead of semantic actions

Cross-links: 8.10, 8.12, 11.2

### Telemetry, Introspection, and Operational Hooks

[Back to Table of Contents](#table-of-contents)

What and why:

- diagnostics systems expose runtime observability for profiling, analysis, and tooling.

Mental model:

- collect spans/samples in runtime hotspots
- inspect spatial/property state to explain behavior

Primary APIs:

- TelemetryCollector, TelemetrySample, configure_telemetry
- telemetry analyzer helpers
- PropertyRegistry/property_registry, PropertyInspectorModel, SceneSpatialIndex

Typical usage flow:

1. enable telemetry profile
2. capture records during scenario run
3. analyze and report

Minimal example:

```python
configure_telemetry(enabled=True)
```

Advanced pattern:

- combine telemetry traces with property inspector snapshots to localize layout or routing regressions.

Common mistakes:

- profiling without representative scenarios
- relying on visual inspection alone for performance issues

Cross-links: 10.3, 11, Appendix B

## Integration Patterns and Composition Recipes

[Back to Table of Contents](#table-of-contents)

### Recipe 1: Routed Feature + Actions + Shortcut Overlay

[Back to Table of Contents](#table-of-contents)

Goal: declarative runtime wiring with discoverable keyboard help.

Pattern:

1. define RoutedRuntimeSpec with ShortcutOverlaySpec
2. register action descriptors and hotkeys
3. bind routed lifecycle in bind_runtime

Validation:

- overlay toggle key works
- filtered/manual shortcuts render as expected

### Recipe 2: Window Presenter + Task Panel + Focus Toggle

[Back to Table of Contents](#table-of-contents)

Goal: multi-window scene with deterministic focus navigation and task-panel controls.

Pattern:

1. declare WindowSpec or AnchoredWindowSpec
2. build scene task panel and window toggles
3. bind TaskPanelFocusToggleSpec

Validation:

- hidden windows are excluded from focus traversal
- task-panel visibility and focus mode stay synchronized

### Recipe 3: State Store + Persistence + Snapshot Migration

[Back to Table of Contents](#table-of-contents)

Goal: resilient state restore across schema versions.

Pattern:

1. keep source-of-truth in AppStateStore
2. serialize workspace/snapshot state
3. migrate with SnapshotMigrator before restore

Validation:

- skipped/missing setting keys are reported, not fatal
- restore report fields are asserted in tests

### Recipe 4: Dataflow Pipeline + Telemetry + Error Boundary

[Back to Table of Contents](#table-of-contents)

Goal: safe background processing with measurable performance and graceful UI failure containment.

Pattern:

1. stage work in DataflowPipeline with cancellation
2. instrument runtime path with telemetry
3. isolate unstable controls inside ErrorBoundary

Validation:

- stale generations are canceled
- telemetry report identifies bottleneck stage

## End-to-End Reference Application

[Back to Table of Contents](#table-of-contents)

This chapter provides one consolidated application listing intended as a practical bridge between quickstart and production architecture. It demonstrates lifecycle hooks, action registration, overlay-related behavior, workspace persistence hooks, and telemetry enablement in one place.

### Reference Listing (Single File)

[Back to Table of Contents](#table-of-contents)

```python
import pathlib
import pygame
from pygame import Rect

from gui_do import (
  ActionSpec,
  Feature,
  FeatureSpec,
  HostApplicationConfig,
  LabelControl,
  ButtonControl,
  ObservableValue,
  RuntimeSceneSpec,
  RoutedRuntimeSpec,
  ShortcutOverlaySpec,
  RoutedFeatureLifecycleSpec,
  SceneSetupSpec,
  TelemetryConfig,
  bootstrap_host_application,
  bind_routed_feature_lifecycle,
  configure_telemetry,
)


WORKSPACE_PATH = pathlib.Path(".gui_do_workspace.json")


class MainFeature(Feature):
  def __init__(self) -> None:
    super().__init__("main_feature", scene_name="main")
    self.count = ObservableValue(0)

  def build(self, host) -> None:
    self.label = host.app.add(
      LabelControl("count_label", Rect(24, 24, 340, 30), "Count: 0"),
      scene_name="main",
    )
    host.app.add(
      ButtonControl("inc_button", Rect(24, 64, 160, 32), "Increment", on_click=self._increment),
      scene_name="main",
    )
    host.app.add(
      ButtonControl("save_button", Rect(200, 64, 160, 32), "Save Workspace", on_click=host.save_workspace),
      scene_name="main",
    )

  def bind_runtime(self, host) -> None:
    def _sync(value: int) -> None:
      self.label.text = f"Count: {value}"

    self._count_sub = self.count.subscribe(_sync)
    _sync(self.count.value)

  def shutdown_runtime(self, host) -> None:
    if hasattr(self, "_count_sub"):
      self._count_sub.dispose()

  def _increment(self) -> None:
    self.count.value = self.count.value + 1


class RoutedMainFeature(MainFeature):
  def __init__(self) -> None:
    super().__init__()
    self._runtime_spec = RoutedRuntimeSpec(
      scene_name="main",
      shortcut_overlays=(
        ShortcutOverlaySpec(
          attr_name="help_overlay",
          action_registry_attr="action_registry",
          toggle_action_name="show_help",
          toggle_key=pygame.K_F9,
          toggle_scene_name="main",
          manual_shortcut_lines=(
            "F9: Toggle shortcut help",
            "Esc: Exit (runtime scene policy)",
          ),
          prepend_manual_shortcuts=True,
        ),
      ),
    )
    self._lifecycle_spec = RoutedFeatureLifecycleSpec(
      runtime_spec=self._runtime_spec,
      runtime_spec_attr_name="_runtime_spec",
      scheduler_attr_name="scheduler",
    )

  def bind_runtime(self, host) -> None:
    super().bind_runtime(host)
    bind_routed_feature_lifecycle(self, host, self._lifecycle_spec)


class ManualReferenceApp:
  def __init__(self) -> None:
    configure_telemetry(enabled=True)
    self.config = HostApplicationConfig(
      display_size=(960, 640),
      window_title="gui_do End-to-End Reference",
      fonts={
        "default": {"system": "arial", "size": 16},
        "window": {"system": "arial", "size": 18, "bold": True},
      },
      font_role_specs=(),
      cursors=(),
      scene_specs=(
        SceneSetupSpec(name="main", pretty_name="Main", initial=True),
      ),
      feature_specs=(
        FeatureSpec(attr_name="main_feature", factory=RoutedMainFeature),
      ),
      window_specs=(),
      runtime_scene_specs=(
        RuntimeSceneSpec(scene_name="main", bind_escape_to_exit=True),
      ),
      action_specs=(
        ActionSpec(action_id="exit", label="Exit", kind="exit", category="File"),
        ActionSpec(action_id="show_help", label="Show Help", kind="command", category="Help"),
      ),
      static_accessibility_specs=(),
      initial_scene_name="main",
      telemetry=TelemetryConfig(enabled=True),
      target_fps=120,
    )
    bootstrap_host_application(self, self.config)

  def load_workspace(self) -> None:
    if WORKSPACE_PATH.exists() and hasattr(self.app, "load_workspace"):
      self.app.load_workspace(str(WORKSPACE_PATH))

  def save_workspace(self) -> None:
    if hasattr(self.app, "save_workspace"):
      self.app.save_workspace(str(WORKSPACE_PATH))
      if hasattr(self.app, "toasts"):
        self.app.toasts.show("Workspace saved")

  def run(self) -> None:
    self.load_workspace()
    try:
      self.app.run_entrypoint(target_fps=self.config.target_fps)
    finally:
      self.save_workspace()


if __name__ == "__main__":
  pygame.init()
  try:
    ManualReferenceApp().run()
  finally:
    pygame.quit()
```

### What This Listing Demonstrates

[Back to Table of Contents](#table-of-contents)

- Lifecycle: build, bind_runtime, and shutdown_runtime with safe subscription cleanup.
- Actions: exit and help actions in host configuration.
- Overlays: shortcut help overlay wiring via routed runtime spec.
- Persistence: load_workspace and save_workspace hooks with startup/shutdown integration.
- Telemetry: runtime telemetry enabled via both config and configure_telemetry.

### Validation Checklist

[Back to Table of Contents](#table-of-contents)

1. App opens into main scene without warnings.
2. Increment updates label through observable subscription.
3. F9 toggles help overlay.
4. Esc exits via runtime scene policy.
5. Workspace file is written on exit and loaded on next run.
6. Telemetry is enabled for runtime traces.

## Testing, Diagnostics, and Reliability

[Back to Table of Contents](#table-of-contents)

### Contract Tests

[Back to Table of Contents](#table-of-contents)

Run high-priority contract checks:

```bash
python -m pytest -q tests/test_public_api_exports.py tests/test_public_api_docs_contracts.py tests/test_runtime_operating_contracts.py tests/test_boundary_contracts.py
```

### Runtime Behavior Tests

[Back to Table of Contents](#table-of-contents)

Target areas:

- workspace load/save contract behavior
- overlay/tooltip/cursor routing
- layout and animation determinism
- control runtime and accessibility expectations

### Debug and Trace Tools

[Back to Table of Contents](#table-of-contents)

- EventRecorder/EventPlayback for reproducible input traces
- DebugOverlay and property inspector for visual/runtime state inspection
- telemetry log analysis for performance regressions

### Maintainer Release Runbook

[Back to Table of Contents](#table-of-contents)

Release gate sequence:

1. Run contract tests and boundary tests.
2. Run runtime operating and workspace contract tests.
3. Run representative integration scenarios from demo features.
4. Verify docs contract parity for public API and architecture docs.
5. Compare telemetry baseline to previous stable release.
6. Confirm migration notes and upgrade checklist are current.

Recommended command set:

```bash
python -m pytest -q tests/test_public_api_exports.py tests/test_public_api_docs_contracts.py tests/test_runtime_operating_contracts.py tests/test_boundary_contracts.py tests/test_gui_application_workspace_contracts.py
```

### Regression Triage Workflow

[Back to Table of Contents](#table-of-contents)

Triage sequence for behavioral regressions:

1. Reproduce with minimal feature-scoped case.
2. Capture input trace via EventRecorder.
3. Confirm whether regression violates a documented contract.
4. Localize to one subsystem: routing, focus, layout, persistence, or scheduling.
5. Add targeted test first, then patch.
6. Run adjacent contract tests before merge.

### Maintainer Diff Checklist

[Back to Table of Contents](#table-of-contents)

Run this checklist on every manual regeneration to keep updates consistent and auditable.

Inventory delta checks:

1. Compare current root exports in gui_do/__init__.py with Appendix D and D.1 entries.
2. Check docs/ contracts for changed guarantees, policies, or boundary rules.
3. Check tests/ for new contract/runtime test modules that imply manual updates.
4. Check demo_features/ for new recommended composition patterns to document.

Content integrity checks:

1. Every changed system has updates in both chapter narrative and quick-index references.
2. Removed APIs are deleted from examples, recipes, and appendix indexes.
3. Added APIs are classified at the right abstraction level (Tier 1 first, then lower tiers).
4. "What Changed Since Last Manual" includes explicit added, removed, and restructured notes.

Navigation and structure checks:

1. All newly added sections are present in TOC and resolve correctly.
2. Every major section still contains a Back to Table of Contents link.
3. Top-level chapter order remains stable unless intentional restructure is recorded.

Operational checks:

1. Re-run high-priority contract tests listed in this manual.
2. Validate end-to-end reference listing assumptions against current runtime behavior.
3. Record unresolved ambiguities as explicit TODO notes in migration/deprecation section.

### Manual Conformance Report (2026-05-04)

[Back to Table of Contents](#table-of-contents)

Checklist execution summary:

- Inventory delta checks: PASS
  - Sampled root-export inventory from gui_do/__init__.py for key systems (ServiceScope, DataflowPipeline, AppStateStore, SnapshotMigrator, ThemeInvalidationBus, UndoContextManager).
  - Verified representative advanced systems are present in chapter narrative or appendix index references.
- Content integrity checks: PASS
  - No stale symbol findings during this pass.
  - Tier guidance and chapter/appendix mapping remain consistent with current tiered API model.
- Navigation and structure checks: PASS
  - New sections introduced in recent passes are present in TOC and resolve.
  - Back to Table of Contents links remain present in major sections.
- Operational checks: PASS
  - Contract test suite executed:
    - python -m pytest -q tests/test_public_api_exports.py tests/test_public_api_docs_contracts.py tests/test_runtime_operating_contracts.py tests/test_boundary_contracts.py tests/test_gui_application_workspace_contracts.py
    - Result: 18 passed in 0.58s.

Open items:

- None identified in this pass.

## Performance and Scaling Guidance

[Back to Table of Contents](#table-of-contents)

### Scheduler Budget Contract

[Back to Table of Contents](#table-of-contents)

Current contract budget settings:

- fraction: 0.12 of frame dt milliseconds
- floor: 0.5 ms
- ceiling: 4.0 ms

### Virtualization and Incremental Rendering

[Back to Table of Contents](#table-of-contents)

Use:

- VirtualizationCore and VirtualizedWindow for large datasets
- ListDiffCalculator for minimal update sets
- DirtyRegionTracker for incremental rendering

### Practical Scaling Checklist

[Back to Table of Contents](#table-of-contents)

- enforce scene-scoped updates and handlers
- avoid per-frame full collection reallocation
- debounce expensive form and search operations
- use object pools for high-churn objects
- profile representative interactions, not synthetic idle only

## Migration, Versioning, and Deprecation Notes

[Back to Table of Contents](#table-of-contents)

### Versioned Snapshot Strategy

[Back to Table of Contents](#table-of-contents)

Use versioned snapshots as the persistence boundary:

1. write snapshot with schema version
2. read version on load
3. migrate through registered steps
4. restore into runtime models

### Deprecation Handling

[Back to Table of Contents](#table-of-contents)

Recommended policy:

- prefer additive transitions with compatibility windows
- remove legacy behavior only after migration path exists
- keep migration/deprecation notes centralized in this section and release notes

No deprecated public APIs are cataloged here currently. Add entries when formal deprecations are introduced.

### Upgrade Checklist

[Back to Table of Contents](#table-of-contents)

- run contract tests before and after upgrade
- verify root import usage for consumer entrypoints
- check action/input/focus routing behavior in active scenes
- validate workspace restore report for skipped/missing settings
- rerun telemetry baseline scenarios

## FAQ and Troubleshooting

[Back to Table of Contents](#table-of-contents)

Q: Should I build apps directly with controls or with features?

A: Use features as the architectural unit; controls are implementation details inside feature boundaries.

Q: When should I use RoutedFeature over Feature?

A: Use RoutedFeature when topic-based message dispatch and declarative runtime wiring reduce glue code.

Q: Why are some key handlers not firing?

A: Check focus ownership, window visibility/scope, overlay modal capture, and scene-scoped routing precedence.

Q: Why do toast clicks not pass through?

A: By contract, toast bounds consume clicks to prevent click-through; use explicit on_click callbacks for toast interactions.

Q: How do I avoid breaking workspace restore across versions?

A: Use versioned snapshots plus migration steps, and verify restore reports for skipped/missing settings.

Q: How do I confirm API usage is within supported surface?

A: Prefer explicit root imports from gui_do and validate with public API contract tests.

## Appendix

[Back to Table of Contents](#table-of-contents)

### Appendix A: Glossary

[Back to Table of Contents](#table-of-contents)

- Feature: lifecycle-managed application unit.
- Spec: declarative data object describing runtime wiring.
- Host: object passed into bootstrap that receives runtime members.
- Scene: top-level interaction context.
- Window presentation: window-level visibility and routing model.
- Routed runtime: declarative bundle of hotkeys, overlays, subscriptions, and toggles.
- Workspace state: persisted runtime context for restore.

### Appendix B: Lifecycle and Event Routing Sequence

[Back to Table of Contents](#table-of-contents)

Reference sequence:

1. bootstrap host from specs
2. feature build phase
3. feature bind_runtime phase
4. runtime loop begins
5. raw event normalized to GuiEvent
6. overlay/focus/window/scene routing
7. feature update and scheduled tasks
8. draw phase and present
9. shutdown_runtime and persistence save

### Appendix C: System Dependency Map

[Back to Table of Contents](#table-of-contents)

- Bootstrap depends on lifecycle, scene, action, and presentation specs.
- Features depend on controls, data/observables, and event/action systems.
- Layout and focus depend on control tree and scene/window visibility.
- Overlays depend on event routing and focus policy.
- Persistence depends on state models and scene/window registration.
- Telemetry/introspection cross-cut all runtime layers.

### Appendix D: API Quick Index by Topic

[Back to Table of Contents](#table-of-contents)

- Bootstrap: HostApplicationConfig, bootstrap_host_application, build_host_application_config
- Lifecycle: Feature, LogicFeature, DirectFeature, RoutedFeature, FeatureManager
- Events/Actions: GuiEvent, EventManager, EventBus, ActionManager, ActionRegistry, InputMap
- State/Data: ObservableValue, ObservableList, ObservableDict, AppStateStore, CollectionView
- Layout: ConstraintLayout, FlexLayout, GridLayout, DockWorkspace, ResponsiveLayout
- Overlays: OverlayManager, DialogManager, ToastManager, CommandPaletteManager, TooltipManager
- Persistence: WorkspacePersistenceManager, WorkspaceState, SceneSnapshot, SnapshotMigrator
- Forms: FormModel, FormSchema, ValidationPipeline, AsyncFormValidator, SchemaFormRuntime
- Graphics/Audio: DrawContext, DirtyRegionTracker, SpriteSheet, ParticleSystem, SoundEventBus
- Diagnostics: TelemetryCollector, configure_telemetry, PropertyInspectorModel, SceneSpatialIndex

### Appendix D.1: Tier-to-System Reference Matrix

[Back to Table of Contents](#table-of-contents)

- Tier 1: host bootstrap, lifecycle, runtime specs, host config builders.
- Tier 2: core app and scene lifecycle entrypoints.
- Tier 3: observable state and binding primitives.
- Tier 4: events, actions, input routing, gesture and interaction state.
- Tier 5: schedulers, timers, tweens, transitions, cooperative tasks.
- Tier 6 and 22: theme, font, scoped theme, theme invalidation.
- Tier 7 and 17: telemetry and inspection models.
- Tier 8: layout engines and spatial orchestration.
- Tier 9: overlays, dialogs, toast, menus, palette, cursor/drag services.
- Tier 10, 24, 31: forms, validation, async validation, schema runtime.
- Tier 11, 23, 27, 32: state history, undo context, app state store, migration.
- Tier 12 and 13: core and extended controls.
- Tier 14 and 15: text and advanced data collections/providers.
- Tier 16 and 20: graphics/rendering and audio cues.
- Tier 18: advanced runtime helpers and presenter orchestration.
- Tier 19: infrastructure internals, generally avoid in app-level code.
- Tier 21: accessibility semantics and announcements.
- Tier 25 and 26: service scopes and cancelable dataflow pipeline.
- Tier 28 to 30: adaptive constraints, virtualization core, interaction state machine framework.

### Appendix D.2: Public API Selection Heuristics

[Back to Table of Contents](#table-of-contents)

Selection rules for choosing the right abstraction level:

1. Prefer Tier 1 APIs first.
2. If you need finer runtime control, descend one tier at a time.
3. Use Tier 18 helpers when extending bootstrap behavior intentionally.
4. Avoid Tier 19 unless contributing framework internals.

Decision shortcuts:

- Need app setup: HostApplicationConfig and bootstrap_host_application.
- Need cross-feature behavior: lifecycle specs + routed runtime helpers.
- Need heavy dataset UI: virtualization/dataflow APIs before custom ad hoc loops.
- Need maintainable persistence: WorkspacePersistenceManager + SnapshotMigrator.

### Appendix E: Architecture Templates

[Back to Table of Contents](#table-of-contents)

Template 1: Small App

- 1 scene
- 2-4 features
- observable state in features
- action registry for commands

Template 2: Multi-Window Workbench

- scene menu strip + task panel
- window presenter and toggles
- routed runtime specs for hotkeys and overlays

Template 3: Data-Heavy Tool

- async provider + sort/filter proxy + virtualization
- dataflow pipeline for background transforms
- dirty-region rendering and telemetry baselines
