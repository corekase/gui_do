---
name: Manual.p2
description: Expand the Conceptual Foundations chapter with comprehensive theory prose
---

# Manual Step 2 — Conceptual Foundations Chapter

## Scope

Replace the `## Conceptual Foundations (Theory)` placeholder in `MANUAL.md` with the
complete, verbose chapter. This chapter is the theoretical backbone of the manual.

## Inventory (Required Before Writing)

1. Read `MANUAL.md`: find the section from `## Conceptual Foundations (Theory)` to the
   next `## ` heading at the same level. That is the range you will replace.
2. Read `gui_do/__init__.py` **Tier 1 and Tier 3** sections to discover current spec and
   observable type names for accurate examples in this chapter.
3. Read `gui_do/features/data_driven_runtime.py` top docstring/comments to verify the spec
   pipeline description and any new builder patterns.
4. Read `gui_do/features/feature_lifecycle.py` top portion to verify current lifecycle phase
   names and HOST_REQUIREMENTS protocol — do not assume names from prior runs.
5. Skim `demo_features/main_scene/main_demo_feature.py` for a concrete lifecycle example.

Use only names found in the actual files. Do not copy names from prior MANUAL.md content
without verifying they still exist in `gui_do/__init__.py`.

## Three Required Subsections

Write these three subsections in order, each with its own `[Back to Table of Contents]` link.

---

### Subsection 1: Data-Driven Design

**Core idea:** In gui_do, application structure is expressed as configuration data — specs,
bindings, and descriptors — rather than as sequences of imperative calls. The runtime receives
that data and performs all wiring automatically.

Write comprehensive prose covering all of these points (cover each thoroughly; do not reduce
to a bullet list):

- **What it means**: Separate description of what to do from the code that does it. A developer
  describes a scene, its features, actions, and windows through spec objects; the framework
  interprets those specs and builds the live application.

- **The spec pipeline**: `HostApplicationBindingSpec` and `build_host_application_config` form the
  entry point. The builder performs a single deterministic pass resolving cross-references,
  validating requirements, and producing a fully wired `HostApplicationConfig`. Then
  `bootstrap_host_application` executes it. This two-step (build config → run) design separates
  description from execution, making both independently testable.

- **Imperative wiring contrast**: In an imperative approach, adding a keyboard shortcut means
  finding input-handling code, inserting a branch, wiring a callback, ensuring cleanup on scene
  exit. In the data-driven approach, add one `ActionSpec`. The framework registers it with the
  action registry, routes the key through the input map, and tears it down when the scene exits.

- **Reorganization without bootstrap impact**: Internal reorganization — moving a class, splitting a
  feature into logic + presentation companions — never requires changes to bootstrap code.
  Bootstrap consumes public class references and spec values, not file paths. As long as each
  feature package's `__init__.py` exports the same public names, the bootstrap is completely
  insulated from structural changes inside the package.

- **Testability**: Specs can be constructed and validated in unit tests with no running display.
  Feature instances can be built with mock hosts. The entire app config can be assembled and
  inspected without starting the event loop.

- **Specs as serialization boundary**: Specs are pure data and could in principle be stored,
  loaded, or generated programmatically. Named fields make specs self-documenting, composable,
  and forward-compatible — adding new optional fields in future versions does not break existing
  callers in the way positional APIs would.

- **Where the boundary is**: The wiring (scene graph, action registry, input routing, feature
  orchestration) is data-driven. The runtime behavior of individual features (what they do in
  `on_update`, `handle_event`, `draw`) is imperative Python inside feature methods. Describe
  structure declaratively; implement behavior imperatively.

---

### Subsection 2: Reactive Data and Observable State

**Core idea:** A reactive value notifies all subscribers automatically when it changes, without
the producer needing to know who the consumers are.

Write comprehensive prose covering all of these points:

- **What reactive data means**: In a traditional imperative GUI, updating a value means calling
  every UI element manually. In a reactive model, the value holds subscribers and notifies them
  on change. The UI element subscribes once; updates flow automatically.

- **The observable primitives**: `ObservableValue` wraps a single value; `.subscribe(callback)`
  notifies on change. `ObservableList` and `ObservableDict` provide the same semantics for
  mutable collections, with `CollectionChange` events identifying what changed.

- **`reactive_batch` and `is_batching`**: Multiple observable mutations can be batched so
  subscribers fire once after all changes rather than once per change. Describe when to use this.

- **`ComputedValue`**: A derived observable that recomputes from one or more source observables.
  Describe how it differs from manually subscribing and writing to a second observable.

- **Subscription lifecycle**: Subscribe in `bind_runtime` or `on_create`; dispose in
  `shutdown_runtime` or equivalent teardown. Failing to unsubscribe causes memory leaks and
  callbacks on dead objects.

- **Control binding model**: Controls accept either a plain value or an observable. When bound to
  an observable, the control registers an internal subscription and refreshes its display on
  change. Feature code only changes the observable; the control updates itself.

- **Cross-feature reactive state**: One feature owns an `ObservableValue` and exposes it; others
  subscribe. The producing feature never knows who observes. Set this up in `bind_runtime` when
  sibling features are available.

- **Anti-patterns**: polling in `on_update` (CPU waste + latency); subscribing in `build` before
  the runtime is ready; forgetting to unsubscribe (memory leaks and phantom callbacks); sharing
  mutable plain Python objects across features instead of observables (breaks reactivity).

---

### Subsection 3: Feature Composition and Lifecycles

**Core idea:** A Feature is the primary unit of application behavior — a self-contained object
that declares its resource requirements, builds its UI, handles events, and tears itself down.

Write comprehensive prose covering all of these points:

- **What a Feature is**: Self-contained; declares what resources it needs via `HOST_REQUIREMENTS`;
  builds its own UI elements; registers its own event handlers; tears itself down cleanly.
  Features are composable: an application is a collection of features that coexist in scenes.

- **Feature types and when to use each**:
  - `DirectFeature`: Renders directly to the screen surface every frame. Use for background
    elements (animated backdrops, full-screen effects) that do not need the control tree. Lowest
    overhead feature type.
  - `Feature`: Standard feature. Builds controls in the scene's control tree during `build`.
    Participates in focus, hit-testing, and event routing. Use for any interactive UI.
  - `LogicFeature`: Has no UI of its own. Exists for domain logic, shared state, background
    computation, and publishing results. Use when behavior should be tested in isolation from
    presentation.
  - `RoutedFeature`: A Feature that also participates in action routing infrastructure. Can define
    route targets that receive named messages dispatched to specific handler methods. Use when a
    feature must respond to framework-level actions or coordinate with the action registry.

- **Lifecycle phases in depth**:
  - `build(host)`: Called once during scene construction. Create controls, add them to the scene
    tree, build static structure. Controls created here exist for the scene's lifetime.
  - `bind_runtime(host)`: Called after all features in the scene have completed `build`. Subscribe
    to observables, bind controls to data, register callbacks, wire cross-feature interactions.
  - `handle_event(host, event)`: Called for every routed `GuiEvent`. Return `True` to consume;
    return `False`/`None` to pass on.
  - `on_update(host, dt_seconds)`: Called every frame. Use for animations, timers, per-frame
    updates. Keep fast; avoid expensive computation.
  - `draw(host, screen)`: Called every frame after `on_update`. Use for custom drawing that
    bypasses the control tree.

- **`HOST_REQUIREMENTS` protocol**: Declares what host attributes each lifecycle method requires.
  The framework validates these at startup and provides clear error messages for missing bindings.
  A feature says "I need `app`, `screen_rect`, and `scene_presentation` in `build`"; the
  framework ensures those are present before calling the method.

- **Feature messaging**: Features communicate through `FeatureMessage` publishing — not direct
  references to each other. A feature publishes a message by name with optional payload; the
  framework delivers it to any feature registered for that name. This prevents implementation
  coupling between features.

- **Scene assignment and transitions**: Each feature belongs to one scene via `scene_name`. The
  framework activates/deactivates features as scenes transition — calling teardown on departing
  features and build/bind on arriving ones. Features from the previous scene do not receive
  events or updates after transition.

- **Folder/package composition convention**: Each feature package lives in its own folder. The
  `__init__.py` is the sole public surface, exporting the Feature class and public types. Internal
  files are separated by concern: `*_feature.py`, `*_presenter.py`, `*_specs.py`,
  `*_logic_feature.py`, standalone data types. Bootstrap code never imports from internal
  submodules — only from the package surface.

- **Composition patterns**: Logic + presentation split (`LogicFeature` runs computations and
  publishes results via observables; `RoutedFeature` subscribes and drives UI); Presenter pattern
  (`WindowPresenter` subclass handles window layout; Feature handles lifecycle); Background feature
  pattern (`LogicFeature` drives `CooperativeScheduler` coroutines for long-running work,
  publishing progress to observables the UI feature displays).

---

## Replace Target

Use `replace_string_in_file` to replace from the line containing:
```
## Conceptual Foundations (Theory)
```
through to (but not including) the line containing:
```
## Quickstart Path (Practice)
```

Include the heading `## Conceptual Foundations (Theory)` in your replacement output.
