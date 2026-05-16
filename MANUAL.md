# gui_do Manual

gui_do is a declarative, lifecycle-driven GUI framework that separates application structure from runtime behavior so teams can build complex, scene-based interfaces with deterministic routing, reactive state, and predictable teardown. This manual is the single, code-aligned reference for understanding the framework from theory through production patterns, using the public root API as the only supported consumer surface.

## Table of Contents

1. [Title and Purpose](#gui_do-manual)
2. [Table of Contents](#table-of-contents)
3. [How to Use This Manual](#how-to-use-this-manual)
   - [Reading Paths](#reading-paths)
   - [Tri-Lens Markers](#tri-lens-markers)
   - [Contract Alignment](#contract-alignment)
   - [Known Non-Goals](#known-non-goals)
4. [Conceptual Foundations (Theory)](#conceptual-foundations-theory)
5. [Quickstart Path (Practice)](#quickstart-path-practice)
6. [Architecture and Runtime Model](#architecture-and-runtime-model)
7. [Core Workflow: Build, Bind, Route, Update, Draw](#core-workflow-build-bind-route-update-draw)
8. [Main Systems Reference](#main-systems-reference)
   - [8.1 Application Bootstrap and Host Configuration](#application-bootstrap-and-host-configuration)
   - [8.2 Feature Lifecycle and Feature Types](#feature-lifecycle-and-feature-types)
   - [8.3 Events, Actions, Input Mapping, and Routing](#events-actions-input-mapping-and-routing)
   - [8.4 State and Observables](#state-and-observables)
   - [8.5 Controls and Control Composition](#controls-and-control-composition)
   - [8.6 Layout Systems](#layout-systems)
   - [8.7 Focus and Accessibility](#focus-and-accessibility)
   - [8.8 Overlays, Dialogs, Notifications, and Command Surfaces](#overlays-dialogs-notifications-and-command-surfaces)
   - [8.9 Scene, Window, and Task-Panel Presentation Models](#scene-window-and-task-panel-presentation-models)
   - [8.10 Scheduling, Timing, Animation, and Transitions](#scheduling-timing-animation-and-transitions)
   - [8.11 Persistence and Workspace/Session State](#persistence-and-workspacesession-state)
   - [8.12 Theme, Styling, and Visual Systems](#theme-styling-and-visual-systems)
   - [8.13 Text, Input, Forms, and Validation Systems](#text-input-forms-and-validation-systems)
   - [8.14 Data and Dataflow Helpers](#data-and-dataflow-helpers)
   - [8.15 Graphics and Audio Integration Points](#graphics-and-audio-integration-points)
   - [8.16 Telemetry, Introspection, and Operational Hooks](#telemetry-introspection-and-operational-hooks)
9. [Integration Patterns and Composition Recipes](#integration-patterns-and-composition-recipes)
10. [End-to-End Reference Application](#end-to-end-reference-application)
11. [Testing, Diagnostics, and Reliability](#testing-diagnostics-and-reliability)
12. [Performance and Scaling Guidance](#performance-and-scaling-guidance)
13. [Migration, Versioning, and Deprecation Notes](#migration-versioning-and-deprecation-notes)
14. [FAQ and Troubleshooting](#faq-and-troubleshooting)
15. [Appendix](#appendix)
   - [Appendix A: Glossary](#appendix-a-glossary)
   - [Appendix B: Lifecycle/Event Sequence](#appendix-b-lifecycleevent-sequence)
   - [Appendix C: System Dependency Map](#appendix-c-system-dependency-map)
   - [Appendix D: API Quick Index](#appendix-d-api-quick-index)
   - [Appendix D.1: Tier Matrix](#appendix-d1-tier-matrix)
   - [Appendix D.2: Selection Heuristics](#appendix-d2-selection-heuristics)
   - [Appendix E: Architecture Templates](#appendix-e-architecture-templates)
   - [Appendix F: Specifications and Option Reference](#appendix-f-specifications-and-option-reference)

## How to Use This Manual

[Back to Table of Contents](#table-of-contents)

This manual is written to support three concrete modes of use: learning, building, and maintaining. In learning mode, start with theory and architecture so the terms used in later sections already have a clear mental model; this avoids cargo-cult usage of APIs without understanding lifecycle ownership and routing boundaries. In building mode, move quickly through the quickstart and core workflow sections, then jump to the relevant systems chapters for implementation details and anti-pattern checks. In maintaining mode, use the testing, migration, and appendix sections as your operational checklist, especially when exports or contracts have changed.

The manual intentionally keeps the top-level section order stable across regenerations so links and team references stay durable. Each systems chapter includes what/why guidance, lifecycle placement, concrete API references, a minimal usage pattern, an advanced composition pattern, and explicit anti-pattern notes. This is deliberate: gui_do behavior is easiest to apply correctly when conceptual intent and runtime lifecycle details are read together.

### Reading Paths

[Back to Table of Contents](#table-of-contents)

Beginner path: read Section 4, then Sections 5 through 7, then systems 8.1, 8.2, 8.3, and 8.4 before touching broader feature sets. This path minimizes accidental misuse of lower-level helpers before mastering the declarative bootstrap and feature lifecycle.

Intermediate path: skim Section 4, then read Sections 6 and 7 in full, followed by systems chapters mapped to your current work (for example, 8.5 and 8.6 for control-heavy interfaces, or 8.11 and 8.12 for persistence/theme-heavy apps).

Maintainer path: read Sections 11 through 15 first, then return to any systems chapter impacted by current export or contract changes. Use Appendix D and D.1 to validate coverage against root exports.

### Tri-Lens Markers

[Back to Table of Contents](#table-of-contents)

Use a three-lens reading method while implementing:

- Theory lens: why the abstraction exists and which constraints it solves.
- Practice lens: what declaration or lifecycle method to use in real code.
- Contract lens: which documented guarantees and tests enforce behavior.

If implementation choices are unclear, prefer the path that keeps you in the highest stable abstraction tier and preserves lifecycle-owned cleanup guarantees.

### Contract Alignment

[Back to Table of Contents](#table-of-contents)

Normative behavior is defined by current source code and contract docs, with this precedence: package behavior, tests, docs contracts, demo usage. When prose in this manual could be interpreted multiple ways, treat runtime contracts and boundary contracts as authoritative. In practice, this means routing, scheduler budget behavior, workspace restore reporting, and import boundaries should always be validated against docs and tests during maintenance updates.

### Known Non-Goals

[Back to Table of Contents](#table-of-contents)

- This manual does not treat internal infrastructure tiers as beginner entry points.
- This manual does not define star-import compatibility as a public API contract.
- gui_do is not designed to provide OS-native widget parity for every platform surface.
- gui_do does not replace application domain architecture decisions outside UI/runtime concerns.

## Conceptual Foundations (Theory)

[Back to Table of Contents](#table-of-contents)

gui_do is built around an explicit split between control-plane declarations and runtime-plane execution. You describe scenes, features, windows, actions, accessibility metadata, runtime hooks, and lifecycle wiring with specs such as `HostApplicationBindingSpec`, `FeatureSpec`, `RuntimeSceneSpec`, `ActionSpec`, `WindowSpec`, and `RoutedRuntimeSpec`; then the runtime materializes that declaration into a live `GuiApplication`. This design is not cosmetic. It is what keeps large interfaces maintainable as teams add features, move files, or refactor internal modules while preserving predictable startup behavior.

### Data-Driven Design

The core data-driven contract is: structure is declared, behavior is executed. In gui_do, structure means your host config graph and its child specs; behavior means feature methods (`build`, `bind_runtime`, `handle_event`, `on_update`, `draw`, and teardown). This gives you a stable startup pipeline because the runtime can validate declarations before frame processing begins.

The standard bootstrap path is two-phase: build configuration, then bootstrap execution. In practical terms, you either construct `HostApplicationConfig` directly or generate it from `build_host_application_config(HostApplicationBindingSpec(...))`. The builder pass resolves related declarations (for scenes, window bundles, actions, roots, accessibility, and palette bindings) into one deterministic object. `bootstrap_host_application` then binds that object to your host and wires runtime managers in a single pass.

This differs materially from imperative UI wiring. In an imperative design, adding one command shortcut often means touching event dispatch logic, registering callbacks in multiple places, and writing custom teardown code. In gui_do, you usually add one declaration (for example, an `ActionSpec` plus `ActionHotkeySpec` or routed lifecycle spec), and the runtime performs registration and lifecycle-owned disposal automatically.

A major consequence is safe internal reorganization. If a feature package is split into `*_feature.py`, `*_presenter.py`, and `*_logic_feature.py`, bootstrap does not change as long as package-root exports from `__init__.py` remain stable. Consumer setup references public classes and spec values, not internal file paths. This is the same reason the boundary contract can be strict: applications consume root exports from `gui_do`, and framework internals can evolve behind that surface.

Data-driven declarations are also highly testable. The config graph can be created and inspected without opening a display loop. Feature instances can be tested with mock host attributes. Builder output can be asserted for scene and action shape. That testability is hard to achieve in imperative startup code where side effects are scattered across callbacks.

Specs also work as an extensible serialization boundary. Named fields in classes like `SceneBundleBindingSpec`, `PaletteBindingSpec`, `FeatureWindowBundleBindingSpec`, `ShortcutOverlaySpec`, and `FailurePolicySpec` are self-documenting and additive over time. Adding a new optional field generally does not break existing call sites, unlike positional or ad hoc wiring APIs.

The boundary of declarative design is intentional: runtime behavior still lives in imperative feature logic. You declare the graph declaratively, then implement domain behavior in Python methods. In short: describe topology with specs, express behavior in lifecycle methods.

[Back to Table of Contents](#table-of-contents)

### Reactive Data and Observable State

Reactive state in gui_do means publishers do not need to know consumers. `ObservableValue`, `ObservableList`, `ObservableDict`, and `ObservableStream` emit changes to subscribers, and controls or companion features react without direct coupling to the producer. This is the default way to keep UI state consistent across multiple feature boundaries.

`ObservableValue` represents scalar state, while `ObservableList` and `ObservableDict` carry collection mutations with explicit change metadata (`CollectionChange`, `ChangeKind`). This lets views update incrementally instead of re-rendering from scratch. `CollectionView` and `CollectionViewQuery` then layer selection, filtering, and projection behavior over those observables.

Batching is a first-class concern because many UI mutations are multi-step. `reactive_batch` and `is_batching` allow you to group several state mutations and emit one coherent notification wave when the context exits. This avoids update storms and reduces redundant control invalidation.

Derived state can be built manually by subscribing and writing to downstream values, but `ComputedValue` offers a higher-level primitive for computed projections. Manual wiring is still useful when you need side effects; `ComputedValue` is usually cleaner when you need pure recalculation from source values.

Subscription lifecycle matters as much as subscription correctness. Register subscriptions when runtime wiring is complete (usually `bind_runtime`), and dispose them in teardown (`shutdown_runtime` or routed lifecycle shutdown). Subscribing in `build` can fire callbacks before peer controls exist. Forgetting disposal causes leaks and callbacks into dead features.

Controls are designed to consume reactive values naturally. Instead of mutating labels, counters, and rows from every code path, features write to observables and let bindings propagate. This keeps presentation replacement cheap: one control can be swapped for another while the state contract remains unchanged.

Cross-feature coordination should prefer observable ownership over direct references. A logic feature can own a value, publish updates, and remain unaware of subscribers. Consumers bind in `bind_runtime` when sibling features are guaranteed to exist.

Common anti-patterns are predictable: polling values in `on_update`, subscribing too early, keeping mutable plain dict/list state across features, and never disposing. Each one weakens determinism and increases lifecycle bugs under scene transitions.

[Back to Table of Contents](#table-of-contents)

### Feature Composition and Lifecycles

Features are gui_do's operational unit. `Feature`, `DirectFeature`, `LogicFeature`, and `RoutedFeature` package state, rendering, event handling, and teardown around clearly defined phases. This phase model is what enables deterministic startup and safe scene transitions.

Use `DirectFeature` when you need low-overhead direct drawing and little or no control-tree participation. Use `Feature` for standard interactive UI hosted in scene controls. Use `LogicFeature` for non-visual orchestration, derived state, and shared domain behavior. Use `RoutedFeature` when you need declarative action wiring, route-target coordination, and lifecycle-managed runtime facilities.

Lifecycle phases are strict by design. `build` creates static structure and controls. `bind_runtime` wires host-dependent resources once all scene features are built. `handle_event` processes routed `GuiEvent` values and may consume propagation. `on_update` performs frame work under budget constraints. `draw` handles custom rendering paths. Runtime resource disposal belongs in `shutdown_runtime` (and routed lifecycle shutdown helpers).

`HOST_REQUIREMENTS` provides explicit dependency declarations per phase, replacing informal constructor injection with machine-checkable host contracts. A feature can state the attributes it requires for each lifecycle method, and bootstrap/runtime setup validates those requirements before method dispatch.

Feature-to-feature communication is intentionally loose. `FeatureMessage` and shared reactive state avoid hard references between peers. Scene transitions remain safe because features are activated and deactivated by scene membership, so stale features are not accidentally updated after transition.

The recommended package convention follows demo features: one package folder per feature, one public `__init__.py` import surface, and focused internal modules by concern. This keeps bootstrap code stable and allows deep refactors without consumer breakage.

Routed runtime composition is an important extension of lifecycle hygiene. `RoutedFeatureLifecycleSpec` + `RoutedRuntimeSpec` let features declare action hotkeys, service publication/consumption (`ServiceBindingSpec`, `ServiceConsumerSpec`), reactive bindings (`StoreSubscriptionSpec`, `StoreSelectorSpec`, `ObservableEffectSpec`, `SignalEffectSpec`), and operation policies (`FeatureOperationSpec`, `FailurePolicySpec`) with runtime-scope ownership. The paired APIs `bind_routed_feature_lifecycle` and `shutdown_routed_feature_lifecycle` ensure setup and cleanup stay symmetric.

If teardown is partial, leaked handlers and stale callbacks are inevitable. A key anti-pattern is manual ad hoc teardown that forgets one routed resource. The lifecycle-safe model is to bind all routed resources into scope and unwind that scope fully at shutdown.

[Back to Table of Contents](#table-of-contents)

### Higher-Level Runtime Faculties and Composition

gui_do now includes higher-order runtime faculties that sit beside service/effect/operation specs as peer declarative facilities. They are not bolt-ons; they are architectural pillars for controlling admission, dependency safety, resilience, diagnostics, and runtime adaptation without collapsing back to bespoke imperative glue.

Dependency planning and startup guards are expressed via `FeatureDependencySpec`, letting runtime validation catch missing or incompatible dependencies before failures manifest as mid-frame errors. Policy admission and decisions are expressed with `RuntimePolicySpec`, `PolicyDecision`, and `RuntimePolicyEngine`, which formalize whether requested operations should proceed under current context.

Effect ownership is explicit through `EffectBindingSpec` and `EffectLifetimeOrchestrator`, preventing forgotten cleanup paths for event handlers, subscriptions, and side-effectful runtime hooks. Event stream transformation is modeled by `EventPipelineStageSpec`, `EventPipelineSpec`, and `EventPipelineRuntime` so routing pipelines can be declared, reasoned about, and torn down coherently.

Durability and recovery concerns are declared with `DurableOperationBindingSpec`, `DurableOperationQueueSpec`, `DurableQueueRecord`, and `DurableOperationQueueRuntime`. This makes retry and replay capabilities explicit rather than hidden inside feature methods.

Capability contracts use `CapabilityProviderSpec`, `CapabilityRequirementSpec`, and `CapabilityContractRuntime` to negotiate provider/consumer relationships declaratively. Projection pipelines use `ProjectionNodeSpec`, `ProjectionSpec`, and `ProjectionRuntime` to keep incremental derived views deterministic and lifecycle-owned.

Workflow and recompute orchestration are formalized by `WorkflowStepSpec`, `WorkflowSpec`, `WorkflowCoordinator`, `RecomputeNodeSpec`, and `RecomputeOrchestrator`. QoS and backpressure concerns are formalized with `QoSPolicySpec` and `QoSPolicyRuntime`, while degradation and health surfaces are modeled through `HealthProbeSpec` and `FeatureHealthRuntime`.

For diagnostics and controlled evolution, routed runtime also includes `ReplaySpec` with `RuntimeReplayHarness` and replace semantics via `ReplacePolicySpec` and `FeatureHotSwapManager`. Related operation resilience facilities include `FeatureOperationBus` and runtime scope ownership via `FeatureRuntimeScope`.

Lifecycle placement stays consistent: declaration in specs, setup in `bind_runtime` (or routed bind helpers), per-frame participation during update/routing paths, and complete unwind in `shutdown_runtime`. This is the main safeguard against leaks, partially detached pipelines, or cross-scene resource ghosts.

```python
from gui_do import (
   FeatureDependencySpec,
   RuntimePolicySpec,
   RoutedRuntimeSpec,
   RoutedFeatureLifecycleSpec,
   bind_routed_feature_lifecycle,
   shutdown_routed_feature_lifecycle,
)

class ExampleRoutedFeature:
   def __init__(self):
      self._runtime = RoutedRuntimeSpec(
         scene_name="main",
         dependencies=(FeatureDependencySpec(provider="service.cache", required=True),),
         runtime_policies=(RuntimePolicySpec(policy_id="allow_main_ops", default_decision="allow"),),
      )
      self._lifecycle = RoutedFeatureLifecycleSpec(runtime_spec=self._runtime)

   def bind_runtime(self, host):
      bind_routed_feature_lifecycle(self, host, self._lifecycle)

   def shutdown_runtime(self, host):
      shutdown_routed_feature_lifecycle(self, host, self._lifecycle)
```

[Back to Table of Contents](#table-of-contents)

## Quickstart Path (Practice)

[Back to Table of Contents](#table-of-contents)

The fastest path to a correct gui_do app is to keep your first implementation spec-driven and scene-local. Start with one scene, one visible feature, one observable state value, and one action. Expand only after lifecycle boundaries are behaving correctly.

Recommended six-milestone progression:

1. Milestone A: bootstrap to a single scene with no runtime errors.
2. Milestone B: one feature creates one visible control.
3. Milestone C: one `ObservableValue` updates one label reactively.
4. Milestone D: one `ActionSpec` and one key binding trigger expected behavior.
5. Milestone E: one overlay or toast routes without leaking input to underlying controls.
6. Milestone F: workspace save/load roundtrip succeeds and restore report is inspected.

```python
from gui_do import (
   Feature,
   FeatureSpec,
   HostApplicationConfig,
   RuntimeSceneSpec,
   LabelControl,
   PanelControl,
   ObservableValue,
   bootstrap_host_application,
)
from pygame import Rect


class HelloFeature(Feature):
   scene_name = "main"

   def __init__(self):
      self.message = ObservableValue("Ready")
      self._sub = None

   def build(self, host):
      self.root = host.app.add(PanelControl("root", Rect(10, 10, 320, 120)), scene_name="main")
      self.label = self.root.add(LabelControl("label", Rect(8, 8, 300, 24), "Ready"))

   def bind_runtime(self, host):
      self._sub = self.message.subscribe(lambda value: setattr(self.label, "text", value))
      self.message.value = "Booted"

   def shutdown_runtime(self, host):
      if self._sub is not None:
         self._sub.dispose()


class Host:
   pass


host = Host()
config = HostApplicationConfig(
   display_size=(1280, 720),
   window_title="Quickstart",
   initial_scene_name="main",
   feature_specs=(FeatureSpec("hello_feature", HelloFeature),),
   runtime_scene_specs=(RuntimeSceneSpec(scene_name="main", bind_escape_to_exit=True),),
)
bootstrap_host_application(host, config)
```

Beginner confidence checklist:

1. You can explain why `build` creates structure and `bind_runtime` wires dependencies.
2. You can add or remove a feature by editing only spec declarations.
3. You can trace one key press from normalized `GuiEvent` to action/handler execution.

Common early failure modes and fixes:

- Feature never appears: verify `FeatureSpec` registration and matching scene scope.
- Hotkey does nothing: verify action descriptor, input binding scope, and active scene/window.
- Overlay steals more input than expected: verify dismissal settings and unhandled-key policy.
- State changes but UI stays stale: subscribe in `bind_runtime` and avoid early disposal.

[Back to Table of Contents](#table-of-contents)

## Architecture and Runtime Model

[Back to Table of Contents](#table-of-contents)

### Boundary Model: Framework vs Consumer

The repository enforces a strict dependency boundary: framework/runtime code lives in `gui_do`, while integration and feature composition examples live in `demo_features` plus the consumer entrypoint. Framework code must not import demo features. Consumer entrypoints should import from root `gui_do` exports, not internal module paths.

This is not just style guidance. Boundary tests validate the rule and protect package portability. The result is a reusable framework package with a stable public surface and independently evolving demos.

### Tiered Public API Model

Public exports are grouped by tier in `gui_do.__init__`. Tier 1 is the preferred default for new application composition: specs, lifecycle abstractions, and bootstrap builders. Tiers 2 through 7 expose core runtime systems (application, events/actions, state, scheduling, theme, telemetry). Tiers 8 and above expose specialized systems (layout, overlays, controls, graphics, introspection, advanced runtime helpers, and additional runtime faculties).

A practical heuristic is to start from the lowest-numbered tier that solves your use case and move downward only when needed. This keeps app code aligned with stable abstractions and reduces direct dependency on low-level helpers.

### Runtime Guarantees

Contract docs and tests define non-negotiable guarantees:

1. Canonical `GuiEvent` normalization before app-level dispatch.
2. Scene-isolated update execution for scene-contained runtime systems.
3. Deterministic focus candidate ordering.
4. Scheduler dispatch budget clamping: fraction `0.12`, floor `0.5 ms`, ceiling `4.0 ms`.
5. Workspace restore skips missing settings keys rather than aborting restore.

### Event Pipeline

The practical event flow is: raw input enters the app loop, is normalized to `GuiEvent`, shared input state updates, overlay/focus routing executes, keyboard policies and bindings resolve, scene/feature handlers run, and propagation stops are respected (`propagation_stopped`, `default_prevented`). Stable ordering contracts make this traceable and testable.

### Known Non-Goals

- Full OS-native widget parity.
- Replacing domain/business architecture outside UI/runtime composition.
- Treating internal tiers as the default beginner API.
- Treating star-import behavior as compatibility contract.

[Back to Table of Contents](#table-of-contents)

## Core Workflow: Build, Bind, Route, Update, Draw

[Back to Table of Contents](#table-of-contents)

This workflow is the central programming model for gui_do applications. If teams keep each responsibility in its phase, runtime behavior stays deterministic and teardown-safe.

`build` constructs static control/tree structure and local state containers. It should avoid subscriptions and host-dependent side effects.

`bind_runtime` attaches runtime concerns: actions, hotkeys, service consumption/publication, store subscriptions, signal effects, operation handlers, and cross-feature reactive wiring. At this point siblings are built, so references are safe.

`route` is the combined event/action/message path. Use `FeatureMessage` for loose feature coordination and routed specs for declarative bindings.

`update` runs per-frame logic, scheduler dispatch, coroutine progress, and time-based transitions. Keep this lightweight and budget-aware.

`draw` is the custom render phase for visuals not represented by controls.

When routed specs are used, lifecycle pairing must be explicit:

```python
from gui_do import (
   RoutedRuntimeSpec,
   RoutedFeatureLifecycleSpec,
   ShortcutOverlaySpec,
   TaskPanelFocusToggleSpec,
   bind_routed_feature_lifecycle,
   shutdown_routed_feature_lifecycle,
)


class RoutedWorkbenchFeature:
   def __init__(self):
      runtime = RoutedRuntimeSpec(
         scene_name="main",
         shortcut_overlay=ShortcutOverlaySpec(toggle_action_name="show_help"),
         task_panel_focus_toggles=(
            TaskPanelFocusToggleSpec(
               toggle_action_name="toggle_tools_window",
               target_window_attr="tools_window",
            ),
         ),
      )
      self._lifecycle = RoutedFeatureLifecycleSpec(runtime_spec=runtime)

   def bind_runtime(self, host):
      bind_routed_feature_lifecycle(self, host, self._lifecycle)

   def shutdown_runtime(self, host):
      shutdown_routed_feature_lifecycle(self, host, self._lifecycle)
```

Use routed runtime specs when they reduce repetitive wiring:

- Multiple hotkeys/actions for one feature.
- Shortcut overlay registration tied to feature lifecycle.
- Task-panel focus toggles synced with window visibility.
- Event/store/signal subscriptions that must auto-clean up.
- Operation orchestration with `FeatureOperationSpec`, `FailurePolicySpec`, and `FeatureOperationBus`.
- Higher-level faculties such as dependency (`FeatureDependencySpec`), workflow (`WorkflowSpec`), recompute (`RecomputeNodeSpec`), QoS (`QoSPolicySpec`), health (`HealthProbeSpec`), replay (`ReplaySpec`), and hot-swap (`ReplacePolicySpec`).

Pairing setup with teardown is mandatory. If a feature calls bind helpers but omits shutdown helpers, routed resources survive scene exit and create stale callbacks, duplicated effects, and cross-scene leakage.

[Back to Table of Contents](#table-of-contents)

## Main Systems Reference

[Back to Table of Contents](#table-of-contents)

### Application Bootstrap and Host Configuration

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Bootstrap turns a declarative graph into a running application. `HostApplicationConfig` and `bootstrap_host_application` provide the stable top-level entrypoint, while `HostApplicationBindingSpec` and `build_host_application_config` provide a higher-level authoring path that composes scene bundles, feature/window bundles, actions, fonts, cursors, palette behavior, accessibility defaults, and telemetry in one deterministic build pass.

#### Mental model and lifecycle placement

Treat bootstrap as compile-then-run for GUI topology. The config build phase resolves declarations; the bootstrap phase attaches runtime objects to your host and initializes scenes, managers, and wiring. This is startup-time behavior and should not be recreated ad hoc inside feature methods.

#### Primary public APIs and key types

Core entry APIs: `HostApplicationConfig`, `HostApplicationBindingSpec`, `build_host_application_config`, `bootstrap_host_application`, `build_scene_bundle_specs`, `build_feature_specs`, `build_feature_window_bundle_specs`, `build_action_specs`, `build_runtime_scene_specs`, `build_static_accessibility_specs`, `build_notification_center`.

Supporting types commonly used at bootstrap: `FeatureSpec`, `WindowSpec`, `RuntimeSceneSpec`, `SceneSetupSpec`, `SceneBundleBindingSpec`, `FeatureWindowBundleBindingSpec`, `ActionBindingSpec`, `FontRoleBindingSpec`, `CursorBindingSpec`, `PaletteBindingSpec`, `TelemetryConfig`.

#### Typical usage flow

1. Create declarations for scenes, features, actions, and presentation bindings.
2. Build a `HostApplicationConfig` directly or via `build_host_application_config`.
3. Call `bootstrap_host_application(host, config)`.
4. Use `host.app.run_entrypoint(...)` and optional workspace save/load hooks.

#### Minimal example

```python
from gui_do import HostApplicationBindingSpec, build_host_application_config, bootstrap_host_application

class Host:
   pass

host = Host()
config = build_host_application_config(
   HostApplicationBindingSpec(display_size=(1280, 720), window_title="Bootstrap", initial_scene_name="main")
)
bootstrap_host_application(host, config)
```

#### Advanced pattern(s)

Use `SceneBundleBindingSpec` + `FeatureWindowBundleBindingSpec` to compose multi-scene workbench apps where scene navigation, window presentation, task panel integration, and command palette entries are generated from declarations rather than manually wired callbacks.

#### Common mistakes and anti-patterns

- Mutating host runtime members after bootstrap in ways that bypass declared specs.
- Declaring features for scenes that do not exist in scene setup/runtime specs.
- Forgetting `initial_scene_name`, then debugging routing with no active scene context.

#### Cross-links to related systems

See 8.2 for lifecycle semantics, 8.9 for scene/window presentation, and 8.11 for persistence lifecycle.

See [Appendix F: Specifications and Option Reference](#appendix-f-specifications-and-option-reference).

[Back to Table of Contents](#table-of-contents)

### Feature Lifecycle and Feature Types

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Features are the compositional runtime unit in gui_do. They isolate UI/control ownership, event handling, frame updates, and teardown. This keeps behavior modular and scenes switch-safe.

#### Mental model and lifecycle placement

`build` creates structure, `bind_runtime` wires runtime dependencies, `handle_event` reacts to routed events, `on_update` runs frame logic, `draw` handles custom rendering, and `shutdown_runtime` must unwind runtime resources. All subscriptions or routed registrations should be created in bind and cleaned in shutdown.

#### Primary public APIs and key types

Feature classes and lifecycle helpers: `Feature`, `DirectFeature`, `LogicFeature`, `RoutedFeature`, `FeatureMessage`, `FeatureManager`, `RoutedRuntimeSpec`, `RoutedFeatureLifecycleSpec`, `bind_routed_feature_lifecycle`, `shutdown_routed_feature_lifecycle`, `register_routed_feature_companions`, `FeatureRuntimeScope`, `FeatureOperationBus`.

#### Typical usage flow

1. Pick feature type based on role (`Feature` for UI, `LogicFeature` for non-visual coordination, `DirectFeature` for direct draw, `RoutedFeature` for routed runtime composition).
2. Implement lifecycle methods and `HOST_REQUIREMENTS`.
3. Register via `FeatureSpec`.
4. Bind observables, actions, and routed runtime resources in `bind_runtime`.
5. Dispose everything in `shutdown_runtime`.

#### Minimal example

```python
from gui_do import Feature, ObservableValue, LabelControl
from pygame import Rect

class CounterFeature(Feature):
   scene_name = "main"

   def __init__(self):
      self.count = ObservableValue(0)
      self._sub = None

   def build(self, host):
      self.label = host.app.add(LabelControl("counter", Rect(20, 20, 200, 24), "0"), scene_name="main")

   def bind_runtime(self, host):
      self._sub = self.count.subscribe(lambda value: setattr(self.label, "text", str(value)))

   def shutdown_runtime(self, host):
      if self._sub:
         self._sub.dispose()
```

#### Advanced pattern(s)

Logic/presentation split: a `LogicFeature` owns state and publishes `FeatureMessage` or observable updates; a `RoutedFeature` handles controls and routed action interactions. Companion registration enables clean feature boundaries.

#### Common mistakes and anti-patterns

- Subscribing in `build` before all peers and controls are ready.
- Mixing heavyweight draw logic into non-draw-focused feature types.
- Calling bind helpers without matching shutdown helpers, which leaks routed services/effects/operations.
- Partial teardown of runtime scope; always unwind full routed lifecycle ownership.

#### Cross-links to related systems

See 8.4 for observables, 8.10 for frame scheduling, and 8.9 for presented windows.

See [Appendix F: Specifications and Option Reference](#appendix-f-specifications-and-option-reference).

[Back to Table of Contents](#table-of-contents)

### Events, Actions, Input Mapping, and Routing

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

This system turns raw input into deterministic command dispatch. `GuiEvent` is the canonical application event object, and action/input systems (`ActionManager`, `ActionRegistry`, `InputMap`, `KeyChordManager`) map user input to named intent rather than ad hoc key branches.

#### Mental model and lifecycle placement

Input lifecycle is normalize -> route -> dispatch -> consume/propagate. Route ordering and scene/window scope are explicit and deterministic. Binding is usually established during bootstrap and feature bind runtime phases.

#### Primary public APIs and key types

Event core: `GuiEvent`, `EventType`, `EventPhase`, `EventManager`, `EventBus`, `InputSnapshot`, `Signal`.

Action/input core: `ActionManager`, `ActionRegistry`, `ActionDescriptor`, `ActionContext`, `ActionMiddleware`, `InputMap`, `InputBinding`, `KeyChordManager`, `KeyChord`, `ChordStep`.

Focus context: `FocusManager`, `FocusScope`, `FocusScopeManager`, `WindowFocusManager`, `FocusRing`.

Event trace tooling: `EventRecorder`, `EventPlayback`, `RecordedEvent`.

#### Typical usage flow

1. Declare actions in config (`ActionSpec` / `ActionBindingSpec`).
2. Bind hotkeys or control key bindings (`ActionHotkeySpec`, `ControlKeyBindingSpec`) or routed runtime specs.
3. Implement handlers and return consume/pass behavior where appropriate.
4. Use tracing tools to validate routing and propagation stops.

#### Minimal example

```python
from gui_do import ActionSpec, ActionHotkeySpec

action_specs = (
   ActionSpec(action_id="exit", label="Exit", kind="exit"),
   ActionSpec(action_id="show_help", label="Show Help", kind="palette_open"),
)
hotkeys = (
   ActionHotkeySpec(action_name="show_help", handler=lambda host: host.app.open_command_palette(), key=120),
)
```

#### Advanced pattern(s)

Use `InteractionStateMachine` for guarded multi-phase pointer/keyboard interactions and combine with `EventRecorder` replay to reproduce tricky sequencing bugs.

#### Common mistakes and anti-patterns

- Handling raw backend input directly in features instead of normalized `GuiEvent`.
- Assuming actions are global when they are scene/window scoped.
- Ignoring `propagation_stopped` and `default_prevented` in custom routing code.

#### Cross-links to related systems

See 8.7 for focus/accessibility interaction, 8.8 for overlay precedence, and 8.16 for diagnostics.

See [Appendix F: Specifications and Option Reference](#appendix-f-specifications-and-option-reference).

[Back to Table of Contents](#table-of-contents)

### State and Observables

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Reactive state is gui_do's default data synchronization model. Features publish state changes and controls or peer features subscribe. This avoids direct mutation chains and keeps updates local and testable.

#### Mental model and lifecycle placement

Create observable containers in feature construction/build, subscribe in `bind_runtime`, dispose in `shutdown_runtime`. Batch mutation when applying groups of updates to avoid callback storms.

#### Primary public APIs and key types

Core observables: `ObservableValue`, `ObservableList`, `ObservableDict`, `ObservableStream`, `CollectionChange`, `ChangeKind`, `ComputedValue`, `reactive_batch`, `is_batching`.

View/projection helpers: `CollectionView`, `CollectionViewQuery`, `Binding`, `BindingGroup`, `SelectionModel`, `SelectionMode`.

Store abstraction: `AppStateStore`, `StateSelector`, `StateTransaction`.

Declarative reactive runtime specs: `StoreSubscriptionSpec`, `StoreSelectorSpec`, `ObservableEffectSpec`, `SignalEffectSpec`.

#### Typical usage flow

1. Own state in observables or `AppStateStore`.
2. Bind UI consumers to selectors/observables.
3. Update source state from feature logic.
4. Dispose subscriptions at teardown.

#### Minimal example

```python
from gui_do import ObservableValue

count = ObservableValue(0)
sub = count.subscribe(lambda value: print("count", value))
count.value = 1
sub.dispose()
```

#### Advanced pattern(s)

Use `AppStateStore` with `StateSelector` slices for cross-feature state and combine with `StateTransaction` for atomic multi-field updates that notify once after commit.

#### Common mistakes and anti-patterns

- Polling in frame update instead of subscribing.
- Subscribing before controls/feature peers are ready.
- Forgetting disposal and leaking callback chains.
- Sharing mutable plain containers across features instead of observable/store contracts.

#### Cross-links to related systems

See 8.2 for lifecycle ownership, 8.13 for form binding, and 8.14 for data pipelines.

See [Appendix F: Specifications and Option Reference](#appendix-f-specifications-and-option-reference).

[Back to Table of Contents](#table-of-contents)

### Controls and Control Composition

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Controls are reusable UI primitives arranged in feature-owned trees. They provide hit testing, focus participation, rendering, and interaction semantics so feature code can focus on behavior instead of low-level widget plumbing.

#### Mental model and lifecycle placement

Create control trees in `build`, then wire callbacks and reactive subscriptions in `bind_runtime`. Avoid creating or reparenting controls from per-frame update loops unless a specific advanced pattern requires it.

#### Primary public APIs and key types

Tier 12 primary controls include `PanelControl`, `LabelControl`, `ButtonControl`, `ToggleControl`, `SliderControl`, `ScrollbarControl`, `CanvasControl`, `CanvasViewport`, `FrameControl`, `ImageControl`, `ArrowBoxControl`, `ButtonGroupControl`, `TabControl`, and `DockWorkspacePanel`.

Tier 13 extended controls include `TextInputControl`, `TextAreaControl`, `RichLabelControl`, `DropdownControl`, `ListViewControl`, `DataGridControl`, `TreeControl`, `SplitterControl`, `ScrollViewControl`, `ProgressBarControl`, `WindowControl`, `TaskPanelControl`, `WindowPresenter`, `PropertyInspectorPanel`, and additional specialized inputs such as `DatePickerControl`, `TimePickerControl`, `ColorPickerControl`, `SplitButtonControl`, and `ChipInputControl`.

Authoring helpers include `ControlDefinition`, `build_specs_from_column_section`, `RowCellSpec`, `build_horizontal_row_specs`, and `build_multi_column_grid_specs`.

#### Typical usage flow

1. Build a root panel for a feature/scene region.
2. Add child controls to that root.
3. Bind control values and callbacks to observables/actions in runtime bind phase.

#### Minimal example

```python
from gui_do import PanelControl, LabelControl, ButtonControl
from pygame import Rect

root = PanelControl("root", Rect(0, 0, 400, 300))
root.add(LabelControl("status", Rect(8, 8, 220, 24), "Ready"))
root.add(ButtonControl("go", Rect(8, 40, 120, 30), "Go"))
```

#### Advanced pattern(s)

Use presenter composition (`WindowPresenter`) to keep feature lifecycle code separate from window UI construction, and combine with `TabbedPresenterSpec`/`TabBuilderSpec` for large, tabbed workbench windows.

#### Common mistakes and anti-patterns

- Cross-feature direct control references.
- Treating controls as canonical state store rather than mirrors of observable/store data.
- Creating control trees outside build lifecycle, causing inconsistent ownership.

#### Cross-links to related systems

See 8.6 for layout ownership, 8.7 for focus semantics, and 8.9 for window/task-panel presentation.

See [Appendix F: Specifications and Option Reference](#appendix-f-specifications-and-option-reference).

[Back to Table of Contents](#table-of-contents)

### Layout Systems

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Layout systems prevent brittle pixel arithmetic by offering declarative structure for container sizing, docking, flow, and constraint-driven placement.

#### Mental model and lifecycle placement

Choose the simplest layout system that fits the region, then keep ownership per container clear. Layout configuration typically happens in build; runtime updates should mutate layout inputs and trigger relayout, not manually move every child each frame.

#### Primary public APIs and key types

Core layout APIs: `FlexLayout`, `GridLayout`, `FlowLayout`, `ConstraintLayout`, `DockWorkspace`, `LayoutPass`, `LayoutRoot`, `WindowLayoutHandler`, `LayoutAnimator`, `Viewport`.

Adaptive and virtualization-adjacent layout APIs: `ConstraintAttr`, `LayoutConstraint`, `ConstraintSet`, `AdaptivePolicy`, `resolve_adaptive_policy`, `VirtualizedWindow`, `VirtualizationCore`, `RecyclePool`.

#### Typical usage flow

1. Pick container layout model (flex/grid/flow/constraint).
2. Add controls and layout items.
3. Re-run layout pass when container bounds or policy breakpoints change.

#### Minimal example

```python
from gui_do import FlexLayout, FlexItem, FlexDirection

layout = FlexLayout(direction=FlexDirection.ROW, gap=8)
layout.add(FlexItem(control=sidebar, grow=0, basis=220))
layout.add(FlexItem(control=content, grow=1))
```

#### Advanced pattern(s)

Compose `ConstraintSet` plus `AdaptivePolicy` to switch constraint behavior at viewport thresholds, and pair with docking for multi-pane workbench UIs.

#### Common mistakes and anti-patterns

- Mixing multiple layout engines in one container without clear ownership.
- Hardcoding pixel positions for responsive panels that should use adaptive policy.
- Calling layout routines before controls are attached to the intended parent tree.

#### Cross-links to related systems

See 8.5 for control composition, 8.9 for window placement, and 8.10 for layout animation timing.

[Back to Table of Contents](#table-of-contents)

### Focus and Accessibility

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Focus and accessibility make keyboard navigation and semantic UI interpretation consistent. Focus managers determine input ownership; accessibility structures expose role/name metadata for assistive and diagnostic tooling.

#### Mental model and lifecycle placement

Focusable controls are registered during build and updated as visibility/enabled states change. Accessibility nodes should be built with control structure and updated as labels/roles change. Subscriptions tied to focus or accessibility announcements should be lifecycle-owned and cleaned in teardown.

#### Primary public APIs and key types

Focus APIs: `FocusManager`, `FocusScope`, `FocusScopeManager`, `WindowFocusManager`, `FocusRing`.

Accessibility APIs: `AccessibilityRole`, `LivePoliteness`, `AccessibilityNode`, `AccessibilityTree`, `AccessibilityAnnouncement`, `AccessibilityBus`.

Spec-level helpers: `StaticAccessibilitySpec`, `AccessibilitySequenceSpec`, `TaskPanelFocusToggleSpec`.

#### Typical usage flow

1. Define semantic role/label metadata for key controls.
2. Ensure hidden or disabled controls are excluded from focus traversal.
3. Use scene/window toggle specs to keep focus ring synchronized with visibility.

#### Minimal example

```python
from gui_do import AccessibilityTree, AccessibilityNode, AccessibilityRole

tree = AccessibilityTree()
tree.root.add_child(AccessibilityNode(role=AccessibilityRole.BUTTON, name="Submit"))
```

#### Advanced pattern(s)

Use scoped focus for modal dialog flows and combine with accessibility announcement bus updates so context switches remain explicit to non-visual consumers.

#### Common mistakes and anti-patterns

- Leaving hidden window controls in focus traversal.
- Missing accessibility metadata on custom canvas-drawn controls.
- Registering focus/accessibility subscribers without scope-owned cleanup.

#### Cross-links to related systems

See 8.3 for routing order, 8.8 for modal overlays, and 8.9 for window visibility coupling.

See [Appendix F: Specifications and Option Reference](#appendix-f-specifications-and-option-reference).

[Back to Table of Contents](#table-of-contents)

### Overlays, Dialogs, Notifications, and Command Surfaces

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Overlays are transient UI layers that must arbitrate input before the underlying control tree. Separate managers provide clear contracts for modals, tooltips, command surfaces, notifications, cursor behavior, and transfer interactions.

#### Mental model and lifecycle placement

Overlay managers run at a higher routing priority than scene controls. Overlay setup usually occurs in bootstrap or feature bind runtime, and any overlay/event subscriptions created via routed runtime must be disposed through lifecycle shutdown.

#### Primary public APIs and key types

Overlay families include `OverlayManager`, `DialogManager`, `ToastManager`, `ContextMenuManager`, `CommandPaletteManager`, `TooltipManager`, `MenuBarManager`, `FileDialogManager`, `NotificationCenter`, `ResizeManager`, `CursorManager`, `DragDropManager`, `ClipboardManager`, `TransferManager`, and `ShortcutHelpOverlay`.

Placement and contracts use `PopupPlacement`, `compute_popup_rect`, `OverlayHandle`, `DialogHandle`, `ToastHandle`, `CommandPaletteHandle`, `TooltipHandle`, and related record types.

Spec integration includes `ShortcutOverlaySpec`, `NotificationSpec`, and routed lifecycle helpers.

#### Typical usage flow

1. Register overlay-capable actions/specs.
2. Show overlay via manager and keep returned handle.
3. Observe dismissal contract and teardown handle usage safely.

#### Minimal example

```python
def on_save(host):
   host.toasts.show("Saved", severity="success")
```

#### Advanced pattern(s)

Combine command palette entries (built-in scene/window groups plus custom provider) with shortcut help overlay to provide discoverable command UX without hand-maintained cheat sheets.

#### Common mistakes and anti-patterns

- Creating overlays without a clear dismissal path.
- Expecting toast click-through when toast bounds intentionally consume clicks.
- Updating dismissed handles without validity checks.
- Wiring overlay subscriptions outside routed lifecycle ownership.

#### Cross-links to related systems

See 8.3 for routing semantics, 8.7 for modal focus constraints, and 8.9 for window presentation composition.

See [Appendix F: Specifications and Option Reference](#appendix-f-specifications-and-option-reference).

[Back to Table of Contents](#table-of-contents)

### Scene, Window, and Task-Panel Presentation Models

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Scene/window/task-panel presentation APIs coordinate what is visible, what is focusable, and which controls represent active work surfaces. This chapter covers scene-local windows, menu/task panel toggles, and presenter-driven window content.

#### Mental model and lifecycle placement

Scene and window topology is declared at bootstrap. Windows and presenters are created in feature build phases, then visibility/focus toggles are bound in runtime. Hidden windows should be removed from active focus traversal.

Scene menu strip, task panel, and command palette are optional runtime facilities. They only exist when explicitly declared in your scene/runtime specs.

#### Primary public APIs and key types

Core model types: `ScenePresentationModel`, `WindowPresenter`, `WindowSpec`, `AnchoredWindowSpec`, `SceneTaskPanelSpec`, `TaskPanelButtonSpec`, `TaskPanelFocusToggleSpec`, `FeatureWindowBundleBindingSpec`, `WindowToggleBindingSpec`, `TabbedPresenterSpec`, `TabBuilderSpec`.

Tier 18 helpers: `set_window_visible_state`, `toggle_window_visibility`, `create_anchored_feature_window`, `create_feature_presented_window`, `add_window_scene_menu_strip`, `ensure_scene_task_panel`, `ActiveTabUpdateRouter`, `TabLayoutContext`.

#### Typical usage flow

1. Declare window/task panel specs in host config.
2. Build presenter-backed windows in feature build.
3. Bind toggle/focus behavior in routed runtime.
4. Keep task panel and window visibility states synchronized.

#### Minimal example

```python
from gui_do import create_feature_presented_window

window = create_feature_presented_window(host, feature=self, spec=my_window_spec, presenter=my_presenter)
```

#### Advanced pattern(s)

Compose multi-window scenes where each window hosts tabbed presenters, and use `ActiveTabUpdateRouter` so only active tabs receive high-frequency update routing.

#### Common mistakes and anti-patterns

- Building windows in runtime bind rather than feature build.
- Letting task panel toggle state drift from actual window visibility.
- Not excluding hidden windows from focus ring traversal.

#### Cross-links to related systems

See 8.2 for lifecycle ownership, 8.7 for focus behavior, and 8.8 for overlay interactions.

See [Appendix F: Specifications and Option Reference](#appendix-f-specifications-and-option-reference).

[Back to Table of Contents](#table-of-contents)

### Scheduling, Timing, Animation, and Transitions

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Scheduling and animation systems keep time-based behavior smooth while enforcing runtime budget guarantees. They support timers, transitions, tweens, debounced/throttled events, scene timelines, and cooperative coroutine workflows.

#### Mental model and lifecycle placement

Frame update work should remain budgeted and cancellable. Start schedulers/tweens in bind/runtime events and cancel or detach them at teardown. Heavy or multi-stage workflows should avoid blocking frame loops.

#### Primary public APIs and key types

Scheduling APIs: `TaskScheduler`, `TaskEvent`, `Timers`, `TweenManager`, `TweenHandle`, `Easing`, `AnimationSequence`, `AnimationHandle`, `TransitionManager`, `TransitionSpec`, `TransitionEvent`, `AnimationStateMachine`, `AnimationTransitionMode`, `SceneTimeline`, `Debouncer`, `Throttler`.

Coroutine scheduling: `CooperativeScheduler`, `CoroutineHandle`, `Pause`, `Sleep`, `WaitForEvent`, `WaitForSignal`, `WaitUntil`, `WaitForAll`.

Cancelable dataflow integration: `CancellationToken`, `PipelineStage`, `DataflowPipeline`, `PipelineHandle`.

Scheduler contract values: fraction `0.12`, floor `0.5 ms`, ceiling `4.0 ms`.

#### Typical usage flow

1. Register timed or animated behavior.
2. Run per-frame progression under scheduler budget.
3. Cancel outstanding work at scene/feature teardown.

#### Minimal example

```python
def fade_in(host, panel):
   return host.tweens.to(panel, "alpha", 255, duration=0.2)
```

#### Advanced pattern(s)

Use `CooperativeScheduler` for multi-step workflows that pause on events/signals while staying on the main loop budget. Pair with failure policies for retry and timeout behaviors instead of custom retry loops.

#### Common mistakes and anti-patterns

- Doing expensive synchronous work in `on_update`.
- Leaving tweens/coroutines running after scene transition.
- Treating timeout/retry logic as ad hoc callbacks instead of scheduled operations.

#### Cross-links to related systems

See 8.14 for data pipeline integration and 8.16 for telemetry-based budget analysis.

[Back to Table of Contents](#table-of-contents)

### Persistence and Workspace/Session State

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Persistence APIs capture and restore workspace/session state so application context survives restarts. They also provide typed settings and versioned migration primitives for schema evolution.

#### Mental model and lifecycle placement

Persist stable, serializable state at controlled save points. Restore during startup and inspect restore reports rather than assuming every key or block is present. Keep migration explicit and version-aware.

#### Primary public APIs and key types

Persistence/state core: `WorkspacePersistenceManager`, `WorkspaceState`, `SettingsRegistry`, `SettingDescriptor`, `SceneSnapshot`, `NodeSnapshot`, `DEFAULT_WORKSPACE_STATE_PATH`, `CommandHistory`, `Command`, `CommandTransaction`, `UndoContextManager`.

Migration layer: `SchemaVersion`, `VersionedSnapshot`, `MigrationStep`, `MigrationRegistry`, `SnapshotMigrator`, `MigrationError`, `make_snapshot`, `read_version`.

Restore report fields: `target_scene`, `switched_scene`, `restored_feature_states`, `restored_scene_nodes`, `applied_settings`, `skipped_settings`, `missing_settings_blocks`.

#### Typical usage flow

1. Save workspace state at controlled checkpoints.
2. Load/restore at startup.
3. Inspect restore report and degrade gracefully if blocks are missing.
4. Migrate older snapshots before applying to runtime.

#### Minimal example

```python
report = host.app.load_workspace("workspace.json")
if report and report.skipped_settings:
   host.toasts.show("Some settings were skipped during restore")
```

#### Advanced pattern(s)

Version snapshot payloads and register one-way migration steps per schema change. Use operation policies for save/load failure handling and user feedback publication.

#### Common mistakes and anti-patterns

- Assuming all settings keys exist forever.
- Applying snapshots without checking/normalizing schema version.
- Using one default workspace path for multiple concurrent app instances.

#### Cross-links to related systems

See 8.1 for bootstrap integration, 8.2 for teardown/save timing, and 8.16 for persistence telemetry.

See [Appendix F: Specifications and Option Reference](#appendix-f-specifications-and-option-reference).

[Back to Table of Contents](#table-of-contents)

### Theme, Styling, and Visual Systems

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Theme and font systems centralize visual semantics so style changes do not require invasive control-by-control edits.

#### Mental model and lifecycle placement

Register fonts and role bindings during bootstrap. Controls reference semantic roles, not file paths. Theme changes should invalidate caches through dedicated invalidation channels.

#### Primary public APIs and key types

Theme/font APIs: `FontManager`, `FontRoleRegistry`, `ColorTheme`, `ThemeManager`, `DesignTokens`, `ScopedTheme`, `ScopedThemeManager`, `ThemeInvalidationBus`, `setup_standard_font_roles`.

Spec-level wiring: `FontRoleBindingSpec`, `CursorSpec`, `CursorBindingSpec`.

#### Typical usage flow

1. Declare fonts and font-role bindings in host config.
2. Use semantic role names in controls and presenters.
3. Switch active theme at runtime and allow invalidation bus subscribers to refresh cached renders.

#### Minimal example

```python
host.theme_manager.set_theme("dark")
```

#### Advanced pattern(s)

Use `ScopedThemeManager` to apply local theme overrides to subtrees (for example, utility panes) while maintaining global token consistency elsewhere.

#### Common mistakes and anti-patterns

- Hardcoding colors in feature draw code instead of semantic tokens.
- Switching theme without cache invalidation integration.
- Registering font roles after controls already depend on them.

#### Cross-links to related systems

See 8.5 for control rendering, 8.15 for custom graphics integration, and 8.16 for visual diagnostics.

See [Appendix F: Specifications and Option Reference](#appendix-f-specifications-and-option-reference).

[Back to Table of Contents](#table-of-contents)

### Text, Input, Forms, and Validation Systems

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Text entry and form workflows are common enough to require dedicated runtime abstractions. gui_do provides low-level input controls and higher-level form/schema/validation orchestration so teams can model constraints once and reuse them across scenes.

#### Mental model and lifecycle placement

Controls handle capture and editing; form models handle field semantics and validation policy. Runtime wiring belongs in feature bind phase so validators and control bindings are established after controls exist.

#### Primary public APIs and key types

Forms and validation: `FormModel`, `FormField`, `ValidationRule`, `FieldError`, `FormSchema`, `SchemaField`, `ValidationResult`, `Validator`, `RequiredValidator`, `RangeValidator`, `LengthValidator`, `PatternValidator`, `CustomValidator`, `DependentValidator`, `ValidationPipeline`.

Text and localization: `TextInputControl`, `TextAreaControl`, `DocumentModel`, `TextFormatter`, `NumericFormatter`, `PatternFormatter`, `FixedPatternFormatter`, `TextFlow`, `TextSpan`, `TextSearcher`, `TextMatch`, `StringTable`, `LocaleRegistry`.

Schema and async validation: `FieldSchema`, `FieldGraphSchema`, `ValidationPolicy`, `SchemaFormRuntime`, `AsyncFieldValidator`, `AsyncFormValidator`.

#### Typical usage flow

1. Define schema/validators.
2. Bind fields to controls.
3. Choose validation policy (`ON_CHANGE`, submit, or mixed strategy).
4. Use async validator where remote checks are needed.

#### Minimal example

```python
from gui_do import RequiredValidator, PatternValidator, ValidationPipeline

pipeline = ValidationPipeline(
   validators=(
      RequiredValidator("Email is required"),
      PatternValidator(r".+@.+", "Email format is invalid"),
   )
)
```

#### Advanced pattern(s)

Use `SchemaFormRuntime` + `FieldGraphSchema` for dependency-driven visibility and policy-bound validation, then layer `AsyncFormValidator` with debounce and stale-result suppression for remote uniqueness checks.

#### Common mistakes and anti-patterns

- Validating only on submit when UX expects immediate feedback.
- Ignoring declared validation policy and manually forcing inconsistent checks.
- Running async validation without cancellation/stale generation handling.

#### Cross-links to related systems

See 8.4 for state binding and 8.14 for async data pipeline support.

See [Appendix F: Specifications and Option Reference](#appendix-f-specifications-and-option-reference).

[Back to Table of Contents](#table-of-contents)

### Data and Dataflow Helpers

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Data-heavy interfaces need scalable loading, filtering, virtualization, and cancellation semantics. This system provides those primitives so large lists/grids/trees remain interactive.

#### Mental model and lifecycle placement

Treat data processing as staged pipelines with cancellation and explicit load state. Keep long-running work out of frame-critical callbacks and publish intermediate state through observables/store selectors.

#### Primary public APIs and key types

Sources/proxies: `VirtualItemSource`, `FixedItemSource`, `SortFilterProxySource`, `AsyncDataProvider`, `LoadState`, `LoadStateKind`.

Pipeline and cancellation: `DataflowPipeline`, `PipelineStage`, `PipelineHandle`, `CancellationToken`.

Virtualization and diffing: `VirtualizationCore`, `VirtualizedWindow`, `RecyclePool`, `ListDiffCalculator`, `ListDiff`, `DiffInsert`, `DiffRemove`, `DiffMove`.

Performance helpers: `ObjectPool`, `DataCache`, `CacheStats`, `AppStateStore`, `StateSelector`, `StateTransaction`.

#### Typical usage flow

1. Establish source/provider.
2. Apply sort/filter proxy.
3. Feed a virtualized control/window.
4. Route expensive transforms through cancelable pipeline stages.

#### Minimal example

```python
from gui_do import FixedItemSource, SortFilterProxySource

source = FixedItemSource(items)
proxy = SortFilterProxySource(source)
proxy.set_filter(lambda item: item.enabled)
proxy.set_sort_key(lambda item: item.name)
```

#### Advanced pattern(s)

Build multi-stage ranking/search pipelines where each user input creates a new generation token and stale in-flight generations are canceled automatically through `CancellationToken`.

#### Common mistakes and anti-patterns

- Full redraw without diffing.
- Not canceling stale dataflow generations.
- Holding large transient data sets without cache eviction policy.

#### Cross-links to related systems

See 8.10 for scheduler interaction, 8.5 for list/grid controls, and 8.16 for telemetry of pipeline costs.

See [Appendix F: Specifications and Option Reference](#appendix-f-specifications-and-option-reference).

[Back to Table of Contents](#table-of-contents)

### Graphics and Audio Integration Points

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Graphics and audio APIs support custom rendering and semantic sound cues without forcing applications to reimplement core render/audio management.

#### Mental model and lifecycle placement

Custom visuals should live in draw paths or canvas-backed controls, with expensive assets initialized before frame loops. Audio should be event/intent-driven rather than tied to low-level pointer noise.

#### Primary public APIs and key types

Graphics core: `BuiltInGraphicsFactory`, `DirtyRegionTracker`, `DrawContext`, `DrawPhase`, `AssetRegistry`, `DebugOverlay`, `SurfaceCompositor`, `Layer`, `ShapeRenderer`, `SurfaceEffects`, `VectorPath`, `SpriteSheet`, `FrameAnimation`, `ParticleSystem`, `Emitter`, `ParticleLayer`, `TileSet`, `TileMap`, `Node2D`, `SceneGraph2D`, `Camera2D`, `RenderTarget`, `LiveRenderTarget`, `OffscreenRenderTarget`, `create_render_target`, `create_surface`.

Audio core: `SoundCue`, `SoundBankRegistry`, `SoundEventBus`.

#### Typical usage flow

1. Initialize assets and render structures.
2. Update animation/particle state in update phase.
3. Draw via dirty-region-aware rendering where possible.
4. Publish semantic sound cues through the sound event bus.

#### Minimal example

```python
def notify_saved(host):
   host.sound_bus.publish(SoundCue("notify"))
```

#### Advanced pattern(s)

Combine `DirtyRegionTracker` with offscreen render targets to redraw only changed regions, then composite final surfaces in layered passes.

#### Common mistakes and anti-patterns

- Full-surface redraw every frame for mostly static scenes.
- Loading assets in draw loop.
- Emitting audio cues from noisy low-level events.

#### Cross-links to related systems

See 8.10 for timing, 8.5 for canvas controls, and 8.16 for profiling support.

[Back to Table of Contents](#table-of-contents)

### Telemetry, Introspection, and Operational Hooks

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Telemetry and introspection provide operational visibility: where frame time goes, how properties evolve, and what spatial regions are active. These APIs reduce guesswork in optimization and debugging.

#### Mental model and lifecycle placement

Enable telemetry before running scenarios you want to analyze. Capture representative user flows, then inspect structured records and reports. Use property and spatial inspection for live diagnostics.

#### Primary public APIs and key types

Telemetry: `TelemetryCollector`, `TelemetrySample`, `configure_telemetry`, `telemetry_collector`, `load_telemetry_log_file`, `analyze_telemetry_log_file`, `analyze_telemetry_records`, `render_telemetry_report`.

Introspection: `ui_property`, `PropertyDescriptor`, `PropertyRegistry`, `property_registry`, `PropertyInspectorModel`, `InspectedProperty`, `SceneSpatialIndex`.

#### Typical usage flow

1. Enable telemetry.
2. Run scenario.
3. Analyze records and render report.
4. Correlate hot spots with property/spatial inspection.

#### Minimal example

```python
from gui_do import configure_telemetry, telemetry_collector, analyze_telemetry_records

configure_telemetry(enabled=True)
report = analyze_telemetry_records(telemetry_collector.records)
```

#### Advanced pattern(s)

Combine telemetry traces with property inspector snapshots and debug overlays to localize regressions in routing, layout, or rendering costs.

#### Common mistakes and anti-patterns

- Profiling only idle loops.
- Starting telemetry after the scenario already ran.
- Ignoring structured reports and relying on visual impression alone.

#### Cross-links to related systems

See 8.10 for scheduler budgets, 8.11 for restore diagnostics, and 8.15 for rendering cost analysis.

[Back to Table of Contents](#table-of-contents)

## Integration Patterns and Composition Recipes

[Back to Table of Contents](#table-of-contents)

### Recipe 1: Routed Feature + Actions + Shortcut Overlay

Goal: provide discoverable shortcuts with lifecycle-owned wiring.

Pattern: declare actions in config, build a `RoutedRuntimeSpec` that includes `ShortcutOverlaySpec`, bind with `bind_routed_feature_lifecycle`, and always unwind with `shutdown_routed_feature_lifecycle`.

Validation notes: verify overlay toggle key path, verify manual and registry-driven entries render expected sections, and verify no duplicated handlers after scene re-entry.

### Recipe 2: Window Presenter + Task Panel + Focus Toggle

Goal: manage floating windows with synchronized task-panel state and focus exclusion when hidden.

Pattern: declare `AnchoredWindowSpec` or `FeatureWindowBundleBindingSpec`, build presenter-backed windows, and apply `TaskPanelFocusToggleSpec` in routed runtime so hidden windows leave focus traversal automatically.

Validation notes: hide/show cycles must keep task-panel toggle, window visibility, and focus ring state aligned.

### Recipe 3: State Store + Persistence + Snapshot Migration

Goal: keep shared state durable across schema versions.

Pattern: own app state in `AppStateStore`, derive slices via `StateSelector`, persist through versioned snapshots (`make_snapshot`), and migrate on load (`read_version`, `SnapshotMigrator`).

Validation notes: ensure restore reports surface skipped/missing settings and migration failures are explicit rather than silent.

### Recipe 4: Dataflow Pipeline + Telemetry + Error Boundary

Goal: run background processing safely and measure it.

Pattern: stage work in `DataflowPipeline` with `CancellationToken`, instrument scenario execution with telemetry, and wrap risky presentation trees in `ErrorBoundary` to degrade gracefully.

Validation notes: stale generations must cancel, telemetry reports should identify bottlenecks, and boundary fallback should render on injected failures.

[Back to Table of Contents](#table-of-contents)

## End-to-End Reference Application

[Back to Table of Contents](#table-of-contents)

```python
from pygame import K_F9, Rect

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
   ShortcutOverlaySpec,
   TelemetryConfig,
   bind_routed_feature_lifecycle,
   bootstrap_host_application,
   shutdown_routed_feature_lifecycle,
)


class DemoFeature(RoutedFeature):
   scene_name = "main"

   def __init__(self):
      super().__init__()
      self.counter = ObservableValue(0)
      self._sub = None
      self._runtime = RoutedRuntimeSpec(
         scene_name="main",
         shortcut_overlay=ShortcutOverlaySpec(
            toggle_action_name="show_help",
            toggle_key=K_F9,
            manual_section_title="Demo",
            manual_shortcut_lines=("F9: Toggle help",),
         ),
      )
      self._lifecycle = RoutedFeatureLifecycleSpec(runtime_spec=self._runtime)

   def build(self, host):
      self.root = host.app.add(PanelControl("demo_root", Rect(20, 20, 420, 200)), scene_name="main")
      self.label = self.root.add(LabelControl("demo_label", Rect(12, 12, 320, 24), "Count: 0"))

   def bind_runtime(self, host):
      self._sub = self.counter.subscribe(lambda value: setattr(self.label, "text", f"Count: {value}"))
      bind_routed_feature_lifecycle(self, host, self._lifecycle)

   def increment(self):
      self.counter.value = self.counter.value + 1

   def shutdown_runtime(self, host):
      shutdown_routed_feature_lifecycle(self, host, self._lifecycle)
      if self._sub:
         self._sub.dispose()


class Host:
   def save_workspace(self):
      self.app.save_workspace("workspace.json")

   def load_workspace(self):
      self.app.load_workspace("workspace.json")


host = Host()
config = HostApplicationConfig(
   display_size=(1280, 720),
   window_title="gui_do reference",
   initial_scene_name="main",
   feature_specs=(FeatureSpec("demo_feature", DemoFeature),),
   runtime_scene_specs=(RuntimeSceneSpec(scene_name="main", bind_escape_to_exit=True),),
   action_specs=(
      ActionSpec(action_id="exit", label="Exit", kind="exit"),
      ActionSpec(action_id="show_help", label="Shortcut Help", kind="palette_open"),
   ),
   telemetry=TelemetryConfig(enabled=True),
)
bootstrap_host_application(host, config)
host.load_workspace()
exit_code = host.app.run_entrypoint(save_workspace_fn=host.save_workspace)
```

### What This Listing Demonstrates

This reference combines declarative bootstrap, routed lifecycle composition, reactive state-to-control updates, action declarations, runtime scene policy (`bind_escape_to_exit=True`), telemetry activation, and workspace save/load hooks in one concise host flow.

### Validation Checklist

1. App opens with active `main` scene.
2. Counter updates are reflected on the label.
3. `F9` toggles shortcut help overlay.
4. Escape key exits because runtime scene binding enables exit handling.
5. Workspace load/save hooks run without aborting runtime entrypoint.
6. Scene re-entry does not duplicate routed handlers.

[Back to Table of Contents](#table-of-contents)

## Testing, Diagnostics, and Reliability

[Back to Table of Contents](#table-of-contents)

Contract testing is the primary guardrail for keeping this manual and the runtime in sync. The contract suite validates public exports, docs alignment, boundary rules, runtime operating guarantees, and workspace behavior. Run these tests before release and after any export, routing, or lifecycle changes.

```bash
python -m pytest -q tests/test_public_api_exports.py tests/test_public_api_docs_contracts.py tests/test_runtime_operating_contracts.py tests/test_boundary_contracts.py tests/test_gui_application_workspace_contracts.py
```

Core contract file intent:

- `test_public_api_exports.py`: verifies root exports are importable.
- `test_public_api_docs_contracts.py`: validates docs/API contract alignment.
- `test_runtime_operating_contracts.py`: validates deterministic runtime guarantees.
- `test_boundary_contracts.py`: enforces framework/demo boundary.
- `test_gui_application_workspace_contracts.py`: validates restore/report behavior.

Runtime behavior tests should also cover overlay routing, tooltip/cursor behavior, control runtime determinism, layout/animation ordering, accessibility behavior, and routed runtime teardown. For routed facilities specifically, require tests for service/effect registration/cleanup, operation retry/timeout/failure publication, and full scope disposal during `shutdown_runtime`.

Debug and trace stack:

- `EventRecorder` / `EventPlayback` for deterministic input reproduction.
- `DebugOverlay` for visual state inspection.
- `PropertyInspectorPanel` and property registry for live control introspection.
- Telemetry log analysis via `analyze_telemetry_log_file` and `render_telemetry_report`.

Maintainer release runbook:

1. Run contract tests.
2. Run targeted runtime suites for changed systems.
3. Replay representative end-to-end scenes.
4. Validate boundary constraints and import discipline.
5. Rebuild docs/manual sections affected by export or contract changes.

Regression triage workflow:

1. Reproduce with minimal deterministic scenario.
2. Capture trace (event + telemetry + relevant snapshots).
3. Localize failing contract or lifecycle phase.
4. Add failing test first.
5. Patch and rerun adjacent contract suites.

### Maintainer Diff Checklist

Inventory delta checks:

1. Compare current root exports in `gui_do/__init__.py` with Appendix D and D.1.
2. Review `docs` contracts for changed guarantees/policies.
3. Scan `tests` for new contract/runtime modules that imply manual updates.
4. Scan `demo_features` for new composition patterns worth documenting.

Content integrity checks:

1. Changed systems are updated in both narrative chapters and API index sections.
2. Removed APIs are removed from examples and appendix groups.
3. Added APIs are placed at the appropriate abstraction tier guidance.

Navigation and structure checks:

1. New sections are present in TOC and anchors resolve.
2. Every major section keeps a back-to-TOC link.
3. Top-level order remains stable unless intentionally restructured.

Operational checks:

1. Re-run high-priority contract tests.
2. Revalidate end-to-end reference assumptions against current runtime.
3. Record unresolved ambiguities in migration/deprecation guidance.

[Back to Table of Contents](#table-of-contents)

## Performance and Scaling Guidance

[Back to Table of Contents](#table-of-contents)

The scheduler dispatch contract is fixed to fraction `0.12` of frame dt in milliseconds with floor `0.5 ms` and ceiling `4.0 ms`. This keeps dispatch from starving under fast frames while bounding worst-case scheduler time in slow frames.

`DirtyRegionTracker` is the primary draw optimization for mixed static/dynamic scenes. The overlap query is cheap because tracker state includes a running union cache; use this to avoid re-rendering unchanged regions.

Virtualization and incremental updates should be preferred for large collections:

- `VirtualizationCore` and `VirtualizedWindow` for windowed rendering.
- `RecyclePool` for view reuse.
- `ListDiffCalculator` for minimal updates.

Scaling checklist:

1. Keep updates scene-scoped.
2. Avoid per-frame full collection reconstruction.
3. Use `ObjectPool` for high-churn structures.
4. Debounce/throttle expensive user-triggered operations.
5. Use cancelable `DataflowPipeline` for preemptible workloads.
6. Profile representative user flows with telemetry, not idle loops.
7. Gate expensive rendering with dirty region checks.

[Back to Table of Contents](#table-of-contents)

## Migration, Versioning, and Deprecation Notes

[Back to Table of Contents](#table-of-contents)

Use versioned snapshots for any persisted schema that may evolve. Write with `make_snapshot`, inspect version with `read_version`, then migrate using `SnapshotMigrator` and registered `MigrationStep` instances before applying state.

Recommended migration flow:

1. Serialize with current schema version.
2. On load, read version from raw snapshot.
3. Run migration path through `SnapshotMigrator`.
4. Apply migrated snapshot and inspect restore report.

Deprecation policy guidance:

- Prefer additive transitions with explicit warnings.
- Remove behavior only after a documented migration path exists.
- Keep active deprecations centralized in this section.

No formal deprecated public APIs are currently cataloged in this generation. Add entries here when formal deprecations are introduced.

Upgrade checklist:

1. Run contract tests before and after upgrade.
2. Verify root-import usage in application entrypoints.
3. Validate action/input/focus behavior in active scenes.
4. Verify restore report fields and skipped/missing handling.
5. Re-run telemetry baselines for representative flows.
6. Ensure routed runtime terminology and examples match current API names.

[Back to Table of Contents](#table-of-contents)

## FAQ and Troubleshooting

[Back to Table of Contents](#table-of-contents)

### Should I build apps directly with controls or with features?

Use features as your architectural unit and controls as implementation details inside them. Features carry lifecycle orchestration, scene scope, routing participation, and cleanup guarantees that controls alone do not provide.

### When should I use RoutedFeature over Feature?

Use `RoutedFeature` when declarative runtime wiring and message-oriented coordination are central to the feature. If the feature only needs basic build/bind/update/draw behavior, plain `Feature` is usually sufficient.

### Why are some key handlers not firing?

Check focus ownership, scene/window scope of bindings, and whether an overlay is currently consuming keys. Then use `EventRecorder` to verify normalized event path and propagation stops.

### Why do toast clicks not pass through?

Toast bounds intentionally consume click events by contract to prevent accidental interactions with underlying controls. Use toast callbacks for intentional click actions.

### How do I avoid breaking workspace restore across versions?

Persist versioned snapshots, migrate explicitly, and inspect restore report fields (`skipped_settings`, `missing_settings_blocks`) rather than assuming complete replay.

### How do I confirm my API usage is supported?

Use explicit root imports from `gui_do` and run contract tests that validate root export integrity and docs alignment.

### Why does bind_runtime ordering seem wrong between features?

The runtime guarantees all scene features complete `build` before any `bind_runtime` call. If behavior appears otherwise, check scene declarations and feature registration scope.

### How do I add a shortcut without touching routing internals?

Declare action and hotkey specs (or routed runtime equivalents). The action/input map path is then established declaratively and cleaned with feature lifecycle.

[Back to Table of Contents](#table-of-contents)

## Appendix

[Back to Table of Contents](#table-of-contents)

### Appendix A: Glossary

[Back to Table of Contents](#table-of-contents)

Feature: lifecycle-managed behavior unit (`Feature`, `DirectFeature`, `LogicFeature`, `RoutedFeature`) that owns runtime setup and cleanup.

Spec: declarative data object used to describe runtime wiring, configuration, and control-plane intent.

Host: plain object passed to bootstrap that receives app/runtime members.

Scene: top-level interaction context containing a scoped set of active features.

Routed runtime: declarative bundle of action, shortcut, service/effect, operation, and higher-level runtime faculties bound to feature lifecycle.

Observable: reactive value or collection that notifies subscribers on change.

Workspace state: persisted runtime context restored between sessions.

Contract test: automated test asserting framework-level guarantees.

Tier: root export grouping by abstraction level and recommended usage order.

Runtime scope: lifecycle-owned container for resources that must be fully unwound.

[Back to Table of Contents](#table-of-contents)

### Appendix B: Lifecycle/Event Sequence

[Back to Table of Contents](#table-of-contents)

1. Bootstrap host from config specs.
2. Run `build` for all features in active scene order.
3. Run `bind_runtime` for all features once build phase completes.
4. Enter runtime loop.
5. Normalize raw input to `GuiEvent`.
6. Route overlays/focus/window handlers.
7. Dispatch feature event handlers.
8. Execute frame updates and scheduled work.
9. Draw feature/custom rendering and control tree.
10. On scene transition, shutdown departing features and build/bind arriving features.
11. On app exit, run feature teardown and persistence save hooks.

[Back to Table of Contents](#table-of-contents)

### Appendix C: System Dependency Map

[Back to Table of Contents](#table-of-contents)

Bootstrap and scene configuration depend on Tier 1 specs and lifecycle semantics. Feature systems depend on controls, event routing, and state. Layout/focus depend on control trees and scene/window visibility. Overlays depend on routing precedence and focus policy. Persistence depends on state and scene/window registration. Scheduling crosses feature updates and animation systems. Telemetry/introspection cut across all layers.

Service scope and routed runtime faculties can be applied across many tiers but should remain lifecycle-owned and scene-aware.

[Back to Table of Contents](#table-of-contents)

### Appendix D: API Quick Index

[Back to Table of Contents](#table-of-contents)

Bootstrap and composition: `HostApplicationConfig`, `HostApplicationBindingSpec`, `build_host_application_config`, `bootstrap_host_application`, `FeatureSpec`, `WindowSpec`, `RuntimeSceneSpec`, `SceneBundleBindingSpec`, `FeatureWindowBundleBindingSpec`, `SceneSetupSpec`.

Features and runtime wiring: `Feature`, `DirectFeature`, `LogicFeature`, `RoutedFeature`, `FeatureMessage`, `FeatureManager`, `RoutedRuntimeSpec`, `RoutedFeatureLifecycleSpec`, `bind_routed_feature_lifecycle`, `shutdown_routed_feature_lifecycle`, `FeatureRuntimeScope`, `FeatureOperationBus`.

Events and actions: `GuiEvent`, `EventType`, `EventPhase`, `EventManager`, `EventBus`, `ActionManager`, `ActionRegistry`, `ActionDescriptor`, `InputMap`, `KeyChordManager`, `Signal`, `EventRecorder`, `EventPlayback`.

State and observables: `ObservableValue`, `ObservableList`, `ObservableDict`, `ComputedValue`, `reactive_batch`, `CollectionView`, `Binding`, `AppStateStore`, `StateSelector`, `StateTransaction`.

Controls and presentation: Tier 12/13 controls including `PanelControl`, `LabelControl`, `ButtonControl`, `CanvasControl`, `WindowControl`, `TaskPanelControl`, `WindowPresenter`, `ListViewControl`, `DataGridControl`, `TreeControl`, `PropertyInspectorPanel`.

Layout and virtualization: `FlexLayout`, `GridLayout`, `FlowLayout`, `ConstraintLayout`, `DockWorkspace`, `AdaptivePolicy`, `VirtualizedWindow`, `VirtualizationCore`, `RecyclePool`.

Overlays and command surfaces: `OverlayManager`, `DialogManager`, `ToastManager`, `CommandPaletteManager`, `TooltipManager`, `NotificationCenter`, `DragDropManager`, `ShortcutHelpOverlay`.

Forms, text, validation: `FormModel`, `FormSchema`, `ValidationPipeline`, `SchemaFormRuntime`, `AsyncFormValidator`, `TextInputControl`, `TextAreaControl`, `TextFormatter`, `StringTable`.

Data pipeline and persistence: `AsyncDataProvider`, `SortFilterProxySource`, `DataflowPipeline`, `CancellationToken`, `WorkspacePersistenceManager`, `SnapshotMigrator`, `MigrationStep`, `make_snapshot`, `read_version`.

Graphics/audio/observability: `DirtyRegionTracker`, `DrawContext`, `SurfaceCompositor`, `ParticleSystem`, `SceneGraph2D`, `SoundEventBus`, `TelemetryCollector`, `configure_telemetry`, `PropertyRegistry`, `SceneSpatialIndex`.

[Back to Table of Contents](#table-of-contents)

### Appendix D.1: Tier Matrix

[Back to Table of Contents](#table-of-contents)

| Tier | System | Representative APIs |
|---|---|---|
| 1 | Primary entrypoints and data-driven APIs | `HostApplicationConfig`, `FeatureSpec`, `RoutedRuntimeSpec`, `build_host_application_config`, `bootstrap_host_application` |
| 2 | Core app and scene management | `GuiApplication`, `create_display`, `SceneTransitionManager` |
| 3 | Essential data and state | `ObservableValue`, `ComputedValue`, `CollectionView`, `reactive_batch` |
| 4 | Events/actions/focus/input | `GuiEvent`, `ActionManager`, `InputMap`, `FocusManager`, `EventRecorder` |
| 5 | Scheduling and animation | `TaskScheduler`, `TweenManager`, `CooperativeScheduler`, `SceneTimeline` |
| 6 | Theme and font | `ThemeManager`, `ColorTheme`, `FontRoleRegistry`, `DesignTokens` |
| 7 | Telemetry and diagnostics | `TelemetryCollector`, `configure_telemetry`, `render_telemetry_report` |
| 8 | Layout and spatial | `FlexLayout`, `GridLayout`, `ConstraintLayout`, `DockWorkspace` |
| 9 | Overlay managers and windows | `DialogManager`, `ToastManager`, `CommandPaletteManager`, `ShortcutHelpOverlay` |
| 10 | Forms and data binding | `FormModel`, `FormSchema`, `ValidationPipeline`, `WizardFlow` |
| 11 | State and persistence | `WorkspacePersistenceManager`, `SettingsRegistry`, `CommandHistory`, `SceneSnapshot` |
| 12 | Primary controls | `PanelControl`, `LabelControl`, `ButtonControl`, `CanvasControl` |
| 13 | Extended controls | `TextInputControl`, `ListViewControl`, `WindowPresenter`, `PropertyInspectorPanel` |
| 14 | Text and localization | `TextFormatter`, `TextFlow`, `TextSearcher`, `LocaleRegistry` |
| 15 | Data and collections | `VirtualItemSource`, `SortFilterProxySource`, `AsyncDataProvider`, `ListDiffCalculator` |
| 16 | Graphics and rendering | `DirtyRegionTracker`, `DrawContext`, `SurfaceCompositor`, `ParticleSystem` |
| 17 | Introspection and inspection | `ui_property`, `PropertyRegistry`, `SceneSpatialIndex` |
| 18 | Advanced runtime and bootstrapping | `set_window_visible_state`, `create_feature_presented_window`, `bind_routed_feature_lifecycle`, `ActiveTabUpdateRouter` |
| 19 | Infrastructure internals | `UiEngine` |
| 20 | Audio | `SoundCue`, `SoundBankRegistry`, `SoundEventBus` |
| 21 | Accessibility | `AccessibilityNode`, `AccessibilityTree`, `AccessibilityBus` |
| 22 | Theme invalidation | `ThemeInvalidationBus` |
| 23 | Undo context routing | `UndoContextManager` |
| 24 | Async form validation | `AsyncFieldValidator`, `AsyncFormValidator` |
| 25 | Scoped service graph | `ServiceKey`, `ServiceScope`, `ScopeStack` |
| 26 | Cancelable dataflow pipeline | `CancellationToken`, `PipelineStage`, `DataflowPipeline` |
| 27 | Transactional app state store | `AppStateStore`, `StateSelector`, `StateTransaction` |
| 28 | Adaptive constraint layout v2 | `ConstraintAttr`, `ConstraintSet`, `AdaptivePolicy` |
| 29 | Unified virtualization core | `MeasureMode`, `VirtualizedWindow`, `VirtualizationCore` |
| 30 | Interaction state machine framework | `InteractionPhase`, `InteractionContext`, `InteractionStateMachine` |
| 31 | Schema-driven form runtime | `FieldGraphSchema`, `ValidationPolicy`, `SchemaFormRuntime` |
| 32 | Portable snapshot and migration | `SchemaVersion`, `VersionedSnapshot`, `SnapshotMigrator`, `MigrationStep` |

[Back to Table of Contents](#table-of-contents)

### Appendix D.2: Selection Heuristics

[Back to Table of Contents](#table-of-contents)

1. Start with Tier 1 declarative bootstrap and feature specs.
2. Move to lower tiers only when Tier 1 composition does not solve the requirement.
3. Use Tier 18 helpers only when extending bootstrap/runtime behavior intentionally.
4. Prefer root imports from `gui_do`; avoid internal module imports in consumer code.
5. Treat Tier 19 (`UiEngine`) as framework-internal.

Decision shortcuts:

- App setup: `HostApplicationConfig` + `bootstrap_host_application`.
- Lifecycle-safe runtime wiring: routed runtime specs + bind/shutdown lifecycle helpers.
- Data-heavy UI: virtualization and dataflow APIs before custom loops.
- Durable persistence: workspace persistence + snapshot migration APIs.
- Discoverable command UX: `ShortcutOverlaySpec` and command palette wiring.

[Back to Table of Contents](#table-of-contents)

### Appendix E: Architecture Templates

[Back to Table of Contents](#table-of-contents)

Template 1, small single-scene app:

- One scene, two to four features.
- Observable-driven UI state.
- Minimal action set and optional escape-to-exit runtime scene binding.

Template 2, multi-window workbench:

- Multiple scenes and presenter-backed windows.
- Scene task panel + focus toggle specs.
- Routed shortcut overlay and command palette integration.

Template 3, data-heavy analysis tool:

- `AsyncDataProvider` + `SortFilterProxySource` + virtualization core.
- Cancelable dataflow pipeline for transforms.
- Telemetry-enabled performance baselining.

Template 4, long-running workflow app:

- Cooperative scheduler-driven multi-step tasks.
- Progress via observables.
- Versioned snapshot persistence with migration.

[Back to Table of Contents](#table-of-contents)

### Appendix F: Specifications and Option Reference

[Back to Table of Contents](#table-of-contents)

This appendix summarizes the major spec families used across the manual. Each entry gives purpose, high-value options, and chapter cross-links.

#### Bootstrap and Host Specs

`HostApplicationBindingSpec`: high-level bootstrap declaration used by `build_host_application_config`.

- Purpose: compose host setup from bundle-style declarations.
- Key options: `display_size`, `window_title`, `initial_scene_name`, `scene_bundle_entries`, `feature_entries`, `feature_window_bundle_entries`, `action_entries`, `font_role_entries`, `cursor_entries`, `telemetry`, `palette_spec`, `target_fps`.
- Notes: prefer for large apps to centralize topology.
- Cross-links: 8.1, 8.9.

`HostApplicationConfig`: direct runtime config object.

- Purpose: lower-level explicit bootstrap configuration.
- Key options: `feature_specs`, `runtime_scene_specs`, `action_specs`, display/title/font/cursor/theme fields, persistence and telemetry fields.
- Notes: useful when generated config is not desired.
- Cross-links: 8.1, End-to-End reference.

`TelemetryConfig`: telemetry bootstrap toggle spec.

- Purpose: enable telemetry paths at startup.
- Key options: `enabled`.
- Cross-links: 8.16.

#### Feature and Lifecycle Specs

`FeatureSpec`: registers a host attribute and feature factory.

- Key options: `attr_name`, `factory`.
- Cross-links: 8.2.

`RuntimeSceneSpec`: scene startup behavior.

- Key options: `scene_name`, `pristine_asset`, `bind_escape_to_exit`, `prewarm`.
- Cross-links: 8.1, 8.9.

`RoutedRuntimeSpec`: declarative routed runtime bundle.

- Key options: scene scope, shortcut overlay settings, action/hotkey subscriptions, service/effect/store/operation declarations, higher-level runtime faculties.
- Notes: bind with `bind_routed_feature_lifecycle` and always teardown with `shutdown_routed_feature_lifecycle`.
- Cross-links: 8.2, 8.3, 8.4.

`RoutedFeatureLifecycleSpec`: lifecycle wrapper for routed runtime.

- Key options: `runtime_spec`.
- Cross-links: 8.2, 7.

#### Action, Input, and Overlay Specs

`ActionSpec` / `ActionBindingSpec`: named command declarations.

- Key options: `action_id`, `label`, `kind`, optional `target`, `category`, `key`.
- Cross-links: 8.3.

`ActionHotkeySpec`: bind action to key and handler.

- Key options: `action_name`, `handler`, optional `key`, `scene_name`.
- Cross-links: 8.3.

`ControlKeyBindingSpec`: key-to-control activation mapping.

- Key options: `key`, `control_attr`, optional `action_name`, `scene_name`.
- Cross-links: 8.3, 8.5.

`EventSubscriptionSpec`: declarative event bus subscription for feature runtime.

- Key options: event/topic binding fields (runtime-specific), handler target and scene scope fields.
- Cross-links: 8.3, 8.8.

`ShortcutOverlaySpec`: shortcut help overlay declaration.

- Key options: `toggle_action_name`, `toggle_key`, `manual_section_title`, `manual_shortcut_lines`, exclusion/include options.
- Cross-links: 8.8, Integration Recipe 1.

`NotificationSpec`: startup/bound notification center declaration.

- Key options: center/binding behavior fields and message metadata (runtime-specific).
- Cross-links: 8.8.

#### Window and Presentation Specs

`WindowSpec` and `AnchoredWindowSpec`: feature window declarations.

- `WindowSpec` key options: `key`, `feature_attribute_name`, toggle/action/task-panel labeling fields.
- `AnchoredWindowSpec` key options: `control_id`, `title`, `size`, `anchor`, `margin`, `use_frame_backdrop`.
- Cross-links: 8.9.

`FeatureWindowBundleBindingSpec`: feature+window+task panel bundle declaration.

- Key options: feature alias/class/presenter and task-panel wiring fields.
- Cross-links: 8.1, 8.9.

`WindowToggleBindingSpec`: declarative toggle behavior for registered windows.

- Key options: action and visibility wiring fields.
- Cross-links: 8.9.

`SceneTaskPanelSpec`, `TaskPanelButtonSpec`, `TaskPanelFocusToggleSpec`, `TaskPanelWindowToggleGroupSpec`, `TaskPanelSlotLayoutSpec`, `TaskPanelSceneNavButtonSpec`:

- Purpose: task panel structure, button declarations, focus coupling, and slot layout.
- Cross-links: 8.9, 8.7.

`SceneMenuStripSpec` and `SceneCommandPaletteSpec`:

- Purpose: optional scene menu and optional per-scene command palette activation.
- Contract: if not declared in specs, these facilities are absent for that scene.

`TabbedPresenterSpec` and `TabBuilderSpec`:

- Purpose: declarative tabbed presenter/window composition.
- Key options: tab ids/titles/builders, update routing integration.
- Cross-links: 8.9.

#### Accessibility and Theme Specs

`StaticAccessibilitySpec` and `AccessibilitySequenceSpec`:

- Purpose: static role/label annotations and navigation sequence declarations.
- Key options: control attribute references, semantic role/label fields, ordering.
- Cross-links: 8.7.

`FontRoleBindingSpec`, `CursorSpec`, `CursorBindingSpec`:

- Purpose: font role and cursor declarations at bootstrap.
- Key options: role names/sizes/family keys and cursor name/path/hotspot fields.
- Cross-links: 8.12.

#### Service, Reactive, and Operation Specs

`ServiceBindingSpec` / `ServiceConsumerSpec`:

- Purpose: declarative service publication and consumption in runtime scope.
- Key options: service key/provider alias and consumer binding fields.
- Cross-links: 8.2, 8.4.

`StoreSubscriptionSpec`, `StoreSelectorSpec`, `ObservableEffectSpec`, `SignalEffectSpec`:

- Purpose: declarative reactive wiring and effect ownership.
- Key options: source selector/effect callback/scene scope binding fields.
- Cross-links: 8.4.

`FeatureOperationSpec` and `FailurePolicySpec`:

- Purpose: operation orchestration and retry/timeout/failure publication.
- Key options: operation id/handler wiring and policy settings (retry count, timeout, publish mode).
- Cross-links: 8.2, 8.10, 8.14.

#### Higher-Level Runtime Faculty Specs

Dependency and policy:

- `FeatureDependencySpec`: startup/runtime dependency requirements.
- `RuntimePolicySpec`: admission control policy declaration.

Effect/event/durable pipelines:

- `EffectBindingSpec`: lifecycle-owned effect registration.
- `EventPipelineStageSpec`, `EventPipelineSpec`: staged event processing declarations.
- `DurableOperationBindingSpec`, `DurableOperationQueueSpec`, `DurableQueueRecord`: durable operation queue/recovery declarations.

Capabilities and projections:

- `CapabilityProviderSpec`, `CapabilityRequirementSpec`: capability contract negotiation.
- `ProjectionNodeSpec`, `ProjectionSpec`: incremental projection graphs.

Workflow/recompute/qos/health/replay/replacement:

- `WorkflowStepSpec`, `WorkflowSpec`
- `RecomputeNodeSpec`
- `QoSPolicySpec`
- `HealthProbeSpec`
- `ReplaySpec`
- `ReplacePolicySpec`

Cross-links: Conceptual Foundations, 8.2, 8.10, 8.16.

#### Persistence and Migration Specs

`MigrationStepSpec`, `MigrationTargetSpec`, `ContractMigrationSpec`:

- Purpose: declarative migration/runtime contract transitions.
- Cross-links: 8.11, Migration chapter.

Snapshot migration types (`SchemaVersion`, `VersionedSnapshot`, `MigrationStep`, `MigrationRegistry`, `SnapshotMigrator`) are not `*Spec` classes but are the implementation path for versioned restore.

#### Selection Notes

Use Tier 1 spec families first. Descend into Tier 18 helpers and higher-order faculties only when defaults cannot represent your requirement. Keep all spec-created resources lifecycle-owned so setup and teardown remain symmetric.

[Back to Table of Contents](#table-of-contents)
