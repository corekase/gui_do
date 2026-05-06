# gui_do Manual

## Title and Purpose

This manual is the primary end-to-end learning and reference source for gui_do. It is written for application developers who need a practical path from first principles to production patterns and for maintainers who need a stable operational reference that stays aligned with code, tests, and contracts. The document is organized so that conceptual foundations come first, system-level reference follows, and operational guidance closes the loop for testing, migration, and long-term maintenance.

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

**Beginner Path:**
1. Read Conceptual Foundations (Section 4) fully.
2. Work through Quickstart Path (Section 5).
3. Read Architecture and Runtime Model (Section 6).
4. Read Core Workflow (Section 7).
5. Read systems 8.1 through 8.4 before building your first multi-feature scene.
6. Use the End-to-End Reference Application (Section 10) as a map when wiring your own app.

**Intermediate Path:**
1. Refresh Conceptual Foundations only where your mental model is weak.
2. Read Section 7 and the system chapters you are actively composing.
3. Use Integration Patterns (Section 9) to compose multiple systems coherently.
4. Keep Appendix D and D.2 nearby for API selection and abstraction-level decisions.

**Maintainer Path:**
1. Inventory changes in root exports, contracts, tests, and demo composition patterns.
2. Use Testing, Diagnostics, and Reliability (Section 11) and the Maintainer Diff Checklist.
3. Validate navigation integrity and chapter-to-appendix consistency before publishing manual updates.

### Tri-Lens Markers

This manual is authored through three complementary lenses.

- **Learn**: explains conceptual intent, rationale, and mental models.
- **Build**: explains implementation flow, practical defaults, and composition techniques.
- **Maintain**: explains conformance checks, diff review, and long-horizon operational stewardship.

If you are short on time, prefer Build-first reading for immediate work and then backfill Learn sections to avoid accidental anti-patterns. Maintain sections should be treated as release-quality gates, not optional notes.

### Contract Alignment

Behavioral guarantees in this manual align to contract sources in docs and tests. The normative runtime behavior sources are `docs/runtime_operating_contracts.md`, `docs/public_api_spec.md`, and `docs/architecture_boundary_spec.md`. Public API surface commitments are anchored to `gui_do/__init__.py` exports. Contract and runtime tests under `tests/` are the executable verification layer that confirms those guarantees remain true.

When this manual and a contract source diverge, treat contract documents and enforcing tests as authoritative and update manual prose accordingly. The goal is not literary consistency; it is behavioral accuracy under current code.

### Known Non-Goals

gui_do intentionally does not aim to:

- Provide a complete game engine; for 2D game development, use pygame directly or a game-focused framework.
- Support cross-platform network synchronization; it is a local GUI library.
- Implement a constraint solver for arbitrary mathematical constraints; it provides layout-specific constraint engines.
- Provide built-in web/remote rendering; it is a local-process GUI framework backed by pygame.
- Replace platform-native dialogs; file dialogs on macOS/Windows wrap native APIs, but gui_do owns all other window chrome.
- Guarantee pixel-perfect rendering across DPI configurations; it maintains ratio consistency and provides DPI-aware scaling.

Understanding these boundaries helps avoid misuse and sets correct expectations for what gui_do is designed for.

## Conceptual Foundations (Theory)

[Back to Table of Contents](#table-of-contents)

The conceptual foundations section establishes the mental models and design philosophies that gui_do is built upon. These concepts appear throughout the codebase and every system in the manual builds on the principles introduced here. Developers should read this section completely before engaging with specific systems, as later chapters assume familiarity with the terminology and design intent described below.

### Data-Driven Design

[Back to Table of Contents](#table-of-contents)

In gui_do, application structure is expressed as configuration data — specs, bindings, and descriptors — rather than as sequences of imperative calls. Instead of writing long setup code that manually instantiates controls, registers handlers, and wires keyboard routes in place, you declare intent through spec objects. The framework interprets those specs and builds the live application. This separates what the application should contain from when and how each part is wired, resulting in predictable startup behavior and a clearer boundary between architecture and behavior.

**What it means in practice:**

When you sit down to build a gui_do application, your first task is not to write event handlers. Instead, you populate spec objects with metadata describing your scene structure, features, actions, and visual appearance. A `SceneSetupSpec` describes a scene context. A `FeatureSpec` describes which Feature class to instantiate and how. An `ActionSpec` describes a user action like "Save" or "Undo" with its label and kind. A `WindowSpec` or `AnchoredWindowSpec` describes where a floating window should appear and how to present its content. You collect all of these into a `HostApplicationBindingSpec` or directly into a `HostApplicationConfig`. This config object becomes a complete declarative description of your application's structure, before a single frame has been rendered or a single event processed.

At the center of this model is the **spec pipeline**: `HostApplicationBindingSpec` plus builder helpers such as `build_feature_specs`, `build_action_specs`, `build_scene_setup_specs`, and `build_scene_bundle_specs`, culminating in `build_host_application_config`. The builder stage is a single deterministic pass that resolves cross-references between specs, applies validation rules, normalizes naming conventions, and materializes a fully wired `HostApplicationConfig` ready for bootstrap. The execution stage begins only when `bootstrap_host_application` receives that config and passes it to `GuiApplication`. This two-stage design is intentional because it gives you one stable, inspectable object graph to verify before the runtime loop begins. You can serialize it, log it, validate it in tests, and ensure all references are satisfied before any code actually runs.

**How this differs from imperative wiring:**

In an imperative approach, adding a keyboard shortcut to your application often requires: finding the event-handling code in your event loop or event handler class; inserting a new conditional branch checking the key code; wiring a callback function to handle the key; ensuring cleanup and unregistration when the feature or scene exits; potentially updating help text or menu listings manually. Changes cascade across multiple places and are easy to get wrong if any cleanup step is forgotten.

In gui_do's data-driven approach, you add one `ActionSpec` entry to your config with an action ID, a display label, and optionally an `ActionHotkeySpec` or `ControlKeyBindingSpec` specifying the key or control activation. The framework automatically: registers the action with the action registry; validates that the action ID is unique within scope; creates an input binding; routes the key through the input map according to scene and window scope policies; manages registration and teardown based on scene/runtime lifecycle; ensures cleanup happens automatically when the scene or window exits; and optionally displays the shortcut in keyboard help surfaces. The developer never touches the router or writes cleanup code. The wiring is declared, validated, and executed by the framework.

**Reorganization without bootstrap impact:**

A profound consequence of data-driven design is that internal package refactoring becomes transparent to bootstrap code. If you decide to reorganize a feature package — moving the Feature class from `feature.py` to a `behavior/` subdirectory, splitting presenter logic into its own `presenter_impl.py` module, extracting helper functions into a separate `_helpers.py` file — the bootstrap code does not need to change at all. The bootstrap only depends on public class references (what the package exports from its `__init__.py`) and spec values (declared in configuration modules). As long as each feature package's `__init__.py` continues to export the same public `Feature` class and any public spec constants, the bootstrap remains completely insulated from structural changes inside the package. This freedom to refactor internal structure without touching bootstrap is unusual and valuable in large codebases.

**Testability:**

Data-driven design makes the framework trivially testable at every level. Configuration specs can be constructed and validated in unit tests with no running display — you can instantiate a `HostApplicationConfig`, inspect its scene/feature/action memberships, and verify error behavior without rendering a window or entering the event loop. Feature instances can be built with lightweight mock host objects for unit testing their `build` and `bind_runtime` hooks. The entire app config can be assembled, inspected, and validated in isolation from pygame and the UI event loop. This determinism is only possible because the application's structure is data, not hidden inside call sequences and imperative state changes. When structure is data, testing becomes straightforward.

**The design philosophy behind specs:**

The framework's authors chose to expose richer, named specs over primitive arguments because **named specs are inherently self-documenting, composable, and forward-compatible**. A `ShortcutOverlaySpec` with named fields like `include_scene_entries`, `include_window_entries`, and `group_order` is immediately clear to a reader without consulting documentation. A raw positional-argument API cannot offer the same clarity. More importantly, specs are forward-compatible: adding a new optional field to a spec in a future gui_do version does not break existing caller code (as long as you provide a sensible default). A positional-argument API forces all existing callers to update their call signatures, breaking compatibility.

Specs are also the serialization boundary: they are pure data structures (usually dataclasses) and could in principle be stored as JSON, loaded from configuration files, or generated programmatically by tooling. This makes specs a natural interchange point for future tools — a visual designer, a configuration generator, or a test harness. Specs separate data (what to build) from code (how to build it).

**Where the boundary is:**

The philosophical boundary is clear: describe structure declaratively, implement behavior imperatively. Wiring of the application (scene graph construction, action registry setup, input routing, feature orchestration, window presentation) is data-driven. The runtime behavior of individual features (what they do in `on_update`, `handle_event`, and `draw` methods) is imperative Python inside feature methods. When a feature's `handle_event` method receives a user action, it can execute any imperative logic it wants. But the wiring that gets that event to that feature in the first place is declarative and managed by the framework.

### Reactive Data and Observable State

[Back to Table of Contents](#table-of-contents)

Reactive state in gui_do means consumers subscribe to observe changing values automatically when those values change. Producers do not need direct references to all consumers. This is a major shift from traditional imperative UI update style, where every mutation must manually push updates into labels, lists, badges, and secondary state. Reactive flow inverts the dependency: the data holds a list of subscribers and notifies them, rather than the producer needing to know who to update.

**What reactive data means in practice:**

In a traditional imperative GUI, the update flow is push-based and manual. Your domain logic computes a result (for example, a list of filtered items) and must then reach out and manually update every UI element that should reflect that result: clear the old list, add new items, update the item count badge, recalculate layout, redraw affected regions. If a UI element is added later or the display logic changes, the domain logic must be updated too. Coupling grows over time.

In a reactive model, the data itself holds a subscription list. When the value changes, the data automatically notifies all subscribers. Subscribers can attach and detach without the producer knowing or caring. A UI element subscribes to an observable once during construction and then simply reacts to notifications. No manual push; no coupling; no synchronization logic needed. The reactive contract is: your job is to update the data, our job is to propagate the change.

**The observable primitives:**

gui_do provides three core reactive primitives from Tier 3: `ObservableValue` for single scalar values, `ObservableList` for ordered mutable collections, and `ObservableDict` for key-value maps. Each can have zero, one, or many subscribers.

`ObservableValue` is the simplest: it wraps a single value of any type. You call `.subscribe(callback)` to register a callback function; the callback is invoked whenever the wrapped value changes via `.value = new_value`. The subscription method returns an unsubscribe function; calling it removes the callback and stops future notifications. Example:

```python
count = ObservableValue(0)

def on_count_changed(new_count):
    print("count is now", new_count)

unsubscribe = count.subscribe(on_count_changed)
count.value = 5  # prints "count is now 5"
unsubscribe()
count.value = 10  # does nothing; unsubscribed
```

`ObservableList` and `ObservableDict` work similarly but notify with `CollectionChange` events that identify what was added, removed, or moved rather than replacing the entire collection. These are the building blocks for all live data that drives UI in gui_do, and virtually every piece of shared state should be expressed as one of these types.

**Batching and `reactive_batch`:**

When a single logical operation mutates multiple observables (for example, loading a record: set the name field, set the email field, set the birthdate field), firing notifications after each individual mutation causes subscribers to react multiple times with partially-updated state. Use `reactive_batch` to defer all notifications until the batch completes:

```python
from gui_do import reactive_batch

with reactive_batch():
    record.name.value = "Alice"
    record.email.value = "alice@example.com"
    record.age.value = 30
    # All three subscribers fire exactly once, when the context exits
```

Use batching for all multi-observable operations where intermediate states do not represent valid domain state. For single-observable changes, batching is unnecessary overhead.

**Derived and computed state:**

When one observable should always reflect a function of another (for example, a label text that shows the count of items in an observable list), gui_do provides `ComputedValue`. Rather than manually subscribing to the source and writing to a second `ObservableValue`, `ComputedValue` models the dependency as a first-class reactive projection:

```python
from gui_do import ComputedValue

items = ObservableList([...])
item_count = ComputedValue(lambda: len(items.items), depends_on=[items])
label.text = item_count  # Now label always shows current item count
```

Manual derivation is still valid when custom timing or side effects are required (for example, loading external data based on a selection change). But for pure data transformations, `ComputedValue` is clearer and more maintainable.

**Subscription lifecycle and cleanup discipline:**

Subscription lifecycle discipline is mandatory for memory safety and correctness. Most subscriptions should be created in `bind_runtime` (after all controls exist and cross-feature wiring is possible) and removed in `shutdown_runtime`. Registering subscriptions too early can race against control availability or runtime initialization. Forgetting to unsubscribe produces memory leaks — the subscriber callback object stays reachable, preventing garbage collection — and causes stale callbacks to fire on dead objects, producing errors and confusing behavior.

A clean pattern:

```python
class MyFeature(Feature):
    def __init__(self):
        super().__init__("my_feature")
        self.data = ObservableValue(0)
        self._unsubscribe_data = None

    def bind_runtime(self, host):
        def _on_data_changed(new_value):
            self.label.text = str(new_value)
        self._unsubscribe_data = self.data.subscribe(_on_data_changed)

    def shutdown_runtime(self, host):
        if callable(self._unsubscribe_data):
            self._unsubscribe_data()
            self._unsubscribe_data = None
```

**Control binding model:**

Controls in gui_do generally expose a value property that accepts either a plain value or an observable. When bound to an observable, the control registers an internal subscription and refreshes its displayed value automatically whenever the observable changes. This means feature code never needs to touch a control to update its displayed state — it only needs to change the observable, and the control updates itself. This is the correct approach because it keeps features decoupled from specific control implementations (you can swap one control for another without changing feature logic) and makes it easy to test feature logic in isolation from control rendering.

**Cross-feature reactive state:**

When multiple features need to share live data, the preferred approach is for one feature to own an `ObservableValue` and expose it through its public interface; other features subscribe to that observable in their `bind_runtime` methods. The producing feature never knows who is observing, and observers do not depend on the producer's internal implementation — only on the published state shape. This is looser coupling than direct method calls and scales well as feature counts grow. Set up these shared-state relationships in `bind_runtime` when both the owning feature and consumer features are already built and the host is available to coordinate them.

**Anti-patterns and what to avoid:**

Several reactive anti-patterns appear consistently across projects. **Polling in `on_update`**: repeatedly reading an observable value in the frame hook instead of subscribing creates unnecessary CPU load and introduces frame-of-latency before changes propagate. Subscribe instead. **Subscribing in `build`** rather than in `bind_runtime`: if subscriptions are created before the runtime wiring phase, they may fire before controls exist, causing reference errors. Always subscribe in `bind_runtime`. **Forgetting to unsubscribe**: this produces memory leaks (callback closures retain references, preventing garbage collection) and causes stale callbacks to execute on shutdown. Clean up in `shutdown_runtime`. **Sharing mutable plain Python objects across features** instead of observables: without observable wrappers, consumers have no way to know when shared state changes, and mutations bypass any validation or notification logic. Always use observable types for shared state.

### Feature Composition and Lifecycles

[Back to Table of Contents](#table-of-contents)

Features are the primary unit of application behavior composition in gui_do. A Feature is a self-contained object that declares what resources it requires from the host, builds its own UI elements, registers its own event handlers, and tears itself down cleanly. Features are composable: an application is built by combining multiple features that coexist in scene scope, each managing its own slice of UI and data. The framework orchestrates their lifecycle phases in the correct order and routes events to the correct feature.

**What a Feature is:**

A Feature encapsulates behavior responsibilities. It expresses its host dependencies explicitly through the `HOST_REQUIREMENTS` protocol rather than relying on hidden assumptions about what the host provides. It builds its own controls in a `build` phase (no controls are created before the feature's `build` is called), registers its own callbacks and bindings in `bind_runtime` (after all sibling features are also built), and cleans up its own runtime state in `shutdown_runtime` (before the feature is removed). Features do not hold references to other features directly; instead, they communicate through `FeatureMessage` publishing and subscription, which maintains loose coupling.

**Feature types and when to use each:**

gui_do provides four feature base classes for different composition needs.

`DirectFeature` is for frame-timed direct rendering that does not need the control tree. It renders directly to the pygame surface every frame. Use `DirectFeature` for background elements (animated backdrops, full-screen effects, particle systems, scrolling tile maps) that would be inefficient to represent as controls. DirectFeature is the lowest-overhead feature type because it bypasses control-tree abstraction and render scheduling. It exposes `on_direct_update(host, dt_seconds)` and `draw_direct(host, screen)` instead of the regular `on_update` and `draw` hooks, and it is ticked separately from regular features. Use this type when you need precise frame-delta timing and direct surface access.

`Feature` is the standard feature type for interactive UI composition. It builds controls in the scene's control tree during `build`, participates in focus management, hit-testing, and event routing through the normal control flow. Use `Feature` for any feature that displays interactive UI, handles input, or manages visible controls. This is the most common feature type.

`LogicFeature` has no UI of its own. It exists to hold pure domain logic, manage shared state, run background computation, and publish results that other features react to. Use `LogicFeature` when behavior should be separated from presentation and tested independently. Logic features are ideal for orchestration patterns where a computation feature publishes data that multiple UI features display, or where a rules engine needs to drive multiple visual surfaces.

`RoutedFeature` extends `Feature` with built-in message routing infrastructure. It can define route targets (named message handlers) that receive framework-dispatched messages and route them to specific methods. Use `RoutedFeature` when a feature must respond to framework-level actions, coordinate with the action registry, or handle topic-dispatched messages from other features in a structured way.

**Lifecycle phases in depth:**

Feature lifecycle has six distinct phases, each with clear responsibilities and a defined point in the runtime sequence.

`build(host)`: Called once when the scene is being constructed. At this point, no other features in the scene have built controls yet, but the host services (app, display, scene root, etc.) are available via `HOST_REQUIREMENTS`. Use this phase to create controls and add them to the scene tree, build window specs, establish static structure that will not change during the scene's lifetime, and perform any initialization that does not depend on cross-feature availability. Controls created in `build` exist for the lifetime of the scene. Do not subscribe to observables or access sibling features in this phase; that happens in `bind_runtime`.

`bind_runtime(host)`: Called after all features in the scene have completed `build`. At this point, all controls exist, all sibling features are built, and cross-feature wiring is safe. Use this phase to subscribe to observable values, bind controls to data sources, register action handlers and input bindings, initialize state from runtime sources (screen size, loaded settings, etc.), and wire up cross-feature interactions. This is where observable subscriptions are established. Any references to sibling features must be obtained here, not before.

`handle_event(host, event)`: Called for every `GuiEvent` that reaches the feature. The routing layer filters events by scene, focus, and overlay state before calling this method. Implement this method to handle keyboard input, pointer events, or custom application events. Return `True` to consume the event and stop further propagation; return `False` or `None` to pass it on to the next handler.

`on_update(host, dt_seconds)`: Called on every frame with the delta time since the previous frame. Use for animations, timers, polling background results, and any per-frame state updates. Keep this method fast; avoid expensive computation here because it blocks UI responsiveness.

`draw(host, screen, theme)`: Called on every frame after `on_update`. The screen surface is ready for drawing. Use for custom drawing operations that bypass the control tree (particles, canvas effects, overlays). Most features do not need this hook because controls handle their own rendering. Implement `draw` only when you need custom visuals beyond standard control composition.

`shutdown_runtime(host)`: Called when the feature is being removed from a scene transition. Use this phase to dispose subscriptions, unregister callbacks and input bindings, clean up resources, and restore any global state. Failing to clean up subscriptions causes memory leaks and stale callbacks. Always pair every `subscribe` call in `bind_runtime` with an `unsubscribe` call here.

**The `HOST_REQUIREMENTS` protocol:**

Each lifecycle method declares what it requires from the host via the `HOST_REQUIREMENTS` class dictionary. This provides a declarative contract that the framework validates before invoking the method. If the host does not provide a required attribute, bootstrap raises a clear error message before startup rather than failing mysteriously later. Example:

```python
class MyFeature(Feature):
    HOST_REQUIREMENTS = {
        "build": ("app", "screen_rect", "scene_presentation"),
        "bind_runtime": (),
        "shutdown_runtime": (),
    }

    def build(self, host):
        # host.app, host.screen_rect, host.scene_presentation are guaranteed to exist
        self.app = host.app
```

The framework calls `validate_host_for(host, "build")` before invoking `build`, which checks that all named attributes are present and raises if any are missing. This removes hidden assumptions and makes host-shape failures explicit and early, which is especially valuable when features are reused across scenes or integrated into different demo assemblies.

**Inter-feature communication:**

Features do not hold direct references to each other. Instead, the `FeatureMessage` envelope provides structured transport: each message has a sender (the feature publishing it), a target (the feature meant to receive it), and a payload (any data). The `FeatureManager` manages a message queue and feature-registered handlers. When one feature wants to signal another, it enqueues a message; the manager delivers it to any feature that has registered a handler for that message type.

This is the loose-coupling mechanism that prevents features from depending on each other's implementations. A `LogicFeature` can publish a "data_loaded" message with a payload, and any UI features that care about data changes can listen for that message without the logic feature knowing who they are or what they'll do with the data. Features can be reused in different scenes and with different peer features without modification.

**Scene assignment and multi-scene composition:**

Each feature declares its scene membership via the `scene_name` parameter in its constructor. A feature belongs to exactly one scene (or the global scene for features that persist across scene transitions). The framework activates and deactivates features as scenes transition — calling `shutdown_runtime` on departing scene features and `build`/`bind_runtime` on arriving scene features. This makes scene transitions safe: features from the previous scene do not receive events or update calls after the transition, so there is no risk of stale state from one scene leaking into another. Scene-local features are automatically isolated from each other during transitions.

**The folder/package composition convention:**

The established organizational convention in demo_features and well-structured features is: each feature package lives in its own folder with a clear public/private boundary. The `__init__.py` file is the sole public surface — it exports the Feature class and any public types, and nothing else. Internal implementation files are separated by concern: the main feature file owns the Feature class and lifecycle methods; the presenter file (if needed) owns `WindowPresenter` subclasses and window composition logic; the specs file owns shared constants and spec objects; companion logic files own background computation or rules engines; standalone data types live in their own files. This organization makes each file's purpose immediately clear from its name and prevents concerns from bleeding across files.

Crucially, bootstrap code never imports from internal submodules — it only imports from the package surface (`__init__.py`). This means any internal reorganization is completely transparent to bootstrap consumers. A feature can split its Feature class and presenter across two files, extract helper functions, or rename internal modules without breaking a single import in the bootstrap code.

**Composition recipes:**

Three composition patterns are particularly effective across projects.

**Logic/presentation split**: A `LogicFeature` owns and publishes domain state through observables. A `RoutedFeature` or `Feature` consumes those observables and drives the UI. The logic feature runs computations and publishes results; the presentation feature displays those results and captures user input, which it sends back to the logic feature via messages. This is the cleanest separation and makes both halves independently testable. Example: a background file-search logic feature publishes an observable list of results; a search-UI feature displays that list and publishes user queries as messages.

**Presenter pattern**: A `WindowPresenter` subclass owns window-scale composition — creating child controls, managing their layout, and handling window-specific behavior. The parent Feature owns lifecycle and routing responsibilities but delegates window content assembly to the presenter. Use this pattern when a feature needs to present content across multiple windows or when window-specific layout logic is complex enough to deserve its own class.

**Background coordination pattern**: A `LogicFeature` runs a long-running workflow (using `CooperativeScheduler` coroutines or a dataflow pipeline) and publishes progress through observables or messages. One or more UI features display progress, handle cancellation, and react to completion. The logic feature is free to run expensive work without blocking the UI because coroutines yield control back to the scheduler. Keep feature hooks lightweight and let the scheduler manage work pacing.



## Quickstart Path (Practice)

[Back to Table of Contents](#table-of-contents)

Use this path when you want a runnable app quickly while preserving architecture contracts.

1. Install dependencies and verify root exports with a targeted contract test.
2. Define a host class and a minimal `HostApplicationConfig`.
3. Add one feature via `FeatureSpec` and one scene via `SceneSetupSpec`/`RuntimeSceneSpec`.
4. Bootstrap with `bootstrap_host_application`.
5. Run with `run_entrypoint` and then add actions, overlays, and persistence incrementally.

Quickstart validation gates:

1. App opens in the expected initial scene.
2. Feature `build` and `bind_runtime` both execute.
3. Declared actions are present and trigger handlers.
4. Shutdown exits cleanly without leaked subscriptions.

## Architecture and Runtime Model

[Back to Table of Contents](#table-of-contents)

gui_do follows a declarative bootstrap + lifecycle runtime model. Specs describe runtime composition, bootstrap materializes managers and scene/feature wiring, and the frame loop executes deterministic routing/update/draw phases. Features are the architectural boundary. Controls are implementation details under feature ownership.

The runtime model is scene-centric: only active-scene feature runtime executes, and transitions enforce teardown/build boundaries to prevent cross-scene leakage. Event routing normalizes to `GuiEvent` and respects propagation/default flags as hard stops. Persistence and migration are explicit contracts, not hidden side effects.

## Core Workflow: Build, Bind, Route, Update, Draw

[Back to Table of Contents](#table-of-contents)

The framework lifecycle is intentionally phase-separated:

1. Build: create controls, observable models, and static wiring.
2. Bind: connect runtime dependencies, subscriptions, actions, overlays, and task-panel hooks.
3. Route: process normalized events through overlays/focus/window/scene dispatch.
4. Update: execute frame-based logic and scheduler/pipeline work within budget.
5. Draw: render controls and any feature-level custom graphics.

Operational rule: keep each phase focused. Construction belongs in build, runtime attachment in bind, and cleanup in shutdown.
@@    CursorSpec,
@@    SceneSetupSpec,
@@    FeatureSpec,
@@    RuntimeSceneSpec,
@@    ActionSpec,
@@    StaticAccessibilitySpec,
@@)
@@
@@
@@class MinimalHost:
@@    def __init__(self) -> None:
@@        self.config = HostApplicationConfig(
@@            display_size=(1280, 720),
@@            window_title="gui_do quickstart",
@@            fonts={"default": {"system": "arial", "size": 14}},
@@            font_role_specs=(
@@                {"body": {"size": 14, "font": "default"}},
@@            ),
@@            cursors=(
@@                CursorSpec("normal", "demo_features/data/cursors/cursor.png", (1, 1)),
@@            ),
@@            scene_specs=(
@@                SceneSetupSpec(name="main", pretty_name="Main", make_initial=True),
@@            ),
@@            feature_specs=(
@@                FeatureSpec("counter_feature", lambda: CounterFeature()),
@@            ),
@@            window_specs=(),
@@            runtime_scene_specs=(
@@                RuntimeSceneSpec(scene_name="main", bind_escape_to_exit=True, prewarm=False),
@@            ),
@@            action_specs=(
@@                ActionSpec(action_id="exit", label="Exit", kind="exit", category="File"),
@@            ),
@@            static_accessibility_specs=(
@@                StaticAccessibilitySpec("counter_label", "label", "Counter value"),
@@            ),
@@            initial_scene_name="main",
@@            telemetry=TelemetryConfig(enabled=False),
@@            target_fps=120,
@@        )
@@```
@@
@@Required fields: `display_size`, `window_title`, `fonts`, `font_role_specs`, `cursors`, `scene_specs`, `feature_specs`, `window_specs`, `runtime_scene_specs`, `action_specs`, `static_accessibility_specs`, and `initial_scene_name`. Start with a minimal config; add complexity only after the baseline runs.
@@
@@### Step 3: Add a Feature with Observable State
@@
@@[Back to Table of Contents](#table-of-contents)
@@
@@```python
@@from pygame import Rect
@@from gui_do import Feature, ObservableValue, LabelControl
@@
@@
@@class CounterFeature(Feature):
@@    HOST_REQUIREMENTS = {
@@        "build": ("app",),
@@        "bind_runtime": (),
@@        "shutdown_runtime": (),
@@    }
@@
@@    def __init__(self) -> None:
@@        super().__init__("counter_feature", scene_name="main")
@@        self.count = ObservableValue(0)
@@        self.counter_label = None
@@        self._unsubscribe_count = None
@@
@@    def build(self, host) -> None:
@@        self.counter_label = host.app.add(
@@            LabelControl("counter_label", Rect(24, 24, 320, 36), text="Count: 0"),
@@            scene_name="main",
@@        )
@@
@@    def bind_runtime(self, host) -> None:
@@        def _on_count_changed(value):
@@            self.counter_label.text = f"Count: {value}"
@@
@@        self._unsubscribe_count = self.count.subscribe(_on_count_changed)
@@
@@    def shutdown_runtime(self, host) -> None:
@@        if callable(self._unsubscribe_count):
@@            self._unsubscribe_count()
@@            self._unsubscribe_count = None
@@```
@@
@@Key pattern: create controls in `build`, attach subscriptions in `bind_runtime`, dispose subscriptions in `shutdown_runtime`.
@@
@@### Step 4: Add Actions and Runtime Scene Policy
@@
@@[Back to Table of Contents](#table-of-contents)
@@
@@Actions and runtime scene policies belong in config, not in ad-hoc event branches:
@@
@@```python
@@import pygame
@@from gui_do import ActionSpec, RuntimeSceneSpec
@@
@@
@@action_specs = (
@@    ActionSpec(action_id="exit", label="Exit", kind="exit", category="File", key=pygame.K_ESCAPE),
@@)
@@
@@runtime_scene_specs = (
@@    RuntimeSceneSpec(scene_name="main", bind_escape_to_exit=True, prewarm=True),
@@)
@@```
@@
@@### Step 5: Run Loop
@@
@@[Back to Table of Contents](#table-of-contents)
@@
@@```python
@@from gui_do import bootstrap_host_application
@@
@@
@@class MinimalHost:
@@    def __init__(self) -> None:
@@        self.config = ...
@@
@@    def run(self) -> int:
@@        bootstrap_host_application(self, self.config)
@@        return self.app.run_entrypoint(target_fps=120)
@@```
@@
@@This pattern mirrors demo assembly: construct config first, bootstrap once, then hand control to the runtime loop.
@@
@@### Guided Build Track (Beginner)
@@
@@[Back to Table of Contents](#table-of-contents)
@@
@@Progress through these milestones to build confidence:
@@
@@**Milestone A:** app boots to one scene without startup exceptions.
@@**Milestone B:** one feature builds one visible control.
@@**Milestone C:** one observable updates one control through subscription.
@@**Milestone D:** one action and one hotkey trigger expected behavior.
@@**Milestone E:** one overlay and one toast route without leaking pointer/keyboard input to underlying controls.
@@**Milestone F:** workspace save/load roundtrip succeeds.
@@
@@Beginner confidence checklist:
@@- You can explain where `build` ends and `bind_runtime` begins.
@@- You can add/remove one feature by editing specs only.
@@- You can trace one keypress from input normalization to action execution.
@@
@@### Quickstart Failure Modes
@@
@@[Back to Table of Contents](#table-of-contents)
@@
@@- **Feature never appears**: verify `feature_specs` entries and scene-name alignment with configured scene setup.
@@- **Hotkey does nothing**: verify action registration and the key-binding scope path used by your runtime wiring.
@@- **Overlay blocks unexpected keys**: inspect overlay dismissal and key-consumption policies (including unhandled-key consumption semantics).
@@- **State updates but UI does not**: verify subscription is attached in `bind_runtime` and not disposed too early.
@@
@@## Architecture and Runtime Model
@@
@@[Back to Table of Contents](#table-of-contents)
@@
@@### Boundary Model: Framework vs Consumer
@@
@@[Back to Table of Contents](#table-of-contents)
@@
@@The architecture boundary is strict and intentional by design. `gui_do/` is the reusable framework layer: runtime loop, event model, controls, layout engines, state and persistence systems, and orchestration helpers. `demo_features/` and `gui_do_demo.py` are consumer integration code that exercise framework capabilities but do not define framework contracts.
@@
@@The hard rule is one-directional dependency flow: framework code must not import from demo packages. Consumer entrypoints should import from the `gui_do` root surface rather than from internal `gui_do.*` submodules. This keeps the package distributable, preserves public-surface discipline, and prevents demos from silently becoming framework dependencies. Boundary compliance is enforced by contract tests in `tests/test_boundary_contracts.py`.
@@
@@### Tiered Public API Model
@@
@@[Back to Table of Contents](#table-of-contents)
@@
@@gui_do exports are organized by tiers in `gui_do/__init__.py` to indicate recommended abstraction order. **Tier 1** is the preferred entrypoint for all new applications: feature lifecycle types, declarative runtime specs, and bootstrap/build helpers. A developer new to gui_do should become comfortable with Tier 1 APIs before exploring lower tiers.
@@
@@**Tier 2-7** covers core runtime systems: application and scene management, reactive state and observables, events/actions/focus/input routing, scheduling/animation, theme/fonts, and telemetry. These tiers implement the systems that Tier 1 apis use; they are stable and should be used whenever needed.
@@
@@**Tier 8+** expands into specialized systems: layout families (constraint, flex, grid, dock, flow, snap, viewport), overlays and modal managers (dialog, toast, tooltip, context menu, command palette), forms and validation, persistence and state machines, all control types (primary, extended, and chrome), graphics and rendering, audio integration, introspection and diagnostics, and advanced operational helpers.
@@
@@Tier numbers are not merely organizational. They are guidance. If two tiers can solve a problem, choose the lower-numbered tier first because it is generally more declarative, stable, and composable. Reach for higher tiers only when you need explicit low-level control or when your application's requirements justify the added complexity.
@@
@@### Runtime Guarantees
@@
@@[Back to Table of Contents](#table-of-contents)
@@
@@The runtime contract makes explicit guarantees that remain true under load and churn. **Canonical `GuiEvent` normalization**: all raw platform input is normalized to `GuiEvent` before any app-level code sees it. **Scene-isolated update execution**: runtime work for a given scene executes only when that scene is active. **Deterministic window-focus ordering**: window focus candidates are sorted by `control_id`, guaranteeing a stable tab order. **Scheduler dispatch budget clamping**: message dispatch work is clamped to a contract: `fraction=0.12` of dt milliseconds, with `floor=0.5 ms` and `ceiling=4.0 ms`. This keeps dispatch work bounded under long frames while preserving progress under short frames. **Resilient workspace restore**: missing settings keys are skipped during restore rather than treated as fatal, and restore reports include detailed information about what was restored, skipped, and missing.
@@
@@### Event Pipeline
@@
@@[Back to Table of Contents](#table-of-contents)
@@
@@`GuiApplication.process_event` follows a deterministic routing pipeline that ensures events reach the correct handlers in a predictable order. (1) Normalize raw input into `GuiEvent` via the event manager. (2) Handle quit events early before other processing. (3) Update shared input snapshot/state. (4) Update logical pointer state, including lock-point/lock-rect behavior. (5) Logicalize pointer events while preserving raw coordinates. (6) Route toasts and overlays with priority before scene fallthrough. (7) Route keyboard events through keyboard manager and screen-handler policy. (8) Route direct-feature handlers, feature handlers, scene dispatch, then fallthrough handlers. (9) Respect `propagation_stopped` and `default_prevented` as hard-stop signals at each stage. This ordering is why pointer focus, overlay dismissal, and scene dispatch behavior remain predictable under mixed input loads.
@@
@@### Known Non-Goals
@@
@@[Back to Table of Contents](#table-of-contents)
@@
@@- OS-native widget parity across all platforms.
@@- Replacing domain/business architecture decisions for application logic.
@@- Treating internal infrastructure tiers as beginner entry points.
@@- Guaranteeing star-import behavior as a public API compatibility contract.
@@
@@## Core Workflow: Build, Bind, Route, Update, Draw
@@
@@[Back to Table of Contents](#table-of-contents)
@@
@@The five-phase workflow is the operational heart of gui_do. It is not just a naming convention; it is the runtime discipline that keeps feature composition deterministic and maintainable. If teams keep responsibilities inside their intended phase boundaries, cross-feature integration stays legible and maintenance costs remain low.
@@
@@### Phase Reference
@@
@@[Back to Table of Contents](#table-of-contents)
@@
@@**Build phase**: Instantiate controls, initialize local observables, and establish static scene structure. Invariant: do not wire runtime subscriptions or host-dependent cross-feature bindings here.
@@
@@**Bind_runtime phase**: Connect host-dependent wiring, action and key paths, observable subscriptions, and cross-feature references. Invariant: sibling features are already built and control instances exist, so reactive bindings are safe.
@@
@@**Route phase**: Process messages and incoming events through declared handler maps and routing policies. This includes feature-level event handling and message-drain patterns for routed/logic features.
@@
@@**Update phase**: Advance per-frame state and scheduled workloads. Regular `Feature` instances use `on_update(host, dt_seconds)`, while `DirectFeature` instances can run `on_direct_update(host, dt_seconds)` for frame-delta-sensitive logic.
@@
@@**Draw phase**: Render custom visuals not represented by standard control composition. For control-tree-driven UI this is often minimal, but direct rendering hooks remain available when required.
@@
@@### Message and Logic Coordination
@@
@@[Back to Table of Contents](#table-of-contents)
@@
@@`FeatureMessage` enables feature-to-feature communication without hard references. A sender publishes structured payloads (`sender`, `target`, `payload`) to a target feature, and recipients handle messages through queue-drain hooks. `LogicFeature` is commonly used as a coordination hub because it cleanly separates domain workflows from visual presentation concerns.
@@
@@Use observables when consumers need continuous reactive state and message dispatch when communication is discrete, command-like, or topic-driven. In practice, many systems use both: messages trigger workflow transitions, observables expose resulting state for UI binding.
@@
@@### When to Use Routed Runtime Specs
@@
@@[Back to Table of Contents](#table-of-contents)
@@
@@`RoutedRuntimeSpec` and `RoutedFeatureLifecycleSpec` reduce repetitive wiring when a feature needs multiple runtime attachments: grouped action hotkeys, shortcut overlays tied to lifecycle, task-panel focus toggles, and event subscriptions with automatic teardown behavior.
@@
@@`bind_routed_feature_lifecycle` centralizes runtime attachment from a declarative lifecycle spec, while `shutdown_routed_feature_lifecycle` unwinds those attachments consistently. Use this path when manual per-feature bind/shutdown code starts duplicating the same routing and cleanup patterns across features.

*This section is reserved. Run the corresponding pipeline sub-prompt to expand it.*

## Main Systems Reference

[Back to Table of Contents](#table-of-contents)

### 8.1 Application Bootstrap and Host Configuration

[Back to Table of Contents](#table-of-contents)

Application bootstrap is the deterministic handoff from declarative specification to a fully wired runtime host. The combination of `HostApplicationConfig` and `bootstrap_host_application` exists so application startup is expressed as data, then realized in one controlled pass. Instead of constructing managers in ad hoc order and mutating globals over time, you declare scenes, features, actions, window bindings, task-panel behavior, and diagnostics at config time and let bootstrap enforce assembly order.

The most useful mental model is: the host starts as a plain Python object, and bootstrap attaches the runtime graph to it. After `bootstrap_host_application(host, config)` returns, `host.app` is a live `GuiApplication`, declared feature attributes are present, scene and window presentation models are registered, and declared actions, key bindings, and overlays are configured.

Primary public APIs and key types in this area include `HostApplicationConfig`, `HostApplicationBindingSpec`, `SceneBundleBindingSpec`, `FeatureWindowBundleBindingSpec`, `WindowSpec`, `AnchoredWindowSpec`, `RuntimeSceneSpec`, `SceneSetupSpec`, `FeatureSpec`, `ActionSpec`, `ActionHotkeySpec`, `ControlKeyBindingSpec`, `SceneRootSpec`, `SceneTaskPanelSpec`, `TaskPanelButtonSpec`, `TaskPanelWindowToggleGroupSpec`, `TaskPanelFocusToggleSpec`, `ShortcutOverlaySpec`, `PaletteBindingSpec`, `CursorSpec`, `CursorBindingSpec`, `FontRoleBindingSpec`, `TabbedPresenterSpec`, `TabBuilderSpec`, `NotificationSpec`, `build_host_application_config`, and `bootstrap_host_application`.

Typical usage flow:

1. Define a host class with runtime-facing methods (for actions, shutdown hooks, optional helpers).
2. Build a `HostApplicationConfig` directly, or create a `HostApplicationBindingSpec` and pass it to `build_host_application_config`.
3. Declare scenes, features, and actions up front with `FeatureSpec`, `RuntimeSceneSpec`, and `ActionSpec`.
4. Optionally declare window/task-panel bundles with `FeatureWindowBundleBindingSpec` and scene bundles with `SceneBundleBindingSpec`.
5. Call `bootstrap_host_application(host, config)` once, then enter the loop with `host.app.run_entrypoint(...)`.

Minimal example:

```python
from gui_do import (
  ActionSpec,
  Feature,
  FeatureSpec,
  HostApplicationConfig,
  RuntimeSceneSpec,
  bootstrap_host_application,
)


class CounterFeature(Feature):
  def build(self, host):
    pass


class Host:
  def on_exit(self, _ctx=None):
    self.app.stop()


host = Host()
config = HostApplicationConfig(
  display_size=(960, 600),
  title="gui_do app",
  initial_scene_name="main",
  feature_specs=[FeatureSpec(attr_name="counter_feature", factory=CounterFeature)],
  runtime_scene_specs=[RuntimeSceneSpec(scene_name="main", bind_escape_to_exit=True)],
  action_specs=[ActionSpec(action_id="app.exit", label="Exit", kind="exit")],
)
bootstrap_host_application(host, config)
host.app.run_entrypoint()
```

Advanced pattern:

Use a composed binding graph when the app has multiple scenes and many windows. A `HostApplicationBindingSpec` can aggregate multiple `SceneBundleBindingSpec` values, each with `FeatureWindowBundleBindingSpec` entries. This allows one call to `build_host_application_config` to resolve scene roots, actions, task-panel groups, window toggles, and presenter tabs in a consistent order before bootstrap executes.

Common mistakes and anti-patterns:

1. Mutating host runtime attributes after bootstrap in ways that bypass declared specs.
2. Declaring feature scene names that do not match any `SceneSetupSpec` or runtime scene declaration.
3. Omitting `initial_scene_name` while depending on scene-scoped startup behavior.
4. Registering cross-scene window toggles without matching `WindowToggleBindingSpec` or scene bundle wiring.

Cross-links: 8.2 feature lifecycle, 8.3 routing/action dispatch, 8.9 scene and window presentation, 8.11 workspace persistence.

[Back to Table of Contents](#table-of-contents)

### 8.2 Feature Lifecycle and Feature Types

[Back to Table of Contents](#table-of-contents)

Features are the primary behavioral unit in gui_do. Lifecycle structure exists to keep construction, runtime wiring, per-frame updates, event handling, and teardown deterministic and testable. Instead of scattering logic across callbacks, a feature implements explicit phases and can declare requirements about host capabilities.

The lifecycle mental model is phase-separated responsibilities:

1. `build(host)`: create controls, models, and local state; avoid runtime subscriptions that assume sibling features are already wired.
2. `bind_runtime(host)`: connect actions, events, subscriptions, companion links, and host-managed resources.
3. `handle_event(host, event)`: process routed `GuiEvent` input for this feature.
4. `on_update(host, dt_seconds)`: advance frame-based behavior and scheduler-coordinated work.
5. `draw(host, screen)`: optional custom rendering beyond control-tree drawing.
6. `shutdown_runtime(host)`: release subscriptions, timers, and runtime attachments.

Primary public APIs and key types include `Feature`, `DirectFeature`, `LogicFeature`, `RoutedFeature`, `FeatureMessage`, `FeatureManager`, `RoutedRuntimeSpec`, `RoutedFeatureLifecycleSpec`, `bind_routed_feature_lifecycle`, `shutdown_routed_feature_lifecycle`, and `register_routed_feature_companions`.

`HOST_REQUIREMENTS` is a dictionary protocol used by lifecycle-aware features to declare host dependencies by phase. Keys are phase names and values are tuples of attribute names the host must expose. Startup validation catches missing requirements early instead of failing deep in frame loops.

Typical usage flow:

1. Choose the minimal feature type (`Feature` for general UI behavior, `LogicFeature` for logic-centric coordination, `DirectFeature` when direct update/draw emphasis is needed, `RoutedFeature` for routed-runtime composition).
2. Declare `HOST_REQUIREMENTS` for each phase that needs host members.
3. Implement `build` for control/model construction.
4. Implement `bind_runtime` for subscriptions, actions, and routed lifecycle attachments.
5. Register via `FeatureSpec` in host config.
6. Dispose everything in `shutdown_runtime`.

Minimal example:

```python
from pygame import Rect
from gui_do import Feature, LabelControl, ObservableValue, PanelControl


class StatusFeature(Feature):
  HOST_REQUIREMENTS = {
    "build": ("app",),
    "bind_runtime": ("app",),
  }

  def __init__(self):
    self.status = ObservableValue("Ready")
    self._status_sub = None

  def build(self, host):
    self.root = host.app.add(PanelControl("status_root", Rect(0, 0, 320, 96)), scene_name="main")
    self.label = self.root.add(LabelControl("status_label", Rect(8, 8, 280, 24), ""))

  def bind_runtime(self, host):
    self._status_sub = self.status.subscribe(lambda text: setattr(self.label, "text", text))
    self.label.text = self.status.value

  def shutdown_runtime(self, host):
    if self._status_sub is not None:
      self._status_sub.dispose()
      self._status_sub = None
```

Advanced pattern:

Split logic and presentation: a `LogicFeature` owns core state and emits `FeatureMessage` updates while a companion `RoutedFeature` renders controls and reacts to both messages and observables. Use `register_routed_feature_companions` plus `bind_routed_feature_lifecycle` to keep wiring centralized and teardown symmetric.

Common mistakes and anti-patterns:

1. Subscribing in `build` before sibling/presenter controls are guaranteed available.
2. Putting expensive rendering logic into non-direct paths when it should live in dedicated draw/update hooks.
3. Forgetting `shutdown_routed_feature_lifecycle` when using routed lifecycle specs.
4. Treating feature instances as global service containers instead of scene-scoped behavioral units.

Cross-links: 8.1 bootstrap, 8.3 events and actions, 8.4 reactive state, 8.10 scheduling.

[Back to Table of Contents](#table-of-contents)

### 8.3 Events, Actions, Input Mapping, and Routing

[Back to Table of Contents](#table-of-contents)

The event and action stack turns raw input into deterministic, policy-driven behavior. gui_do normalizes platform events into `GuiEvent`, routes through overlays/focus/window/scene layers, and dispatches command semantics through action registries and input maps. This separation exists so input handling remains testable, scene-aware, and composable.

Mental model: raw `pygame` event stream enters the runtime, gets normalized into `GuiEvent`, then routed in stable order. Routed handlers can stop propagation or prevent defaults via hard-stop flags. Action handling sits beside this route: `InputMap` and chord helpers map key patterns to `ActionManager` actions, then action middleware and registry handlers execute domain behavior.

Primary APIs include `GuiEvent`, `EventType`, `EventPhase`, `EventManager`, `EventBus`, `Signal`, `SignalConnection`, `GestureRecognizer`, `EventRecorder`, `EventPlayback`, `RecordedEvent`, `InputSnapshot`, `ActionManager`, `ActionContext`, `ActionMiddleware`, `ActionDescriptor`, `ActionRegistry`, `InputMap`, `InputBinding`, `KeyChordManager`, `KeyChord`, `ChordStep`, `InteractionPhase`, `InteractionContext`, `InteractionTransition`, and `InteractionStateMachine`.

For declarative wiring at config time, use `ActionSpec`, `ActionHotkeySpec`, `ControlKeyBindingSpec`, and `EventSubscriptionSpec`.

`GuiEvent` canonical fields are: `kind`, `type`, `key`, `pos`, `rel`, `raw_pos`, `raw_rel`, `button`, `wheel_x`, `wheel_y`, `mod`, `text`, `control_id`, `group`, `window`, `task_panel`, `task_id`, `error`, `source_event`, `phase`, `propagation_stopped`, and `default_prevented`.

Current `EventType` values are: `PASS`, `QUIT`, `KEY_DOWN`, `KEY_UP`, `MOUSE_BUTTON_DOWN`, `MOUSE_BUTTON_UP`, `MOUSE_MOTION`, `MOUSE_WHEEL`, `TEXT_INPUT`, and `TEXT_EDITING`.

Typical usage flow:

1. Declare named actions using `ActionSpec`.
2. Register hotkeys/chords with `ActionHotkeySpec` and optionally `KeyChordManager`.
3. Add feature/runtime subscriptions via `EventSubscriptionSpec` or routed runtime setup.
4. Handle domain behavior in action handlers, not in scattered key branches.
5. Use propagation/default flags when custom routing layers are introduced.

Minimal example:

```python
from gui_do import ActionSpec, HostApplicationConfig

config = HostApplicationConfig(
  title="actions-demo",
  display_size=(900, 560),
  initial_scene_name="main",
  action_specs=[
    ActionSpec(action_id="app.exit", label="Exit", kind="exit"),
    ActionSpec(action_id="help.shortcuts", label="Shortcuts", kind="palette_open"),
  ],
)
```

Advanced pattern:

Use `InteractionStateMachine` to model press-drag-release gestures with explicit guarded transitions, and record end-to-end behavior with `EventRecorder`/`EventPlayback` so regressions can be replayed deterministically from captured traces.

Common mistakes and anti-patterns:

1. Handling raw `pygame` events directly in features and bypassing `GuiEvent` normalization.
2. Assuming action handlers are always global even when registration is scene or window scoped.
3. Ignoring `propagation_stopped` and `default_prevented` when writing custom dispatch adapters.
4. Registering overlapping key paths without explicit precedence policy.

Cross-links: 8.2 feature lifecycle, 8.7 focus/accessibility, 8.8 overlays, 8.9 scene/window presentation.

[Back to Table of Contents](#table-of-contents)

### 8.4 State and Observables

[Back to Table of Contents](#table-of-contents)

State and observable primitives provide the reactive contract between logic and UI. Instead of imperative cross-feature mutation, a feature writes to state and subscribers react. This keeps feature boundaries clean and makes runtime updates deterministic.

Mental model: `ObservableValue`, `ObservableList`, and `ObservableDict` are publish/subscribe primitives. Features own state and expose it as observables. Controls and companion features subscribe during `bind_runtime` and dispose in teardown. For derived state and transactional updates, use computed and store-level APIs.

Primary APIs include `ObservableValue`, `PresentationModel`, `ComputedValue`, `InvalidationTracker`, `ChangeKind`, `CollectionChange`, `ObservableList`, `ObservableDict`, `CollectionViewQuery`, `CollectionView`, `Binding`, `BindingGroup`, `ObservableStream`, `SelectionModel`, `SelectionMode`, `AppStateStore`, `StateSelector`, and `StateTransaction`.

`ObservableValue` exposes a `.value` property and `.subscribe(callback)` for change notifications. `ObservableList` and `ObservableDict` emit `CollectionChange` notifications that include change kind and affected keys or indices.

Typical usage flow:

1. Create observables in feature construction or `build`.
2. Create controls in `build`.
3. Subscribe in `bind_runtime` and apply initial values immediately.
4. Dispose subscriptions in `shutdown_runtime`.
5. Use `StateSelector` for derived slices when multiple features share an `AppStateStore`.

Minimal example:

```python
self.count = ObservableValue(0)
# in bind_runtime:
self._sub = self.count.subscribe(lambda v: setattr(self.label, "text", str(v)))
# in shutdown_runtime:
self._sub.dispose()
```

Advanced pattern:

Combine `AppStateStore` with `StateSelector` for centralized shared state and use `StateTransaction` for atomic multi-field updates. Pair this with `CollectionView`/`CollectionViewQuery` to maintain sorted and filtered views over `ObservableList` while preserving reactive updates.

Common mistakes and anti-patterns:

1. Polling `.value` every frame in `on_update` instead of subscribing.
2. Subscribing before controls exist or forgetting disposal on shutdown.
3. Using plain lists and dicts for cross-feature state where observable collections are required.
4. Recomputing expensive derived values manually instead of using `ComputedValue` or selectors.

Cross-links: 8.2 feature lifecycle, 8.5 controls composition, 8.11 persistence, 8.14 data/dataflow.

[Back to Table of Contents](#table-of-contents)

### 8.5 Controls and Control Composition

[Back to Table of Contents](#table-of-contents)

Controls are the reusable UI primitives that features assemble into behavior-specific trees. This abstraction exists so layout, hit testing, focus, and rendering are consistent across the framework without each feature re-implementing those concerns.

Mental model: a feature owns a root container and composes a subtree beneath it. The tree is the operational unit for layout and event targeting. Cross-feature communication should not happen through direct control references; use observables or messages instead.

Primary controls in Tier 12 are `PanelControl`, `LabelControl`, `ButtonControl`, `ToggleControl`, `SliderControl`, `ScrollbarControl`, `CanvasControl`, `CanvasEventPacket`, `CanvasViewport`, `FrameControl`, `ImageControl`, `ArrowBoxControl`, `ButtonGroupControl`, `TabControl`, `TabItem`, and `DockWorkspacePanel`.

Extended controls in Tier 13 are `TextInputControl`, `TextAreaControl`, `RichLabelControl`, `DropdownControl`, `DropdownOption`, `ListViewControl`, `ListItem`, `OverlayPanelControl`, `DataGridControl`, `GridColumn`, `GridRow`, `TreeControl`, `TreeNode`, `SplitterControl`, `SpinnerControl`, `RangeSliderControl`, `ColorPickerControl`, `ScrollViewControl`, `ProgressBarControl`, `AnimatedImageControl`, `ErrorBoundary`, `WindowControl`, `TaskPanelControl`, `WindowPresenter`, `MenuBarControl`, `MenuEntry`, `SceneMenuStripControl`, `NotificationPanelControl`, `PropertyInspectorPanel`, `ToolbarControl`, `ToolbarItem`, `StatusBarControl`, `StatusSlot`, `ExpanderControl`, `DatePickerControl`, `TimePickerControl`, `BreadcrumbControl`, `BreadcrumbItem`, `SplitButtonControl`, `SplitButtonOption`, and `ChipInputControl`.

Declarative helpers related to control composition include `ControlDefinition` and `build_specs_from_column_section`.

Typical usage flow:

1. In `build`, create a root `PanelControl` for the feature.
2. Add child controls and keep references only where runtime updates are needed.
3. Bind actions/subscriptions in `bind_runtime`, not in constructors.
4. Keep control state as a projection of observable state.

Minimal example:

```python
from pygame import Rect
from gui_do import ButtonControl, LabelControl, PanelControl


def build(self, host):
  self.root = host.app.add(PanelControl("my_root", Rect(0, 0, 400, 300)), scene_name="main")
  self.label = self.root.add(LabelControl("status", Rect(8, 8, 240, 24), "Ready"))
  self.root.add(ButtonControl("go", Rect(8, 40, 100, 28), "Go", on_click=self._on_go))
```

Advanced pattern:

Use the presenter split for window-level composition. A `WindowPresenter` subclass owns window-internal tree construction while the feature owns lifecycle and routing. For tabbed windows, pair `TabbedPresenterSpec` with `TabBuilderSpec` and route active-tab updates through `ActiveTabUpdateRouter`.

Common mistakes and anti-patterns:

1. Directly mutating sibling feature controls instead of publishing state.
2. Using controls as source-of-truth domain state.
3. Constructing controls in `on_update`.
4. Skipping `ErrorBoundary` around unstable experimental subtrees.

Cross-links: 8.2 feature lifecycle, 8.6 layout systems, 8.7 focus/accessibility, 8.9 scene/window presentation.

[Back to Table of Contents](#table-of-contents)

### 8.6 Layout Systems

[Back to Table of Contents](#table-of-contents)

Layout systems exist to make spatial behavior robust under resize, density changes, and dynamic content. Declarative layout policies reduce brittle pixel arithmetic and centralize geometry rules in composable engines.

Mental model: pick one layout owner per container. The app-level layout pass resolves control bounds before draw; controls should consume assigned bounds rather than continually recomputing parent-relative positions.

Primary APIs in this area include `LayoutAxis`, `LayoutManager`, `WindowTilingManager`, `ConstraintLayout`, `AnchorConstraint`, `DockPane`, `DockTabs`, `DockSplit`, `DockWorkspace`, `FlexLayout`, `FlexItem`, `FlexDirection`, `FlexAlign`, `FlexJustify`, `GridLayout`, `GridTrack`, `GridPlacement`, `CellCaretLayout`, `CellCaretState`, `LayoutAnimator`, `LayoutPass`, `MeasureContext`, `ArrangeContext`, `LayoutRoot`, `ResponsiveLayout`, `Breakpoint`, `SnapGrid`, `AlignmentGuide`, `SnapComposer`, `SnapTarget`, `FlowLayout`, `FlowItem`, `Viewport`, `ConstraintAttr`, `LayoutConstraint`, `ConstraintSet`, `ConstraintLayoutEngine`, `AdaptivePolicy`, `resolve_adaptive_policy`, `MeasureMode`, `MeasurePolicy`, `VirtualizedWindow`, `RecyclePool`, and `VirtualizationCore`.

Typical usage flow:

1. Select container strategy (`FlexLayout`, `GridLayout`, `FlowLayout`, constraint family, docking, or virtualization).
2. Declare child placement metadata (`FlexItem`, `GridPlacement`, constraints, or virtual measure policy).
3. Resolve layout during standard passes, then draw.
4. Introduce breakpoint/adaptive policies only where responsiveness is required.

Minimal example:

```python
from gui_do import FlexDirection, FlexItem, FlexLayout

layout = FlexLayout(direction=FlexDirection.ROW, gap=8)
layout.add(FlexItem(control=sidebar, grow=0, basis=220))
layout.add(FlexItem(control=content, grow=1, basis=0))
```

Advanced pattern:

Use `ConstraintLayoutEngine` with `AdaptivePolicy` to swap constraint sets at breakpoints, and pair with `WindowTilingManager` for desktop-like pane behavior. For very large lists/grids, integrate `VirtualizationCore` and `RecyclePool` to keep measure/arrange cost proportional to visible items.

Common mistakes and anti-patterns:

1. Mixing multiple independent layout engines in one container without a clear owner.
2. Hardcoding dimensions where `Breakpoint` or adaptive constraints should drive behavior.
3. Running manual layout before controls are attached to the active tree.
4. Rendering huge collections without virtualization.

Cross-links: 8.5 controls, 8.9 window presentation, 8.14 dataflow and virtualization, 8.15 graphics.

[Back to Table of Contents](#table-of-contents)

### 8.7 Focus and Accessibility

[Back to Table of Contents](#table-of-contents)

Focus and accessibility systems keep keyboard interaction coherent and expose semantic structure for assistive tooling and automated diagnostics. They exist so interaction behavior remains predictable even in complex, multi-window scenes.

Mental model: focus is an ordered runtime graph and accessibility is a semantic mirror graph. `FocusManager` and related scope/ring managers decide who receives keyboard input. Accessibility APIs define what that control means (`role`, labels, descriptions, live-region announcements).

Focus-related APIs include `FocusManager`, `FocusScope`, `FocusScopeManager`, `WindowFocusManager`, and `FocusRing`.

Accessibility APIs include `AccessibilityRole`, `LivePoliteness`, `AccessibilityNode`, `AccessibilityTree`, `AccessibilityAnnouncement`, and `AccessibilityBus`.

Specification-level helpers include `StaticAccessibilitySpec`, `AccessibilitySequenceSpec`, and `TaskPanelFocusToggleSpec`.

Typical usage flow:

1. Build focusable controls and register stable traversal order.
2. Define accessibility annotations with static specs and/or runtime nodes.
3. For modal or windowed surfaces, constrain traversal with `FocusScope` and window focus routing.
4. For task-panel managed window toggles, use `TaskPanelFocusToggleSpec` to auto-exclude hidden window controls.

Minimal example:

```python
from gui_do import AccessibilityNode, AccessibilityRole, AccessibilityTree

tree = AccessibilityTree()
node = AccessibilityNode(role=AccessibilityRole.BUTTON, name="Submit")
tree.root.add_child(node)
```

Advanced pattern:

Use `AccessibilitySequenceSpec` for explicit scene-level reading/traversal order and `FocusScope` to lock focus within modal overlays. Combine with task-panel toggle specs so hidden windows leave the focus ring and rejoin correctly on restore.

Common mistakes and anti-patterns:

1. Leaving hidden or disabled controls in the focus ring.
2. Omitting semantic role data for custom canvas-driven widgets.
3. Creating accessibility nodes before tree initialization.
4. Assuming window visibility and focus inclusion stay synchronized without explicit policy.

Cross-links: 8.3 event routing, 8.5 controls, 8.8 overlays/modal behavior, 8.9 window/task-panel presentation.

[Back to Table of Contents](#table-of-contents)

### 8.8 Overlays, Dialogs, Notifications, and Command Surfaces

[Back to Table of Contents](#table-of-contents)

Overlay systems handle transient and modal UI layers above the main control tree. They exist to enforce correct routing precedence, dismissal contracts, and visual stacking for dialogs, menus, command palettes, tooltips, and notifications.

Mental model: overlays process events before underlying scene controls. If an overlay consumes an input, the base tree should not see it. Different overlay families have intentionally different lifecycles and dismissal rules.

Primary APIs include `OverlayManager`, `OverlayHandle`, `Alignment`, `PlacementResult`, `PopupPlacement`, `Side`, `compute_popup_rect`, `DialogManager`, `DialogHandle`, `ToastManager`, `ToastHandle`, `ToastSeverity`, `ContextMenuManager`, `ContextMenuItem`, `ContextMenuHandle`, `CommandPaletteManager`, `CommandEntry`, `CommandPaletteHandle`, `TooltipManager`, `TooltipHandle`, `MenuBarManager`, `FileDialogManager`, `FileDialogOptions`, `FileDialogHandle`, `NotificationCenter`, `NotificationRecord`, `ResizeManager`, `CursorManager`, `CursorHandle`, `CursorShape`, `DragDropManager`, `DragPayload`, `ClipboardManager`, `TransferData`, `TransferManager`, `ShortcutHelpOverlay`, `ShortcutSection`, and `ShortcutEntry`.

Config-level integration points include `ShortcutOverlaySpec` and `NotificationSpec`.

Typical usage flow:

1. Instantiate and attach overlay managers through bootstrap/runtime setup.
2. Show overlays through manager APIs and keep returned handles for lifecycle checks.
3. Ensure every overlay has an explicit dismissal path.
4. Use scene-aware command palette and shortcut overlay wiring via runtime specs.

Minimal example:

```python
host.toasts.show("File saved", severity=ToastSeverity.SUCCESS)
```

Advanced pattern:

Build a discoverable keyboard surface by combining `ShortcutOverlaySpec`, `create_shortcut_help_overlay`, and scene action declarations, then populate a `CommandPaletteManager` dynamically from action descriptors and custom entries for scene/window commands.

Common mistakes and anti-patterns:

1. Showing overlays without a dismissal contract.
2. Expecting toast clicks to pass through to underlying controls.
3. Updating a dismissed overlay through stale handles.
4. Forgetting modal focus capture when dialog overlays are active.

Cross-links: 8.3 events/actions, 8.7 focus/accessibility, 8.9 scene/window model, 8.13 forms/dialog workflows.

[Back to Table of Contents](#table-of-contents)

### 8.9 Scene, Window, and Task-Panel Presentation Models

[Back to Table of Contents](#table-of-contents)

Scene and window presentation models coordinate what is visible, where interaction is routed, and how workspace chrome reflects runtime state. This system exists so large applications can expose many working surfaces without drifting into ad hoc visibility and focus logic.

Mental model: scenes are top-level interaction contexts; windows are scoped work surfaces inside scenes; task panels and scene menu strips are presentation adapters that make scene/window state discoverable and controllable.

Primary APIs in this area include `ScenePresentationModel`, `WindowSpec`, `AnchoredWindowSpec`, `SceneTaskPanelSpec`, `TaskPanelButtonSpec`, `TaskPanelFocusToggleSpec`, `FeatureWindowBundleBindingSpec`, `WindowToggleBindingSpec`, `TabbedPresenterSpec`, `TabBuilderSpec`, `WindowPresenter`, `set_window_visible_state`, `toggle_window_visibility`, `create_anchored_feature_window`, `create_feature_presented_window`, `create_presented_anchored_window`, `create_presented_window_from_spec`, `add_window_scene_menu_strip`, `ensure_scene_task_panel`, `add_task_panel_button`, `add_task_panel_buttons`, `add_task_panel_window_toggle_group`, `add_window_toggle_task_panel_controls`, `add_task_panel_scene_nav_button`, `add_scene_task_panel_items`, `setup_feature_presenter_tabs`, `setup_feature_presenter_tabs_from_window_content`, `create_tab_control_from_specs`, `compute_tabbed_window_layout`, `register_window_tab_builder_specs`, `register_tab_update_handlers`, `ActiveTabUpdateRouter`, and `TabLayoutContext`.

Typical usage flow:

1. Declare scene/runtime specs and window specs in config.
2. Build window content with a `WindowPresenter` subclass.
3. Register window toggles/task-panel bindings and scene menu-strip entries.
4. Use visibility helpers (`set_window_visible_state`/`toggle_window_visibility`) instead of manual state mutation.
5. Keep task-panel button and focus behavior synchronized with `TaskPanelFocusToggleSpec`.

Minimal example:

```python
from gui_do import AnchoredWindowSpec, create_feature_presented_window

spec = AnchoredWindowSpec(
  control_id="inspector_window",
  title="Inspector",
  size=(420, 520),
  anchor="right",
  margin=(16, 16),
)
window = create_feature_presented_window(host, scene_name="main", spec=spec, presenter=self.presenter)
```

Advanced pattern:

Use `FeatureWindowBundleBindingSpec` to declare feature+window bundles, combine `TabbedPresenterSpec`/`TabBuilderSpec` for tabbed windows, and route tab-specific refresh logic through `ActiveTabUpdateRouter` so only active tab content receives expensive update work.

Common mistakes and anti-patterns:

1. Mixing scene scope and window scope when registering actions.
2. Toggling window internals directly instead of presentation helpers.
3. Failing to synchronize task-panel visual state with actual window visibility.
4. Creating windows in `bind_runtime` when other features expect them after `build`.

Cross-links: 8.2 feature lifecycle, 8.5 controls, 8.7 focus/accessibility, 8.8 overlays.

[Back to Table of Contents](#table-of-contents)

### 8.10 Scheduling, Timing, Animation, and Transitions

[Back to Table of Contents](#table-of-contents)

Scheduling and animation systems exist to run time-based work without violating frame budgets. gui_do supports basic timers, tween/transition orchestration, scene timelines, and generator-based cooperative workflows for multi-frame logic.

Mental model: all runtime time work is budgeted per frame. The dispatch budget contract is clamped to fraction `0.12` of frame dt milliseconds, floor `0.5 ms`, and ceiling `4.0 ms`. This keeps background dispatch bounded on slow frames while preventing starvation on fast frames.

Primary APIs include `TaskEvent`, `TaskScheduler`, `Timers`, `TweenManager`, `TweenHandle`, `Easing`, `AnimationSequence`, `AnimationHandle`, `TransitionManager`, `TransitionSpec`, `TransitionEvent`, `AnimationStateMachine`, `AnimationTransitionMode`, `SceneTimeline`, `Debouncer`, `Throttler`, `CooperativeScheduler`, `CoroutineHandle`, `Pause`, `Sleep`, `WaitForEvent`, `WaitForSignal`, `WaitUntil`, `WaitForAll`, and dataflow scheduling helpers `CancellationToken`, `PipelineStage`, `DataflowPipeline`, and `PipelineHandle`.

Typical usage flow:

1. Register timed and animation work in `bind_runtime` or action handlers.
2. Advance animation and scheduler state each frame via the runtime loop.
3. Keep expensive multi-step workflows in cooperative coroutines or pipelines.
4. Cancel stale handles on scene exit and in `shutdown_runtime`.

Minimal example:

```python
# Tween a panel alpha to visible state.
self._fade = host.tweens.to(self.panel, "alpha", 255, duration=0.2)


def workflow():
  yield Sleep(0.5)
  host.toasts.show("Done")


host.scheduler.run(workflow())
```

Advanced pattern:

Use `CooperativeScheduler` with `WaitForSignal` to coordinate multi-step workflows that depend on user interaction, then continue through pipeline stages in `DataflowPipeline` where each generation carries a `CancellationToken` so stale runs terminate immediately when new input arrives.

Common mistakes and anti-patterns:

1. Running unbounded loops in `on_update`.
2. Performing blocking I/O inside cooperative coroutines.
3. Forgetting to cancel tweens/animations on scene shutdown.
4. Profiling idle loops and assuming those metrics reflect real workloads.

Cross-links: 8.2 lifecycle update hooks, 8.14 data pipelines, 8.15 draw systems, 8.16 telemetry.

[Back to Table of Contents](#table-of-contents)

### 8.11 Persistence and Workspace/Session State

[Back to Table of Contents](#table-of-contents)

Persistence systems keep session state portable across runs and resilient across schema evolution. The design goal is robust restore behavior with explicit observability instead of silent failures.

Mental model: workspace state is a structured snapshot. On load, the runtime restores scene targeting, feature states, scene nodes, and settings with skip/missing reporting instead of fatal failure for unknown keys.

Primary APIs include `WorkspaceState`, `WorkspacePersistenceManager`, `DEFAULT_WORKSPACE_STATE_PATH`, `SceneSnapshot`, `NodeSnapshot`, `SettingsRegistry`, `SettingDescriptor`, `CommandHistory`, `Command`, `CommandTransaction`, `UndoContextManager`, `SchemaVersion`, `VersionedSnapshot`, `MigrationStep`, `MigrationRegistry`, `SnapshotMigrator`, `MigrationError`, `make_snapshot`, and `read_version`.

Restore-report fields are `target_scene`, `switched_scene`, `restored_feature_states`, `restored_scene_nodes`, `applied_settings`, `skipped_settings`, and `missing_settings_blocks`.

Typical usage flow:

1. Register settings and state participants at startup.
2. Save workspace snapshots at controlled points.
3. On load, inspect the restore report and handle skipped/missing settings gracefully.
4. Migrate older snapshots before applying restore.

Minimal example:

```python
host.app.save_workspace("workspace.json")
report = host.app.load_workspace("workspace.json")
if report and report.skipped_settings:
  host.toasts.show("Some settings were skipped during restore")
```

Advanced pattern:

Version snapshot payloads with `SchemaVersion`, create data with `make_snapshot`, and route every load through `read_version` and `SnapshotMigrator.migrate(...)`. Register one-way `MigrationStep` transitions in `MigrationRegistry` so upgrades are explicit, testable, and monotonic.

Common mistakes and anti-patterns:

1. Restoring snapshots without checking version metadata.
2. Assuming all settings keys are always present.
3. Reusing `DEFAULT_WORKSPACE_STATE_PATH` for multi-instance app deployments.
4. Treating command history as durable state without explicit serialization boundaries.

Cross-links: 8.1 bootstrap config, 8.2 shutdown lifecycle, 8.10 scheduler safety, 8.16 diagnostics.

[Back to Table of Contents](#table-of-contents)

### 8.12 Theme, Styling, and Visual Systems

[Back to Table of Contents](#table-of-contents)

Theme and styling systems centralize visual policy so controls can remain semantic instead of hardcoded. The goal is to make visual changes compositional: update roles/tokens/themes and let the tree re-render consistently.

Mental model: `ThemeManager` owns active theme selection, `ColorTheme` and `DesignTokens` represent semantic values, `FontRoleRegistry` maps role names to concrete fonts, and `ThemeInvalidationBus` tells cached renderers to flush when visual inputs change.

Primary APIs include `FontManager`, `FontRoleRegistry`, `ColorTheme`, `ThemeManager`, `DesignTokens`, `ScopedTheme`, `ScopedThemeManager`, `ThemeInvalidationBus`, and bootstrap role helpers `setup_standard_font_roles` and `FontRoleBindingSpec`.

Related setup specs in this visual family include `CursorSpec` and `CursorBindingSpec` for cursor-theme alignment.

Typical usage flow:

1. Declare font resources and role bindings in host config.
2. Define one or more `ColorTheme` values and assign active theme through `ThemeManager`.
3. Use role/token lookups in controls and custom draw code.
4. Subscribe caches to `ThemeInvalidationBus` and redraw on theme changes.

Minimal example:

```python
from gui_do import ThemeManager

host.theme_manager = ThemeManager()
host.theme_manager.set_theme("default")
```

Advanced pattern:

Use `ScopedThemeManager` to apply subtree-local overrides (for example, a tool window with different contrast rules) while retaining global role names. Pair with token-driven custom draw paths and invalidation-bus subscriptions for deterministic cache refresh.

Common mistakes and anti-patterns:

1. Hardcoding color literals in feature draw code.
2. Changing themes without invalidating cached surfaces.
3. Registering font roles after controls have already built assumptions around missing roles.
4. Mixing semantic tokens and raw constants in the same rendering path.

Cross-links: 8.1 bootstrap/font setup, 8.5 control rendering, 8.15 graphics surfaces, 8.16 telemetry for visual cost.

[Back to Table of Contents](#table-of-contents)

### 8.13 Text, Input, Forms, and Validation Systems

[Back to Table of Contents](#table-of-contents)

Text, input, form, and validation systems provide a structured path from keystrokes to validated domain data. This layer exists to avoid every feature rebuilding ad hoc form orchestration and error handling.

Mental model: input controls capture raw user edits, form/schema models represent logical field state, and validators enforce constraints. Runtime policy determines when validation runs (`on change`, `on submit`, or hybrid), while async validators protect responsiveness and prevent stale-result corruption.

Primary APIs in this area include `FormModel`, `FormField`, `ValidationRule`, `FieldError`, `FormSchema`, `SchemaField`, `DocumentModel`, `WizardFlow`, `WizardStep`, `WizardHandle`, `ValidationResult`, `Validator`, `RequiredValidator`, `RangeValidator`, `LengthValidator`, `PatternValidator`, `CustomValidator`, `DependentValidator`, `ValidationPipeline`, `AsyncFieldValidator`, `AsyncFormValidator`, `FieldSchema`, `FieldGraphSchema`, `ValidationPolicy`, `SchemaFormRuntime`, `TextFormatter`, `NumericFormatter`, `PatternFormatter`, `FixedPatternFormatter`, `TextFlow`, `TextSpan`, `TextSearcher`, `TextMatch`, `StringTable`, `LocaleRegistry`, and input controls such as `TextInputControl`, `TextAreaControl`, `SpinnerControl`, `DatePickerControl`, `TimePickerControl`, `ColorPickerControl`, and `ChipInputControl`.

Typical usage flow:

1. Define `FormSchema` fields and validation expectations.
2. Convert to `FieldGraphSchema` for dependency-aware visibility/validation.
3. Construct `SchemaFormRuntime` with the selected `ValidationPolicy`.
4. Bind field values to input controls and display `FieldError` output.
5. Add `AsyncFormValidator` for remote checks that need debouncing and stale suppression.

Minimal example:

```python
from gui_do import (
  FormSchema,
  PatternValidator,
  RequiredValidator,
  SchemaField,
  SchemaFormRuntime,
  ValidationPolicy,
)

schema = FormSchema(fields=(
  SchemaField(name="email", validators=(RequiredValidator(), PatternValidator(r".+@.+"))),
  SchemaField(name="password", validators=(RequiredValidator(),)),
))
runtime = SchemaFormRuntime(FieldGraphSchema.from_form_schema(schema), ValidationPolicy.ON_CHANGE)
```

Advanced pattern:

Build registration flows with `AsyncFormValidator` for uniqueness checks and combine with `WizardFlow` when onboarding requires staged progression. Keep each stage policy-scoped and aggregate errors through a shared validation pipeline.

Common mistakes and anti-patterns:

1. Validating only on submit when immediate feedback is expected.
2. Ignoring `ValidationPolicy` and firing validators from every keystroke path.
3. Running async checks without generation cancellation.
4. Treating rich document editing and scalar field editing as the same model.

Cross-links: 8.4 state observables, 8.5 input controls, 8.8 dialogs/overlays, 8.14 data pipelines.

[Back to Table of Contents](#table-of-contents)

### 8.14 Data and Dataflow Helpers

[Back to Table of Contents](#table-of-contents)

Data and dataflow helpers support scalable collection handling, staged transforms, and cancelable background processing. They exist so UI responsiveness survives heavy filtering/sorting/loading scenarios.

Mental model: data sources (`VirtualItemSource`, `AsyncDataProvider`) feed proxies (`SortFilterProxySource`) and virtualized surfaces (`VirtualizedWindow`, `VirtualizationCore`). Transform-heavy workloads go through `DataflowPipeline` where each generation can be canceled by a `CancellationToken`.

Primary APIs include `VirtualItemSource`, `FixedItemSource`, `SortFilterProxySource`, `AsyncDataProvider`, `LoadState`, `LoadStateKind`, `ObjectPool`, `DataCache`, `CacheStats`, `ListDiffCalculator`, `ListDiff`, `DiffInsert`, `DiffRemove`, `DiffMove`, `CancellationToken`, `PipelineStage`, `DataflowPipeline`, `PipelineHandle`, `AppStateStore`, `StateSelector`, `StateTransaction`, `MeasureMode`, `MeasurePolicy`, `VirtualizedWindow`, `RecyclePool`, and `VirtualizationCore`.

Typical usage flow:

1. Start with a source (`FixedItemSource` or custom `VirtualItemSource`).
2. Layer filtering/sorting through `SortFilterProxySource`.
3. Bind the result to list/grid/tree controls or virtualization core.
4. Route expensive transforms through `DataflowPipeline`.
5. Cancel stale generations whenever new user input supersedes prior work.

Minimal example:

```python
from gui_do import FixedItemSource, SortFilterProxySource

source = FixedItemSource(items)
proxy = SortFilterProxySource(source)
proxy.set_filter(lambda item: item.active)
proxy.set_sort_key(lambda item: item.name)
list_view.set_source(proxy)
```

Advanced pattern:

Compose a three-stage pipeline (`load -> parse -> rank`) in `DataflowPipeline` and emit stage metrics to telemetry. Use `ListDiffCalculator` between generations so rendering applies minimal patches, and back the visible region with `VirtualizationCore` plus `RecyclePool` for high-volume datasets.

Common mistakes and anti-patterns:

1. Full redraw or full replacement of lists for every update.
2. Not canceling stale pipeline generations.
3. Keeping unbounded cache/object pools without lifecycle policy.
4. Running async load completion handlers without checking generation identity.

Cross-links: 8.4 observables/store, 8.10 scheduler cooperation, 8.13 form validation inputs, 8.16 telemetry.

[Back to Table of Contents](#table-of-contents)

### 8.15 Graphics and Audio Integration Points

[Back to Table of Contents](#table-of-contents)

Graphics and audio integration points cover custom draw workloads and semantic sound playback. This layer exists for scenarios where standard controls are not sufficient, while still preserving consistent runtime coordination.

Mental model: drawing can happen through control composition or direct render helpers; audio cues should be domain events, not raw input noise. For rendering performance, dirty regions and offscreen targets should gate expensive redraws.

Primary graphics APIs include `BuiltInGraphicsFactory`, `DirtyRegionTracker`, `DrawContext`, `DrawPhase`, `AssetRegistry`, `DebugOverlay`, `SurfaceCompositor`, `Layer`, `ShapeRenderer`, `SurfaceEffects`, `VectorPath`, `SpriteSheet`, `FrameAnimation`, `ParticleSystem`, `Emitter`, `ParticleLayer`, `TileSet`, `TileMap`, `RenderTarget`, `LiveRenderTarget`, `OffscreenRenderTarget`, `create_render_target`, `create_surface`, `Node2D`, `SceneGraph2D`, and `Camera2D`.

Primary audio APIs include `SoundCue`, `SoundBankRegistry`, and `SoundEventBus`.

Typical usage flow:

1. Load assets once via `AssetRegistry`.
2. Update animation/particles in update hooks.
3. Use `DirtyRegionTracker` to mark changed regions.
4. Draw into layers or offscreen targets, then composite.
5. Publish semantic sound cues through `SoundEventBus`.

Minimal example:

```python
# update
self.particles.tick(dt_seconds)

# draw
self.particles.draw(screen)
host.sound_bus.publish(SoundCue("notify"))
```

Advanced pattern:

Use `OffscreenRenderTarget` to cache expensive world rendering, track changes with `DirtyRegionTracker`, and composite only dirty areas. Pair `SceneGraph2D` and `Camera2D` for transformed world coordinates while keeping UI overlay layers separate.

Common mistakes and anti-patterns:

1. Full-surface redraw every frame without dirty-region gating.
2. Loading assets in draw loops.
3. Triggering sounds from low-level pointer chatter rather than semantic actions.
4. Letting particle systems run without bounds/lifetime limits.

Cross-links: 8.2 draw hooks, 8.5 canvas controls, 8.10 scheduler timing, 8.16 profiling.

[Back to Table of Contents](#table-of-contents)

### 8.16 Telemetry, Introspection, and Operational Hooks

[Back to Table of Contents](#table-of-contents)

Telemetry and introspection APIs provide runtime observability for correctness and performance diagnostics. They exist so maintainers can localize regressions with data rather than visual guesswork.

Mental model: telemetry captures structured runtime samples and spans; introspection surfaces runtime object properties and geometry for live inspection. Use both during development and release hardening.

Primary telemetry APIs include `TelemetryCollector`, `TelemetrySample`, `configure_telemetry`, `telemetry_collector`, `analyze_telemetry_log_file`, `analyze_telemetry_records`, `load_telemetry_log_file`, and `render_telemetry_report`.

Primary introspection APIs include `SceneSpatialIndex`, `ui_property`, `PropertyDescriptor`, `PropertyRegistry`, `property_registry`, `PropertyInspectorModel`, and `InspectedProperty`.

Typical usage flow:

1. Enable telemetry early in startup.
2. Run representative scenarios.
3. Analyze records and compare to baseline behavior.
4. Use property and spatial inspection to localize problematic subtrees.

Minimal example:

```python
from gui_do import analyze_telemetry_records, configure_telemetry, render_telemetry_report, telemetry_collector

configure_telemetry(enabled=True)
report = analyze_telemetry_records(telemetry_collector.records)
print(render_telemetry_report(report))
```

Advanced pattern:

Build a debug panel that combines telemetry stage timings, `SceneSpatialIndex` query overlays, and `PropertyInspectorModel` snapshots for the selected control. This gives a unified diagnosis loop for layout, event routing, and rendering regressions.

Common mistakes and anti-patterns:

1. Profiling idle loops only.
2. Comparing telemetry runs with different scenario scripts.
3. Skipping telemetry configuration until after the behavior under test has already executed.
4. Treating property inspection as static snapshots instead of live runtime state.

Cross-links: 8.10 scheduling budgets, 8.11 persistence logs, 8.14 pipeline metrics, 8.15 draw cost analysis.

[Back to Table of Contents](#table-of-contents)

## Integration Patterns and Composition Recipes

[Back to Table of Contents](#table-of-contents)

### Recipe 1: Routed Feature + Actions + Shortcut Overlay

Goal: build a routed feature with discoverable keyboard commands and lifecycle-managed overlay wiring.

Why this combination: `RoutedRuntimeSpec` consolidates hotkeys, subscriptions, and shortcut-overlay attachment in one declaration, so feature code stays thin and teardown stays symmetric.

Step-by-step pattern:

1. Declare action IDs via `ActionSpec` in host config.
2. Build `RoutedRuntimeSpec` in feature init/build.
3. Wrap it with `RoutedFeatureLifecycleSpec`.
4. Attach in `bind_runtime` using `bind_routed_feature_lifecycle`.
5. Detach in `shutdown_runtime` using `shutdown_routed_feature_lifecycle`.

Complete code example:

```python
class ShortcutsFeature(RoutedFeature):
  def __init__(self):
    super().__init__()
    self._runtime_spec = RoutedRuntimeSpec(
      scene_name="main",
      shortcut_overlays=(
        ShortcutOverlaySpec(
          attr_name="_shortcut_overlay",
          toggle_action_name="help.shortcuts",
          manual_shortcut_lines=("F9  Toggle shortcut help",),
        ),
      ),
    )
    self._lifecycle = RoutedFeatureLifecycleSpec(runtime_spec=self._runtime_spec)

  def bind_runtime(self, host):
    bind_routed_feature_lifecycle(self, host, self._lifecycle)

  def shutdown_runtime(self, host):
    shutdown_routed_feature_lifecycle(self, host, self._lifecycle)
```

Validation notes: verify the toggle key/action opens the shortcut overlay and that manual lines render with expected filtering.

### Recipe 2: Window Presenter + Task Panel + Focus Toggle

Goal: host a floating window that can be toggled from the task panel while keeping focus traversal correct.

Why this combination: presenter separation keeps feature lifecycle clean, and task-panel focus toggle specs maintain visibility/focus coherence automatically.

Step-by-step pattern:

1. Declare `AnchoredWindowSpec` (or bundle spec).
2. Implement a `WindowPresenter` for window content.
3. Create the window in `build` with `create_feature_presented_window`.
4. Add `TaskPanelFocusToggleSpec` to routed runtime config.
5. Use `set_window_visible_state` for toggle behavior.

Complete code example:

```python
class InspectorFeature(RoutedFeature):
  def build(self, host):
    spec = AnchoredWindowSpec(
      control_id="inspector_window",
      title="Inspector",
      size=(420, 520),
      anchor="right",
      margin=(16, 16),
    )
    self.window = create_feature_presented_window(
      host,
      scene_name="main",
      spec=spec,
      presenter=self.presenter,
    )

  def toggle_window(self):
    set_window_visible_state(self.window, not bool(self.window.visible))
```

Validation notes: hidden windows should be excluded from focus traversal; task-panel toggle state should mirror visibility immediately.

### Recipe 3: State Store + Persistence + Snapshot Migration

Goal: keep centralized state durable across schema changes.

Why this combination: state-store APIs provide coherent app state while snapshot migration preserves compatibility between released versions.

Step-by-step pattern:

1. Initialize `AppStateStore` with canonical app state.
2. Expose slices through `StateSelector`.
3. Persist snapshots with `make_snapshot`.
4. On load, use `read_version` then `SnapshotMigrator.migrate`.
5. Restore and inspect restore report fields.

Complete code example:

```python
store = AppStateStore({"version": 3, "items": []})
visible_items = StateSelector(store, lambda s: s["items"])

snapshot = make_snapshot(SchemaVersion(3), dict(store.state))
raw_version = read_version(snapshot)
migrated = migrator.migrate(snapshot)
store.replace(dict(migrated.payload))
```

Validation notes: assert skipped/missing settings are reported but non-fatal; run migration tests for every historical version step.

### Recipe 4: Dataflow Pipeline + Telemetry + Error Boundary

Goal: execute cancelable background transforms with observability and UI failure containment.

Why this combination: `DataflowPipeline` handles stale-run cancellation, telemetry highlights bottlenecks, and `ErrorBoundary` keeps UI usable under presenter/render exceptions.

Step-by-step pattern:

1. Define pipeline stages with `PipelineStage` and `CancellationToken`.
2. Capture stage timing in telemetry samples/spans.
3. Wrap result subtree in `ErrorBoundary`.
4. Publish progress through `ObservableValue`.

Complete code example:

```python
self.progress = ObservableValue("idle")
self.pipeline = DataflowPipeline(stages=(load_stage, parse_stage, rank_stage))

def run_query(term: str):
  self.progress.value = "running"
  handle = self.pipeline.start(term)
  return handle

self.results_root = ErrorBoundary("results_boundary", fallback_builder=self._build_fallback)
```

Validation notes: stale generations should cancel immediately; telemetry report should isolate slow stage; fallback UI should render when presenter raises.

## End-to-End Reference Application

[Back to Table of Contents](#table-of-contents)

```python
from __future__ import annotations

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
  SceneSetupSpec,
  ShortcutOverlaySpec,
  TelemetryConfig,
  WorkspacePersistenceManager,
  bind_routed_feature_lifecycle,
  bootstrap_host_application,
  shutdown_routed_feature_lifecycle,
)


class CounterFeature(RoutedFeature):
  def __init__(self):
    super().__init__()
    self.count = ObservableValue(0)
    self._count_sub = None
    runtime_spec = RoutedRuntimeSpec(
      scene_name="main",
      shortcut_overlays=(
        ShortcutOverlaySpec(
          attr_name="_shortcut_overlay",
          toggle_key=K_F9,
          manual_shortcut_lines=("F9  Toggle keyboard shortcuts",),
        ),
      ),
    )
    self._lifecycle = RoutedFeatureLifecycleSpec(runtime_spec=runtime_spec)

  def build(self, host):
    self.root = host.app.add(PanelControl("counter_root", Rect(0, 0, 360, 140)), scene_name="main")
    self.label = self.root.add(LabelControl("counter_value", Rect(12, 12, 300, 28), "0"))

  def bind_runtime(self, host):
    bind_routed_feature_lifecycle(self, host, self._lifecycle)
    self._count_sub = self.count.subscribe(lambda value: setattr(self.label, "text", str(value)))
    self.label.text = str(self.count.value)

  def shutdown_runtime(self, host):
    shutdown_routed_feature_lifecycle(self, host, self._lifecycle)
    if self._count_sub is not None:
      self._count_sub.dispose()
      self._count_sub = None


class Host:
  def __init__(self):
    self.workspace_manager = WorkspacePersistenceManager()

  def start(self):
    config = HostApplicationConfig(
      display_size=(960, 600),
      window_title="gui_do reference app",
      fonts={"default": {"system_name": "Segoe UI", "size": 14}},
      font_role_specs=(),
      cursors=(),
      scene_specs=(SceneSetupSpec(name="main", make_initial=True),),
      feature_specs=(FeatureSpec(attr_name="counter_feature", factory=CounterFeature),),
      window_specs=(),
      runtime_scene_specs=(RuntimeSceneSpec(scene_name="main", bind_escape_to_exit=True),),
      action_specs=(
        ActionSpec(action_id="app.exit", label="Exit", kind="exit"),
        ActionSpec(action_id="help.shortcuts", label="Shortcuts", kind="palette_open"),
      ),
      static_accessibility_specs=(),
      initial_scene_name="main",
      telemetry=TelemetryConfig(enabled=True),
    )
    bootstrap_host_application(self, config)
    self.app.load_workspace(self.workspace_manager, "workspace.json")
    self.app.save_workspace(self.workspace_manager, "workspace.json")
    self.app.run_entrypoint(WORKSPACE_SAVE=True, workspace_manager=self.workspace_manager)


if __name__ == "__main__":
  Host().start()
```

### What This Listing Demonstrates

This listing shows a full bootstrap path using current `HostApplicationConfig` field names, routed feature lifecycle wiring, observable-to-control projection, declarative action declarations, runtime-scene escape policy, telemetry enablement, and workspace load/save hooks through `WorkspacePersistenceManager`.

### Validation Checklist

1. Application opens and enters the main scene.
2. The counter label reflects observable updates.
3. F9 toggles shortcut help overlay.
4. Escape exits through runtime-scene policy.
5. Workspace load/save calls succeed without aborting startup.
6. Telemetry is enabled during runtime.
7. Routed lifecycle wiring binds and tears down without leaked subscriptions.

## Testing, Diagnostics, and Reliability

[Back to Table of Contents](#table-of-contents)

This chapter defines how gui_do behavior is verified, diagnosed, and release-gated. The goal is operational confidence: deterministic runtime behavior, reproducible regressions, and documented release checks that fail loudly when contracts drift.

### Contract Tests

The contract suite verifies that the root API, behavioral guarantees, and layering boundaries stay aligned with documentation and runtime policy. Run the core contract gate with:

```bash
python -m pytest -q tests/test_public_api_exports.py tests/test_public_api_docs_contracts.py tests/test_runtime_operating_contracts.py tests/test_boundary_contracts.py tests/test_gui_application_workspace_contracts.py
```

Coverage responsibilities:

1. `test_public_api_exports.py`: ensures root `__all__` names are importable and present.
2. `test_public_api_docs_contracts.py`: ensures published API names remain synchronized with contract docs.
3. `test_runtime_operating_contracts.py`: validates runtime guarantees including scheduler budget clamping, deterministic routing, scene isolation, and event normalization.
4. `test_boundary_contracts.py`: enforces gui_do/demo separation with no reverse-boundary imports.
5. `test_gui_application_workspace_contracts.py`: verifies workspace restore behavior and restore-report semantics.

### Runtime Behavior Tests

Beyond contract gates, runtime behavior tests should target workspace load/save sequencing, overlay/tooltip/cursor routing order, layout and animation determinism under frame pressure, control runtime edge-cases, and accessibility wiring. In this repository, related modules include `test_runtime_operating_contracts.py`, `test_runtime_guarantees_and_determinism.py`, `test_core_only_bootstrap_contracts.py`, and accessibility/control-focused runtime tests under `tests/`.

### Debug and Trace Tools

Use reproducible traces first, then visual and metric diagnostics:

1. `EventRecorder` and `EventPlayback` reproduce input sequences and route-order regressions.
2. `DebugOverlay` surfaces live scene/control state for visual inspection.
3. `PropertyInspectorPanel` with `PropertyInspectorModel` and `ui_property` metadata exposes runtime control properties.
4. Telemetry analysis (`analyze_telemetry_log_file`, `analyze_telemetry_records`, `render_telemetry_report`) highlights frame-budget and pipeline hot spots.

### Maintainer Release Runbook

1. Run the high-priority contract gate command and stop on first failure.
2. Run runtime determinism and boundary-focused tests (`test_runtime_guarantees_and_determinism.py`, `test_boundary_contracts.py`, workspace contracts).
3. Validate current MANUAL examples against root-import API names in `gui_do/__init__.py`.
4. Execute an end-to-end smoke run using a workspace restore cycle (load, run, save).
5. Capture telemetry baseline traces for representative scenarios and compare with prior baseline.
6. Confirm migration path behavior for any snapshot/schema changes using `SnapshotMigrator` tests.
7. Finalize release only when runtime guarantees, docs contracts, and full test suite pass.

### Regression Triage Workflow

1. Reproduce: isolate the smallest user flow that triggers the issue.
2. Trace: record input and routing with `EventRecorder` and compare with expected dispatch order.
3. Localize: inspect state/property/layout using telemetry and inspector overlays.
4. Test-first: add or tighten a failing regression/contract test.
5. Patch: apply the minimal fix that restores contract behavior.
6. Adjacent contracts: rerun related contract modules to detect collateral drift.

### Maintainer Diff Checklist

**Inventory delta checks:**

1. Compare current root exports in `gui_do/__init__.py` with Appendix D and D.1 entries. Identify any new or removed tiers and APIs.
2. Check `docs/` contracts for changed guarantees, policies, or boundary rules. Note any changes to runtime operating contracts, public API specifications, or architecture boundaries.
3. Check `tests/` for new contract/runtime test modules that imply manual updates. Look for new `test_*_contracts.py` or `test_runtime_*` files.
4. Check `demo_features/` for new recommended composition patterns to document. Review feature organization and cross-feature wiring patterns.

**Content integrity checks:**

1. Every changed system has updates in both chapter narrative and quick-index references. Verify that narrative sections and API quick-index entries remain synchronized.
2. Removed APIs are deleted from examples, recipes, and appendix indexes. Confirm that deprecated APIs are moved to migration notes, not left in active guidance.
3. Added APIs are classified at the right abstraction level (Tier 1 first, then lower tiers). Verify that new exports follow the tier organization in `gui_do/__init__.py`.

**Navigation and structure checks:**

1. All newly added sections are present in TOC and resolve correctly. Verify that anchor links in the TOC match actual section headings.
2. Every major section still contains a Back to Table of Contents link. Ensure navigation links are preserved.
3. Top-level chapter order remains stable unless intentional restructure is recorded. Document any reordering rationale.

**Operational checks:**

1. Re-run high-priority contract tests:
   ```bash
   python -m pytest -q tests/test_public_api_exports.py tests/test_public_api_docs_contracts.py tests/test_runtime_operating_contracts.py tests/test_boundary_contracts.py tests/test_gui_application_workspace_contracts.py
   ```
2. Validate end-to-end reference listing assumptions against current runtime behavior. Confirm that example code patterns match actual API signatures.
3. Record unresolved ambiguities as explicit TODO notes in Migration, Versioning, and Deprecation Notes section.

[Back to Table of Contents](#table-of-contents)

## Performance and Scaling Guidance

[Back to Table of Contents](#table-of-contents)

### Scheduler Budget Contract

The scheduler dispatch contract is clamped to fraction `0.12` of `dt` milliseconds, floor `0.5 ms`, and ceiling `4.0 ms`. The fraction bounds work under slow frames, the floor avoids starvation under fast frames, and the ceiling prevents background dispatch from consuming frame time catastrophically.

### Dirty-Region Rendering

`DirtyRegionTracker` is the primary draw-cost optimization in complex scenes. Mark changed rectangles and avoid rendering unaffected regions. The incremental union cache means `overlaps_dirty()` can answer overlap checks in O(1) time without scanning all dirty rectangles on each query.

### Virtualization and Incremental Rendering

Use `VirtualizationCore` and `VirtualizedWindow` for large collections; use `RecyclePool` for view reuse; and use `ListDiffCalculator` to compute minimal update patches (`DiffInsert`, `DiffRemove`, `DiffMove`) rather than replacing full lists each frame.

### Practical Scaling Checklist

1. Keep update handlers scene-scoped and short.
2. Avoid full per-frame reallocation of large collections.
3. Use `ObjectPool` for high-churn temporary objects.
4. Debounce expensive input/search paths with `Debouncer`.
5. Use `DataflowPipeline` with `CancellationToken` for preemptible background transforms.
6. Profile representative user journeys instead of idle loops.
7. Gate expensive draw paths with `DirtyRegionTracker`.

[Back to Table of Contents](#table-of-contents)

## Migration, Versioning, and Deprecation Notes

[Back to Table of Contents](#table-of-contents)

### Versioned Snapshot Strategy

Recommended migration workflow:

1. Write snapshots with `make_snapshot(current_version, state_dict)`.
2. On load, read version with `read_version(raw)`.
3. Pass the payload through `SnapshotMigrator.migrate(snapshot)`.
4. Apply migrated state to runtime restore paths.

`MigrationRegistry` holds one-directional `MigrationStep` registrations (source -> target). `SnapshotMigrator` resolves migration paths over this graph. If no path is resolvable, `MigrationError` is raised and should be surfaced as a migration failure, not silently ignored.

### Deprecation Handling

Preferred policy is additive transitions first: introduce new fields/parameters, preserve old behavior with warnings, provide migration paths, then remove deprecated behavior on a documented timeline. Centralize all deprecation notes here so maintainers and integrators have one authoritative history.

No deprecated public APIs are cataloged as of this manual generation. Add entries here when formal deprecations are introduced.

### Upgrade Checklist

1. Run contract tests before and after upgrade.
2. Validate consumer imports remain root-import based (`from gui_do import ...`).
3. Re-verify action/input/focus routing in active scenes and window scopes.
4. Validate restore report behavior for `skipped_settings` and `missing_settings_blocks`.
5. Re-run telemetry baselines and compare with prior release baselines.

[Back to Table of Contents](#table-of-contents)

## FAQ and Troubleshooting

[Back to Table of Contents](#table-of-contents)

### Q: Should I build apps directly with controls or with features?

Use features as the architectural unit. Controls are implementation details inside feature boundaries. Features provide lifecycle ordering, event routing, structured teardown, and scene ownership; controls alone do not provide those contracts.

### Q: When should I use `RoutedFeature` over `Feature`?

Use `RoutedFeature` when you need topic-based message routing and declarative runtime attachments such as shortcut overlays, task-panel toggles, and event subscriptions. Use plain `Feature` when behavior is local and simple lifecycle hooks are sufficient.

### Q: Why are some key handlers not firing?

Check focus ownership first, then scope registration. A hidden window, active modal overlay, or mismatched scene/window scope can intercept or exclude key routing. Use `EventRecorder` traces to confirm whether the key reached your expected candidate set.

### Q: Why do toast clicks not pass through?

Toast bounds consume left-clicks by contract to prevent accidental click-through into underlying controls. Use toast callbacks for intentional interactions instead of relying on event pass-through.

### Q: How do I avoid breaking workspace restore across versions?

Persist versioned snapshots, register migration steps for every schema transition, and inspect restore reports for skipped/missing settings. Treat missing keys as non-fatal compatibility cases and surface user-facing notifications where appropriate.

### Q: How do I confirm my API usage is within the supported surface?

Use explicit root imports (`from gui_do import Name`) and run export contract tests. Avoid importing from internal modules (`gui_do.features.*`, `gui_do.controls.*`, etc.) in consumer applications unless you are explicitly extending internals.

### Q: Why does my feature's `bind_runtime` run before my sibling's `build`?

By contract it should not. All scene features complete `build` before `bind_runtime` begins. If ordering appears wrong, verify both features are registered in the same scene and that setup code is not manually invoking lifecycle hooks out of order.

### Q: How do I add a keyboard shortcut without touching every location where that key is handled?

Declare an `ActionSpec`, then register hotkeys via `ActionHotkeySpec` or `RoutedRuntimeSpec`. This centralizes binding through the action/input infrastructure and avoids scattered key-condition branches.

[Back to Table of Contents](#table-of-contents)

## Appendix

[Back to Table of Contents](#table-of-contents)

### Appendix A: Glossary

[Back to Table of Contents](#table-of-contents)

**Feature**: A lifecycle-managed behavior unit that owns scene-scoped runtime logic and control composition. `Feature`, `DirectFeature`, `LogicFeature`, and `RoutedFeature` share core lifecycle contracts while specializing update, message, and routing behavior.

**Spec**: A declarative object that describes runtime wiring and policy rather than executing it immediately. Specs make bootstrap deterministic and serialize architectural intent.

**Host**: A plain Python object passed to bootstrap. Bootstrap attaches runtime members (application, features, scene/window models, action and palette managers, and helpers) onto this host.

**Scene**: A top-level interaction context. Features are scene-associated and runtime routing favors active-scene containment for predictable behavior.

**Window presentation**: The visibility, focus, and toggle model for windows within scenes, including task-panel/menu-strip integration and deterministic show/hide behavior.

**Routed runtime**: Declarative runtime attachments for a feature (`hotkeys`, `subscriptions`, `shortcut overlays`, `focus toggles`, optional palette key registration) expressed through routed runtime specs.

**Observable**: A reactive value or collection that notifies subscribers on change, enabling decoupled UI updates and cross-feature state projection.

**Workspace state**: Persisted runtime context used for session restore, including scene selection, feature states, scene snapshots, and setting replay metadata.

**Contract test**: A test that validates framework-level guarantees (exports, docs alignment, runtime determinism, restore semantics, and architectural boundaries) rather than only local function correctness.

**Tier**: A grouping of root exports in `gui_do/__init__.py` by abstraction level and intended usage priority.

### Appendix B: Lifecycle/Event Sequence

[Back to Table of Contents](#table-of-contents)

1. `bootstrap_host_application` materializes host runtime state from specs.
2. Scene feature `build(host)` executes in scene order.
3. Scene feature `bind_runtime(host)` executes after all `build` calls complete.
4. Runtime loop begins.
5. Each frame normalizes raw pygame events into `GuiEvent`.
6. Overlay/focus/window/scene routing pass runs.
7. Feature `handle_event` executes for candidate handlers.
8. Feature update hooks execute and scheduler dispatches in budget.
9. Feature/control draw passes render and present.
10. Scene transitions run `shutdown_runtime` for departing features, then `build` and `bind_runtime` for arriving features.
11. On exit, active feature runtime shuts down and workspace persistence hooks run when configured.

### Appendix C: System Dependency Map

[Back to Table of Contents](#table-of-contents)

Bootstrap depends on declarative spec families, feature lifecycle primitives, scene/window presentation, action/input wiring, and theme/font setup. It does not replace those systems; it composes them deterministically.

Feature and app-core layers depend on control composition, observables/state primitives, and event/action routing for operational behavior. They consume layout/focus/overlay systems rather than reimplementing them.

Layout and focus systems depend on a stable control tree and scene/window visibility state. Overlays depend on routing precedence and focus policy to enforce modal/transient behavior.

Persistence and migration depend on state models and scene/window registration metadata so restore can map serialized snapshots back to live runtime structures.

Scheduling and animation depend on per-frame lifecycle hooks and scene scope boundaries. Dataflow builds on scheduling for staged preemptible work.

Telemetry and introspection are cross-cutting: they observe nearly every layer. Audio depends on pygame mixer integration and semantic event publishing through `SoundEventBus`.

Service scopes are orthogonal and can be used across tiers as dependency containers without changing scene or feature contracts.

### Appendix D: API Quick Index

[Back to Table of Contents](#table-of-contents)

#### Bootstrap and Declarative Composition

`Feature`, `DirectFeature`, `LogicFeature`, `RoutedFeature`, `FeatureMessage`, `FeatureManager`, `ScenePresentationModel`, `SceneSetupSpec`, `setup_standard_font_roles`, `FeatureSpec`, `WindowSpec`, `RuntimeSceneSpec`, `ActionSpec`, `StaticAccessibilitySpec`, `CursorSpec`, `SceneRootSpec`, `AnchoredWindowSpec`, `LogicBindingSpec`, `TaskPanelButtonSpec`, `TaskPanelWindowToggleGroupSpec`, `SceneCommandPaletteSpec`, `ActionHotkeySpec`, `ControlKeyBindingSpec`, `SceneTaskPanelSpec`, `TaskPanelLinearLayoutSpec`, `TaskPanelSceneNavButtonSpec`, `EventSubscriptionSpec`, `ShortcutOverlaySpec`, `TaskPanelFocusToggleSpec`, `RoutedRuntimeSpec`, `RoutedFeatureLifecycleSpec`, `FeatureWindowBundleBindingSpec`, `WindowToggleBindingSpec`, `SceneSetupBindingSpec`, `RuntimeSceneBindingSpec`, `SceneRootBindingSpec`, `CursorBindingSpec`, `FontRoleBindingSpec`, `ActionBindingSpec`, `PaletteBindingSpec`, `SceneBundleBindingSpec`, `HostApplicationBindingSpec`, `TabbedPresenterSpec`, `AccessibilitySequenceSpec`, `TabBuilderSpec`, `NotificationSpec`, `HostApplicationConfig`, `TelemetryConfig`, `bootstrap_host_application`, `build_notification_center`, `make_window_toggle_spec`, `make_scene_nav_action`, `make_exit_action`, `make_palette_open_action`, `make_static_accessibility_spec`, `build_feature_specs`, `build_feature_window_bundle_specs`, `build_window_toggle_specs`, `build_scene_setup_specs`, `build_runtime_scene_specs`, `build_scene_root_specs`, `build_cursor_specs`, `build_font_role_specs`, `build_scene_nav_actions`, `build_action_specs`, `build_scene_bundle_specs`, `build_static_accessibility_specs`, `build_host_application_config`

#### Application Core and Scene Transitions

`GuiApplication`, `create_display`, `SceneTransitionManager`, `SceneTransitionStyle`, `apply_scene_setup_specs`

#### Data, Reactive State, and Persistence

`ObservableValue`, `PresentationModel`, `ComputedValue`, `InvalidationTracker`, `ChangeKind`, `CollectionChange`, `ObservableList`, `ObservableDict`, `CollectionViewQuery`, `CollectionView`, `Binding`, `BindingGroup`, `ObservableStream`, `SelectionModel`, `SelectionMode`, `CommandHistory`, `Command`, `CommandTransaction`, `StateMachine`, `HierarchicalStateMachine`, `Router`, `RouteEntry`, `SettingsRegistry`, `SettingDescriptor`, `WorkspaceState`, `WorkspacePersistenceManager`, `DEFAULT_WORKSPACE_STATE_PATH`, `SceneSnapshot`, `NodeSnapshot`, `UndoContextManager`, `AppStateStore`, `StateSelector`, `StateTransaction`, `SchemaVersion`, `VersionedSnapshot`, `MigrationStep`, `MigrationRegistry`, `SnapshotMigrator`, `MigrationError`, `make_snapshot`, `read_version`

#### Events, Actions, Focus, and Interaction Routing

`EventPhase`, `EventType`, `GuiEvent`, `ValueChangeCallback`, `ValueChangeReason`, `EventManager`, `EventBus`, `GestureRecognizer`, `EventRecorder`, `EventPlayback`, `RecordedEvent`, `InputSnapshot`, `Signal`, `SignalConnection`, `ActionManager`, `ActionContext`, `ActionMiddleware`, `ActionDescriptor`, `ActionRegistry`, `InputMap`, `InputBinding`, `KeyChordManager`, `KeyChord`, `ChordStep`, `FocusManager`, `FocusScope`, `FocusScopeManager`, `WindowFocusManager`, `FocusRing`, `InteractionPhase`, `InteractionContext`, `InteractionTransition`, `InteractionStateMachine`

#### Scheduling, Animation, and Pipelines

`TaskEvent`, `TaskScheduler`, `Timers`, `TweenManager`, `TweenHandle`, `Easing`, `AnimationSequence`, `AnimationHandle`, `TransitionManager`, `TransitionSpec`, `TransitionEvent`, `AnimationStateMachine`, `AnimationTransitionMode`, `SceneTimeline`, `Debouncer`, `Throttler`, `CooperativeScheduler`, `CoroutineHandle`, `Pause`, `Sleep`, `WaitForEvent`, `WaitForSignal`, `WaitUntil`, `WaitForAll`, `CancellationToken`, `PipelineStage`, `DataflowPipeline`, `PipelineHandle`

#### Theme, Typography, and Localization

`FontManager`, `FontRoleRegistry`, `ColorTheme`, `ThemeManager`, `DesignTokens`, `ScopedTheme`, `ScopedThemeManager`, `TextFormatter`, `NumericFormatter`, `PatternFormatter`, `FixedPatternFormatter`, `TextFlow`, `TextSpan`, `TextSearcher`, `TextMatch`, `StringTable`, `LocaleRegistry`, `ThemeInvalidationBus`

#### Layout and Virtualization

`LayoutAxis`, `LayoutManager`, `WindowTilingManager`, `ConstraintLayout`, `AnchorConstraint`, `DockPane`, `DockTabs`, `DockSplit`, `DockWorkspace`, `FlexLayout`, `FlexItem`, `FlexDirection`, `FlexAlign`, `FlexJustify`, `GridLayout`, `GridTrack`, `GridPlacement`, `CellCaretLayout`, `CellCaretState`, `LayoutAnimator`, `LayoutPass`, `MeasureContext`, `ArrangeContext`, `LayoutRoot`, `ResponsiveLayout`, `Breakpoint`, `SnapGrid`, `AlignmentGuide`, `SnapComposer`, `SnapTarget`, `FlowLayout`, `FlowItem`, `Viewport`, `ConstraintAttr`, `LayoutConstraint`, `ConstraintSet`, `ConstraintLayoutEngine`, `AdaptivePolicy`, `resolve_adaptive_policy`, `MeasureMode`, `MeasurePolicy`, `VirtualizedWindow`, `RecyclePool`, `VirtualizationCore`

#### Overlay and Command Surfaces

`OverlayManager`, `OverlayHandle`, `Alignment`, `PlacementResult`, `PopupPlacement`, `Side`, `compute_popup_rect`, `DialogManager`, `DialogHandle`, `ToastManager`, `ToastHandle`, `ToastSeverity`, `ContextMenuManager`, `ContextMenuItem`, `ContextMenuHandle`, `CommandPaletteManager`, `CommandEntry`, `CommandPaletteHandle`, `TooltipManager`, `TooltipHandle`, `MenuBarManager`, `FileDialogManager`, `FileDialogOptions`, `FileDialogHandle`, `NotificationCenter`, `NotificationRecord`, `ResizeManager`, `CursorManager`, `CursorHandle`, `CursorShape`, `DragDropManager`, `DragPayload`, `ClipboardManager`, `TransferData`, `TransferManager`, `ShortcutHelpOverlay`, `ShortcutSection`, `ShortcutEntry`

#### Form and Validation Runtime

`FormModel`, `FormField`, `ValidationRule`, `FieldError`, `FormSchema`, `SchemaField`, `DocumentModel`, `WizardFlow`, `WizardStep`, `WizardHandle`, `ValidationResult`, `Validator`, `RequiredValidator`, `RangeValidator`, `LengthValidator`, `PatternValidator`, `CustomValidator`, `DependentValidator`, `ValidationPipeline`, `AsyncFieldValidator`, `AsyncFormValidator`, `FieldSchema`, `FieldGraphSchema`, `ValidationPolicy`, `SchemaFormRuntime`

#### Control Catalog

`PanelControl`, `LabelControl`, `ButtonControl`, `ToggleControl`, `SliderControl`, `ScrollbarControl`, `CanvasControl`, `CanvasEventPacket`, `CanvasViewport`, `FrameControl`, `ImageControl`, `ArrowBoxControl`, `ButtonGroupControl`, `TabControl`, `TabItem`, `DockWorkspacePanel`, `TextInputControl`, `TextAreaControl`, `RichLabelControl`, `DropdownControl`, `DropdownOption`, `ListViewControl`, `ListItem`, `OverlayPanelControl`, `DataGridControl`, `GridColumn`, `GridRow`, `TreeControl`, `TreeNode`, `SplitterControl`, `SpinnerControl`, `RangeSliderControl`, `ColorPickerControl`, `ScrollViewControl`, `ProgressBarControl`, `AnimatedImageControl`, `ErrorBoundary`, `WindowControl`, `TaskPanelControl`, `WindowPresenter`, `MenuBarControl`, `MenuEntry`, `SceneMenuStripControl`, `NotificationPanelControl`, `PropertyInspectorPanel`, `ToolbarControl`, `ToolbarItem`, `StatusBarControl`, `StatusSlot`, `ExpanderControl`, `DatePickerControl`, `TimePickerControl`, `BreadcrumbControl`, `BreadcrumbItem`, `SplitButtonControl`, `SplitButtonOption`, `ChipInputControl`

#### Graphics, Audio, Telemetry, and Introspection

`BuiltInGraphicsFactory`, `DirtyRegionTracker`, `DrawContext`, `DrawPhase`, `AssetRegistry`, `DebugOverlay`, `SurfaceCompositor`, `Layer`, `ShapeRenderer`, `SurfaceEffects`, `VectorPath`, `SpriteSheet`, `FrameAnimation`, `ParticleSystem`, `Emitter`, `ParticleLayer`, `TileSet`, `TileMap`, `TelemetryCollector`, `TelemetrySample`, `configure_telemetry`, `telemetry_collector`, `analyze_telemetry_log_file`, `analyze_telemetry_records`, `load_telemetry_log_file`, `render_telemetry_report`, `SceneSpatialIndex`, `ui_property`, `PropertyDescriptor`, `PropertyRegistry`, `property_registry`, `PropertyInspectorModel`, `InspectedProperty`, `SoundCue`, `SoundBankRegistry`, `SoundEventBus`

#### Accessibility and Advanced Runtime Helpers

`AccessibilityRole`, `LivePoliteness`, `AccessibilityNode`, `AccessibilityTree`, `AccessibilityAnnouncement`, `AccessibilityBus`, `FrameTimer`, `TabPanelManager`, `WindowRelativeRect`, `resolve_scene_selection_callback`, `minimize_window_menu_entries`, `set_window_visible_state`, `toggle_window_visibility`, `create_anchored_feature_window`, `add_window_scene_menu_strip`, `inset_rect`, `centered_horizontal_strip_layout`, `split_slot_bounds`, `partition_rects`, `place_control`, `place_control_unlabeled`, `register_placed_control`, `add_group_label`, `PlacedControl`, `make_labeled_slot_height_fn`, `ControlRegistry`, `build_tools_menu_entries`, `add_standard_scene_menu_strip`, `apply_accessibility_sequence`, `apply_accessibility_sequence_from_attrs`, `register_companion_logic_features`, `ensure_scene_scheduler`, `sorted_window_bindings`, `collect_window_toggle_controls`, `apply_window_toggle_accessibility`, `add_window_toggle_task_panel_controls`, `add_task_panel_window_toggle_group`, `setup_scene_command_palette_key`, `register_window_toggle_tooltips`, `initialize_locale_registry`, `bind_input_map_actions`, `register_descriptors`, `resolve_canvas_local_point`, `apply_runtime_scene_pristine_assets`, `bind_runtime_scene_exit_keys`, `prewarm_runtime_scenes`, `add_task_panel_button`, `add_task_panel_buttons`, `register_tooltip_specs`, `register_action_hotkeys`, `draw_controls_prewarm`, `ensure_scene_task_panel`, `create_task_panel_linear_layout`, `add_task_panel_scene_nav_button`, `add_scene_task_panel_items`, `centered_overlay_rect`, `create_shortcut_help_overlay`, `bind_feature_event_subscription`, `unbind_feature_event_subscription`, `setup_routed_runtime`, `shutdown_routed_runtime`, `bind_task_panel_focus_toggle`, `add_window_control`, `add_window_label`, `add_window_button`, `add_window_button_row`, `instantiate_features_from_specs`, `register_features_from_specs`, `register_window_presentation_specs`, `register_window_tab_builders`, `build_tab_builder_specs`, `create_tab_control_from_specs`, `compute_tabbed_window_layout`, `setup_feature_presenter_tabs_from_window_content`, `register_window_tab_builder_specs`, `setup_feature_presenter_tabs`, `register_tab_update_handlers`, `create_presented_anchored_window`, `create_presented_window_from_spec`, `create_feature_presented_window`, `bind_feature_logic_aliases`, `setup_routed_feature_runtime`, `register_routed_feature_companions`, `bind_routed_feature_lifecycle`, `shutdown_routed_feature_lifecycle`, `ActiveTabUpdateRouter`, `TabLayoutContext`, `declare_host_actions`, `build_host_main_tab_order`, `apply_host_main_accessibility`, `UiEngine`, `ServiceKey`, `ServiceScope`, `ScopeStack`

### Appendix D.1: Tier Matrix

[Back to Table of Contents](#table-of-contents)

| Tier | System | Representative Key Types |
| --- | --- | --- |
| 1 | Primary entry points and data-driven APIs | `HostApplicationConfig`, `bootstrap_host_application`, `FeatureSpec`, `RoutedRuntimeSpec`, `SceneBundleBindingSpec` |
| 2 | Core application and scene management | `GuiApplication`, `create_display`, `SceneTransitionManager`, `SceneTransitionStyle`, `apply_scene_setup_specs` |
| 3 | Essential data and state | `ObservableValue`, `ComputedValue`, `ObservableList`, `CollectionView`, `SelectionModel` |
| 4 | Events, actions, focus, input | `GuiEvent`, `EventManager`, `ActionManager`, `InputMap`, `FocusManager` |
| 5 | Scheduling and animation | `TaskScheduler`, `TweenManager`, `TransitionManager`, `SceneTimeline`, `CooperativeScheduler` |
| 6 | Theme and font management | `ThemeManager`, `ColorTheme`, `DesignTokens`, `FontManager`, `ScopedThemeManager` |
| 7 | Telemetry and diagnostics | `TelemetryCollector`, `configure_telemetry`, `analyze_telemetry_records`, `render_telemetry_report` |
| 8 | Layout and spatial | `LayoutManager`, `FlexLayout`, `GridLayout`, `DockWorkspace`, `ResponsiveLayout` |
| 9 | Overlay managers and windows | `OverlayManager`, `DialogManager`, `ToastManager`, `CommandPaletteManager`, `ShortcutHelpOverlay` |
| 10 | Forms and data binding | `FormModel`, `FormSchema`, `ValidationPipeline`, `WizardFlow`, `DocumentModel` |
| 11 | State and persistence | `WorkspacePersistenceManager`, `SettingsRegistry`, `CommandHistory`, `StateMachine`, `SceneSnapshot` |
| 12 | Primary controls | `PanelControl`, `LabelControl`, `ButtonControl`, `CanvasControl`, `TabControl` |
| 13 | Extended controls | `TextInputControl`, `DropdownControl`, `DataGridControl`, `WindowControl`, `PropertyInspectorPanel` |
| 14 | Text and localization | `TextFormatter`, `TextFlow`, `TextSearcher`, `StringTable`, `LocaleRegistry` |
| 15 | Data and collections | `VirtualItemSource`, `SortFilterProxySource`, `AsyncDataProvider`, `DataCache`, `ListDiffCalculator` |
| 16 | Graphics and rendering | `DirtyRegionTracker`, `DrawContext`, `SurfaceCompositor`, `ParticleSystem`, `TileMap` |
| 17 | Introspection and inspection | `SceneSpatialIndex`, `ui_property`, `PropertyRegistry`, `PropertyInspectorModel` |
| 18 | Advanced runtime and bootstrapping | `set_window_visible_state`, `create_feature_presented_window`, `bind_routed_feature_lifecycle`, `ActiveTabUpdateRouter`, `TabLayoutContext` |
| 19 | Infrastructure internals | `UiEngine` |
| 20 | Audio | `SoundCue`, `SoundBankRegistry`, `SoundEventBus` |
| 21 | Accessibility | `AccessibilityRole`, `AccessibilityNode`, `AccessibilityTree`, `AccessibilityBus` |
| 22 | Theme invalidation | `ThemeInvalidationBus` |
| 23 | Undo context routing | `UndoContextManager` |
| 24 | Async form validation | `AsyncFieldValidator`, `AsyncFormValidator` |
| 25 | Scoped service graph | `ServiceKey`, `ServiceScope`, `ScopeStack` |
| 26 | Cancelable dataflow pipeline | `CancellationToken`, `PipelineStage`, `DataflowPipeline`, `PipelineHandle` |
| 27 | Transactional app state store | `AppStateStore`, `StateSelector`, `StateTransaction` |
| 28 | Adaptive constraint layout v2 | `ConstraintLayoutEngine`, `AdaptivePolicy`, `resolve_adaptive_policy`, `ConstraintSet` |
| 29 | Unified virtualization core | `VirtualizedWindow`, `VirtualizationCore`, `RecyclePool`, `MeasurePolicy` |
| 30 | Interaction state machine framework | `InteractionPhase`, `InteractionContext`, `InteractionTransition`, `InteractionStateMachine` |
| 31 | Schema-driven form runtime | `FieldSchema`, `FieldGraphSchema`, `ValidationPolicy`, `SchemaFormRuntime` |
| 32 | Portable snapshot and migration layer | `SchemaVersion`, `VersionedSnapshot`, `MigrationStep`, `SnapshotMigrator`, `MigrationError` |

### Appendix D.2: Selection Heuristics

[Back to Table of Contents](#table-of-contents)

Decision rules:

1. Start at Tier 1. If `HostApplicationConfig` + `bootstrap_host_application` + feature lifecycle types solve the problem, stop there.
2. Descend one tier at a time only when a higher tier cannot express the required behavior.
3. Use Tier 18 helpers for stable bootstrap/runtime extension points.
4. In consumer code, prefer root imports (`from gui_do import ...`) over submodule imports.
5. Avoid Tier 19 (`UiEngine`) in application code.

Decision shortcuts:

1. Need app setup: `HostApplicationConfig` + `bootstrap_host_application`.
2. Need cross-feature runtime wiring: `RoutedRuntimeSpec` + routed lifecycle helpers.
3. Need large dataset UI: virtualization and dataflow APIs before custom loops.
4. Need durable persistence: `WorkspacePersistenceManager` + `SnapshotMigrator`.
5. Need discoverable shortcuts: `ShortcutOverlaySpec` on routed runtime.

### Appendix E: Architecture Templates

[Back to Table of Contents](#table-of-contents)

**Template 1: Small Single-Scene App**

Use one scene and two to four features. Keep feature-local `ObservableValue` state, declare actions with `ActionSpec`, and include `RuntimeSceneSpec(bind_escape_to_exit=True)` for predictable exit behavior. Skip task-panel/window presenter complexity unless required.

**Template 2: Multi-Window Workbench**

Use two or more scenes with scene navigation and task-panel affordances. Pair per-window presenters with `FeatureWindowBundleBindingSpec` and `TaskPanelFocusToggleSpec` to keep visibility and focus synchronized. Add shortcut overlays via routed runtime specs for discoverability.

**Template 3: Data-Heavy Analysis Tool**

Use `AsyncDataProvider`, `SortFilterProxySource`, and virtualization primitives to avoid rendering full datasets. Route expensive transformations through `DataflowPipeline` with cancellation and instrument with telemetry. Use `DirtyRegionTracker` for incremental redraw.

**Template 4: Long-Running Workflow App**

Use `CooperativeScheduler` for multi-step workflows, expose progress via observables, and collect structured user input through form/wizard models. Persist with versioned snapshots and migrations so long-lived work sessions survive upgrades.

[Back to Table of Contents](#table-of-contents)
