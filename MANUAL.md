# gui_do Manual: Theory, Practice, and System Reference

This manual is the primary learning and reference document for gui_do. It is written for developers who are new to the framework, developers who are actively building production features, and maintainers who need to validate contract alignment over time. The document is organized so you can start with conceptual models, move into practical implementation flows, and then use the systems chapters and appendices as day-to-day operational reference.

## Table of Contents
[Back to Table of Contents](#table-of-contents)

- [Title and Purpose](#gui_do-manual-theory-practice-and-system-reference)
- [Table of Contents](#table-of-contents)
- [How to Use This Manual](#how-to-use-this-manual)
  - [Learn Build Maintain Modes](#learn-build-maintain-modes)
  - [Reading Paths](#reading-paths)
  - [Tri-Lens Markers](#tri-lens-markers)
  - [Contract Alignment](#contract-alignment)
  - [Known Non-Goals](#known-non-goals)
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
  - [Maintainer Diff Checklist](#maintainer-diff-checklist)
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
  - [Appendix F: Specifications and Option Reference](#appendix-f-specifications-and-option-reference)

## How to Use This Manual
[Back to Table of Contents](#table-of-contents)

This manual is designed to support three practical modes of work: learning the framework, building with the framework, and maintaining framework-aligned code over time. You can read it front to back as a curriculum, or you can enter through the system chapter that matches your immediate task. The ordering is intentional: theory first, practical build path second, and detailed systems reference after the mental model is established.

### Learn Build Maintain Modes

Use Learn mode when you are new to gui_do and need a durable mental model rather than isolated snippets. In this mode, focus first on Conceptual Foundations, then Quickstart, then Architecture and Core Workflow, and only then branch into specific system chapters. The key outcome is understanding why data-driven specs and lifecycle phases exist so you can reason about behavior before writing code.

Use Build mode when you are actively implementing features. In this mode, keep Quickstart and Core Workflow open, then jump between Main Systems Reference chapters as needed. The practical pattern is to select Tier 1 entry points first, verify behavior against contracts, and only move down to lower-level APIs when the higher-tier APIs do not fit your use case.

Use Maintain mode when you are updating docs, reviewing API drift, or validating changes across contracts, demos, and tests. In this mode, rely heavily on the Testing chapter checklist and Appendix quick indexes. The goal is to keep guidance current with code behavior and avoid stale symbols, stale assumptions, or chapter-level omissions.

### Reading Paths

Beginner path: read Sections 3, 4, 5, 6, and 7 in order, then review system chapters 8.1, 8.2, 8.3, 8.4, 8.5, and 8.6 before exploring the rest of Chapter 8. This sequence builds a complete mental model before introducing specialized facilities.

Intermediate path: skim Section 4 to refresh core principles, then read Sections 7 and 8 in the order of your current feature work. Use Section 9 for composition recipes and Section 11 for verification discipline as you finalize implementation details.

Maintainer path: start at Section 11 (Testing, Diagnostics, and Reliability), run the Maintainer Diff Checklist, then validate chapter references against Sections 8 and 15. Use Appendix D and D.1 as index and classification checkpoints for root export consistency.

### Tri-Lens Markers

This manual uses a tri-lens framing throughout each major area so readers can translate between intent, implementation, and operations. The three lenses are Theory, Practice, and Contracts. Theory explains design rationale and boundaries. Practice explains typical implementation flow and examples. Contracts identify normative behavior that must align with specs and tests.

When sections are expanded by later pipeline steps, each chapter should preserve this lens behavior explicitly: concept explanation, practical usage guidance, and contract-sensitive notes where behavior is constrained by docs or tests. This keeps the document useful for both builders and maintainers without forcing separate manuals.

### Contract Alignment

When behavior is normative, the contract documents in docs/ are authoritative reference points for wording and guarantees. In particular, API-surface rules and tier guidance are defined in docs/public_api_spec.md, runtime guarantees and observable report fields are defined in docs/runtime_operating_contracts.md, and architecture boundaries are defined in docs/architecture_boundary_spec.md. If narrative guidance and contract docs diverge, contract docs must be treated as the source to reconcile against current code and tests.

The maintainer workflow should verify that examples in this manual remain consistent with root exports in `gui_do/__init__.py`, contract tests under `tests/`, and representative usage patterns in `demo_features/`. This alignment practice prevents drift between conceptual guidance and executable behavior.

### Known Non-Goals

- gui_do is not intended to be a no-code visual designer.
- gui_do does not promise browser-style HTML/CSS compatibility semantics.
- gui_do does not replace domain modeling; it provides UI/runtime infrastructure.
- gui_do does not treat internal low-level infrastructure tiers as first-choice application APIs.

## Conceptual Foundations (Theory)
[Back to Table of Contents](#table-of-contents)

This chapter establishes the mental models that make the rest of gui_do predictable. If you skip this section and jump directly to API usage, you can still produce working code, but you are much more likely to write fragile wiring, duplicate lifecycle logic, or over-couple features that should stay independent. The framework is intentionally organized around declarative structure plus imperative behavior. Once that split is clear, design and maintenance decisions become straightforward.

### Data-Driven Design
[Back to Table of Contents](#table-of-contents)

Data-driven design in gui_do means that application structure is represented as data first, then executed by runtime systems second. Instead of writing long sequences of imperative setup calls that directly manipulate registries, focus scopes, and window managers, you describe what exists and how pieces relate using specs and binding descriptors. The runtime interprets that specification graph and performs wiring in a deterministic order. This is not merely a stylistic preference: it is the core reason the framework can keep setup consistent across growing applications.

The practical entry path for this model is a spec pipeline centered on `HostApplicationBindingSpec`, `build_host_application_config`, and `bootstrap_host_application`. You gather scene, feature, action, window, and optional runtime descriptors into a coherent binding model, then run a build phase that resolves references and validates assumptions before execution starts. The resulting `HostApplicationConfig` is the concrete artifact of the description phase. Bootstrapping then consumes that artifact to initialize runtime state. This explicit two-step workflow separates "what should exist" from "start executing now," which makes failure modes easier to reason about and easier to test.

Compared to imperative wiring, this removes a large amount of manual glue code. In an imperative setup, adding a key shortcut often means touching event dispatch branches, registry calls, teardown cleanup, and scene activation logic. In gui_do's data-driven path, the same intent is represented by adding an `ActionSpec` and related scene/runtime bindings. Registration, routing, and teardown behavior become responsibilities of the framework pipeline rather than responsibilities repeated in each application. You still retain imperative control where it matters, but wiring concerns move out of feature code.

This design also insulates bootstrap logic from internal package reorganization. If a feature package splits one module into multiple files, introduces a presenter companion, or separates logic from UI into additional internals, bootstrap code does not need to change as long as package-level exports remain stable through each feature package surface. In practice, this means `__init__.py` remains the contractual import boundary while internal files remain free to evolve. The manual's recommended feature organization under demo_features follows this rule deliberately: one folder per feature package, a package-root export surface, and internal modules segmented by concern.

Testability is a direct consequence of representing structure as data. Specs can be composed in unit tests without a running event loop or display. Configuration assembly can be asserted independently from runtime stepping. Mock hosts can validate feature construction contracts without pulling in full scene execution. Because structure is explicit, tests can focus on deterministic output of builders and validators before any interactive behavior is exercised.

Specs also serve as a natural serialization and evolution boundary. A named dataclass spec can add optional fields over time with minimal breakage risk and higher readability than positional configuration APIs. Builders can apply defaults, verify required invariants, and keep signatures stable while extending behavior. This gives maintainers a disciplined way to grow capabilities without forcing broad rewrites across consumer code.

The boundary of data-driven design in gui_do is precise: structural wiring is declarative, while feature behavior remains imperative Python. Scene composition, action mapping, runtime binding, and presentation registration are configured through specs. Inside a feature, logic still lives in methods like `build`, `bind_runtime`, `handle_event`, `on_update`, and `draw`. That split is intentional. You declare architecture with data, then implement behavior with code.

```python
from gui_do import HostApplicationBindingSpec, build_host_application_config

binding = HostApplicationBindingSpec(
  display_size=(1280, 720),
  window_title="Data-Driven Example",
  fonts={"default": {"file": None, "size": 16}},
  initial_scene_name="main",
)
config = build_host_application_config(binding)
```

See [Appendix F: Specifications and Option Reference](#appendix-f-specifications-and-option-reference).

### Reactive Data and Observable State
[Back to Table of Contents](#table-of-contents)

Reactive state in gui_do means producers of state do not need to know all current or future consumers. A source value changes once, and every subscriber is notified through the observable contract. In an imperative GUI model, that same update would require manually calling each dependent control or presenter. Reactive flow removes that fan-out burden from business logic and makes update propagation consistent.

The core primitives are `ObservableValue`, `ObservableList`, and `ObservableDict`, with collection deltas represented by `CollectionChange` and `ChangeKind`. `ObservableValue` models single-value state and emits to callbacks registered via subscription. Collection observables preserve the same principle while describing structural mutations such as insertions, removals, and updates. These primitives should represent most UI-driving mutable state because they make change semantics explicit and inspectable.

For multi-step changes, `reactive_batch` and `is_batching` are important operational tools. If several related observable mutations happen in one logical transaction, batching avoids noisy intermediate notifications and prevents controls from re-rendering repeatedly with transient values. You use batching when partial intermediate states are not meaningful to consumers and when you want one coherent post-change notification boundary.

Derived state is handled either through `ComputedValue` or explicit subscription pipelines. A `ComputedValue` is appropriate when a value is purely a function of one or more source observables and should remain declaratively derived. Manual subscribe-and-write pipelines are still valid when derivation requires side effects, cross-system orchestration, or lifecycle-aware guards. The distinction is practical: prefer computed derivation for pure projections, and explicit subscriptions for effectful coordination.

Subscription lifecycle discipline is mandatory. The safe default is to register subscriptions in `bind_runtime`, when sibling features and control trees are fully available, and to clean them in `shutdown_runtime` or equivalent teardown paths. Subscriptions retained past feature lifetime keep dead objects reachable and can trigger callbacks after scene transitions. That creates memory pressure and hard-to-debug phantom updates.

Control binding follows the same contract-oriented pattern. Controls typically accept static values or observables; when given an observable, they subscribe internally and refresh presentation when values change. Feature code should mutate source observables rather than manually pushing presentation updates into controls. That preserves separation between domain state ownership and UI rendering mechanisms.

Cross-feature sharing should favor observables over direct feature-to-feature mutation. One feature owns an observable and exposes it as part of its public behavior surface; consuming features subscribe during runtime binding. This keeps dependencies directional and loose. Producers stay unaware of subscribers, and subscribers depend on a state contract instead of implementation details.

Common reactive anti-patterns are predictable and avoidable. Polling values in `on_update` instead of subscribing wastes frame budget and introduces avoidable latency. Subscribing in `build` before runtime topology is complete can produce early callbacks against partially initialized controls. Failing to unsubscribe leaks references and event traffic. Passing plain mutable objects between features without observable wrappers breaks automatic propagation and often leads to ad hoc manual refresh code.

### Feature Composition and Lifecycles
[Back to Table of Contents](#table-of-contents)

A feature is the primary unit of behavior composition in gui_do. A feature carries a name, optional scene ownership, declared host dependencies through `HOST_REQUIREMENTS`, lifecycle hooks, and message/logic binding affordances. The framework's feature manager orchestrates registration, runtime binding, updates, and teardown so each feature can focus on its own responsibilities rather than manual orchestration of peers.

Feature classes represent different composition intents. `DirectFeature` is ideal for direct frame rendering tasks that do not need control-tree participation. `Feature` is the standard UI composition unit that builds controls and participates in routed interaction. `LogicFeature` isolates non-visual domain workflows, background coordination, and shared state publication. `RoutedFeature` extends the standard model with action-routing integration for message and route target handling patterns. Choosing correctly at design time reduces accidental coupling and keeps responsibilities clear.

Lifecycle timing is the operational backbone. `build(host)` runs to create durable scene structure such as controls and static attachments. `bind_runtime(host)` runs after feature construction to wire subscriptions, callbacks, and cross-feature coordination when full runtime context is available. `handle_event(host, event)` processes routed events and returns consumption state. `on_update(host)` executes per-frame incremental logic and should remain lightweight. `draw(host, surface, theme)` supports custom rendering passes outside the control tree. `shutdown_runtime(host)` is the corresponding cleanup phase for runtime bindings and subscriptions.

`HOST_REQUIREMENTS` makes dependency needs explicit and machine-checkable. A feature can declare per-method host attributes it requires, and startup validation can surface missing bindings early instead of failing deep in execution. This protocol serves as declarative dependency documentation and practical guardrail. It also enables cleaner testing because host doubles can be shaped against explicit requirements.

Feature coordination should avoid direct object graph coupling wherever possible. `FeatureMessage` pathways provide named payload delivery so senders and receivers coordinate by contract rather than by concrete references. This supports independent evolution of feature internals and clearer boundaries in multi-scene applications.

Scene assignment governs activation boundaries. Each feature belongs to a specific scene or a global context. During scene transitions, departing scene features are no longer updated or event-routed, and arriving scene features are built/bound in the correct order. This lifecycle isolation prevents stale state interactions across scene boundaries and improves teardown correctness.

The project's recommended package layout, demonstrated under demo_features, reinforces these lifecycle and boundary principles. A feature package should expose only its public surface from package `__init__.py`, while internal modules separate lifecycle host logic, presenter concerns, and spec declarations. Cross-feature imports should target package roots, not internal module paths, preserving refactor freedom.

Three composition patterns recur and scale well. The logic plus presentation split keeps compute-heavy or domain-oriented work in `LogicFeature` while a UI feature binds observables for rendering. Presenter-backed composition keeps layout construction in `WindowPresenter` subclasses while feature classes focus on lifecycle and routing. Background workflow composition uses scheduling primitives such as cooperative scheduling in logic features, then publishes progress and results through observables consumed by UI features. All three patterns produce clearer tests, cleaner boundaries, and easier long-term maintenance.

## Quickstart Path (Practice)
[Back to Table of Contents](#table-of-contents)

This quickstart is structured to get you from a clean clone to a working, spec-driven application with one reactive feature and one routed action. The flow intentionally mirrors the framework model: verify the environment, declare host configuration data, add a feature with lifecycle-safe binding, add scene/action policy, then execute the runtime loop.

### Step 1: Install and Verify

Install the package in editable mode and verify root export contracts before writing new app code.

```bash
python -m pip install -e . --no-deps
python -m pytest -q tests/test_public_api_exports.py
```

This repository expects pygame and numpy to be available in your environment. numpy is used internally by pixel-buffer operations (for example via `PixelArray` integration points), so a missing dependency can produce runtime failures that appear unrelated to your feature code.

### Step 2: Create a Minimal Host

The minimal host can construct `HostApplicationConfig` directly with current required fields, then pass that config to `bootstrap_host_application`. The field names below are the authoritative constructor names used by the runtime model.

```python
from __future__ import annotations

from pygame import Rect

from gui_do import (
  ActionSpec,
  Feature,
  FeatureSpec,
  HostApplicationConfig,
  RuntimeSceneSpec,
  SceneSetupSpec,
  ObservableValue,
  LabelControl,
  bootstrap_host_application,
)


class MinimalFeature(Feature):
  HOST_REQUIREMENTS = {
    "build": ("app",),
    "bind_runtime": (),
  }

  def __init__(self) -> None:
    super().__init__("minimal_feature", scene_name="main")
    self._title_text = ObservableValue("hello gui_do")
    self._title_label = None
    self._unsubscribe = None

  def build(self, host) -> None:
    self._title_label = host.app.add(
      LabelControl("title", Rect(32, 32, 360, 30), self._title_text.value),
      scene_name="main",
    )

  def bind_runtime(self, host) -> None:
    def _on_change(change) -> None:
      if self._title_label is not None:
        self._title_label.set_text(str(change.new_value))

    self._unsubscribe = self._title_text.subscribe(_on_change)

  def shutdown_runtime(self, host) -> None:
    if callable(self._unsubscribe):
      self._unsubscribe()
      self._unsubscribe = None


class MinimalHost:
  def __init__(self) -> None:
    self._config = HostApplicationConfig(
      display_size=(1280, 720),
      window_title="minimal gui_do app",
      fonts={"default": {"file": None, "size": 16}},
      font_role_specs=(),
      cursors=(),
      scene_specs=(SceneSetupSpec("main"),),
      feature_specs=(FeatureSpec("_feature", MinimalFeature),),
      window_specs=(),
      runtime_scene_specs=(
        RuntimeSceneSpec(
          scene_name="main",
          bind_escape_to_exit=True,
          prewarm=False,
        ),
      ),
      action_specs=(
        ActionSpec(
          action_id="exit",
          label="Exit",
          kind="exit",
          category="File",
        ),
      ),
      static_accessibility_specs=(),
      initial_scene_name="main",
    )
    self.app = bootstrap_host_application(self, self._config)

  def run(self) -> int:
    return int(self.app.run_entrypoint(target_fps=120))
```

### Step 3: Add a Feature with Observable State

The minimal feature above demonstrates the intended lifecycle boundary. Initialize local observable state in `__init__`, create controls in `build`, connect subscriptions in `bind_runtime`, and tear subscriptions down in `shutdown_runtime`. This guarantees controls exist before callbacks run, and guarantees callbacks stop once the feature is deactivated or removed.

### Step 4: Add an Action and Runtime Scene Policy

Use `ActionSpec` to declare behavior and `RuntimeSceneSpec` to declare scene policy. `bind_escape_to_exit=True` on the active scene spec is the simplest way to enforce ESC-to-exit behavior without ad hoc keyboard branch logic in feature handlers.

### Step 5: Run Loop

Execution should flow through a host-owned app instance returned by `bootstrap_host_application`, then call `run_entrypoint` at a target FPS. Keeping run-loop entry centralized in the host class helps testing and allows controlled startup/teardown in integration tests.

### Guided Build Track (Beginner)

Milestone A: app boots to a single scene with no errors.
Milestone B: one feature creates one visible control.
Milestone C: one observable updates one control reactively.
Milestone D: one action and one hotkey trigger expected behavior.
Milestone E: one overlay and one toast route without input leakage.
Milestone F: workspace save/load roundtrip succeeds.

Beginner confidence checklist:
- you can explain where `build` ends and `bind_runtime` begins.
- you can add and remove one feature through specs only.
- you can trace one keypress through routing to action execution.

### Quickstart Failure Modes

Feature never appears: verify that the feature is present in `feature_specs` and the feature's `scene_name` matches a configured scene in `scene_specs`.

Hotkey does nothing: verify both the action descriptor and the input binding scope. In scene-scoped setups, a valid action id without matching route scope can still appear silent.

Overlay blocks unexpected keys: verify overlay key handling policy, including `consume_unhandled_keys` and dismissal behavior. Overlays are intentionally given priority in key routing.

State updates but UI does not: verify the observable subscription is attached in `bind_runtime` and is not disposed too early by teardown paths.

## Architecture and Runtime Model
[Back to Table of Contents](#table-of-contents)

The architecture is split between reusable framework systems and consumer composition code. This boundary is central to package reusability and documentation stability. In this repository, framework runtime code lives under gui_do, while consumer-facing integration and demonstrations live under demo_features plus the application entry module.

### Boundary Model: Framework vs Consumer

The framework package contains runtime, controls, event processing, layout, state, persistence, and supporting systems intended for reuse. Consumer code composes those systems into an application through declarative specs and feature implementations. The contract is strict: framework code must not import demo feature packages, and consumer entrypoints should import from root `gui_do` exports rather than internal module paths. This rule is enforced by boundary contract tests, including `tests/test_boundary_contracts.py`.

### Tiered Public API Model

The root package is organized by tiers to communicate recommended abstraction order. Tier 1 is the primary path for new applications and contains lifecycle abstractions plus data-driven runtime specs and bootstrap functions. Tier 2 through Tier 7 cover core runtime systems: application/scene management, state and observables, events and actions, scheduling, theme/font management, and telemetry/diagnostics. Tier 8 and above expose progressively more specialized systems, including layout engines, overlays, forms, persistence helpers, controls, graphics, introspection, and advanced runtime composition helpers.

Tier numbering is guidance, not prohibition, but it is meaningful guidance. If two tiers can solve the same need, prefer the lower-numbered tier first because it usually provides a more stable and less error-prone abstraction surface. Higher tiers may expose more control, but they also typically demand stronger lifecycle and coupling discipline from application code.

### Runtime Guarantees

The runtime operating contracts define specific guarantees that shape architecture decisions. Raw input is normalized to `GuiEvent` before app-level dispatch. Scene-contained runtime work executes with scene isolation. Window focus candidate ordering is deterministic and sorted by `control_id`. Scheduler dispatch budget is clamped to fixed bounds: fraction 0.12, floor 0.5 ms, and ceiling 4.0 ms. Workspace restore skips missing settings keys rather than aborting the full restore process.

These guarantees matter because they let application developers treat routing and scheduling as stable infrastructure. Deterministic candidate ordering avoids intermittent focus behavior. Budget clamping prevents scheduler starvation and unbounded frame consumption. Restore skip behavior prevents brittle startup failures when configuration evolves.

### Event Pipeline

`GuiApplication.process_event` follows a strict flow. First, raw input is normalized via the event manager to `GuiEvent`. Quit events are handled immediately. Shared input state is updated, then logical pointer state is reconciled using lock areas, pointer-capture constraints, and relative motion rules. Pointer-bearing events are logicalized while preserving raw coordinate context. Toasts and overlays receive high-priority routing where applicable. Keyboard routing then passes through overlay interception and keyboard manager policy. Feature direct handlers, feature handlers, scene dispatch, and fallthrough handlers run in defined order. At each routing stage, `propagation_stopped` and `default_prevented` are respected as hard stop signals.

The practical takeaway is that application code should rely on routing stages instead of bypassing them. If a feature wants predictable key handling, it should register through the supported action/input pathways, not inject ad hoc ordering assumptions.

```python
import pygame

from gui_do import ActionSpec, ActionHotkeySpec

actions = (
  ActionSpec(action_id="save", label="Save", kind="palette_open", category="File"),
)
hotkeys = (
  ActionHotkeySpec(action_name="save", key=pygame.K_s, ctrl=True, scene_name="main"),
)
```

See [Appendix F: Specifications and Option Reference](#appendix-f-specifications-and-option-reference).

### Known Non-Goals

- OS-native widget parity across all platforms.
- Replacing domain-layer architecture decisions for business logic.
- Exposing infrastructure-oriented tiers as beginner entry points.
- Treating star-import behavior as part of public API compatibility.

## Core Workflow: Build, Bind, Route, Update, Draw
[Back to Table of Contents](#table-of-contents)

The build-bind-route-update-draw model is the primary programming loop for gui_do features. It gives each responsibility a clear phase boundary, which is the main protection against hidden coupling and lifecycle races.

### Phase Reference

Build phase establishes static scene structure. Create controls, initialize local observables, and register durable structural nodes in `build`. Invariant: do not attach runtime subscriptions or cross-feature dependencies that assume sibling readiness in this phase.

Bind runtime phase attaches host-dependent wiring. In `bind_runtime`, all sibling features are already built and scene controls are available, so this is where subscriptions, action registrations, inter-feature observable bindings, and callback wiring should be attached. Invariant: runtime-sensitive connections belong here, not in build.

Route phase consumes events and messages through declared handlers and routing policy. This includes feature event handlers, action routing, and message-based coordination where enabled. Invariant: routing should follow the framework's declared dispatch channels and stop-signal semantics.

Update phase executes frame-based logic and scheduled progression. `on_update` should keep per-frame work small, defer expensive work to schedulers or staged systems, and publish resulting state through observables.

Draw phase handles custom rendering paths that controls cannot express. Use `draw` for specialized visuals while keeping state mutation in earlier phases where possible.

### Message and Logic Coordination

`FeatureMessage` is the preferred loose-coupling channel for targeted feature communication. A sender publishes a message contract; receivers react without requiring direct object graph references. This helps keep features independently testable and easier to replace.

`LogicFeature` is a strong coordination hub for shared, non-visual behavior. It can own longer-running workflows, expose reactive state, and issue messages while UI-facing features stay focused on interaction and presentation.

Use observable shared state when consumers need ongoing data synchronization. Use messages when the interaction is event-like, discrete, and contract-oriented. Many robust compositions use both: observables for state continuity, messages for transitions and intents.

### When to Use Routed Runtime Specs

`RoutedRuntimeSpec` and `RoutedFeatureLifecycleSpec` reduce repetitive lifecycle boilerplate when a feature needs structured action/hotkey wiring, shortcut overlays, task-panel focus toggles, or lifecycle-managed event subscriptions. They centralize declaration while the runtime handles bind/unbind behavior.

`bind_routed_feature_lifecycle` is the runtime entry for attaching routed feature policy at bind time, while `shutdown_routed_feature_lifecycle` is the matching teardown path that releases those attachments. Together they provide deterministic setup and cleanup for routed composition without requiring each feature to duplicate the same wiring code.

```python
from gui_do import RoutedRuntimeSpec, RoutedFeatureLifecycleSpec

runtime_spec = RoutedRuntimeSpec(scene_name="main")
lifecycle_spec = RoutedFeatureLifecycleSpec(runtime_spec=runtime_spec)
```

See [Appendix F: Specifications and Option Reference](#appendix-f-specifications-and-option-reference).

## Main Systems Reference
[Back to Table of Contents](#table-of-contents)

### 8.1 Application Bootstrap and Host Configuration
[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Application bootstrap in gui_do exists to turn a declarative description into a running application without ad hoc wiring code spread across entrypoints. `HostApplicationConfig` is the concrete runtime input model. `bootstrap_host_application` is the realization step that attaches the configured runtime graph to a host object, creates the `GuiApplication`, registers features and scene bundles, and prepares action and window composition.

The design intent is deterministic startup. You should be able to inspect one config object and answer what scenes exist, which features are present, what actions are routable, and which runtime scene policies apply. This helps debugging, testability, and migration safety because startup behavior is explicit instead of hidden across side-effecting setup functions.

#### Mental model and lifecycle placement

Think of the host as a plain object receiving runtime capabilities. Before bootstrap, it is just your application container. After `bootstrap_host_application(host, config)`, it has a fully initialized `host.app` and any configured feature attributes/presentation attachments. This is lifecycle phase zero: it runs before per-feature `build` and `bind_runtime` flow and sets the operating context all other systems rely on.

In direct-config mode, you populate `HostApplicationConfig` yourself. In builder mode, you declare `HostApplicationBindingSpec` plus binding entries, then call `build_host_application_config` to resolve that higher-level declaration into runtime config data.

#### Primary public APIs and key types

Key Tier 1 and Tier 2 names for this chapter include: `HostApplicationConfig`, `HostApplicationBindingSpec`, `bootstrap_host_application`, `build_host_application_config`, `FeatureSpec`, `WindowSpec`, `RuntimeSceneSpec`, `SceneSetupSpec`, `ActionSpec`, `SceneBundleBindingSpec`, `FeatureWindowBundleBindingSpec`, `ActionBindingSpec`, `FontRoleBindingSpec`, `CursorBindingSpec`, `PaletteBindingSpec`, `TelemetryConfig`, `build_feature_specs`, `build_feature_window_bundle_specs`, `build_scene_setup_specs`, `build_runtime_scene_specs`, `build_action_specs`, `build_scene_bundle_specs`, `GuiApplication`, `create_display`, `SceneTransitionManager`, `SceneTransitionStyle`, and `apply_scene_setup_specs`.

#### Typical usage flow

1. Choose direct config or binding-spec builder style.
2. Define scenes and initial scene selection.
3. Register features and optional feature-window bundles.
4. Add action specs and optional command palette bindings.
5. Configure runtime scene policies (for example prewarm and escape behavior).
6. Build config and call `bootstrap_host_application`.
7. Enter `run_entrypoint` through your host/application wrapper.

#### Minimal example

```python
from gui_do import (
  HostApplicationConfig,
  SceneSetupSpec,
  RuntimeSceneSpec,
  bootstrap_host_application,
)


class Host:
  pass


host = Host()
config = HostApplicationConfig(
  display_size=(1280, 720),
  window_title="Bootstrap Example",
  fonts={"default": {"file": None, "size": 16}},
  font_role_specs=(),
  cursors=(),
  scene_specs=(SceneSetupSpec("main"),),
  feature_specs=(),
  window_specs=(),
  runtime_scene_specs=(RuntimeSceneSpec(scene_name="main", bind_escape_to_exit=True),),
  action_specs=(),
  static_accessibility_specs=(),
  initial_scene_name="main",
)
app = bootstrap_host_application(host, config)
app.run_entrypoint(target_fps=120)
```

#### Advanced pattern(s)

For multi-scene applications, use `HostApplicationBindingSpec` with `SceneBundleBindingSpec` and `FeatureWindowBundleBindingSpec` entries, then call `build_host_application_config`. This keeps scene/window/action linkage declarative and lets builders generate coherent config with one deterministic resolution pass.

Another advanced composition is pairing palette binding (`PaletteBindingSpec`) with scene/window bundles so command surfaces remain synchronized with scene and window presentation metadata.

#### Common mistakes and anti-patterns

- Mutating runtime host attributes after bootstrap in ways that bypass declared config contracts.
- Declaring features whose `scene_name` has no corresponding scene declaration.
- Omitting or mismatching `initial_scene_name`, resulting in confusing startup behavior.
- Mixing direct and builder-generated config fragments without validating resulting tuples.

#### Cross-links to related systems

See 8.2 for feature lifecycle timing, 8.3 for action/input routing, 8.9 for scene/window presentation patterns, and 8.11 for workspace/session persistence behavior.

See [Appendix F: Specifications and Option Reference](#appendix-f-specifications-and-option-reference).

[Back to Table of Contents](#table-of-contents)

### 8.2 Feature Lifecycle and Feature Types
[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Features are gui_do's unit of behavior composition. They isolate concerns, expose lifecycle hooks, and declare host dependencies through `HOST_REQUIREMENTS`. This gives the framework a stable way to orchestrate many independent behavior modules without forcing direct references between modules.

The framework offers multiple feature types because rendering and coordination needs differ. `Feature` is the general interactive type, `DirectFeature` is optimized for direct frame drawing, `LogicFeature` isolates non-visual behavior, and `RoutedFeature` integrates route-driven action semantics.

#### Mental model and lifecycle placement

Feature lifecycle is ordered and intentional. Use `build` for structural creation, `bind_runtime` for runtime wiring, `handle_event` for event consumption, `on_update` for per-frame state changes, and `draw` for custom rendering passes. `shutdown_runtime` is where runtime-bound subscriptions and handlers are released.

Subscription lifecycle placement is especially important for memory safety. Register subscriptions in `bind_runtime`, when all sibling features and controls exist, and always clean them in `shutdown_runtime`. Registering too early or cleaning too late can produce callbacks into stale objects after scene transitions.

#### Primary public APIs and key types

Primary names: `Feature`, `DirectFeature`, `LogicFeature`, `RoutedFeature`, `FeatureMessage`, `FeatureManager`, `FeatureSpec`, `RoutedRuntimeSpec`, `RoutedFeatureLifecycleSpec`, `register_routed_feature_companions`, `bind_routed_feature_lifecycle`, and `shutdown_routed_feature_lifecycle`.

#### Typical usage flow

1. Choose the correct feature base type.
2. Declare `HOST_REQUIREMENTS` for each lifecycle phase used.
3. Build controls or non-visual structures in `build`.
4. Attach subscriptions and cross-feature bindings in `bind_runtime`.
5. Handle routed events and frame updates in dedicated hooks.
6. Unsubscribe and unbind runtime resources in `shutdown_runtime`.
7. Register the feature via `FeatureSpec` in host config.

#### Minimal example

```python
from pygame import Rect
from gui_do import Feature, ObservableValue, LabelControl


class CounterFeature(Feature):
  HOST_REQUIREMENTS = {"build": ("app",), "bind_runtime": ()}

  def __init__(self) -> None:
    super().__init__("counter", scene_name="main")
    self.count = ObservableValue(0)
    self.label = None
    self._unsubscribe = None

  def build(self, host) -> None:
    self.label = host.app.add(LabelControl("counter_label", Rect(16, 16, 180, 28), "0"), scene_name="main")

  def bind_runtime(self, host) -> None:
    self._unsubscribe = self.count.subscribe(lambda change: self.label.set_text(str(change.new_value)))

  def shutdown_runtime(self, host) -> None:
    if callable(self._unsubscribe):
      self._unsubscribe()
      self._unsubscribe = None
```

#### Advanced pattern(s)

A robust composition pattern is logic/presentation split: a `LogicFeature` owns domain state and periodic computation, while a companion `RoutedFeature` handles routed actions and view updates. Use `register_routed_feature_companions` to keep the association declarative.

For route-heavy features, define a `RoutedFeatureLifecycleSpec` and bind it with `bind_routed_feature_lifecycle` so action/hotkey/event subscription setup and cleanup happen consistently.

#### Common mistakes and anti-patterns

- Subscribing in `build` before runtime topology is stable.
- Forgetting `shutdown_runtime` cleanup for subscriptions and routed bindings.
- Overusing `draw` for logic updates that belong in `on_update`.
- Direct feature-to-feature object references where messages or observables are cleaner.
- Registering routed lifecycle helpers without symmetric shutdown, causing lingering handlers.

#### Cross-links to related systems

See 8.1 for bootstrap registration, 8.3 for routing/action flow, 8.4 for observable lifecycle rules, and 8.10 for scheduling-driven feature updates.

[Back to Table of Contents](#table-of-contents)

### 8.3 Events, Actions, Input Mapping, and Routing
[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

This system converts raw input into predictable, composable behavior. `GuiEvent` provides canonical event shape. Actions and input bindings decouple physical input from application intent. Focus and scope models prevent ambiguous dispatch in multi-window and multi-scene contexts.

Without this layer, each feature would implement its own key/pointer dispatch semantics and conflict handling. With it, behavior is consistent and testable across the app.

#### Mental model and lifecycle placement

The routing model is pipeline-based: normalize to `GuiEvent`, resolve pointer and focus context, route overlays/toasts, process keyboard routing and action maps, then dispatch into feature and scene handlers. Routing sits between bootstrap and frame updates and is executed per event.

Lifecycle placement for subscriptions and event hookups follows the same safety rule as observables: register in `bind_runtime`, release in `shutdown_runtime`. Persistent event subscriptions that outlive scene activation are a primary source of memory leaks and phantom behavior.

#### Primary public APIs and key types

Key names include `EventType`, `EventPhase`, `GuiEvent`, `EventManager`, `EventBus`, `GestureRecognizer`, `EventRecorder`, `EventPlayback`, `RecordedEvent`, `InputSnapshot`, `Signal`, `SignalConnection`, `ActionManager`, `ActionContext`, `ActionMiddleware`, `ActionDescriptor`, `ActionRegistry`, `InputMap`, `InputBinding`, `KeyChordManager`, `KeyChord`, `ChordStep`, `FocusManager`, `FocusScope`, `FocusScopeManager`, `WindowFocusManager`, `FocusRing`, `ActionSpec`, `ActionHotkeySpec`, `ControlKeyBindingSpec`, and `EventSubscriptionSpec`.

Current `EventType` values are `PASS`, `QUIT`, `KEY_DOWN`, `KEY_UP`, `MOUSE_BUTTON_DOWN`, `MOUSE_BUTTON_UP`, `MOUSE_MOTION`, `MOUSE_WHEEL`, `TEXT_INPUT`, and `TEXT_EDITING`.

Important `GuiEvent` fields include `kind`, `type`, `key`, `pos`, `rel`, `raw_pos`, `raw_rel`, `button`, `wheel_x`, `wheel_y`, `mod`, `text`, `control_id`, `group`, `window`, `task_panel`, `task_id`, `error`, `source_event`, `phase`, `propagation_stopped`, and `default_prevented`.

#### Typical usage flow

1. Declare actions via `ActionSpec` entries in host config.
2. Register hotkeys/key bindings (`ActionHotkeySpec`, input map bindings, or routed runtime specs).
3. Implement action handlers on host/features.
4. Let normalized `GuiEvent` routing drive dispatch through focus/window/scene scope.
5. Respect stop/prevent flags when introducing custom handlers.

#### Minimal example

```python
from gui_do import ActionSpec, RuntimeSceneSpec, HostApplicationConfig

action_specs = (
  ActionSpec(action_id="exit", label="Exit", kind="exit", category="File"),
  ActionSpec(action_id="open_palette", label="Open Palette", kind="palette_open"),
)

runtime_scene_specs = (
  RuntimeSceneSpec(scene_name="main", bind_escape_to_exit=True),
)

# Insert into HostApplicationConfig(... action_specs=action_specs,
# runtime_scene_specs=runtime_scene_specs, ...)
```

#### Advanced pattern(s)

Use `InteractionStateMachine` (Tier 30) to model multi-phase interaction flows where pointer press, drag, and release transitions need guards and explicit phase state.

Use `EventRecorder` and `EventPlayback` to capture deterministic interaction traces for regression testing of event-heavy features.

#### Common mistakes and anti-patterns

- Handling raw pygame events directly in feature code instead of `GuiEvent` paths.
- Assuming global key routing when handlers are scene or window scoped.
- Ignoring `propagation_stopped` and `default_prevented` in custom dispatch logic.
- Registering event subscriptions without teardown, causing stale callbacks after scene exit.

#### Cross-links to related systems

See 8.2 for feature hook placement, 8.7 for focus/accessibility behavior, 8.8 for overlay routing precedence, and 8.16 for operational diagnostics.

[Back to Table of Contents](#table-of-contents)

### 8.4 State and Observables
[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

State and observables provide the reactive backbone of gui_do applications. They exist to decouple state mutation from UI update mechanics and to make cross-feature synchronization explicit. When state changes are represented through observable contracts, consumers update automatically without manual fan-out calls.

This reduces fragility as applications scale. Instead of hidden dependencies where one feature must remember to notify several others, updates flow from source state through subscriptions and bindings.

#### Mental model and lifecycle placement

Treat observable primitives as shared state channels and app-store abstractions as consistency layers. Initialize owning state early, then attach subscriptions in `bind_runtime` when dependent controls and features are present. Always release subscriptions in `shutdown_runtime` to prevent retained references and stale callbacks.

Subscription lifecycle is the key memory-safety boundary in this chapter. Registering persistent callbacks too early or cleaning them too late is a common source of leaks and phantom updates after scene transitions.

#### Primary public APIs and key types

Core names include `ObservableValue`, `ObservableList`, `ObservableDict`, `ChangeKind`, `CollectionChange`, `ComputedValue`, `PresentationModel`, `reactive_batch`, `is_batching`, `InvalidationTracker`, `CollectionViewQuery`, `CollectionView`, `Binding`, `BindingGroup`, `ObservableStream`, `SelectionModel`, `SelectionMode`, `AppStateStore`, `StateSelector`, and `StateTransaction`.

#### Typical usage flow

1. Create observable state in feature initialization.
2. Build controls in `build`.
3. Subscribe in `bind_runtime` and map change payloads to control updates.
4. Use `reactive_batch` for multi-field atomic-style updates.
5. Unsubscribe in `shutdown_runtime`.
6. Use `AppStateStore` selectors/transactions for broader shared-state scenarios.

#### Minimal example

```python
from gui_do import ObservableValue, reactive_batch

count = ObservableValue(0)
label = ObservableValue("count: 0")

unsubscribe = count.subscribe(lambda change: label.set(f"count: {change.new_value}"))

with reactive_batch():
  count.set(1)
  count.set(2)

unsubscribe()
```

#### Advanced pattern(s)

For multi-feature applications, use `AppStateStore` as a source-of-truth model and expose feature-specific slices through `StateSelector`. Apply `StateTransaction` for grouped updates that should be observed as one coherent mutation boundary.

When working with dynamic lists, pair `ObservableList` with `CollectionView` and `CollectionViewQuery` to keep sorted/filtered projections synchronized automatically instead of recomputing UI lists imperatively.

#### Common mistakes and anti-patterns

- Polling values every frame in `on_update` instead of subscribing to change events.
- Subscribing during `build` when dependent controls or siblings are not fully ready.
- Failing to unsubscribe during teardown, causing memory leaks and callbacks on dead controls.
- Sharing plain Python mutable objects across features instead of observable containers.
- Misusing batched updates by combining unrelated state changes in one batch, obscuring causality.

#### Cross-links to related systems

See 8.2 for lifecycle phase boundaries, 8.3 for event-to-state transition triggers, 8.13 for form/text reactive validation flows, and 8.14 for dataflow and async data integration.

[Back to Table of Contents](#table-of-contents)

### 8.5 Controls and Control Composition
[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Controls are reusable interface primitives that let features compose rich UI without rewriting rendering, hit-testing, stateful interaction plumbing, and accessibility semantics from scratch. They exist so application behavior can be expressed through lifecycle and data flow, while visual interaction scaffolding remains standardized and consistent.

Control composition is not only a convenience layer. It is a correctness layer. A coherent control tree gives the runtime one place to enforce focus order, route pointer intent, apply layout passes, and propagate invalidation.

#### Mental model and lifecycle placement

Each feature should own a root control subtree, usually a `PanelControl`, and build that subtree in `build`. Controls in one feature should not directly manipulate controls owned by another feature. Cross-feature coordination should happen through observables, actions, and messages.

Control creation belongs in `build`; runtime callbacks and subscriptions belong in `bind_runtime`. This separation prevents partially initialized controls from receiving callbacks and keeps teardown predictable.

#### Primary public APIs and key types

Tier 12 primary controls: `PanelControl`, `LabelControl`, `ButtonControl`, `ToggleControl`, `SliderControl`, `ScrollbarControl`, `CanvasControl`, `CanvasEventPacket`, `CanvasViewport`, `FrameControl`, `ImageControl`, `ArrowBoxControl`, `ButtonGroupControl`, `TabControl`, `TabItem`, and `DockWorkspacePanel`.

Tier 13 extended controls: `TextInputControl`, `TextAreaControl`, `RichLabelControl`, `DropdownControl`, `DropdownOption`, `ListViewControl`, `ListItem`, `OverlayPanelControl`, `DataGridControl`, `GridColumn`, `GridRow`, `TreeControl`, `TreeNode`, `SplitterControl`, `SpinnerControl`, `RangeSliderControl`, `ColorPickerControl`, `ScrollViewControl`, `ProgressBarControl`, `AnimatedImageControl`, `ErrorBoundary`, `WindowControl`, `TaskPanelControl`, `WindowPresenter`, `MenuBarControl`, `MenuEntry`, `SceneMenuStripControl`, `NotificationPanelControl`, `PropertyInspectorPanel`, `ToolbarControl`, `ToolbarItem`, `StatusBarControl`, `StatusSlot`, `ExpanderControl`, `DatePickerControl`, `TimePickerControl`, `BreadcrumbControl`, `BreadcrumbItem`, `SplitButtonControl`, `SplitButtonOption`, and `ChipInputControl`.

Higher-level control spec helpers in Tier 1: `ControlDefinition`, `build_specs_from_column_section`, `RowCellSpec`, `build_horizontal_row_specs`, and `build_multi_column_grid_specs`.

#### Typical usage flow

1. Create a feature root container in `build`.
2. Add child controls for display and interaction.
3. Apply layout ownership for the container region.
4. In `bind_runtime`, connect control callbacks and observable bindings.
5. Keep controls as presentation surfaces; keep canonical state in observables/store.

#### Minimal example

```python
from pygame import Rect
from gui_do import PanelControl, LabelControl, ButtonControl


def build(self, host) -> None:
  self.root = host.app.add(PanelControl("my_root", Rect(0, 0, 420, 320)), scene_name="main")
  self.status = self.root.add(LabelControl("status", Rect(12, 12, 220, 24), "Ready"))
  self.root.add(ButtonControl("run", Rect(12, 48, 120, 28), "Run", on_click=self._on_run))
```

#### Advanced pattern(s)

Use the presenter pattern for window content: subclass `WindowPresenter`, keep window-level control creation in presenter hooks (`on_create`, `on_show`, `on_resize`, `update`), and keep feature classes focused on lifecycle and routing. Instantiate presenters in feature build paths when window controls are created.

Use `ErrorBoundary` to isolate risky subtrees so a rendering/event exception in one panel does not fail the entire frame. Combine with telemetry to capture recurring subtree faults.

#### Common mistakes and anti-patterns

- Treating controls as authoritative state stores instead of reflecting observable state.
- Creating controls in update loops or ad hoc callback paths outside lifecycle intent.
- Holding direct references to sibling-feature controls (tight coupling and lifecycle hazards).
- Forgetting teardown for dynamically created presenter controls on window detach/hide.

#### Cross-links to related systems

See 8.2 for lifecycle ownership, 8.6 for layout orchestration, 8.7 for focus and accessibility semantics, and 8.9 for scene/window presentation composition.

[Back to Table of Contents](#table-of-contents)

### 8.6 Layout Systems
[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Layout systems determine where controls live spatially and how they react to resize, content changes, and docking transitions. They exist to keep features declarative about intent while leaving geometry solving to dedicated engines.

Without layout systems, features quickly accumulate brittle pixel arithmetic that fails on DPI changes, display size changes, and dynamic content.

#### Mental model and lifecycle placement

Treat each container as owned by one layout strategy at a time. Build control trees first, then apply layout structures and constraints. Layout resolution happens during layout passes before draw and may be re-triggered by invalidation.

For adaptive behavior, define policies once and let the resolver choose constraints by viewport conditions instead of rebuilding control trees per breakpoint.

#### Primary public APIs and key types

Tier 8 layout APIs: `LayoutAxis`, `ConstraintLayout`, `AnchorConstraint`, `DockPane`, `DockTabs`, `DockSplit`, `DockWorkspace`, `FlexLayout`, `FlexItem`, `FlexDirection`, `FlexAlign`, `FlexJustify`, `GridLayout`, `GridTrack`, `GridPlacement`, `LayoutAnimator`, `LayoutPass`, `MeasureContext`, `ArrangeContext`, `LayoutRoot`, `FlowLayout`, `FlowItem`, `Viewport`, and `WindowLayoutHandler`.

Tier 28 adaptive APIs: `ConstraintAttr`, `LayoutConstraint`, `ConstraintSet`, `AdaptivePolicy`, and `resolve_adaptive_policy`.

Tier 29 virtualization APIs: `MeasureMode`, `MeasurePolicy`, `VirtualizedWindow`, `RecyclePool`, and `VirtualizationCore`.

#### Typical usage flow

1. Choose layout family based on container behavior.
2. Add controls and register them with layout items/tracks/constraints.
3. For responsive containers, define adaptive policies and resolve by viewport.
4. For large datasets, combine layout with virtualization windows.
5. Recompute on invalidation rather than manual per-control rect churn.

#### Minimal example

```python
from gui_do import FlexLayout, FlexDirection, FlexItem

layout = FlexLayout(direction=FlexDirection.ROW, gap=10)
layout.add(FlexItem(control=self.sidebar, grow=0, basis=220))
layout.add(FlexItem(control=self.content, grow=1, basis=0))
```

#### Advanced pattern(s)

Compose `ConstraintSet` variants under `AdaptivePolicy`, then call `resolve_adaptive_policy` at runtime to switch constraints by viewport shape without reauthoring control logic.

For heavy list/tree/grid surfaces, pair host layout containers with `VirtualizationCore` and a `RecyclePool` to keep memory use and frame cost stable across large item counts.

#### Common mistakes and anti-patterns

- Mixing multiple layout owners in one container without explicit boundaries.
- Hardcoding fixed pixel dimensions where adaptive policies are needed.
- Applying layout before controls are attached to their parent tree.
- Running expensive manual geometry updates in `on_update` instead of relying on layout passes.

#### Cross-links to related systems

See 8.5 for control tree construction, 8.9 for window/task-panel presentation geometry, 8.10 for animated transitions, and 12 for performance scaling.

[Back to Table of Contents](#table-of-contents)

### 8.7 Focus and Accessibility
[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Focus management and accessibility ensure input predictability and semantic discoverability. Focus systems guarantee keyboard intent lands on the right target. Accessibility systems expose a semantic tree and announcement pathways for assistive tooling and automated diagnostics.

Together, they prevent a common class of UI failures where controls render correctly but cannot be reached or understood by keyboard and screen-reader workflows.

#### Mental model and lifecycle placement

Focus is an ordered, scoped navigation state. Controls become focusable when built and appropriately configured. Scope managers constrain focus to the active interaction context (for example modal windows). Window focus management coordinates focus transitions across windowed presentation surfaces.

Accessibility is a semantic overlay on top of control structure. Accessibility nodes should be attached once controls exist and updated as visibility/state changes. Subscriptions used to mirror dynamic labels/roles should be attached in runtime binding phases and cleaned in teardown.

#### Primary public APIs and key types

Tier 4 focus APIs: `FocusManager`, `FocusScope`, `FocusScopeManager`, `WindowFocusManager`, and `FocusRing`.

Tier 21 accessibility APIs: `AccessibilityRole`, `LivePoliteness`, `AccessibilityNode`, `AccessibilityTree`, `AccessibilityAnnouncement`, and `AccessibilityBus`.

Tier 1 supporting specs: `AccessibilitySequenceSpec`, `StaticAccessibilitySpec`, and `TaskPanelFocusToggleSpec`.

#### Typical usage flow

1. Build controls and assign focus participation appropriately.
2. Register static semantic annotations through accessibility specs.
3. Use focus scopes for modal/overlay contexts.
4. Ensure hidden/disabled windows and controls leave active focus traversal.
5. Emit announcements through accessibility bus for critical state changes.

#### Minimal example

```python
from gui_do import AccessibilityTree, AccessibilityNode, AccessibilityRole

tree = AccessibilityTree()
submit = AccessibilityNode(role=AccessibilityRole.BUTTON, name="Submit")
tree.root.add_child(submit)
```

#### Advanced pattern(s)

Use `AccessibilitySequenceSpec` to define deterministic scene-level traversal order that matches task-panel and window presentation intent. Pair with `TaskPanelFocusToggleSpec` so hidden window targets are removed from focus routes automatically.

Use `FocusScope` for modal dialog capture so tab traversal cannot leak to background controls while overlays are active.

#### Common mistakes and anti-patterns

- Leaving hidden window controls in focus rings, causing invisible traversal targets.
- Omitting semantic roles for custom canvas-driven interactive regions.
- Building accessibility nodes before control identity and hierarchy are stable.
- Registering reactive accessibility updates without teardown, producing stale announcements.

#### Cross-links to related systems

See 8.3 for keyboard/event routing order, 8.5 for control ownership, 8.8 for modal overlay behavior, and 8.9 for window/task-panel presentation coordination.

See [Appendix F: Specifications and Option Reference](#appendix-f-specifications-and-option-reference).

[Back to Table of Contents](#table-of-contents)

### 8.8 Overlays, Dialogs, Notifications, and Command Surfaces
[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Overlay and command-surface systems manage transient UI layers that should not destabilize base-scene interaction flow. They exist to provide explicit routing precedence, dismissal contracts, and isolated lifecycle handling for temporary surfaces.

This includes modal dialogs, non-modal toasts, tooltips, context menus, command palette entries, and related transfer/clipboard interactions.

#### Mental model and lifecycle placement

Overlays are top-layer routers. For many event classes, overlay and toast managers evaluate first; consumed events do not fall through to scene controls. This prevents accidental click-through and keeps modal semantics reliable.

Overlay creation usually happens from actions or callbacks after runtime bind. Overlay cleanup should be explicit via handles or dismissal policy. Any event subscriptions associated with custom overlay content must be released when the overlay is dismissed.

#### Primary public APIs and key types

Tier 9 APIs: `OverlayManager`, `OverlayHandle`, `Alignment`, `PlacementResult`, `PopupPlacement`, `Side`, `compute_popup_rect`, `DialogManager`, `DialogHandle`, `ToastManager`, `ToastHandle`, `ToastSeverity`, `ContextMenuManager`, `ContextMenuItem`, `ContextMenuHandle`, `CommandPaletteManager`, `CommandEntry`, `CommandPaletteHandle`, `TooltipManager`, `TooltipHandle`, `MenuBarManager`, `FileDialogManager`, `FileDialogOptions`, `FileDialogHandle`, `NotificationCenter`, `NotificationRecord`, `ResizeManager`, `CursorManager`, `CursorHandle`, `CursorShape`, `DragDropManager`, `DragPayload`, `ClipboardManager`, `TransferData`, `TransferManager`, `ShortcutHelpOverlay`, `ShortcutSection`, and `ShortcutEntry`.

Tier 1 integration specs: `ShortcutOverlaySpec` and `NotificationSpec`.

#### Typical usage flow

1. Trigger surface creation from action or control callback.
2. Receive and retain manager handle when mutation/dismissal may be needed.
3. Respect dismissal policies (escape, outside click, explicit close).
4. Ensure focus behavior is compatible with modal/non-modal semantics.
5. Teardown custom bindings when overlay lifetime ends.

#### Minimal example

```python
from gui_do import ToastSeverity

def on_saved(host) -> None:
  host.toasts.show("File saved", severity=ToastSeverity.SUCCESS)
```

#### Advanced pattern(s)

Integrate `ShortcutHelpOverlay` using `ShortcutOverlaySpec` so action registry hotkeys and curated manual sections render in one discoverable command surface.

Compose command palette entries dynamically through `CommandPaletteManager` plus scene/window entry grouping to keep command discoverability aligned with current runtime context.

#### Common mistakes and anti-patterns

- Showing overlays without a clear dismissal path.
- Assuming toast pointer events should fall through to controls beneath.
- Updating dismissed overlay handles without validity checks.
- Retaining overlay subscriptions after dismissal, causing stale callbacks and memory leaks.

#### Cross-links to related systems

See 8.3 for dispatch ordering, 8.7 for modal focus capture, 8.9 for scene/window integration, and 8.16 for operational diagnostics of transient surfaces.

[Back to Table of Contents](#table-of-contents)

### 8.9 Scene, Window, and Task-Panel Presentation Models
[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Scenes, windows, and task-panel models define how users move across application contexts and how feature surfaces are presented inside each context. Scenes represent high-level work modes. Windows represent localized tools or content surfaces inside a scene. Task-panel controls and scene menu strips provide discoverable command and visibility controls.

This system centralizes visibility and routing coherence. Without a presentation model, each feature would implement its own visibility toggles and focus exclusions, which becomes error-prone as scene count grows.

#### Mental model and lifecycle placement

Scene declarations are part of bootstrap configuration; windows and task-panel composition are usually built during feature build phases and then bound to routed behavior in runtime binding phases. Visibility changes should flow through helper APIs so focus, accessibility, and menu/task-panel state remain synchronized.

Use scene-level models to answer "what is active" and window-level models to answer "what is visible and interactive." This separation improves maintainability and prevents mode changes from being mixed with local tool-window toggles.

#### Primary public APIs and key types

Core names include `ScenePresentationModel`, `WindowSpec`, `AnchoredWindowSpec`, `SceneTaskPanelSpec`, `TaskPanelButtonSpec`, `TaskPanelFocusToggleSpec`, `TaskPanelSlotLayoutSpec`, `TaskPanelWindowToggleGroupSpec`, `FeatureWindowBundleBindingSpec`, `WindowToggleBindingSpec`, `TabbedPresenterSpec`, and `TabBuilderSpec`.

Tier 18 helper APIs include `set_window_visible_state`, `toggle_window_visibility`, `create_anchored_feature_window`, `create_presented_anchored_window`, `create_presented_window_from_spec`, `create_feature_presented_window`, `add_window_scene_menu_strip`, `ensure_scene_task_panel`, `create_task_panel_slot_layout`, `add_scene_task_panel_items`, `setup_feature_presenter_tabs`, `register_window_tab_builder_specs`, `compute_tabbed_window_layout`, `register_tab_update_handlers`, `ActiveTabUpdateRouter`, and `TabLayoutContext`.

#### Typical usage flow

1. Declare scene and window specs in host configuration.
2. Build window and task-panel chrome during feature build.
3. Connect toggle actions/menu/task-panel controls through routed helpers.
4. Use visibility helpers to change window state, not ad hoc property mutation.
5. Keep focus and accessibility toggle behavior synchronized with visibility.

#### Minimal example

```python
from gui_do import create_feature_presented_window, AnchoredWindowSpec

window = create_feature_presented_window(
  host=host,
  feature=self,
  spec=AnchoredWindowSpec(
    control_id="inspector_window",
    title="Inspector",
    size=(420, 320),
    anchor="top_right",
    margin=(16, 16),
  ),
)
```

#### Advanced pattern(s)

Use tabbed window composition with `TabbedPresenterSpec` and `TabBuilderSpec`, then route per-tab updates using `ActiveTabUpdateRouter` so only active tab content receives update work where possible.

For desktop-style multi-window scenes, pair task-panel toggle groups with scene menu strip window entries and route both through `ScenePresentationModel.handle_window_toggle` to guarantee one source of visibility truth.

#### Common mistakes and anti-patterns

- Mismatching scene scope and window scope for action handlers.
- Toggling raw visibility flags without focus-ring synchronization.
- Building windows in runtime bind phases where sibling dependencies already expect them to exist.
- Duplicating toggle state in both task-panel button and window model instead of deriving from model state.

#### Cross-links to related systems

See 8.2 for lifecycle timing, 8.5 for control composition, 8.7 for focus integration, and 8.8 for transient overlay surfaces.

See [Appendix F: Specifications and Option Reference](#appendix-f-specifications-and-option-reference).

[Back to Table of Contents](#table-of-contents)

### 8.10 Scheduling, Timing, Animation, and Transitions
[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Scheduling systems let time-based behavior run predictably inside frame constraints. Animations, transition effects, timers, debounce/throttle policies, and cooperative multi-step workflows all depend on this layer.

The core design goal is bounded per-frame work. Scheduler budget clamping prevents a single frame's task queue from monopolizing update time and degrading interaction latency.

#### Mental model and lifecycle placement

Schedulers and animation managers are runtime resources used from feature update/bind phases. Register tasks and animations once, then let the runtime tick them each frame. Keep heavy work chunked into resumable steps.

Runtime operating contracts define these scheduler budget values: fraction 0.12 of dt milliseconds, floor 0.5 ms, and ceiling 4.0 ms. These bounds apply to scheduler dispatch budgeting.

#### Primary public APIs and key types

Tier 5 APIs: `TaskEvent`, `TaskScheduler`, `Timers`, `TweenManager`, `TweenHandle`, `Easing`, `AnimationSequence`, `AnimationHandle`, `TransitionManager`, `TransitionSpec`, `TransitionEvent`, `AnimationStateMachine`, `AnimationTransitionMode`, `SceneTimeline`, `Debouncer`, `Throttler`, `CooperativeScheduler`, `CoroutineHandle`, `Pause`, `Sleep`, `WaitForEvent`, `WaitForSignal`, `WaitUntil`, and `WaitForAll`.

Related Tier 26 APIs: `CancellationToken`, `PipelineStage`, `DataflowPipeline`, and `PipelineHandle`.

#### Typical usage flow

1. Choose the simplest timing primitive that solves the need.
2. Register tweens/transitions/timers in response to user or lifecycle events.
3. Use cooperative scheduler yield primitives for multi-frame workflows.
4. Cancel or teardown pending handles when scene/feature exits.
5. Monitor frame behavior and adjust granularity when budget pressure appears.

#### Minimal example

```python
from gui_do import Sleep

def show_after_delay(host):
  yield Sleep(0.5)
  host.toasts.show("Ready")

host.scheduler.run(show_after_delay(host))
```

#### Advanced pattern(s)

Use `WaitForSignal` and `WaitForAll` in cooperative workflows to orchestrate user confirmation plus background completion without threads or blocking loops.

Combine `AnimationStateMachine` with `TransitionManager` and scene timeline markers to coordinate visual state transitions with route changes and task completion milestones.

#### Common mistakes and anti-patterns

- Doing unbounded work directly in `on_update` rather than yielding/chunking.
- Running blocking I/O in cooperative coroutines.
- Forgetting to cancel tweens/timers on feature teardown.
- Treating debounce/throttle as global defaults instead of context-specific policies.

#### Cross-links to related systems

See 8.2 for per-frame lifecycle hooks, 8.9 for scene transition presentation, 8.14 for dataflow integration, and 12 for performance diagnosis.

[Back to Table of Contents](#table-of-contents)

### 8.11 Persistence and Workspace/Session State
[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Persistence systems preserve user workspace and feature/session state across process restarts. They exist so applications can restore context safely rather than forcing users to rebuild their working state manually.

The restore path is contract-driven and observable. Instead of opaque success/failure, runtime exposes a structured report describing scene switch outcome, restored items, applied settings, skipped settings, and missing settings blocks.

#### Mental model and lifecycle placement

State capture usually occurs during shutdown/save operations, while restoration occurs during startup or explicit load workflows. Feature-level save/restore hooks must cooperate with lifecycle ordering: build structural controls first, then apply restored values.

Unknown settings keys are skipped instead of aborting restore, which supports forward/backward compatibility across evolving settings schemas.

#### Primary public APIs and key types

Tier 11 APIs: `CommandHistory`, `Command`, `CommandTransaction`, `StateMachine`, `HierarchicalStateMachine`, `Router`, `RouteEntry`, `SettingsRegistry`, `SettingDescriptor`, `WorkspaceState`, `WorkspacePersistenceManager`, `DEFAULT_WORKSPACE_STATE_PATH`, `SceneSnapshot`, and `NodeSnapshot`.

Tier 23 API: `UndoContextManager`.

Tier 32 migration APIs: `SchemaVersion`, `VersionedSnapshot`, `MigrationStep`, `MigrationRegistry`, `SnapshotMigrator`, `MigrationError`, `make_snapshot`, and `read_version`.

Restore report fields are `target_scene`, `switched_scene`, `restored_feature_states`, `restored_scene_nodes`, `applied_settings`, `skipped_settings`, and `missing_settings_blocks`.

#### Typical usage flow

1. Save workspace state through application persistence facade.
2. Load workspace state and inspect restore report.
3. Surface skipped/missing details to diagnostics or user feedback.
4. Apply migration before state consumption when snapshot schema versions differ.
5. Use undo context routing where multi-panel independent history is needed.

#### Minimal example

```python
report = host.app.load_workspace(path)
if report and report.skipped_settings:
  host.toasts.show("Some settings were skipped during restore")
```

#### Advanced pattern(s)

Define migration steps in `MigrationRegistry` and apply through `SnapshotMigrator` so older snapshots are upgraded before runtime restore logic consumes them.

Use `UndoContextManager` to route undo/redo into named contexts, allowing separate history stacks per tool panel while preserving a common command architecture.

#### Common mistakes and anti-patterns

- Assuming all settings keys always exist across versions.
- Restoring snapshot payloads without version inspection via `read_version`.
- Using default workspace path in multi-instance scenarios without per-instance override.
- Applying restored state before control tree/build prerequisites are satisfied.

#### Cross-links to related systems

See 8.1 for bootstrap sequencing, 8.2 for save/restore lifecycle hooks, 8.9 for window presentation state, and 13 for migration/deprecation policy.

See [Appendix F: Specifications and Option Reference](#appendix-f-specifications-and-option-reference).

[Back to Table of Contents](#table-of-contents)

### 8.12 Theme, Styling, and Visual Systems
[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Theme and styling systems centralize visual identity so controls can adapt to design changes without feature-level rewrites. Font roles and design tokens give semantic naming to visual resources and remove hardcoded values from feature logic.

This makes visual updates lower risk and enables runtime theme switching with deterministic invalidation behavior.

#### Mental model and lifecycle placement

Theme and font resources are configured during bootstrap and consumed during rendering and layout. Controls should refer to theme roles/tokens rather than concrete colors and font file details.

On theme switch, caches must invalidate. Theme invalidation bus exists to broadcast this change so cached surfaces can be re-rendered safely.

#### Primary public APIs and key types

Tier 6 APIs: `FontManager`, `FontRoleRegistry`, `ColorTheme`, `ThemeManager`, `DesignTokens`, `ScopedTheme`, and `ScopedThemeManager`.

Tier 22 API: `ThemeInvalidationBus`.

Related binding/spec types include `FontRoleBindingSpec`, `CursorSpec`, `CursorBindingSpec`, and `setup_standard_font_roles`.

#### Typical usage flow

1. Declare font resources in host configuration.
2. Map semantic roles through font-role bindings.
3. Reference semantic roles/tokens from controls and draw code.
4. Switch themes through theme manager APIs.
5. Invalidate cached render surfaces via theme invalidation bus subscriptions.

#### Minimal example

```python
theme = host.theme_manager
theme.set_theme("dark")
```

#### Advanced pattern(s)

Use `ScopedThemeManager` to apply local visual overrides for specific windows or panels while keeping global theme unchanged.

In custom rendering controls, subscribe cache invalidation handlers to `ThemeInvalidationBus` so expensive cached surfaces are rebuilt only when needed.

#### Common mistakes and anti-patterns

- Hardcoding color/font literals in feature draw paths.
- Switching theme without invalidating cached surfaces.
- Registering font roles too late in lifecycle after controls are already resolved.
- Using scoped themes without documenting local contrast/accessibility implications.

#### Cross-links to related systems

See 8.1 for bootstrap binding, 8.5 for control rendering usage, 8.15 for graphics integration, and 12 for performance implications of cache invalidation.

[Back to Table of Contents](#table-of-contents)

### 8.13 Text, Input, Forms, and Validation Systems
[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Text and form systems provide a coherent path from low-level input widgets to validated domain-level form state. They exist to avoid fragmented ad hoc validation and inconsistent field lifecycle behavior.

This stack combines control-level entry (`TextInputControl`, `TextAreaControl`) with schema/model layers (`FormModel`, `FormSchema`, `SchemaFormRuntime`) and both synchronous and asynchronous validation strategies.

#### Mental model and lifecycle placement

Text controls capture and expose user input. Form model/schema layers define logical structure and rules. Runtime validation policies decide when validation is evaluated (`ValidationPolicy`) and how errors are surfaced. Asynchronous validators are for external checks and should be debounced with stale-result suppression.

Bindings from control values to model fields are typically attached in `bind_runtime`. Validation subscriptions and async handles must be cleaned during teardown to avoid stale callbacks.

#### Primary public APIs and key types

Tier 10 forms/validation APIs: `FormModel`, `FormField`, `ValidationRule`, `FieldError`, `FormSchema`, `SchemaField`, `DocumentModel`, `WizardFlow`, `WizardStep`, `WizardHandle`, `ValidationResult`, `Validator`, `RequiredValidator`, `RangeValidator`, `LengthValidator`, `PatternValidator`, `CustomValidator`, `DependentValidator`, and `ValidationPipeline`.

Tier 24 async validation APIs: `AsyncFieldValidator` and `AsyncFormValidator`.

Tier 31 schema runtime APIs: `FieldSchema`, `FieldGraphSchema`, `ValidationPolicy`, and `SchemaFormRuntime`.

Tier 14 text/localization APIs: `TextFormatter`, `NumericFormatter`, `PatternFormatter`, `FixedPatternFormatter`, `TextFlow`, `TextSpan`, `TextSearcher`, `TextMatch`, `StringTable`, and `LocaleRegistry`.

Related Tier 13 input controls: `TextInputControl`, `TextAreaControl`, `SpinnerControl`, `DatePickerControl`, `TimePickerControl`, `ColorPickerControl`, and `ChipInputControl`.

#### Typical usage flow

1. Define schema/model fields and validators.
2. Build text/input controls in feature build phase.
3. Connect control values to form fields in runtime bind phase.
4. Choose validation policy and trigger strategy.
5. Use async validators for remote checks with stale-result suppression.
6. Render field-level validation feedback near controls.

#### Minimal example

```python
from gui_do import RequiredValidator, PatternValidator, ValidationPipeline

email_pipeline = ValidationPipeline(
  validators=(
    RequiredValidator("Email is required"),
    PatternValidator(r".+@.+\..+", "Invalid email format"),
  )
)
result = email_pipeline.validate("user@example.com")
```

#### Advanced pattern(s)

Use `SchemaFormRuntime` with `FieldGraphSchema` to support field visibility dependencies and policy-controlled validation timing across multi-step forms.

Use `AsyncFormValidator` with per-field debouncing for username/email uniqueness checks, and suppress stale async generations when users continue typing.

#### Common mistakes and anti-patterns

- Validating only on submit when immediate feedback is expected.
- Ignoring `ValidationPolicy` and triggering validation indiscriminately.
- Using async validation without cancellation/stale suppression.
- Keeping form truth in controls instead of model/runtime state.

#### Cross-links to related systems

See 8.4 for observable binding patterns, 8.5 for control composition, 8.14 for async pipeline orchestration, and 11 for testing/diagnostics.

See [Appendix F: Specifications and Option Reference](#appendix-f-specifications-and-option-reference).

[Back to Table of Contents](#table-of-contents)

### 8.14 Data and Dataflow Helpers
[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Data-heavy interfaces need loading, sorting, filtering, caching, diffing, and cancellation-aware background processing. This system exists to make those operations composable and observable rather than monolithic.

It is the bridge between data acquisition/transformation and scalable presentation layers like virtualized list/grid/tree surfaces.

#### Mental model and lifecycle placement

Think in stages: source, transform, projection, and render. Use provider/source abstractions for data access, proxy/query abstractions for projection, and pipeline abstractions for cancellation-aware processing. Bind resulting state into controls reactively.

Long-running operations should run through staged pipelines rather than blocking frame updates.

#### Primary public APIs and key types

Tier 15 APIs: `VirtualItemSource`, `FixedItemSource`, `SortFilterProxySource`, `AsyncDataProvider`, `LoadState`, `LoadStateKind`, `ObjectPool`, `DataCache`, `CacheStats`, `ListDiffCalculator`, `ListDiff`, `DiffInsert`, `DiffRemove`, and `DiffMove`.

Tier 26 APIs: `CancellationToken`, `PipelineStage`, `DataflowPipeline`, and `PipelineHandle`.

Tier 27 shared-store APIs: `AppStateStore`, `StateSelector`, and `StateTransaction`.

Tier 29 virtualization APIs: `MeasureMode`, `MeasurePolicy`, `VirtualizedWindow`, `RecyclePool`, and `VirtualizationCore`.

#### Typical usage flow

1. Load source data through async provider or fixed source.
2. Apply sort/filter proxy layer for dynamic projections.
3. Feed projected data into virtualized display surfaces.
4. Use `DataflowPipeline` for cancellable multi-stage transforms.
5. Publish progress and state transitions via observables/store selectors.
6. Apply list diffs for incremental UI updates.

#### Minimal example

```python
from gui_do import FixedItemSource, SortFilterProxySource

source = FixedItemSource(items)
proxy = SortFilterProxySource(source)
proxy.set_filter(lambda item: item.active)
proxy.set_sort_key(lambda item: item.name)
```

#### Advanced pattern(s)

Build a three-stage `DataflowPipeline` (load, normalize, rank) with generation cancellation. On each new query, cancel stale generations and update progress indicators from stage telemetry.

Pair `ListDiffCalculator` with virtualized rendering to apply minimal change sets rather than full list rebuilds on every data refresh.

#### Common mistakes and anti-patterns

- Full redraw/rebuilds without diffing or virtualization.
- Not canceling stale pipeline generations on new user input.
- Unbounded cache growth without eviction policy.
- Returning pooled objects while still referenced by UI/state.

#### Cross-links to related systems

See 8.4 for reactive state propagation, 8.10 for scheduling coordination, 8.13 for async validation parallels, and 8.16 for telemetry-backed bottleneck diagnosis.

[Back to Table of Contents](#table-of-contents)

### 8.15 Graphics and Audio Integration Points
[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Graphics and audio integration points support experiences beyond standard controls: custom rendering pipelines, scene-graph-based visuals, sprite/particle/tile systems, and semantic audio cues.

These systems let advanced visual/audio behavior remain structured and testable rather than becoming raw draw-call sprawl.

#### Mental model and lifecycle placement

Use `draw` and graphics helpers for custom visual work, while keeping data and timing logic in update/scheduling layers. Audio should be triggered from semantic events (actions/state transitions), not noisy low-level pointers.

Asset loading belongs in setup/build phases; per-frame paths should operate on already loaded resources and incremental state.

#### Primary public APIs and key types

Tier 16 graphics APIs: `BuiltInGraphicsFactory`, `DirtyRegionTracker`, `DrawContext`, `DrawPhase`, `AssetRegistry`, `DebugOverlay`, `SurfaceCompositor`, `Layer`, `ShapeRenderer`, `SurfaceEffects`, `VectorPath`, `SpriteSheet`, `FrameAnimation`, `ParticleSystem`, `Emitter`, `ParticleLayer`, `TileSet`, `TileMap`, `RenderTarget`, `LiveRenderTarget`, `OffscreenRenderTarget`, `create_render_target`, `create_surface`, `Node2D`, `SceneGraph2D`, and `Camera2D`.

Tier 20 audio APIs: `SoundCue`, `SoundBankRegistry`, and `SoundEventBus`.

#### Typical usage flow

1. Initialize assets and graphics helpers during feature setup.
2. Update animation/particle/tile state in `on_update`.
3. Draw via phased or layered composition in `draw`.
4. Use dirty-region tracking where full redraw is unnecessary.
5. Publish semantic sound cues through sound event bus.

#### Minimal example

```python
def on_update(self, host) -> None:
  self.particles.tick(host.frame_dt)

def draw(self, host, surface, theme) -> None:
  self.particles.draw(surface)
```

#### Advanced pattern(s)

Combine `DirtyRegionTracker` with `OffscreenRenderTarget` to redraw only changed regions of expensive canvases, then composite through `SurfaceCompositor` layers.

Use `SceneGraph2D` and `Camera2D` for scroll/zoom worlds with hierarchical transforms, then synchronize audio cues through `SoundEventBus` for state-driven feedback.

#### Common mistakes and anti-patterns

- Loading assets inside per-frame draw paths.
- Full-screen redraw every frame when dirty regions suffice.
- Triggering audio from low-level event noise instead of semantic actions.
- Unbounded particle emitters without lifecycle cleanup.

#### Cross-links to related systems

See 8.2 for draw lifecycle hooks, 8.5 for `CanvasControl` integration, 8.10 for timing/animation scheduling, and 8.16 for profiling graphics hot paths.

[Back to Table of Contents](#table-of-contents)

### 8.16 Telemetry, Introspection, and Operational Hooks
[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Telemetry and introspection systems make runtime behavior measurable and inspectable. They exist to replace guesswork with evidence when diagnosing performance, routing, and state issues.

Operational hooks support both live diagnosis and offline analysis through recorded telemetry artifacts.

#### Mental model and lifecycle placement

Enable telemetry before scenarios you want to measure. Instrument critical paths with spans and correlate results with frame/update behavior. Introspection tools expose property and spatial state while application is running.

Keep diagnostic subscriptions and overlays scoped to runtime lifecycle so operational tooling does not leak into inactive scenes.

#### Primary public APIs and key types

Tier 7 telemetry APIs: `TelemetryCollector`, `TelemetrySample`, `configure_telemetry`, `telemetry_collector`, `analyze_telemetry_log_file`, `analyze_telemetry_records`, `load_telemetry_log_file`, and `render_telemetry_report`.

Tier 17 introspection APIs: `SceneSpatialIndex`, `ui_property`, `PropertyDescriptor`, `PropertyRegistry`, `property_registry`, `PropertyInspectorModel`, and `InspectedProperty`.

#### Typical usage flow

1. Enable telemetry through configuration/bootstrap.
2. Execute representative usage scenarios.
3. Analyze records and render reports.
4. Use property/spatial inspection to localize anomalies.
5. Feed findings back into scheduling/layout/render optimizations.

#### Minimal example

```python
from gui_do import configure_telemetry, telemetry_collector, analyze_telemetry_records

configure_telemetry(enabled=True)
report = analyze_telemetry_records(telemetry_collector.records)
```

#### Advanced pattern(s)

Combine telemetry spans from dataflow stages with property inspector snapshots and scene spatial queries to isolate whether a bottleneck is transform logic, layout churn, or draw cost.

Build targeted debug overlays that visualize spatial-index query results while recording telemetry around routing and invalidation hot paths.

#### Common mistakes and anti-patterns

- Measuring only idle loop behavior and extrapolating to active scenarios.
- Forgetting to enable telemetry before collecting traces.
- Relying on visual intuition without instrumented evidence.
- Leaving debug instrumentation active in production paths without policy.

#### Cross-links to related systems

See 8.10 for scheduler budget context, 8.11 for persistence/log artifacts, 8.14 for pipeline instrumentation, and 8.15 for graphics hot-path analysis.

[Back to Table of Contents](#table-of-contents)

## Integration Patterns and Composition Recipes
[Back to Table of Contents](#table-of-contents)

### Recipe 1: Routed Feature + Actions + Shortcut Overlay

Goal: build a feature with discoverable keyboard shortcuts that stay synchronized with action wiring.

Why this combination: `RoutedRuntimeSpec` and `RoutedFeatureLifecycleSpec` consolidate hotkeys, event subscriptions, and shortcut overlay lifecycle into one declarative bundle, reducing manual wiring drift.

Step-by-step pattern:
1. Declare `ActionSpec` entries in host config.
2. In feature init, define `RoutedRuntimeSpec` with `action_hotkeys` and `shortcut_overlays`.
3. Wrap it in a `RoutedFeatureLifecycleSpec`.
4. Bind in `bind_runtime` with `bind_routed_feature_lifecycle`.
5. Teardown in `shutdown_runtime` with `shutdown_routed_feature_lifecycle`.

```python
self._runtime_spec = RoutedRuntimeSpec(
  scene_name="main",
  shortcut_overlays=(
    ShortcutOverlaySpec(
      attr_name="_help_overlay",
      toggle_action_name="help",
      toggle_key=pygame.K_F9,
      toggle_scene_name="main",
      manual_shortcut_lines=("Esc - Exit",),
    ),
  ),
)
self._lifecycle_spec = RoutedFeatureLifecycleSpec(runtime_spec=self._runtime_spec)
```

Validation notes: confirm F9 toggles the overlay, action entries appear, and overlay content reflects filtered/manual shortcut sections as configured.

### Recipe 2: Window Presenter + Task Panel + Focus Toggle

Goal: manage a floating tool window with task-panel toggle and safe focus behavior.

Why this combination: presenter separation keeps feature lifecycle thin, and task-panel focus toggle wiring ensures hidden windows do not stay in traversal order.

Step-by-step pattern:
1. Define `AnchoredWindowSpec` for geometry/chrome.
2. Implement a `WindowPresenter` subclass for window content.
3. Build window with `create_feature_presented_window` or `create_anchored_feature_window`.
4. Add `TaskPanelFocusToggleSpec` in routed runtime spec.
5. Use `set_window_visible_state` for toggles.

```python
set_window_visible_state(host.window_presentation, key="inspector", visible=True)
```

Validation notes: when hidden, window controls are excluded from focus traversal; task-panel toggle state and window visibility remain consistent.

### Recipe 3: State Store + Persistence + Snapshot Migration

Goal: retain centralized application state across schema evolution.

Why this combination: store selectors keep feature reads focused, persistence handles session restore, and migration graph ensures old snapshots remain loadable.

Step-by-step pattern:
1. Initialize `AppStateStore` and selectors.
2. Save snapshots with `make_snapshot`.
3. On load, inspect schema with `read_version`.
4. Apply `SnapshotMigrator` with registered `MigrationStep` chain.
5. Inspect restore report fields for skipped/missing details.

```python
snapshot = make_snapshot(SchemaVersion(2), state_dict)
version = read_version(snapshot)
migrated = migrator.migrate(snapshot) if version != SchemaVersion(2) else snapshot
```

Validation notes: restore must not fail on missing keys; assert `target_scene`, `switched_scene`, `restored_feature_states`, `restored_scene_nodes`, `applied_settings`, `skipped_settings`, and `missing_settings_blocks` expectations.

### Recipe 4: Dataflow Pipeline + Telemetry + Error Boundary

Goal: run cancellable background transforms with measurable performance and graceful UI failure containment.

Why this combination: data pipelines prevent blocking UI, telemetry identifies stage bottlenecks, and `ErrorBoundary` isolates rendering faults.

Step-by-step pattern:
1. Build `DataflowPipeline` stages with generation cancellation.
2. Wrap stage execution in telemetry spans.
3. Bind pipeline progress to observable UI state.
4. Wrap output UI subtree in `ErrorBoundary`.

```python
with telemetry_collector().span("pipeline", "rank_stage"):
  result = rank_stage(input_payload)
```

Validation notes: stale generations cancel correctly, telemetry report surfaces longest stage, and `ErrorBoundary` displays fallback instead of crashing frame loop.

[Back to Table of Contents](#table-of-contents)

## End-to-End Reference Application
[Back to Table of Contents](#table-of-contents)

```python
from __future__ import annotations

import pygame
from pygame import Rect

from gui_do import (
  ActionSpec,
  FeatureSpec,
  HostApplicationConfig,
  LabelControl,
  ObservableValue,
  RoutedFeature,
  RoutedFeatureLifecycleSpec,
  RoutedRuntimeSpec,
  RuntimeSceneSpec,
  SceneSetupSpec,
  ShortcutOverlaySpec,
  TelemetryConfig,
  bind_routed_feature_lifecycle,
  bootstrap_host_application,
  shutdown_routed_feature_lifecycle,
)


class CounterFeature(RoutedFeature):
  HOST_REQUIREMENTS = {"build": ("app",), "bind_runtime": (), "shutdown_runtime": ()}

  def __init__(self) -> None:
    super().__init__("counter", scene_name="main")
    self.count = ObservableValue(0)
    self.label = None
    self._unsubscribe = None
    self._runtime_spec = RoutedRuntimeSpec(
      scene_name="main",
      shortcut_overlays=(
        ShortcutOverlaySpec(
          attr_name="_help_overlay",
          toggle_action_name="help",
          toggle_key=pygame.K_F9,
          toggle_scene_name="main",
          manual_shortcut_lines=("F9 - Toggle Help", "Esc - Exit"),
        ),
      ),
    )
    self._lifecycle_spec = RoutedFeatureLifecycleSpec(runtime_spec=self._runtime_spec)

  def build(self, host) -> None:
    self.label = host.app.add(LabelControl("count_label", Rect(24, 24, 240, 30), "count: 0"), scene_name="main")

  def bind_runtime(self, host) -> None:
    bind_routed_feature_lifecycle(self, host, self._lifecycle_spec)
    self._unsubscribe = self.count.subscribe(lambda c: self.label.set_text(f"count: {c.new_value}"))

  def shutdown_runtime(self, host) -> None:
    if callable(self._unsubscribe):
      self._unsubscribe()
      self._unsubscribe = None
    shutdown_routed_feature_lifecycle(self, host, self._lifecycle_spec)


class ReferenceHost:
  def __init__(self) -> None:
    config = HostApplicationConfig(
      display_size=(1280, 720),
      window_title="gui_do Reference App",
      fonts={"default": {"file": None, "size": 16}},
      font_role_specs=(),
      cursors=(),
      scene_specs=(SceneSetupSpec("main"),),
      feature_specs=(FeatureSpec("_counter_feature", CounterFeature),),
      window_specs=(),
      runtime_scene_specs=(RuntimeSceneSpec(scene_name="main", bind_escape_to_exit=True),),
      action_specs=(
        ActionSpec(action_id="exit", label="Exit", kind="exit", category="File"),
        ActionSpec(action_id="help", label="Toggle Help", kind="palette_open", category="View"),
      ),
      static_accessibility_specs=(),
      initial_scene_name="main",
      telemetry=TelemetryConfig(enabled=True),
      target_fps=120,
    )
    self.app = bootstrap_host_application(self, config)

  def run(self) -> int:
    return int(self.app.run_entrypoint(target_fps=120))

  def save_workspace(self, path: str):
    return self.app.save_workspace(path)

  def load_workspace(self, path: str):
    return self.app.load_workspace(path)
```

### What This Listing Demonstrates

This reference combines the core bootstrap model (`HostApplicationConfig` + `bootstrap_host_application`) with routed feature lifecycle management, reactive label updates via `ObservableValue`, scene runtime policy (`bind_escape_to_exit=True`), and telemetry-enabled runtime execution. It also shows where workspace save/load hooks live in a host wrapper so persistence behavior can be integrated without scattering calls through feature code.

### Validation Checklist

1. Application opens and enters the main scene.
2. Counter updates propagate to the label through observable subscription.
3. F9 toggles shortcut help overlay in the main scene.
4. Escape exits according to runtime scene policy.
5. Routed lifecycle binding and shutdown complete without leaked handlers.
6. Workspace save/load calls return without fatal restore errors.

[Back to Table of Contents](#table-of-contents)

## Testing, Diagnostics, and Reliability
[Back to Table of Contents](#table-of-contents)

Reliability in gui_do is contract-first. The framework intentionally defines operating guarantees and boundary rules that are validated by tests and tied to documentation contracts. The correct maintainer workflow is to treat these tests as release gates, not optional confidence checks.

### Contract Tests

Run the high-priority contract command:

```bash
python -m pytest -q tests/test_public_api_exports.py tests/test_public_api_docs_contracts.py tests/test_runtime_operating_contracts.py tests/test_boundary_contracts.py tests/test_gui_application_workspace_contracts.py
```

What each file validates:
- `tests/test_public_api_exports.py`: verifies public root exports and importability contract.
- `tests/test_public_api_docs_contracts.py`: verifies alignment between documented API contract and exported names.
- `tests/test_runtime_operating_contracts.py`: verifies runtime guarantees, including normalization and deterministic behavior constraints.
- `tests/test_boundary_contracts.py`: verifies architecture boundary constraints between framework and demo layers.
- `tests/test_gui_application_workspace_contracts.py`: verifies workspace load/save behavior and restore summary expectations.

Additional contract/runtime-focused files currently present include `tests/test_architecture_boundary_docs_contracts.py`, `tests/test_demo_feature_package_contracts.py`, `tests/test_core_only_bootstrap_contracts.py`, and `tests/test_runtime_guarantees_and_determinism.py`.

### Runtime Behavior Tests

Runtime confidence depends on scenario-level tests, not isolated assertions alone. Focus on workspace persistence roundtrips, overlay/tooltip/cursor routing precedence, deterministic layout and animation progression, control runtime behavior under focus transitions, and accessibility sequence behavior under scene/window visibility changes.

For scene-heavy apps, include tests that intentionally transition scenes mid-workflow and assert teardown/build/bind sequencing. For routed features, assert both event consumption behavior and cleanup semantics after scene deactivation.

### Debug and Trace Tools

Use `EventRecorder` and `EventPlayback` to capture real user interaction traces and replay regressions deterministically. Use `DebugOverlay` and `PropertyInspectorPanel` to inspect live control/runtime state without modifying feature logic. For performance diagnosis, analyze telemetry with `analyze_telemetry_log_file`, `analyze_telemetry_records`, and `render_telemetry_report`.

These tools are most effective when used together: event trace establishes reproduction, telemetry identifies hot paths, and inspector overlays localize state inconsistencies.

### Maintainer Release Runbook

1. Run contract and boundary tests.
2. Run runtime determinism and workspace restore tests.
3. Regenerate or validate documentation contracts against current exports.
4. Execute representative end-to-end user scenarios with telemetry enabled.
5. Confirm scheduler budget behavior remains within contract.
6. Confirm no architecture-boundary regressions in imports.
7. Record unresolved risks in migration/deprecation notes before release decision.

### Regression Triage Workflow

Use a strict sequence: reproduce, trace, localize, test-first, patch, and revalidate adjacent contracts. Start from a failing observable behavior, capture the event/data trace, isolate the layer at fault (routing/state/layout/draw/persistence), write or update a focused regression test, patch at the correct abstraction tier, and finally run nearby contract suites to prevent collateral regressions.

### Maintainer Diff Checklist

Inventory delta checks:
1. Compare current root exports in `gui_do/__init__.py` with Appendix D and D.1 entries.
2. Check `docs/` contracts for changed guarantees, policies, or boundary rules.
3. Check `tests/` for new contract/runtime test modules that imply manual updates.
4. Check `demo_features/` for new recommended composition patterns to document.

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

[Back to Table of Contents](#table-of-contents)

## Performance and Scaling Guidance
[Back to Table of Contents](#table-of-contents)

### Scheduler Budget Contract

Scheduler dispatch is contract-bounded: fraction 0.12 of dt milliseconds, floor 0.5 ms, and ceiling 4.0 ms. These values provide predictable upper bounds under slow frames while still allowing useful progress under fast frames.

Treat budget compliance as an operational SLO. If workloads regularly saturate budget, refactor work into finer-grained stages or defer non-critical processing.

### Dirty-Region Rendering

`DirtyRegionTracker` is the primary optimization for complex visual surfaces. It tracks changed regions and supports fast overlap checks through an incremental union cache, so `overlaps_dirty()` avoids scanning every dirty rectangle each time.

Use dirty gating to avoid expensive redraw of unchanged areas, especially for canvas-heavy or multi-layered scenes.

### Virtualization and Incremental Rendering

Use `VirtualizationCore` and `VirtualizedWindow` for large lists/grids/trees so only visible windows are rendered. Use `RecyclePool` for view reuse and `ListDiffCalculator` for minimal update patches (`DiffInsert`, `DiffRemove`, `DiffMove`) instead of full reconstruction.

Combine virtualization with dataflow cancellation for responsive filters/search.

### Practical Scaling Checklist

- Enforce scene-scoped updates and handlers.
- Avoid per-frame full collection reallocation; use `ObjectPool` for high-churn allocations.
- Debounce expensive operations with `Debouncer`.
- Use `DataflowPipeline` and `CancellationToken` for preemptible background work.
- Profile representative user interactions, not idle loops only.
- Gate expensive draw passes with `DirtyRegionTracker`.

[Back to Table of Contents](#table-of-contents)

## Migration, Versioning, and Deprecation Notes
[Back to Table of Contents](#table-of-contents)

### Versioned Snapshot Strategy

Use versioned snapshots for all persisted state that may evolve. Recommended flow:
1. Write snapshot with `make_snapshot(current_version, state_dict)`.
2. Read incoming version with `read_version(raw_snapshot)`.
3. Apply `SnapshotMigrator.migrate(snapshot)` to reach current schema.
4. Restore migrated data into runtime models.

Migration steps are registered in `MigrationRegistry` as one-directional transitions. Unresolvable migration paths should raise `MigrationError` and be treated as explicit migration failures.

### Deprecation Handling

Preferred policy is additive evolution: add new optional fields first, keep legacy fields with warnings, and remove legacy behavior only after documented migration windows. Deprecation notes should be centralized in this chapter to avoid scattered and contradictory guidance.

No deprecated public APIs are cataloged in this generation. Add entries here when formal deprecations are introduced.

### Upgrade Checklist

- Run contract tests before and after upgrade.
- Validate consumer imports use root `gui_do` surface.
- Recheck action/input/focus behavior in active scenes.
- Inspect restore report for `skipped_settings` and `missing_settings_blocks`.
- Re-run telemetry baseline scenarios and compare distributions.

[Back to Table of Contents](#table-of-contents)

## FAQ and Troubleshooting
[Back to Table of Contents](#table-of-contents)

### Should I Build Apps Directly With Controls or With Features?

Use features as your architectural unit. Controls are implementation details inside feature boundaries. Feature lifecycle hooks provide orchestration points for build, runtime wiring, routing, updates, and teardown. If you build directly around controls without features, lifecycle and coupling concerns quickly become implicit and difficult to test.

### When Should I Use RoutedFeature Over Feature?

Use `RoutedFeature` when you need declarative routing bundles, lifecycle-managed hotkeys, overlays, subscriptions, or route-target behavior. Use plain `Feature` when straightforward lifecycle plus control composition is enough and routed indirection would add unnecessary complexity.

### Why Are Some Key Handlers Not Firing?

Check four layers in order: focus ownership, window scope visibility, overlay/modal capture behavior, and scene scope alignment. A handler can be correctly registered but still not execute if a higher-precedence routing stage consumes the event. Use `EventRecorder` traces to inspect actual routing sequence.

### Why Do Toast Clicks Not Pass Through?

By contract, toast bounds consume pointer clicks to prevent accidental interactions with controls beneath transient notifications. If you need interaction, wire explicit toast callbacks rather than expecting pass-through behavior.

### How Do I Avoid Breaking Workspace Restore Across Versions?

Version snapshots with `SchemaVersion`, register migration steps for each transition, and inspect restore summaries for skipped/missing settings. Handle partial restore gracefully, including user-facing feedback when optional settings could not be applied.

### How Do I Confirm My API Usage Is Within Supported Surface?

Use explicit root imports (`from gui_do import ...`) and run public export contract tests. Avoid direct imports from internal submodules for consumer application code unless you are intentionally extending internal systems and accept maintenance coupling risk.

### Why Does bind_runtime Seem Out of Order?

Framework contract is that all scene features complete `build` before any scene feature enters `bind_runtime`. Apparent ordering issues usually indicate scene assignment mismatch or a dependency on side effects not declared through specs/requirements.

### How Do I Add a Keyboard Shortcut Without Manual Wiring Everywhere?

Declare action intent with `ActionSpec`, then declare hotkey wiring via `ActionHotkeySpec` or routed runtime spec bundles. Let registry/input map integration perform binding and teardown consistently.

[Back to Table of Contents](#table-of-contents)

## Appendix
[Back to Table of Contents](#table-of-contents)

The appendix provides practical reference artifacts intended for daily implementation and maintenance workflows.

### Appendix A: Glossary
[Back to Table of Contents](#table-of-contents)

Feature: a lifecycle-managed unit of application behavior. A feature expresses dependencies via host requirements, builds/updates/draws within scene scope, and can be specialized as `DirectFeature`, `Feature`, `LogicFeature`, or `RoutedFeature`.

Spec: a declarative data object describing runtime wiring intent. Specs define scene/feature/action/window relationships and are consumed by bootstrap/build helpers to produce deterministic runtime setup.

Host: a plain Python object passed into bootstrap and populated with runtime members. This design keeps entrypoint code simple while allowing explicit, testable runtime attachment.

Scene: a top-level interaction context. Features belong to one scene scope, and scene activation governs which features receive events/updates.

Window presentation: the model that coordinates window registration, visibility, and focus-aware toggling inside a scene.

Routed runtime: declarative bundle describing routed feature runtime wiring such as hotkeys, shortcut overlays, task-panel focus toggles, and event subscriptions.

Observable: value container with subscriber notification semantics used for reactive state propagation.

Workspace state: persisted session context including scene selection, feature state, and settings replay.

Contract test: test that validates framework-level behavioral guarantees, API contracts, and architecture boundaries.

Tier: a grouping of public exports by abstraction level and intended usage priority.

### Appendix B: Lifecycle/Event Sequence
[Back to Table of Contents](#table-of-contents)

1. `bootstrap_host_application` realizes host from config specs.
2. Scene features run `build(host)`.
3. Scene features run `bind_runtime(host)` after build completes.
4. Runtime loop starts.
5. Raw events normalize to `GuiEvent`.
6. Overlay/focus/window/scene routing stages execute.
7. Feature event handlers consume or pass events.
8. Feature update hooks run and scheduler dispatches work.
9. Draw hooks and control-tree rendering present frame.
10. Scene transitions trigger runtime shutdown for departing features and build/bind for arriving features.
11. Application exit triggers active feature runtime shutdown and optional workspace save.

### Appendix C: System Dependency Map
[Back to Table of Contents](#table-of-contents)

Bootstrap systems depend on feature lifecycle abstractions, configuration specs, action/input wiring, and scene/window models. Feature systems depend on controls, event routing, and reactive state primitives. Layout and focus systems depend on control-tree structure and visibility state. Overlay systems depend on routing order and modal focus policy. Persistence/migration systems depend on state models and scene/feature registration. Scheduling and animation systems depend on update-loop timing and scene scope. Telemetry and introspection are cross-cutting and observe all major runtime layers. Audio integration depends on semantic application events and mixer-backed cue routing.

### Appendix D: API Quick Index
[Back to Table of Contents](#table-of-contents)

Bootstrap and configuration: `HostApplicationConfig`, `HostApplicationBindingSpec`, `build_host_application_config`, `bootstrap_host_application`, `FeatureSpec`, `WindowSpec`, `RuntimeSceneSpec`, `ActionSpec`, `SceneSetupSpec`, `SceneBundleBindingSpec`, `FeatureWindowBundleBindingSpec`, `WindowToggleBindingSpec`, `FontRoleBindingSpec`, `CursorBindingSpec`, `PaletteBindingSpec`, `TelemetryConfig`.

Feature lifecycle and routed runtime: `Feature`, `DirectFeature`, `LogicFeature`, `RoutedFeature`, `FeatureMessage`, `FeatureManager`, `RoutedRuntimeSpec`, `RoutedFeatureLifecycleSpec`, `bind_routed_feature_lifecycle`, `shutdown_routed_feature_lifecycle`, `register_routed_feature_companions`, `setup_routed_runtime`.

Events, actions, focus, input: `GuiEvent`, `EventType`, `EventPhase`, `EventManager`, `EventBus`, `EventRecorder`, `EventPlayback`, `RecordedEvent`, `ActionManager`, `ActionRegistry`, `ActionDescriptor`, `InputMap`, `InputBinding`, `KeyChordManager`, `FocusManager`, `FocusScope`, `FocusScopeManager`, `WindowFocusManager`, `FocusRing`, `Signal`, `SignalConnection`.

Reactive state and store: `ObservableValue`, `ObservableList`, `ObservableDict`, `CollectionChange`, `ChangeKind`, `ComputedValue`, `PresentationModel`, `reactive_batch`, `is_batching`, `CollectionView`, `CollectionViewQuery`, `AppStateStore`, `StateSelector`, `StateTransaction`.

Controls and presenters: `PanelControl`, `LabelControl`, `ButtonControl`, `ToggleControl`, `SliderControl`, `ScrollbarControl`, `CanvasControl`, `CanvasViewport`, `FrameControl`, `ImageControl`, `TabControl`, `TabItem`, `WindowControl`, `TaskPanelControl`, `WindowPresenter`, `MenuBarControl`, `SceneMenuStripControl`, `PropertyInspectorPanel`, `ErrorBoundary`, `TextInputControl`, `TextAreaControl`, `DropdownControl`, `DataGridControl`, `TreeControl`, `SplitButtonControl`, `ChipInputControl`.

Layout and virtualization: `FlexLayout`, `GridLayout`, `FlowLayout`, `ConstraintLayout`, `DockWorkspace`, `LayoutPass`, `LayoutAnimator`, `WindowLayoutHandler`, `AdaptivePolicy`, `ConstraintSet`, `resolve_adaptive_policy`, `VirtualizationCore`, `VirtualizedWindow`, `RecyclePool`, `MeasurePolicy`.

Overlays and command surfaces: `OverlayManager`, `DialogManager`, `ToastManager`, `TooltipManager`, `ContextMenuManager`, `CommandPaletteManager`, `MenuBarManager`, `FileDialogManager`, `NotificationCenter`, `ShortcutHelpOverlay`, `DragDropManager`, `ClipboardManager`, `TransferManager`, `compute_popup_rect`.

Forms and text: `FormModel`, `FormSchema`, `SchemaField`, `FieldError`, `ValidationPipeline`, `RequiredValidator`, `PatternValidator`, `AsyncFormValidator`, `AsyncFieldValidator`, `SchemaFormRuntime`, `FieldGraphSchema`, `ValidationPolicy`, `DocumentModel`, `WizardFlow`, `TextFormatter`, `TextFlow`, `TextSearcher`, `StringTable`, `LocaleRegistry`.

Data and pipelines: `VirtualItemSource`, `FixedItemSource`, `SortFilterProxySource`, `AsyncDataProvider`, `LoadState`, `DataCache`, `ObjectPool`, `ListDiffCalculator`, `DataflowPipeline`, `PipelineStage`, `PipelineHandle`, `CancellationToken`.

Graphics and audio: `DirtyRegionTracker`, `DrawContext`, `DrawPhase`, `AssetRegistry`, `DebugOverlay`, `SurfaceCompositor`, `Layer`, `ShapeRenderer`, `SurfaceEffects`, `VectorPath`, `SpriteSheet`, `FrameAnimation`, `ParticleSystem`, `TileMap`, `SceneGraph2D`, `Camera2D`, `RenderTarget`, `OffscreenRenderTarget`, `SoundCue`, `SoundBankRegistry`, `SoundEventBus`.

Telemetry and introspection: `TelemetryCollector`, `TelemetrySample`, `configure_telemetry`, `telemetry_collector`, `analyze_telemetry_records`, `render_telemetry_report`, `SceneSpatialIndex`, `ui_property`, `PropertyRegistry`, `PropertyInspectorModel`, `InspectedProperty`.

Persistence and migration: `WorkspacePersistenceManager`, `WorkspaceState`, `SceneSnapshot`, `NodeSnapshot`, `SettingsRegistry`, `SettingDescriptor`, `UndoContextManager`, `SchemaVersion`, `VersionedSnapshot`, `MigrationStep`, `MigrationRegistry`, `SnapshotMigrator`, `MigrationError`, `make_snapshot`, `read_version`.

### Appendix D.1: Tier Matrix
[Back to Table of Contents](#table-of-contents)

| Tier | System | Representative Key Types |
|---|---|---|
| 1 | Primary entry points and data-driven APIs | `HostApplicationConfig`, `FeatureSpec`, `RoutedRuntimeSpec`, `bootstrap_host_application`, `build_host_application_config` |
| 2 | Core application and scene management | `GuiApplication`, `create_display`, `SceneTransitionManager`, `SceneTransitionStyle` |
| 3 | Essential data and state management | `ObservableValue`, `ObservableList`, `CollectionView`, `ComputedValue`, `Binding` |
| 4 | Events, actions, focus, input | `GuiEvent`, `EventType`, `ActionManager`, `InputMap`, `FocusManager` |
| 5 | Scheduling and animation | `TaskScheduler`, `TweenManager`, `TransitionManager`, `CooperativeScheduler`, `Debouncer` |
| 6 | Theme and font management | `ThemeManager`, `DesignTokens`, `ColorTheme`, `FontManager`, `ScopedThemeManager` |
| 7 | Telemetry and diagnostics | `TelemetryCollector`, `configure_telemetry`, `analyze_telemetry_records`, `render_telemetry_report` |
| 8 | Layout and spatial | `FlexLayout`, `GridLayout`, `ConstraintLayout`, `DockWorkspace`, `LayoutPass` |
| 9 | Overlay managers and windows | `OverlayManager`, `DialogManager`, `ToastManager`, `CommandPaletteManager`, `ShortcutHelpOverlay` |
| 10 | Forms and data binding | `FormModel`, `FormSchema`, `ValidationPipeline`, `WizardFlow`, `DocumentModel` |
| 11 | State and persistence | `CommandHistory`, `Router`, `WorkspacePersistenceManager`, `SettingsRegistry`, `SceneSnapshot` |
| 12 | Primary controls | `PanelControl`, `LabelControl`, `ButtonControl`, `CanvasControl`, `TabControl` |
| 13 | Extended controls | `TextInputControl`, `DataGridControl`, `TreeControl`, `WindowPresenter`, `ErrorBoundary` |
| 14 | Text and localization | `TextFormatter`, `TextFlow`, `TextSearcher`, `StringTable`, `LocaleRegistry` |
| 15 | Data and collections | `VirtualItemSource`, `AsyncDataProvider`, `DataCache`, `ObjectPool`, `ListDiffCalculator` |
| 16 | Graphics and rendering | `DirtyRegionTracker`, `SurfaceCompositor`, `ParticleSystem`, `SceneGraph2D`, `RenderTarget` |
| 17 | Introspection and inspection | `SceneSpatialIndex`, `ui_property`, `PropertyRegistry`, `PropertyInspectorModel` |
| 18 | Advanced runtime and bootstrapping | `set_window_visible_state`, `create_feature_presented_window`, `ensure_scene_task_panel`, `ActiveTabUpdateRouter`, `bind_routed_feature_lifecycle` |
| 19 | Infrastructure internals | `UiEngine` |
| 20 | Audio | `SoundCue`, `SoundBankRegistry`, `SoundEventBus` |
| 21 | Accessibility | `AccessibilityNode`, `AccessibilityTree`, `AccessibilityRole`, `AccessibilityBus` |
| 22 | Theme invalidation | `ThemeInvalidationBus` |
| 23 | Undo context routing | `UndoContextManager` |
| 24 | Async form validation | `AsyncFieldValidator`, `AsyncFormValidator` |
| 25 | Scoped service graph | `ServiceKey`, `ServiceScope`, `ScopeStack` |
| 26 | Cancelable dataflow pipeline | `DataflowPipeline`, `PipelineStage`, `PipelineHandle`, `CancellationToken` |
| 27 | Transactional app state store | `AppStateStore`, `StateSelector`, `StateTransaction` |
| 28 | Adaptive constraint layout v2 | `ConstraintAttr`, `LayoutConstraint`, `ConstraintSet`, `AdaptivePolicy` |
| 29 | Unified virtualization core | `VirtualizedWindow`, `VirtualizationCore`, `RecyclePool`, `MeasurePolicy` |
| 30 | Interaction state machine framework | `InteractionPhase`, `InteractionContext`, `InteractionTransition`, `InteractionStateMachine` |
| 31 | Schema-driven form runtime | `FieldSchema`, `FieldGraphSchema`, `ValidationPolicy`, `SchemaFormRuntime` |
| 32 | Portable snapshot and migration layer | `SchemaVersion`, `VersionedSnapshot`, `MigrationRegistry`, `SnapshotMigrator`, `MigrationStep` |

### Appendix D.2: Selection Heuristics
[Back to Table of Contents](#table-of-contents)

1. Start at Tier 1 and stop if it solves the use case.
2. Descend one tier at a time only when additional control is required.
3. Use Tier 18 helpers for advanced bootstrap/runtime extension points.
4. Use root imports from `gui_do`; avoid submodule imports in consumer code.
5. Avoid Tier 19 (`UiEngine`) in application code.

Decision shortcuts:
- App setup: `HostApplicationConfig` and `bootstrap_host_application`.
- Cross-feature workflows: routed runtime plus lifecycle helpers.
- Large datasets: virtualization/dataflow before custom loops.
- Persistence with evolution: workspace persistence plus snapshot migration.
- Shortcut discoverability: `ShortcutOverlaySpec` in routed runtime.

### Appendix E: Architecture Templates
[Back to Table of Contents](#table-of-contents)

Template 1, small single-scene app: one scene, 2-4 features, observable feature state, command actions via `ActionSpec`, and minimal runtime scene policy (`bind_escape_to_exit=True`).

Template 2, multi-window workbench: multiple scenes, scene menu strip, task-panel toggles, presenter-backed windows, routed runtime shortcut overlay, and feature-window bundle specs.

Template 3, data-heavy analysis tool: async providers, sorting/filtering proxy, virtualization core, cancelable dataflow stages, dirty-region rendering, and telemetry baseline scenarios.

Template 4, long-running workflow app: cooperative scheduler workflows, observable progress channels, wizard-driven input collection, and snapshot migration-aware session persistence.

### Appendix F: Specifications and Option Reference
[Back to Table of Contents](#table-of-contents)

#### Bootstrap Specs

`HostApplicationBindingSpec`: high-level bootstrap declaration used by `build_host_application_config`. Key options: `display_size`, `window_title`, `fonts`, `initial_scene_name`, binding entry tuples, `telemetry`, and palette options. Use when you want one cohesive declaration instead of direct tuple assembly. Cross-links: 8.1, 5, 6.

`HostApplicationConfig`: concrete runtime config consumed by `bootstrap_host_application`. Key options: `display_size`, `window_title`, `fonts`, `font_role_specs`, `cursors`, `scene_specs`, `feature_specs`, `window_specs`, `runtime_scene_specs`, `action_specs`, `static_accessibility_specs`, `initial_scene_name`, optional `scene_roots`, `telemetry`, `target_fps`, and `palette_spec`. Cross-links: 5, 8.1, 10.

#### Feature and Runtime Wiring Specs

`FeatureSpec`: maps host attribute names to feature factories. Key fields: `attr_name`, `factory`. Cross-links: 8.1, 8.2.

`RoutedRuntimeSpec`: declarative routed wiring for scene-aware hotkeys, subscriptions, shortcut overlays, and task-panel focus toggles. Key fields: `scene_name`, `scheduler_attr_name`, `scheduler_dispatch_limit`, `logic_bindings`, `action_hotkeys`, `control_key_bindings`, `event_subscriptions`, `shortcut_overlays`, `task_panel_focus_toggles`, and `command_palette`. Cross-links: 7, 8.2, 8.3.

`RoutedFeatureLifecycleSpec`: lifecycle wrapper for routed runtime binding and optional companion providers. Key fields: `companion_providers`, `runtime_spec`, `runtime_spec_factory`, `runtime_spec_attr_name`, `scheduler_attr_name`. Cross-links: 7, 8.2.

#### Action and Input Specs

`ActionSpec`: named action declaration. Key fields: `action_id`, `label`, `kind`, optional `target`, `category`, `key`. Cross-links: 5, 8.3.

`ActionHotkeySpec`: declarative key to action mapping. Key fields: `action_name`, key/modifier controls, scene/window scope fields. Cross-links: 8.3.

`ControlKeyBindingSpec`: control-scoped key dispatch mapping for routed runtime. Key fields: target control, action target, and key binding metadata. Cross-links: 8.3, 8.5.

`EventSubscriptionSpec`: feature-managed event bus subscription declaration. Key fields: `attr_name`, `topic`, `handler`, optional `scope`. Cross-links: 8.3, 8.16.

#### Window and Presentation Specs

`WindowSpec`: window presentation binding metadata for feature windows and toggles. Key fields include window key, feature attribute mapping, toggle action info, task-panel label/style/slot, and accessibility label. Cross-links: 8.1, 8.9.

`AnchoredWindowSpec`: presenter-backed anchored window declaration. Key fields: `control_id`, `title`, `size`, `anchor`, `margin`, `use_frame_backdrop`. Cross-links: 8.9.

`TabbedPresenterSpec` and `TabBuilderSpec`: declarative tabbed window composition entries. Use to define tab identity, labels, and content builders. Cross-links: 8.9.

`FeatureWindowBundleBindingSpec` and `WindowToggleBindingSpec`: pair feature registration with window toggle metadata. Use for self-contained windowed feature declarations. Cross-links: 8.1, 8.9.

#### Task Panel and Command Surface Specs

`SceneTaskPanelSpec`: scene task-panel chrome declaration. Key options: scene association, control id, sizing, docking, and hide behavior. Cross-links: 8.9.

`TaskPanelButtonSpec`, `TaskPanelWindowToggleGroupSpec`, and `TaskPanelFocusToggleSpec`: button/toggle/focus options for task-panel interactions. Cross-links: 8.7, 8.9.

`SceneCommandPaletteSpec` and `PaletteBindingSpec`: per-scene palette activation and entry-group options. Cross-links: 8.3, 8.8.

`ShortcutOverlaySpec`: shortcut help overlay declaration. Key fields: `attr_name`, sizing/offsets, `toggle_action_name`, `toggle_key`, `toggle_scene_name`, manual line options, filtering options. Cross-links: 7, 8.8.

`NotificationSpec`: notification-center entry declaration. Key fields: label/title/severity and related payload fields. Cross-links: 8.8.

#### Accessibility and Theming Specs

`StaticAccessibilitySpec` and `AccessibilitySequenceSpec`: static semantic annotations and traversal ordering declarations. Cross-links: 8.7.

`FontRoleBindingSpec`, `CursorSpec`, and `CursorBindingSpec`: semantic font/cursor role declarations and bindings. Cross-links: 8.1, 8.12.

#### Persistence and Migration Specs

`VersionedSnapshot`, `SchemaVersion`, `MigrationStep`, and `MigrationRegistry`: migration graph building blocks for schema evolution. Use `SnapshotMigrator` to apply transitions and `read_version` to route migration logic. Cross-links: 8.11, 13.

[Back to Table of Contents](#table-of-contents)
