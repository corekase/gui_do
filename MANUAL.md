# gui_do Manual

## Title and Purpose

[Back to Table of Contents](#table-of-contents)

This manual is the primary end-to-end guide for developers building applications with gui_do. It is written for first-time users who need a clear mental model before writing any code, intermediate implementers who need a complete system-level reference, and maintainers who need a reliable operational guide rooted in the current public API surface, runtime contracts, and tested behavior. The document is deliberately structured to move from theory to practice to system-level reference, so a reader can both understand the architectural intent and apply it directly in production code without needing to read the source. Every major system exposed by the framework has its own chapter, and every chapter follows the same structure to reduce the cognitive overhead of navigation. The manual is a single self-contained file; no external supplementary documents are required to follow the guidance here.

---

## Table of Contents

- [Title and Purpose](#title-and-purpose)
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
  - [Maintainer Diff Checklist](#maintainer-diff-checklist)
- [Performance and Scaling Guidance](#performance-and-scaling-guidance)
- [Migration, Versioning, and Deprecation Notes](#migration-versioning-and-deprecation-notes)
- [FAQ and Troubleshooting](#faq-and-troubleshooting)
- [Appendix](#appendix)
  - [Appendix A: Glossary](#appendix-a-glossary)
  - [Appendix B: Lifecycle and Event Sequence Reference](#appendix-b-lifecycle-and-event-sequence-reference)
  - [Appendix C: System Dependency Map](#appendix-c-system-dependency-map)
  - [Appendix D: API Quick Index](#appendix-d-api-quick-index)
    - [D.1 Tier Matrix](#d1-tier-matrix)
    - [D.2 Selection Heuristics](#d2-selection-heuristics)
  - [Appendix E: Architecture Templates](#appendix-e-architecture-templates)

---

## How to Use This Manual

[Back to Table of Contents](#table-of-contents)

gui_do is a layered framework: its outermost layer is a declarative, data-driven bootstrap API; beneath that live cooperative runtime systems for state, events, layout, and rendering; and at the foundation are low-level infrastructure pieces that most applications never touch directly. This manual mirrors that layering. It does not assume prior knowledge of gui_do, but it does assume the reader is a competent Python developer who understands basic object-oriented patterns and is familiar with pygame at a conceptual level.

The manual is written to support three distinct modes of reading. You do not need to read it sequentially unless you are learning from scratch. The sections below describe the three intended modes and suggest a reading order for each.

### Reading Paths

**Beginner path — I am new to gui_do and want to build my first application.**

Start with the Conceptual Foundations chapter. Read all three subsections there (Data-Driven Design, Reactive Data and Observable State, Feature Composition and Lifecycles) before writing any code. These sections form the theoretical backbone of the entire framework; every other chapter assumes you understand them. After Conceptual Foundations, proceed through the Quickstart Path chapter, which gives you a minimal working application. Then read 8.1 (Bootstrap), 8.2 (Feature Lifecycle), 8.3 (Events and Actions), and 8.4 (State and Observables) as your core systems. By the time you have read those six sections, you can build a complete interactive application. Return to other system chapters as your needs require.

**Intermediate path — I understand the basics and need a complete reference for a specific system.**

Go directly to the relevant system chapter under section 8. Each system chapter is self-contained and cross-links to related systems. If you need to understand how a system relates to others, use Appendix C (System Dependency Map) to identify the dependency chain, then read those chapters in dependency order.

**Maintainer path — I am regenerating, auditing, or significantly updating the manual.**

Begin with the Maintainer Diff Checklist in the Testing, Diagnostics, and Reliability chapter. That checklist is your operational guide. Then use Appendix D.1 (Tier Matrix) to compare the current gui_do/__init__.py exports against the chapter and appendix coverage. Any tier that appears in the codebase but lacks corresponding manual coverage is a gap to fill. Any chapter that references a name not currently exported is a stale reference to fix.

### Tri-Lens Markers

Throughout the manual, content is sometimes annotated with one of three focus lenses to help readers quickly identify what kind of guidance they are reading:

- **[CONCEPT]** marks explanatory prose that describes what something is, why it exists, and how to think about it. These paragraphs build mental models. Read them to understand before you implement.
- **[PRACTICE]** marks procedural guidance: how to set something up, the idiomatic order of operations, numbered steps. These paragraphs are directly actionable.
- **[REFERENCE]** marks lookup-oriented content: API names, field lists, enum values, callback signatures. These are skimmable and intended for readers who already understand the concept.

Not all paragraphs are annotated. The markers appear only when a clear distinction is useful. In particular, most minimal examples are implicitly [PRACTICE] and most API signature tables are implicitly [REFERENCE].

### Contract Alignment

Several behavioral claims in this manual are governed by formal contracts under docs/. The documents there define normative behavior that automated tests enforce. Where this manual cites a specific behavioral guarantee such as scheduler budget bounds, restore report fields, or action routing precedence, that guarantee originates in a contract document, not in prose convention. The relevant files are:

- docs/runtime_operating_contracts.md: scheduler budgets, workspace restore fields, determinism guarantees
- docs/public_api_spec.md: tier organization, stability policy, import contracts
- docs/architecture_boundary_spec.md: boundaries between library code and demo code
- docs/package_contracts.md: per-package internal structure contracts
- docs/event_system_spec.md: event dispatch and routing rules

When you observe a behavior that contradicts this manual, consult the contract documents to determine which is authoritative. The code and its tests are the ultimate ground truth; the contract documents formalize the intent; the manual explains the reasoning.

### Known Non-Goals

gui_do intentionally does not attempt the following. Understanding these non-goals prevents misapplication:

- **Native OS widget embedding.** gui_do renders everything to a pygame surface. It does not wrap platform-native controls and does not support mixing native and pygame rendering.
- **Declarative UI markup.** There is no XML, JSON, or DSL file format for describing UI. All structure is expressed through Python spec objects and feature classes.
- **Automatic layout from constraint solving at runtime for all controls.** The constraint layout engines (Tier 8 and 28) are available, but most applications use simpler positional or flex layouts. There is no system-wide auto-layout that runs every frame.
- **Multi-process or multi-window rendering.** gui_do manages a single pygame display surface. Multi-window is a presentation abstraction (floating panels within the surface), not true OS multi-window.
- **Network or server-client state sync.** The framework has no built-in remote-state or CRDT layer. Observable values and the state store are entirely in-process.
- **Hot-reload or live editing.** No mechanism exists for reloading feature code at runtime without restarting the application.
- **Accessibility tree bridging to platform APIs.** The AccessibilityTree (Tier 21) provides a semantic node model, but it does not bridge to AT-SPI, UIA, or macOS NSAccessibility.
- **Target OS-native widget parity across all platforms.** gui_do does not replace application-specific domain architecture decisions and does not define star-import behavior as a compatibility contract.

---

## Conceptual Foundations (Theory)

[Back to Table of Contents](#table-of-contents)

The three concepts in this chapter — data-driven design, reactive observable state, and feature composition — form the theoretical backbone of everything else in the manual. Every other chapter assumes you have understood them. Read this chapter fully before writing any application code. These ideas govern why gui_do is structured the way it is, and understanding them will save you hours of debugging mismatched expectations later.

### Data-Driven Design

[Back to Table of Contents](#table-of-contents)

Data-driven design in gui_do means that the application is described first and executed second. Instead of wiring behavior through long chains of imperative setup calls — create this object, attach that handler, register this callback — you define configuration objects that express scenes, features, actions, windows, accessibility annotations, and runtime policies. The framework receives those configuration objects and performs all wiring automatically in a single deterministic pass. Your code never manually threads dependencies; it only expresses intent.

The entry point for this model is the specification pipeline centered on `HostApplicationBindingSpec`, the family of typed `*Spec` descriptors, and `build_host_application_config`. In practice, a developer populates spec objects such as `FeatureSpec`, `SceneSetupSpec`, `RuntimeSceneSpec`, `WindowSpec`, `ActionSpec`, `AccessibilitySequenceSpec`, `ShortcutOverlaySpec`, and dozens of others, then hands a high-level binding object to the builder. The builder performs a single deterministic pass that resolves all cross-references, validates requirements, and produces a fully wired `HostApplicationConfig`. That config is then passed to `bootstrap_host_application`, which constructs the live runtime against the host object.

This two-phase approach is deliberate. The first phase constructs and validates data — all spec relationships are resolved, all class references are checked for protocol compliance, and all required attributes are confirmed present. The second phase executes runtime behavior — scenes are registered, features are instantiated, action registries are populated, input maps are bound. Because those phases are entirely separated, tests can assert correctness at either boundary independently. You can test that config construction produces the expected feature and action graph without ever opening a display window, and you can test runtime behavior separately against known-good config input. This sharply reduces debugging ambiguity because failures are localized to either the description phase or the execution phase.

The contrast with imperative wiring is substantial enough to warrant a concrete example. In an imperative approach, adding one keyboard shortcut typically requires: finding the input-dispatch code, inserting a new conditional branch, constructing and registering a callback object, ensuring that callback is cleaned up when the relevant scene exits, and testing that the cleanup actually runs and does not leave stale handlers. Each step is a separate code edit in a separate location, and forgetting any one of them creates subtle bugs that appear only during transitions. In gui_do's data-driven approach, the developer adds one `ActionSpec` entry and optionally one `ActionHotkeySpec` or `ControlKeyBindingSpec`. The framework picks it up, registers it with the action registry under the correct scene scope, routes the key through the input map, and tears it all down automatically when the scene exits. The developer never touches the router.

Data-driven structure also provides meaningful protection against internal code reorganization. You can move a class from one file to another, extract a presenter into its own module, split a feature into logic and presentation companion objects, or rename every internal helper — none of these changes require any modification to bootstrap code, as long as each feature package's `__init__.py` continues to export the same public names. Bootstrap code consumes class references and spec values, not file paths or module location assumptions. This is a direct consequence of the data-driven approach: the data that drives the application (the spec objects and the class references they hold) is kept in one place, not scattered throughout the codebase's internal structure. When you maintain a gui_do application over time, internal reorganizations are low-risk precisely because the bootstrap surface is stable.

Testability is one of the most concrete benefits. Spec objects can be constructed and validated in pure unit tests with no running display, no pygame initialization, and no event loop. `FeatureSpec` instances can be checked for protocol compliance without instantiating anything. The entire `HostApplicationConfig` can be assembled and examined in tests to verify that exactly the right features, actions, windows, and accessibility annotations were registered. This determinism is only possible because the application's structure is expressed as data rather than hidden inside call sequences.

The design philosophy behind using rich, named spec objects deserves explicit mention. An `ActionSpec` with named fields — `action_id`, `label`, `kind`, `target`, `category`, `key` — is self-documenting, composable, and forward-compatible. When the framework evolves and new optional fields are added, existing code that constructs `ActionSpec` objects does not break because keyword arguments with defaults are backward-compatible. A raw positional-argument call site cannot offer the same stability guarantee. Specs are also a natural serialization boundary: they are pure data with no side effects, and they could in principle be stored in configuration files, generated programmatically, or compared in test assertions.

The boundary between declarative and imperative is worth stating precisely, because misunderstanding it is a common source of over-engineering. The wiring of the application — scene graph construction, action registry population, input routing, feature orchestration, accessibility tree seeding — is data-driven and should stay that way. The runtime behavior of individual features — what they do inside `handle_event`, `on_update`, and `draw` — is imperative Python inside feature methods, and there is no benefit to trying to declarativize it. The philosophy is: describe static structure declaratively; implement dynamic behavior imperatively. Spec objects are for structure; Python methods are for behavior.

---

### Reactive Data and Observable State

[Back to Table of Contents](#table-of-contents)

Reactive data in gui_do means that when a value changes, everything that depends on that value updates automatically — without the producer needing to know who the consumers are. In a traditional imperative GUI, if you want a label to show the current count of items in a list, you must call `label.set_text(str(len(items)))` every time the list changes. You have to manually remember every place that should react to a change, and if you add a new dependent later, you have to find every mutation site and add another call. This approach scales poorly and creates brittle, tightly coupled code. Reactive design solves this: the list is an observable, the label subscribes to it once, and forever after, the label stays synchronized without any further intervention from the code that modifies the list.

The foundational reactive primitives are `ObservableValue`, `ObservableList`, and `ObservableDict`. `ObservableValue` wraps a single value of any type. Any code that calls `.subscribe(callback)` will have its callback invoked whenever the `.value` attribute is assigned a new value. The subscription is registered once, and the observable handles delivery for all future changes. `ObservableList` and `ObservableDict` provide the same notification semantics for mutable collections, with `CollectionChange` events that carry a `ChangeKind` indicator (insert, remove, update) and enough detail for consumers to react intelligently to specific changes rather than being forced to reprocess the entire structure on every modification.

The framework also provides `ComputedValue`, a derived observable that recomputes its value from one or more source observables whenever those sources change. A computed value makes derivation relationships explicit and localized: instead of scattering subscribe-and-copy callbacks across multiple features, you express a derivation once as a `ComputedValue` and it behaves like any other observable from the consumer's perspective. This is especially valuable when multiple controls or features all need to display a derived quantity, because the derivation logic exists in exactly one place.

When multiple related observable mutations need to happen together, `reactive_batch` exists to batch them. Without batching, each individual assignment fires its subscribers immediately, which can cause intermediate inconsistent states to be observed. With `reactive_batch`, all mutations within the batch block are queued and subscribers are notified exactly once after all mutations are complete, seeing only the final coherent state. `is_batching` allows guarded logic to check whether a batch is currently open, which is useful in code that needs to behave differently during mass initialization. Batching is particularly valuable during workspace restore operations, where many observable values are updated simultaneously and you do not want UI components flashing through partial states.

Subscription lifecycle is one of the most important operational concerns in a reactive system. Subscriptions hold references: the observable holds a reference to the callback, and the callback typically holds a reference to the subscribing object. If a feature is destroyed without unsubscribing, the observable continues to hold a live reference to the dead feature's methods, preventing garbage collection and causing the callback to fire on an object in an invalid state. The correct subscription pattern is: subscribe in `bind_runtime` or equivalent runtime-ready lifecycle hooks, and unsubscribe in `shutdown_runtime` or the feature's teardown path. Store the unsubscribe handles (the return values of `.subscribe(callback)`) on the feature instance and call them deterministically during cleanup. Features that follow this discipline never produce phantom callbacks or memory leaks.

The control binding model in gui_do is built directly on reactive observables. Controls accept either a plain literal value or an observable for their primary data properties. When a control is bound to an observable, it registers an internal subscription and refreshes its displayed content whenever the observable changes. This means feature code never needs to reach into a control instance to update its display state — it only changes the observable, and the control responds. This decoupling has a practical benefit beyond cleanliness: it makes it straightforward to replace one control type with another because the business state (the observable) is not entangled with any specific control implementation. The observable does not know or care whether it is being observed by a label, a rich label, a tooltip, or a status bar slot.

For cross-feature reactive state, observable values are the preferred mechanism. One feature owns an `ObservableValue` and exposes it through its public interface or through a shared state store; other features subscribe to it in `bind_runtime`, when sibling features are guaranteed to already exist. This is looser coupling than direct method calls: the producing feature does not know who is observing, and the observing feature does not depend on the producer's internal structure. This makes features independently testable and makes composition of many features in one scene straightforward — each feature only declares its subscriptions; the runtime does not require any global coordination of which feature must be initialized first.

Several anti-patterns consistently cause problems in reactive code and should be actively avoided. Polling an observable in `on_update` instead of subscribing defeats the reactive model: it wastes CPU cycles every frame even when nothing changed, and introduces up to one frame of latency in updates. Subscribing in `build` before the runtime is ready can cause callbacks to fire before controls exist and produce null-reference exceptions. Forgetting to unsubscribe at teardown creates memory leaks and phantom callbacks that fire on destroyed features, often producing cryptic errors during scene transitions. Sharing mutable plain Python objects (plain dicts, plain lists) between features instead of observable wrappers breaks the reactive contract entirely: mutations to plain objects are invisible to any code that read them before the mutation, and the UI never updates. Use observable wrappers for any data that should automatically drive UI state.

---

### Feature Composition and Lifecycles

[Back to Table of Contents](#table-of-contents)

A Feature is the primary unit of application behavior in gui_do. It is a self-contained object that declares what resources it requires from the host, builds its own UI elements, registers its own event handlers and subscriptions, and tears itself down cleanly when it is no longer needed. Features are composable: a gui_do application is a collection of features that coexist within scenes, each managing its own slice of the UI and data. The framework orchestrates their lifecycle phases in the correct order and routes events to the correct feature based on scene membership, focus state, and event type.

The framework exposes four primary feature types, and choosing the right one is the first design decision when implementing new functionality.

`DirectFeature` renders directly to the screen surface on every frame, bypassing the control tree entirely. It receives `draw(host, screen)` and `on_update(host, dt_seconds)` calls but does not build controls and does not participate in focus or hit-testing. Use `DirectFeature` for background elements such as animated backdrops, particle effects, and full-screen visual transitions that do not need interactive UI. It is the lowest-overhead feature type because it skips the control tree machinery.

`Feature` is the standard interactive feature. It builds controls in the scene's control tree during `build`, participates in focus and hit-testing, and receives `handle_event` calls for routed events. Use `Feature` for any feature that shows interactive UI elements. Most application features are of this type.

`LogicFeature` has no UI of its own. It exists to hold domain logic, manage shared state, run background computations via the cooperative scheduler or data pipeline system, and publish results that other features react to. Use `LogicFeature` when behavior needs to be separated from presentation — for example, when you want to unit-test business logic independently of any display code. A `LogicFeature` and a `Feature` working together is one of the most powerful composition patterns in the framework.

`RoutedFeature` extends feature behavior with explicit participation in the action routing infrastructure. It can define route targets that receive named messages dispatched to specific handler methods. Use `RoutedFeature` when a feature must respond to framework-level actions, coordinate with the action registry, or integrate tightly with the routed runtime lifecycle managed by `RoutedRuntimeSpec` and `RoutedFeatureLifecycleSpec`.

Every feature participates in a defined lifecycle, and keeping phase boundaries strict is essential for predictable behavior. The lifecycle phases are:

`build(host)` is called exactly once during scene construction. This is the phase for creating controls, adding them to the scene tree, building window specs, and setting up any static structure that does not depend on runtime state from sibling features. The `host` object provides all resources declared in `HOST_REQUIREMENTS["build"]`. Controls created in `build` exist for the entire lifetime of the scene; do not create controls in later phases. Subscriptions to observables should not be established here because sibling features may not yet be fully built.

`bind_runtime(host)` is called after all features in the scene have completed `build`. By this point, all controls exist and all sibling features are built. This is the phase for subscribing to observable values, binding controls to data, registering callbacks, initializing state from runtime sources (screen size, settings, workspace state), and wiring cross-feature interactions. The invariant that all sibling features are built before `bind_runtime` fires is a critical design guarantee: it makes safe cross-feature initialization possible without requiring features to have explicit ordering dependencies.

`handle_event(host, event)` is called for every `GuiEvent` that the routing layer delivers to this feature. The routing layer filters events by scene membership, focus state, and overlay routing policy before calling this method. Return `True` to consume the event and stop further propagation; return `False` or `None` to pass it on to the next handler in the routing chain.

`on_update(host, dt_seconds)` is called every frame with the elapsed time in seconds. Use this for lightweight per-frame logic: progressing animations, polling background results, triggering timers, updating state that changes smoothly over time. Keep this method fast. Anything with non-trivial computational cost belongs in a cooperative scheduler coroutine or a data pipeline stage, not in `on_update`.

`draw(host, screen)` is called every frame after `on_update`. Use this for custom rendering that bypasses the control tree: particles, canvas effects, debug overlays, procedural graphics. Most features do not need this hook because the control tree handles standard rendering. Only implement `draw` when controls genuinely cannot express the visual output you need.

The `HOST_REQUIREMENTS` dictionary is the mechanism by which features declare their dependencies. It maps lifecycle method names to tuples of host attribute names that must be present before the method is called. For example, `{"build": ("app", "screen_rect", "scene_presentation")}` tells the framework that the `build` method needs `host.app`, `host.screen_rect`, and `host.scene_presentation` to be available. The framework validates these at startup and produces actionable error messages when a required attribute is missing. This explicit declaration replaces hidden constructor injection and makes dependency relationships both machine-verifiable and human-readable. Looking at a feature's `HOST_REQUIREMENTS` tells you exactly what the feature depends on — which is far more informative than having to read the method body to discover implicit attribute accesses.

Feature messaging is the mechanism for loosely coupled communication between features. Features do not hold direct references to each other; instead, one feature publishes a `FeatureMessage` by name with an optional payload, and the framework delivers it to any feature that has registered a handler for that message name. This prevents features from coupling to each other's implementations. A `LogicFeature` can publish a `"data_ready"` message when a background computation finishes, and any number of UI features can register handlers for that message without the LogicFeature knowing anything about them. FeatureMessage is a good fit for discrete events — something happened, here is the result. For continuous state streams, observable values are usually the better choice.

Scene assignment controls feature activation and deactivation. Each feature belongs to exactly one scene (specified via `scene_name` in its constructor). When the application transitions from one scene to another, the framework calls teardown lifecycle methods on the departing scene's features and calls `build` then `bind_runtime` on the arriving scene's features if they have not yet been initialized. Features from the previous scene do not receive events, `on_update` calls, or `draw` calls after the transition. This hard boundary prevents stale state from one scene from leaking into another, which is a common source of subtle bugs in imperative frameworks.

The folder and package composition convention used throughout `demo_features` is the recommended organizational pattern for any gui_do application. Each feature package lives in its own folder. The `__init__.py` is the sole public surface of the package: it exports the feature class and any public types, and nothing else. Internal files are separated strictly by concern: `*_feature.py` owns the feature class and lifecycle methods; `*_presenter.py` owns any `WindowPresenter` subclass; `*_specs.py` owns shared constants and spec objects; `*_logic_feature.py` owns a companion `LogicFeature` if one exists; standalone data types and models live in their own files. This separation makes each file's purpose immediately clear from its name and prevents concerns from bleeding across files. Critically, bootstrap code imports only from the package's `__init__.py` surface — never from internal submodules. This means any internal reorganization inside the package is completely transparent to bootstrap consumers. You can split a large feature file into five files, merge two files, or rename every internal helper, and nothing in the application's startup code needs to change.

Three composition patterns recur in real applications and are worth naming explicitly. The **logic plus presentation split** pairs a `LogicFeature` that owns computation and publishes state through observable values with a `Feature` or `RoutedFeature` that subscribes to those values and drives the UI. The logic feature is independently testable because it has no UI dependencies; the presentation feature is testable with a mock logic feature. The **presenter pattern** uses a `WindowPresenter` subclass to encapsulate window content and layout, while the owning feature coordinates lifecycle and routing. The feature lazily constructs the presenter in `build` to avoid circular import issues. The **background workflow pattern** uses a `LogicFeature` with a `CooperativeScheduler` coroutine for long-running work such as file loading or complex computation. The coroutine publishes progress updates through an observable, and a UI feature subscribes to display a progress indicator. When the coroutine completes, it publishes a final result through another observable or a `FeatureMessage`, and the UI feature updates its display. This pattern keeps the frame loop responsive even during expensive operations because the coroutine yields control back to the scheduler on each iteration.

---

## Quickstart Path (Practice)

[Back to Table of Contents](#table-of-contents)

This quickstart gives you a working gui_do application as quickly as possible. It is deliberately opinionated: start with Tier 1 configuration and bootstrap APIs, validate the build early with contract tests, and only then add complexity. The fastest path to a successful first application is to treat application startup and wiring as declarative data from the beginning.

### Step 1: Install and Verify

Install the package in development mode and immediately run the public API export contract test:

```bash
python -m pip install -e . --no-deps
python -m pytest -q tests/test_public_api_exports.py
```

Install the required runtime dependencies before running an app. `pygame` is required for input, surfaces, and the frame loop. `numpy` is used internally for pixel buffer operations via `PixelArray` in rendering paths. Running the export contract test immediately after installation confirms that your import surface is aligned with the package's public API specification.

### Step 2: Create a Minimal Host

The simplest way to construct a working config is to populate `HostApplicationConfig` directly. The fields below are required:

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


class HelloFeature(Feature):
    def __init__(self) -> None:
        super().__init__("hello", scene_name="main")


cfg = HostApplicationConfig(
    display_size=(1280, 720),
    window_title="My First App",
    fonts={"default": {"system": "arial", "size": 14}},
    font_role_specs=(),
    cursors=(),
    scene_specs=(SceneSetupSpec(scene_name="main", pretty_name="Main"),),
    feature_specs=(FeatureSpec("hello_feature", HelloFeature),),
    window_specs=(),
    runtime_scene_specs=(RuntimeSceneSpec(scene_name="main", bind_escape_to_exit=True),),
    action_specs=(ActionSpec(action_id="exit", label="Exit", kind="exit"),),
    static_accessibility_specs=(),
    initial_scene_name="main",
)
```

For larger applications, use `build_host_application_config` with `HostApplicationBindingSpec` and bundle helpers such as `SceneBundleBindingSpec`, `FeatureWindowBundleBindingSpec`, `ActionBindingSpec`, `FontRoleBindingSpec`, and `CursorBindingSpec`. The bundle approach generates most of the boilerplate relationships automatically and scales well as scene and feature count grows.

### Step 3: Add a Feature with Observable State

A minimal feature that creates a label and keeps it synchronized with an observable value:

```python
from pygame import Rect

from gui_do import Feature, LabelControl, ObservableValue, PanelControl


class CounterFeature(Feature):
    HOST_REQUIREMENTS = {"build": ("app",), "bind_runtime": ()}

    def __init__(self) -> None:
        super().__init__("counter", scene_name="main")
        self.count = ObservableValue(0)
        self._unsub = None

    def build(self, host) -> None:
        self.root = host.app.add(
            PanelControl("counter_root", Rect(20, 20, 400, 120)),
            scene_name="main",
        )
        self.label = self.root.add(
            LabelControl("count_label", Rect(8, 8, 200, 28), "Count: 0")
        )

    def bind_runtime(self, host) -> None:
        self._unsub = self.count.subscribe(
            lambda v: setattr(self.label, "text", f"Count: {v}")
        )

    def shutdown_runtime(self, host) -> None:
        if self._unsub is not None:
            self._unsub()
            self._unsub = None
```

Notice the strict phase separation: controls are created in `build`, subscriptions are wired in `bind_runtime`, and subscriptions are torn down in `shutdown_runtime`. This pattern prevents phantom callbacks and guarantees controls exist before bindings fire.

### Step 4: Add an Action and Runtime Scene Policy

Declare actions in `action_specs` and scene behavior policies in `runtime_scene_specs`. The most common starter policy is `bind_escape_to_exit=True` in `RuntimeSceneSpec`, which wires a consistent exit behavior without custom event plumbing. To add keyboard shortcuts to feature-level actions, add `ActionHotkeySpec` or `ControlKeyBindingSpec` entries to the config:

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

Keep action IDs stable across updates. They are referenced by routed runtime specs, input bindings, and command palette entries. Changing an action ID requires updating every binding that references it.

### Step 5: Run Loop

Wrap the host object and run it:

```python
class Host:
    def __init__(self) -> None:
        bootstrap_host_application(self, cfg)

    def run(self) -> int:
        return self.app.run_entrypoint(target_fps=120)


if __name__ == "__main__":
    raise SystemExit(Host().run())
```

`bootstrap_host_application` sets `self.app` (a `GuiApplication` instance) plus all other host attributes derived from the config. `run_entrypoint` starts the pygame event loop and returns an integer exit code. It tolerates workspace load/save failures without aborting and reports runtime loop failures with a non-zero exit code.

### Guided Build Track (Beginner)

Work through these milestones in order. Each builds on the previous.

- **Milestone A:** App boots to a single scene with no display errors or import failures.
- **Milestone B:** One feature creates one visible control that appears on screen.
- **Milestone C:** One `ObservableValue` updates one control's text reactively when the value changes.
- **Milestone D:** One `ActionSpec` and one hotkey binding produce the expected behavior when triggered.
- **Milestone E:** One overlay surface and one toast both route correctly without leaking input to underlying controls.
- **Milestone F:** Workspace save and load complete successfully and the app restores the same scene.

**Beginner confidence checklist:**
- You can explain precisely where `build` ends and `bind_runtime` begins and why the boundary exists.
- You can add or remove one feature entirely through spec configuration without touching any lifecycle code.
- You can trace one keypress from the pygame event queue through event normalization, routing policy, and into action execution.

### Quickstart Failure Modes

**Feature never appears on screen.** Verify that the feature is listed in `feature_specs` and that its `scene_name` matches a `scene_name` declared in `scene_specs`. A mismatch silently places the feature in a scene that is never activated.

**Hotkey does nothing.** Verify that the action descriptor exists in `action_specs` and that the input binding scope matches the current scene and window context. Hotkeys bound to a specific window scope do not fire when that window is hidden or focus is elsewhere.

**Overlay blocks unexpected keys.** Inspect the overlay's unhandled-key consumption policy and its dismissal configuration. Some overlay managers consume all keyboard input while open. If the behavior is wrong, configure the overlay to pass through specific key types or check whether the wrong overlay is being opened.

**State updates but UI does not reflect the change.** Ensure subscriptions are established in `bind_runtime` and that `shutdown_runtime` is not being called prematurely. Also verify that the subscription callback is actually setting the correct control property and that the control is not being recreated after the subscription fires.

---

## Architecture and Runtime Model

[Back to Table of Contents](#table-of-contents)

This chapter describes the structural rules that govern how gui_do is organized and how its runtime operates. Understanding the architecture helps you place new code in the right layer, diagnose unexpected behavior, and read contract documentation with full context.

### Boundary Model: Framework vs Consumer

The repository enforces a hard architectural boundary between the framework and consumer code. `gui_do/` is the reusable framework package. It contains the runtime, controls, events, layout engines, state and persistence systems, scheduling, theming, and all other infrastructure. It must not import from `demo_features/` or any other consumer code. This keeps `gui_do/` usable as a standalone package in any application.

`demo_features/` and `gui_do_demo.py` form the consumer integration layer. They import from `gui_do` and compose features, scenes, and configurations, but they are not part of the framework. Changes to `demo_features/` never affect `gui_do/` behavior.

Consumer entrypoints must import from the `gui_do` root package using explicit named imports. They must not import from `gui_do.*` internal submodules directly. This rule ensures that internal refactors inside the framework (moving a class from one internal module to another) cannot silently break consumer code. The root package's `__init__.py` is the stable consumer surface.

Both rules are enforced by automated tests: `tests/test_boundary_contracts.py` uses AST import inspection to verify that no file in `gui_do/` imports from `demo_features/`, and that consumer entrypoints use root package imports.

### Tiered Public API Model

`gui_do/__init__.py` organizes all public exports into numbered tiers. Each tier comment block (`# TIER N: NAME`) groups related exports and signals their intended usage level. Tier numbers are a guidance mechanism: when two tiers offer overlapping capability, you should prefer the lower-numbered (more abstract) tier first, because it typically carries better lifecycle integration and fewer manual responsibilities.

**Tier 1 — Primary Entry Points and Data-Driven APIs.** This is the recommended starting point for all new applications. Contains feature lifecycle base classes (`Feature`, `DirectFeature`, `LogicFeature`, `RoutedFeature`), the complete family of declarative spec types (`FeatureSpec`, `WindowSpec`, `RuntimeSceneSpec`, `ActionSpec`, and all binding spec variants), and the bootstrap pipeline (`HostApplicationConfig`, `bootstrap_host_application`, `build_host_application_config`). If your application code primarily uses Tier 1 names, it is structured correctly.

**Tiers 2–7 — Core Runtime Systems.** These tiers expose the systems that Tier 1 bootstraps and manages: app and scene management (Tier 2), essential data and state primitives like `ObservableValue`, `ObservableList`, `CollectionView`, `Binding` (Tier 3), events, actions, focus, and input infrastructure (Tier 4), scheduling and animation (Tier 5), theme and font management (Tier 6), and telemetry (Tier 7). Feature code frequently uses names from these tiers.

**Tiers 8 and above — Specialized Systems.** Layout engines (Tier 8), overlay managers (Tier 9), forms and validation (Tier 10), state and persistence (Tier 11), primary controls (Tier 12), extended controls (Tier 13), text and localization (Tier 14), data helpers (Tier 15), graphics and rendering (Tier 16), introspection (Tier 17), advanced bootstrap helpers (Tier 18), audio (Tier 20), accessibility (Tier 21), theme invalidation (Tier 22), undo routing (Tier 23), async validation (Tier 24), service scope (Tier 25), dataflow pipeline (Tier 26), transactional state store (Tier 27), adaptive constraint layout (Tier 28), virtualization (Tier 29), interaction state machine (Tier 30), schema form runtime (Tier 31), and snapshot migration (Tier 32). Use these when Tiers 1–7 do not provide sufficient abstraction for your specific need.

The tier matrix in Appendix D.1 lists all tiers with their contained names for quick lookup.

### Runtime Guarantees

The following behavioral guarantees are contractually specified in `docs/runtime_operating_contracts.md` and enforced by automated tests:

**Canonical GuiEvent normalization.** All raw pygame input events are normalized to `GuiEvent` before any application-level dispatch occurs. Feature code always receives `GuiEvent` objects, never raw pygame events. This ensures consistent event semantics across all feature handlers.

**Scene-isolated update execution.** Scene-contained runtime systems (features, schedulers, tweens, timers, overlays registered to a scene) execute their update and event logic only when that scene is active. Deactivated scenes do not accumulate state or fire callbacks.

**Deterministic window focus cycling.** Window focus candidates within a scene are sorted by `control_id` before traversal. This makes keyboard focus navigation order predictable and testable.

**Scheduler dispatch budget clamping.** The task scheduler's per-frame dispatch time is clamped to contract-defined bounds: a fraction of `0.12` of the frame's `dt` in milliseconds, with a floor of `0.5 ms` and a ceiling of `4.0 ms`. This prevents scheduler work from starving rendering under slow frames and prevents it from running unconstrained under fast frames.

**Missing settings keys are skipped during workspace restore.** When restoring workspace state, settings keys that do not exist in the current application are silently skipped. The restore operation produces a detailed report with `applied_settings`, `skipped_settings`, and `missing_settings_blocks` fields rather than failing hard on unknown keys.

### Event Pipeline

When `GuiApplication` processes an incoming pygame event, it executes a deterministic sequence:

1. **Normalize to GuiEvent.** The raw pygame event is converted to a `GuiEvent` with a canonical type from `EventType`, a phase from `EventPhase`, and fully populated payload fields.
2. **Handle quit events early.** QUIT events are handled before any further routing so application shutdown is never delayed by routing policy.
3. **Update shared input state.** The `InputSnapshot` is updated with the current keyboard, mouse, and modifier state.
4. **Update logical pointer state and apply capture clamping.** Pointer position is updated. If pointer capture or lock is active, coordinates are clamped to the capture region.
5. **Logicalize pointer events.** Pointer events carry both raw screen coordinates and logicalized scene coordinates. Logicalization accounts for any viewport or camera transform in the active scene.
6. **Route through overlay, toast, and focus management.** If a modal overlay, toast, or context menu is active, it receives the event first. Some overlay types consume all input while open.
7. **Route keyboard events through key routing policy.** Global key bindings (registered via `bind_global_key`) are tested before focus dispatch. Scene-level and window-level key handlers are then dispatched in stable candidate order.
8. **Dispatch to feature handlers and scene dispatch.** The event is delivered to feature `handle_event` methods in scene order, then to registered scene-level handlers. Fallthrough handlers receive events that no earlier handler consumed.
9. **Respect hard stop signals.** `propagation_stopped` and `default_prevented` on a `GuiEvent` are checked after each handler. A handler that returns `True` or explicitly sets these flags stops further delivery. `GuiEvent.clone()` produces independent copies; mutations to a clone do not affect the original.

### Known Non-Goals

The architecture intentionally does not address:
- OS-native widget parity across all platforms. gui_do renders entirely to pygame surfaces.
- Replacing application-specific domain architecture for business logic. The framework orchestrates UI behavior; it does not dictate application domain design.
- Exposing internal infrastructure tiers as recommended entry points. Tiers 18 and above are for framework extension, not application bootstrapping.
- Making star-import behavior part of the public compatibility contract. Use explicit named imports from `gui_do`.

---

## Core Workflow: Build, Bind, Route, Update, Draw

[Back to Table of Contents](#table-of-contents)

The five-phase workflow is the practical core of gui_do application development. Every feature participates in some or all of these phases. Keeping phase boundaries strict produces applications that are easier to debug, test, and extend because each piece of code has one job at one point in the lifecycle.

### Phase Reference

**build** is the construction phase. Instantiate controls, create observable containers, and declare static structural relationships between UI elements. The invariant for `build` is: no runtime-dependent subscriptions and no cross-feature coordination. Controls added to the scene tree in `build` exist for the lifetime of the scene. Never create controls in `on_update`, `handle_event`, or `draw`.

**bind_runtime** is the wiring phase. All features in the scene have completed `build` before any feature's `bind_runtime` is called. This guarantees that sibling feature controls and host attributes are available. Use `bind_runtime` to subscribe to observables, bind controls to data, register cross-feature callbacks, apply initial state from workspace or runtime sources, and invoke routed lifecycle helpers like `setup_routed_runtime` or `bind_routed_feature_lifecycle`. The invariant for `bind_runtime` is: controls exist, siblings are built, runtime services are active.

**route** is the intent dispatch phase. Events delivered to `handle_event` and messages published through `FeatureMessage` flow through declared routing rules. Routing separates the recognition of user intent from the implementation of what to do about it. A feature that needs to respond to the action `"open_file"` registers a handler for that action ID; it does not parse keyboard codes directly. This separation makes the behavior testable and the UI remappable without code changes.

**update** is the frame-time logic phase. Per-frame logic runs in `on_update(host, dt_seconds)`. Keep update logic bounded and lightweight. Use `dt_seconds` for smooth time-based animation rather than frame-count arithmetic. Anything with non-trivial cost — file loading, heavy computation, network round trips — belongs in a cooperative scheduler coroutine or a data pipeline stage, not in `on_update`. Features that block `on_update` for more than a millisecond will visibly degrade frame rate.

**draw** is the custom rendering escape hatch. Most features do not override `draw` because the control tree handles all standard rendering. Override `draw(host, screen)` only when controls genuinely cannot express the visual output you need — particles, procedural terrain, custom compositing effects, debug overlays. Keep rendering code separate from model mutation to prevent frame-order-dependent bugs.

### Message and Logic Coordination

`FeatureMessage` enables loosely coupled communication between features. A feature calls its messaging API to publish a named message with an optional payload dictionary. Any feature that has registered a handler for that name receives the delivery. Neither party holds a direct reference to the other. This prevents features from coupling to each other's internal implementations and makes each feature independently replaceable.

Use `FeatureMessage` for discrete events: "computation finished," "user confirmed dialog," "item selected." Use observable values for continuous state: "current count," "selected item," "progress fraction." The heuristic is: if a consumer needs the value over time and should display it in a reactive widget, use an observable. If a consumer needs to be notified that something happened once and should take an action in response, use a message.

`LogicFeature` naturally serves as the coordination hub in multi-feature scenes. A logic feature owns domain processing, maintains shared observable state, and publishes `FeatureMessage` events when significant state transitions occur. One or more UI features subscribe to the observables and handle the messages. This split keeps UI features small and focused on presentation and the logic feature independently testable.

### When to Use Routed Runtime Specs

`RoutedRuntimeSpec` and `RoutedFeatureLifecycleSpec` reduce boilerplate for features with dense routing concerns. When a single feature needs to register multiple action hotkeys, a shortcut help overlay, a task-panel focus toggle, and several event subscriptions — all of which should bind and unbind in synchrony with the feature's lifecycle — declaring them as a `RoutedRuntimeSpec` is far cleaner than writing manual registration and cleanup code.

`setup_routed_runtime` performs coordinated registration of all elements declared in a `RoutedRuntimeSpec` during the bind phase. `bind_routed_feature_lifecycle` performs the corresponding setup for `RoutedFeatureLifecycleSpec`, registering action hotkeys, shortcut overlays, and event subscriptions as a single coordinated operation. `shutdown_routed_feature_lifecycle` is the symmetric teardown: it unregisters all elements that were registered during bind, preventing stale handlers from surviving scene transitions.

The practical benefit of routed lifecycle specs is that registration and deregistration become a single declaration rather than paired imperative calls spread across `bind_runtime` and `shutdown_runtime`. This eliminates the class of bug where a feature registers a hotkey but forgets to unregister it, leaving an active binding after the feature is gone.

---

## Main Systems Reference

[Back to Table of Contents](#table-of-contents)

The chapters below are organized in dependency order: each chapter assumes you have read the chapters before it. Every chapter follows the same structure: what it is and why it exists, mental model and lifecycle placement, primary public APIs and key types, typical usage flow, minimal example, advanced patterns, common mistakes, cross-links, and a back-to-top link.

---

### 8.1 Application Bootstrap and Host Configuration

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Application bootstrap is the deterministic assembly layer for gui_do. Its job is to take a complete declarative description of an application — all scenes, features, actions, windows, fonts, cursors, accessibility annotations, and runtime policies — and materialize a fully wired runtime in a single coordinated pass. Without this layer, each application would have to manually construct and connect runtime services in the right order, which creates fragile setup code that is difficult to test and maintain. The bootstrap system eliminates that problem: you describe what you want, and the framework figures out how to produce it.

#### Mental model and lifecycle placement

Think of the host object as a plain Python object that bootstrap populates. Before `bootstrap_host_application` is called, the host has no runtime attributes. After it returns, `host.app` is the live `GuiApplication` instance, and every declared feature, action registry entry, window presentation spec, font role, cursor, and scene is wired and ready. The entire application lifecycle then flows through `host.app.run_entrypoint()`.

Bootstrap sits at the very beginning of the application lifecycle, before any scene activates and before any feature lifecycle phase runs. It is intentionally a one-shot operation: you construct the config once, hand it to bootstrap, and then run the event loop.

#### Primary public APIs and key types

**Config and bootstrap:** `HostApplicationConfig`, `bootstrap_host_application`, `build_host_application_config`, `HostApplicationBindingSpec`, `TelemetryConfig`.

**Core spec types (Tier 1):** `FeatureSpec`, `WindowSpec`, `RuntimeSceneSpec`, `ActionSpec`, `StaticAccessibilitySpec`, `CursorSpec`, `SceneRootSpec`, `AnchoredWindowSpec`, `LogicBindingSpec`, `TaskPanelButtonSpec`, `TaskPanelWindowToggleGroupSpec`, `SceneCommandPaletteSpec`, `ActionHotkeySpec`, `ControlKeyBindingSpec`, `SceneTaskPanelSpec`, `TaskPanelLinearLayoutSpec`, `TaskPanelSceneNavButtonSpec`, `EventSubscriptionSpec`, `ShortcutOverlaySpec`, `TaskPanelFocusToggleSpec`, `RoutedRuntimeSpec`, `RoutedFeatureLifecycleSpec`, `FeatureWindowBundleBindingSpec`, `WindowToggleBindingSpec`, `SceneSetupBindingSpec`, `RuntimeSceneBindingSpec`, `SceneRootBindingSpec`, `CursorBindingSpec`, `FontRoleBindingSpec`, `ActionBindingSpec`, `PaletteBindingSpec`, `SceneBundleBindingSpec`, `HostApplicationBindingSpec`, `TabbedPresenterSpec`, `AccessibilitySequenceSpec`, `TabBuilderSpec`, `NotificationSpec`.

**Builder helpers (Tier 1):** `build_host_application_config`, `build_feature_specs`, `build_feature_window_bundle_specs`, `build_window_toggle_specs`, `build_scene_setup_specs`, `build_runtime_scene_specs`, `build_scene_root_specs`, `build_cursor_specs`, `build_font_role_specs`, `build_scene_nav_actions`, `build_action_specs`, `build_scene_bundle_specs`, `build_static_accessibility_specs`, `build_notification_center`, `make_window_toggle_spec`, `make_scene_nav_action`, `make_exit_action`, `make_palette_open_action`, `make_static_accessibility_spec`.

**App and scene types (Tier 2):** `GuiApplication`, `create_display`, `SceneTransitionManager`, `SceneTransitionStyle`, `apply_scene_setup_specs`.

#### Typical usage flow

1. Choose between direct `HostApplicationConfig` construction or the `HostApplicationBindingSpec` + `build_host_application_config` approach. Direct construction is simpler for small apps; binding specs scale better.
2. Declare all scenes via `SceneSetupSpec` (or `SceneBundleBindingSpec` in the binding approach).
3. Declare all features via `FeatureSpec`.
4. Declare actions, runtime scene policies, font roles, cursors, and accessibility specs.
5. Call `bootstrap_host_application(host, config)`.
6. Call `host.app.run_entrypoint(target_fps=...)`.

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

For multi-scene, multi-window applications, use `HostApplicationBindingSpec` with bundle helpers. This approach automatically generates related spec cross-references that would be tedious to write manually:

```python
from gui_do import (
    ActionBindingSpec,
    FeatureWindowBundleBindingSpec,
    HostApplicationBindingSpec,
    SceneBundleBindingSpec,
    build_host_application_config,
)


cfg = build_host_application_config(
    HostApplicationBindingSpec(
        display_size=(1920, 1080),
        window_title="Full App",
        fonts={"default": {"system": "arial", "size": 14}},
        initial_scene_name="main",
        scene_bundle_entries=(
            SceneBundleBindingSpec(
                scene_name="main",
                pretty_name="Main",
                include_nav_action=True,
                nav_action_id="nav_main",
                nav_label="Go to Main",
            ),
        ),
        feature_window_bundle_entries=(
            FeatureWindowBundleBindingSpec(
                "_tools_feature",
                ToolsFeature,
                "tools",
                task_panel_label="Tools",
                task_panel_style="round",
            ),
        ),
        action_entries=(
            ActionBindingSpec(kind="exit", action_id="exit", label="Exit", category="File"),
        ),
    )
)
```

`SceneBundleBindingSpec` automatically generates the `SceneSetupSpec`, `RuntimeSceneSpec`, `SceneRootSpec`, and navigation action entries for a scene. `FeatureWindowBundleBindingSpec` generates all the window toggle wiring for a feature-window pair.

#### Common mistakes and anti-patterns

- Manually mutating host attributes after bootstrap in ways that bypass the spec graph. For example, registering new actions by reaching into `host.action_manager` directly after bootstrap creates entries that are not tracked by the declarative config, which breaks scene-scoped teardown.
- Declaring feature `scene_name` values that do not match any `scene_name` in `scene_specs`. This silently places a feature in an unactivatable scene.
- Forgetting `initial_scene_name` in `HostApplicationConfig`. Without it, the runtime has no entry scene and startup behavior is undefined.
- Using `FeatureSpec` factory functions that have side effects at construction time. Spec factories should be pure — they should only create and return the feature instance.

#### Cross-links to related systems

See [8.2 Feature Lifecycle and Feature Types](#82-feature-lifecycle-and-feature-types) for how features are activated after bootstrap, [8.3 Events, Actions, Input Mapping, and Routing](#83-events-actions-input-mapping-and-routing) for action registry wiring, and [8.11 Persistence and Workspace/Session State](#811-persistence-and-workspacesession-state) for workspace restore behavior that runs after bootstrap.

[Back to Table of Contents](#table-of-contents)

---

### 8.2 Feature Lifecycle and Feature Types

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Feature lifecycle orchestration is the primary behavior model in gui_do. The lifecycle system provides a principled way to structure application code so that construction, wiring, event handling, frame updates, and rendering each happen in a defined phase with clear invariants. Without this structure, it is easy to accidentally write code that assumes something exists before it is created, or that leaves subscriptions active after a scene exits.

The framework activates and deactivates complete feature sets as scenes transition. This makes multi-scene applications straightforward: each scene's features start cleanly and stop cleanly, with no risk of stale state leaking from one scene to the next.

#### Mental model and lifecycle placement

Think of each feature as a self-contained behavioral object with separated phases. The lifecycle is not an ad-hoc collection of callbacks; it is a deliberate contract. `build` constructs; `bind_runtime` wires; `handle_event` routes; `on_update` progresses; `draw` renders. Mixing responsibilities across phases is the single most common source of lifecycle bugs.

Features are registered via `FeatureSpec` in the bootstrap config and instantiated by `FeatureManager`. They are not singletons; each feature instance belongs to exactly one scene context.

#### Primary public APIs and key types

**Feature base classes (Tier 1):** `Feature`, `DirectFeature`, `LogicFeature`, `RoutedFeature`, `FeatureMessage`, `FeatureManager`, `ScenePresentationModel`, `SceneSetupSpec`, `setup_standard_font_roles`.

**Spec types:** `FeatureSpec`, `RoutedRuntimeSpec`, `RoutedFeatureLifecycleSpec`.

**Routed lifecycle helpers (Tier 18):** `setup_routed_feature_runtime`, `register_routed_feature_companions`, `bind_routed_feature_lifecycle`, `shutdown_routed_feature_lifecycle`, `bind_feature_logic_aliases`, `register_companion_logic_features`, `ActiveTabUpdateRouter`, `TabLayoutContext`.

#### Typical usage flow

1. Choose the feature type that matches the responsibility: `Feature` for interactive UI, `LogicFeature` for background computation or shared state, `DirectFeature` for full-screen rendering, `RoutedFeature` for action-routing-heavy features.
2. Declare `HOST_REQUIREMENTS` as a class attribute mapping phase names to required host attribute tuples.
3. Implement `build` to create controls and observables.
4. Implement `bind_runtime` to wire subscriptions, cross-feature links, and routed lifecycle helpers.
5. Implement `handle_event`, `on_update`, and `draw` as needed.
6. Implement `shutdown_runtime` to dispose subscriptions and clean up routed registrations.
7. Register the feature via `FeatureSpec` in the bootstrap config.

#### Minimal example

```python
from pygame import Rect

from gui_do import Feature, LabelControl, ObservableValue, PanelControl


class StatusFeature(Feature):
    HOST_REQUIREMENTS = {"build": ("app",), "bind_runtime": ()}

    def __init__(self) -> None:
        super().__init__("status", scene_name="main")
        self.status_text = ObservableValue("Ready")
        self._unsub = None

    def build(self, host) -> None:
        self.root = host.app.add(
            PanelControl("status_root", Rect(8, 8, 320, 80)),
            scene_name="main",
        )
        self.label = self.root.add(
            LabelControl("status_label", Rect(8, 8, 260, 24), "Ready")
        )

    def bind_runtime(self, host) -> None:
        self._unsub = self.status_text.subscribe(
            lambda text: setattr(self.label, "text", text)
        )

    def shutdown_runtime(self, host) -> None:
        if self._unsub is not None:
            self._unsub()
            self._unsub = None
```

#### Advanced pattern(s)

The most scalable pattern for complex features is the logic plus presentation split. A `LogicFeature` owns all domain state and computation; a companion `RoutedFeature` owns all UI and action routing. Wire them together through `register_routed_feature_companions` so their lifecycles are synchronized:

```python
class AnalysisLogicFeature(LogicFeature):
    HOST_REQUIREMENTS = {"bind_runtime": ()}

    def __init__(self) -> None:
        super().__init__("analysis_logic", scene_name="analysis")
        self.result = ObservableValue(None)
        self.progress = ObservableValue(0.0)

    def bind_runtime(self, host) -> None:
        # Start background work via cooperative scheduler
        pass


class AnalysisFeature(RoutedFeature):
    HOST_REQUIREMENTS = {"build": ("app",), "bind_runtime": ()}

    def __init__(self) -> None:
        super().__init__("analysis", scene_name="analysis")

    def build(self, host) -> None:
        # Create UI controls for result display
        pass

    def bind_runtime(self, host) -> None:
        logic: AnalysisLogicFeature = host.analysis_logic
        self._unsub_result = logic.result.subscribe(self._on_result)
        self._unsub_progress = logic.progress.subscribe(self._on_progress)
```

Use `RoutedFeatureLifecycleSpec` with `bind_routed_feature_lifecycle` to declaratively register action hotkeys, shortcut overlays, focus toggles, and event subscriptions together in one coordinated operation. Call `shutdown_routed_feature_lifecycle` in teardown to ensure symmetric cleanup.

#### Common mistakes and anti-patterns

- Subscribing to observables in `build` before sibling features and their state are guaranteed to exist. Always subscribe in `bind_runtime`.
- Implementing expensive computation directly in `on_update` instead of delegating to a cooperative scheduler coroutine or data pipeline.
- Using `RoutedFeatureLifecycleSpec` without implementing the matching `shutdown_routed_feature_lifecycle` call. This leaves action hotkeys and event subscriptions active after the feature's scene deactivates.
- Creating controls in `handle_event` or `on_update`. Controls must be created in `build` to participate in the scene tree correctly.

#### Cross-links to related systems

See [8.1 Application Bootstrap and Host Configuration](#81-application-bootstrap-and-host-configuration) for how features are registered, [8.3 Events, Actions, Input Mapping, and Routing](#83-events-actions-input-mapping-and-routing) for event routing to feature handlers, [8.4 State and Observables](#84-state-and-observables) for the reactive data model, and [8.10 Scheduling, Timing, Animation, and Transitions](#810-scheduling-timing-animation-and-transitions) for background work patterns.

[Back to Table of Contents](#table-of-contents)

---

### 8.3 Events, Actions, Input Mapping, and Routing

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

The events, actions, and input mapping system translates raw pygame input into stable semantic events and routes them through a deterministic policy chain. Without this layer, every feature would need to implement its own input interpretation, key-scope filtering, and routing fallback logic, producing inconsistent behavior and duplicate code across the application. This system centralizes all of that so feature authors deal only with clean, typed `GuiEvent` objects and named action identifiers.

#### Mental model and lifecycle placement

The mental model has three distinct concerns. The event system normalizes and routes `GuiEvent` objects through a stable dispatch pipeline — overlays first, then focus-based keyboard routing, then scene and feature handlers. The action system maps semantic action names to executing handlers. The input map bridges the two: keys and chords in the input map fire action IDs when triggered, and the action manager looks up and executes the corresponding handler.

This system operates during the frame loop, after features have been built and bound. It does not participate in `build` or `bind_runtime` directly, though features register action handlers and subscriptions during those phases.

#### Primary public APIs and key types

**Event types (Tier 4):** `GuiEvent`, `EventType`, `EventPhase`, `EventManager`, `EventBus`, `InputSnapshot`, `Signal`, `SignalConnection`, `ValueChangeCallback`, `ValueChangeReason`, `GestureRecognizer`, `EventRecorder`, `EventPlayback`, `RecordedEvent`.

**Action and input types (Tier 4):** `ActionManager`, `ActionDescriptor`, `ActionRegistry`, `ActionContext`, `ActionMiddleware`, `InputMap`, `InputBinding`, `KeyChordManager`, `KeyChord`, `ChordStep`.

**Focus routing types (Tier 4):** `FocusManager`, `FocusScope`, `FocusScopeManager`, `WindowFocusManager`, `FocusRing`.

**Interaction state machine (Tier 30):** `InteractionPhase`, `InteractionContext`, `InteractionTransition`, `InteractionStateMachine`.

**Spec types (Tier 1):** `ActionSpec`, `ActionHotkeySpec`, `ControlKeyBindingSpec`, `EventSubscriptionSpec`, `SceneCommandPaletteSpec`.

**`EventType` values:** `PASS`, `QUIT`, `KEY_DOWN`, `KEY_UP`, `MOUSE_BUTTON_DOWN`, `MOUSE_BUTTON_UP`, `MOUSE_MOTION`, `MOUSE_WHEEL`, `TEXT_INPUT`, `TEXT_EDITING`.

**`EventPhase` values:** `CAPTURE`, `TARGET`, `BUBBLE`.

**`GuiEvent` fields:** `kind`, `type`, `key`, `pos`, `rel`, `raw_pos`, `raw_rel`, `button`, `wheel_x`, `wheel_y`, `mod`, `text`, `control_id`, `group`, `window`, `task_panel`, `task_id`, `error`, `source_event`, `phase`, `propagation_stopped`, `default_prevented`.

**`GuiEvent` helpers:** `is_kind`, `is_key_down`, `is_key_up`, `is_mouse_down`, `is_mouse_up`, `is_mouse_motion`, `is_mouse_wheel`, `is_text_event`, `is_left_down`, `is_left_up`, `is_right_down`, `is_right_up`, `is_middle_down`, `is_middle_up`, `clone`, `with_phase`, `stop_propagation`, `prevent_default`, `wheel_delta`, `collides`.

#### Typical usage flow

1. Declare named actions with `ActionSpec` entries in the bootstrap config.
2. Bind hotkeys with `ActionHotkeySpec` or `ControlKeyBindingSpec` entries, or use `RoutedRuntimeSpec` for auto-wiring.
3. Implement action handlers on the host object or in feature code.
4. In `handle_event`, use `GuiEvent` helper methods rather than raw attribute comparisons for readable, future-proof event checks.
5. Return `True` from `handle_event` when the event is consumed; return `None` or `False` to pass it on.

#### Minimal example

```python
# In bootstrap config
action_specs = (
    ActionSpec(action_id="exit", label="Exit", kind="exit"),
    ActionSpec(action_id="palette_open", label="Open Command Palette", kind="palette_open"),
)

# In a feature's handle_event
def handle_event(self, host, event) -> bool:
    if event.is_key_down() and event.key == pygame.K_r:
        self._refresh()
        return True
    return False
```

#### Advanced pattern(s)

Use `InteractionStateMachine` for guarded multi-phase pointer interactions. This is useful for drag-and-drop, resize handles, and multi-step gesture recognition where each phase has explicit entry conditions and exit transitions:

```python
from gui_do import (
    InteractionPhase,
    InteractionStateMachine,
    InteractionTransition,
)


sm = InteractionStateMachine(initial=InteractionPhase.IDLE)
sm.add_transition(
    InteractionTransition(
        from_phase=InteractionPhase.IDLE,
        to_phase=InteractionPhase.PRESSING,
        guard=lambda ctx: ctx.event.is_left_down(),
        action=self._begin_drag,
    )
)
```

For deterministic regression testing, record live event sequences with `EventRecorder` and replay them with `EventPlayback`. This captures the exact sequence of normalized `GuiEvent` objects seen during a test run and allows the sequence to be replayed precisely later.

For complex multi-step key sequences, use `KeyChordManager` with `KeyChord` and `ChordStep` to register chord sequences that fire only when the full sequence is completed.

#### Common mistakes and anti-patterns

- Handling raw pygame events in feature code by checking `event.source_event` attributes directly instead of using `GuiEvent` helper methods. This bypasses normalization and produces platform-dependent behavior.
- Assuming action handlers are globally registered. Actions registered via `ActionSpec` are scene-scoped. They are active only when the scene they belong to is active.
- Forgetting to respect `propagation_stopped`. When processing events in custom routing loops or feature composites, always check whether the event has been consumed before processing it further.
- Using `bind_global_key` for non-command-palette uses without understanding that global keys fire before any focus or overlay check.

#### Cross-links to related systems

See [8.2 Feature Lifecycle and Feature Types](#82-feature-lifecycle-and-feature-types) for how features receive and handle events, [8.7 Focus and Accessibility](#87-focus-and-accessibility) for how focus state affects routing order, and [8.8 Overlays, Dialogs, Notifications, and Command Surfaces](#88-overlays-dialogs-notifications-and-command-surfaces) for how overlays intercept routing.

[Back to Table of Contents](#table-of-contents)

---

### 8.4 State and Observables

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Reactive state management is the preferred data model for any value in gui_do that drives UI. Instead of writing imperative refresh calls every time a value changes, you express values as observables and let consumers subscribe once. The producer changes the value; all consumers update automatically. This decoupling makes features independently testable, makes UI consistently synchronized, and eliminates an entire category of "forgot to update the label" bugs.

#### Mental model and lifecycle placement

Observables are the data bus. Features write values into observables; controls and sibling features read values from observables through subscriptions. The framework itself is not in this path — observable subscriptions are pure Python callbacks, and the reactive system is entirely library-level, not framework-level. This means you can use observables in tests without any framework initialization.

Create observables in feature `__init__` or `build`. Subscribe in `bind_runtime`. Dispose subscriptions in `shutdown_runtime`. This ordering guarantees that subscribers are active when they should be and inactive when the feature is gone.

#### Primary public APIs and key types

**Reactive primitives (Tier 3):** `ObservableValue`, `ObservableList`, `ObservableDict`, `CollectionChange`, `ChangeKind`, `ComputedValue`, `PresentationModel`, `reactive_batch`, `is_batching`, `InvalidationTracker`.

**Binding and view helpers (Tier 3):** `Binding`, `BindingGroup`, `CollectionView`, `CollectionViewQuery`, `ObservableStream`, `SelectionModel`, `SelectionMode`.

**Transactional state store (Tier 27):** `AppStateStore`, `StateSelector`, `StateTransaction`.

#### Typical usage flow

1. Create an `ObservableValue` (or `ObservableList`/`ObservableDict`) in feature initialization.
2. Create controls that will display the value in `build`.
3. Subscribe the control update logic to the observable in `bind_runtime`.
4. Mutate the observable's `.value` attribute anywhere business logic requires it; subscribers are notified automatically.
5. Dispose the subscription callable in `shutdown_runtime`.

#### Minimal example

```python
from gui_do import ObservableValue


class CounterFeature(Feature):
    def __init__(self) -> None:
        super().__init__("counter", scene_name="main")
        self.count = ObservableValue(0)
        self._unsub = None

    def bind_runtime(self, host) -> None:
        self._unsub = self.count.subscribe(
            lambda v: setattr(self.label, "text", str(v))
        )

    def on_update(self, host, dt) -> None:
        self.count.value += 1

    def shutdown_runtime(self, host) -> None:
        if self._unsub is not None:
            self._unsub()
            self._unsub = None
```

#### Advanced pattern(s)

For applications with many features sharing the same domain state, use `AppStateStore` as a single source of truth. Derive feature-local reactive slices with `StateSelector`, which creates computed observables derived from specific store fields. Apply coordinated multi-field mutations with `StateTransaction` so subscribers see the fully updated state rather than intermediate partial states:

```python
from gui_do import AppStateStore, StateSelector, StateTransaction


store = AppStateStore({"count": 0, "name": "", "active": False})
count_selector = StateSelector(store, lambda s: s["count"])

# count_selector behaves like ObservableValue for consumers
count_selector.subscribe(lambda v: print(f"Count changed to {v}"))

# Atomic multi-field update
with StateTransaction(store) as tx:
    tx["count"] = 42
    tx["name"] = "Alice"
```

Use `CollectionView` with `CollectionViewQuery` to create sorted and filtered live views of `ObservableList` data. The view re-sorts and re-filters automatically when the source list changes, making it suitable for driving `ListViewControl` or `DataGridControl` with minimal coupling between the data model and the presentation layer.

Use `reactive_batch` whenever you need to apply multiple related observable updates that should fire downstream subscribers only once:

```python
from gui_do import reactive_batch

with reactive_batch():
    self.title.value = "New Title"
    self.count.value = 0
    self.active.value = True
# All three subscribers fire here, once, after all mutations
```

#### Common mistakes and anti-patterns

- **Polling in `on_update`.** Calling `observable.value` every frame to check for changes wastes CPU and introduces up to one frame of latency. Subscribe to the observable and react only when the value actually changes.
- **Subscribing in `build`.** Sibling features may not have finished building yet, so cross-feature observables may not exist. Always subscribe in `bind_runtime`.
- **Leaking subscriptions.** `subscribe` returns a callable that must be called to unsubscribe. If you discard the return value or forget to call it at teardown, the subscription remains active and fires on dead objects.
- **Using plain Python lists or dicts for shared state.** Plain collections are invisible to the reactive system. If two features share a plain list, mutations in one feature do not notify the other. Always use `ObservableList` or `ObservableDict` for shared mutable collections.

#### Cross-links to related systems

See [8.2 Feature Lifecycle and Feature Types](#82-feature-lifecycle-and-feature-types) for lifecycle-safe subscription management, [8.5 Controls and Control Composition](#85-controls-and-control-composition) for how controls bind to observable values, and [8.11 Persistence and Workspace/Session State](#811-persistence-and-workspacesession-state) for serializing and restoring state store snapshots.

[Back to Table of Contents](#table-of-contents)

---

### 8.5 Controls and Control Composition

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Controls are the reusable UI primitives from which gui_do interfaces are assembled. Rather than drawing directly to surfaces in every feature, you compose typed control objects that handle hit-testing, focus eligibility, layout participation, and rendering in a consistent, predictable way. The control tree model ensures that all of these concerns are coordinated without features needing to implement any of them manually.

#### Mental model and lifecycle placement

Controls form a parent–child tree rooted at scene root panels. A feature owns exactly one root `PanelControl` that it registers with the scene, and all of its UI lives inside that root. Controls never reach across feature boundaries — a feature that needs data from another feature reads that data through observables and messages, not by holding a reference to a sibling feature's control.

Controls are created in `build` and wired in `bind_runtime`. Modifying the control tree outside `build` requires care; adding or removing controls at runtime can affect layout passes and focus ring state in ways that are not always obvious.

#### Primary public APIs and key types

**Primary controls (Tier 12):** `PanelControl`, `LabelControl`, `ButtonControl`, `ToggleControl`, `SliderControl`, `ScrollbarControl`, `CanvasControl`, `CanvasEventPacket`, `CanvasViewport`, `FrameControl`, `ImageControl`, `ArrowBoxControl`, `ButtonGroupControl`, `TabControl`, `TabItem`, `DockWorkspacePanel`.

**Extended controls (Tier 13):** `TextInputControl`, `TextAreaControl`, `RichLabelControl`, `DropdownControl`, `DropdownOption`, `ListViewControl`, `ListItem`, `OverlayPanelControl`, `DataGridControl`, `GridColumn`, `GridRow`, `TreeControl`, `TreeNode`, `SplitterControl`, `SpinnerControl`, `RangeSliderControl`, `ColorPickerControl`, `ScrollViewControl`, `ProgressBarControl`, `AnimatedImageControl`, `ErrorBoundary`, `WindowControl`, `TaskPanelControl`, `WindowPresenter`, `MenuBarControl`, `MenuEntry`, `SceneMenuStripControl`, `NotificationPanelControl`, `PropertyInspectorPanel`, `ToolbarControl`, `ToolbarItem`, `StatusBarControl`, `StatusSlot`, `ExpanderControl`, `DatePickerControl`, `TimePickerControl`, `BreadcrumbControl`, `BreadcrumbItem`, `SplitButtonControl`, `SplitButtonOption`, `ChipInputControl`.

**Builder helpers (Tier 1):** `ControlDefinition`, `build_specs_from_column_section`.

#### Typical usage flow

1. In `build`, create a root `PanelControl` with the desired bounds and add it to the scene via `host.app.add(root, scene_name=...)`.
2. Add child controls to the root with `root.add(...)`.
3. Connect observable subscriptions and callback wiring in `bind_runtime`.
4. Clean up subscriptions in `shutdown_runtime`.

#### Minimal example

```python
from pygame import Rect

from gui_do import (
    ButtonControl,
    Feature,
    LabelControl,
    ObservableValue,
    PanelControl,
)


class MyFeature(Feature):
    def __init__(self) -> None:
        super().__init__("my_feature", scene_name="main")
        self.message = ObservableValue("Ready")
        self._unsub = None

    def build(self, host) -> None:
        self.root = host.app.add(
            PanelControl("my_root", Rect(0, 0, 400, 300)),
            scene_name="main",
        )
        self.label = self.root.add(LabelControl("msg", Rect(8, 8, 384, 24), "Ready"))
        self.root.add(
            ButtonControl("action_btn", Rect(8, 40, 120, 28), "Do It", on_click=self._on_click)
        )

    def bind_runtime(self, host) -> None:
        self._unsub = self.message.subscribe(
            lambda text: setattr(self.label, "text", text)
        )

    def shutdown_runtime(self, host) -> None:
        if self._unsub:
            self._unsub()

    def _on_click(self, event) -> None:
        self.message.value = "Done"
```

#### Advanced pattern(s)

The presenter pattern separates window construction from feature lifecycle management. Subclass `WindowPresenter` and implement the window's control layout inside its `build` method. Instantiate the presenter from the feature's `build`. This is especially effective when combined with `TabbedPresenterSpec` and `TabBuilderSpec` for multi-tab window content where each tab section has its own builder:

```python
class ToolsWindowPresenter(WindowPresenter):
    def build(self, host, root) -> None:
        self.input = root.add(TextInputControl("query", Rect(8, 8, 300, 28)))
        self.results = root.add(ListViewControl("results", Rect(8, 44, 300, 200)))
```

Use `ErrorBoundary` to wrap any control subtree where third-party or plugin-managed controls might raise during rendering. The boundary catches the exception and renders a neutral fallback frame rather than crashing the entire scene frame.

Use `CanvasControl` with `CanvasViewport` for custom drawing surfaces that need pan/zoom. `CanvasEventPacket` delivers pointer events in canvas-local coordinates, so your drawing code does not need to perform coordinate transforms manually.

For declarative property panels with labeled columns, use `ControlDefinition` objects and `build_specs_from_column_section` to generate the control and label pairs from a data-driven description.

#### Common mistakes and anti-patterns

- Creating direct cross-feature control references. If Feature A holds a reference to Feature B's `LabelControl`, changing Feature B's internal structure breaks Feature A. Always use observables or `FeatureMessage` for cross-feature communication.
- Using controls as the source of truth for application state. Reading `label.text` to determine application state is fragile. Controls should mirror observable state, not own it.
- Building or modifying controls outside the `build` phase (e.g., adding child panels in `on_update`). Late control additions can miss layout registration and may not appear in the focus ring.

#### Cross-links to related systems

See [8.2 Feature Lifecycle and Feature Types](#82-feature-lifecycle-and-feature-types) for when and how controls are created, [8.4 State and Observables](#84-state-and-observables) for binding observable values to control properties, [8.6 Layout Systems](#86-layout-systems) for positioning controls without hardcoded pixel arithmetic, and [8.9 Scene, Window, and Task-Panel Presentation Models](#89-scene-window-and-task-panel-presentation-models) for window-level composition.

[Back to Table of Contents](#table-of-contents)

---

### 8.6 Layout Systems

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Layout engines manage spatial relationships between controls so that features do not need to hardcode pixel positions that break when the display size changes. gui_do provides a family of layout engines covering the common spatial patterns: flex-direction flow, fixed grid tracks, wrapping flow, anchor-based constraints, adaptive breakpoint switching, and dock-pane workbenches.

#### Mental model and lifecycle placement

Each layout engine owns a region and arranges its children according to its own rules. Engines run as a coordinated layout pass triggered by the framework's `LayoutManager` before each draw. You do not call layout manually per frame; you describe the spatial policy once, and the framework applies it when needed.

Choose the simplest layout family that satisfies your requirements. Use flex for toolbars and side-by-side panels. Use grid for forms and data tables. Use constraint for dialogs with relative placement. Use adaptive policy when the arrangement must change at specific display size thresholds.

#### Primary public APIs and key types

**Core layout types (Tier 8):** `LayoutAxis`, `LayoutManager`, `WindowTilingManager`, `ConstraintLayout`, `AnchorConstraint`, `DockPane`, `DockTabs`, `DockSplit`, `DockWorkspace`, `FlexLayout`, `FlexItem`, `FlexDirection`, `FlexAlign`, `FlexJustify`, `GridLayout`, `GridTrack`, `GridPlacement`, `CellCaretLayout`, `CellCaretState`, `LayoutAnimator`, `LayoutPass`, `MeasureContext`, `ArrangeContext`, `LayoutRoot`, `ResponsiveLayout`, `Breakpoint`, `SnapGrid`, `AlignmentGuide`, `SnapComposer`, `SnapTarget`, `FlowLayout`, `FlowItem`, `Viewport`.

**Adaptive constraint layout (Tier 28):** `ConstraintAttr`, `LayoutConstraint`, `ConstraintSet`, `ConstraintLayoutEngine`, `AdaptivePolicy`, `resolve_adaptive_policy`.

**Virtualization core (Tier 29):** `MeasureMode`, `MeasurePolicy`, `VirtualizedWindow`, `RecyclePool`, `VirtualizationCore`.

#### Typical usage flow

1. Choose the layout family for the region.
2. Instantiate the layout engine with its configuration parameters.
3. Add controls as layout items with their sizing policies.
4. Attach the engine to the root panel or region. The framework will run layout before draw.

#### Minimal example

```python
from gui_do import FlexAlign, FlexDirection, FlexItem, FlexJustify, FlexLayout

layout = FlexLayout(direction=FlexDirection.ROW, gap=8, align=FlexAlign.CENTER)
layout.add(FlexItem(control=self.sidebar, grow=0, basis=200))
layout.add(FlexItem(control=self.main_area, grow=1))
self.root.layout = layout
```

#### Advanced pattern(s)

Use `ConstraintLayoutEngine` combined with `AdaptivePolicy` and `resolve_adaptive_policy` for panels that rearrange at specific viewport width breakpoints. This pattern is useful for responsive panels that need to switch from a two-column arrangement at wide display sizes to a single-column stack at narrow sizes:

```python
from gui_do import (
    AdaptivePolicy,
    ConstraintAttr,
    ConstraintLayoutEngine,
    ConstraintSet,
    LayoutConstraint,
    resolve_adaptive_policy,
)


wide_constraints = ConstraintSet([
    LayoutConstraint(target=self.sidebar, attr=ConstraintAttr.WIDTH, constant=200),
    LayoutConstraint(target=self.main_area, attr=ConstraintAttr.LEFT,
                     source=self.sidebar, source_attr=ConstraintAttr.RIGHT, constant=8),
])
narrow_constraints = ConstraintSet([
    LayoutConstraint(target=self.sidebar, attr=ConstraintAttr.WIDTH, multiplier=1.0),
])
policy = AdaptivePolicy(breakpoints={800: wide_constraints, 0: narrow_constraints})
engine = ConstraintLayoutEngine(resolve_adaptive_policy(policy, current_width=1280))
self.root.layout = engine
```

For dock-based workbench layouts, use `DockWorkspace` with `DockPane`, `DockSplit`, and `DockTabs`. This provides the familiar split-pane, tabbed-editor pattern seen in IDE-style applications.

Use `VirtualizationCore` with `RecyclePool` when building list or grid views with thousands of items. Virtualization ensures that only the visible subset of controls is instantiated and rendered, reducing memory and draw time proportionally.

#### Common mistakes and anti-patterns

- Mixing conflicting layout systems in one container without clear ownership. When a container has both a `FlexLayout` assigned and manually positioned children, the manual positions will be overwritten by the flex pass.
- Hardcoding pixel dimensions in `FlexItem` `basis` values instead of using `Breakpoint`-based responsive policies. This prevents the layout from adapting to different display sizes.
- Calling layout methods before controls are added to the tree. Layout runs a measure pass that requires the control's preferred size, which is not valid until the control is initialized and parented.

#### Cross-links to related systems

See [8.5 Controls and Control Composition](#85-controls-and-control-composition) for how controls are added to layout containers, [8.7 Focus and Accessibility](#87-focus-and-accessibility) for how layout affects focus ring membership, and [8.9 Scene, Window, and Task-Panel Presentation Models](#89-scene-window-and-task-panel-presentation-models) for how layout engines apply within floating windows.

[Back to Table of Contents](#table-of-contents)

---

### 8.7 Focus and Accessibility

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Focus management keeps keyboard interaction coherent: at any given moment exactly one control receives keyboard events. Accessibility semantics expose a parallel, machine-readable role tree that testing tools and assistive technology can read without any dependency on control rendering. These two concerns are logically separate but operationally linked: losing focus ring coherence silently breaks keyboard accessibility.

#### Mental model and lifecycle placement

`FocusManager` maintains the focused control. `FocusScopeManager` groups controls into scopes so that when a modal surface is active, focus can be locked to that scope's subtree and cannot cycle out to the underlying scene's controls. `AccessibilityTree` is a parallel tree of `AccessibilityNode` objects that mirrors the semantic structure of the live control tree; `AccessibilityBus` delivers `AccessibilityAnnouncement` events for live-region updates.

Focus membership is determined at `build` time when controls are added to the scene tree. Removing a control from the tree (or hiding it) must be coordinated with the focus ring so that subsequent Tab navigation does not stall on invisible targets.

#### Primary public APIs and key types

**Focus types (Tier 4):** `FocusManager`, `FocusScope`, `FocusScopeManager`, `WindowFocusManager`, `FocusRing`.

**Accessibility types (Tier 21):** `AccessibilityRole`, `LivePoliteness`, `AccessibilityNode`, `AccessibilityTree`, `AccessibilityAnnouncement`, `AccessibilityBus`.

**Spec types (Tier 1):** `StaticAccessibilitySpec`, `AccessibilitySequenceSpec`, `TaskPanelFocusToggleSpec`.

**Utility helpers (Tier 18):** `apply_accessibility_sequence`, `apply_accessibility_sequence_from_attrs`, `apply_window_toggle_accessibility`, `collect_window_toggle_controls`, `add_window_toggle_task_panel_controls`, `bind_task_panel_focus_toggle`.

#### Typical usage flow

1. Declare `StaticAccessibilitySpec` entries in `HostApplicationConfig` with semantic `role` and `name` values for each key control.
2. For scene-level sequential focus ordering, declare an `AccessibilitySequenceSpec` and call `apply_accessibility_sequence` in `bind_runtime`.
3. For windows managed by the task panel, declare a `TaskPanelFocusToggleSpec` in `RoutedRuntimeSpec` to ensure that hidden windows are automatically excluded from the focus ring.
4. For custom `CanvasControl` widgets, create `AccessibilityNode` entries with the appropriate role and add them to `AccessibilityTree`.
5. Use `AccessibilityBus` to post `AccessibilityAnnouncement` events when significant runtime state changes (e.g., operation completed, error occurred).

#### Minimal example

```python
from gui_do import AccessibilityNode, AccessibilityRole, AccessibilityTree

tree = AccessibilityTree()
node = AccessibilityNode(role=AccessibilityRole.BUTTON, name="Submit Form")
tree.root.add_child(node)
```

#### Advanced pattern(s)

Use `FocusScope` to lock focus inside a modal dialog's control subtree during its lifetime. When the dialog opens, activate the scope to prevent Tab from cycling out to underlying scene controls. When the dialog closes, deactivate the scope to restore normal focus cycling:

```python
from gui_do import FocusScope, FocusScopeManager

scope = FocusScope(controls=[self.dialog_ok, self.dialog_cancel])
manager = FocusScopeManager()
manager.push_scope(scope)
# ... dialog in use ...
manager.pop_scope()
```

Combine `AccessibilitySequenceSpec` with `apply_accessibility_sequence_from_attrs` for a data-driven approach that assigns Tab order and semantic names from a declarative list. This is simpler and more maintainable than adding nodes individually when the scene has many sequentially ordered controls.

#### Common mistakes and anti-patterns

- Leaving hidden windows in the focus ring. If a window becomes hidden without removing its controls from the ring, Tab navigation stalls on invisible targets. Use `TaskPanelFocusToggleSpec` to handle this automatically for task-panel-managed windows.
- Omitting semantic roles on custom `CanvasControl` widgets. From an accessibility perspective a canvas is opaque; you must add `AccessibilityNode` entries with meaningful roles and names for any interactive regions inside the canvas.
- Building accessibility nodes before the `AccessibilityTree` is initialized. Nodes must be added in `build` or `bind_runtime`, not in `__init__`.

#### Cross-links to related systems

See [8.3 Events, Actions, Input Mapping, and Routing](#83-events-actions-input-mapping-and-routing) for how focus state affects keyboard event routing, [8.5 Controls and Control Composition](#85-controls-and-control-composition) for how controls participate in the focus ring, and [8.8 Overlays, Dialogs, Notifications, and Command Surfaces](#88-overlays-dialogs-notifications-and-command-surfaces) for modal focus capture during overlay lifetime.

[Back to Table of Contents](#table-of-contents)

---

### 8.8 Overlays, Dialogs, Notifications, and Command Surfaces

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Transient and modal surfaces require their own routing and dismissal contract. Overlays intercept events before the main control tree; if an overlay consumes an event, the scene underneath never sees it. Each overlay family (dialogs, toasts, context menus, command palette, tooltips, menu bar, file dialogs, notifications, drag-and-drop, clipboard) has a dedicated manager so that routing, animation, and teardown concerns are localized.

#### Mental model and lifecycle placement

Overlays sit on top of the main scene. The `OverlayManager` processes events first in each frame. Only after the overlay pass concludes do scene-level and feature-level handlers receive events. Handles returned by manager `show` methods are valid only while the overlay is open; always check handle validity before attempting updates on a surface that may have been dismissed.

#### Primary public APIs and key types

**Tier 9:** `OverlayManager`, `OverlayHandle`, `Alignment`, `PlacementResult`, `PopupPlacement`, `Side`, `compute_popup_rect`, `DialogManager`, `DialogHandle`, `ToastManager`, `ToastHandle`, `ToastSeverity`, `ContextMenuManager`, `ContextMenuItem`, `ContextMenuHandle`, `CommandPaletteManager`, `CommandEntry`, `CommandPaletteHandle`, `TooltipManager`, `TooltipHandle`, `MenuBarManager`, `FileDialogManager`, `FileDialogOptions`, `FileDialogHandle`, `NotificationCenter`, `NotificationRecord`, `ResizeManager`, `CursorManager`, `CursorHandle`, `CursorShape`, `DragDropManager`, `DragPayload`, `ClipboardManager`, `TransferData`, `TransferManager`, `ShortcutHelpOverlay`, `ShortcutSection`, `ShortcutEntry`.

**Spec types (Tier 1):** `ShortcutOverlaySpec`, `NotificationSpec`, `CursorSpec`, `CursorBindingSpec`.

#### Dismissal contracts

- **Toasts:** Shown for a configured duration and then auto-dismissed. Pointer clicks within toast bounds are consumed; they do not pass through to underlying controls.
- **Dialogs:** Modal by default. Can be configured to dismiss on Escape or outside-click.
- **Context menus:** Dismiss on outside click or Escape.
- **Command palette:** Dismiss on Escape or after a command is selected.
- **Tooltip:** Shown after pointer dwell; dismissed on pointer leave.
- **File dialog:** Platform-delegated; future native integration may apply.

#### Typical usage flow

```python
# Toast
host.toasts.show("File saved", severity=ToastSeverity.SUCCESS)

# Modal dialog
handle = host.dialogs.show(my_dialog_control, modal=True)
handle.on_dismiss = lambda: self._on_dialog_dismissed()

# Context menu
items = [ContextMenuItem("Copy", on_click=self._copy), ContextMenuItem("Paste", on_click=self._paste)]
host.context_menus.show(items, at=event.pos)
```

#### Minimal example

```python
from gui_do import ToastSeverity


def _on_save(self, event) -> None:
    self._do_save()
    self.host.toasts.show("Saved successfully", severity=ToastSeverity.SUCCESS)
```

#### Advanced pattern(s)

`ShortcutHelpOverlay` with `ShortcutOverlaySpec` in `RoutedRuntimeSpec` provides a toggleable shortcut reference screen that automatically populates itself from the action registry. You can inject `ShortcutSection` entries for manually-documented shortcuts and filter out sections from the action registry that should not be exposed:

```python
from gui_do import ShortcutEntry, ShortcutOverlaySpec, ShortcutSection

spec = ShortcutOverlaySpec(
    toggle_action_name="toggle_shortcuts",
    toggle_key="F1",
    manual_shortcut_lines=[
        ShortcutSection("Canvas", [
            ShortcutEntry("Pan", "Middle-drag"),
            ShortcutEntry("Zoom", "Ctrl+Scroll"),
        ])
    ],
    exclude_section_titles=["Debug"],
)
```

Use `PopupPlacement` and `compute_popup_rect` to position context menus and dropdowns so they avoid clipping at screen edges. Pass the anchor control's screen rect, the preferred `Side`, and the `Alignment`, and the function returns a `PlacementResult` with the final rect.

For drag-and-drop, initiate a drag with `DragDropManager.begin_drag(payload)` where `payload` is a `DragPayload` carrying the transfer data. Register drop targets by calling the manager's registration API. The manager fires drag-enter, drag-leave, and drop events on registered targets.

#### Common mistakes and anti-patterns

- Creating overlays without a dismissal contract. An overlay with no Escape handler, no close button, and no timeout leaves the user stuck with no way to dismiss the surface.
- Expecting toast clicks to pass through to underlying controls. Toast bounds consume pointer events; design toast interactions (e.g., undo actions) to be self-contained within the toast.
- Holding an `OverlayHandle` and calling methods on it after the overlay is dismissed. Always check handle validity or gate on an `on_dismiss` callback.

#### Cross-links to related systems

See [8.3 Events, Actions, Input Mapping, and Routing](#83-events-actions-input-mapping-and-routing) for how overlay routing intercepts the event pipeline, [8.7 Focus and Accessibility](#87-focus-and-accessibility) for modal focus capture during dialog lifetime, and [8.9 Scene, Window, and Task-Panel Presentation Models](#89-scene-window-and-task-panel-presentation-models) for how the command palette and menu bar integrate with scene-level layout.

[Back to Table of Contents](#table-of-contents)

---

### 8.9 Scene, Window, and Task-Panel Presentation Models

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Scenes, windows, and task panels are the primary spatial organizing structures in a gui_do application. A scene defines a top-level interaction mode (e.g., a main desktop, a control gallery, a simulation view). Within a scene, windows are focused work surfaces that can be shown, hidden, and repositioned by the user or by application logic. The task panel is a persistent chrome element that provides discoverable access to window toggles, scene navigation, and frequently used commands. This system coordinates visibility state, focus assignment, action availability, and scene-menu presentation without requiring features to implement any of that coordination themselves.

#### Mental model and lifecycle placement

Think of scenes as application "modes". The active scene determines which features, windows, task panel, and menu strip are live. Windows are independent surfaces within a scene; each can be shown or hidden independently without affecting other windows or the scene itself. The task panel is anchored to the scene chrome and contains buttons wired to window-visibility actions.

This system is configured in the bootstrap spec (scene specs, window specs, task panel specs) and realized at startup. Runtime state changes (toggling windows, transitioning scenes) operate on the live scene presentation model.

#### Primary public APIs and key types

**Spec types (Tier 1):** `ScenePresentationModel`, `WindowSpec`, `AnchoredWindowSpec`, `SceneRootSpec`, `SceneTaskPanelSpec`, `TaskPanelButtonSpec`, `TaskPanelLinearLayoutSpec`, `TaskPanelWindowToggleGroupSpec`, `TaskPanelFocusToggleSpec`, `TaskPanelSceneNavButtonSpec`, `FeatureWindowBundleBindingSpec`, `WindowToggleBindingSpec`, `SceneSetupBindingSpec`, `RuntimeSceneBindingSpec`, `SceneRootBindingSpec`, `TabbedPresenterSpec`, `TabBuilderSpec`, `SceneCommandPaletteSpec`.

**Presentation helpers (Tier 18):** `set_window_visible_state`, `toggle_window_visibility`, `create_anchored_feature_window`, `create_feature_presented_window`, `create_presented_anchored_window`, `create_presented_window_from_spec`, `add_window_scene_menu_strip`, `ensure_scene_task_panel`, `create_task_panel_linear_layout`, `add_task_panel_button`, `add_task_panel_buttons`, `add_task_panel_scene_nav_button`, `add_scene_task_panel_items`, `add_task_panel_window_toggle_group`, `sorted_window_bindings`, `collect_window_toggle_controls`, `apply_window_toggle_accessibility`, `add_window_toggle_task_panel_controls`, `setup_scene_command_palette_key`, `register_window_toggle_tooltips`, `minimize_window_menu_entries`, `build_tools_menu_entries`, `add_standard_scene_menu_strip`, `setup_feature_presenter_tabs`, `setup_feature_presenter_tabs_from_window_content`, `register_window_tab_builder_specs`, `register_window_tab_builders`, `build_tab_builder_specs`, `create_tab_control_from_specs`, `compute_tabbed_window_layout`, `register_window_presentation_specs`, `ActiveTabUpdateRouter`, `TabLayoutContext`.

**Tier 2:** `SceneTransitionManager`, `SceneTransitionStyle`, `apply_scene_setup_specs`.

#### Typical usage flow

1. Declare `WindowSpec` or `AnchoredWindowSpec` entries in the bootstrap config.
2. Implement `WindowPresenter` subclasses to own each window's internal control layout.
3. Use `FeatureWindowBundleBindingSpec` to wire each feature–window pair, including task panel button configuration, in a single binding spec entry.
4. Set `TaskPanelFocusToggleSpec` in `RoutedRuntimeSpec` so the framework automatically removes hidden windows from the focus ring on toggle.
5. At runtime, call `set_window_visible_state` or `toggle_window_visibility` to change window visibility, or use registered action IDs for user-initiated toggles.

#### Minimal example

```python
from gui_do import (
    AnchoredWindowSpec,
    Feature,
    FeatureSpec,
    FeatureWindowBundleBindingSpec,
    HostApplicationBindingSpec,
    SceneBundleBindingSpec,
    WindowPresenter,
    build_host_application_config,
)


class InfoPresenter(WindowPresenter):
    def build(self, host, root) -> None:
        self.label = root.add(LabelControl("info_label", Rect(8, 8, 300, 24), "Ready"))


class InfoFeature(Feature):
    def __init__(self) -> None:
        super().__init__("info", scene_name="main")

    def build(self, host) -> None:
        self.presenter = InfoPresenter()
        create_feature_presented_window(host, self, self.presenter, scene_name="main")
```

#### Advanced pattern(s)

Multi-window scenes with tabbed content use `TabbedPresenterSpec` and `TabBuilderSpec` to declaratively describe each tab's control factory. `create_tab_control_from_specs` assembles the `TabControl` from the specs. `ActiveTabUpdateRouter` routes `on_update` and `draw` calls only to the active tab's presenter, preventing background tabs from performing unnecessary work:

```python
from gui_do import ActiveTabUpdateRouter, TabBuilderSpec, TabbedPresenterSpec

specs = TabbedPresenterSpec(tabs=[
    TabBuilderSpec(tab_id="props", label="Properties", build_fn=self._build_props_tab),
    TabBuilderSpec(tab_id="preview", label="Preview", build_fn=self._build_preview_tab),
])
tab_control = create_tab_control_from_specs(host, specs)
self.router = ActiveTabUpdateRouter(tab_control, specs)
```

Pair `add_standard_scene_menu_strip` with `ScenePresentationModel` to add a consistent window-management menu strip to every scene. The menu strip lists all registered windows with checkmarks indicating current visibility and dispatches `toggle_window_visibility` on selection.

#### Common mistakes and anti-patterns

- Mismatching scene scope and window scope for action handlers. Action handlers registered for a different scene than the window's scene will not be active when the window is visible.
- Not synchronizing task panel button state with window visibility when toggling windows programmatically outside the spec-managed action system.
- Creating window controls in `bind_runtime` instead of `build`. Window controls must exist before sibling features bind so that cross-feature observable wiring has valid targets.

#### Cross-links to related systems

See [8.2 Feature Lifecycle and Feature Types](#82-feature-lifecycle-and-feature-types) for feature lifecycle phases, [8.5 Controls and Control Composition](#85-controls-and-control-composition) for window-internal control layout, [8.7 Focus and Accessibility](#87-focus-and-accessibility) for focus ring exclusion on window hide, and [8.8 Overlays, Dialogs, Notifications, and Command Surfaces](#88-overlays-dialogs-notifications-and-command-surfaces) for command palette integration.

[Back to Table of Contents](#table-of-contents)

---

### 8.10 Scheduling, Timing, Animation, and Transitions

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Time-based work — animations, deferred callbacks, multi-step workflows, and cooperative background tasks — must execute within deterministic per-frame budgets to avoid blocking the render path. gui_do provides a layered scheduling system that covers simple timers, property tweens, state-machine-driven animation sequences, coroutine-based cooperative tasks, scene timelines, and rate-limiting utilities.

#### Mental model and lifecycle placement

The scheduler is a per-scene resource that the framework ticks each frame. Frame time is divided between rendering and scheduling work. The scheduler's budget is clamped: it runs for at most a fraction of the available frame time (`fraction = 0.12` of dt in milliseconds), with a hard floor of `0.5 ms` and a ceiling of `4.0 ms`. Coroutines that yield control at safe points are resumed each frame within budget. Animations and tweens are registered once and ticked automatically.

Register coroutines and timers in `bind_runtime`. Cancel them in `shutdown_runtime` to prevent stale callbacks from firing after the scene deactivates.

#### Primary public APIs and key types

**Tier 5:** `TaskEvent`, `TaskScheduler`, `Timers`, `TweenManager`, `TweenHandle`, `Easing`, `AnimationSequence`, `AnimationHandle`, `TransitionManager`, `TransitionSpec`, `TransitionEvent`, `AnimationStateMachine`, `AnimationTransitionMode`, `SceneTimeline`, `Debouncer`, `Throttler`, `CooperativeScheduler`, `CoroutineHandle`, `Pause`, `Sleep`, `WaitForEvent`, `WaitForSignal`, `WaitUntil`, `WaitForAll`.

**Tier 26 (Dataflow Pipeline):** `CancellationToken`, `PipelineStage`, `DataflowPipeline`, `PipelineHandle`.

**Tier 18 helper:** `ensure_scene_scheduler`.

#### Scheduler budget contract

The cooperative scheduler's dispatch budget is defined in `docs/runtime_operating_contracts.md` Section 6:

- **fraction:** 0.12 of dt milliseconds — the scheduler may use up to 12% of the frame's dt
- **floor:** 0.5 ms — minimum guaranteed budget per frame even on very fast frames
- **ceiling:** 4.0 ms — hard cap per frame to protect rendering from runaway coroutines

#### Typical usage flow

1. Create timer, tween, or coroutine handles in `bind_runtime`.
2. Register coroutines with the scene scheduler using `ensure_scene_scheduler(host, scene_name)` then `scheduler.run(coroutine)`.
3. Cancel all active handles in `shutdown_runtime` to prevent stale mutations on dead controls.

```python
# Tween a panel's alpha on show
self._fade_tween = host.tweens.to(self.panel, "alpha", target=255, duration=0.2, easing=Easing.EASE_OUT)

# Cooperative coroutine
def startup_sequence(host):
    yield Sleep(0.5)
    self.status.value = "Initialized"
    yield WaitForSignal(self.ready_signal)
    self.status.value = "Ready"

scheduler = ensure_scene_scheduler(host, "main")
scheduler.run(startup_sequence(host))
```

#### Minimal example

```python
from gui_do import Easing, TweenHandle

class AnimatedPanel(Feature):
    def bind_runtime(self, host) -> None:
        self._tween: TweenHandle = host.tweens.to(
            self.root, "alpha", target=255, duration=0.3, easing=Easing.EASE_OUT
        )

    def shutdown_runtime(self, host) -> None:
        if self._tween and self._tween.is_active():
            self._tween.cancel()
```

#### Advanced pattern(s)

Use `CooperativeScheduler` coroutines with `WaitForSignal` to implement multi-step workflows that span many frames without blocking the UI thread. This is the preferred alternative to threading for sequential async work:

```python
from gui_do import Sleep, WaitForSignal, WaitUntil

def analysis_workflow(host):
    self.progress.value = 0.0
    yield Sleep(0.1)                         # yield to let UI redraw first
    yield WaitUntil(lambda: self.data_ready)  # wait for data without spinning
    self.progress.value = 0.5
    yield WaitForSignal(self.confirm_signal)  # wait for user confirmation
    self.progress.value = 1.0
    self.status.value = "Complete"
```

Use `AnimationStateMachine` to drive complex multi-state visual feedback. Declare named animation states and transitions; the machine applies the correct `AnimationSequence` when transitioning between states. Use `AnimationTransitionMode` to control whether the current animation completes or is immediately interrupted.

Use `Debouncer` for search inputs that should not trigger a backend query on every keystroke, and `Throttler` for resize or scroll handlers where firing on every pixel change is wasteful.

#### Common mistakes and anti-patterns

- Performing unbounded computation in `on_update` directly. Heavy work in `on_update` blocks every render frame. Move multi-step work into a `CooperativeScheduler` coroutine.
- Placing blocking I/O inside coroutines. Coroutines run on the main thread within the frame budget. Blocking I/O (file reads, network calls) will freeze the frame. Use `DataflowPipeline` with a `CancellationToken` for I/O-bound work.
- Forgetting to cancel tweens on scene exit. Active tweens continue to apply mutations to target controls each frame. A tween on a dead control will raise or silently corrupt state.

#### Cross-links to related systems

See [8.2 Feature Lifecycle and Feature Types](#82-feature-lifecycle-and-feature-types) for the `on_update` frame contract, [8.14 Data and Dataflow Helpers](#814-data-and-dataflow-helpers) for the pipeline stage model for I/O-bound work, and [8.16 Telemetry, Diagnostics, and Introspection](#816-telemetry-diagnostics-and-introspection) for measuring scheduler performance.

[Back to Table of Contents](#table-of-contents)

---

### 8.11 Persistence and Workspace/Session State

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Users expect their application state — open windows, scene selection, feature-specific data, and settings — to survive application restarts. gui_do provides a workspace persistence layer that snapshots the session to JSON on save and restores it deterministically on load. The restore operation produces a structured report so that application code can detect and surface any gaps in the restored state.

#### Mental model and lifecycle placement

The workspace is a JSON document containing the saved scene, feature states, scene node snapshots, and settings values. On restore, the runtime switches to the saved scene, replays feature states, restores scene snapshots, and applies settings. Unknown keys are skipped without aborting the restore. The restore report enumerates what was applied, what was skipped, and which settings blocks were missing.

This system sits at the application lifecycle boundary: save is called on shutdown, load is called on startup before scene activation.

#### Primary public APIs and key types

**Tier 11:** `CommandHistory`, `Command`, `CommandTransaction`, `StateMachine`, `HierarchicalStateMachine`, `Router`, `RouteEntry`, `SettingsRegistry`, `SettingDescriptor`, `WorkspaceState`, `WorkspacePersistenceManager`, `DEFAULT_WORKSPACE_STATE_PATH`, `SceneSnapshot`, `NodeSnapshot`.

**Tier 32 (snapshot migration):** `SchemaVersion`, `VersionedSnapshot`, `MigrationStep`, `MigrationRegistry`, `SnapshotMigrator`, `MigrationError`, `make_snapshot`, `read_version`.

**Tier 23 (undo context):** `UndoContextManager`.

**Restore report fields** (from `docs/runtime_operating_contracts.md` Section 4):

- `target_scene`
- `switched_scene`
- `restored_feature_states`
- `restored_scene_nodes`
- `applied_settings`
- `skipped_settings`
- `missing_settings_blocks`

#### Typical usage flow

1. Call `host.app.save_workspace(path)` at application shutdown or at checkpoint save points.
2. On startup, call `report = host.app.load_workspace(path)` before the first scene activates.
3. Inspect the restore report to surface warnings about missing or skipped settings to the user.

```python
# Save workspace
host.app.save_workspace(DEFAULT_WORKSPACE_STATE_PATH)

# Load workspace
report = host.app.load_workspace(DEFAULT_WORKSPACE_STATE_PATH)
if report and report.skipped_settings:
    host.toasts.show(
        f"Could not restore {len(report.skipped_settings)} settings",
        severity=ToastSeverity.WARNING,
    )
```

#### Minimal example

```python
from gui_do import DEFAULT_WORKSPACE_STATE_PATH, WorkspacePersistenceManager

manager = WorkspacePersistenceManager(DEFAULT_WORKSPACE_STATE_PATH)
snapshot = manager.load()
if snapshot is not None:
    report = manager.restore(host.app, snapshot)
```

#### Advanced pattern(s)

Use `SnapshotMigrator` when the schema of persisted state evolves across releases. Register `MigrationStep` objects that transform a `VersionedSnapshot` from one version to the next. On load, call `read_version` to detect the snapshot's version, then have the migrator walk the registered steps forward to the current schema version before restoring:

```python
from gui_do import MigrationRegistry, MigrationStep, SnapshotMigrator, read_version

registry = MigrationRegistry()
registry.register(MigrationStep(from_version="1.0", to_version="1.1", apply=migrate_v1_to_v1_1))
migrator = SnapshotMigrator(registry)

raw = load_raw_snapshot(path)
version = read_version(raw)
migrated = migrator.migrate(raw, to_version="1.1")
```

Use `UndoContextManager` to provide independent undo/redo stacks for different editor panels in the same application. For example, a text editor panel and a property inspector panel can each have their own stack, with their respective `CommandHistory` instances registered under named contexts.

Use `SettingsRegistry` with typed `SettingDescriptor` entries to define application settings declaratively. Registered settings participate automatically in workspace save/restore without additional plumbing.

#### Common mistakes and anti-patterns

- Assuming all settings keys exist in a loaded workspace. Always inspect `restore_report.skipped_settings` and `missing_settings_blocks` before relying on restored values.
- Restoring snapshots without calling `read_version` first. When the schema has evolved, restoring an unversioned snapshot may silently apply stale field mappings.
- Using `DEFAULT_WORKSPACE_STATE_PATH` without qualification in multi-instance scenarios. Multiple application instances sharing the same path will overwrite each other's workspace on save.

#### Cross-links to related systems

See [8.1 Application Bootstrap and Host Configuration](#81-application-bootstrap-and-host-configuration) for how workspace load integrates with application startup, [8.4 State and Observables](#84-state-and-observables) for `AppStateStore` as the in-memory state layer, and [8.16 Telemetry, Diagnostics, and Introspection](#816-telemetry-diagnostics-and-introspection) for measuring restore performance.

[Back to Table of Contents](#table-of-contents)

---

### 8.12 Theme, Styling, and Visual Systems

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Theming centralizes all design decisions — colors, spacing, border radii, typography, cursor shapes — into a single authoritative source. Without a theme system, color literals and size constants scatter across hundreds of draw calls, making a visual style change a multi-day refactoring exercise. With the theme system, changing the active theme is a single operation; every control picks up the updated values on the next frame.

#### Mental model and lifecycle placement

The `ThemeManager` holds the active `ColorTheme`. Controls and features query `DesignTokens` for named values at render time rather than using literals. `FontRoleRegistry` maps semantic role names (e.g., `"heading"`, `"body"`, `"caption"`) to font configurations. When the theme changes, `ThemeInvalidationBus` broadcasts to all registered subscribers so caches of pre-rendered surfaces are invalidated and re-rendered on the next frame.

This system is initialized during bootstrap via the `fonts` dict and `FontRoleBindingSpec` entries in `HostApplicationConfig`, and is then available throughout the feature lifecycle.

#### Primary public APIs and key types

**Tier 6:** `FontManager`, `FontRoleRegistry`, `ColorTheme`, `ThemeManager`, `DesignTokens`, `ScopedTheme`, `ScopedThemeManager`.

**Tier 22:** `ThemeInvalidationBus`.

**Tier 1 spec types:** `FontRoleBindingSpec`, `CursorSpec`, `CursorBindingSpec`.

**Tier 1 helper:** `setup_standard_font_roles`.

#### Typical usage flow

1. Declare a `fonts` dict in `HostApplicationConfig` with font configuration entries.
2. Add `FontRoleBindingSpec` entries to map semantic role names to font configurations. Or call `setup_standard_font_roles` with the fonts dict to register a standard role set in one call.
3. In controls and features, query the active theme's color via `host.theme_manager.active_theme` and `host.design_tokens.get(token_name)` rather than using hard-coded literals.
4. To switch themes at runtime, call `host.theme_manager.set_theme(name)`. `ThemeInvalidationBus` handles cache flush.

#### Minimal example

```python
# In bootstrap config
fonts = {
    "default": {"system": "arial", "size": 14},
    "heading": {"system": "arial", "size": 20, "bold": True},
}
font_role_specs = (
    FontRoleBindingSpec(role="body", font_key="default"),
    FontRoleBindingSpec(role="heading", font_key="heading"),
)

# In feature draw code (using design tokens)
color = host.design_tokens.get("panel_bg")
pygame.draw.rect(surface, color, self.root.rect)
```

#### Advanced pattern(s)

Use `ScopedThemeManager` to apply per-window or per-subtree theme overrides. For example, a dark sidebar panel in an otherwise light-themed application can register its root control as a `ScopedTheme` override context:

```python
from gui_do import ScopedTheme, ScopedThemeManager

dark_tokens = DesignTokens({"panel_bg": (30, 30, 30, 255), "label_fg": (220, 220, 220, 255)})
scoped = ScopedTheme(root_control=self.sidebar, tokens=dark_tokens)
host.scoped_theme_manager.register(scoped)
```

Subscribe to `ThemeInvalidationBus` in any custom control that caches pre-rendered surface content (e.g., rich text rendered to an offscreen surface). When invalidation fires, clear the cached surface so it is re-rendered with the updated theme values on the next draw call:

```python
from gui_do import ThemeInvalidationBus

self._unsub_theme = ThemeInvalidationBus.subscribe(self._on_theme_changed)

def _on_theme_changed(self) -> None:
    self._cached_surface = None  # cleared; will re-render on next draw
```

#### Common mistakes and anti-patterns

- Hardcoding `pygame` color tuples in feature or control draw code. Literals break theme switching and make visual audits impossible. Always reference a `DesignTokens` key.
- Switching themes without invalidating surface caches. If your control pre-renders content to an offscreen surface and does not subscribe to `ThemeInvalidationBus`, stale colors will persist until the next forced redraw.
- Registering fonts in feature `build` methods rather than in the bootstrap config. The `FontRoleRegistry` may not be fully initialized or associated with the scene at that point.

#### Cross-links to related systems

See [8.1 Application Bootstrap and Host Configuration](#81-application-bootstrap-and-host-configuration) for how font configs and `CursorSpec` entries are declared, [8.5 Controls and Control Composition](#85-controls-and-control-composition) for how controls consume theme values in rendering, and [8.16 Telemetry, Diagnostics, and Introspection](#816-telemetry-diagnostics-and-introspection) for identifying theme-switch performance regressions.

[Back to Table of Contents](#table-of-contents)

---

### 8.13 Text, Input, Forms, and Validation Systems

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Structured text entry, document editing, form modeling, and validation logic are features common enough across applications to warrant a first-class system rather than ad hoc implementations scattered across features. gui_do provides a layered text and forms stack: low-level input controls handle keystroke-level entry; `FormModel` and `FormSchema` sit above them managing logical form state, field validation, and cross-field dependencies; `SchemaFormRuntime` drives declarative validation policy; and `AsyncFormValidator` handles debounced remote validation against backend services.

#### Mental model and lifecycle placement

Think in layers. `TextInputControl` and `TextAreaControl` (Tier 13) handle raw text entry. `FormModel`, `FormField`, `FormSchema`, and `SchemaField` (Tier 10) model the logical form above the controls — they track field values, dirty state, and validation status independently of how the controls are rendered. `SchemaFormRuntime` (Tier 31) drives a `FieldGraphSchema` (a DAG of fields with visibility dependencies) through a `ValidationPolicy`. `AsyncFormValidator` (Tier 24) wraps `AsyncFieldValidator` instances with debouncing and stale-result suppression.

Form modeling happens in `build` and `bind_runtime`. Validation policies run as reactive responses to field value changes.

#### Primary public APIs and key types

**Forms and validation (Tier 10):** `FormModel`, `FormField`, `ValidationRule`, `FieldError`, `FormSchema`, `SchemaField`, `DocumentModel`, `WizardFlow`, `WizardStep`, `WizardHandle`, `ValidationResult`, `Validator`, `RequiredValidator`, `RangeValidator`, `LengthValidator`, `PatternValidator`, `CustomValidator`, `DependentValidator`, `ValidationPipeline`.

**Async validation (Tier 24):** `AsyncFieldValidator`, `AsyncFormValidator`.

**Schema-driven form runtime (Tier 31):** `FieldSchema`, `FieldGraphSchema`, `ValidationPolicy`, `SchemaFormRuntime`.

**Text utilities (Tier 14):** `TextFormatter`, `NumericFormatter`, `PatternFormatter`, `FixedPatternFormatter`, `TextFlow`, `TextSpan`, `TextSearcher`, `TextMatch`, `StringTable`, `LocaleRegistry`.

**Input controls (Tier 13):** `TextInputControl`, `TextAreaControl`, `RichLabelControl`, `SpinnerControl`, `DatePickerControl`, `TimePickerControl`, `ColorPickerControl`, `ChipInputControl`.

#### Typical usage flow

1. Define a `FormSchema` with `SchemaField` entries specifying field names, types, and validation rules.
2. Build a `FieldGraphSchema` from the schema to capture field visibility dependencies.
3. Construct a `SchemaFormRuntime` with the field graph schema and a `ValidationPolicy` (e.g., `ON_CHANGE` for continuous feedback).
4. Bind each `FormField`'s value to its corresponding `TextInputControl` via observables in `bind_runtime`.
5. React to `FieldError` events from the runtime to display inline error labels near each field.

#### Minimal example

```python
from gui_do import (
    FieldError,
    FormField,
    FormSchema,
    PatternValidator,
    RequiredValidator,
    SchemaField,
    ValidationPipeline,
    ValidationPolicy,
    FieldGraphSchema,
    SchemaFormRuntime,
)


schema = FormSchema(fields=[
    SchemaField(name="email", validators=[RequiredValidator(), PatternValidator(r".+@.+\..+")]),
    SchemaField(name="password", validators=[RequiredValidator(), LengthValidator(min_len=8)]),
])
graph = FieldGraphSchema.from_form_schema(schema)
runtime = SchemaFormRuntime(graph, policy=ValidationPolicy.ON_CHANGE)
```

#### Advanced pattern(s)

Use `AsyncFormValidator` for registration forms that need server-side uniqueness checks. The validator debounces each keystroke and suppresses results from earlier generations when the user keeps typing:

```python
from gui_do import AsyncFieldValidator, AsyncFormValidator


class UsernameAvailabilityValidator(AsyncFieldValidator):
    async def validate(self, value: str) -> FieldError | None:
        available = await check_username_api(value)
        return None if available else FieldError("username", "Username already taken")


validator = AsyncFormValidator(debounce_ms=400)
validator.add_field("username", UsernameAvailabilityValidator())
```

Use `WizardFlow` with `WizardStep` entries to guide users through a multi-page form sequence where each step can independently validate before allowing progression. `WizardHandle.next()` runs the current step's validation; it advances only if the step passes.

#### Common mistakes and anti-patterns

- Validating only on submit when the UX expectation is continuous per-field feedback. Use `ValidationPolicy.ON_CHANGE` for responsive validation.
- Wiring `AsyncFormValidator` without stale-generation suppression. If the user types quickly and the first async request resolves after the second, the older error will overwrite the current result.
- Mixing validation logic into `handle_event` callbacks. All validation should flow through the `FormModel` or `SchemaFormRuntime` so the policy layer controls when and how errors are surfaced.

#### Cross-links to related systems

See [8.4 State and Observables](#84-state-and-observables) for how to bind form field values reactively, [8.5 Controls and Control Composition](#85-controls-and-control-composition) for the input control family, and [8.14 Data and Dataflow Helpers](#814-data-and-dataflow-helpers) for cancelable async pipelines.

[Back to Table of Contents](#table-of-contents)

---

### 8.14 Data and Dataflow Helpers

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Data-heavy features — search results, inventory lists, property grids, trees — require efficient loading, sorting, filtering, and virtualized rendering to remain responsive with large datasets. gui_do provides a composable pipeline from async loading through sort/filter proxies to virtualized display, with cancellation support to handle rapidly changing user inputs without stale results appearing.

#### Mental model and lifecycle placement

Data flows downstream: a source (`AsyncDataProvider`, `FixedItemSource`) feeds a `SortFilterProxySource`, which feeds a virtualized display control (`ListViewControl`, `DataGridControl`, `TreeControl`, or the lower-level `VirtualizationCore`). For processing-heavy transformation pipelines, `DataflowPipeline` coordinates multi-stage work with per-stage `CancellationToken` objects so that starting a new user input immediately cancels stale in-progress pipeline runs.

#### Primary public APIs and key types

**Virtual sources (Tier 15):** `VirtualItemSource`, `FixedItemSource`, `SortFilterProxySource`, `AsyncDataProvider`, `LoadState`, `LoadStateKind`, `ObjectPool`, `DataCache`, `CacheStats`, `ListDiffCalculator`, `ListDiff`, `DiffInsert`, `DiffRemove`, `DiffMove`.

**Dataflow pipeline (Tier 26):** `CancellationToken`, `PipelineStage`, `DataflowPipeline`, `PipelineHandle`.

**Transactional state (Tier 27):** `AppStateStore`, `StateSelector`, `StateTransaction`.

**Virtualization (Tier 29):** `MeasureMode`, `MeasurePolicy`, `VirtualizedWindow`, `RecyclePool`, `VirtualizationCore`.

#### Typical usage flow

```python
from gui_do import FixedItemSource, SortFilterProxySource

# Wrap a plain list in a virtual source
source = FixedItemSource(items)

# Apply sort and filter
proxy = SortFilterProxySource(source)
proxy.set_filter(lambda item: item.active)
proxy.set_sort_key(lambda item: item.name.lower())

# Connect to a list view
self.list_view.set_source(proxy)
```

#### Minimal example

```python
from gui_do import AsyncDataProvider, LoadStateKind

class FileLoader(AsyncDataProvider):
    async def load(self) -> list:
        return await fetch_files()

loader = FileLoader()
self._sub = loader.state.subscribe(
    lambda state: self.spinner.visible if state.kind == LoadStateKind.LOADING else None
)
```

#### Advanced pattern(s)

Use `DataflowPipeline` with multiple `PipelineStage` steps and per-stage `CancellationToken` for search pipelines that can be preempted by new user input:

```python
from gui_do import CancellationToken, DataflowPipeline, PipelineStage

pipeline = DataflowPipeline([
    PipelineStage("load", self._load_stage),
    PipelineStage("filter", self._filter_stage),
    PipelineStage("rank", self._rank_stage),
])

def _on_query_changed(self, query: str) -> None:
    if self._pipeline_handle:
        self._pipeline_handle.cancel()
    token = CancellationToken()
    self._pipeline_handle = pipeline.run(query, token=token)
    self._pipeline_handle.on_complete = self._on_results_ready
```

Use `ListDiffCalculator` to produce minimal `DiffInsert`/`DiffRemove`/`DiffMove` patches when the dataset changes. Apply these patches incrementally to the control source rather than performing full redraws, which significantly reduces visual flicker in live-updating lists.

`VirtualizationCore` with `RecyclePool` is the correct model for lists or grids with more items than can fit on screen. Only visible item views are instantiated; as the user scrolls, off-screen views are recycled and repopulated from the pool.

#### Common mistakes and anti-patterns

- Full-list redraws on every data change when `ListDiffCalculator` could produce incremental updates.
- Forgetting to cancel in-flight `DataflowPipeline` runs when new input arrives. Stale pipeline completions write old results to UI, overwriting the newer result.
- Holding large datasets in unbounded memory structures without `DataCache` expiry policies for infrequently accessed items.
- Returning pooled objects from `ObjectPool` that are still referenced elsewhere. Once an object is returned to the pool it may immediately be handed to another consumer.

#### Cross-links to related systems

See [8.4 State and Observables](#84-state-and-observables) for observable collection primitives, [8.5 Controls and Control Composition](#85-controls-and-control-composition) for `ListViewControl`, `DataGridControl`, and `TreeControl`, [8.10 Scheduling, Timing, Animation, and Transitions](#810-scheduling-timing-animation-and-transitions) for coordinating pipeline work with the cooperative scheduler, and [8.16 Telemetry, Introspection, and Operational Hooks](#816-telemetry-introspection-and-operational-hooks) for measuring pipeline stage latency.

[Back to Table of Contents](#table-of-contents)

---

### 8.15 Graphics and Audio Integration Points

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Some features require rendering that goes beyond what the control tree provides — particle effects, tile maps, hierarchical 2D transform scenes, and custom sprite animations. Others require sound feedback tied to semantic application events. gui_do provides a set of graphics helpers and an audio event bus that integrate with the feature lifecycle without requiring direct dependency on mixer or surface internals.

#### Mental model and lifecycle placement

Custom rendering lives in the feature's `draw(host, screen)` method or inside a `CanvasControl`. Graphics helpers are surface-level utilities that build on pygame; they do not replace the control tree but augment it for regions that need low-level control. Audio cues are published to `SoundEventBus` as named events; the bus routes them to the mixer without the publishing feature needing to know mixer configuration.

#### Primary public APIs and key types

**Graphics (Tier 16):** `BuiltInGraphicsFactory`, `DirtyRegionTracker`, `DrawContext`, `DrawPhase`, `AssetRegistry`, `DebugOverlay`, `SurfaceCompositor`, `Layer`, `ShapeRenderer`, `SurfaceEffects`, `VectorPath`, `SpriteSheet`, `FrameAnimation`, `ParticleSystem`, `Emitter`, `ParticleLayer`, `TileSet`, `TileMap`, `RenderTarget`, `LiveRenderTarget`, `OffscreenRenderTarget`, `create_render_target`, `create_surface`, `Node2D`, `SceneGraph2D`, `Camera2D`.

**Audio (Tier 20):** `SoundCue`, `SoundBankRegistry`, `SoundEventBus`.

#### Typical usage flow

```python
# Particle system — tick in on_update, draw in draw
def on_update(self, host, dt) -> None:
    self.particles.tick(dt)

def draw(self, host, screen) -> None:
    self.particles.draw(screen)
```

```python
# Sound cue on semantic action
host.sound_bus.publish(SoundCue("notify"))
```

#### Minimal example

```python
from gui_do import DirtyRegionTracker, OffscreenRenderTarget, create_render_target

class MiniMapFeature(Feature):
    def build(self, host) -> None:
        self.cache = create_render_target(OffscreenRenderTarget, size=(256, 256))
        self.dirty = DirtyRegionTracker()

    def on_update(self, host, dt) -> None:
        if self._world_changed:
            self.dirty.mark_dirty(pygame.Rect(0, 0, 256, 256))

    def draw(self, host, screen) -> None:
        if self.dirty.has_dirty():
            self._render_to_cache()
            self.dirty.consume_dirty_regions()
        screen.blit(self.cache.surface, self.root.rect.topleft)
```

#### Advanced pattern(s)

Combine `DirtyRegionTracker` with `OffscreenRenderTarget` for a complex canvas that changes rarely. Only re-render the dirty tiles from the offscreen cache on each frame; composite the final result in one blit. Layer `SceneGraph2D` with `Camera2D` on top for a scrollable 2D world view where node transforms apply hierarchically and the camera provides viewport panning and zoom:

```python
from gui_do import Camera2D, Node2D, SceneGraph2D

graph = SceneGraph2D()
world_root = Node2D("world")
graph.root.add_child(world_root)
self.camera = Camera2D(position=(0, 0), zoom=1.0)

def draw(self, host, screen) -> None:
    transform = self.camera.get_transform()
    graph.draw(screen, transform)
```

Use `SpriteSheet` with `FrameAnimation` to play sprite animations without manual frame index tracking. `FrameAnimation` handles frame timing and looping:

```python
from gui_do import FrameAnimation, SpriteSheet

sheet = SpriteSheet(surface, frame_size=(32, 32))
anim = FrameAnimation(sheet, frames=[0, 1, 2, 3], fps=12, loop=True)

def on_update(self, host, dt) -> None:
    anim.tick(dt)

def draw(self, host, screen) -> None:
    screen.blit(anim.current_frame(), self.sprite_rect)
```

#### Common mistakes and anti-patterns

- Full surface redraws every frame when `DirtyRegionTracker` could gate unnecessary work. Even simple background panels benefit from dirty tracking under frequent motion.
- Loading assets (`SpriteSheet`, fonts, tilesets) in `draw` or `on_update`. Asset loading causes disk I/O that stalls the frame. Load all assets in `build` or `bind_runtime`.
- Triggering `SoundCue` events from low-level pointer noise (every mouse motion) instead of from semantic application events. This floods the audio bus and produces unpleasant repeated sound.
- Creating `ParticleSystem` emitters without bounding their spawn radius, allowing particles to escape the intended rendering region and corrupt adjacent control areas.

#### Cross-links to related systems

See [8.2 Feature Lifecycle and Feature Types](#82-feature-lifecycle-and-feature-types) for the `draw` hook contract, [8.5 Controls and Control Composition](#85-controls-and-control-composition) for `CanvasControl` integration, [8.10 Scheduling, Timing, Animation, and Transitions](#810-scheduling-timing-animation-and-transitions) for particle tick timing, and [8.16 Telemetry, Introspection, and Operational Hooks](#816-telemetry-introspection-and-operational-hooks) for profiling draw cost.

[Back to Table of Contents](#table-of-contents)

---

### 8.16 Telemetry, Introspection, and Operational Hooks

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Runtime observability — performance measurement, live property inspection, and spatial query support — enables developers to diagnose behavioral and performance issues without relying on visual inspection alone. Telemetry spans instrument hot paths and accumulate structured records for offline analysis. The property registry and inspector model expose control attributes for live examination during development. The spatial index answers geometric queries about control positions for both feature logic and debugging tools.

#### Mental model and lifecycle placement

Telemetry is a passive instrumentation layer: spans record start and end times without altering runtime behavior. `PropertyRegistry` is populated at module load time by `@ui_property` decorators on control classes; `PropertyInspectorModel` drives the `PropertyInspectorPanel` control to show live property values. `SceneSpatialIndex` is a scene-level query engine that the runtime maintains as controls are added and moved.

#### Primary public APIs and key types

**Telemetry (Tier 7):** `TelemetryCollector`, `TelemetrySample`, `configure_telemetry`, `telemetry_collector`, `analyze_telemetry_log_file`, `analyze_telemetry_records`, `load_telemetry_log_file`, `render_telemetry_report`.

**Tier 1 config:** `TelemetryConfig`.

**Introspection (Tier 17):** `SceneSpatialIndex`, `ui_property`, `PropertyDescriptor`, `PropertyRegistry`, `property_registry`, `PropertyInspectorModel`, `InspectedProperty`.

#### Typical usage flow

```python
from gui_do import analyze_telemetry_records, configure_telemetry, telemetry_collector

configure_telemetry(enabled=True)

# ... run representative scenarios ...

report = analyze_telemetry_records(telemetry_collector.records)
print(render_telemetry_report(report))
```

#### Minimal example

```python
from gui_do import TelemetryConfig, bootstrap_host_application, HostApplicationConfig

cfg = HostApplicationConfig(
    # ...
    telemetry=TelemetryConfig(enabled=True, log_path="telemetry.jsonl"),
)
bootstrap_host_application(host, cfg)
```

#### Advanced pattern(s)

Combine telemetry traces with `PropertyInspectorModel` snapshots to localize layout or routing regressions. Build a `DebugOverlay` that renders `SceneSpatialIndex` query results as colored rects overlaid on the live scene, making the spatial index structure visible:

```python
from gui_do import DebugOverlay, SceneSpatialIndex

spatial = SceneSpatialIndex(scene=host.active_scene)
overlay = DebugOverlay(surface=screen)

def draw(self, host, screen) -> None:
    hits = spatial.query_point(host.pointer.pos)
    for hit in hits:
        overlay.draw_rect(hit.bounds, color=(255, 0, 0, 100))
```

Use `analyze_telemetry_log_file` to post-process telemetry stored from production runs and identify which feature or system is exceeding the scheduler budget:

```python
from gui_do import analyze_telemetry_log_file, render_telemetry_report

report = analyze_telemetry_log_file("telemetry.jsonl")
print(render_telemetry_report(report))
```

#### Common mistakes and anti-patterns

- Profiling during idle or trivial scenarios. The telemetry record is only meaningful when it captures representative user interaction flows.
- Forgetting to call `configure_telemetry(enabled=True)` before the scenarios you want to measure. The collector is disabled by default to avoid overhead in production.
- Using `SceneSpatialIndex` for per-frame hit-testing in production code. The index is a diagnostic and layout aid, not a replacement for the control tree's built-in hit-testing.

#### Cross-links to related systems

See [8.10 Scheduling, Timing, Animation, and Transitions](#810-scheduling-timing-animation-and-transitions) for scheduler budget values, [8.11 Persistence and Workspace/Session State](#811-persistence-and-workspacesession-state) for telemetry log paths, and [8.15 Graphics and Audio Integration Points](#815-graphics-and-audio-integration-points) for profiling draw cost.

[Back to Table of Contents](#table-of-contents)

---

## Integration Patterns and Composition Recipes

[Back to Table of Contents](#table-of-contents)

This section presents four end-to-end composition recipes for common patterns in gui_do applications. Each recipe shows the goal, explains why this particular combination of systems is the right approach, provides step-by-step wiring instructions, and includes a complete code example with a validation checklist.

---

### Recipe 1: Routed Feature + Actions + Shortcut Overlay

**Goal:** A feature with discoverable keyboard shortcuts, auto-wired via `RoutedRuntimeSpec` so the shortcut help overlay automatically reflects the registered action list without manual maintenance.

**Why this combination:** Declaring shortcuts in `RoutedRuntimeSpec` with `ShortcutOverlaySpec` means the overlay content is always consistent with the actual registered bindings. There is no separate "shortcut help data" to keep synchronized with the actual hotkeys — the overlay queries the action registry directly.

**Step-by-step:**

1. Declare `ActionSpec` entries in `HostApplicationConfig` with `action_id`, `label`, and `category`.
2. In the feature's `__init__`, build a `RoutedRuntimeSpec` that includes a `ShortcutOverlaySpec` referencing the overlay toggle action and key.
3. Build a `RoutedFeatureLifecycleSpec` that references the runtime spec.
4. In `bind_runtime`, call `bind_routed_feature_lifecycle(self, host, self._lifecycle_spec)`.
5. In `shutdown_runtime`, call `shutdown_routed_feature_lifecycle(self, host, self._lifecycle_spec)` to clean up all registrations symmetrically.

```python
from gui_do import (
    ActionSpec,
    FeatureSpec,
    RoutedFeature,
    RoutedFeatureLifecycleSpec,
    RoutedRuntimeSpec,
    ShortcutOverlaySpec,
    bind_routed_feature_lifecycle,
    shutdown_routed_feature_lifecycle,
)


class EditorFeature(RoutedFeature):
    def __init__(self) -> None:
        super().__init__("editor", scene_name="main")
        runtime_spec = RoutedRuntimeSpec(
            shortcut_overlay=ShortcutOverlaySpec(
                toggle_action_name="toggle_shortcuts",
                toggle_key="F1",
            ),
        )
        self._lifecycle_spec = RoutedFeatureLifecycleSpec(runtime_spec=runtime_spec)

    def build(self, host) -> None:
        # build controls here
        pass

    def bind_runtime(self, host) -> None:
        bind_routed_feature_lifecycle(self, host, self._lifecycle_spec)

    def shutdown_runtime(self, host) -> None:
        shutdown_routed_feature_lifecycle(self, host, self._lifecycle_spec)
```

**Validation:** Press `F1` — the shortcut overlay appears and lists all registered actions. Press `F1` again or `Escape` — overlay dismisses. Add a new `ActionSpec` — it appears in the overlay without any other change.

---

### Recipe 2: Window Presenter + Task Panel + Focus Toggle

**Goal:** A floating window in a scene that is toggled from the task panel with correct focus routing — when the window is hidden, its controls are excluded from Tab-key cycling.

**Why this combination:** `TaskPanelFocusToggleSpec` inside `RoutedRuntimeSpec` automates the focus ring exclusion. Without it, Tab navigation stalls on hidden window controls. This approach ensures the window toggle button state, focus ring membership, and accessibility annotations stay synchronized.

**Step-by-step:**

1. Implement a `WindowPresenter` subclass with the window's internal control layout.
2. Declare the window's size and chrome properties in `AnchoredWindowSpec`.
3. In the feature's `build`, call `create_feature_presented_window` to instantiate the presenter and register the window.
4. In `RoutedRuntimeSpec`, declare a `TaskPanelFocusToggleSpec` referencing the window.
5. Wire the window toggle button to `set_window_visible_state` via the task panel spec.

```python
from pygame import Rect

from gui_do import (
    AnchoredWindowSpec,
    LabelControl,
    RoutedFeature,
    RoutedFeatureLifecycleSpec,
    RoutedRuntimeSpec,
    TaskPanelFocusToggleSpec,
    WindowPresenter,
    bind_routed_feature_lifecycle,
    create_feature_presented_window,
    set_window_visible_state,
    shutdown_routed_feature_lifecycle,
)


class InfoPresenter(WindowPresenter):
    def build(self, host, root) -> None:
        self.label = root.add(LabelControl("info_text", Rect(8, 8, 300, 24), "Details"))


class InfoFeature(RoutedFeature):
    def __init__(self) -> None:
        super().__init__("info", scene_name="main")
        runtime_spec = RoutedRuntimeSpec(
            focus_toggle=TaskPanelFocusToggleSpec(
                window_id="info_window",
                toggle_action_name="toggle_info",
                task_panel_label="Info",
            ),
        )
        self._lifecycle_spec = RoutedFeatureLifecycleSpec(runtime_spec=runtime_spec)

    def build(self, host) -> None:
        self.presenter = InfoPresenter()
        create_feature_presented_window(
            host, self, self.presenter, window_id="info_window", scene_name="main"
        )

    def bind_runtime(self, host) -> None:
        bind_routed_feature_lifecycle(self, host, self._lifecycle_spec)

    def shutdown_runtime(self, host) -> None:
        shutdown_routed_feature_lifecycle(self, host, self._lifecycle_spec)
```

**Validation:** Open the app — the info window is visible and `Tab` cycles through its controls. Press the toggle action or task panel button — the window hides and `Tab` no longer visits its controls. Press again — the window reappears and focus cycling resumes.

---

### Recipe 3: State Store + Persistence + Snapshot Migration

**Goal:** Centralized application state that survives schema evolution across releases, with a restore report so the application can surface gaps to the user.

**Why this combination:** `AppStateStore` provides a single source of truth for domain state; `StateSelector` gives each feature a reactive slice without coupling them to the full store shape; `SnapshotMigrator` ensures that snapshots written by older releases can be upgraded before being applied, preventing silent data loss or corrupt restores.

**Step-by-step:**

1. Define `AppStateStore` with the initial state shape.
2. Create `StateSelector` instances in each feature's `__init__` for the fields they care about.
3. On save, serialize the store's state via `make_snapshot(version, state_dict)` and persist it.
4. On load, call `read_version(raw)` to detect the snapshot's schema version.
5. Call `SnapshotMigrator.migrate(snapshot, to_version=CURRENT_VERSION)` to upgrade old snapshots.
6. Inspect the restore report's fields (`skipped_settings`, `missing_settings_blocks`) to surface warnings.

```python
from gui_do import (
    AppStateStore,
    MigrationRegistry,
    MigrationStep,
    SnapshotMigrator,
    StateSelector,
    StateTransaction,
    make_snapshot,
    read_version,
)

CURRENT_VERSION = "2.0"

store = AppStateStore({"selected_scene": "main", "last_query": "", "panel_visible": True})
selected_selector = StateSelector(store, lambda s: s["selected_scene"])

registry = MigrationRegistry()
registry.register(
    MigrationStep(
        from_version="1.0",
        to_version="2.0",
        apply=lambda snap: {**snap, "panel_visible": True},  # added in v2
    )
)
migrator = SnapshotMigrator(registry)

def save_state(path: str) -> None:
    snapshot = make_snapshot(CURRENT_VERSION, store.state)
    write_json(path, snapshot)

def load_state(path: str) -> None:
    raw = read_json(path)
    version = read_version(raw)
    migrated = migrator.migrate(raw, to_version=CURRENT_VERSION)
    store.apply(migrated)
```

**Validation:** Save state with version 1.0 schema; reload with version 2.0 migrator — `panel_visible` field appears with its default. Introduce an unknown key in the saved JSON — restore report's `skipped_settings` list contains the unknown key and the app continues normally.

---

### Recipe 4: Dataflow Pipeline + Telemetry + Error Boundary

**Goal:** Safe background processing with measurable per-stage performance and UI failure containment so that a rendering error in one feature does not crash the entire frame.

**Why this combination:** `DataflowPipeline` with per-stage `CancellationToken` prevents stale results from overwriting fresh ones when user input arrives faster than the pipeline completes. Telemetry spans on stage callbacks expose which stage is the performance bottleneck. `ErrorBoundary` wrapping the output control tree ensures that rendering failures in the result display degrade gracefully to a neutral fallback.

**Step-by-step:**

1. Stage pipeline work in `DataflowPipeline` with each `PipelineStage` checking its `CancellationToken`.
2. Wrap stage callbacks with telemetry spans using the `telemetry_collector`.
3. Wrap the output control subtree in `ErrorBoundary` during `build`.
4. Drive progress feedback via `ObservableValue` subscribed to in `bind_runtime`.
5. On new input, cancel the current `PipelineHandle` and start a fresh generation.

```python
from gui_do import (
    CancellationToken,
    DataflowPipeline,
    ErrorBoundary,
    ObservableValue,
    PipelineStage,
    configure_telemetry,
    telemetry_collector,
)


class SearchFeature(RoutedFeature):
    def __init__(self) -> None:
        super().__init__("search", scene_name="main")
        self.progress = ObservableValue(0.0)
        self._pipeline = DataflowPipeline([
            PipelineStage("load", self._load_stage),
            PipelineStage("filter", self._filter_stage),
            PipelineStage("rank", self._rank_stage),
        ])
        self._handle = None

    def build(self, host) -> None:
        self.root = host.app.add(
            ErrorBoundary("search_boundary", Rect(0, 0, 800, 600)),
            scene_name="main",
        )
        self.results = self.root.add(ListViewControl("results", Rect(8, 8, 784, 580)))

    def _on_query_changed(self, query: str) -> None:
        if self._handle:
            self._handle.cancel()
        token = CancellationToken()
        self._handle = self._pipeline.run(query, token=token)
        self._handle.on_complete = self._apply_results

    def _load_stage(self, query: str, token: CancellationToken) -> list:
        with telemetry_collector.span("search.load"):
            if token.is_cancelled():
                return []
            return fetch_items(query)
```

**Validation:** Type quickly in the search input — only the result from the final keystroke appears (stale pipeline runs are cancelled). Enable telemetry and run the search — `render_telemetry_report` identifies the slowest stage. Introduce a rendering error in the results presenter — `ErrorBoundary` renders a fallback frame instead of crashing.

[Back to Table of Contents](#table-of-contents)

---

## End-to-End Reference Application

[Back to Table of Contents](#table-of-contents)

The following self-contained listing demonstrates the core gui_do assembly pattern in one place. It is intended as a verified reference, not a minimal Hello World — every line corresponds to a real system documented in this manual.

```python
"""
gui_do End-to-End Reference Application.

Demonstrates: bootstrap, RoutedFeature lifecycle, ObservableValue → LabelControl binding,
RoutedRuntimeSpec + ShortcutOverlaySpec, ActionSpec, RuntimeSceneSpec, TelemetryConfig,
workspace save/load, and the host run_entrypoint pattern.
"""

from pygame import Rect

import pygame

from gui_do import (
    ActionSpec,
    ButtonControl,
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
    bind_routed_feature_lifecycle,
    bootstrap_host_application,
    configure_telemetry,
    shutdown_routed_feature_lifecycle,
)


# ---------------------------------------------------------------------------
# Feature
# ---------------------------------------------------------------------------


class CounterFeature(RoutedFeature):
    """Simple counter feature — demonstrates the full feature lifecycle."""

    HOST_REQUIREMENTS = {"build": ("app",), "bind_runtime": ()}

    def __init__(self) -> None:
        super().__init__("counter", scene_name="main")
        self.count = ObservableValue(0)
        self._unsub = None
        runtime_spec = RoutedRuntimeSpec(
            shortcut_overlay=ShortcutOverlaySpec(
                toggle_action_name="toggle_shortcuts",
                toggle_key="F1",
            ),
        )
        self._lifecycle_spec = RoutedFeatureLifecycleSpec(runtime_spec=runtime_spec)

    def build(self, host) -> None:
        self.root = host.app.add(
            PanelControl("counter_root", Rect(40, 40, 400, 200)),
            scene_name="main",
        )
        self.label = self.root.add(
            LabelControl("count_label", Rect(8, 8, 384, 40), "Count: 0")
        )
        self.root.add(
            ButtonControl(
                "increment_btn",
                Rect(8, 60, 160, 36),
                "Increment",
                on_click=self._on_increment,
            )
        )

    def bind_runtime(self, host) -> None:
        self._unsub = self.count.subscribe(
            lambda v: setattr(self.label, "text", f"Count: {v}")
        )
        bind_routed_feature_lifecycle(self, host, self._lifecycle_spec)

    def shutdown_runtime(self, host) -> None:
        if self._unsub:
            self._unsub()
            self._unsub = None
        shutdown_routed_feature_lifecycle(self, host, self._lifecycle_spec)

    def _on_increment(self, event) -> None:
        self.count.value += 1


# ---------------------------------------------------------------------------
# Bootstrap configuration
# ---------------------------------------------------------------------------


cfg = HostApplicationConfig(
    display_size=(1280, 720),
    window_title="gui_do Reference App",
    fonts={"default": {"system": "arial", "size": 14}},
    font_role_specs=(),
    cursors=(),
    scene_specs=(SceneSetupSpec(scene_name="main", pretty_name="Main"),),
    feature_specs=(FeatureSpec("counter", CounterFeature),),
    window_specs=(),
    runtime_scene_specs=(
        RuntimeSceneSpec(scene_name="main", bind_escape_to_exit=True),
    ),
    action_specs=(
        ActionSpec(action_id="exit", label="Exit", kind="exit", category="File"),
        ActionSpec(
            action_id="toggle_shortcuts",
            label="Toggle Shortcut Help",
            kind="shortcut_overlay",
            category="Help",
        ),
    ),
    static_accessibility_specs=(),
    initial_scene_name="main",
    telemetry=TelemetryConfig(enabled=True, log_path="telemetry.jsonl"),
)


# ---------------------------------------------------------------------------
# Host
# ---------------------------------------------------------------------------


class AppHost:
    """Plain object populated by bootstrap_host_application."""


def main() -> None:
    configure_telemetry(enabled=True)
    host = AppHost()
    bootstrap_host_application(host, cfg)

    # Attempt workspace restore (non-fatal if missing)
    try:
        report = host.app.load_workspace("workspace.json")
        if report and report.skipped_settings:
            print(f"Skipped settings: {report.skipped_settings}")
    except FileNotFoundError:
        pass

    host.app.run_entrypoint(target_fps=60)

    # Save workspace on clean exit
    host.app.save_workspace("workspace.json")


if __name__ == "__main__":
    main()
```

### What This Listing Demonstrates

**Bootstrap configuration.** `HostApplicationConfig` declares all scenes, features, actions, font configurations, and runtime scene policies in one place. After `bootstrap_host_application(host, cfg)` returns, the application is fully wired and `host.app` is live.

**Feature lifecycle.** `CounterFeature` subclasses `RoutedFeature` and implements all four lifecycle phases: `build` creates controls, `bind_runtime` subscribes observables and registers routed lifecycle bindings, `shutdown_runtime` disposes them symmetrically.

**Reactive state.** `ObservableValue(0)` holds the counter state. A single `subscribe` call in `bind_runtime` keeps the `LabelControl`'s text property synchronized without polling.

**Routed runtime spec.** `RoutedRuntimeSpec` with `ShortcutOverlaySpec` registers the `F1` shortcut help overlay toggle declaratively. `bind_routed_feature_lifecycle` applies all registrations in one coordinated call; `shutdown_routed_feature_lifecycle` removes them symmetrically on teardown.

**Action specs.** `ActionSpec` entries declare named actions for `exit` and the shortcut overlay toggle. `bind_escape_to_exit=True` in `RuntimeSceneSpec` binds Escape to the exit action automatically.

**Telemetry.** `TelemetryConfig(enabled=True, log_path=...)` enables the telemetry collector at bootstrap. `configure_telemetry(enabled=True)` confirms it before the run loop starts.

**Workspace save/load.** `host.app.load_workspace` is called before the first scene activates; `host.app.save_workspace` is called after `run_entrypoint` returns. A missing workspace file is tolerated without aborting startup.

### Validation Checklist

1. Application opens to a 1280×720 window with the counter panel visible.
2. Clicking "Increment" increments the label text from "Count: 0" to "Count: 1", "Count: 2", etc.
3. Pressing `F1` opens the shortcut help overlay listing both registered actions.
4. Pressing `F1` again (or `Escape` while the overlay is open) dismisses the overlay.
5. Pressing `Escape` while the overlay is not visible triggers the exit action and closes the application.
6. On second run, `workspace.json` is found and loaded without error.
7. Telemetry records are written to `telemetry.jsonl` and can be analyzed via `analyze_telemetry_log_file`.

[Back to Table of Contents](#table-of-contents)

---

## Testing, Diagnostics, and Reliability

[Back to Table of Contents](#table-of-contents)

Reliable gui_do applications are tested at two complementary levels: a contract test suite that verifies framework-level behavioral guarantees, and feature-level runtime behavior tests that cover application-specific scenarios. This chapter describes both levels, the diagnostic tools available for investigation, the maintainer release runbook, and the operational checklist that governs manual updates.

### Contract Tests

The contract test suite is the primary gate for confirming that the framework's behavioral guarantees are intact. Run it before and after any significant change to the framework itself, to documentation contracts, or to the public API surface:

```bash
python -m pytest -q tests/test_public_api_exports.py tests/test_public_api_docs_contracts.py tests/test_runtime_operating_contracts.py tests/test_boundary_contracts.py tests/test_gui_application_workspace_contracts.py
```

Each file in this suite has a specific scope:

- **`test_public_api_exports.py`** — Verifies that every name listed in `gui_do.__all__` is importable from the root package and that no names are missing. If a name appears in `__init__.py` but fails import, this test catches it. Run after any public API addition or removal.

- **`test_public_api_docs_contracts.py`** — Verifies that the API names documented in the contract specification files (`docs/public_api_spec.md`, `docs/package_contracts.md`) match the names actually exported. Catches staleness in both directions: a contract that documents a name that has been removed, or an export that is missing from the contract documentation.

- **`test_runtime_operating_contracts.py`** — Verifies the runtime behavioral guarantees: scheduler budget clamping (fraction 0.12, floor 0.5 ms, ceiling 4.0 ms), event normalization to `GuiEvent` before dispatch, scene-isolated update execution, and deterministic focus candidate ordering by `control_id`. This is the primary test for Section 1 and Section 6 of `docs/runtime_operating_contracts.md`.

- **`test_boundary_contracts.py`** — Verifies the architectural isolation rule: no module in `gui_do/` imports from `demo_features/`. Any violation of this rule breaks the library–demo separation contract specified in `docs/architecture_boundary_spec.md` and `docs/library_demo_separation_contract.md`. Run after any import change in the library or demo packages.

- **`test_gui_application_workspace_contracts.py`** — Verifies the workspace restore behavior: `GuiApplication.restore_workspace` and `load_workspace` return structured restore reports; missing settings keys are skipped without aborting restore; unknown keys appear in `skipped_settings`; the full set of restore report fields is present. Run after any change to workspace persistence or the settings registry.

### Runtime Behavior Tests

Beyond contract tests, the test suite includes focused runtime behavior tests. Key areas covered:

- **Workspace load and save behavior** — `test_gui_application_workspace_contracts.py` and related persistence tests verify save/load round-trips, version handling, and restore report completeness.
- **Overlay, tooltip, and cursor routing** — Tests that confirm overlay surfaces intercept events before the control tree, and that cursor and tooltip state changes are applied correctly.
- **Layout and animation determinism** — Tests that verify `FlexLayout`, `ConstraintLayoutEngine`, and `AdaptivePolicy` produce the same output given the same input, and that tween animations reach their target values at the declared duration.
- **Control runtime behavior** — Tests for individual controls (`test_canvas_viewport_scrollbar_slider.py`, `test_cell_caret_layout.py`, `test_data_grid_text_input.py`, etc.) that verify input handling, state transitions, and rendering invariants.
- **Accessibility specs** — `test_demo_accessibility_specs.py` verifies that declared `StaticAccessibilitySpec` entries resolve to valid `AccessibilityNode` trees with correct roles and names.

### Debug and Trace Tools

When a behavioral issue occurs that is not caught by tests, the following tools provide runtime visibility:

- **`EventRecorder` / `EventPlayback`** — Record the exact sequence of normalized `GuiEvent` objects seen during a live session. Replay the recording to reproduce the issue deterministically in a later session. This is the primary tool for reproducing routing and focus issues that are difficult to trigger manually.
- **`DebugOverlay`** — Visual inspection layer that renders control tree state (bounds, IDs, focus ring state) as colored rects over the live scene. Activate at runtime to inspect layout problems without modifying feature code.
- **`PropertyInspectorPanel`** — Driven by `PropertyInspectorModel`, this panel lists all `@ui_property` descriptors on live controls and shows their current values. Use to inspect control state during development without print statements.
- **`analyze_telemetry_records` / `render_telemetry_report`** — Offline analysis of telemetry records. After enabling `TelemetryConfig` and running representative scenarios, call `analyze_telemetry_records(telemetry_collector.records)` to identify which frame path, feature, or pipeline stage is exceeding the scheduler budget.
- **`analyze_telemetry_log_file`** — Same analysis pipeline applied to a persisted `telemetry.jsonl` log. Useful for comparing baseline performance across releases.

### Maintainer Release Runbook

Before tagging a release, run through this sequence in order. Each step is a gate: if it fails, fix the issue before proceeding.

1. Run the full test suite: `python -m pytest -q`.
2. Run the contract tests explicitly (see command above) and verify all pass.
3. Compare `gui_do/__init__.py` tier blocks against Appendix D and Appendix D.1 in this manual. Correct any gaps.
4. Verify `docs/runtime_operating_contracts.md` values (scheduler budget Section 6, restore report fields Section 4) are accurately reflected in the manual.
5. Check `docs/architecture_boundary_spec.md` — confirm no new cross-boundary imports have been introduced.
6. Run `test_public_api_docs_contracts.py` to confirm the contract documentation and the exports are synchronized.
7. Verify the End-to-End Reference Application listing compiles without import errors.
8. Run the telemetry baseline scenario and confirm the scheduler does not exceed its ceiling budget under representative load.

### Regression Triage Workflow

When a behavioral regression is reported:

1. **Reproduce.** Use `EventRecorder` to capture the exact event sequence that triggers the issue. If the issue involves scene transitions, record from scene entry.
2. **Trace.** Enable telemetry and replay the recording. Identify the frame or event where behavior diverges from expectation.
3. **Localize.** Use `DebugOverlay` or `PropertyInspectorPanel` to narrow the issue to a specific control, feature, or routing step.
4. **Test first.** Before patching, write a failing test that encodes the expected behavior. Prefer adding it to the relevant contract test file if it represents a framework-level guarantee.
5. **Patch.** Fix the issue. Verify the new test passes and no regression tests regress.
6. **Adjacent contracts.** After patching, run the full contract test suite. A routing or visibility fix may inadvertently break a sibling behavioral guarantee.

### Maintainer Diff Checklist

This checklist is an operational guide for anyone regenerating or significantly updating this manual. Run through every item in every category before publishing an updated version. The goal is to ensure that the manual accurately reflects the current state of the codebase no more and no less.

#### Inventory Delta Checks

1. **Root export changes.** Open gui_do/__init__.py and compare its tier comment blocks and exported names against Appendix D and Appendix D.1. Any tier that does not appear in the appendix is a gap. Any name in the appendix that is no longer exported is a stale reference. Record additions and removals, then propagate them to the relevant system chapter, the quick-index table, and the tier matrix.
2. **Docs contract changes.** Read each file under docs/ and compare its content against the manual section that cites it. If a contract document has changed its guarantee, policy, or boundary rule, update the corresponding manual section accordingly. In particular check scheduler budget values in docs/runtime_operating_contracts.md Section 6, restore report fields in Section 4, and tier stability policies in docs/public_api_spec.md.
3. **Contract and runtime test additions.** List the tests/ directory and filter for files matching test_*_contracts.py and test_runtime_*. Any file that does not appear in the Testing chapter contract test list is a new test that may imply new behavioral guarantees to document. Check whether the new test subject is already covered in the relevant system chapter.
4. **Demo composition pattern changes.** Browse demo_features/ and compare the feature package structures and composition patterns against the Integration Patterns and Feature Lifecycle chapters. New demo patterns that represent best-practice composition should be documented as recipes. Removed demo patterns that were used as examples in the manual should be replaced with current equivalents.

#### Content Integrity Checks

1. **Changed systems: chapter narrative and quick-index reconciliation.** For every system that had API additions or removals, update both the full chapter prose (the Primary Public APIs subsection at minimum) and the corresponding rows in Appendix D. Partial updates that fix the chapter but leave the appendix stale create confusion and must be caught here.
2. **Removed APIs: clean sweep.** After identifying removed exports, search the entire manual for each removed name. Remove or replace every occurrence. Do not leave phantom API names in examples, recipes, or appendix rows.
3. **Added APIs: abstraction-level placement.** Every new API should be introduced at the abstraction level appropriate to its tier. Tier 1 names belong in the earliest practical system chapter and in the Quickstart Path. Higher-tier names belong in the relevant system chapter and the appendix. Avoid surfacing Tier 18+ names in the Quickstart or in the introductory paragraphs of system chapters unless they are genuinely required for common usage.

#### Navigation and Structure Checks

1. **TOC completeness.** Verify that every top-level section and every system sub-chapter (8.1 through 8.N) appears in the Table of Contents with a working anchor link. After adding new sections, regenerate or manually update the TOC entry.
2. **Back-to-top links.** Every major section (every ## and ### that corresponds to a distinct manual topic) must have a Back to Table of Contents link immediately below its heading. Check that no sections added during an update pass are missing this link.
3. **Anchor stability.** Section heading text drives GitHub-Flavored Markdown anchor names. If a section heading is renamed, all TOC entries and cross-references that point to the old anchor must be updated. Prefer heading renames only when necessary, and always do a full-document anchor scan afterward.

#### Operational Checks

1. **Re-run high-priority contract tests.** Before publishing the updated manual, run the following command to confirm the behavioral guarantees cited in the manual are still enforced by the test suite:

   ```bash
   python -m pytest -q tests/test_public_api_exports.py tests/test_public_api_docs_contracts.py tests/test_runtime_operating_contracts.py tests/test_boundary_contracts.py tests/test_gui_application_workspace_contracts.py
   ```

   If any of these tests fail, the manual content derived from those contracts is potentially incorrect. Fix the discrepancy before publishing.

2. **End-to-end reference application assumptions.** The End-to-End Reference Application chapter describes a concrete application structure tied to real demo feature packages. After updating, verify that the feature class names, spec types, and lifecycle method signatures referenced in that chapter still match what is actually exported from the relevant packages. If the demo features have been restructured, update the examples to match.

3. **Unresolved ambiguities.** If any behavioral question arose during the update that could not be resolved from code or contracts, record it as an explicit TODO comment in the draft. Do not publish the TODO; resolve it before merging. If resolution requires a contract change, file that separately and leave the section conservative.

---

## Performance and Scaling Guidance

[Back to Table of Contents](#table-of-contents)

### Scheduler Budget Contract

The cooperative scheduler's per-frame dispatch budget is governed by three values defined in `docs/runtime_operating_contracts.md` Section 6:

- **fraction = 0.12** — The scheduler may use up to 12% of the frame's dt in milliseconds. On a 60 FPS frame (dt ≈ 16.7 ms) this is approximately 2 ms.
- **floor = 0.5 ms** — The minimum guaranteed budget per frame. Even on a very fast frame where 12% of dt is less than 0.5 ms, the scheduler receives at least 0.5 ms. This prevents starvation of background coroutines during burst performance scenarios.
- **ceiling = 4.0 ms** — The hard maximum per frame. Even on a very slow frame (e.g., dt = 50 ms, 12% = 6 ms), the scheduler is capped at 4.0 ms to protect render time from runaway scheduling work.

These bounds together give predictable scheduling behavior across a wide range of frame rates. Coroutines that yield at safe points will make progress every frame, but they cannot monopolize the render budget. Design coroutines to yield frequently for best responsiveness — any coroutine that does more than 1–2 ms of work before yielding may spike above the floor and delay subsequent features.

### Dirty-Region Rendering

`DirtyRegionTracker` is the primary frame-rate optimization for complex scenes with large but mostly static control trees. Instead of redrawing the entire screen surface every frame, you mark only the regions that actually changed as dirty, then check each expensive draw region against the dirty set before drawing.

The key performance characteristic: `overlaps_dirty(rect)` is O(1). The tracker maintains a running union rectangle of all dirty rects added in the current frame. An overlaps check tests only against the union rect, not against each individual dirty rect. This means the cost of checking many controls against the dirty set is essentially constant regardless of how many individual dirty regions were added.

Use `consume_dirty_regions()` at the end of each frame's draw pass to retrieve the final dirty list and reset the tracker for the next frame.

### Virtualization and Incremental Rendering

For controls that display large datasets (`ListViewControl`, `DataGridControl`, `TreeControl`), the framework provides virtualization primitives that ensure rendering and memory costs scale with the visible viewport, not the full dataset:

- **`VirtualizationCore` with `RecyclePool`** — Only the visible subset of item views is instantiated. As the user scrolls, off-screen views are returned to the `RecyclePool` and repopulated with new data for newly visible items. This keeps the instantiated control count constant regardless of dataset size.
- **`VirtualizedWindow`** — A higher-level wrapper around `VirtualizationCore` suitable for most list-of-items use cases.
- **`ListDiffCalculator`** — When the dataset changes, compute a minimal `ListDiff` (insertions, removals, moves) and apply the patch incrementally to the control source rather than replacing the entire dataset. This eliminates full-list redraws and significantly reduces visual flicker in live-updating lists.

### Practical Scaling Checklist

Apply these practices when a feature is growing in complexity or when frame rate becomes a concern:

- **Enforce scene-scoped updates and handlers.** Features registered to the wrong scene may receive unnecessary `on_update` calls. Confirm `scene_name` is correct in every `FeatureSpec`.
- **Avoid per-frame collection reallocation.** Allocating a new list or dict inside `on_update` every frame creates GC pressure. Use `ObjectPool` for high-churn temporary objects (particles, event records).
- **Debounce expensive operations.** Search inputs, resize handlers, and filter callbacks that trigger expensive work should use `Debouncer` (fires after a quiet period) or `Throttler` (fires at most once per interval).
- **Use `DataflowPipeline` + `CancellationToken` for preemptible background work.** Any processing pipeline that may be superseded by new user input should be cancelable. Never let a stale pipeline run write to live UI.
- **Profile representative scenarios.** Idle loop performance is not meaningful. Profile while simulating real user interactions — search, scroll, scene transitions, window toggles.
- **Gate expensive draw regions with `DirtyRegionTracker`.** Any `draw` method that builds a complex composited surface should check `dirty.overlaps_dirty(self.rect)` before doing any work.

[Back to Table of Contents](#table-of-contents)

---

## Migration, Versioning, and Deprecation Notes

[Back to Table of Contents](#table-of-contents)

### Versioned Snapshot Strategy

When the schema of persisted workspace state evolves across releases, `SnapshotMigrator` provides a safe forward-migration path that prevents both silent data loss and runtime errors on old snapshots. The recommended workflow is:

1. When saving, call `make_snapshot(current_version, state_dict)` to produce a `VersionedSnapshot` tagged with the current schema version string.
2. On load, call `read_version(raw)` to read the snapshot's stored schema version before attempting to restore it.
3. If the stored version is older than the current version, call `SnapshotMigrator.migrate(snapshot, to_version=CURRENT_VERSION)`. The migrator walks the `MigrationRegistry` in BFS order, applying each registered `MigrationStep` in sequence from the stored version to the target.
4. If no migration path exists from the stored version to the current version, `MigrationError` is raised. Catch this at the application level and fall back to a fresh default state rather than crashing.
5. Restore the migrated snapshot into the runtime.

Register migration steps as part of application startup, before any load attempt:

```python
registry = MigrationRegistry()
registry.register(MigrationStep(from_version="1.0", to_version="1.1", apply=upgrade_1_0_to_1_1))
registry.register(MigrationStep(from_version="1.1", to_version="2.0", apply=upgrade_1_1_to_2_0))
migrator = SnapshotMigrator(registry)
```

Migration steps are one-directional. Each step knows its source and target version. There is no automatic rollback; downgrade paths must be registered separately if required.

### Deprecation Handling

The recommended policy for deprecating public API elements is additive transition: add the new form first, keep the old form with a deprecation warning, then remove the old form in a subsequent release. This gives consumers a migration window. Removals without a deprecation window are breaking changes.

Preferred practices:

- Add new fields or parameters alongside old ones; mark old ones with a deprecation comment in the source and in this section.
- For renamed types, expose the new name and alias the old name pointing to the new type with a deprecation note.
- Remove legacy behavior only after the migration path has been available for at least one release.

No deprecated public APIs are cataloged as of this generation. Maintainers must add explicit entries here when formal deprecations are introduced. Each entry should specify: the deprecated name, the replacement, the release it was deprecated, and the release it will be removed.

### Upgrade Checklist

When upgrading an application or the framework itself:

1. Run contract tests before and after the upgrade to identify behavioral changes.
2. Verify all imports use the `from gui_do import ...` form from the root package. Internal submodule imports (`gui_do.features.*`, `gui_do.controls.*`, etc.) are not part of the stable surface.
3. Check action routing, input binding, and focus cycling behavior in all active scenes — these are the most common surfaces for behavioral regressions.
4. Validate workspace restore: load an existing saved workspace and inspect the restore report for unexpected `skipped_settings` or `missing_settings_blocks` entries.
5. Re-run the telemetry baseline scenarios and compare against the previous baseline. A scheduler budget increase is a performance regression even if no tests fail.

[Back to Table of Contents](#table-of-contents)

---

## FAQ and Troubleshooting

[Back to Table of Contents](#table-of-contents)

**Q: Should I build applications directly with controls, or should I use features?**

Use features as the primary architectural unit. Controls are implementation details inside feature boundaries — they handle rendering and user interaction primitives, but they have no lifecycle orchestration, no event routing integration, no observable wiring protocol, and no clean teardown contract. A feature provides all of these things. Think of a feature as a bounded context: it builds its controls, wires its reactive subscriptions, handles relevant events, and tears down cleanly when its scene exits. A control alone cannot do any of this. Reserve direct control use for simple utility compositions inside a feature's `build` method.

**Q: When should I use `RoutedFeature` instead of `Feature`?**

Use `RoutedFeature` when your feature needs two or more of the following: topic-based message dispatch via `FeatureMessage`, declarative hotkey registration, shortcut overlay integration, task panel window toggle with automatic focus exclusion, or event subscription specs. `RoutedRuntimeSpec` and `RoutedFeatureLifecycleSpec` wire all of these together in one coordinated bind/shutdown pair. If your feature only needs basic lifecycle phases, a control tree, and reactive observable subscriptions, plain `Feature` is simpler and entirely sufficient.

**Q: Why are some key handlers not firing?**

There are four common causes. First, focus ownership: if a `TextInputControl` or similar text-capturing control has focus, it consumes key events before they reach feature handlers. Second, window scope: if the action was registered with a window scope and the window is hidden, the action's handler is not active. Third, overlay modal capture: if a dialog, context menu, or command palette is open, it intercepts key events before the scene's routing chain. Fourth, scene scope mismatch: an action registered for `scene_name="settings"` does not fire in `scene_name="main"`. Use `EventRecorder` to trace exactly which routing layer consumed the event.

**Q: Why do toast clicks not pass through to controls underneath?**

By contract, toast surface bounds consume left-click pointer events. This prevents accidental button activations underneath a transient notification. Design all intentional interactions within toasts using the `on_click` callback provided by the toast API.

**Q: How do I avoid breaking workspace restore across schema versions?**

Use `VersionedSnapshot` with `SchemaVersion` tagging; register a `MigrationStep` for every schema version transition; always call `read_version` before restoring; and inspect the restore report's `skipped_settings` and `missing_settings_blocks` fields after every load. Surface gaps to the user via a toast rather than silently ignoring them. See [8.11 Persistence and Workspace/Session State](#811-persistence-and-workspacesession-state) for the full workflow.

**Q: How do I confirm my API usage is within the supported surface?**

Use explicit named imports from the `gui_do` root package only: `from gui_do import Feature, ObservableValue, ...`. Do not import from internal submodules like `gui_do.features.feature_lifecycle` or `gui_do.controls.button`. Run `tests/test_public_api_exports.py` to verify that every name you use appears in `gui_do.__all__`. The root import surface is the only surface covered by stability guarantees.

**Q: Why does my feature's `bind_runtime` seem to run before a sibling feature's `build` completes?**

It does not. The framework guarantees that all features registered to the same scene complete their `build` phase before any feature's `bind_runtime` is invoked. If you see ordering issues, confirm that both features declare the same `scene_name` in their `FeatureSpec` entries. A feature whose `scene_name` does not match the active scene will not be built in the same pass.

**Q: How do I add a keyboard shortcut without touching event handler code?**

Declare an `ActionSpec` in `HostApplicationConfig` with a unique `action_id`. Then declare an `ActionHotkeySpec` with the `action_id` and the key binding, either as a top-level entry in the config or inside a `RoutedRuntimeSpec` applied to the owning feature. The framework registers the binding with the action registry and input map automatically. No direct wiring in `handle_event` is needed for command-style shortcuts.

[Back to Table of Contents](#table-of-contents)

---

## Appendix

[Back to Table of Contents](#table-of-contents)

### Appendix A: Glossary

[Back to Table of Contents](#table-of-contents)

**Feature** — The primary unit of application behavior in gui_do. A feature is a Python class that subclasses one of the feature base types (`Feature`, `DirectFeature`, `LogicFeature`, `RoutedFeature`) and implements lifecycle phases (`build`, `bind_runtime`, `handle_event`, `on_update`, `draw`, `shutdown_runtime`). Features own a subtree of controls, hold observable state, subscribe to other features' observables, and handle input events within their scope. Features are registered via `FeatureSpec` in `HostApplicationConfig` and are instantiated and orchestrated by `FeatureManager`. A feature's identity is tied to a single scene; features do not span scenes.

**Spec** — A declarative data object that describes a runtime entity, wiring relationship, or configuration policy without executing any behavior itself. Spec objects are pure data: `FeatureSpec`, `ActionSpec`, `WindowSpec`, `RuntimeSceneSpec`, `RoutedRuntimeSpec`, `RoutedFeatureLifecycleSpec`, and so on. Bootstrap resolves all specs into live runtime objects in one coordinated pass. Using specs keeps application setup declarative and testable without requiring a running framework.

**Host** — A plain Python object (no special base class required) that is passed to `bootstrap_host_application`. Bootstrap populates it with runtime attributes: `host.app` becomes the live `GuiApplication`; other attributes hold managers, registries, and feature references as declared in the bootstrap config. Features receive the host object in every lifecycle method, giving them access to the full runtime surface through a single object rather than through global singletons.

**Scene** — A top-level interaction context within an application. Each scene has its own set of active features, windows, task panel, and action bindings. Only one scene is active at any time; scene transitions activate the arriving scene's features and deactivate the departing scene's features. Scenes are declared via `SceneSetupSpec` and given runtime policies via `RuntimeSceneSpec`. The `initial_scene_name` in `HostApplicationConfig` determines which scene is active on startup.

**Window presentation** — The system that coordinates floating window visibility, focus routing, task panel integration, and scene-menu toggle binding. A window is a focused work surface within a scene, implemented by a `WindowPresenter` subclass. Windows can be shown and hidden independently. Task panel buttons toggle window visibility. `TaskPanelFocusToggleSpec` ensures that hidden windows are excluded from the focus ring. The `ScenePresentationModel` tracks window registration and visibility state within a scene.

**Routed runtime** — A declarative bundle of per-feature runtime wiring: action hotkeys, shortcut overlay spec, task panel focus toggle spec, event subscription specs, and related registrations. Expressed as a `RoutedRuntimeSpec` and applied via `RoutedFeatureLifecycleSpec`. A single call to `bind_routed_feature_lifecycle` applies all registrations; `shutdown_routed_feature_lifecycle` removes them symmetrically. The routed runtime pattern is the preferred approach for features with complex wiring needs.

**Observable** — A value container that notifies all subscribed callbacks when its value changes. `ObservableValue`, `ObservableList`, and `ObservableDict` are the three observable primitives. `subscribe(callback)` returns a callable that, when called, removes the subscription. `ComputedValue` derives a new observable from one or more source observables. `reactive_batch` defers all subscriber notifications to the end of a `with` block. Observables are the mechanism for reactive state propagation in gui_do — they are not pygame or framework primitives, they are pure Python objects.

**Workspace state** — The persisted runtime context for a session: current scene name, feature-specific state, scene node snapshots, and settings values. Saved to JSON by `WorkspacePersistenceManager`. Restored by `GuiApplication.load_workspace`, which produces a structured restore report listing what was applied, skipped, and missing. Workspace state evolution across releases is managed by `SnapshotMigrator` with registered `MigrationStep` objects.

**Contract test** — An automated test in `tests/` that verifies a framework-level behavioral guarantee rather than an application-level behavior. Examples: `test_public_api_exports.py` guarantees all `__all__` names are importable; `test_boundary_contracts.py` guarantees no reverse imports from `gui_do/` into `demo_features/`; `test_runtime_operating_contracts.py` guarantees scheduler budget clamping. Contract tests are the release gate for the framework surface.

**Tier** — A grouping of related public API exports in `gui_do/__init__.py`, organized by abstraction level and recommended usage priority. Tier 1 contains the highest-level, most commonly used bootstrap and feature types. Higher tier numbers represent lower-level or more specialized primitives. The tier organization is documented in `docs/public_api_spec.md` and reflected in Appendix D.1.

---

### Appendix B: Lifecycle and Event Routing Sequence

[Back to Table of Contents](#table-of-contents)

The following numbered sequence is the authoritative reference for the order in which framework operations execute. Use this as a debugging aid when behavior occurs at an unexpected point.

1. **`bootstrap_host_application(host, config)`** — All spec objects in `HostApplicationConfig` are resolved into runtime objects in one pass: scenes, features, actions, windows, font roles, cursors, accessibility specs, telemetry, and workspace managers are initialized. `host.app` becomes the live `GuiApplication`. All registered features are instantiated but no lifecycle phases have run yet.

2. **Feature `build(host)` calls** — All features registered to the initial scene have their `build` method called. Controls are created and added to the scene tree. Observables are created. The framework guarantees that all `build` calls for a scene are completed before any `bind_runtime` call begins.

3. **Feature `bind_runtime(host)` calls** — After all `build` calls are complete, all features in the scene have `bind_runtime` called. Reactive subscriptions are wired. Routed lifecycle registrations are applied. Cross-feature references are established. At this point the full scene graph is available.

4. **Runtime loop begins** — `host.app.run_entrypoint(target_fps=...)` enters the frame loop.

5. **Each frame: pygame event polling and `GuiEvent` normalization** — Raw pygame events are polled. Each event is converted to a `GuiEvent` via `EventManager.to_gui_event`. Unknown event types map to `EventType.PASS`.

6. **Overlay / focus / window / scene routing pass** — Normalized events are processed by the overlay manager first. If an overlay is open and consumes the event, no further routing occurs. Otherwise, focus management and keyboard routing proceed based on scope (global, window, scene).

7. **Feature `handle_event(host, event)` calls** — Events not consumed by overlay/focus routing are passed to scene-registered feature handlers in stable order. A handler returns `True` to consume the event; returning `False` or `None` passes it to the next handler.

8. **Feature `on_update(host, dt)` calls; scheduler dispatch** — All scene features have `on_update` called. The cooperative scheduler dispatches coroutines within its per-frame budget (fraction 0.12, floor 0.5 ms, ceiling 4.0 ms). Tweens, timers, and animation state machines tick.

9. **Feature `draw(host, screen)` calls; control tree render; present** — All scene features with a `draw` method are called. The control tree renders all visible controls. The compositor presents the frame to the display surface.

10. **On scene transition** — `shutdown_runtime` is called for all features in the departing scene (in reverse build order). `build` and then `bind_runtime` are called for all features in the arriving scene.

11. **On application exit** — `shutdown_runtime` is called for all active features. The cooperative scheduler is stopped. Workspace state is saved if configured. `run_entrypoint` returns.

---

### Appendix C: System Dependency Map

[Back to Table of Contents](#table-of-contents)

The following map describes which systems depend on which, expressed as directional dependency relationships. Use this as an architecture reasoning tool when planning changes that might have cascading effects.

**Bootstrap (Tier 1) is the root assembly layer.** It depends on every spec type (Tier 1 spec objects), the feature lifecycle system, the scene/window presentation system, the action/input system, and the font/theme configuration. Changes to the bootstrap API surface ripple into all dependent systems.

**Features (Tiers 1–2) depend on controls, data/observables, and event/action systems.** A feature builds its control subtree (Tier 12–13), holds observable state (Tier 3), subscribes to other observables, and handles events routed by the event/action system (Tier 4). Features are the primary integration point for nearly every other system.

**Layout (Tier 8) and focus (Tier 4) depend on the control tree and scene/window visibility.** Layout engines operate on control bounds declared in `build`. Focus ring membership is determined by which controls are in the scene tree and which windows are currently visible. Changes to window visibility must be coordinated with both layout and focus.

**Overlays (Tier 9) depend on event routing and focus policy.** Overlays intercept events before the main routing chain. Modal overlays activate a `FocusScope` to lock Tab cycling to their control subtree. Overlay dismissal restores focus to the pre-overlay state.

**Persistence (Tiers 11, 32) depends on state models and scene/window registration.** Workspace save reads the active scene name, registered feature states, scene node snapshots, and settings registry values. Workspace restore replays these into the live runtime via `WorkspacePersistenceManager`. `SnapshotMigrator` sits above persistence and transforms old snapshots forward before they reach the runtime.

**Scheduling and animation (Tier 5) depend on the feature update loop and scene scope.** The cooperative scheduler is a per-scene resource. Coroutines, tweens, and timers are all cancelled when a scene deactivates. Animation state machines tick inside `on_update`, which only runs for active scene features.

**Telemetry and introspection (Tiers 7, 17) cross-cut all runtime layers.** Telemetry spans can be placed anywhere. `PropertyRegistry` collects `@ui_property` descriptors at module load time. `SceneSpatialIndex` is maintained alongside the live scene control tree. Neither system depends on other runtime systems, but both observe them.

**Audio (Tier 20) depends on the pygame mixer through `SoundEventBus`.** Features publish `SoundCue` events to `SoundEventBus`. The bus routes to the mixer without requiring the publishing feature to hold a mixer reference. This is a deliberate indirection: feature code is mixer-agnostic.

**Service scope (Tier 25) is usable at any tier as a dependency container.** `ServiceScope` and `ScopeStack` provide a lightweight inversion-of-control container that is independent of the gui_do bootstrap lifecycle.

---

### Appendix D: API Quick Index

[Back to Table of Contents](#table-of-contents)

This index groups all `gui_do` public API names by topic for quick lookup. Names are taken from the verified tier blocks in `gui_do/__init__.py`.

#### Bootstrap and Configuration

`HostApplicationConfig`, `HostApplicationBindingSpec`, `TelemetryConfig`, `bootstrap_host_application`, `build_host_application_config`, `declare_host_actions`, `build_host_main_tab_order`, `apply_host_main_accessibility`

#### Feature Types and Lifecycle

`Feature`, `DirectFeature`, `LogicFeature`, `RoutedFeature`, `FeatureMessage`, `FeatureManager`, `FeatureSpec`, `RoutedRuntimeSpec`, `RoutedFeatureLifecycleSpec`

#### Spec Objects (Bootstrap Declarations)

`ScenePresentationModel`, `SceneSetupSpec`, `WindowSpec`, `RuntimeSceneSpec`, `ActionSpec`, `StaticAccessibilitySpec`, `CursorSpec`, `SceneRootSpec`, `AnchoredWindowSpec`, `LogicBindingSpec`, `TaskPanelButtonSpec`, `TaskPanelWindowToggleGroupSpec`, `SceneCommandPaletteSpec`, `ActionHotkeySpec`, `ControlKeyBindingSpec`, `SceneTaskPanelSpec`, `TaskPanelLinearLayoutSpec`, `TaskPanelSceneNavButtonSpec`, `EventSubscriptionSpec`, `ShortcutOverlaySpec`, `TaskPanelFocusToggleSpec`, `FeatureWindowBundleBindingSpec`, `WindowToggleBindingSpec`, `SceneSetupBindingSpec`, `RuntimeSceneBindingSpec`, `SceneRootBindingSpec`, `CursorBindingSpec`, `FontRoleBindingSpec`, `ActionBindingSpec`, `PaletteBindingSpec`, `SceneBundleBindingSpec`, `TabbedPresenterSpec`, `AccessibilitySequenceSpec`, `TabBuilderSpec`, `NotificationSpec`

#### Builder and Factory Helpers (Tier 1)

`setup_standard_font_roles`, `make_window_toggle_spec`, `make_scene_nav_action`, `make_exit_action`, `make_palette_open_action`, `make_static_accessibility_spec`, `build_feature_specs`, `build_feature_window_bundle_specs`, `build_window_toggle_specs`, `build_scene_setup_specs`, `build_runtime_scene_specs`, `build_scene_root_specs`, `build_cursor_specs`, `build_font_role_specs`, `build_scene_nav_actions`, `build_action_specs`, `build_scene_bundle_specs`, `build_static_accessibility_specs`, `build_notification_center`, `ControlDefinition`, `build_specs_from_column_section`

#### Application and Scene Runtime (Tier 2)

`GuiApplication`, `create_display`, `SceneTransitionManager`, `SceneTransitionStyle`, `apply_scene_setup_specs`

#### Observables and Reactive State (Tier 3)

`ObservableValue`, `PresentationModel`, `ComputedValue`, `reactive_batch`, `is_batching`, `InvalidationTracker`, `ChangeKind`, `CollectionChange`, `ObservableList`, `ObservableDict`, `CollectionViewQuery`, `CollectionView`, `Binding`, `BindingGroup`, `ObservableStream`, `SelectionModel`, `SelectionMode`

#### Events and Input (Tier 4)

`EventPhase`, `EventType`, `GuiEvent`, `ValueChangeCallback`, `ValueChangeReason`, `EventManager`, `EventBus`, `GestureRecognizer`, `EventRecorder`, `EventPlayback`, `RecordedEvent`, `InputSnapshot`, `Signal`, `SignalConnection`

#### Actions and Input Map (Tier 4)

`ActionManager`, `ActionContext`, `ActionMiddleware`, `ActionDescriptor`, `ActionRegistry`, `InputMap`, `InputBinding`, `KeyChordManager`, `KeyChord`, `ChordStep`

#### Focus (Tier 4)

`FocusManager`, `FocusScope`, `FocusScopeManager`, `WindowFocusManager`, `FocusRing`

#### Scheduling and Animation (Tier 5)

`TaskEvent`, `TaskScheduler`, `Timers`, `TweenManager`, `TweenHandle`, `Easing`, `AnimationSequence`, `AnimationHandle`, `TransitionManager`, `TransitionSpec`, `TransitionEvent`, `AnimationStateMachine`, `AnimationTransitionMode`, `SceneTimeline`, `Debouncer`, `Throttler`, `CooperativeScheduler`, `CoroutineHandle`, `Pause`, `Sleep`, `WaitForEvent`, `WaitForSignal`, `WaitUntil`, `WaitForAll`

#### Theme, Font, and Design Tokens (Tier 6)

`FontManager`, `FontRoleRegistry`, `ColorTheme`, `ThemeManager`, `DesignTokens`, `ScopedTheme`, `ScopedThemeManager`

#### Telemetry (Tier 7)

`TelemetryCollector`, `TelemetrySample`, `configure_telemetry`, `telemetry_collector`, `analyze_telemetry_log_file`, `analyze_telemetry_records`, `load_telemetry_log_file`, `render_telemetry_report`

#### Layout (Tier 8)

`LayoutAxis`, `LayoutManager`, `WindowTilingManager`, `ConstraintLayout`, `AnchorConstraint`, `DockPane`, `DockTabs`, `DockSplit`, `DockWorkspace`, `FlexLayout`, `FlexItem`, `FlexDirection`, `FlexAlign`, `FlexJustify`, `GridLayout`, `GridTrack`, `GridPlacement`, `CellCaretLayout`, `CellCaretState`, `LayoutAnimator`, `LayoutPass`, `MeasureContext`, `ArrangeContext`, `LayoutRoot`, `ResponsiveLayout`, `Breakpoint`, `SnapGrid`, `AlignmentGuide`, `SnapComposer`, `SnapTarget`, `FlowLayout`, `FlowItem`, `Viewport`

#### Overlays, Dialogs, and Notifications (Tier 9)

`OverlayManager`, `OverlayHandle`, `Alignment`, `PlacementResult`, `PopupPlacement`, `Side`, `compute_popup_rect`, `DialogManager`, `DialogHandle`, `ToastManager`, `ToastHandle`, `ToastSeverity`, `ContextMenuManager`, `ContextMenuItem`, `ContextMenuHandle`, `CommandPaletteManager`, `CommandEntry`, `CommandPaletteHandle`, `TooltipManager`, `TooltipHandle`, `MenuBarManager`, `FileDialogManager`, `FileDialogOptions`, `FileDialogHandle`, `NotificationCenter`, `NotificationRecord`, `ResizeManager`, `CursorManager`, `CursorHandle`, `CursorShape`, `DragDropManager`, `DragPayload`, `ClipboardManager`, `TransferData`, `TransferManager`, `ShortcutHelpOverlay`, `ShortcutSection`, `ShortcutEntry`

#### Forms and Validation (Tier 10)

`FormModel`, `FormField`, `ValidationRule`, `FieldError`, `FormSchema`, `SchemaField`, `DocumentModel`, `WizardFlow`, `WizardStep`, `WizardHandle`, `ValidationResult`, `Validator`, `RequiredValidator`, `RangeValidator`, `LengthValidator`, `PatternValidator`, `CustomValidator`, `DependentValidator`, `ValidationPipeline`

#### Persistence and State Management (Tier 11)

`CommandHistory`, `Command`, `CommandTransaction`, `StateMachine`, `HierarchicalStateMachine`, `Router`, `RouteEntry`, `SettingsRegistry`, `SettingDescriptor`, `WorkspaceState`, `WorkspacePersistenceManager`, `DEFAULT_WORKSPACE_STATE_PATH`, `SceneSnapshot`, `NodeSnapshot`

#### Primary Controls (Tier 12)

`PanelControl`, `LabelControl`, `ButtonControl`, `ToggleControl`, `SliderControl`, `ScrollbarControl`, `CanvasControl`, `CanvasEventPacket`, `CanvasViewport`, `FrameControl`, `ImageControl`, `ArrowBoxControl`, `ButtonGroupControl`, `TabControl`, `TabItem`, `DockWorkspacePanel`

#### Extended Controls (Tier 13)

`TextInputControl`, `TextAreaControl`, `RichLabelControl`, `DropdownControl`, `DropdownOption`, `ListViewControl`, `ListItem`, `OverlayPanelControl`, `DataGridControl`, `GridColumn`, `GridRow`, `TreeControl`, `TreeNode`, `SplitterControl`, `SpinnerControl`, `RangeSliderControl`, `ColorPickerControl`, `ScrollViewControl`, `ProgressBarControl`, `AnimatedImageControl`, `ErrorBoundary`, `WindowControl`, `TaskPanelControl`, `WindowPresenter`, `MenuBarControl`, `MenuEntry`, `SceneMenuStripControl`, `NotificationPanelControl`, `PropertyInspectorPanel`, `ToolbarControl`, `ToolbarItem`, `StatusBarControl`, `StatusSlot`, `ExpanderControl`, `DatePickerControl`, `TimePickerControl`, `BreadcrumbControl`, `BreadcrumbItem`, `SplitButtonControl`, `SplitButtonOption`, `ChipInputControl`

#### Text and Localization (Tier 14)

`TextFormatter`, `NumericFormatter`, `PatternFormatter`, `FixedPatternFormatter`, `TextFlow`, `TextSpan`, `TextSearcher`, `TextMatch`, `StringTable`, `LocaleRegistry`

#### Data and Collections (Tier 15)

`VirtualItemSource`, `FixedItemSource`, `SortFilterProxySource`, `AsyncDataProvider`, `LoadState`, `LoadStateKind`, `ObjectPool`, `DataCache`, `CacheStats`, `ListDiffCalculator`, `ListDiff`, `DiffInsert`, `DiffRemove`, `DiffMove`

#### Graphics and Rendering (Tier 16)

`BuiltInGraphicsFactory`, `DirtyRegionTracker`, `DrawContext`, `DrawPhase`, `AssetRegistry`, `DebugOverlay`, `SurfaceCompositor`, `Layer`, `ShapeRenderer`, `SurfaceEffects`, `VectorPath`, `SpriteSheet`, `FrameAnimation`, `ParticleSystem`, `Emitter`, `ParticleLayer`, `TileSet`, `TileMap`, `RenderTarget`, `LiveRenderTarget`, `OffscreenRenderTarget`, `create_render_target`, `create_surface`, `Node2D`, `SceneGraph2D`, `Camera2D`

#### Introspection (Tier 17)

`SceneSpatialIndex`, `ui_property`, `PropertyDescriptor`, `PropertyRegistry`, `property_registry`, `PropertyInspectorModel`, `InspectedProperty`

#### Advanced Runtime Helpers (Tier 18)

`FrameTimer`, `TabPanelManager`, `WindowRelativeRect`, `resolve_scene_selection_callback`, `minimize_window_menu_entries`, `set_window_visible_state`, `toggle_window_visibility`, `create_anchored_feature_window`, `add_window_scene_menu_strip`, `inset_rect`, `centered_horizontal_strip_layout`, `split_slot_bounds`, `partition_rects`, `place_control`, `place_control_unlabeled`, `register_placed_control`, `add_group_label`, `PlacedControl`, `make_labeled_slot_height_fn`, `ControlRegistry`, `build_tools_menu_entries`, `add_standard_scene_menu_strip`, `apply_accessibility_sequence`, `apply_accessibility_sequence_from_attrs`, `register_companion_logic_features`, `ensure_scene_scheduler`, `sorted_window_bindings`, `collect_window_toggle_controls`, `apply_window_toggle_accessibility`, `add_window_toggle_task_panel_controls`, `add_task_panel_window_toggle_group`, `setup_scene_command_palette_key`, `register_window_toggle_tooltips`, `initialize_locale_registry`, `bind_input_map_actions`, `register_descriptors`, `resolve_canvas_local_point`, `apply_runtime_scene_pristine_assets`, `bind_runtime_scene_exit_keys`, `prewarm_runtime_scenes`, `add_task_panel_button`, `add_task_panel_buttons`, `register_tooltip_specs`, `register_action_hotkeys`, `draw_controls_prewarm`, `ensure_scene_task_panel`, `create_task_panel_linear_layout`, `add_task_panel_scene_nav_button`, `add_scene_task_panel_items`, `centered_overlay_rect`, `create_shortcut_help_overlay`, `bind_feature_event_subscription`, `unbind_feature_event_subscription`, `setup_routed_runtime`, `shutdown_routed_runtime`, `bind_task_panel_focus_toggle`, `add_window_control`, `add_window_label`, `add_window_button`, `add_window_button_row`, `instantiate_features_from_specs`, `register_features_from_specs`, `register_window_presentation_specs`, `register_window_tab_builders`, `build_tab_builder_specs`, `create_tab_control_from_specs`, `compute_tabbed_window_layout`, `setup_feature_presenter_tabs_from_window_content`, `register_window_tab_builder_specs`, `setup_feature_presenter_tabs`, `register_tab_update_handlers`, `create_presented_anchored_window`, `create_presented_window_from_spec`, `create_feature_presented_window`, `bind_feature_logic_aliases`, `setup_routed_feature_runtime`, `register_routed_feature_companions`, `bind_routed_feature_lifecycle`, `shutdown_routed_feature_lifecycle`, `ActiveTabUpdateRouter`, `TabLayoutContext`

#### Infrastructure Internals (Tier 19)

`UiEngine` — Avoid using directly in application code; this is framework infrastructure.

#### Audio (Tier 20)

`SoundCue`, `SoundBankRegistry`, `SoundEventBus`

#### Accessibility (Tier 21)

`AccessibilityRole`, `LivePoliteness`, `AccessibilityNode`, `AccessibilityTree`, `AccessibilityAnnouncement`, `AccessibilityBus`

#### Theme Invalidation (Tier 22)

`ThemeInvalidationBus`

#### Undo Context (Tier 23)

`UndoContextManager`

#### Async Form Validation (Tier 24)

`AsyncFieldValidator`, `AsyncFormValidator`

#### Service Scope (Tier 25)

`ServiceKey`, `ServiceScope`, `ScopeStack`

#### Dataflow Pipeline (Tier 26)

`CancellationToken`, `PipelineStage`, `DataflowPipeline`, `PipelineHandle`

#### Transactional App State (Tier 27)

`AppStateStore`, `StateSelector`, `StateTransaction`

#### Adaptive Constraint Layout (Tier 28)

`ConstraintAttr`, `LayoutConstraint`, `ConstraintSet`, `ConstraintLayoutEngine`, `AdaptivePolicy`, `resolve_adaptive_policy`

#### Virtualization (Tier 29)

`MeasureMode`, `MeasurePolicy`, `VirtualizedWindow`, `RecyclePool`, `VirtualizationCore`

#### Interaction State Machine (Tier 30)

`InteractionPhase`, `InteractionContext`, `InteractionTransition`, `InteractionStateMachine`

#### Schema-Driven Forms (Tier 31)

`FieldSchema`, `FieldGraphSchema`, `ValidationPolicy`, `SchemaFormRuntime`

#### Snapshot Migration (Tier 32)

`SchemaVersion`, `VersionedSnapshot`, `MigrationStep`, `MigrationRegistry`, `SnapshotMigrator`, `MigrationError`, `make_snapshot`, `read_version`

[Back to Table of Contents](#table-of-contents)

---

#### D.1 Tier-to-System Reference Matrix

[Back to Table of Contents](#table-of-contents)

| Tier | System | Representative Key Types |
|------|--------|--------------------------|
| 1 | Bootstrap and spec declarations | `HostApplicationConfig`, `bootstrap_host_application`, `FeatureSpec`, `ActionSpec`, `RoutedRuntimeSpec` |
| 2 | Application and scene runtime | `GuiApplication`, `create_display`, `SceneTransitionManager`, `SceneTransitionStyle` |
| 3 | Observables and reactive state | `ObservableValue`, `ObservableList`, `ComputedValue`, `reactive_batch`, `CollectionView` |
| 4 | Events, actions, input, focus | `GuiEvent`, `EventType`, `ActionManager`, `InputMap`, `FocusManager`, `FocusScope` |
| 5 | Scheduling and animation | `CooperativeScheduler`, `TweenManager`, `AnimationStateMachine`, `Debouncer`, `Sleep` |
| 6 | Theme, font, and design tokens | `ThemeManager`, `ColorTheme`, `FontRoleRegistry`, `DesignTokens`, `ScopedThemeManager` |
| 7 | Telemetry | `TelemetryCollector`, `configure_telemetry`, `analyze_telemetry_records`, `render_telemetry_report` |
| 8 | Layout engines | `FlexLayout`, `GridLayout`, `ConstraintLayout`, `DockWorkspace`, `FlowLayout`, `Viewport` |
| 9 | Overlays and command surfaces | `OverlayManager`, `DialogManager`, `ToastManager`, `CommandPaletteManager`, `ShortcutHelpOverlay` |
| 10 | Forms and validation | `FormModel`, `FormSchema`, `ValidationPipeline`, `WizardFlow`, `DocumentModel` |
| 11 | Persistence and state management | `WorkspacePersistenceManager`, `SettingsRegistry`, `CommandHistory`, `StateMachine` |
| 12 | Primary controls | `PanelControl`, `LabelControl`, `ButtonControl`, `CanvasControl`, `TabControl` |
| 13 | Extended controls | `TextInputControl`, `ListViewControl`, `DataGridControl`, `WindowPresenter`, `ErrorBoundary` |
| 14 | Text and localization | `TextFormatter`, `TextFlow`, `TextSearcher`, `StringTable`, `LocaleRegistry` |
| 15 | Data and collections | `VirtualItemSource`, `SortFilterProxySource`, `AsyncDataProvider`, `DataCache`, `ListDiffCalculator` |
| 16 | Graphics and rendering | `DirtyRegionTracker`, `SurfaceCompositor`, `ParticleSystem`, `SceneGraph2D`, `Camera2D` |
| 17 | Introspection | `SceneSpatialIndex`, `ui_property`, `PropertyRegistry`, `PropertyInspectorModel` |
| 18 | Advanced runtime helpers | `set_window_visible_state`, `create_feature_presented_window`, `bind_routed_feature_lifecycle`, `ActiveTabUpdateRouter` |
| 19 | Infrastructure internals | `UiEngine` — framework use only |
| 20 | Audio | `SoundCue`, `SoundBankRegistry`, `SoundEventBus` |
| 21 | Accessibility | `AccessibilityTree`, `AccessibilityNode`, `AccessibilityRole`, `AccessibilityBus` |
| 22 | Theme invalidation | `ThemeInvalidationBus` |
| 23 | Undo context | `UndoContextManager` |
| 24 | Async form validation | `AsyncFieldValidator`, `AsyncFormValidator` |
| 25 | Service scope | `ServiceKey`, `ServiceScope`, `ScopeStack` |
| 26 | Dataflow pipeline | `DataflowPipeline`, `PipelineStage`, `CancellationToken`, `PipelineHandle` |
| 27 | Transactional app state | `AppStateStore`, `StateSelector`, `StateTransaction` |
| 28 | Adaptive constraint layout | `ConstraintLayoutEngine`, `AdaptivePolicy`, `resolve_adaptive_policy`, `ConstraintSet` |
| 29 | Virtualization | `VirtualizationCore`, `VirtualizedWindow`, `RecyclePool`, `MeasurePolicy` |
| 30 | Interaction state machine | `InteractionStateMachine`, `InteractionPhase`, `InteractionTransition` |
| 31 | Schema-driven forms | `SchemaFormRuntime`, `FieldGraphSchema`, `ValidationPolicy`, `FieldSchema` |
| 32 | Snapshot migration | `SnapshotMigrator`, `MigrationRegistry`, `MigrationStep`, `make_snapshot`, `read_version` |

[Back to Table of Contents](#table-of-contents)

---

#### D.2 Public API Selection Heuristics

[Back to Table of Contents](#table-of-contents)

Use these decision rules to choose the right API for a task:

1. **Start at Tier 1.** If `HostApplicationConfig` + `bootstrap_host_application` + Feature types solve the problem, stop there. Most application-level concerns are covered by Tier 1 spec objects and Tier 3 observables.

2. **Descend one tier at a time when you need finer control.** Moving from `ObservableValue` (Tier 3) to `AppStateStore` (Tier 27) is appropriate when multiple features share state and you need atomic multi-field updates. Moving from `Feature` to `RoutedFeature` (Tier 1) is appropriate when you need declarative runtime wiring. Do not skip tiers.

3. **Use Tier 18 helpers when extending bootstrap behavior.** The Tier 18 helpers (`bind_routed_feature_lifecycle`, `create_feature_presented_window`, `add_standard_scene_menu_strip`, etc.) are the stable extension points for advanced application assembly patterns. They are not internal APIs; they are the intended mechanism for composition beyond the Tier 1 spec declarations.

4. **Never import from `gui_do.*` submodules in application code.** Always use `from gui_do import ...` from the root package. The root `__init__.py` surface is the only surface with stability guarantees. Internal submodule paths (`gui_do.features.feature_lifecycle`, `gui_do.controls.button`, etc.) may change without notice.

5. **Avoid Tier 19 (`UiEngine`) in application code.** `UiEngine` is framework infrastructure. Its interface is not part of the application-level stability guarantee.

**Decision shortcuts:**

| Goal | First API to reach for |
|------|------------------------|
| App setup | `HostApplicationConfig` + `bootstrap_host_application` |
| Reactive UI | `ObservableValue` + `subscribe` |
| Cross-feature behavior | Lifecycle specs + `RoutedRuntimeSpec` |
| Action/hotkey wiring | `ActionSpec` + `ActionHotkeySpec` (or `RoutedRuntimeSpec`) |
| Heavy dataset UI | `VirtualizationCore` / `SortFilterProxySource` |
| Maintainable persistence | `WorkspacePersistenceManager` + `SnapshotMigrator` |
| Discoverable shortcuts | `ShortcutOverlaySpec` in `RoutedRuntimeSpec` |
| Background work | `CooperativeScheduler` coroutines or `DataflowPipeline` |
| Audio | `SoundEventBus.publish(SoundCue(...))` |
| Performance investigation | `configure_telemetry` + `analyze_telemetry_records` |

[Back to Table of Contents](#table-of-contents)

---

### Appendix E: Architecture Templates

[Back to Table of Contents](#table-of-contents)

The following templates describe the structural skeleton of two common application archetypes. Use them as starting points for new projects.

**Template 1: Small Single-Scene Application**

This template covers apps with a single scene, a small number of features (2–4), and no floating windows or task panel.

- One `SceneSetupSpec` and one `RuntimeSceneSpec` with `bind_escape_to_exit=True`.
- 2–4 `FeatureSpec` entries, each pointing to a `Feature` subclass.
- `ObservableValue` state owned by each feature; subscriptions in `bind_runtime`, disposed in `shutdown_runtime`.
- `ActionSpec` entries for commands (exit, toggle-shortcuts).
- No `SceneTaskPanelSpec`, no `WindowPresenter`, no task panel buttons.

This is the pattern shown in the End-to-End Reference Application chapter. The counter feature is a complete, self-contained example.

**Template 2: Multi-Window Workbench**

This template covers apps with multiple scenes, multiple floating windows per scene, a task panel, scene navigation, and a command palette.

- Two or more `SceneBundleBindingSpec` entries (via `HostApplicationBindingSpec`), each generating the scene setup, runtime scene, root, and nav action entries automatically.
- A `SceneTaskPanelSpec` per scene, or a shared task panel layout via `TaskPanelLinearLayoutSpec`.
- One `FeatureWindowBundleBindingSpec` per window, which generates the feature spec, window spec, task panel button, focus toggle, and accessibility annotation in one declarative entry.
- `WindowPresenter` subclass per floating window, with `TabbedPresenterSpec` + `TabBuilderSpec` for tabbed windows.
- `RoutedRuntimeSpec` with `ShortcutOverlaySpec` for the primary scene's shortcut help overlay.
- `SceneCommandPaletteSpec` for command-palette access to all registered actions.
- `add_standard_scene_menu_strip` called in each scene's `bind_runtime` to wire the window-management menu strip.
- `WorkspacePersistenceManager` with workspace load on startup and save on exit.
- `SnapshotMigrator` with `MigrationRegistry` for handling schema evolution across releases.

[Back to Table of Contents](#table-of-contents)
