# gui_do Manual

## Title and Purpose
[Back to Table of Contents](#table-of-contents)

This manual is the primary end-to-end guide for developers building applications with gui_do. It is written for first-time users, intermediate implementers, and maintainers who need a reliable operational reference rooted in the current public API surface, runtime contracts, and tested behavior. The document is intentionally structured from theory to practice to system-level reference so a reader can both understand the architectural intent and apply it directly in production code.

## Table of Contents
[Back to Table of Contents](#table-of-contents)

- [Title and Purpose](#title-and-purpose)
- [Table of Contents](#table-of-contents)
- [How to Use This Manual](#how-to-use-this-manual)
- [Conceptual Foundations (Theory)](#conceptual-foundations-theory)
- [Quickstart Path (Practice)](#quickstart-path-practice)
- [Architecture and Runtime Model](#architecture-and-runtime-model)
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
  - [Appendix B: Lifecycle/Event Sequence](#appendix-b-lifecycleevent-sequence)
  - [Appendix C: System Dependency Map](#appendix-c-system-dependency-map)
  - [Appendix D: API Quick Index](#appendix-d-api-quick-index)
  - [Appendix D.1: Tier Matrix](#appendix-d1-tier-matrix)
  - [Appendix D.2: Selection Heuristics](#appendix-d2-selection-heuristics)
  - [Appendix E: Architecture Templates](#appendix-e-architecture-templates)

## How to Use This Manual
[Back to Table of Contents](#table-of-contents)

gui_do is broad enough that a linear read is not always the fastest route to results, so this chapter defines practical reading modes. Use Learn mode if you are new to the framework and want conceptual grounding before code. Use Build mode if you already know the architecture style and need to assemble a working app quickly. Use Maintain mode if you are validating API drift, contracts, and long-term compatibility.

Reading paths are intentionally opinionated. Beginner path: read Sections 3, 4, 5, 7, then systems 8.1 through 8.8 before attempting custom architecture. Intermediate path: read Sections 5, 6, 7, then jump to the system chapters that match your current workstream (for example, 8.10 for timing or 8.14 for data-heavy features). Maintainer path: read Sections 6 through 16 in full, then Appendix D and D.1 to verify exported names and tier mapping against current code.

Tri-Lens markers are used throughout this manual: Theory explains why a subsystem exists and which tradeoffs it makes, Practice shows concrete assembly patterns and code, and Operations defines runtime guarantees, diagnostics, and maintenance expectations. If you are debugging behavior, prioritize Practice and Operations. If you are designing new composition patterns, start with Theory and then validate in Operations.

Contract alignment is a standing requirement. This manual explains intent and usage, but normative guarantees are enforced by contract documentation and tests. Treat runtime contracts and boundary contracts as source-of-truth for guarantees such as scheduler budget clamping, restore report semantics, and import boundaries between framework and demo layers. When manual prose and runtime evidence diverge, update the prose to match code and tests.

### Known Non-Goals
[Back to Table of Contents](#table-of-contents)

- gui_do does not target OS-native widget parity across all platforms.
- gui_do does not replace application-specific domain architecture decisions.
- gui_do does not treat internal infrastructure tiers as beginner entry points.
- gui_do does not define star-import behavior as a compatibility contract.

## Conceptual Foundations (Theory)
[Back to Table of Contents](#table-of-contents)

### Data-Driven Design
[Back to Table of Contents](#table-of-contents)

Data-driven design in gui_do means the application is described first and executed second. Instead of wiring behavior through long chains of imperative setup calls, you define configuration objects that express scenes, features, actions, windows, accessibility, and runtime policies. The framework then interprets that configuration and performs the wiring in a deterministic way. This creates a clear boundary between intent and mechanism: your code describes what the application should contain, and the runtime decides how to realize it safely and consistently.

The entry point for this model is the specification pipeline centered on `HostApplicationBindingSpec`, the family of typed `*Spec` descriptors, and `build_host_application_config`. In practice, you define `FeatureSpec`, `SceneSetupSpec`, `RuntimeSceneSpec`, `WindowSpec`, `ActionSpec`, and related binding specs, then hand a high-level binding object to the builder. The builder resolves references and composes a concrete `HostApplicationConfig`. That config is then passed to `bootstrap_host_application`, which constructs the live runtime against the host object.

This two-phase approach is deliberate. First phase: construct and validate data. Second phase: execute runtime behavior. Because those phases are separated, tests can assert correctness at either boundary. You can test that config construction produces the expected feature and action graph without opening a display, and you can test runtime behavior separately with known-good config input. This sharply reduces ambiguity during debugging because failures are localized to either description or execution.

Compared to imperative wiring, the difference is substantial. In a traditional setup, adding one shortcut often means editing input dispatch code, injecting callback registration, and remembering teardown paths. In gui_do, you typically add an `ActionSpec` plus optional hotkey binding spec, and the runtime handles registration, routing, scope, and shutdown. The same pattern applies to scene setup, window toggles, and accessibility annotations. The framework centralizes lifecycle ownership so feature authors do not repeat infrastructure code.

Data-driven structure also protects bootstrap code from internal package churn. You can split a feature package into `*_feature.py`, `*_presenter.py`, and `*_specs.py`, or move helpers between modules, without touching app startup as long as public package exports remain stable. Bootstrap consumes class references and spec objects, not module path assumptions. This is a practical benefit for long-lived codebases where internal refactors are common.

Specs are intentionally rich objects rather than positional argument lists because they are self-describing and forward-compatible. Optional fields can be added over time without invalidating existing callers, which is difficult with narrowly shaped call signatures. They also form a clean serialization boundary: spec values are plain data and can be generated from templates, composed from higher-level builders, or inspected in tests for policy compliance.

The boundary of declarative design is important: wiring is declarative, behavior is imperative. Scene topology, action registration, and routing policies belong in specs. Frame-to-frame feature behavior still lives in Python methods such as `handle_event`, `on_update`, and `draw`. The recommended mental rule is to describe static structure declaratively and implement dynamic behavior imperatively.

### Reactive Data and Observable State
[Back to Table of Contents](#table-of-contents)

Reactive data in gui_do means state changes propagate to interested consumers without direct producer knowledge of those consumers. A feature that mutates state should not need to know which controls, presenters, or sibling features currently depend on that state. Instead, the state object handles subscription and notification. This reduces coupling and avoids fragile manual update chains where one missed callback can desynchronize the UI.

The foundational primitives are `ObservableValue`, `ObservableList`, and `ObservableDict`. `ObservableValue` wraps a single scalar or object reference and notifies subscribers when `.value` changes. Collection variants expose similar semantics for mutable data and can emit richer change descriptions through `CollectionChange` and `ChangeKind`, allowing consumers to react intelligently to inserts, removes, and updates instead of reprocessing entire structures.

Batching exists to control notification granularity. With `reactive_batch`, multiple related mutations can be grouped so downstream observers react once to the final coherent state instead of many intermediate states. `is_batching` allows advanced logic to guard work while a batch is open. This is especially useful when initializing form state, applying workspace restore payloads, or replaying synchronized updates where per-mutation callbacks would produce flicker or wasted computation.

Derived state is represented explicitly with `ComputedValue` when possible. A computed observable expresses dependency-driven recalculation as part of the model itself, whereas manual subscribe-and-copy patterns distribute derivation logic across callbacks and teardown points. Both approaches can work, but computed values make intent clearer and reduce subscription housekeeping in complex feature graphs.

Lifecycle discipline is critical for reactive systems. Subscriptions belong in runtime-aware phases such as `bind_runtime`, where sibling features and controls are known to exist. Cleanup belongs in teardown paths such as `shutdown_runtime` or equivalent feature shutdown hooks. If subscriptions outlive feature lifetime, memory leaks and phantom callbacks follow. A good pattern is to store unsubscribers on the feature instance and clear them deterministically during shutdown.

Control binding in gui_do is designed around the same principle: features mutate observables, controls react. Whether the binding is direct or wrapped through presenter code, the goal is that control rendering reflects model state without requiring imperative UI refresh calls across the app. This enables easier swapping of visual controls because business state and visual widgets are not tightly interleaved.

For cross-feature communication, observables are usually the first choice when sharing live state streams. One feature owns the source observable and exposes read/update pathways; other features subscribe in `bind_runtime`. This creates looser coupling than direct method calls and reduces order dependencies at scene startup. Messages and routing still matter for command-style interactions, but observables remain the preferred channel for continuous state propagation.

Common anti-patterns should be avoided early: polling observables every frame in `on_update`, subscribing in `build` before runtime wiring is stable, forgetting unsubscription on teardown, and sharing mutable plain dictionaries or lists between features without observable wrappers. These patterns either waste CPU or break the reactive contract, producing stale UI and hard-to-trace behavior.

### Feature Composition and Lifecycles
[Back to Table of Contents](#table-of-contents)

Features are the core composition unit in gui_do. A feature owns behavior scope, lifecycle hooks, and dependency declarations for one coherent slice of an application. Instead of centralizing all app logic in one monolith, gui_do expects applications to be assembled from multiple features that coexist in scenes and coordinate through observable state and message routing.

The framework exposes four primary feature types with distinct roles. `DirectFeature` is optimized for direct draw/update behavior when control-tree participation is unnecessary. `Feature` is the general-purpose interactive UI type that builds controls and participates in focus and routing. `LogicFeature` has no UI and is ideal for orchestration, domain processing, and shared reactive state. `RoutedFeature` extends feature behavior with routing-centric composition and works well when you want declarative runtime bundles for actions, overlays, and subscriptions.

Lifecycle phases are intentionally separated. `build(host)` constructs stable structure and creates controls. `bind_runtime(host)` performs runtime wiring after all scene features have completed build, enabling safe cross-feature coordination. `handle_event(host, event)` processes routed `GuiEvent` input and can consume propagation. `on_update(host, dt_seconds)` runs frame-based logic and should remain lightweight. `draw(host, screen)` handles custom rendering paths not captured by controls.

`HOST_REQUIREMENTS` makes dependencies explicit and machine-checkable. A feature declares the host attributes required by each lifecycle method, and runtime validation enforces that those attributes exist before invocation. This improves error quality and shifts dependency failures to startup rather than mid-frame exceptions. It also documents feature contracts in a way that is easier to test and review than implicit attribute access.

Inter-feature coordination favors loose coupling. `FeatureMessage` provides a route for message-style communication where producers emit intent and consumers subscribe by topic or handler registration, rather than holding direct references to each other. Combined with observables for shared state, this gives a practical split: use messages for discrete events and observables for continuous values.

Scene assignment keeps lifecycle boundaries clean. Each feature belongs to one scene context, and transitions activate/deactivate feature sets predictably. Departing scene features stop receiving event/update calls after teardown, reducing accidental bleed-through of stale state. Arriving scene features run build then bind in the same deterministic order guarantees used elsewhere.

A maintainable package convention further supports composition. Feature packages typically expose only public entry points from `__init__.py`, while internal files separate lifecycle code, presenter logic, and specs. Bootstrap imports from package surfaces, not internal modules. This keeps internal refactors low-risk and preserves stable consumer patterns.

Three composition recipes recur across real applications. First, logic plus presentation split: a `LogicFeature` owns computation and published state while a UI feature renders it. Second, presenter-led windows: a `WindowPresenter` subclass encapsulates window UI and a feature coordinates lifecycle. Third, long-running workflows: a logic feature coordinates scheduler/coroutine work and emits progress observables consumed by UI. These patterns are scalable because each concern has explicit ownership.

## Quickstart Path (Practice)
[Back to Table of Contents](#table-of-contents)

This quickstart is deliberately opinionated: start with Tier 1 configuration and bootstrap APIs, validate the build with contract tests, and only then add complexity. The fastest way to succeed in gui_do is to treat startup and wiring as declarative data from the beginning.

### Step 1: Install and Verify

```bash
python -m pip install -e . --no-deps
python -m pytest -q tests/test_public_api_exports.py
```

Install dependencies required by runtime behavior before launching an app. In this repository, `pygame` is required for input, surfaces, and frame loop operations, and `numpy` is required internally for pixel buffer operations through `PixelArray` workflows and related rendering paths. Running the export contract test immediately confirms your import surface is aligned with the package public API.

### Step 2: Create a Minimal Host

```python
from gui_do import (
  ActionSpec,
  Feature,
  FeatureSpec,
  HostApplicationConfig,
  RuntimeSceneSpec,
  SceneSetupSpec,
  WindowSpec,
  bootstrap_host_application,
)


class CounterFeature(Feature):
  def __init__(self) -> None:
    super().__init__("counter", scene_name="main")


config = HostApplicationConfig(
  display_size=(1280, 720),
  window_title="Quickstart",
  fonts={"default": {"system": "arial", "size": 14}},
  font_role_specs=(),
  cursors=(),
  scene_specs=(SceneSetupSpec(scene_name="main", pretty_name="Main"),),
  feature_specs=(FeatureSpec("counter_feature", CounterFeature),),
  window_specs=(),
  runtime_scene_specs=(
    RuntimeSceneSpec(scene_name="main", bind_escape_to_exit=True),
  ),
  action_specs=(
    ActionSpec(action_id="exit", label="Exit", kind="exit"),
  ),
  static_accessibility_specs=(),
  initial_scene_name="main",
)
```

`HostApplicationConfig` is the concrete runtime description consumed by bootstrap. For most real applications, you can build this object directly or generate it via `build_host_application_config` using `HostApplicationBindingSpec` and related bundle specs.

### Step 3: Add a Feature with Observable State

```python
from pygame import Rect

from gui_do import Feature, LabelControl, ObservableValue, PanelControl


class CounterFeature(Feature):
  HOST_REQUIREMENTS = {
    "build": ("app",),
    "bind_runtime": (),
  }

  def __init__(self) -> None:
    super().__init__("counter", scene_name="main")
    self.count = ObservableValue(0)
    self._unsubscribe = None

  def build(self, host) -> None:
    self.root = host.app.add(PanelControl("root", Rect(0, 0, 480, 160)), scene_name="main")
    self.label = self.root.add(LabelControl("count_label", Rect(16, 16, 260, 28), "Count: 0"))

  def bind_runtime(self, host) -> None:
    self._unsubscribe = self.count.subscribe(
      lambda value: setattr(self.label, "text", f"Count: {value}")
    )

  def shutdown_runtime(self, host) -> None:
    if self._unsubscribe is not None:
      self._unsubscribe()
      self._unsubscribe = None
```

### Step 4: Add an Action and Runtime Scene Policy

Add action entries to `action_specs` and scene execution policy to `runtime_scene_specs`. The most common starter policy is `bind_escape_to_exit=True` in `RuntimeSceneSpec`, which wires a consistent exit behavior without custom event plumbing. If you add additional command actions, keep action IDs stable and bind them with hotkey specs or routed runtime configuration.

### Step 5: Run Loop

```python
class Host:
  def __init__(self, cfg: HostApplicationConfig) -> None:
    bootstrap_host_application(self, cfg)

  def run(self) -> int:
    return self.app.run_entrypoint(target_fps=120)


if __name__ == "__main__":
  host = Host(config)
  raise SystemExit(host.run())
```

### Guided Build Track (Beginner)

1. Milestone A: app boots to a single scene with no errors.
2. Milestone B: one feature creates one visible control.
3. Milestone C: one observable updates one control reactively.
4. Milestone D: one action and one hotkey trigger expected behavior.
5. Milestone E: one overlay and one toast route without input leakage.
6. Milestone F: workspace save/load roundtrip succeeds.

Beginner confidence checklist:
- You can explain where `build` ends and `bind_runtime` begins.
- You can add or remove one feature through specs only.
- You can trace one keypress through routing into action execution.

### Quickstart Failure Modes

- Feature never appears: verify `feature_specs` contains the feature, and its `scene_name` matches a declared `SceneSetupSpec`.
- Hotkey does nothing: verify action descriptor exists and input binding scope matches current scene/window context.
- Overlay blocks unexpected keys: inspect overlay policy such as unhandled key consumption and dismissal configuration.
- State updates but UI does not: move subscription setup to `bind_runtime` and ensure teardown is not called early.

## Architecture and Runtime Model
[Back to Table of Contents](#table-of-contents)

### Boundary Model: Framework vs Consumer

The repository enforces a strict architectural boundary. `gui_do` is the reusable framework package and must not import from consumer code. Consumer composition lives in `demo_features` and the entrypoint module. This split protects framework portability and keeps demo/application concerns from leaking into runtime internals.

Consumer entrypoints should import from the root package surface, not internal submodules. This keeps applications resilient to internal framework refactors and aligns with the documented public API contract. Boundary behavior is enforced by tests, including checks that framework modules do not import demo features and that entrypoints use root imports.

### Tiered Public API Model

The root package exports are grouped by tier to signal recommended abstraction level. Tier 1 is the preferred starting point for new work: feature lifecycle classes, declarative specs, and bootstrap/config builders. Tier 2 through Tier 7 cover core runtime systems such as app management, observables, routing, scheduling, theming, and telemetry. Tier 8 and beyond provide lower-level or specialized capabilities including layout engines, overlays, form/runtime helpers, virtualization, graphics, introspection, and migration.

Tier numbers are a guidance mechanism, not merely categorization. When two approaches solve the same problem, prefer the lower-numbered tier first because it typically carries better lifecycle integration and fewer manual responsibilities.

### Runtime Guarantees

The runtime guarantees canonical `GuiEvent` normalization before app-level dispatch, scene-isolated execution for scene-contained runtime work, deterministic focus candidate ordering sorted by `control_id`, and scheduler dispatch budget clamping. Budget values are contract-defined: fraction `0.12`, floor `0.5 ms`, ceiling `4.0 ms`.

Workspace restore behavior is also contractual: missing settings keys are skipped rather than treated as fatal errors, and restore operations report applied, skipped, and missing categories to support diagnostics.

### Event Pipeline

At a high level, event processing follows a deterministic sequence:
1. Normalize incoming pygame input into `GuiEvent`.
2. Handle quit semantics early.
3. Update shared input state snapshots.
4. Update logical pointer state and apply lock/capture bounds.
5. Logicalize pointer payload while preserving raw coordinates.
6. Route through overlays, toasts, and focus-related infrastructure.
7. Route keyboard events through key routing policy and screen handlers.
8. Dispatch to feature and scene handlers in stable candidate order.
9. Honor `propagation_stopped` and `default_prevented` as hard stops.

### Known Non-Goals

- Full OS-native widget parity across every platform is not a framework objective.
- gui_do does not choose your domain-layer architecture for business logic.
- Internal infrastructure tiers are not intended as the default starting point.
- Star-import compatibility is not part of the public API contract.

## Core Workflow: Build, Bind, Route, Update, Draw
[Back to Table of Contents](#table-of-contents)

The five-phase workflow is the practical core of gui_do application design. It gives each piece of code one job at one time: construct stable structure, wire runtime dependencies, process routed intent, update time-based state, and render custom visuals only where necessary. Teams that preserve this separation get simpler debugging and more predictable scene behavior.

### Phase Reference

`build` is construction-only. Instantiate controls, initialize local observable containers, and define static structural relationships. The invariant is that runtime wiring should not happen here; no cross-feature assumptions and no long-lived subscriptions.

`bind_runtime` is wiring-only. Attach actions, subscriptions, routed lifecycle helpers, and host-bound integrations after all scene siblings are built. The invariant is that controls and sibling features now exist, so cross-feature links and subscriptions are safe.

`route` is intent dispatch. Events and messages flow through declared mappings and handlers instead of ad hoc branching spread across modules. This is where action IDs, message names, and routing policies convert input into behavior.

`update` is frame-time logic. Timers, transitions, coroutines, and incremental state progression occur here. The invariant is bounded work: avoid unbounded loops and heavy blocking operations.

`draw` is custom rendering escape hatch. Use it when control primitives cannot express visual needs. Keep rendering concerns separate from model mutation to prevent order-dependent bugs.

### Message and Logic Coordination

`FeatureMessage` is designed for decoupled signaling between features. Use messages when you need discrete semantic events such as state transition completion, command intent, or data readiness notifications. Use observable state when consumers need continuous value updates over time. A common pattern is a `LogicFeature` that owns processing state and emits both observables and occasional feature messages to drive UI feature reactions.

### When to Use Routed Runtime Specs

`RoutedRuntimeSpec` and `RoutedFeatureLifecycleSpec` reduce repetitive lifecycle boilerplate where routing concerns are dense. They are especially useful when one feature has multiple action hotkeys, shortcut overlay behavior, task-panel focus toggles, and event subscriptions that should automatically bind/unbind with lifecycle. In that model, `bind_routed_feature_lifecycle` performs coordinated runtime registration during bind, and `shutdown_routed_feature_lifecycle` guarantees symmetric cleanup on teardown.

The practical benefit is less manual registration drift. Declarative routed lifecycle specs keep registration state visible in one place and reduce the risk of orphaned bindings during scene transitions.

## Main Systems Reference
[Back to Table of Contents](#table-of-contents)

### Application Bootstrap and Host Configuration
[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Application bootstrap is the deterministic assembly layer for gui_do. Instead of constructing runtime services piecemeal, you hand a complete config graph to the bootstrap system and it materializes app state in one coordinated pass. This avoids the common failure mode of partial wiring where actions, scenes, and features are initialized in different places with implicit ordering dependencies.

#### Mental model and lifecycle placement

Treat the host as a plain object that receives runtime members after bootstrap. Configuration comes first, then execution. `build_host_application_config` transforms high-level binding specs into a concrete `HostApplicationConfig`; `bootstrap_host_application` applies it. Once bootstrap returns, scene setup, feature registration, action mappings, fonts, cursors, and runtime scene policies are ready for `run_entrypoint`.

#### Primary public APIs and key types

Primary bootstrap APIs: `HostApplicationConfig`, `HostApplicationBindingSpec`, `bootstrap_host_application`, `build_host_application_config`.

Common spec types: `FeatureSpec`, `WindowSpec`, `RuntimeSceneSpec`, `ActionSpec`, `SceneSetupSpec`, `SceneRootSpec`, `StaticAccessibilitySpec`, `CursorSpec`, `ActionHotkeySpec`, `ControlKeyBindingSpec`, `PaletteBindingSpec`, `SceneBundleBindingSpec`, `FeatureWindowBundleBindingSpec`, `WindowToggleBindingSpec`, `RuntimeSceneBindingSpec`, `SceneSetupBindingSpec`, `FontRoleBindingSpec`, `CursorBindingSpec`.

Bootstrap-related app APIs: `GuiApplication`, `create_display`, `SceneTransitionManager`, `SceneTransitionStyle`, `apply_scene_setup_specs`.

#### Typical usage flow

1. Declare scenes and features with `SceneSetupSpec` and `FeatureSpec`.
2. Declare actions, runtime scene policy, accessibility, fonts, and cursors.
3. Build config directly or via `HostApplicationBindingSpec` plus builder helpers.
4. Call `bootstrap_host_application(host, config)`.
5. Run the loop with `host.app.run_entrypoint(...)`.

#### Minimal example

```python
from gui_do import (
  ActionSpec,
  Feature,
  FeatureSpec,
  HostApplicationConfig,
  RuntimeSceneSpec,
  SceneSetupSpec,
  bootstrap_host_application,
)


class MyFeature(Feature):
  def __init__(self) -> None:
    super().__init__("my_feature", scene_name="main")


cfg = HostApplicationConfig(
  display_size=(1280, 720),
  window_title="My App",
  fonts={"default": {"system": "arial", "size": 14}},
  font_role_specs=(),
  cursors=(),
  scene_specs=(SceneSetupSpec(scene_name="main", pretty_name="Main"),),
  feature_specs=(FeatureSpec("my_feature", MyFeature),),
  window_specs=(),
  runtime_scene_specs=(RuntimeSceneSpec(scene_name="main", bind_escape_to_exit=True),),
  action_specs=(ActionSpec(action_id="exit", label="Exit", kind="exit"),),
  static_accessibility_specs=(),
  initial_scene_name="main",
)


class Host:
  pass


host = Host()
bootstrap_host_application(host, cfg)
```

#### Advanced pattern(s)

For larger apps, use `HostApplicationBindingSpec` with bundles such as `SceneBundleBindingSpec` and `FeatureWindowBundleBindingSpec`, then generate config through `build_host_application_config`. This scales better than hand-managing cross-references because the builder resolves relationships in a single deterministic pass.

#### Common mistakes and anti-patterns

- Mixing direct host mutation with declarative config causes drift between declared and actual runtime state.
- Declaring feature scene names that do not exist in scene setup specs results in unreachable features.
- Forgetting `initial_scene_name` can produce startup routing ambiguity.

#### Cross-links to related systems

See 8.2 for lifecycle behavior, 8.3 for routing internals, and 8.11 for workspace persistence interactions.

[Back to Table of Contents](#table-of-contents)

### Feature Lifecycle and Feature Types
[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Feature lifecycle orchestration is the primary behavior model in gui_do. Features let you express independent units of app behavior that can be built, wired, updated, and torn down predictably as scenes activate and deactivate. This is the main mechanism that keeps applications composable as scope grows.

#### Mental model and lifecycle placement

Each feature owns a scene scope and a lifecycle. `build` constructs stable UI structure; `bind_runtime` attaches runtime dependencies after all scene features are built; `handle_event`, `on_update`, and `draw` participate in frame execution; shutdown hooks release subscriptions and runtime registrations. Keep phase boundaries strict for predictable startup and teardown.

#### Primary public APIs and key types

Core types: `Feature`, `DirectFeature`, `LogicFeature`, `RoutedFeature`, `FeatureMessage`, `FeatureManager`, `ScenePresentationModel`.

Routed lifecycle helpers: `RoutedRuntimeSpec`, `RoutedFeatureLifecycleSpec`, `bind_routed_feature_lifecycle`, `shutdown_routed_feature_lifecycle`, `setup_routed_feature_runtime`, `register_routed_feature_companions`, `register_companion_logic_features`.

Dependency contract: `HOST_REQUIREMENTS` per lifecycle phase.

#### Typical usage flow

1. Choose the right feature type (`Feature`, `LogicFeature`, `RoutedFeature`, or `DirectFeature`).
2. Declare `HOST_REQUIREMENTS` for methods that need host attributes.
3. Build controls in `build`.
4. Bind subscriptions and cross-feature links in `bind_runtime`.
5. Clean up subscriptions and routed lifecycle registrations in shutdown.

#### Minimal example

```python
from pygame import Rect

from gui_do import Feature, LabelControl, ObservableValue, PanelControl


class StatusFeature(Feature):
  HOST_REQUIREMENTS = {"build": ("app",), "bind_runtime": ()}

  def __init__(self) -> None:
    super().__init__("status", scene_name="main")
    self.status = ObservableValue("Ready")
    self._unsubscribe = None

  def build(self, host) -> None:
    self.root = host.app.add(PanelControl("status_root", Rect(8, 8, 320, 80)), scene_name="main")
    self.label = self.root.add(LabelControl("status_label", Rect(8, 8, 260, 24), "Ready"))

  def bind_runtime(self, host) -> None:
    self._unsubscribe = self.status.subscribe(lambda value: setattr(self.label, "text", value))

  def shutdown_runtime(self, host) -> None:
    if self._unsubscribe is not None:
      self._unsubscribe()
```

#### Advanced pattern(s)

Use logic/presentation splits: a `LogicFeature` owns processing and publishes state through observables while a `RoutedFeature` owns UI and action routing. Combine with `RoutedFeatureLifecycleSpec` to declaratively bind hotkeys, event subscriptions, and overlay behavior with automatic cleanup.

#### Common mistakes and anti-patterns

- Subscribing in `build` before all runtime peers exist.
- Putting expensive computation in `on_update` instead of scheduler/dataflow systems.
- Registering routed hooks without symmetric shutdown, which leaves stale handlers after scene transitions.

#### Cross-links to related systems

See 8.1 for bootstrap setup, 8.3 for event/action routing, and 8.10 for timing and scheduler usage.

[Back to Table of Contents](#table-of-contents)

### Events, Actions, Input Mapping, and Routing
[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

This system translates raw input into stable semantic events and routes them through action and focus-aware policies. Without this layer, each feature would implement its own input interpretation and key-scoping logic, quickly producing inconsistent behavior.

#### Mental model and lifecycle placement

The runtime first normalizes incoming pygame events into `GuiEvent`, then routes through overlays, focus/window policy, scene handlers, and feature handlers in deterministic order. Actions are named intents executed by the action subsystem, while input maps bind keys/chords to action IDs. Routing semantics are contract-defined, including hard stops for `propagation_stopped` and `default_prevented`.

#### Primary public APIs and key types

Events: `GuiEvent`, `EventType`, `EventPhase`, `EventManager`, `EventBus`, `InputSnapshot`, `Signal`, `SignalConnection`, `ValueChangeCallback`, `ValueChangeReason`, `GestureRecognizer`, `EventRecorder`, `EventPlayback`, `RecordedEvent`.

Actions/input: `ActionManager`, `ActionRegistry`, `ActionDescriptor`, `ActionContext`, `ActionMiddleware`, `InputMap`, `InputBinding`, `KeyChordManager`, `KeyChord`, `ChordStep`.

Focus/routing context: `FocusManager`, `FocusScope`, `FocusScopeManager`, `WindowFocusManager`, `FocusRing`.

Spec-layer bindings: `ActionSpec`, `ActionHotkeySpec`, `ControlKeyBindingSpec`, `EventSubscriptionSpec`.

#### Typical usage flow

1. Define `ActionSpec` entries in config.
2. Bind hotkeys through runtime specs or input map helpers.
3. Process events as `GuiEvent` in features, not raw pygame payloads.
4. Return consumption signals from handlers (`True` or propagation/default flags).
5. Use recorder/playback for deterministic event regression tests.

#### Minimal example

```python
from gui_do import ActionSpec, RuntimeSceneSpec


action_specs = (
  ActionSpec(action_id="exit", label="Exit", kind="exit"),
  ActionSpec(action_id="palette_open", label="Open Command Palette", kind="palette_open"),
)

runtime_scene_specs = (
  RuntimeSceneSpec(scene_name="main", bind_escape_to_exit=True),
)
```

#### Advanced pattern(s)

Use `InteractionStateMachine` for guarded multi-phase input flows such as press-drag-release gestures with explicit transition guards. For difficult regressions, capture traces with `EventRecorder` and replay them through `EventPlayback` to validate routing behavior under controlled conditions.

#### Common mistakes and anti-patterns

- Handling raw pygame events in feature code and bypassing normalized `GuiEvent` behavior.
- Assuming handlers are global when they are scene/window scoped.
- Ignoring hard-stop semantics from `propagation_stopped` and `default_prevented`.

#### Cross-links to related systems

See 8.2 for lifecycle placement of routing hooks, 8.7 for focus/accessibility implications, and 8.8 for overlay routing precedence.

[Back to Table of Contents](#table-of-contents)

### State and Observables
[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

State and observables provide the reactive substrate for gui_do features and controls. The goal is to keep model mutation decoupled from view update mechanics so UI stays synchronized without imperative refresh orchestration.

#### Mental model and lifecycle placement

Treat observables as the live data bus. Features mutate observable state, controls and sibling features subscribe. Set up long-lived subscriptions in `bind_runtime` and tear them down in shutdown. Use higher-level state stores when multiple features need atomic updates and selector-based derived views.

#### Primary public APIs and key types

Reactive primitives: `ObservableValue`, `ObservableList`, `ObservableDict`, `CollectionChange`, `ChangeKind`, `ComputedValue`, `PresentationModel`, `reactive_batch`, `is_batching`.

Querying/binding helpers: `CollectionView`, `CollectionViewQuery`, `Binding`, `BindingGroup`, `ObservableStream`, `InvalidationTracker`, `SelectionModel`, `SelectionMode`.

Transactional store: `AppStateStore`, `StateSelector`, `StateTransaction`.

#### Typical usage flow

1. Create observables in feature initialization.
2. Build controls in `build`.
3. Subscribe in `bind_runtime` and update control properties in callbacks.
4. Use `reactive_batch` when applying related multi-field updates.
5. Dispose callbacks in shutdown.

#### Minimal example

```python
from gui_do import ObservableValue, reactive_batch


counter = ObservableValue(0)


def on_change(value):
  print("counter", value)


unsubscribe = counter.subscribe(on_change)
with reactive_batch():
  counter.value = 1
  counter.value = 2
unsubscribe()
```

#### Advanced pattern(s)

Use `AppStateStore` as a single source of truth for multi-feature applications. Derive feature-local slices with `StateSelector`, apply coordinated mutations with `StateTransaction`, and expose read-only projections to UI features while logic features own mutation authority.

#### Common mistakes and anti-patterns

- Polling state from `on_update` instead of subscribing.
- Sharing mutable plain dict/list objects between features without observable wrappers.
- Forgetting to unsubscribe callbacks, causing leaks and stale notifications.

#### Cross-links to related systems

See 8.2 for lifecycle-safe wiring, 8.5 for control binding surfaces, and 8.11 for persistence interactions with state snapshots.

[Back to Table of Contents](#table-of-contents)

### Controls and Control Composition
[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Controls are reusable UI primitives and composites that let features express interface structure without re-implementing rendering, hit-testing, or event wiring each time. gui_do treats controls as implementation details inside feature boundaries, which supports clean architecture: features own behavior and orchestration, controls own visual and interaction components.

#### Mental model and lifecycle placement

A feature builds a root container, then composes child controls under that root. Control trees participate in layout and event routing while feature lifecycle methods decide when and how those trees are created and wired. Keep control creation in `build`, and keep cross-feature coordination out of direct control references.

#### Primary public APIs and key types

Tier 12 controls: `PanelControl`, `LabelControl`, `ButtonControl`, `ToggleControl`, `SliderControl`, `ScrollbarControl`, `CanvasControl`, `CanvasEventPacket`, `CanvasViewport`, `FrameControl`, `ImageControl`, `ArrowBoxControl`, `ButtonGroupControl`, `TabControl`, `TabItem`, `DockWorkspacePanel`.

Tier 13 controls: `TextInputControl`, `TextAreaControl`, `RichLabelControl`, `DropdownControl`, `DropdownOption`, `ListViewControl`, `ListItem`, `OverlayPanelControl`, `DataGridControl`, `GridColumn`, `GridRow`, `TreeControl`, `TreeNode`, `SplitterControl`, `SpinnerControl`, `RangeSliderControl`, `ColorPickerControl`, `ScrollViewControl`, `ProgressBarControl`, `AnimatedImageControl`, `ErrorBoundary`, `WindowControl`, `TaskPanelControl`, `WindowPresenter`, `MenuBarControl`, `MenuEntry`, `SceneMenuStripControl`, `NotificationPanelControl`, `PropertyInspectorPanel`, `ToolbarControl`, `ToolbarItem`, `StatusBarControl`, `StatusSlot`, `ExpanderControl`, `DatePickerControl`, `TimePickerControl`, `BreadcrumbControl`, `BreadcrumbItem`, `SplitButtonControl`, `SplitButtonOption`, `ChipInputControl`.

Declarative helper APIs: `ControlDefinition`, `build_specs_from_column_section`.

#### Typical usage flow

1. Build a root `PanelControl` for feature-owned UI.
2. Add child controls for display and input.
3. Apply layout manager or layout primitives.
4. Bind controls to observables in runtime wiring.
5. Use presenters for window-level composition when needed.

#### Minimal example

```python
from pygame import Rect

from gui_do import ButtonControl, LabelControl, PanelControl


def build(self, host):
  self.root = host.app.add(PanelControl("my_root", Rect(0, 0, 400, 220)), scene_name="main")
  self.label = self.root.add(LabelControl("status", Rect(12, 12, 240, 24), "Ready"))
  self.root.add(ButtonControl("go", Rect(12, 44, 120, 28), "Go", on_click=self._on_go))
```

#### Advanced pattern(s)

Use `WindowPresenter` as a presenter/controller boundary for window content. The presenter owns window child controls and window-level behavior (`on_create`, `on_show`, `on_hide`, `on_resize`, `before_update`, `after_update`) while `WindowControl` continues to own chrome and host-level routing. This keeps feature lifecycle code focused on composition and wiring rather than window-internal rendering details.

`ErrorBoundary` is useful for fault isolation in high-risk UI subtrees. Wrap complex or plugin-like control branches so one rendering exception degrades gracefully instead of crashing the frame.

#### Common mistakes and anti-patterns

- Using controls as the source of truth instead of binding them to observables.
- Creating hidden cross-feature control references instead of communicating through feature state or messages.
- Building controls in `on_update` or event handlers, which causes lifecycle instability.

#### Cross-links to related systems

See 8.2 for lifecycle placement, 8.6 for layout strategy, 8.7 for focus/accessibility behavior, and 8.9 for window presentation composition.

[Back to Table of Contents](#table-of-contents)

### Layout Systems
[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Layout systems in gui_do solve spatial organization problems so feature code does not hardcode fragile pixel arithmetic. They enable responsive behavior, docking, snapping, and adaptive constraints with predictable update costs.

#### Mental model and lifecycle placement

Choose the simplest layout model that matches your region. Use flow/flex for straightforward stacks, grid/constraint for structured forms and anchored relationships, dock workspace for complex pane composition, and virtualization-aware layout where item counts are large. Layout runs as part of frame lifecycle after control trees exist.

#### Primary public APIs and key types

Tier 8 layout APIs: `LayoutAxis`, `LayoutManager`, `WindowTilingManager`, `ConstraintLayout`, `AnchorConstraint`, `DockPane`, `DockTabs`, `DockSplit`, `DockWorkspace`, `FlexLayout`, `FlexItem`, `FlexDirection`, `FlexAlign`, `FlexJustify`, `GridLayout`, `GridTrack`, `GridPlacement`, `CellCaretLayout`, `CellCaretState`, `LayoutAnimator`, `LayoutPass`, `MeasureContext`, `ArrangeContext`, `LayoutRoot`, `ResponsiveLayout`, `Breakpoint`, `SnapGrid`, `AlignmentGuide`, `SnapComposer`, `SnapTarget`, `FlowLayout`, `FlowItem`, `Viewport`.

Tier 28 adaptive constraint APIs: `ConstraintAttr`, `LayoutConstraint`, `ConstraintSet`, `ConstraintLayoutEngine`, `AdaptivePolicy`, `resolve_adaptive_policy`.

Tier 29 virtualization APIs: `MeasureMode`, `MeasurePolicy`, `VirtualizedWindow`, `RecyclePool`, `VirtualizationCore`.

#### Typical usage flow

1. Select layout family based on region needs.
2. Create container controls and attach layout engine.
3. Register child controls and constraints/items.
4. Apply responsive/adaptive policies for breakpoints.
5. Validate with resize and high-density test cases.

#### Minimal example

```python
from gui_do import FlexDirection, FlexItem, FlexLayout


layout = FlexLayout(direction=FlexDirection.ROW, gap=8)
layout.add(FlexItem(control=sidebar, grow=0, basis=220))
layout.add(FlexItem(control=content, grow=1))
```

#### Advanced pattern(s)

Use `ConstraintLayoutEngine` with `AdaptivePolicy` to switch constraints across width breakpoints while preserving semantic control relationships. For large dynamic collections, combine virtualization (`VirtualizationCore`, `RecyclePool`) with diffed updates so layout cost scales with visible windows, not total item count.

#### Common mistakes and anti-patterns

- Mixing multiple layout engines on one container without clear ownership boundaries.
- Hardcoding fixed dimensions for regions that should respond to viewport changes.
- Running manual geometry mutation loops every frame instead of expressing constraints once.

#### Cross-links to related systems

See 8.5 for control composition, 8.9 for window/scene presentation geometry, and 8.10 for layout animation timing.

[Back to Table of Contents](#table-of-contents)

### Focus and Accessibility
[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Focus and accessibility systems ensure keyboard routing is coherent and UI semantics are available to assistive and testing tools. In multi-window and overlay-heavy apps, this subsystem prevents lost key focus, hidden-target traversal, and inaccessible custom controls.

#### Mental model and lifecycle placement

Focus management determines which control receives keyboard input at any moment, while accessibility provides a semantic tree parallel to control structure. Focus scope controls interaction boundaries (for example, modal dialog lock-in), and accessibility nodes communicate role/name/description/live updates.

#### Primary public APIs and key types

Focus APIs from Tier 4: `FocusManager`, `FocusScope`, `FocusScopeManager`, `WindowFocusManager`, `FocusRing`.

Accessibility APIs from Tier 21: `AccessibilityRole`, `LivePoliteness`, `AccessibilityNode`, `AccessibilityTree`, `AccessibilityAnnouncement`, `AccessibilityBus`.

Related spec APIs: `AccessibilitySequenceSpec`, `StaticAccessibilitySpec`, `TaskPanelFocusToggleSpec`.

#### Typical usage flow

1. Define static accessibility descriptors for known controls.
2. Add custom accessibility nodes for custom-rendered controls.
3. Ensure hidden or disabled controls are removed/excluded from focus traversal.
4. Use focus scopes for modal or constrained interaction contexts.
5. Verify traversal and announcements with focused behavior tests.

#### Minimal example

```python
from gui_do import AccessibilityNode, AccessibilityRole, AccessibilityTree


tree = AccessibilityTree()
button_node = AccessibilityNode(role=AccessibilityRole.BUTTON, name="Save")
tree.root.add_child(button_node)
```

#### Advanced pattern(s)

Use `TaskPanelFocusToggleSpec` with window visibility controls so hidden windows are automatically excluded from focus traversal and restored when shown again. For complex forms and panels, apply `AccessibilitySequenceSpec` to guarantee deterministic keyboard traversal independent of visual nesting complexity.

#### Common mistakes and anti-patterns

- Leaving hidden-window controls in focus traversal order.
- Omitting semantic roles for custom canvas-based controls.
- Creating accessibility nodes before owning trees and runtime context are initialized.

#### Cross-links to related systems

See 8.3 for routing behavior, 8.5 for control semantics, and 8.8 for modal overlay focus capture.

[Back to Table of Contents](#table-of-contents)

### Overlays, Dialogs, Notifications, and Command Surfaces
[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Transient and modal surfaces need explicit event routing contracts so they do not destabilize main scene input behavior. gui_do provides specialized managers for overlays, dialogs, toasts, context menus, command surfaces, and transfer operations, each with clear dismissal and consumption policies.

#### Mental model and lifecycle placement

Overlay routing runs ahead of normal scene dispatch. If an overlay consumes input, underlying controls do not receive it. This ordering prevents click-through errors and preserves modal semantics. Managers are specialized because each surface type has different activation and dismissal rules.

#### Primary public APIs and key types

Tier 9 overlay APIs: `OverlayManager`, `OverlayHandle`, `Alignment`, `PlacementResult`, `PopupPlacement`, `Side`, `compute_popup_rect`, `DialogManager`, `DialogHandle`, `ToastManager`, `ToastHandle`, `ToastSeverity`, `ContextMenuManager`, `ContextMenuItem`, `ContextMenuHandle`, `CommandPaletteManager`, `CommandEntry`, `CommandPaletteHandle`, `TooltipManager`, `TooltipHandle`, `MenuBarManager`, `FileDialogManager`, `FileDialogOptions`, `FileDialogHandle`, `NotificationCenter`, `NotificationRecord`, `ResizeManager`, `CursorManager`, `CursorHandle`, `CursorShape`, `DragDropManager`, `DragPayload`, `ClipboardManager`, `TransferData`, `TransferManager`, `ShortcutHelpOverlay`, `ShortcutSection`, `ShortcutEntry`.

Spec-level integration: `ShortcutOverlaySpec`, `NotificationSpec`, scene command palette bindings.

#### Typical usage flow

1. Register overlay managers through bootstrap/runtime setup.
2. Show overlays/dialogs/toasts through their manager APIs.
3. Configure dismissal and input consumption behavior explicitly.
4. Use popup placement helpers for edge-safe positioning.
5. Route command palette and shortcut help through declarative bindings.

#### Minimal example

```python
def on_saved(host):
  host.toasts.show("Saved", severity="info")
```

#### Advanced pattern(s)

Use `ShortcutOverlaySpec` with routed lifecycle setup so help overlays are auto-registered with feature bind/unbind. Combine `DragDropManager`, `TransferManager`, and `ClipboardManager` for cross-surface transfer workflows where drop targets can also accept pasted payload representations.

#### Common mistakes and anti-patterns

- Expecting toast clicks to pass through to underlying controls.
- Registering overlay-specific key handlers without considering modal capture policy.
- Positioning popups manually and ignoring edge clamping from `compute_popup_rect`.

#### Cross-links to related systems

See 8.3 for routing order, 8.7 for focus lock behavior, and 8.9 for scene/window presentation integration.

[Back to Table of Contents](#table-of-contents)

### Scene, Window, and Task-Panel Presentation Models
[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Scenes provide top-level interaction contexts, windows provide focused work surfaces within scenes, and task panels expose discoverable command affordances for scene-local operations. Together they form the presentation model that controls what is visible, what can receive focus, and which interaction affordances are currently active.

#### Mental model and lifecycle placement

Scenes are mode boundaries. Features are registered to scenes, windows are registered to scene presentation state, and task-panel controls are scene-scoped command surfaces. Build window structure during feature build, wire toggles and dynamic presentation behavior during bind runtime, and keep window visibility and focus policy synchronized through presentation helpers.

#### Primary public APIs and key types

Primary presentation types: `ScenePresentationModel`, `WindowSpec`, `AnchoredWindowSpec`, `SceneTaskPanelSpec`, `TaskPanelButtonSpec`, `TaskPanelLinearLayoutSpec`, `TaskPanelWindowToggleGroupSpec`, `TaskPanelFocusToggleSpec`, `TaskPanelSceneNavButtonSpec`, `SceneCommandPaletteSpec`, `TabbedPresenterSpec`, `TabBuilderSpec`, `FeatureWindowBundleBindingSpec`, `WindowToggleBindingSpec`.

Tier 18 helpers for this chapter: `set_window_visible_state`, `toggle_window_visibility`, `create_anchored_feature_window`, `create_feature_presented_window`, `create_presented_window_from_spec`, `create_presented_anchored_window`, `register_window_presentation_specs`, `add_window_scene_menu_strip`, `ensure_scene_task_panel`, `create_task_panel_linear_layout`, `add_task_panel_button`, `add_task_panel_buttons`, `add_task_panel_window_toggle_group`, `add_task_panel_scene_nav_button`, `add_scene_task_panel_items`, `bind_task_panel_focus_toggle`, `setup_feature_presenter_tabs`, `setup_feature_presenter_tabs_from_window_content`, `register_window_tab_builders`, `register_window_tab_builder_specs`, `create_tab_control_from_specs`, `build_tab_builder_specs`, `compute_tabbed_window_layout`, `register_tab_update_handlers`, `ActiveTabUpdateRouter`, `TabLayoutContext`.

#### Typical usage flow

1. Declare scene and window specs in config.
2. Build window content via feature code and optional presenter pattern.
3. Register task-panel and menu-strip integration for window toggles.
4. Bind focus toggle behavior for hidden-window exclusion.
5. Keep menu/task-panel state synchronized with presentation model visibility.

#### Minimal example

```python
from gui_do import create_feature_presented_window


self.window = create_feature_presented_window(
  host,
  feature=self,
  control_id="tools_window",
  title="Tools",
)
```

#### Advanced pattern(s)

Use tabbed window composition with `TabbedPresenterSpec`, `TabBuilderSpec`, and `ActiveTabUpdateRouter` so only active-tab logic receives expensive updates. Pair this with task-panel window toggle groups to provide consistent visibility controls and explicit slot ordering.

#### Common mistakes and anti-patterns

- Creating windows in bind phase rather than build phase, which breaks sibling assumptions.
- Toggling window visibility without updating focus exclusion rules.
- Treating scene and window scope as interchangeable for action handlers.

#### Cross-links to related systems

See 8.2 for lifecycle ordering, 8.7 for focus synchronization, and 8.8 for command/overlay surfaces.

[Back to Table of Contents](#table-of-contents)

### Scheduling, Timing, Animation, and Transitions
[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Timing systems in gui_do let applications run animations, staged transitions, delayed work, and cooperative workflows without blocking frame delivery. They exist to keep behavior smooth under changing frame times while maintaining deterministic operational limits.

#### Mental model and lifecycle placement

Scheduler and animation managers are runtime services consumed by features during update/bind phases. Time-based operations should be registered once, then ticked by the runtime each frame. Contract-defined dispatch limits prevent scheduler work from starving rendering.

#### Primary public APIs and key types

Tier 5 scheduling APIs: `TaskEvent`, `TaskScheduler`, `Timers`, `TweenManager`, `TweenHandle`, `Easing`, `AnimationSequence`, `AnimationHandle`, `TransitionManager`, `TransitionSpec`, `TransitionEvent`, `AnimationStateMachine`, `AnimationTransitionMode`, `SceneTimeline`, `Debouncer`, `Throttler`, `CooperativeScheduler`, `CoroutineHandle`, `Pause`, `Sleep`, `WaitForEvent`, `WaitForSignal`, `WaitUntil`, `WaitForAll`.

Related dataflow APIs: `CancellationToken`, `PipelineStage`, `DataflowPipeline`, `PipelineHandle`.

Scheduler budget contract: fraction `0.12` of dt milliseconds, floor `0.5 ms`, ceiling `4.0 ms`.

#### Typical usage flow

1. Register timers/tweens/transitions in runtime wiring.
2. Use `on_update` for lightweight progression and trigger checks.
3. Use cooperative yields (`Sleep`, `WaitForSignal`, `WaitUntil`) for multi-frame workflows.
4. Cancel or dispose handles at shutdown.
5. Profile timeline-heavy scenes with telemetry.

#### Minimal example

```python
def show_panel(self, host):
  self._fade = host.tweens.to(self.panel, "alpha", 255, duration=0.2)
```

#### Advanced pattern(s)

Use cooperative scheduler workflows that wait for user-driven signals without blocking UI: coroutine starts, yields `WaitForSignal`, continues to trigger transition and toast, then yields `Sleep` before final cleanup. For expensive staged transforms, compose with `DataflowPipeline` and cancellation tokens so stale generations are discarded when input changes.

#### Common mistakes and anti-patterns

- Doing heavy synchronous work directly in `on_update`.
- Forgetting to cancel animation/tween handles on scene exit.
- Running blocking I/O in cooperative coroutine bodies.

#### Cross-links to related systems

See 8.2 for update lifecycle placement, 8.14 for dataflow background work, and 8.16 for telemetry profiling.

[Back to Table of Contents](#table-of-contents)

### Persistence and Workspace/Session State
[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Persistence systems preserve user context across sessions and protect application behavior during upgrades by making state serialization, restore reporting, and snapshot migration explicit. This improves reliability for real-world workflows where restarts and version changes are normal.

#### Mental model and lifecycle placement

Think of workspace persistence as structured checkpointing. Save captures runtime state; restore rehydrates scene and feature state with safety rails for unknown or missing settings keys. Versioned snapshot migration handles schema evolution before restore applies state to runtime objects.

#### Primary public APIs and key types

Tier 11: `CommandHistory`, `Command`, `CommandTransaction`, `StateMachine`, `HierarchicalStateMachine`, `Router`, `RouteEntry`, `SettingsRegistry`, `SettingDescriptor`, `WorkspaceState`, `WorkspacePersistenceManager`, `DEFAULT_WORKSPACE_STATE_PATH`, `SceneSnapshot`, `NodeSnapshot`.

Tier 23: `UndoContextManager`.

Tier 32 migration APIs: `SchemaVersion`, `VersionedSnapshot`, `MigrationStep`, `MigrationRegistry`, `SnapshotMigrator`, `MigrationError`, `make_snapshot`, `read_version`.

Restore report fields: `target_scene`, `switched_scene`, `restored_feature_states`, `restored_scene_nodes`, `applied_settings`, `skipped_settings`, `missing_settings_blocks`.

#### Typical usage flow

1. Register settings descriptors and stable keys.
2. Save workspace on lifecycle boundaries.
3. Load workspace and inspect restore report.
4. Handle skipped/missing categories gracefully.
5. Use snapshot versioning and migration for schema changes.

#### Minimal example

```python
host.app.save_workspace(path)
report = host.app.load_workspace(path)
if report and report.skipped_settings:
  host.toasts.show("Some settings were skipped during restore")
```

#### Advanced pattern(s)

Combine `AppStateStore` snapshots with `VersionedSnapshot` and `SnapshotMigrator` so state schema changes remain backward-loadable. Register explicit migration steps for each version transition and treat `MigrationError` as a recoverable operational path with user-visible fallback behavior.

#### Common mistakes and anti-patterns

- Assuming all historical settings keys always exist.
- Loading snapshots without checking schema version and migration path.
- Using one default workspace path for multi-instance deployments.

#### Cross-links to related systems

See 8.1 for bootstrap wiring, 8.4 for state model composition, and 8.16 for operational diagnostics.

[Back to Table of Contents](#table-of-contents)

### Theme, Styling, and Visual Systems
[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Theme and styling systems centralize visual policy so applications can change look-and-feel without rewriting feature logic or hardcoding color/font constants across control code.

#### Mental model and lifecycle placement

Fonts and theme tokens are configured during bootstrap, then consumed by controls and render paths at runtime. Theme switches should trigger invalidation of cached visual artifacts so new tokens are reflected immediately and consistently.

#### Primary public APIs and key types

Tier 6 theme APIs: `FontManager`, `FontRoleRegistry`, `ColorTheme`, `ThemeManager`, `DesignTokens`, `ScopedTheme`, `ScopedThemeManager`.

Tier 22 invalidation API: `ThemeInvalidationBus`.

Related spec types: `FontRoleBindingSpec`, `CursorSpec`, `CursorBindingSpec`, and utility `setup_standard_font_roles`.

#### Typical usage flow

1. Declare fonts and font roles in config.
2. Build controls using role-based style assumptions, not literal font handles.
3. Configure theme manager with tokenized color/spacing policy.
4. Apply scoped theme overrides where local visual language differs.
5. Broadcast invalidation on theme change for cached draw surfaces.

#### Minimal example

```python
host.theme_manager.set_theme("light")
```

#### Advanced pattern(s)

Use `ScopedThemeManager` for per-window visual identity while retaining global token inheritance. Subscribe custom caches to `ThemeInvalidationBus` so expensive offscreen text or shape caches rebuild only when theme changes, not every frame.

#### Common mistakes and anti-patterns

- Hardcoding colors and spacing in feature draw code.
- Switching themes without invalidating render caches.
- Registering font roles late after controls assume role availability.

#### Cross-links to related systems

See 8.1 for bootstrap role setup, 8.5 for control rendering behavior, and 8.15 for custom drawing integration.

[Back to Table of Contents](#table-of-contents)

### Text, Input, Forms, and Validation Systems
[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

This system area covers interactive text entry, structured forms, validation policies, and localization-aware text formatting. It exists because real UI workflows need far more than raw key events: they need form semantics, validation pipelines, async checks, and maintainable field dependencies.

#### Mental model and lifecycle placement

Controls capture raw input, form/runtime models define structure and validation behavior, and validators produce domain-level correctness signals. Build controls in feature build, wire model bindings in runtime bind, and route expensive validations through debounced/async paths to avoid frame stalls.

#### Primary public APIs and key types

Tier 10 forms/data-binding APIs: `FormModel`, `FormField`, `ValidationRule`, `FieldError`, `FormSchema`, `SchemaField`, `DocumentModel`, `WizardFlow`, `WizardStep`, `WizardHandle`, `ValidationResult`, `Validator`, `RequiredValidator`, `RangeValidator`, `LengthValidator`, `PatternValidator`, `CustomValidator`, `DependentValidator`, `ValidationPipeline`.

Tier 24 async validation APIs: `AsyncFieldValidator`, `AsyncFormValidator`.

Tier 31 schema runtime APIs: `FieldSchema`, `FieldGraphSchema`, `ValidationPolicy`, `SchemaFormRuntime`.

Tier 14 text/localization APIs: `TextFormatter`, `NumericFormatter`, `PatternFormatter`, `FixedPatternFormatter`, `TextFlow`, `TextSpan`, `TextSearcher`, `TextMatch`, `StringTable`, `LocaleRegistry`.

Input-oriented controls from Tier 13: `TextInputControl`, `TextAreaControl`, `SpinnerControl`, `DatePickerControl`, `TimePickerControl`, `ColorPickerControl`, `ChipInputControl`.

#### Typical usage flow

1. Define form schema and validation rules.
2. Build input controls and bind them to form fields.
3. Configure validation policy (`on change`, `on submit`, or mixed).
4. Add async validators for remote checks.
5. Surface errors and completion status through observables.

#### Minimal example

```python
from gui_do import FormModel, PatternValidator, RequiredValidator


form = FormModel()
form.add_field("email", validators=[RequiredValidator(), PatternValidator(r".+@.+")])
```

#### Advanced pattern(s)

Use `SchemaFormRuntime` with a `FieldGraphSchema` to express conditional visibility and dependency-driven validation. Pair this with `AsyncFormValidator` to debounce uniqueness checks against external services while suppressing stale results when users keep typing.

#### Common mistakes and anti-patterns

- Validating only at submit for workflows that require immediate feedback.
- Running async checks on every keystroke without debounce/cancellation.
- Splitting validation logic across feature methods instead of central pipelines.

#### Cross-links to related systems

See 8.4 for observable binding strategy, 8.5 for input control composition, and 8.14 for dataflow-backed validation workflows.

[Back to Table of Contents](#table-of-contents)

### Data and Dataflow Helpers
[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Data systems provide scalable loading, filtering, sorting, diffing, caching, and virtualization for data-heavy UI experiences. They exist to avoid rebuilding large collections every frame and to keep interaction responsive under large datasets.

#### Mental model and lifecycle placement

Treat data handling as a staged pipeline: source data providers, transform proxies, and render windows. Use cancellation-aware background stages for expensive transforms and incremental diff application for view updates.

#### Primary public APIs and key types

Tier 15 data APIs: `VirtualItemSource`, `FixedItemSource`, `SortFilterProxySource`, `AsyncDataProvider`, `LoadState`, `LoadStateKind`, `ObjectPool`, `DataCache`, `CacheStats`, `ListDiffCalculator`, `ListDiff`, `DiffInsert`, `DiffRemove`, `DiffMove`.

Tier 26 pipeline APIs: `CancellationToken`, `PipelineStage`, `DataflowPipeline`, `PipelineHandle`.

Tier 27 store APIs: `AppStateStore`, `StateSelector`, `StateTransaction`.

Tier 29 virtualization APIs: `MeasureMode`, `MeasurePolicy`, `VirtualizedWindow`, `RecyclePool`, `VirtualizationCore`.

#### Typical usage flow

1. Choose or implement a source (`FixedItemSource` or custom `VirtualItemSource`).
2. Apply transforms with `SortFilterProxySource`.
3. Feed visible windows/controls through virtualization.
4. Run expensive transform stages in `DataflowPipeline`.
5. Apply incremental UI updates from list diff output.

#### Minimal example

```python
source = FixedItemSource(items)
proxy = SortFilterProxySource(source)
proxy.set_filter(lambda item: item.active)
proxy.set_sort_key(lambda item: item.name)
```

#### Advanced pattern(s)

Build a cancelable three-stage pipeline (load, normalize, score) using `DataflowPipeline` and `CancellationToken`, and bind progress/status to observables consumed by list or grid controls. Use `RecyclePool` with virtualization to avoid churn in item renderers and keep frame costs predictable as data volume scales.

#### Common mistakes and anti-patterns

- Recomputing full sorted/filtered lists every frame.
- Ignoring cancellation, causing stale-result flashes.
- Using object pooling without ownership discipline.

#### Cross-links to related systems

See 8.10 for cooperative timing, 8.13 for form-bound search/filter UX, and 8.16 for performance instrumentation.

[Back to Table of Contents](#table-of-contents)

### Graphics and Audio Integration Points
[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Graphics and audio integrations support experiences that exceed stock control rendering, including particles, tile maps, scene graphs, custom draw phases, and semantic sound cues. They exist so advanced visuals and audio can remain structured and testable instead of ad hoc draw side effects.

#### Mental model and lifecycle placement

Custom rendering belongs in feature draw hooks or canvas controls, while audio cues belong to semantic events rather than raw pointer noise. Use asset registries and render targets for deterministic resource use and layered compositing.

#### Primary public APIs and key types

Tier 16 graphics APIs: `BuiltInGraphicsFactory`, `DirtyRegionTracker`, `DrawContext`, `DrawPhase`, `AssetRegistry`, `DebugOverlay`, `SurfaceCompositor`, `Layer`, `ShapeRenderer`, `SurfaceEffects`, `VectorPath`, `SpriteSheet`, `FrameAnimation`, `ParticleSystem`, `Emitter`, `ParticleLayer`, `TileSet`, `TileMap`, `RenderTarget`, `LiveRenderTarget`, `OffscreenRenderTarget`, `create_render_target`, `create_surface`, `Node2D`, `SceneGraph2D`, `Camera2D`.

Tier 20 audio APIs: `SoundCue`, `SoundBankRegistry`, `SoundEventBus`.

#### Typical usage flow

1. Load assets via `AssetRegistry`.
2. Update visual systems (particles, animation, scene graph) during update phase.
3. Draw through `DrawContext`/phases and optional offscreen targets.
4. Use dirty-region tracking to reduce redraw work.
5. Publish semantic audio cues through `SoundEventBus`.

#### Minimal example

```python
def on_notify(host):
  host.sound_bus.publish(SoundCue("notify"))
```

#### Advanced pattern(s)

Combine `DirtyRegionTracker` with `OffscreenRenderTarget` and layer compositing to redraw only changed regions in a complex scene. For world-space visualization, use `SceneGraph2D` + `Camera2D` and emit particles from interaction events while keeping audio cues attached to semantic action completion.

#### Common mistakes and anti-patterns

- Full-surface redraws for small local changes.
- Loading assets in per-frame draw paths.
- Triggering sounds from low-level movement noise instead of user-level actions.

#### Cross-links to related systems

See 8.5 for canvas/control integration, 8.10 for animation timing, and 8.16 for draw-cost telemetry.

[Back to Table of Contents](#table-of-contents)

### Telemetry, Introspection, and Operational Hooks
[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Operational visibility systems provide measurable insight into runtime behavior and make regressions diagnosable. Telemetry captures performance data, introspection exposes inspectable properties, and spatial indexing supports geometry-aware diagnostics.

#### Mental model and lifecycle placement

Instrumentation should be enabled before running representative interaction scenarios. Introspection metadata should be declared alongside control/property definitions. Diagnostics are most useful when integrated with testing and release gating rather than used ad hoc only after failures.

#### Primary public APIs and key types

Tier 7 telemetry APIs: `TelemetryCollector`, `TelemetrySample`, `configure_telemetry`, `telemetry_collector`, `analyze_telemetry_log_file`, `analyze_telemetry_records`, `load_telemetry_log_file`, `render_telemetry_report`.

Tier 17 introspection APIs: `SceneSpatialIndex`, `ui_property`, `PropertyDescriptor`, `PropertyRegistry`, `property_registry`, `PropertyInspectorModel`, `InspectedProperty`.

Related integration points: `TelemetryConfig`, `DebugOverlay`, `PropertyInspectorPanel`.

#### Typical usage flow

1. Enable telemetry at startup.
2. Execute representative scenarios.
3. Analyze captured records and identify hotspots.
4. Inspect runtime properties and geometry to localize anomalies.
5. Convert findings to regression tests.

#### Minimal example

```python
from gui_do import analyze_telemetry_records, configure_telemetry, telemetry_collector


configure_telemetry(enabled=True)
report = analyze_telemetry_records(telemetry_collector.records)
```

#### Advanced pattern(s)

Pair telemetry traces with a custom debug panel fed by `PropertyInspectorModel` and `SceneSpatialIndex` overlays. This allows frame-time spikes to be correlated with specific control regions and runtime property transitions.

#### Common mistakes and anti-patterns

- Profiling idle loops and treating results as representative.
- Enabling diagnostics only after regressions appear, without baseline traces.
- Ignoring telemetry when adjusting scheduler or dataflow policies.

#### Cross-links to related systems

See 8.10 for scheduler budget behavior, 8.11 for restore diagnostics, and 8.15 for graphics performance analysis.

[Back to Table of Contents](#table-of-contents)

## Integration Patterns and Composition Recipes
[Back to Table of Contents](#table-of-contents)

### Recipe 1: Routed Feature + Actions + Shortcut Overlay

Goal: build a feature whose shortcuts are discoverable and lifecycle-managed.

Why this combination: routed lifecycle specs keep shortcut registration, overlay behavior, and cleanup in one declarative place, reducing registration drift.

Pattern:
1. Define `ActionSpec` entries.
2. Build `RoutedRuntimeSpec` with `ShortcutOverlaySpec`.
3. Create `RoutedFeatureLifecycleSpec` that references runtime spec.
4. Bind with `bind_routed_feature_lifecycle` in `bind_runtime`.
5. Unbind with `shutdown_routed_feature_lifecycle` in shutdown.

Validation notes: confirm overlay toggle key works, action list appears as expected, and shutdown removes handlers.

### Recipe 2: Window Presenter + Task Panel + Focus Toggle

Goal: make a toggleable floating window with correct focus behavior.

Why this combination: window presenters isolate UI construction, and task-panel focus toggles keep traversal coherent when windows hide/show.

Pattern:
1. Declare `AnchoredWindowSpec` and task-panel metadata.
2. Implement `WindowPresenter` subclass for content.
3. Create window in feature build (`create_feature_presented_window`).
4. Configure `TaskPanelFocusToggleSpec` in routed runtime.
5. Route visibility through `set_window_visible_state`.

Validation notes: hidden window exits focus ring; task-panel toggle state matches visibility.

### Recipe 3: State Store + Persistence + Snapshot Migration

Goal: keep app state evolvable across versions.

Why this combination: centralized state plus versioned snapshots gives deterministic restore and explicit migration paths.

Pattern:
1. Define `AppStateStore` and selectors.
2. Snapshot with `make_snapshot`.
3. Read version with `read_version` on load.
4. Migrate with `SnapshotMigrator` and registered `MigrationStep`s.
5. Restore and inspect report fields for skipped/missing settings.

Validation notes: contract tests cover restore behavior; migration graph includes all supported legacy versions.

### Recipe 4: Dataflow Pipeline + Telemetry + Error Boundary

Goal: run background transforms safely and measurably.

Why this combination: cancellation avoids stale UI, telemetry finds bottlenecks, and error boundaries prevent total-frame failure.

Pattern:
1. Define staged `DataflowPipeline` with per-stage cancellation tokens.
2. Add telemetry spans around stage callbacks.
3. Render output inside `ErrorBoundary` subtree.
4. Publish stage progress through `ObservableValue`.

Validation notes: stale generations cancel cleanly, telemetry identifies hottest stage, and fallback UI appears on renderer exception.

[Back to Table of Contents](#table-of-contents)

## End-to-End Reference Application
[Back to Table of Contents](#table-of-contents)

```python
from pygame import Rect

from gui_do import (
  ActionSpec,
  FeatureSpec,
  HostApplicationConfig,
  LabelControl,
  ObservableValue,
  PanelControl,
  RoutedFeature,
  RoutedFeatureLifecycleSpec,
  RoutedRuntimeSpec,
  RuntimeSceneSpec,
  SceneSetupSpec,
  ShortcutOverlaySpec,
  TelemetryConfig,
  bootstrap_host_application,
  bind_routed_feature_lifecycle,
  shutdown_routed_feature_lifecycle,
)


class CounterFeature(RoutedFeature):
  HOST_REQUIREMENTS = {"build": ("app",), "bind_runtime": ()}

  def __init__(self) -> None:
    super().__init__("counter_feature", scene_name="main")
    self.count = ObservableValue(0)
    self._unsub = None
    runtime = RoutedRuntimeSpec(
      shortcut_overlay=ShortcutOverlaySpec(
        toggle_action_name="help_toggle",
        toggle_key=None,
        manual_shortcut_lines=("F9: Toggle help", "Esc: Exit"),
      )
    )
    self._lifecycle = RoutedFeatureLifecycleSpec(runtime=runtime)

  def build(self, host) -> None:
    self.root = host.app.add(PanelControl("counter_root", Rect(0, 0, 420, 140)), scene_name="main")
    self.label = self.root.add(LabelControl("counter_label", Rect(12, 12, 260, 24), "Count: 0"))

  def bind_runtime(self, host) -> None:
    self._unsub = self.count.subscribe(
      lambda value: setattr(self.label, "text", f"Count: {value}")
    )
    bind_routed_feature_lifecycle(self, host, self._lifecycle)

  def shutdown_runtime(self, host) -> None:
    shutdown_routed_feature_lifecycle(self, host, self._lifecycle)
    if self._unsub is not None:
      self._unsub()
      self._unsub = None


config = HostApplicationConfig(
  display_size=(1280, 720),
  window_title="Reference App",
  fonts={"default": {"system": "arial", "size": 14}},
  font_role_specs=(),
  cursors=(),
  scene_specs=(SceneSetupSpec(scene_name="main", pretty_name="Main"),),
  feature_specs=(FeatureSpec("counter_feature", CounterFeature),),
  window_specs=(),
  runtime_scene_specs=(RuntimeSceneSpec(scene_name="main", bind_escape_to_exit=True),),
  action_specs=(
    ActionSpec(action_id="exit", label="Exit", kind="exit"),
    ActionSpec(action_id="help_toggle", label="Toggle Help", kind="palette_open"),
  ),
  static_accessibility_specs=(),
  initial_scene_name="main",
  telemetry=TelemetryConfig(enabled=True),
)


class Host:
  def __init__(self) -> None:
    bootstrap_host_application(self, config)

  def run(self) -> int:
    return self.app.run_entrypoint(target_fps=120)

  def save_workspace(self, path: str) -> None:
    self.app.save_workspace(path)

  def load_workspace(self, path: str):
    return self.app.load_workspace(path)


if __name__ == "__main__":
  host = Host()
  raise SystemExit(host.run())
```

### What This Listing Demonstrates

This listing demonstrates declarative startup with `HostApplicationConfig`, routed feature lifecycle wiring, reactive label updates via `ObservableValue`, action-driven behavior, scene runtime policy with escape-to-exit, telemetry enablement, and workspace save/load hooks on the host facade.

### Validation Checklist

1. App opens to `main` scene and remains responsive.
2. Counter observable mutations update label text.
3. Help toggle action binds correctly and overlay can be shown/hidden.
4. Escape exits via runtime scene policy.
5. Telemetry collector receives records during interactive use.
6. Workspace save/load calls return expected restore report data.

[Back to Table of Contents](#table-of-contents)

## Testing, Diagnostics, and Reliability
[Back to Table of Contents](#table-of-contents)

Reliability in gui_do is contract-driven. Behavior is not considered stable because it appears to work in an ad hoc demo run; it is stable only when it aligns with root exports, documentation contracts, runtime operating guarantees, and test-enforced boundary rules. This chapter describes how to validate that alignment before release and how to triage regressions when it breaks.

### Contract Tests

Run the high-priority contract command:

```bash
python -m pytest -q tests/test_public_api_exports.py tests/test_public_api_docs_contracts.py tests/test_runtime_operating_contracts.py tests/test_boundary_contracts.py tests/test_gui_application_workspace_contracts.py
```

File coverage intent:
- `test_public_api_exports.py`: verifies root-exported names are importable and present.
- `test_public_api_docs_contracts.py`: validates API documentation alignment.
- `test_runtime_operating_contracts.py`: validates normalization, determinism, and runtime guarantees.
- `test_boundary_contracts.py`: verifies framework/consumer import boundaries.
- `test_gui_application_workspace_contracts.py`: verifies workspace load/save and restore behavior.

Additional contract/runtime-focused modules discovered in this repository include:
- `test_architecture_boundary_docs_contracts.py`
- `test_demo_feature_package_contracts.py`
- `test_core_only_bootstrap_contracts.py`
- `test_runtime_guarantees_and_determinism.py`

### Runtime Behavior Tests

Prioritize runtime scenarios that combine subsystems: workspace restore with missing settings keys, overlay/focus/key-routing interactions, animation determinism under bounded budgets, and accessibility/focus traversal in window hide/show transitions. These tests catch integration regressions that isolated unit tests can miss.

### Debug and Trace Tools

Use `EventRecorder` and `EventPlayback` to capture and replay deterministic input traces. Use `DebugOverlay` and `PropertyInspectorPanel` to inspect live visual and property state without modifying feature logic. For performance profiling, enable telemetry and analyze traces with `analyze_telemetry_log_file`, `analyze_telemetry_records`, and `render_telemetry_report`.

### Maintainer Release Runbook

1. Run contract tests first and fix any API/contract drift.
2. Run runtime determinism tests and scene/workspace restore tests.
3. Execute targeted demo workflows that exercise overlays, routing, layout, and persistence.
4. Capture telemetry baselines on representative interactions.
5. Re-verify manual guidance against observed behavior before tagging release.

### Regression Triage Workflow

1. Reproduce with a deterministic scenario.
2. Capture event and telemetry traces.
3. Localize subsystem ownership (routing, state, layout, persistence, etc.).
4. Write or extend a failing test before patching.
5. Patch with minimum scope and re-run adjacent contract tests.
6. Record unresolved ambiguity in migration/deprecation notes.

### Maintainer Diff Checklist

Inventory delta checks:
1. Compare current root exports in gui_do/__init__.py with Appendix D and D.1 entries.
2. Check docs contracts for changed guarantees, policies, or boundary rules.
3. Check tests for new contract/runtime test modules that imply manual updates.
4. Check demo_features for new recommended composition patterns to document.

Content integrity checks:
1. Every changed system has updates in both chapter narrative and quick-index references.
2. Removed APIs are deleted from examples, recipes, and appendix indexes.
3. Added APIs are classified at the right abstraction level (Tier 1 first, then lower tiers).

Navigation and structure checks:
1. All newly added sections are present in TOC and resolve correctly.
2. Every major section still contains a Back to Table of Contents link.
3. Top-level chapter order remains stable unless intentional restructure is recorded.

Operational checks:
1. Re-run high-priority contract tests.
2. Validate end-to-end reference listing assumptions against current runtime behavior.
3. Record unresolved ambiguities as explicit TODO notes in migration/deprecation section.

Contract test command:

```bash
python -m pytest -q tests/test_public_api_exports.py tests/test_public_api_docs_contracts.py tests/test_runtime_operating_contracts.py tests/test_boundary_contracts.py tests/test_gui_application_workspace_contracts.py
```

[Back to Table of Contents](#table-of-contents)

## Performance and Scaling Guidance
[Back to Table of Contents](#table-of-contents)

### Scheduler Budget Contract

Scheduler dispatch budget is contract-defined: fraction `0.12` of dt milliseconds, floor `0.5 ms`, ceiling `4.0 ms`. The fraction prevents unbounded scheduling growth when frames are slow, and floor/ceiling values avoid starvation under both very fast and very slow frame conditions.

### Dirty-Region Rendering

`DirtyRegionTracker` is the first optimization to apply in complex scenes. Use dirty marks for changed regions and check overlap before costly redraws. This prevents full-frame redraws when only localized areas change.

### Virtualization and Incremental Rendering

Use `VirtualizationCore` and `VirtualizedWindow` for large list/tree/grid workloads. Pair with `RecyclePool` for view reuse and `ListDiffCalculator` for minimal update patches. Combined, these reduce both draw and allocation pressure.

### Practical Scaling Checklist

1. Keep updates scene-scoped and handler-scoped.
2. Avoid per-frame full collection allocation.
3. Debounce expensive search/form work with `Debouncer`.
4. Use `DataflowPipeline` plus `CancellationToken` for preemptible transforms.
5. Profile representative user flows, not idle loops.
6. Gate expensive draw paths with dirty-region checks.

[Back to Table of Contents](#table-of-contents)

## Migration, Versioning, and Deprecation Notes
[Back to Table of Contents](#table-of-contents)

### Versioned Snapshot Strategy

Recommended workflow:
1. Write snapshots with `make_snapshot(current_version, state_dict)`.
2. Read incoming version with `read_version(raw_snapshot)`.
3. Migrate via `SnapshotMigrator` and registered `MigrationStep` graph.
4. Restore only migrated snapshots into runtime.

`MigrationRegistry` owns directed migration steps, and `SnapshotMigrator` resolves paths across versions. `MigrationError` indicates missing or invalid migration routes and should be handled with recoverable UX paths.

### Deprecation Handling

Prefer additive transitions: introduce new optional fields and maintain compatibility while warning. Remove old behavior only after a documented migration path is available. As of this generation pass, no formal deprecated public APIs are cataloged here; maintainers should add entries when explicit deprecation policy is adopted for specific symbols.

### Upgrade Checklist

1. Run contract tests before and after upgrades.
2. Verify consumer imports use `from gui_do import ...` root imports.
3. Validate action/input/focus behavior in active scenes.
4. Validate workspace restore reports for skipped or missing settings.
5. Compare telemetry baselines between old and upgraded versions.

[Back to Table of Contents](#table-of-contents)

## FAQ and Troubleshooting
[Back to Table of Contents](#table-of-contents)

### Q: Should I build apps directly with controls or with features?

Use features as the architectural unit. Controls are implementation details inside feature boundaries. Features provide lifecycle orchestration, runtime dependency contracts, and cleanup patterns that controls do not provide by themselves.

### Q: When should I use `RoutedFeature` over `Feature`?

Use `RoutedFeature` when you need declarative runtime wiring for action-driven interactions, shortcut overlays, and route-like feature coordination. Use plain `Feature` when lifecycle hooks and control-tree composition are sufficient.

### Q: Why are some key handlers not firing?

Check focus ownership first, then scene/window action scope, then modal overlay capture behavior. The most common cause is scope mismatch: action registered in one scene/window while current focus lives elsewhere.

### Q: Why do toast clicks not pass through?

By contract, toast bounds consume click events to prevent accidental activation of controls beneath transient surfaces. Use toast callbacks for intentional interactions.

### Q: How do I avoid breaking workspace restore across versions?

Adopt versioned snapshots and explicit migration steps, then inspect restore report fields (`skipped_settings`, `missing_settings_blocks`) during load to provide graceful fallbacks.

### Q: How do I confirm my API usage is supported?

Use explicit root imports and validate against export/contract tests. Avoid importing framework internals directly from submodule paths in consumer applications.

### Q: Why does `bind_runtime` seem out of order?

The runtime contract is that all features complete `build` before any feature runs `bind_runtime` for the scene. If behavior appears otherwise, verify scene assignments and test assumptions in feature registration.

### Q: How do I add a shortcut without touching every event handler?

Declare an `ActionSpec` and hotkey/routed runtime configuration. Let action registration and input mapping route the key to behavior instead of manually branching in event handlers.

[Back to Table of Contents](#table-of-contents)

## Appendix
[Back to Table of Contents](#table-of-contents)

### Appendix A: Glossary

Feature: lifecycle-managed unit of behavior (`DirectFeature`, `Feature`, `LogicFeature`, `RoutedFeature`) that owns structure, routing hooks, and teardown.

Spec: declarative data object that describes runtime wiring (scenes, features, actions, windows, accessibility, etc.).

Host: plain Python object passed to bootstrap and populated with runtime members.

Scene: top-level interaction context; features belong to scene scopes.

Window presentation: visibility/focus/task-panel model for windowed surfaces.

Routed runtime: declarative bundle of runtime bindings for a routed feature.

Observable: reactive value/collection that notifies subscribers on change.

Workspace state: persisted session model for restore of scene, feature state, and settings.

Contract test: automated test that asserts framework-level behavior guarantees.

Tier: public API grouping by abstraction level and recommended usage priority.

### Appendix B: Lifecycle/Event Sequence

1. `bootstrap_host_application` builds runtime from config.
2. Scene features run `build(host)`.
3. Scene features run `bind_runtime(host)`.
4. Frame loop begins.
5. Input is normalized to `GuiEvent`.
6. Overlay/focus/window/scene routing runs.
7. Feature `handle_event` executes by route policy.
8. Feature `on_update` and scheduler work execute.
9. Feature/control drawing executes.
10. Scene transition triggers departing shutdown and arriving build/bind.
11. Exit triggers shutdown and optional workspace save.

### Appendix C: System Dependency Map

Bootstrap systems (Tier 1) are the root composition layer and depend on spec definitions, lifecycle orchestration, and presentation/runtime services from lower tiers. Feature systems consume controls, observables, and routing systems to realize behavior. Layout/focus systems rely on control-tree shape and visibility state, while overlays depend on routing/focus ordering to enforce modal semantics. Persistence systems depend on state models and scene/window registries for restore coherence. Scheduling systems depend on update loop contracts and scene scope, and telemetry/introspection cross-cut nearly every runtime path. Audio integration is event-driven through the sound bus. Service scopes can be used at any tier for dependency management without forcing direct coupling.

### Appendix D: API Quick Index by Topic

Bootstrap and Specs: `Feature`, `DirectFeature`, `LogicFeature`, `RoutedFeature`, `FeatureMessage`, `FeatureManager`, `ScenePresentationModel`, `SceneSetupSpec`, `FeatureSpec`, `WindowSpec`, `RuntimeSceneSpec`, `ActionSpec`, `StaticAccessibilitySpec`, `CursorSpec`, `SceneRootSpec`, `AnchoredWindowSpec`, `LogicBindingSpec`, `TaskPanelButtonSpec`, `TaskPanelWindowToggleGroupSpec`, `SceneCommandPaletteSpec`, `ActionHotkeySpec`, `ControlKeyBindingSpec`, `SceneTaskPanelSpec`, `TaskPanelLinearLayoutSpec`, `TaskPanelSceneNavButtonSpec`, `EventSubscriptionSpec`, `ShortcutOverlaySpec`, `TaskPanelFocusToggleSpec`, `RoutedRuntimeSpec`, `RoutedFeatureLifecycleSpec`, `FeatureWindowBundleBindingSpec`, `WindowToggleBindingSpec`, `SceneSetupBindingSpec`, `RuntimeSceneBindingSpec`, `SceneRootBindingSpec`, `CursorBindingSpec`, `FontRoleBindingSpec`, `ActionBindingSpec`, `PaletteBindingSpec`, `SceneBundleBindingSpec`, `HostApplicationBindingSpec`, `TabbedPresenterSpec`, `AccessibilitySequenceSpec`, `TabBuilderSpec`, `NotificationSpec`, `HostApplicationConfig`, `TelemetryConfig`, `bootstrap_host_application`, `build_notification_center`, `build_feature_specs`, `build_feature_window_bundle_specs`, `build_window_toggle_specs`, `build_scene_setup_specs`, `build_runtime_scene_specs`, `build_scene_root_specs`, `build_cursor_specs`, `build_font_role_specs`, `build_scene_nav_actions`, `build_action_specs`, `build_scene_bundle_specs`, `build_static_accessibility_specs`, `build_host_application_config`.

Application and Scene Core: `GuiApplication`, `create_display`, `SceneTransitionManager`, `SceneTransitionStyle`, `apply_scene_setup_specs`.

State and Reactive Data: `ObservableValue`, `PresentationModel`, `ComputedValue`, `InvalidationTracker`, `ChangeKind`, `CollectionChange`, `ObservableList`, `ObservableDict`, `CollectionViewQuery`, `CollectionView`, `Binding`, `BindingGroup`, `ObservableStream`, `SelectionModel`, `SelectionMode`, `AppStateStore`, `StateSelector`, `StateTransaction`.

Events, Actions, Focus: `EventPhase`, `EventType`, `GuiEvent`, `ValueChangeCallback`, `ValueChangeReason`, `EventManager`, `EventBus`, `GestureRecognizer`, `EventRecorder`, `EventPlayback`, `RecordedEvent`, `InputSnapshot`, `Signal`, `SignalConnection`, `ActionManager`, `ActionContext`, `ActionMiddleware`, `ActionDescriptor`, `ActionRegistry`, `InputMap`, `InputBinding`, `KeyChordManager`, `KeyChord`, `ChordStep`, `FocusManager`, `FocusScope`, `FocusScopeManager`, `WindowFocusManager`, `FocusRing`, `InteractionPhase`, `InteractionContext`, `InteractionTransition`, `InteractionStateMachine`.

Scheduling and Pipelines: `TaskEvent`, `TaskScheduler`, `Timers`, `TweenManager`, `TweenHandle`, `Easing`, `AnimationSequence`, `AnimationHandle`, `TransitionManager`, `TransitionSpec`, `TransitionEvent`, `AnimationStateMachine`, `AnimationTransitionMode`, `SceneTimeline`, `Debouncer`, `Throttler`, `CooperativeScheduler`, `CoroutineHandle`, `Pause`, `Sleep`, `WaitForEvent`, `WaitForSignal`, `WaitUntil`, `WaitForAll`, `CancellationToken`, `PipelineStage`, `DataflowPipeline`, `PipelineHandle`.

Theme and Styling: `FontManager`, `FontRoleRegistry`, `ColorTheme`, `ThemeManager`, `DesignTokens`, `ScopedTheme`, `ScopedThemeManager`, `ThemeInvalidationBus`.

Layout and Virtualization: `LayoutAxis`, `LayoutManager`, `WindowTilingManager`, `ConstraintLayout`, `AnchorConstraint`, `DockPane`, `DockTabs`, `DockSplit`, `DockWorkspace`, `FlexLayout`, `FlexItem`, `FlexDirection`, `FlexAlign`, `FlexJustify`, `GridLayout`, `GridTrack`, `GridPlacement`, `CellCaretLayout`, `CellCaretState`, `LayoutAnimator`, `LayoutPass`, `MeasureContext`, `ArrangeContext`, `LayoutRoot`, `ResponsiveLayout`, `Breakpoint`, `SnapGrid`, `AlignmentGuide`, `SnapComposer`, `SnapTarget`, `FlowLayout`, `FlowItem`, `Viewport`, `ConstraintAttr`, `LayoutConstraint`, `ConstraintSet`, `ConstraintLayoutEngine`, `AdaptivePolicy`, `resolve_adaptive_policy`, `MeasureMode`, `MeasurePolicy`, `VirtualizedWindow`, `RecyclePool`, `VirtualizationCore`.

Overlays and Surface Managers: `OverlayManager`, `OverlayHandle`, `Alignment`, `PlacementResult`, `PopupPlacement`, `Side`, `compute_popup_rect`, `DialogManager`, `DialogHandle`, `ToastManager`, `ToastHandle`, `ToastSeverity`, `ContextMenuManager`, `ContextMenuItem`, `ContextMenuHandle`, `CommandPaletteManager`, `CommandEntry`, `CommandPaletteHandle`, `TooltipManager`, `TooltipHandle`, `MenuBarManager`, `FileDialogManager`, `FileDialogOptions`, `FileDialogHandle`, `NotificationCenter`, `NotificationRecord`, `ResizeManager`, `CursorManager`, `CursorHandle`, `CursorShape`, `DragDropManager`, `DragPayload`, `ClipboardManager`, `TransferData`, `TransferManager`, `ShortcutHelpOverlay`, `ShortcutSection`, `ShortcutEntry`.

Forms, Text, and Validation: `FormModel`, `FormField`, `ValidationRule`, `FieldError`, `FormSchema`, `SchemaField`, `DocumentModel`, `WizardFlow`, `WizardStep`, `WizardHandle`, `ValidationResult`, `Validator`, `RequiredValidator`, `RangeValidator`, `LengthValidator`, `PatternValidator`, `CustomValidator`, `DependentValidator`, `ValidationPipeline`, `TextFormatter`, `NumericFormatter`, `PatternFormatter`, `FixedPatternFormatter`, `TextFlow`, `TextSpan`, `TextSearcher`, `TextMatch`, `StringTable`, `LocaleRegistry`, `AsyncFieldValidator`, `AsyncFormValidator`, `FieldSchema`, `FieldGraphSchema`, `ValidationPolicy`, `SchemaFormRuntime`.

Controls and Presenters: `PanelControl`, `LabelControl`, `ButtonControl`, `ToggleControl`, `SliderControl`, `ScrollbarControl`, `CanvasControl`, `CanvasEventPacket`, `CanvasViewport`, `FrameControl`, `ImageControl`, `ArrowBoxControl`, `ButtonGroupControl`, `TabControl`, `TabItem`, `DockWorkspacePanel`, `TextInputControl`, `TextAreaControl`, `RichLabelControl`, `DropdownControl`, `DropdownOption`, `ListViewControl`, `ListItem`, `OverlayPanelControl`, `DataGridControl`, `GridColumn`, `GridRow`, `TreeControl`, `TreeNode`, `SplitterControl`, `SpinnerControl`, `RangeSliderControl`, `ColorPickerControl`, `ScrollViewControl`, `ProgressBarControl`, `AnimatedImageControl`, `ErrorBoundary`, `WindowControl`, `TaskPanelControl`, `WindowPresenter`, `MenuBarControl`, `MenuEntry`, `SceneMenuStripControl`, `NotificationPanelControl`, `PropertyInspectorPanel`, `ToolbarControl`, `ToolbarItem`, `StatusBarControl`, `StatusSlot`, `ExpanderControl`, `DatePickerControl`, `TimePickerControl`, `BreadcrumbControl`, `BreadcrumbItem`, `SplitButtonControl`, `SplitButtonOption`, `ChipInputControl`.

Data, Graphics, Introspection, and Advanced Runtime: `VirtualItemSource`, `FixedItemSource`, `SortFilterProxySource`, `AsyncDataProvider`, `LoadState`, `LoadStateKind`, `ObjectPool`, `DataCache`, `CacheStats`, `ListDiffCalculator`, `ListDiff`, `DiffInsert`, `DiffRemove`, `DiffMove`, `BuiltInGraphicsFactory`, `DirtyRegionTracker`, `DrawContext`, `DrawPhase`, `AssetRegistry`, `DebugOverlay`, `SurfaceCompositor`, `Layer`, `ShapeRenderer`, `SurfaceEffects`, `VectorPath`, `SpriteSheet`, `FrameAnimation`, `ParticleSystem`, `Emitter`, `ParticleLayer`, `TileSet`, `TileMap`, `SceneSpatialIndex`, `ui_property`, `PropertyDescriptor`, `PropertyRegistry`, `property_registry`, `PropertyInspectorModel`, `InspectedProperty`, `FrameTimer`, `TabPanelManager`, `WindowRelativeRect`, `resolve_scene_selection_callback`, `minimize_window_menu_entries`, `set_window_visible_state`, `toggle_window_visibility`, `create_anchored_feature_window`, `add_window_scene_menu_strip`, `inset_rect`, `centered_horizontal_strip_layout`, `split_slot_bounds`, `partition_rects`, `place_control`, `place_control_unlabeled`, `register_placed_control`, `add_group_label`, `PlacedControl`, `make_labeled_slot_height_fn`, `ControlRegistry`, `build_tools_menu_entries`, `add_standard_scene_menu_strip`, `apply_accessibility_sequence`, `apply_accessibility_sequence_from_attrs`, `register_companion_logic_features`, `ensure_scene_scheduler`, `sorted_window_bindings`, `collect_window_toggle_controls`, `apply_window_toggle_accessibility`, `add_window_toggle_task_panel_controls`, `add_task_panel_window_toggle_group`, `setup_scene_command_palette_key`, `register_window_toggle_tooltips`, `initialize_locale_registry`, `bind_input_map_actions`, `register_descriptors`, `resolve_canvas_local_point`, `apply_runtime_scene_pristine_assets`, `bind_runtime_scene_exit_keys`, `prewarm_runtime_scenes`, `add_task_panel_button`, `add_task_panel_buttons`, `register_tooltip_specs`, `register_action_hotkeys`, `draw_controls_prewarm`, `ensure_scene_task_panel`, `create_task_panel_linear_layout`, `add_task_panel_scene_nav_button`, `add_scene_task_panel_items`, `centered_overlay_rect`, `create_shortcut_help_overlay`, `bind_feature_event_subscription`, `unbind_feature_event_subscription`, `setup_routed_runtime`, `shutdown_routed_runtime`, `bind_task_panel_focus_toggle`, `add_window_control`, `add_window_label`, `add_window_button`, `add_window_button_row`, `instantiate_features_from_specs`, `register_features_from_specs`, `register_window_presentation_specs`, `register_window_tab_builders`, `build_tab_builder_specs`, `create_tab_control_from_specs`, `compute_tabbed_window_layout`, `setup_feature_presenter_tabs_from_window_content`, `register_window_tab_builder_specs`, `setup_feature_presenter_tabs`, `register_tab_update_handlers`, `create_presented_anchored_window`, `create_presented_window_from_spec`, `create_feature_presented_window`, `bind_feature_logic_aliases`, `setup_routed_feature_runtime`, `register_routed_feature_companions`, `bind_routed_feature_lifecycle`, `shutdown_routed_feature_lifecycle`, `ActiveTabUpdateRouter`, `TabLayoutContext`, `declare_host_actions`, `build_host_main_tab_order`, `apply_host_main_accessibility`, `UiEngine`, `ServiceKey`, `ServiceScope`, `ScopeStack`, `SchemaVersion`, `VersionedSnapshot`, `MigrationStep`, `MigrationRegistry`, `SnapshotMigrator`, `MigrationError`, `make_snapshot`, `read_version`.

### Appendix D.1: Tier-to-System Reference Matrix

| Tier | System | Representative key types |
|---|---|---|
| 1 | Primary entry points and data-driven APIs | `HostApplicationConfig`, `bootstrap_host_application`, `FeatureSpec`, `RoutedRuntimeSpec`, `ActionSpec` |
| 2 | Core application and scene management | `GuiApplication`, `create_display`, `SceneTransitionManager` |
| 3 | Essential data and state management | `ObservableValue`, `ComputedValue`, `ObservableList`, `CollectionView` |
| 4 | Events, actions, focus, input | `GuiEvent`, `EventType`, `ActionRegistry`, `InputMap`, `FocusManager` |
| 5 | Scheduling and animation | `TaskScheduler`, `TweenManager`, `TransitionManager`, `CooperativeScheduler` |
| 6 | Theme and font management | `ThemeManager`, `DesignTokens`, `FontRoleRegistry` |
| 7 | Telemetry and diagnostics | `TelemetryCollector`, `configure_telemetry`, `render_telemetry_report` |
| 8 | Layout and spatial | `FlexLayout`, `GridLayout`, `ConstraintLayout`, `Viewport` |
| 9 | Overlay managers and windows | `OverlayManager`, `DialogManager`, `ToastManager`, `CommandPaletteManager` |
| 10 | Forms and data binding | `FormModel`, `FormSchema`, `ValidationPipeline`, `WizardFlow` |
| 11 | State and persistence | `CommandHistory`, `WorkspacePersistenceManager`, `SettingsRegistry` |
| 12 | Primary controls | `PanelControl`, `LabelControl`, `ButtonControl`, `CanvasControl` |
| 13 | Extended controls | `TextInputControl`, `DataGridControl`, `WindowControl`, `WindowPresenter` |
| 14 | Text and localization | `TextFormatter`, `TextFlow`, `TextSearcher`, `LocaleRegistry` |
| 15 | Data and collections | `AsyncDataProvider`, `DataCache`, `ListDiffCalculator` |
| 16 | Graphics and rendering | `DrawContext`, `DirtyRegionTracker`, `SurfaceCompositor`, `ParticleSystem` |
| 17 | Introspection and inspection | `SceneSpatialIndex`, `PropertyRegistry`, `PropertyInspectorModel` |
| 18 | Advanced runtime and bootstrapping | `set_window_visible_state`, `create_feature_presented_window`, `bind_routed_feature_lifecycle` |
| 19 | Infrastructure internals | `UiEngine` |
| 20 | Audio | `SoundCue`, `SoundBankRegistry`, `SoundEventBus` |
| 21 | Accessibility | `AccessibilityRole`, `AccessibilityTree`, `AccessibilityBus` |
| 22 | Theme invalidation | `ThemeInvalidationBus` |
| 23 | Undo context routing | `UndoContextManager` |
| 24 | Async form validation | `AsyncFieldValidator`, `AsyncFormValidator` |
| 25 | Scoped service graph | `ServiceKey`, `ServiceScope`, `ScopeStack` |
| 26 | Cancelable dataflow pipeline | `CancellationToken`, `PipelineStage`, `DataflowPipeline` |
| 27 | Transactional app state store | `AppStateStore`, `StateSelector`, `StateTransaction` |
| 28 | Adaptive constraint layout v2 | `ConstraintLayoutEngine`, `ConstraintSet`, `AdaptivePolicy` |
| 29 | Unified virtualization core | `VirtualizationCore`, `VirtualizedWindow`, `RecyclePool` |
| 30 | Interaction state machine framework | `InteractionStateMachine`, `InteractionPhase`, `InteractionTransition` |
| 31 | Schema-driven form runtime | `SchemaFormRuntime`, `FieldGraphSchema`, `ValidationPolicy` |
| 32 | Portable snapshot and migration layer | `SnapshotMigrator`, `MigrationRegistry`, `VersionedSnapshot` |

### Appendix D.2: Public API Selection Heuristics

1. Start at Tier 1 APIs (`HostApplicationConfig`, bootstrap, feature/spec types).
2. Descend one tier at a time only when lower-level control is required.
3. Use Tier 18 helpers for supported advanced bootstrap extension paths.
4. Keep consumer imports on root package exports.
5. Avoid Tier 19 internals in consumer code.

Decision shortcuts:
- Need app setup: use `HostApplicationConfig` + `bootstrap_host_application`.
- Need cross-feature routing: use routed lifecycle specs and helpers.
- Need large datasets: use virtualization/dataflow APIs before custom loops.
- Need durable session restore: use workspace persistence plus snapshot migration.
- Need shortcut discoverability: use `ShortcutOverlaySpec` via routed runtime.

### Appendix E: Architecture Templates

Template 1: Small single-scene app
- 1 scene, 2-4 features
- Observable state and minimal action specs
- no task-panel or window presenter required

Template 2: Multi-window workbench
- multiple scenes and per-window presenters
- task-panel toggles and scene menu strip
- routed runtime specs for shortcuts and focus toggles

Template 3: Data-heavy analysis tool
- async providers + sort/filter proxy + virtualization
- cancelable dataflow pipeline and cache strategy
- telemetry enabled for interaction baselines

Template 4: Long-running workflow app
- cooperative scheduler workflows for staged operations
- progress observables bound to UI
- versioned snapshot migration for durable sessions

[Back to Table of Contents](#table-of-contents)
