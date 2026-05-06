# gui_do Manual

## Title and Purpose

[Back to Table of Contents](#table-of-contents)

This manual is the primary end-to-end learning and reference source for gui_do. It is written for application developers who need a practical path from first principles to production patterns and for maintainers who need a stable operational reference that stays aligned with code, tests, and contracts. The document is organized so that conceptual foundations come first, system-level reference follows, and operational guidance closes the loop for testing, migration, and long-term maintenance.

## Table of Contents

- [Title and Purpose](#title-and-purpose)
- [How to Use This Manual](#how-to-use-this-manual)
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

## How to Use This Manual

[Back to Table of Contents](#table-of-contents)

This manual supports three practical workflows that map to the real way teams use gui_do. In a learning workflow, you should read from theory to implementation because each later section assumes terms, lifecycle boundaries, and architectural decisions introduced earlier. In a build workflow, you should jump directly to the relevant system chapter and then return to adjacent chapters when integration questions appear. In a maintenance workflow, you should treat this document as an operational artifact that must remain synchronized with root exports, contracts, tests, and demo composition practices.

The manual is intentionally structured as a progression from model to mechanism. Conceptual Foundations explains why gui_do emphasizes data-driven application structure and reactive state over ad-hoc wiring. Quickstart then gives an immediately useful assembly path, while Architecture and Core Workflow clarify runtime ordering and lifecycle placement. The system reference chapters are then organized by concern so you can reason about boundaries instead of searching by symbol alone.

The expected reading style is selective but disciplined. When you are implementing features, read your target system chapter fully, then read the cross-linked chapters it references before making architectural choices. This avoids common mistakes where a design appears correct within one subsystem but violates assumptions in routing, focus, persistence, or scheduler behavior.

### Reading Paths

Beginner path:
1. Read Conceptual Foundations (Section 4) fully.
2. Work through Quickstart Path (Section 5).
3. Read Architecture and Runtime Model (Section 6).
4. Read Core Workflow (Section 7).
5. Read systems 8.1 through 8.4 before building your first multi-feature scene.
6. Use the End-to-End Reference Application (Section 10) as a map when wiring your own app.

Intermediate path:
1. Refresh Conceptual Foundations only where your mental model is weak.
2. Read Section 7 and the system chapters you are actively composing.
3. Use Integration Patterns (Section 9) to compose multiple systems coherently.
4. Keep Appendix D and D.2 nearby for API selection and abstraction-level decisions.

Maintainer path:
1. Inventory changes in root exports, contracts, tests, and demo composition patterns.
2. Use Testing, Diagnostics, and Reliability (Section 11) and the Maintainer Diff Checklist.
3. Validate navigation integrity and chapter-to-appendix consistency before publishing manual updates.

### Tri-Lens Markers

This manual is authored through three complementary lenses.

- Learn: explains conceptual intent, rationale, and mental models.
- Build: explains implementation flow, practical defaults, and composition techniques.
- Maintain: explains conformance checks, diff review, and long-horizon operational stewardship.

If you are short on time, prefer Build-first reading for immediate work and then backfill Learn sections to avoid accidental anti-patterns. Maintain sections should be treated as release-quality gates, not optional notes.

### Contract Alignment

Behavioral guarantees in this manual align to contract sources in docs and tests. The normative runtime behavior sources are docs/runtime_operating_contracts.md, docs/public_api_spec.md, and docs/architecture_boundary_spec.md. Public API surface commitments are anchored to gui_do/__init__.py exports. Contract and runtime tests under tests are the executable verification layer that confirms those guarantees remain true.

When this manual and a contract source diverge, treat contract documents and enforcing tests as authoritative and update manual prose accordingly. The goal is not literary consistency; it is behavioral accuracy under current code.

### Known Non-Goals

- gui_do is not a general-purpose game engine.
- gui_do does not hide pygame primitives when low-level rendering control is needed.
- gui_do does not provide native operating-system widgets.
- gui_do is not a no-code or drag-only GUI framework.
- gui_do does not promise stability for internal-only modules outside public exports.

## Conceptual Foundations (Theory)

[Back to Table of Contents](#table-of-contents)

### Data-Driven Design

[Back to Table of Contents](#table-of-contents)

Data-driven design in gui_do means that application structure is described as data first, then executed by runtime machinery second. Instead of writing long imperative setup code that manually instantiates controls, registers handlers, and wires keyboard routes in place, you declare intent through spec objects. This separates what the application should contain from when and how each part is wired. The result is predictable startup behavior and a clearer boundary between architecture and behavior.

At the center of this model is the Tier 1 spec pipeline: `HostApplicationBindingSpec` plus builder helpers such as `build_feature_specs`, `build_action_specs`, and `build_scene_bundle_specs`, culminating in `build_host_application_config`. The builder stage resolves cross-links, applies normalization, and materializes a full `HostApplicationConfig`. The execution stage starts only when `bootstrap_host_application` receives that config. This two-stage design is deliberate because it gives you one stable object graph to inspect and test before the runtime loop begins.

This differs from imperative wiring in an important operational way. In imperative code, introducing a shortcut often requires editing event branches, callback registration, and teardown paths in multiple places. In the data-driven path, you declare an `ActionSpec` (and related key bindings such as `ActionHotkeySpec` or `ControlKeyBindingSpec`) and let runtime helpers perform registration and scene-scoped routing. The cleanup path is then governed by scene/runtime lifecycle rather than by handwritten teardown branches.

Data-driven design also protects bootstrap code from internal package refactors. Bootstrapping depends on exported symbols and spec values, not on internal module layout. A feature package can split presenter logic, move helpers, or reorganize files while keeping its package-level public surface stable; the config entry points remain unchanged. This is why architecture changes inside feature packages typically do not force bootstrap edits.

The model is highly testable because configuration is plain data. You can build a complete host configuration in a unit test, assert expected feature/action/window bindings, and validate error behavior without rendering a window. You can also instantiate feature objects with lightweight hosts and verify lifecycle contracts independently from pygame loop execution.

Specs also serve as a serialization-friendly boundary. Dataclass specs like `FeatureSpec`, `WindowSpec`, `RuntimeSceneSpec`, `SceneSetupSpec`, `SceneRootSpec`, `CursorSpec`, and `PaletteBindingSpec` use named fields that are self-describing and forward-compatible. Adding optional fields is safer than changing positional-argument conventions, and machine-generated config pipelines become practical because inputs are structured records rather than ad-hoc call sequences.

The architectural boundary is explicit: wiring is declarative, behavior is imperative. Scene composition, action routing declarations, runtime scene setup, and feature/window registration are data-driven. Feature logic inside methods such as `handle_event`, `on_update`, and `draw` remains imperative Python by design. In practice, this gives teams both stability and flexibility: stable wiring contracts with full freedom to implement rich behavior per feature.

### Reactive Data and Observable State

[Back to Table of Contents](#table-of-contents)

Reactive state in gui_do means consumers subscribe once and receive updates automatically when source values change. Producers do not need direct references to all consumers. This is a major shift from imperative UI update style, where every mutation must manually push updates into labels, lists, badges, and secondary state. Reactive flow centralizes mutation and decentralizes observation.

Tier 3 exports provide the foundational primitives: `ObservableValue` for scalar state, `ObservableList` and `ObservableDict` for mutable collections, and `CollectionChange` plus `ChangeKind` for describing collection deltas. This evented model allows renderers, presenters, and logic components to observe one source of truth while staying decoupled from the code that mutates it.

`reactive_batch` and `is_batching` are important for throughput-sensitive updates. If a workflow mutates several observables in one logical transaction, batching prevents intermediate notification storms and emits consolidated updates after the batch completes. Use batching for operations like list refresh + selection fixup + summary recompute, where intermediate states are not meaningful to UI subscribers.

`ComputedValue` addresses derived state directly. Instead of manually subscribing to source observables and writing into a second `ObservableValue`, `ComputedValue` models the dependency as a first-class reactive projection. Manual derivation is still valid when custom timing or side effects are required, but `ComputedValue` is typically clearer for pure data derivations.

Subscription lifecycle discipline is mandatory. In current lifecycle contracts, most subscriptions are best created in `bind_runtime` (after feature construction and cross-feature availability) and removed in `shutdown_runtime`. Registering too early can race control availability; forgetting teardown produces stale callbacks and retain cycles that keep dead features reachable.

Control binding should be data-centric: mutate observables, let bindings update controls. When controls are fed observable-backed values, the rendering layer reacts to change notifications without feature code manually poking widget internals each frame. This keeps feature logic focused on domain intent instead of display bookkeeping.

Cross-feature sharing works best when one feature owns a reactive value and others subscribe via runtime wiring. The owner stays agnostic about consumers, and consumers depend only on published state shape, not implementation internals. This pattern is especially useful for logic/presentation splits where `LogicFeature` instances publish state and UI features consume it.

Common anti-patterns are consistent across projects: polling for changes in `on_update` instead of subscribing, subscribing in `build` before runtime wiring is complete, forgetting to unsubscribe in teardown, and passing mutable plain containers across feature boundaries without observability. Each of these bypasses deterministic reactive contracts and usually manifests as stale UI, excess CPU cost, or ghost callbacks.

### Feature Composition and Lifecycles

[Back to Table of Contents](#table-of-contents)

Features are the primary composition unit in gui_do. A feature owns behavior boundaries, lifecycle hooks, declared host dependencies, and optional message-driven coordination with peers. Applications are built by composing multiple features within scene scope rather than by centralizing behavior in one monolithic event loop module.

The core base class is `Feature`, with specialized variants `DirectFeature`, `LogicFeature`, and `RoutedFeature`. `Feature` is the standard control-tree participant for most UI behavior. `DirectFeature` is for frame-timed direct rendering paths and exposes `on_direct_update(host, dt_seconds)` plus `draw_direct`, which is useful for effects that should bypass control-tree abstraction. `LogicFeature` is intended for non-visual domain behavior and message-command processing. `RoutedFeature` extends message routing conventions with topic-dispatch helpers.

Current lifecycle hooks are explicit in `Feature`: `build(host)`, `bind_runtime(host)`, `handle_event(host, event)`, `on_update(host)`, `draw(host, surface, theme)`, and `shutdown_runtime(host)`, plus registration hooks and optional persistence hooks (`save_state` and `restore_state`). `FeatureManager` invokes these in coordinated passes and also separates direct-feature update/draw paths from regular feature update/draw paths.

`HOST_REQUIREMENTS` provides declarative dependency contracts per hook. A feature can declare required host attributes per lifecycle phase, and `validate_host_for` enforces them before invocation. This removes hidden assumptions and makes host-shape failures explicit early, which is especially valuable when features are reused across scenes or demo assemblies.

Inter-feature communication is intentionally loose. The `FeatureMessage` envelope provides structured transport (`sender`, `target`, `payload`), and features can enqueue/drain messages through manager-mediated delivery rather than hard references. `LogicFeature` and `RoutedFeature` both use message draining patterns (`command`-oriented and `topic`-oriented, respectively), which supports composition without tight type coupling.

Scene assignment is handled through the feature `scene_name`. Manager iteration limits event/update/draw calls to active scene entries, and scene transitions rebuild which features are considered active. This prevents stale features from previous scenes receiving runtime calls, reducing cross-scene state bleed and simplifying mental models for scene-local behavior.

The package composition convention in demo features reinforces this architecture: package-level exports are public contracts, while internal modules split concerns (feature lifecycle glue, presenter/window composition, specs/constants, optional logic companions). Keeping bootstrap imports at package boundaries preserves refactor freedom and keeps data-driven config stable over time.

Three composition recipes are particularly effective. First, logic-plus-presentation split: a `LogicFeature` maintains derived domain state, while a UI feature consumes and displays it. Second, presenter-centered windows: a feature handles lifecycle and delegates layout assembly to `WindowPresenter`-style helpers. Third, background orchestration: logic features coordinate cooperative or scheduled work and publish progress through observables/messages, allowing UI features to stay responsive.

## Quickstart Path (Practice)

[Back to Table of Contents](#table-of-contents)

This quickstart path is intentionally practical: install, verify contracts, build one minimal host, add one feature, wire one action, and run the loop. It is designed to produce a working baseline with explicit checkpoints, so you can detect configuration errors early before adding system complexity.

### Step 1: Install and Verify

[Back to Table of Contents](#table-of-contents)

```bash
python -m pip install -e . --no-deps
python -m pytest -q tests/test_public_api_exports.py
```

Runtime notes:
- Install pygame and numpy in your environment. gui_do expects pygame for event/rendering and uses numpy internally for pixel-buffer operations (for example through PixelArray-related flows).
- If this first contract test fails, do not continue quickstart work until root exports are consistent.

### Step 2: Create a Minimal Host

[Back to Table of Contents](#table-of-contents)

Use `HostApplicationConfig` directly with the current required fields.

```python
import pygame

from gui_do import (
  HostApplicationConfig,
  TelemetryConfig,
  CursorSpec,
  SceneSetupSpec,
  FeatureSpec,
  RuntimeSceneSpec,
  ActionSpec,
  StaticAccessibilitySpec,
)


class MinimalHost:
  def __init__(self) -> None:
    self.config = HostApplicationConfig(
      display_size=(1280, 720),
      window_title="gui_do quickstart",
      fonts={"default": {"system": "arial", "size": 14}},
      font_role_specs=(
        {"body": {"size": 14, "font": "default"}},
      ),
      cursors=(
        CursorSpec("normal", "demo_features/data/cursors/cursor.png", (1, 1)),
      ),
      scene_specs=(
        SceneSetupSpec(name="main", pretty_name="Main", make_initial=True),
      ),
      feature_specs=(
        FeatureSpec("counter_feature", lambda: CounterFeature()),
      ),
      window_specs=(),
      runtime_scene_specs=(
        RuntimeSceneSpec(scene_name="main", bind_escape_to_exit=True, prewarm=False),
      ),
      action_specs=(
        ActionSpec(action_id="exit", label="Exit", kind="exit", category="File"),
      ),
      static_accessibility_specs=(
        StaticAccessibilitySpec("counter_label", "label", "Counter value"),
      ),
      initial_scene_name="main",
      telemetry=TelemetryConfig(enabled=False),
      target_fps=120,
    )
```

The key required fields are `display_size`, `window_title`, `fonts`, `font_role_specs`, `cursors`, `scene_specs`, `feature_specs`, `window_specs`, `runtime_scene_specs`, `action_specs`, `static_accessibility_specs`, and `initial_scene_name`. Keep this object small at first; add complexity only after the baseline runs.

### Step 3: Add a Feature with Observable State

[Back to Table of Contents](#table-of-contents)

```python
from pygame import Rect

from gui_do import Feature, ObservableValue, LabelControl


class CounterFeature(Feature):
  HOST_REQUIREMENTS = {
    "build": ("app",),
    "bind_runtime": (),
    "shutdown_runtime": (),
  }

  def __init__(self) -> None:
    super().__init__("counter_feature", scene_name="main")
    self.count = ObservableValue(0)
    self.counter_label = None
    self._unsubscribe_count = None

  def build(self, host) -> None:
    self.counter_label = host.app.add(
      LabelControl("counter_label", Rect(24, 24, 320, 36), text="Count: 0"),
      scene_name="main",
    )

  def bind_runtime(self, host) -> None:
    def _on_count_changed(value):
      self.counter_label.text = f"Count: {value}"

    self._unsubscribe_count = self.count.subscribe(_on_count_changed)

  def shutdown_runtime(self, host) -> None:
    if callable(self._unsubscribe_count):
      self._unsubscribe_count()
      self._unsubscribe_count = None
```

The critical boundary is lifecycle placement: create controls in `build`, attach subscriptions in `bind_runtime`, and dispose subscriptions in `shutdown_runtime`.

### Step 4: Add an Action and Runtime Scene Policy

[Back to Table of Contents](#table-of-contents)

Action and runtime scene declarations belong in config, not ad-hoc event branches.

```python
import pygame

from gui_do import ActionSpec, RuntimeSceneSpec


host.config.action_specs = (
  ActionSpec(action_id="exit", label="Exit", kind="exit", category="File", key=pygame.K_ESCAPE),
)

host.config.runtime_scene_specs = (
  RuntimeSceneSpec(scene_name="main", bind_escape_to_exit=True, prewarm=True),
)
```

`bind_escape_to_exit=True` provides a predictable baseline policy for quickstart scenes.

### Step 5: Run Loop

[Back to Table of Contents](#table-of-contents)

```python
from gui_do import bootstrap_host_application


class MinimalHost:
  def __init__(self) -> None:
    self.config = ...

  def run(self) -> int:
    bootstrap_host_application(self, self.config)
    return self.app.run_entrypoint(target_fps=120)
```

This pattern mirrors current demo assembly flow: construct config first, bootstrap once, then hand control to the managed runtime loop.

### Guided Build Track (Beginner)

[Back to Table of Contents](#table-of-contents)

Milestone A: app boots to one scene without startup exceptions.
Milestone B: one feature builds one visible control.
Milestone C: one observable updates one control through subscription.
Milestone D: one action and one hotkey trigger expected behavior.
Milestone E: one overlay and one toast route without leaking pointer/keyboard input to underlying controls.
Milestone F: workspace save/load roundtrip succeeds.

Beginner confidence checklist:
- You can explain where `build` ends and `bind_runtime` begins.
- You can add/remove one feature by editing specs only.
- You can trace one keypress from input normalization to action execution.

### Quickstart Failure Modes

[Back to Table of Contents](#table-of-contents)

- Feature never appears: verify `feature_specs` entries and scene-name alignment with configured scene setup.
- Hotkey does nothing: verify action registration and the key-binding scope path used by your runtime wiring.
- Overlay blocks unexpected keys: inspect overlay dismissal and key-consumption policies (including unhandled-key consumption semantics).
- State updates but UI does not: verify subscription is attached in `bind_runtime` and not disposed too early.

## Architecture and Runtime Model

[Back to Table of Contents](#table-of-contents)

### Boundary Model: Framework vs Consumer

[Back to Table of Contents](#table-of-contents)

The architecture boundary is strict and intentional. `gui_do/` is the reusable framework layer: runtime loop, event model, controls, layout engines, state/persistence systems, and orchestration helpers. `demo_features/` and `gui_do_demo.py` are consumer integration code that exercise framework capabilities but do not define framework contracts.

The hard rule is one-directional dependency flow: framework code must not import demo packages. Consumer entrypoints should import from the `gui_do` root surface rather than internal `gui_do.*` modules. This keeps the package distributable, preserves public-surface discipline, and prevents demos from silently becoming framework dependencies. Boundary compliance is enforced by `tests/test_boundary_contracts.py`.

### Tiered Public API Model

[Back to Table of Contents](#table-of-contents)

gui_do exports are organized by tiers in `gui_do/__init__.py` to indicate recommended abstraction order. Tier 1 is the preferred entrypoint for all new applications: feature lifecycle types, declarative runtime specs, and bootstrap/build helpers. Tier 2-7 covers core runtime systems (application and scenes, reactive state, events/actions/focus/input, scheduling/animation, theme/fonts, telemetry). Tier 8+ expands into specialized systems such as layout families, overlays, forms, persistence, controls, graphics, audio, introspection, and advanced operational helpers.

Tier numbers are not merely taxonomy; they are guidance. If two tiers can solve a problem, choose the lower-numbered tier first because it is generally more declarative, stable, and composable. Reach for higher tiers when you need explicit low-level control or when chapter-level patterns identify a justified escape hatch.

### Runtime Guarantees

[Back to Table of Contents](#table-of-contents)

The runtime contract guarantees canonical `GuiEvent` normalization before app-level dispatch, scene-isolated update execution for scene-contained runtime work, deterministic window-focus candidate ordering (sorted by `control_id`), scheduler dispatch budget clamping, and resilient workspace restore behavior where missing settings keys are skipped rather than treated as fatal.

Current scheduler clamp constants are contractual: fraction `0.12`, floor `0.5 ms`, and ceiling `4.0 ms`. This keeps dispatch work bounded under long frames while preserving minimum progress under short frames.

### Event Pipeline

[Back to Table of Contents](#table-of-contents)

`GuiApplication.process_event` follows a deterministic routing pipeline:
1. Normalize raw input into `GuiEvent` via the event manager.
2. Handle quit events early.
3. Update shared input snapshot/state.
4. Update logical pointer state, including lock-point/lock-rect behavior.
5. Logicalize pointer events while preserving raw coordinates.
6. Route toasts and overlays with priority before scene fallthrough.
7. Route keyboard events through keyboard manager and screen-handler policy.
8. Route direct-feature handlers, feature handlers, scene dispatch, then fallthrough handlers.
9. Respect `propagation_stopped` and `default_prevented` as hard-stop signals at each stage.

This ordering is why pointer focus, overlay dismissal, and scene dispatch behavior remain predictable under mixed input loads.

### Known Non-Goals

[Back to Table of Contents](#table-of-contents)

- OS-native widget parity across all platforms.
- Replacing domain/business architecture decisions for application logic.
- Treating internal infrastructure tiers as beginner entry points.
- Guaranteeing star-import behavior as a public API compatibility contract.

## Core Workflow: Build, Bind, Route, Update, Draw

[Back to Table of Contents](#table-of-contents)

The five-phase workflow is the operational heart of gui_do. It is not just a naming convention; it is the runtime discipline that keeps feature composition deterministic. If teams keep responsibilities inside their intended phase boundaries, cross-feature integration stays legible and maintenance costs remain low.

### Phase Reference

[Back to Table of Contents](#table-of-contents)

Build phase: instantiate controls, initialize local observables, and establish static scene structure. Invariant: do not wire runtime subscriptions or host-dependent cross-feature bindings here.

Bind_runtime phase: connect host-dependent wiring, action and key paths, observable subscriptions, and cross-feature references. Invariant: sibling features are already built and control instances exist, so reactive bindings are safe.

Route phase: process messages and incoming events through declared handler maps and routing policies. This includes feature-level event handling and message-drain patterns for routed/logic features.

Update phase: advance per-frame state and scheduled workloads. Regular `Feature` instances use `on_update(host)`, while `DirectFeature` instances can run `on_direct_update(host, dt_seconds)` for frame-delta-sensitive logic.

Draw phase: render custom visuals not represented by standard control composition. For control-tree-driven UI this is often minimal, but direct rendering hooks remain available when required.

### Message and Logic Coordination

[Back to Table of Contents](#table-of-contents)

`FeatureMessage` enables feature-to-feature communication without hard references. A sender publishes structured payloads to a target feature, and recipients handle messages through queue-drain hooks. `LogicFeature` is commonly used as a coordination hub because it cleanly separates domain workflows from visual presentation concerns.

Use observables when consumers need continuous reactive state and message dispatch when communication is discrete, command-like, or topic-driven. In practice, many systems use both: messages trigger workflow transitions, observables expose resulting state for UI binding.

### When to Use Routed Runtime Specs

[Back to Table of Contents](#table-of-contents)

`RoutedRuntimeSpec` and `RoutedFeatureLifecycleSpec` reduce repetitive wiring when a feature needs multiple runtime attachments: grouped action hotkeys, shortcut overlays tied to lifecycle, task-panel focus toggles, and event subscriptions with automatic teardown behavior.

`bind_routed_feature_lifecycle` centralizes runtime attachment from a declarative lifecycle spec, while `shutdown_routed_feature_lifecycle` unwinds those attachments consistently. Use this path when manual per-feature bind/shutdown code starts duplicating the same routing and cleanup patterns across features.

## Main Systems Reference

[Back to Table of Contents](#table-of-contents)

### 8.1 Application Bootstrap and Host Configuration

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Bootstrap is the deterministic startup contract for gui_do applications. Instead of progressively mutating a live runtime object graph in ad-hoc order, you define startup intent in declarative specs and then execute one bootstrap pass. This keeps startup reproducible, auditable, and testable.

The design intent is to make the host object a plain container that is populated by bootstrap. `bootstrap_host_application(host, config)` performs display setup, font role registration, cursor registration, scene setup, feature registration, action wiring, and runtime helper attachment in a stable sequence.

#### Mental model and lifecycle placement

Think in two phases: describe, then realize. Description uses `HostApplicationConfig` or `HostApplicationBindingSpec` plus builders. Realization uses `bootstrap_host_application`. After realization, `host.app` is live and configured scenes/features/actions are attached for runtime execution.

#### Primary public APIs and key types

- Tier 1: `HostApplicationConfig`, `HostApplicationBindingSpec`, `bootstrap_host_application`, `build_host_application_config`, `FeatureSpec`, `WindowSpec`, `RuntimeSceneSpec`, `ActionSpec`, `SceneSetupSpec`, `SceneRootSpec`, `CursorSpec`, `StaticAccessibilitySpec`, `FeatureWindowBundleBindingSpec`, `SceneBundleBindingSpec`, `WindowToggleBindingSpec`, `SceneSetupBindingSpec`, `RuntimeSceneBindingSpec`, `SceneRootBindingSpec`, `CursorBindingSpec`, `FontRoleBindingSpec`, `ActionBindingSpec`, `PaletteBindingSpec`, `TelemetryConfig`, `build_feature_specs`, `build_window_toggle_specs`, `build_scene_setup_specs`, `build_runtime_scene_specs`, `build_scene_root_specs`, `build_action_specs`, `build_host_application_config`.
- Tier 2: `GuiApplication`, `create_display`, `SceneTransitionManager`, `SceneTransitionStyle`, `apply_scene_setup_specs`.

#### Typical usage flow

1. Define fonts, scenes, features, actions, cursors, and optional bundles.
2. Build `HostApplicationConfig` directly or via `build_host_application_config(HostApplicationBindingSpec(...))`.
3. Call `bootstrap_host_application(host, config)` once.
4. Run `host.app.run_entrypoint(target_fps=...)`.

#### Minimal example

```python
from gui_do import (
  HostApplicationConfig,
  TelemetryConfig,
  FeatureSpec,
  SceneSetupSpec,
  RuntimeSceneSpec,
  ActionSpec,
  bootstrap_host_application,
)


class Host:
  def __init__(self) -> None:
    self.config = HostApplicationConfig(
      display_size=(1280, 720),
      window_title="Bootstrap Demo",
      fonts={"default": {"system": "arial", "size": 14}},
      font_role_specs=({"body": {"size": 14, "font": "default"}},),
      cursors=(),
      scene_specs=(SceneSetupSpec(name="main", make_initial=True),),
      feature_specs=(FeatureSpec("feature", lambda: object()),),
      window_specs=(),
      runtime_scene_specs=(RuntimeSceneSpec(scene_name="main", bind_escape_to_exit=True),),
      action_specs=(ActionSpec(action_id="exit", label="Exit", kind="exit"),),
      static_accessibility_specs=(),
      initial_scene_name="main",
      telemetry=TelemetryConfig(enabled=False),
    )

  def run(self) -> int:
    bootstrap_host_application(self, self.config)
    return self.app.run_entrypoint(target_fps=120)
```

#### Advanced pattern(s)

Compose startup with `HostApplicationBindingSpec` using `SceneBundleBindingSpec` for scene setup/runtime/nav bundles and `FeatureWindowBundleBindingSpec` for feature + window toggle bundles. This pattern minimizes repetitive spec declarations in larger multi-scene applications while preserving deterministic builder output.

#### Common mistakes and anti-patterns

- Mutating host runtime members manually after bootstrap in ways that bypass spec declarations.
- Declaring feature scene names with no matching scene setup entries.
- Forgetting `initial_scene_name` consistency with declared scenes.
- Mixing direct config construction and builder input conventions without validating final config.

#### Cross-links to related systems

- 8.2 Feature Lifecycle and Feature Types
- 8.3 Events, Actions, Input Mapping, and Routing
- 8.11 Persistence and Workspace/Session State

[Back to Table of Contents](#table-of-contents)

### 8.2 Feature Lifecycle and Feature Types

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Features are the unit of behavior composition in gui_do. They isolate responsibilities, declare host requirements, and participate in deterministic lifecycle execution managed by `FeatureManager`.

Different feature types exist to separate concerns: general UI composition (`Feature`), direct frame-driven rendering (`DirectFeature`), logic-centric coordination (`LogicFeature`), and message-topic routing (`RoutedFeature`).

#### Mental model and lifecycle placement

Treat each feature as a small runtime module with explicit phase boundaries. Build creates structure. Bind_runtime performs host-dependent wiring. Handle_event/on_update/draw execute runtime behavior. Shutdown_runtime releases runtime bindings.

#### Primary public APIs and key types

- Tier 1 core: `Feature`, `DirectFeature`, `LogicFeature`, `RoutedFeature`, `FeatureMessage`, `FeatureManager`, `FeatureSpec`.
- Tier 18 lifecycle helpers: `register_routed_feature_companions`, `bind_routed_feature_lifecycle`, `shutdown_routed_feature_lifecycle`, `setup_routed_feature_runtime`, `bind_feature_logic_aliases`.

#### Typical usage flow

1. Choose a feature base type.
2. Declare `HOST_REQUIREMENTS` for each lifecycle hook you implement.
3. Implement `build`, `bind_runtime`, and runtime hooks (`handle_event`, `on_update`, `draw`) as needed.
4. Register the feature through `FeatureSpec` in bootstrap config.
5. Ensure teardown logic runs in `shutdown_runtime`.

#### Minimal example

```python
from pygame import Rect
from gui_do import Feature, ObservableValue, LabelControl


class CounterFeature(Feature):
  HOST_REQUIREMENTS = {"build": ("app",), "bind_runtime": (), "shutdown_runtime": ()}

  def __init__(self) -> None:
    super().__init__("counter", scene_name="main")
    self.value = ObservableValue(0)
    self.label = None
    self._dispose = None

  def build(self, host) -> None:
    self.label = host.app.add(LabelControl("counter_label", Rect(20, 20, 300, 32), text="0"), scene_name="main")

  def bind_runtime(self, host) -> None:
    self._dispose = self.value.subscribe(lambda v: setattr(self.label, "text", str(v)))

  def shutdown_runtime(self, host) -> None:
    if callable(self._dispose):
      self._dispose()
```

#### Advanced pattern(s)

Use a logic/presentation companion pattern: a `LogicFeature` owns domain state and publishes `FeatureMessage` updates, while a `RoutedFeature` translates message topics into UI updates. Register companionship with `register_routed_feature_companions` and use lifecycle helpers for setup/teardown consistency.

#### Common mistakes and anti-patterns

- Subscribing in `build` rather than `bind_runtime`.
- Treating `DirectFeature` as a generic replacement for all UI behavior.
- Forgetting to shutdown routed lifecycle wiring.
- Omitting `HOST_REQUIREMENTS` for hooks that depend on host members.

#### Cross-links to related systems

- 8.1 Application Bootstrap and Host Configuration
- 8.4 State and Observables
- 8.10 Scheduling, Timing, Animation, and Transitions

[Back to Table of Contents](#table-of-contents)

### 8.3 Events, Actions, Input Mapping, and Routing

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

This system turns raw platform input into deterministic application behavior. gui_do first normalizes incoming events to `GuiEvent`, then routes them through overlays, focus, keyboard, feature handlers, scene dispatch, and optional fallthrough handlers.

Actions and input mappings decouple user intent from specific input devices. You define named actions, then bind keys/chords or control activations to those actions.

#### Mental model and lifecycle placement

Model the pipeline as normalized event transport plus command execution. Normalization and routing happen per event in `GuiApplication.process_event`. Action registration and key binding are usually established during runtime wiring (`bind_runtime`) or through Tier 1 runtime specs.

#### Primary public APIs and key types

- Event model: `GuiEvent`, `EventType`, `EventPhase`, `EventManager`, `EventBus`, `EventRecorder`, `EventPlayback`, `RecordedEvent`, `GestureRecognizer`, `InputSnapshot`, `Signal`, `SignalConnection`.
- Action/input model: `ActionManager`, `ActionRegistry`, `ActionDescriptor`, `ActionContext`, `ActionMiddleware`, `InputMap`, `InputBinding`, `KeyChordManager`, `KeyChord`, `ChordStep`.
- Focus/routing context: `FocusManager`, `FocusScope`, `FocusScopeManager`, `WindowFocusManager`, `FocusRing`.
- Supporting Tier 1 specs: `ActionSpec`, `ActionHotkeySpec`, `ControlKeyBindingSpec`, `EventSubscriptionSpec`.

`GuiEvent` fields and canonical `EventType` values are specified in docs/event_system_spec.md and must remain aligned with runtime behavior.

#### Typical usage flow

1. Declare `ActionSpec` values for user commands.
2. Bind input via hotkey specs, input maps, or routed runtime helper wiring.
3. Route and consume events through feature handlers as needed.
4. Respect `default_prevented` and `propagation_stopped` signals in custom handlers.

#### Minimal example

```python
import pygame
from gui_do import ActionSpec, RuntimeSceneSpec

action_specs = (
  ActionSpec(action_id="exit", label="Exit", kind="exit", key=pygame.K_ESCAPE),
  ActionSpec(action_id="open_palette", label="Open Palette", kind="palette_open", key=pygame.K_p),
)

runtime_scene_specs = (
  RuntimeSceneSpec(scene_name="main", bind_escape_to_exit=True),
)
```

#### Advanced pattern(s)

Use `InteractionStateMachine` (Tier 30) for guarded gesture phase transitions (press, drag, release) and record event sessions with `EventRecorder`/`EventPlayback` to reproduce routing regressions deterministically during tests.

#### Common mistakes and anti-patterns

- Bypassing normalization and handling raw pygame events directly in feature code.
- Assuming routing is global when handlers are scene/window scoped.
- Ignoring `propagation_stopped` or `default_prevented` in custom dispatch layers.
- Binding keys without validating scene scope and active-window context.

#### Cross-links to related systems

- 8.2 Feature Lifecycle and Feature Types
- 8.7 Focus and Accessibility
- 8.10 Scheduling, Timing, Animation, and Transitions

[Back to Table of Contents](#table-of-contents)

### 8.4 State and Observables

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

State and observables provide the reactive data backbone for gui_do. They let features publish changing values without hard wiring all consumers, and they support efficient update paths for scalar values, collections, derived values, and transactional state.

#### Mental model and lifecycle placement

Treat observables as live state channels. Create them when feature state is established, subscribe during runtime binding, and dispose during shutdown. For app-wide coordination, use store/selectors/transactions rather than ad-hoc global mutable structures.

#### Primary public APIs and key types

- Tier 3 primitives: `ObservableValue`, `ObservableList`, `ObservableDict`, `CollectionChange`, `ChangeKind`, `ComputedValue`, `PresentationModel`, `Binding`, `BindingGroup`, `ObservableStream`, `InvalidationTracker`, `CollectionView`, `CollectionViewQuery`, `SelectionModel`, `SelectionMode`, `reactive_batch`, `is_batching`.
- Tier 27 transactional state: `AppStateStore`, `StateSelector`, `StateTransaction`.

Runtime restore observability is also contractual: workspace restore reporting includes `target_scene`, `switched_scene`, `restored_feature_states`, `restored_scene_nodes`, `applied_settings`, `skipped_settings`, and `missing_settings_blocks`.

#### Typical usage flow

1. Define observable state in feature construction.
2. Subscribe in `bind_runtime` and bind changes to controls or dependent state.
3. Use `reactive_batch` for grouped changes.
4. Dispose subscriptions in `shutdown_runtime`.
5. Use `AppStateStore` when multiple features require coordinated atomic updates.

#### Minimal example

```python
from gui_do import ObservableValue

count = ObservableValue(0)
dispose = count.subscribe(lambda value: print("count changed", value))
count.value = 1
dispose()
```

#### Advanced pattern(s)

For multi-feature applications, centralize shared state in `AppStateStore` and expose stable selectors with `StateSelector`. Use `StateTransaction` for atomic updates and pair with `CollectionView` over observable collections when UI requires filtered or sorted live projections.

#### Common mistakes and anti-patterns

- Polling state in `on_update` instead of subscribing.
- Subscribing before runtime wiring is complete.
- Leaking subscriptions during scene transitions.
- Sharing plain mutable lists/dicts across features instead of observable collections.

#### Cross-links to related systems

- 8.2 Feature Lifecycle and Feature Types
- 8.3 Events, Actions, Input Mapping, and Routing
- 8.11 Persistence and Workspace/Session State

[Back to Table of Contents](#table-of-contents)

### 8.5 Controls and Control Composition

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Controls are the reusable UI building blocks of gui_do. They let features describe interface structure declaratively while the framework handles hit testing, update sequencing, rendering order, and interaction state.

The composition goal is clean ownership: each feature owns a root panel and composes children under that subtree. Inter-feature coordination should happen through messages and reactive state, not through cross-tree control references.

#### Mental model and lifecycle placement

Controls are created in `build`, wired in `bind_runtime`, and updated through framework-managed event/update loops. A feature should treat controls as presentation endpoints that mirror state, not as primary state containers.

#### Primary public APIs and key types

- Tier 12 primary controls: `PanelControl`, `LabelControl`, `ButtonControl`, `ToggleControl`, `SliderControl`, `ScrollbarControl`, `CanvasControl`, `CanvasEventPacket`, `CanvasViewport`, `FrameControl`, `ImageControl`, `ArrowBoxControl`, `ButtonGroupControl`, `TabControl`, `TabItem`, `DockWorkspacePanel`.
- Tier 13 extended controls: `TextInputControl`, `TextAreaControl`, `RichLabelControl`, `DropdownControl`, `DropdownOption`, `ListViewControl`, `ListItem`, `OverlayPanelControl`, `DataGridControl`, `GridColumn`, `GridRow`, `TreeControl`, `TreeNode`, `SplitterControl`, `SpinnerControl`, `RangeSliderControl`, `ColorPickerControl`, `ScrollViewControl`, `ProgressBarControl`, `AnimatedImageControl`, `ErrorBoundary`, `WindowControl`, `TaskPanelControl`, `WindowPresenter`, `MenuBarControl`, `MenuEntry`, `SceneMenuStripControl`, `NotificationPanelControl`, `PropertyInspectorPanel`, `ToolbarControl`, `ToolbarItem`, `StatusBarControl`, `StatusSlot`, `ExpanderControl`, `DatePickerControl`, `TimePickerControl`, `BreadcrumbControl`, `BreadcrumbItem`, `SplitButtonControl`, `SplitButtonOption`, `ChipInputControl`.
- Tier 1 control-spec helpers: `ControlDefinition`, `build_specs_from_column_section`, plus tab/window composition helpers such as `TabbedPresenterSpec` and `TabBuilderSpec`.

#### Typical usage flow

1. Add one feature root `PanelControl` to the scene in `build`.
2. Add child controls under that root.
3. Attach callbacks and state bindings in `bind_runtime`.
4. Keep feature logic and state in the feature layer, not inside control objects.

#### Minimal example

```python
from pygame import Rect
from gui_do import PanelControl, LabelControl, ButtonControl


def build(self, host):
  self.root = host.app.add(PanelControl("my_root", Rect(0, 0, 400, 300)), scene_name="main")
  self.label = self.root.add(LabelControl("status", Rect(8, 8, 220, 24), "Ready"))
  self.root.add(ButtonControl("go", Rect(8, 40, 100, 28), "Go", on_click=self._on_go))
```

#### Advanced pattern(s)

Use the presenter pattern for window-scale composition: `WindowPresenter` owns child controls and window behavior while the feature owns lifecycle and routing responsibilities. Combine with tabbed composition helpers to build multi-tab floating windows without bloating feature classes.

#### Common mistakes and anti-patterns

- Holding direct references to controls owned by another feature.
- Treating controls as domain state sources rather than observable state mirrors.
- Constructing controls in `on_update`.
- Skipping `ErrorBoundary` around high-risk custom subtrees.

#### Cross-links to related systems

- 8.2 Feature Lifecycle and Feature Types
- 8.6 Layout Systems
- 8.7 Focus and Accessibility
- 8.9 Scene, Window, and Task-Panel Presentation Models

[Back to Table of Contents](#table-of-contents)

### 8.6 Layout Systems

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Layout systems in gui_do provide spatial contracts so UI remains coherent across window sizes, panel reshaping, and dynamic content changes. They reduce brittle absolute-position arithmetic and centralize sizing/placement strategy.

#### Mental model and lifecycle placement

Choose the simplest layout family that matches the local container problem. Layout definitions are typically established during `build` and recalculated by layout passes before draw or on explicit invalidation/resizing triggers.

#### Primary public APIs and key types

- Tier 8: `LayoutAxis`, `LayoutManager`, `WindowTilingManager`, `ConstraintLayout`, `AnchorConstraint`, `DockPane`, `DockTabs`, `DockSplit`, `DockWorkspace`, `FlexLayout`, `FlexItem`, `FlexDirection`, `FlexAlign`, `FlexJustify`, `GridLayout`, `GridTrack`, `GridPlacement`, `CellCaretLayout`, `CellCaretState`, `LayoutAnimator`, `LayoutPass`, `MeasureContext`, `ArrangeContext`, `LayoutRoot`, `ResponsiveLayout`, `Breakpoint`, `SnapGrid`, `AlignmentGuide`, `SnapComposer`, `SnapTarget`, `FlowLayout`, `FlowItem`, `Viewport`.
- Tier 28: `ConstraintAttr`, `LayoutConstraint`, `ConstraintSet`, `ConstraintLayoutEngine`, `AdaptivePolicy`, `resolve_adaptive_policy`.
- Tier 29: `MeasureMode`, `MeasurePolicy`, `VirtualizedWindow`, `RecyclePool`, `VirtualizationCore`.

#### Typical usage flow

1. Create container controls.
2. Choose one layout model per container boundary.
3. Register children with layout items/tracks/constraints.
4. Trigger layout invalidation when content or bounds change.

#### Minimal example

```python
from gui_do import FlexLayout, FlexDirection, FlexItem


layout = FlexLayout(direction=FlexDirection.ROW, gap=8)
layout.add(FlexItem(control=sidebar, grow=0, basis=220))
layout.add(FlexItem(control=content, grow=1))
```

#### Advanced pattern(s)

Use `ConstraintLayoutEngine` with `AdaptivePolicy` to switch constraints across breakpoints, and pair with `VirtualizationCore` for large scrolling datasets where only visible rows/nodes should be materialized.

#### Common mistakes and anti-patterns

- Mixing multiple conflicting layout engines for one container without ownership boundaries.
- Hardcoding fixed dimensions where responsive constraints are required.
- Applying layout before child controls are registered.

#### Cross-links to related systems

- 8.5 Controls and Control Composition
- 8.9 Scene, Window, and Task-Panel Presentation Models
- 8.12 Theme, Styling, and Visual Systems

[Back to Table of Contents](#table-of-contents)

### 8.7 Focus and Accessibility

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Focus and accessibility systems guarantee coherent keyboard interaction and semantic discoverability. Focus ensures only the intended target receives keyboard input, and accessibility metadata provides a structured semantic model for assistive and automated consumers.

#### Mental model and lifecycle placement

Focus membership is established when controls are built and updated as visibility/enablement changes. Accessibility semantics are attached as controls are created and refined during runtime when content changes. Modal overlays and scoped focus regions should constrain navigation intentionally.

#### Primary public APIs and key types

- Tier 4 focus APIs: `FocusManager`, `FocusScope`, `FocusScopeManager`, `WindowFocusManager`, `FocusRing`.
- Tier 21 accessibility APIs: `AccessibilityRole`, `LivePoliteness`, `AccessibilityNode`, `AccessibilityTree`, `AccessibilityAnnouncement`, `AccessibilityBus`.
- Tier 1 related specs: `AccessibilitySequenceSpec`, `StaticAccessibilitySpec`, `TaskPanelFocusToggleSpec`.

#### Typical usage flow

1. Register focusable controls during build.
2. Declare static accessibility labels/roles through config specs.
3. Apply focus scope rules for modal/dialog contexts.
4. Keep hidden/disabled controls out of active focus traversal.

#### Minimal example

```python
from gui_do import AccessibilityTree, AccessibilityNode, AccessibilityRole


tree = AccessibilityTree()
submit = AccessibilityNode(role=AccessibilityRole.BUTTON, name="Submit")
tree.root.add_child(submit)
```

#### Advanced pattern(s)

Use `AccessibilitySequenceSpec` to enforce explicit traversal ordering for complex scenes and combine `FocusScope` with overlay dialogs so tab navigation remains trapped within active modal content until dismissal.

#### Common mistakes and anti-patterns

- Leaving hidden-window controls inside active focus rings.
- Omitting semantic roles on custom canvas-like widgets.
- Creating accessibility nodes before tree/runtime ownership is initialized.

#### Cross-links to related systems

- 8.3 Events, Actions, Input Mapping, and Routing
- 8.5 Controls and Control Composition
- 8.8 Overlays, Dialogs, Notifications, and Command Surfaces

[Back to Table of Contents](#table-of-contents)

### 8.8 Overlays, Dialogs, Notifications, and Command Surfaces

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Overlays and command surfaces provide transient interaction layers that sit above main scene controls. They isolate modal behavior, command discovery, notifications, and contextual actions so base scene routing remains stable.

#### Mental model and lifecycle placement

Overlay routing precedes normal scene control routing for relevant events. Each manager owns one surface type and its dismissal semantics. Features configure overlays during runtime wiring and keep handles for updates/dismissal.

#### Primary public APIs and key types

- Tier 9 managers and types: `OverlayManager`, `OverlayHandle`, `DialogManager`, `DialogHandle`, `ToastManager`, `ToastHandle`, `ToastSeverity`, `ContextMenuManager`, `ContextMenuItem`, `ContextMenuHandle`, `CommandPaletteManager`, `CommandEntry`, `CommandPaletteHandle`, `TooltipManager`, `TooltipHandle`, `MenuBarManager`, `FileDialogManager`, `FileDialogOptions`, `FileDialogHandle`, `NotificationCenter`, `NotificationRecord`, `ResizeManager`, `CursorManager`, `CursorHandle`, `CursorShape`, `DragDropManager`, `DragPayload`, `ClipboardManager`, `TransferData`, `TransferManager`, `ShortcutHelpOverlay`, `ShortcutSection`, `ShortcutEntry`, `PopupPlacement`, `PlacementResult`, `Alignment`, `Side`, `compute_popup_rect`.
- Tier 1 integration specs: `ShortcutOverlaySpec`, `NotificationSpec`.

#### Typical usage flow

1. Choose overlay surface type by interaction need (toast, dialog, context menu, palette, tooltip).
2. Show through manager and keep returned handle if later updates/dismissal are needed.
3. Ensure each overlay has a clear dismissal contract.
4. Route commands/entries through action registry or explicit callbacks.

#### Minimal example

```python
from gui_do import ToastSeverity


host.toasts.show("Saved", severity=ToastSeverity.SUCCESS)
```

#### Advanced pattern(s)

Build a shortcut-help surface by combining `ShortcutOverlaySpec` with action registry metadata and optional manual entries/section filters. For command-heavy tools, use `CommandPaletteManager` with dynamic `CommandEntry` providers and ordered scene/window/custom grouping.

#### Common mistakes and anti-patterns

- Creating overlays without explicit dismissal behavior.
- Expecting pointer events on toast bounds to pass through.
- Updating disposed overlay handles.
- Mixing command palette and context menu responsibilities into a single surface.

#### Cross-links to related systems

- 8.3 Events, Actions, Input Mapping, and Routing
- 8.7 Focus and Accessibility
- 8.9 Scene, Window, and Task-Panel Presentation Models

[Back to Table of Contents](#table-of-contents)

### 8.9 Scene, Window, and Task-Panel Presentation Models

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Scene and window presentation APIs define what context is active, what surfaces are visible, and which controls/actions are discoverable at a given moment. This subsystem separates broad application mode switching (scenes) from focused work surfaces (windows) and persistent command surfaces (task panel and scene menus).

#### Mental model and lifecycle placement

Think of scene presentation as top-level context management and window presentation as scene-local composition. Scene/window declarations are part of bootstrap configuration, window/control construction occurs in feature `build`, and visibility/focus toggles are routed during runtime through presentation helpers and action bindings.

#### Primary public APIs and key types

- Tier 1 specs/models: `ScenePresentationModel`, `WindowSpec`, `AnchoredWindowSpec`, `SceneTaskPanelSpec`, `TaskPanelButtonSpec`, `TaskPanelFocusToggleSpec`, `FeatureWindowBundleBindingSpec`, `WindowToggleBindingSpec`, `TabbedPresenterSpec`, `TabBuilderSpec`, `SceneCommandPaletteSpec`, `TaskPanelSceneNavButtonSpec`.
- Tier 18 helpers: `set_window_visible_state`, `toggle_window_visibility`, `create_anchored_feature_window`, `add_window_scene_menu_strip`, `ensure_scene_task_panel`, `add_task_panel_buttons`, `add_task_panel_window_toggle_group`, `register_window_toggle_tooltips`, `create_presented_anchored_window`, `create_presented_window_from_spec`, `create_feature_presented_window`, `register_window_presentation_specs`, `register_window_tab_builders`, `build_tab_builder_specs`, `create_tab_control_from_specs`, `compute_tabbed_window_layout`, `setup_feature_presenter_tabs`, `register_tab_update_handlers`, `ActiveTabUpdateRouter`, `TabLayoutContext`.
- Related control abstraction: `WindowPresenter`.

#### Typical usage flow

1. Declare scene and window specs in host config/bindings.
2. Build feature roots and presenter-backed windows in `build`.
3. Register task-panel buttons and window toggles.
4. Keep visibility and focus synchronized through scene presentation handlers.

#### Minimal example

```python
from gui_do import AnchoredWindowSpec, create_feature_presented_window


spec = AnchoredWindowSpec(
  control_id="systems_window",
  title="Systems",
  size=(520, 420),
  anchor="top_right",
  margin=(16, 48),
)

window = create_feature_presented_window(host, self, spec)
```

#### Advanced pattern(s)

Compose multi-window scenes with tabbed presenters: use `TabbedPresenterSpec` and `TabBuilderSpec` for per-tab factories, then route only active-tab updates with `ActiveTabUpdateRouter`. Pair this with task-panel toggle groups so window visibility, focus inclusion, and command surfaces remain synchronized.

#### Common mistakes and anti-patterns

- Creating windows during `bind_runtime` instead of `build`.
- Letting task-panel toggle state drift from actual window visibility.
- Registering actions in scene scope while target windows are bound to different scopes.

#### Cross-links to related systems

- 8.2 Feature Lifecycle and Feature Types
- 8.5 Controls and Control Composition
- 8.7 Focus and Accessibility
- 8.8 Overlays, Dialogs, Notifications, and Command Surfaces

[Back to Table of Contents](#table-of-contents)

### 8.10 Scheduling, Timing, Animation, and Transitions

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Scheduling and timing systems keep per-frame work bounded while supporting animation, transitions, delayed callbacks, and multi-step workflows. They prevent UI stalls by formalizing how time-based work is advanced each frame.

#### Mental model and lifecycle placement

Treat schedulers and animation managers as scene/runtime services that are configured once and ticked each frame by the application loop. Features should register work and keep frame hooks lightweight.

Scheduler dispatch is contract-bounded: fraction `0.12` of dt milliseconds, floor `0.5 ms`, ceiling `4.0 ms`.

#### Primary public APIs and key types

- Tier 5: `TaskEvent`, `TaskScheduler`, `Timers`, `TweenManager`, `TweenHandle`, `Easing`, `AnimationSequence`, `AnimationHandle`, `TransitionManager`, `TransitionSpec`, `TransitionEvent`, `AnimationStateMachine`, `AnimationTransitionMode`, `SceneTimeline`, `Debouncer`, `Throttler`, `CooperativeScheduler`, `CoroutineHandle`, `Pause`, `Sleep`, `WaitForEvent`, `WaitForSignal`, `WaitUntil`, `WaitForAll`.
- Tier 26 dataflow bridge: `CancellationToken`, `PipelineStage`, `DataflowPipeline`, `PipelineHandle`.
- Tier 18 runtime helper: `ensure_scene_scheduler`.

#### Typical usage flow

1. Register scheduler/timer/tween services for the scene.
2. Start tweens/timelines/coroutines in response to user actions or scene lifecycle.
3. Cancel or complete work on scene exit.
4. Keep heavy background stages in dataflow pipeline stages rather than `on_update`.

#### Minimal example

```python
def on_show(self, host):
  self._fade = host.tweens.to(self.panel, "alpha", 255, duration=0.2)
```

#### Advanced pattern(s)

Use `CooperativeScheduler` for long workflows that yield via `Sleep` and `WaitForSignal`, then hand expensive transformation stages to `DataflowPipeline` with cancellation tokens. This preserves responsiveness while keeping workflow logic linear and readable.

#### Common mistakes and anti-patterns

- Doing unbounded CPU work in frame hooks.
- Running blocking I/O directly inside cooperative coroutines.
- Forgetting to cancel tweens/coroutines when scene objects are destroyed.

#### Cross-links to related systems

- 8.2 Feature Lifecycle and Feature Types
- 8.14 Data and Dataflow Helpers
- 8.16 Telemetry, Introspection, and Operational Hooks

[Back to Table of Contents](#table-of-contents)

### 8.11 Persistence and Workspace/Session State

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Persistence systems capture and restore user sessions so applications can resume reliably after restart. They also provide explicit contracts for what was restored, skipped, or unavailable.

#### Mental model and lifecycle placement

Treat workspace state as versioned runtime data, not incidental files. Save at explicit checkpoints, restore early during startup flow, and inspect structured restore reports to handle partial restores safely.

Restore report fields are contractual: `target_scene`, `switched_scene`, `restored_feature_states`, `restored_scene_nodes`, `applied_settings`, `skipped_settings`, `missing_settings_blocks`.

#### Primary public APIs and key types

- Tier 11 state and persistence: `CommandHistory`, `Command`, `CommandTransaction`, `StateMachine`, `HierarchicalStateMachine`, `Router`, `RouteEntry`, `SettingsRegistry`, `SettingDescriptor`, `WorkspaceState`, `WorkspacePersistenceManager`, `DEFAULT_WORKSPACE_STATE_PATH`, `SceneSnapshot`, `NodeSnapshot`.
- Tier 23 undo routing: `UndoContextManager`.
- Tier 32 migration layer: `SchemaVersion`, `VersionedSnapshot`, `MigrationStep`, `MigrationRegistry`, `SnapshotMigrator`, `MigrationError`, `make_snapshot`, `read_version`.

#### Typical usage flow

1. Register settings and stateful feature save/restore hooks.
2. Save workspace state on demand or shutdown.
3. Load workspace and inspect restore report.
4. Apply migration path before replay when snapshot versions differ.

#### Minimal example

```python
report = host.app.load_workspace(path)
if report and report.skipped_settings:
  host.toasts.show("Some settings were skipped during restore")
```

#### Advanced pattern(s)

Adopt versioned snapshot migration from day one. Register forward `MigrationStep` edges in `MigrationRegistry`, then use `SnapshotMigrator` to normalize old snapshots before restore replay. Pair with `UndoContextManager` to maintain independent undo stacks per workspace surface.

#### Common mistakes and anti-patterns

- Assuming missing settings are fatal instead of checking restore report fields.
- Restoring snapshots without version inspection (`read_version`).
- Reusing `DEFAULT_WORKSPACE_STATE_PATH` in multi-instance scenarios.

#### Cross-links to related systems

- 8.1 Application Bootstrap and Host Configuration
- 8.2 Feature Lifecycle and Feature Types
- 8.16 Telemetry, Introspection, and Operational Hooks

[Back to Table of Contents](#table-of-contents)

### 8.12 Theme, Styling, and Visual Systems

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Theme and styling systems centralize visual semantics so applications can change appearance without touching feature logic. They provide color themes, design tokens, font role registries, and scoped overrides.

#### Mental model and lifecycle placement

Define baseline theme and font roles during bootstrap, then let controls resolve visual values by semantic role names. On theme changes, invalidate visual caches through the invalidation bus rather than manual redraw bookkeeping.

#### Primary public APIs and key types

- Tier 6: `FontManager`, `FontRoleRegistry`, `ColorTheme`, `ThemeManager`, `DesignTokens`, `ScopedTheme`, `ScopedThemeManager`.
- Tier 22: `ThemeInvalidationBus`.
- Tier 1 related binding specs: `FontRoleBindingSpec`, `CursorSpec`, `CursorBindingSpec`, and `setup_standard_font_roles`.

#### Typical usage flow

1. Declare fonts and role bindings in host configuration.
2. Use semantic font/theme roles in controls.
3. Apply global or scoped theme changes through managers.
4. Rely on invalidation bus notifications for cache refresh.

#### Minimal example

```python
host.app.register_font_role("body", size=14, system_name="arial")
host.app.register_font_role("title", size=20, system_name="arial", bold=True)
```

#### Advanced pattern(s)

Use `ScopedThemeManager` to apply local theme overrides to selected window subtrees (for example, utility panes with alternate visual contrast) while retaining a shared global theme. Subscribe render caches to `ThemeInvalidationBus` so theme switches trigger deterministic cache flush and redraw.

#### Common mistakes and anti-patterns

- Hardcoding colors and spacing constants inside feature draw methods.
- Changing theme without invalidating cached rendered surfaces.
- Registering font roles late after controls already assumed unavailable role names.

#### Cross-links to related systems

- 8.1 Application Bootstrap and Host Configuration
- 8.5 Controls and Control Composition
- 8.16 Telemetry, Introspection, and Operational Hooks

[Back to Table of Contents](#table-of-contents)

### 8.13 Text, Input, Forms, and Validation Systems

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Text entry and form workflows are central to application UX, so gui_do exposes dedicated APIs for text formatting/search, form schemas, validation pipelines, wizard-style progression, and schema-driven runtime validation. The intent is to avoid bespoke form systems that become inconsistent across features.

#### Mental model and lifecycle placement

Input controls (`TextInputControl`, `TextAreaControl`, related typed controls) handle interaction and display. Form models and schema runtime hold logical form state and validation policy. Validation and async validation wiring happens in runtime bind phases; field state updates flow through observables and form runtime callbacks.

#### Primary public APIs and key types

- Tier 10 forms and validators: `FormModel`, `FormField`, `ValidationRule`, `FieldError`, `FormSchema`, `SchemaField`, `DocumentModel`, `WizardFlow`, `WizardStep`, `WizardHandle`, `ValidationResult`, `Validator`, `RequiredValidator`, `RangeValidator`, `LengthValidator`, `PatternValidator`, `CustomValidator`, `DependentValidator`, `ValidationPipeline`.
- Tier 24 async validation: `AsyncFieldValidator`, `AsyncFormValidator`.
- Tier 31 schema runtime: `FieldSchema`, `FieldGraphSchema`, `ValidationPolicy`, `SchemaFormRuntime`.
- Tier 14 text/localization: `TextFormatter`, `NumericFormatter`, `PatternFormatter`, `FixedPatternFormatter`, `TextFlow`, `TextSpan`, `TextSearcher`, `TextMatch`, `StringTable`, `LocaleRegistry`.
- Tier 13 input controls commonly used with form flows: `TextInputControl`, `TextAreaControl`, `SpinnerControl`, `DatePickerControl`, `TimePickerControl`, `ColorPickerControl`, `ChipInputControl`.

#### Typical usage flow

1. Define form fields and schema.
2. Build schema graph and runtime policy.
3. Bind controls to field values/errors.
4. Run synchronous validators and optional async validators.
5. Drive step progression with wizard handles when flow is multi-stage.

#### Minimal example

```python
from gui_do import FormModel, FormField, RequiredValidator, PatternValidator


model = FormModel(
  fields=[
    FormField("email", "", validators=[RequiredValidator(), PatternValidator(r".+@.+")]),
    FormField("password", "", validators=[RequiredValidator()]),
  ]
)
ok = model.validate()
```

#### Advanced pattern(s)

Use `SchemaFormRuntime` with `ValidationPolicy` for policy-driven validation timing, then layer `AsyncFormValidator` for debounced server-side checks (for example username uniqueness) with stale-result suppression when users continue typing.

#### Common mistakes and anti-patterns

- Triggering all validation only at submit when immediate feedback is expected.
- Ignoring validation policy and forcing validation on every mutation.
- Running async validation without cancellation/debounce strategy.

#### Cross-links to related systems

- 8.4 State and Observables
- 8.5 Controls and Control Composition
- 8.14 Data and Dataflow Helpers

[Back to Table of Contents](#table-of-contents)

### 8.14 Data and Dataflow Helpers

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Data-heavy UI workflows require more than simple collections. gui_do provides source abstractions, async loading state, sort/filter proxies, caching, list diffs, virtualization primitives, and cancelable pipelines so large datasets remain interactive.

#### Mental model and lifecycle placement

Data enters through source/provider abstractions, is transformed through proxies or pipeline stages, and is presented via virtualized controls. Data orchestration is typically configured in `bind_runtime` and advanced by scheduler/pipeline callbacks rather than blocking UI hooks.

#### Primary public APIs and key types

- Tier 15: `VirtualItemSource`, `FixedItemSource`, `SortFilterProxySource`, `AsyncDataProvider`, `LoadState`, `LoadStateKind`, `ObjectPool`, `DataCache`, `CacheStats`, `ListDiffCalculator`, `ListDiff`, `DiffInsert`, `DiffRemove`, `DiffMove`.
- Tier 26: `CancellationToken`, `PipelineStage`, `DataflowPipeline`, `PipelineHandle`.
- Tier 27: `AppStateStore`, `StateSelector`, `StateTransaction`.
- Tier 29 virtualization core: `MeasureMode`, `MeasurePolicy`, `VirtualizedWindow`, `RecyclePool`, `VirtualizationCore`.

#### Typical usage flow

1. Choose a source/provider strategy.
2. Apply sort/filter proxy or staged pipeline transformations.
3. Present data through virtualized views where volume is high.
4. Diff incremental changes for efficient UI updates.
5. Track cache and load state for UX feedback.

#### Minimal example

```python
from gui_do import FixedItemSource, SortFilterProxySource


source = FixedItemSource(items)
proxy = SortFilterProxySource(source)
proxy.set_filter(lambda item: item.active)
proxy.set_sort_key(lambda item: item.name)
```

#### Advanced pattern(s)

Build a multi-stage `DataflowPipeline` (load, normalize, rank) where each generation carries a `CancellationToken`. On new user input, cancel the current generation and start a new one, then feed the result into virtualized views and update UI incrementally via list-diff patches.

#### Common mistakes and anti-patterns

- Full-repaint list updates instead of diff-driven updates.
- Allowing stale pipeline generations to commit late results.
- Keeping unbounded datasets resident without cache policy.
- Returning pooled objects that are still referenced elsewhere.

#### Cross-links to related systems

- 8.4 State and Observables
- 8.10 Scheduling, Timing, Animation, and Transitions
- 8.16 Telemetry, Introspection, and Operational Hooks

[Back to Table of Contents](#table-of-contents)

### 8.15 Graphics and Audio Integration Points

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Graphics and audio APIs support scenarios where standard controls are insufficient: particle effects, custom draw layers, tile maps, scene graph rendering, and semantic sound cues. These integration points preserve framework structure while enabling rich media behavior.

#### Mental model and lifecycle placement

Asset and renderer setup belongs in build/startup phases. Runtime updates advance animation or particle state. Draw hooks compose onto the frame via draw contexts, layers, and optional offscreen targets. Audio is event-driven from semantic actions rather than low-level pointer noise.

#### Primary public APIs and key types

- Tier 16 graphics: `BuiltInGraphicsFactory`, `DirtyRegionTracker`, `DrawContext`, `DrawPhase`, `AssetRegistry`, `DebugOverlay`, `SurfaceCompositor`, `Layer`, `ShapeRenderer`, `SurfaceEffects`, `VectorPath`, `SpriteSheet`, `FrameAnimation`, `ParticleSystem`, `Emitter`, `ParticleLayer`, `TileSet`, `TileMap`, `RenderTarget`, `LiveRenderTarget`, `OffscreenRenderTarget`, `create_render_target`, `create_surface`, `Node2D`, `SceneGraph2D`, `Camera2D`.
- Tier 20 audio: `SoundCue`, `SoundBankRegistry`, `SoundEventBus`.

#### Typical usage flow

1. Register and load visual/audio assets.
2. Update animation/particle state each frame.
3. Draw through scene graph/compositor layers.
4. Publish semantic sound cues for UX events.

#### Minimal example

```python
def on_update(self, host):
  self.particles.tick(1 / 120)


def draw(self, host, surface, theme):
  self.particles.draw(surface)
```

#### Advanced pattern(s)

Combine `DirtyRegionTracker` and `OffscreenRenderTarget` to redraw only changed regions of expensive canvases, then composite with `SurfaceCompositor`. Pair with `SceneGraph2D` and `Camera2D` for camera-relative world rendering and controlled zoom/pan.

#### Common mistakes and anti-patterns

- Full-surface redraws when dirty-region gating is possible.
- Loading assets in draw hooks.
- Emitting sounds from raw pointer noise instead of semantic events.
- Unbounded particle emitters without lifecycle cleanup.

#### Cross-links to related systems

- 8.2 Feature Lifecycle and Feature Types
- 8.5 Controls and Control Composition
- 8.10 Scheduling, Timing, Animation, and Transitions

[Back to Table of Contents](#table-of-contents)

### 8.16 Telemetry, Introspection, and Operational Hooks

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Operational observability APIs make runtime behavior measurable and debuggable. Telemetry spans provide timing visibility, while introspection APIs expose inspectable properties and spatial queries for diagnostics tooling.

#### Mental model and lifecycle placement

Enable telemetry at bootstrap and instrument critical paths during runtime. Use property and spatial introspection for live diagnostics surfaces and regression triage. Operational hooks should remain low-overhead and targeted.

#### Primary public APIs and key types

- Tier 7 telemetry: `TelemetryCollector`, `TelemetrySample`, `configure_telemetry`, `telemetry_collector`, `analyze_telemetry_log_file`, `analyze_telemetry_records`, `load_telemetry_log_file`, `render_telemetry_report`.
- Tier 17 introspection: `SceneSpatialIndex`, `ui_property`, `PropertyDescriptor`, `PropertyRegistry`, `property_registry`, `PropertyInspectorModel`, `InspectedProperty`.
- Related bootstrap toggle: `TelemetryConfig`.

#### Typical usage flow

1. Enable telemetry in host config.
2. Run representative scenarios.
3. Analyze records or logs and render reports.
4. Use introspection APIs for targeted property/spatial diagnostics.

#### Minimal example

```python
from gui_do import configure_telemetry, telemetry_collector, analyze_telemetry_records


configure_telemetry(enabled=True)
records = telemetry_collector().records
report = analyze_telemetry_records(records)
```

#### Advanced pattern(s)

Correlate telemetry span outliers with property snapshots from `PropertyInspectorModel` and spatial hits from `SceneSpatialIndex` to identify whether regressions originate in layout churn, routing loops, or draw hotspots.

#### Common mistakes and anti-patterns

- Profiling idle loops and treating results as representative.
- Turning on deep diagnostics without scenario boundaries.
- Skipping early telemetry configuration and missing startup spans.

#### Cross-links to related systems

- 8.10 Scheduling, Timing, Animation, and Transitions
- 8.11 Persistence and Workspace/Session State
- 8.15 Graphics and Audio Integration Points

[Back to Table of Contents](#table-of-contents)

## Integration Patterns and Composition Recipes

[Back to Table of Contents](#table-of-contents)

### Recipe 1: Routed Feature, Actions, and Shortcut Overlay

Goal: provide discoverable keyboard shortcuts with lifecycle-safe wiring.

Why this combination: `RoutedRuntimeSpec` centralizes hotkeys, subscriptions, and overlays in one declarative object. `ShortcutOverlaySpec` ensures the help surface remains synchronized with actions.

Step-by-step pattern:
1. Declare `ActionSpec` entries in host config.
2. Build `RoutedRuntimeSpec` with `ShortcutOverlaySpec` and any hotkeys.
3. Wrap in `RoutedFeatureLifecycleSpec`.
4. Bind in `bind_runtime` with `bind_routed_feature_lifecycle`.
5. Unbind in `shutdown_runtime` with `shutdown_routed_feature_lifecycle`.

```python
self._runtime_spec = RoutedRuntimeSpec(
  scene_name="main",
  shortcut_overlays=(
    ShortcutOverlaySpec(
      attr_name="_help_overlay",
      action_registry_attr="action_registry",
      toggle_action_name="show_help",
      toggle_key=pygame.K_F9,
      toggle_scene_name="main",
    ),
  ),
)
self._lifecycle_spec = RoutedFeatureLifecycleSpec(runtime_spec=self._runtime_spec)
```

Validation notes: confirm overlay toggle works, overlay content reflects actions, and shutdown removes bindings.

### Recipe 2: Window Presenter, Task Panel, and Focus Toggle

Goal: manage floating windows with predictable visibility and focus behavior.

Why this combination: presenter classes isolate window internals, while task-panel and focus-toggle specs keep window UX coherent during show/hide transitions.

Step-by-step pattern:
1. Declare `AnchoredWindowSpec` (or bundle spec).
2. Implement a `WindowPresenter` subclass.
3. Create presenter-backed window in feature `build`.
4. Configure `TaskPanelFocusToggleSpec` in routed runtime wiring.
5. Toggle visibility with presentation helpers.

```python
self.window = create_feature_presented_window(host, self, PresenterClass, window_spec)
set_window_visible_state(self.window, visible=True)
```

Validation notes: hidden windows should leave focus traversal; task-panel toggle and actual visibility must stay synchronized.

### Recipe 3: State Store, Persistence, and Snapshot Migration

Goal: keep shared application state stable across schema evolution.

Why this combination: centralized state (`AppStateStore`) plus versioned snapshots (`SnapshotMigrator`) allows controlled forward migration without brittle ad-hoc transforms.

Step-by-step pattern:
1. Define app state in `AppStateStore`.
2. Expose per-feature slices using `StateSelector`.
3. Save snapshots via `make_snapshot` with schema version.
4. Read incoming version with `read_version` and migrate with `SnapshotMigrator`.
5. Restore and inspect report fields for partial replay.

```python
snapshot = make_snapshot(current_version, state_dict)
version = read_version(snapshot)
migrated = migrator.migrate(snapshot)
```

Validation notes: migration path should cover older versions; restore report should show skipped/missing settings without fatal failure.

### Recipe 4: Dataflow Pipeline, Telemetry, and Error Boundary

Goal: process data safely in background-like stages with measurable performance and graceful UI degradation.

Why this combination: pipeline cancellation prevents stale commits, telemetry locates bottlenecks, and `ErrorBoundary` protects UI continuity when presenter/render code fails.

Step-by-step pattern:
1. Compose pipeline stages with cancellation tokens.
2. Add telemetry spans around stage execution.
3. Surface progress via observables.
4. Wrap visual output subtree in `ErrorBoundary`.

```python
pipeline = DataflowPipeline(stages=(
  PipelineStage("load", load_fn),
  PipelineStage("rank", rank_fn),
))
```

Validation notes: stale generations must cancel, reports should identify slow stages, and boundary fallback should render if subtree errors occur.

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
  StaticAccessibilitySpec,
  TelemetryConfig,
  bootstrap_host_application,
  bind_routed_feature_lifecycle,
  shutdown_routed_feature_lifecycle,
)


class CounterFeature(RoutedFeature):
  HOST_REQUIREMENTS = {
    "build": ("app",),
    "bind_runtime": ("action_registry",),
  }

  def __init__(self) -> None:
    super().__init__("counter", scene_name="main")
    self.value = ObservableValue(0)
    self.label = None
    self._dispose = None
    self._runtime_spec = RoutedRuntimeSpec(
      scene_name="main",
      shortcut_overlays=(
        ShortcutOverlaySpec(
          attr_name="_help_overlay",
          action_registry_attr="action_registry",
          toggle_action_name="show_help",
          toggle_key=pygame.K_F9,
          toggle_scene_name="main",
        ),
      ),
    )
    self._lifecycle_spec = RoutedFeatureLifecycleSpec(runtime_spec=self._runtime_spec)

  def build(self, host) -> None:
    self.label = host.app.add(LabelControl("counter_label", Rect(24, 24, 360, 32), text="Count: 0"), scene_name="main")

  def bind_runtime(self, host) -> None:
    self._dispose = self.value.subscribe(lambda v: setattr(self.label, "text", f"Count: {v}"))
    bind_routed_feature_lifecycle(self, host, self._lifecycle_spec)

  def shutdown_runtime(self, host) -> None:
    if callable(self._dispose):
      self._dispose()
      self._dispose = None
    shutdown_routed_feature_lifecycle(self, host, self._lifecycle_spec)


class ReferenceHost:
  def __init__(self) -> None:
    self.config = HostApplicationConfig(
      display_size=(1280, 720),
      window_title="gui_do Reference",
      fonts={"default": {"system": "arial", "size": 14}},
      font_role_specs=({"body": {"size": 14, "font": "default"}},),
      cursors=(),
      scene_specs=(SceneSetupSpec(name="main", pretty_name="Main", make_initial=True),),
      feature_specs=(FeatureSpec("counter_feature", CounterFeature),),
      window_specs=(),
      runtime_scene_specs=(RuntimeSceneSpec(scene_name="main", bind_escape_to_exit=True),),
      action_specs=(
        ActionSpec(action_id="exit", label="Exit", kind="exit", key=pygame.K_ESCAPE),
        ActionSpec(action_id="show_help", label="Show Help", kind="palette_open"),
      ),
      static_accessibility_specs=(
        StaticAccessibilitySpec("counter_label", "label", "Counter output"),
      ),
      initial_scene_name="main",
      telemetry=TelemetryConfig(enabled=True),
      target_fps=120,
    )

  def run(self) -> int:
    bootstrap_host_application(self, self.config)
    self._restore_workspace("workspace.json")
    result = self.app.run_entrypoint(target_fps=120)
    self._save_workspace("workspace.json")
    return result

  def _restore_workspace(self, path: str) -> None:
    try:
      self.app.load_workspace(path)
    except Exception:
      pass

  def _save_workspace(self, path: str) -> None:
    try:
      self.app.save_workspace(path)
    except Exception:
      pass
```

### What This Listing Demonstrates

This reference app shows the complete Tier-1/Tier-2 bootstrap path with a routed feature, reactive label binding, declarative action/runtime scene configuration, lifecycle-managed shortcut overlay wiring, telemetry enablement, and workspace restore/save hooks around the runtime entrypoint.

### Validation Checklist

1. Application opens to the main scene without startup errors.
2. Counter label updates when the feature observable changes.
3. `F9` toggles the shortcut overlay.
4. `Escape` triggers exit behavior via action/runtime scene policy.
5. Workspace load/save hooks run without aborting startup/shutdown on failures.

[Back to Table of Contents](#table-of-contents)

## Testing, Diagnostics, and Reliability

[Back to Table of Contents](#table-of-contents)

Testing and reliability work in gui_do are organized around contracts first, then runtime behavior, then operational diagnostics. The contract suite validates what must remain true across releases (public API, runtime guarantees, architecture boundaries, workspace semantics). Runtime tests then validate subsystem composition under normal and stressed paths. Diagnostics tooling closes the loop when regressions appear in real scenarios.

### Contract Tests

[Back to Table of Contents](#table-of-contents)

Run the core contract set with:

```bash
python -m pytest -q tests/test_public_api_exports.py tests/test_public_api_docs_contracts.py tests/test_runtime_operating_contracts.py tests/test_boundary_contracts.py tests/test_gui_application_workspace_contracts.py
```

Coverage intent by file:
- `tests/test_public_api_exports.py`: verifies root exports in `__all__` are present and importable.
- `tests/test_public_api_docs_contracts.py`: verifies public API docs alignment with exported names.
- `tests/test_runtime_operating_contracts.py`: verifies runtime guarantees such as scheduler budget clamps, event normalization, scene isolation, and deterministic routing order.
- `tests/test_boundary_contracts.py`: verifies package boundary contracts between `gui_do` and demo layers.
- `tests/test_gui_application_workspace_contracts.py`: verifies workspace load/restore behavior and report semantics.

Additional high-value contract/runtime files currently present include:
- `tests/test_architecture_boundary_docs_contracts.py`
- `tests/test_core_only_bootstrap_contracts.py`
- `tests/test_demo_feature_package_contracts.py`
- `tests/test_runtime_guarantees_and_determinism.py`

### Runtime Behavior Tests

[Back to Table of Contents](#table-of-contents)

Runtime behavior testing should explicitly cover workspace load/save roundtrips, overlay/tooltip/cursor routing, deterministic layout and animation outcomes, control runtime interactions, and accessibility spec wiring. The objective is not only correctness on happy paths but stable behavior under scene transitions, visibility toggles, and partial restore states.

### Debug and Trace Tools

[Back to Table of Contents](#table-of-contents)

Use `EventRecorder` and `EventPlayback` to capture and replay input traces for deterministic bug reproduction. Use `DebugOverlay` for visual diagnostics during runtime and `PropertyInspectorPanel` plus Tier 17 introspection APIs for structural/runtime property inspection. For performance analysis, use telemetry log workflows (`load_telemetry_log_file`, `analyze_telemetry_log_file`, `analyze_telemetry_records`, `render_telemetry_report`) to identify sustained hotspots instead of relying on subjective visual smoothness.

### Maintainer Release Runbook

[Back to Table of Contents](#table-of-contents)

1. Run contract tests and confirm no public API or boundary regressions.
2. Run targeted runtime suites for touched systems.
3. Validate docs contract alignment with current root exports.
4. Verify representative end-to-end scenarios and scene transitions.
5. Capture telemetry baselines for representative interactions.
6. Validate workspace restore behavior and inspect skipped/missing settings in restore reports.
7. Finalize manual updates only after behavior and contracts are consistent.

### Regression Triage Workflow

[Back to Table of Contents](#table-of-contents)

Start with reproducibility: record a failing sequence or write a minimal test case. Then trace event and lifecycle flow (normalization, routing, feature hooks, scheduler involvement). Localize the failure to one subsystem boundary. Add or update tests first to lock expected behavior. Patch at the narrowest layer that preserves contracts. Finally, run adjacent contract/runtime suites to prevent collateral regressions.

### Maintainer Diff Checklist

[Back to Table of Contents](#table-of-contents)

Inventory delta checks:
1. Compare current root exports in gui_do/__init__.py with Appendix D and Appendix D.1 entries.
2. Check docs contracts for changed runtime guarantees, API policies, and architecture boundary rules.
3. Check tests for new contract and runtime modules that imply manual coverage changes.
4. Check demo_features for new composition patterns that should be codified in Integration Patterns.

Content integrity checks:
1. Ensure every changed system is updated in both chapter narrative and appendix quick-index references.
2. Remove deleted APIs from examples, recipes, and appendix indexes.
3. Classify added APIs at the correct abstraction level, preferring Tier 1 guidance before lower tiers.

Navigation and structure checks:
1. Verify all newly added sections are present in the Table of Contents and anchors resolve.
2. Verify every major section still includes a Back to Table of Contents link.
3. Keep top-level chapter order stable unless an intentional restructure is documented in migration notes.

Operational checks:
1. Re-run high-priority contract tests.
2. Validate End-to-End Reference Application assumptions against current runtime behavior.
3. Record unresolved ambiguities as explicit TODO notes in migration/deprecation notes.

Contract test command:

```bash
python -m pytest -q tests/test_public_api_exports.py tests/test_public_api_docs_contracts.py tests/test_runtime_operating_contracts.py tests/test_boundary_contracts.py tests/test_gui_application_workspace_contracts.py
```

[Back to Table of Contents](#table-of-contents)

## Performance and Scaling Guidance

[Back to Table of Contents](#table-of-contents)

### Scheduler Budget Contract

Runtime contract values are:
- fraction: `0.12` of dt milliseconds
- floor: `0.5 ms`
- ceiling: `4.0 ms`

These bounds prevent scheduler starvation on fast frames and prevent runaway dispatch on slow frames.

### Dirty-Region Rendering

`DirtyRegionTracker` is a primary draw optimization path for complex scenes. Maintain dirty regions as state changes occur, and gate expensive redraw paths by checking dirty overlap. The incremental union cache means overlap checks can be handled without scanning every dirty rect for each candidate region.

### Virtualization and Incremental Rendering

Use `VirtualizationCore` and `VirtualizedWindow` for large collections. Use `ListDiffCalculator` to compute incremental patches instead of full-list redraws. Reuse item views with `RecyclePool` to minimize churn and allocation pressure.

### Practical Scaling Checklist

- Enforce scene-scoped update and handler routing.
- Avoid per-frame full collection/object reallocation.
- Use `ObjectPool` for high-churn short-lived objects.
- Debounce expensive input-driven operations with `Debouncer`.
- Use `DataflowPipeline` and `CancellationToken` for preemptible transforms.
- Profile representative user interactions instead of idle loops.
- Gate expensive render paths with `DirtyRegionTracker`.

[Back to Table of Contents](#table-of-contents)

## Migration, Versioning, and Deprecation Notes

[Back to Table of Contents](#table-of-contents)

### Versioned Snapshot Strategy

Recommended migration flow:
1. Save with `make_snapshot(current_version, state_dict)`.
2. Read incoming version with `read_version(raw)`.
3. Migrate with `SnapshotMigrator.migrate(snapshot)` using registered `MigrationStep` edges on `MigrationRegistry`.
4. Restore migrated data into runtime state.

`MigrationError` indicates no valid migration path or failed migration execution.

### Deprecation Handling

Preferred policy is additive change first, removals second. Add new optional fields/entry points while preserving previous behavior with warnings, then remove only after documented migration paths exist. As of this generation, no deprecated public APIs are formally cataloged in the root export surface. Future deprecations should be recorded here with replacement guidance and removal timelines.

### Upgrade Checklist

1. Run contract tests before and after upgrade.
2. Verify consumer imports remain root-based (`from gui_do import ...`).
3. Re-check action/input/focus behavior in active scenes.
4. Validate restore report fields, especially `skipped_settings` and `missing_settings_blocks`.
5. Compare telemetry baselines under representative scenarios.

[Back to Table of Contents](#table-of-contents)

## FAQ and Troubleshooting

[Back to Table of Contents](#table-of-contents)

### Should I build apps directly with controls or with features?

Build with features as the architectural unit. Controls are vital, but they should remain implementation details inside feature boundaries. Features provide lifecycle ordering, host dependency contracts, runtime wiring, and teardown behavior that controls alone do not provide.

### When should I use `RoutedFeature` over `Feature`?

Use `RoutedFeature` when topic-based message dispatch and declarative runtime wiring are central to the feature (hotkeys, overlay wiring, task-panel toggles, event subscriptions). Use `Feature` when you only need standard lifecycle hooks and local control composition.

### Why are some key handlers not firing?

Check four things in order: focus ownership, scene/window scope alignment, modal overlay capture, and action binding registration. If uncertain, record and replay with `EventRecorder` to confirm where the event stops.

### Why do toast clicks not pass through?

Toast click consumption is intentional to prevent accidental click-through to underlying controls. Use toast callbacks for intentional interactions.

### How do I avoid breaking workspace restore across versions?

Always version snapshots and migrate explicitly. Use `VersionedSnapshot` patterns (`make_snapshot`, `read_version`, `SnapshotMigrator`) and treat restore report fields as required diagnostics, not optional metadata.

### How do I confirm my API usage is on the supported surface?

Use explicit named imports from root `gui_do` and validate against export contracts with the public API tests. Avoid direct imports from internal submodules in consumer applications.

### Why does my feature `bind_runtime` appear to run before sibling `build`?

The framework contract is all-build then all-bind for the scene set. If behavior appears otherwise, inspect scene assignment and feature registration order first, then trace with instrumentation.

### How do I add shortcuts without editing every event handler path?

Declare `ActionSpec` plus `ActionHotkeySpec` or routed runtime spec entries. Let the action/input routing system perform wiring and teardown automatically.

[Back to Table of Contents](#table-of-contents)

## Appendix

[Back to Table of Contents](#table-of-contents)

### Appendix A: Glossary

[Back to Table of Contents](#table-of-contents)

**Feature**: A lifecycle-managed behavior unit (`Feature`, `DirectFeature`, `LogicFeature`, `RoutedFeature`) that encapsulates UI/logic composition and runtime hooks.

**Spec**: Declarative data describing runtime wiring (for example feature specs, action specs, scene specs, window specs) consumed by bootstrap/build helpers.

**Host**: A plain Python object passed to bootstrap and populated with runtime members (`app`, scene presentation, registered features, routing helpers).

**Scene**: A top-level interaction context. Feature activation and routing are scene-scoped.

**Window presentation**: The visibility/focus/toggle model for windows within a scene, including menu-strip and task-panel integrations.

**Routed runtime**: A declarative bundle (`RoutedRuntimeSpec`) for feature-level runtime wiring such as hotkeys, overlays, and subscriptions.

**Observable**: A value or collection that notifies subscribers on mutation.

**Workspace state**: Persisted session context, including scene state, feature state, and settings replay metadata.

**Contract test**: A test that verifies normative framework guarantees rather than isolated implementation details.

**Tier**: A root-export grouping that communicates abstraction level and recommended adoption order.

[Back to Table of Contents](#table-of-contents)

### Appendix B: Lifecycle/Event Sequence

[Back to Table of Contents](#table-of-contents)

1. `bootstrap_host_application` builds host runtime members from declarative config.
2. All feature `build(host)` hooks execute.
3. All feature `bind_runtime(host)` hooks execute.
4. Runtime loop starts.
5. Raw pygame events normalize to `GuiEvent`.
6. Overlay/focus/window/scene routing stages process events.
7. Feature event handlers run in active-scene routing context.
8. Feature update hooks run and scheduler work is dispatched within budget.
9. Draw hooks and control rendering compose the frame.
10. Scene transitions apply shutdown/build/bind ordering for departing/arriving scene features.
11. Shutdown runs final runtime teardown and optional workspace save workflows.

[Back to Table of Contents](#table-of-contents)

### Appendix C: System Dependency Map

[Back to Table of Contents](#table-of-contents)

Tier 1 bootstrap depends on lifecycle abstractions, runtime spec dataclasses, action/input declarations, and scene/window presentation helpers to realize complete application startup. This creates the integration backbone that higher-level app code uses.

Feature systems depend on controls, data/observables, and event/action routing. Layout and focus policies then depend on control-tree state and current scene/window visibility. Overlays depend on routing precedence and focus-capture semantics.

Persistence and migration depend on state models and registered scene/feature surfaces so restore replay can map persisted data onto active runtime objects. Scheduling systems depend on per-frame lifecycle loops and scene-scoped runtime services.

Telemetry and introspection are cross-cutting layers: they instrument and inspect all runtime strata without owning business behavior. Audio integrates through semantic event publication and pygame mixer-backed cue routing. Service scope can be injected across tiers as a dependency container.

[Back to Table of Contents](#table-of-contents)

### Appendix D: API Quick Index

[Back to Table of Contents](#table-of-contents)

This quick index is organized by topic using names exported at the `gui_do` root. For complete authoritative membership, also see `gui_do/__init__.py`.

Bootstrap and host configuration:
- `HostApplicationConfig`, `HostApplicationBindingSpec`, `bootstrap_host_application`, `build_host_application_config`, `SceneSetupSpec`, `SceneRootSpec`, `FeatureSpec`, `WindowSpec`, `RuntimeSceneSpec`, `ActionSpec`, `TelemetryConfig`, `SceneBundleBindingSpec`, `FeatureWindowBundleBindingSpec`, `WindowToggleBindingSpec`, `PaletteBindingSpec`, `FontRoleBindingSpec`, `CursorBindingSpec`, `StaticAccessibilitySpec`.

Features and lifecycle:
- `Feature`, `DirectFeature`, `LogicFeature`, `RoutedFeature`, `FeatureMessage`, `FeatureManager`, `RoutedRuntimeSpec`, `RoutedFeatureLifecycleSpec`, `bind_routed_feature_lifecycle`, `shutdown_routed_feature_lifecycle`, `register_routed_feature_companions`, `setup_routed_runtime`.

Events, actions, input, focus:
- `GuiEvent`, `EventType`, `EventPhase`, `EventManager`, `EventBus`, `EventRecorder`, `EventPlayback`, `RecordedEvent`, `ActionManager`, `ActionRegistry`, `ActionDescriptor`, `InputMap`, `InputBinding`, `KeyChordManager`, `FocusManager`, `FocusScopeManager`, `WindowFocusManager`, `FocusRing`, `InteractionStateMachine`.

State and observables:
- `ObservableValue`, `ObservableList`, `ObservableDict`, `CollectionChange`, `ChangeKind`, `ComputedValue`, `Binding`, `BindingGroup`, `CollectionView`, `CollectionViewQuery`, `reactive_batch`, `AppStateStore`, `StateSelector`, `StateTransaction`.

Controls and presenters:
- `PanelControl`, `LabelControl`, `ButtonControl`, `ToggleControl`, `SliderControl`, `ScrollbarControl`, `CanvasControl`, `CanvasViewport`, `TabControl`, `TextInputControl`, `TextAreaControl`, `DropdownControl`, `ListViewControl`, `DataGridControl`, `TreeControl`, `WindowControl`, `TaskPanelControl`, `WindowPresenter`, `ErrorBoundary`, `PropertyInspectorPanel`.

Layout and spatial:
- `LayoutManager`, `FlexLayout`, `GridLayout`, `ConstraintLayout`, `ConstraintLayoutEngine`, `AdaptivePolicy`, `ResponsiveLayout`, `DockWorkspace`, `WindowTilingManager`, `SnapGrid`, `FlowLayout`, `Viewport`, `VirtualizationCore`, `VirtualizedWindow`, `RecyclePool`.

Overlays and command surfaces:
- `OverlayManager`, `DialogManager`, `ToastManager`, `ContextMenuManager`, `CommandPaletteManager`, `TooltipManager`, `NotificationCenter`, `ShortcutHelpOverlay`, `PopupPlacement`, `compute_popup_rect`, `DragDropManager`, `ClipboardManager`, `TransferManager`.

Forms, text, validation:
- `FormModel`, `FormSchema`, `DocumentModel`, `WizardFlow`, `ValidationPipeline`, `AsyncFormValidator`, `SchemaFormRuntime`, `ValidationPolicy`, `TextFormatter`, `TextFlow`, `TextSearcher`, `StringTable`, `LocaleRegistry`.

Data and pipelines:
- `VirtualItemSource`, `FixedItemSource`, `SortFilterProxySource`, `AsyncDataProvider`, `LoadState`, `DataflowPipeline`, `PipelineStage`, `CancellationToken`, `DataCache`, `ObjectPool`, `ListDiffCalculator`.

Graphics and audio:
- `DirtyRegionTracker`, `DrawContext`, `SurfaceCompositor`, `ShapeRenderer`, `SpriteSheet`, `ParticleSystem`, `TileMap`, `SceneGraph2D`, `Camera2D`, `OffscreenRenderTarget`, `SoundCue`, `SoundBankRegistry`, `SoundEventBus`.

Telemetry and introspection:
- `TelemetryCollector`, `TelemetrySample`, `configure_telemetry`, `telemetry_collector`, `analyze_telemetry_log_file`, `render_telemetry_report`, `SceneSpatialIndex`, `ui_property`, `PropertyRegistry`, `PropertyInspectorModel`.

Persistence and migration:
- `WorkspacePersistenceManager`, `WorkspaceState`, `SettingsRegistry`, `SceneSnapshot`, `UndoContextManager`, `SchemaVersion`, `VersionedSnapshot`, `MigrationStep`, `MigrationRegistry`, `SnapshotMigrator`, `MigrationError`, `make_snapshot`, `read_version`.

[Back to Table of Contents](#table-of-contents)

### Appendix D.1: Tier Matrix

[Back to Table of Contents](#table-of-contents)

| Tier | System | Representative key types |
|---|---|---|
| 1 | Primary entry points and data-driven APIs | `HostApplicationConfig`, `FeatureSpec`, `ActionSpec`, `bootstrap_host_application`, `build_host_application_config` |
| 2 | Core application and scene management | `GuiApplication`, `create_display`, `SceneTransitionManager`, `SceneTransitionStyle`, `apply_scene_setup_specs` |
| 3 | Essential data and state management | `ObservableValue`, `ComputedValue`, `ObservableList`, `CollectionView`, `Binding` |
| 4 | Events, actions, focus and input | `GuiEvent`, `EventType`, `ActionRegistry`, `InputMap`, `FocusManager` |
| 5 | Scheduling and animation | `TaskScheduler`, `TweenManager`, `TransitionManager`, `CooperativeScheduler`, `SceneTimeline` |
| 6 | Theme and font management | `ThemeManager`, `ColorTheme`, `FontManager`, `FontRoleRegistry`, `ScopedThemeManager` |
| 7 | Telemetry and diagnostics | `TelemetryCollector`, `configure_telemetry`, `analyze_telemetry_records`, `render_telemetry_report` |
| 8 | Layout and spatial | `LayoutManager`, `FlexLayout`, `GridLayout`, `DockWorkspace`, `Viewport` |
| 9 | Overlay managers and windows | `OverlayManager`, `DialogManager`, `ToastManager`, `CommandPaletteManager`, `ShortcutHelpOverlay` |
| 10 | Forms and data binding | `FormModel`, `FormSchema`, `DocumentModel`, `WizardFlow`, `ValidationPipeline` |
| 11 | State and persistence | `CommandHistory`, `StateMachine`, `SettingsRegistry`, `WorkspacePersistenceManager`, `SceneSnapshot` |
| 12 | Primary controls | `PanelControl`, `LabelControl`, `ButtonControl`, `SliderControl`, `TabControl` |
| 13 | Extended controls | `TextInputControl`, `ListViewControl`, `DataGridControl`, `WindowControl`, `ErrorBoundary` |
| 14 | Text and localization | `TextFormatter`, `TextFlow`, `TextSearcher`, `StringTable`, `LocaleRegistry` |
| 15 | Data and collections | `VirtualItemSource`, `AsyncDataProvider`, `DataCache`, `ObjectPool`, `ListDiffCalculator` |
| 16 | Graphics and rendering | `DirtyRegionTracker`, `DrawContext`, `SurfaceCompositor`, `ParticleSystem`, `SceneGraph2D` |
| 17 | Introspection and inspection | `SceneSpatialIndex`, `ui_property`, `PropertyRegistry`, `PropertyInspectorModel` |
| 18 | Advanced runtime and bootstrapping | `set_window_visible_state`, `create_feature_presented_window`, `register_routed_feature_companions`, `ActiveTabUpdateRouter`, `TabLayoutContext` |
| 19 | Infrastructure internals | `UiEngine` |
| 20 | Audio | `SoundCue`, `SoundBankRegistry`, `SoundEventBus` |
| 21 | Accessibility | `AccessibilityRole`, `AccessibilityNode`, `AccessibilityTree`, `AccessibilityBus` |
| 22 | Theme invalidation | `ThemeInvalidationBus` |
| 23 | Undo context routing | `UndoContextManager` |
| 24 | Async form validation | `AsyncFieldValidator`, `AsyncFormValidator` |
| 25 | Scoped service graph | `ServiceKey`, `ServiceScope`, `ScopeStack` |
| 26 | Cancelable dataflow pipeline | `DataflowPipeline`, `PipelineStage`, `CancellationToken`, `PipelineHandle` |
| 27 | Transactional app state store | `AppStateStore`, `StateSelector`, `StateTransaction` |
| 28 | Adaptive constraint layout v2 | `ConstraintLayoutEngine`, `ConstraintSet`, `AdaptivePolicy`, `resolve_adaptive_policy` |
| 29 | Unified virtualization core | `VirtualizationCore`, `VirtualizedWindow`, `RecyclePool`, `MeasurePolicy` |
| 30 | Interaction state machine framework | `InteractionStateMachine`, `InteractionPhase`, `InteractionContext`, `InteractionTransition` |
| 31 | Schema-driven form runtime | `SchemaFormRuntime`, `FieldGraphSchema`, `FieldSchema`, `ValidationPolicy` |
| 32 | Portable snapshot and migration layer | `SnapshotMigrator`, `MigrationRegistry`, `MigrationStep`, `VersionedSnapshot`, `SchemaVersion` |

[Back to Table of Contents](#table-of-contents)

### Appendix D.2: Selection Heuristics

[Back to Table of Contents](#table-of-contents)

1. Start at Tier 1. If data-driven bootstrap and lifecycle specs solve the problem, stop there.
2. Move down tiers incrementally only when lower-level control is required.
3. Use Tier 18 helpers for advanced bootstrap/runtime extension patterns.
4. Keep application imports root-based (`from gui_do import ...`).
5. Avoid Tier 19 internals in consumer code.

Decision shortcuts:
- App setup: `HostApplicationConfig` plus `bootstrap_host_application`.
- Cross-feature runtime wiring: `RoutedRuntimeSpec` and routed lifecycle helpers.
- Large dataset UI: virtualization and pipeline APIs before custom manual loops.
- Persistence compatibility: `WorkspacePersistenceManager` plus migration APIs.
- Discoverable shortcuts: `ShortcutOverlaySpec` with routed runtime wiring.

[Back to Table of Contents](#table-of-contents)

### Appendix E: Architecture Templates

[Back to Table of Contents](#table-of-contents)

### Template 1: Small Single-Scene App

Use one scene and a small set of features, with observable state local to features. Define commands through `ActionSpec` and use `RuntimeSceneSpec(bind_escape_to_exit=True)` for safe baseline behavior.

### Template 2: Multi-Window Workbench

Use multiple scenes, scene menu strip, task panel toggles, and one `WindowPresenter` subclass per window. Bundle features and windows with `FeatureWindowBundleBindingSpec` and use routed specs for shortcut surfaces.

### Template 3: Data-Heavy Analysis Tool

Use `AsyncDataProvider`, `SortFilterProxySource`, virtualization APIs, and `DataflowPipeline` cancellation. Gate expensive draws with `DirtyRegionTracker` and keep telemetry enabled for baselines.

### Template 4: Long-Running Workflow App

Use `CooperativeScheduler` coroutines for staged workflows, expose progress through observables, gather user input via wizard/form systems, and persist sessions with migration-aware snapshots.

[Back to Table of Contents](#table-of-contents)
