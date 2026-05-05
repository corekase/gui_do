# gui_do Manual

This manual is the primary learning and reference resource for the `gui_do` framework. It covers the framework end-to-end: from foundational theory through every major system, integration patterns, testing, and maintenance. It is written for developers building applications with `gui_do` and for maintainers responsible for keeping the framework and this document aligned. Whether you are encountering `gui_do` for the first time or tracing the behavior of a specific subsystem, this document is designed to be your complete reference without needing to read source code.

---

## Table of Contents

- [How to Use This Manual](#how-to-use-this-manual)
  - [Reading Paths](#reading-paths)
  - [Tri-Lens Markers](#tri-lens-markers)
  - [Contract Alignment](#contract-alignment)
  - [Known Non-Goals](#known-non-goals)
- [Conceptual Foundations (Theory)](#conceptual-foundations-theory)
  - [Data-Driven Design](#data-driven-design)
  - [Reactive Data and Observable State](#reactive-data-and-observable-state)
  - [Feature Composition and Lifecycles](#feature-composition-and-lifecycles)
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
  - [Contract Tests](#contract-tests)
  - [Runtime Behavior Tests](#runtime-behavior-tests)
  - [Debug and Trace Tools](#debug-and-trace-tools)
  - [Maintainer Release Runbook](#maintainer-release-runbook)
  - [Regression Triage Workflow](#regression-triage-workflow)
  - [Maintainer Diff Checklist](#maintainer-diff-checklist)
- [Performance and Scaling Guidance](#performance-and-scaling-guidance)
- [Migration, Versioning, and Deprecation Notes](#migration-versioning-and-deprecation-notes)
- [FAQ and Troubleshooting](#faq-and-troubleshooting)
- [Appendix](#appendix)
  - [Appendix A: Glossary](#appendix-a-glossary)
  - [Appendix B: Lifecycle and Event Routing Sequence](#appendix-b-lifecycle-and-event-routing-sequence)
  - [Appendix C: System Dependency Map](#appendix-c-system-dependency-map)
  - [Appendix D: API Quick Index by Topic](#appendix-d-api-quick-index-by-topic)
  - [Appendix D.1: Tier-to-System Reference Matrix](#appendix-d1-tier-to-system-reference-matrix)
  - [Appendix D.2: Public API Selection Heuristics](#appendix-d2-public-api-selection-heuristics)
  - [Appendix E: Architecture Templates](#appendix-e-architecture-templates)

---

## How to Use This Manual

[Back to Table of Contents](#table-of-contents)

This manual is organized to support three distinct modes of use: **learning**, **building**, and **maintaining**. A developer reading `gui_do` for the first time should progress through the manual linearly from Conceptual Foundations onward — each chapter assumes the concepts from prior chapters. A developer actively building a feature or application can jump directly to the relevant system chapter; each chapter is written to stand alone as a complete reference. A maintainer responsible for keeping this manual and the codebase aligned should use the Maintainer Diff Checklist and the system chapter structure as their working scaffold.

Every system chapter follows a fixed template: what the system is and why it exists, the mental model, the primary public APIs, a typical usage flow, a minimal example, an advanced pattern, common mistakes, and cross-links to related systems. This uniformity is intentional — once you have learned how one system chapter is organized, you can navigate any chapter efficiently.

### Reading Paths

**Beginner path** — if you are new to `gui_do` and want to build your first application:
1. Read Conceptual Foundations in full. Do not skip it — the theory here explains choices that will otherwise seem arbitrary.
2. Work through the Quickstart Path.
3. Read Architecture and Runtime Model.
4. Read Core Workflow: Build, Bind, Route, Update, Draw.
5. Read system chapters 8.1 (Bootstrap), 8.2 (Feature Lifecycle), 8.3 (Events/Actions), and 8.4 (State/Observables).
6. Read the End-to-End Reference Application listing and trace through it.
7. Return to specific system chapters as needed.

**Intermediate path** — if you are building non-trivial features and need system depth:
1. Skim Conceptual Foundations for the sections you have not internalized yet.
2. Read the Architecture and Core Workflow chapters.
3. Jump directly to the system chapters for the systems you are using.
4. Read Integration Patterns for composition recipes.
5. Use the API Quick Index (Appendix D) as your day-to-day reference.

**Maintainer path** — if you are maintaining the framework or this document:
1. Run the contract test suite first (command in Testing chapter).
2. Use the Maintainer Diff Checklist as your working checklist.
3. Consult the System Dependency Map (Appendix C) when evaluating change impact.

### Tri-Lens Markers

Some content is marked with a lens tag to indicate the primary audience it serves:

- **[Learn]** — conceptual explanation; most useful when building a mental model.
- **[Build]** — practical pattern or example; most useful when implementing.
- **[Maintain]** — operational guidance; most useful for maintainers and framework contributors.

Most content serves all three lenses simultaneously. Markers appear only when a section is primarily useful to one audience and might be safely skimmed by others.

### Contract Alignment

Several behavioral guarantees documented in this manual are formally specified in the `docs/` contract files. Where this manual states a behavioral guarantee, it is derived from one of these sources:

- `docs/runtime_operating_contracts.md` — scheduler budget, event normalization, scene isolation, focus candidate ordering.
- `docs/public_api_spec.md` — the canonical definition of which symbols are public.
- `docs/architecture_boundary_spec.md` — the boundary rules between `gui_do` and `demo_features`.
- `docs/package_contracts.md` — package-level contracts for imports and dependency direction.

When in doubt about a specific behavioral guarantee, the contract document takes precedence over this manual's prose. The contract tests in `tests/` verify these guarantees automatically.

### Known Non-Goals

`gui_do` intentionally does not aim to:

- **Be a general-purpose game engine.** The framework is designed for structured GUI applications and productivity tools on a pygame surface.
- **Abstract away pygame.** Developers using advanced graphics features will interact with pygame surfaces and rects directly.
- **Provide native OS widget toolkit.** All rendering is software-rendered to a pygame surface.
- **Support non-Python targets.** The framework is Python-only and depends on CPython behaviors.
- **Be a web framework.** There is no HTML/CSS rendering, no DOM model, and no network I/O in the framework core.
- **Replace a full accessibility toolkit.** Accessibility support covers practical keyboard navigation and ARIA-style role annotation, not full WCAG conformance.

---

## Conceptual Foundations (Theory)

[Back to Table of Contents](#table-of-contents)

This chapter describes the three foundational ideas that everything in `gui_do` builds on. Understanding these ideas before writing any application code will save you from puzzling over design decisions later. The framework's API surface is a direct consequence of these ideas — each system exists to make one of these ideas practical.

### Data-Driven Design

[Back to Table of Contents](#table-of-contents)

In `gui_do`, application structure is expressed as configuration data — specs, bindings, and descriptors — rather than as sequences of imperative calls. The runtime receives that data and performs all wiring automatically.

**What it means.** To separate description of *what to do* from the code that *does it*, a developer describes a scene, its features, actions, and windows through spec objects. The framework interprets those specs and builds the live application. The developer's job is to assemble a correct description; the framework's job is to execute it. This inversion of responsibility is not a stylistic preference — it is the core architectural contract of `gui_do`.

**The spec pipeline.** `HostApplicationBindingSpec` is the top-level description of an application. You populate it with scene specs, feature specs, action specs, window specs, and binding specs drawn from the `HostApplicationBindingSpec`, `RuntimeSceneSpec`, `FeatureSpec`, `ActionSpec`, `WindowSpec`, and their associated builder helpers. When you call `build_host_application_config`, the framework performs a single deterministic pass over those specs: resolving cross-references, validating requirements, merging defaults, and producing a fully wired `HostApplicationConfig`. Nothing in the output is ambiguous. You then hand that config to `bootstrap_host_application`, which starts the event loop.

The two-step design — build config, then run — is intentional. Building the config is a pure computation with no side effects; it can be done in test code with no running display. Running it is the side-effecting step. This means you can unit-test your entire application configuration, verify that all features are declared, and confirm that all required resources are referenced — all before the first window appears.

**Imperative wiring contrast.** In a traditional imperative GUI, adding a keyboard shortcut means finding input-handling code, inserting a branch, wiring a callback, and ensuring cleanup when the scene exits. In the data-driven approach, you add one `ActionSpec` with an `ActionHotkeySpec`. The framework registers it with the action registry, routes the key through the input map, and tears it down when the scene exits. No manual cleanup code is required, and no branching logic is scattered across unrelated methods.

**Reorganization without bootstrap impact.** Moving a class to a different file, splitting a large feature into a logic feature and a presentation feature, or reorganizing a package's internal modules — none of these changes require any modification to bootstrap code. Bootstrap code consumes public class references (the feature class itself) and spec values (plain data). It never imports from internal submodules. As long as each feature package's `__init__.py` exports the same public names, the bootstrap is completely insulated from internal reorganization.

**Testability.** Specs can be constructed and validated in unit tests with no running display. Feature instances can be built with mock host objects. The entire application configuration can be assembled and inspected without starting the event loop. This makes it practical to test configuration correctness — "are all required windows declared?", "are all scene transitions connected?" — before running anything.

**Specs as a serialization boundary.** Specs are pure data objects with named fields. They could in principle be stored, loaded from a configuration file, or generated programmatically. Named fields make specs self-documenting and forward-compatible: adding a new optional field in a future version does not break existing callers the way positional APIs would. This is the same reason the framework exposes many small named spec classes rather than a single large constructor.

**Where the boundary is.** The data-driven model governs *structure*: scene registration, feature assignment, action routing, window binding, focus group declaration. It does not govern *behavior*: what happens in `on_update`, what a feature draws, how it responds to an event. Behavior is imperative Python inside feature methods. The framework provides the skeleton; your features provide the meat.

---

### Reactive Data and Observable State

[Back to Table of Contents](#table-of-contents)

A reactive value notifies all subscribers automatically when it changes, without the producer needing to know who the consumers are. This is the second foundational idea in `gui_do` and the reason that UI code in feature methods tends to be surprisingly small.

**What reactive data means.** In a traditional imperative GUI, updating a model value means calling every UI element that depends on it. The producer must know all its consumers; adding a new consumer requires modifying the producer. In a reactive model, the value holds a list of subscribers and notifies them on change. A UI element subscribes once at setup time; subsequent changes flow to it automatically. The producer never changes when new consumers are added.

**The observable primitives.** `ObservableValue` wraps a single value. Call `.subscribe(callback)` to be notified whenever the value changes; the callback receives the new value. `ObservableList` and `ObservableDict` provide the same semantics for mutable collections, emitting `CollectionChange` events that identify exactly what changed (the `ChangeKind` and the affected item or key). These three primitives cover the vast majority of reactive state needs.

**`reactive_batch` and `is_batching`.** When multiple observables are mutated together — for example, updating several fields of a presentation model atomically — subscribers would normally fire once per mutation. Wrapping the mutations in a `reactive_batch` context manager batches all notifications and fires each subscriber exactly once after all mutations complete. Use `is_batching()` inside low-level code to check whether batching is currently active. Batching is important for consistency: a subscriber that reads multiple observables should see a coherent state, not a partially updated one.

**`ComputedValue`.** A derived observable that automatically recomputes from one or more source observables. When any source changes, the computed value recalculates and notifies its own subscribers. The key difference from manually subscribing and writing to a second `ObservableValue`: a `ComputedValue` is lazily re-evaluated, never out of sync, and automatically disposed when its dependencies are disposed. Use `ComputedValue` whenever a displayed value is a function of other observables; do not manually chain subscriptions for simple derivations.

**Subscription lifecycle.** Subscribe to observables in `bind_runtime` or in `on_create`-equivalent setup, when the full runtime is available. Dispose subscriptions in `shutdown_runtime` or the equivalent teardown method. `ObservableValue.subscribe` returns a token; call the token to unsubscribe. Failing to unsubscribe causes memory leaks and callbacks that fire on objects that have already been cleaned up — a common source of subtle bugs that manifest only after scene transitions.

**Control binding model.** Controls in the `gui_do` control tree accept either a plain value or an observable. When a control is bound to an `ObservableValue`, it registers an internal subscription and refreshes its display whenever the value changes. Feature code changes the observable; the control updates itself. No manual "refresh the label" calls are needed. This is how reactive state reaches the UI without feature methods explicitly poking controls.

**Cross-feature reactive state.** When one feature owns shared state that other features need to observe, it exposes an `ObservableValue` (or `ObservableList`) as a public attribute or via the host. Other features subscribe in their `bind_runtime` methods, when sibling features are available. The producing feature never holds references to its observers. This decoupling means features can be added, removed, or replaced without changing the producing feature.

**Anti-patterns to avoid.** Polling an `ObservableValue` inside `on_update` to detect changes defeats the reactive model, wastes CPU every frame, and introduces a one-frame latency. Subscribing in `build` before the runtime is ready causes errors or stale initial state. Forgetting to unsubscribe causes memory leaks and phantom callbacks that fire after the feature is supposed to be gone. Sharing mutable plain Python objects (lists, dicts) across features instead of observables breaks reactivity entirely — other features have no way to know when the data changed.

---

### Feature Composition and Lifecycles

[Back to Table of Contents](#table-of-contents)

A Feature is the primary unit of application behavior in `gui_do`. A self-contained object that declares its resource requirements, builds its UI, handles events, and tears itself down cleanly. Understanding the feature lifecycle and feature types is essential for writing well-structured `gui_do` applications.

**What a Feature is.** A Feature is a Python class that inherits from one of the four feature base classes. It is self-contained: it declares what resources it needs, builds its own UI elements, registers its own event handlers, and tears itself down cleanly. Features are composable: an application is a collection of features that coexist within scenes, each responsible for a discrete aspect of the application's behavior.

**Feature types and when to use each.** There are four feature base classes:

- `DirectFeature`: Renders directly to the screen surface every frame. Does not participate in the control tree, hit-testing, or keyboard focus. Use for background elements — animated backdrops, full-screen visual effects — that do not need to interact with the UI event system. Lowest overhead of the four types.

- `Feature`: The standard feature type. Builds controls in the scene's control tree during `build`. Participates in focus, hit-testing, and event routing. Use for any interactive UI — buttons, panels, input fields, or any control that the user interacts with directly.

- `LogicFeature`: Has no UI of its own. Exists to implement domain logic, manage shared state, run background computation, and publish results via observables that other features subscribe to. A `LogicFeature` is completely invisible to the user; its value is entirely in what it exposes to other features. Use when behavior must be testable in complete isolation from presentation.

- `RoutedFeature`: A `Feature` that also participates in action routing infrastructure. Can define route targets that receive named messages dispatched by the framework's action routing layer. Use when a feature must respond to framework-level named actions, or when it must coordinate with the action registry in ways that go beyond the standard event handling path.

**Lifecycle phases in depth.** Every feature passes through the same lifecycle phases, called in the same order by the framework:

- `build(host)`: Called once during scene construction. Create controls, add them to the scene tree, and build static structure. Everything created here exists for the scene's lifetime and will be cleaned up when the scene exits.

- `bind_runtime(host)`: Called after all features in the scene have completed `build`. This is the correct place to subscribe to observables, bind controls to data, register callbacks, and wire cross-feature interactions. All sibling features are available in `bind_runtime`; none are available in `build`.

- `handle_event(host, event)`: Called for every routed `GuiEvent` the framework delivers to this feature. Return `True` to consume the event (preventing further routing); return `False` or `None` to pass it on.

- `on_update(host, dt_seconds)`: Called every frame by the scheduler. `dt_seconds` is the elapsed time since the last frame in seconds. Use for animations, timers, and per-frame state updates. Keep fast: any computation that takes more than a small fraction of the frame budget delays the entire application.

- `draw(host, screen)`: Called every frame after `on_update`. Use for custom drawing that bypasses the control tree — raw pygame surface operations, particle effects, custom renders. Most features that use only the control tree can leave this method as a no-op.

- `shutdown_runtime(host)`: Called when the scene is exiting. Dispose subscriptions, cancel background tasks, and release resources.

**`HOST_REQUIREMENTS` protocol.** Each lifecycle method's resource needs are declared statically in the `HOST_REQUIREMENTS` class attribute — a dict mapping method names to tuples of required host attribute names. The framework validates these declarations at startup and raises clear errors for missing bindings before the first frame executes. A feature that says it needs `screen_rect` in `build` will never be called with a host that lacks it; the framework fails fast and explicitly rather than producing mysterious `AttributeError`s mid-run.

**Feature messaging.** Features communicate with each other through `FeatureMessage` objects, not through direct references to each other's classes or instances. A feature publishes a message by name with an optional payload dict; the framework routes it to features registered to receive messages of that name. This prevents implementation coupling: a feature sending a message does not need to know whether zero, one, or ten other features are listening.

**Scene assignment and transitions.** Each feature declares a `scene_name` that assigns it to a scene. The framework activates and deactivates features as scenes transition: teardown is called on departing features; `build` and `bind_runtime` are called on arriving features. Features from the previous scene do not receive events or updates after the transition completes. This makes scene transition a clean boundary — features do not need to guard against being called after their scene has exited.

**Folder and package composition convention.** Each feature package lives in its own folder. The package's `__init__.py` is its sole public surface, exporting the Feature class and public types. Internal files are organized by concern: a `*_feature.py` for the Feature subclass, a `*_presenter.py` for window layout, a `*_specs.py` for domain spec types, a `*_logic_feature.py` for the `LogicFeature` companion. Bootstrap code imports only from the package surface — never from internal submodules. This means the internal file structure of a feature package can be reorganized freely without any change to bootstrap or test code.

**Composition patterns.** The most common patterns are:

- *Logic + presentation split*: A `LogicFeature` runs computations and publishes results via `ObservableValue`s. A `Feature` or `RoutedFeature` subscribes to those observables and drives the UI. This separates testable logic from display code and allows the UI to be redesigned without changing the logic.
- *Presenter pattern*: A `Feature` delegates window layout to a `WindowPresenter` subclass that manages a `Window` and its internal structure. The feature owns the lifecycle; the presenter owns the layout.
- *Background feature pattern*: A `LogicFeature` drives `CooperativeScheduler` coroutines for long-running work (data loading, computation), publishing progress and results to observables that a UI feature displays. The user sees responsive progress updates while work happens off the hot frame path.

---

## Quickstart Path (Practice)

[Back to Table of Contents](#table-of-contents)

This chapter takes you from a fresh Python environment to a running `gui_do` application. Each step introduces exactly one idea; together they form the complete mental model you need to build non-trivial apps.

### Step 1: Install and Verify

```bash
python -m pip install -e . --no-deps
python -m pytest -q tests/test_public_api_exports.py
```

The first command installs `gui_do` in editable mode using only the dependencies already declared in `pyproject.toml`; this workflow requires `pygame` and `numpy` to already be installed in the environment (`numpy` is used internally for pixel buffer operations). The second command verifies that the public API surface exported from `gui_do/__init__.py` matches what the test suite expects. If both commands succeed without errors, your environment is ready.

### Step 2: Create a Minimal Host Configuration

The entry point for every `gui_do` application is `build_host_application_config` + `bootstrap_host_application`. You describe your application as a `HostApplicationBindingSpec`; the framework resolves it into a `HostApplicationConfig`; you hand that to `bootstrap_host_application`. Here is the minimal pattern:

```python
from gui_do import (
    HostApplicationBindingSpec,
    SceneBundleBindingSpec,
    SceneTransitionStyle,
    build_host_application_config,
    bootstrap_host_application,
)

config = build_host_application_config(
    HostApplicationBindingSpec(
        display_size=(1280, 720),
        window_title="My Application",
        fonts={
            "default": {"file": "path/to/font.ttf", "size": 14},
        },
        initial_scene_name="main",
        scene_bundle_entries=(
            SceneBundleBindingSpec(
                scene_name="main",
                pretty_name="Main",
                transition_style=SceneTransitionStyle.SLIDE_RIGHT,
                transition_duration=0.3,
                bind_escape_to_exit=True,
            ),
        ),
        feature_entries=(
            ("_my_feature", MyFeature),
        ),
    )
)

host = bootstrap_host_application(config)
host.app.run_entrypoint(target_fps=120)
```

`HostApplicationBindingSpec` accepts many optional fields — scene root specs, action bindings, cursor specs, telemetry config, and more. The minimal form shown above is enough to start an application; add binding specs incrementally as your application grows.

### Step 3: Add a Feature with Observable State

A Feature is the primary unit of behavior. Here is the simplest possible feature:

```python
from gui_do import Feature, ObservableValue

class CounterFeature(Feature):
    HOST_REQUIREMENTS = {
        "build": ("scene_controls", "screen_rect"),
        "bind_runtime": ("scene_controls",),
    }

    def __init__(self):
        super().__init__()
        self._count = ObservableValue(0)
        self._label = None
        self._subscription = None

    def build(self, host):
        from gui_do import LabelControl
        self._label = LabelControl(text=str(self._count.value), rect=host.screen_rect.inflate(-100, -100))
        host.scene_controls.add(self._label)

    def bind_runtime(self, host):
        self._subscription = self._count.subscribe(lambda v: self._label.set_text(str(v)))

    def shutdown_runtime(self, host):
        if self._subscription:
            self._subscription()
            self._subscription = None
```

This feature creates a label in `build` and wires it to an `ObservableValue` in `bind_runtime`. When `_count` changes anywhere, the label updates automatically. The subscription is cleaned up in `shutdown_runtime` to prevent callbacks after the feature is destroyed.

### Step 4: Add an Action and a Runtime Scene Policy

Actions let users trigger behavior through keyboard shortcuts, palette entries, or buttons. Add an `ActionSpec` and a `RuntimeSceneSpec` to your binding spec:

```python
from gui_do import ActionSpec, ActionHotkeySpec, SceneBundleBindingSpec

# Inside your HostApplicationBindingSpec:
action_entries=(
    ActionSpec(
        action_id="increment",
        label="Increment Counter",
        hotkey=ActionHotkeySpec(key="up"),
        scene_name="main",
    ),
),
```

`bind_escape_to_exit=True` on the `SceneBundleBindingSpec` automatically wires the Escape key to an exit action for that scene.

### Step 5: Run Loop

`bootstrap_host_application` returns a host object whose `.app` attribute is a `GuiApplication`. Call `.run_entrypoint(target_fps=120)` to start the event loop. The framework handles all frame pacing, event normalization, and shutdown:

```python
host = bootstrap_host_application(config)
host.app.run_entrypoint(target_fps=120)
```

The loop runs until the user closes the window or an exit action fires.

### Guided Build Track (Beginner)

Work through these six milestones in order. Each milestone has a single success criterion:

- **Milestone A**: App boots to a single scene with no errors in the console.
- **Milestone B**: One feature creates one visible control (e.g., a label with static text).
- **Milestone C**: One `ObservableValue` updates one label reactively when you change its value programmatically in `on_update`.
- **Milestone D**: One `ActionSpec` with one `ActionHotkeySpec` triggers expected behavior when the hotkey is pressed.
- **Milestone E**: One overlay (e.g., a shortcut overlay) opens and closes without blocking unrelated keypresses.
- **Milestone F**: A workspace save and load roundtrip preserves the expected state.

**Beginner confidence checklist.** Before moving past the Quickstart, verify that you can:
- Explain where `build` ends and `bind_runtime` begins (and why the distinction matters).
- Add or remove a feature by changing only the `feature_entries` tuple and nothing else.
- Trace a single keypress from raw input through the action registry to the handler that executes.

### Quickstart Failure Modes

**Feature never appears.** Verify that the `scene_name` in your `FeatureSpec` matches the `scene_name` in the `SceneBundleBindingSpec`, and that the feature entry is included in `feature_entries` of the `HostApplicationBindingSpec`.

**Hotkey does nothing.** Check that the `action_id` in `ActionSpec` matches the handler registration, the hotkey key name is correct (pygame key name string), and the action's `scene_name` matches the active scene.

**Overlay blocks unexpected keys.** Check whether `consume_unhandled_keys=True` is set on the overlay spec. Overlays with key consumption enabled intercept all keyboard events; you may need to configure explicit dismissal hotkeys or set `consume_unhandled_keys=False`.

**State updates but UI does not refresh.** Confirm that the subscription is created in `bind_runtime` (not `build`), that the `ObservableValue` you subscribed to is the same instance you are mutating, and that `shutdown_runtime` does not dispose the subscription prematurely.

---

## Architecture and Runtime Model

[Back to Table of Contents](#table-of-contents)

This chapter describes how `gui_do` is organized structurally and what behavioral guarantees the runtime provides. Read this before diving into specific system chapters — the boundary model, tier model, event pipeline, and runtime contracts are referenced throughout.

### Boundary Model: Framework vs Consumer

`gui_do` maintains a strict two-layer structure:

- **`gui_do/`**: The reusable framework package. Contains all runtime, controls, events, layout, state, persistence, scheduling, theme, and graphics systems. This package must not import from `demo_features/` or any consumer layer. It is designed to be usable as a standalone Python package independent of any demo code.

- **`demo_features/` and `gui_do_demo.py`**: The consumer integration layer. `gui_do_demo.py` is the application entrypoint; `demo_features/` contains feature packages that use the framework. Consumer code imports from the `gui_do` root package — never from `gui_do.*` internal submodules.

This boundary is enforced automatically by tests:
- `tests/test_boundary_contracts.py::test_gui_package_does_not_import_demo_features` — verifies via AST inspection that no file under `gui_do/` imports from `demo_features/`.
- `tests/test_boundary_contracts.py::test_demo_entrypoint_uses_gui_root_import` — verifies that the demo entrypoint imports only from `gui_do`, not internal submodules.

Run the boundary check at any time:
```bash
python -m pytest -q tests/test_boundary_contracts.py
```

The practical consequence: you can use `gui_do` as a library in your own application without any dependency on the demo layer.

### Tiered Public API Model

All public symbols in `gui_do` are organized into numbered tiers. The tier number communicates how abstract and how central the API is:

- **Tier 1 — Primary Entry Points and Data-Driven APIs**: The spec types, builder functions, and bootstrap entry point. This is where all new application code should start. If you can express what you need with Tier 1 APIs, you should.
- **Tier 2 — Core Application and Scene Management**: The `GuiApplication`, `create_display`, `SceneTransitionManager`, and scene setup utilities. Needed for apps that manage application state directly.
- **Tier 3 — Essential Data and State Management**: Observable primitives, reactive batching, collection views, selection models, binding helpers. Core reactive data layer.
- **Tier 4 — Events, Actions, Focus, and Input**: Event types, action registry, input mapping, focus management, and pointer routing. For features that need direct access to the event system beyond what specs provide.
- **Tier 5 — Scheduling and Animation**: The cooperative scheduler, tween engine, animation state machine. For frame-timed workloads and property animations.
- **Tier 6 — Theme and Font Management**: Theme registry, font role resolution, palette management. For UI features that respond to theme changes.
- **Tier 7 — Telemetry and Diagnostics**: Performance counters, frame time tracking, telemetry export. For monitoring and operational insight.
- **Tiers 8+**: Layout, overlay managers, forms, state/persistence, primary controls, extended controls, text/localization, data/collections, graphics, introspection, and advanced runtime systems. These are the building blocks; use them after you have established your Tier 1 spec structure.

The rule of thumb: when two tiers offer overlapping capability, use the lower-numbered (more abstract) tier first. Tier 1 spec fields are almost always sufficient for feature declaration; reaching into Tier 4 event system APIs is occasionally necessary for advanced routing requirements, not the default.

### Runtime Guarantees

The following behavioral guarantees are contractual — they are specified in `docs/runtime_operating_contracts.md` and verified by `tests/test_runtime_operating_contracts.py`:

- **Canonical `GuiEvent` normalization**: All raw pygame events are normalized to `GuiEvent` instances before any application-level dispatch. Application code receives only canonical events; it never needs to inspect raw pygame event types.
- **Scene-isolated update execution**: Runtime systems contained within a scene receive updates only while that scene is active. Cross-scene state leakage through the update loop is prevented by design.
- **Deterministic focus candidate ordering**: Window focus cycling produces a consistent order sorted by `control_id`. Adding or removing a window changes the candidate list but does not randomize the ordering of remaining candidates.
- **Scheduler dispatch budget clamping**: The cooperative scheduler's per-frame dispatch budget is clamped: fraction 0.12 of frame time, minimum floor 0.5 ms, maximum ceiling 4.0 ms. No single scheduler pass can consume an unbounded share of the frame.
- **Graceful workspace restore on missing keys**: When loading a saved workspace, missing settings keys are skipped without aborting the restore. The application loads what it can and leaves missing values at their defaults.

### Event Pipeline

`GuiApplication.process_event` routes every event through a fixed sequence of processing stages. Understanding this sequence is essential for debugging unexpected event behaviors:

1. **Normalize raw input**: Raw pygame events are converted to canonical `GuiEvent` instances with normalized coordinates and event types.
2. **Handle quit events early**: Platform quit events (window close) are checked immediately and trigger clean shutdown before any further routing.
3. **Update shared input state**: The shared input state (pressed keys, mouse buttons, modifiers) is updated for use by frame-timed logic.
4. **Update logical pointer state; apply lock/capture clamping**: The logical pointer position is updated and constrained by any active pointer lock or pointer capture region.
5. **Logicalize pointer events while preserving raw coordinates**: Pointer events are transformed to logical coordinates (accounting for scene camera or viewport offset) while raw coordinates are preserved on the event object for hit-testing.
6. **Route overlays, toasts, and focus management**: Active overlays and toast messages receive events first. Overlay dismissal and focus management are handled at this stage.
7. **Route keyboard events through keyboard manager and screen handler policy**: The keyboard manager applies input map lookups, routes hotkeys to their bound actions, and enforces screen-level key handler policy.
8. **Route feature handlers, scene dispatch, then fallthrough handlers**: The event is dispatched to feature `handle_event` methods in declaration order, then to any scene-level dispatch handlers, then to registered fallthrough handlers.
9. **Respect `propagation_stopped` and `default_prevented`**: These flags on the event object act as hard stop signals. Setting `propagation_stopped` ends routing immediately; setting `default_prevented` skips default framework behavior for the event.

### Known Non-Goals

`gui_do` intentionally does not aim to:

- Achieve OS-native widget parity across all platforms. The surface is pygame; native widget integration is out of scope.
- Make architectural decisions for application business logic. The framework provides structure for UI features; domain logic organization is the application's responsibility.
- Expose internal infrastructure tiers as beginner entry points. Tiers 19 and above are framework internals; application code should not depend on them.
- Make star-import behavior part of the public API compatibility contract. Import from the `gui_do` root by explicit name; `from gui_do import *` is not a supported usage pattern.

---

## Core Workflow: Build, Bind, Route, Update, Draw

[Back to Table of Contents](#table-of-contents)

Every `gui_do` application, regardless of size, follows the same five-phase workflow. Understanding what each phase is responsible for — and what it must not do — prevents the most common structural bugs.

### Phase Reference

**Build.** Instantiate controls, initialize local observables, and declare the static structure of the feature's UI. Invariant: no subscriptions, no references to sibling features, and no host-dependent wiring should be established here. `build` is called before all features in the scene have completed their own `build`, so sibling features may not yet exist in a usable state.

**Bind Runtime.** Attach all host-dependent wiring: subscribe to observables, bind controls to data sources, register callbacks, and establish cross-feature references. Invariant: all siblings have completed `build`; all controls exist; it is safe to subscribe. This is the correct place for all reactive wiring. Any subscription established in `bind_runtime` must be disposed in `shutdown_runtime`.

**Route.** Receive and respond to `GuiEvent` messages delivered by the framework through `handle_event`. Feature code examines the event, performs any state changes it implies, and returns `True` to consume the event or `False`/`None` to pass it on. Route-phase code should be fast; expensive computation belongs in `on_update` triggered by a state change, not inside the event handler.

**Update.** Execute frame-based logic through `on_update(host, dt_seconds)`. This is where animations progress, timers tick, and per-frame state transitions happen. `dt_seconds` is the elapsed time since the last frame. Keep `on_update` fast — it runs every frame, and any delay here delays the entire application.

**Draw.** Perform custom rendering through `draw(host, screen)`. Use for anything that cannot be expressed through the control tree: raw pygame surface operations, particle systems, custom geometric rendering. Most features that use only standard controls can leave this method as a no-op.

### Message and Logic Coordination

Features communicate with each other without direct coupling through `FeatureMessage` publishing. A feature constructs a `FeatureMessage` with a target name and optional payload; the framework delivers it to any feature registered to receive messages of that name. The sending feature holds no reference to receivers; receivers hold no reference to the sender.

Use `FeatureMessage` for events where a producer signals that something happened and zero or more consumers respond. Use `ObservableValue` (shared through the host or via the logic feature pattern) for state that multiple consumers want to track continuously. The distinction: messages are fire-and-forget events; observables are continuous shared state.

`LogicFeature` is the natural coordination hub for shared application state. A `LogicFeature` computes results, stores them in `ObservableValue` attributes, and exposes those attributes through the host or a reference held by the logic feature. UI features subscribe to the observables in `bind_runtime`. The `LogicFeature` never references UI features directly; the decoupling is complete.

### When to Use Routed Runtime Specs

`RoutedRuntimeSpec` and `RoutedFeatureLifecycleSpec` exist to reduce repetitive boilerplate when a feature needs several framework-level bindings that all share the same lifecycle. Common cases:

- **Multiple action hotkeys for one feature**: Instead of manually registering several `ActionSpec`s and wiring each to cleanup in `shutdown_runtime`, a `RoutedFeatureLifecycleSpec` registers them all and tears them down automatically.
- **Shortcut overlays tied to feature lifecycle**: A shortcut overlay that should appear and disappear with a specific feature is cleanly expressed in a `RoutedFeatureLifecycleSpec` — the overlay is activated when the feature activates and deactivated when it deactivates.
- **Task-panel focus toggles**: A `TaskPanelFocusToggleSpec` in a `RoutedRuntimeSpec` wires a task-panel button to toggle focus into a specific window — all teardown is automatic.
- **Event subscriptions with auto-cleanup**: An `EventSubscriptionSpec` inside a `RoutedFeatureLifecycleSpec` registers a framework-level event subscription that is automatically removed when the feature shuts down.

Use `bind_routed_feature_lifecycle` in `bind_runtime` to activate a `RoutedFeatureLifecycleSpec`, and call `shutdown_routed_feature_lifecycle` in `shutdown_runtime` to deactivate it. This pair replaces what would otherwise be several manual registration and deregistration calls.

---

## Main Systems Reference

[Back to Table of Contents](#table-of-contents)

### 8.1 Application Bootstrap and Host Configuration

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Application bootstrap is the process of turning a declarative application description into a live, running `gui_do` application. It exists to ensure that all wiring — scenes, features, actions, windows, fonts, cursors, telemetry — is established in a single deterministic pass before the event loop starts. Nothing in the bootstrap sequence is deferred or lazy; when `bootstrap_host_application` returns, the application is fully wired and ready.

#### Mental model and lifecycle placement

Think of the host as a plain Python object that bootstrap populates. You fill a `HostApplicationBindingSpec` with high-level declarations; `build_host_application_config` resolves those declarations into a concrete `HostApplicationConfig`; then `bootstrap_host_application(config)` attaches the live runtime to the host object — `host.app`, `host.scene_manager`, and the other runtime attributes are populated and ready.

Bootstrap happens once, at application startup, before the first frame. After bootstrap completes, you call `host.app.run_entrypoint(target_fps=N)` to start the event loop.

#### Primary public APIs

From **Tier 1** (bootstrap, specs, builders):
- `bootstrap_host_application` — executes the config and starts the host
- `build_host_application_config` — builds a `HostApplicationConfig` from a `HostApplicationBindingSpec`
- `HostApplicationConfig` — the concrete config object passed to bootstrap
- `HostApplicationBindingSpec` — high-level declarative app description
- `TelemetryConfig` — optional telemetry/diagnostics configuration
- `SceneBundleBindingSpec` — declares a scene with all its settings in one spec
- `FeatureWindowBundleBindingSpec` — declares a feature + its window binding in one spec
- `ActionBindingSpec`, `CursorBindingSpec`, `FontRoleBindingSpec`, `PaletteBindingSpec` — per-resource binding specs
- `FeatureSpec`, `WindowSpec`, `RuntimeSceneSpec`, `ActionSpec`, `SceneSetupSpec`, `SceneRootSpec`, `AnchoredWindowSpec`, `LogicBindingSpec`, `TaskPanelButtonSpec`, `ActionHotkeySpec`, `ControlKeyBindingSpec`, `ShortcutOverlaySpec`, `TaskPanelFocusToggleSpec`, `RoutedRuntimeSpec`, `RoutedFeatureLifecycleSpec`, `FeatureWindowBundleBindingSpec`, `WindowToggleBindingSpec`, `SceneSetupBindingSpec`, `RuntimeSceneBindingSpec`, `SceneRootBindingSpec`, `CursorBindingSpec`, `FontRoleBindingSpec`, `ActionHotkeySpec`, `StaticAccessibilitySpec`, `CursorSpec`, `EventSubscriptionSpec`, `NotificationSpec`, `TabbedPresenterSpec`, `AccessibilitySequenceSpec`, `TabBuilderSpec`, `SceneTaskPanelSpec`, `SceneReturnButtonSpec` — the full spec vocabulary
- `build_host_application_config`, `build_feature_specs`, `build_feature_window_bundle_specs`, `build_window_toggle_specs`, `build_scene_setup_specs`, `build_runtime_scene_specs`, `build_scene_root_specs`, `build_cursor_specs`, `build_font_role_specs`, `build_scene_nav_actions`, `build_action_specs`, `build_scene_bundle_specs`, `build_static_accessibility_specs`, `build_notification_center` — builder helpers that transform binding specs into config tuples
- `make_window_toggle_spec`, `make_scene_nav_action`, `make_exit_action`, `make_palette_open_action`, `make_static_accessibility_spec` — factory helpers for common spec patterns

From **Tier 2** (app and scene management):
- `GuiApplication` — the live application object; `host.app` after bootstrap
- `create_display` — creates the pygame display surface at the declared size and title
- `SceneTransitionManager`, `SceneTransitionStyle` — manages animated scene transitions
- `apply_scene_setup_specs` — applies `SceneSetupSpec` entries to a running scene

#### Typical usage flow

1. Import feature classes and spec helpers from `gui_do`.
2. Construct a `HostApplicationBindingSpec` with all scene, feature, action, cursor, font, and telemetry declarations.
3. Call `build_host_application_config(spec)` — this resolves all cross-references and produces a `HostApplicationConfig`.
4. Call `bootstrap_host_application(config)` — this wires the full runtime and returns the host.
5. Call `host.app.run_entrypoint(target_fps=120)` to start the event loop.

#### Minimal example

```python
from gui_do import (
    HostApplicationBindingSpec, SceneBundleBindingSpec, SceneTransitionStyle,
    build_host_application_config, bootstrap_host_application,
)
from my_app.main_feature import MainFeature

config = build_host_application_config(
    HostApplicationBindingSpec(
        display_size=(1280, 720),
        window_title="My App",
        fonts={"default": {"file": "assets/fonts/Regular.ttf", "size": 14}},
        initial_scene_name="main",
        scene_bundle_entries=(
            SceneBundleBindingSpec(
                scene_name="main",
                pretty_name="Main",
                transition_style=SceneTransitionStyle.SLIDE_RIGHT,
                transition_duration=0.3,
                bind_escape_to_exit=True,
            ),
        ),
        feature_entries=(("_main", MainFeature),),
    )
)
host = bootstrap_host_application(config)
host.app.run_entrypoint(target_fps=120)
```

#### Advanced pattern

Use `SceneBundleBindingSpec` entries with `include_nav_action=True` and `FeatureWindowBundleBindingSpec` to compose a multi-scene, multi-window application entirely from binding specs. `build_host_application_config` resolves all cross-references (nav actions, window bundles, task panel buttons, accessibility sequences) in one deterministic pass, so no manual wiring is needed even for complex multi-scene apps.

```python
from gui_do import FeatureWindowBundleBindingSpec

feature_window_bundle_entries=(
    FeatureWindowBundleBindingSpec(
        "_tools_feature",
        ToolsFeature,
        "tools_window",
        slot_index=0,
        task_panel_label="Tools",
    ),
),
```

#### Common mistakes

- Declaring a feature with a `scene_name` that does not match any `SceneBundleBindingSpec` — the feature is silently excluded.
- Forgetting `initial_scene_name` in `HostApplicationBindingSpec` — the framework has no scene to start on and raises an error at bootstrap.
- Manually mutating host attributes after bootstrap — post-bootstrap mutation bypasses the spec graph and may produce inconsistent state.
- Using `HostApplicationConfig` directly (manually setting all fields) when `build_host_application_config` + `HostApplicationBindingSpec` would handle the cross-reference resolution automatically.

#### Cross-links

→ 8.2 Feature Lifecycle (feature phases begin after bootstrap completes) | 8.3 Events and Actions (ActionSpec is declared in bootstrap config) | 8.9 Scene and Presentation Models (SceneBundleBindingSpec) | Appendix D.1 (Tier 1 matrix)

---

### 8.2 Feature Lifecycle and Feature Types

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

The Feature is the primary unit of application behavior in `gui_do`. The lifecycle system ensures that every feature progresses through the same sequence of phases in the same order, that all sibling features are ready before reactive wiring begins, and that all resources are released cleanly on scene exit. The system exists to make feature code predictable: if you know which phase you are in, you know exactly what is and is not safe to do.

#### Mental model and lifecycle placement

Think of each Feature as a black box with a defined interface. The framework calls lifecycle methods in a fixed order; the feature never calls them on itself. There is one instance per feature per scene per application lifetime. The phases are: `build` → `bind_runtime` → event loop (`handle_event`, `on_update`, `draw`) → `shutdown_runtime`. After shutdown, the feature should be considered dead.

#### Primary public APIs

From **Tier 1** (feature base classes and managers):
- `Feature` — standard interactive feature; builds controls in the scene tree
- `DirectFeature` — renders directly to the surface; no control tree participation
- `LogicFeature` — logic-only feature; no UI; ideal for shared state and background work
- `RoutedFeature` — extends `Feature` with action routing infrastructure
- `FeatureMessage` — cross-feature communication object; use `.from_payload(sender, target, payload)` to construct
- `FeatureManager` — framework-internal orchestrator; manages feature activation/deactivation
- `ScenePresentationModel` — the scene's runtime data holder; accessible via the host in lifecycle methods
- `SceneSetupSpec` — declares how a scene initializes; consumed by `apply_scene_setup_specs`
- `setup_standard_font_roles` — registers the standard font role set for a new scene

From **Tier 18** (advanced runtime and bootstrapping — routed lifecycle helpers):
Verify names in `gui_do/__init__.py` Tier 18 before using. Routed feature lifecycle helpers (`bind_routed_feature_lifecycle`, `shutdown_routed_feature_lifecycle`, `register_routed_feature_companions`) automate multi-binding teardown.

#### Lifecycle phases in depth

**`build(host)`** — called once during scene construction. Instantiate controls, add them to the scene tree, initialize `ObservableValue` attributes. Invariant: no subscriptions, no cross-feature references, no host-dependent wiring. Sibling features may not yet exist.

**`bind_runtime(host)`** — called after all features in the scene complete `build`. Subscribe to observables, bind controls to data, establish cross-feature references. All siblings are built and available. All subscriptions established here must be disposed in `shutdown_runtime`.

**`handle_event(host, event)`** — called for every routed `GuiEvent`. Return `True` to consume; return `False` or `None` to pass on. Keep fast; avoid expensive computation here.

**`on_update(host, dt_seconds)`** — called every frame. `dt_seconds` is elapsed seconds since last frame. Animations, timers, per-frame transitions. Keep fast; any delay here delays all rendering.

**`draw(host, screen)`** — called every frame after `on_update`. Custom pygame surface operations. Features using only the control tree can leave this as a no-op.

**`shutdown_runtime(host)`** — called when the scene exits. Dispose all subscriptions; cancel any coroutines; release all resources. After this returns, the feature must be considered inactive.

#### `HOST_REQUIREMENTS` protocol

```python
class MyFeature(Feature):
    HOST_REQUIREMENTS = {
        "build": ("scene_controls", "screen_rect"),
        "bind_runtime": ("scene_controls", "action_manager"),
        "shutdown_runtime": (),
    }
```

`HOST_REQUIREMENTS` is a class-level dict mapping lifecycle method names to tuples of required host attribute names. The framework validates these at startup and raises clear errors for any missing binding before the first frame executes. Declare every host attribute you use; omit a key entirely for phases where you have no requirements.

#### Minimal example

```python
from gui_do import Feature, ObservableValue

class CounterFeature(Feature):
    HOST_REQUIREMENTS = {
        "build": ("scene_controls", "screen_rect"),
        "bind_runtime": ("scene_controls",),
        "shutdown_runtime": (),
    }

    def __init__(self):
        super().__init__()
        self._count = ObservableValue(0)
        self._label = None
        self._sub = None

    def build(self, host):
        from gui_do import LabelControl
        self._label = LabelControl(text="0", rect=host.screen_rect.move(20, 20).inflate(-1200, -600))
        host.scene_controls.add(self._label)

    def bind_runtime(self, host):
        self._sub = self._count.subscribe(lambda v: self._label.set_text(str(v)))

    def shutdown_runtime(self, host):
        if self._sub:
            self._sub()
            self._sub = None
```

#### Advanced pattern: logic + presentation split

A `LogicFeature` owns `ObservableValue`s and publishes `FeatureMessage` events. A companion `Feature` subscribes to the observables and drives the control tree. Wire them with `register_routed_feature_companions` (Tier 18) so the framework knows they belong together.

```python
class DataLogicFeature(LogicFeature):
    def __init__(self):
        super().__init__()
        self.result = ObservableValue(None)

    def on_logic_command(self, host, message: FeatureMessage) -> None:
        if message.target == "compute":
            self.result.value = expensive_computation(message.payload)
```

The companion `Feature` subscribes to `logic_feature.result` in `bind_runtime`. Neither feature holds a direct reference to the other — they communicate only through the observable.

#### Common mistakes

- Subscribing to observables in `build` — controls may not be fully initialized; use `bind_runtime`.
- Forgetting `shutdown_runtime` cleanup — subscriptions fire on dead objects after scene exit.
- Mixing draw-heavy rendering into `Feature.draw` for a feature that could use `DirectFeature` — `DirectFeature` is lower overhead when controls are not needed.
- Failing to call `shutdown_routed_feature_lifecycle` in `shutdown_runtime` when `RoutedFeatureLifecycleSpec` was used — routed bindings leak.

#### Cross-links

→ 8.1 Bootstrap (features declared in bootstrap config) | 8.3 Events/Actions (handle_event receives GuiEvents) | 8.4 State/Observables (ObservableValue subscription pattern) | 8.10 Scheduling (CooperativeScheduler driven from on_update)

---

### 8.3 Events, Actions, Input Mapping, and Routing

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

The event system normalizes all raw pygame input to canonical `GuiEvent` instances before any application-level code sees them. The action system maps named commands to input bindings, providing a stable semantic layer above raw key events. Together they ensure that features respond to meaning (a "save" action) rather than mechanism (Ctrl+S key down), making input rebinding, accessibility, and testing straightforward.

#### Mental model and lifecycle placement

Raw pygame event → `GuiEvent` normalization → overlay/focus/toast routing → keyboard manager / action registry → feature `handle_event` dispatch → fallthrough handlers. Features always receive normalized `GuiEvent` objects. Actions fire through the `ActionManager` when their bound input occurs. Both paths respect `propagation_stopped` and `default_prevented` as hard stops.

#### Primary public APIs

From **Tier 4** (events, actions, focus, input):
- `GuiEvent` — canonical event object; all routing is based on this type
- `EventType` — enum of semantic event kinds: `PASS`, `QUIT`, `KEY_DOWN`, `KEY_UP`, `MOUSE_BUTTON_DOWN`, `MOUSE_BUTTON_UP`, `MOUSE_MOTION`, `MOUSE_WHEEL`, `TEXT_INPUT`, `TEXT_EDITING`
- `EventPhase` — routing phase: `CAPTURE`, `TARGET`, `BUBBLE`
- `EventManager` — runtime conversion gateway; `to_gui_event()` converts raw pygame events
- `EventBus` — publish/subscribe bus for application-level events
- `GestureRecognizer` — multi-phase pointer gesture detection
- `EventRecorder`, `EventPlayback`, `RecordedEvent` — deterministic event recording and playback for tests
- `InputSnapshot` — snapshot of input device state at a point in time
- `Signal`, `SignalConnection` — typed observer/emitter for in-process notifications
- `ActionManager` — registers and executes named actions
- `ActionContext`, `ActionMiddleware` — middleware chain for action dispatch
- `ActionDescriptor`, `ActionRegistry` — declares and stores named action definitions
- `InputMap`, `InputBinding` — maps input chords to action IDs
- `KeyChordManager`, `KeyChord`, `ChordStep` — multi-key chord definition and detection
- `FocusManager` — manages logical keyboard focus across controls
- `FocusScope`, `FocusScopeManager` — groups controls into focus scopes
- `WindowFocusManager` — manages focus cycling across windows; candidates sorted by `control_id`
- `FocusRing` — ordered ring of focusable elements
- `ValueChangeCallback`, `ValueChangeReason` — typed change notification helpers

From **Tier 1** (spec types):
- `ActionSpec` — declares a named action with optional hotkey binding
- `ActionHotkeySpec` — declares a key binding for an action
- `ControlKeyBindingSpec` — declares a key binding scoped to a specific control
- `EventSubscriptionSpec` — declares an event subscription with auto-cleanup

#### `GuiEvent` fields and helpers

Fields: `kind`, `type`, `key`, `pos`, `rel`, `raw_pos`, `raw_rel`, `button`, `wheel_x`, `wheel_y`, `mod`, `text`, `control_id`, `group`, `window`, `task_panel`, `task_id`, `error`, `source_event`, `phase`, `propagation_stopped`, `default_prevented`.

Semantic checks: `is_kind()`, `is_key_down()`, `is_key_up()`, `is_mouse_down()`, `is_mouse_up()`, `is_mouse_motion()`, `is_mouse_wheel()`, `is_text_event()`.

Button helpers: `is_left_down()`, `is_left_up()`, `is_right_down()`, `is_right_up()`, `is_middle_down()`, `is_middle_up()`.

Behavior helpers: `clone()`, `with_phase()`, `stop_propagation()`, `prevent_default()`, `wheel_delta()`, `collides()`.

#### Routing contract (from `docs/runtime_operating_contracts.md`)

- All events are normalized to `GuiEvent` before any application routing.
- Window focus candidates are sorted deterministically by `control_id`.
- `propagation_stopped` and `default_prevented` are hard stops — no further routing occurs.
- Scene dispatch always targets the active scene; inactive scene features do not receive events.

#### Typical usage flow

1. Declare `ActionSpec` entries (with `ActionHotkeySpec`) in `HostApplicationBindingSpec.action_entries`.
2. Implement action handlers on the host object or in feature lifecycle methods.
3. In `handle_event`, check `event.type` and `event.key` to respond to non-action events.
4. Use `event.stop_propagation()` or `event.prevent_default()` when consuming events that should not reach other handlers.

#### Minimal example

```python
from gui_do import Feature, EventType

class KeyboardFeature(Feature):
    HOST_REQUIREMENTS = {"handle_event": ()}

    def handle_event(self, host, event):
        if event.type == EventType.KEY_DOWN and event.key == "space":
            self._toggle_state()
            event.stop_propagation()
            return True
        return False
```

With `ActionSpec` in bootstrap config:
```python
ActionSpec(action_id="toggle", label="Toggle", hotkey=ActionHotkeySpec(key="space"), scene_name="main"),
```

#### Advanced pattern: interaction state machine

For multi-phase pointer gestures (press → drag → release), use `InteractionStateMachine` (Tier 30):

```python
from gui_do import InteractionStateMachine, InteractionPhase, InteractionContext, InteractionTransition

# Declare transitions between IDLE, PRESSING, DRAGGING, RELEASED states
# The state machine guards transitions and tracks phase context
```

For deterministic test scenarios, use `EventRecorder` and `EventPlayback` to record a sequence of events and replay them, verifying that the application state reaches the expected outcome.

#### Common mistakes

- Handling raw `pygame.event.get()` events directly in features — they bypass normalization and will not work correctly with the routing system.
- Assuming that key handlers are globally scoped — action bindings are scene-scoped unless declared otherwise.
- Not respecting `propagation_stopped` in custom fallthrough handlers — events that have already been consumed should not be re-handled.
- Subscribing to the same `Signal` or `EventBus` channel without unsubscribing — memory leak and phantom callbacks.

#### Cross-links

→ 8.1 Bootstrap (ActionSpec declared in config) | 8.2 Feature Lifecycle (handle_event phase) | 8.7 Focus/Accessibility (FocusManager and FocusScope) | 8.13 Forms (AsyncFormValidator subscribes to value changes)

---

### 8.4 State and Observables

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Reactive state is the mechanism by which `gui_do` separates the act of changing a value from the act of updating the display. When application logic changes an observable, every subscribed control and feature updates automatically — without the logic code knowing who is watching. This makes UI code smaller, eliminates entire classes of "forgot to refresh" bugs, and makes state changes trivially testable.

#### Mental model and lifecycle placement

Observables are the data bus. Features write to observables in response to events or computation; controls read from observables and update themselves. The framework is not involved in the subscription mechanism — it is pure Python callbacks, no magic. Set up subscriptions in `bind_runtime`; dispose them in `shutdown_runtime`.

#### Primary public APIs

From **Tier 3** (observable primitives, reactive batch, collections, bindings):
- `ObservableValue` — wraps a single value; `.value` to get/set; `.subscribe(callback)` returns a disposable; mutation triggers all subscribers
- `PresentationModel` — base class for objects that expose multiple `ObservableValue` attributes as a coherent presentation unit
- `ComputedValue` — derived observable; auto-recomputes from source observables when they change
- `reactive_batch` — context manager; defers all subscriber notifications until the `with` block exits
- `is_batching` — returns `True` if currently inside a `reactive_batch` context
- `InvalidationTracker` — tracks which observables have changed since the last frame; useful for dirty-region optimization
- `ChangeKind` — enum of collection change types: `ADD`, `REMOVE`, `REPLACE`, `CLEAR`, `MOVE`
- `CollectionChange` — change event for `ObservableList`/`ObservableDict`; carries `kind`, affected index/key, old/new values
- `ObservableList` — observable mutable list; emits `CollectionChange` events on mutation
- `ObservableDict` — observable mutable dict; emits `CollectionChange` events on mutation
- `CollectionViewQuery` — declarative filter/sort specification for a live collection view
- `CollectionView` — live sorted/filtered view over an `ObservableList`
- `Binding`, `BindingGroup` — declarative one-way or two-way property bindings between observables
- `ObservableStream` — push-based stream of values; for event-like data flows where subscription order matters
- `SelectionModel`, `SelectionMode` — manages which item(s) in a collection are selected; emits change events

From **Tier 27** (transactional app state store):
- `AppStateStore` — central single-source-of-truth state store
- `StateSelector` — derives a slice of store state; recomputes when the relevant keys change
- `StateTransaction` — atomic multi-field update; subscribers fire once after the transaction commits

#### Subscription lifecycle

```python
# In bind_runtime:
self._sub = self.my_value.subscribe(lambda v: self.label.set_text(str(v)))

# In shutdown_runtime:
if self._sub:
    self._sub()  # call the disposable to unsubscribe
    self._sub = None
```

`ObservableValue.subscribe` returns a zero-argument callable that unsubscribes when called.

#### Typical usage flow

1. Create `ObservableValue` attributes in `__init__` or `build`.
2. Subscribe to them in `bind_runtime`, storing the returned disposable.
3. Mutate `.value` anywhere — in event handlers, `on_update`, or action callbacks.
4. Dispose subscriptions in `shutdown_runtime`.

#### Minimal example

```python
from gui_do import ObservableValue, reactive_batch

class StatusModel:
    def __init__(self):
        self.score = ObservableValue(0)
        self.level = ObservableValue(1)

    def advance_level(self):
        with reactive_batch():
            self.score.value = 0
            self.level.value += 1  # subscribers fire once after both changes
```

#### Advanced pattern: `AppStateStore` with `StateSelector`

For state shared across many features, use `AppStateStore`:

```python
from gui_do import AppStateStore, StateSelector, StateTransaction

store = AppStateStore({"score": 0, "level": 1, "high_score": 0})

score_selector = StateSelector(store, keys=("score",))
score_selector.subscribe(lambda state: update_score_display(state["score"]))

with StateTransaction(store) as tx:
    tx.set("score", new_score)
    tx.set("high_score", max(new_score, store.get("high_score")))
# subscribers fire once here
```

Use `CollectionView` with `CollectionViewQuery` for sorted/filtered live views of `ObservableList`:

```python
from gui_do import CollectionView, CollectionViewQuery

view = CollectionView(
    source_list,
    CollectionViewQuery(sort_key=lambda item: item.name, filter_fn=lambda item: item.active)
)
```

#### Common mistakes

- Polling `.value` in `on_update` instead of subscribing — wastes CPU every frame and adds one-frame latency.
- Subscribing in `build` instead of `bind_runtime` — controls may not be ready; `build` is not the wiring phase.
- Forgetting to call the disposable in `shutdown_runtime` — subscriptions fire on dead objects after scene exit.
- Passing plain Python `list` or `dict` objects to controls or across features — plain collections are not observable; mutations are invisible to subscribers.

#### Cross-links

→ 8.2 Feature Lifecycle (subscription lifecycle follows feature lifecycle) | 8.5 Controls (controls accept ObservableValue for reactive display) | 8.11 Persistence (AppStateStore state can be persisted) | 8.13 Forms (reactive validation driven by ObservableValue changes)

---

### 8.5 Controls and Control Composition

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Controls are the reusable UI primitives of `gui_do`. A feature builds a tree of controls during its `build` phase; the framework then handles layout, hit-testing, focus routing, and rendering for the entire tree automatically. Controls exist so that features can describe their UI in terms of semantic components (a button, a label, a slider) rather than raw pixel operations.

#### Mental model and lifecycle placement

Controls are children of panels, which are children of scene roots. A Feature owns one root `PanelControl`; everything it creates lives inside that root. Controls never reach across feature boundaries — cross-feature communication uses observables and messages, not control references.

Controls are created in `build`, bound to data in `bind_runtime`, and cleaned up automatically when the scene exits. Do not create controls outside the `build` phase.

#### Primary Controls (Tier 12)

- `PanelControl` — container for other controls; the natural root for a feature's UI
- `LabelControl` — static or dynamically updated text label
- `ButtonControl` — clickable button with `on_click` callback
- `ToggleControl` — on/off toggle with observable state
- `SliderControl` — numeric range selector with drag interaction
- `ScrollbarControl` — horizontal or vertical scroll position control
- `CanvasControl`, `CanvasEventPacket` — raw drawing surface inside the control tree; pointer events carry canvas-local coordinates via `CanvasEventPacket`
- `CanvasViewport` — scrollable/zoomed view wrapping a `CanvasControl`
- `FrameControl` — visual grouping frame with optional title
- `ImageControl` — static image display from a pygame surface or asset
- `ArrowBoxControl` — callout box with a directional arrow pointer
- `ButtonGroupControl` — group of mutually exclusive buttons (radio group)
- `TabControl`, `TabItem` — tabbed panel; each `TabItem` wraps a child control
- `DockWorkspacePanel` — renders a `DockWorkspace` layout within the control tree

#### Extended Controls (Tier 13)

- `TextInputControl` — single-line text entry with cursor, selection, placeholder text
- `TextAreaControl` — multi-line text entry
- `RichLabelControl` — label supporting inline markup for mixed text styles
- `DropdownControl`, `DropdownOption` — single-select dropdown selector
- `ListViewControl`, `ListItem` — scrollable list with item selection
- `OverlayPanelControl` — panel that renders above sibling controls at a given z-order
- `DataGridControl`, `GridColumn`, `GridRow` — tabular data display with column headers
- `TreeControl`, `TreeNode` — hierarchical tree with expand/collapse
- `SplitterControl` — draggable divider between two sibling panels
- `SpinnerControl` — numeric spinner with up/down buttons and keyboard increment
- `RangeSliderControl` — dual-handle range selector
- `ColorPickerControl` — HSL/RGB color selection widget
- `ScrollViewControl` — panel with scrollable content area
- `ProgressBarControl` — linear progress indicator (determinate or indeterminate)
- `AnimatedImageControl` — sprite-sheet animation display
- `ErrorBoundary` — wraps a control subtree; catches rendering/event errors and displays a fallback instead of crashing the frame
- `WindowControl` — floating titled window chrome (draggable, resizable, closeable)
- `TaskPanelControl` — docked task panel chrome with button strip
- `WindowPresenter` — base class for window-level UI construction; subclass to encapsulate window layout and hand it to a Feature
- `MenuBarControl`, `MenuEntry` — application-level horizontal menu bar
- `SceneMenuStripControl` — scene-scoped horizontal action strip
- `NotificationPanelControl` — persistent notification display panel
- `PropertyInspectorPanel` — generates an editable property form from a `PropertyInspectorModel`
- `ToolbarControl`, `ToolbarItem` — horizontal toolbar with icon/label buttons
- `StatusBarControl`, `StatusSlot` — bottom-of-window status bar with named slot regions
- `ExpanderControl` — collapsible section with a toggle header
- `DatePickerControl` — calendar-based date selection
- `TimePickerControl` — time-of-day selection widget
- `BreadcrumbControl`, `BreadcrumbItem` — navigational breadcrumb trail
- `SplitButtonControl`, `SplitButtonOption` — primary button with attached dropdown of options
- `ChipInputControl` — tag/chip entry with inline chip display and removal

#### Typical usage flow

1. In `build`, create a root `PanelControl` and register it with the scene.
2. Create child controls and add them to the root using `.add(child)`.
3. In `bind_runtime`, subscribe to observables and wire them to control update methods.
4. In `shutdown_runtime`, dispose subscriptions (controls clean themselves up automatically).

#### Minimal example

```python
from gui_do import PanelControl, LabelControl, ButtonControl, Feature
import pygame

class DemoFeature(Feature):
    HOST_REQUIREMENTS = {"build": ("scene_controls", "screen_rect")}

    def build(self, host):
        root = PanelControl("root", host.screen_rect)
        label = LabelControl("status", pygame.Rect(16, 16, 300, 28), "Hello")
        btn = ButtonControl("go", pygame.Rect(16, 52, 100, 32), "Go", on_click=self._on_go)
        root.add(label)
        root.add(btn)
        host.scene_controls.add(root)
        self._label = label

    def _on_go(self):
        self._label.set_text("Clicked!")
```

#### Advanced pattern: WindowPresenter

Subclass `WindowPresenter` to encapsulate window construction, keeping the Feature focused on lifecycle:

```python
from gui_do import WindowPresenter, WindowControl, LabelControl
import pygame

class ToolWindowPresenter(WindowPresenter):
    def build(self, host):
        win = WindowControl("tool_win", pygame.Rect(100, 100, 400, 300), title="Tools")
        win.add(LabelControl("hint", pygame.Rect(8, 8, 200, 24), "Select a tool"))
        self.window = win
        host.scene_controls.add(win)
```

Combine with `TabbedPresenterSpec` and `TabBuilderSpec` for multi-tab windows where each tab is a separate presenter.

#### Common mistakes

- Holding direct references to controls owned by sibling features — use observables and messages instead.
- Using control state (e.g., a button's label text) as the source of truth — observable state should drive controls, not the reverse.
- Creating controls in `on_update` or event handlers — controls must be created in `build`.
- Not using `ErrorBoundary` around complex custom-drawn subtrees — unhandled rendering exceptions crash the entire frame.

#### Cross-links

→ 8.2 Feature Lifecycle (build and bind_runtime phases) | 8.6 Layout (spatial arrangement of controls) | 8.7 Focus/Accessibility (focus ring and role annotation) | 8.9 Window and Task-Panel Presentation

---

### 8.6 Layout Systems

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Layout engines manage spatial constraints, responsive behavior, and composition of controls so that features do not hardcode pixel positions that break on resize or different display configurations. `gui_do` provides a family of layout engines for different spatial problems; features choose the simplest engine that fits their region.

#### Mental model and lifecycle placement

Layout runs as a pass before each draw. Spatial declarations (flex items, grid tracks, constraints) are set up in `build`; the layout manager resolves them each frame. Do not hardcode pixel positions when a layout engine can compute them — hardcoded positions require manual recalculation on every resize.

#### Primary public APIs

From **Tier 8** (layout and spatial):
- `LayoutAxis` — horizontal or vertical axis enum
- `LayoutManager` — central layout coordinator; drives layout passes for the control tree
- `WindowTilingManager` — manages desktop-style tiled window arrangements
- `ConstraintLayout`, `AnchorConstraint` — anchor-based constraint layout; declare relationships between control edges
- `DockPane`, `DockTabs`, `DockSplit`, `DockWorkspace` — complex multi-pane workspace with draggable splits and tabbed panes
- `FlexLayout`, `FlexItem`, `FlexDirection`, `FlexAlign`, `FlexJustify` — row/column flex with grow/shrink ratios and alignment
- `GridLayout`, `GridTrack`, `GridPlacement` — fixed track grid with column/row spanning
- `CellCaretLayout`, `CellCaretState` — caret-based navigation within a cell grid
- `LayoutAnimator` — animates layout transitions when constraints change
- `LayoutPass`, `MeasureContext`, `ArrangeContext`, `LayoutRoot` — low-level layout pass infrastructure for custom layout engines
- `ResponsiveLayout`, `Breakpoint` — policy selection by width breakpoint; switches layout family at declared breakpoints
- `SnapGrid`, `AlignmentGuide`, `SnapComposer`, `SnapTarget` — snap-to-grid and alignment guide system for drag-placed controls
- `FlowLayout`, `FlowItem` — wrapping item flow (left-to-right with line breaks); best for tags and chips
- `Viewport` — scrollable/scalable view window over a larger virtual space

From **Tier 28** (adaptive constraint layout v2):
- `ConstraintAttr` — constraint attribute (left, right, top, bottom, width, height, center_x, center_y)
- `LayoutConstraint` — declarative relationship between two controls' attributes
- `ConstraintSet` — collection of `LayoutConstraint` objects for a layout region
- `ConstraintLayoutEngine` — resolves `ConstraintSet` at layout time; priority-based conflict resolution
- `AdaptivePolicy` — breakpoint-aware constraint switching policy
- `resolve_adaptive_policy` — selects the appropriate `ConstraintSet` for the current viewport

From **Tier 29** (virtualization core):
- `MeasureMode`, `MeasurePolicy` — item measure strategy for virtualized lists/grids
- `VirtualizedWindow` — the sliding viewport into the virtual item space
- `RecyclePool` — pooled item container for recycling rendered items by type key
- `VirtualizationCore` — main engine for list/tree/grid windowing with recycle pools and identity tracking

#### Family selection guide

| Scenario | Engine |
|---|---|
| Toolbar or button strip | `FlexLayout` with `FlexDirection.ROW` |
| Multi-column form | `GridLayout` |
| Tag/chip display | `FlowLayout` |
| Dialog with anchored elements | `ConstraintLayout` or `ConstraintLayoutEngine` |
| Responsive panel (narrow/wide) | `AdaptivePolicy` + `resolve_adaptive_policy` |
| Desktop-style multi-pane app | `DockWorkspace` |
| Drag-placed controls | `SnapGrid` + `SnapComposer` |
| Large list/tree/grid | `VirtualizationCore` with `RecyclePool` |
| Animating between layouts | `LayoutAnimator` |

#### Typical usage flow: FlexLayout

```python
from gui_do import FlexLayout, FlexItem, FlexDirection

layout = FlexLayout(direction=FlexDirection.ROW, gap=8)
layout.add(FlexItem(control=sidebar, grow=0, basis=200))
layout.add(FlexItem(control=content, grow=1))
# Register layout with LayoutManager in build
host.layout_manager.register(root_panel, layout)
```

#### Advanced pattern: adaptive constraint layout

```python
from gui_do import ConstraintLayoutEngine, ConstraintSet, LayoutConstraint, ConstraintAttr, AdaptivePolicy, resolve_adaptive_policy

narrow = ConstraintSet([
    LayoutConstraint(sidebar, ConstraintAttr.WIDTH, constant=0),  # hide sidebar
    LayoutConstraint(content, ConstraintAttr.LEFT, constant=0),
])
wide = ConstraintSet([
    LayoutConstraint(sidebar, ConstraintAttr.WIDTH, constant=220),
    LayoutConstraint(content, ConstraintAttr.LEFT, sidebar, ConstraintAttr.RIGHT, constant=8),
])
policy = AdaptivePolicy(breakpoints={640: narrow, 1024: wide})
# In on_update or layout pass:
active = resolve_adaptive_policy(policy, viewport_width)
engine.apply(active)
```

#### Common mistakes

- Mixing conflicting layout systems in one container without clear ownership — pick one engine per container.
- Hardcoding pixel dimensions where `FlexItem(grow=1)` or breakpoint policies are needed.
- Calling layout APIs before controls are added to the tree — layout needs the child set to be complete.
- Using `VirtualizationCore` with identity-less items — always provide stable identity keys for correct recycle pool behavior.

#### Cross-links

→ 8.5 Controls (controls are the nodes layout operates on) | 8.7 Focus (layout affects focus ring order) | 8.9 Window and Task-Panel (window layout uses ConstraintLayout)

---

### 8.7 Focus and Accessibility

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Focus management ensures that only one control receives keyboard events at a time and that keyboard navigation (Tab, arrow keys) moves focus in a predictable order. Accessibility semantics expose a machine-readable role tree for assistive technology, test automation, and keyboard-first workflows. Both systems exist to make `gui_do` applications usable without a mouse and comprehensible to tools that inspect UI structure.

#### Mental model and lifecycle placement

`FocusManager` owns the currently focused control. `FocusScopeManager` groups controls into scopes so focus can be locked to a subtree (e.g., inside an open dialog). `WindowFocusManager` coordinates per-window focus cycling, producing a deterministic candidate order sorted by `control_id`. Accessibility is a parallel tree of `AccessibilityNode` objects that mirrors the semantic structure of the control tree.

#### Primary public APIs

From **Tier 4** (focus management):
- `FocusManager` — owns logical keyboard focus; `request_focus(control)`, `release_focus()`, `focused_control` property
- `FocusScope`, `FocusScopeManager` — group controls into scopes; lock focus to a scope (modal dialog pattern)
- `WindowFocusManager` — manages focus cycling across windows; window candidates sorted by `control_id`
- `FocusRing` — ordered ring of focusable elements; `next()`, `prev()`, `set_focus(index)`, wraps around

From **Tier 21** (accessibility):
- `AccessibilityRole` — enum of semantic roles: `BUTTON`, `LABEL`, `TEXT_INPUT`, `CHECKBOX`, `SLIDER`, `LIST`, `LIST_ITEM`, `TREE`, `TREE_ITEM`, `PANEL`, `WINDOW`, `MENU`, `MENU_ITEM`, `TAB`, `TAB_PANEL`, `TOOLBAR`, `STATUS_BAR`, `DIALOG`, `ALERT`, `GRID`, `GRID_CELL`, `REGION`, `NONE`, and others
- `LivePoliteness` — politeness level for live-region announcements: `OFF`, `POLITE`, `ASSERTIVE`
- `AccessibilityNode` — semantic node: `role`, `name`, `description`, `live_politeness`, `children`, `is_hidden`
- `AccessibilityTree` — the root tree of `AccessibilityNode` objects for the scene
- `AccessibilityAnnouncement` — event object for screen-reader-style notifications
- `AccessibilityBus` — delivers `AccessibilityAnnouncement` events to registered listeners

From **Tier 1** (spec integration):
- `StaticAccessibilitySpec` — declares a static accessibility node in the spec tree
- `AccessibilitySequenceSpec` — declares a sequential focus order for a scene region
- `TaskPanelFocusToggleSpec` — wires a task-panel button to toggle focus into a specific window; handles focus-exclusion automatically when the window is hidden

#### Focus lifecycle

Controls join the focus ring in `build` when they are added to the scene tree. Hidden or disabled controls must be excluded from the ring — a control in the ring that is invisible will stall focus cycling. `TaskPanelFocusToggleSpec` manages this automatically for task-panel-managed windows: when a window is hidden via the task panel, its controls are excluded from the focus ring; when shown, they are re-included.

`FocusScope` is the correct mechanism for modal dialogs: create a scope, add the dialog's controls to it, then call `FocusScopeManager.lock(scope)` to trap focus inside the dialog until dismissed.

#### Typical usage flow

1. Declare `StaticAccessibilitySpec` entries in `HostApplicationBindingSpec` for scene-level static nodes.
2. For custom controls (especially `CanvasControl` widgets), add `AccessibilityNode` to `AccessibilityTree` in `build`.
3. Use `TaskPanelFocusToggleSpec` in `RoutedRuntimeSpec` for windows that need automatic focus-exclusion.
4. Use `AccessibilityBus.announce()` for live-region updates (e.g., announcing a save completion).

#### Minimal example

```python
from gui_do import AccessibilityTree, AccessibilityNode, AccessibilityRole

# In a feature's build method:
tree = host.accessibility_tree  # provided by framework
node = AccessibilityNode(
    role=AccessibilityRole.BUTTON,
    name="Submit",
    description="Submit the current form",
)
tree.root.add_child(node)
```

#### Advanced pattern: modal focus lock

```python
from gui_do import FocusScope, FocusScopeManager

# In build:
scope = FocusScope("dialog_scope")
scope.add(ok_button)
scope.add(cancel_button)

# When dialog opens:
host.focus_scope_manager.lock(scope)

# When dialog closes:
host.focus_scope_manager.unlock(scope)
```

Use `AccessibilitySequenceSpec` for scene-level sequential navigation order that overrides the default tab order.

#### Common mistakes

- Forgetting to exclude hidden window controls from the focus ring — Tab cycling stalls on invisible controls.
- Omitting semantic roles on custom `CanvasControl` widgets — they become invisible to accessibility tools.
- Building `AccessibilityNode` objects before `AccessibilityTree` is initialized (in pre-`build` code) — nodes attached too early are discarded on scene init.
- Using `FocusScope` without unlocking it on dialog dismissal — focus remains trapped after the dialog is gone.

#### Cross-links

→ 8.3 Events (keyboard events routed through FocusManager) | 8.5 Controls (controls register with the focus ring) | 8.8 Overlays (modal dialogs use FocusScope lock) | 8.13 Forms (form field focus sequencing)

---

### 8.8 Overlays, Dialogs, Notifications, and Command Surfaces

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Transient and modal surfaces — dialogs, toasts, context menus, command palettes, tooltips, shortcut help — need their own routing layer so they do not destabilize the main control event flow. `gui_do` provides a family of overlay managers, each handling a distinct surface kind with a defined dismissal contract. The overlay layer processes events before the main control tree, so active overlays intercept input correctly without requiring changes to feature event handlers.

#### Mental model and lifecycle placement

Overlays sit above the main control tree in the rendering and event order. The `OverlayManager` maintains the active overlay stack. Each specialized manager (`DialogManager`, `ToastManager`, `ContextMenuManager`, etc.) handles one surface type with the correct lifecycle and dismissal behavior. Overlays are created in response to user actions or feature state changes; they are not declared in `build`.

#### Primary public APIs

From **Tier 9** (overlay managers):
- `OverlayManager`, `OverlayHandle` — base overlay stack manager; `OverlayHandle` is the reference to an active overlay
- `Alignment`, `PlacementResult`, `PopupPlacement`, `Side`, `compute_popup_rect` — compute a popup rect that avoids screen-edge clipping given an anchor rect, preferred side, and alignment
- `DialogManager`, `DialogHandle` — modal and non-modal dialogs; `DialogHandle.on_dismiss` callback
- `ToastManager`, `ToastHandle`, `ToastSeverity` — transient toast notifications with severity levels (`INFO`, `SUCCESS`, `WARNING`, `ERROR`)
- `ContextMenuManager`, `ContextMenuItem`, `ContextMenuHandle` — right-click context menu with item list
- `CommandPaletteManager`, `CommandEntry`, `CommandPaletteHandle` — searchable command palette populated from the action registry or custom entries
- `TooltipManager`, `TooltipHandle` — hover-dwell tooltip; shown after configurable dwell time, dismissed on pointer leave
- `MenuBarManager` — application-level menu bar manager; coordinates with `MenuBarControl`
- `FileDialogManager`, `FileDialogOptions`, `FileDialogHandle` — async file open/save dialog
- `NotificationCenter`, `NotificationRecord` — persistent notification log (distinct from transient toasts)
- `ResizeManager` — manages draggable resize handles on `WindowControl` instances
- `CursorManager`, `CursorHandle`, `CursorShape` — manages the active cursor shape; overlays can temporarily set a cursor while active
- `DragDropManager`, `DragPayload` — manages drag-and-drop; source initiates with a `DragPayload`; manager routes drag-enter/leave/drop events to registered targets
- `ClipboardManager` — cross-control clipboard operations (copy, cut, paste)
- `TransferData`, `TransferManager` — structured data transfer between controls and features
- `ShortcutHelpOverlay`, `ShortcutSection`, `ShortcutEntry` — full or partial overlay displaying the action registry's shortcut list, with manual sections and section filtering

From **Tier 1** (spec integration):
- `ShortcutOverlaySpec` — declares a shortcut help overlay with toggle action, key, manual lines, and section config
- `NotificationSpec` — declares a notification center spec for the bootstrap config

#### Dismissal contracts

Each overlay type has a defined dismissal contract:

| Surface | Dismissal |
|---|---|
| Toast | Auto-expires after timeout; click within bounds is consumed (no click-through); `on_click` for intentional interaction |
| Dialog (modal) | Only Escape or explicit dismiss button; no click-outside by default |
| Dialog (non-modal) | Dismiss on outside click, Escape, or explicit close |
| Context menu | Outside click or Escape |
| Command palette | Escape or item selection |
| Tooltip | Pointer leave (dismissed immediately) |
| File dialog | Confirm or Cancel button |
| Shortcut help | Toggle action key (same key that opened it) |

#### Typical usage flow

**Toast:**
```python
host.toasts.show("File saved successfully", severity=ToastSeverity.SUCCESS)
```

**Dialog:**
```python
handle = host.dialogs.show(my_dialog_panel, modal=True)
handle.on_dismiss = lambda: self._handle_close()
```

**Context menu:**
```python
items = [
    ContextMenuItem("Open", on_click=self._open),
    ContextMenuItem("Delete", on_click=self._delete),
]
host.context_menus.show(items, anchor_rect=event_rect)
```

**Shortcut overlay (via spec):**
```python
# In HostApplicationBindingSpec, inside a RoutedRuntimeSpec:
ShortcutOverlaySpec(
    toggle_action_name="toggle_shortcuts",
    toggle_key="f1",
    manual_shortcut_lines=[("F1", "Show/hide shortcuts")],
)
```

#### Advanced pattern: command palette grouped auto-populate + callable custom entries

```python
from gui_do import CommandEntry, HostApplicationBindingSpec, PaletteBindingSpec

def palette_custom_entries(app):
    # User-defined callable returning CommandEntry values.
    return (
        CommandEntry(
            entry_id="custom:retile",
            title="Retile Windows",
            action=lambda: app.tile_windows(),
            category="Custom",
        ),
    )

HostApplicationBindingSpec(
    ...,
    palette_spec=PaletteBindingSpec(
        enable_builtin_entries=True,
        include_scene_entries=True,      # optional built-in Scene group
        include_window_entries=True,     # optional built-in Window group
        group_order=("windows", "custom", "scenes"),
        # group_order controls whether Scene/Window groups appear before,
        # after, or between custom entries.
        custom_entries_provider=palette_custom_entries,
        connect_window_presentation=True,
    ),
)
```

When `connect_window_presentation=True`, built-in **Window** entries are ordered
by `FeatureWindowBinding.task_panel_slot_index` (same order as task panel window
toggles), not by control id.

#### Common mistakes

- Expecting toast clicks to pass through to controls underneath — clicks within a toast's bounds are consumed.
- Showing a modal dialog without a dismissal path (no Escape binding, no close button) — users cannot close it.
- Not checking `OverlayHandle` validity before updating a dismissed overlay — the handle may refer to a surface that is already gone.
- Using `ShortcutHelpOverlay` without a `ShortcutOverlaySpec` — the overlay spec is required for action-registry integration and keyboard toggle.

#### Cross-links

→ 8.3 Events (overlay layer processes events before feature routing) | 8.7 Focus (modal dialogs use FocusScope lock) | 8.9 Scene/Window Presentation (window chrome and task panel) | 8.10 Scheduling (tooltip dwell timer)

---

### 8.9 Scene, Window, and Task-Panel Presentation Models

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Scenes define broad interaction contexts — the "modes" of the application, such as a main desktop, a control showcase, or a settings screen. Within a scene, windows are floating or docked UI surfaces that can be individually shown or hidden. The task panel is a persistent chrome element that houses toggle buttons for windows and scene navigation. This system coordinates what is visible, what has focus, and which actions are available at any given moment.

#### Mental model and lifecycle placement

Think of scenes as application-level modes. Each scene has its own feature set, windows, task panel, and scene menu strip. Transitions between scenes are animated. Within a scene, windows are managed by `ScenePresentationModel`; their visibility, focus integration, and task panel buttons are all coordinated through the presentation layer. Features own windows; they do not manage scene transitions directly.

#### Primary public APIs

From **Tier 1** (spec types):
- `ScenePresentationModel` — tracks which windows are registered in a scene and their visibility state; provides `handle_window_toggle` for scene menu strip integration
- `WindowSpec`, `AnchoredWindowSpec` — declare window geometry, anchoring strategy, and chrome properties
- `SceneTaskPanelSpec`, `TaskPanelButtonSpec`, `TaskPanelFocusToggleSpec` — declare the scene's task panel and per-window toggle buttons
- `FeatureWindowBundleBindingSpec` — wires feature + window + task panel button in a single spec; the recommended way to add a feature window
- `WindowToggleBindingSpec`, `SceneSetupBindingSpec`, `RuntimeSceneBindingSpec`, `SceneRootBindingSpec` — lower-level binding specs for advanced wiring
- `TabbedPresenterSpec`, `TabBuilderSpec` — declaratively specify tabbed window content
- `SceneReturnButtonSpec` — adds a return/back button to the scene menu strip

From **Tier 18** (advanced runtime helpers):
- `set_window_visible_state` — programmatically show or hide a window and update the focus ring
- `toggle_window_visibility` — toggle a window's visibility, updating task panel button state
- `create_anchored_feature_window` — creates and registers an anchored window for a feature
- `create_feature_presented_window` — creates a window from a `WindowPresenter` subclass
- `add_window_scene_menu_strip` — adds a window toggle entry to the scene menu strip
- `ensure_scene_task_panel` — ensures a task panel control exists in the scene, creating one if needed
- `ActiveTabUpdateRouter` — efficiently routes updates only to the currently active tab's presenter
- `TabLayoutContext` — provides layout context for tabbed window content
- `create_presented_anchored_window`, `create_presented_window_from_spec` — presenter-based window creation helpers
- `setup_feature_presenter_tabs`, `setup_feature_presenter_tabs_from_window_content` — wire tabbed content into a presenter window
- `bind_task_panel_focus_toggle` — binds a task panel focus toggle for a window
- `add_task_panel_button`, `add_task_panel_buttons` — programmatically add buttons to the task panel
- `add_scene_return_button` — adds a return/back button to the scene's menu strip
- `sorted_window_bindings`, `collect_window_toggle_controls`, `apply_window_toggle_accessibility`, `add_window_toggle_task_panel_controls`, `register_window_toggle_tooltips` — bulk window-toggle wiring helpers
- `add_window_control`, `add_window_label`, `add_window_button`, `add_window_button_row` — convenience helpers for building window interiors

#### Typical usage flow

1. Declare a `SceneBundleBindingSpec` in `HostApplicationBindingSpec` for the scene. Set `include_scene_root`, `include_nav_action`, and other flags as needed.
2. Use `FeatureWindowBundleBindingSpec` to declare features that have windows — this wires the feature, its `WindowPresenter`, its `AnchoredWindowSpec`, and its task panel toggle button in one declaration.
3. Implement `WindowPresenter` subclasses to build each window's interior.
4. Use `TaskPanelFocusToggleSpec` inside `RoutedRuntimeSpec` for automatic focus ring management when windows are shown/hidden.

#### Minimal example

```python
from gui_do import FeatureWindowBundleBindingSpec

feature_window_bundle_entries=(
    FeatureWindowBundleBindingSpec(
        "_tools",
        ToolsFeature,
        "tools_window",
        slot_index=0,
        task_panel_label="Tools",
    ),
),
```

This single spec wires `ToolsFeature`, creates its window, adds its task panel toggle button in slot 0, and configures focus cycling correctly.

#### Advanced pattern: tabbed window with `ActiveTabUpdateRouter`

```python
from gui_do import TabbedPresenterSpec, TabBuilderSpec, ActiveTabUpdateRouter

# In HostApplicationBindingSpec:
TabbedPresenterSpec(
    window_id="analysis",
    tabs=(
        TabBuilderSpec(tab_id="summary", label="Summary", builder=SummaryPresenter),
        TabBuilderSpec(tab_id="details", label="Details", builder=DetailsPresenter),
    ),
),

# In bind_runtime, after creating the tabbed window:
router = ActiveTabUpdateRouter(tab_control, presenters)
self._tab_router = router
```

`ActiveTabUpdateRouter` ensures that only the active tab's presenter receives data updates, avoiding unnecessary computation for hidden tabs.

#### Common mistakes

- Mismatching scene name in `FeatureSpec` vs `SceneBundleBindingSpec` — the feature is silently excluded from the scene.
- Not using `TaskPanelFocusToggleSpec` for windows that can be hidden — Tab cycling stalls on invisible window controls.
- Creating window controls in `bind_runtime` instead of `build` — window controls must exist when sibling features call `bind_runtime`.
- Forgetting to synchronize task panel button state when manually changing window visibility — use `set_window_visible_state` instead of directly hiding the control.

#### Cross-links

→ 8.1 Bootstrap (SceneBundleBindingSpec, FeatureWindowBundleBindingSpec) | 8.2 Feature Lifecycle (build and bind_runtime) | 8.5 Controls (WindowControl, TaskPanelControl, WindowPresenter) | 8.7 Focus (TaskPanelFocusToggleSpec) | 8.8 Overlays (overlay layer sits above window layer)

---
Scenes define broad interaction contexts — the "modes" of the application, such as a main desktop, a control showcase, or a settings screen. Within a scene, windows are floating or docked UI surfaces that can be individually shown or hidden.  `gui_do` provides three built-in optional facilities that a scene may declare: a **task panel**, a **scene menu strip**, and a **command palette**.  Every facility is per-scene and optional — a scene that does not declare it simply does not have it.  This system coordinates what is visible, what has focus, and which commands are reachable at any given moment.
### 8.10 Scheduling, Timing, Animation, and Transitions

[Back to Table of Contents](#table-of-contents)
Think of scenes as application-level modes.  Each scene has its own feature set, windows, and optionally a task panel, scene menu strip, and command palette.  Transitions between scenes are animated.  Within a scene, windows are managed by `ScenePresentationModel`; their visibility, focus integration, and task panel buttons are all coordinated through the presentation layer.  Features own windows; they do not manage scene transitions directly.
#### What it is and why it exists
All three facilities are **built in to gui_do** and available to every scene — they are enabled or disabled purely by what specs a scene declares.  The spec-driven approach is the expected and preferred way for user code to interact with these facilities.
Time-based work — animations, timed callbacks, multi-step background workflows — must execute within per-frame budgets. If time-based work exceeds its budget, rendering stalls and the UI freezes. `gui_do` provides a layered scheduling system: from simple timers and debouncing at one end, through tweens and animation state machines in the middle, to cooperative coroutine scheduling for multi-frame workflows at the other end.
#### The three optional per-scene facilities
- **Floor**: 0.5 ms (minimum dispatch time even on very fast frames)
##### Task panel
- `CoroutineHandle` — reference to a running coroutine; `.cancel()` to stop it
The task panel is a docked strip of buttons at the bottom (or top) of the scene.  It contains **no default items** — every button and group must be declared explicitly.  Declare a task panel with `SceneTaskPanelSpec` passed to `ensure_scene_task_panel`.  Then add whatever buttons your scene needs.
- `Sleep` — yield primitive: sleep for a wall-clock duration in seconds
**Window toggle group** — if the scene has windows, you may optionally declare a `TaskPanelWindowToggleGroupSpec(start_index=N)`.  This tells the framework to automatically create one toggle button per registered window, starting at slot *N* of the task panel's linear layout.  Individual windows declare their own absolute `slot_index` in their `FeatureWindowBundleBindingSpec`; the group spec just marks where the toggle block begins.  Other controls (exit buttons, navigation buttons, etc.) can freely coexist at slot indices before or after the toggle group — and even within the group's slot range — without conflict.  Omitting `TaskPanelWindowToggleGroupSpec` means no automatic window toggles appear in the task panel for this scene.

Use `add_task_panel_window_toggle_group` instead of `add_window_toggle_task_panel_controls` when you have a `TaskPanelWindowToggleGroupSpec` — it is the spec-driven form of the same operation.

##### Scene menu strip

The scene menu strip (`SceneMenuStripSpec`) is a menu bar anchored to the top of the scene root.  It contains **no default menu entries**.  Two optional sections may be included:

- **Scene section** (`scenes_shown=True`) — lists all registered scenes so the user can navigate between them
- **Windows section** (`windows_shown=True`) — lists all windows registered in the current scene; each entry shows the window's current visibility state as a check mark and toggles it when selected

Both sections are optional independently.  A scene menu with `scenes_shown=False, windows_shown=False` is effectively empty.  The Windows section coordinates automatically with the task panel toggle buttons — when a toggle button changes a window's visible state, the menu reflects the change, and vice versa.  This coordination is built in to `ScenePresentationModel.handle_window_toggle` and requires no additional code.

##### Command palette

The command palette (`SceneCommandPaletteSpec`) is a keyboard-driven command entry overlay.  Each scene declares its own activation key:

```python
# In the scene's RoutedRuntimeSpec:
MAIN_RUNTIME_SPEC = RoutedRuntimeSpec(
    scene_name="main",
    command_palette=SceneCommandPaletteSpec(
        key=pygame.K_F5,
        scene_name="main",
    ),
    ...
)
```

`setup_routed_runtime` automatically registers the activation key as a **global key** — a key that is tested at the very start of event routing, before overlay focus, task-panel focus, widget focus, active-window handlers, and screen-event handlers.  This guarantees the palette is always reachable regardless of which window or control has keyboard input.  The routing order (from first-tested to last) is:

1. Overlay intercept (`gui_application.py` — ESC to dismiss dialogs, etc.)
2. **Global keys** — command palette and any other per-scene global bindings
3. Task-panel focus branch
4. Accessibility keys (Tab, Shift-Tab, arrow traversal)
5. Focused widget
6. Active window
7. Screen-event handler
8. Action manager normal bindings

The command palette key is **per-scene and user-definable**: each scene declares its own `SceneCommandPaletteSpec` with any key, and scenes can use the same or different keys.  Omitting `SceneCommandPaletteSpec` from a scene's `RoutedRuntimeSpec` means that scene has no command palette key.

User code may also call `setup_scene_command_palette_key(app, palette_manager, spec)` directly if finer control is needed.

#### Primary public APIs

From **Tier 1** (spec types):
- `ScenePresentationModel` — tracks which windows are registered in a scene and their visibility state; provides `handle_window_toggle` for scene menu strip integration
- `WindowSpec`, `AnchoredWindowSpec` — declare window geometry, anchoring strategy, and chrome properties
- `SceneTaskPanelSpec`, `TaskPanelButtonSpec`, `TaskPanelFocusToggleSpec` — declare the scene's task panel and per-window toggle buttons
- `TaskPanelWindowToggleGroupSpec` — declares where the automatic window-toggle button group begins in the task panel; optional, per-scene
- `SceneCommandPaletteSpec` — declares the per-scene command palette activation key; optional, global key routing
- `FeatureWindowBundleBindingSpec` — wires feature + window + task panel button in a single spec; the recommended way to add a feature window
- `WindowToggleBindingSpec`, `SceneSetupBindingSpec`, `RuntimeSceneBindingSpec`, `SceneRootBindingSpec` — lower-level binding specs for advanced wiring
- `TabbedPresenterSpec`, `TabBuilderSpec` — declaratively specify tabbed window content
- `SceneReturnButtonSpec` — adds a return/back button to the scene menu strip
- `SceneMenuStripSpec` — declares the scene menu strip (optionally with Scene and Window sections)

From **Tier 18** (advanced runtime helpers):
- `set_window_visible_state` — programmatically show or hide a window and update the focus ring
- `toggle_window_visibility` — toggle a window's visibility, updating task panel button state
- `create_anchored_feature_window` — creates and registers an anchored window for a feature
- `create_feature_presented_window` — creates a window from a `WindowPresenter` subclass
- `add_window_scene_menu_strip` — adds a window toggle entry to the scene menu strip
- `ensure_scene_task_panel` — ensures a task panel control exists in the scene, creating one if needed
- `add_task_panel_window_toggle_group` — spec-driven helper; creates window toggle controls from `TaskPanelWindowToggleGroupSpec`
- `setup_scene_command_palette_key` — registers a global per-scene command palette activation key
- `bind_global_key` — registers an `ActionManager` global key (tested first in routing, before focus and active-window handlers)
- `ActiveTabUpdateRouter` — efficiently routes updates only to the currently active tab's presenter
- `TabLayoutContext` — provides layout context for tabbed window content
- `create_presented_anchored_window`, `create_presented_window_from_spec` — presenter-based window creation helpers
- `setup_feature_presenter_tabs`, `setup_feature_presenter_tabs_from_window_content` — wire tabbed content into a presenter window
- `bind_task_panel_focus_toggle` — binds a task panel focus toggle for a window
- `add_task_panel_button`, `add_task_panel_buttons` — programmatically add buttons to the task panel
- `add_scene_return_button` — adds a return/back button to the scene's menu strip
- `sorted_window_bindings`, `collect_window_toggle_controls`, `apply_window_toggle_accessibility`, `add_window_toggle_task_panel_controls`, `register_window_toggle_tooltips` — bulk window-toggle wiring helpers
- `add_window_control`, `add_window_label`, `add_window_button`, `add_window_button_row` — convenience helpers for building window interiors

#### Typical usage flow

1. Declare a `SceneBundleBindingSpec` in `HostApplicationBindingSpec` for the scene. Set `include_scene_root`, `include_nav_action`, and other flags as needed.
2. Use `FeatureWindowBundleBindingSpec` to declare features that have windows — this wires the feature, its `WindowPresenter`, its `AnchoredWindowSpec`, and its task panel toggle button in one declaration.
3. Implement `WindowPresenter` subclasses to build each window's interior.
4. In the scene's `RoutedRuntimeSpec`, add `command_palette=SceneCommandPaletteSpec(key=..., scene_name=...)` to enable the command palette activation key for that scene.
5. In the scene's `build` method, call `ensure_scene_task_panel` with a `SceneTaskPanelSpec`, add navigation/exit buttons with `add_task_panel_buttons`, and call `add_task_panel_window_toggle_group` with a `TaskPanelWindowToggleGroupSpec` to add the window toggle block.
6. Use `TaskPanelFocusToggleSpec` inside `RoutedRuntimeSpec` for automatic focus ring management when windows are shown/hidden.

**Tween animation:**
```python
# In bind_runtime:
self._fade_in = host.tweens.to(self.panel, "alpha", 255, duration=0.3, easing=Easing.EASE_OUT)
```

**Cooperative coroutine:**
```python
def _save_workflow(self, host):
    host.toasts.show("Saving...", severity=ToastSeverity.INFO)
    yield Sleep(0.5)  # simulate async save
    host.toasts.show("Saved!", severity=ToastSeverity.SUCCESS)

# In on_update or an action handler:
host.scheduler.run(self._save_workflow(host))
```

**Debouncer for search input:**
```python
# In __init__:
self._search_debounce = Debouncer(delay=0.3, callback=self._run_search)

# In bind_runtime, subscribe to text input changes:
self._sub = self.search_input.text.subscribe(lambda t: self._search_debounce.trigger(t))
```

#### Advanced pattern: `AnimationStateMachine` for hover effects

```python
from gui_do import AnimationStateMachine, AnimationTransitionMode

machine = AnimationStateMachine()
machine.add_state("idle", AnimationSequence([...]))
machine.add_state("hovered", AnimationSequence([...]))
machine.add_transition("idle", "hovered", condition=lambda: self._hovered)
machine.add_transition("hovered", "idle", condition=lambda: not self._hovered)
```

For multi-step user workflows that span multiple frames without blocking the UI, use `CooperativeScheduler` with `WaitForSignal` to wait for user confirmation between steps:

```python
def _wizard_workflow(self, host):
    self.show_step_1()
    yield WaitForSignal(self._step1_confirmed)
    self.show_step_2()
    yield WaitForSignal(self._step2_confirmed)
    self._finalize(host)
```

#### Common mistakes

- Unbounded work per frame in `on_update` — any computation that takes more than a fraction of a millisecond belongs in a `CooperativeScheduler` coroutine, not inline in `on_update`.
- Blocking I/O inside a `CooperativeScheduler` coroutine — cooperative scheduling is not threading; blocking calls will block the entire frame. Use `DataflowPipeline` (Tier 26) for I/O-bound work.
- Not canceling tweens on scene exit — tweens that apply mutations to dead controls cause errors after the scene leaves.
- Forgetting to cancel `CoroutineHandle` objects in `shutdown_runtime` — coroutines referencing dead host objects will crash on their next resume.

#### Cross-links

→ 8.2 Feature Lifecycle (on_update drives the scheduler) | 8.14 Data and Dataflow (DataflowPipeline for I/O-bound multi-stage pipelines) | 8.16 Telemetry (scheduler budget tracking)

---

### 8.11 Persistence and Workspace/Session State

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Users expect their session to survive application restarts — last open scene, window positions, feature-specific state, and user settings. `gui_do` provides a workspace persistence layer that saves and restores this state with a robust restore-report contract, a typed settings registry, and a versioned snapshot system with BFS migration for schema evolution.

#### Mental model and lifecycle placement

The workspace is a structured JSON snapshot of the session at a save point. On restore, the runtime can switch to the saved scene, replay feature state, restore scene snapshots, and replay settings. Missing keys are always skipped, not fatal — the restore report tells you precisely what was applied, skipped, or absent. For schema evolution, `SnapshotMigrator` walks a registered migration graph to bring old snapshots up to the current schema before passing them to the runtime.

#### Primary public APIs

From **Tier 11** (state and persistence):
- `CommandHistory`, `Command`, `CommandTransaction` — undo/redo stack; `Command` is an executable+undoable pair; `CommandTransaction` groups multiple commands into a single undo step
- `StateMachine` — general-purpose state machine with guarded transitions
- `HierarchicalStateMachine` — state machine supporting nested (orthogonal) states
- `Router`, `RouteEntry` — named route registration and dispatch
- `SettingsRegistry`, `SettingDescriptor` — typed named settings with defaults, type validation, and workspace round-trip; `SettingDescriptor` declares the key, type, and default
- `WorkspaceState`, `WorkspacePersistenceManager`, `DEFAULT_WORKSPACE_STATE_PATH` — workspace save/restore; `WorkspacePersistenceManager.restore()` returns a structured restore report
- `SceneSnapshot`, `NodeSnapshot` — serializable snapshot of a scene or node's state

From **Tier 32** (portable snapshot and migration):
- `SchemaVersion` — type alias for versioned schema identifiers
- `VersionedSnapshot` — a snapshot object tagged with a schema version
- `MigrationStep` — a single version-to-version migration function
- `MigrationRegistry` — collects registered `MigrationStep` objects; defines the migration graph
- `SnapshotMigrator` — BFS migration executor; walks the registered steps to bring an old snapshot to the current schema
- `MigrationError` — raised when the migration graph cannot reach the target version
- `make_snapshot` — creates a new `VersionedSnapshot` at the current schema version
- `read_version` — reads the schema version from a snapshot without fully deserializing it

From **Tier 23** (undo context routing):
- `UndoContextManager` — named multi-stack undo/redo routing; different UI panels can have independent undo stacks all routed through a single manager

#### Restore report fields (from `docs/runtime_operating_contracts.md` Section 4)

The restore report includes: `target_scene`, `switched_scene`, `restored_feature_states`, `restored_scene_nodes`, `applied_settings`, `skipped_settings`, `missing_settings_blocks`.

#### Typical usage flow

```python
# Save:
host.app.save_workspace(path)

# Load:
report = host.app.load_workspace(path)
if report and report.skipped_settings:
    host.toasts.show(
        f"{len(report.skipped_settings)} setting(s) could not be restored",
        severity=ToastSeverity.WARNING,
    )
```

#### Minimal example

```python
from gui_do import SettingsRegistry, SettingDescriptor

registry = SettingsRegistry()
registry.register(SettingDescriptor("theme", str, default="light"))
registry.register(SettingDescriptor("font_size", int, default=14))

# Save happens automatically via WorkspacePersistenceManager
```

#### Advanced pattern: `SnapshotMigrator` for schema evolution

```python
from gui_do import MigrationRegistry, MigrationStep, SnapshotMigrator, SchemaVersion, read_version

registry = MigrationRegistry()
registry.register(MigrationStep(from_version="1.0", to_version="1.1", migrate=add_new_fields))
registry.register(MigrationStep(from_version="1.1", to_version="1.2", migrate=rename_field))

migrator = SnapshotMigrator(registry, current_version="1.2")

snapshot = load_snapshot_from_disk()
if read_version(snapshot) != "1.2":
    snapshot = migrator.migrate(snapshot)
```

Register `CommandHistory` per panel or per-document. Combine with `UndoContextManager` to route undo/redo keyboard shortcuts to the appropriate panel's history based on which panel has focus.

#### Common mistakes

- Assuming all settings keys always exist in the restore report — use `skipped_settings` and `missing_settings_blocks` to detect incomplete restores.
- Restoring snapshots without checking `read_version` first — a snapshot from a future schema version may have fields the current runtime does not understand.
- Using `DEFAULT_WORKSPACE_STATE_PATH` in multi-instance or multi-user scenarios — define per-instance or per-user paths to avoid collisions.
- Not registering settings before calling `restore_workspace` — unregistered settings are silently skipped.

#### Cross-links

→ 8.1 Bootstrap (workspace restore can switch initial scene) | 8.2 Feature Lifecycle (shutdown_runtime is the correct place to snapshot feature state) | 8.16 Telemetry (telemetry log is a separate observability mechanism)

---

### 8.12 Theme, Styling, and Visual Systems

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Theming centralizes design tokens, colors, and font roles so that changing the visual style of an application does not require modifying individual controls or features. A theme switch updates every control that reads from the theme system simultaneously, without manual notification code. `gui_do`'s theme system makes it practical to support dark/light modes, user-customizable palettes, and per-window style overrides.

#### Mental model and lifecycle placement

The `ThemeManager` holds the active theme. `DesignTokens` provides named values (colors, spacing, radii, icon sizes) that controls read at render time. `FontRoleRegistry` maps semantic role names (e.g., "heading", "body", "caption") to font configurations. When the theme changes, `ThemeInvalidationBus` notifies all registered subscribers — typically cached rendered surfaces — to flush and re-render. Controls never cache theme values directly; they query the theme at render time.

#### Primary public APIs

From **Tier 6** (theme and font management):
- `FontManager` — loads and caches pygame font instances by name and size
- `FontRoleRegistry` — maps semantic font role names to font configurations; controls look up fonts by role
- `ColorTheme` — a named set of color mappings from semantic roles to RGBA values
- `ThemeManager`, `DesignTokens` — `ThemeManager` holds the active `ColorTheme` and `DesignTokens`; controls query `DesignTokens` for named scalar or color values (border radius, spacing, etc.)
- `ScopedTheme`, `ScopedThemeManager` — apply a local theme override to a control subtree; useful for windows that should look visually distinct from the main scene

From **Tier 22** (theme invalidation):
- `ThemeInvalidationBus` — broadcast channel; when the active theme changes, all registered subscribers receive an invalidation signal and must flush their caches

From **Tier 1** (spec integration):
- `FontRoleBindingSpec` — declares the mapping from semantic font role names to font configurations in the bootstrap spec
- `CursorSpec`, `CursorBindingSpec` — declare custom cursor shapes and their scene bindings
- `PaletteBindingSpec` — declares command-palette entry-group behavior (Scene group, Window group, custom callable entries, and group order)
- `setup_standard_font_roles` — convenience function (Tier 1) to register standard font roles from a font config dictionary

#### Typical usage flow

1. Declare a `fonts` dict in `HostApplicationBindingSpec` mapping name → font config (file path and size).
2. Declare `FontRoleBindingSpec` entries to map semantic role names to font configurations.
3. Controls look up fonts by semantic role name via `FontRoleRegistry` — they automatically use the right font.
4. To switch themes at runtime: call `host.theme_manager.set_theme(name)` — `ThemeInvalidationBus` fires invalidation to all registered caches automatically.
5. For per-window style overrides, use `ScopedThemeManager` to apply a local override to the window's control subtree.

#### Minimal example

In `HostApplicationBindingSpec`:
```python
fonts={
    "default": {"file": "assets/fonts/Regular.ttf", "size": 14},
    "heading": {"file": "assets/fonts/Bold.ttf", "size": 18},
},
font_role_entries=(
    FontRoleBindingSpec(role="body", font_name="default"),
    FontRoleBindingSpec(role="heading", font_name="heading"),
),
```

#### Advanced pattern: `ThemeInvalidationBus` for custom surface caches

```python
from gui_do import ThemeInvalidationBus

# In a custom control's build or __init__:
self._surface_cache = {}

def _on_theme_invalidated(self):
    self._surface_cache.clear()

# Register the invalidation callback:
host.theme_invalidation_bus.subscribe(self._on_theme_invalidated)

# In shutdown_runtime, unsubscribe:
host.theme_invalidation_bus.unsubscribe(self._on_theme_invalidated)
```

Use `ScopedTheme` with `ScopedThemeManager` for a dark sidebar in a light-themed application:
```python
from gui_do import ScopedTheme, ScopedThemeManager

dark_theme = ScopedTheme(overrides={"background": (30, 30, 30, 255), "text": (240, 240, 240, 255)})
scoped_mgr = ScopedThemeManager(sidebar_root, dark_theme)
```

#### Common mistakes

- Hardcoding color literals in feature or control draw code — hardcoded values break theme switching.
- Caching rendered text or color surfaces without subscribing to `ThemeInvalidationBus` — stale colors persist after a theme switch.
- Registering font roles after bootstrap (in `build`) — `FontRoleRegistry` may already be in use; register roles in the bootstrap spec phase.
- Using `ScopedTheme` without `ScopedThemeManager` — scope changes must be tracked so they can be unapplied when the control subtree is destroyed.

#### Cross-links

→ 8.1 Bootstrap (font and palette config) | 8.5 Controls (controls read theme tokens at render time) | 8.16 Telemetry (visual diagnostics can read theme state)

---

### 8.13 Text, Input, Forms, and Validation Systems

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Structured text entry, document editing, form modeling, and validation are requirements common enough to deserve first-class framework support. `gui_do` provides a layered system: low-level text controls handle keystroke-level interaction; `FormModel` and `FormSchema` model the logical form; `SchemaFormRuntime` drives validation policy; `AsyncFormValidator` handles debounced async validation. Taken together, they cover the full spectrum from a simple single-field input to a multi-step wizard with cross-field dependencies.

#### Mental model and lifecycle placement

Text controls receive keystrokes and expose their text as an `ObservableValue`. Form models sit above them: they hold field definitions, validation rules, and cross-field dependencies. Validation runs according to a `ValidationPolicy`. Async validation (server-side checks) is managed through a debounced pipeline that suppresses stale results. Wire everything in `bind_runtime`; tear it down in `shutdown_runtime`.

#### Primary public APIs

From **Tier 10** (forms and data binding):
- `FormModel`, `FormField`, `ValidationRule`, `FieldError` — model a form as a collection of typed fields with rules; `FieldError` carries field-level error messages
- `FormSchema`, `SchemaField` — declarative schema definition; `SchemaField` declares field name, type, constraints, and visibility dependencies
- `DocumentModel` — rich-text document backing for `TextAreaControl`; represents text as a sequence of styled spans with editing operations
- `WizardFlow`, `WizardStep`, `WizardHandle` — multi-step guided workflow; each step has its own control tree and validation; `WizardHandle` navigates forward/backward and reports completion
- `ValidationResult`, `Validator`, `RequiredValidator`, `RangeValidator`, `LengthValidator`, `PatternValidator`, `CustomValidator`, `DependentValidator`, `ValidationPipeline` — composable validator types; `ValidationPipeline` runs an ordered list of validators and collects all errors or stops on first failure

From **Tier 24** (async form validation):
- `AsyncFieldValidator` — single-field async validator with debounce and stale-result suppression
- `AsyncFormValidator` — coordinates multiple `AsyncFieldValidator` instances across a form; fires combined `ValidationResult` after all async validators settle

From **Tier 31** (schema-driven form runtime):
- `FieldSchema` — per-field schema declaration for the runtime
- `FieldGraphSchema` — directed acyclic graph of fields with visibility and enablement dependencies
- `ValidationPolicy` — controls when validation fires: `ON_CHANGE`, `ON_BLUR`, `ON_SUBMIT`, `ALWAYS`
- `SchemaFormRuntime` — drives `FieldGraphSchema` with a `ValidationPolicy`; automatically recalculates field visibility when dependency values change

From **Tier 14** (text and localization):
- `TextFormatter`, `NumericFormatter`, `PatternFormatter`, `FixedPatternFormatter` — format values for display with type-specific formatting rules
- `TextFlow`, `TextSpan` — rich text flow model with inline styled spans for display
- `TextSearcher`, `TextMatch` — text search with match highlighting
- `StringTable`, `LocaleRegistry` — internationalization; register locale-keyed string tables; look up strings by key at render time

#### Typical usage flow

1. Define a `FormSchema` with `SchemaField` entries (name, type, required, constraints).
2. Build a `FieldGraphSchema.from_form_schema(schema)` to create the dependency graph.
3. Construct a `SchemaFormRuntime` with the field graph and a `ValidationPolicy`.
4. Bind form fields to `TextInputControl`, `DropdownControl`, or other input controls; subscribe to their text/value observables.
5. Run validation; display `FieldError` messages adjacent to each field.

#### Minimal example

```python
from gui_do import (
    FormSchema, SchemaField, FieldGraphSchema, SchemaFormRuntime,
    ValidationPolicy, RequiredValidator, PatternValidator, ValidationPipeline,
)

schema = FormSchema(fields=[
    SchemaField("email", str, validators=ValidationPipeline([
        RequiredValidator(),
        PatternValidator(r"^[^@]+@[^@]+\.[^@]+$", message="Enter a valid email address"),
    ])),
    SchemaField("password", str, validators=ValidationPipeline([
        RequiredValidator(),
    ])),
])

field_graph = FieldGraphSchema.from_form_schema(schema)
runtime = SchemaFormRuntime(field_graph, policy=ValidationPolicy.ON_CHANGE)
```

#### Advanced pattern: `AsyncFormValidator` for server-side checks

```python
from gui_do import AsyncFieldValidator, AsyncFormValidator

username_validator = AsyncFieldValidator(
    field="username",
    validate_fn=check_username_available_async,  # returns ValidationResult
    debounce_seconds=0.4,
)
form_validator = AsyncFormValidator(validators=[username_validator])
# In bind_runtime, subscribe to username text changes:
self._sub = username_input.text.subscribe(
    lambda v: form_validator.trigger("username", v, on_result=self._on_validation_result)
)
```

Stale results (from a previous debounce window) are automatically suppressed — only the result for the most recent generation is delivered.

#### Common mistakes

- Validating only on submit when users expect continuous feedback — use `ValidationPolicy.ON_CHANGE` for real-time error display.
- Ignoring `DependentValidator` for cross-field rules — a "confirm password" check belongs in a `DependentValidator`, not in `on_update`.
- Wiring `AsyncFormValidator` without cancellation — if the user submits before async validation completes, the result may arrive after the form is dismissed.

#### Cross-links

→ 8.4 State/Observables (field values stored as ObservableValues) | 8.5 Controls (TextInputControl, DropdownControl) | 8.14 Data pipeline (DataflowPipeline for async validation backends)

---

### 8.14 Data and Dataflow Helpers

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Data-heavy features need efficient loading, sorting, filtering, and virtualized rendering of large datasets — and all of this must happen without blocking the frame loop. `gui_do` provides a composable pipeline from async loading through sort/filter proxies into virtualized display, with cancelable multi-stage processing for long-running background work.

#### Mental model and lifecycle placement

Data flows from a source (`AsyncDataProvider` or `FixedItemSource`) through a `SortFilterProxySource` into a virtualized control or a `VirtualizationCore`. The `DataflowPipeline` handles multi-stage background processing with `CancellationToken` for stale-generation suppression. Wire sources and pipelines in `bind_runtime`; cancel them in `shutdown_runtime`.

#### Primary public APIs

From **Tier 15** (data and collections):
- `VirtualItemSource`, `FixedItemSource` — abstract item provider and plain-list implementation; `count` + `get_item(index)` on demand
- `SortFilterProxySource` — wraps a `VirtualItemSource`; provides sort/filter without copying; `set_sort_key()`, `set_filter()`, `set_sort_reverse()`
- `AsyncDataProvider`, `LoadState`, `LoadStateKind` — async data loader; exposes `LoadState` with kind `IDLE`, `LOADING`, `LOADED`, `ERROR`; subscribe to state changes to drive a progress indicator
- `ObjectPool` — pre-allocated pool for high-churn objects; `acquire()` / `release(obj)` to reduce GC pressure
- `DataCache`, `CacheStats` — LRU-keyed cache with hit/miss metrics via `CacheStats`
- `ListDiffCalculator`, `ListDiff`, `DiffInsert`, `DiffRemove`, `DiffMove` — compute minimal diff patches between two list snapshots; use to drive incremental UI updates

From **Tier 26** (cancelable dataflow pipeline):
- `CancellationToken` — token passed to each pipeline stage; stages check `is_cancelled()` to bail out early
- `PipelineStage` — a single processing step; receives input and `CancellationToken`, produces output
- `DataflowPipeline` — multi-stage pipeline; new `run()` calls cancel the previous generation automatically
- `PipelineHandle` — reference to the running pipeline; `.cancel()` to stop it manually

From **Tier 29** (virtualization core):
- `MeasureMode`, `MeasurePolicy` — item measure strategy for variable-height or fixed-height virtualized lists
- `VirtualizedWindow` — higher-level windowed rendering: given scroll position and viewport, produces the visible item range
- `RecyclePool` — view recycling by type key; `acquire(key)` to get a reusable item view; `release(key, view)` to return it
- `VirtualizationCore` — main windowing engine for list/tree/grid; handles scroll offset, item identity tracking, and recycle pool coordination

#### Typical usage flow: sort/filter with a list view

```python
from gui_do import FixedItemSource, SortFilterProxySource

source = FixedItemSource(my_items)
proxy = SortFilterProxySource(source)
proxy.set_filter(lambda item: item.active)
proxy.set_sort_key(lambda item: item.name)
list_view_control.set_source(proxy)
```

#### Minimal example: async data provider with progress indicator

```python
from gui_do import AsyncDataProvider, LoadStateKind

provider = AsyncDataProvider(load_fn=fetch_records_async)

# In bind_runtime:
self._sub = provider.state.subscribe(self._on_load_state)

def _on_load_state(self, state):
    if state.kind == LoadStateKind.LOADING:
        self.progress_bar.set_visible(True)
    elif state.kind == LoadStateKind.LOADED:
        self.progress_bar.set_visible(False)
        self.list_view.set_source(FixedItemSource(state.data))
    elif state.kind == LoadStateKind.ERROR:
        self.error_label.set_text(str(state.error))
```

#### Advanced pattern: cancelable `DataflowPipeline`

```python
from gui_do import DataflowPipeline, PipelineStage, CancellationToken

def load_stage(token: CancellationToken, query: str):
    results = fetch_matching(query)
    if token.is_cancelled():
        return None
    return results

def rank_stage(token: CancellationToken, results):
    ranked = rank_by_score(results)
    if token.is_cancelled():
        return None
    return ranked

pipeline = DataflowPipeline([
    PipelineStage(load_stage),
    PipelineStage(rank_stage),
])

# Each call to run() cancels the previous generation:
handle = pipeline.run(query=self.search_query)
```

Use `ListDiffCalculator` to compute incremental updates when a data source refreshes:

```python
from gui_do import ListDiffCalculator

diff = ListDiffCalculator.compute(old_items, new_items, key_fn=lambda x: x.id)
for op in diff.ops:
    if isinstance(op, DiffInsert):
        list_view.insert_item(op.index, op.item)
    elif isinstance(op, DiffRemove):
        list_view.remove_item(op.index)
    elif isinstance(op, DiffMove):
        list_view.move_item(op.from_index, op.to_index)
```

#### Common mistakes

- Full-list re-renders when only a few items changed — use `ListDiffCalculator` to apply minimal patches.
- Forgetting to cancel stale `DataflowPipeline` generations — old results can arrive after newer ones and overwrite them.
- Holding large datasets in memory without `DataCache` eviction — memory grows unbounded.
- Returning `ObjectPool` objects that are still referenced elsewhere — the pool assumes released objects are no longer in use.

#### Cross-links

→ 8.4 State/Observables (LoadState changes drive observable updates) | 8.5 Controls (ListViewControl, DataGridControl use VirtualItemSource) | 8.10 Scheduling (CooperativeScheduler for async orchestration) | 8.16 Telemetry (pipeline stage timing)

---

### 8.15 Graphics and Audio Integration Points

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Some features go beyond what the control tree can express — particle effects, tile maps, 2D camera-relative worlds, or custom sprite animations. `gui_do` provides graphics helpers that build on pygame surfaces, giving features structured access to offscreen rendering, dirty-region tracking, shape drawing, and layered compositing. For audio, a portable cue-based system wraps `pygame.mixer` so features can trigger named sounds without knowing mixer internals.

#### Mental model and lifecycle placement

Custom rendering lives in `draw(host, screen)` for features that need full-frame control, or inside `CanvasControl` for self-contained drawing surfaces within the control tree. Graphics helpers are stateless utilities; the state (particle systems, tile maps, sprite animations) lives on the feature. Audio cues are event-driven via `SoundEventBus`.

#### Primary public APIs

From **Tier 16** (graphics and rendering):
- `BuiltInGraphicsFactory` — factory for common visual assets (checkboxes, icons, arrows) without external files
- `DirtyRegionTracker` — per-frame dirty-rect accumulation; `mark_dirty(rect)`, `overlaps_dirty(rect)`, `consume_dirty_regions()`
- `DrawContext`, `DrawPhase` — structured draw pass with explicit phases (background, content, overlay, debug)
- `AssetRegistry` — centralized registry for loaded surfaces, fonts, and other assets; prevents duplicate loading
- `DebugOverlay` — renders debug visualizations (control bounds, spatial index queries) over the live scene
- `SurfaceCompositor`, `Layer` — layered rendering pipeline; each `Layer` has z-order and optional blend mode; `SurfaceCompositor` composites in order
- `ShapeRenderer` — utility for drawing common shapes (rounded rects, arrows, circles, lines) without low-level pygame draw calls
- `SurfaceEffects` — post-processing effects on a surface (blur, tint, darken)
- `VectorPath` — declarative path builder (move_to, line_to, curve_to, arc) rendered via pygame primitives
- `SpriteSheet`, `FrameAnimation` — extract frames from a sprite atlas; drive playback with frame duration and loop settings
- `ParticleSystem`, `Emitter`, `ParticleLayer` — particle emission with configurable spawn rates, velocities, lifetimes, colors; tick in `on_update`, draw in `draw`
- `TileSet`, `TileMap` — grid-based tile rendering; `TileSet` holds the texture atlas; `TileMap` holds grid data and renders only visible tiles
- `RenderTarget`, `LiveRenderTarget`, `OffscreenRenderTarget`, `create_render_target`, `create_surface` — render to an offscreen surface then composite it; for caching expensive draws or applying effects
- `Node2D`, `SceneGraph2D`, `Camera2D` — hierarchical 2D transform tree; nodes inherit parent transforms; `Camera2D` applies a viewport transform for scrolling/zooming

From **Tier 20** (audio):
- `SoundCue` — named audio cue event; carries the cue name and optional parameters
- `SoundBankRegistry` — registry of named sound cues mapped to audio files
- `SoundEventBus` — publish `SoundCue` events; the bus routes to the mixer without features knowing mixer internals

#### Typical usage flow: particle effect

```python
from gui_do import ParticleSystem, Emitter

# In build:
self.particles = ParticleSystem()
self.emitter = Emitter(spawn_rate=30, lifetime=1.5, velocity=(0, -80))
self.particles.add_layer(ParticleLayer(emitter=self.emitter))

# In on_update:
self.particles.tick(dt)

# In draw:
self.particles.draw(screen)
```

Audio cue:
```python
host.sound_bus.publish(SoundCue("explosion"))
```

#### Advanced pattern: dirty-region + offscreen cache

```python
from gui_do import DirtyRegionTracker, OffscreenRenderTarget, create_render_target

# In build:
self.cache = create_render_target(width=800, height=600, live=False)
self.dirty = DirtyRegionTracker()

# In on_update:
if data_changed:
    self.dirty.mark_dirty(affected_rect)

# In draw:
dirty_regions = self.dirty.consume_dirty_regions()
for region in dirty_regions:
    self.cache.surface.fill(background, region)
    draw_tiles_in_region(self.cache.surface, region, self.tile_map)
screen.blit(self.cache.surface, dest)
```

Combine `SceneGraph2D` with `Camera2D` for a scrollable world:
```python
from gui_do import SceneGraph2D, Node2D, Camera2D

world = SceneGraph2D()
camera = Camera2D(viewport=screen_rect)
camera.position = (player_x - 640, player_y - 360)
world.camera = camera
# Nodes added to world.root use world-space coordinates; camera transform is applied at draw
```

#### Common mistakes

- Full-surface redraw every frame when `DirtyRegionTracker` could gate it — mark dirty only the regions that actually changed.
- Triggering audio cues from low-level pointer events (e.g., every `MOUSE_MOTION`) — cues should fire on semantic application events (button click, level start), not raw input noise.
- Loading assets in `draw` — this causes per-frame disk I/O; load in `build` and use `AssetRegistry` to cache.
- Creating `ParticleSystem` emitters without bounds so particles escape the rendering region — always set emitter bounds or clip the draw target.

#### Cross-links

→ 8.2 Feature Lifecycle (draw hook) | 8.5 Controls (CanvasControl for in-tree custom drawing) | 8.10 Scheduling (particle tick driven from on_update) | 8.16 Telemetry (profiling draw cost)

---

### 8.16 Telemetry, Introspection, and Operational Hooks

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Runtime observability — performance measurement, property inspection, and spatial querying — lets developers diagnose behavior precisely without relying on visual inspection alone. `gui_do` instruments hot paths with telemetry spans, exposes control properties through a `PropertyRegistry` for runtime inspection, and provides a `SceneSpatialIndex` for geometric queries over the live control tree.

#### Mental model and lifecycle placement

Telemetry is opt-in: enable it at bootstrap via `TelemetryConfig` or at runtime via `configure_telemetry`. Once enabled, spans are recorded throughout the app pipeline. Telemetry analysis can be performed inline or from saved log files. Property introspection is always on — `@ui_property` decorators annotate control attributes at class-definition time, and `PropertyRegistry` collects them automatically.

#### Primary public APIs

From **Tier 7** (telemetry and diagnostics):
- `TelemetryCollector`, `TelemetrySample` — the active collector singleton and per-sample data class
- `configure_telemetry` — enable or disable telemetry globally
- `telemetry_collector` — module-level singleton `TelemetryCollector` instance
- `analyze_telemetry_log_file`, `analyze_telemetry_records`, `load_telemetry_log_file`, `render_telemetry_report` — offline and inline analysis and formatted reporting

From **Tier 17** (introspection and inspection):
- `SceneSpatialIndex` — spatial query engine for the control tree; find controls overlapping a rect, at a point, or within a region
- `ui_property` — decorator; marks a control attribute as an inspectable UI property
- `PropertyDescriptor`, `PropertyRegistry`, `property_registry` — collects all `@ui_property` descriptors; `property_registry` is the module-level singleton
- `PropertyInspectorModel`, `InspectedProperty` — drives the `PropertyInspectorPanel` control; `InspectedProperty` carries name, type, current value, and setter

From **Tier 1** (spec):
- `TelemetryConfig` — declare in `HostApplicationBindingSpec` to enable telemetry at bootstrap time

#### Typical usage flow

```python
from gui_do import configure_telemetry, telemetry_collector, analyze_telemetry_records, render_telemetry_report

configure_telemetry(enabled=True)

# ... run representative scenarios ...

report = analyze_telemetry_records(telemetry_collector.records)
print(render_telemetry_report(report))
```

For property inspection:
```python
from gui_do import ui_property, PropertyInspectorModel

class MyControl:
    @ui_property
    def alpha(self) -> int:
        return self._alpha

model = PropertyInspectorModel(target=my_control_instance)
# Bind model to PropertyInspectorPanel control
```

#### Advanced pattern: `DebugOverlay` + `SceneSpatialIndex`

```python
from gui_do import DebugOverlay, SceneSpatialIndex

# In draw:
index = host.scene_spatial_index
controls_under_cursor = index.query_at(host.pointer_pos)
debug.draw_bounds(screen, [c.rect for c in controls_under_cursor], color=(255, 0, 0))
```

Combine telemetry traces with `PropertyInspectorModel` snapshots taken at the moment of a regression to localize layout or routing issues to a specific frame and control.

#### Common mistakes

- Profiling without representative user scenarios — the idle loop has a flat telemetry profile; measure under realistic load (many controls active, transitions firing, data pipeline running).
- Relying on visual inspection alone for frame budget violations — telemetry reports identify the exact span that exceeded budget.
- Forgetting `configure_telemetry(enabled=True)` before the scenarios you want to measure — spans are no-ops when telemetry is disabled.

#### Cross-links

→ 8.1 Bootstrap (TelemetryConfig) | 8.10 Scheduling (scheduler budget) | 8.11 Persistence (telemetry log paths) | 8.15 Graphics (draw cost profiling)

---

## Integration Patterns and Composition Recipes

[Back to Table of Contents](#table-of-contents)

This chapter documents four concrete composition patterns that appear repeatedly in well-structured `gui_do` applications. Each recipe is self-contained: it states the goal, explains why this combination of systems is appropriate, walks through the construction step by step, and includes a validation checklist.

### Recipe 1: Routed Feature + Actions + Shortcut Overlay

**Goal.** A feature that has keyboard shortcuts visible to the user via a help overlay, all wired automatically without manual cleanup code.

**Why this combination.** `RoutedRuntimeSpec` and `RoutedFeatureLifecycleSpec` declare all action hotkeys, event subscriptions, and overlay specs in one data structure. `bind_routed_feature_lifecycle` activates them in one call; `shutdown_routed_feature_lifecycle` tears them all down cleanly. This eliminates scattered registration and deregistration calls spread across `bind_runtime` and `shutdown_runtime`.

**Steps:**
1. Declare `ActionSpec` entries with `ActionHotkeySpec` in `HostApplicationBindingSpec`.
2. In the feature's `__init__`, build a `RoutedRuntimeSpec` with a `ShortcutOverlaySpec`:
   ```python
   from gui_do import RoutedRuntimeSpec, ShortcutOverlaySpec, RoutedFeatureLifecycleSpec

   self._lifecycle_spec = RoutedFeatureLifecycleSpec(
       runtime_spec=RoutedRuntimeSpec(
           shortcut_overlay=ShortcutOverlaySpec(
               toggle_action_name="help",
               toggle_key="f1",
               manual_shortcut_lines=[("F1", "Show/hide shortcuts")],
           ),
       ),
   )
   ```
3. In `bind_runtime`, call `bind_routed_feature_lifecycle(self, host, self._lifecycle_spec)`.
4. In `shutdown_runtime`, call `shutdown_routed_feature_lifecycle(self, host, self._lifecycle_spec)`.

**Validation.** The F1 key toggles the shortcut overlay. The overlay lists the declared actions. Pressing F1 again dismisses it. Scene exit disposes all bindings automatically.

---

### Recipe 2: Window Presenter + Task Panel + Focus Toggle

**Goal.** A floating window in a scene, toggled from the task panel, with correct focus-ring exclusion when hidden.

**Why this combination.** `WindowPresenter` keeps window construction separated from feature lifecycle. `FeatureWindowBundleBindingSpec` wires the feature, window, and task panel button in one spec. `TaskPanelFocusToggleSpec` automatically excludes hidden window controls from the focus ring.

**Steps:**
1. Implement a `WindowPresenter` subclass that builds the window's control tree in its `build` method.
2. In `HostApplicationBindingSpec`, add a `FeatureWindowBundleBindingSpec`:
   ```python
   FeatureWindowBundleBindingSpec(
       "_my_feature", MyFeature, "my_window",
       slot_index=0, task_panel_label="My Tool",
   )
   ```
3. In the feature's `RoutedRuntimeSpec`, add a `TaskPanelFocusToggleSpec`:
   ```python
   TaskPanelFocusToggleSpec(window_id="my_window", toggle_action="toggle_my_window")
   ```
4. Wire the window toggle button to `set_window_visible_state(host, "my_window", visible)`.

**Validation.** Task panel button toggles the window. Tab cycling skips hidden window controls. Button state is in sync with window visibility. Focus returns to the scene root when the window is hidden.

---

### Recipe 3: State Store + Persistence + Snapshot Migration

**Goal.** Centralized application state that survives application restarts and schema evolution across releases.

**Why this combination.** `AppStateStore` provides a single source of truth. `WorkspacePersistenceManager` saves and restores the session. `SnapshotMigrator` handles schema evolution so users do not lose state when the app updates.

**Steps:**
1. Create an `AppStateStore` with the initial state dict.
2. Create `StateSelector` instances for each feature that needs a state slice.
3. On save, call `make_snapshot(current_version, store.snapshot())` and persist it.
4. On load, call `read_version(raw)`, then `migrator.migrate(snapshot)` if needed, then restore into the store.
5. Register `MigrationStep` objects for each schema version transition in a `MigrationRegistry`.

```python
from gui_do import AppStateStore, StateSelector, make_snapshot, read_version, SnapshotMigrator, MigrationRegistry, MigrationStep

store = AppStateStore({"theme": "light", "recent_files": []})
selector = StateSelector(store, keys=("theme",))

# On save:
snapshot = make_snapshot(current_version="2.0", data=store.snapshot())

# On load:
raw = load_from_disk()
version = read_version(raw)
if version != "2.0":
    snapshot = migrator.migrate(raw)
store.restore(snapshot.data)
```

**Validation.** Restore report `skipped_settings` is empty for compatible saves. Old v1.0 snapshots migrate to v2.0 without errors. Missing keys log to `missing_settings_blocks` without raising.

---

### Recipe 4: Dataflow Pipeline + Telemetry + Error Boundary

**Goal.** Safe background processing with measurable performance and UI failure containment.

**Why this combination.** `DataflowPipeline` keeps background work cancelable and off the hot frame path. Telemetry traces identify which stage is slow. `ErrorBoundary` ensures that rendering failures in the output panel degrade gracefully rather than crashing the frame.

**Steps:**
1. Define pipeline stages as functions that accept a `CancellationToken` and return early if cancelled.
2. Wrap the output control subtree in `ErrorBoundary` with a fallback label.
3. Instrument each stage with a `telemetry_collector` span.
4. Expose progress via `ObservableValue`; subscribe in the UI feature's `bind_runtime`.
5. Call `pipeline.run(input)` on each new user query; the previous run is cancelled automatically.

```python
from gui_do import DataflowPipeline, PipelineStage, CancellationToken, ErrorBoundary, ObservableValue

self.progress = ObservableValue(0.0)

def fetch_stage(token: CancellationToken, query):
    data = fetch(query)
    self.progress.value = 0.5
    return data if not token.is_cancelled() else None

def rank_stage(token: CancellationToken, data):
    ranked = rank(data)
    self.progress.value = 1.0
    return ranked if not token.is_cancelled() else None

pipeline = DataflowPipeline([PipelineStage(fetch_stage), PipelineStage(rank_stage)])
```

In `build`, wrap results panel:
```python
results_panel = ErrorBoundary("results_safe", results_rect, child=results_control, fallback=error_label)
```

**Validation.** New query cancels previous pipeline run. Telemetry report shows per-stage timing. If results panel raises during draw, `ErrorBoundary` catches it and renders the fallback without crashing the frame.

---

## End-to-End Reference Application

[Back to Table of Contents](#table-of-contents)

The following listing demonstrates the complete `gui_do` programming model in one annotated example. It is not a toy — every element maps to a real system documented in this manual.

```python
# e2e_reference_app.py
# Complete reference application demonstrating the gui_do programming model.

from gui_do import (
    # Bootstrap
    HostApplicationBindingSpec, SceneBundleBindingSpec, SceneTransitionStyle,
    TelemetryConfig, build_host_application_config, bootstrap_host_application,
    # Feature base
    RoutedFeature, FeatureMessage,
    # State
    ObservableValue,
    # Actions and specs
    ActionSpec, ActionHotkeySpec, RoutedRuntimeSpec, ShortcutOverlaySpec,
    RoutedFeatureLifecycleSpec,
    # Controls
    PanelControl, LabelControl, ButtonControl,
    # Scheduling/overlay
    ToastSeverity,
    # Telemetry
    configure_telemetry,
)
import pygame


class CounterFeature(RoutedFeature):
    """A minimal feature: observable counter wired to a label, with action routing."""

    HOST_REQUIREMENTS = {
        "build": ("scene_controls", "screen_rect"),
        "bind_runtime": ("scene_controls", "toasts"),
        "shutdown_runtime": (),
    }

    def __init__(self):
        super().__init__()
        self._count = ObservableValue(0)
        self._label = None
        self._sub = None
        self._lifecycle_spec = RoutedFeatureLifecycleSpec(
            runtime_spec=RoutedRuntimeSpec(
                shortcut_overlay=ShortcutOverlaySpec(
                    toggle_action_name="help",
                    toggle_key="f9",
                    manual_shortcut_lines=[
                        ("Up", "Increment counter"),
                        ("F9", "Toggle shortcut help"),
                    ],
                ),
            ),
        )

    def build(self, host):
        root = PanelControl("root", host.screen_rect)
        self._label = LabelControl("count_label", pygame.Rect(40, 40, 300, 40), "Count: 0")
        btn = ButtonControl("inc_btn", pygame.Rect(40, 100, 160, 36), "Increment", on_click=self._increment)
        root.add(self._label)
        root.add(btn)
        host.scene_controls.add(root)

    def bind_runtime(self, host):
        self._sub = self._count.subscribe(lambda v: self._label.set_text(f"Count: {v}"))
        bind_routed_feature_lifecycle(self, host, self._lifecycle_spec)

    def shutdown_runtime(self, host):
        if self._sub:
            self._sub()
            self._sub = None
        shutdown_routed_feature_lifecycle(self, host, self._lifecycle_spec)

    def _increment(self):
        self._count.value += 1


def build_reference_config():
    return build_host_application_config(
        HostApplicationBindingSpec(
            display_size=(1280, 720),
            window_title="E2E Reference Application",
            fonts={"default": {"file": "demo_features/data/fonts/Gimbot.ttf", "size": 14}},
            initial_scene_name="main",
            telemetry=TelemetryConfig(enabled=True),
            scene_bundle_entries=(
                SceneBundleBindingSpec(
                    scene_name="main",
                    pretty_name="Main",
                    transition_style=SceneTransitionStyle.SLIDE_RIGHT,
                    transition_duration=0.3,
                    bind_escape_to_exit=True,
                ),
            ),
            feature_entries=(("_counter", CounterFeature),),
            action_entries=(
                ActionSpec(action_id="help", label="Toggle Shortcut Help",
                           hotkey=ActionHotkeySpec(key="f9"), scene_name="main"),
                ActionSpec(action_id="increment", label="Increment Counter",
                           hotkey=ActionHotkeySpec(key="up"), scene_name="main"),
            ),
        )
    )


if __name__ == "__main__":
    configure_telemetry(enabled=True)
    config = build_reference_config()
    host = bootstrap_host_application(config)
    host.app.run_entrypoint(target_fps=120)
```

### What This Listing Demonstrates

- **Bootstrap**: `HostApplicationBindingSpec` + `build_host_application_config` + `bootstrap_host_application` — the full declarative startup path.
- **Feature lifecycle**: `RoutedFeature` with `build`, `bind_runtime`, `shutdown_runtime` — correct phase separation.
- **Reactive state**: `ObservableValue` wired to `LabelControl` via subscription in `bind_runtime`.
- **Routed runtime**: `RoutedRuntimeSpec` with `ShortcutOverlaySpec` — automatic shortcut overlay toggled with F9.
- **Routed lifecycle**: `RoutedFeatureLifecycleSpec` + `bind_routed_feature_lifecycle` / `shutdown_routed_feature_lifecycle` — single-call setup and teardown.
- **Actions**: `ActionSpec` entries for exit (via `bind_escape_to_exit`) and help — discoverable keyboard shortcuts.
- **Telemetry**: `TelemetryConfig(enabled=True)` in the binding spec; `configure_telemetry` enables collection before bootstrap.

### Validation Checklist

1. Application opens to the main scene with a "Count: 0" label and an "Increment" button.
2. Clicking "Increment" updates the label to "Count: 1", "Count: 2", etc.
3. Pressing the Up arrow key increments the counter (action hotkey).
4. Pressing F9 opens the shortcut help overlay showing both declared shortcuts.
5. Pressing F9 again (or Escape) dismisses the overlay.
6. Pressing Escape exits the application.
7. Telemetry records are populated after any interaction.

---

## Testing, Diagnostics, and Reliability

[Back to Table of Contents](#table-of-contents)

### Contract Tests

Contract tests validate behavioral guarantees that the framework must uphold regardless of implementation changes. They are the single most important signal that a change is safe to ship.

**Run the high-priority contract test suite with:**

```bash
python -m pytest -q \
  tests/test_public_api_exports.py \
  tests/test_public_api_docs_contracts.py \
  tests/test_runtime_operating_contracts.py \
  tests/test_boundary_contracts.py \
  tests/test_gui_application_workspace_contracts.py
```

What each test file covers:

- `test_public_api_exports.py` — verifies that every name in `gui_do.__all__` is importable and present. A failure here means the public API surface has a hole: a name was declared but not delivered. If you add a new type to `__all__`, add it to the source file first and confirm this test passes before merging.

- `test_public_api_docs_contracts.py` — verifies that API names in the public contract documentation match the names actually exported from `gui_do`. This test catches documentation drift: when a name is renamed or removed from the package but the docs still reference the old name.

- `test_runtime_operating_contracts.py` — verifies the runtime guarantees enumerated in `docs/runtime_operating_contracts.md`: canonical event normalization, scene-isolated update execution, deterministic focus candidate ordering, and scheduler dispatch budget clamping. This test must pass before any scheduler, event pipeline, or focus system change is considered stable.

- `test_boundary_contracts.py` — verifies the gui_do/demo_features boundary: demo code must not import from `gui_do` internal submodules (e.g., `gui_do.features.*`), and `gui_do` library code must not import from `demo_features`. A failure here means an architectural boundary has been violated and the offending import must be removed.

- `test_gui_application_workspace_contracts.py` — verifies workspace restore behavior: that `GuiApplication.restore_workspace` and `GuiApplication.load_workspace` return the expected restore report fields (`target_scene`, `switched_scene`, `restored_feature_states`, `restored_scene_nodes`, `applied_settings`, `skipped_settings`, `missing_settings_blocks`), that missing settings keys are skipped without aborting, and that workspace load/save failures do not abort shutdown sequencing.

---

### Runtime Behavior Tests

Beyond the contract tests above, behavioral tests target specific runtime subsystems. Areas where behavioral test coverage is most critical:

**Workspace load/save behavior.** Confirm that round-trip save/restore (write state → reload → verify) produces identical restore reports. Edge cases: missing keys land in `missing_settings_blocks`; unknown keys land in `skipped_settings`; scene switch happens only when `target_scene` differs from current scene.

**Overlay, tooltip, and cursor routing.** Confirm that toasts consume left-click by contract (no accidental click-through). Confirm tooltip show/hide is tied to pointer-enter/leave cycles with correct debouncing. Confirm cursor shape is restored correctly when cursor handles are released out of order.

**Layout and animation determinism.** Confirm that `ConstraintLayoutEngine` produces identical rects for identical constraint sets regardless of solve-order heuristics. Confirm that `AnimationStateMachine` transitions are deterministic given the same input sequence and frame durations.

**Control runtime.** Confirm that controls disposed during an event dispatch do not fire callbacks after disposal. Confirm that `ErrorBoundary` catches render exceptions without crashing the frame.

**Accessibility specs.** Confirm that `apply_accessibility_sequence` populates the `AccessibilityTree` with correct roles and live-region politeness. Confirm that hidden controls are excluded from the accessibility tree.

---

### Debug and Trace Tools

**`EventRecorder` / `EventPlayback`** — record a session of raw `GuiEvent` objects and replay them deterministically against the same application state. Use this to reproduce intermittent input bugs, confirm fix correctness, and build regression tests from real user session traces.

```python
from gui_do import EventRecorder, EventPlayback

recorder = EventRecorder()
recorder.start()
# ... run scenario ...
trace = recorder.stop()
trace.save("regression_trace.json")

# Later: replay
playback = EventPlayback.load("regression_trace.json")
playback.run(host)
```

**`DebugOverlay`** — renders control bounds, focus rings, dirty regions, and spatial index query results as visual overlays on the live scene. Enable in the feature's `draw` phase. Disable before release.

**`PropertyInspectorPanel`** — a built-in control that renders the live values of all `@ui_property`-decorated attributes on a target control or feature. Mount it in a developer window to inspect state at runtime without print statements.

**Telemetry log analysis** — after enabling telemetry (`configure_telemetry(enabled=True)`), run representative scenarios and analyze the collected spans:

```bash
python -c "
from gui_do import load_telemetry_log_file, analyze_telemetry_records, render_telemetry_report
records = load_telemetry_log_file('telemetry.log')
report = analyze_telemetry_records(records)
print(render_telemetry_report(report))
"
```

The report shows per-span p50/p95/max frame times and flags any span that exceeded the scheduler ceiling budget.

---

### Maintainer Release Runbook

The following sequence is required before every tagged release:

1. **Run the full test suite.** `python -m pytest -q` must produce zero failures. No exceptions.
2. **Run the contract tests explicitly.** Run the five contract test files listed in the Contract Tests section above. A passing full suite may still miss contract-specific regressions if the test discovery order is unusual.
3. **Verify MANUAL.md has no remaining placeholders.** `grep -r "MANUAL_PLACEHOLDER" MANUAL.md` must return no matches. If it does, the corresponding pipeline step was not completed.
4. **Verify the public API quick index (Appendix D) is complete.** Every name in `gui_do.__all__` must appear in exactly one topic group in Appendix D. Use `test_public_api_exports.py` as a proxy, but also visually scan for any names not yet categorized in the index.
5. **Re-run the telemetry baseline scenario.** Run `gui_do_demo.py` with telemetry enabled, perform the standard interaction sequence (start → increment counter → toggle shortcut overlay → navigate between scenes → exit), capture the report, and verify no span exceeds 4.0 ms.
6. **Run the E2E reference application.** Confirm all 7 validation checklist items from the End-to-End Reference Application section pass.
7. **Bump version in `gui_do/_version.py`** and update the changelog. Tag the release.

---

### Regression Triage Workflow

When a behavioral regression is reported, follow this sequence:

1. **Reproduce.** Confirm the regression is consistently reproducible with a minimal scenario. Use `EventRecorder` to capture a trace if it involves a specific input sequence.
2. **Trace.** Enable telemetry and replay the trace. Identify which span or system boundary is behaving differently.
3. **Localize.** Run the affected contract tests in isolation. Determine whether the regression is a contract violation (the framework is breaking a guarantee) or an application-level issue (the feature is using the API incorrectly).
4. **Test-first.** Write a failing test that specifically captures the regression. The test must fail on the current code and pass after the fix.
5. **Patch.** Fix the regression. Confirm the new test passes and no existing tests regress.
6. **Check adjacent contracts.** Run all five contract test files. Run any test file whose name references a related system. A layout regression may also affect focus, and a scheduling regression may affect animation — check both.

---

### Maintainer Diff Checklist

[Back to Table of Contents](#table-of-contents)

Use this checklist on every manual regeneration or update pass.

**Inventory delta checks:**

1. Compare current root exports in `gui_do/__init__.py` with Appendix D and D.1 entries. Every name in `__all__` must appear in the quick index; names removed from `__all__` must be removed from all examples and index entries.
2. Check `docs/` contracts for changed guarantees, policies, or boundary rules. Any change to `runtime_operating_contracts.md`, `public_api_spec.md`, `architecture_boundary_spec.md`, or `package_contracts.md` may require narrative updates in the corresponding system chapters.
3. Check `tests/` for new contract or runtime test modules. A new test file named `test_*_contracts.py` or `test_runtime_*` almost always implies a behavioral guarantee that should be documented.
4. Check `demo_features/` for new recommended composition patterns. If a new demo feature introduces a novel pattern, the Integration Patterns chapter and relevant system chapters should reflect it.

**Content integrity checks:**

1. Every changed system has updates in both its chapter narrative and in its quick-index references (Appendix D and D.1).
2. Removed APIs are deleted from examples, recipes, and all appendix index entries.
3. Added APIs are classified at the right abstraction level (Tier 1 first, then lower tiers).

**Navigation and structure checks:**

1. All newly added sections are present in the Table of Contents and their anchor links resolve correctly.
2. Every major section still contains a `[Back to Table of Contents](#table-of-contents)` link immediately below its heading.
3. Top-level chapter order remains stable unless an intentional restructure is explicitly noted.

**Operational checks:**

1. Re-run the high-priority contract tests before finalizing any update:
   ```bash
   python -m pytest -q tests/test_public_api_exports.py tests/test_public_api_docs_contracts.py tests/test_runtime_operating_contracts.py tests/test_boundary_contracts.py tests/test_gui_application_workspace_contracts.py
   ```
2. Validate end-to-end reference listing assumptions against current runtime behavior. If any API name in the E2E reference listing was renamed or removed, update the listing.
3. Record any unresolved ambiguities as explicit TODO notes in the Migration, Versioning, and Deprecation Notes section.

---

## Performance and Scaling Guidance

[Back to Table of Contents](#table-of-contents)

### Scheduler Budget Contract

The cooperative task scheduler dispatches queued messages from the feature update loop subject to a time budget derived from the actual frame delta. The contract values from `docs/runtime_operating_contracts.md` Section 6 are:

- **fraction**: 0.12 — the scheduler may consume at most 12% of the current frame's elapsed milliseconds
- **floor**: 0.5 ms — even if 12% of dt would be less than 0.5 ms, the scheduler is always allowed at least 0.5 ms
- **ceiling**: 4.0 ms — even if 12% of dt would be more than 4.0 ms, the scheduler is capped at 4.0 ms

This gives predictable upper bounds under slow frames (the scheduler cannot starve rendering) while ensuring progress under fast frames (there is always a minimum dispatch window). Features should not schedule work that itself takes longer than 4.0 ms per task; break long-running work into continuations that yield back to the scheduler.

### Dirty-Region Rendering

`DirtyRegionTracker` is the primary frame-rate optimization for scenes with complex backgrounds or expensive draw operations. Rather than redrawing the full surface every frame, features mark the screen regions that have actually changed and gate expensive draw calls with `overlaps_dirty(rect)`.

The tracker maintains a running union rect. `overlaps_dirty()` is therefore O(1) — it checks the region against the union in a single comparison, not against each individual dirty rect. This makes dirty-region gating safe to call in tight draw loops without per-rect overhead.

Use `mark_dirty(rect)` when data that affects a visual region changes, and `consume_dirty_regions()` at the start of each draw pass to get the set of regions requiring redraw. Combine with `OffscreenRenderTarget` to cache the expensive background and only redraw affected portions.

### Virtualization and Incremental Rendering

When a feature displays a large dataset (hundreds to thousands of rows), full control tree rendering becomes prohibitively expensive. Use the virtualization stack:

- `VirtualizationCore` and `VirtualizedWindow` — given the current scroll offset and viewport rect, compute exactly which item indices are visible and delegate rendering only to those items.
- `RecyclePool` — when items scroll out of view, their view objects are returned to a typed pool and re-acquired for newly visible items, avoiding per-item allocation.
- `ListDiffCalculator` — when a data source refreshes, compute the minimal diff (inserts, removes, moves) between the old and new lists and apply incremental patches, rather than destroying and rebuilding the entire item tree.

### Practical Scaling Checklist

Before declaring performance acceptable, verify:

- [ ] Scene-scoped updates: every `on_update` handler does work only for its own scene's active features; no global per-frame iteration over all controls or features in inactive scenes.
- [ ] Avoid per-frame full collection reallocation: use `ObjectPool` for high-churn objects (particles, list items, event records) to avoid repeated GC pressure.
- [ ] Debounce expensive form and search operations: wrap expensive filtering or validation with `Debouncer` so they fire at most once per debounce window, not on every keystroke.
- [ ] Preemptible background work: use `DataflowPipeline` + `CancellationToken` for any operation that may become stale before it completes (search, data load, ranking).
- [ ] Profile representative interactions: idle-loop telemetry is flat and misleading. Measure under realistic load: many controls visible, transitions firing, data pipelines running, overlays open.
- [ ] Gate expensive draw regions: use `DirtyRegionTracker` to skip redraws in regions that haven't changed. A canvas-heavy scene with a dirty region gate can reduce draw CPU by 80% or more.

---

## Migration, Versioning, and Deprecation Notes

[Back to Table of Contents](#table-of-contents)

### Versioned Snapshot Strategy

The recommended persistence strategy uses `VersionedSnapshot` to stamp every saved state with a schema version, and `SnapshotMigrator` to transform stale snapshots forward to the current schema automatically on load. The full workflow:

1. **Write.** Call `make_snapshot(current_version, state_dict)` to produce a `VersionedSnapshot`. Serialize it to disk (JSON or pickle). `SchemaVersion` is a string (e.g., `"2.0"`) that you define and control.

2. **Read.** On load, read raw bytes and call `read_version(raw)` to extract the stored version without fully deserializing. Compare against the current expected version.

3. **Migrate.** If the stored version is older, pass the snapshot to `SnapshotMigrator.migrate(snapshot)`. The migrator applies registered `MigrationStep` objects in BFS order to produce a snapshot at the current schema version. Each `MigrationStep` knows its `from_version` and `to_version`. `MigrationRegistry` holds the graph of all registered steps.

4. **Restore.** Pass the migrated `VersionedSnapshot.data` to the `AppStateStore` or `WorkspacePersistenceManager` restore method.

```python
from gui_do import (
    make_snapshot, read_version, SnapshotMigrator, MigrationRegistry, MigrationStep,
    SchemaVersion, VersionedSnapshot,
)

# Define migration from v1.0 to v2.0:
def migrate_1_to_2(data: dict) -> dict:
    data["new_field"] = data.pop("old_field", None)
    return data

registry = MigrationRegistry()
registry.register(MigrationStep(from_version="1.0", to_version="2.0", migrate_fn=migrate_1_to_2))
migrator = SnapshotMigrator(registry, target_version="2.0")

# On load:
raw = load_bytes_from_disk()
version = read_version(raw)
if version != "2.0":
    snapshot = migrator.migrate(raw)
else:
    snapshot = VersionedSnapshot.from_raw(raw)
store.restore(snapshot.data)
```

If no migration path exists from the stored version to the current version, `SnapshotMigrator.migrate` raises `MigrationError`. Catch this at startup and offer the user a choice: start fresh, or keep the old file as a backup.

### Deprecation Handling

The recommended policy for deprecating public API:

- **Prefer additive transitions.** Add new parameters with defaults; keep old parameters accepting their old types. Add a `DeprecationWarning` via Python's `warnings` module to any code path that uses the old calling convention.
- **Remove legacy behavior only after a migration path is available.** Document the migration path in this section before removing the old behavior.
- **One version minimum.** Deprecated behavior should remain functional (with a warning) for at least one released version before removal.
#### Scene with all three facilities: command palette, scene menu, and task panel with window toggles

```python
import pygame
from gui_do import (
    RoutedRuntimeSpec, SceneCommandPaletteSpec, SceneMenuStripSpec,
    SceneTaskPanelSpec, TaskPanelButtonSpec, TaskPanelWindowToggleGroupSpec,
    add_task_panel_buttons, add_task_panel_window_toggle_group,
    add_scene_menu_strip_from_spec, ensure_scene_task_panel,
    setup_routed_runtime,
)

MY_RUNTIME_SPEC = RoutedRuntimeSpec(
    scene_name="main",
    command_palette=SceneCommandPaletteSpec(
        key=pygame.K_F5,
        scene_name="main",
    ),
    # task_panel_focus_toggles=(...),  # optional
)

# In the feature's build(self, host) method:
host.desktop_menu_bar = add_scene_menu_strip_from_spec(
    host.root,
    host,
    SceneMenuStripSpec(
        control_id="menu_bar",
        rect=Rect(0, 0, width, 28),
        scene_name="main",
        scenes_shown=True,    # optional: include Scene navigation menu
        windows_shown=True,   # optional: include Windows menu with visibility toggles
        on_window_toggled=host.window_presentation.handle_window_toggle,
    ),
)
host.task_panel = ensure_scene_task_panel(
    host,
    SceneTaskPanelSpec(scene_name="main", control_id="task_panel", ...),
)
add_task_panel_buttons(host, host.task_panel, host.app.layout, [
    TaskPanelButtonSpec(attr_name="exit_button", slot_index=0, label="Exit", on_click=host.app.quit, ...),
])
# Window toggles declared as a group starting at slot 1.  Individual windows
# declare their absolute slot_index in their FeatureWindowBundleBindingSpec.
toggle_controls = add_task_panel_window_toggle_group(
    host, host.task_panel, host.app.layout, host.window_presentation,
    TaskPanelWindowToggleGroupSpec(start_index=1),
)

# In the feature's bind_runtime(self, host) method:
setup_routed_runtime(self, host, MY_RUNTIME_SPEC)
```


→ 8.1 Bootstrap (SceneBundleBindingSpec, FeatureWindowBundleBindingSpec) | 8.2 Feature Lifecycle (build and bind_runtime) | 8.3 Events and Actions (global key routing, bind_global_key) | 8.5 Controls (WindowControl, TaskPanelControl, WindowPresenter) | 8.7 Focus (TaskPanelFocusToggleSpec) | 8.8 Overlays (command palette overlay, overlay intercept layer)
As of the current generation, no public API names in `gui_do` are formally deprecated. Maintainers should add entries to this section whenever a formal deprecation is introduced, including: the deprecated name, the replacement name or approach, the version in which the deprecation was introduced, and the planned removal version.

### Upgrade Checklist

When upgrading `gui_do` across minor or major versions:

- [ ] Run all contract tests before the upgrade: `python -m pytest -q tests/test_public_api_exports.py tests/test_public_api_docs_contracts.py tests/test_runtime_operating_contracts.py tests/test_boundary_contracts.py tests/test_gui_application_workspace_contracts.py`
- [ ] Run the same contract tests after the upgrade and diff any new failures.
- [ ] Verify root import usage: all application code uses `from gui_do import ...` and does not import from internal submodules.
- [ ] Check action/input/focus routing behavior in active scenes after the upgrade; routing behavior can be affected by changes to `ActionManager`, `FocusManager`, or `InputMap` ordering.
- [ ] Validate workspace restore: load an existing workspace state file and confirm the restore report shows no unexpected `skipped_settings` or `missing_settings_blocks`.
- [ ] Re-run the telemetry baseline scenario and compare to the previous baseline. A scheduler budget change, event pipeline change, or layout pass change can affect frame budget consumption.

---

## FAQ and Troubleshooting

[Back to Table of Contents](#table-of-contents)

**Q: Should I build apps directly with controls or with features?**

Use features as the architectural unit. Controls are implementation details inside feature boundaries. A feature provides lifecycle orchestration (build, bind_runtime, shutdown_runtime), event routing, observable subscription wiring, and clean teardown. A control alone can do none of these things — it has no lifecycle hooks, no subscription management, and no awareness of scene or window scope. Every application-level behavior should live in a feature. Controls are the leaf nodes that the feature composes.

---

**Q: When should I use `RoutedFeature` over `Feature`?**

Use `RoutedFeature` when you need topic-based message dispatch and declarative runtime wiring — hotkeys, shortcut overlays, task-panel focus toggles, event subscriptions — from a single spec (`RoutedRuntimeSpec`). The routed lifecycle (`bind_routed_feature_lifecycle` / `shutdown_routed_feature_lifecycle`) sets all of this up and tears it down in one call, eliminating scattered registration and deregistration code. If your feature only needs `build`, `bind_runtime`, `shutdown_runtime`, and a control tree with no declarative wiring, plain `Feature` is sufficient and simpler.

---

**Q: Why are some key handlers not firing?**

Check in order: (1) **Focus ownership** — is a `TextInputControl` or other keyboard-capturing control holding focus? Key events go to the focused control first; if the control handles the key, routing stops. (2) **Window scope** — is the action registered in a window scope but that window is currently hidden? Actions scoped to a hidden window are not reachable. (3) **Overlay modal capture** — is a modal dialog or command palette open? Overlay managers consume unhandled keys to prevent accidental background actions. (4) **Scene scope** — is the action registered for a scene that is not the current scene? Action routing is scene-scoped by contract. Use `EventRecorder` to trace the exact event routing path and identify where propagation is stopped.

---

**Q: Why do toast clicks not pass through?**

By contract, the bounds of an active toast consume left-click events to prevent accidental activation of controls beneath the toast notification. This is a deliberate safety rail, not a bug. If you need an intentional action triggered by clicking a toast, use the `on_click` callback in the `ToastManager.show(...)` API call.

---

**Q: How do I avoid breaking workspace restore across versions?**

Use `VersionedSnapshot` with `SchemaVersion`; register `MigrationStep` objects in a `MigrationRegistry` for every schema-level field addition or removal; and inspect the restore report after every save/load cycle. The restore report's `skipped_settings` list tells you which saved keys had no matching handler in the current runtime; `missing_settings_blocks` tells you which expected blocks were absent from the saved file. Handle both gracefully — for example, by logging a warning or showing a toast notification — rather than crashing.

---

**Q: How do I confirm my API usage is within the supported surface?**

Use explicit named imports from the `gui_do` root — `from gui_do import Feature, ButtonControl, ObservableValue` — never from internal submodules like `gui_do.features.feature_lifecycle`. Run `tests/test_public_api_exports.py` to confirm every name you use appears in `gui_do.__all__`. If a name is not in `__all__`, it is an internal implementation detail and may change or be removed without notice. Appendix D provides a complete topic-organized index of the supported public surface.

---

**Q: Why does my feature's `bind_runtime` run before my sibling's `build`?**

It does not. The framework guarantees that all features registered in a scene complete their `build(host)` phase before any feature's `bind_runtime(host)` is called. This ordering guarantee means features can depend on the existence of shared host attributes set up during any sibling's `build` phase when writing their own `bind_runtime`. If you observe an apparent ordering issue, confirm that both features are declared in the same scene's `FeatureSpec` entries, and that neither feature is dynamically added to the scene after the initial build pass.

---

**Q: How do I add a keyboard shortcut without touching every handler?**

Declare an `ActionSpec` in `HostApplicationBindingSpec` with an `ActionHotkeySpec` naming the key. The framework registers it with `ActionManager` and `InputMap` automatically during bootstrap. In a `RoutedFeature`, include a `RoutedRuntimeSpec` with the action name to receive it as a message. Include it in a `ShortcutOverlaySpec` to make it discoverable via the help overlay. No manual per-handler wiring needed.

---

## Appendix

[Back to Table of Contents](#table-of-contents)

### Appendix A: Glossary

**Feature** — the primary lifecycle-managed unit of application behavior in `gui_do`. A feature owns a region of the control tree, manages its own subscriptions, and participates in the framework's ordered lifecycle phases: `build`, `bind_runtime`, `on_update`, `handle_event`, `draw`, and `shutdown_runtime`. Four concrete types are provided: `DirectFeature` (full control over all phases), `Feature` (standard declarative pattern), `LogicFeature` (logic-only, no drawing), and `RoutedFeature` (adds topic-based message dispatch and declarative wiring specs). Applications should think in terms of features as their architectural unit, not individual controls.

**Spec** — a declarative Python dataclass describing runtime wiring requirements. Specs are pure data — they do not execute, they do not depend on runtime state, and they can be constructed before `bootstrap_host_application` is called. The framework reads specs during bootstrap to set up action routing, window presentation, task-panel bindings, accessibility sequences, and more. Writing specs instead of imperative wiring code makes the relationship between configuration and runtime behavior explicit and auditable.

**Host** — a plain Python namespace object passed to every feature lifecycle method. `bootstrap_host_application` populates it with runtime members — `host.app`, `host.screen_rect`, `host.scene_controls`, `host.overlays`, `host.toasts`, `host.sound_bus`, and others — that features may use to interact with the framework. Features declare their host dependencies in `HOST_REQUIREMENTS` so the framework can validate and provide the correct members per lifecycle phase.

**Scene** — a top-level interaction context that groups features, controls, and routing rules. Features belong to exactly one scene. Scene transitions coordinate shutdown and startup of the departing and arriving feature sets. Actions and key bindings are scene-scoped by default; an action registered in scene "A" is not reachable when scene "B" is active. `SceneTransitionManager` orchestrates transitions with optional animation.

**Window presentation** — the model by which floating tool windows or inspector panels are shown, hidden, and focused within a scene. A window has a visibility state, a focus-ring scope, and optionally a task-panel toggle button. `WindowPresenter` builds the window's control tree; `set_window_visible_state` toggles visibility; `TaskPanelFocusToggleSpec` excludes hidden window controls from tab-cycle.

**Routed runtime** — a declarative bundle of hotkeys, shortcut overlay specs, event subscriptions, and task-panel focus toggles that is attached to a `RoutedFeature` via `RoutedRuntimeSpec` and `RoutedFeatureLifecycleSpec`. `bind_routed_feature_lifecycle` activates all declared bindings in one call; `shutdown_routed_feature_lifecycle` tears them all down. This eliminates scattered setup and cleanup code across `bind_runtime` and `shutdown_runtime`.

**Observable** — a value that automatically notifies subscribers when it changes. `ObservableValue` is the primary type. `subscribe(callback)` returns an unsubscribe function that must be called in `shutdown_runtime` to avoid memory leaks. `ComputedValue` derives from one or more observables using a function. `ObservableList` and `ObservableDict` extend the pattern to collections.

**Workspace state** — the persisted runtime context that enables session restore: current scene, active feature states, scene node snapshots, and registered settings. `WorkspacePersistenceManager` saves and restores workspace state. The restore report (`target_scene`, `switched_scene`, `restored_feature_states`, `restored_scene_nodes`, `applied_settings`, `skipped_settings`, `missing_settings_blocks`) describes exactly what was and was not restored.

**Contract test** — an automated test that verifies a behavioral guarantee rather than an implementation detail. Contract tests in `tests/test_*_contracts.py` and `tests/test_runtime_*` files enforce guarantees from `docs/runtime_operating_contracts.md`, `docs/public_api_spec.md`, `docs/architecture_boundary_spec.md`, and `docs/package_contracts.md`. Adding a new behavioral guarantee without a corresponding contract test is an incomplete change.

**Tier** — a grouping of public API exports in `gui_do/__init__.py` by abstraction level and recommended usage priority. Tier 1 contains the highest-level recommended entry points; Tier 18 contains extension helpers for advanced bootstrap customization; Tier 19 is internal infrastructure to avoid in application code. Tiers are informational — they help developers find the right level of API for their problem without reading the full source. See Appendix D.1 for the full tier-to-system reference matrix.

---

### Appendix B: Lifecycle and Event Routing Sequence

The following numbered reference describes the complete application lifecycle from bootstrap to exit:

1. **Bootstrap.** `bootstrap_host_application(config)` initializes the host from `HostApplicationConfig`. Spec processing runs: fonts are loaded, scenes are registered, action routing tables are built, accessibility sequences are applied, windows are declared, task-panel buttons are registered, tooltip specs are registered.

2. **Feature build.** All features registered in the initial scene have their `build(host)` method called in declaration order. All build calls for the scene complete before any `bind_runtime` call begins.

3. **Feature bind_runtime.** All features in the scene have their `bind_runtime(host)` method called. Features subscribe to observables, bind actions, register routed lifecycles, and complete any initialization that depends on sibling features having run `build`.

4. **Runtime loop begins.** `host.app.run_entrypoint(target_fps=N)` starts the frame loop at the target frame rate.

5. **Event normalization.** Each frame, raw `pygame` events are normalized to `GuiEvent` objects with canonical `EventType`, `EventPhase`, and spatial coordinates. `GuiEvent.clone()` is available for independent copies that do not share propagation state.

6. **Event routing pass.** Overlay, focus, window, and scene routing runs in order: overlay managers receive first opportunity to handle or consume events; focused controls in the active window receive keyboard events next; scene-scope routing runs last.

7. **Feature `handle_event` calls.** Features receive `handle_event(event, host)` in routing order. A feature may stop propagation by calling `event.stop_propagation()`.

8. **Feature `on_update` calls.** Each feature's `on_update(dt, host)` runs. The cooperative scheduler dispatches queued tasks within the budget window (fraction=0.12, floor=0.5 ms, ceiling=4.0 ms).

9. **Feature `draw` calls.** Each feature's `draw(host, screen)` runs. The control tree renders its full tree. `DirtyRegionTracker` regions gate expensive background draws. The frame is presented to the display.

10. **Scene transition.** When a scene transition is triggered: `shutdown_runtime` is called for all departing features; the transition animation runs (if any); `build` + `bind_runtime` are called for all arriving features in declaration order.

11. **Application exit.** On the exit event (Escape with `bind_escape_to_exit=True`, or an explicit exit action): `shutdown_runtime` is called for all active features; workspace state is saved via `WorkspacePersistenceManager`; pygame is quit. `run_entrypoint` exits with code 0 on clean exit, non-zero on runtime loop failure.

---

### Appendix C: System Dependency Map

Bootstrap (Tier 1) depends on virtually all other tiers: it reads spec objects to build action routing tables (Tier 4), initialize font and theme systems (Tier 6), set up persistence paths (Tier 11), wire window presentation (Tier 13), configure telemetry (Tier 7), and populate the locale registry (Tier 14). It is the integration seam — changes to any tier's bootstrap-facing API require corresponding changes to the Tier 1 spec types.

Features (Tiers 1–2) depend on controls (Tiers 12–13), data/observables (Tier 3), event and action systems (Tier 4), and scheduling (Tier 5). A feature is essentially a coordinator: it holds references to these subsystems but is not directly implemented by any of them.

Layout (Tier 8) and focus (Tier 4) depend on the control tree and scene/window visibility. Layout runs before rendering; focus management is updated when layout changes or window visibility changes. The constraint layout engine (Tier 28) is a higher-level extension of the base layout system.

Overlays (Tier 9) depend on event routing (Tier 4) and focus policy. Modal overlays must capture focus and suppress key events to background content; this is coordinated through `FocusScope` and `OverlayManager`.

Persistence (Tiers 11 and 32) depends on state models and scene/window registration. `WorkspacePersistenceManager` reads from `SceneSnapshot` and `NodeSnapshot` objects; `SnapshotMigrator` transforms `VersionedSnapshot` objects through registered migration steps. Both are independent of the rendering pipeline.

Scheduling (Tier 5) and animation depend on the feature update loop and scene scope. `CooperativeScheduler` is driven from `on_update`; `TweenManager` and `AnimationStateMachine` register callbacks that also fire during the update phase. Scene-scoped timers are automatically cancelled when the scene becomes inactive.

Telemetry and introspection (Tiers 7 and 17) cross-cut all runtime layers. Telemetry spans are recorded in the scheduler, event pipeline, layout pass, and draw phase. `SceneSpatialIndex` queries the live control tree geometry, so it depends on layout having completed for the current frame.

Audio (Tier 20) depends on `pygame.mixer` and surfaces through `SoundEventBus`. It is intentionally isolated from all other GUI systems so it can be enabled/disabled independently. Features interact with it only through `SoundCue` events on the bus.

Service scope (Tier 25) can be used at any tier as a hierarchical dependency injection container. It has no runtime dependencies of its own — it is pure Python bookkeeping. Features that need to share services across a scene can use a `ServiceScope` attached to the host.

---

### Appendix D: API Quick Index by Topic

This index organizes every name in `gui_do.__all__` by topic. Use it to find the right type for a given task without reading the full source.

**Bootstrap and Configuration**

`HostApplicationBindingSpec`, `HostApplicationConfig`, `TelemetryConfig`, `build_host_application_config`, `bootstrap_host_application`, `SceneBundleBindingSpec`, `RuntimeSceneBindingSpec`, `SceneSetupBindingSpec`, `FeatureSpec`, `WindowSpec`, `RuntimeSceneSpec`, `SceneSetupSpec`, `SceneRootBindingSpec`, `SceneRootSpec`, `CursorBindingSpec`, `CursorSpec`, `FontRoleBindingSpec`, `ActionBindingSpec`, `PaletteBindingSpec`, `build_feature_specs`, `build_feature_window_bundle_specs`, `build_window_toggle_specs`, `build_scene_setup_specs`, `build_runtime_scene_specs`, `build_scene_root_specs`, `build_cursor_specs`, `build_font_role_specs`, `build_scene_nav_actions`, `build_action_specs`, `build_scene_bundle_specs`, `build_static_accessibility_specs`, `build_host_application_config`, `build_notification_center`, `ControlDefinition`, `build_specs_from_column_section`

**Features and Lifecycle**

`Feature`, `DirectFeature`, `LogicFeature`, `RoutedFeature`, `FeatureMessage`, `FeatureManager`, `ScenePresentationModel`, `setup_standard_font_roles`, `apply_scene_setup_specs`

**Routed Runtime and Wiring Specs**

`RoutedRuntimeSpec`, `RoutedFeatureLifecycleSpec`, `ShortcutOverlaySpec`, `TaskPanelFocusToggleSpec`, `FeatureWindowBundleBindingSpec`, `WindowToggleBindingSpec`, `LogicBindingSpec`, `EventSubscriptionSpec`, `SceneTaskPanelSpec`, `SceneReturnButtonSpec`, `TaskPanelButtonSpec`, `TabbedPresenterSpec`, `AccessibilitySequenceSpec`, `TabBuilderSpec`, `NotificationSpec`, `AnchoredWindowSpec`, `ActionHotkeySpec`, `ControlKeyBindingSpec`, `StaticAccessibilitySpec`, `make_window_toggle_spec`, `make_scene_nav_action`, `make_exit_action`, `make_palette_open_action`, `make_static_accessibility_spec`

**Application Runtime**

`GuiApplication`, `create_display`, `SceneTransitionManager`, `SceneTransitionStyle`

**State and Observables**

`ObservableValue`, `PresentationModel`, `ComputedValue`, `reactive_batch`, `is_batching`, `InvalidationTracker`, `ChangeKind`, `CollectionChange`, `ObservableList`, `ObservableDict`, `CollectionViewQuery`, `CollectionView`, `Binding`, `BindingGroup`, `ObservableStream`, `SelectionModel`, `SelectionMode`

**Events, Input, and Gestures**

`GuiEvent`, `EventType`, `EventPhase`, `EventManager`, `EventBus`, `GestureRecognizer`, `EventRecorder`, `EventPlayback`, `RecordedEvent`, `InputSnapshot`, `Signal`, `SignalConnection`, `ValueChangeCallback`, `ValueChangeReason`

**Actions and Input Mapping**

`ActionManager`, `ActionContext`, `ActionMiddleware`, `ActionDescriptor`, `ActionRegistry`, `InputMap`, `InputBinding`, `KeyChordManager`, `KeyChord`, `ChordStep`

**Focus Management**

`FocusManager`, `FocusScope`, `FocusScopeManager`, `WindowFocusManager`, `FocusRing`

**Scheduling and Timers**

`TaskScheduler`, `TaskEvent`, `Timers`, `TweenManager`, `TweenHandle`, `Easing`, `AnimationSequence`, `AnimationHandle`, `TransitionManager`, `TransitionSpec`, `TransitionEvent`, `AnimationStateMachine`, `AnimationTransitionMode`, `SceneTimeline`, `Debouncer`, `Throttler`, `CooperativeScheduler`, `CoroutineHandle`, `Pause`, `Sleep`, `WaitForEvent`, `WaitForSignal`, `WaitUntil`, `WaitForAll`

**Theme, Fonts, and Design Tokens**

`FontManager`, `FontRoleRegistry`, `ColorTheme`, `ThemeManager`, `DesignTokens`, `ScopedTheme`, `ScopedThemeManager`, `ThemeInvalidationBus`

**Telemetry and Diagnostics**

`TelemetryCollector`, `TelemetrySample`, `configure_telemetry`, `telemetry_collector`, `analyze_telemetry_log_file`, `analyze_telemetry_records`, `load_telemetry_log_file`, `render_telemetry_report`

**Layout and Spatial**

`LayoutAxis`, `LayoutManager`, `WindowTilingManager`, `ConstraintLayout`, `AnchorConstraint`, `DockPane`, `DockTabs`, `DockSplit`, `DockWorkspace`, `FlexLayout`, `FlexItem`, `FlexDirection`, `FlexAlign`, `FlexJustify`, `GridLayout`, `GridTrack`, `GridPlacement`, `CellCaretLayout`, `CellCaretState`, `LayoutAnimator`, `LayoutPass`, `MeasureContext`, `ArrangeContext`, `LayoutRoot`, `ResponsiveLayout`, `Breakpoint`, `SnapGrid`, `AlignmentGuide`, `SnapComposer`, `SnapTarget`, `FlowLayout`, `FlowItem`, `Viewport`

**Adaptive Constraint Layout**

`ConstraintAttr`, `LayoutConstraint`, `ConstraintSet`, `ConstraintLayoutEngine`, `AdaptivePolicy`, `resolve_adaptive_policy`

**Overlays, Dialogs, and Menus**

`OverlayManager`, `OverlayHandle`, `Alignment`, `PlacementResult`, `PopupPlacement`, `Side`, `compute_popup_rect`, `DialogManager`, `DialogHandle`, `ToastManager`, `ToastHandle`, `ToastSeverity`, `ContextMenuManager`, `ContextMenuItem`, `ContextMenuHandle`, `CommandPaletteManager`, `CommandEntry`, `CommandPaletteHandle`, `TooltipManager`, `TooltipHandle`, `MenuBarManager`, `FileDialogManager`, `FileDialogOptions`, `FileDialogHandle`, `NotificationCenter`, `NotificationRecord`, `ResizeManager`, `CursorManager`, `CursorHandle`, `CursorShape`, `DragDropManager`, `DragPayload`, `ClipboardManager`, `TransferData`, `TransferManager`, `ShortcutHelpOverlay`, `ShortcutSection`, `ShortcutEntry`

**Forms and Validation**

`FormModel`, `FormField`, `ValidationRule`, `FieldError`, `FormSchema`, `SchemaField`, `DocumentModel`, `WizardFlow`, `WizardStep`, `WizardHandle`, `ValidationResult`, `Validator`, `RequiredValidator`, `RangeValidator`, `LengthValidator`, `PatternValidator`, `CustomValidator`, `DependentValidator`, `ValidationPipeline`, `AsyncFieldValidator`, `AsyncFormValidator`, `FieldSchema`, `FieldGraphSchema`, `ValidationPolicy`, `SchemaFormRuntime`

**State and Persistence**

`CommandHistory`, `Command`, `CommandTransaction`, `StateMachine`, `HierarchicalStateMachine`, `Router`, `RouteEntry`, `SettingsRegistry`, `SettingDescriptor`, `WorkspaceState`, `WorkspacePersistenceManager`, `DEFAULT_WORKSPACE_STATE_PATH`, `SceneSnapshot`, `NodeSnapshot`, `UndoContextManager`

**Transactional App State Store**

`AppStateStore`, `StateSelector`, `StateTransaction`

**Versioned Snapshot and Migration**

`SchemaVersion`, `VersionedSnapshot`, `MigrationStep`, `MigrationRegistry`, `SnapshotMigrator`, `MigrationError`, `make_snapshot`, `read_version`

**Primary Controls**

`PanelControl`, `LabelControl`, `ButtonControl`, `ToggleControl`, `SliderControl`, `ScrollbarControl`, `CanvasControl`, `CanvasEventPacket`, `CanvasViewport`, `FrameControl`, `ImageControl`, `ArrowBoxControl`, `ButtonGroupControl`, `TabControl`, `TabItem`, `DockWorkspacePanel`

**Extended Controls**

`TextInputControl`, `TextAreaControl`, `RichLabelControl`, `DropdownControl`, `DropdownOption`, `ListViewControl`, `ListItem`, `OverlayPanelControl`, `DataGridControl`, `GridColumn`, `GridRow`, `TreeControl`, `TreeNode`, `SplitterControl`, `SpinnerControl`, `RangeSliderControl`, `ColorPickerControl`, `ScrollViewControl`, `ProgressBarControl`, `AnimatedImageControl`, `ErrorBoundary`, `WindowControl`, `TaskPanelControl`, `WindowPresenter`, `MenuBarControl`, `MenuEntry`, `SceneMenuStripControl`, `NotificationPanelControl`, `PropertyInspectorPanel`, `ToolbarControl`, `ToolbarItem`, `StatusBarControl`, `StatusSlot`, `ExpanderControl`, `DatePickerControl`, `TimePickerControl`, `BreadcrumbControl`, `BreadcrumbItem`, `SplitButtonControl`, `SplitButtonOption`, `ChipInputControl`

**Text and Localization**

`TextFormatter`, `NumericFormatter`, `PatternFormatter`, `FixedPatternFormatter`, `TextFlow`, `TextSpan`, `TextSearcher`, `TextMatch`, `StringTable`, `LocaleRegistry`

**Data and Collections**

`VirtualItemSource`, `FixedItemSource`, `SortFilterProxySource`, `AsyncDataProvider`, `LoadState`, `LoadStateKind`, `ObjectPool`, `DataCache`, `CacheStats`, `ListDiffCalculator`, `ListDiff`, `DiffInsert`, `DiffRemove`, `DiffMove`

**Dataflow Pipeline**

`CancellationToken`, `PipelineStage`, `DataflowPipeline`, `PipelineHandle`

**Virtualization**

`MeasureMode`, `MeasurePolicy`, `VirtualizedWindow`, `RecyclePool`, `VirtualizationCore`

**Graphics and Rendering**

`BuiltInGraphicsFactory`, `DirtyRegionTracker`, `DrawContext`, `DrawPhase`, `AssetRegistry`, `DebugOverlay`, `SurfaceCompositor`, `Layer`, `ShapeRenderer`, `SurfaceEffects`, `VectorPath`, `SpriteSheet`, `FrameAnimation`, `ParticleSystem`, `Emitter`, `ParticleLayer`, `TileSet`, `TileMap`, `RenderTarget`, `LiveRenderTarget`, `OffscreenRenderTarget`, `create_render_target`, `create_surface`, `Node2D`, `SceneGraph2D`, `Camera2D`

**Audio**

`SoundCue`, `SoundBankRegistry`, `SoundEventBus`

**Accessibility**

`AccessibilityRole`, `LivePoliteness`, `AccessibilityNode`, `AccessibilityTree`, `AccessibilityAnnouncement`, `AccessibilityBus`

**Introspection and Inspection**

`SceneSpatialIndex`, `ui_property`, `PropertyDescriptor`, `PropertyRegistry`, `property_registry`, `PropertyInspectorModel`, `InspectedProperty`

**Service Scope**

`ServiceKey`, `ServiceScope`, `ScopeStack`

**Interaction State Machine**

`InteractionPhase`, `InteractionContext`, `InteractionTransition`, `InteractionStateMachine`

**Advanced Bootstrap Helpers (Tier 18)**

`FrameTimer`, `TabPanelManager`, `WindowRelativeRect`, `resolve_scene_selection_callback`, `minimize_window_menu_entries`, `set_window_visible_state`, `toggle_window_visibility`, `create_anchored_feature_window`, `add_window_scene_menu_strip`, `inset_rect`, `centered_horizontal_strip_layout`, `split_slot_bounds`, `partition_rects`, `place_control`, `place_control_unlabeled`, `register_placed_control`, `add_group_label`, `PlacedControl`, `make_labeled_slot_height_fn`, `ControlRegistry`, `build_tools_menu_entries`, `add_standard_scene_menu_strip`, `apply_accessibility_sequence`, `apply_accessibility_sequence_from_attrs`, `register_companion_logic_features`, `ensure_scene_scheduler`, `sorted_window_bindings`, `collect_window_toggle_controls`, `apply_window_toggle_accessibility`, `add_window_toggle_task_panel_controls`, `register_window_toggle_tooltips`, `initialize_locale_registry`, `bind_input_map_actions`, `register_descriptors`, `resolve_canvas_local_point`, `apply_runtime_scene_pristine_assets`, `bind_runtime_scene_exit_keys`, `prewarm_runtime_scenes`, `add_task_panel_button`, `add_task_panel_buttons`, `register_tooltip_specs`, `register_action_hotkeys`, `draw_controls_prewarm`, `ensure_scene_task_panel`, `add_scene_return_button`, `centered_overlay_rect`, `create_shortcut_help_overlay`, `bind_feature_event_subscription`, `unbind_feature_event_subscription`, `setup_routed_runtime`, `shutdown_routed_runtime`, `bind_task_panel_focus_toggle`, `add_window_control`, `add_window_label`, `add_window_button`, `add_window_button_row`, `instantiate_features_from_specs`, `register_features_from_specs`, `register_window_presentation_specs`, `register_window_tab_builders`, `build_tab_builder_specs`, `create_tab_control_from_specs`, `compute_tabbed_window_layout`, `setup_feature_presenter_tabs_from_window_content`, `register_window_tab_builder_specs`, `setup_feature_presenter_tabs`, `register_tab_update_handlers`, `create_presented_anchored_window`, `create_presented_window_from_spec`, `create_feature_presented_window`, `bind_feature_logic_aliases`, `setup_routed_feature_runtime`, `register_routed_feature_companions`, `bind_routed_feature_lifecycle`, `shutdown_routed_feature_lifecycle`, `ActiveTabUpdateRouter`, `TabLayoutContext`, `declare_host_actions`, `build_host_main_tab_order`, `apply_host_main_accessibility`

**Infrastructure (Avoid in Application Code)**

`UiEngine`

---

### Appendix D.1: Tier-to-System Reference Matrix

| Tier | System | Representative Key Types |
|------|--------|--------------------------|
| 1 | Primary Entry Points & Data-Driven APIs | `HostApplicationBindingSpec`, `bootstrap_host_application`, `RoutedFeature`, `SceneBundleBindingSpec` |
| 2 | Core Application & Scene Management | `GuiApplication`, `create_display`, `SceneTransitionManager`, `SceneTransitionStyle` |
| 3 | Essential Data & State Management | `ObservableValue`, `ComputedValue`, `ObservableList`, `CollectionView`, `Binding` |
| 4 | Events, Actions, Focus & Input | `GuiEvent`, `ActionManager`, `InputMap`, `FocusManager`, `EventRecorder` |
| 5 | Scheduling & Animation | `TaskScheduler`, `TweenManager`, `CooperativeScheduler`, `AnimationStateMachine`, `Debouncer` |
| 6 | Theme & Font Management | `FontManager`, `ThemeManager`, `ColorTheme`, `DesignTokens`, `ScopedTheme` |
| 7 | Telemetry & Diagnostics | `TelemetryCollector`, `configure_telemetry`, `analyze_telemetry_records`, `render_telemetry_report` |
| 8 | Layout & Spatial | `LayoutManager`, `FlexLayout`, `GridLayout`, `ConstraintLayout`, `Viewport` |
| 9 | Overlay Managers & Windows | `OverlayManager`, `DialogManager`, `ToastManager`, `TooltipManager`, `DragDropManager` |
| 10 | Forms & Data Binding | `FormModel`, `FormField`, `ValidationPipeline`, `WizardFlow`, `DocumentModel` |
| 11 | State & Persistence | `CommandHistory`, `StateMachine`, `WorkspacePersistenceManager`, `SettingsRegistry`, `SceneSnapshot` |
| 12 | Primary Controls | `PanelControl`, `LabelControl`, `ButtonControl`, `SliderControl`, `CanvasControl` |
| 13 | Extended Controls | `TextInputControl`, `ListViewControl`, `DataGridControl`, `WindowPresenter`, `ErrorBoundary` |
| 14 | Text & Localization | `TextFormatter`, `TextFlow`, `TextSearcher`, `StringTable`, `LocaleRegistry` |
| 15 | Data & Collections | `VirtualItemSource`, `SortFilterProxySource`, `AsyncDataProvider`, `DataCache`, `ListDiffCalculator` |
| 16 | Graphics & Rendering | `DirtyRegionTracker`, `SurfaceCompositor`, `ParticleSystem`, `SceneGraph2D`, `RenderTarget` |
| 17 | Introspection & Inspection | `SceneSpatialIndex`, `ui_property`, `PropertyRegistry`, `PropertyInspectorModel` |
| 18 | Advanced Runtime & Bootstrapping | `set_window_visible_state`, `bind_routed_feature_lifecycle`, `create_feature_presented_window`, `ActiveTabUpdateRouter` |
| 19 | Infrastructure & Internals | `UiEngine` — avoid in application code |
| 20 | Audio | `SoundCue`, `SoundBankRegistry`, `SoundEventBus` |
| 21 | Accessibility | `AccessibilityRole`, `AccessibilityTree`, `AccessibilityBus`, `LivePoliteness` |
| 22 | Theme Invalidation | `ThemeInvalidationBus` |
| 23 | Undo Context Routing | `UndoContextManager` |
| 24 | Async Form Validation | `AsyncFieldValidator`, `AsyncFormValidator` |
| 25 | Scoped Service Graph | `ServiceKey`, `ServiceScope`, `ScopeStack` |
| 26 | Cancelable Dataflow Pipeline | `DataflowPipeline`, `PipelineStage`, `CancellationToken`, `PipelineHandle` |
| 27 | Transactional App State Store | `AppStateStore`, `StateSelector`, `StateTransaction` |
| 28 | Adaptive Constraint Layout v2 | `ConstraintLayoutEngine`, `ConstraintSet`, `AdaptivePolicy`, `resolve_adaptive_policy` |
| 29 | Unified Virtualization Core | `VirtualizationCore`, `VirtualizedWindow`, `RecyclePool`, `MeasurePolicy` |
| 30 | Interaction State Machine Framework | `InteractionStateMachine`, `InteractionPhase`, `InteractionContext`, `InteractionTransition` |
| 31 | Schema-Driven Form Runtime | `SchemaFormRuntime`, `FieldGraphSchema`, `FieldSchema`, `ValidationPolicy` |
| 32 | Portable Snapshot & Migration Layer | `SnapshotMigrator`, `MigrationRegistry`, `make_snapshot`, `read_version`, `MigrationError` |

---

### Appendix D.2: Public API Selection Heuristics

Apply these decision rules when you are unsure which API tier to use for a given task:

1. **Start at Tier 1.** If `HostApplicationBindingSpec` + `build_host_application_config` + `bootstrap_host_application` + a `Feature` subclass solve the problem, stop there. The most common mistake is reaching for Tier 18 helpers before exhausting what Tier 1 specs already provide.

2. **Descend one tier at a time.** If Tier 1 is insufficient, look at Tier 4 (events/actions), Tier 5 (scheduling), Tier 3 (observables), or Tier 8 (layout) before reaching for anything beyond Tier 12. Each tier is a distinct abstraction level; skipping tiers means skipping safety guarantees.

3. **Use Tier 18 helpers for extending bootstrap behavior.** Functions like `bind_routed_feature_lifecycle`, `set_window_visible_state`, `add_task_panel_button`, and `create_feature_presented_window` are stable extension points designed for this purpose. They are not internals — they are the recommended way to assemble complex window/presenter configurations that go beyond what a spec alone expresses.

4. **Never import from internal submodules.** Always use `from gui_do import ...`. Code that imports from `gui_do.features.feature_lifecycle` or `gui_do.controls.input.button_control` is depending on implementation details that may change without notice.

5. **Avoid Tier 19 (`UiEngine`) in application code.** `UiEngine` is low-level infrastructure used by the framework itself. No feature should need to interact with it directly.

**Decision shortcuts by task:**

| Need | Use |
|------|-----|
| App setup and bootstrap | `HostApplicationConfig` + `bootstrap_host_application` |
| Feature with keyboard shortcuts and overlays | `RoutedFeature` + `RoutedRuntimeSpec` + `ShortcutOverlaySpec` |
| Cross-feature shared behavior | Lifecycle specs + routed runtime helpers (Tier 18) |
| Large dataset display | `VirtualizationCore` + `SortFilterProxySource` + `ListDiffCalculator` |
| Cancelable background processing | `DataflowPipeline` + `CancellationToken` |
| Maintainable persistence with schema evolution | `WorkspacePersistenceManager` + `SnapshotMigrator` |
| Performance-safe animations | `TweenManager` + `AnimationStateMachine` (Tier 5) |
| Discoverable keyboard shortcuts | `ShortcutOverlaySpec` in `RoutedRuntimeSpec` |
| Runtime state observability | `telemetry_collector` + `render_telemetry_report` (Tier 7) |

---

### Appendix E: Architecture Templates

These templates describe the recommended composition patterns for common application sizes and shapes.

**Template 1: Small Single-Scene App**

Appropriate for tools, demos, and single-purpose applications with one screen of interaction.

- 1 scene, 2–4 `Feature` instances declared in `FeatureSpec` entries
- `ObservableValue` state fields in each feature; subscriptions wired in `bind_runtime` and unsubscribed in `shutdown_runtime`
- `ActionSpec` entries with `ActionHotkeySpec` for all commands; no manual `InputMap` wiring
- `SceneBundleBindingSpec` with `bind_escape_to_exit=True` for the single scene
- No task panel, no floating windows, no `WindowPresenter`
- `TelemetryConfig(enabled=True)` during development; disable before release

**Template 2: Multi-Window Workbench**

Appropriate for developer tools, editors, and dashboards with multiple independent panels.

- 2+ scenes with a `SceneMenuStripControl` for scene navigation
- `SceneTaskPanelSpec` per scene with per-window toggle buttons
- `TaskPanelFocusToggleSpec` for each floating window to exclude hidden window controls from tab cycle
- One `WindowPresenter` subclass per floating tool window, declared via `FeatureWindowBundleBindingSpec`
- `RoutedRuntimeSpec` with `ShortcutOverlaySpec` in the main feature for discoverable shortcuts
- `WorkspacePersistenceManager` + `SettingsRegistry` for window positions and layout state
- `AppStateStore` with `StateSelector` for shared cross-feature state
- Telemetry baseline established during development for frame-budget regression detection
