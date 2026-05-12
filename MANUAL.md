# gui_do Manual

## 1. Title and Purpose
[Back to Table of Contents](#table-of-contents)

This manual is the primary learning and reference source for gui_do. It is written for developers who need both conceptual understanding and day-to-day implementation guidance: first-time users who want to build correctly from the start, intermediate users who need deeper system-level clarity, and maintainers who must keep documentation synchronized with runtime contracts, exports, and test-enforced guarantees. The document is organized so you can read it linearly for full onboarding or jump directly to targeted system chapters and appendices for operational work.

## 2. Table of Contents
[Back to Table of Contents](#table-of-contents)

- [1. Title and Purpose](#1-title-and-purpose)
- [2. Table of Contents](#2-table-of-contents)
- [3. How to Use This Manual](#3-how-to-use-this-manual)
  - [Learn, Build, and Maintain Modes](#learn-build-and-maintain-modes)
  - [Reading Paths](#reading-paths)
  - [Tri-Lens Markers](#tri-lens-markers)
  - [Contract Alignment](#contract-alignment)
  - [Known Non-Goals](#known-non-goals)
- [4. Conceptual Foundations (Theory)](#4-conceptual-foundations-theory)
- [5. Quickstart Path (Practice)](#5-quickstart-path-practice)
- [6. Architecture and Runtime Model](#6-architecture-and-runtime-model)
- [7. Core Workflow: Build, Bind, Route, Update, Draw](#7-core-workflow-build-bind-route-update-draw)
- [8. Main Systems Reference](#8-main-systems-reference)
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
- [9. Integration Patterns and Composition Recipes](#9-integration-patterns-and-composition-recipes)
- [10. End-to-End Reference Application](#10-end-to-end-reference-application)
- [11. Testing, Diagnostics, and Reliability](#11-testing-diagnostics-and-reliability)
  - [Maintainer Diff Checklist](#maintainer-diff-checklist)
- [12. Performance and Scaling Guidance](#12-performance-and-scaling-guidance)
- [13. Migration, Versioning, and Deprecation Notes](#13-migration-versioning-and-deprecation-notes)
- [14. FAQ and Troubleshooting](#14-faq-and-troubleshooting)
- [15. Appendix](#15-appendix)
  - [Appendix A: Glossary](#appendix-a-glossary)
  - [Appendix B: Lifecycle/Event Sequence](#appendix-b-lifecycleevent-sequence)
  - [Appendix C: System Dependency Map](#appendix-c-system-dependency-map)
  - [Appendix D: API Quick Index](#appendix-d-api-quick-index)
  - [Appendix D.1: Tier Matrix](#appendix-d1-tier-matrix)
  - [Appendix D.2: Selection Heuristics](#appendix-d2-selection-heuristics)
  - [Appendix E: Architecture Templates](#appendix-e-architecture-templates)
  - [Appendix F: Specifications and Option Reference](#appendix-f-specifications-and-option-reference)

## 3. How to Use This Manual
[Back to Table of Contents](#table-of-contents)

This manual is intentionally structured for three practical usage modes. In learn mode, read linearly from conceptual foundations through systems reference so terminology and lifecycle assumptions are established before implementation details. In build mode, use the core workflow and relevant system chapters as a task-oriented playbook while actively coding. In maintain mode, use testing, migration, and appendix sections to validate that docs, runtime behavior, and contracts remain aligned as exports and internals evolve.

### Learn, Build, and Maintain Modes

Learn mode emphasizes mental models: what each subsystem is for, where it appears in runtime lifecycle, and how design choices reduce coupling. Build mode emphasizes executable flows: which specs to create, which feature phases to use, and how to compose actions, routing, overlays, persistence, and state without fragile custom wiring. Maintain mode emphasizes drift prevention: compare root exports, contracts, runtime guarantees, demo composition patterns, and contract test inventory whenever manual updates are made.

### Reading Paths

- Beginner path: Sections 1-7, then 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, and 11.
- Intermediate path: Sections 4-9 in order, then appendices D, D.1, D.2, and F.
- Maintainer path: Sections 2, 6, 8, 11, 13, and appendices C, D, D.1, and F, followed by the maintainer diff checklist.

These paths are intentionally overlapping so developers can switch modes without losing context. If your current task is runtime troubleshooting, start with Section 11 and jump backward only when a conceptual dependency is unclear. If your task is new feature implementation, start with Section 7 and the relevant 8.x chapter, then return to Section 4 if behavior or lifecycle rationale needs deeper grounding.

### Tri-Lens Markers

The manual uses a tri-lens reading approach even when explicit badges are absent: Theory explains why the system exists and which constraints shaped it, Practice explains how to apply it with concrete flow and examples, and Operations explains what must be verified in tests and contracts to keep behavior stable. Read each system chapter through all three lenses for complete understanding. Skipping the operations lens is the most common source of documentation drift and behavior regressions during maintenance.

### Contract Alignment

When chapter guidance appears to conflict with implementation assumptions, contracts and tests are normative. In particular, public surface and stability language is governed by docs under docs/ and enforcement tests in tests/. Runtime behavior guarantees such as scheduler budget clamping and workspace restore report structure must be treated as contract-backed facts, not implementation suggestions. This manual is a practical synthesis layer; contract documents and test suites remain the final authority for normative guarantees.

### Known Non-Goals

- gui_do is not a browser UI framework and does not aim to mirror web platform APIs.
- gui_do is not a retained-mode desktop toolkit with hidden global wiring; explicit spec-driven composition is preferred.
- gui_do is not intended to auto-generate complete applications from minimal metadata without developer-authored feature behavior.
- gui_do does not position internal or infrastructure tiers as the default starting point for most users.

## 4. Conceptual Foundations (Theory)
[Back to Table of Contents](#table-of-contents)

This chapter establishes the conceptual model that makes the rest of gui_do predictable. The core idea is that gui_do is not just a control collection; it is a composition runtime with explicit boundaries between declarative structure and imperative behavior. If you internalize those boundaries here, implementation chapters become straightforward because each API family has a clear role in the same pipeline.

### Data-Driven Design
[Back to Table of Contents](#table-of-contents)

Data-driven design in gui_do means you describe application structure as data first, then let the runtime interpret that data and wire the executable system. Instead of writing broad bootstrap scripts that manually connect scenes, features, action handlers, task-panel toggles, and palette entries in many imperative branches, you define that structure through named specs. The specs express intent, while the runtime owns orchestration. This keeps feature behavior code focused on behavior and UI logic rather than on framework plumbing.

The entry point to that model is the pair of binding/config objects and builders exported at the root: `HostApplicationBindingSpec` and `build_host_application_config`, producing `HostApplicationConfig`, then launching with `bootstrap_host_application`. That two-stage sequence is intentional. In stage one, you construct and validate all structural declarations, including `FeatureSpec`, `RuntimeSceneSpec`, `ActionSpec`, `WindowSpec`, and companion binding specs. In stage two, you execute the already-built config. Separating build from run prevents accidental coupling between declaration-time decisions and loop-time side effects, and it gives maintainers one deterministic artifact to inspect when validating app composition.

This differs sharply from imperative wiring. In an imperative architecture, adding one shortcut can require touching event branches, callback registration points, teardown paths, and focus-order assumptions. In gui_do, a new action is usually a data entry in an `ActionSpec` collection plus optional key metadata. The runtime wiring layer then registers descriptors, binds keys through input-map/action infrastructure, and tears down routing when scene context changes. The feature does not need to know every path through that lifecycle because the spec is interpreted in the same orchestration pipeline as the rest of runtime composition.

One practical payoff is structural reorganization safety. Bootstrap code depends on public symbols and spec values, not on internal folder layout. If you split one feature package into `*_feature.py`, `*_presenter.py`, and `*_logic_feature.py`, or move presenter helpers into separate modules, bootstrap consumers remain unaffected as long as the package surface still exports the same public names. This is why the package-level export boundary matters: data-driven declarations point to stable names, and implementation internals can evolve independently.

Another payoff is testability. Because composition is data, you can build full app configs in unit tests without starting a graphical loop. You can assert that scenes, actions, windows, and bindings were produced as expected before runtime starts. At the feature layer, you can instantiate features against lightweight host doubles, validate `HOST_REQUIREMENTS` behavior, and run targeted lifecycle tests with deterministic setup. Tests become focused on contracts rather than on fragile end-to-end setup scripts.

Specs also function as a forward-compatible boundary. Named dataclass-style specs are self-documenting and extensible: adding new optional fields can preserve existing callers while enabling richer behavior for new consumers. That is substantially safer than positional-argument APIs, where signature evolution often forces broad call-site edits. It also opens the door to generated or persisted configs: while typical apps author specs directly in Python, the model itself is data-friendly and can be serialized or composed by higher-level tooling.

The most important nuance is the boundary of declarative design. gui_do does not attempt to make all behavior declarative. Structure and wiring are declarative: scenes, features, action/route connections, task-panel/menu/palette declarations, and startup composition. Behavior inside features is imperative Python: `build`, `bind_runtime`, `handle_event`, `on_update`, `draw`, and related direct-mode hooks implement actual logic. In short: describe system shape declaratively, implement system behavior imperatively.

See [Appendix F: Specifications and Option Reference](#appendix-f-specifications-and-option-reference).

### Reactive Data and Observable State
[Back to Table of Contents](#table-of-contents)

Reactive state in gui_do is about propagation without explicit fan-out code. In a manual imperative UI approach, when a value changes you must push that new value into every dependent widget. This makes update logic brittle because producers must know all consumers. In gui_do's reactive model, values are observable objects that notify subscribers, so producers publish state changes once and subscribers update themselves through established bindings.

The core primitives are `ObservableValue`, `ObservableList`, and `ObservableDict`. `ObservableValue` wraps a single value and supports subscription callbacks. `ObservableList` and `ObservableDict` extend the same concept to mutable collections and provide structured change payloads (`CollectionChange` with `ChangeKind`) so consumers can react incrementally instead of re-rendering everything. These primitives provide a shared vocabulary for feature-to-feature data sharing, control bindings, and presenter updates.

For burst updates, gui_do provides `reactive_batch` and `is_batching`. `reactive_batch` lets you group related mutations so subscribers observe a coherent post-update state instead of many intermediate transitions. This is valuable when one user action updates multiple observables that represent one logical transaction. Subscribers can then perform one UI refresh or one recomputation pass, reducing unnecessary work and avoiding transient inconsistent states during intermediate assignments.

For derived state, use `ComputedValue` when the value is a pure function of other observables and should remain synchronized automatically. You can manually subscribe to source values and write into another observable, but that pattern spreads derivation logic and disposal bookkeeping across more code paths. `ComputedValue` centralizes the derivation rule and conveys intent clearly: this value is calculated, not authored independently.

Subscription lifecycle discipline is mandatory. The safest default is to attach subscriptions in `bind_runtime`, when sibling features and runtime services are available, and release them in `shutdown_runtime` or equivalent teardown paths. Forgetting disposal leaves stale callbacks alive, which can trigger updates against detached controls and cause memory retention. Subscribing too early in `build` can also fail because runtime dependencies are not fully wired yet.

Controls benefit from this model by binding to observables instead of receiving repeated imperative assignments. Many gui_do controls and control-composition patterns are designed so the feature updates observable state and the view layer responds automatically. This decouples feature logic from concrete widget update choreography. If a control implementation changes later, state producers remain stable because they speak in observables, not control-specific update sequences.

Reactive primitives also support cross-feature collaboration. A logic-oriented feature can own and publish an `ObservableValue` representing status, progress, or derived domain output. Presentation features subscribe and render without needing direct ownership coupling. The producer does not need a list of consumers, and consumers do not need intimate knowledge of producer internals. That loose coupling is especially useful in routed or multi-window scenes where composition can change over time.

Common anti-patterns are consistent across GUI codebases and especially costly here. Polling values in `on_update` instead of subscribing wastes frame budget and introduces lag between change and render. Subscribing before runtime bind often creates ordering bugs. Skipping unsubscription causes phantom callbacks and hard-to-trace teardown faults. Sharing mutable plain Python objects across features without observables breaks propagation guarantees and silently reintroduces manual fan-out complexity. Treat observables as the authoritative runtime signaling layer for live state.

### Feature Composition and Lifecycles
[Back to Table of Contents](#table-of-contents)

Features are gui_do's primary behavior unit. A feature encapsulates a coherent slice of app behavior: what host resources it requires, what controls it creates (if any), how it reacts to input and messages, and how it shuts down. This keeps functionality modular and scene-scoped, so application complexity grows by composition rather than by expanding one central controller.

The base `Feature` class defines lifecycle hooks and dependency declarations through `HOST_REQUIREMENTS`. A feature can declare per-hook host fields and rely on runtime validation via `validate_host_for`, which raises precise errors when required bindings are missing. This makes dependencies explicit and reviewable. Instead of relying on implicit globals or ad hoc constructor injection trees, each lifecycle method documents its required host context as contract data.

Feature subtypes define composition intent. `Feature` is the standard interactive unit for control-tree participation and common lifecycle flow. `LogicFeature` is optimized for domain/message processing without owning visual composition; by default its `on_update` drains queued command messages into `on_logic_command`, making it a strong fit for computation or orchestration concerns. `RoutedFeature` extends message-topic routing and guarantees `app` availability for runtime wiring by extending `host_requirements_for` for `bind_runtime`. `DirectFeature` provides direct-mode hooks (`handle_direct_event`, `on_direct_update`, `draw_direct`) for rendering paths that intentionally bypass the control pipeline.

Lifecycle sequencing is deliberate. `build(host)` sets up structural elements such as roots, windows, controls, and static registrations. `bind_runtime(host)` then attaches dynamic behaviors: subscriptions, routed runtime setup, cross-feature bindings, and key registrations. `handle_event(host, event)` receives routed events and can consume them. `on_update(host)` handles per-frame logic at feature level, while `draw(host, surface, theme)` supports custom drawing in standard feature mode. `shutdown_runtime(host)` is the teardown point for subscriptions and runtime registrations. For direct mode, dedicated direct hooks operate on raw per-frame timing and direct rendering surfaces.

The `demo_features/main/main_feature.py` flow illustrates this model concretely. In `build`, the feature creates the scene root, menu strip, task panel, and tooltip bindings using spec objects (`SceneMenuStripSpec`, `SceneTaskPanelSpec`, `TaskPanelLinearLayoutSpec`, `TaskPanelButtonSpec`, `TaskPanelWindowToggleGroupSpec`). In `bind_runtime`, it calls `setup_routed_runtime` with a routed runtime spec and optionally binds global keys. Structural composition is therefore established first, then dynamic runtime behavior is attached when runtime services are guaranteed available.

Feature communication should remain message- and state-oriented instead of direct object coupling. `FeatureMessage` queueing and dispatch patterns allow one feature to communicate intent while preserving encapsulation. The base feature API includes explicit logic-binding helpers (`bind_logic`, `send_logic_message`, `unbind_logic`) that support logic/presentation splits without hard dependencies on implementation internals. `RoutedFeature` topic-based handling further centralizes message dispatch policy.

Scene assignment is part of lifecycle correctness. Features are registered with scene context (`scene_name`) and participate only when that scene is active. Scene transitions therefore become activation-boundary transitions: outgoing scene features stop receiving active runtime flow, incoming scene features build/bind and assume control. This prevents stale cross-scene event handling and keeps update paths predictable.

The package composition convention used by demo features reinforces those lifecycle guarantees. Public import surfaces are provided by package `__init__.py` files, while internal concerns are separated into feature, presenter, specs, and logic modules. Bootstrap code imports stable package surfaces, not deep internal modules, so teams can refactor internals without rewriting runtime assembly code. Combined with spec-driven runtime composition, this enables maintainable growth: each feature remains independently understandable, testable, and replaceable.

Two high-value composition recipes emerge repeatedly. First, logic/presentation split: a `LogicFeature` owns long-running or domain-heavy work and publishes observable state; a `Feature` or `RoutedFeature` renders and handles UI routing based on that state. Second, presenter-backed windows: feature lifecycle manages runtime and scene integration while presenter-oriented helpers own window/control construction details. Both patterns reduce monolithic feature classes and improve test granularity.

```python
from gui_do import Feature, ObservableValue

class CounterFeature(Feature):
  HOST_REQUIREMENTS = {
    "build": ("app",),
    "bind_runtime": ("app",),
  }

  def __init__(self) -> None:
    super().__init__("counter", scene_name="main")
    self.count = ObservableValue(0)
    self._unsubscribe = None

  def build(self, host) -> None:
    # Create controls here; omitted for brevity.
    pass

  def bind_runtime(self, host) -> None:
    self._unsubscribe = self.count.subscribe(lambda _v: None)

  def shutdown_runtime(self, host) -> None:
    if callable(self._unsubscribe):
      self._unsubscribe()
      self._unsubscribe = None
```

## 5. Quickstart Path (Practice)
[Back to Table of Contents](#table-of-contents)

This chapter is a practical path from clean checkout to a functioning scene-driven app. The goal is not only to produce a running window, but to establish the habits that keep gui_do apps maintainable: declarative config first, feature lifecycle discipline second, and routing/overlay behavior verified by explicit checks.

### Step 1: Install and Verify

```bash
python -m pip install -e . --no-deps
python -m pytest -q tests/test_public_api_exports.py
```

Install in editable mode so documentation-driven experiments reflect local source edits immediately. The quick export contract test validates that your local runtime surface matches documented root imports before you start authoring app code. Also ensure `pygame` and `numpy` are installed; `numpy` is used internally for pixel-buffer workflows through `PixelArray`-based operations.

### Step 2: Create a Minimal Host

Start with a complete `HostApplicationConfig` using current field names. Even when many collections are empty, use explicit fields so intent and extension points are visible from day one.

```python
from gui_do import (
  HostApplicationConfig,
  SceneSetupSpec,
)

config = HostApplicationConfig(
  display_size=(1280, 720),
  window_title="Quickstart App",
  fonts={"default": {"size": 14}},
  font_role_specs=(),
  cursors=(),
  scene_specs=(SceneSetupSpec(scene_name="main", pretty_name="Main"),),
  feature_specs=(),
  window_specs=(),
  runtime_scene_specs=(),
  action_specs=(),
  static_accessibility_specs=(),
  initial_scene_name="main",
)
```

If you prefer the binding-spec builder style, use `HostApplicationBindingSpec` and `build_host_application_config`; both paths produce a valid `HostApplicationConfig` that is consumed by `bootstrap_host_application`.

### Step 3: Add a Feature with Observable State

Create one standard feature that owns state and one visible control. Keep structure in `build`, subscriptions in `bind_runtime`, and cleanup in `shutdown_runtime`.

```python
from pygame import Rect
from gui_do import Feature, ObservableValue, LabelControl


class CounterFeature(Feature):
  HOST_REQUIREMENTS = {
    "build": ("app",),
    "bind_runtime": ("app",),
  }

  def __init__(self) -> None:
    super().__init__("counter_feature", scene_name="main")
    self.count = ObservableValue(0)
    self._label = None
    self._unsubscribe = None

  def build(self, host) -> None:
    root = host.app.scene("main")
    self._label = root.add(LabelControl("counter_label", Rect(24, 24, 240, 32), "Count: 0"))

  def bind_runtime(self, host) -> None:
    def _on_count(value: int) -> None:
      if self._label is not None:
        self._label.text = f"Count: {value}"

    self._unsubscribe = self.count.subscribe(_on_count)
    _on_count(self.count.value)

  def shutdown_runtime(self, host) -> None:
    if callable(self._unsubscribe):
      self._unsubscribe()
      self._unsubscribe = None
```

### Step 4: Add an Action and Runtime Scene Policy

Register one scene action and one runtime scene policy. The key quickstart behavior is explicit exit-key binding through runtime scene config.

```python
from gui_do import ActionSpec, RuntimeSceneSpec

config.action_specs = (
  ActionSpec(
    action_id="exit",
    label="Exit",
    kind="exit",
    category="File",
  ),
)

config.runtime_scene_specs = (
  RuntimeSceneSpec(
    scene_name="main",
    bind_escape_to_exit=True,
    prewarm=False,
  ),
)
```

### Step 5: Run Loop

Create a host class that owns startup and run-loop entrypoint. This keeps app creation deterministic and testable.

```python
from gui_do import bootstrap_host_application


class QuickstartHost:
  def __init__(self, config):
    self.config = config
    self.app = None

  def run(self) -> int:
    self.app = bootstrap_host_application(self.config)
    return int(self.app.run_entrypoint(target_fps=120))
```

### Guided Build Track (Beginner)

- Milestone A: app boots to a single scene with no errors.
- Milestone B: one feature creates one visible control.
- Milestone C: one observable updates one control reactively.
- Milestone D: one action and one hotkey trigger expected behavior.
- Milestone E: one overlay and one toast route without input leakage.
- Milestone F: workspace save/load roundtrip succeeds.

Beginner confidence checklist:
- You can explain where `build` ends and `bind_runtime` begins.
- You can add or remove one feature by editing specs only.
- You can trace one keypress from input routing to action execution.

### Quickstart Failure Modes

- Feature never appears: verify `feature_specs` includes the feature and that `scene_name` matches a declared scene.
- Hotkey does nothing: verify action descriptor registration and input-binding scope (global, scene, or focused window path).
- Overlay blocks unexpected keys: verify overlay flags such as `consume_unhandled_keys` and dismissal options (for example `dismiss_on_escape`) match intended behavior.
- State changes but UI does not: verify subscriptions are attached in `bind_runtime` and not disposed prematurely.

## 6. Architecture and Runtime Model
[Back to Table of Contents](#table-of-contents)

The architecture model for gui_do is intentionally explicit: framework runtime and consumer composition are separated by hard boundaries, public access is tiered, and runtime behavior guarantees are documented and test-enforced. This gives teams freedom to evolve demo or product-level features while preserving stable framework contracts.

### Boundary Model: Framework vs Consumer

`gui_do/` is reusable framework code: runtime loop, feature lifecycle, controls, overlays, events, layout, state, persistence, and diagnostics. `demo_features/` plus `gui_do_demo.py` are consumer composition layers that use framework exports to define app-specific scenes, feature bundles, and runtime behavior. The hard boundary is one-directional: framework code must not import demo code. Consumer entrypoints should import named symbols from the `gui_do` root package rather than internal `gui_do.*` modules. This boundary is enforced by AST-based tests in `tests/test_boundary_contracts.py`, so architecture drift is caught as a contract failure rather than discovered late during refactors.

### Tiered Public API Model

The root package organizes exports by tier in `gui_do/__init__.py`, and tier order communicates recommended abstraction level. Tier 1 is the intended starting point for nearly all new applications: feature classes, declarative runtime specs, binding specs, and bootstrap/config builders. Tier 2 through Tier 7 cover core runtime systems: app/scene management, observables/state, events/actions/input/focus, scheduling/animation, theme/fonts, and telemetry/diagnostics. Tier 8 and above expose deeper composition systems (layout engines, overlays, forms, persistence/state machines, controls, graphics, introspection, and advanced runtime helpers).

Tier numbers are not just organization labels; they are decision guidance. When two tiers can solve the same problem, choose the lower-numbered tier first because it is typically more declarative, more stable, and more integration-aware. Reach into higher tiers when the abstraction boundary is intentional for your use case, not because lower-tier APIs are unfamiliar.

### Runtime Guarantees

- Canonical `GuiEvent` normalization occurs before app-level dispatch.
- Scene-isolated updates apply for scene-contained runtime systems.
- Window-focus candidate ordering is deterministic and sorted by `control_id`.
- Scheduler dispatch budget is clamped to fraction=0.12, floor=0.5 ms, ceiling=4.0 ms.
- Missing settings keys are skipped without aborting workspace restore.

These guarantees are operational contracts. Treat them as assumptions you can design around and test against.

### Event Pipeline

`GuiApplication.process_event` follows a strict order:
1. Normalize raw input into `GuiEvent` via event manager conversion.
2. Handle quit events early and terminate run state when required.
3. Update shared input snapshot/state from normalized event data.
4. Update logical pointer state and apply lock/capture clamping policies.
5. Logicalize pointer events while preserving raw coordinate context.
6. Route pointer/key behavior through overlays and toast interception, including focus adjustments.
7. Route keyboard events through keyboard manager policy and screen handler integration.
8. Route feature handlers, scene dispatch, then fallthrough handlers in order.
9. Honor `propagation_stopped` and `default_prevented` as hard stop signals.

This order matters: it prevents hidden focus races, keeps overlay interaction deterministic, and ensures that keyboard/pointer handling obeys consistent interception rules before scene graph dispatch.

```python
from gui_do import EventManager

def normalize_then_dispatch(self, raw_event):
  gui_event = EventManager().to_gui_event(raw_event)
  return self.app.process_event(gui_event)
```

### Known Non-Goals

- gui_do does not target OS-native widget parity across all platforms.
- gui_do does not replace domain/business-layer architecture decisions.
- gui_do does not present infrastructure tiers as beginner entry points.
- Star-import behavior is not part of public API compatibility guarantees.

## 7. Core Workflow: Build, Bind, Route, Update, Draw
[Back to Table of Contents](#table-of-contents)

The five-phase workflow is the practical programming model for gui_do apps. You can think of it as a contract between your feature code and the runtime orchestrator: compose structure first, attach live runtime wiring second, then process events/messages and frame work predictably.

### Phase Reference

- Build phase: instantiate controls, roots, windows, and local observable containers. Invariant: avoid host-runtime subscriptions and cross-feature runtime coupling here.
- Bind runtime phase: attach host-dependent wiring, subscriptions, action/route bindings, and cross-feature references. Invariant: sibling features and controls are available; this is the safe wiring boundary.
- Route phase: consume input and feature messages through declared mappings, handlers, and action infrastructure.
- Update phase: run frame-based logic, scheduler-driven work, and state transitions.
- Draw phase: render custom visuals for cases that control composition alone cannot express.

When teams violate these phase boundaries, failures often look random (missing controls, dead subscriptions, duplicate bindings). Keeping the boundaries explicit makes failures local and diagnosable.

### Message and Logic Coordination

`FeatureMessage` enables communication without direct feature references as the default coupling strategy. Use `LogicFeature` as a coordination hub when multiple visual features depend on shared domain state or command execution. Prefer observable state for continuous value propagation (status, counts, progress), and prefer messages for discrete intent events (execute action, request transition, trigger workflow step). Combining both gives clear semantics: messages for intent edges, observables for state surfaces.

### When to Use Routed Runtime Specs

Use `RoutedRuntimeSpec` and `RoutedFeatureLifecycleSpec` when one feature needs repeated wiring that would otherwise be boilerplate-heavy: multiple action hotkeys, shortcut overlays bound to lifecycle, task-panel focus toggles, and event subscriptions that must be cleaned up reliably. In those cases, declarative routed specs centralize wiring policy and keep feature classes focused on behavior.

Operationally, `bind_routed_feature_lifecycle` is the attach phase for routed behavior bundles, while `shutdown_routed_feature_lifecycle` is the corresponding teardown phase that removes handlers/subscriptions and prevents stale callbacks after feature deactivation. Treat them as a pair: if lifecycle wiring is spec-driven on bind, lifecycle cleanup should be spec-driven on shutdown.

## 8. Main Systems Reference
[Back to Table of Contents](#table-of-contents)

This reference section covers the sixteen major runtime systems in operational sequence. Each chapter includes rationale, lifecycle placement, public APIs, usage flow, concise examples, advanced patterns, and anti-pattern guidance.

### 8.1 Application Bootstrap and Host Configuration
[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

The bootstrap system is the deterministic entrypoint for assembling a gui_do application from declarative configuration. Instead of having each app invent its own startup sequence, gui_do standardizes startup through `HostApplicationConfig` and `bootstrap_host_application`, optionally generated through binding builders like `build_host_application_config(HostApplicationBindingSpec(...))`. This makes startup reproducible, testable, and auditable: all scene, feature, action, window, cursor, and font composition is described in one configuration graph.

#### Mental model and lifecycle placement

Treat bootstrap as the runtime construction phase before frame-loop behavior begins. You provide a plain config graph; the runtime resolves and wires it into live application state. After bootstrap, the host has a live `GuiApplication` and registered runtime systems that are ready for event/update/draw flow. In lifecycle terms, bootstrap is upstream of every feature hook; it defines the world in which feature lifecycle executes.

#### Primary public APIs and key types

See [Appendix F: Specifications and Option Reference](#appendix-f-specifications-and-option-reference).

Tier 1 entrypoints and builders:
- `HostApplicationConfig`, `HostApplicationBindingSpec`, `bootstrap_host_application`, `build_host_application_config`
- Spec types: `FeatureSpec`, `WindowSpec`, `RuntimeSceneSpec`, `ActionSpec`, `StaticAccessibilitySpec`, `CursorSpec`, `SceneRootSpec`, `AnchoredWindowSpec`, `SceneSetupSpec`, `NotificationSpec`
- Binding helpers: `FeatureWindowBundleBindingSpec`, `SceneBundleBindingSpec`, `ActionBindingSpec`, `CursorBindingSpec`, `FontRoleBindingSpec`, `PaletteBindingSpec`, `SceneSetupBindingSpec`, `RuntimeSceneBindingSpec`, `WindowToggleBindingSpec`, `SceneRootBindingSpec`
- Builder helpers: `build_feature_specs`, `build_window_toggle_specs`, `build_scene_setup_specs`, `build_runtime_scene_specs`, `build_scene_root_specs`, `build_action_specs`, `build_host_application_config`

Tier 2 core runtime types frequently used with bootstrap outcomes:
- `GuiApplication`, `create_display`, `SceneTransitionManager`, `SceneTransitionStyle`, `apply_scene_setup_specs`

#### Typical usage flow

1. Define scene declarations and initial scene identity.
2. Define feature declarations and optional window presentation declarations.
3. Define action and runtime-scene policies.
4. Construct `HostApplicationConfig` directly or through `HostApplicationBindingSpec` plus `build_host_application_config`.
5. Call `bootstrap_host_application` and run `GuiApplication.run_entrypoint(...)`.

#### Minimal example

```python
from gui_do import HostApplicationConfig, SceneSetupSpec, bootstrap_host_application

config = HostApplicationConfig(
  display_size=(1280, 720),
  window_title="Bootstrap Example",
  fonts={"default": {"size": 14}},
  font_role_specs=(),
  cursors=(),
  scene_specs=(SceneSetupSpec(scene_name="main", pretty_name="Main"),),
  feature_specs=(),
  window_specs=(),
  runtime_scene_specs=(),
  action_specs=(),
  static_accessibility_specs=(),
  initial_scene_name="main",
)

app = bootstrap_host_application(config)
app.run_entrypoint(target_fps=120)
```

#### Advanced pattern(s)

For multi-scene, multi-window applications, use binding-spec composition: `HostApplicationBindingSpec` as root, `SceneBundleBindingSpec` for scene bundles, and `FeatureWindowBundleBindingSpec` for feature-plus-window bundles. Then generate concrete runtime config with `build_host_application_config`. This keeps app topology declarative while still allowing focused, reusable bundle factories per feature area.

#### Common mistakes and anti-patterns

- Mutating host/runtime attributes after bootstrap in ways that bypass the declared spec graph.
- Registering features for scenes that are not declared in `SceneSetupSpec` entries.
- Omitting or misspelling `initial_scene_name`.
- Mixing direct `HostApplicationConfig` edits and binding-spec builders without validating final assembled config.

#### Cross-links to related systems

See Chapter 8.2 for feature lifecycle responsibilities, Chapter 8.3 for action/input routing integration, and Chapter 8.11 for workspace restore/state persistence behavior.

[Back to Table of Contents](#table-of-contents)

### 8.2 Feature Lifecycle and Feature Types
[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

The feature lifecycle is gui_do's primary composition contract. Features encapsulate behavior and optional UI, while the runtime provides deterministic sequencing and routing. This allows large apps to grow by adding or replacing focused features instead of centralizing behavior in one monolithic loop controller.

#### Mental model and lifecycle placement

Model each feature as a lifecycle state machine managed by the framework. `build` defines structure, `bind_runtime` attaches runtime dependencies, `handle_event` and `on_update` process interaction/frame work, and `draw` contributes custom rendering when needed. Teardown (`shutdown_runtime`) closes subscriptions and temporary bindings. Lifecycle boundaries are strict because they preserve ordering guarantees across all active features.

#### Primary public APIs and key types

See [Appendix F: Specifications and Option Reference](#appendix-f-specifications-and-option-reference).

- Core types: `Feature`, `DirectFeature`, `LogicFeature`, `RoutedFeature`, `FeatureMessage`, `FeatureManager`
- Lifecycle-adjacent helpers: `setup_routed_feature_runtime`, `bind_routed_feature_lifecycle`, `shutdown_routed_feature_lifecycle`, `register_routed_feature_companions`, `register_companion_logic_features`
- Composition specs: `RoutedRuntimeSpec`, `RoutedFeatureLifecycleSpec`, `LogicBindingSpec`, `EventSubscriptionSpec`, `ActionHotkeySpec`

#### Typical usage flow

1. Choose feature type (`Feature`, `LogicFeature`, `RoutedFeature`, `DirectFeature`) based on runtime behavior needs.
2. Declare `HOST_REQUIREMENTS` per hook.
3. Implement `build` for structure and `bind_runtime` for dynamic wiring.
4. Implement `handle_event` and/or `on_update` for runtime behavior.
5. Register via `FeatureSpec` and verify teardown in `shutdown_runtime`.

#### Minimal example

```python
from pygame import Rect
from gui_do import Feature, ObservableValue, LabelControl

class LifecycleExampleFeature(Feature):
  HOST_REQUIREMENTS = {"build": ("app",), "bind_runtime": ("app",)}

  def __init__(self):
    super().__init__("lifecycle_example", scene_name="main")
    self.text = ObservableValue("Ready")
    self.label = None
    self._unsubscribe = None

  def build(self, host):
    root = host.app.scene("main")
    self.label = root.add(LabelControl("status", Rect(20, 20, 260, 28), ""))

  def bind_runtime(self, host):
    self._unsubscribe = self.text.subscribe(lambda v: setattr(self.label, "text", v))

  def shutdown_runtime(self, host):
    if callable(self._unsubscribe):
      self._unsubscribe()
      self._unsubscribe = None
```

#### Advanced pattern(s)

Use logic/presentation companions: a `LogicFeature` owns durable computation and state publication while a `RoutedFeature` handles UI and routed messages. Register both through companion wiring helpers so lifecycle bind/shutdown of routed pieces remains symmetric and cleanup-safe.

#### Common mistakes and anti-patterns

- Subscribing in `build` before runtime dependencies are fully available.
- Placing heavy custom rendering in standard `Feature` when `DirectFeature` is a better fit.
- Omitting routed lifecycle shutdown when using routed lifecycle specs.
- Treating `HOST_REQUIREMENTS` as documentation-only rather than an enforceable contract.

#### Cross-links to related systems

See Chapter 8.1 for bootstrap graph assembly, Chapter 8.4 for observable-state conventions, and Chapter 8.10 for frame-scheduler integration patterns.

[Back to Table of Contents](#table-of-contents)

### 8.3 Events, Actions, Input Mapping, and Routing
[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

This system converts heterogeneous input into a canonical routing model so behavior remains deterministic under complexity. gui_do normalizes incoming events into `GuiEvent`, then routes through overlays/focus/keyboard/feature/scene fallthrough layers with hard-stop flags. The action subsystem overlays semantic intent (`ActionRegistry`, `ActionManager`) on top of raw key/mouse activity so application logic can reason about named commands instead of device details.

#### Mental model and lifecycle placement

Think in two planes: event transport and action intent. Transport is the `GuiEvent` pipeline from normalization through dispatch. Intent is named actions mapped from bindings and executed in scope-aware order. This system runs continuously during the runtime loop after bootstrap and before/alongside feature update logic.

#### Primary public APIs and key types

See [Appendix F: Specifications and Option Reference](#appendix-f-specifications-and-option-reference).

- Event core: `GuiEvent`, `EventType`, `EventPhase`, `EventManager`, `EventBus`, `InputSnapshot`
- Signals/recording: `Signal`, `SignalConnection`, `EventRecorder`, `EventPlayback`, `RecordedEvent`, `GestureRecognizer`
- Actions and input: `ActionManager`, `ActionRegistry`, `ActionDescriptor`, `ActionMiddleware`, `ActionContext`, `InputMap`, `InputBinding`, `KeyChordManager`, `KeyChord`, `ChordStep`
- Focus/routing context: `FocusManager`, `FocusScope`, `FocusScopeManager`, `WindowFocusManager`, `FocusRing`
- Composition specs: `ActionSpec`, `ActionHotkeySpec`, `ControlKeyBindingSpec`, `EventSubscriptionSpec`

`GuiEvent` fields include: `kind`, `type`, `key`, `pos`, `rel`, `raw_pos`, `raw_rel`, `button`, `wheel_x`, `wheel_y`, `mod`, `text`, `control_id`, `group`, `window`, `task_panel`, `task_id`, `error`, `source_event`, `phase`, `propagation_stopped`, and `default_prevented`.

`EventType` values are: `PASS`, `QUIT`, `KEY_DOWN`, `KEY_UP`, `MOUSE_BUTTON_DOWN`, `MOUSE_BUTTON_UP`, `MOUSE_MOTION`, `MOUSE_WHEEL`, `TEXT_INPUT`, and `TEXT_EDITING`.

#### Typical usage flow

1. Declare actions (`ActionSpec`) as part of host/runtime config.
2. Register action handlers and bindings via input map/chord facilities.
3. Let runtime normalize raw events into `GuiEvent`.
4. Handle feature- or scene-level events where appropriate.
5. Respect `propagation_stopped` and `default_prevented` in custom handlers.

#### Minimal example

```python
from gui_do import ActionSpec, HostApplicationConfig

config = HostApplicationConfig(
  display_size=(1280, 720),
  window_title="Actions Example",
  fonts={"default": {"size": 14}},
  font_role_specs=(),
  cursors=(),
  scene_specs=(),
  feature_specs=(),
  window_specs=(),
  runtime_scene_specs=(),
  action_specs=(
    ActionSpec(action_id="exit", label="Exit", kind="exit", category="File"),
    ActionSpec(action_id="palette_open", label="Open Palette", kind="palette_open"),
  ),
  static_accessibility_specs=(),
  initial_scene_name="main",
)
```

#### Advanced pattern(s)

Use `InteractionStateMachine` (Tier 30) to track guarded input phases (press, drag, release) for complex pointer gestures and tool workflows. Pair with `EventRecorder`/`EventPlayback` to replay deterministic interaction traces in tests and validate regression-sensitive routing behavior.

#### Common mistakes and anti-patterns

- Handling raw pygame events directly in feature logic and bypassing normalization.
- Assuming global action scope when bindings are scene- or window-scoped.
- Forgetting hard-stop semantics for `propagation_stopped` and `default_prevented`.
- Writing custom routing layers that reorder candidate evaluation and break deterministic focus/control precedence.

#### Cross-links to related systems

See Chapter 8.2 for lifecycle hook placement of event wiring, Chapter 8.7 for focus/accessibility interplay, and Chapter 8.8 for overlay interception policies.

[Back to Table of Contents](#table-of-contents)

### 8.4 State and Observables
[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

State in gui_do is designed for explicit reactivity and controlled mutation. Observable primitives decouple producers and consumers, while higher-level state utilities add batching, derived views, and transactional updates. This prevents UI updates from becoming manual fan-out code and supports stable cross-feature collaboration.

#### Mental model and lifecycle placement

Treat observables as the live data transport layer. Features own state, publish changes, and subscribe where needed during runtime bind. Controls and companion features react through subscriptions rather than pull polling. Use transactional/batched tools when many dependent values must change together.

#### Primary public APIs and key types

Tier 3 core:
- `ObservableValue`, `ObservableList`, `ObservableDict`, `CollectionChange`, `ChangeKind`
- `ComputedValue`, `PresentationModel`, `Binding`, `BindingGroup`
- `reactive_batch`, `is_batching`, `InvalidationTracker`
- `CollectionView`, `CollectionViewQuery`, `ObservableStream`, `SelectionModel`, `SelectionMode`

Tier 27 store:
- `AppStateStore`, `StateSelector`, `StateTransaction`

Restore-report contract fields (runtime observability):
- `target_scene`, `switched_scene`, `restored_feature_states`, `restored_scene_nodes`, `applied_settings`, `skipped_settings`, `missing_settings_blocks`

#### Typical usage flow

1. Create feature-owned observables in feature initialization.
2. Bind subscriptions in `bind_runtime` after controls/siblings exist.
3. Use `reactive_batch` for coordinated multi-value updates.
4. Use `ComputedValue` or selectors for derived data.
5. Dispose subscriptions in `shutdown_runtime`.

#### Minimal example

```python
from gui_do import ObservableValue

count = ObservableValue(0)
unsubscribe = count.subscribe(lambda v: print("count", v))
count.value = 1
unsubscribe()
```

#### Advanced pattern(s)

For medium/large apps, centralize domain state in `AppStateStore`, expose narrow `StateSelector` projections to features, and use `StateTransaction` for atomic multi-field updates that should notify consumers coherently. For collection-heavy UIs, combine `ObservableList` with `CollectionView`/`CollectionViewQuery` so sorting and filtering remain reactive without duplicating list mutation logic.

#### Common mistakes and anti-patterns

- Polling observable values in `on_update` instead of subscribing.
- Creating subscriptions in `build` before runtime graph completion.
- Forgetting to release subscription disposers in `shutdown_runtime`.
- Sharing mutable plain lists/dicts between features instead of observable containers.
- Recomputing derived values ad hoc in many handlers instead of using `ComputedValue` or selectors.

#### Cross-links to related systems

See Chapter 8.2 for lifecycle-safe subscription placement, Chapter 8.13 for form and validation state flows, and Chapter 8.14 for data-pipeline/state integration.

[Back to Table of Contents](#table-of-contents)

### 8.5 Controls and Control Composition
[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Controls are gui_do's reusable UI primitives. They provide composition, hit-testing, drawing, and interaction boundaries so features can express behavior without re-implementing rendering and event plumbing. The control system exists to keep UI structure explicit and local: a feature owns its subtree, while cross-feature behavior is coordinated through state/messages rather than by control references.

#### Mental model and lifecycle placement

Think of controls as a scene-local tree rooted in feature-owned panels or windows. You create the tree in `build`, attach dynamic behavior in `bind_runtime`, and then let runtime event/update/draw flow target that tree. Control composition should remain within feature boundaries; when a feature needs to influence another feature's UI, publish state or messages instead of directly mutating foreign controls.

#### Primary public APIs and key types

Tier 12 primary controls:
- `PanelControl`, `LabelControl`, `ButtonControl`, `ToggleControl`, `SliderControl`, `ScrollbarControl`
- `CanvasControl`, `CanvasEventPacket`, `CanvasViewport`
- `FrameControl`, `ImageControl`, `ArrowBoxControl`, `ButtonGroupControl`
- `TabControl`, `TabItem`, `DockWorkspacePanel`

Tier 13 extended controls:
- Inputs and text: `TextInputControl`, `TextAreaControl`, `DropdownControl`, `DropdownOption`, `SpinnerControl`, `RangeSliderControl`, `DatePickerControl`, `TimePickerControl`, `SplitButtonControl`, `SplitButtonOption`, `ChipInputControl`
- Data and navigation: `ListViewControl`, `ListItem`, `DataGridControl`, `GridColumn`, `GridRow`, `TreeControl`, `TreeNode`, `BreadcrumbControl`, `BreadcrumbItem`
- Composite and chrome: `OverlayPanelControl`, `SplitterControl`, `ScrollViewControl`, `WindowControl`, `TaskPanelControl`, `WindowPresenter`, `MenuBarControl`, `MenuEntry`, `SceneMenuStripControl`, `NotificationPanelControl`, `PropertyInspectorPanel`, `ToolbarControl`, `ToolbarItem`, `StatusBarControl`, `StatusSlot`, `ExpanderControl`
- Visual/support: `RichLabelControl`, `ColorPickerControl`, `ProgressBarControl`, `AnimatedImageControl`, `ErrorBoundary`

Declarative control-spec helpers:
- `ControlDefinition`, `build_specs_from_column_section`, `RowCellSpec`, `build_horizontal_row_specs`, `build_multi_column_grid_specs`

#### Typical usage flow

1. In feature `build`, create a scene-local root control (often `PanelControl` or a presenter-backed window).
2. Add child controls and assign identifiers/roles.
3. In `bind_runtime`, connect control behavior to observables, actions, and routed callbacks.
4. Keep control state as a projection of model state, not the source of truth.

#### Minimal example

```python
from pygame import Rect
from gui_do import PanelControl, LabelControl, ButtonControl

def build(self, host):
  self.root = host.app.add(PanelControl("my_root", Rect(0, 0, 400, 300)), scene_name="main")
  self.label = self.root.add(LabelControl("status", Rect(8, 8, 200, 24), "Ready"))
  self.root.add(ButtonControl("go", Rect(8, 40, 100, 28), "Go", on_click=self._on_go))
```

#### Advanced pattern(s)

Use presenter composition for floating windows: subclass `WindowPresenter`, implement `on_create` plus resize/show/hide hooks, and instantiate from feature `build`. This keeps feature lifecycle focused on routing and state, while presenter lifecycle owns window subtree composition. For fault-tolerant rendering islands, wrap volatile subtrees in `ErrorBoundary` so localized failures degrade gracefully instead of collapsing a frame.

#### Common mistakes and anti-patterns

- Holding direct control references across features.
- Treating control properties as canonical domain state instead of reflecting observables.
- Creating controls in `on_update` rather than in `build`.
- Letting presenter setup leak into unrelated feature lifecycle hooks.

#### Cross-links to related systems

See Chapter 8.2 for lifecycle boundaries, Chapter 8.6 for layout ownership, Chapter 8.7 for focus semantics, and Chapter 8.9 for scene/window/task-panel presentation composition.

[Back to Table of Contents](#table-of-contents)

### 8.6 Layout Systems
[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Layout systems provide deterministic spatial composition without forcing manual pixel arithmetic in feature code. gui_do exposes multiple layout families because different UI regions have different geometry constraints: flows, tracks, constraints, docking workspaces, adaptive breakpoints, and virtualization. The purpose is to choose an appropriate geometric model per region while keeping resize behavior predictable.

#### Mental model and lifecycle placement

Layout belongs to structural composition and frame arrangement passes. Controls establish tree membership first, then layout engines compute geometry for that tree. Use the simplest layout family that matches a region's behavior. If a region must adapt by viewport size or data volume, choose adaptive and virtualization systems early rather than layering ad hoc geometry hacks later.

#### Primary public APIs and key types

Tier 8 layout and spatial APIs:
- `LayoutAxis`, `LayoutManager`, `WindowTilingManager`
- `ConstraintLayout`, `AnchorConstraint`
- `DockPane`, `DockTabs`, `DockSplit`, `DockWorkspace`
- `FlexLayout`, `FlexItem`, `FlexDirection`, `FlexAlign`, `FlexJustify`
- `GridLayout`, `GridTrack`, `GridPlacement`
- `CellCaretLayout`, `CellCaretState`, `LayoutAnimator`
- `LayoutPass`, `MeasureContext`, `ArrangeContext`, `LayoutRoot`
- `ResponsiveLayout`, `Breakpoint`
- `SnapGrid`, `AlignmentGuide`, `SnapComposer`, `SnapTarget`
- `FlowLayout`, `FlowItem`, `Viewport`

Tier 28 adaptive constraint layout:
- `ConstraintAttr`, `LayoutConstraint`, `ConstraintSet`, `ConstraintLayoutEngine`, `AdaptivePolicy`, `resolve_adaptive_policy`

Tier 29 virtualization core:
- `MeasureMode`, `MeasurePolicy`, `VirtualizedWindow`, `RecyclePool`, `VirtualizationCore`

#### Typical usage flow

1. Pick one layout owner per container/region.
2. Add controls first, then attach layout metadata.
3. For responsive regions, declare breakpoint/adaptive policy instead of branching on raw width in many places.
4. For long lists/trees/grids, use virtualization to avoid full-materialization cost.

#### Minimal example

```python
from gui_do import FlexLayout, FlexItem, FlexDirection

layout = FlexLayout(direction=FlexDirection.ROW, gap=8)
layout.add(FlexItem(control=sidebar, grow=0, basis=240))
layout.add(FlexItem(control=content, grow=1))
```

#### Advanced pattern(s)

Compose `ConstraintLayoutEngine` with `AdaptivePolicy` to switch between compact and wide panel arrangements at breakpoints while preserving semantic relationships. For workbench-style interfaces, combine `DockWorkspace` for pane composition with `WindowTilingManager` for deterministic top-level window arrangement. In data-heavy regions, pair `VirtualizationCore` with measurement policy tuning to maintain responsive interaction under large datasets.

#### Common mistakes and anti-patterns

- Mixing multiple active layout owners for one container without explicit ownership.
- Hardcoding dimensions where adaptive policy is required.
- Running layout before control tree membership is finalized.
- Ignoring virtualization for large item sets and then compensating with ad hoc update throttling.

#### Cross-links to related systems

See Chapter 8.5 for control composition, Chapter 8.9 for presentation models, and Chapter 12 for scaling guidance when layout complexity increases.

[Back to Table of Contents](#table-of-contents)

### 8.7 Focus and Accessibility
[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Focus and accessibility keep interaction coherent and semantically meaningful. Focus determines which control receives keyboard input and how tab/arrow navigation progresses. Accessibility provides a parallel semantic model that enables assistive consumers and test tooling to reason about interface intent independent of visual layout.

#### Mental model and lifecycle placement

Focus is runtime state layered over the control tree. Accessibility is a semantic tree that should be assembled with control construction and then maintained as controls appear/disappear. During event routing, focus and overlay scope decisions directly influence dispatch order and consumption behavior.

#### Primary public APIs and key types

Focus APIs (Tier 4):
- `FocusManager`, `FocusScope`, `FocusScopeManager`, `WindowFocusManager`, `FocusRing`

Accessibility APIs (Tier 21):
- `AccessibilityRole`, `LivePoliteness`, `AccessibilityNode`, `AccessibilityTree`, `AccessibilityAnnouncement`, `AccessibilityBus`

Related declarative specs (Tier 1):
- `AccessibilitySequenceSpec`, `StaticAccessibilitySpec`, `TaskPanelFocusToggleSpec`

#### Typical usage flow

1. Create focusable controls in `build` and set stable focus order.
2. Register static accessibility semantics for known controls.
3. For dynamic/windowed UI, keep focus ring synchronized with visibility/enabled state.
4. Use focus scopes for modal surfaces.
5. Emit announcements for meaningful live updates when appropriate.

#### Minimal example

```python
from gui_do import AccessibilityTree, AccessibilityNode, AccessibilityRole

tree = AccessibilityTree()
submit = AccessibilityNode(role=AccessibilityRole.BUTTON, name="Submit")
tree.root.add_child(submit)
```

#### Advanced pattern(s)

Use `AccessibilitySequenceSpec` to define scene-level semantic traversal for complex screens, and combine it with `FocusScope` during modal activation so keyboard focus cannot escape dialog subtrees. For task-panel-managed windows, use `TaskPanelFocusToggleSpec` to keep hidden windows out of the active focus ring without writing manual focus cleanup code.

#### Common mistakes and anti-patterns

- Leaving hidden controls in focus traversal.
- Creating duplicate semantic nodes for one logical control.
- Omitting role/name semantics for custom canvas-driven controls.
- Building accessibility structures before control identity/ownership is stable.

#### Cross-links to related systems

See Chapter 8.3 for routing precedence, Chapter 8.5 for control ownership, and Chapter 8.8 for modal overlay capture behavior.

[Back to Table of Contents](#table-of-contents)

### 8.8 Overlays, Dialogs, Notifications, and Command Surfaces
[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Overlay systems provide controlled transient and modal surfaces that sit above scene controls without breaking underlying event invariants. Dialogs, toasts, tooltips, command palettes, and context menus all have different dismissal and routing semantics; gui_do separates those concerns into dedicated managers so each surface type can be configured and tested precisely.

#### Mental model and lifecycle placement

Overlays are top-layer surfaces with first-pass routing privileges for relevant events. If an overlay consumes input, underlying scene controls should not process it. Overlay creation typically happens from feature runtime actions; overlay teardown is driven by dismissal contracts (escape, outside click, selection, timeout, or explicit close).

#### Primary public APIs and key types

Tier 9 overlay/window-surface APIs:
- `OverlayManager`, `OverlayHandle`
- Popup geometry: `Alignment`, `PlacementResult`, `PopupPlacement`, `Side`, `compute_popup_rect`
- Surface managers: `DialogManager`, `DialogHandle`, `ToastManager`, `ToastHandle`, `ToastSeverity`, `ContextMenuManager`, `ContextMenuItem`, `ContextMenuHandle`, `CommandPaletteManager`, `CommandEntry`, `CommandPaletteHandle`, `TooltipManager`, `TooltipHandle`, `MenuBarManager`, `FileDialogManager`, `FileDialogOptions`, `FileDialogHandle`, `NotificationCenter`, `NotificationRecord`, `ResizeManager`, `CursorManager`, `CursorHandle`, `CursorShape`, `DragDropManager`, `DragPayload`, `ClipboardManager`, `TransferData`, `TransferManager`, `ShortcutHelpOverlay`, `ShortcutSection`, `ShortcutEntry`

Tier 1 overlay-related specs:
- `ShortcutOverlaySpec`, `NotificationSpec`

#### Typical usage flow

1. Trigger a surface from action/feature logic.
2. Configure dismissal and event-consumption policy for that surface type.
3. Route follow-up interactions through returned handles where available.
4. Ensure teardown updates focus/visibility state as needed.

#### Minimal example

```python
from gui_do import ToastSeverity

def _on_saved(self, host):
  host.toasts.show("File saved", severity=ToastSeverity.SUCCESS)
```

#### Advanced pattern(s)

Use `ShortcutHelpOverlay` with `ShortcutOverlaySpec` to expose scene-specific command discoverability tied to routed lifecycle setup. For command-heavy apps, combine `CommandPaletteManager` entries with scene/window grouping and dynamic providers so command surfaces reflect active runtime context without duplicating routing logic.

#### Common mistakes and anti-patterns

- Showing overlays without explicit dismissal policy.
- Expecting pointer/key events to fall through after overlay consumption.
- Updating dismissed handles without validity checks.
- Forgetting overlay configuration like `consume_unhandled_keys` when designing keyboard pass-through behavior.

#### Cross-links to related systems

See Chapter 8.3 for event-routing order, Chapter 8.7 for modal focus constraints, and Chapter 8.9 for scene/window presentation coordination.

[Back to Table of Contents](#table-of-contents)

### 8.9 Scene, Window, and Task-Panel Presentation Models
[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

This chapter covers the presentation model that sits between scene-level application modes and window-level work surfaces. Scenes provide context boundaries, windows provide focused interaction regions, and task-panel/menu-strip surfaces provide discoverable control points for visibility and navigation actions. The model exists to keep visibility, focus participation, and command availability synchronized instead of scattered across feature-specific flags.

#### Mental model and lifecycle placement

Treat scenes as top-level runtime modes. Within each active scene, windows are registered presentation units that can be shown, hidden, tabbed, and routed. The task panel is scene chrome that exposes user-facing toggles and navigation entries. All of this should be assembled during feature build/bootstrap composition so runtime bind can safely wire shortcuts and event routes against already-existing controls.

#### Primary public APIs and key types

Presentation specs and models (Tier 1):
- `ScenePresentationModel`, `WindowSpec`, `AnchoredWindowSpec`, `SceneTaskPanelSpec`, `TaskPanelButtonSpec`, `TaskPanelLinearLayoutSpec`, `TaskPanelWindowToggleGroupSpec`, `TaskPanelSceneNavButtonSpec`, `TaskPanelFocusToggleSpec`, `FeatureWindowBundleBindingSpec`, `WindowToggleBindingSpec`, `TabbedPresenterSpec`, `TabBuilderSpec`

Presentation/runtime helpers (Tier 18):
- Visibility and window composition helpers such as `set_window_visible_state`, `toggle_window_visibility`, `create_anchored_feature_window`, `create_feature_presented_window`, `create_presented_anchored_window`, `create_presented_window_from_spec`, `add_window_scene_menu_strip`, `ensure_scene_task_panel`, `add_window_toggle_task_panel_controls`, `add_task_panel_window_toggle_group`, `add_task_panel_scene_nav_button`, `add_scene_task_panel_items`, `register_window_tab_builder_specs`, `setup_feature_presenter_tabs`, `register_tab_update_handlers`
- Tab/presentation routing helpers: `ActiveTabUpdateRouter`, `TabLayoutContext`, `compute_tabbed_window_layout`, `create_tab_control_from_specs`, `setup_feature_presenter_tabs_from_window_content`

#### Typical usage flow

1. Declare scene and window specs (or bundle specs) in host config.
2. Build window content through feature build and presenter helpers.
3. Register task-panel/menu-strip controls for discoverable visibility and navigation actions.
4. Wire focus toggle and routed runtime specs in bind phase.
5. Keep window visibility and task-panel/menu state synchronized through scene presentation model logic.

#### Minimal example

```python
from gui_do import AnchoredWindowSpec, create_anchored_feature_window

spec = AnchoredWindowSpec(
  control_id="inspector_window",
  title="Inspector",
  size=(420, 520),
  anchor="right",
  margin=(12, 12),
)
window = create_anchored_feature_window(host, spec)
```

#### Advanced pattern(s)

For dense tool UIs, compose feature-window bundles with tabbed presenters. Use `TabbedPresenterSpec` and `TabBuilderSpec` for declarative tab content and `ActiveTabUpdateRouter` so update work targets only active tabs. Pair with scene menu-strip integration (`add_window_scene_menu_strip`) and task-panel toggle groups (`add_task_panel_window_toggle_group`) to keep command surfaces aligned with real visibility state.

#### Common mistakes and anti-patterns

- Creating windows in `bind_runtime` when sibling features expect windows during bind.
- Letting task-panel toggle state drift from actual window visibility.
- Mixing scene-scoped actions with window-scoped expectations without explicit route policy.
- Skipping focus-toggle integration when hiding windows, causing tab traversal stalls.

#### Cross-links to related systems

See Chapter 8.2 for feature phase boundaries, Chapter 8.5 for control composition, Chapter 8.7 for focus behavior, and Chapter 8.8 for overlay/menu command surfaces.

[Back to Table of Contents](#table-of-contents)

### 8.10 Scheduling, Timing, Animation, and Transitions
[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Scheduling systems let gui_do perform time-based behavior without sacrificing frame stability. The framework includes timers, tweens, animation sequencing, transitions, rate limiters, and cooperative coroutines so you can express temporal logic at the right abstraction level. This exists to avoid ad hoc per-frame counters and blocking workflows in feature code.

#### Mental model and lifecycle placement

Time-based systems run inside the frame loop and must respect budget limits. Per contract, scheduler dispatch budget is clamped to fraction 0.12 of frame dt milliseconds, with floor 0.5 ms and ceiling 4.0 ms. Use this model when deciding where to place work: visual interpolation and finite-step workflows belong in scheduler/tween/timeline systems; heavy CPU or IO orchestration should be split into staged/cancelable flows.

#### Primary public APIs and key types

Tier 5 scheduling and animation:
- `TaskEvent`, `TaskScheduler`, `Timers`
- `TweenManager`, `TweenHandle`, `Easing`
- `AnimationSequence`, `AnimationHandle`
- `TransitionManager`, `TransitionSpec`, `TransitionEvent`
- `AnimationStateMachine`, `AnimationTransitionMode`, `SceneTimeline`
- `Debouncer`, `Throttler`
- `CooperativeScheduler`, `CoroutineHandle`, `Pause`, `Sleep`, `WaitForEvent`, `WaitForSignal`, `WaitUntil`, `WaitForAll`

Related pipeline primitives (Tier 26):
- `CancellationToken`, `PipelineStage`, `DataflowPipeline`, `PipelineHandle`

#### Typical usage flow

1. Choose abstraction: timer, tween, transition, coroutine, or dataflow pipeline.
2. Register work once and let the runtime tick it each frame.
3. Keep frame-hook (`on_update`) logic small and state-oriented.
4. Cancel or complete outstanding temporal work on scene/feature teardown.

#### Minimal example

```python
from gui_do import Easing

def on_show(self, host):
  self._fade = host.tweens.to(self.panel, "alpha", 255, duration=0.2, easing=Easing.OUT_QUAD)
```

#### Advanced pattern(s)

Use `CooperativeScheduler` for multi-step workflows that wait on signals or staged conditions without blocking the UI thread. Combine `WaitForSignal` and `Sleep` with `DataflowPipeline` for CPU-heavy staged tasks, and only publish final state updates back into observables on safe scheduler checkpoints. This pattern keeps long operations responsive and cancellation-friendly.

#### Common mistakes and anti-patterns

- Running unbounded work in `on_update` instead of scheduler/pipeline primitives.
- Placing blocking IO directly in cooperative coroutines.
- Leaving tweens/coroutines active after scene transitions.
- Assuming budget-free execution under low FPS; budget clamping still applies.

#### Cross-links to related systems

See Chapter 8.2 for lifecycle-safe update placement, Chapter 8.14 for dataflow composition, and Chapter 8.16 for telemetry-backed performance analysis.

[Back to Table of Contents](#table-of-contents)

### 8.11 Persistence and Workspace/Session State
[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Persistence services provide workspace/session continuity so users can resume where they left off. gui_do supports scene restoration, feature state replay, settings replay, and snapshot migration. It also exposes structured restore diagnostics so restore behavior can be inspected and validated rather than guessed.

#### Mental model and lifecycle placement

Treat workspace state as a versioned contract between runtime and disk. Save operations serialize state snapshots at known safe points; restore operations switch scene context, replay feature and node state, and apply settings with resilience to unknown or missing keys. Feature lifecycle should expose state save/restore hooks that are idempotent and version-aware.

#### Primary public APIs and key types

Tier 11 state and persistence:
- `CommandHistory`, `Command`, `CommandTransaction`
- `StateMachine`, `HierarchicalStateMachine`
- `Router`, `RouteEntry`
- `SettingsRegistry`, `SettingDescriptor`
- `WorkspaceState`, `WorkspacePersistenceManager`, `DEFAULT_WORKSPACE_STATE_PATH`
- `SceneSnapshot`, `NodeSnapshot`

Tier 23 undo routing:
- `UndoContextManager`

Tier 32 snapshot and migration:
- `SchemaVersion`, `VersionedSnapshot`, `MigrationStep`, `MigrationRegistry`, `SnapshotMigrator`, `MigrationError`, `make_snapshot`, `read_version`

Restore-report fields (runtime contract):
- `target_scene`, `switched_scene`, `restored_feature_states`, `restored_scene_nodes`, `applied_settings`, `skipped_settings`, `missing_settings_blocks`

#### Typical usage flow

1. Register settings descriptors and feature save-state behavior.
2. Save workspace snapshots at user checkpoints or shutdown.
3. On load, inspect restore report fields to detect skips/missing blocks.
4. When schema changes, migrate snapshots before applying them.

#### Minimal example

```python
report = host.app.load_workspace(path)
if report and report.skipped_settings:
  host.toasts.show("Some settings were skipped during restore")
```

#### Advanced pattern(s)

Use `SnapshotMigrator` with registered `MigrationStep` chains to evolve persisted schemas safely across releases. For multi-surface editors, route undo stacks through `UndoContextManager` so each panel/workspace region has independent undo history while still sharing a common command infrastructure.

#### Common mistakes and anti-patterns

- Assuming all settings keys always exist on restore.
- Loading snapshots without validating/reading snapshot version first.
- Reusing `DEFAULT_WORKSPACE_STATE_PATH` for multi-instance app scenarios.
- Treating restore report as optional telemetry rather than operational truth.

#### Cross-links to related systems

See Chapter 8.1 for config/bootstrap foundations, Chapter 8.2 for feature save/restore hooks, and Chapter 13 for migration/deprecation policy guidance.

[Back to Table of Contents](#table-of-contents)

### 8.12 Theme, Styling, and Visual Systems
[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

The theme system centralizes visual semantics so UI appearance can evolve without touching every control implementation. Fonts, color roles, design tokens, and scoped overrides are all coordinated through dedicated registries/managers. This exists to keep style policy explicit, reusable, and runtime-switchable.

#### Mental model and lifecycle placement

Bootstrap establishes base font/theme resources; features consume roles/tokens during build and draw. Runtime theme changes should invalidate visual caches so the next render pass reflects new values. Use scoped themes when one region intentionally diverges from global appearance, but keep semantic token naming consistent across scopes.

#### Primary public APIs and key types

Tier 6 theme and font APIs:
- `FontManager`, `FontRoleRegistry`, `ColorTheme`, `ThemeManager`, `DesignTokens`, `ScopedTheme`, `ScopedThemeManager`

Tier 22 invalidation:
- `ThemeInvalidationBus`

Related binding specs:
- `FontRoleBindingSpec`, `CursorSpec`, `CursorBindingSpec`

Related lifecycle helper:
- `setup_standard_font_roles`

#### Typical usage flow

1. Declare font assets and role mappings in app config.
2. Reference semantic font/theme roles from controls and presenters.
3. Switch theme through theme manager operations.
4. Let theme invalidation broadcast trigger cache refresh and redraw.

#### Minimal example

```python
def switch_theme(self, host, theme_name: str) -> None:
  host.theme_manager.set_theme(theme_name)
```

#### Advanced pattern(s)

Apply `ScopedThemeManager` for per-window/per-panel style variance while preserving shared semantic tokens for typography and spacing. In custom draw controls, subscribe cache invalidation logic to `ThemeInvalidationBus` so offscreen surfaces and text caches are rebuilt exactly when theme state changes.

#### Common mistakes and anti-patterns

- Hardcoding color/spacing constants in feature draw code.
- Switching themes without invalidating cached rendered assets.
- Registering font roles too late in lifecycle for dependent controls.
- Using scope overrides as one-off patches instead of consistent design policy.

#### Cross-links to related systems

See Chapter 8.1 for bootstrap font/theme declaration, Chapter 8.5 for control rendering consumers, and Chapter 8.16 for operational diagnostics around theme switches and invalidation cost.

[Back to Table of Contents](#table-of-contents)

### 8.13 Text, Input, Forms, and Validation Systems
[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

These systems provide a coherent stack for user input, text handling, form modeling, and validation. Instead of treating each input widget as an isolated control with ad hoc checks, gui_do provides model-level abstractions (`FormModel`, `FormSchema`, validation pipelines, schema runtime, async validators) so correctness, user feedback timing, and field dependencies remain explicit as forms grow.

#### Mental model and lifecycle placement

Think in layers: controls capture input, form/runtime models hold logical field state, validators enforce policy, and text/localization services shape display formatting and language selection. Control creation belongs in `build`; field bindings and validator subscriptions belong in `bind_runtime`; validation timing should respect policy (`on change`, `on submit`, async/debounced).

#### Primary public APIs and key types

Forms and validation (Tier 10):
- `FormModel`, `FormField`, `ValidationRule`, `FieldError`
- `FormSchema`, `SchemaField`, `DocumentModel`
- `WizardFlow`, `WizardStep`, `WizardHandle`
- Validation core: `ValidationResult`, `Validator`, `RequiredValidator`, `RangeValidator`, `LengthValidator`, `PatternValidator`, `CustomValidator`, `DependentValidator`, `ValidationPipeline`

Async and schema-driven runtime:
- Tier 24: `AsyncFieldValidator`, `AsyncFormValidator`
- Tier 31: `FieldSchema`, `FieldGraphSchema`, `ValidationPolicy`, `SchemaFormRuntime`

Text and localization (Tier 14):
- `TextFormatter`, `NumericFormatter`, `PatternFormatter`, `FixedPatternFormatter`
- `TextFlow`, `TextSpan`, `TextSearcher`, `TextMatch`
- `StringTable`, `LocaleRegistry`

Input-related controls (Tier 13):
- `TextInputControl`, `TextAreaControl`, `SpinnerControl`, `DatePickerControl`, `TimePickerControl`, `ColorPickerControl`, `ChipInputControl`

#### Typical usage flow

1. Define logical fields and validation rules in schema/model layer.
2. Create input controls and bind to form state.
3. Select validation policy (`SchemaFormRuntime` + `ValidationPolicy`).
4. Add async validators where server/slow checks are required.
5. Surface validation errors near controls and keep them synchronized with field state.

#### Minimal example

```python
from gui_do import RequiredValidator, PatternValidator, ValidationPipeline

email_validation = ValidationPipeline(
  validators=(
    RequiredValidator("Email is required"),
    PatternValidator(r".+@.+\..+", "Enter a valid email"),
  )
)
```

#### Advanced pattern(s)

Use `SchemaFormRuntime` with `FieldGraphSchema` to model field visibility/dependency graphs (for example: optional billing section shown only when a toggle is enabled), and attach `AsyncFormValidator` for debounced remote checks such as username availability. This keeps synchronous and asynchronous validation in one policy-governed flow rather than splitting logic across many control callbacks.

#### Common mistakes and anti-patterns

- Validating only on submit when product UX expects immediate guidance.
- Ignoring validation policy and forcing all checks on every keystroke.
- Running async validators without stale-result suppression.
- Embedding locale-dependent formatting directly in control callbacks instead of using formatter/localization services.

#### Cross-links to related systems

See Chapter 8.4 for observable binding patterns, Chapter 8.5 for input-control composition, and Chapter 8.14 for pipeline-backed async data/validation flows.

[Back to Table of Contents](#table-of-contents)

### 8.14 Data and Dataflow Helpers
[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Data-heavy interfaces need more than plain lists and manual refresh calls. gui_do provides sources, proxies, caches, diff tools, transactional state stores, virtualization, and cancelable pipelines so large or dynamic datasets remain responsive and correct under frequent updates.

#### Mental model and lifecycle placement

Model data as a staged flow: source acquisition, transformation/filter/sort, optional background pipeline processing, and virtualized presentation. Lifecycle-wise, configure providers and pipeline stages during build/bind, then push updates through observables/selectors so presentation features react incrementally.

#### Primary public APIs and key types

Tier 15 data/collections:
- `VirtualItemSource`, `FixedItemSource`, `SortFilterProxySource`
- `AsyncDataProvider`, `LoadState`, `LoadStateKind`
- `ObjectPool`, `DataCache`, `CacheStats`
- `ListDiffCalculator`, `ListDiff`, `DiffInsert`, `DiffRemove`, `DiffMove`

Tier 26 cancelable pipelines:
- `CancellationToken`, `PipelineStage`, `DataflowPipeline`, `PipelineHandle`

Tier 27 state store:
- `AppStateStore`, `StateSelector`, `StateTransaction`

Tier 29 virtualization:
- `MeasureMode`, `MeasurePolicy`, `VirtualizedWindow`, `RecyclePool`, `VirtualizationCore`

#### Typical usage flow

1. Choose an item source (`FixedItemSource` or custom `VirtualItemSource`).
2. Add `SortFilterProxySource` transforms for user-driven filtering/sorting.
3. Use async providers/pipelines for costly stages.
4. Feed output into virtualized list/grid/tree rendering paths.
5. Use diff and cache tooling to minimize redraw and allocation churn.

#### Minimal example

```python
from gui_do import FixedItemSource, SortFilterProxySource

source = FixedItemSource(items)
proxy = SortFilterProxySource(source)
proxy.set_filter(lambda item: item.active)
proxy.set_sort_key(lambda item: item.name)
```

#### Advanced pattern(s)

Implement a three-stage `DataflowPipeline` (load -> normalize -> rank) with generation cancellation. Each new user query starts a new generation and invalidates stale work via `CancellationToken`. Publish stage progress to observable values and connect resulting items to a virtualized view (`VirtualizationCore` + `RecyclePool`) so performance scales with viewport, not dataset size.

#### Common mistakes and anti-patterns

- Rebuilding full lists when `ListDiffCalculator` can patch incrementally.
- Ignoring pipeline cancellation, leading to stale-result flashes.
- Keeping large unbounded caches without expiration policy.
- Misusing object pools by returning still-referenced objects.

#### Cross-links to related systems

See Chapter 8.4 for reactive state transport, Chapter 8.10 for scheduler coordination, and Chapter 8.16 for telemetry of pipeline and cache behavior.

[Back to Table of Contents](#table-of-contents)

### 8.15 Graphics and Audio Integration Points
[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

When standard control rendering is insufficient, gui_do exposes graphics and audio integration points for richer interactive experiences. Graphics APIs support layered compositing, scene graphs, particle/tile systems, and offscreen targets. Audio APIs provide semantic cue routing so sound playback follows application events rather than low-level control internals.

#### Mental model and lifecycle placement

Graphics custom work usually lives in feature draw hooks or canvas-oriented controls; update hooks drive simulation/state and draw hooks render current state. Audio is event-semantic: features publish cues to an audio bus when meaningful actions occur. Keep asset loading and renderer setup out of per-frame paths.

#### Primary public APIs and key types

Tier 16 graphics/rendering:
- `BuiltInGraphicsFactory`, `DirtyRegionTracker`, `DrawContext`, `DrawPhase`, `AssetRegistry`, `DebugOverlay`
- `SurfaceCompositor`, `Layer`, `ShapeRenderer`, `SurfaceEffects`, `VectorPath`
- `SpriteSheet`, `FrameAnimation`, `ParticleSystem`, `Emitter`, `ParticleLayer`
- `TileSet`, `TileMap`
- Render targets: `RenderTarget`, `LiveRenderTarget`, `OffscreenRenderTarget`, `create_render_target`, `create_surface`
- Scene graph: `Node2D`, `SceneGraph2D`, `Camera2D`

Tier 20 audio:
- `SoundCue`, `SoundBankRegistry`, `SoundEventBus`

#### Typical usage flow

1. Load/register assets once (startup/build).
2. Update simulation in `on_update` (particles, animation frame state, camera).
3. Draw through context/layers/targets in `draw`.
4. Publish semantic audio cues from domain actions.
5. Use dirty-region/target caching to reduce redraw cost where possible.

#### Minimal example

```python
def on_update(self, host):
  self.particles.tick(host.app.dt_seconds)

def draw(self, host, surface, theme):
  self.particles.draw(surface)
```

#### Advanced pattern(s)

Combine `DirtyRegionTracker` with `OffscreenRenderTarget` and `SurfaceCompositor` for large canvases: redraw only changed regions into an offscreen layer, then composite once per frame. Add `SceneGraph2D` + `Camera2D` when world-space transforms and panning/zooming are needed. Route completion/error cues through `SoundEventBus` so audio remains tied to semantic state changes.

#### Common mistakes and anti-patterns

- Full-surface redraw every frame without dirty-region checks.
- Loading assets in draw/update loops.
- Triggering audio on noisy low-level pointer events.
- Forgetting scene teardown cleanup for emitters/animations.

#### Cross-links to related systems

See Chapter 8.2 for draw lifecycle ownership, Chapter 8.5 for canvas/control integration, Chapter 8.10 for timed animation orchestration, and Chapter 8.16 for performance instrumentation.

[Back to Table of Contents](#table-of-contents)

### 8.16 Telemetry, Introspection, and Operational Hooks
[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Operational visibility is required for reliable GUI systems. Telemetry captures performance and behavior traces, introspection exposes inspectable runtime properties, and spatial indexing provides geometric diagnostics. Together these tools make regressions measurable instead of anecdotal.

#### Mental model and lifecycle placement

Enable telemetry before scenario execution, instrument hot paths or rely on built-in spans, then analyze traces after representative interactions. Use property registries and inspector models during runtime diagnosis to inspect control state. Use spatial indexing for hit-test and layout debugging.

#### Primary public APIs and key types

Tier 7 telemetry:
- `TelemetryCollector`, `TelemetrySample`, `configure_telemetry`, `telemetry_collector`
- `analyze_telemetry_log_file`, `analyze_telemetry_records`, `load_telemetry_log_file`, `render_telemetry_report`

Tier 17 introspection:
- `SceneSpatialIndex`
- `ui_property`, `PropertyDescriptor`, `PropertyRegistry`, `property_registry`
- `PropertyInspectorModel`, `InspectedProperty`

#### Typical usage flow

1. Configure telemetry (`TelemetryConfig` or runtime configure call).
2. Execute realistic user scenarios.
3. Analyze records/logs and inspect report hotspots.
4. Use property and spatial inspection tools to validate hypotheses.
5. Apply fixes and rerun the same scenario for comparison.

#### Minimal example

```python
from gui_do import configure_telemetry, analyze_telemetry_records, render_telemetry_report, telemetry_collector

configure_telemetry(enabled=True)
report = analyze_telemetry_records(telemetry_collector().records)
print(render_telemetry_report(report))
```

#### Advanced pattern(s)

Build an operational debug mode that combines telemetry spans, `PropertyInspectorModel` snapshots, and `SceneSpatialIndex` overlays. This enables you to correlate frame spikes with concrete control/property/layout regions and catch regressions introduced by new composition patterns before release.

#### Common mistakes and anti-patterns

- Profiling only idle loops instead of representative workflows.
- Enabling telemetry too late (missing startup/bind spans).
- Ignoring inspector metadata and relying purely on visual guesses.
- Treating diagnostics as optional in maintenance-heavy applications.

#### Cross-links to related systems

See Chapter 8.10 for scheduler-budget interpretation, Chapter 8.11 for persistence diagnostics, and Chapter 12 for sustained scaling analysis.

[Back to Table of Contents](#table-of-contents)

## 9. Integration Patterns and Composition Recipes
[Back to Table of Contents](#table-of-contents)

See [Appendix F: Specifications and Option Reference](#appendix-f-specifications-and-option-reference).

### Recipe 1: Routed Feature + Actions + Shortcut Overlay

Goal: build a feature whose shortcuts are discoverable and lifecycle-managed from one declarative runtime spec. This combination works because action declarations remain centralized while overlay rendering and hotkey toggling remain feature-local.

Pattern:
1. Declare `ActionSpec` entries in app config.
2. Build `RoutedRuntimeSpec` with action hotkeys and one `ShortcutOverlaySpec`.
3. Wrap that in `RoutedFeatureLifecycleSpec`.
4. In feature bind/shutdown, call `bind_routed_feature_lifecycle` and `shutdown_routed_feature_lifecycle`.

```python
from gui_do import (
  RoutedFeature,
  RoutedRuntimeSpec,
  RoutedFeatureLifecycleSpec,
  ShortcutOverlaySpec,
  ActionHotkeySpec,
  bind_routed_feature_lifecycle,
  shutdown_routed_feature_lifecycle,
)

class HelpRoutedFeature(RoutedFeature):
  def __init__(self):
    super().__init__("help_routed", scene_name="main")
    runtime_spec = RoutedRuntimeSpec(
      scene_name="main",
      action_hotkeys=(
        ActionHotkeySpec(action_name="help.toggle", handler=self._toggle_help, key=pygame.K_F9, scene_name="main"),
      ),
      shortcut_overlays=(
        ShortcutOverlaySpec(attr_name="_help_overlay", toggle_action_name="help.toggle", toggle_key=pygame.K_F9),
      ),
    )
    self._lifecycle_spec = RoutedFeatureLifecycleSpec(runtime_spec=runtime_spec)

  def bind_runtime(self, host):
    bind_routed_feature_lifecycle(self, host, self._lifecycle_spec)

  def shutdown_runtime(self, host):
    shutdown_routed_feature_lifecycle(self, host, self._lifecycle_spec)

  def _toggle_help(self, host):
    return None
```

Validation notes: verify the F9 toggle works in scene scope, manual shortcut lines render as expected, and lifecycle shutdown removes registered keys/subscriptions.

### Recipe 2: Window Presenter + Task Panel + Focus Toggle

Goal: present a floating window that is toggled from task-panel controls while focus traversal remains correct. This combination is effective because presenter code owns window internals, while task-panel and routed focus toggles own visibility/focus policy.

Pattern:
1. Define `AnchoredWindowSpec` and presenter class.
2. Create the window during feature `build`.
3. Add task-panel toggle integration and `TaskPanelFocusToggleSpec`.
4. Use visibility helpers for state synchronization.

```python
from gui_do import (
  WindowPresenter,
  AnchoredWindowSpec,
  TaskPanelFocusToggleSpec,
  create_feature_presented_window,
  set_window_visible_state,
)

class InspectorPresenter(WindowPresenter):
  def on_create(self):
    return None

def build(self, host):
  spec = AnchoredWindowSpec(control_id="inspector", title="Inspector", size=(420, 520), anchor="right", margin=(12, 12))
  self.inspector_window = create_feature_presented_window(host, self, spec)

def toggle_inspector(self, host, visible: bool):
  set_window_visible_state(host.app, self.inspector_window, visible)
```

Validation notes: when hidden, window controls should leave traversal order; task-panel state and menu-strip visibility indicators should match actual window visibility.

### Recipe 3: State Store + Persistence + Snapshot Migration

Goal: maintain centralized state that survives schema evolution between versions. This combination works because the store provides one state authority, while snapshot migration provides version-safe load behavior.

Pattern:
1. Initialize `AppStateStore` and expose `StateSelector` views to features.
2. Serialize with `make_snapshot`.
3. On load, inspect version via `read_version`, migrate with `SnapshotMigrator`.
4. Apply restore and inspect report fields (`skipped_settings`, `missing_settings_blocks`, and related fields).

```python
from gui_do import (
  AppStateStore,
  StateSelector,
  SnapshotMigrator,
  MigrationRegistry,
  MigrationStep,
  make_snapshot,
  read_version,
)

store = AppStateStore(initial_state={"counter": 0})
counter_selector = StateSelector(lambda s: s["counter"])
snapshot = make_snapshot(2, store.snapshot())
version = read_version(snapshot)
```

Validation notes: migrations should be deterministic, unknown settings should not abort restore, and restore report should be asserted in integration tests.

### Recipe 4: Dataflow Pipeline + Telemetry + Error Boundary

Goal: run background processing safely, measure bottlenecks, and contain rendering failures. This combination works because cancellation and telemetry protect runtime responsiveness while `ErrorBoundary` keeps UI failures localized.

Pattern:
1. Build staged `DataflowPipeline` with cancellation-aware transforms.
2. Wrap stage execution with telemetry spans.
3. Render results in an `ErrorBoundary` subtree.
4. Publish progress/result state through observables.

```python
from gui_do import DataflowPipeline, PipelineStage, CancellationToken, ErrorBoundary, telemetry_collector

pipeline = DataflowPipeline(stages=(
  PipelineStage("load", load_fn),
  PipelineStage("rank", rank_fn),
))

def run_query(payload):
  with telemetry_collector().span("pipeline", "run_query"):
    return pipeline.run(payload, CancellationToken())
```

Validation notes: stale generations must cancel under rapid input changes, telemetry reports should identify highest-cost stage, and injected presenter exceptions should render boundary fallback rather than crash the scene.

[Back to Table of Contents](#table-of-contents)

## 10. End-to-End Reference Application
[Back to Table of Contents](#table-of-contents)

See [Appendix F: Specifications and Option Reference](#appendix-f-specifications-and-option-reference).

```python
import pygame
from pygame import Rect

from gui_do import (
  FeatureSpec,
  HostApplicationConfig,
  ActionSpec,
  RuntimeSceneSpec,
  SceneSetupSpec,
  RoutedFeature,
  RoutedRuntimeSpec,
  RoutedFeatureLifecycleSpec,
  ShortcutOverlaySpec,
  ActionHotkeySpec,
  ObservableValue,
  LabelControl,
  PanelControl,
  TelemetryConfig,
  bind_routed_feature_lifecycle,
  shutdown_routed_feature_lifecycle,
  bootstrap_host_application,
)


class CounterFeature(RoutedFeature):
  HOST_REQUIREMENTS = {"build": ("app",), "bind_runtime": ("app",)}

  def __init__(self):
    super().__init__("counter", scene_name="main")
    self.count = ObservableValue(0)
    self._label = None
    self._unsubscribe = None
    runtime_spec = RoutedRuntimeSpec(
      scene_name="main",
      action_hotkeys=(
        ActionHotkeySpec(action_name="help.toggle", handler=self._toggle_help, key=pygame.K_F9, scene_name="main"),
      ),
      shortcut_overlays=(
        ShortcutOverlaySpec(attr_name="_help_overlay", toggle_action_name="help.toggle", toggle_key=pygame.K_F9),
      ),
    )
    self._lifecycle = RoutedFeatureLifecycleSpec(runtime_spec=runtime_spec)

  def build(self, host):
    self.root = host.app.add(PanelControl("root", Rect(0, 0, 800, 600)), scene_name="main")
    self._label = self.root.add(LabelControl("count", Rect(16, 16, 260, 30), "Count: 0"))

  def bind_runtime(self, host):
    bind_routed_feature_lifecycle(self, host, self._lifecycle)
    self._unsubscribe = self.count.subscribe(lambda v: setattr(self._label, "text", f"Count: {v}"))

  def shutdown_runtime(self, host):
    if callable(self._unsubscribe):
      self._unsubscribe()
      self._unsubscribe = None
    shutdown_routed_feature_lifecycle(self, host, self._lifecycle)

  def _toggle_help(self, host):
    return None


class DemoHost:
  def __init__(self):
    self.app = None
    self.config = HostApplicationConfig(
      display_size=(1280, 720),
      window_title="Reference App",
      fonts={"default": {"size": 14}},
      font_role_specs=(),
      cursors=(),
      scene_specs=(SceneSetupSpec(scene_name="main", pretty_name="Main"),),
      feature_specs=(FeatureSpec("counter_feature", CounterFeature),),
      window_specs=(),
      runtime_scene_specs=(RuntimeSceneSpec(scene_name="main", bind_escape_to_exit=True),),
      action_specs=(
        ActionSpec(action_id="exit", label="Exit", kind="exit", category="File"),
        ActionSpec(action_id="help.toggle", label="Toggle Help", kind="palette_open", category="View"),
      ),
      static_accessibility_specs=(),
      initial_scene_name="main",
      telemetry=TelemetryConfig(enabled=True),
    )

  def run(self):
    self.app = bootstrap_host_application(self.config)
    self._load_workspace()
    code = self.app.run_entrypoint(target_fps=120)
    self._save_workspace()
    return code

  def _load_workspace(self):
    try:
      self.app.load_workspace("workspace.json")
    except Exception:
      pass

  def _save_workspace(self):
    try:
      self.app.save_workspace("workspace.json")
    except Exception:
      pass
```

### What This Listing Demonstrates

This reference app ties together bootstrap configuration, scene setup, routed feature lifecycle, observable-to-control binding, shortcut-overlay wiring, action declarations, runtime scene exit policy, telemetry configuration, and workspace save/load integration. It is intentionally compact while still showing where each system belongs in build/bind/shutdown and host run orchestration.

### Validation Checklist

1. Application opens and enters the `main` scene.
2. Label renders and updates when `count` changes.
3. F9 help toggle route is registered and callable.
4. Escape exits via `RuntimeSceneSpec(bind_escape_to_exit=True)` policy.
5. Routed lifecycle bind/shutdown paths run without stale handlers.
6. Telemetry can be enabled and records are produced during runtime.
7. Workspace load/save hooks execute without aborting app loop on failure.

[Back to Table of Contents](#table-of-contents)

## 11. Testing, Diagnostics, and Reliability
[Back to Table of Contents](#table-of-contents)

Reliability in gui_do comes from aligning three sources: public surface contracts, runtime operating contracts, and behavior-proving tests. The practical rule is simple: treat docs under `docs/` and high-priority contract tests as normative, and treat this manual as operational guidance that should always reconcile to those contracts. Whenever behavior changes, the fastest path to confidence is contract-test-first validation followed by focused runtime traces.

### Contract Tests

The core contract suite should run on every documentation-sensitive change:

```bash
python -m pytest -q tests/test_public_api_exports.py tests/test_public_api_docs_contracts.py tests/test_runtime_operating_contracts.py tests/test_boundary_contracts.py tests/test_gui_application_workspace_contracts.py
```

What each test validates:
- `test_public_api_exports.py`: `gui_do.__all__` names exist and import cleanly.
- `test_public_api_docs_contracts.py`: documented API contracts and exported names remain aligned.
- `test_runtime_operating_contracts.py`: runtime guarantees (normalization, determinism, scheduler budget clamping, scene scope).
- `test_boundary_contracts.py`: framework/demo boundary rules are preserved.
- `test_gui_application_workspace_contracts.py`: workspace restore behavior and report semantics.

Additional currently discovered contract/runtime files:
- `test_architecture_boundary_docs_contracts.py`
- `test_demo_feature_package_contracts.py`
- `test_core_only_bootstrap_contracts.py`
- `test_runtime_guarantees_and_determinism.py`

### Runtime Behavior Tests

In addition to contract tests, maintain focused behavior tests for workspace roundtrips, overlay/tooltip/cursor routing, layout and animation determinism, control runtime behavior, and accessibility sequencing. This helps catch regressions where APIs remain stable but runtime interaction changes. Favor test scenarios that mirror real user flows (scene transitions, hidden-window focus traversal, modal capture behavior) over isolated micro-cases only.

### Debug and Trace Tools

- `EventRecorder` and `EventPlayback`: capture and replay exact input sequences for reproducible bug reports.
- `DebugOverlay`: inspect live control geometry and rendering diagnostics.
- `PropertyInspectorPanel` with `PropertyInspectorModel`: inspect runtime-exposed UI properties.
- Telemetry analysis stack: `analyze_telemetry_log_file`, `analyze_telemetry_records`, `render_telemetry_report` for frame and pipeline performance triage.

Use these tools in combination: replay the failing trace, capture telemetry during replay, then inspect control properties/spatial boundaries to localize root cause quickly.

### Maintainer Release Runbook

1. Run contract suite and runtime-determinism tests.
2. Validate boundary imports (`gui_do` does not depend on `demo_features`).
3. Run representative scene workflows with telemetry enabled.
4. Verify workspace restore reports include expected fields and no unexpected skips.
5. Confirm API docs/manual references match current `__all__` exports.
6. Re-run critical visual/interaction scenarios (focus cycling, overlays, scene transition).
7. Ship only after contracts, integration tests, and manual coherence checks all pass.

### Regression Triage Workflow

1. Reproduce: capture exact user path and environment assumptions.
2. Trace: record input sequence and telemetry spans.
3. Localize: identify subsystem boundary (routing, layout, persistence, rendering, etc.).
4. Test-first: add failing regression test closest to contract boundary.
5. Patch: apply minimal fix preserving established invariants.
6. Adjacent contracts: rerun neighboring contract/runtime suites to detect collateral effects.

### Maintainer Diff Checklist

Use this checklist on every regeneration pass or targeted chapter update to prevent drift between runtime behavior, contracts, and documentation.

Inventory delta checks:
1. Compare current root exports in gui_do/__init__.py with Appendix D and D.1 entries.
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

[Back to Table of Contents](#table-of-contents)

## 12. Performance and Scaling Guidance
[Back to Table of Contents](#table-of-contents)

### Scheduler Budget Contract

Per runtime operating contracts, scheduler dispatch budget is clamped to:
- fraction: 0.12 of dt milliseconds
- floor: 0.5 ms
- ceiling: 4.0 ms

This gives two guarantees simultaneously: bounded overhead under slow frames and non-starvation under fast frames.

### Dirty-Region Rendering

`DirtyRegionTracker` is the primary optimization for complex custom-draw scenes. Instead of blindly redrawing entire surfaces, mark changed regions and skip unchanged work. The tracker maintains an incremental union rectangle, so `overlaps_dirty()` checks can operate in constant time before evaluating detailed regions.

### Virtualization and Incremental Rendering

- `VirtualizationCore` and `VirtualizedWindow`: render only visible item windows.
- `ListDiffCalculator`: compute minimal change patches (`DiffInsert`, `DiffRemove`, `DiffMove`).
- `RecyclePool`: reuse item views to reduce allocation churn.

Together these tools prevent O(n) redraw/update patterns in large datasets.

### Practical Scaling Checklist

- Enforce scene-scoped updates and handlers.
- Avoid per-frame full collection reallocation; use `ObjectPool` where churn is high.
- Debounce expensive search/form operations (`Debouncer`).
- Use `DataflowPipeline` + `CancellationToken` for preemptible background work.
- Profile representative user interactions, not idle loops.
- Use `DirtyRegionTracker` to gate expensive draw paths.

[Back to Table of Contents](#table-of-contents)

## 13. Migration, Versioning, and Deprecation Notes
[Back to Table of Contents](#table-of-contents)

### Versioned Snapshot Strategy

Recommended snapshot workflow:
1. Write snapshots with `make_snapshot(current_version, state_dict)`.
2. On load, read source version via `read_version(raw)`.
3. Use `SnapshotMigrator.migrate(snapshot)` to apply registered `MigrationStep` transitions.
4. Restore migrated output into runtime state.

`MigrationRegistry` stores one-directional graph edges between versions. `SnapshotMigrator` traverses available paths and raises `MigrationError` when no valid path exists.

### Deprecation Handling

Recommended policy:
- Prefer additive transitions first (new optional fields/parameters).
- Keep old behavior with warnings until a migration path exists.
- Remove legacy only after documented migration guidance and test updates.

No deprecated public APIs are formally cataloged in this generation. Maintain this section as the canonical deprecation ledger when future deprecations are introduced.

### Upgrade Checklist

- Run contract tests before and after upgrade.
- Verify consumers import only from `gui_do` root.
- Validate action/input/focus routing in active scenes.
- Inspect restore report for `skipped_settings` and `missing_settings_blocks`.
- Re-run telemetry baseline scenarios and compare to prior baselines.

[Back to Table of Contents](#table-of-contents)

## 14. FAQ and Troubleshooting
[Back to Table of Contents](#table-of-contents)

### Should I build apps directly with controls or with features?

Use features as your architectural unit. Controls are implementation details inside a feature boundary. A feature gives you lifecycle staging, routing integration, observable wiring discipline, and teardown behavior. A control alone cannot safely own those concerns.

### When should I use RoutedFeature over Feature?

Use `RoutedFeature` when you need declarative routed runtime wiring (hotkeys, shortcut overlays, task-panel focus toggles, event subscriptions) or topic-style message dispatch patterns. If you only need basic lifecycle hooks and a local control subtree, plain `Feature` is usually sufficient.

### Why are some key handlers not firing?

Check, in order: focus ownership, action scope (scene/window/global), overlay capture (including unhandled-key consumption), and active scene mismatch. If uncertain, record an input trace with `EventRecorder` and replay it with `EventPlayback` while inspecting dispatch path.

### Why do toast clicks not pass through?

By runtime contract, toast-hit clicks are consumed to prevent accidental interactions with controls underneath transient surfaces. For intentional click behavior, use the toast's explicit click callback path.

### How do I avoid breaking workspace restore across versions?

Persist versioned snapshots (`SchemaVersion` + `VersionedSnapshot`), register all schema transitions as `MigrationStep`s, and inspect restore reports for skipped/missing settings. Unknown keys should be treated as recoverable compatibility signals, not fatal errors.

### How do I confirm my API usage is within supported surface?

Import from root (`from gui_do import ...`) and run `test_public_api_exports.py`. Avoid relying on internal module paths because stability policy is defined on root exports, not internal structure.

### Why does bind_runtime run before a sibling build?

It should not. The framework guarantees all feature `build` hooks complete before scene `bind_runtime` hooks begin. If behavior appears otherwise, verify scene assignment and feature registration assumptions.

### How do I add a shortcut without touching every key-handler branch?

Declare an `ActionSpec` and wire it through `ActionHotkeySpec` (or a `RoutedRuntimeSpec`). The runtime resolves action registration and key routing declaratively.

[Back to Table of Contents](#table-of-contents)

## 15. Appendix
[Back to Table of Contents](#table-of-contents)

This appendix is operational reference: definitions, lifecycle sequence, dependency mapping, full API quick index, tier matrix, heuristics, and architecture templates.

[Back to Table of Contents](#table-of-contents)

### Appendix A: Glossary
[Back to Table of Contents](#table-of-contents)

**Feature**: A lifecycle-managed unit of behavior. Features encapsulate scene ownership, resource requirements, runtime hooks, and teardown. `Feature`, `DirectFeature`, `LogicFeature`, and `RoutedFeature` differ by dispatch and rendering model, but share the same contract-first lifecycle philosophy.

**Spec**: A declarative data object that describes runtime wiring rather than executing it. Specs are the structural language of gui_do: scene specs, action specs, window specs, routed runtime specs, and binding specs all let you describe topology and policy before execution.

**Host**: A plain Python object used as the bootstrap integration target. Bootstrap populates host members with runtime services and declared bindings, making host attributes the integration boundary between configuration and live systems.

**Scene**: A top-level interaction context. Features belong to a scene scope; routing, updates, and presentation policies operate relative to active scene identity.

**Window presentation**: The visibility/focus/routing model for floating or anchored windows inside a scene. It includes task-panel toggles, menu-strip integration, and tabbed presenter coordination.

**Routed runtime**: A declarative bundle of runtime wiring for routed features (hotkeys, overlays, subscriptions, focus toggles, command palette activation).

**Observable**: A reactive value/container that notifies subscribers on mutation (`ObservableValue`, `ObservableList`, `ObservableDict`).

**Workspace state**: Persisted runtime context used to resume sessions, including scene identity, feature state, node snapshots, and settings replay diagnostics.

**Contract test**: A test that verifies framework-level guarantees (public surface, runtime behavior, boundaries, restore semantics) rather than only local function behavior.

**Tier**: A public API grouping in `gui_do/__init__.py` that communicates abstraction level and usage priority.

[Back to Table of Contents](#table-of-contents)

### Appendix B: Lifecycle/Event Sequence
[Back to Table of Contents](#table-of-contents)

1. `bootstrap_host_application` initializes host/runtime from declarative config.
2. Active-scene feature `build(host)` hooks execute.
3. Active-scene feature `bind_runtime(host)` hooks execute (after all build hooks complete).
4. Runtime loop begins.
5. Per-frame events normalize into `GuiEvent`.
6. Overlay/focus/window/scene routing passes execute.
7. Feature event handlers run according to routing order.
8. Feature update hooks run; scheduler/animation systems dispatch within budget.
9. Draw hooks and control tree rendering execute; frame presents.
10. Scene transition: departing features shut down, arriving features build/bind.
11. Exit path: active features shutdown, optional workspace save persists state.

[Back to Table of Contents](#table-of-contents)

### Appendix C: System Dependency Map
[Back to Table of Contents](#table-of-contents)

Bootstrap and feature lifecycle systems form the spine. Tier 1 bootstrap/configuration depends on spec composition, feature registration, scene/window/action declarations, and theme/font initialization. Features then consume controls, observables, and routing systems.

Layout and focus layers depend on control-tree ownership and scene/window visibility semantics. Overlay systems depend on routing/focus policy to guarantee modal correctness. Persistence depends on state models plus scene/window registration to replay runtime context accurately.

Scheduling and animation depend on lifecycle update flow and scene isolation guarantees. Telemetry and introspection are cross-cutting: they instrument or inspect all layers without becoming the source of behavior decisions.

Audio depends on pygame mixer integration but should be driven through semantic cue publication (`SoundEventBus`). Service scopes (Tier 25) can be introduced at any layer to organize dependencies without violating public-API boundaries.

[Back to Table of Contents](#table-of-contents)

### Appendix D: API Quick Index
[Back to Table of Contents](#table-of-contents)

This index is organized by topic and derived from current root exports.

**Bootstrap and Composition**:
`HostApplicationConfig`, `HostApplicationBindingSpec`, `bootstrap_host_application`, `build_host_application_config`, `FeatureSpec`, `WindowSpec`, `RuntimeSceneSpec`, `ActionSpec`, `StaticAccessibilitySpec`, `CursorSpec`, `SceneRootSpec`, `AnchoredWindowSpec`, `SceneSetupSpec`, `SceneBundleBindingSpec`, `FeatureWindowBundleBindingSpec`, `SceneSetupBindingSpec`, `RuntimeSceneBindingSpec`, `WindowToggleBindingSpec`, `SceneRootBindingSpec`, `PaletteBindingSpec`, `ActionBindingSpec`, `CursorBindingSpec`, `FontRoleBindingSpec`, `make_window_toggle_spec`, `make_scene_nav_action`, `make_exit_action`, `make_palette_open_action`, `make_static_accessibility_spec`, `build_feature_specs`, `build_feature_window_bundle_specs`, `build_window_toggle_specs`, `build_scene_setup_specs`, `build_runtime_scene_specs`, `build_scene_root_specs`, `build_cursor_specs`, `build_font_role_specs`, `build_scene_nav_actions`, `build_action_specs`, `build_scene_bundle_specs`, `build_static_accessibility_specs`, `build_notification_center`

**Feature Lifecycle and Routing**:
`Feature`, `DirectFeature`, `LogicFeature`, `RoutedFeature`, `FeatureMessage`, `FeatureManager`, `RoutedRuntimeSpec`, `RoutedFeatureLifecycleSpec`, `LogicBindingSpec`, `ActionHotkeySpec`, `ControlKeyBindingSpec`, `EventSubscriptionSpec`, `ShortcutOverlaySpec`, `TaskPanelFocusToggleSpec`, `setup_routed_runtime`, `shutdown_routed_runtime`, `bind_routed_feature_lifecycle`, `shutdown_routed_feature_lifecycle`, `register_routed_feature_companions`, `register_companion_logic_features`, `bind_feature_logic_aliases`, `setup_routed_feature_runtime`, `bind_feature_event_subscription`, `unbind_feature_event_subscription`

**Application and Scene Runtime**:
`GuiApplication`, `create_display`, `SceneTransitionManager`, `SceneTransitionStyle`, `apply_scene_setup_specs`, `ScenePresentationModel`, `declare_host_actions`, `apply_runtime_scene_pristine_assets`, `bind_runtime_scene_exit_keys`, `prewarm_runtime_scenes`

**Events, Actions, Input, Focus**:
`GuiEvent`, `EventType`, `EventPhase`, `EventManager`, `EventBus`, `GestureRecognizer`, `EventRecorder`, `EventPlayback`, `RecordedEvent`, `InputSnapshot`, `Signal`, `SignalConnection`, `ActionManager`, `ActionContext`, `ActionMiddleware`, `ActionDescriptor`, `ActionRegistry`, `InputMap`, `InputBinding`, `KeyChordManager`, `KeyChord`, `ChordStep`, `FocusManager`, `FocusScope`, `FocusScopeManager`, `WindowFocusManager`, `FocusRing`, `ValueChangeCallback`, `ValueChangeReason`

**State and Reactivity**:
`ObservableValue`, `PresentationModel`, `ComputedValue`, `reactive_batch`, `is_batching`, `InvalidationTracker`, `ObservableList`, `ObservableDict`, `CollectionChange`, `ChangeKind`, `CollectionViewQuery`, `CollectionView`, `Binding`, `BindingGroup`, `ObservableStream`, `SelectionModel`, `SelectionMode`, `AppStateStore`, `StateSelector`, `StateTransaction`

**Scheduling and Animation**:
`TaskEvent`, `TaskScheduler`, `Timers`, `TweenManager`, `TweenHandle`, `Easing`, `AnimationSequence`, `AnimationHandle`, `TransitionManager`, `TransitionSpec`, `TransitionEvent`, `AnimationStateMachine`, `AnimationTransitionMode`, `SceneTimeline`, `Debouncer`, `Throttler`, `CooperativeScheduler`, `CoroutineHandle`, `Pause`, `Sleep`, `WaitForEvent`, `WaitForSignal`, `WaitUntil`, `WaitForAll`

**Theme and Styling**:
`FontManager`, `FontRoleRegistry`, `ColorTheme`, `ThemeManager`, `DesignTokens`, `ScopedTheme`, `ScopedThemeManager`, `ThemeInvalidationBus`, `setup_standard_font_roles`

**Controls and Presenters**:
`PanelControl`, `LabelControl`, `ButtonControl`, `ToggleControl`, `SliderControl`, `ScrollbarControl`, `CanvasControl`, `CanvasEventPacket`, `CanvasViewport`, `FrameControl`, `ImageControl`, `ArrowBoxControl`, `ButtonGroupControl`, `TabControl`, `TabItem`, `DockWorkspacePanel`, `TextInputControl`, `TextAreaControl`, `RichLabelControl`, `DropdownControl`, `DropdownOption`, `ListViewControl`, `ListItem`, `OverlayPanelControl`, `DataGridControl`, `GridColumn`, `GridRow`, `TreeControl`, `TreeNode`, `SplitterControl`, `SpinnerControl`, `RangeSliderControl`, `ColorPickerControl`, `ScrollViewControl`, `ProgressBarControl`, `AnimatedImageControl`, `ErrorBoundary`, `WindowControl`, `TaskPanelControl`, `WindowPresenter`, `MenuBarControl`, `MenuEntry`, `SceneMenuStripControl`, `NotificationPanelControl`, `PropertyInspectorPanel`, `ToolbarControl`, `ToolbarItem`, `StatusBarControl`, `StatusSlot`, `ExpanderControl`, `DatePickerControl`, `TimePickerControl`, `BreadcrumbControl`, `BreadcrumbItem`, `SplitButtonControl`, `SplitButtonOption`, `ChipInputControl`

**Layout and Geometry**:
`LayoutAxis`, `LayoutManager`, `WindowTilingManager`, `ConstraintLayout`, `AnchorConstraint`, `DockPane`, `DockTabs`, `DockSplit`, `DockWorkspace`, `FlexLayout`, `FlexItem`, `FlexDirection`, `FlexAlign`, `FlexJustify`, `GridLayout`, `GridTrack`, `GridPlacement`, `CellCaretLayout`, `CellCaretState`, `LayoutAnimator`, `LayoutPass`, `MeasureContext`, `ArrangeContext`, `LayoutRoot`, `ResponsiveLayout`, `Breakpoint`, `SnapGrid`, `AlignmentGuide`, `SnapComposer`, `SnapTarget`, `FlowLayout`, `FlowItem`, `Viewport`, `ConstraintAttr`, `LayoutConstraint`, `ConstraintSet`, `ConstraintLayoutEngine`, `AdaptivePolicy`, `resolve_adaptive_policy`

**Overlays and Command Surfaces**:
`OverlayManager`, `OverlayHandle`, `Alignment`, `PlacementResult`, `PopupPlacement`, `Side`, `compute_popup_rect`, `DialogManager`, `DialogHandle`, `ToastManager`, `ToastHandle`, `ToastSeverity`, `ContextMenuManager`, `ContextMenuItem`, `ContextMenuHandle`, `CommandPaletteManager`, `CommandEntry`, `CommandPaletteHandle`, `TooltipManager`, `TooltipHandle`, `MenuBarManager`, `FileDialogManager`, `FileDialogOptions`, `FileDialogHandle`, `NotificationCenter`, `NotificationRecord`, `ResizeManager`, `CursorManager`, `CursorHandle`, `CursorShape`, `DragDropManager`, `DragPayload`, `ClipboardManager`, `TransferData`, `TransferManager`, `ShortcutHelpOverlay`, `ShortcutSection`, `ShortcutEntry`

**Forms, Text, and Localization**:
`FormModel`, `FormField`, `ValidationRule`, `FieldError`, `FormSchema`, `SchemaField`, `DocumentModel`, `WizardFlow`, `WizardStep`, `WizardHandle`, `ValidationResult`, `Validator`, `RequiredValidator`, `RangeValidator`, `LengthValidator`, `PatternValidator`, `CustomValidator`, `DependentValidator`, `ValidationPipeline`, `AsyncFieldValidator`, `AsyncFormValidator`, `FieldSchema`, `FieldGraphSchema`, `ValidationPolicy`, `SchemaFormRuntime`, `TextFormatter`, `NumericFormatter`, `PatternFormatter`, `FixedPatternFormatter`, `TextFlow`, `TextSpan`, `TextSearcher`, `TextMatch`, `StringTable`, `LocaleRegistry`

**Data, Pipeline, and Virtualization**:
`VirtualItemSource`, `FixedItemSource`, `SortFilterProxySource`, `AsyncDataProvider`, `LoadState`, `LoadStateKind`, `ObjectPool`, `DataCache`, `CacheStats`, `ListDiffCalculator`, `ListDiff`, `DiffInsert`, `DiffRemove`, `DiffMove`, `CancellationToken`, `PipelineStage`, `DataflowPipeline`, `PipelineHandle`, `MeasureMode`, `MeasurePolicy`, `VirtualizedWindow`, `RecyclePool`, `VirtualizationCore`

**Persistence, Undo, and Migration**:
`CommandHistory`, `Command`, `CommandTransaction`, `StateMachine`, `HierarchicalStateMachine`, `Router`, `RouteEntry`, `SettingsRegistry`, `SettingDescriptor`, `WorkspaceState`, `WorkspacePersistenceManager`, `DEFAULT_WORKSPACE_STATE_PATH`, `SceneSnapshot`, `NodeSnapshot`, `UndoContextManager`, `SchemaVersion`, `VersionedSnapshot`, `MigrationStep`, `MigrationRegistry`, `SnapshotMigrator`, `MigrationError`, `make_snapshot`, `read_version`

**Graphics, Audio, and Diagnostics**:
`BuiltInGraphicsFactory`, `DirtyRegionTracker`, `DrawContext`, `DrawPhase`, `AssetRegistry`, `DebugOverlay`, `SurfaceCompositor`, `Layer`, `ShapeRenderer`, `SurfaceEffects`, `VectorPath`, `SpriteSheet`, `FrameAnimation`, `ParticleSystem`, `Emitter`, `ParticleLayer`, `TileSet`, `TileMap`, `RenderTarget`, `LiveRenderTarget`, `OffscreenRenderTarget`, `create_render_target`, `create_surface`, `Node2D`, `SceneGraph2D`, `Camera2D`, `SoundCue`, `SoundBankRegistry`, `SoundEventBus`, `TelemetryCollector`, `TelemetrySample`, `configure_telemetry`, `telemetry_collector`, `analyze_telemetry_log_file`, `analyze_telemetry_records`, `load_telemetry_log_file`, `render_telemetry_report`, `SceneSpatialIndex`, `ui_property`, `PropertyDescriptor`, `PropertyRegistry`, `property_registry`, `PropertyInspectorModel`, `InspectedProperty`

**Advanced Runtime Extensions**:
`FrameTimer`, `TabPanelManager`, `WindowRelativeRect`, `resolve_scene_selection_callback`, `minimize_window_menu_entries`, `set_window_visible_state`, `toggle_window_visibility`, `create_anchored_feature_window`, `add_window_scene_menu_strip`, `inset_rect`, `centered_horizontal_strip_layout`, `split_slot_bounds`, `partition_rects`, `place_control`, `place_control_unlabeled`, `register_placed_control`, `add_group_label`, `PlacedControl`, `make_labeled_slot_height_fn`, `apply_category_visibility`, `ControlRegistry`, `ControlDefinition`, `RowCellSpec`, `build_specs_from_column_section`, `build_horizontal_row_specs`, `build_multi_column_grid_specs`, `build_tools_menu_entries`, `add_standard_scene_menu_strip`, `apply_accessibility_sequence`, `apply_accessibility_sequence_from_attrs`, `ensure_scene_scheduler`, `sorted_window_bindings`, `collect_window_toggle_controls`, `apply_window_toggle_accessibility`, `add_window_toggle_task_panel_controls`, `add_task_panel_window_toggle_group`, `setup_scene_command_palette_key`, `register_window_toggle_tooltips`, `initialize_locale_registry`, `bind_input_map_actions`, `register_descriptors`, `resolve_canvas_local_point`, `add_task_panel_button`, `add_task_panel_buttons`, `register_tooltip_specs`, `register_action_hotkeys`, `draw_controls_prewarm`, `ensure_scene_task_panel`, `create_task_panel_linear_layout`, `add_task_panel_scene_nav_button`, `add_scene_task_panel_items`, `centered_overlay_rect`, `create_shortcut_help_overlay`, `add_window_control`, `add_window_label`, `add_window_button`, `add_window_button_row`, `instantiate_features_from_specs`, `register_features_from_specs`, `register_window_presentation_specs`, `register_window_tab_builders`, `build_tab_builder_specs`, `create_tab_control_from_specs`, `compute_tabbed_window_layout`, `setup_feature_presenter_tabs_from_window_content`, `register_window_tab_builder_specs`, `setup_feature_presenter_tabs`, `register_tab_update_handlers`, `create_presented_anchored_window`, `create_presented_window_from_spec`, `create_feature_presented_window`, `ActiveTabUpdateRouter`, `TabLayoutContext`, `declare_host_actions`, `build_host_main_tab_order`, `apply_host_main_accessibility`

**Infrastructure and Service Scope**:
`UiEngine`, `ServiceKey`, `ServiceScope`, `ScopeStack`, `InteractionPhase`, `InteractionContext`, `InteractionTransition`, `InteractionStateMachine`

[Back to Table of Contents](#table-of-contents)

### Appendix D.1: Tier Matrix
[Back to Table of Contents](#table-of-contents)

| Tier | System | Representative Key Types |
|---|---|---|
| 1 | Primary entry points and data-driven APIs | `HostApplicationConfig`, `FeatureSpec`, `bootstrap_host_application`, `RoutedRuntimeSpec`, `HostApplicationBindingSpec` |
| 2 | Core application and scene management | `GuiApplication`, `SceneTransitionManager`, `SceneTransitionStyle`, `apply_scene_setup_specs`, `create_display` |
| 3 | Essential data and state management | `ObservableValue`, `ComputedValue`, `ObservableList`, `Binding`, `CollectionView` |
| 4 | Events, actions, focus and input | `GuiEvent`, `ActionManager`, `InputMap`, `KeyChordManager`, `FocusManager` |
| 5 | Scheduling and animation | `TaskScheduler`, `TweenManager`, `TransitionManager`, `CooperativeScheduler`, `SceneTimeline` |
| 6 | Theme and font management | `ThemeManager`, `DesignTokens`, `ColorTheme`, `FontManager`, `ScopedThemeManager` |
| 7 | Telemetry and diagnostics | `TelemetryCollector`, `configure_telemetry`, `analyze_telemetry_records`, `render_telemetry_report`, `telemetry_collector` |
| 8 | Layout and spatial systems | `FlexLayout`, `GridLayout`, `DockWorkspace`, `ConstraintLayout`, `LayoutPass` |
| 9 | Overlay managers and windows | `OverlayManager`, `DialogManager`, `ToastManager`, `CommandPaletteManager`, `TooltipManager` |
| 10 | Forms and data binding | `FormModel`, `FormSchema`, `ValidationPipeline`, `DocumentModel`, `WizardFlow` |
| 11 | State and persistence | `CommandHistory`, `SettingsRegistry`, `WorkspacePersistenceManager`, `SceneSnapshot`, `Router` |
| 12 | Primary controls | `PanelControl`, `LabelControl`, `ButtonControl`, `CanvasControl`, `TabControl` |
| 13 | Extended controls | `TextInputControl`, `DataGridControl`, `WindowPresenter`, `ErrorBoundary`, `PropertyInspectorPanel` |
| 14 | Text and localization | `TextFormatter`, `TextFlow`, `TextSearcher`, `StringTable`, `LocaleRegistry` |
| 15 | Data and collections | `VirtualItemSource`, `SortFilterProxySource`, `AsyncDataProvider`, `DataCache`, `ListDiffCalculator` |
| 16 | Graphics and rendering | `DirtyRegionTracker`, `SurfaceCompositor`, `SpriteSheet`, `ParticleSystem`, `SceneGraph2D` |
| 17 | Introspection and inspection | `SceneSpatialIndex`, `ui_property`, `PropertyRegistry`, `PropertyInspectorModel`, `InspectedProperty` |
| 18 | Advanced runtime and bootstrapping | `set_window_visible_state`, `create_feature_presented_window`, `bind_routed_feature_lifecycle`, `ActiveTabUpdateRouter`, `TabLayoutContext` |
| 19 | Infrastructure and internals | `UiEngine` |
| 20 | Audio | `SoundCue`, `SoundBankRegistry`, `SoundEventBus` |
| 21 | Accessibility | `AccessibilityRole`, `AccessibilityNode`, `AccessibilityTree`, `AccessibilityAnnouncement`, `AccessibilityBus` |
| 22 | Theme invalidation | `ThemeInvalidationBus` |
| 23 | Undo context routing | `UndoContextManager` |
| 24 | Async form validation | `AsyncFieldValidator`, `AsyncFormValidator` |
| 25 | Scoped service graph | `ServiceKey`, `ServiceScope`, `ScopeStack` |
| 26 | Cancelable dataflow pipeline | `CancellationToken`, `PipelineStage`, `DataflowPipeline`, `PipelineHandle` |
| 27 | Transactional app state store | `AppStateStore`, `StateSelector`, `StateTransaction` |
| 28 | Adaptive constraint layout v2 | `ConstraintAttr`, `ConstraintSet`, `ConstraintLayoutEngine`, `AdaptivePolicy`, `resolve_adaptive_policy` |
| 29 | Unified virtualization core | `MeasureMode`, `MeasurePolicy`, `VirtualizedWindow`, `RecyclePool`, `VirtualizationCore` |
| 30 | Interaction state machine framework | `InteractionPhase`, `InteractionContext`, `InteractionTransition`, `InteractionStateMachine` |
| 31 | Schema-driven form runtime | `FieldSchema`, `FieldGraphSchema`, `ValidationPolicy`, `SchemaFormRuntime` |
| 32 | Portable snapshot and migration layer | `SchemaVersion`, `VersionedSnapshot`, `MigrationRegistry`, `SnapshotMigrator`, `MigrationStep` |

[Back to Table of Contents](#table-of-contents)

### Appendix D.2: Selection Heuristics
[Back to Table of Contents](#table-of-contents)

1. Start with Tier 1. If `HostApplicationConfig`, feature types, and routed/runtime specs solve the problem, stay there.
2. Descend one tier at a time only when you need finer control or specialized behavior.
3. Use Tier 18 helpers for supported bootstrap/runtime extensions.
4. Import from root package only (`from gui_do import ...`) in consumer code.
5. Avoid Tier 19 (`UiEngine`) in application code.

Decision shortcuts:
- App setup: `HostApplicationConfig` + `bootstrap_host_application`
- Cross-feature runtime wiring: lifecycle specs + routed runtime helpers
- Data-heavy UI: virtualization and dataflow before custom loops
- Durable persistence: `WorkspacePersistenceManager` + `SnapshotMigrator`
- Discoverable shortcuts: `ShortcutOverlaySpec` in `RoutedRuntimeSpec`

[Back to Table of Contents](#table-of-contents)

### Appendix E: Architecture Templates
[Back to Table of Contents](#table-of-contents)

**Template 1: Small Single-Scene App**

Use one scene with two to four features, each owning local observables and simple controls. Define core actions in config and bind escape-to-exit in `RuntimeSceneSpec`. Keep composition strictly in Tier 1 plus minimal Tier 12 controls.

**Template 2: Multi-Window Workbench**

Use multiple scenes with menu strip and task panel. Give each window a `WindowPresenter`, and wire visibility/focus through task-panel focus toggle specs. Use feature-window bundle specs for maintainable declaration.

**Template 3: Data-Heavy Analysis Tool**

Use `AsyncDataProvider` plus `SortFilterProxySource`, virtualized rendering (`VirtualizationCore`), and preemptible background transforms (`DataflowPipeline` + `CancellationToken`). Enable telemetry and maintain baseline scenarios.

**Template 4: Long-Running Workflow App**

Use `CooperativeScheduler` for multi-step workflows, publish progress via observables, and use `WizardFlow` for user-guided input. Persist versioned workspace state with migration steps to preserve continuity across releases.

[Back to Table of Contents](#table-of-contents)

### Appendix F: Specifications and Option Reference
[Back to Table of Contents](#table-of-contents)

This appendix is a concise option map for frequently used specification families.

#### Bootstrap Specifications

`HostApplicationConfig`
- Purpose: complete bootstrap payload consumed by runtime startup.
- Key options: `display_size`, `window_title`, `fonts`, `font_role_specs`, `cursors`, `scene_specs`, `feature_specs`, `window_specs`, `runtime_scene_specs`, `action_specs`, `static_accessibility_specs`, `initial_scene_name`, optional `scene_roots`, `telemetry`, `target_fps`, `palette_spec`.
- Cross-links: Chapters 5, 8.1, 10.

`HostApplicationBindingSpec`
- Purpose: high-level binding-centric configuration that builders collapse into `HostApplicationConfig`.
- Key options: scene, feature, window, action, cursor, font-role, palette, telemetry, target-fps entries.
- Cross-links: Chapters 5, 8.1.

#### Feature and Routed Runtime Specifications

`FeatureSpec`
- Purpose: bind one feature attribute to a factory.
- Key options: `attr_name`, `factory`.
- Cross-links: Chapters 5, 8.2, 10.

`RoutedRuntimeSpec`
- Purpose: declarative runtime wiring bundle for routed features.
- Key options: `scene_name`, `scheduler_attr_name`, `scheduler_dispatch_limit`, `logic_bindings`, `action_hotkeys`, `control_key_bindings`, `event_subscriptions`, `shortcut_overlays`, `task_panel_focus_toggles`, `command_palette`.
- Cross-links: Chapters 7, 8.2, 9, 10.

`RoutedFeatureLifecycleSpec`
- Purpose: lifecycle wrapper for runtime spec attach/teardown.
- Key options: `companion_providers`, `runtime_spec`, `runtime_spec_factory`, `runtime_spec_attr_name`, `scheduler_attr_name`.
- Cross-links: Chapters 7, 8.2, 9, 10.

#### Action, Input, and Accessibility Specifications

`ActionSpec`
- Purpose: named action declaration for action registry wiring.
- Key options: `action_id`, `label`, `kind`, optional `target`, `category`, `key`.
- Cross-links: Chapters 5, 8.3, 10.

`ActionHotkeySpec`
- Purpose: bind an action to a handler and optional key/scope.
- Key options: `action_name`, `handler`, optional `key`, `scene_name`.
- Cross-links: Chapters 8.2, 8.3, 9.

`ControlKeyBindingSpec`
- Purpose: key-to-control activation binding by control attribute name.
- Key options: `key`, `control_attr`, optional `action_name`, `scene_name`.
- Cross-links: Chapters 8.3, 9.

`StaticAccessibilitySpec` and `AccessibilitySequenceSpec`
- Purpose: semantic role/label and focus/sequence annotation.
- Key options: control identity, semantic role, ordering metadata.
- Cross-links: Chapters 8.1, 8.7.

#### Window, Task-Panel, and Overlay Specifications

`WindowSpec` and `AnchoredWindowSpec`
- Purpose: declare window registration plus anchored geometry/chrome behavior.
- Key options: window identity/toggle metadata and anchor/size/margin settings.
- Cross-links: Chapters 8.1, 8.9.

`SceneTaskPanelSpec`, `TaskPanelButtonSpec`, `TaskPanelLinearLayoutSpec`, `TaskPanelWindowToggleGroupSpec`, `TaskPanelSceneNavButtonSpec`, `TaskPanelFocusToggleSpec`
- Purpose: define task-panel chrome, controls, and focus-correct window toggling.
- Key options: panel geometry/behavior and per-button/per-toggle action metadata.
- Cross-links: Chapters 8.7, 8.9, 9.

`ShortcutOverlaySpec`
- Purpose: configure feature-owned shortcut overlay behavior.
- Key options: `attr_name`, dimensions/offsets, `toggle_action_name`, `toggle_key`, `toggle_scene_name`, `manual_shortcut_lines`, `manual_section_title`, prepend/filter/exclude options.
- Cross-links: Chapters 8.8, 9, 10.

`NotificationSpec`
- Purpose: notification-center/toast declaration record.
- Key options: message/severity/display metadata.
- Cross-links: Chapters 8.8, 9.

#### Persistence and Migration Specifications

`WorkspaceState`
- Purpose: structured persisted session data consumed by restore pipeline.
- Key notes: restore reports include `target_scene`, `switched_scene`, `restored_feature_states`, `restored_scene_nodes`, `applied_settings`, `skipped_settings`, `missing_settings_blocks`.
- Cross-links: Chapters 8.11, 11, 13.

`SchemaVersion`, `VersionedSnapshot`, `MigrationStep`, `MigrationRegistry`, `SnapshotMigrator`
- Purpose: versioned snapshot and migration graph.
- Key notes: one-directional steps; unresolved paths raise `MigrationError`.
- Cross-links: Chapters 8.11, 13.

[Back to Table of Contents](#table-of-contents)
