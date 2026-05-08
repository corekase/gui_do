# gui_do — Developer Manual

## Title and Purpose

This manual is the primary learning and reference source for **gui_do**, a data-driven Python GUI framework built on top of pygame. It covers every major system the framework exposes, from first principles through advanced composition patterns, and is designed to be read cover-to-cover by newcomers or consulted chapter-by-chapter by experienced users seeking API details. The intended audience is developers who want to build non-trivial graphical applications with gui_do — people who need to understand not just what the API is, but why it is designed the way it is, how the pieces fit together, and where the boundaries of the framework lie. This manual replaces the need to read framework source code in order to understand purpose and design; the source code remains the authority for implementation detail, but this document provides the working mental models that make the source code comprehensible.

---

## Table of Contents

- [Title and Purpose](#title-and-purpose)
- [How to Use This Manual](#how-to-use-this-manual)
  - [Reading Paths](#reading-paths)
  - [Tri-Lens Markers](#tri-lens-markers)
  - [Contract Alignment](#contract-alignment)
- [Known Non-Goals](#known-non-goals)
- [Conceptual Foundations](#conceptual-foundations)
  - [Data-Driven Design](#data-driven-design)
  - [Reactive Data and Observable State](#reactive-data-and-observable-state)
  - [Feature Composition and Lifecycles](#feature-composition-and-lifecycles)
- [Quickstart Path](#quickstart-path)
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
  - [A: Glossary](#a-glossary)
  - [B: Lifecycle and Event Sequence](#b-lifecycle-and-event-sequence)
  - [C: System Dependency Map](#c-system-dependency-map)
  - [D: API Quick Index](#d-api-quick-index)
  - [D.1: Tier Matrix](#d1-tier-matrix)
  - [D.2: Selection Heuristics](#d2-selection-heuristics)
  - [E: Architecture Templates](#e-architecture-templates)
  - [F: Specifications and Option Reference](#f-specifications-and-option-reference)

---

## How to Use This Manual

[Back to Table of Contents](#table-of-contents)

This manual is organized to serve three distinct audiences simultaneously: developers learning gui_do for the first time, developers building applications who need system-level API references, and maintainers who revisit the codebase after intervals and need to orient themselves quickly. The material is arranged so that earlier sections establish the conceptual vocabulary and mental models that later sections assume. If you read the Conceptual Foundations chapter first, every system chapter will be easier to absorb because the motivations behind design decisions will already be clear.

### Reading Paths

**Beginner path** — If you are new to gui_do and have not yet built anything with it, follow this sequence: read the Conceptual Foundations chapter first, in its entirety. This chapter is long deliberately; it contains the theoretical models that everything else builds on. Then read the Quickstart Path to see those concepts in action at small scale. Then read the Architecture and Runtime Model chapter and the Core Workflow chapter to understand how the framework executes at runtime. After that, read system chapters 8.1 and 8.2 (Bootstrap and Feature Lifecycle) in full, because every feature you write will exercise those systems. Work through the remaining system chapters as you encounter the corresponding system in your own development work. The Integration Patterns chapter and End-to-End Reference become useful once you have implemented two or more features and want to understand how they compose.

**Intermediate path** — If you are familiar with pygame and with event-driven GUI programming but are new to gui_do specifically, start with the Conceptual Foundations chapter but read it as a diff: focus on what gui_do's approach differs from frameworks you already know. The subsections on data-driven design, reactive state, and feature lifecycles describe design choices that are specific to gui_do and may not match your intuitions from other frameworks. Then jump directly to the system chapter that covers the feature you are trying to build. Cross-reference the Integration Patterns chapter for multi-system composition patterns.

**Maintainer path** — If you are a developer who has worked with gui_do before and is returning to update, audit, or extend the codebase, begin with the Maintainer Diff Checklist in the Testing chapter. That checklist describes exactly what to look for when the codebase has changed. Then consult Appendix D.1 (Tier Matrix) to understand what is currently exported at each tier. Use Appendix D (API Quick Index) to find current function and type names quickly. Each system chapter's "Primary Public APIs and Key Types" subsection gives a compact reference to what that system exposes. The Conceptual Foundations chapter is stable and rarely needs to be re-read unless the framework's design philosophy has changed.

### Tri-Lens Markers

Some sections in this manual are marked with one of three lenses to help you read at the right level of abstraction:

- **[Theory]** — explains the underlying design principle or mental model. Read these when you want to understand why something works the way it does, not just how to call it.
- **[Practice]** — explains how to use a system to accomplish a task. Read these when you are actively building and need concrete steps.
- **[Reference]** — lists types, functions, parameters, and behaviors precisely. Consult these when you need exact API names or behavioral guarantees.

Not every section carries an explicit marker; many combine all three lenses naturally. The markers appear where the distinction is most useful for navigation.

### Contract Alignment

Several behavioral guarantees in this manual are backed by normative contract documents in the `docs/` directory of the repository. When this manual states something is guaranteed or deterministic, that statement traces to a contract document. The primary contracts are:

- `docs/runtime_operating_contracts.md` — scheduler budget values, restore report fields, determinism guarantees, and cross-system behavioral contracts.
- `docs/public_api_spec.md` — tier structure, stability policy, and consumer import rules.
- `docs/architecture_boundary_spec.md` — rules governing what the library layer may and may not depend on from the demo layer.
- `docs/event_system_spec.md` — event dispatch semantics and phase definitions.
- `docs/package_contracts.md` — package-level boundaries and import rules.

When you encounter behavior that appears to contradict this manual, check the contract document first. If the contract and the manual differ, the contract document takes precedence; file an issue against the manual.

---

## Known Non-Goals

[Back to Table of Contents](#table-of-contents)

Understanding what gui_do deliberately does not do is as important as understanding what it does. The following are explicit non-goals — areas where the framework intentionally offers no support, where alternative tools are more appropriate, or where the design philosophy actively resists a feature.

- **Web or mobile deployment.** gui_do targets desktop applications running natively on Windows, macOS, and Linux via pygame. It does not compile to JavaScript, WebAssembly, or mobile platform APIs. If web or mobile deployment is required, a different framework is the right choice.

- **Retained-mode scene graph with automatic dirty tracking.** gui_do controls are drawn on every frame (or on demand via dirty-region tracking when enabled). The framework does not maintain a persistent retained-mode tree that automatically determines the minimal repaint set. Dirty-region support exists as an opt-in optimization but is not the default draw model.

- **Native OS widget integration.** gui_do renders all UI elements itself via pygame surfaces. It does not wrap native operating system widgets (Win32 controls, AppKit views, GTK widgets, etc.). Applications built with gui_do look and behave consistently across platforms because the rendering is entirely self-contained.

- **A declarative markup language (HTML/XML/QML equivalent).** Specs are Python data structures, not a separate markup syntax. There is no template language, no GUI designer that generates markup, and no runtime that parses XML. This is intentional: keeping specs in Python means they benefit from type checking, refactoring tools, and normal Python testing infrastructure.

- **Automatic layout for arbitrary content.** gui_do provides powerful layout engines but they require explicit configuration. It does not perform browser-style automatic flow layout where arbitrary nested content determines container size. Applications must use the layout engine APIs to describe their intended spatial organization.

- **Networking, cloud, or server-side rendering.** The framework provides no built-in networking, HTTP client, or remote rendering capabilities. Applications that require network connectivity should use Python's standard library or dedicated networking libraries alongside gui_do.

- **A widget library pre-populated with platform-style themes.** gui_do ships with a theming system and a set of design tokens, but it does not ship platform-native theme implementations (Material Design, Fluent, macOS Aqua, etc.). The visual style is intentionally neutral and application-specific.

---

## Conceptual Foundations

[Back to Table of Contents](#table-of-contents)

The Conceptual Foundations chapter exists to give you the mental models that make every other part of gui_do legible. The framework makes design choices that may seem unusual if you are coming from an imperative GUI toolkit — things like expressing application structure as data rather than as code, making values reactive by default rather than by exception, and organizing application behavior into self-contained lifecycle objects rather than into a monolithic application class. These choices are not arbitrary. They serve specific, principled goals: testability, separation of concerns, resilience to internal code reorganization, and a clean boundary between what a developer describes and what the framework executes. If you understand the three theoretical pillars in this chapter, you will find that every system chapter, every API signature, and every architectural pattern in gui_do has a straightforward explanation that traces back to one or more of those pillars. If you skip this chapter, the API will feel like a collection of arbitrary conventions with no underlying logic. Read it first.

---

### Data-Driven Design

[Back to Table of Contents](#table-of-contents)

**What it means.** Data-driven design is the principle of separating the description of what a program should do from the code that carries out those actions. In practical terms, it means that application structure — the set of scenes, the features active in each scene, the windows each feature manages, the keyboard shortcuts it responds to, the actions it makes available — is expressed not as a sequence of imperative function calls scattered throughout the codebase, but as configuration data assembled in one deterministic pass. The runtime receives that data and performs all wiring automatically. A developer working with gui_do never calls "register this keyboard shortcut with the input system" directly; instead, they declare that shortcut in a spec object and hand that spec to the builder. The framework reads the spec and does the registration, the routing, the cleanup, and the teardown — everything mechanical is delegated to the runtime, leaving the developer free to express intent.

This philosophy runs deeper than a surface-level preference for configuration files over code. Data-driven design is a claim about what belongs where: the structure of an application (its scenes, its features, its input bindings, its persistence policy) is structural data. The runtime behavior of those scenes and features (what an animated bouncing shape does every frame, how a Mandelbrot explorer reacts to a zoom gesture, how a settings panel validates its form) is imperative behavior that only a developer can write. The framework's job is to read structure and execute the mechanical parts; the developer's job is to write behavior. Keeping those two things in separate layers makes both independently comprehensible and independently testable.

**The spec pipeline.** The entry point for building a gui_do application is `HostApplicationBindingSpec`, a data class that aggregates all the other binding specs that describe your application: which features exist at the scene level, what scenes are available, what actions they expose, what windows each feature manages, what cursors to show in different contexts, and more. You populate this binding spec with instances of types like `FeatureSpec`, `RuntimeSceneSpec`, `ActionSpec`, `WindowSpec`, `AnchoredWindowSpec`, and dozens of others — each of which is a pure data class with named fields. Once you have assembled your binding spec, you pass it to `build_host_application_config`, which performs a single deterministic pass over the entire spec tree: resolving cross-references between features and their windows, validating that required relationships are satisfied, and producing a fully wired `HostApplicationConfig`. That config object is then passed to `bootstrap_host_application`, which starts the event loop and hands control to the runtime.

This two-step design — build config first, then run — is deliberate. The build step produces an artifact that can be inspected in tests without ever starting a display window. You can assert that the correct features are registered, that the correct actions are wired, and that the scene structure is as expected, all in a unit test that runs in milliseconds. The run step is the only place where pygame's event loop is involved. Separating these two phases means that the structural correctness of your application is always independently verifiable, and refactoring the structure of your application never requires running the whole application to check that nothing broke.

**How it differs from imperative wiring.** Consider a concrete case: adding a keyboard shortcut that opens a settings panel. In a traditional imperative approach, this requires finding the event-handling code for the relevant scene, inserting a new conditional branch that checks for the key combination, calling a function that makes the panel visible, and adding corresponding cleanup code to the scene-exit handler so the shortcut is deregistered when the scene changes. If the shortcut should only be active when the settings window is focused, additional branching is needed in the focus-handling code. All of this is spread across multiple files and is maintained by whoever happens to remember where everything is.

In gui_do, the developer adds one `ActionSpec` to the `RoutedRuntimeSpec` for the scene, specifying the action name, the label, and the key binding. The framework picks up that spec during the build pass, registers the action with the `ActionRegistry`, routes the key through the `InputMap`, and when the scene exits, tears everything down automatically. The developer never touches the router. They never insert conditional branches. They never write cleanup code for the shortcut. The framework handles all of that because the spec declared the intent; the framework knew what the intent required.

**Reorganization without bootstrap impact.** One of the most practically important consequences of data-driven design is that internal code reorganization is completely transparent to the bootstrap layer. When a feature's implementation grows large enough that it makes sense to split it into a main feature class, a presenter class, a logic companion, and a standalone data type, all of that splitting happens inside the feature's package. The `__init__.py` of that package continues to export the same public names — the feature class, any public spec types — and the bootstrap code, which only imports from that `__init__.py` surface, is completely unaware that anything changed internally. The bootstrap is insulated from structural changes inside the package because it consumes public class references and spec values, not file paths or internal module locations.

This matters in practice because applications grow over time, and the most common form of growth is discovering that a piece of code that started small needs to be reorganized to stay maintainable. In a framework that couples bootstrap code to internal file structure, that reorganization breaks bootstrap references and requires coordinating changes across multiple files. In gui_do, internal reorganization is a local concern. As long as the public surface of a feature package does not change, nothing outside that package is affected. This property is a direct consequence of the data-driven principle: the data that drives the application (spec objects and class references) is assembled in one place, and all other code depends on that assembly — not on the internal structure of the packages it assembles.

**Testability.** Data-driven design makes gui_do applications trivially testable at multiple levels. Because specs are pure Python data classes, they can be constructed and validated in unit tests that never touch a display or an event loop. Because `build_host_application_config` is a pure function from spec to config, you can test that the build step produces the expected config without running any rendering code. Because feature instances receive their dependencies through a host interface rather than constructing them internally, they can be given mock hosts in tests that provide only the dependencies being exercised. The entire app config can be assembled and inspected in a test that runs in under a millisecond, giving you a continuous safety net against structural regressions.

The test suite for gui_do itself demonstrates this extensively: the majority of tests that cover application structure and routing never start a pygame display window. They build specs, call builders, inspect the resulting config, or construct feature instances with minimal mock hosts. This is only possible because the data-driven architecture keeps structure and behavior in clearly separated, independently instantiable layers.

**Specs as serialization boundary.** Because specs are pure data — frozen dataclasses with named fields and no behavior beyond data storage — they occupy a natural position as a serialization boundary. In principle, a spec tree could be stored to disk, loaded back, and passed to `build_host_application_config` to reconstruct the application. In practice, gui_do does not ship a spec serializer (see Known Non-Goals), but the architecture does not preclude it. Named fields make specs self-documenting: a `ShortcutOverlaySpec` with fields `scene_name`, `key`, and `entries` conveys its purpose in the type system itself. New optional fields added to specs in future versions do not break existing callers, because Python dataclass optional fields with defaults are backwards compatible. A positional-argument API cannot offer the same stability guarantee — adding a new parameter changes all call sites.

**Where the boundary is.** It is worth being precise about what is and is not data-driven in gui_do. The wiring of the application — which features exist, how they are connected to scenes and windows, what actions are available, how input is routed, what persistence policy applies — is data-driven. The runtime behavior of individual features — what they compute in `on_update`, how they respond to events in `handle_event`, what they draw in `draw` — is imperative Python code inside feature methods. The framework does not try to make behavior declarative; it confines the declarative approach to structure. The philosophy is: describe structure declaratively, implement behavior imperatively. The framework is responsible for making the structure correct; the developer is responsible for making the behavior correct. Each is independently verifiable and independently maintainable.

---

### Reactive Data and Observable State

[Back to Table of Contents](#table-of-contents)

**What reactive data means.** Reactive programming is a style in which values automatically propagate their changes to anything that depends on them, without the producer needing to know who the consumers are. In a conventional imperative GUI application, a developer who wants to show the current item count in a label must write code that updates the label every time the count changes: add an item, update the label; remove an item, update the label; clear all items, update the label. This works, but it couples the data-management code to the display code. Every place that modifies the count must also be aware of every display element that shows it, and must remember to update each one. As applications grow, this coupling produces code that is difficult to reason about because any modification to data has implicit side effects scattered throughout the codebase.

In a reactive model, the count is not a plain integer — it is an observable value that notifies all its subscribers whenever it changes. The label subscribes once, at initialization time, and is notified automatically whenever the count changes, regardless of what caused the change. The code that modifies the count has no knowledge of the label; the label has no knowledge of which code modifies the count. The observable value is the only point of coupling, and that coupling is explicit, typed, and unidirectional. This is not merely an implementation detail; it is an architectural guarantee that makes large applications tractable by ensuring that data flows in a single, auditable direction.

**The observable primitives.** gui_do provides three foundational observable types that together cover almost all reactive state patterns. `ObservableValue` wraps a single typed value. Any object can call `.subscribe(callback)` on an `ObservableValue` and will be notified every time the value is changed via `.set()`. The callback receives the new value as its argument. Subscription returns a token that the subscriber can use to unsubscribe later, which is essential for preventing memory leaks.

`ObservableList` and `ObservableDict` extend the reactive model to mutable collections. They behave like Python's built-in `list` and `dict` types but emit structured change notifications — `CollectionChange` objects of type `ChangeKind` — whenever elements are added, removed, updated, or reordered. Subscribers can react to the specific kind of change rather than re-evaluating the entire collection state. This is important for performance when collections are large: a subscriber that only needs to handle item additions can ignore removal events without inspecting the entire list.

Beyond these three primitives, `ComputedValue` provides a derived observable that automatically recomputes itself from one or more source observables whenever any of them changes. A `ComputedValue` is the cleanest way to express a value that should always equal some function of other observable values — for example, a label text that should always read "N items selected" where N comes from an observable selection count. Rather than manually subscribing to the count and writing to a second observable, you declare the derivation once and the framework handles propagation. Unlike a manually maintained derived observable, a `ComputedValue` cannot get out of sync with its sources because the framework recomputes it automatically.

**Batching with `reactive_batch` and `is_batching`.** When multiple observable values are modified in a single logical operation — for example, initializing a dozen fields of a form model from a loaded file — it is inefficient and potentially incorrect for subscribers to fire once per assignment. `reactive_batch` is a context manager that defers all subscriber notifications until the batch completes, then fires each affected subscriber exactly once. Inside the batch, `is_batching()` returns `True`, which can be used by code that needs to know whether it is executing in a batch context. Batching is particularly important in `bind_runtime` when initializing many observables simultaneously: without batching, each assignment triggers a separate rendering pass; with batching, a single rendering pass processes all changes together.

**Subscription lifecycle and cleanup.** The most common source of bugs in reactive systems is subscription leaks: callbacks that continue to fire after the object that registered them has been destroyed. In gui_do, the correct places to subscribe are `bind_runtime` (for feature-level subscriptions to observables owned by sibling features or shared state) and feature constructors when the subscription should persist for the feature's entire lifetime. The correct place to unsubscribe is the feature's shutdown or teardown path, which varies by feature type but is always called when the feature is removed from its scene. Every call to `.subscribe()` returns a token; store that token and call its unsubscribe method (or pass it to a cleanup context) during teardown. Never discard subscription tokens — a dropped token is a guaranteed leak.

Failing to unsubscribe has two failure modes. The first is a memory leak: the observable holds a strong reference to the callback, which holds a reference to the feature, so the feature cannot be garbage collected even after its scene exits. The second is a phantom callback: the observable fires the callback on a feature that no longer exists in any meaningful sense, potentially causing it to write to controls that have been removed or to access host resources that are no longer valid. Both failure modes are silent and produce intermittent, difficult-to-diagnose bugs. The discipline of always pairing subscribe with unsubscribe is not optional.

**How controls bind to observable state.** Controls in gui_do generally accept either a plain value or an observable for properties like text content, visibility, and enabled state. When a control receives a plain value, it uses that value as a static initial state. When a control receives an `ObservableValue`, it registers an internal subscription and refreshes its display automatically whenever the observable changes. This means that feature code responsible for updating the display never needs to interact with a control directly after binding; it only changes the observable. The control reacts automatically.

This design keeps feature code decoupled from specific control implementations. A feature that manages a count observable does not know or care whether that count is displayed in a `LabelControl`, a `RichLabelControl`, a `ProgressBarControl`, or some future control type. Changing which control is used to display the count requires only a change in the `build` method where the control is created; the binding, the data model, and the feature logic are completely unchanged. This decoupling is one of the most practical benefits of the reactive model in GUI development.

**Cross-feature reactive state.** Observable values are the preferred mechanism for features to share live data with each other. The pattern is simple: one feature owns an `ObservableValue` and exposes it as part of its public interface (either directly or through a presentation model). Other features that need to display or react to that value access the owning feature through the host and subscribe to the observable in their `bind_runtime` method. This happens after all features in the scene have completed their `build` phase, so all features and their observables are available at the time subscriptions are established.

The producing feature never knows who is observing its observable. The consuming feature does not depend on the producing feature's internal implementation — it only needs the observable reference. If the producing feature's internal logic changes completely, the consuming feature is unaffected as long as the observable it subscribed to continues to be updated correctly. This loose coupling, enforced by the observable layer, is what makes it practical to compose many features in a single scene without any of them becoming tangled together.

**Anti-patterns.** Several reactive patterns are seductive but harmful, and it is worth naming them explicitly because they are common mistakes for developers new to reactive design. Polling an observable in `on_update` — checking its value every frame to see if it has changed — is the most common mistake. This eliminates the efficiency advantage of subscriptions (the notification fires only when the value changes) and introduces latency (the change is not visible until the next frame's update call). It is always correct to subscribe instead; polling is never necessary.

Subscribing to observables in the `build` method, before the runtime phase begins, is another common mistake. Controls do not yet exist and the scene is not yet fully constructed during `build`. A subscription established here may fire before the subscriber's controls are ready to receive updates, producing null-reference errors or rendering artifacts. Always subscribe in `bind_runtime`, which is called after all controls are constructed and all features are built.

Sharing mutable plain Python objects across features instead of observables is a subtler anti-pattern. If two features share a reference to a plain Python list, they can read and write it freely, but there is no notification mechanism: a change made by one feature is invisible to the other until the other decides to check. This breaks the reactive contract and requires manual synchronization (polling in `on_update`, or explicit method calls between features) that reintroduces the coupling that reactive design is meant to eliminate. If data is shared across features, it should be shared as an observable type so that changes propagate automatically.

---

### Feature Composition and Lifecycles

[Back to Table of Contents](#table-of-contents)

**What a Feature is.** A Feature is the primary unit of application behavior in gui_do. It is a self-contained object that owns one cohesive slice of an application's functionality: it declares what resources it needs from the host environment, builds its own UI controls in the scene's control tree, registers its own event handlers, manages its own data model, and tears everything down cleanly when its scene exits. Features are composable in the sense that a complete application is a collection of features that coexist in scenes, each managing its own portion of the UI and its own state. No feature needs to know about the other features in its scene; the framework manages their coexistence, dispatches events to the appropriate feature, and orchestrates their lifecycle phases in the correct order.

This design is a deliberate departure from the monolithic application class pattern common in pygame tutorials. In a typical pygame application, there is one large game loop with one update function, one draw function, and one event handler, all of which grow without bound as the application grows. Features solve this by providing a stable unit of decomposition: each independent piece of application functionality gets its own Feature, which has its own clearly bounded lifecycle methods and its own clearly bounded control tree. The framework provides the scaffolding that makes these independent units work together safely.

**Feature types and when to use each.** gui_do provides four feature base classes, each suited to a different composition role. Understanding which to use for a given purpose is the first practical skill for building gui_do applications.

`DirectFeature` is the lowest-overhead feature type. It renders directly to the screen surface on every frame by overriding the `draw` method, and it does not participate in the control tree, focus management, or hit-testing. Use `DirectFeature` for elements that cover the entire screen background — animated backdrops, particle effects, full-screen visual demonstrations, or any content that does not need to be clickable or focusable. Because `DirectFeature` bypasses the control tree entirely, it has minimal framework overhead: the framework only calls its lifecycle methods and its `draw` call, with nothing in between.

`Feature` is the standard feature type and is correct for the majority of application functionality. A `Feature` builds controls in the scene's control tree during its `build` phase. Those controls participate in focus management, keyboard navigation, hit-testing, and event routing. Any feature that needs to show interactive UI — buttons, labels, sliders, text inputs, windows, panels — should be a `Feature`. The control tree ensures that user input reaches the correct control and that the accessibility tree reflects the current UI state.

`LogicFeature` has no UI of its own. It exists to hold domain logic, manage shared state, run background computations, and publish results that other features consume reactively. A `LogicFeature` has the same lifecycle phases as a `Feature` — `build`, `bind_runtime`, `handle_event`, `on_update` — but its `build` phase typically creates no controls. Use `LogicFeature` when you want to test behavior in complete isolation from presentation, when a computation is too expensive or complex to run inline in a UI feature's `on_update`, or when multiple UI features need to share the same data source. The `LogicFeature` owns the data model; UI features subscribe to it and render it.

`RoutedFeature` is a `Feature` that additionally participates in the action routing infrastructure. It can define named route targets — handler methods that receive messages dispatched by the framework's action system. Use `RoutedFeature` when a feature must respond to framework-level actions (such as receiving a notification that a menu command was triggered), when it needs to receive messages published by sibling features, or when it is part of a tabbed presentation model where the active-tab routing system dispatches update messages to whichever feature is currently visible. The routing infrastructure that `RoutedFeature` integrates with is the same infrastructure driven by `ActionSpec` declarations in the application config.

**Lifecycle phases in depth.** Every feature class participates in a structured lifecycle that the framework manages. Each phase has a specific purpose, and using phases for the wrong purpose is the most common source of subtle bugs in gui_do applications.

`build(host)` is called once when the scene is being constructed, before the event loop has started. This is the phase for creating controls, adding them to the scene's control tree (via the host's layout manager or scene presentation model), building window specs, and setting up any static structure that does not change over the feature's lifetime. Controls created during `build` persist for as long as the feature's scene is active. The `host` object provides all resources declared in `HOST_REQUIREMENTS` for the build phase. Do not subscribe to observables in `build` — the sibling features may not yet have completed their own build phase, so their observables may not exist yet.

`bind_runtime(host)` is called after every feature in the scene has completed its `build` phase. This is the phase for subscribing to observable values (from sibling features, shared state stores, or the app's observable properties), binding controls to data models, registering callbacks that should fire when observable state changes, initializing state from runtime sources (such as screen dimensions, user settings, or persisted workspace state), and wiring cross-feature interactions. By the time `bind_runtime` is called, all controls exist and all sibling features are fully built, so it is safe to access any feature's observables and any control in the scene tree.

`handle_event(host, event)` is called for every `GuiEvent` that reaches the feature. The routing layer filters events by scene, focus state, overlay state, and action scope before calling this method, so features generally only see events that are relevant to them. A feature returns `True` to consume the event — which stops further routing down the handler chain — or returns `False` or `None` to pass it on. Use `handle_event` for input that the control tree cannot handle automatically (custom keyboard shortcuts, gesture recognition, drag-and-drop coordination, canvas interactions) and for reacting to event types that are not handled by any control in the feature's tree.

`on_update(host, dt_seconds)` is called once per frame, before drawing. The `dt_seconds` parameter is the elapsed time in seconds since the last frame. Use this phase for time-based animations, timer checks, polling for results from background computations (via `CooperativeScheduler` or `AsyncDataProvider`), and any per-frame state updates that are not event-driven. Keep `on_update` fast: it is called on every frame, and expensive computation here will directly degrade the application's frame rate. If a computation is too expensive to run every frame, use `CooperativeScheduler` to spread it across multiple frames.

`draw(host, screen)` is called once per frame, after `on_update`, for features that need to draw directly to the pygame screen surface. The `screen` parameter is the pygame `Surface` for the current display. Use this phase for custom rendering that bypasses the control tree entirely: particle systems, canvas effects, custom chart rendering, procedural graphics. Most features that use the control tree do not need to override `draw` — the framework handles drawing controls through the control tree. `DirectFeature` uses `draw` as its primary rendering method.

**The `HOST_REQUIREMENTS` protocol.** `HOST_REQUIREMENTS` is a class-level dictionary that declares what attributes the host must provide for each lifecycle method. A feature declares its requirements like this:

```python
HOST_REQUIREMENTS = {
    "build": ["app", "screen_rect", "scene_presentation", "layout_manager"],
    "bind_runtime": ["app", "screen_rect", "my_logic_feature"],
}
```

The framework reads this dictionary at startup and validates that all declared requirements are satisfied before calling the corresponding lifecycle method. If a requirement is not met — for example, because a feature attribute name is misspelled in the binding spec — the framework raises a clear error that names the missing attribute and the feature that needs it, rather than producing a confusing `AttributeError` deep in the feature code. This protocol replaces the anti-pattern of features internally constructing their own dependencies (which makes them hard to test) and the anti-pattern of receiving many arguments through the constructor (which makes spec-driven composition awkward). Instead, each feature declares its dependencies precisely and the framework ensures they are available.

**Feature messaging and coordination.** Features do not hold direct references to each other. The framework does not provide a feature-to-feature calling API; direct references would create tight coupling that makes testing difficult and scene transitions error-prone. Instead, features communicate through `FeatureMessage` publishing. A feature publishes a message by name with an optional payload; the framework delivers it to any feature in the scene that has registered a handler for that message name. The publishing feature does not know who receives the message; the receiving feature does not know who sent it.

This is the correct loose-coupling mechanism for cases where a feature needs to trigger behavior in another feature without knowing its type or implementation details. Common patterns include a `LogicFeature` publishing a `"data_ready"` message when a background computation finishes (so that multiple UI features can refresh simultaneously), a `RoutedFeature` listening for a `"selection_changed"` message to update its detail view, and features using message publishing for cross-scene coordination when observable state alone is not sufficient. For tighter coupling where one feature genuinely owns shared state that others consume, observable state (described in the previous section) is often cleaner than messaging because it does not require the producing feature to know when to publish.

**Scene assignment and multi-scene composition.** Each feature belongs to exactly one scene, declared via its `scene_name` attribute in the `FeatureSpec` or equivalent binding. The framework activates and deactivates features as scenes transition. When a transition to a new scene is triggered, the framework calls the departing scene's features' teardown paths first, then calls `build` and `bind_runtime` on the arriving scene's features. Features from the previous scene receive no further events, update calls, or draw calls after the transition completes. This is a safety guarantee: stale state from one scene cannot leak into another because the framework ensures that departing features are fully quiesced before arriving features begin their lifecycle.

Multi-scene applications compose naturally with this model. Each scene is an independent collection of features that knows nothing about the features in other scenes. Shared state that must persist across scene transitions is managed either in global features (features that belong to no scene and are always active) or in the workspace persistence system (which saves and restores state between sessions). Navigation between scenes is handled through `ActionSpec` entries and the `SceneTransitionManager`, both of which are data-driven and require no imperative wiring.

**The folder and package composition convention.** For any non-trivial application built with gui_do, the established organizational convention is that each feature lives in its own package (a folder with an `__init__.py`). The `__init__.py` of that package is the sole public surface: it exports the feature class and any public types, and nothing else. Internal implementation files are named by concern: the file ending in `_feature.py` owns the `Feature` subclass and its lifecycle methods; the file ending in `_presenter.py` owns the `WindowPresenter` subclass that handles window layout; the file ending in `_specs.py` owns shared constants and spec objects; files ending in `_logic_feature.py` own `LogicFeature` companions that handle background computation; standalone data types that are shared across files within the package live in their own files.

This convention has a specific, deliberate consequence: bootstrap code that imports from a feature package only ever imports from the package's `__init__.py`. It imports the feature class, instantiates it, and puts it into a spec. It never imports from `my_feature.my_feature_presenter` or `my_feature.my_feature_specs` directly. This means that any reorganization inside the feature's package — splitting files, renaming internal modules, extracting a new companion — is completely invisible to the bootstrap code. The only commitment the feature package makes to the outside world is its `__init__.py` surface, and that surface rarely needs to change even when the internal implementation changes significantly.

**Composition patterns.** The three most common multi-feature composition patterns in gui_do are worth naming explicitly because they appear throughout the framework's own demo features and should be applied in similar situations in user code.

The logic-and-presentation split is the cleanest separation for computationally intensive features. A `LogicFeature` handles all domain logic — data loading, background computation via `CooperativeScheduler`, state management, result publishing — and exposes its results as observable values. A `RoutedFeature` (or `Feature`) subscribes to those observables in `bind_runtime` and drives the UI accordingly. Neither component contains the other's concerns. The `LogicFeature` can be tested entirely without any controls or rendering; the `RoutedFeature` can be tested by giving it a mock `LogicFeature` with observable test values.

The presenter pattern is used when a feature's window layout is complex enough to warrant its own class. A `WindowPresenter` subclass handles the construction and layout of all controls within a window, while the feature class handles the feature lifecycle and routing. The feature lazily imports the presenter in its `build` method to avoid circular imports between the feature and presenter files. The presenter creates controls and registers them with the window; the feature accesses those controls through the presenter interface.

The background-feature pattern applies when a long-running computation must proceed without blocking the event loop. A `LogicFeature` creates a `CooperativeScheduler` and registers coroutines that advance the computation in small slices each frame, respecting the scheduler's time budget. The results of each slice are published to observables. A UI feature subscribes to those observables and displays progress in real time. The Mandelbrot demo feature in `demo_features/mandelbrot/` is the canonical example of this pattern in the gui_do codebase.

---

## Quickstart Path

[Back to Table of Contents](#table-of-contents)

This chapter gives you a direct, practical path from first installation to a working application. It is intentionally hands-on and concrete. The Conceptual Foundations chapter explains why everything works the way it does; this chapter tells you how to do it. Read the two chapters together: every step here has a "why" that the Conceptual Foundations chapter answers.

### Step 1: Install and Verify

Install gui_do in editable mode from the repository root. The `--no-deps` flag assumes you have already installed `pygame` and `numpy` separately; remove it if you want pip to install dependencies automatically. `numpy` is used internally for pixel-buffer operations via `PixelArray`.

```bash
python -m pip install -e . --no-deps
python -m pytest -q tests/test_public_api_exports.py
```

If the test passes, the public API surface is intact and your environment is correctly set up. If any imports fail, check that your Python environment has `pygame` installed and that you are running from the repository root.

### Step 2: Create a Minimal Host

The entry point for any gui_do application is `build_host_application_config`, which takes a `HostApplicationBindingSpec` and produces a `HostApplicationConfig`. You then pass the config to `bootstrap_host_application` to start the application. Here is the minimal structure:

```python
from gui_do import (
    HostApplicationBindingSpec,
    SceneBundleBindingSpec,
    ActionBindingSpec,
    build_host_application_config,
    bootstrap_host_application,
)

config = build_host_application_config(
    HostApplicationBindingSpec(
        display_size=(1280, 720),
        window_title="My App",
        fonts={
            "default": {"file": "assets/fonts/MyFont.ttf", "size": 14},
        },
        initial_scene_name="main",
        scene_bundle_entries=(
            SceneBundleBindingSpec(
                scene_name="main",
                pretty_name="Main",
                include_nav_action=False,
            ),
        ),
        feature_entries=(
            ("_my_feature", MyFeature),
        ),
        action_entries=(
            ActionBindingSpec(kind="exit", action_id="exit", label="Exit", category="File"),
        ),
    )
)

app = bootstrap_host_application(config)
app.run_entrypoint(target_fps=120)
```

The key fields to understand are `display_size` (the initial window dimensions), `initial_scene_name` (which scene is shown on startup), `scene_bundle_entries` (the set of available scenes), `feature_entries` (the features active in the application), and `action_entries` (the actions the application recognizes). All other fields have sensible defaults.

### Step 3: Add a Feature with Observable State

A feature creates its controls in `build` and wires them to data in `bind_runtime`. Here is a minimal feature that displays a reactive label:

```python
from gui_do import Feature, ObservableValue, LabelControl

class MyFeature(Feature):
    HOST_REQUIREMENTS = {
        "build": ["layout_manager"],
        "bind_runtime": [],
    }

    def __init__(self):
        super().__init__(scene_name="main")
        self._count = ObservableValue(0)
        self._label: LabelControl | None = None
        self._sub = None

    def build(self, host):
        self._label = LabelControl(text="Count: 0", rect=(100, 100, 200, 30))
        host.layout_manager.add(self._label)

    def bind_runtime(self, host):
        self._sub = self._count.subscribe(
            lambda v: self._label.set_text(f"Count: {v}")
        )

    def shutdown_runtime(self, host):
        if self._sub:
            self._sub()
            self._sub = None

    def on_update(self, host, dt_seconds):
        # Increment the count every second
        self._count.set(self._count.get() + 1)
```

Note that `bind_runtime` subscribes to the observable and updates the label whenever the observable changes. The `shutdown_runtime` method disposes the subscription to prevent memory leaks when the scene exits.

### Step 4: Add an Action and Runtime Scene Policy

Actions connect keyboard shortcuts to application behavior. A `RuntimeSceneSpec` describes per-scene startup policies, including whether the Escape key exits:

```python
from gui_do import (
    HostApplicationBindingSpec,
    SceneBundleBindingSpec,
    ActionBindingSpec,
    ActionHotkeySpec,
    build_host_application_config,
)

config = build_host_application_config(
    HostApplicationBindingSpec(
        # ...other fields...
        action_entries=(
            ActionBindingSpec(kind="exit", action_id="exit", label="Exit", category="File"),
            ActionBindingSpec(
                kind="custom",
                action_id="reset_count",
                label="Reset Count",
                category="Edit",
            ),
        ),
        # runtime_scene_entries can specify bind_escape_to_exit=True
        # inside each SceneBundleBindingSpec or via RuntimeSceneSpec
    )
)
```

For scene-level escape binding, use the `bind_escape_to_exit` parameter in a `RuntimeSceneSpec` or configure it through `RoutedRuntimeSpec`. The Escape key exit is the most common runtime policy applied at the scene level.

### Step 5: Run Loop

Once you have built your config, the run loop is a single call:

```python
app = bootstrap_host_application(config)
app.run_entrypoint(target_fps=120)
```

`run_entrypoint` owns the pygame event loop, calling update and draw on every registered feature at the specified target frame rate. It handles workspace save and restore across the application's lifetime and exits cleanly when the exit action fires. You do not need to write a `while True` loop.

### Guided Build Track (Beginner)

If you are building your first gui_do application and are not sure what order to tackle things in, follow these six milestones in sequence. Each milestone is a concrete, verifiable outcome that confirms a complete subsystem is working before you add the next one.

**Milestone A — App boots to a single scene with no errors.** Your config has one `scene_bundle_entries` entry, one feature in `feature_entries` with an empty `build` method, and a working font path. Run the app; it should display a blank window at the correct size. This confirms that the config build pass, the bootstrap, and the display setup are all correct.

**Milestone B — One feature creates one visible control.** Add one `LabelControl` in the feature's `build` method and add it to the layout manager. The label should appear on screen. This confirms that the build phase, the layout manager, and the draw pipeline are all working.

**Milestone C — One observable updates one control reactively.** Add an `ObservableValue` to the feature, subscribe to it in `bind_runtime`, and change its value in `on_update`. The label should update every frame. This confirms that the reactive subscription model is working correctly.

**Milestone D — One action and one hotkey trigger expected behavior.** Add an `ActionBindingSpec` to the config and add an `ActionHotkeySpec` binding a key to it. In the feature's `handle_event` method, check for the action event and respond. Pressing the key should trigger the response. This confirms that action registration, input mapping, and event routing are all working.

**Milestone E — One overlay and one toast route without input leakage.** Use a `ToastManager` to show a toast notification; use a `DialogManager` to show a modal dialog and confirm that keyboard input does not reach the underlying scene while the dialog is open. This confirms that the overlay and focus management systems are correctly configured.

**Milestone F — Workspace save/load roundtrip succeeds.** Use the `SettingsRegistry` to save one setting in the feature's teardown and load it in `bind_runtime`. Exit and relaunch the app; the setting should be restored. This confirms that the persistence system is configured and that the restore report includes the expected fields.

**Beginner confidence checklist.** Before moving to intermediate work, you should be able to answer yes to each of these:
- You can explain where `build` ends and `bind_runtime` begins, and why the split exists.
- You can add or remove one feature from the application by changing specs alone, without touching any other feature's code.
- You can trace a single keypress from the raw pygame event through the routing layer to the action that handles it.

### Quickstart Failure Modes

These are the four most common early failures and their specific fixes:

**Feature never appears on screen.** Verify that the feature's `scene_name` in its constructor matches the `scene_name` in the `scene_bundle_entries` entry for that scene, and that the feature appears in `feature_entries` (or `feature_window_bundle_entries` if it owns a window). A mismatch between scene names means the feature is built for a scene that does not exist.

**Hotkey does nothing.** Verify that the action ID in the `ActionBindingSpec` matches the action ID in the `ActionHotkeySpec` binding. Verify that the action's scope matches the context in which you press the key — an action scoped to a specific window only fires when that window has focus. Verify that the feature's `handle_event` method checks for the correct event type and action name.

**Overlay blocks unexpected keys.** An overlay that has `consume_unhandled_keys=True` set in its manager will absorb all keyboard events that reach it, preventing them from reaching the scene. If an overlay is open and your keys are not reaching their handlers, check the overlay manager's consume-unhandled-keys setting and verify that your feature is dismissing the overlay correctly before expecting scene-level key events to resume.

**State updates but UI does not.** This almost always means the subscription was established in `build` instead of `bind_runtime`, or the subscription token was discarded and garbage-collected before the subscription could fire. Verify that `self._sub = self._count.subscribe(...)` is called in `bind_runtime` and that the token is stored on `self` (not in a local variable). If the subscription is established correctly but the UI still does not update, verify that the control's text-setting method is being called with the correct value by adding a temporary `print` inside the subscription callback.

---

## Architecture and Runtime Model

[Back to Table of Contents](#table-of-contents)

The architecture of gui_do is organized around a clear separation between framework code and consumer code, a tiered public API that guides developers toward the correct level of abstraction, and a runtime that makes strong behavioral guarantees about event ordering, focus cycling, and scheduler budget consumption. Understanding this architecture helps you make correct design decisions about where code belongs and what guarantees you can rely on.

### Boundary Model: Framework vs Consumer

The gui_do codebase has a hard boundary between two layers. The `gui_do/` package is reusable framework code: it contains the runtime, all control implementations, the event system, the layout engines, the state and persistence systems, the theming infrastructure, and every other system described in the Main Systems Reference. The `demo_features/` directory and the `gui_do_demo.py` entrypoint are consumer code: they implement application-specific behavior by composing the framework's public APIs.

The critical rule is that `gui_do/` must not import from `demo_features/`. Framework code must remain usable independently of any specific application. Consumer code imports from the `gui_do` root package only — never from internal `gui_do.*` submodules. This rule ensures that the public API surface, defined by `gui_do/__init__.py`, is the only coupling point between the framework and its consumers. Changing the internal organization of the `gui_do/` package is safe as long as the public surface does not change.

This boundary is not a convention; it is enforced by automated tests. `tests/test_boundary_contracts.py` uses AST import inspection to verify that `gui_do/` does not import from `demo_features/`, and that consumer entrypoints use only root-package imports. Any violation of these rules causes the test suite to fail.

The practical implication for developers writing new applications is simple: import everything from `gui_do` at the root level (`from gui_do import Feature, ObservableValue, LayoutManager`). Never import from internal submodules like `gui_do.controls.input.button_control`. The root package exports everything that is part of the supported public surface.

### Tiered Public API Model

The `gui_do/__init__.py` file is organized into numbered tier sections. Each tier groups exports that serve a related purpose and are intended to be used at the same level of abstraction. The tier number is also the recommended approach order: when two tiers offer overlapping capability, the lower-numbered tier is more abstract, more stable, and should be preferred. Higher tiers are available when lower tiers are insufficient or when you are building low-level extensions to the framework.

**Tier 1: Primary entry points and data-driven APIs.** This is where new applications start. Tier 1 contains all the feature lifecycle base classes (`Feature`, `DirectFeature`, `LogicFeature`, `RoutedFeature`, `FeatureMessage`), all the spec types used to build application configs (`FeatureSpec`, `WindowSpec`, `RuntimeSceneSpec`, `ActionSpec`, `AnchoredWindowSpec`, and many others), the `HostApplicationBindingSpec`, `build_host_application_config`, and `bootstrap_host_application`. If you use only Tier 1 exports, you are using the framework at the intended level of abstraction.

**Tiers 2–7: Core runtime systems.** These tiers expose the managers and primitives that Tier 1 orchestrates on your behalf. Tier 2 provides `GuiApplication`, `create_display`, `SceneTransitionManager`, and `apply_scene_setup_specs`. Tier 3 provides the observable types: `ObservableValue`, `ObservableList`, `ObservableDict`, `ComputedValue`, `CollectionView`, `Binding`, and `reactive_batch`. Tier 4 provides the event and input system: `GuiEvent`, `EventType`, `EventPhase`, `EventManager`, `ActionManager`, `InputMap`, `FocusManager`, and the key chord manager. Tier 5 provides scheduling and animation: `TaskScheduler`, `TweenManager`, `AnimationSequence`, `TransitionManager`, `CooperativeScheduler`, and related types. Tier 6 provides theming and fonts: `ThemeManager`, `ColorTheme`, `FontManager`, `FontRoleRegistry`. Tier 7 provides telemetry: `TelemetryCollector`, `configure_telemetry`.

**Tiers 8 and above: Specialized systems.** These tiers provide layout engines, overlay managers, forms and validation, state and persistence, controls, graphics, audio, accessibility, introspection, and advanced bootstrapping helpers. They are intended for use when Tier 1 is not sufficient — for example, when you need to configure a custom layout engine, when you want to use a specific overlay manager directly rather than through the data-driven config, or when you are building advanced features that require low-level access to runtime internals.

The tier model is a reading guide as much as it is a grouping mechanism. When you encounter an unfamiliar export, its tier tells you how often you should expect to need it. Tier 1 exports appear in virtually every application. Tier 25 exports (`ServiceKey`, `ServiceScope`, `ScopeStack`) appear only in advanced dependency injection scenarios.

### Runtime Guarantees

The runtime operating contracts (`docs/runtime_operating_contracts.md`) define the behavioral guarantees that the runtime makes. These are not aspirational; they are enforced by automated tests. The guarantees relevant to understanding the architecture are:

**Canonical `GuiEvent` normalization.** All input from pygame — keyboard events, mouse events, window events, custom events — is normalized into `GuiEvent` objects before any application-level dispatch occurs. Features and controls always see `GuiEvent` instances, never raw pygame events. The `GuiEvent.clone()` method produces an independent copy: mutations to the clone (setting `propagation_stopped` or `default_prevented`) do not affect the original.

**Scene-isolated update execution.** Runtime systems that are scoped to a scene — feature update loops, scene-local timers, scene-local tween managers — are only executed when that scene is active. A feature in scene B does not receive `on_update` calls while scene A is active. This means that per-scene state does not advance during scene transitions, eliminating a whole class of bugs that arise from off-screen features continuing to accumulate state.

**Deterministic window focus cycling.** When the focus system cycles through focusable windows (for example, via Tab key), the candidate list is sorted by `control_id`. This sorting is deterministic and stable, so the focus order is always the same for the same set of visible windows. The `control_id` values are assigned when windows are created and do not change for the lifetime of the window.

**Scheduler dispatch budget clamping.** The `TaskScheduler` processes pending messages on each frame within a time budget that is clamped to fixed bounds: `fraction=0.12` of the frame's elapsed milliseconds, `floor=0.5 ms`, and `ceiling=4.0 ms`. This means the scheduler will consume at least 0.5 ms and at most 4.0 ms per frame for message dispatch, regardless of the actual frame time. This prevents both starvation (no messages processed on fast frames) and frame-rate destruction (all time consumed by messages on slow frames).

**Missing settings keys skipped during restore.** When the workspace persistence system restores a saved workspace, settings keys that do not exist in the current `SettingsRegistry` are silently skipped rather than raising errors. This makes it safe to rename or remove settings between versions of an application without corrupting restore behavior. The restore report (a structured dict returned by `WorkspacePersistenceManager.restore`) includes fields for `applied_settings`, `skipped_settings`, and `missing_settings_blocks`, allowing you to audit what was and was not restored.

### Event Pipeline

Understanding the order in which the runtime processes events helps you reason about why certain event handlers fire or do not fire in specific contexts. The `GuiApplication.process_event` pipeline processes each event in the following order:

1. **Normalize raw input to `GuiEvent`.** The raw pygame event is converted into a canonical `GuiEvent` with fully populated fields, normalized coordinates, and correct phase classification.
2. **Handle quit events early.** A pygame `QUIT` event triggers application shutdown immediately, before any other dispatch.
3. **Update shared input state.** The `InputSnapshot` is updated to reflect the current state of all keyboard keys and mouse buttons, making it available to features that poll input state rather than responding to events.
4. **Update logical pointer state.** The pointer manager updates its internal model (position, button states, capture state). Pointer lock and pointer capture clamping are applied here.
5. **Logicalize pointer events.** Pointer events are converted from raw screen coordinates to scene-relative logical coordinates, while raw coordinates are preserved on the event for cases where the raw position is needed.
6. **Route to overlay and focus management.** Overlays, dialogs, and focus managers get first look at events. This is where modal overlays consume events before they reach the scene, and where the focus manager updates keyboard focus in response to Tab presses.
7. **Route keyboard events through keyboard manager and screen handler policy.** Global key bindings (including the command palette activation key), then scene-level key handlers, then feature-level handlers, are evaluated in order.
8. **Route to feature handlers, scene dispatch, then fallthrough handlers.** Features with matching `handle_event` methods receive the event in priority order. `propagation_stopped` is checked between each handler; if set, routing stops immediately.
9. **Respect `propagation_stopped` and `default_prevented`.** These flags on the `GuiEvent` are hard stop signals. No handler downstream of a `propagation_stopped` event will receive it.

Understanding this pipeline is essential for debugging routing problems. If a feature never receives an event, work through this pipeline mentally: is the event being consumed by an overlay? Is a global key binding intercepting it? Is `propagation_stopped` being set by an earlier handler?

### Known Non-Goals (Architecture)

A few architectural commitments that the runtime intentionally does not make, to prevent misunderstanding of where the framework ends and application code begins:

- **No native OS widget parity.** The framework does not wrap native OS widgets and does not aim to match platform-native appearance or behavior precisely.
- **No business logic decisions.** The framework provides data and state primitives, but does not prescribe how application business logic should be structured beyond the feature lifecycle model.
- **No internal tier exposure as beginner entry points.** Tier 18 and above are documented as available when needed, not as the starting point for new applications. Beginner documentation focuses on Tier 1.
- **No star-import compatibility guarantees.** The `__all__` list is defined as a convenience, but star-import behavior is not part of the public API contract. Always use explicit named imports.

---

## Core Workflow: Build, Bind, Route, Update, Draw

[Back to Table of Contents](#table-of-contents)

Every feature in a gui_do application participates in a five-phase workflow: build, bind, route, update, and draw. These phases are not just API conventions; they are an architectural model that enforces the separation of concerns at the most granular level of feature implementation. Understanding when each phase runs, what invariants hold during it, and what belongs in it is the foundation of writing correct gui_do features.

### Phase Reference

**Build** is the construction phase. It runs once when the scene is assembled, before the event loop starts. During build, you instantiate controls, initialize local observable values, and set up any static structure that will not change during the feature's lifetime. Controls created during build exist for the lifetime of the scene; do not create controls you plan to destroy before the scene exits, as the control tree does not support removal of controls from within a build phase without careful coordination with the layout manager.

The invariant for build is: no subscriptions, no runtime dependencies, no cross-feature references. You cannot subscribe to sibling features' observables during build because those features may not have completed their own build phase yet. You cannot access runtime resources (screen size, loaded settings, workspace state) during build because those may not yet be resolved. Build is purely structural: it says "I have these controls and this layout."

**Bind runtime** is the wiring phase. It runs after every feature in the scene has completed build, so all controls exist and all sibling features are available. During bind_runtime, you establish all subscriptions to observable values, bind controls to data sources, wire callbacks, read initial values from runtime resources (screen size, settings, the workspace restore report), and set up any cross-feature coordination. This is also where you should perform any initialization that depends on knowing the initial screen dimensions or other runtime-resolved values.

The invariant for bind_runtime is: all controls exist, all siblings are built, subscriptions are safe. This phase is the correct and only correct place to subscribe to observables. Subscriptions established here will fire for the lifetime of the feature's scene; dispose them in the corresponding teardown method (`shutdown_runtime` or equivalent).

**Route** is the event-handling phase. Features handle events through two channels: the `handle_event` method, which is called directly by the routing pipeline for every event that reaches the feature, and the action routing system, which delivers named messages to handler methods on `RoutedFeature` subclasses. The route phase is reactive: it runs only when there is an event to handle, not on every frame.

When implementing `handle_event`, return `True` to consume the event and stop further routing, or return `False`/`None` to pass it on. Consuming an event is appropriate when the event is fully handled and you do not want it to reach other features or controls below your handler in the routing chain. Do not consume events indiscriminately — consuming events that you do not handle prevents other features from receiving them.

**Update** is the per-frame computation phase. It runs once per frame, unconditionally, for every feature in the active scene. Use it for time-based animations (advancing a tween, incrementing a timer), polling for results from background computations, and any state transitions that must happen on a specific schedule. The `dt_seconds` parameter gives the elapsed time since the last frame; use it to make time-based logic frame-rate independent.

Keep update fast. It is the most frequently called method in any feature, running at the target frame rate (typically 60 or 120 times per second). Expensive computation in update directly increases per-frame time and degrades the application's responsiveness. If a computation takes more than a fraction of a millisecond, consider whether it can be moved to a `CooperativeScheduler` coroutine that spreads work across multiple frames. The scheduler budget contract ensures that coroutine work does not consume more than 4 ms per frame.

**Draw** is the custom rendering phase. It runs once per frame, after update, for features that need to render directly to the pygame screen surface. Most features do not override this method because their controls are rendered automatically by the control tree. Use draw for custom rendering that the control tree cannot express: procedural graphics, particle systems, canvas overlays, debug visualizations. The `screen` parameter is the pygame `Surface` for the current display; draw to it using pygame's drawing functions or any pygame-compatible renderer.

For `DirectFeature`, draw is the primary rendering method and is called on every frame. For standard `Feature` subclasses, override draw only when you have a specific custom rendering need that the control tree cannot satisfy.

### Message and Logic Coordination

Features communicate without direct references to each other through two mechanisms: `FeatureMessage` publishing and shared observable state. Choosing between them depends on whether the communication is event-like (a one-time notification that something happened) or state-like (a continuously valid value that should always reflect some condition).

`FeatureMessage` is the event-like mechanism. A feature publishes a message with `host.publish_message(FeatureMessage(name="data_ready", payload=result))`. Any feature in the same scene that has registered a handler for `"data_ready"` receives the message. The publisher does not know who receives it; the receiver does not know who published it. This is the correct mechanism for "fire and forget" notifications — a `LogicFeature` announcing that a background computation is complete, a feature announcing that the user performed an action that other features should react to, or a coordinator feature signaling that all prerequisites for a transition are met.

Observable state is the state-like mechanism. A `LogicFeature` that owns a result value exposes it as an `ObservableValue`. UI features subscribe to it in `bind_runtime` and update their display whenever the observable changes. This is the correct mechanism for values that should always be reflected in the UI — a running count, a loading state, a selected item, a computed result. Observable state is always current; a feature that subscribes to it gets the current value immediately on subscription and is notified on every subsequent change.

A `LogicFeature` is the natural coordination hub for features that need both mechanisms. It can hold shared observable state that multiple UI features subscribe to, and it can publish messages when discrete events occur (a background task starts, completes, or fails). UI features are lightweight consumers of both: they subscribe to observables for continuous state and register message handlers for discrete events.

### When to Use Routed Runtime Specs

`RoutedRuntimeSpec` and `RoutedFeatureLifecycleSpec` are advanced spec types that reduce boilerplate when a feature has multiple related wiring needs that would otherwise require repetitive manual setup. If you are building a feature that needs several action hotkeys, a shortcut overlay showing those hotkeys, a task-panel focus toggle, and event subscriptions with automatic cleanup, doing all of that manually in `bind_runtime` and `shutdown_runtime` is verbose and error-prone. `RoutedRuntimeSpec` groups those declarations into a single spec that the framework wires automatically.

The most important functions in this subsystem are `setup_routed_runtime` and `shutdown_routed_runtime` (from Tier 18). `setup_routed_runtime` reads the `RoutedRuntimeSpec` and applies all its declarations: it registers action hotkeys via `register_action_hotkeys`, creates the shortcut help overlay if declared, binds the task-panel focus toggle if declared, and registers event subscriptions via `bind_feature_event_subscription`. `shutdown_routed_runtime` reverses all of that: it unregisters hotkeys, tears down the overlay, and unbinds all subscriptions. Calling these two functions in `bind_runtime` and `shutdown_runtime` respectively eliminates the need to write that teardown logic manually.

`RoutedFeatureLifecycleSpec` is the per-feature variant that works similarly but applies to `RoutedFeature` instances that participate in the full feature lifecycle — it wraps `bind_routed_feature_lifecycle` and `shutdown_routed_feature_lifecycle` with the same cleanup guarantee. Use it when a `RoutedFeature` has a complex set of routing bindings that should all be established and torn down together atomically.

Use these spec types when the manual setup code for a feature's routing bindings exceeds a few lines, or when you find yourself writing the same pattern of register-in-bind / unregister-in-shutdown across multiple features. The spec approach is more maintainable because the declaration is co-located with the feature definition rather than split across two lifecycle methods.

---

## Main Systems Reference

[Back to Table of Contents](#table-of-contents)

The sixteen system chapters below are the primary reference for gui_do's runtime systems. Each chapter covers one coherent area of the framework in depth, following the standard template: what the system is, the mental model for using it, its public API surface, a typical usage flow, a minimal working example, advanced patterns, common mistakes, and cross-links to related systems.

---

### 8.1 Application Bootstrap and Host Configuration

[Back to Table of Contents](#table-of-contents) · [See Appendix F: Specifications and Option Reference](#f-specifications-and-option-reference) (§F.1 Bootstrap and Host Config, §F.2 Feature and Scene Specs)

#### What it is and why it exists

The bootstrap system is the entry point for every gui_do application. Its job is to take a complete, declarative description of an application's structure — its scenes, features, windows, actions, fonts, cursors, persistence policy, and accessibility metadata — and realize that description as a fully wired, running application. The design goal is that no application code should contain imperative wiring: no manual calls to register an action with the action manager, no manual calls to bind a font to the font manager, no manual calls to set up scene transitions. All of that is the bootstrap's responsibility, driven by the specs the developer provides.

The two-phase approach — build config, then bootstrap — separates description from execution. `build_host_application_config` takes a `HostApplicationBindingSpec` and performs a single deterministic pass that resolves all cross-references (for example, matching feature window bundle specs to their features, matching action hotkey specs to their action descriptors), validates all requirements, and produces a `HostApplicationConfig`. This config object can be inspected in tests without starting a display. `bootstrap_host_application` then takes that config and a host object, wires everything onto the host, starts pygame, creates the display, and hands control to the application runtime.

#### Mental model and lifecycle placement

Think of the host as a plain Python object that bootstrap populates. Before `bootstrap_host_application` is called, the host has no runtime attributes. After it returns, the host carries `app` (the live `GuiApplication`), a reference to every feature, every scene manager, every font role registry entry, and every other runtime artifact that the config declared. Your application code then calls `host.app.run_entrypoint(target_fps=120)` to start the event loop.

The config is built once, at application startup, before any display window exists. The bootstrap pass is not reentrant; it runs once and produces a stable host state that persists for the application's lifetime.

#### Primary public APIs and key types

**From Tier 1:**
- `HostApplicationBindingSpec` — high-level declarative spec aggregating all binding sub-specs
- `HostApplicationConfig` — fully resolved config produced by `build_host_application_config`
- `build_host_application_config` — builder that resolves a `HostApplicationBindingSpec` to `HostApplicationConfig`
- `bootstrap_host_application` — executes the config and populates the host
- `SceneBundleBindingSpec` — declares one scene with its name, transition style, prewarm policy, and optional scene root
- `FeatureWindowBundleBindingSpec` — declares a feature that owns a toggleable window, bundling feature, window, task-panel button, and action into a single spec
- `ActionBindingSpec`, `CursorBindingSpec`, `FontRoleBindingSpec`, `PaletteBindingSpec` — binding specs for specific subsystems
- `TelemetryConfig` — optional telemetry configuration
- `SceneTransitionStyle` — enum for slide-left, slide-right, fade, and other transition styles
- All spec types (`FeatureSpec`, `WindowSpec`, `RuntimeSceneSpec`, `ActionSpec`, `AnchoredWindowSpec`, `LogicBindingSpec`, `TaskPanelButtonSpec`, `ShortcutOverlaySpec`, `RoutedRuntimeSpec`, `RoutedFeatureLifecycleSpec`, `FeatureWindowBundleBindingSpec`, `WindowToggleBindingSpec`, `SceneSetupBindingSpec`, `RuntimeSceneBindingSpec`, `SceneRootBindingSpec`, `CursorBindingSpec`, `FontRoleBindingSpec`, `ActionBindingSpec`, `PaletteBindingSpec`, `SceneBundleBindingSpec`, `HostApplicationBindingSpec`, `TabbedPresenterSpec`, `TabBuilderSpec`, `NotificationSpec`)
- All builder helpers (`build_feature_specs`, `build_feature_window_bundle_specs`, `build_window_toggle_specs`, `build_scene_setup_specs`, `build_runtime_scene_specs`, `build_scene_root_specs`, `build_cursor_specs`, `build_font_role_specs`, `build_scene_nav_actions`, `build_action_specs`, `build_scene_bundle_specs`, `build_static_accessibility_specs`, `build_host_application_config`, `build_notification_center`)
- Helper factories (`make_window_toggle_spec`, `make_scene_nav_action`, `make_exit_action`, `make_palette_open_action`, `make_static_accessibility_spec`)
- Control spec builders (`ControlDefinition`, `build_specs_from_column_section`, `RowCellSpec`, `build_horizontal_row_specs`, `build_multi_column_grid_specs`)

**From Tier 2:**
- `GuiApplication` — the live application runtime; provides `run_entrypoint`, `restore_workspace`, `load_workspace`
- `create_display` — creates the pygame display surface
- `SceneTransitionManager` — manages scene transition animations and scene activation sequencing
- `apply_scene_setup_specs` — applies `SceneSetupSpec` entries to an existing scene
- `SceneSetupSpec` — declares per-scene setup customization

#### Typical usage flow

1. Define your feature classes (each in its own package with a public `__init__.py` surface).
2. Import them in your config module.
3. Construct a `HostApplicationBindingSpec` with all field entries populated: `display_size`, `window_title`, `fonts`, `initial_scene_name`, `scene_bundle_entries`, `feature_entries` or `feature_window_bundle_entries`, `action_entries`, `static_accessibility_entries`.
4. Pass the binding spec to `build_host_application_config` to produce `HostApplicationConfig`.
5. In your host class's `__init__`, call `bootstrap_host_application(self, config)`.
6. Call `self.app.run_entrypoint(target_fps=120)`.

#### Minimal example

```python
from gui_do import (
    HostApplicationBindingSpec,
    SceneBundleBindingSpec,
    ActionBindingSpec,
    build_host_application_config,
    bootstrap_host_application,
    Feature,
)

class MyFeature(Feature):
    HOST_REQUIREMENTS = {"build": ["layout_manager"]}
    def __init__(self):
        super().__init__(scene_name="main")
    def build(self, host):
        pass  # add controls here

class MyApp:
    def __init__(self):
        config = build_host_application_config(
            HostApplicationBindingSpec(
                display_size=(1280, 720),
                window_title="My App",
                fonts={"default": {"file": "assets/fonts/Font.ttf", "size": 14}},
                initial_scene_name="main",
                scene_bundle_entries=(
                    SceneBundleBindingSpec(scene_name="main", pretty_name="Main"),
                ),
                feature_entries=(("_my_feature", MyFeature),),
                action_entries=(
                    ActionBindingSpec(kind="exit", action_id="exit", label="Exit"),
                ),
            )
        )
        bootstrap_host_application(self, config)

    def run(self):
        self.app.run_entrypoint(target_fps=120)

MyApp().run()
```

#### Advanced pattern

For a multi-scene application with per-scene toggled windows, use `FeatureWindowBundleBindingSpec` to bundle a feature, its window, its task-panel button, and its toggle action into a single declaration. Pair with `SceneBundleBindingSpec` entries for each scene (each with its own `transition_style` and optional `pristine_asset` for a background image) and `PaletteBindingSpec` to add scene-navigation and window-visibility entries to the command palette automatically. The `build_host_application_config` builder resolves all cross-references between these specs in one pass, so adding a new window is a single `FeatureWindowBundleBindingSpec` entry with no manual registration code anywhere.

#### Common mistakes and anti-patterns

- **Manually mutating host attributes after bootstrap.** Bootstrap wires a specific graph of objects. Manually replacing a wired object (e.g., reassigning `host.app`) breaks the graph's internal references. Use spec-driven config to describe what you need before bootstrap runs.
- **Scene name mismatch.** A feature declares `scene_name="main"` in its constructor but there is no `SceneBundleBindingSpec` with `scene_name="main"`. The feature builds but is never activated. Always verify that `scene_name` values in features match `scene_name` values in `scene_bundle_entries`.
- **Forgetting `initial_scene_name`.** Without an `initial_scene_name`, the application does not know which scene to activate on startup. This field is required.
- **Using internal `gui_do.*` imports.** Consumer code must import from `gui_do` only, not from `gui_do.features.data_driven_runtime` or other internal modules. The root package exports all supported public types.

#### Cross-links to related systems

- **8.2 Feature Lifecycle** — features are the units that bootstrap assembles into scenes.
- **8.3 Events and Actions** — action specs in the bootstrap config are the source of all registered actions.
- **8.9 Scene Presentation** — `SceneBundleBindingSpec` configures scene transition styles and optional task panels.
- **8.11 Persistence** — `HostApplicationConfig` includes workspace persistence policy configuration.

---

### 8.2 Feature Lifecycle and Feature Types

[Back to Table of Contents](#table-of-contents) · [See Appendix F: Specifications and Option Reference](#f-specifications-and-option-reference) (§F.2 Feature and Scene Specs, §F.4 Routed Runtime Specs)

#### What it is and why it exists

The feature lifecycle system is the mechanism by which application behavior is organized into self-contained, composable units. Every piece of application logic — interactive UI, background computation, shared state management, event handling — lives inside a feature. The lifecycle system ensures that each feature's phases run in the correct order, that features have access to exactly the resources they need when they need them, and that features are cleanly torn down when their scenes exit.

Without a lifecycle system, application code tends to accumulate in monolithic update loops and event handlers that grow without bound and are difficult to test or reuse. The feature model provides a principled decomposition: each independent concern becomes its own feature, with its own clearly bounded lifecycle methods and its own clearly bounded control tree. The framework provides the orchestration that makes these units work together safely.

#### Mental model and lifecycle placement

Think of a feature's lifecycle as having two phases: the construction phase (build, then bind_runtime), and the operational phase (handle_event, on_update, draw). The construction phase runs once when the scene is assembled. The operational phase runs on every frame for the duration of the scene's active lifetime. When the scene exits, the framework calls teardown methods in reverse order.

The critical mental model is the separation between build and bind_runtime. During build, the world is not yet fully constructed: sibling features may not have completed their own build phase. During bind_runtime, the world is fully constructed: all controls exist, all sibling features are built, all observables are available. This separation makes it safe to write cross-feature wiring in bind_runtime without worrying about order-of-initialization issues.

#### Primary public APIs and key types

**From Tier 1 (feature lifecycle base classes):**
- `Feature` — standard feature; builds controls in the control tree
- `DirectFeature` — renders directly to the screen surface; bypasses the control tree
- `LogicFeature` — has no UI; exists for domain logic and shared state
- `RoutedFeature` — a `Feature` that participates in the action routing infrastructure
- `FeatureMessage` — named message with optional payload, published for cross-feature communication
- `FeatureManager` — the runtime manager that orchestrates feature lifecycle phases
- `ScenePresentationModel` — the presentation model exposed to features through the host
- `SceneSetupSpec` — per-scene setup customization
- `setup_standard_font_roles` — helper to register font roles for a feature or demo

**From Tier 18 (advanced wiring helpers):**
- `bind_routed_feature_lifecycle` — establishes all routing for a `RoutedFeatureLifecycleSpec`
- `shutdown_routed_feature_lifecycle` — tears down all routing established by the corresponding bind
- `register_routed_feature_companions` — wires logic feature companions to a routed feature
- `ActiveTabUpdateRouter` — routes update messages to the currently active tab's feature
- `TabLayoutContext` — context object for tab-based presentation layouts
- `FrameTimer`, `TabPanelManager`, `WindowRelativeRect` — layout and timing helpers

#### Typical usage flow

1. Choose the appropriate feature base class for your concern (`Feature`, `DirectFeature`, `LogicFeature`, or `RoutedFeature`).
2. Declare `HOST_REQUIREMENTS` as a class-level dict mapping phase names to lists of required host attribute names.
3. Implement `build(host)` to create controls and add them to the scene tree.
4. Implement `bind_runtime(host)` to subscribe to observables, bind controls to data, and wire cross-feature interactions.
5. Implement `handle_event(host, event)`, `on_update(host, dt_seconds)`, and/or `draw(host, screen)` for the operational phase as needed.
6. Implement `shutdown_runtime(host)` to dispose subscriptions and clean up any resources acquired in `bind_runtime`.
7. Register the feature via `FeatureSpec` in the application config (Tier 1 `FeatureSpec`) or in a `FeatureWindowBundleBindingSpec`.

#### Minimal example

```python
from gui_do import Feature, ObservableValue, LabelControl

class CounterFeature(Feature):
    HOST_REQUIREMENTS = {
        "build": ["layout_manager"],
        "bind_runtime": [],
    }

    def __init__(self):
        super().__init__(scene_name="main")
        self._count = ObservableValue(0)
        self._label: LabelControl | None = None
        self._sub = None

    def build(self, host):
        self._label = LabelControl(text="Count: 0", rect=(50, 50, 200, 30))
        host.layout_manager.add(self._label)

    def bind_runtime(self, host):
        self._sub = self._count.subscribe(
            lambda v: self._label.set_text(f"Count: {v}")
        )

    def shutdown_runtime(self, host):
        if self._sub:
            self._sub()
            self._sub = None

    def on_update(self, host, dt_seconds):
        self._count.set(self._count.get() + 1)
```

#### Advanced pattern

The logic-and-presentation split is the most important advanced pattern in the feature system. A `LogicFeature` owns all domain state as observable values and runs expensive computation via `CooperativeScheduler` coroutines. A `RoutedFeature` companion subscribes to the logic feature's observables in `bind_runtime` and drives the control tree. Neither component contains the other's concerns. Wire them together using `register_routed_feature_companions` in Tier 18, which makes the logic feature available on the host under a declared attribute name so the routed feature can access it in its `bind_runtime`.

For features that participate in tabbed presentations, `ActiveTabUpdateRouter` dispatches update messages to whichever tab's feature is currently visible, preventing off-screen features from consuming update budget unnecessarily.

#### Common mistakes and anti-patterns

- **Subscribing to observables in `build`.** The sibling feature that owns the observable may not have completed `build` yet, so the observable may not exist. Always subscribe in `bind_runtime`.
- **Performing expensive computation in `on_update`.** `on_update` runs every frame; expensive work here directly degrades frame rate. Use `CooperativeScheduler` to spread work across frames.
- **Forgetting `shutdown_runtime` subscription cleanup.** Subscriptions that are not disposed when the feature's scene exits cause memory leaks and phantom callbacks. Always pair `.subscribe()` in `bind_runtime` with disposal in `shutdown_runtime`.
- **Using `DirectFeature` for interactive UI.** `DirectFeature` bypasses the control tree and does not participate in focus or hit-testing. Use `Feature` for any content that should receive mouse clicks or keyboard focus.
- **Failing to call `shutdown_routed_feature_lifecycle`.** If you use `RoutedFeatureLifecycleSpec` and call `bind_routed_feature_lifecycle` in `bind_runtime`, you must call `shutdown_routed_feature_lifecycle` in `shutdown_runtime`. Omitting the shutdown leaves hotkeys, overlays, and event subscriptions registered indefinitely.

#### Cross-links to related systems

- **8.1 Bootstrap** — features are declared via `FeatureSpec` and `FeatureWindowBundleBindingSpec` in the bootstrap config.
- **8.3 Events and Actions** — features receive events via `handle_event` and respond to actions via `RoutedFeature` routing.
- **8.4 State and Observables** — features use `ObservableValue` and other observable types for reactive state.
- **8.10 Scheduling** — `CooperativeScheduler` is the tool for spreading expensive feature computation across frames.

---

### 8.3 Events, Actions, Input Mapping, and Routing

[Back to Table of Contents](#table-of-contents) · [See Appendix F: Specifications and Option Reference](#f-specifications-and-option-reference) (§F.3 Action and Input Specs, §F.4 Routed Runtime Specs)

#### What it is and why it exists

The event system is the runtime's input-handling infrastructure. Its job is to normalize all raw pygame input into a canonical `GuiEvent` form and then route those events through a stable, ordered pipeline to the appropriate handlers. On top of the event system, the action system provides a named command model: actions are identifiers for discrete user operations (like "exit", "open command palette", "toggle window"), and the input mapping system bridges key presses and mouse interactions to action identifiers. Together, these three subsystems — events, actions, and input mapping — replace the ad-hoc `if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE` patterns that characterize low-level pygame programming with a structured, testable, data-driven alternative.

The key design insight is that separating "what the user did at the hardware level" (raw pygame events) from "what the application should do" (named actions) makes the application dramatically more maintainable. Remapping a keyboard shortcut requires only a change to the input binding spec, not a search-and-replace through event-handling code. Adding a new way to trigger an action (keyboard, mouse button, gamepad) requires only a new binding entry, not a new branch in every handler.

#### Mental model and lifecycle placement

Raw pygame events enter the pipeline and are immediately normalized to `GuiEvent`. The routing pipeline then dispatches the `GuiEvent` through an ordered sequence of handlers: overlay managers and focus systems take first look, then global key bindings (including the command palette), then scene-level handlers, then feature-level handlers. At any point in this chain, a handler can set `propagation_stopped` on the event, which stops routing immediately. Named actions are executed when an `InputMap` binding matches an incoming event; the `ActionManager` then dispatches the action to any registered handler.

The event system runs entirely within the application's event loop — during `GuiApplication.process_event`, which is called for every pygame event on every frame tick. There is no asynchronous event delivery; all event processing is synchronous and deterministic.

#### Primary public APIs and key types

**From Tier 4:**
- `EventPhase` — `CAPTURE`, `TARGET`, `BUBBLE`
- `EventType` — `PASS`, `QUIT`, `KEY_DOWN`, `KEY_UP`, `MOUSE_BUTTON_DOWN`, `MOUSE_BUTTON_UP`, `MOUSE_MOTION`, `MOUSE_WHEEL`, `TEXT_INPUT`, `TEXT_EDITING`
- `GuiEvent` — canonical event object with full field set; see below
- `ValueChangeCallback`, `ValueChangeReason` — typed callback protocol for observable-to-event bridges
- `EventManager` — the runtime normalization and dispatch gateway; `to_gui_event()` is the conversion entry point
- `EventBus` — simple publish/subscribe bus for application-level events
- `GestureRecognizer` — detects and normalizes multi-step pointer gestures
- `EventRecorder`, `EventPlayback`, `RecordedEvent` — record and replay event sequences for deterministic testing
- `InputSnapshot` — frozen snapshot of current keyboard and mouse button states; available to features that poll input rather than responding to events
- `Signal`, `SignalConnection` — typed signal/slot mechanism for direct callback wiring within a component
- `ActionManager` — registers and dispatches named actions
- `ActionContext`, `ActionMiddleware` — middleware pipeline for wrapping action execution with cross-cutting concerns
- `ActionDescriptor`, `ActionRegistry` — type and registry for registered action descriptors
- `InputMap`, `InputBinding` — maps key/mouse bindings to action IDs
- `KeyChordManager`, `KeyChord`, `ChordStep` — multi-step key sequence recognition
- `FocusManager` — manages keyboard focus within a scene; see also chapter 8.7
- `FocusScope`, `FocusScopeManager` — nested focus scopes for modal regions
- `WindowFocusManager` — manages focus cycling across windows
- `FocusRing` — the ordered list of focusable elements within a scope

**From Tier 30:**
- `InteractionPhase`, `InteractionContext`, `InteractionTransition`, `InteractionStateMachine` — pointer/keyboard/gesture phase tracking with guarded state transitions

**From Tier 1 (spec types for actions):**
- `ActionSpec`, `ActionHotkeySpec`, `ControlKeyBindingSpec`, `EventSubscriptionSpec` — declarative action and input binding specs

#### GuiEvent fields

Every event delivered to a feature's `handle_event` method is a `GuiEvent` with these fields:
- `kind` / `type` — the `EventType` value
- `key` — the pygame key constant for keyboard events
- `pos` / `rel` — logical (scene-relative) pointer position and relative motion
- `raw_pos` / `raw_rel` — raw screen-coordinate position and relative motion
- `button` — mouse button index for button events
- `wheel_x` / `wheel_y` — scroll wheel delta
- `mod` — modifier key bitmask
- `text` — text string for `TEXT_INPUT` events
- `control_id` — the ID of the control that generated this event, if any
- `group`, `window`, `task_panel`, `task_id` — routing context for windowed and task-panel events
- `error` — error payload for error events
- `source_event` — the original pygame event that was normalized
- `phase` — `EventPhase` value
- `propagation_stopped` — set to stop further routing
- `default_prevented` — set to suppress the event's default behavior

Useful `GuiEvent` helpers: `is_key_down()`, `is_key_up()`, `is_mouse_down()`, `is_mouse_up()`, `is_mouse_motion()`, `is_left_down()`, `is_right_down()`, `stop_propagation()`, `prevent_default()`, `clone()`, `with_phase()`, `collides(rect)`.

#### Typical usage flow

1. Declare `ActionSpec` entries in the `HostApplicationBindingSpec.action_entries` for each named action your application supports (exit, palette open, scene navigation, etc.).
2. Declare `ActionHotkeySpec` entries (either directly or via `RoutedRuntimeSpec`) to bind specific keys to action IDs.
3. In your feature's `handle_event`, check `event.type` and `event.key` (or use the `is_*` helpers) to handle events that the control tree does not handle automatically.
4. For action handling, use the `RoutedFeature` base class and register methods as action handlers; the framework delivers matching action events directly to those methods.
5. Use `InputSnapshot` in `on_update` for continuous polling of key/button state (for example, holding a key to pan a camera).

#### Minimal example

```python
from gui_do import RoutedFeature, GuiEvent, EventType, ActionSpec

class SearchFeature(RoutedFeature):
    HOST_REQUIREMENTS = {"build": ["layout_manager"]}

    def __init__(self):
        super().__init__(scene_name="main")

    def build(self, host):
        pass  # build controls here

    def handle_event(self, host, event: GuiEvent) -> bool | None:
        if event.is_key_down() and event.key == K_ESCAPE:
            # dismiss search, consume event
            event.stop_propagation()
            return True
        return None
```

Declaring the action in config:
```python
ActionBindingSpec(kind="custom", action_id="open_search", label="Open Search", category="Edit")
```

#### Advanced pattern

`InteractionStateMachine` is the tool for features that need to track multi-phase pointer interactions: press, drag, and release, with guarded transitions between phases. Rather than manually managing boolean flags (`is_dragging`, `drag_start`, etc.) in `handle_event`, you declare `InteractionTransition` rules and the state machine tracks which phase you are in, ensuring that transitions only occur when guard conditions are met. This eliminates an entire class of bugs where a "drag" continues after a button release is missed.

`EventRecorder` and `EventPlayback` enable deterministic test scenarios: record a sequence of events during a real interaction, then replay them in automated tests to verify that the feature responds correctly. This is particularly valuable for testing complex gesture sequences that are difficult to construct programmatically.

#### Common mistakes and anti-patterns

- **Handling raw pygame events instead of `GuiEvent`.** The framework has already normalized events by the time they reach feature handlers. Bypassing this and calling `pygame.event.get()` in a feature creates a second event queue consumer that starves the main pipeline.
- **Assuming global routing when handlers are scene-scoped.** An `ActionSpec` declared for scene "main" is only active when scene "main" is active. If you press the corresponding key while scene "settings" is active, no handler fires. Design action scopes intentionally.
- **Consuming events indiscriminately.** Returning `True` from `handle_event` stops routing for that event. If your feature consumes a keyboard event that other controls also need (for example, Tab for focus cycling), you silently break those controls. Only consume events you have fully handled.
- **Ignoring `propagation_stopped` in custom routing code.** If you write code that dispatches events to multiple handlers in sequence, always check `event.propagation_stopped` between calls. The `GuiEvent.propagation_stopped` flag is the routing pipeline's stop signal.

#### Cross-links to related systems

- **8.2 Feature Lifecycle** — features receive events through `handle_event`; `RoutedFeature` adds action routing participation.
- **8.7 Focus and Accessibility** — the `FocusManager` and `FocusScope` types from Tier 4 govern which controls receive keyboard events.
- **8.8 Overlays** — overlay managers intercept events before they reach the scene's features.
- **8.9 Scene Presentation** — the command palette activation key is registered at the scene level via `SceneCommandPaletteSpec`.

---

### 8.4 State and Observables

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

The state and observables system provides the reactive data layer that connects application logic to the visual display without requiring either side to know about the other. Observable values are the primary mechanism for sharing live data between features, between features and controls, and between the application's data model and its presentation model. Without this system, updating the UI when data changes requires either polling (checking values every frame) or explicit imperative calls to every display element that shows the changed value — both of which create coupling that makes the application hard to maintain.

The system is deliberately simple: at its core, it is just typed wrappers around Python values that maintain a list of subscribers and notify them when the value changes. This simplicity is a feature: there are no hidden state machines, no complex ownership semantics, no framework-level scheduling of notifications. When a value changes, subscribers are called synchronously, in registration order, before the calling code returns. This makes the behavior of the reactive system completely predictable and easy to reason about.

#### Mental model and lifecycle placement

Observables are data nodes. Features are producers and consumers of those nodes. Controls are consumers. The reactive graph forms when features subscribe in `bind_runtime`; it dissolves when features unsubscribe in `shutdown_runtime`. Between those two points, any change to an observable automatically propagates to every subscriber.

The placement in the lifecycle is precise: create observables in `__init__` (or `build` if their initial value depends on host state), subscribe in `bind_runtime`, unsubscribe in `shutdown_runtime`. Do not subscribe in `build` — the reactive graph is established in `bind_runtime` after the full construction phase is complete.

#### Primary public APIs and key types

**From Tier 3:**
- `ObservableValue` — wraps a single typed value; `.subscribe(cb)` returns a disposable token; `.get()` / `.set(v)` for read/write
- `PresentationModel` — base class for objects that aggregate multiple observable values into a presentation unit
- `ComputedValue` — a derived `ObservableValue` that recomputes automatically from source observables
- `reactive_batch` — context manager that defers all subscriber notifications until the `with` block exits
- `is_batching` — returns `True` if currently inside a `reactive_batch` context
- `InvalidationTracker` — tracks which observable-derived values are stale and need recomputation
- `ChangeKind` — enum: `ADDED`, `REMOVED`, `UPDATED`, `MOVED`
- `CollectionChange` — notification object carrying `kind`, affected index/key, and old/new values
- `ObservableList` — observable wrapper around a mutable list
- `ObservableDict` — observable wrapper around a mutable dict
- `CollectionViewQuery` — query spec for sorting and filtering an `ObservableList`
- `CollectionView` — a live sorted/filtered view of an `ObservableList` that updates automatically
- `Binding`, `BindingGroup` — typed two-way binding between observable values and control properties
- `ObservableStream` — a push-based stream of values (useful for events with a history)
- `SelectionModel`, `SelectionMode` — selection state for list/grid controls, with observable current selection

**From Tier 27:**
- `AppStateStore` — single-source-of-truth state store for application-wide state
- `StateSelector` — a derived slice of the store that recomputes when relevant parts of the store change
- `StateTransaction` — atomic multi-field update that fires subscribers once after all fields are updated

#### Typical usage flow

1. Declare `ObservableValue` instances as fields on the feature (`self._count = ObservableValue(0)`).
2. In `build`, optionally set initial values from static configuration.
3. In `bind_runtime`, subscribe to observables (`self._sub = self._count.subscribe(self._on_count_changed)`). Store the returned token on `self`.
4. In the subscription callback, update the corresponding control (`self._label.set_text(f"Count: {v}")`).
5. In the operational phase, change observable values by calling `.set(new_value)`. Subscribers fire automatically.
6. In `shutdown_runtime`, dispose all subscriptions (`self._sub()` if the token is callable, or call its `.dispose()` method).

#### Minimal example

```python
from gui_do import Feature, ObservableValue, ComputedValue, LabelControl, reactive_batch

class InventoryFeature(Feature):
    HOST_REQUIREMENTS = {"build": ["layout_manager"]}

    def __init__(self):
        super().__init__(scene_name="main")
        self._item_count = ObservableValue(0)
        self._selected = ObservableValue(False)
        self._status = ComputedValue(
            sources=[self._item_count, self._selected],
            compute=lambda count, sel: f"{count} items" + (" (selected)" if sel else "")
        )
        self._label = None
        self._sub = None

    def build(self, host):
        self._label = LabelControl(text="", rect=(50, 50, 300, 30))
        host.layout_manager.add(self._label)

    def bind_runtime(self, host):
        self._sub = self._status.subscribe(
            lambda text: self._label.set_text(text)
        )

    def shutdown_runtime(self, host):
        if self._sub:
            self._sub()
            self._sub = None

    def on_update(self, host, dt_seconds):
        # Simulate adding items
        with reactive_batch():
            self._item_count.set(self._item_count.get() + 1)
            self._selected.set(self._item_count.get() % 3 == 0)
```

#### Advanced pattern

`AppStateStore` is the tool for state that must be shared across many features that do not have a direct parent-child relationship. Rather than threading observables through feature references, features read from and write to a centralized store. `StateSelector` creates a derived observable slice: `store.select(lambda state: state.active_scene_name)` returns an observable that updates whenever `active_scene_name` changes in the store, even if other parts of the store are mutated simultaneously. `StateTransaction` groups multiple store mutations into a single atomic update, ensuring that subscribers see a consistent state rather than intermediate states.

`CollectionView` with `CollectionViewQuery` is the right tool when UI needs a sorted/filtered live view of an `ObservableList`. Rather than sorting the list on every frame or on every mutation, the `CollectionView` maintains an incrementally updated sorted/filtered projection that updates automatically whenever the source list changes. `ListViewControl` and `DataGridControl` can bind directly to a `CollectionView`.

#### Common mistakes and anti-patterns

- **Polling `.get()` in `on_update`.** Polling defeats the purpose of observables: it re-evaluates every frame regardless of whether the value changed, and it introduces one-frame latency. Subscribe instead.
- **Subscribing in `build`.** Controls may not exist yet during build; subscriptions established here may fire before their callback targets are ready. Always subscribe in `bind_runtime`.
- **Discarding subscription tokens.** `self._count.subscribe(cb)` returns a token. If you write `_ = self._count.subscribe(cb)` or just call `.subscribe(cb)` without storing the result, you have no way to dispose the subscription during teardown. Every subscription must be stored and disposed.
- **Sharing plain Python lists across features.** A plain list has no notification mechanism; changes made by one feature are invisible to another until the next poll cycle. Use `ObservableList` for any collection that must be shared reactively.
- **Using `reactive_batch` across an `await` or across features.** Batching is synchronous and single-threaded. Do not start a batch in one feature and expect it to defer notifications in another; batch scopes should be small and local.

#### Cross-links to related systems

- **8.2 Feature Lifecycle** — observables are created in feature `__init__`/`build` and subscribed to in `bind_runtime`.
- **8.5 Controls** — controls accept observable values for their reactive properties.
- **8.11 Persistence** — `SettingsRegistry` integrates with observable state to persist and restore values across sessions.
- **8.14 Data and Dataflow** — `AsyncDataProvider` and `DataflowPipeline` bridge async operations to observable state for driving reactive UI from background work.

---

### 8.5 Controls and Control Composition

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Controls are the reusable UI primitives that features compose to build interactive interfaces. Every visible UI element — buttons, labels, text inputs, lists, sliders, progress bars, canvases, windows — is a control instance. Controls handle their own rendering, hit-testing, and basic input handling internally, so features do not need to implement any of that infrastructure themselves. A feature's responsibility is to create the right controls with the right configuration, add them to the correct container, and keep their state synchronized with the feature's observable data model.

The control tree is hierarchical: controls are children of `PanelControl` containers, which are children of scene roots or window root panels. This hierarchy drives layout, clipping, hit-testing, and the focus ring's spatial ordering. The framework traverses the tree every frame to draw controls and every event cycle to route pointer events to the correct hit target.

#### Mental model and lifecycle placement

A feature owns one root control (typically a `PanelControl`) that it adds to the scene or window during `build`. All controls the feature creates are children or descendants of that root. This ownership boundary is important: controls should never be moved from one feature's root to another's, and a feature should never hold references to controls owned by sibling features. Cross-feature data sharing uses observables and messages; it never happens through direct control references.

Controls are created in `build`, bound to data in `bind_runtime`, and used throughout the operational phase. They are implicitly destroyed when the scene exits — features do not need to manually remove controls from the tree on teardown.

#### Primary public APIs and key types

**From Tier 12 (primary controls):**
- `PanelControl` — rectangular container for grouping and clipping child controls
- `LabelControl` — static or dynamic text display
- `ButtonControl` — clickable button with text label and `on_click` callback
- `ToggleControl` — binary toggle with `on_toggle` callback and observable binding
- `SliderControl` — horizontal or vertical value slider
- `ScrollbarControl` — scrollbar for driving scroll position in `ScrollViewControl` or `CanvasViewport`
- `CanvasControl`, `CanvasEventPacket` — raw drawing surface; receives pointer events with canvas-local coordinates
- `CanvasViewport` — adds scrolling and zooming around a `CanvasControl`
- `FrameControl` — bordered frame container
- `ImageControl` — displays a static pygame `Surface`
- `ArrowBoxControl` — a box with a directional arrow pointer, useful for callouts
- `ButtonGroupControl` — a group of radio-style buttons where only one is selected at a time
- `TabControl`, `TabItem` — horizontal tab strip for switching between panels
- `DockWorkspacePanel` — a panel wired to a `DockWorkspace` for complex multi-pane layouts

**From Tier 13 (extended controls):**
- `TextInputControl` — single-line text entry with cursor and selection
- `TextAreaControl` — multi-line text entry
- `RichLabelControl` — text label supporting inline markup and spans
- `DropdownControl`, `DropdownOption` — single-selection dropdown
- `ListViewControl`, `ListItem` — scrollable list of selectable items; binds to `ObservableList`
- `OverlayPanelControl` — panel that renders above the normal control tree
- `DataGridControl`, `GridColumn`, `GridRow` — tabular data display with column definitions
- `TreeControl`, `TreeNode` — hierarchical tree view
- `SplitterControl` — resizable split between two panels
- `SpinnerControl` — numeric spinner with increment/decrement buttons
- `RangeSliderControl` — two-handle range selector
- `ColorPickerControl` — HSV/RGB color picker
- `ScrollViewControl` — scrollable viewport for oversized content
- `ProgressBarControl` — visual progress indicator
- `AnimatedImageControl` — displays a sequence of frames as animation
- `ErrorBoundary` — wraps a control subtree; catches rendering errors and shows a fallback
- `WindowControl` — a floating, titled, draggable window panel
- `TaskPanelControl` — the horizontal task panel bar
- `WindowPresenter` — base class for building the control layout of a floating window; subclass this for complex window UIs
- `MenuBarControl`, `MenuEntry` — horizontal menu bar with drop-down menus
- `SceneMenuStripControl` — specialized menu strip with scene-navigation and window-visibility menus
- `NotificationPanelControl` — displays active `NotificationRecord` entries
- `PropertyInspectorPanel` — property editing panel driven by `PropertyInspectorModel`
- `ToolbarControl`, `ToolbarItem` — horizontal toolbar with icon/text tool items
- `StatusBarControl`, `StatusSlot` — bottom status bar with independent named slots
- `ExpanderControl` — collapsible section with a toggle header
- `DatePickerControl` — calendar-based date selection
- `TimePickerControl` — time-of-day selection
- `BreadcrumbControl`, `BreadcrumbItem` — path breadcrumb navigation
- `SplitButtonControl`, `SplitButtonOption` — a button combined with a dropdown of secondary actions
- `ChipInputControl` — tokenized text input producing removable chip items

**From Tier 1 (control spec helpers):**
- `ControlDefinition`, `build_specs_from_column_section`, `RowCellSpec`, `build_horizontal_row_specs`, `build_multi_column_grid_specs` — declarative column-layout spec builders for property panels

#### Typical usage flow

1. In `build`, create a root `PanelControl` and add it to the host via `host.app.add()` with the scene name.
2. Add child controls to the root by calling `root.add(control)`.
3. Set static initial values (text, rect, style) in the constructor arguments.
4. In `bind_runtime`, bind controls to observable state: either pass the observable directly to the control constructor if it accepts observables, or subscribe manually and update the control in the callback.
5. Wire `on_click`, `on_toggle`, and other callback properties in `build` (since these are structural bindings) or in `bind_runtime` (if the callback depends on runtime state).

#### Minimal example

```python
from gui_do import Feature, PanelControl, LabelControl, ButtonControl, ObservableValue
from pygame import Rect

class CounterFeature(Feature):
    HOST_REQUIREMENTS = {"build": ["app"]}

    def __init__(self):
        super().__init__(scene_name="main")
        self._count = ObservableValue(0)
        self._label = None
        self._sub = None

    def build(self, host):
        root = host.app.add(PanelControl("counter_root", Rect(50, 50, 300, 100)), scene_name="main")
        self._label = root.add(LabelControl("counter_label", Rect(10, 10, 200, 30), "Count: 0"))
        root.add(ButtonControl("inc_btn", Rect(10, 50, 100, 30), "Increment", on_click=self._increment))

    def bind_runtime(self, host):
        self._sub = self._count.subscribe(lambda v: self._label.set_text(f"Count: {v}"))

    def shutdown_runtime(self, host):
        if self._sub:
            self._sub()
            self._sub = None

    def _increment(self):
        self._count.set(self._count.get() + 1)
```

#### Advanced pattern

The `WindowPresenter` pattern separates window layout from feature lifecycle. Subclass `WindowPresenter` and override its `build` method to construct all the controls for a floating window. Instantiate the presenter lazily in the feature's `build` method (to avoid circular imports) and call `host.app.add_presenter(presenter)` to register it. The feature's `bind_runtime` can then bind the presenter's controls to observable state through the presenter's public interface. Combine `WindowPresenter` with `TabbedPresenterSpec` and `TabBuilderSpec` when the window has multiple tabs; the framework constructs the tab strip and wires tab switching automatically.

`ErrorBoundary` wraps a subtree that may fail during rendering (for example, a third-party visualization control or a complex canvas drawing operation). If rendering inside the boundary raises, the boundary catches the exception, logs it via the telemetry system, and renders a fallback UI instead of crashing the frame. This is the correct way to isolate experimental or high-risk rendering code from the rest of the application.

#### Common mistakes and anti-patterns

- **Cross-feature control references.** Features must not hold references to controls owned by other features. Data is shared via observables; UI is independently rendered by each feature. Cross-feature control references create hidden coupling that breaks when either feature is reorganized.
- **Using controls as the source of truth for state.** A control's text value or toggle state is not the authoritative source of application data; the `ObservableValue` that drives it is. Reading state from controls (e.g., `my_label.text`) instead of from observables will produce stale values after observables are updated but before controls have re-rendered.
- **Creating controls outside `build`.** Controls created in `on_update` or `bind_runtime` are added to the control tree at unpredictable times and may not be laid out correctly. All control construction belongs in `build`.
- **Adding the same control to multiple containers.** A control can only have one parent. Adding it to a second container will produce incorrect layout behavior.

#### Cross-links to related systems

- **8.2 Feature Lifecycle** — controls are created in `build` and bound in `bind_runtime`.
- **8.4 State and Observables** — controls reflect observable state; observables are the correct source of truth.
- **8.6 Layout Systems** — layout engines manage the spatial arrangement of controls within containers.
- **8.7 Focus and Accessibility** — controls participate in the focus ring and the accessibility tree.
- **8.9 Scene and Window Presentation** — `WindowControl` and `WindowPresenter` are the building blocks of floating windows.

---

### 8.6 Layout Systems

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Layout systems manage the spatial organization of controls in a scene or window. Without a layout system, every control's position and size must be computed manually — typically as hardcoded pixel values — which breaks when the window is resized, when the font size changes, or when a new control is added between two existing controls. gui_do provides a family of layout engines that express spatial relationships declaratively, recompute positions when constraints change, and support responsive behavior that adapts to viewport size.

The variety of layout engines is intentional: different UI structures are best expressed by different layout models. A toolbar is best expressed as a flex row; a settings panel with labeled fields is best expressed as a two-column grid; a complex workbench is best expressed as a dock workspace with splits and tabbed panes. The framework provides all of these, and features choose the right engine for their specific need.

#### Mental model and lifecycle placement

Layout runs as a pass before drawing: the layout manager calls each control's measure and arrange methods, accumulating the resolved positions into the control tree. Controls that participate in a layout engine report their preferred size to the engine; the engine resolves positions and sets each control's bounding rect. Layout typically runs after `build` when the scene is first assembled, and again whenever a layout-affecting event occurs (window resize, content change, visibility toggle).

Features configure their layout engine in `build` by creating the engine, adding items to it, and applying it to the root control. They do not call layout methods directly during the operational phase; the framework triggers relayout automatically when needed.

#### Primary public APIs and key types

**From Tier 8 (layout engines):**
- `LayoutAxis` — enum for `HORIZONTAL` / `VERTICAL` axis
- `LayoutManager` — the top-level layout orchestrator; add layout engines to it; call `.layout()` to run a layout pass
- `WindowTilingManager` — tiles multiple `WindowControl` instances within a scene, like a desktop window manager
- `ConstraintLayout`, `AnchorConstraint` — anchor-based constraint layout between controls
- `DockPane`, `DockTabs`, `DockSplit`, `DockWorkspace` — hierarchical dock workspace for multi-pane layouts
- `FlexLayout`, `FlexItem`, `FlexDirection`, `FlexAlign`, `FlexJustify` — flex-box-style row/column layout
- `GridLayout`, `GridTrack`, `GridPlacement` — CSS-Grid-style fixed-track layout
- `CellCaretLayout`, `CellCaretState` — text-cell-based caret layout for structured text editing
- `LayoutAnimator` — smoothly animates from one layout pass to another using tweens
- `LayoutPass`, `MeasureContext`, `ArrangeContext`, `LayoutRoot` — low-level layout pass protocol for custom layout engines
- `ResponsiveLayout`, `Breakpoint` — selects one of several layout configurations based on viewport width breakpoints
- `SnapGrid`, `AlignmentGuide`, `SnapComposer`, `SnapTarget` — snap-to-grid and alignment guides for drag-positioned controls
- `FlowLayout`, `FlowItem` — wrapping item flow for tag/chip displays
- `Viewport` — manages a scrollable/zoomable view window over a large content area

**From Tier 28 (adaptive constraint layout v2):**
- `ConstraintAttr`, `LayoutConstraint`, `ConstraintSet`, `ConstraintLayoutEngine` — declarative priority-based constraint solver
- `AdaptivePolicy`, `resolve_adaptive_policy` — breakpoint-aware policy selection for the constraint engine

**From Tier 29 (virtualization core):**
- `MeasureMode`, `MeasurePolicy`, `VirtualizedWindow`, `RecyclePool`, `VirtualizationCore` — list/tree/grid windowing engine that renders only the visible subset of a large collection, with a recycle pool for reusing control instances

#### Layout family guide

- **`FlexLayout`** — best for toolbars, button rows, and panels where items should grow or shrink to fill available space. Configure with `FlexDirection.ROW` or `FlexDirection.COLUMN`, `gap`, alignment, and justification. Each `FlexItem` has a `grow` ratio and optional `basis` (preferred size).
- **`GridLayout`** — best for forms and data grids with fixed column/row definitions. Define tracks with `GridTrack`, place controls with `GridPlacement` specifying row/column spans.
- **`FlowLayout`** — best for tag clouds, chip inputs, and any content where items wrap to the next row when the row is full. Add `FlowItem` instances; flow direction and gap are configurable.
- **`ConstraintLayout` / `ConstraintLayoutEngine`** — best for dialog layouts and complex panels where controls have anchor relationships (e.g., "align my left edge to the right edge of this label, with 8px gap"). The adaptive variant supports breakpoint-driven constraint switching.
- **`DockWorkspace`** — best for IDE-style multi-pane workbenches with resizable splits and tabbed panes. `DockSplit` creates a resizable split; `DockPane` is a leaf region; `DockTabs` groups multiple panes in a tab strip.
- **`ResponsiveLayout`** — selects one of several pre-configured layouts based on a viewport width breakpoint list. The simplest option for "rearrange on narrow viewport."
- **`SnapGrid`** — for drag-and-drop canvas experiences where controls should snap to grid lines or align to other controls' edges. Use `SnapComposer` to combine multiple snap targets.
- **`VirtualizationCore`** — for displaying very large collections (thousands of items) in a list, tree, or grid. Only the visible rows are rendered; off-screen rows are recycled.

#### Typical usage flow

1. In `build`, create the layout engine appropriate for your UI structure.
2. Add items to the engine with their controls and growth/sizing rules.
3. Apply the engine to the root control or register it with the `LayoutManager`.
4. The framework calls layout passes automatically; you do not need to call `.layout()` manually in most cases unless you are building a custom layout engine.

#### Minimal example

```python
from gui_do import FlexLayout, FlexItem, FlexDirection, PanelControl, ButtonControl, LabelControl
from pygame import Rect

def build(self, host):
    root = host.app.add(PanelControl("my_panel", Rect(0, 0, 800, 40)), scene_name="main")
    flex = FlexLayout(direction=FlexDirection.ROW, gap=8)
    flex.add(FlexItem(control=root.add(LabelControl("title", Rect(0,0,0,0), "Status:")), grow=0, basis=80))
    flex.add(FlexItem(control=root.add(LabelControl("value", Rect(0,0,0,0), "OK")), grow=1))
    flex.add(FlexItem(control=root.add(ButtonControl("close", Rect(0,0,0,0), "X", on_click=self._close)), grow=0, basis=30))
    root.set_layout(flex)
```

#### Advanced pattern

`ConstraintLayoutEngine` with `AdaptivePolicy` enables a panel that switches its constraint set at defined viewport width breakpoints. Define a `ConstraintSet` for a "wide" layout (three columns) and another for a "narrow" layout (single column), then use `AdaptivePolicy` with `Breakpoint` thresholds to select between them. `resolve_adaptive_policy(engine, viewport_width)` selects and applies the correct policy. This is the correct approach for panels that must be usable both on full-HD monitors and on smaller embedded displays.

`LayoutAnimator` smoothly interpolates between two layout states by tweening each control's bounding rect from its current position to the new position produced by a relayout pass. Use this when layout changes (adding/removing controls, expanding an expander) should be visually animated rather than instant.

#### Common mistakes and anti-patterns

- **Hardcoding pixel positions instead of using layout engines.** Hardcoded positions break on window resize and make it impossible to add new controls without manually adjusting all sibling positions. Always use a layout engine for anything that might change.
- **Mixing conflicting layout systems in one container without clear ownership.** If a container has both a `FlexLayout` and manual position assignments, the manual positions will be overwritten by the flex pass on every layout tick. Choose one layout mechanism per container.
- **Calling layout APIs before controls are added to the tree.** Some layout engines defer measurement until layout is actually run. If you configure a layout engine before all its items are added, the layout pass will produce incorrect sizes.
- **Using `VirtualizationCore` for small collections.** Virtualization has overhead: it requires item height estimation, recycling logic, and scroll position tracking. For lists with fewer than a few hundred items, a plain `ListViewControl` is simpler and performs fine.

#### Cross-links to related systems

- **8.5 Controls** — layout engines arrange control instances within containers.
- **8.7 Focus** — layout affects the spatial order of the focus ring.
- **8.9 Window Presentation** — windows use layout engines to organize their interior controls.
- **8.10 Scheduling** — `LayoutAnimator` uses the tween system from chapter 8.10.

---

### 8.7 Focus and Accessibility

[Back to Table of Contents](#table-of-contents) · [See Appendix F: Specifications and Option Reference](#f-specifications-and-option-reference) (§F.7 Accessibility Specs, §F.6 Task Panel Specs)

#### What it is and why it exists

Focus management ensures that only one control receives keyboard events at any given time, and that the user can navigate between focusable controls using Tab and Shift+Tab without touching a mouse. Without explicit focus management, keyboard input reaches all controls simultaneously, making it impossible to reason about which control "has" a key press. The focus system also handles window-level focus cycling (Alt+Tab between floating windows within a scene) and focus locking (trapping focus inside an open modal dialog).

Accessibility semantics provide a machine-readable description of the UI's structure and meaning. The `AccessibilityTree` mirrors the control tree with a parallel hierarchy of `AccessibilityNode` objects, each carrying a semantic role, name, and optional live-region politeness level. This tree is the interface point for assistive technology, automated UI testing, and screen-reader-like announcement systems. Keeping the accessibility tree consistent with the control tree is a requirement for applications that need to be usable by people with visual impairments or that need automated accessibility auditing.

#### Mental model and lifecycle placement

Focus is a cursor that moves through the focus ring — an ordered list of focusable controls in the active scene. The `FocusManager` owns this cursor. When the user presses Tab, the cursor advances to the next control in the ring; Shift+Tab reverses it. Controls join the focus ring in `build`; they must leave it (or be marked as hidden/disabled) when they become non-interactive, to prevent focus from becoming stuck on invisible targets.

Accessibility nodes are created in `build` alongside their corresponding controls and added to the `AccessibilityTree`. When control state changes — a button becomes disabled, a label's text changes — the corresponding accessibility node should be updated to reflect the change. `AccessibilityBus` delivers `AccessibilityAnnouncement` messages to registered listeners when live regions change.

#### Primary public APIs and key types

**From Tier 4 (focus):**
- `FocusManager` — owns the scene's active focus cursor; `focus(control_id)`, `advance_focus()`, `retreat_focus()`
- `FocusScope`, `FocusScopeManager` — creates a bounded focus region; focus cycling stays within the scope until the scope is deactivated. Use for modal dialogs.
- `WindowFocusManager` — coordinates per-window focus so that Alt+Tab-style window cycling works correctly; candidates sorted by `control_id` (deterministic order)
- `FocusRing` — the ordered list of focusable controls; managed by `FocusManager`

**From Tier 21 (accessibility):**
- `AccessibilityRole` — enum of semantic roles: `BUTTON`, `CHECKBOX`, `SLIDER`, `TEXT_INPUT`, `LABEL`, `PANEL`, `DIALOG`, `LIST_ITEM`, `TREE_ITEM`, `MENU_ITEM`, `TAB`, and others
- `LivePoliteness` — `OFF`, `POLITE`, `ASSERTIVE` — controls when announcements interrupt vs. queue
- `AccessibilityNode` — a semantic node carrying `role`, `name`, `description`, and `live` politeness
- `AccessibilityTree` — the root of the accessibility hierarchy; provides `root` and `find_by_id()`
- `AccessibilityAnnouncement` — a pending announcement for live-region consumers
- `AccessibilityBus` — delivers announcements to registered listeners; subscribe to receive announcements

**From Tier 1 (accessibility specs):**
- `AccessibilitySequenceSpec` — declares a scene-level sequential focus traversal order
- `StaticAccessibilitySpec` — statically names a control for accessibility (name resolved at build time)
- `TaskPanelFocusToggleSpec` — automatically excludes/includes a window's controls from the focus ring when the window is hidden/shown

#### Typical usage flow

1. Declare `StaticAccessibilitySpec` entries in the `HostApplicationBindingSpec.static_accessibility_entries` for controls with stable, meaningful names (buttons, important labels).
2. For custom rendering controls (`CanvasControl` subclasses or custom drawing), create `AccessibilityNode` instances in `build` and add them to `AccessibilityTree`.
3. Use `TaskPanelFocusToggleSpec` in `RoutedRuntimeSpec` for any window that can be hidden, to ensure focus cycling does not stall on invisible targets.
4. For modal dialogs, create a `FocusScope` that contains the dialog's controls and activate it when the dialog opens; deactivate it when the dialog closes.
5. For live-region announcements (status changes, errors), call `AccessibilityBus.announce(AccessibilityAnnouncement(...))` when the relevant state changes.

#### Minimal example

```python
from gui_do import AccessibilityTree, AccessibilityNode, AccessibilityRole, AccessibilityBus, LivePoliteness

# In build:
tree = host.accessibility_tree
status_node = AccessibilityNode(
    role=AccessibilityRole.LABEL,
    name="status_label",
    description="Shows current operation status",
    live=LivePoliteness.POLITE,
)
tree.root.add_child(status_node)

# When status changes:
bus = host.accessibility_bus
bus.announce(AccessibilityAnnouncement(node_id=status_node.id, message="Operation complete"))
```

#### Advanced pattern

`AccessibilitySequenceSpec` declares an explicit scene-level focus traversal order — a list of control IDs in the intended Tab order. This is useful when the spatial order of controls in the layout does not match the logical Tab order (for example, when a form's fields are arranged in two columns but should be tabbed top-to-bottom, left-then-right). The framework applies the declared sequence after `build`, overriding the default spatial ordering.

`FocusScope` with a `FocusScopeManager` traps focus inside an open modal dialog or popover. Create the scope before showing the dialog; all Tab navigation stays within the scope's registered controls until the scope is deactivated. This prevents users from accidentally tabbing to controls behind a modal without closing it first.

#### Common mistakes and anti-patterns

- **Leaving hidden windows in the focus ring.** If a window is hidden (by toggling its visibility) but its controls remain in the focus ring, pressing Tab will cycle to those invisible controls — which appears to the user as Tab "doing nothing." Always use `TaskPanelFocusToggleSpec` or explicitly remove hidden controls from the ring.
- **Forgetting semantic roles on canvas-based custom controls.** A `CanvasControl` that functions as a button has no automatic accessibility role. Without an `AccessibilityNode`, it is invisible to assistive technology and automated accessibility testing. Add an `AccessibilityNode` with the correct role for every custom interactive control.
- **Using live politeness `ASSERTIVE` for non-critical updates.** `ASSERTIVE` interrupts the user immediately; reserve it for errors and urgent alerts. Use `POLITE` for informational status updates that should wait until the user is not busy.
- **Building accessibility nodes before the tree is initialized.** If `host.accessibility_tree` is not available in `build` (because the host does not declare it in `HOST_REQUIREMENTS`), adding nodes will fail. Declare `accessibility_tree` in `HOST_REQUIREMENTS` for the build phase.

#### Cross-links to related systems

- **8.3 Events** — keyboard events reach the focused control; `FocusManager` updates focus in response to Tab events.
- **8.5 Controls** — controls register with the focus ring and carry accessibility roles.
- **8.8 Overlays** — modal overlays use `FocusScope` to trap focus within their bounds.
- **8.9 Scene and Window Presentation** — `TaskPanelFocusToggleSpec` coordinates focus exclusion with window visibility.

---

### 8.8 Overlays, Dialogs, Notifications, and Command Surfaces

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Overlays are transient surfaces — dialogs, toasts, context menus, tooltips, the command palette, drag previews, shortcut help — that appear on top of the main control tree and require their own routing layer so they do not destabilize main control event flow. Without a dedicated overlay system, implementing a modal dialog requires the feature to manually disable all background controls, intercept all keyboard events, and re-enable everything on dismiss — a complex, error-prone, and untestable process. gui_do provides a family of overlay managers, each handling one surface kind with the correct dismissal contract and event-interception semantics.

The design principle is separation by surface kind: toasts, dialogs, context menus, command palette, tooltips, and shortcuts each have their own manager because each has subtly different dismissal rules, animation requirements, and event-handling semantics. Combining them into a single generic "show a popup" API would force every feature to handle concerns that are irrelevant to its specific surface kind.

#### Mental model and lifecycle placement

Overlays sit above the main control tree in a dedicated rendering layer. The overlay routing system processes events first — before the main control tree sees them. If an overlay consumes an event (by returning `True` from its event handler), the main tree never sees it. This is the correct behavior for modal dialogs (all events are consumed until the dialog is dismissed) but incorrect for non-modal toasts (which should not consume events that the main tree also needs to see). Each manager handles this distinction correctly for its surface kind.

Overlay managers are accessed through the host (e.g., `host.toasts`, `host.dialogs`) and are available in both `build` and the operational phase. Most overlay operations happen during event handling or in response to user actions, not during `build`.

#### Primary public APIs and key types

**From Tier 9:**
- `OverlayManager`, `OverlayHandle` — generic overlay surface management; `show(control, ...)`, `dismiss(handle)`
- `Alignment`, `PlacementResult`, `PopupPlacement`, `Side`, `compute_popup_rect` — compute a screen rect for an overlay that avoids clipping at viewport edges, given an anchor rect and preferred placement side
- `DialogManager`, `DialogHandle` — modal and non-modal dialog management with dismiss-on-escape, dismiss-on-outside-click, and focus trapping
- `ToastManager`, `ToastHandle`, `ToastSeverity` — non-blocking notification toasts with configurable duration, severity (`INFO`, `SUCCESS`, `WARNING`, `ERROR`), and optional click handler
- `ContextMenuManager`, `ContextMenuItem`, `ContextMenuHandle` — right-click context menus with hierarchical items and keyboard navigation
- `CommandPaletteManager`, `CommandEntry`, `CommandPaletteHandle` — searchable command palette with action registry integration and dynamic entry population
- `TooltipManager`, `TooltipHandle` — hover-triggered tooltip popups with dwell-time configuration
- `MenuBarManager` — application menu bar manager
- `FileDialogManager`, `FileDialogOptions`, `FileDialogHandle` — file open/save dialog with filter configuration
- `NotificationCenter`, `NotificationRecord` — persistent notification history with severity and read/unread tracking
- `ResizeManager` — handles resize drag operations on resizable window borders
- `CursorManager`, `CursorHandle`, `CursorShape` — per-context cursor shape management; stacks cursor overrides by priority
- `DragDropManager`, `DragPayload` — pointer drag-and-drop with drag-start detection, drag-enter/leave/drop routing to registered targets
- `ClipboardManager` — cross-control clipboard copy/paste
- `TransferData`, `TransferManager` — structured data transfer between controls (drag-and-drop data model)
- `ShortcutHelpOverlay`, `ShortcutSection`, `ShortcutEntry` — full-screen or panel shortcut help overlay populated from the action registry

**From Tier 1 (spec types):**
- `ShortcutOverlaySpec` — declares shortcut overlay configuration in `RoutedRuntimeSpec`
- `NotificationSpec` — declares a notification's content and severity

#### Dismissal contracts

Each overlay surface type has a specific dismissal contract that the manager enforces automatically:

- **Toasts** — shown for a configured duration, then automatically dismissed. Pointer events inside the toast bounds are consumed (no click-through to underlying controls). The optional `on_click` callback fires on intentional toast clicks.
- **Dialogs** — modal by default: all events are intercepted until the dialog is dismissed. Configure `dismiss_on_escape=True` for Escape-key dismissal. Configure `dismiss_on_outside_click=True` for click-outside dismissal. The `DialogHandle.on_dismiss` callback fires on any dismissal.
- **Context menus** — dismissed on outside click, Escape, or item selection. Click events on items are consumed.
- **Command palette** — dismissed on Escape or item selection. All keyboard events are consumed while open; pointer events outside the palette are consumed.
- **Tooltips** — shown after a hover dwell time; dismissed on pointer leave or when a competing event fires.
- **Shortcut help overlay** — shown on a configurable toggle key; dismissed on the same key or on Escape.

#### Typical usage flow

1. In `build`, do not show overlays; overlays are shown in response to user actions during the operational phase.
2. In `handle_event` or an `on_click` callback, call the appropriate manager's `show` or `display` method.
3. Store the returned handle if you need to dismiss programmatically or subscribe to the dismiss callback.
4. For command palette, populate `CommandEntry` instances from the action registry or from feature-specific commands.
5. For file dialogs, configure `FileDialogOptions` with file filter, initial directory, and title.

#### Minimal example

```python
from gui_do import ToastSeverity

# In a button's on_click handler:
def _on_save_clicked(self):
    # ... perform save operation ...
    host.toasts.show("File saved successfully", severity=ToastSeverity.SUCCESS, duration=3.0)

# Modal dialog:
def _on_delete_clicked(self):
    handle = host.dialogs.show(
        ConfirmDialogControl("confirm", "Delete this item?"),
        modal=True,
        dismiss_on_escape=True,
    )
    handle.on_dismiss = lambda confirmed: self._perform_delete() if confirmed else None
```

#### Advanced pattern

`ShortcutHelpOverlay` with `ShortcutOverlaySpec` provides a complete shortcut reference surface that is populated automatically from the action registry. Configure it via `RoutedRuntimeSpec.shortcut_overlay` with `toggle_action_name`, a list of `ShortcutSection` descriptors for manual sections, `exclude_section_titles` for sections that should be hidden, and `manual_shortcut_lines` for lines not driven by the registry. The overlay renders as a full-screen or bounded panel that the user can toggle at any time. This replaces the need to manually maintain a "help" screen with hardcoded shortcut lists.

`CommandPaletteManager` with dynamic `CommandEntry` population supports applications where the available commands change based on context (which window is active, what is selected, what scene is current). Register a `custom_entries_provider` callable in `PaletteBindingSpec`; it is called each time the palette opens and can return the current context-appropriate entry list. Combined with `include_scene_entries` and `include_window_entries`, this produces a fully dynamic command palette with no manual maintenance.

#### Common mistakes and anti-patterns

- **Showing overlays in `build`.** Overlays are runtime artifacts; they should be created in response to user actions, not during scene construction. Showing a dialog in `build` will display it before the user has had any interaction with the scene.
- **Allowing overlays without a dismissal path.** An overlay that cannot be dismissed (no Escape binding, no outside-click dismiss, no close button) traps the user. Always configure at least one dismissal mechanism.
- **Expecting toast events to pass to underlying controls.** Toasts consume pointer events within their bounds. A toast that appears over an interactive control will block pointer events to that control for the duration of the toast's visibility.
- **Checking `OverlayHandle` validity after an overlay has been dismissed.** After dismissal, the handle is invalidated. Calling methods on a dismissed handle produces errors. Always check handle validity or use the `on_dismiss` callback pattern instead.
- **Using `CursorManager` without matching push/pop semantics.** Cursor overrides are stacked. If you push a cursor override (e.g., a resize cursor) and never pop it, the cursor will remain in the override state indefinitely. Always pair cursor push with pop in a cleanup path.

#### Cross-links to related systems

- **8.3 Events and Actions** — the command palette is activated via a configured action key; overlay managers intercept events before scene dispatch.
- **8.7 Focus and Accessibility** — modal dialogs use `FocusScope` to trap focus within their bounds.
- **8.9 Scene Presentation** — the command palette activation key is declared per-scene in `SceneCommandPaletteSpec`; shortcut overlays are wired via `RoutedRuntimeSpec`.

---

### 8.9 Scene, Window, and Task-Panel Presentation Models

[Back to Table of Contents](#table-of-contents) · [See Appendix F: Specifications and Option Reference](#f-specifications-and-option-reference) (§F.2 Feature and Scene Specs, §F.5 Window and Presentation Specs, §F.6 Task Panel Specs)

#### What it is and why it exists

Scenes, windows, and task panels are the three nested levels of gui_do's presentation model. Scenes define broad application modes — the full-screen state of the application with a specific set of features, a specific background, and a specific set of available actions. Windows are floating or anchored UI surfaces within a scene, each managed by a `WindowControl` and associated `WindowPresenter`. The task panel is a persistent chrome strip at the edge of the scene that houses toggle buttons for windows and scene-navigation controls.

This layered model exists because GUI applications have fundamentally different levels of UI scope. A "main scene" and a "settings scene" require completely different sets of features and a completely different root layout — that is scene scope. Within the main scene, a "system info" window and a "life simulation" window can be independently shown and hidden by the user — that is window scope. The task panel provides a consistent, always-visible entry point to window visibility without requiring features to implement their own show/hide UI. Each level has its own lifecycle, its own event routing priority, and its own accessibility integration.

#### Mental model and lifecycle placement

Think of scenes as top-level modes. Only one scene is active at a time; transitioning between scenes replaces the entire active feature set. Windows within a scene are independent floating surfaces: the user can show, hide, move, and resize them without affecting other windows or the underlying scene. The task panel is always visible when configured and provides the primary mechanism for the user to discover and toggle windows.

`ScenePresentationModel` is the runtime object that coordinates all of these: it tracks which windows are registered in the active scene, their visibility state, their task panel associations, and their accessibility metadata. Features access it through the host during `build` and `bind_runtime` to register their windows and subscribe to visibility change events.

#### Primary public APIs and key types

**From Tier 1 (spec types):**
- `ScenePresentationModel` — tracks registered windows, visibility state, and coordinates window/task-panel synchronization
- `WindowSpec` — declares a feature window with its key, feature attribute, toggle action, task panel button, and accessibility label
- `AnchoredWindowSpec` — declares a window with specific anchoring, size, and chrome configuration
- `SceneTaskPanelSpec` — configures the task panel strip for a scene (height, position, background)
- `TaskPanelButtonSpec` — declares one task panel button
- `TaskPanelLinearLayoutSpec` — linear layout strategy for task panel items
- `TaskPanelWindowToggleGroupSpec` — a group of task panel toggle buttons automatically created from registered windows
- `TaskPanelFocusToggleSpec` — wires focus-ring exclusion to window visibility changes
- `TaskPanelSceneNavButtonSpec` — a scene-navigation button in the task panel
- `FeatureWindowBundleBindingSpec` — bundles a feature, its window, its task panel button, and its toggle action into a single spec
- `WindowToggleBindingSpec` — lower-level version of the window bundle spec for existing features
- `TabbedPresenterSpec` — declares a tabbed window layout with multiple `TabBuilderSpec` tabs
- `TabBuilderSpec` — declares one tab's content factory and label
- `SceneCommandPaletteSpec` — declares the command palette activation key for a scene

**From Tier 18 (presentation helpers):**
- `set_window_visible_state` — programmatically show/hide a window and synchronize task panel button state
- `toggle_window_visibility` — toggle a window's visibility and synchronize
- `create_anchored_feature_window` — create a floating anchored window from an `AnchoredWindowSpec`
- `create_feature_presented_window` — create a window wired to a `WindowPresenter`
- `create_presented_anchored_window`, `create_presented_window_from_spec` — presenter-pattern window creation variants
- `add_window_scene_menu_strip`, `add_standard_scene_menu_strip` — add a scene menu strip showing scene-navigation and window-toggle menus
- `ensure_scene_task_panel`, `add_task_panel_buttons`, `add_task_panel_window_toggle_group`, `add_task_panel_scene_nav_button`, `add_scene_task_panel_items` — build and populate the task panel
- `add_window_toggle_task_panel_controls`, `register_window_toggle_tooltips`, `apply_window_toggle_accessibility` — detailed window-toggle wiring helpers
- `ActiveTabUpdateRouter` — routes update messages to the currently active tab's feature
- `TabLayoutContext` — context object passed to `TabBuilderSpec` factories
- `build_host_main_tab_order`, `apply_host_main_accessibility` — scene-level tab order and accessibility helpers
- `WindowRelativeRect` — rect expressed relative to a window's bounds rather than screen space
- `inset_rect`, `centered_horizontal_strip_layout`, `split_slot_bounds`, `partition_rects` — layout geometry helpers
- `place_control`, `place_control_unlabeled`, `register_placed_control`, `add_group_label`, `PlacedControl`, `make_labeled_slot_height_fn` — slot-based control placement helpers for property panels
- `minimize_window_menu_entries`, `build_tools_menu_entries` — scene menu entry builders

#### Typical usage flow

1. Declare scenes via `SceneBundleBindingSpec` in `HostApplicationBindingSpec.scene_bundle_entries`.
2. For each feature that owns a window, use `FeatureWindowBundleBindingSpec` — this single spec wires the feature, window, task panel toggle, and toggle action together.
3. Implement `WindowPresenter` as the window's internal layout manager; instantiate it in the feature's `build`.
4. Use `ensure_scene_task_panel` in `build` to create the task panel strip.
5. For tabbed windows, declare `TabbedPresenterSpec` with one `TabBuilderSpec` per tab; the framework creates the tab strip and wires switching automatically.
6. Use `TaskPanelFocusToggleSpec` in `RoutedRuntimeSpec` to auto-manage focus on window show/hide.

#### Minimal example

```python
from gui_do import (
    RoutedFeature, WindowPresenter, AnchoredWindowSpec, create_anchored_feature_window
)

class MyWindowPresenter(WindowPresenter):
    def build(self, host, window: WindowControl):
        window.add(LabelControl("info", Rect(8, 8, 200, 30), "Hello from window"))

class InfoFeature(RoutedFeature):
    HOST_REQUIREMENTS = {"build": ["app", "scene_presentation"]}
    def __init__(self):
        super().__init__(scene_name="main")
    def build(self, host):
        presenter = MyWindowPresenter()
        spec = AnchoredWindowSpec(
            control_id="info_window",
            title="Info",
            anchor="top_right",
            size=(300, 200),
        )
        create_anchored_feature_window(host, presenter, spec)
```

#### Advanced pattern

Multi-window scenes with `TabbedPresenterSpec` and `ActiveTabUpdateRouter` enable complex IDE-style interfaces. Each window declares its tab content via `TabBuilderSpec` factories. `ActiveTabUpdateRouter` ensures that `on_update` calls are routed only to the factory whose tab is currently selected, preventing off-screen tabs from consuming frame budget. Combined with `add_standard_scene_menu_strip`, the scene menu strip automatically populates with scene-navigation and window-toggle entries, requiring no manual menu maintenance.

For scenes with many windows, `TaskPanelWindowToggleGroupSpec` automatically creates one toggle button per registered window and arranges them in a group starting at a declared slot index. This eliminates the need to declare individual `TaskPanelButtonSpec` entries for each window; the group spec is updated automatically when windows are added or removed.

#### Common mistakes and anti-patterns

- **Mismatching scene scope and window scope for action handlers.** An action declared as scene-scoped fires for the entire scene; an action declared as window-scoped fires only when that window has focus. Ensure action scopes match the intended interaction model.
- **Not synchronizing task panel button state with window visibility.** The `set_window_visible_state` and `toggle_window_visibility` helpers handle synchronization automatically. If you show/hide windows manually without using these helpers, the task panel button will show an incorrect state.
- **Creating windows in `bind_runtime` instead of `build`.** Window controls must exist when sibling features run their `build` phase (since siblings may reference windows by their `control_id`). Create all windows in `build`.
- **Forgetting `TaskPanelFocusToggleSpec`.** Without this spec, hiding a window does not remove its controls from the focus ring. Users will experience Tab "stalling" on invisible controls.

#### Cross-links to related systems

- **8.2 Feature Lifecycle** — `WindowPresenter` is instantiated in `build`; window wiring is completed in `bind_runtime`.
- **8.5 Controls** — `WindowControl` is a Tier 13 control; `WindowPresenter` builds its interior.
- **8.7 Focus** — `TaskPanelFocusToggleSpec` coordinates focus with window visibility.
- **8.8 Overlays** — overlay managers share the scene's overlay rendering layer with window chrome.

---

### 8.10 Scheduling, Timing, Animation, and Transitions

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Time-based work — animations, timed callbacks, cooperative background tasks, rate-limited event handlers — must execute within the application's frame budget. Running expensive computation synchronously in `on_update` causes frame drops because it blocks the pygame event loop. gui_do provides a layered scheduling system that lets features express time-based work at the right level of abstraction, from simple one-shot timers up to full cooperative multi-step coroutines that yield control on every frame.

The system is built around the principle that the application must remain responsive at all times. The `CooperativeScheduler`'s budget contract ensures that coroutine work never consumes more than a bounded slice of each frame's time. The `TweenManager` integrates into the update loop automatically, requiring no per-feature update calls. `AnimationStateMachine` drives animated state without requiring manual state management in `on_update`. Together, these abstractions keep `on_update` methods lean — each one should express intent, not implement a scheduler.

#### Mental model and lifecycle placement

The scheduler is a per-scene resource accessed through the host. Features register coroutines, tweens, and timers in `build` or `bind_runtime`; the framework calls them on each frame within the appropriate budget. The operational phase (`on_update`) is where features check the results of scheduled work and respond, not where they perform the work.

The scheduling stack has three layers:
1. **Timers and tweens** — for duration-bounded, simple time-based work (fade in/out, delayed callbacks).
2. **Animation sequences and state machines** — for multi-step or state-driven animation logic.
3. **`CooperativeScheduler` coroutines** — for arbitrarily complex multi-frame workflows.

#### Primary public APIs and key types

**From Tier 5:**
- `TaskEvent`, `TaskScheduler` — the core per-frame dispatch scheduler; processes queued tasks within a frame budget
- `Timers` — fire a callback after a delay (`after`), or repeatedly (`every`); cancel with the returned handle
- `TweenManager`, `TweenHandle`, `Easing` — interpolate a property on an object from current to target value over a duration using an easing function; `TweenHandle` allows cancellation and chaining
- `AnimationSequence`, `AnimationHandle` — a scripted sequence of tween and wait steps
- `TransitionManager`, `TransitionSpec`, `TransitionEvent` — manages named scene-level transitions with enter/exit animation specs
- `AnimationStateMachine`, `AnimationTransitionMode` — state-machine-driven animation: declare states and transitions; the machine drives sequences based on active state
- `SceneTimeline` — a sequence of timed events relative to scene entry; useful for tutorial flows and scripted demo sequences
- `Debouncer`, `Throttler` — rate-limiting: `Debouncer` fires only after a quiet period (use for search input); `Throttler` fires at most once per interval (use for resize handlers)
- `CooperativeScheduler`, `CoroutineHandle` — runs Python generator-based coroutines within the frame budget
- `Pause`, `Sleep`, `WaitForEvent`, `WaitForSignal`, `WaitUntil`, `WaitForAll` — yield primitives for coroutines; suspend a coroutine until a condition is met

**From Tier 26:**
- `CancellationToken`, `PipelineStage`, `DataflowPipeline`, `PipelineHandle` — thread-safe multi-stage processing pipeline with stale-generation cancellation; the bridge between background threads and the reactive observable layer

#### Scheduler budget contract

The `TaskScheduler` dispatch budget is contractually defined in `docs/runtime_operating_contracts.md` Section 6:
- `fraction`: 0.12 of the frame's elapsed milliseconds
- `floor`: 0.5 ms — minimum budget per frame, regardless of dt
- `ceiling`: 4.0 ms — maximum budget per frame, regardless of dt

These bounds ensure that the scheduler processes messages on every frame (no starvation) without consuming a runaway share of frame time (no ceiling bypass under slow frames). Features using `CooperativeScheduler` should yield frequently — at least once per few milliseconds of computation — to stay within budget.

#### Typical usage flow

1. For a simple delayed callback, use `host.timers.after(delay_seconds, callback)`.
2. For a smooth animation, use `host.tweens.to(target_object, "property_name", end_value, duration=0.3, easing=Easing.EASE_OUT)`.
3. For a multi-step workflow that spans multiple frames, implement it as a Python generator function using `yield Sleep(t)`, `yield WaitForEvent(...)`, etc., and run it with `host.scheduler.run(my_coroutine())`.
4. For heavy computation, implement it as a `DataflowPipeline` with one or more `PipelineStage` callables; retrieve results in `on_update` and publish them to observable values.
5. For rate-limited event handling, wrap the handler in a `Debouncer` or `Throttler`.

#### Minimal example

```python
from gui_do import TweenManager, Easing, CooperativeScheduler, Sleep

class FadeInFeature(Feature):
    def build(self, host):
        self.panel = host.app.add(PanelControl("panel", Rect(0, 0, 400, 300)), scene_name="main")
        self.panel.alpha = 0

    def bind_runtime(self, host):
        # Fade in over 0.5 seconds on scene entry
        host.tweens.to(self.panel, "alpha", 255, duration=0.5, easing=Easing.EASE_OUT)

    # Coroutine example:
    def _run_workflow(self, host):
        yield Sleep(1.0)
        host.toasts.show("Ready!")
        yield WaitForEvent("user_confirmed")
        host.toasts.show("Processing...")

    # Start in bind_runtime: host.scheduler.run(self._run_workflow(host))
```

#### Advanced pattern

`CooperativeScheduler` with `WaitForSignal` enables multi-step user workflows that are written as linear-looking coroutines but execute across many frames. For example, a "guided tour" coroutine can show a tooltip, `yield WaitForSignal(user_closed_tooltip)`, advance to the next element, show another tooltip, and so on — all in a single generator function with no state machine. The `CoroutineHandle` returned by `host.scheduler.run(...)` allows the coroutine to be canceled if the user navigates away before it completes.

`AnimationStateMachine` is the tool for controls with complex visual states (hover, pressed, focused, disabled, animated transitions between them). Declare named states with `AnimationSequence` entries and transitions with `AnimationTransitionMode` (instant, cross-fade, complete-first). The state machine handles the transition timing and sequencing automatically; the feature only calls `machine.set_state("hovered")`.

#### Common mistakes and anti-patterns

- **Running expensive computation in `on_update` without `CooperativeScheduler`.** A computation that takes 5 ms in `on_update` adds 5 ms to every frame. Use a coroutine or `DataflowPipeline` to spread the work across frames or a background thread.
- **Creating coroutines with blocking I/O inside.** A coroutine that calls `time.sleep()`, `requests.get()`, or any blocking call will block the entire event loop for the duration. Use `DataflowPipeline` for work that involves blocking I/O; only yield-based suspension is safe inside coroutines.
- **Not canceling tweens and timers on scene exit.** Tweens registered with `host.tweens` that are not canceled before scene exit may attempt to mutate properties on controls that no longer exist. Cancel all tweens in `shutdown_runtime`.
- **Using `Throttler` where `Debouncer` is needed.** A `Throttler` fires at most once per interval, even if events keep arriving — it fires immediately on the first event and suppresses the rest. A `Debouncer` waits until a quiet period. For search input, debounce (wait until typing stops); for resize, throttle (process the most recent resize at a limited rate).

#### Cross-links to related systems

- **8.2 Feature Lifecycle** — scheduling is registered in `build`/`bind_runtime` and canceled in teardown.
- **8.14 Data and Dataflow** — `DataflowPipeline` bridges background computation to reactive observable state.
- **8.15 Graphics** — `SceneGraph2D` and `ParticleSystem` update on each frame tick driven by the scheduler.
- **8.16 Telemetry** — telemetry spans cover the scheduler dispatch path for performance monitoring.

---

### 8.11 Persistence and Workspace/Session State

[Back to Table of Contents](#table-of-contents) · [See Appendix F: Specifications and Option Reference](#f-specifications-and-option-reference) (§F.9 Persistence and Migration Specs)

#### What it is and why it exists

Application users expect their session state — which windows are open, what values they entered in settings fields, which scene they were viewing — to survive application restarts. gui_do provides a workspace persistence layer that saves a structured snapshot of session state to disk and restores it on the next launch. The restore process is deliberately fault-tolerant: unknown settings keys are skipped rather than causing crashes, missing settings blocks are logged rather than aborting the restore, and the entire restore process produces a structured report that features can inspect to understand what was and was not successfully restored.

Beyond session persistence, the system also provides command history (undo/redo), named undo context routing for multi-panel applications, versioned snapshot migration for evolving schemas, and a settings registry that provides typed, validated, declaratively registered settings with automatic round-trip support.

#### Mental model and lifecycle placement

The workspace is a JSON snapshot. At save time, the workspace manager calls each registered feature's `save_state` method and collects the resulting dictionaries into a structured file. At restore time, it replays those dictionaries to the corresponding features' `load_state` methods, applies settings registry entries, switches to the saved scene, and restores scene snapshots. The restore report is the authoritative record of what happened.

Features interact with persistence primarily in `bind_runtime` (loading initial state from a restored workspace) and in `shutdown_runtime` (saving state before teardown). The `SettingsRegistry` integrates with the workspace automatically: settings registered via `SettingDescriptor` are saved and restored without any explicit feature code.

#### Primary public APIs and key types

**From Tier 11:**
- `CommandHistory`, `Command`, `CommandTransaction` — undo/redo stack; `Command` is an executable+undoable pair; `CommandTransaction` groups multiple commands into a single undo step
- `StateMachine` — simple finite state machine with named states and transitions
- `HierarchicalStateMachine` — nested/hierarchical state machine for complex state topologies
- `Router`, `RouteEntry` — URL-style routing for application navigation state
- `SettingsRegistry`, `SettingDescriptor` — typed setting declaration; settings automatically participate in workspace save/restore
- `WorkspaceState`, `WorkspacePersistenceManager`, `DEFAULT_WORKSPACE_STATE_PATH` — workspace save/load/restore management; `restore` returns a structured report with the fields from the contract document
- `SceneSnapshot`, `NodeSnapshot` — typed snapshot objects for scene and control node state

**From Tier 23:**
- `UndoContextManager` — named multi-stack undo/redo routing; multiple UI panels can have independent undo stacks routed through one manager

**From Tier 32:**
- `SchemaVersion`, `VersionedSnapshot`, `MigrationStep`, `MigrationRegistry`, `SnapshotMigrator`, `MigrationError` — versioned persistence with BFS migration graph and composable migration steps
- `make_snapshot`, `read_version` — create a new `VersionedSnapshot` and extract version from a raw snapshot dict

#### Workspace restore report fields

The restore report returned by `WorkspacePersistenceManager.restore` and `GuiApplication.load_workspace` contains the following fields (from `docs/runtime_operating_contracts.md` Section 4):

- `target_scene` — the scene name the workspace requested to restore to
- `switched_scene` — whether a scene switch was actually performed
- `restored_feature_states` — list of feature attributes whose states were restored
- `restored_scene_nodes` — list of scene node IDs whose snapshots were restored
- `applied_settings` — list of settings keys that were successfully applied
- `skipped_settings` — list of settings keys that were skipped (value failed validation)
- `missing_settings_blocks` — list of settings blocks in the snapshot that had no matching registry entry

#### Typical usage flow

1. Declare settings via `SettingsRegistry.register(SettingDescriptor(...))` in `build`.
2. In `bind_runtime`, read restored setting values from the registry and initialize observable state.
3. In `shutdown_runtime`, any custom state that the settings registry does not cover can be saved manually to a feature state dictionary.
4. Call `host.app.save_workspace(path)` before exit; call `host.app.load_workspace(path)` on startup.
5. Inspect the restore report to show warnings for skipped settings.

#### Minimal example

```python
from gui_do import SettingsRegistry, SettingDescriptor, WorkspacePersistenceManager

class SettingsFeature(Feature):
    HOST_REQUIREMENTS = {"build": ["settings_registry"], "bind_runtime": ["settings_registry"]}

    def build(self, host):
        host.settings_registry.register(SettingDescriptor(
            key="ui.show_grid",
            type=bool,
            default=True,
            label="Show grid overlay",
        ))

    def bind_runtime(self, host):
        show_grid = host.settings_registry.get("ui.show_grid")
        self._show_grid = ObservableValue(show_grid)

# Save/load via app:
# host.app.save_workspace("session.json")
# report = host.app.load_workspace("session.json")
```

#### Advanced pattern

`SnapshotMigrator` with a `MigrationRegistry` enables safe schema evolution as an application grows. When the snapshot schema changes — a field is renamed, a new required field is added, a nested structure is reorganized — register a `MigrationStep` that transforms snapshots from schema version N to version N+1. On load, call `read_version(raw_snapshot)` to determine the current version, then call `SnapshotMigrator.migrate(snapshot, target_version)` to walk the BFS migration graph to the current version. This ensures that user workspaces saved with any previous version of the application can be loaded with the current version without data loss.

`UndoContextManager` is the correct approach for applications with multiple independent editing contexts (for example, a document editor with separate undo stacks for text editing and for diagram editing). Register each context with a unique name; route undo/redo actions to the currently focused context. This provides the expected per-context undo behavior without requiring each editing panel to implement its own undo stack management.

#### Common mistakes and anti-patterns

- **Assuming all settings keys always exist after restore.** The restore report's `skipped_settings` and `missing_settings_blocks` fields tell you what was not restored. Always read these fields and handle the case where a setting was not restored (for example, by using the `SettingDescriptor`'s default value).
- **Restoring snapshots without version checking.** Always call `read_version(raw_snapshot)` before attempting to use a snapshot's fields. A snapshot written by an older version of the application may have a different field structure.
- **Using `DEFAULT_WORKSPACE_STATE_PATH` in multi-instance scenarios.** If two instances of the application run simultaneously and both read/write the same path, they will corrupt each other's workspaces. Use per-instance paths in multi-instance configurations.
- **Not using `CommandTransaction` for multi-step operations.** If a user action modifies multiple independent pieces of state, wrapping all modifications in a `CommandTransaction` ensures that a single Ctrl+Z undoes the entire operation atomically rather than requiring the user to press Ctrl+Z once for each individual change.

#### Cross-links to related systems

- **8.1 Bootstrap** — workspace persistence policy is configured as part of the bootstrap config.
- **8.2 Feature Lifecycle** — `load_state`/`save_state` methods are part of the feature lifecycle for features that participate in workspace persistence.
- **8.4 State and Observables** — settings values are loaded from the registry and bound to observable state in `bind_runtime`.
- **8.16 Telemetry** — workspace restore telemetry spans provide observability into restore performance.

---

### 8.12 Theme, Styling, and Visual Systems

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Theming centralizes the design decisions — colors, fonts, spacing, border radii, icon sizes — that give an application its visual identity. Without a theming system, these values are scattered as magic literals throughout control rendering code, making it impossible to change the application's appearance without touching dozens of files. gui_do's theming system consolidates all of these decisions into named `ColorTheme` and `DesignTokens` objects that controls read at render time, and a `ThemeInvalidationBus` that notifies all cached rendered surfaces when the theme changes so they can flush their caches and re-render with the new values.

The system is also the mechanism for font management. `FontManager` loads font files and provides rendered font objects by size and style. `FontRoleRegistry` maps semantic role names ("heading", "body", "caption", "controls.label") to font configurations, so controls can request a font by role without knowing which font file implements that role. This decoupling means that swapping a body font requires only a change to the font role configuration, not a change to every control that renders text.

#### Mental model and lifecycle placement

The theme is a shared resource held by `ThemeManager`. Controls read from `ThemeManager.current_theme` and `ThemeManager.design_tokens` at render time. When the theme changes, controls do not poll for changes; instead, the `ThemeInvalidationBus` broadcasts an invalidation signal to all registered subscribers (cached surface maps, pre-rendered text, computed color values), which flush their caches and re-render on the next frame.

Font roles are set up at application startup in `build`, using `setup_standard_font_roles` or `FontRoleBindingSpec` entries in the bootstrap config. Once registered, roles are stable for the application's lifetime — they do not change when the theme changes (only the theme's color tokens change).

#### Primary public APIs and key types

**From Tier 6:**
- `FontManager` — loads font files and provides `pygame.font.Font` instances by role, size, bold, and italic; accessed via `host.font_manager`
- `FontRoleRegistry` — maps semantic role names to font configurations; `define(role_name, ...)`, `resolve(role_name)`, `get_font(role_name)`
- `ColorTheme` — a named mapping from semantic color role names to RGBA tuples; contains all color decisions for one visual theme
- `ThemeManager`, `DesignTokens` — the runtime theme manager; `set_theme(name)` switches themes; `design_tokens` provides named scalar and color values
- `ScopedTheme`, `ScopedThemeManager` — apply a local theme override to a subtree without affecting the global theme; useful for dark-sidebar-in-light-app patterns

**From Tier 22:**
- `ThemeInvalidationBus` — broadcast channel for theme change notifications; register caches here with `subscribe(callback)`; call `invalidate()` when the theme changes to flush all registered caches

**From Tier 1 (spec types):**
- `FontRoleBindingSpec` — declares a semantic font role mapping in the bootstrap config
- `CursorSpec`, `CursorBindingSpec` — declares cursor shapes for different interaction states
- `setup_standard_font_roles` — convenience function to register a standard set of font roles from a font config dictionary

#### Typical usage flow

1. Declare `fonts` in `HostApplicationBindingSpec` mapping short names to font file paths or config dicts.
2. Declare `font_role_entries` as `FontRoleBindingSpec` instances mapping semantic role names to font configurations.
3. Controls request fonts by role name from `host.font_manager` at render time.
4. To support theme switching, define multiple `ColorTheme` instances and call `host.theme_manager.set_theme(new_theme_name)` when the user changes themes.
5. Register surface caches with `ThemeInvalidationBus` so they flush on theme switch.

#### Minimal example

```python
from gui_do import ThemeManager, ColorTheme, DesignTokens, ThemeInvalidationBus

# Declaring a color theme:
light_theme = ColorTheme(
    name="light",
    colors={
        "surface": (255, 255, 255, 255),
        "on_surface": (30, 30, 30, 255),
        "primary": (70, 130, 180, 255),
        "border": (200, 200, 200, 255),
    }
)

# Switching themes:
# host.theme_manager.set_theme("light")

# Registering a cache for invalidation:
class MyRenderedTextCache:
    def __init__(self, bus: ThemeInvalidationBus):
        self._cache = {}
        bus.subscribe(self._flush)

    def _flush(self):
        self._cache.clear()
```

#### Advanced pattern

`ScopedThemeManager` enables per-subtree theme overrides. A window that should render in a "dark" style while the overall application uses a "light" theme creates a `ScopedTheme` with the dark color overrides and registers it with the `ScopedThemeManager`. Controls inside that window read from the scoped theme rather than the global theme. This is the correct approach for UI patterns like dark sidebars, "night mode" panels, or differentiated visual treatment for specific windows.

For applications that allow users to define custom themes (branding tools, presentation applications), the combination of `ColorTheme` (which is a pure data class) and `ThemeInvalidationBus` (which handles cache flushing) makes runtime theme switching straightforward: construct a new `ColorTheme` from the user's color choices, call `theme_manager.register_theme(new_theme)`, then `theme_manager.set_theme(new_theme.name)`. The invalidation bus handles the rest.

#### Common mistakes and anti-patterns

- **Hardcoding color literals in feature or control rendering code.** Color literals scattered through rendering code cannot be updated by theme switching. Always use `host.theme_manager.current_theme.get_color("semantic_name")` or `DesignTokens` values.
- **Switching themes without triggering `ThemeInvalidationBus`.** If you replace the active theme without calling `bus.invalidate()`, all cached rendered surfaces will continue to show old colors until they happen to be regenerated. Always pair theme switching with invalidation.
- **Registering font roles after controls have been constructed.** Controls capture their font reference during `build`. If font roles are registered after `build` (for example, in `bind_runtime`), controls may use fallback fonts or fail to find the role. Always register font roles in the bootstrap config or at the very start of `build`.
- **Using pixel-hardcoded spacing instead of `DesignTokens`.** Spacing values (padding, gap, border width) belong in `DesignTokens` so they can be adjusted for different display densities or theme variants.

#### Cross-links to related systems

- **8.1 Bootstrap** — font and cursor configuration is declared in `HostApplicationBindingSpec`; font role binding specs are resolved during the build pass.
- **8.5 Controls** — controls read color and font values from the theme system at render time.
- **8.15 Graphics** — graphics rendering code should use `ColorTheme` colors rather than hardcoded literals.
- **8.16 Telemetry** — theme switch events can be tracked as telemetry spans for performance measurement.

---

### 8.13 Text, Input, Forms, and Validation Systems

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Structured text entry, document editing, form modeling, and validation are recurring needs that most GUI applications share but that are surprisingly difficult to implement correctly. Validation logic that lives inside event handlers is untestable, not reusable, and inconsistent. Form state that lives in control properties is impossible to serialize, cannot be reset atomically, and cannot be validated without navigating the control tree. gui_do provides a first-class form and validation subsystem that separates the logical model (field values, validation rules, dependencies) from the visual presentation (input controls, error label positions), enabling unit testing of validation logic without any GUI infrastructure.

The text formatting and localization layer provides an equally important separation: display strings, date formats, and locale-specific formatting should not be hardcoded at the point of use. `StringTable` and `LocaleRegistry` provide a lookup-based localization mechanism; `TextFormatter` and `NumericFormatter` provide configurable value formatting; `TextFlow` and `TextSpan` provide rich-text composition that controls can render without knowing the formatting details.

#### Mental model and lifecycle placement

At the bottom of the stack, input controls (`TextInputControl`, `TextAreaControl`, `SpinnerControl`, `DatePickerControl`, `TimePickerControl`, `ColorPickerControl`, `ChipInputControl`) handle raw user input events and expose their values as observables. `FormModel` sits one level above: it models the logical form with named `FormField` objects, `ValidationRule` instances, and the current validation state. `SchemaFormRuntime` sits above that, driving a `FieldGraphSchema` (a DAG of fields with computed visibility dependencies) according to a `ValidationPolicy`. `AsyncFormValidator` adds debounced remote validation at the top of the stack.

Features create the form model in `build` and bind it to controls in `bind_runtime`. The form model is the source of truth for field values; controls are its view. Validation is driven by the form model in response to observable field changes; error display is driven by subscribing to each `FormField`'s validation state observable.

#### Primary public APIs and key types

**From Tier 10 (forms and validation):**
- `FormModel`, `FormField` — the logical form; fields have `value`, `is_valid`, `errors` observables
- `ValidationRule` — abstract base for validation rules
- `FieldError` — a structured validation error with `field_name`, `message`, and `code`
- `FormSchema`, `SchemaField` — declarative schema for a form; each `SchemaField` declares type, default, label, and validators
- `DocumentModel` — rich-text document backing for `TextAreaControl`; represents text as a sequence of styled spans with insert, delete, and selection operations
- `WizardFlow`, `WizardStep`, `WizardHandle` — multi-step guided workflow; each step has its own control tree and validation; `WizardHandle` navigates forward/backward and reports completion
- `ValidationResult`, `Validator`, `RequiredValidator`, `RangeValidator`, `LengthValidator`, `PatternValidator`, `CustomValidator`, `DependentValidator`, `ValidationPipeline` — the full validator library; `ValidationPipeline` runs an ordered sequence of validators and stops on first failure or collects all failures depending on configuration

**From Tier 24 (async form validation):**
- `AsyncFieldValidator`, `AsyncFormValidator` — async validators with debouncing and stale-generation suppression; use for server-side uniqueness checks, email existence verification, and any validation that requires I/O

**From Tier 31 (schema-driven form runtime):**
- `FieldSchema`, `FieldGraphSchema`, `ValidationPolicy`, `SchemaFormRuntime` — the schema DAG and runtime; `FieldGraphSchema` models field visibility dependencies as a directed graph; `SchemaFormRuntime` drives validation according to the declared policy (`ON_CHANGE`, `ON_BLUR`, `ON_SUBMIT`)

**From Tier 14 (text and localization):**
- `TextFormatter`, `NumericFormatter`, `PatternFormatter`, `FixedPatternFormatter` — value-to-string formatters; configure format patterns, decimal separators, and locale-specific rules
- `TextFlow`, `TextSpan` — rich-text composition; a `TextFlow` is a sequence of `TextSpan` objects, each with text, font role, color, and inline style
- `TextSearcher`, `TextMatch` — text search within a string or `DocumentModel`; returns ranked `TextMatch` results with span offsets
- `StringTable`, `LocaleRegistry` — internationalization; register locale-keyed `StringTable` objects; look up strings by key at render time with `LocaleRegistry.resolve(key, locale=None)`

#### Typical usage flow

1. Define a `FormSchema` with `SchemaField` entries specifying key, type, default, label, and validators.
2. Build a `FieldGraphSchema.from_form_schema(schema)`.
3. Construct a `SchemaFormRuntime(graph, policy=ValidationPolicy.ON_CHANGE)`.
4. In `build`, create input controls for each field and add them to the root panel.
5. In `bind_runtime`, bind each `FormField.value` observable to the corresponding input control's value, and subscribe to `FormField.errors` to drive error label visibility.
6. On submit, call `runtime.validate_all()` and inspect `FormModel.is_valid`.

#### Minimal example

```python
from gui_do import (
    FormSchema, SchemaField, FieldGraphSchema, SchemaFormRuntime, ValidationPolicy,
    RequiredValidator, PatternValidator, TextInputControl, LabelControl
)
from pygame import Rect

schema = FormSchema(fields=[
    SchemaField("email", type=str, default="", label="Email",
                validators=[RequiredValidator(), PatternValidator(r".+@.+\..+")]),
    SchemaField("password", type=str, default="", label="Password",
                validators=[RequiredValidator(), LengthValidator(min=8)]),
])
graph = FieldGraphSchema.from_form_schema(schema)
runtime = SchemaFormRuntime(graph, policy=ValidationPolicy.ON_CHANGE)

# In build:
self._email_input = root.add(TextInputControl("email", Rect(10, 40, 280, 30)))
self._email_err = root.add(LabelControl("email_err", Rect(10, 72, 280, 18), ""))

# In bind_runtime:
field = runtime.form.field("email")
self._email_input.bind_value(field.value)
field.errors.subscribe(lambda errs: self._email_err.set_text(errs[0].message if errs else ""))
```

#### Advanced pattern

`AsyncFormValidator` for a registration form checks username availability via a debounced async call with stale-result suppression. When the user types in the username field, each keystroke schedules a delayed async validation after 400 ms of quiet time. If the user types again before 400 ms elapses, the previous scheduled call is canceled. If the user types again after the async call has been dispatched but before it returns, the returned result carries a stale generation token and is discarded. This ensures that a slow network response for an old username does not overwrite the validation state for the current username value.

`WizardFlow` with multi-step `WizardStep` provides guided data entry workflows (setup assistants, import wizards, configuration dialogs). Each step has an independent `FormModel`; the wizard validates the current step before allowing navigation to the next one. `WizardHandle.on_complete` fires with the aggregated values from all steps when the user reaches and submits the final step.

#### Common mistakes and anti-patterns

- **Validating only on submit when continuous feedback is the UX expectation.** Users expect to see "Password must be at least 8 characters" as they type, not only after clicking Submit. Use `ValidationPolicy.ON_CHANGE` for fields that need immediate feedback.
- **Using control property values as the form's source of truth.** Reading `text_input.text` to build a submission payload produces stale values if the `FormField` value has been updated programmatically. Always read from `FormField.value` or `FormModel.values_dict`.
- **Wiring `AsyncFormValidator` without cancellation support for stale generations.** Without stale-generation suppression, a slow network response for an old query can arrive after the user has already corrected the value, displaying an incorrect validation error.
- **Hardcoding display strings instead of using `StringTable`.** Hardcoded strings cannot be translated or updated centrally. All user-visible strings should be registered in a `StringTable` and looked up via `LocaleRegistry`.

#### Cross-links to related systems

- **8.4 State and Observables** — `FormField` values are observables; form binding uses the same subscribe pattern as other observable state.
- **8.5 Controls** — input controls (Tier 13) are the view layer for form fields.
- **8.10 Scheduling** — `AsyncFormValidator` uses the cooperative scheduler for debounced async dispatch.
- **8.14 Data and Dataflow** — `DataflowPipeline` can be used for async validation pipelines that require multi-stage processing.

---

### 8.14 Data and Dataflow Helpers

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Data-heavy features need efficient loading, sorting, filtering, pagination, and virtualized rendering of large datasets without blocking the UI thread. They also need safe cancellation when the user changes the query before the previous load completes, and efficient incremental updates when a subset of the data changes. gui_do provides a composable data layer that addresses all of these needs: virtual item sources compose with proxy sources, cancelable dataflow pipelines bridge background threads to reactive observables, a transactional app state store provides globally shared state with selector-based subscription, and virtualization infrastructure renders only the visible subset of a large collection.

The design philosophy is that data flow should be unidirectional and explicit. Data starts in a source, flows through transformation stages, and is committed to observable state that the UI subscribes to. There are no hidden side channels, no implicit polling, and no shared mutable state outside of the `AppStateStore` transaction mechanism.

#### Mental model and lifecycle placement

Data flows from a source (`AsyncDataProvider` or `FixedItemSource`) through a `SortFilterProxySource` into a virtualized control (`ListViewControl`, `DataGridControl`, `TreeControl`) or directly into `VirtualizationCore`. Expensive computation — parsing, ranking, search — runs in a `DataflowPipeline` on a background thread or in the cooperative scheduler. Results flow back to the UI via `ObservableValue` or `AppStateStore` transactions. `ListDiffCalculator` computes minimal patches for incremental UI updates.

Features set up their data sources in `build`, configure sort/filter in `bind_runtime`, and update data in response to user interaction or async completion callbacks.

#### Primary public APIs and key types

**From Tier 15 (data and collections):**
- `VirtualItemSource` — abstract base for item providers; `count` property and `get_item(index)` method
- `FixedItemSource` — wraps a plain Python list as a `VirtualItemSource`
- `SortFilterProxySource` — wraps a `VirtualItemSource` with sort/filter; `set_sort_key`, `set_filter`, `set_sort_reverse`, `refresh`
- `AsyncDataProvider`, `LoadState`, `LoadStateKind` — async item source with `IDLE`, `LOADING`, `LOADED`, `ERROR` states; subscribe to `state_changed` to drive a progress indicator
- `ObjectPool` — pre-allocated pool for high-churn objects; `acquire()` and `release(obj)`; reduces GC pressure
- `DataCache`, `CacheStats` — LRU-style keyed cache; `get(key)`, `set(key, value)`, `evict(key)`, `stats` property for hit/miss metrics
- `ListDiffCalculator`, `ListDiff`, `DiffInsert`, `DiffRemove`, `DiffMove` — compute minimal patches between two list snapshots; use to drive incremental UI updates instead of full re-renders

**From Tier 26 (cancelable dataflow pipeline):**
- `CancellationToken` — generation-based cancellation token; check `is_canceled` inside pipeline stage callbacks
- `PipelineStage` — a callable that takes `(input, token)` and returns output or `None` when canceled
- `DataflowPipeline` — multi-stage processing pipeline with stale-generation suppression; `submit(input)` starts a new generation, canceling the previous; `on_result` callback fires with the result of the current generation
- `PipelineHandle` — returned by `DataflowPipeline.submit`; call `cancel()` to cancel the current run

**From Tier 27 (app state store):**
- `AppStateStore`, `StateSelector`, `StateTransaction` — globally shared transactional state store; `select(selector_fn)` returns a `StateSelector` observable; `dispatch(transaction)` commits a `StateTransaction` atomically; multiple features observe the same slice without coupling to each other

**From Tier 29 (virtualization core):**
- `MeasureMode`, `MeasurePolicy` — item height measurement strategies for the virtualization engine
- `VirtualizedWindow` — higher-level windowed rendering wrapper for large lists
- `RecyclePool` — provides item view reuse for the virtualized renderer; `acquire_view(item_type)`, `release_view(view)`
- `VirtualizationCore` — low-level windowed rendering engine; only renders items visible in the scroll window; drives `RecyclePool` for view reuse

#### Typical usage flow

1. Create a `FixedItemSource` (or `AsyncDataProvider` for remote data) wrapping your data.
2. Wrap it in a `SortFilterProxySource` to add sort and filter without copying the source.
3. Pass the proxy source to a `ListViewControl`, `DataGridControl`, or `VirtualizationCore`.
4. For heavy data transformation, create a `DataflowPipeline` with one or more `PipelineStage` callables; publish results to an `ObservableValue` from the `on_result` callback.
5. Use `ListDiffCalculator` to drive incremental updates when the underlying dataset changes partially.

#### Minimal example

```python
from gui_do import FixedItemSource, SortFilterProxySource, ListViewControl, ListItem
from pygame import Rect

items = [ListItem(key=str(i), label=f"Item {i}", data={"value": i}) for i in range(1000)]
source = FixedItemSource(items)
proxy = SortFilterProxySource(source)
proxy.set_filter(lambda item: item.data["value"] % 2 == 0)
proxy.set_sort_key(lambda item: item.label)

list_view = root.add(ListViewControl("list", Rect(10, 10, 400, 500)))
list_view.set_source(proxy)
```

#### Advanced pattern

`DataflowPipeline` with three stages (load → parse → rank) and per-stage `CancellationToken` enables a search pipeline that handles the user typing quickly. Each keystroke calls `pipeline.submit(query_string)`, which increments the generation counter and cancels the previous run. Each `PipelineStage` checks `token.is_canceled` at the start and at yield points; if the token is canceled, the stage returns `None` immediately, short-circuiting the remaining pipeline stages. Only the result from the latest generation reaches `on_result` and updates the UI.

`AppStateStore` with `StateSelector` provides a pattern for features that need to share application state without direct references to each other. Feature A writes `StateTransaction({"selected_item_id": item.id})`; Feature B subscribes to `store.select(lambda s: s["selected_item_id"])` and reacts to changes. The store is the only shared object; the features never reference each other.

#### Common mistakes and anti-patterns

- **Full-list redraws without `ListDiffCalculator`.** Replacing all items in a list view on every data change triggers full re-render and loses scroll position, selection state, and animation state. Use `ListDiffCalculator` to compute minimal patches and apply them incrementally.
- **Forgetting to cancel stale `DataflowPipeline` generations.** If a new search query is submitted before the previous one completes, the previous `PipelineHandle` should be canceled. If not canceled, both pipeline runs complete and the older result may overwrite the newer one depending on which finishes last.
- **Holding large datasets in memory without `DataCache` expiry.** An unbounded in-memory store of remote records causes unbounded memory growth. Use `DataCache` with a configured capacity to automatically evict least-recently-used entries.
- **Using `ObjectPool` incorrectly.** If you release an object to the pool while another part of the code still holds a reference to it, the pool will hand the same object to a different consumer while the first consumer still uses it. Always ensure a released object has no other living references before calling `pool.release(obj)`.

#### Cross-links to related systems

- **8.4 State and Observables** — `AppStateStore` extends the observable model to globally shared state; `ObservableList` drives incremental list updates.
- **8.5 Controls** — `ListViewControl`, `DataGridControl`, and `TreeControl` consume `VirtualItemSource` implementations.
- **8.10 Scheduling** — `CooperativeScheduler` can host `DataflowPipeline` stages that run in the frame budget rather than a background thread.
- **8.16 Telemetry** — telemetry spans on pipeline stages identify bottleneck stages and track per-generation latency.

---

### 8.15 Graphics and Audio Integration Points

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Most controls handle their own rendering through the framework's draw pass, but some features require high-fidelity custom rendering that goes beyond the control tree: particle systems, tile maps, sprite animations, 2D scene graphs with camera transforms, complex shape compositing, or post-processing effects. The graphics integration layer provides building blocks for these cases without requiring features to manage low-level pygame surface operations directly.

Audio is event-driven: features should not call mixer APIs directly, because doing so couples the feature to pygame's audio internals and makes audio behavior impossible to test. The `SoundEventBus` provides a semantic event channel: features publish named `SoundCue` events; the bus routes them to the mixer without the feature knowing how the cue is loaded, decoded, or played.

#### Mental model and lifecycle placement

Custom rendering lives in the feature's `draw(host, screen)` method, which is called once per frame after all control rendering is complete. Features that render inside a `CanvasControl` provide a `draw` callback to the canvas instead. Graphics helpers build on pygame surfaces but manage dirty tracking, offscreen caching, and compositing so that features can express high-level rendering intent rather than low-level blit sequences.

Assets (surfaces, sprite sheets, tile sets) are loaded in `build` and registered with `AssetRegistry`. Particle systems and scene graphs are updated in `on_update` and drawn in `draw`. Audio cues are published in response to user actions or gameplay events; the `SoundBankRegistry` loads the actual audio files and the `SoundEventBus` routes cue events to the mixer.

#### Primary public APIs and key types

**From Tier 16 (graphics and rendering):**
- `BuiltInGraphicsFactory` — factory for creating pre-configured graphics objects
- `DirtyRegionTracker` — per-frame dirty-rect accumulation; `mark_dirty(rect)`, `overlaps_dirty(rect)`, `consume_dirty_regions()`; uses incremental union cache for O(1) overlap checks
- `DrawContext`, `DrawPhase` — structured draw pass with explicit phases: `BACKGROUND`, `CONTENT`, `OVERLAY`, `DEBUG`; controls and features draw in the appropriate phase
- `AssetRegistry` — centralized registry for loaded surfaces, fonts, and other assets; prevents duplicate loading; `register(key, asset)`, `get(key)`
- `DebugOverlay` — renders control bounds, focus ring, spatial index queries, and performance stats as a live overlay
- `SurfaceCompositor`, `Layer` — layered rendering pipeline with configurable z-order and blend modes
- `ShapeRenderer` — draws common shapes (rounded rects, arrows, circles, dashed lines) without managing low-level pygame draw calls
- `SurfaceEffects` — post-processing effects on a surface: blur, tint, darken, and brightness adjustment
- `VectorPath` — declarative path builder (`move_to`, `line_to`, `curve_to`, `arc_to`); rendered via pygame draw primitives
- `SpriteSheet`, `FrameAnimation` — extract frames from a sprite atlas; drive playback with frame duration and loop settings
- `ParticleSystem`, `Emitter`, `ParticleLayer` — particle emission with configurable spawn rates, velocities, lifetimes, gravity, and colors; `tick(dt)` in `on_update`; `draw(screen)` in `draw`
- `TileSet`, `TileMap` — grid-based tile rendering; `TileSet` holds the texture atlas; `TileMap` holds the grid and renders only visible tiles
- `RenderTarget`, `LiveRenderTarget`, `OffscreenRenderTarget`, `create_render_target`, `create_surface` — render to an offscreen pygame surface then composite; use for caching expensive drawing or applying post-processing effects
- `Node2D`, `SceneGraph2D`, `Camera2D` — hierarchical 2D transform tree; nodes inherit parent transforms; `Camera2D` applies a viewport translation/zoom for scrollable worlds

**From Tier 20 (audio):**
- `SoundCue` — a named audio cue event; publish to trigger playback
- `SoundBankRegistry` — loads and stores named audio assets; `register(name, path)`, `get(name)`
- `SoundEventBus` — semantic event channel for audio cues; `publish(SoundCue("name"))` routes to the mixer

#### Typical usage flow

1. In `build`, load assets and register them with `AssetRegistry`; create `SpriteSheet`, `TileSet`, or `SoundBankRegistry` entries.
2. Create `ParticleSystem` or `SceneGraph2D` and configure them.
3. In `on_update`, call `particle_system.tick(dt)`, `scene_graph.update(dt)`, or other per-frame update methods.
4. In `draw`, call `particle_system.draw(screen)`, `tile_map.draw(screen, camera)`, or `scene_graph.draw(context)`.
5. Wrap expensive drawing in `DirtyRegionTracker` to skip unchanged regions.
6. Publish `SoundCue` events via `host.sound_bus.publish(SoundCue("name"))` in response to user actions.

#### Minimal example

```python
from gui_do import ParticleSystem, Emitter, SoundCue

# In build:
self.particles = ParticleSystem()
self.emitter = self.particles.add_emitter(Emitter(
    origin=(200, 300),
    rate=50,
    lifetime=(0.5, 1.5),
    velocity_range=((-30, 30), (-80, -20)),
    color=(255, 200, 50, 255),
))

# In on_update:
def on_update(self, host, dt):
    self.particles.tick(dt)

# In draw:
def draw(self, host, screen):
    self.particles.draw(screen)

# Audio:
# host.sound_bus.publish(SoundCue("explosion"))
```

#### Advanced pattern

`DirtyRegionTracker` combined with `OffscreenRenderTarget` enables efficient caching of complex tile maps. On the first frame, render the full tile map to an `OffscreenRenderTarget`; then each frame, only re-render the tiles in dirty regions into the offscreen surface and blit the result to the screen. This reduces per-frame rendering cost from O(visible tiles) to O(changed tiles).

Combine `SceneGraph2D` and `Camera2D` for a scrollable world with smooth camera movement. Add `Node2D` instances for each game object; set their local transforms. The `Camera2D` transform is applied to the entire graph before rendering, so scrolling requires only updating the camera position — not repositioning every object.

#### Common mistakes and anti-patterns

- **Full-surface redraw every frame when `DirtyRegionTracker` could gate it.** For complex scenes where only a small portion changes per frame, checking `overlaps_dirty(region_rect)` before re-rendering can eliminate 90% of rendering work.
- **Loading assets in `draw` instead of `build`.** Loading a surface from disk in `draw` causes per-frame disk I/O, producing severe frame stutter. Load all assets once in `build` and cache them in `AssetRegistry`.
- **Triggering audio cues from low-level pointer noise instead of semantic actions.** Publishing a `SoundCue` on every `MOUSEMOVE` event produces a continuous stream of audio events. Publish cues only on discrete semantic events (button click, item selection, error notification).
- **Creating `ParticleSystem` emitters without bounds.** Particles that fly outside the rendering region continue to be updated and drawn each frame at off-screen positions. Configure emitter bounds and particle lifetime to prevent unbounded accumulation.
- **Not registering the `SceneGraph2D` with the scene's update loop.** A scene graph that is created but never receives `update(dt)` calls will not animate. Ensure it is called in `on_update`.

#### Cross-links to related systems

- **8.2 Feature Lifecycle** — custom rendering hooks (`draw`) and update hooks (`on_update`) are part of the feature lifecycle.
- **8.5 Controls** — `CanvasControl` is the integration point for custom rendering inside the control tree.
- **8.10 Scheduling** — particle ticks and scene graph updates run on the frame update cadence driven by the scheduler.
- **8.16 Telemetry** — instrument draw path with telemetry spans to identify per-frame rendering hot spots.

---

### 8.16 Telemetry, Introspection, and Operational Hooks

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Runtime observability — performance measurement, property inspection, and geometric spatial querying — lets developers diagnose behavior during development and integration without relying on visual inspection alone. Without telemetry, the only way to know whether a feature is consuming too much frame budget is to run a profiler; the only way to know which control is at a given screen position is to read the control tree manually. gui_do's telemetry and introspection layer provides structured, in-process observability that integrates with the framework's own hot paths.

`TelemetryCollector` instruments arbitrary code spans with named measurements; `analyze_telemetry_records` produces a report that identifies slow spans. `PropertyRegistry` and `PropertyInspectorModel` expose control and feature properties for runtime inspection without requiring the inspector to know the exact type of the object being inspected. `SceneSpatialIndex` answers geometric queries — "which controls overlap this rect?" — in the framework's coordinate system.

#### Mental model and lifecycle placement

Telemetry is configured once at bootstrap time via `configure_telemetry(enabled=True)`. Once enabled, the `telemetry_collector` singleton begins recording spans whenever instrumented code runs. Features and framework code wrap measured sections with context managers or decorator patterns; the collector accumulates `TelemetrySample` records. After a scenario completes, `analyze_telemetry_records(telemetry_collector.records)` produces a structured report that can be formatted with `render_telemetry_report` or saved to a log file.

Property introspection is set up by decorating control or feature attributes with `@ui_property`. The `property_registry` singleton collects all decorated attributes at import time. `PropertyInspectorModel` queries the registry to build a displayable property list for a given object, which `PropertyInspectorPanel` then renders.

#### Primary public APIs and key types

**From Tier 7 (telemetry):**
- `TelemetryCollector` — the collector class; holds `records` (a list of `TelemetrySample`); accessed via the `telemetry_collector` singleton
- `TelemetrySample` — one measurement record: span name, duration, timestamp, and metadata
- `configure_telemetry` — enable/disable the global collector; `configure_telemetry(enabled=True)`
- `telemetry_collector` — module-level singleton `TelemetryCollector` instance
- `analyze_telemetry_records` — analyze a list of `TelemetrySample` records; returns a report with per-span statistics (count, mean, min, max, p95)
- `analyze_telemetry_log_file` — analyze a previously saved telemetry log file by path
- `render_telemetry_report` — format a telemetry report as a human-readable string for logging or display
- `load_telemetry_log_file` — load a telemetry log file into a list of `TelemetrySample` records

**From Tier 17 (introspection):**
- `SceneSpatialIndex` — spatial query engine for the control tree; `controls_at_point(pt)`, `controls_overlapping_rect(rect)`, `enumerate_bounds()` — returns controls in z-order
- `ui_property` — decorator that marks a control or feature attribute as inspectable; adds `PropertyDescriptor` metadata
- `PropertyDescriptor` — descriptor metadata: name, type, label, read-only flag, display group
- `PropertyRegistry` — registry of all `@ui_property` descriptors; `property_registry` is the module-level singleton; `descriptors_for(obj)` returns all inspectable properties for an object
- `property_registry` — module-level singleton `PropertyRegistry` instance
- `PropertyInspectorModel` — drives the `PropertyInspectorPanel` control; queries `PropertyRegistry` to build a property list for a given object; updates live as the object changes
- `InspectedProperty` — a single live property entry in the inspector model: current value, descriptor, and an observable for value changes

#### Typical usage flow

1. At bootstrap: `configure_telemetry(enabled=True)` in `HostApplicationConfig` or before `bootstrap_host_application`.
2. Run user scenarios (the collector records all instrumented spans automatically).
3. After the scenario: `report = analyze_telemetry_records(telemetry_collector.records)`.
4. Format: `print(render_telemetry_report(report))`.
5. For offline analysis: use `load_telemetry_log_file(path)` then `analyze_telemetry_log_file(path)`.
6. For property inspection: decorate attributes with `@ui_property`; instantiate `PropertyInspectorModel(target_object)` and bind it to a `PropertyInspectorPanel`.
7. For spatial queries: acquire `SceneSpatialIndex` from the host; call `controls_at_point(mouse_pos)` in debug overlays.

#### Minimal example

```python
from gui_do import configure_telemetry, telemetry_collector, analyze_telemetry_records, render_telemetry_report

configure_telemetry(enabled=True)

# ... run scenarios ...

report = analyze_telemetry_records(telemetry_collector.records)
print(render_telemetry_report(report))

# Property introspection:
from gui_do import ui_property, PropertyInspectorModel

class MyControl(PanelControl):
    @ui_property(label="Fill Color", group="Appearance")
    def fill_color(self):
        return self._fill_color

model = PropertyInspectorModel(my_control_instance)
inspector_panel.bind_model(model)
```

#### Advanced pattern

Combine telemetry spans with `DebugOverlay` and `SceneSpatialIndex` to build a live development inspector. Enable `DebugOverlay` in debug builds to render control bounds. Use `SceneSpatialIndex.controls_at_point(mouse_pos)` on each frame to identify the control under the cursor. Instantiate `PropertyInspectorModel` for the hovered control and display its properties in a sidebar `PropertyInspectorPanel`. This gives a live, point-and-click property inspector without any additional infrastructure.

`analyze_telemetry_log_file` supports post-run offline analysis. Record a session to disk with a file appender, then load and analyze the log after the run to identify frame budget regressions introduced by a code change — without needing to reproduce the scenario interactively.

#### Common mistakes and anti-patterns

- **Profiling without representative user scenarios.** The idle event loop consumes trivial budget. Telemetry recorded while the user is not interacting produces no signal about real performance. Always record telemetry during realistic interaction scenarios.
- **Relying on visual inspection alone for frame budget issues.** A feature that causes occasional frame drops may not produce any visible artifact that is easy to spot. Always correlate visual observations with telemetry span data.
- **Forgetting to call `configure_telemetry` before the scenarios you want to measure.** The collector does not record spans until it is enabled. Enable it before beginning any scenario you intend to measure, not after the scenario has already run.
- **Leaving telemetry enabled in production builds.** The telemetry collector accumulates `TelemetrySample` records in memory with no automatic eviction. In a long-running production session, this will grow without bound. Disable telemetry in release builds or configure a maximum record count.

#### Cross-links to related systems

- **8.1 Bootstrap** — `TelemetryConfig` is declared in `HostApplicationConfig`; `configure_telemetry` is called during bootstrap.
- **8.10 Scheduling** — the `TaskScheduler` dispatch path is instrumented with telemetry spans; the scheduler budget contract appears in the telemetry report.
- **8.11 Persistence** — telemetry log files can be analyzed offline via `analyze_telemetry_log_file`.
- **8.15 Graphics** — instrument `draw` paths with telemetry spans to identify per-frame rendering hot spots.

---

## Integration Patterns and Composition Recipes

[Back to Table of Contents](#table-of-contents)

This chapter presents four composable patterns that each combine multiple gui_do systems into a complete, tested architecture. Each recipe is self-contained: it explains the goal, why this combination of systems is the right approach, provides step-by-step assembly instructions, a complete code example, and validation notes.

---

### Recipe 1: Routed Feature + Actions + Shortcut Overlay

**Goal:** A feature with discoverable keyboard shortcuts that are automatically registered via `RoutedRuntimeSpec` and displayed in a full-screen shortcut help overlay when the user presses the overlay toggle key.

**Why this combination:** `RoutedRuntimeSpec` is the declarative wire-up mechanism for the features-actions-shortcuts subsystem. Without it, features must manually call `host.action_manager.register(...)`, `host.input_map.bind(...)`, and `host.shortcut_overlay.register(...)` in `bind_runtime` and must manually undo all of those in `shutdown_runtime`. This is error-prone and produces inconsistent shortcut registry state when features enter and exit scenes. `RoutedRuntimeSpec` declares the intent; `bind_routed_feature_lifecycle` / `shutdown_routed_feature_lifecycle` handle all the plumbing atomically.

**Step-by-step:**

1. Declare `ActionSpec` entries for this feature's actions in `HostApplicationConfig.actions`.
2. In the feature's `__init__`, build a `RoutedRuntimeSpec` that references those action names, declares their input bindings, and configures a `ShortcutOverlaySpec`.
3. Wrap the `RoutedRuntimeSpec` in a `RoutedFeatureLifecycleSpec`.
4. In `bind_runtime`, call `bind_routed_feature_lifecycle(self, host, self._lifecycle_spec)`.
5. In `shutdown_runtime`, call `shutdown_routed_feature_lifecycle(self, host, self._lifecycle_spec)`.

```python
from gui_do import (
    RoutedFeature, RoutedRuntimeSpec, RoutedFeatureLifecycleSpec,
    ShortcutOverlaySpec, ShortcutSection, ShortcutEntry,
    bind_routed_feature_lifecycle, shutdown_routed_feature_lifecycle,
)

class ToolFeature(RoutedFeature):
    HOST_REQUIREMENTS = {
        "build": ["app"],
        "bind_runtime": ["action_manager", "input_map"],
    }

    def __init__(self):
        super().__init__(scene_name="main")
        self._lifecycle_spec = RoutedFeatureLifecycleSpec(
            runtime_spec=RoutedRuntimeSpec(
                action_bindings={"tool.undo": "ctrl+z", "tool.redo": "ctrl+shift+z"},
                shortcut_overlay=ShortcutOverlaySpec(
                    toggle_action_name="help.show_shortcuts",
                    sections=[
                        ShortcutSection(title="Editing", entries=[
                            ShortcutEntry(action="tool.undo", label="Undo"),
                            ShortcutEntry(action="tool.redo", label="Redo"),
                        ])
                    ],
                ),
            )
        )

    def build(self, host):
        # Build the control tree ...
        pass

    def bind_runtime(self, host):
        bind_routed_feature_lifecycle(self, host, self._lifecycle_spec)

    def shutdown_runtime(self, host):
        shutdown_routed_feature_lifecycle(self, host, self._lifecycle_spec)
```

**Validation:** Press the overlay toggle key declared in `ShortcutOverlaySpec.toggle_action_name`; the shortcut help overlay appears and shows the "Editing" section. Press Ctrl+Z in the scene; the `tool.undo` action fires. Enter another scene and return; the actions are re-registered and the overlay still works.

---

### Recipe 2: Window Presenter + Task Panel + Focus Toggle

**Goal:** A floating window in a scene that can be toggled from a task panel button, with correct focus ring behavior — the window's controls are excluded from Tab navigation when the window is hidden.

**Why this combination:** Without `TaskPanelFocusToggleSpec`, a hidden window's controls remain in the focus ring. Pressing Tab when the window is hidden appears to skip focus entirely — the focus cursor moves to an invisible control. `set_window_visible_state` keeps the task panel button indicator synchronized with the actual window visibility, preventing a mismatch where the button shows "active" but the window is not visible.

**Step-by-step:**

1. Implement a `WindowPresenter` subclass that constructs the window's control tree.
2. In the feature's `build`, call `create_anchored_feature_window` to create the window and associate it with the presenter.
3. In the feature's `RoutedRuntimeSpec`, add a `TaskPanelFocusToggleSpec` for this window.
4. Wire the task panel toggle button to call `set_window_visible_state(host, window_id, visible)`.
5. In `bind_runtime`, initialize window visibility and task panel button state.

```python
from gui_do import (
    WindowPresenter, AnchoredWindowSpec, create_anchored_feature_window,
    TaskPanelFocusToggleSpec, set_window_visible_state,
    RoutedRuntimeSpec, RoutedFeatureLifecycleSpec,
)
from pygame import Rect

class InfoPresenter(WindowPresenter):
    def build(self, host, window):
        window.add(LabelControl("info_label", Rect(8, 8, 280, 30), "Status: OK"))

class InfoFeature(RoutedFeature):
    HOST_REQUIREMENTS = {"build": ["app", "scene_presentation"]}

    def __init__(self):
        super().__init__(scene_name="main")
        self._lifecycle_spec = RoutedFeatureLifecycleSpec(
            runtime_spec=RoutedRuntimeSpec(
                focus_toggles=[TaskPanelFocusToggleSpec(window_id="info_window")],
            )
        )

    def build(self, host):
        presenter = InfoPresenter()
        spec = AnchoredWindowSpec(
            control_id="info_window",
            title="Info",
            anchor="top_right",
            size=(300, 150),
        )
        create_anchored_feature_window(host, presenter, spec)

    def bind_runtime(self, host):
        bind_routed_feature_lifecycle(self, host, self._lifecycle_spec)
        # Start with the window hidden:
        set_window_visible_state(host, "info_window", visible=False)

    def shutdown_runtime(self, host):
        shutdown_routed_feature_lifecycle(self, host, self._lifecycle_spec)
```

**Validation:** Press Tab repeatedly with the window hidden — focus cycles through only the visible controls; no invisible focus stall occurs. Toggle the window from the task panel button; the button indicator and window visibility are always synchronized.

---

### Recipe 3: AppStateStore + Persistence + Snapshot Migration

**Goal:** Globally shared application state that is persisted across sessions and survives schema evolution between application versions.

**Why this combination:** `AppStateStore` provides a transactional, selector-based shared state container that decouples features from each other — they observe state slices without direct references. `WorkspacePersistenceManager` serializes the store's state to disk. `SnapshotMigrator` ensures that snapshots written by older application versions can be loaded and transformed to the current schema without data loss.

**Step-by-step:**

1. Define the initial state shape as a Python dict; instantiate `AppStateStore` with it.
2. Use `StateSelector` to derive observable slices for individual features.
3. On save, call `make_snapshot(current_version, store.state_dict)` to create a `VersionedSnapshot`.
4. On load, call `read_version(raw_snapshot_dict)` to determine the saved version; call `SnapshotMigrator.migrate(snapshot, current_version)` to bring it to the current schema.
5. Apply the migrated snapshot to `AppStateStore` via `store.dispatch(StateTransaction.restore(snapshot.data))`.
6. Register `MigrationStep` objects for each schema version transition.

```python
from gui_do import (
    AppStateStore, StateSelector, StateTransaction,
    VersionedSnapshot, make_snapshot, read_version,
    MigrationStep, MigrationRegistry, SnapshotMigrator, SchemaVersion,
)

CURRENT_VERSION = SchemaVersion(2)

# Build the store:
store = AppStateStore({"selected_tab": "overview", "theme": "light", "zoom": 1.0})

# Feature A: observe selected_tab
tab_selector = store.select(lambda s: s["selected_tab"])

# Feature B: change selected_tab
store.dispatch(StateTransaction({"selected_tab": "settings"}))

# Save:
snapshot = make_snapshot(CURRENT_VERSION, store.state_dict())

# Load:
raw = load_from_disk("session.json")
version = read_version(raw)
registry = MigrationRegistry()
# v1 added "zoom" field:
registry.register(MigrationStep(from_version=SchemaVersion(1), to_version=CURRENT_VERSION,
    migrate=lambda data: {**data, "zoom": data.get("zoom", 1.0)}))
migrator = SnapshotMigrator(registry)
migrated = migrator.migrate(VersionedSnapshot(version=version, data=raw), CURRENT_VERSION)
store.dispatch(StateTransaction.restore(migrated.data))
```

**Validation:** Save a session, close the application, change the schema (add a field), reopen, and confirm the restore report has no fatal errors; confirm old sessions load with the new field at its default value.

---

### Recipe 4: DataflowPipeline + Telemetry + ErrorBoundary

**Goal:** Safe background data processing with measurable per-stage performance and UI failure containment, so that rendering bugs in one subtree do not crash the entire frame.

**Why this combination:** `DataflowPipeline` handles the stale-generation problem for multi-step async computation. Telemetry spans on pipeline stages identify which stage is the bottleneck and how latency scales with input size. `ErrorBoundary` wraps the output control tree; if a presenter bug or data shape mismatch causes a rendering exception, the boundary catches it, reports it via telemetry, and renders a neutral fallback — the rest of the scene continues normally.

**Step-by-step:**

1. Define one `PipelineStage` callable per processing step; check `token.is_canceled` at each yield point.
2. Create `DataflowPipeline` with the stages; register an `on_result` callback that publishes to an `ObservableValue`.
3. Wrap the result-rendering control in `ErrorBoundary`.
4. Instrument stage entry and exit with telemetry spans.
5. Subscribe the `ObservableValue` to the control in `bind_runtime`.

```python
from gui_do import (
    DataflowPipeline, PipelineStage, CancellationToken,
    ObservableValue, ErrorBoundary,
    configure_telemetry, telemetry_collector, analyze_telemetry_records,
)

configure_telemetry(enabled=True)

def parse_stage(raw_input, token):
    if token.is_canceled:
        return None
    # ... expensive parse ...
    return parsed

def rank_stage(parsed, token):
    if token.is_canceled:
        return None
    # ... expensive rank ...
    return ranked

results = ObservableValue([])
pipeline = DataflowPipeline(
    stages=[PipelineStage(parse_stage), PipelineStage(rank_stage)],
    on_result=lambda r: results.set(r),
)

# In build:
boundary = root.add(ErrorBoundary("results_boundary",
    content=ResultsListControl("results_list", Rect(0, 0, 400, 600)),
    fallback=LabelControl("err", Rect(0, 0, 400, 30), "Unable to display results."),
))

# On user query change:
pipeline.submit(user_query)

# After a session:
report = analyze_telemetry_records(telemetry_collector.records)
print(render_telemetry_report(report))
```

**Validation:** Type a new query before the previous pipeline run finishes; confirm only one result set is applied (the latest). Force a rendering exception in `ResultsListControl.draw`; confirm the boundary renders the fallback without crashing the scene. Run `render_telemetry_report` and identify which stage dominates the latency.

---

## End-to-End Reference Application

[Back to Table of Contents](#table-of-contents)

The following listing is a complete, self-contained gui_do application that demonstrates the full bootstrap-to-shutdown lifecycle with real API names. It can serve as a template for new projects. Each system it exercises is labeled in a comment.

```python
"""
gui_do End-to-End Reference Application
Demonstrates: bootstrap, RoutedFeature, observables, actions, shortcut overlay,
telemetry, and workspace save/load.
"""
import sys
import pygame
from gui_do import (
    # Bootstrap tier
    bootstrap_host_application, build_host_application_config,
    HostApplicationBindingSpec, HostApplicationConfig,
    FeatureSpec, ActionSpec, RuntimeSceneSpec, TelemetryConfig,
    # Feature and lifecycle
    RoutedFeature, RoutedRuntimeSpec, RoutedFeatureLifecycleSpec,
    ShortcutOverlaySpec, ShortcutSection, ShortcutEntry,
    bind_routed_feature_lifecycle, shutdown_routed_feature_lifecycle,
    # Controls
    PanelControl, LabelControl, ButtonControl,
    # State
    ObservableValue,
    # Telemetry
    configure_telemetry, telemetry_collector, analyze_telemetry_records, render_telemetry_report,
)
from pygame import Rect


# ── Feature ─────────────────────────────────────────────────────────────────

class CounterFeature(RoutedFeature):
    HOST_REQUIREMENTS = {
        "build": ["app"],
        "bind_runtime": ["action_manager", "input_map", "toasts"],
    }

    def __init__(self):
        super().__init__(scene_name="main")
        self._count = ObservableValue(0)            # State & Observables (§8.4)
        self._label = None
        self._sub = None
        self._lifecycle_spec = RoutedFeatureLifecycleSpec(
            runtime_spec=RoutedRuntimeSpec(
                action_bindings={                    # Actions & Input Mapping (§8.3)
                    "app.increment": "space",
                    "help.show_shortcuts": "f9",
                },
                shortcut_overlay=ShortcutOverlaySpec(  # Overlays (§8.8)
                    toggle_action_name="help.show_shortcuts",
                    sections=[
                        ShortcutSection(title="Counter", entries=[
                            ShortcutEntry(action="app.increment", label="Increment counter"),
                            ShortcutEntry(action="help.show_shortcuts", label="Toggle this help"),
                        ]),
                    ],
                ),
            )
        )

    def build(self, host):                           # Feature Lifecycle (§8.2)
        root = host.app.add(                         # Controls (§8.5)
            PanelControl("root", Rect(100, 100, 400, 200)),
            scene_name="main",
        )
        self._label = root.add(
            LabelControl("count_label", Rect(10, 10, 380, 40), "Count: 0")
        )
        root.add(ButtonControl(
            "inc_btn", Rect(10, 60, 150, 36), "Increment",
            on_click=self._increment,
        ))

    def bind_runtime(self, host):
        bind_routed_feature_lifecycle(self, host, self._lifecycle_spec)
        self._sub = self._count.subscribe(            # Observable subscription
            lambda v: self._label.set_text(f"Count: {v}")
        )
        # Wire the increment action to the method
        host.action_manager.set_handler("app.increment", self._increment)

    def shutdown_runtime(self, host):
        if self._sub:
            self._sub()
            self._sub = None
        shutdown_routed_feature_lifecycle(self, host, self._lifecycle_spec)

    def _increment(self):
        self._count.set(self._count.get() + 1)


# ── Bootstrap ────────────────────────────────────────────────────────────────

class ReferenceApp:
    WORKSPACE_PATH = "reference_session.json"

    def run(self):
        configure_telemetry(enabled=True)             # Telemetry (§8.16)

        binding = HostApplicationBindingSpec(
            feature_entries=[
                FeatureSpec(attribute="counter", factory=CounterFeature),
            ],
            actions=[                                  # Actions (§8.3)
                ActionSpec(name="app.increment", label="Increment counter"),
                ActionSpec(name="app.exit", label="Exit application"),
                ActionSpec(name="help.show_shortcuts", label="Show shortcut help"),
            ],
            scene_bundle_entries=[
                RuntimeSceneSpec(
                    name="main",
                    feature_attributes=["counter"],
                    bind_escape_to_exit=True,          # Architecture (§7)
                ),
            ],
        )

        config = build_host_application_config(
            title="Reference Application",
            size=(800, 600),
            telemetry=TelemetryConfig(enabled=True),
        )

        host = bootstrap_host_application(config, binding)  # Bootstrap (§8.1)

        # Restore workspace if it exists:
        try:
            report = host.app.load_workspace(self.WORKSPACE_PATH)  # Persistence (§8.11)
            if report and report.skipped_settings:
                print(f"Skipped settings on restore: {report.skipped_settings}")
        except FileNotFoundError:
            pass  # First run — no saved workspace yet

        host.app.run_entrypoint()

        # Save workspace on exit:
        host.app.save_workspace(self.WORKSPACE_PATH)

        # Report telemetry after exit:
        report = analyze_telemetry_records(telemetry_collector.records)
        print(render_telemetry_report(report))


if __name__ == "__main__":
    ReferenceApp().run()
```

### What This Listing Demonstrates

**Bootstrap (§8.1):** `build_host_application_config` constructs the runtime configuration; `bootstrap_host_application` initializes all systems and returns the host; `run_entrypoint` starts the pygame event loop.

**Feature Lifecycle (§8.2):** `CounterFeature` subclasses `RoutedFeature` and implements `build`, `bind_runtime`, and `shutdown_runtime`. Control creation happens in `build`; observable binding happens in `bind_runtime`; cleanup happens in `shutdown_runtime`.

**Events and Actions (§8.3):** `ActionSpec` entries declare named actions; `RoutedRuntimeSpec.action_bindings` declares their input bindings; `host.action_manager.set_handler` wires the runtime callback.

**State and Observables (§8.4):** `ObservableValue` is the source of truth for the counter; `subscribe` drives the label update; `set` triggers all subscribers.

**Controls (§8.5):** `PanelControl`, `LabelControl`, and `ButtonControl` are created in `build` and added to the scene.

**Overlays (§8.8):** `ShortcutOverlaySpec` declares the F9 overlay toggle; `bind_routed_feature_lifecycle` wires it automatically.

**Persistence (§8.11):** `load_workspace` restores session state on launch; `save_workspace` persists it on exit; the restore report exposes skipped settings.

**Telemetry (§8.16):** `configure_telemetry` enables recording; `analyze_telemetry_records` and `render_telemetry_report` produce a post-session performance summary.

### Validation Checklist

1. Application opens to an 800×600 window with the "Reference Application" title.
2. Pressing Space or clicking "Increment" updates the label to "Count: N".
3. Pressing F9 opens the shortcut help overlay showing the "Counter" section.
4. Pressing Escape or F9 again closes the overlay.
5. Pressing Escape in the main scene exits the application.
6. On restart, the saved workspace is loaded; no crash occurs even if the workspace file does not exist.
7. The telemetry report printed to stdout after exit contains span data for the bootstrap and dispatch paths.
8. `report.skipped_settings` is empty on a clean first run.

---

## Testing, Diagnostics, and Reliability

[Back to Table of Contents](#table-of-contents)

### Contract Tests

The contract test suite verifies the behavioral guarantees that the rest of this manual describes. These tests are the authoritative source of truth for which guarantees are mechanically enforced — they are not documentation that could be out of date. Run them after any change to public API, event routing, workspace persistence, or boundary policy:

```bash
python -m pytest -q tests/test_public_api_exports.py tests/test_public_api_docs_contracts.py tests/test_runtime_operating_contracts.py tests/test_boundary_contracts.py tests/test_gui_application_workspace_contracts.py
```

**`test_public_api_exports.py`** — Verifies that every name in `gui_do.__all__` is importable from the root package and that no name in `__all__` is absent from the actual module. This test is the canary for accidental deletion or misnamed re-exports. If it fails, a name was either added to `__all__` without a corresponding implementation, or removed from the module without being removed from `__all__`.

**`test_public_api_docs_contracts.py`** — Verifies that the API names described in the contract documents under `docs/` match the names actually exported from `gui_do`. This test catches documentation drift: when a type is renamed in the code but the contract document still uses the old name.

**`test_runtime_operating_contracts.py`** — Verifies the four runtime guarantees from `docs/runtime_operating_contracts.md` Section 1: canonical event normalization to `GuiEvent`, scene-isolated update execution, deterministic window focus candidate ordering (sorted by `control_id`), and scheduler dispatch budget clamping within the min/max bounds from Section 6.

**`test_boundary_contracts.py`** — Verifies the architectural boundary rule: no module under `gui_do/` may import from `demo_features/`. This is enforced by static import analysis. If a `gui_do` module acquires a direct or transitive import of a demo module, this test will fail — and the boundary violation must be fixed before the release gate is considered clear.

**`test_gui_application_workspace_contracts.py`** — Verifies the workspace restore behavior documented in Section 4 of the contracts document: the restore report contains all seven required fields, missing settings keys are skipped without aborting the restore, missing settings blocks are tracked, `GuiApplication.run_entrypoint` tolerates load/save failures without aborting shutdown, and the restore report is exposed via both `restore_workspace` and `load_workspace`.

### Runtime Behavior Tests

Beyond the contract tests, the following behavioral areas have dedicated test coverage:

- **Workspace load/save round-trip** — tests verify that a state written with `save_workspace` and loaded with `load_workspace` produces an identical runtime configuration, that the restore report accurately reflects what was and was not applied, and that workspace load failure is non-fatal.
- **Overlay, tooltip, and cursor routing** — tests verify that modal overlays consume events before the main tree, that non-modal toasts do not consume events directed at underlying controls, and that `CursorManager` push/pop semantics maintain correct stacking.
- **Layout and animation determinism** — tests verify that `FlexLayout`, `GridLayout`, and `ConstraintLayoutEngine` produce identical rects given identical input regardless of the order controls were added, and that `LayoutAnimator` produces reproducible intermediate positions.
- **Control runtime** — tests verify control state transitions (enabled, disabled, hidden, visible), focus ring membership, accessibility node synchronization, and correct event propagation through the control tree.
- **Accessibility specs** — tests verify that `StaticAccessibilitySpec` entries produce the declared node structure, that `TaskPanelFocusToggleSpec` correctly removes/adds controls to the focus ring on visibility change, and that `AccessibilityBus` delivers announcements to subscribers.

### Debug and Trace Tools

**`EventRecorder` and EventPlayback** — Record a sequence of `GuiEvent` objects during a live session for later replay. Use this to create reproducible regression test inputs from user-reported bugs. Record the session, save the event log, and add it as a test fixture. Future test runs replay the events deterministically to confirm the bug does not recur.

**`DebugOverlay`** — A visual inspection tool that overlays control bounds, focus ring order, spatial index regions, and frame budget bars directly on the live scene. Enable in debug builds; disable in release builds. Combine with `SceneSpatialIndex.controls_at_point(mouse_pos)` to produce a point-and-click control inspector.

**`PropertyInspectorPanel` and `PropertyInspectorModel`** — Bind any object decorated with `@ui_property` to a `PropertyInspectorPanel` to see its live property values at runtime. Use this during development to verify that observable state is being applied to controls correctly, without adding print statements.

**Telemetry log analysis** — After running a scenario with `configure_telemetry(enabled=True)`, call `analyze_telemetry_records(telemetry_collector.records)` and `render_telemetry_report(report)` to see per-span statistics. For offline analysis of previously saved logs, use `load_telemetry_log_file(path)` followed by `analyze_telemetry_log_file(path)`. Compare results against a baseline snapshot to detect regressions.

### Maintainer Release Runbook

This is the step-by-step sequence for clearing the release gate before publishing a new version of this manual or a new version of the framework.

1. **Run the full test suite.** `python -m pytest -q` must pass with zero failures and zero errors.
2. **Run the contract test subset explicitly.** See the command in the Contract Tests section above. Confirm each contract test is green individually — they can fail for different reasons and should each be reviewed separately.
3. **Check the boundary.** Review any new module in `gui_do/` for imports from `demo_features/`. Run `test_boundary_contracts.py`. Confirm no violations.
4. **Verify API inventory.** Run `test_public_api_exports.py`. If it fails, find the missing or extra name and fix the export list.
5. **Audit API docs contract.** Run `test_public_api_docs_contracts.py`. If it fails, find the divergence between `docs/` and `__init__.py` and update the contract document.
6. **Validate end-to-end reference.** Manually confirm the End-to-End Reference Application chapter compiles and runs without errors in the current environment.
7. **Validate workspace round-trip.** Run a save-then-load cycle with the reference app. Confirm the restore report has no unexpected skipped settings.
8. **Record and check telemetry baseline.** Run the reference app through a representative scenario with telemetry enabled. Compare the telemetry report against the previous baseline. Flag any span that exceeds its historical mean by more than 30%.
9. **Update the Migration chapter.** If any public API was renamed, removed, or had its behavior changed, add a migration note to the Migration, Versioning, and Deprecation Notes chapter.

### Regression Triage Workflow

When a behavioral regression is reported:

1. **Reproduce.** Create a minimal reproduction of the failure. If the failure is event-triggered, use `EventRecorder` to capture the exact event sequence.
2. **Trace.** Enable `configure_telemetry(enabled=True)` and run the repro. Examine the telemetry report to identify which system span is slow, missing, or anomalous.
3. **Localize.** Enable `DebugOverlay` and trace the event routing through the scene. Use `SceneSpatialIndex.controls_at_point` to confirm which control is at the failure point.
4. **Test-first.** Before writing the fix, write a failing test that captures the expected behavior. This ensures the regression is documented and prevents recurrence.
5. **Patch.** Implement the minimal fix that makes the new test pass without breaking existing tests.
6. **Check adjacent contracts.** After fixing, run the full contract test suite to confirm that fixing the regression did not introduce a contract violation in an adjacent system.

### Maintainer Diff Checklist

This checklist is the operational guide for developers regenerating or updating this manual after codebase changes. Work through every item before publishing an updated MANUAL.md. The checklist is organized into four categories: inventory deltas, content integrity, navigation and structure, and operational checks.

#### Inventory Delta Checks

1. **Root export delta.** Compare every tier block in `gui_do/__init__.py` against the corresponding entries in Appendix D (API Quick Index) and Appendix D.1 (Tier Matrix). For each name that has been added, confirm it appears in the appropriate system chapter's "Primary Public APIs and Key Types" subsection and in the appendix index. For each name that has been removed, confirm it has been removed from examples, recipes, and the appendix — or moved to the Migration chapter with a deprecation note.
2. **Contract document delta.** Read every file under `docs/` and check for changes to guarantees, boundary rules, field lists, or behavioral contracts. Pay particular attention to `docs/runtime_operating_contracts.md` Sections 4 and 6 (restore report fields and scheduler budget values) — these appear verbatim in system chapters and appendices and must match exactly.
3. **Contract test file delta.** List `tests/` and filter for files whose names begin with `test_*_contracts.py` or `test_runtime_*`. New files may imply new behavioral guarantees that require documentation in the relevant system chapter or in the Testing chapter.
4. **Demo composition pattern delta.** Inspect `demo_features/` for new feature packages or new composition patterns that represent usage best practices. If a new demo introduces a pattern not documented in the Integration Patterns chapter, add it there.

#### Content Integrity Checks

1. **Chapter and appendix consistency.** Every system that has changed must have its changes reflected in both the narrative chapter and the Appendix D quick-index entries. Partial updates — where the chapter is updated but the appendix index still references old names — introduce confusion and must be caught.
2. **Example staleness.** All code examples throughout the manual must reference names that currently exist in `gui_do/__init__.py`. Use grep or a search tool to find every occurrence of a removed or renamed API in code blocks, and update or remove each one. Do not leave examples that import names that no longer exist.
3. **Abstraction level placement.** APIs introduced at Tier 1 (primary entry points) should be documented in the early system chapters and the Quickstart. APIs introduced at Tier 18 or higher (advanced bootstrapping, infrastructure) should be documented in system chapter subsections on advanced patterns, not in the beginner-path sections. Verify that new additions are placed at the right abstraction level.

#### Navigation and Structure Checks

1. **TOC completeness.** Every section heading that appears in the document must have a corresponding entry in the Table of Contents with a working anchor link. Verify this after adding or renaming sections.
2. **Back-to-top links.** Every major section (H2 and H3 system chapters) must contain a `[Back to Table of Contents](#table-of-contents)` link immediately after the section heading. Verify that no section added during the update is missing this link.
3. **Chapter order stability.** The top-level chapter order must remain stable across updates unless an intentional restructure is recorded in the Migration chapter. If order changes are necessary, update all cross-references and the TOC simultaneously.

#### Operational Checks

1. **Re-run high-priority contract tests.** Before publishing the updated manual, run the command from the Contract Tests section and confirm all tests pass.
2. **Validate end-to-end reference assumptions.** After a codebase update, verify that the feature types, spec names, and lifecycle methods referenced in the End-to-End Reference Application chapter still exist and behave as described.
3. **Record unresolved ambiguities.** If the update reveals a behavioral area not fully covered by either a contract document or this manual, add an explicit TODO note in the Migration chapter rather than guessing.

---

## Performance and Scaling Guidance

[Back to Table of Contents](#table-of-contents)

### Scheduler Budget Contract

The `TaskScheduler` dispatch budget is a hard contract (from `docs/runtime_operating_contracts.md` Section 6):

- **fraction:** 0.12 of the frame's elapsed milliseconds (`dt`)
- **floor:** 0.5 ms — the minimum budget per frame, regardless of how fast the frame ran
- **ceiling:** 4.0 ms — the maximum budget per frame, regardless of how slow the frame ran

The floor prevents starvation: even if the application is running at 1000 fps with a 1 ms frame time, the scheduler gets at least 0.5 ms per frame to process queued tasks. The ceiling prevents runaway work: even if a frame takes 100 ms (10 fps), the scheduler will not consume more than 4.0 ms of it, leaving frame time for rendering and input handling.

The practical implication is that individual tasks dispatched through the scheduler should complete in well under 4.0 ms. Work that takes longer must be broken into smaller steps yielded across multiple frames, or offloaded to a background thread via `DataflowPipeline`.

### Dirty-Region Rendering

`DirtyRegionTracker` is the primary frame-rate optimization for scenes with complex custom rendering. Rather than redrawing the entire screen surface every frame, features call `mark_dirty(rect)` when a region of the screen has changed, and `overlaps_dirty(rect)` before re-rendering any region to skip unchanged areas.

The tracker maintains an incremental union rect as dirty regions are added. `overlaps_dirty(rect)` checks against this union rect in O(1) — it does not iterate over the list of individual dirty rects. This means the cost of `overlaps_dirty` calls does not grow with the number of dirty regions accumulated in a frame. `consume_dirty_regions()` returns the full list of dirty rects and resets the tracker for the next frame.

For scenes where most regions are static (tile maps with a moving character, canvases with fixed backgrounds and animated foregrounds), dirty-region tracking can reduce per-frame rendering time by 80–90%. Combine with `OffscreenRenderTarget` to cache expensive background rendering: only re-render the offscreen cache for the dirty tiles, then blit the cache to the screen.

### Virtualization and Incremental Rendering

For large datasets in list, grid, or tree views:

- **`VirtualizationCore` and `VirtualizedWindow`** — render only the items currently visible in the scroll viewport. For a list of 10,000 items with a viewport that shows 30 at a time, only 30 item controls are live at any moment. The `RecyclePool` recycles off-screen item views rather than destroying and recreating them, eliminating per-scroll GC pressure.
- **`ListDiffCalculator`** — when a dataset changes partially (a filter is applied, an item is added), `ListDiffCalculator` computes the minimal set of `DiffInsert`, `DiffRemove`, and `DiffMove` operations needed to transform the old list into the new list. Applying this patch to the UI produces smooth incremental updates — selection and scroll position are preserved, and only the changed items are re-rendered.
- **`RecyclePool`** — for features that manually manage a pool of item views (outside `VirtualizationCore`), `RecyclePool` provides a typed acquire/release interface that prevents duplicate allocation of view objects.

### Practical Scaling Checklist

Apply these practices to maintain frame budget as the application grows:

1. **Enforce scene-scoped updates.** Features registered in a scene's `feature_attributes` only run `on_update` when that scene is active. Never register a feature globally if it only needs to update in one scene.
2. **Avoid per-frame full collection reallocation.** Creating new lists or dicts in `on_update` every frame generates GC pressure. Use `ObjectPool` for high-churn temporary objects; reuse fixed-size buffers for particle positions, event records, and frame-local data.
3. **Debounce expensive operations.** Wrap search queries, form validation, and resize handlers in `Debouncer` or `Throttler`. A search query that runs on every keystroke can be debounced to fire 300 ms after the user stops typing with a single call to `Debouncer(callback, delay=0.3)`.
4. **Use `DataflowPipeline` for preemptible background work.** Any data transformation that could take more than 1 ms should run inside a `DataflowPipeline` stage with a `CancellationToken`. This allows the pipeline run to be canceled and restarted when new input arrives, preventing queued-up work from causing frame stalls when the user interacts quickly.
5. **Profile representative user interactions, not synthetic idle scenarios.** Telemetry recorded during an idle event loop measures nothing meaningful. Always record telemetry while performing the specific scenario that feels slow — typing in a search field, resizing a large grid, opening a complex dialog.
6. **Gate expensive draw regions with `DirtyRegionTracker`.** Before redrawing any complex custom region (particle systems, tile maps, canvas visualizations), check `overlaps_dirty(region_rect)`. If the region has not changed, skip the draw call entirely.

---

## Migration, Versioning, and Deprecation Notes

[Back to Table of Contents](#table-of-contents)

### Versioned Snapshot Strategy

gui_do's persistence layer is designed for schema evolution. As an application grows, its workspace schema changes: new fields are added, old fields are removed or renamed, nested structures are reorganized. Without a versioned migration strategy, loading an old workspace snapshot with new application code produces a runtime error or silent data loss.

The recommended workflow:

1. **Write snapshots** with `make_snapshot(current_version, state_dict)` to create a `VersionedSnapshot` that carries the current schema version alongside the data.
2. **On load**, call `read_version(raw_snapshot_dict)` to determine the stored version. If the version equals the current version, apply the snapshot directly. If the version is older, run migrations.
3. **Register migration steps.** Create a `MigrationRegistry` and register a `MigrationStep` for each schema version transition (N → N+1). Each step is a callable that takes the previous schema's data dict and returns the next schema's data dict.
4. **Migrate.** Call `SnapshotMigrator(registry).migrate(snapshot, target_version)`. The migrator walks the registered steps in BFS order, transforming the snapshot from its stored version to the current version. If no migration path exists between the stored version and the current version, `MigrationError` is raised.
5. **Apply.** Restore the migrated snapshot into the runtime.

This strategy ensures that workspaces saved by any previous version of the application can be loaded with the current version, as long as migration steps are registered for each schema transition.

```python
from gui_do import (
    SchemaVersion, make_snapshot, read_version,
    MigrationStep, MigrationRegistry, SnapshotMigrator, VersionedSnapshot
)

V1 = SchemaVersion(1)
V2 = SchemaVersion(2)

registry = MigrationRegistry()
registry.register(MigrationStep(
    from_version=V1, to_version=V2,
    migrate=lambda data: {**data, "new_field": data.get("new_field", "default_value")},
))
migrator = SnapshotMigrator(registry)

raw = load_json_from_disk("session.json")
version = read_version(raw)
snapshot = VersionedSnapshot(version=version, data=raw)
migrated = migrator.migrate(snapshot, target_version=V2)
# apply migrated.data to the runtime...
```

### Deprecation Handling

The recommended deprecation policy for public API changes:

- **Prefer additive transitions.** Add new parameters or fields with defaults; keep the old parameters working. This prevents most breakage at the call site and allows gradual migration.
- **Warn before removing.** If an old interface must be removed, add a `DeprecationWarning` in the old code path for at least one release cycle before removal.
- **Provide a migration path.** Every removal should be documented here with "old usage → new usage" so developers can find the correct replacement without guessing.
- **Centralize deprecations.** All formal deprecation notices belong in this section. Do not scatter deprecation notices through the narrative chapters.

**Current deprecations:** No public API deprecations are cataloged in this release. Maintainers should add entries here when formal deprecations are introduced, using the format:

```
### [API Name] — Deprecated in vX.Y
Old usage: `from gui_do import OldName`
New usage: `from gui_do import NewName`
Migration: Replace `OldName(...)` with `NewName(...)`. The signature is identical except ...
Removal target: vZ.W
```

### Upgrade Checklist

When upgrading from one version of gui_do to the next:

1. **Run contract tests before and after.** The contract tests are the fast signal for whether any behavioral guarantee has changed. Run them on the current version; then upgrade; then run them again. Any newly failing test identifies a behavioral change that needs investigation.
2. **Verify root import usage.** Consumer code should only import from `gui_do` root (`from gui_do import Feature`), never from internal submodules. After an upgrade, search your codebase for imports from `gui_do.features`, `gui_do.controls`, `gui_do.events`, etc., and replace them with root imports.
3. **Check action/input/focus routing in active scenes.** Actions registered via `RoutedRuntimeSpec` are wired differently from manually registered actions. After an upgrade, verify that all hotkeys still fire correctly in each scene, that focus cycling does not stall, and that overlay toggle keys still work.
4. **Validate workspace restore report.** Load a workspace saved with the old version using the new version. Inspect `report.skipped_settings` and `report.missing_settings_blocks`. Skipped settings indicate validation failures; missing blocks indicate removed settings keys. Handle each with a migration step or a default value.
5. **Re-run telemetry baseline.** Run the same representative scenario you used for the previous baseline. Compare the new telemetry report against the old baseline. A span that has grown significantly signals a performance regression in the new version.

---

## FAQ and Troubleshooting

[Back to Table of Contents](#table-of-contents)

**Q: Should I build applications directly with controls, or with features?**

Use features as the architectural unit. Controls are implementation details that live inside feature boundaries. A feature provides lifecycle orchestration (build → bind → update → draw → shutdown), event routing through the action and input systems, observable state binding, and clean teardown. A control alone cannot do any of these things — it has no lifecycle, no event registration mechanism, and no observable subscription management. The feature is the unit of composition; the control is the unit of rendering.

**Q: When should I use `RoutedFeature` over `Feature`?**

Use `RoutedFeature` when your feature needs declarative runtime wiring: hotkeys registered via `RoutedRuntimeSpec.action_bindings`, a shortcut help overlay declared via `ShortcutOverlaySpec`, task panel focus toggles declared via `TaskPanelFocusToggleSpec`, or topic-based message dispatch. These concerns are expressed as a data object (`RoutedRuntimeSpec`) and wired automatically by `bind_routed_feature_lifecycle`. If your feature only needs the basic lifecycle phases (build, bind, update, draw, shutdown) and a control tree — with no hotkeys, no overlays, and no topic routing — plain `Feature` is sufficient and simpler.

**Q: Why are some key handlers not firing?**

Check each of the following in order: (1) **Focus ownership** — is another control capturing keyboard input? A `TextInputControl` that has focus will consume most key events before they reach the action system. (2) **Window scope** — is the action registered in a window scope but the window is hidden? Window-scoped actions only fire when that window has focus. (3) **Overlay modal capture** — is an open modal dialog or command palette consuming all keyboard events? While a modal overlay is open, the main scene does not receive key events. (4) **Scene scope** — is the action registered for the wrong scene? An action bound in a `RoutedRuntimeSpec` is only active in the scene of its owning feature. Use `EventRecorder` to capture the exact event sequence and inspect which routing stage consumed the event.

**Q: Why do toast clicks not pass through to controls underneath?**

By contract, toast bounds consume left-click events within their bounds to prevent accidental clicks on controls beneath a toast during the toast's visibility period. This is intentional. If you want a toast that responds to clicks, use the `on_click` callback in `ToastManager.show`. If you need click-through behavior, do not use the toast system — use a `LabelControl` with a custom position and lifetime instead.

**Q: How do I avoid breaking workspace restore across application versions?**

Use `VersionedSnapshot` from the beginning. Wrap all persisted state in `make_snapshot(current_version, state_dict)` on save. On load, call `read_version(raw)` before applying the snapshot. Register `MigrationStep` objects for each schema change in a `MigrationRegistry`. Inspect the restore report for `skipped_settings` and `missing_settings_blocks` and handle them gracefully — for example, by showing a non-blocking toast that informs the user that some preferences could not be restored and have been reset to defaults. The restore is never fatal; it is designed to succeed with partial data rather than abort.

**Q: How do I confirm my API usage is within the supported public surface?**

Always import from the `gui_do` root package: `from gui_do import Feature, ObservableValue, ...`. Never import from internal submodules (`gui_do.features`, `gui_do.controls`, `gui_do.events`, `gui_do.scheduling`, etc.) — these are implementation details that are not covered by the stability policy. Run `tests/test_public_api_exports.py` to verify that every name you import from `gui_do` is in `__all__`. If a name you need is not in `__all__`, it is not a supported public API.

**Q: Why does my feature's `bind_runtime` run before my sibling feature's `build`?**

It does not. The framework guarantees that all features in a scene complete their `build` phase before any feature's `bind_runtime` phase begins. If you observe ordering issues, confirm that all features are declared in the same scene's `feature_attributes` list in the `RuntimeSceneSpec`. Features declared in different scenes build and bind independently. If a feature in scene A needs to see the controls of a feature in scene B, you have a design problem: cross-scene control references violate the scene isolation boundary.

**Q: How do I add a keyboard shortcut without changing every place that key is handled?**

Declare an `ActionSpec` in `HostApplicationConfig.actions` and bind it to a key in `RoutedRuntimeSpec.action_bindings`. The framework registers the action with the `ActionManager` and the key binding with the `InputMap` automatically via `bind_routed_feature_lifecycle`. The handler is set via `host.action_manager.set_handler("action.name", callback)` in `bind_runtime`. There is no need to implement event handling logic in `handle_event` for standard key shortcuts.

---

## Appendix

[Back to Table of Contents](#table-of-contents)

### A: Glossary

**Feature** — The fundamental unit of application behavior in gui_do. A feature owns a bounded set of controls, observables, and event handlers for one cohesive piece of application functionality. Features implement the phased lifecycle: `build` (construct controls), `bind_runtime` (wire observables and actions), `on_update`/`handle_event`/`draw` (operational phase), and `shutdown_runtime` (cleanup). The four feature base classes provide different levels of framework integration: `DirectFeature` (minimal, no spec wiring), `Feature` (standard lifecycle), `LogicFeature` (headless, no controls), and `RoutedFeature` (full declarative wiring via `RoutedRuntimeSpec`).

**Spec** — A plain Python dataclass that declaratively describes runtime wiring. Specs are data, not behavior. They describe what should be wired (an action's name and label, a window's anchor and size, a shortcut overlay's toggle key and sections), and the bootstrap system reads them to perform the actual wiring. The separation of specs from behavior is what makes the framework testable: specs can be constructed and inspected in unit tests without instantiating any GUI infrastructure.

**Host** — A plain Python object created by `bootstrap_host_application` and passed to each feature's lifecycle methods. The host provides access to all runtime members (app, action manager, input map, theme manager, toasts, dialogs, timers, tweens, scheduler, font manager, etc.) as named attributes. Features declare which host attributes they require in `HOST_REQUIREMENTS`; the framework validates these at bootstrap time and raises a clear error if a declared requirement is not available.

**Scene** — A top-level interaction context. Only one scene is active at a time; switching scenes replaces the entire set of active features, background, layout, and available actions. Each feature belongs to exactly one scene, declared via `scene_name` in the feature's constructor. The `SceneTransitionManager` manages animated transitions between scenes.

**Window presentation** — The window-level visibility, focus, and routing model within a scene. Windows are floating or anchored UI surfaces managed by `WindowControl` and `WindowPresenter`. The `ScenePresentationModel` coordinates window registration, visibility state, and task panel association. `TaskPanelFocusToggleSpec` ensures that hidden windows do not retain focus ring membership.

**Routed runtime** — The declarative bundle of hotkeys, overlay configuration, topic subscriptions, and focus toggles for a `RoutedFeature`. Expressed as a `RoutedRuntimeSpec` data object; wired into the framework by `bind_routed_feature_lifecycle` and unwired by `shutdown_routed_feature_lifecycle`. The routed runtime is the recommended pattern for all features that interact with the action system, shortcut overlay, or task panel.

**Observable** — A value container that notifies registered subscribers when its value changes. `ObservableValue` is the simplest form; `ObservableList` and `ObservableDict` track collection mutations; `ComputedValue` derives from other observables. Observables are the reactive data layer: the UI subscribes to observables and updates itself automatically when the underlying data changes, with no polling and no manual refresh calls.

**Workspace state** — The persisted runtime context that survives application restarts: which scene was active, what state each feature had saved, what settings were configured. Saved by `GuiApplication.save_workspace` as a versioned JSON file; restored by `GuiApplication.load_workspace`. The restore produces a structured report with seven fields identifying what was applied, skipped, and missing.

**Contract test** — An automated test that verifies a framework-level behavioral guarantee. Contract tests are not unit tests of internal implementation — they test observable behavior from the outside. They are the authoritative source of truth for which guarantees are mechanically enforced, and they are the release gate: no release is complete until all contract tests pass.

**Tier** — A grouping of public API exports by abstraction level and recommended usage priority. Tier 1 contains the most important entry points (feature types, bootstrap, spec types). Higher tier numbers indicate more specialized or lower-level APIs. The Tier Matrix (Appendix D.1) maps each tier to its system chapter and representative types. Application code should prefer lower-numbered tiers and should never import from higher-numbered tiers unless a specific advanced need requires it.

---

### B: Lifecycle and Event Routing Sequence

The following is the complete ordered sequence of framework lifecycle events from application startup through shutdown.

1. **`bootstrap_host_application(config, binding)`** — The framework reads the `HostApplicationConfig` and `HostApplicationBindingSpec`, initializes pygame, creates the display surface, builds the host object, registers all specs (actions, font roles, cursor bindings), and constructs the initial scene.
2. **All feature `build(host)` calls in scene order** — For each scene, all features in `feature_attributes` have their `build` method called in declaration order. Controls are created and added to the control tree. No feature's `bind_runtime` is called until all features in the scene have completed `build`.
3. **All feature `bind_runtime(host)` calls** — After all builds are complete, each feature's `bind_runtime` is called. Observable subscriptions are created, actions are wired, routed lifecycle specs are bound, and initial data is loaded from workspace state.
4. **Runtime loop begins** — `GuiApplication.run_entrypoint` enters the main frame loop.
5. **Each frame: raw pygame events → `GuiEvent` normalization** — Raw `pygame.event.Event` objects are converted to `GuiEvent` instances with normalized type codes, sender references, and cloneable metadata.
6. **Overlay/focus/window/scene routing pass** — Normalized events are routed through the overlay routing layer first (modal overlays consume events), then through the window routing layer (window-scoped actions fire for the focused window), then through the scene routing layer (scene-scoped actions fire).
7. **Feature `handle_event(host, event)` calls in routing order** — Events that are not consumed by the routing layer are dispatched to features' `handle_event` methods.
8. **Feature `on_update(host, dt)` calls; scheduler dispatches tasks** — Each feature's `on_update` is called with the elapsed frame time. The `TaskScheduler` then dispatches queued cooperative scheduler tasks within the per-frame budget.
9. **Feature `draw(host, screen)` calls; control tree renders; present to screen** — Custom feature rendering runs; the control tree is drawn in z-order; the compositor assembles the final frame; `pygame.display.flip()` presents it.
10. **On scene transition** — `shutdown_runtime` is called for all departing scene's features (in reverse declaration order). The new scene's features then run `build` followed by `bind_runtime` before the next frame.
11. **On application exit** — `shutdown_runtime` is called for all active features. Workspace save is performed (if configured). pygame is quit. `run_entrypoint` returns.

---

### C: System Dependency Map

Understanding which systems depend on which others helps when diagnosing bootstrap failures, planning feature composition, and deciding which systems to initialize in which order.

**Bootstrap (Tier 1)** depends on almost everything: all spec types (feature, action, scene, window, font role, cursor, task panel), the Feature lifecycle protocol, the scene and window presentation model, the action/input system, font and theme configuration, and the persistence manager. The bootstrap pass is intentionally heavyweight — it exists to perform all wiring at once so that the operational phase is dependency-free.

**Features (Tiers 1–2)** depend on the control system (to construct their UI), the observable/data layer (for reactive state), and the event/action system (for user interaction). Features do not depend on each other; inter-feature communication happens through `AppStateStore` or observables declared on a shared spec.

**Layout (Tier 8)** and **Focus (Tier 4)** depend on the control tree and the scene/window visibility model. Layout engines receive their control tree from features during `build`; the focus ring is populated from the same control tree. Both systems react to window visibility changes (via `TaskPanelFocusToggleSpec`) to stay synchronized with what the user can actually interact with.

**Overlays (Tier 9)** depend on the event routing layer (to intercept events before the main tree) and the focus policy (to trap focus during modal sessions). The overlay rendering layer is above the control tree in z-order; overlay managers enforce their own dismissal contracts independent of the main control tree.

**Persistence (Tiers 11, 32)** depends on the state model (to know what to save), the settings registry (for settings round-trip), and the scene and window registration (to know which scene to restore to). The persistence layer is intentionally decoupled from the feature lifecycle — features opt in via `save_state`/`load_state` methods, but the workspace manager does not require features to implement these.

**Scheduling (Tier 5)** and animation depend on the feature update loop (to receive per-frame ticks) and the scene scope (to stop updating when a scene exits). `TweenManager` and `CooperativeScheduler` are per-scene resources that become inactive when their scene is not the active scene.

**Telemetry and introspection (Tiers 7, 17)** cross-cut all runtime layers. Telemetry spans can be added to any code path without affecting the code path's behavior. The `PropertyRegistry` collects `@ui_property` descriptors at import time, independent of the runtime lifecycle.

**Audio (Tier 20)** depends on pygame's mixer (which is initialized during bootstrap) and is surfaced through `SoundEventBus`. Features publish named `SoundCue` events without knowing which audio backend is active; the bus handles routing to the mixer.

**Service scope (Tier 25)** is a general-purpose dependency injection container that is usable at any tier. `ServiceScope` and `ScopeStack` allow features to declare and resolve named services without hard-coded cross-feature references.

---

### D: API Quick Index by Topic

The following index lists all exported names from `gui_do` organized by functional topic. Every name in `gui_do.__all__` appears in exactly one topic group.

**Bootstrap and Host Configuration**
`bootstrap_host_application`, `build_host_application_config`, `HostApplicationConfig`, `HostApplicationBindingSpec`

**Feature Types and Lifecycle**
`DirectFeature`, `Feature`, `LogicFeature`, `RoutedFeature`, `FeatureSpec`, `FeatureWindowBundleBindingSpec`, `WindowToggleBindingSpec`

**Application and Display**
`GuiApplication`, `create_display`, `UiEngine`

**Scene Management**
`SceneTransitionManager`, `apply_scene_setup_specs`, `RuntimeSceneSpec`, `SceneBundleBindingSpec`, `ScenePresentationModel`, `SceneCommandPaletteSpec`

**Observables and Reactive State**
`ObservableValue`, `ObservableList`, `ObservableDict`, `CollectionView`, `Binding`, `ObservableStream`, `SelectionModel`, `PresentationModel`, `ComputedValue`, `reactive_batch`, `is_batching`

**App State Store**
`AppStateStore`, `StateSelector`, `StateTransaction`

**Events and Input**
`EventPhase`, `EventType`, `GuiEvent`, `EventManager`, `EventBus`, `GestureRecognizer`, `EventRecorder`, `InputSnapshot`, `Signal`

**Actions and Key Bindings**
`ActionManager`, `ActionRegistry`, `InputMap`, `KeyChordManager`, `ActionSpec`, `ActionHotkeySpec`, `ActionBindingSpec`

**Focus and Window Focus**
`FocusManager`, `FocusScope`, `WindowFocusManager`, `FocusRing`

**Routed Runtime and Lifecycle Specs**
`RoutedRuntimeSpec`, `RoutedFeatureLifecycleSpec`, `bind_routed_feature_lifecycle`, `shutdown_routed_feature_lifecycle`, `AccessibilitySequenceSpec`, `StaticAccessibilitySpec`, `TaskPanelFocusToggleSpec`, `ShortcutOverlaySpec`, `ShortcutSection`, `ShortcutEntry`

**Window and Scene Presentation Specs**
`WindowSpec`, `AnchoredWindowSpec`, `WindowPresenter`, `TabbedPresenterSpec`, `TabBuilderSpec`, `SceneTaskPanelSpec`, `TaskPanelButtonSpec`, `TaskPanelLinearLayoutSpec`, `TaskPanelWindowToggleGroupSpec`, `TaskPanelSceneNavButtonSpec`

**Scheduling and Timing**
`TaskEvent`, `TaskScheduler`, `Timers`, `TweenManager`, `TweenHandle`, `Easing`, `AnimationSequence`, `AnimationHandle`, `TransitionManager`, `TransitionSpec`, `TransitionEvent`, `AnimationStateMachine`, `AnimationTransitionMode`, `SceneTimeline`, `Debouncer`, `Throttler`, `CooperativeScheduler`, `CoroutineHandle`, `Pause`, `Sleep`, `WaitForEvent`, `WaitForSignal`, `WaitUntil`, `WaitForAll`

**Theme, Fonts, and Design Tokens**
`FontManager`, `FontRoleRegistry`, `ColorTheme`, `ThemeManager`, `DesignTokens`, `ScopedTheme`, `ScopedThemeManager`, `FontRoleBindingSpec`, `CursorSpec`, `CursorBindingSpec`, `setup_standard_font_roles`

**Theme Invalidation**
`ThemeInvalidationBus`

**Telemetry**
`TelemetryCollector`, `TelemetrySample`, `configure_telemetry`, `telemetry_collector`, `analyze_telemetry_log_file`, `analyze_telemetry_records`, `load_telemetry_log_file`, `render_telemetry_report`, `TelemetryConfig`

**Layout Engines**
`LayoutAxis`, `LayoutManager`, `WindowTilingManager`, `FlexLayout`, `FlexItem`, `FlexDirection`, `FlexAlign`, `FlexJustify`, `GridLayout`, `GridTrack`, `GridPlacement`, `FlowLayout`, `FlowItem`, `CellCaretLayout`, `CellCaretState`, `LayoutAnimator`, `LayoutPass`, `MeasureContext`, `ArrangeContext`, `LayoutRoot`, `ResponsiveLayout`, `Breakpoint`, `SnapGrid`, `AlignmentGuide`, `SnapComposer`, `SnapTarget`, `Viewport`

**Dock Workspace Layout**
`DockPane`, `DockTabs`, `DockSplit`, `DockWorkspace`

**Constraint Layout**
`ConstraintLayout`, `AnchorConstraint`, `ConstraintAttr`, `LayoutConstraint`, `ConstraintSet`, `ConstraintLayoutEngine`, `AdaptivePolicy`, `resolve_adaptive_policy`

**Virtualization**
`MeasureMode`, `MeasurePolicy`, `VirtualizedWindow`, `RecyclePool`, `VirtualizationCore`

**Overlays and Dialogs**
`OverlayManager`, `OverlayHandle`, `Alignment`, `PlacementResult`, `PopupPlacement`, `Side`, `compute_popup_rect`, `DialogManager`, `DialogHandle`, `ToastManager`, `ToastHandle`, `ToastSeverity`, `ContextMenuManager`, `ContextMenuItem`, `ContextMenuHandle`, `CommandPaletteManager`, `CommandEntry`, `CommandPaletteHandle`, `TooltipManager`, `TooltipHandle`, `MenuBarManager`, `FileDialogManager`, `FileDialogOptions`, `FileDialogHandle`, `NotificationCenter`, `NotificationRecord`, `ResizeManager`, `CursorManager`, `CursorHandle`, `CursorShape`, `DragDropManager`, `DragPayload`, `ClipboardManager`, `TransferData`, `TransferManager`, `ShortcutHelpOverlay`

**Forms and Validation**
`FormModel`, `FormField`, `ValidationRule`, `FieldError`, `FormSchema`, `SchemaField`, `DocumentModel`, `WizardFlow`, `WizardStep`, `WizardHandle`, `ValidationResult`, `Validator`, `RequiredValidator`, `RangeValidator`, `LengthValidator`, `PatternValidator`, `CustomValidator`, `DependentValidator`, `ValidationPipeline`

**Async Form Validation**
`AsyncFieldValidator`, `AsyncFormValidator`

**Schema-Driven Form Runtime**
`FieldSchema`, `FieldGraphSchema`, `ValidationPolicy`, `SchemaFormRuntime`

**Text and Localization**
`TextFormatter`, `NumericFormatter`, `PatternFormatter`, `FixedPatternFormatter`, `TextFlow`, `TextSpan`, `TextSearcher`, `TextMatch`, `StringTable`, `LocaleRegistry`

**Persistence and State Machines**
`CommandHistory`, `Command`, `CommandTransaction`, `StateMachine`, `HierarchicalStateMachine`, `Router`, `RouteEntry`, `SettingsRegistry`, `SettingDescriptor`, `WorkspaceState`, `WorkspacePersistenceManager`, `DEFAULT_WORKSPACE_STATE_PATH`, `SceneSnapshot`, `NodeSnapshot`

**Undo Context**
`UndoContextManager`

**Versioned Snapshots and Migration**
`SchemaVersion`, `VersionedSnapshot`, `MigrationStep`, `MigrationRegistry`, `SnapshotMigrator`, `MigrationError`, `make_snapshot`, `read_version`

**Data and Collections**
`VirtualItemSource`, `FixedItemSource`, `SortFilterProxySource`, `AsyncDataProvider`, `LoadState`, `LoadStateKind`, `ObjectPool`, `DataCache`, `CacheStats`, `ListDiffCalculator`, `ListDiff`, `DiffInsert`, `DiffRemove`, `DiffMove`

**Dataflow Pipeline**
`CancellationToken`, `PipelineStage`, `DataflowPipeline`, `PipelineHandle`

**Graphics and Rendering**
`BuiltInGraphicsFactory`, `DirtyRegionTracker`, `DrawContext`, `DrawPhase`, `AssetRegistry`, `DebugOverlay`, `SurfaceCompositor`, `Layer`, `ShapeRenderer`, `SurfaceEffects`, `VectorPath`, `SpriteSheet`, `FrameAnimation`, `ParticleSystem`, `Emitter`, `ParticleLayer`, `TileSet`, `TileMap`, `RenderTarget`, `LiveRenderTarget`, `OffscreenRenderTarget`, `create_render_target`, `create_surface`, `Node2D`, `SceneGraph2D`, `Camera2D`

**Audio**
`SoundCue`, `SoundBankRegistry`, `SoundEventBus`

**Accessibility**
`AccessibilityRole`, `LivePoliteness`, `AccessibilityNode`, `AccessibilityTree`, `AccessibilityAnnouncement`, `AccessibilityBus`

**Introspection and Spatial Index**
`SceneSpatialIndex`, `ui_property`, `PropertyDescriptor`, `PropertyRegistry`, `property_registry`, `PropertyInspectorModel`, `InspectedProperty`

**Interaction State Machine**
`InteractionPhase`, `InteractionContext`, `InteractionTransition`, `InteractionStateMachine`

**Service Scope**
`ServiceKey`, `ServiceScope`, `ScopeStack`

**Primary Controls (Tier 12)**
`PanelControl`, `LabelControl`, `ButtonControl`, `ToggleControl`, `SliderControl`, `ScrollbarControl`, `CanvasControl`, `CanvasEventPacket`, `CanvasViewport`, `FrameControl`, `ImageControl`, `ArrowBoxControl`, `ButtonGroupControl`, `TabControl`, `TabItem`, `DockWorkspacePanel`

**Extended Controls (Tier 13)**
`TextInputControl`, `TextAreaControl`, `RichLabelControl`, `DropdownControl`, `DropdownOption`, `ListViewControl`, `ListItem`, `OverlayPanelControl`, `DataGridControl`, `GridColumn`, `GridRow`, `TreeControl`, `TreeNode`, `SplitterControl`, `SpinnerControl`, `RangeSliderControl`, `ColorPickerControl`, `ScrollViewControl`, `ProgressBarControl`, `AnimatedImageControl`, `ErrorBoundary`, `WindowControl`, `TaskPanelControl`, `WindowPresenter`, `MenuBarControl`, `MenuEntry`, `SceneMenuStripControl`, `NotificationPanelControl`, `PropertyInspectorPanel`, `ToolbarControl`, `ToolbarItem`, `StatusBarControl`, `StatusSlot`, `ExpanderControl`, `DatePickerControl`, `TimePickerControl`, `BreadcrumbControl`, `BreadcrumbItem`, `SplitButtonControl`, `SplitButtonOption`, `ChipInputControl`

**Advanced Bootstrap Helpers (Tier 18)**
`FrameTimer`, `TabPanelManager`, `WindowRelativeRect`, `ActiveTabUpdateRouter`, `TabLayoutContext`, `set_window_visible_state`, `toggle_window_visibility`, `create_anchored_feature_window`, `create_feature_presented_window`, `create_presented_anchored_window`, `create_presented_window_from_spec`, `add_window_scene_menu_strip`, `add_standard_scene_menu_strip`, `ensure_scene_task_panel`, `add_task_panel_buttons`, `add_task_panel_window_toggle_group`, `add_task_panel_scene_nav_button`, `add_scene_task_panel_items`, `add_window_toggle_task_panel_controls`, `register_window_toggle_tooltips`, `apply_window_toggle_accessibility`, `build_host_main_tab_order`, `apply_host_main_accessibility`, `inset_rect`, `centered_horizontal_strip_layout`, `split_slot_bounds`, `partition_rects`, `place_control`, `place_control_unlabeled`, `register_placed_control`, `add_group_label`, `PlacedControl`, `make_labeled_slot_height_fn`, `minimize_window_menu_entries`, `build_tools_menu_entries`, `ControlDefinition`, `build_specs_from_column_section`, `RowCellSpec`, `build_horizontal_row_specs`, `build_multi_column_grid_specs`, `NotificationSpec`, `ShortcutOverlaySpec`

**Infrastructure**
`UiEngine`

---

### D.1: Tier-to-System Reference Matrix

| Tier | System | Representative Key Types |
|------|--------|--------------------------|
| 1 | Feature types, spec types, bootstrap | `Feature`, `RoutedFeature`, `HostApplicationBindingSpec`, `bootstrap_host_application`, `RuntimeSceneSpec` |
| 2 | Application and display | `GuiApplication`, `create_display`, `SceneTransitionManager`, `apply_scene_setup_specs` |
| 3 | Observables and reactive state | `ObservableValue`, `PresentationModel`, `ComputedValue`, `ObservableList`, `CollectionView` |
| 4 | Events, actions, input, focus | `EventManager`, `ActionManager`, `InputMap`, `FocusManager`, `FocusScope`, `FocusRing` |
| 5 | Scheduling, timing, animation | `TaskScheduler`, `TweenManager`, `AnimationStateMachine`, `CooperativeScheduler`, `Sleep`, `WaitForSignal` |
| 6 | Theme, fonts, design tokens | `FontManager`, `FontRoleRegistry`, `ColorTheme`, `ThemeManager`, `DesignTokens`, `ScopedTheme` |
| 7 | Telemetry | `TelemetryCollector`, `configure_telemetry`, `analyze_telemetry_records`, `render_telemetry_report` |
| 8 | Layout engines | `FlexLayout`, `GridLayout`, `DockWorkspace`, `ConstraintLayout`, `SnapGrid`, `LayoutAnimator` |
| 9 | Overlays, dialogs, notifications | `DialogManager`, `ToastManager`, `ContextMenuManager`, `CommandPaletteManager`, `DragDropManager` |
| 10 | Forms and validation | `FormModel`, `FormSchema`, `SchemaFormRuntime`, `ValidationPipeline`, `WizardFlow`, `DocumentModel` |
| 11 | Persistence and state machines | `WorkspacePersistenceManager`, `SettingsRegistry`, `CommandHistory`, `StateMachine`, `Router` |
| 12 | Primary controls | `PanelControl`, `ButtonControl`, `LabelControl`, `SliderControl`, `CanvasControl`, `TabControl` |
| 13 | Extended controls | `TextInputControl`, `ListViewControl`, `DataGridControl`, `TreeControl`, `ErrorBoundary`, `DropdownControl` |
| 14 | Text and localization | `TextFormatter`, `NumericFormatter`, `TextFlow`, `TextSpan`, `TextSearcher`, `LocaleRegistry` |
| 15 | Data and collections | `VirtualItemSource`, `SortFilterProxySource`, `AsyncDataProvider`, `DataCache`, `ListDiffCalculator` |
| 16 | Graphics and rendering | `DirtyRegionTracker`, `SurfaceCompositor`, `ParticleSystem`, `TileMap`, `SceneGraph2D`, `Camera2D` |
| 17 | Introspection and spatial index | `SceneSpatialIndex`, `ui_property`, `PropertyRegistry`, `PropertyInspectorModel` |
| 18 | Advanced bootstrap helpers | `set_window_visible_state`, `create_feature_presented_window`, `ActiveTabUpdateRouter`, `ensure_scene_task_panel` |
| 19 | Infrastructure internals | `UiEngine` — avoid in application code |
| 20 | Audio | `SoundCue`, `SoundBankRegistry`, `SoundEventBus` |
| 21 | Accessibility | `AccessibilityRole`, `AccessibilityNode`, `AccessibilityTree`, `AccessibilityBus` |
| 22 | Theme invalidation | `ThemeInvalidationBus` |
| 23 | Undo context | `UndoContextManager` |
| 24 | Async form validation | `AsyncFieldValidator`, `AsyncFormValidator` |
| 25 | Service scope | `ServiceKey`, `ServiceScope`, `ScopeStack` |
| 26 | Dataflow pipeline | `CancellationToken`, `PipelineStage`, `DataflowPipeline`, `PipelineHandle` |
| 27 | App state store | `AppStateStore`, `StateSelector`, `StateTransaction` |
| 28 | Adaptive constraint layout | `ConstraintAttr`, `ConstraintSet`, `ConstraintLayoutEngine`, `AdaptivePolicy`, `resolve_adaptive_policy` |
| 29 | Virtualization core | `MeasureMode`, `MeasurePolicy`, `VirtualizedWindow`, `RecyclePool`, `VirtualizationCore` |
| 30 | Interaction state machine | `InteractionPhase`, `InteractionContext`, `InteractionTransition`, `InteractionStateMachine` |
| 31 | Schema-driven form runtime | `FieldSchema`, `FieldGraphSchema`, `ValidationPolicy`, `SchemaFormRuntime` |
| 32 | Versioned snapshots and migration | `SchemaVersion`, `VersionedSnapshot`, `MigrationStep`, `SnapshotMigrator`, `make_snapshot`, `read_version` |

---

### D.2: Public API Selection Heuristics

Apply these decision rules to find the right tier for a task:

1. **Start at Tier 1.** If `HostApplicationConfig`, `bootstrap_host_application`, and one of the four feature base types solve the problem, stop there. Tier 1 is intentionally complete for most applications.
2. **Descend one tier at a time.** If Tier 1 is insufficient, read the next relevant tier's entries and evaluate whether they solve the remaining need. Do not skip to lower-level tiers speculatively.
3. **Use Tier 18 for bootstrap extension points.** When extending the scene presentation (adding windows, task panels, menu strips), the Tier 18 helpers (`create_anchored_feature_window`, `ensure_scene_task_panel`, `add_standard_scene_menu_strip`) are the stable extension surface. They are more stable than constructing `WindowControl` or `TaskPanelControl` instances directly.
4. **Never import from submodules.** Always use `from gui_do import <Name>`. Internal submodule paths are not covered by the stability policy and may change between minor versions without notice.
5. **Avoid Tier 19 (`UiEngine`) in application code.** `UiEngine` is the internal rendering orchestrator. It is exported for framework extension scenarios only; application code has no legitimate use for it.

**Decision shortcuts by common need:**

- Need application setup → `HostApplicationConfig` + `bootstrap_host_application` (Tier 1)
- Need reactive UI state → `ObservableValue` + `subscribe` (Tier 3)
- Need keyboard shortcuts → `ActionSpec` + `RoutedRuntimeSpec.action_bindings` (Tiers 1, 4)
- Need cross-feature shared state → `AppStateStore` + `StateSelector` (Tier 27)
- Need large dataset display → `SortFilterProxySource` + `VirtualizationCore` (Tiers 15, 29)
- Need background computation → `DataflowPipeline` + `CancellationToken` (Tier 26)
- Need workspace persistence across restarts → `WorkspacePersistenceManager` + `SnapshotMigrator` (Tiers 11, 32)
- Need discoverable shortcuts → `ShortcutOverlaySpec` in `RoutedRuntimeSpec` (Tier 1, Tier 9)
- Need multi-step user workflow → `CooperativeScheduler` + `WaitForSignal` (Tier 5)
- Need form validation → `SchemaFormRuntime` + `ValidationPolicy` (Tier 31)

---

### E: Architecture Templates

The following four templates serve as starting points for common gui_do application architectures. Each lists the key components and their roles; adapt to your specific requirements.

**Template 1: Small Single-Scene Application**

Best for: utilities, tools, simple viewers, embedded applications.

- 1 scene with 2–4 `Feature` subclasses
- `ObservableValue` state owned by each feature
- `ActionSpec` entries in config for all commands
- `RuntimeSceneSpec` with `bind_escape_to_exit=True` for simple exit
- No task panel; no window presenter; no routed runtime
- `HostApplicationConfig` with `title`, `size`, and a small set of `actions`
- Optional: `TelemetryConfig` enabled for development profiling

**Template 2: Multi-Window Workbench**

Best for: IDEs, design tools, data analysis dashboards, professional applications.

- 2+ scenes connected via `SceneBundleBindingSpec` and a scene menu strip
- `SceneTaskPanelSpec` for each scene's task panel strip
- `TaskPanelFocusToggleSpec` for every toggleable window
- `WindowPresenter` subclass per floating window
- `RoutedRuntimeSpec` with `ShortcutOverlaySpec` for discoverable shortcuts
- `FeatureWindowBundleBindingSpec` to bundle each feature + window + task panel toggle
- `ActiveTabUpdateRouter` for tabbed windows with multiple content panes
- `add_standard_scene_menu_strip` for scene navigation and window visibility menus

**Template 3: Data-Heavy Analysis Tool**

Best for: log browsers, database explorers, scientific visualization, report builders.

- `AsyncDataProvider` for remote or file-based data loading
- `SortFilterProxySource` wrapping the provider for sort/filter without data copies
- `VirtualizationCore` or `ListViewControl`/`DataGridControl` consuming the proxy source
- `DataflowPipeline` with `CancellationToken` for multi-stage background transforms (parse → rank → format)
- `ListDiffCalculator` for incremental UI updates when filter or sort changes
- `DirtyRegionTracker` for custom canvas visualizations that change partially per frame
- `TelemetryConfig` enabled; telemetry baseline tests in the CI suite for frame-budget regression detection

**Template 4: Long-Running Workflow Application**

Best for: import/export tools, build systems, processing pipelines, guided configuration assistants.

- `CooperativeScheduler` coroutines for multi-step background work that yields control between steps
- `ObservableValue` progress exposed to a UI feature that drives a `ProgressBarControl`
- `WizardFlow` with `WizardStep` instances for multi-step guided user input
- `CommandHistory` with `CommandTransaction` for undo/redo of workflow stages
- `SnapshotMigrator` for versioned session state that survives application version upgrades
- `AsyncFormValidator` for server-side validation in input-heavy steps
- `ErrorBoundary` wrapping the output rendering for fault-tolerant result display

[Back to Table of Contents](#table-of-contents)

---

### F: Specifications and Option Reference

### F: Specifications and Option Reference

[Back to Table of Contents](#table-of-contents)

This appendix provides a concise field-by-field reference for every major specification type used in gui_do bootstrap and runtime wiring. Entries are grouped by family. Cross-references point to the chapter where each spec is used in context.

---

#### F.1 Bootstrap and Host Configuration Specs

**`HostApplicationConfig`** — Top-level runtime configuration passed to `build_host_application_config`. See [§8.1 Application Bootstrap](#81-application-bootstrap-and-host-configuration).

| Field | Purpose | Default/Notes |
|-------|---------|---------------|
| `title` | Window title bar text | Required |
| `size` | `(width, height)` tuple for the display surface | Required |
| `flags` | pygame display flags (`pygame.RESIZABLE`, etc.) | `0` |
| `target_fps` | Frame rate cap | `60` |
| `telemetry` | `TelemetryConfig` instance to enable telemetry | `None` (disabled) |
| `background_color` | Scene background RGBA fill | `(30, 30, 30, 255)` |
| `fonts` | Dict mapping short font names to file paths or font config dicts | `{}` |
| `icon_path` | Path to window icon surface | `None` |

**`TelemetryConfig`** — Nested inside `HostApplicationConfig`. See [§8.16 Telemetry](#816-telemetry-introspection-and-operational-hooks).

| Field | Purpose | Default |
|-------|---------|---------|
| `enabled` | Enable/disable the telemetry collector | `False` |
| `max_records` | Maximum number of `TelemetrySample` records to retain | Unbounded if `None` |

**`HostApplicationBindingSpec`** — Wiring spec passed to `bootstrap_host_application` alongside `HostApplicationConfig`. See [§8.1 Application Bootstrap](#81-application-bootstrap-and-host-configuration).

| Field | Purpose | Notes |
|-------|---------|-------|
| `feature_entries` | List of `FeatureSpec` instances | One per feature in the application |
| `actions` | List of `ActionSpec` instances | Declares the named action registry |
| `scene_bundle_entries` | List of `RuntimeSceneSpec` instances | One per scene |
| `font_role_entries` | List of `FontRoleBindingSpec` instances | Maps semantic roles to font configs |
| `cursor_entries` | List of `CursorBindingSpec` instances | Maps cursor shapes to interaction contexts |
| `static_accessibility_entries` | List of `StaticAccessibilitySpec` instances | Pre-declared accessibility nodes |

---

#### F.2 Feature and Scene Specs

**`FeatureSpec`** — Declares one feature in the application. See [§8.2 Feature Lifecycle](#82-feature-lifecycle-and-feature-types).

| Field | Purpose | Notes |
|-------|---------|-------|
| `attribute` | Name of the host attribute that receives the feature instance | Used as identifier in scene membership |
| `factory` | Callable that constructs the feature | Usually a class reference |
| `args`, `kwargs` | Optional arguments forwarded to `factory` | `()`, `{}` |

**`RuntimeSceneSpec`** — Declares one scene. See [§8.1 Bootstrap](#81-application-bootstrap-and-host-configuration) and [§8.9 Scene Presentation](#89-scene-window-and-task-panel-presentation-models).

| Field | Purpose | Default |
|-------|---------|---------|
| `name` | Unique scene identifier | Required |
| `feature_attributes` | List of host attribute names belonging to this scene | `[]` |
| `bind_escape_to_exit` | Whether Escape key exits the application in this scene | `False` |
| `background_color` | Per-scene background color override | Inherits from host config |
| `command_palette` | `SceneCommandPaletteSpec` for this scene's command palette | `None` |

**`SceneBundleBindingSpec`** — Groups a scene with its associated presentation elements. See [§8.9 Scene Presentation](#89-scene-window-and-task-panel-presentation-models).

| Field | Purpose | Notes |
|-------|---------|-------|
| `scene_spec` | `RuntimeSceneSpec` for this scene | Required |
| `task_panel_spec` | Optional `SceneTaskPanelSpec` | `None` |
| `window_specs` | List of `WindowSpec` or `AnchoredWindowSpec` | `[]` |

**`SceneCommandPaletteSpec`** — Activates the command palette in a scene. See [§8.8 Overlays](#88-overlays-dialogs-notifications-and-command-surfaces).

| Field | Purpose | Default |
|-------|---------|---------|
| `toggle_action_name` | Action that opens/closes the palette | Required |
| `include_scene_entries` | Auto-include scene-navigation commands | `True` |
| `include_window_entries` | Auto-include window-toggle commands | `True` |
| `custom_entries_provider` | Callable returning context-sensitive `CommandEntry` list | `None` |

---

#### F.3 Action and Input Specs

**`ActionSpec`** — Declares a named action in the registry. See [§8.3 Events, Actions, Input Mapping, and Routing](#83-events-actions-input-mapping-and-routing).

| Field | Purpose | Notes |
|-------|---------|-------|
| `name` | Unique action identifier (e.g., `"app.exit"`) | Required |
| `label` | Human-readable label for shortcut overlays and menus | Required |
| `description` | Optional longer description | `""` |
| `icon` | Optional icon key for menu display | `None` |

**`ActionHotkeySpec`** — Declares a static hotkey binding for an action.

| Field | Purpose | Notes |
|-------|---------|-------|
| `action_name` | Name of the action to bind | Required |
| `key_chord` | Key chord string (e.g., `"ctrl+s"`, `"f9"`) | Required |
| `scope` | `"scene"` or `"window"` scope | `"scene"` |

**`ActionBindingSpec`** — A binding entry inside `RoutedRuntimeSpec.action_bindings`. See [§8.3 Events](#83-events-actions-input-mapping-and-routing).

Expressed as a dict `{action_name: key_chord_string}` in `RoutedRuntimeSpec`.

---

#### F.4 Routed Runtime Specs

**`RoutedRuntimeSpec`** — The declarative bundle for a `RoutedFeature`. See [§8.2 Feature Lifecycle](#82-feature-lifecycle-and-feature-types) and [§8.3 Events](#83-events-actions-input-mapping-and-routing).

| Field | Purpose | Default |
|-------|---------|---------|
| `action_bindings` | Dict mapping action names to key chord strings | `{}` |
| `shortcut_overlay` | `ShortcutOverlaySpec` for this feature's shortcut help | `None` |
| `focus_toggles` | List of `TaskPanelFocusToggleSpec` entries | `[]` |
| `topic_subscriptions` | List of topic names this feature subscribes to via message bus | `[]` |
| `window_toggle_specs` | List of `WindowToggleBindingSpec` entries | `[]` |

**`RoutedFeatureLifecycleSpec`** — Wraps a `RoutedRuntimeSpec` for lifecycle management.

| Field | Purpose | Notes |
|-------|---------|-------|
| `runtime_spec` | The `RoutedRuntimeSpec` to manage | Required |

**`ShortcutOverlaySpec`** — Configures the shortcut help overlay. See [§8.8 Overlays](#88-overlays-dialogs-notifications-and-command-surfaces).

| Field | Purpose | Default |
|-------|---------|---------|
| `toggle_action_name` | Action that opens/closes the overlay | Required |
| `sections` | List of `ShortcutSection` instances | `[]` |
| `exclude_section_titles` | Section titles to omit from auto-populated sections | `[]` |
| `manual_shortcut_lines` | Additional plain-text lines appended after sections | `[]` |

**`ShortcutSection`** — One named group of shortcuts in the overlay.

| Field | Purpose |
|-------|---------|
| `title` | Section header text |
| `entries` | List of `ShortcutEntry` instances |

**`ShortcutEntry`** — One row in a `ShortcutSection`.

| Field | Purpose |
|-------|---------|
| `action` | Action name (resolved to key chord via registry) |
| `label` | Override label; falls back to `ActionSpec.label` if `None` |

---

#### F.5 Window and Presentation Specs

**`WindowSpec`** — Declares a feature window by reference. See [§8.9 Scene Presentation](#89-scene-window-and-task-panel-presentation-models).

| Field | Purpose | Notes |
|-------|---------|-------|
| `control_id` | Unique `WindowControl` identifier | Required |
| `feature_attribute` | Host attribute name of the owning feature | Required |
| `toggle_action_name` | Action that shows/hides this window | Optional |
| `task_panel_button` | `TaskPanelButtonSpec` for this window's toggle button | `None` |
| `accessibility_label` | Accessibility name for the window | `None` |

**`AnchoredWindowSpec`** — Declares an anchored floating window with position and chrome. See [§8.9 Scene Presentation](#89-scene-window-and-task-panel-presentation-models).

| Field | Purpose | Default |
|-------|---------|---------|
| `control_id` | Unique `WindowControl` identifier | Required |
| `title` | Title bar text | Required |
| `anchor` | Anchor position string (`"top_left"`, `"top_right"`, `"center"`, etc.) | `"top_left"` |
| `size` | `(width, height)` tuple | Required |
| `resizable` | Whether the user can resize the window | `False` |
| `show_chrome` | Whether to render the title bar and border | `True` |
| `initial_visible` | Initial visibility state | `True` |

**`FeatureWindowBundleBindingSpec`** — Bundles a feature, its window, toggle action, and task panel button. See [§8.9 Scene Presentation](#89-scene-window-and-task-panel-presentation-models).

| Field | Purpose | Notes |
|-------|---------|-------|
| `feature_spec` | `FeatureSpec` for the owning feature | Required |
| `window_spec` | `WindowSpec` or `AnchoredWindowSpec` | Required |
| `toggle_action` | `ActionSpec` for the window toggle | Optional |
| `task_panel_button` | `TaskPanelButtonSpec` | Optional |

**`TabbedPresenterSpec`** — Configures a tabbed window layout. See [§8.9 Scene Presentation](#89-scene-window-and-task-panel-presentation-models).

| Field | Purpose | Notes |
|-------|---------|-------|
| `tabs` | List of `TabBuilderSpec` instances | Required |
| `initial_tab_index` | Which tab is selected on open | `0` |
| `tab_bar_height` | Height in pixels of the tab strip | `32` |

**`TabBuilderSpec`** — One tab in a `TabbedPresenterSpec`.

| Field | Purpose | Notes |
|-------|---------|-------|
| `label` | Tab strip label text | Required |
| `factory` | Callable `(host, parent_panel) → None` that builds the tab's controls | Required |
| `feature_attribute` | Host attribute for `ActiveTabUpdateRouter` routing | Optional |

---

#### F.6 Task Panel Specs

**`SceneTaskPanelSpec`** — Configures the task panel strip. See [§8.9 Scene Presentation](#89-scene-window-and-task-panel-presentation-models).

| Field | Purpose | Default |
|-------|---------|---------|
| `height` | Height in pixels | `48` |
| `position` | `"bottom"` or `"top"` | `"bottom"` |
| `background_color` | Fill color | Theme surface color |
| `padding` | Horizontal padding inside the strip | `8` |
| `gap` | Gap between items | `4` |

**`TaskPanelButtonSpec`** — One button in the task panel strip.

| Field | Purpose | Notes |
|-------|---------|-------|
| `label` | Button text or icon label | Required |
| `action_name` | Action to fire on click | Required |
| `icon` | Optional icon key | `None` |
| `tooltip` | Tooltip text on hover | `None` |

**`TaskPanelFocusToggleSpec`** — Wires focus ring exclusion to window visibility. See [§8.7 Focus](#87-focus-and-accessibility) and [§8.9 Scene Presentation](#89-scene-window-and-task-panel-presentation-models).

| Field | Purpose | Notes |
|-------|---------|-------|
| `window_id` | `control_id` of the `WindowControl` to track | Required |
| `toggle_action_name` | Action that triggers the toggle | Optional; inferred from `WindowSpec` if set |

**`TaskPanelWindowToggleGroupSpec`** — Auto-creates toggle buttons for all registered windows.

| Field | Purpose | Default |
|-------|---------|---------|
| `start_slot_index` | Position index in the task panel to begin placing buttons | `0` |
| `include_window_ids` | Explicit list of window IDs to include; `None` means all | `None` |
| `exclude_window_ids` | Window IDs to exclude from the group | `[]` |

**`TaskPanelSceneNavButtonSpec`** — A scene-navigation button in the task panel.

| Field | Purpose | Notes |
|-------|---------|-------|
| `target_scene_name` | Scene to navigate to on click | Required |
| `label` | Button label | Required |
| `icon` | Optional icon key | `None` |

---

#### F.7 Accessibility Specs

**`StaticAccessibilitySpec`** — Declares a named accessibility node at build time. See [§8.7 Focus and Accessibility](#87-focus-and-accessibility).

| Field | Purpose | Notes |
|-------|---------|-------|
| `control_id` | ID of the control this node describes | Required |
| `role` | `AccessibilityRole` enum value | Required |
| `name` | Human-readable name for the node | Required |
| `description` | Optional longer description | `""` |
| `live` | `LivePoliteness` for live-region updates | `LivePoliteness.OFF` |

**`AccessibilitySequenceSpec`** — Declares an explicit Tab order for a scene.

| Field | Purpose | Notes |
|-------|---------|-------|
| `scene_name` | Scene this order applies to | Required |
| `ordered_control_ids` | Ordered list of control IDs defining the Tab sequence | Required |

---

#### F.8 Font and Theme Specs

**`FontRoleBindingSpec`** — Maps a semantic font role to a font configuration. See [§8.12 Theme](#812-theme-styling-and-visual-systems).

| Field | Purpose | Notes |
|-------|---------|-------|
| `role_name` | Semantic role identifier (e.g., `"body"`, `"heading"`) | Required |
| `font_name` | Short font name from `HostApplicationConfig.fonts` | Required |
| `size` | Font size in points | Required |
| `bold` | Bold weight | `False` |
| `italic` | Italic style | `False` |

**`CursorSpec`** — Declares a cursor shape for a named cursor role.

| Field | Purpose | Notes |
|-------|---------|-------|
| `role_name` | Cursor role identifier | Required |
| `shape` | `CursorShape` enum value | Required |

**`CursorBindingSpec`** — Binds a cursor spec to an interaction context.

| Field | Purpose | Notes |
|-------|---------|-------|
| `cursor_spec` | `CursorSpec` to apply | Required |
| `interaction_context` | Context name where this cursor applies | Required |

---

#### F.9 Persistence and Migration Specs

**`SettingDescriptor`** — Declares one typed setting. See [§8.11 Persistence](#811-persistence-and-workspacesession-state).

| Field | Purpose | Default |
|-------|---------|---------|
| `key` | Unique setting key (e.g., `"ui.show_grid"`) | Required |
| `type` | Python type (`bool`, `int`, `float`, `str`) | Required |
| `default` | Default value when the key is not found in a restored workspace | Required |
| `label` | Human-readable label for property inspector display | `""` |
| `validator` | Optional callable `(value) → bool` for validation | `None` |

**`MigrationStep`** — One schema version transition step. See [§8.11 Persistence](#811-persistence-and-workspacesession-state) and [Migration chapter](#migration-versioning-and-deprecation-notes).

| Field | Purpose | Notes |
|-------|---------|-------|
| `from_version` | Source `SchemaVersion` | Required |
| `to_version` | Target `SchemaVersion` | Required |
| `migrate` | Callable `(data: dict) → dict` that transforms the snapshot data | Required |

---

#### F.10 Form and Validation Specs

**`SchemaField`** — One field in a `FormSchema`. See [§8.13 Text, Input, Forms](#813-text-input-forms-and-validation-systems).

| Field | Purpose | Default |
|-------|---------|---------|
| `key` | Field identifier | Required |
| `type` | Python type for the field value | Required |
| `default` | Initial value | Required |
| `label` | Human-readable field label | `""` |
| `validators` | List of `Validator` instances | `[]` |
| `visible_when` | Optional callable `(form_values: dict) → bool` for visibility dependency | `None` |

**`ValidationPolicy`** — Enum controlling when validation runs. See [§8.13 Text, Input, Forms](#813-text-input-forms-and-validation-systems).

| Value | Trigger |
|-------|---------|
| `ON_CHANGE` | Validates on every value change |
| `ON_BLUR` | Validates when a field loses focus |
| `ON_SUBMIT` | Validates only when the form is explicitly submitted |
| `MANUAL` | Never validates automatically; caller invokes `validate_all()` |

**`FieldGraphSchema`** — A DAG of fields with visibility dependencies, built from `FormSchema`. Use `FieldGraphSchema.from_form_schema(schema)` — do not construct directly.

---

#### F.11 Overlay and Dialog Specs

**`NotificationSpec`** — Declares a notification entry. See [§8.8 Overlays](#88-overlays-dialogs-notifications-and-command-surfaces).

| Field | Purpose | Notes |
|-------|---------|-------|
| `title` | Short notification title | Required |
| `body` | Full notification body text | `""` |
| `severity` | `ToastSeverity` value | `ToastSeverity.INFO` |

**`FileDialogOptions`** — Configuration for a file open/save dialog. See [§8.8 Overlays](#88-overlays-dialogs-notifications-and-command-surfaces).

| Field | Purpose | Default |
|-------|---------|---------|
| `title` | Dialog title bar text | `"Open File"` |
| `initial_dir` | Initial directory path | Current working directory |
| `filters` | List of `(label, pattern)` filter tuples (e.g., `("Python", "*.py")`) | `[]` |
| `mode` | `"open"` or `"save"` | `"open"` |
| `allow_multiple` | Allow selecting multiple files | `False` |

See [Appendix F: Specifications and Option Reference](#f-specifications-and-option-reference) — you are here.
