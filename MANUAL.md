# gui_do — Developer Manual

`gui_do` is a data-driven, reactive GUI framework built on top of pygame. This manual is the
primary learning and reference source for developers who want to build applications with
`gui_do` — from a first hello-world scene through advanced multi-system integrations. It is
aimed first at developers new to the framework who need to build a complete mental model, and
second at experienced users who need a precise API and system reference. Every major concept is
explained with enough depth that a developer reading only that section can come away with a
genuine working understanding of purpose, design rationale, and practical application.

---

## Table of Contents

- [1. How to Use This Manual](#how-to-use-this-manual)
  - [Reading Paths](#reading-paths)
  - [Tri-Lens Markers](#tri-lens-markers)
  - [Contract Alignment](#contract-alignment)
  - [Known Non-Goals](#known-non-goals)
- [2. Conceptual Foundations](#conceptual-foundations)
  - [Data-Driven Design](#data-driven-design)
  - [Reactive Data and Observable State](#reactive-data-and-observable-state)
  - [Feature Composition and Lifecycles](#feature-composition-and-lifecycles)
- [3. Quickstart Path](#quickstart-path)
- [4. Architecture and Runtime Model](#architecture-and-runtime-model)
- [5. Core Workflow: Build, Bind, Route, Update, Draw](#core-workflow-build-bind-route-update-draw)
- [6. Main Systems Reference](#main-systems-reference)
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
- [7. Integration Patterns and Composition Recipes](#integration-patterns-and-composition-recipes)
- [8. End-to-End Reference Application](#end-to-end-reference-application)
- [9. Testing, Diagnostics, and Reliability](#testing-diagnostics-and-reliability)
  - [Maintainer Diff Checklist](#maintainer-diff-checklist)
- [10. Performance and Scaling Guidance](#performance-and-scaling-guidance)
- [11. Migration, Versioning, and Deprecation Notes](#migration-versioning-and-deprecation-notes)
- [12. FAQ and Troubleshooting](#faq-and-troubleshooting)
- [Appendix A: Glossary](#appendix-a-glossary)
- [Appendix B: Lifecycle and Event Sequence](#appendix-b-lifecycle-and-event-sequence)
- [Appendix C: System Dependency Map](#appendix-c-system-dependency-map)
- [Appendix D: API Quick Index](#appendix-d-api-quick-index)
  - [D.1 Tier Matrix](#d1-tier-matrix)
  - [D.2 Selection Heuristics](#d2-selection-heuristics)
- [Appendix E: Architecture Templates](#appendix-e-architecture-templates)
- [Appendix F: Specifications and Option Reference](#appendix-f-specifications-and-option-reference)

---

## How to Use This Manual

[Back to Table of Contents](#table-of-contents)

This manual is organized to serve three distinct use modes: learning, building, and maintaining.
Understanding which mode you are in will help you navigate directly to what you need without
reading the entire document linearly.

**Learn mode** is for developers who are new to `gui_do` or who want to build a complete
mental model of how the framework operates. Begin with [Conceptual Foundations](#conceptual-foundations),
which explains the three core ideas that underpin every system in the framework. Then read the
[Quickstart Path](#quickstart-path) to see those concepts applied in a working skeleton. After
that, move through the [Architecture and Runtime Model](#architecture-and-runtime-model) and the
[Core Workflow](#core-workflow-build-bind-route-update-draw) chapters to understand the runtime's
operating logic. You can then read system chapters selectively in any order, as each is
self-contained.

**Build mode** is for developers actively implementing features. Use the [Quickstart Path](#quickstart-path)
as the starting template, consult the system chapters in [Main Systems Reference](#main-systems-reference)
for the APIs relevant to your task, and check [Integration Patterns](#integration-patterns-and-composition-recipes)
for multi-system composition recipes. The appendices — particularly [Appendix D (API Quick Index)](#appendix-d-api-quick-index)
and [Appendix F (Specifications and Option Reference)](#appendix-f-specifications-and-option-reference)
— are the fastest reference lookup paths.

**Maintain mode** is for developers updating existing applications or regenerating this manual
after codebase changes. Read the [Maintainer Diff Checklist](#maintainer-diff-checklist) first.
Consult [Migration, Versioning, and Deprecation Notes](#migration-versioning-and-deprecation-notes)
for guidance on handling API evolution. The [System Dependency Map](#appendix-c-system-dependency-map)
identifies which chapters are affected by changes to a given tier.

### Reading Paths

**Beginner path** (new to `gui_do`):
1. Conceptual Foundations — all three subsections
2. Quickstart Path
3. Architecture and Runtime Model
4. Core Workflow
5. System chapters 8.1 → 8.4 (foundation systems)
6. System chapters 8.5 → 8.8 (UI systems)
7. Integration Patterns — at least the first recipe

**Intermediate path** (comfortable with the basics, building non-trivial apps):
1. Core Workflow (refresh)
2. System chapters for the specific systems you are using
3. Integration Patterns — full chapter
4. End-to-End Reference Application
5. Testing, Diagnostics, and Reliability

**Maintainer path** (responsible for codebase evolution):
1. Maintainer Diff Checklist (runs at the start of every session)
2. Migration, Versioning, and Deprecation Notes
3. System Dependency Map (Appendix C)
4. Tier Matrix (Appendix D.1)
5. Relevant system chapters for changed areas

### Tri-Lens Markers

Throughout this manual, sections and examples are tagged with one of three lenses to indicate
the type of guidance they provide:

- **[CONCEPT]** — Explains why something is designed the way it is and what mental model to use.
- **[PRACTICE]** — Provides concrete usage instructions, patterns, or code examples.
- **[CONTRACT]** — States normative behavior that the framework guarantees and tests enforce.
  These statements are backed by the contract test suite described in the Testing chapter.

When you encounter a `[CONTRACT]` marker, the corresponding behavior is verified by automated
tests. If that behavior ever changes, both the contract doc under `docs/` and the relevant test
must be updated. See [Contract Alignment](#contract-alignment) for the enforcement model.

### Contract Alignment

`gui_do` maintains a set of normative contract documents under `docs/`. These documents specify
the boundaries, stability policies, and operational guarantees that the runtime upholds. This
manual is written to be consistent with those contracts, but in case of any discrepancy, the
contracts take precedence because they are the machine-verifiable ground truth.

The key contract documents and their roles:

| Document | Role |
|---|---|
| `docs/public_api_spec.md` | Tier groupings, stability policy, import contract |
| `docs/runtime_operating_contracts.md` | Scheduler budgets, restore report fields, cross-system guarantees |
| `docs/architecture_boundary_spec.md` | Rules separating library code from demo code |
| `docs/library_demo_separation_contract.md` | Dependency direction and feature isolation requirements |
| `docs/package_contracts.md` | Per-package public surface rules |
| `docs/event_system_spec.md` | Event routing and dispatch model |

The contract test suite enforces these documents automatically. High-priority tests include:

```bash
python -m pytest -q \
  tests/test_public_api_exports.py \
  tests/test_public_api_docs_contracts.py \
  tests/test_runtime_operating_contracts.py \
  tests/test_boundary_contracts.py \
  tests/test_gui_application_workspace_contracts.py
```

### Known Non-Goals

`gui_do` deliberately does not aim to:

- **Replace a native widget toolkit.** The framework targets pygame-hosted applications — games,
  tools, and creative software — not desktop productivity apps that expect OS-native controls and
  accessibility infrastructure.
- **Provide a layout engine that matches CSS.** The layout systems are purpose-built for
  pygame surfaces and rects. They do not implement the CSS box model.
- **Abstract away pygame.** Developers are expected to understand pygame's surface, event, and
  display APIs. `gui_do` builds on top of them; it does not hide them.
- **Support multithreaded rendering.** The rendering path is single-threaded. Background threads
  are used only for data computation; all UI mutations must occur on the main thread.
- **Be a game engine.** While `gui_do` is built on pygame and includes graphics utilities, it is
  a GUI framework first. Game-specific systems (physics, collision, etc.) are out of scope.
- **Provide backwards-compatible public APIs indefinitely.** The framework uses a tier-based
  stability model. Lower tiers (Tier 1) have the highest stability; higher tiers may evolve more
  freely. See the Tier Matrix in Appendix D.1.

---

## Conceptual Foundations

[Back to Table of Contents](#table-of-contents)

`gui_do` rests on three interlocking ideas that permeate every system in the framework. These
ideas are not incidental — they are the design principles that explain why the framework is
organized the way it is, why certain patterns are recommended, and why certain approaches that
feel natural from imperative GUI experience will produce friction here. Understanding these
three ideas deeply is the most valuable investment you can make before writing your first
feature.

### Data-Driven Design

[Back to Table of Contents](#table-of-contents)

**[CONCEPT]**

Data-driven design is the principle that application structure — the set of scenes, features,
actions, windows, keyboard shortcuts, accessibility annotations, cursors, and font roles that
make up a running application — should be expressed as data that the framework interprets,
rather than as a sequence of imperative function calls that the developer orchestrates. The
developer describes what the application should be; the framework figures out how to build it.

In concrete terms, this means that every structural decision in a `gui_do` application is
captured in spec objects. There are specs for features (`FeatureSpec`), for windows
(`WindowSpec`), for runtime scenes (`RuntimeSceneSpec`), for actions (`ActionSpec`), for
shortcuts (`ActionHotkeySpec`), for keyboard bindings (`ControlKeyBindingSpec`), for task
panel layout (`SceneTaskPanelSpec`, `TaskPanelButtonSpec`, `TaskPanelWindowToggleGroupSpec`),
for the command palette (`SceneCommandPaletteSpec`), for accessibility annotations
(`StaticAccessibilitySpec`, `AccessibilitySequenceSpec`), for cursors (`CursorSpec`), for font
roles (`FontRoleBindingSpec`), and for higher-level bundles that group these together
(`RoutedRuntimeSpec`, `FeatureWindowBundleBindingSpec`, `SceneBundleBindingSpec`,
`HostApplicationBindingSpec`). These specs are plain Python dataclass instances — pure data
with no behavior of their own.

The spec pipeline works in two phases. In the first phase, the developer populates a
`HostApplicationBindingSpec` — a single top-level object that collects all of the application's
structural declarations — and passes it to `build_host_application_config`. The builder performs
a single deterministic pass over all the specs: it resolves cross-references between features
and windows, validates that required attributes are present and consistent, derives implied
registrations (such as generating action registry entries from `ActionSpec` lists and window
toggle controls from `WindowSpec` lists), and produces a fully wired `HostApplicationConfig`
object. The builder is a pure function — same input always produces the same output. In the
second phase, the developer passes the `HostApplicationConfig` to `bootstrap_host_application`,
which executes the application by creating the runtime systems, initializing the display,
running the feature lifecycle, and starting the event loop.

This two-step separation — build config, then run — is deliberate. It means the entire
application structure can be built and inspected in a unit test with no display, no event loop,
and no pygame initialization. Tests can verify that the right features were registered, that
the correct action names were wired, that the correct scenes exist, and that accessibility
sequences were applied — all without running the application at all. This is a decisive
testability advantage over imperative wiring.

To understand why data-driven design matters in practice, compare adding a keyboard shortcut
in each approach. In a traditional imperative approach, a developer would find the
input-handling code in the scene manager or the event loop, add a new `elif` branch for the
key constant, write a callback or dispatch call, and add cleanup logic to the scene exit
handler to avoid leaking the binding across scene transitions. Each step is a mutation to an
existing procedure, and the correctness depends on knowing exactly where each hook lives and
in what order things run. In the data-driven approach, the developer adds one `ActionSpec` to
the binding spec with the desired action id, label, key, and kind. The builder picks it up,
registers it with the `ActionManager` via `ActionRegistry`, routes the key through `InputMap`,
and generates the teardown automatically as part of the scene transition lifecycle. The
developer never touches the router or the event loop.

The same principle applies at a larger scale when internal code is reorganized. Moving a class
from one submodule to another, extracting a presenter into its own file, splitting a monolithic
feature into a logic companion and a presentation companion — none of these changes require
touching bootstrap code. The bootstrap only cares about class references and spec values, not
file paths or module layouts. As long as the feature package's `__init__.py` continues to
export the same public names (the Feature class, any public spec constants), the bootstrap is
completely insulated from the restructuring. This is the practical meaning of the spec being
the public surface: the spec is what the bootstrap imports, and the spec is the stable
interface. Everything behind the spec's class references can change freely.

Specs are also inherently forward-compatible. A `HostApplicationBindingSpec` with named fields
can accept new optional fields in a future framework version without requiring existing callers
to change. A purely positional API cannot offer this stability without version-specific
compatibility shims. The named-field design of the spec objects is a deliberate choice to
protect the developer's bootstrap code across framework evolution.

It is important to be precise about where the data-driven boundary sits. The framework uses
specs to describe structure: which features exist in which scenes, which actions are registered,
which windows are visible by default, how the task panel is organized. It does not use specs to
describe behavior. What a feature does in `build`, `bind_runtime`, `handle_event`, `on_update`,
and `draw` is imperative Python inside the feature's methods. The philosophy is: describe
structure declaratively, implement behavior imperatively. This boundary is not a limitation —
it is what makes both halves tractable. Declarative structure is easy to validate, test, and
generate. Imperative behavior is where Python's full expressiveness is needed and appropriate.

**[PRACTICE]**

The minimal data-driven bootstrap looks like this:

```python
from gui_do import (
    bootstrap_host_application,
    build_host_application_config,
    HostApplicationBindingSpec,
    FeatureSpec,
)
from my_app.my_feature import MyFeature

spec = HostApplicationBindingSpec(
    title="My App",
    features=[
        FeatureSpec(attr_name="my_feature", factory=MyFeature),
    ],
)
config = build_host_application_config(spec)
bootstrap_host_application(config)
```

All structural wiring — action registration, scene setup, window layout, accessibility — is
expressed through the spec, not through code. The only imperative code is inside `MyFeature`.

---

### Reactive Data and Observable State

[Back to Table of Contents](#table-of-contents)

**[CONCEPT]**

A reactive value is a value that knows how to notify interested parties when it changes. In a
non-reactive model, updating a value is a write to memory that produces no side effects. Any
code that needs to reflect the new value must poll for it, or the producer must know every
consumer and call them explicitly after the write. Both approaches break down as the application
grows: polling wastes CPU and introduces display latency, and explicit notification coupling
makes the codebase brittle and hard to extend because every new consumer requires a code change
in the producer.

The reactive model inverts this. A reactive value holds a list of subscribers — callbacks that
want to be notified on change. A producer writes to the value and the value notifies all
subscribers automatically. Neither the producer nor the subscribers know about each other.
The producer only knows the value; the subscriber only knows the value. This is the pattern
that allows a feature's domain state to drive UI controls, other features, and diagnostic
systems simultaneously, without any of them being coupled to each other.

`gui_do` provides three core observable primitives. `ObservableValue` wraps a single value of
any type. Calling `.set(new_value)` updates the value and fires all registered callbacks with
the new value. Calling `.subscribe(callback)` returns a subscription handle; calling
`.unsubscribe(handle)` (or calling the handle directly) removes the subscription. The
`.get()` method reads the current value without triggering notifications.
`ObservableList` provides the same semantics for a mutable list. Any mutation — append, insert,
remove, sort — fires registered callbacks with a `CollectionChange` event that identifies
the `ChangeKind` (added, removed, moved) and the affected indices or items. This is more
informative than a simple "something changed" notification, and allows efficient incremental
UI updates for controls like `ListViewControl` that display collections. `ObservableDict`
does the same for mutable dictionaries.

When multiple observable values must be updated atomically — for example, when updating both
the title and body of a message object to keep them in sync — the `reactive_batch` context
manager (and the companion predicate `is_batching`) allow all mutations inside the block to be
queued, with subscribers notified only once after the block exits. This prevents intermediate
states from propagating to subscribers and producing flickering or inconsistent UI.

`ComputedValue` takes the reactive model one step further. It is an `ObservableValue` whose
value is always the result of a pure function applied to one or more source observables. When
any source changes, the computed value recomputes and notifies its own subscribers. This
eliminates the common pattern of subscribing to a source, writing to a second observable, and
hoping the two stay in sync. A `ComputedValue` makes the derivation declarative and automatic.
Use it whenever one piece of state is a deterministic function of another — for example, a
formatted display string derived from a numeric measurement value.

Subscription lifecycle is the most important operational concern in a reactive system. A
subscription holds a reference to the subscriber via the callback. If a feature creates a
subscription in `build_runtime` and the feature is later destroyed (for example, by a scene
transition), the subscription must be explicitly removed before destruction. Failing to do so
keeps the feature's callback registered in the observable, which prevents garbage collection
of the feature and causes the callback to fire on a dead object — typically producing
attribute errors or corrupted state. The correct pattern is to store subscription handles
returned by `.subscribe()` in a list, and to call unsubscribe on all handles in the feature's
teardown phase. Subscriptions should be created in `bind_runtime` (when the runtime is ready
and sibling features are built), not in `build` (when other features may not yet exist) or in
`on_update` (which would create duplicate subscriptions on every frame).

The binding model for controls follows naturally from this. Most `gui_do` controls accept an
`ObservableValue` anywhere they accept a plain value for display properties — a label's text,
a progress bar's value, a toggle's checked state. When a control receives an observable, it
subscribes internally and redraws itself whenever the observable changes. The feature code
never needs to reach into the control to update it — it only changes the observable, and the
control updates itself. This separation means the control can be swapped for a different
control type (or completely hidden) without changing the data logic at all.

Observable values are also the preferred mechanism for cross-feature data sharing. One feature
owns an `ObservableValue` and exposes it through its public interface or through the shared
host attributes. Other features subscribe to it in their `bind_runtime` phase, when all
sibling features are guaranteed to be built and their public attributes available. The
producing feature never knows who is observing, and the observing features do not depend on
the producer's internal implementation. The only shared contract is the observable itself — a
stable public attribute on the producing feature or a shared state store.

The most common reactive mistakes are: polling an observable in `on_update` instead of
subscribing (this introduces one-frame latency and burns CPU every frame instead of running
only when the value changes), subscribing in `build` before sibling features are ready
(subscriptions to sibling observables must wait for `bind_runtime`), forgetting to unsubscribe
when a feature is torn down (produces memory leaks and phantom callbacks that fire on dead
objects), and passing mutable plain Python objects across features instead of wrapping them in
`ObservableValue` or `ObservableList` (the receiving feature has no way to know when the value
changes, so the reactive contract is broken and the UI stops updating correctly). These anti-
patterns share a common root: they reintroduce the coupling and polling that reactive design
is intended to eliminate.

**[PRACTICE]**

```python
from gui_do import ObservableValue, ComputedValue

# Plain observable
count = ObservableValue(0)
handle = count.subscribe(lambda v: print(f"Count changed to {v}"))
count.set(1)   # prints "Count changed to 1"
count.unsubscribe(handle)

# Computed (derived) observable
label_text = ComputedValue(count, lambda n: f"Items: {n}")
# label_text.get() → "Items: 1"

# Batch multiple mutations so subscribers fire only once
from gui_do import reactive_batch
title = ObservableValue("old title")
body = ObservableValue("old body")
with reactive_batch():
    title.set("new title")
    body.set("new body")
# subscribers for title and body fire once each, after the block exits
```

---

### Feature Composition and Lifecycles

[Back to Table of Contents](#table-of-contents)

**[CONCEPT]**

A Feature is the primary unit of application behavior in `gui_do`. Everything that a `gui_do`
application does — displaying UI, handling input, running background logic, managing state,
responding to events — is organized into features. A feature is self-contained: it declares
what host resources it needs, builds its own UI elements during construction, registers its own
callbacks and subscriptions during runtime binding, processes events that are routed to it, and
tears itself down cleanly when its scene exits. The framework is responsible only for
orchestrating the lifecycle phases in the correct order and routing events to the correct
features; the features are responsible for their own behavior.

The framework provides four concrete feature base classes, each designed for a specific role:

`DirectFeature` is the lightest-weight type. It renders directly to the screen surface on every
frame but does not participate in the control tree, hit-testing, or focus management. Use it for
background elements — animated backdrops, full-screen particle effects, looping visual scenes —
where the overhead of the control tree is unnecessary and would add latency for no benefit. A
`DirectFeature` implements `draw_direct(host, surface, theme)` for its per-frame drawing.

`Feature` is the standard workhorse. It builds controls in the scene's control tree during
`build`, participates in focus management and hit-testing, and receives routed events. Use it
for any feature that shows interactive UI. Most application features are `Feature` subclasses.

`LogicFeature` has no UI of its own. It exists to hold domain logic, manage shared state, run
background computations via `CooperativeScheduler` coroutines, and publish results as observables
that UI features react to. A `LogicFeature` never creates controls and never handles GUI events;
it only manages data and computation. Separating logic into `LogicFeature` instances makes the
logic independently testable: it can be instantiated and exercised in unit tests with a mock
host and no display.

`RoutedFeature` is a `Feature` that additionally participates in the action routing
infrastructure. It can declare route targets — named handler methods that the framework
dispatches named action messages to. Use a `RoutedFeature` when a feature must respond to
framework-level named actions (such as "open_file", "undo", "show_help") in addition to raw
GUI events.

Every feature class defines a class attribute `HOST_REQUIREMENTS`, which is a dictionary
mapping lifecycle method names to tuples of attribute names that the host must provide before
calling that method. For example:

```python
class MyFeature(Feature):
    HOST_REQUIREMENTS = {
        "build": ("app", "screen_rect", "controls"),
        "bind_runtime": ("app", "screen_rect", "my_logic_feature"),
    }
```

The framework validates `HOST_REQUIREMENTS` at application startup, before any lifecycle
methods are called. If a required attribute is missing from the host, the framework raises a
clear error message identifying the missing binding and the feature that needs it. This
transforms what would otherwise be a runtime `AttributeError` halfway through initialization
into a startup-time configuration error. The `HOST_REQUIREMENTS` protocol is how features
express their dependencies declaratively, and it replaces constructor injection as the
primary dependency-declaration mechanism in `gui_do`.

The lifecycle phases execute in a fixed order. When a scene is first activated:

1. `build(host)` is called on every feature in the scene. Use this phase to create controls,
   add them to the scene's control tree, create window presenters, and set up any static
   structure that does not depend on runtime state or on other features. Controls created during
   `build` live for the full lifetime of the scene.

2. `bind_runtime(host)` is called on every feature in the scene after all features have
   completed `build`. At this point, all controls exist, all sibling features are built and
   their public attributes are set, and the runtime is fully initialized. Use this phase to
   subscribe to observables, bind controls to data sources, register callbacks that depend on
   sibling feature state, initialize display state from runtime sources (current screen size,
   loaded settings, etc.), and wire cross-feature interactions.

3. On every frame, `on_update(host)` is called on every active feature (passing
   elapsed time in seconds via the `dt_seconds` argument on `Feature.on_update` — note that
   `on_update(host)` is the actual signature; the elapsed time is typically read from the host).
   Use this for animations, cooperative scheduler ticks, polling background results, and any
   per-frame state changes. Keep this method fast: expensive computation in `on_update` directly
   reduces frame rate.

4. On every frame after `on_update`, `draw(host, surface, theme)` is called on features that
   override it. Use this for custom drawing that bypasses the control tree — particle overlays,
   canvas effects, debug visualizations. Most features do not need to override `draw`.

5. `handle_event(host, event)` is called whenever the event routing system delivers a
   `GuiEvent` to the feature. Return `True` to consume the event and stop further propagation;
   return `False` or `None` to pass it through. The framework filters events by scene scope,
   focus state, and overlay state before delivering them, so features only receive events they
   are eligible to handle.

When a scene transitions out, the framework calls shutdown lifecycle hooks on the departing
scene's features. Features from the previous scene do not receive `on_update`, `draw`, or
`handle_event` calls after the transition completes, so there is no risk of stale callbacks
or data mutations from a previous scene leaking into the new one. The arriving scene's features
go through `build` and `bind_runtime` fresh.

Features communicate with each other through `FeatureMessage` publishing rather than through
direct references. A feature publishes a message by name with an optional payload dictionary;
the framework delivers it to any feature in the same scene that has registered a handler for
that name. This loose-coupling mechanism prevents features from depending on each other's
implementations: the producer never imports the consumer, and the consumer never imports the
producer. Both depend only on the message name string, which serves as the contract. For
tighter real-time coupling — when one feature must continuously reflect the state of another —
observable values shared through the host's attributes are the preferred alternative to direct
method calls.

The organizational convention for feature packages — enforced by the architecture boundary
contract and tested in `tests/test_architecture_boundary_docs_contracts.py` — is that each
feature lives in its own folder as a Python package. The `__init__.py` of that package is the
sole public surface: it exports the Feature class and any public types that outside code needs,
and nothing else. Internal files are separated by concern and named descriptively:
`myfeature_feature.py` owns the Feature class and lifecycle methods; `myfeature_presenter.py`
owns the `WindowPresenter` subclass; `myfeature_specs.py` owns shared constants; logic
companion files own background computation. Bootstrap code imports only from the package
surface, never from the internal submodules. This means any internal reorganization is
completely transparent to the bootstrap and to other packages that consume the feature.

The most common multi-feature composition patterns are the logic-presentation split and the
presenter pattern. In the logic-presentation split, a `LogicFeature` runs background
computation (typically via `CooperativeScheduler` coroutines) and publishes results as
`ObservableValue` or `ObservableList` instances on its public interface. A `RoutedFeature`
subscribes to those observables in `bind_runtime` and uses them to drive the UI. The two
features are independently testable: the logic feature can be tested with a mock host and
verified to produce correct observable state; the presentation feature can be tested with a
mock host whose attributes include a mock logic feature with pre-set observable values. In the
presenter pattern, a `WindowPresenter` subclass handles the window layout and control
construction, while the `Feature` handles lifecycle coordination and routing. The feature
instantiates the presenter in `build` (lazily importing it to avoid circular imports) and
delegates window-related work to it.

**[PRACTICE]**

```python
from gui_do import Feature, LogicFeature, ObservableValue, FeatureMessage

class CounterLogic(LogicFeature):
    HOST_REQUIREMENTS = {"build": ("app",), "bind_runtime": ("app",)}

    def build(self, host):
        self.count = ObservableValue(0)

    def increment(self):
        self.count.set(self.count.get() + 1)
        self.publish(FeatureMessage("count_changed", {"value": self.count.get()}))


class CounterDisplay(Feature):
    HOST_REQUIREMENTS = {
        "build": ("app", "screen_rect", "controls"),
        "bind_runtime": ("app", "counter_logic"),   # sibling feature attribute
    }

    def build(self, host):
        from gui_do import LabelControl
        self._label = LabelControl(text="Count: 0")
        host.controls.add(self._label)

    def bind_runtime(self, host):
        # Bind label directly to the logic feature's observable
        host.counter_logic.count.subscribe(
            lambda v: self._label.set_text(f"Count: {v}")
        )
```

---

## Quickstart Path

[Back to Table of Contents](#table-of-contents)

This chapter provides a practical path from zero to a working `gui_do` application. The steps
are ordered to build understanding incrementally: each step introduces exactly one new concept
so you can verify it works before moving on. After completing this path, you will have a
functioning application and the mental scaffolding to read any system chapter independently.

### Step 1: Install and Verify

Install `gui_do` in editable mode and confirm the public API is intact:

```bash
python -m pip install -e . --no-deps
python -m pytest -q tests/test_public_api_exports.py
```

`gui_do` requires `pygame` and `numpy` (numpy is used internally for pixel buffer operations
via `pygame.PixelArray`). Both must be installed before starting the application runtime.

### Step 2: Create a Minimal Host Configuration

A `gui_do` application is bootstrapped by constructing a `HostApplicationBindingSpec`,
converting it to a `HostApplicationConfig` with `build_host_application_config`, and then
passing the config to `bootstrap_host_application`. The spec is where every structural
decision is declared. The following shows a realistic minimal spec:

```python
from gui_do import (
    build_host_application_config,
    bootstrap_host_application,
    HostApplicationBindingSpec,
    SceneBundleBindingSpec,
    ActionBindingSpec,
    TelemetryConfig,
)
from my_app.my_feature import MyFeature

config = build_host_application_config(
    HostApplicationBindingSpec(
        display_size=(1280, 720),
        window_title="My App",
        initial_scene_name="main",
        fonts={
            "default": {"file": "assets/fonts/Body.ttf", "size": 14},
        },
        scene_bundle_entries=(
            SceneBundleBindingSpec(
                scene_name="main",
                pretty_name="Main",
                bind_escape_to_exit=True,
            ),
        ),
        feature_entries=(
            ("_my_feature", MyFeature),
        ),
        action_entries=(
            ActionBindingSpec(kind="exit", action_id="exit", label="Exit", category="File"),
        ),
        telemetry=TelemetryConfig(enabled=False),
        target_fps=120,
    )
)

bootstrap_host_application(config)
```

The key fields:

| Field | Purpose |
|---|---|
| `display_size` | Window dimensions in pixels |
| `window_title` | OS window title bar text |
| `initial_scene_name` | Which scene activates on startup |
| `fonts` | Font file paths and sizes keyed by role name |
| `scene_bundle_entries` | Declares the application's scenes |
| `feature_entries` | Declares features and their host attribute names |
| `feature_window_bundle_entries` | Features with managed floating windows |
| `action_entries` | Named application-level actions |
| `target_fps` | Frame rate cap passed to the event loop |

### Step 3: Add a Feature with Observable State

Every feature inherits from `Feature` and implements lifecycle methods. The following is a
minimal feature that creates a label and updates it reactively from an observable value:

```python
from gui_do import Feature, ObservableValue, LabelControl

class MyFeature(Feature):
    HOST_REQUIREMENTS = {
        "build": ("app", "screen_rect", "controls"),
        "bind_runtime": ("app",),
    }

    def build(self, host):
        self.message = ObservableValue("Hello, gui_do!")
        rect = host.screen_rect.inflate(-40, -40)
        self._label = LabelControl(
            rect=rect,
            text=self.message.get(),
        )
        host.controls.add(self._label)
        self._sub = None

    def bind_runtime(self, host):
        self._sub = self.message.subscribe(
            lambda v: self._label.set_text(v)
        )

    def shutdown_runtime(self, host):
        if self._sub is not None:
            self.message.unsubscribe(self._sub)
```

`HOST_REQUIREMENTS` declares what the host must provide before each lifecycle method is called.
The framework validates these at startup and raises clear errors if bindings are missing.

### Step 4: Add an Action and Runtime Scene Policy

Actions let you declare named application behaviors and bind them to keyboard shortcuts:

```python
from gui_do import ActionBindingSpec, SceneBundleBindingSpec

# In HostApplicationBindingSpec:
scene_bundle_entries=(
    SceneBundleBindingSpec(
        scene_name="main",
        pretty_name="Main",
        bind_escape_to_exit=True,    # Pressing Escape exits the app
        prewarm=True,                # Render the scene before first display
    ),
),
action_entries=(
    ActionBindingSpec(kind="exit", action_id="exit", label="Exit", category="File"),
    ActionBindingSpec(
        kind="palette_open",
        action_id="palette_open",
        label="Open Command Palette",
    ),
),
```

### Step 5: Run the Application

`bootstrap_host_application` builds all runtime systems and runs the event loop. It does not
return until the application exits. The `target_fps` value controls the frame budget:

```python
bootstrap_host_application(config)
# Application runs here. Control returns after the window closes.
```

### Guided Build Track

Six milestones for building confidence with the framework:

- **Milestone A** — Application boots to a single scene with no errors. Confirm by running
  the script and seeing the window open without tracebacks.
- **Milestone B** — One feature creates one visible control. Add a `LabelControl` in `build`
  and confirm it renders on screen.
- **Milestone C** — One observable updates one control reactively. Change the observable
  value from `on_update` or from an event handler and confirm the label text updates.
- **Milestone D** — One action and one hotkey trigger expected behavior. Add an `ActionBindingSpec`
  with a `key` field and confirm the callback fires when the key is pressed.
- **Milestone E** — One overlay and one toast route without input leakage. Show a toast from
  `ToastManager` and confirm input is not blocked while it is visible.
- **Milestone F** — Workspace save/load roundtrip succeeds. Use `WorkspacePersistenceManager`
  to save and restore scene state; confirm values survive an app restart.

**Beginner confidence checklist:**
- You can explain where `build` ends and `bind_runtime` begins, and why the split exists.
- You can add and remove a feature by changing only the `HostApplicationBindingSpec`.
- You can trace a keypress through routing: keyboard event → `InputMap` → `ActionManager` →
  action handler.

### Quickstart Failure Modes

**Feature never appears on screen:** Verify that the feature's `factory` is listed in
`feature_entries` and that the feature's `scene_name` (or scene targeting) matches the
`initial_scene_name` in the spec. If the feature does not set a `scene_name`, it defaults to
all scenes; if it sets a scene name that does not match an active scene, it will not run.

**Hotkey does nothing:** Verify that the `ActionSpec` or `ActionBindingSpec` has a `key` field
set, that the action's `action_id` matches what the handler is registered for, and that the
input binding's scope does not restrict it to a specific window when no window is focused.

**Overlay blocks unexpected keys:** Check the `consume_unhandled_keys` setting of the overlay
or dialog. Some overlay types consume all keyboard input by default to prevent background
features from receiving keys while a modal is active. Explicitly set the policy to allow
passthrough if needed.

**State updates but UI does not change:** Confirm that the observable subscription was created
in `bind_runtime` (not in `build`), that the subscription handle was stored and not
inadvertently disposed, and that the control's update callback correctly calls the control's
setter method rather than trying to reassign a local variable.

---

## Architecture and Runtime Model

[Back to Table of Contents](#table-of-contents)

Understanding `gui_do`'s architecture — how the framework is structured, where the boundaries
are, and how the runtime operates at a systems level — is essential before you can reason
confidently about why a particular behavior occurs and how to change it. This chapter describes
the boundary model, the tiered API design, and the runtime's operational guarantees.

### Boundary Model: Framework vs Consumer

`gui_do` enforces a strict one-directional boundary between framework code and consumer code.
The `gui_do/` package is the framework: a reusable runtime that knows nothing about any
specific application. The `demo_features/` directory and `gui_do_demo.py` are the consumer
integration layer for the reference demo application. Application developers create their own
equivalent of `demo_features/` — their feature packages — and their own `demo_config.py`-
equivalent — their bootstrap configuration.

The hard rule is: **`gui_do/` must not import from `demo_features/`**. The framework code
must remain application-agnostic and independently deployable as a package. This boundary is
not advisory — it is enforced by automated tests:

```
tests/test_boundary_contracts.py::test_gui_package_does_not_import_demo_features
tests/test_boundary_contracts.py::test_demo_entrypoint_uses_gui_root_import
```

The boundary exists to keep `gui_do/` reusable across multiple projects. Code in `gui_do/`
can only depend on pygame, numpy, the standard library, and other modules within `gui_do/`.
The framework never imports any application-specific class.

The consumer side has a corresponding rule: consumer code (your application's feature packages
and bootstrap script) imports from the `gui_do` root — `from gui_do import X` — never from
`gui_do.*` internal submodules. The public API exported from `gui_do/__init__.py` is the
stable surface; internal module paths can change without notice. This rule is part of the
`docs/architecture_boundary_spec.md` contract.

### Tiered Public API Model

`gui_do/__init__.py` organizes all public exports into numbered tiers. Each tier is a logical
group of related functionality. The tier number conveys the recommended entry point order: when
two tiers offer overlapping capability, start with the lower-numbered tier because it provides
the more abstract, data-driven interface with more framework support.

**Tier 1 — Primary Entry Points and Data-Driven APIs.** This tier contains everything a new
application needs: the Feature base classes (`Feature`, `DirectFeature`, `LogicFeature`,
`RoutedFeature`), the spec types (`FeatureSpec`, `WindowSpec`, `RuntimeSceneSpec`, `ActionSpec`,
and dozens more), the builder (`build_host_application_config`), and the bootstrap entry point
(`bootstrap_host_application`). Start every new `gui_do` application here and only descend to
lower tiers when Tier 1 abstractions do not cover your need.

**Tiers 2–7 — Core Runtime Systems.** These tiers provide the systems that Tier 1 sits on top
of. Tier 2 exposes `GuiApplication`, `create_display`, and `SceneTransitionManager` for
direct application and scene control. Tier 3 provides the observable primitives
(`ObservableValue`, `ObservableList`, `ObservableDict`, `ComputedValue`). Tier 4 covers events,
actions, focus, and input primitives. Tier 5 is scheduling and animation. Tier 6 is theme and
fonts. Tier 7 is telemetry and diagnostics.

**Tiers 8–32 — Specialized Systems.** These tiers cover layout engines, overlay managers, form
models, controls, text and localization, data helpers, graphics, state machines, persistence,
introspection, audio, accessibility, and advanced infrastructure. Use these tiers when you need
capabilities not provided by the higher-level Tier 1 abstractions.

The tier numbering is not an arbitrary ordering — it reflects the dependency structure of the
framework. Higher-tier code depends on lower-tier code. Application code should prefer the
highest tier that meets its needs, which minimizes the amount of internal framework behavior it
must manage explicitly.

Tier 19 (`UiEngine`) is marked "Infrastructure & Internals — avoid in application code." Do
not use it directly; it is exported only for advanced extension scenarios.

### Runtime Guarantees

**[CONTRACT]** The following guarantees are contractually enforced by the runtime and verified by tests:

- **Canonical `GuiEvent` normalization.** Raw pygame events are normalized to `GuiEvent` objects
  before any application-level dispatch. Application code only ever receives `GuiEvent` instances
  in `handle_event`. The mapping from raw event types to `EventType` enum values is deterministic.

- **Scene-isolated update execution.** Runtime systems that are scene-scoped (schedulers,
  animation state machines, coroutine runners, etc.) execute only for the currently active scene.
  Background scenes do not receive update ticks, animation steps, or coroutine progress.

- **Deterministic focus candidate ordering.** Window focus cycling iterates candidates in
  ascending `control_id` order. This means keyboard tab order and focus cycling behavior is
  stable across runs and not dependent on creation order or memory layout.

- **Scheduler dispatch budget clamping.** The `TaskScheduler` dispatches messages within a
  per-frame budget calculated as `max(floor, min(ceiling, fraction × dt_ms))`. The values are:
  `fraction = 0.12`, `floor = 0.5 ms`, `ceiling = 4.0 ms`. This gives predictable upper bounds
  under slow frames (no starvation) and prevents over-allocation under fast frames.

- **Missing settings keys are skipped gracefully.** During workspace restore, unknown or missing
  settings keys are recorded in the restore report's `skipped_settings` and `missing_settings_blocks`
  fields but do not abort the restore process. The restore report is returned by
  `WorkspacePersistenceManager.restore` and includes the fields: `target_scene`,
  `switched_scene`, `restored_feature_states`, `restored_scene_nodes`, `applied_settings`,
  `skipped_settings`, and `missing_settings_blocks`.

### Event Pipeline

When a raw pygame event arrives at the runtime's process_event method, it passes through these
stages in order:

1. **Normalization.** The raw event is converted to a `GuiEvent` with a typed `EventType`,
   normalized coordinates, and metadata. At this point propagation and default behavior flags
   are at their initial state.

2. **Quit handling.** `QUIT` events are intercepted early before reaching any feature code.

3. **Input state update.** Shared keyboard and pointer state is updated so downstream code
   reads consistent state.

4. **Pointer localization.** Pointer events receive scene-relative coordinates while retaining
   raw screen coordinates. Pointer lock and capture constraints are applied here.

5. **Overlay and focus routing.** If a modal overlay is active, keyboard and pointer events
   are directed to the overlay. Focus manager state is updated. Toast hover reconciliation runs.

6. **Keyboard routing.** Keyboard events pass through the global key bindings (registered via
   `ActionManager.bind_global_key`), the active-window key handlers, and then the scene's
   keyboard handler policy. The command palette activation key is a global key and therefore
   checked before focus dispatch.

7. **Feature and scene dispatch.** Events are delivered to active features via `handle_event`.
   Features return `True` to consume an event and stop propagation.

8. **Propagation enforcement.** If `propagation_stopped` or `default_prevented` is set on the
   event, further delivery stops immediately. `GuiEvent.clone()` produces an independent copy;
   mutations to the clone do not affect the original.

---

## Core Workflow: Build, Bind, Route, Update, Draw

[Back to Table of Contents](#table-of-contents)

The five-phase workflow is the programming model for every feature in `gui_do`. Understanding
what each phase is for, what invariants hold during it, and what must not cross phase boundaries
gives you the mental model you need to write correct, maintainable features.

### Phase Reference

**Build** is the construction phase. When a scene activates, `build(host)` is called on every
feature in that scene in registration order. During `build`, a feature creates its controls,
adds them to the scene's control tree or window tree, allocates its observable values, and
establishes any static structure that does not depend on runtime state. The critical invariant
of `build` is: do not create subscriptions and do not access sibling features. At build time,
sibling features may not yet have been built, and their public attributes may not yet exist.
Subscriptions created during `build` may fire before controls are ready. Everything that
depends on the runtime being fully initialized must wait for `bind_runtime`.

**Bind_runtime** is the wiring phase. It is called on every feature in the scene only after
all features have completed `build`. At this point, every feature's controls exist, every
sibling feature's `build` has completed and its public observable attributes are accessible,
and the runtime infrastructure (theme, scheduler, font roles, etc.) is fully initialized. This
is the correct phase for: subscribing to observable values, binding controls to data sources,
registering callbacks that depend on sibling feature state, reading initial values from the
host (screen rect, settings, scene state), and wiring up cross-feature coordination.

**Route** is not a lifecycle method called by name — it describes what happens during event
delivery. When the framework calls `handle_event(host, event)` on a feature, the feature is in
the routing phase. The feature examines the event's `EventType` and decides whether to handle
it. Returning `True` consumes the event; returning `False` or `None` passes it to the next
eligible recipient. `RoutedFeature` subclasses additionally receive named action messages
dispatched through the routing infrastructure, mapped to specific handler methods declared as
route targets.

**Update** is the per-frame logic phase. `on_update(host)` is called every frame on every
active feature after all events have been processed. This is where animations advance, timers
tick, cooperative scheduler coroutines run, and per-frame state transitions are calculated. The
elapsed time between frames is available through the host or through the `Timers` system. Keep
`on_update` implementations fast: any computation that takes significant time belongs in a
`CooperativeScheduler` coroutine on a `LogicFeature`, not in the update loop directly.

**Draw** is the custom rendering phase. `draw(host, surface, theme)` is called every frame
after `on_update`, for features that override it. The feature receives the pygame `Surface`
and the current `ThemeManager` instance and may render anything it wants. Most features do not
need to override `draw` — the control tree handles all standard rendering. Override `draw`
only for effects that controls cannot express: particle systems, procedural backgrounds, canvas
overlays, debug visualizations.

### Message and Logic Coordination

`FeatureMessage` publishing is the loose-coupling mechanism for cross-feature communication. A
feature calls `self.publish(FeatureMessage("event_name", {"payload_key": value}))` and the
framework delivers the message to any feature in the same scene that has registered a handler
for `"event_name"`. Neither the publisher nor the subscribers hold references to each other.
The message name string is the only shared contract.

When real-time state sharing is needed — where one feature must continuously reflect the value
of another — observable values are more appropriate than messages. A `LogicFeature` computes
state and stores it in `ObservableValue` attributes. UI features subscribe to those attributes
in `bind_runtime`. State updates flow automatically whenever the `LogicFeature` writes to an
observable, without any explicit message passing. Observable state is preferred for continuous
values; messages are preferred for discrete events ("computation complete", "user confirmed",
"error occurred").

The `LogicFeature` class is the natural coordination hub for shared state in a multi-feature
scene. It holds the observables, runs the background computation (typically in a
`CooperativeScheduler` coroutine), and publishes both observable changes and event-style
messages. UI features subscribe to its observables and listen for its messages without knowing
anything about how the logic feature works internally.

### When to Use Routed Runtime Specs

For features that participate in the full data-driven runtime — with action hotkeys, shortcut
overlay declarations, task-panel focus toggles, and event subscriptions — `RoutedRuntimeSpec`
and `RoutedFeatureLifecycleSpec` reduce the boilerplate dramatically. Instead of manually
calling `bind_input_map_actions`, `register_action_hotkeys`, `create_shortcut_help_overlay`,
and `bind_task_panel_focus_toggle` in `build` and `bind_runtime`, you declare them once in a
`RoutedRuntimeSpec` and call `setup_routed_runtime` to apply all wiring in a single call.
`shutdown_routed_runtime` reverses the wiring during scene teardown.

`bind_routed_feature_lifecycle` and `shutdown_routed_feature_lifecycle` are the finer-grained
equivalents — they apply the routed feature wiring for a single `RoutedFeature` within a
scene, rather than for the full scene bundle. Use these when only one feature in a scene needs
routed lifecycle management while others use manual wiring.

A `RoutedRuntimeSpec` declaration looks like:

```python
from gui_do import RoutedRuntimeSpec, ActionHotkeySpec, ShortcutOverlaySpec
import pygame

ROUTED_SPEC = RoutedRuntimeSpec(
    scene_name="main",
    action_hotkeys=(
        ActionHotkeySpec(
            action_id="open_panel",
            key=pygame.K_p,
            label="Open Panel",
        ),
    ),
    shortcut_overlay=ShortcutOverlaySpec(
        activation_key=pygame.K_F1,
        title="Keyboard Shortcuts",
    ),
)
```

This single spec drives hotkey registration, input map binding, shortcut overlay creation, and
cleanup — all without the feature implementing any of that machinery manually.



## Main Systems Reference

[Back to Table of Contents](#table-of-contents)

The Main Systems Reference contains one chapter for each of the 16 major system areas exposed
by `gui_do`. Each chapter follows a fixed template: purpose, mental model, public APIs, typical
usage flow, minimal example, advanced patterns, common mistakes, and cross-links to related
systems.

### 8.1 Application Bootstrap and Host Configuration

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Application bootstrap is the process of translating the developer's declarative spec graph
into a live, running `gui_do` application. The bootstrap system exists because `gui_do` is
built on the data-driven design principle: the developer describes what the application should
be, and the framework builds it. Without a centralized bootstrap, each of the framework's
systems — the action registry, the input map, the window presenter, the scene transition
manager, the font role registry, the cursor manager — would need to be initialized and wired
separately by hand, in the correct order, with correct cross-references. The bootstrap system
performs all of that work in a single deterministic pass.

The result of a successful bootstrap is that the host object (the Python namespace that the
bootstrap populates) has every declared feature, scene, action, window, font role, cursor, and
runtime system available as a named attribute. After `bootstrap_host_application` returns, the
application is in its first scene, fully wired and ready to run its event loop.

#### Mental model and lifecycle placement

Think of the host as a plain Python object that starts empty and is progressively populated by
the bootstrap. The bootstrap reads the `HostApplicationConfig`, resolves the spec graph, creates
all the runtime systems, calls `build` and `bind_runtime` on all features in order, and then
starts the event loop. Bootstrap is a one-time, startup-time operation. It runs once; everything
after it is the steady-state event loop.

The builder function `build_host_application_config` operates at a higher level of abstraction
than the raw `HostApplicationConfig` fields. It accepts a `HostApplicationBindingSpec` —
a single top-level binding object that collects all of the application's structural declarations
using bundle helpers — and produces a fully resolved `HostApplicationConfig`. The binding spec
is designed for composability: instead of constructing every low-level spec individually, the
developer uses bundles (`SceneBundleBindingSpec`, `FeatureWindowBundleBindingSpec`,
`FontRoleBindingSpec`, `CursorBindingSpec`, `ActionBindingSpec`, `PaletteBindingSpec`) that
the builder expands into the low-level specs automatically.

#### Primary public APIs and key types

From **Tier 1**:
- `bootstrap_host_application(config)` — builds all runtime systems and starts the event loop
- `build_host_application_config(spec)` — converts `HostApplicationBindingSpec` to `HostApplicationConfig`
- `HostApplicationConfig` — the fully resolved config structure passed to bootstrap
- `HostApplicationBindingSpec` — the high-level binding spec; the recommended entry point
- `SceneBundleBindingSpec` — bundles a scene's setup, pristine asset, and transition style
- `FeatureWindowBundleBindingSpec` — bundles a feature with its managed floating window
- `FontRoleBindingSpec` — binds a font role name to a size and font key
- `CursorBindingSpec` — binds a cursor name to an image file and hotspot
- `ActionBindingSpec` — declares a named application action with optional key and kind
- `PaletteBindingSpec` — configures the command palette's entry groups
- `TelemetryConfig` — controls telemetry collection
- `SceneTransitionStyle` — enum for scene transition animations (e.g. `SLIDE_RIGHT`, `SLIDE_LEFT`)
- `TelemetryConfig` — controls telemetry sampling behavior
- All `build_*` builder functions: `build_feature_specs`, `build_action_specs`, `build_scene_bundle_specs`, etc.

From **Tier 2**:
- `GuiApplication` — the live application runtime; available as `host.app` after bootstrap
- `create_display` — creates the pygame display at the specified size
- `SceneTransitionManager` — manages animated scene transitions

#### Typical usage flow

1. Import `HostApplicationBindingSpec`, `build_host_application_config`, `bootstrap_host_application`.
2. Import all feature classes used by the application.
3. Construct a `HostApplicationBindingSpec` with `display_size`, `window_title`,
   `initial_scene_name`, `fonts`, `scene_bundle_entries`, `feature_entries`, and any
   additional binding entries for windows, actions, cursors, font roles, and palette.
4. Pass the spec to `build_host_application_config` to produce a `HostApplicationConfig`.
5. Pass the config to `bootstrap_host_application`. This is a blocking call — it runs the
   event loop and returns only when the application exits.

#### Minimal example

```python
from gui_do import (
    HostApplicationBindingSpec,
    SceneBundleBindingSpec,
    ActionBindingSpec,
    TelemetryConfig,
    build_host_application_config,
    bootstrap_host_application,
)
from my_app.counter_feature import CounterFeature

config = build_host_application_config(
    HostApplicationBindingSpec(
        display_size=(1280, 720),
        window_title="Counter App",
        initial_scene_name="main",
        fonts={"default": {"file": "assets/Body.ttf", "size": 14}},
        scene_bundle_entries=(
            SceneBundleBindingSpec(
                scene_name="main",
                pretty_name="Main",
                bind_escape_to_exit=True,
            ),
        ),
        feature_entries=(
            ("_counter", CounterFeature),
        ),
        action_entries=(
            ActionBindingSpec(kind="exit", action_id="exit", label="Exit", category="File"),
        ),
        telemetry=TelemetryConfig(enabled=False),
        target_fps=120,
    )
)

bootstrap_host_application(config)
```

#### Advanced pattern: multi-scene, multi-window composition

`FeatureWindowBundleBindingSpec` is the recommended way to add a feature that owns a floating,
toggle-able window. The bundle automatically creates a task panel button and a window toggle
action for the window, links them, and registers them with the spec graph:

```python
from gui_do import FeatureWindowBundleBindingSpec

feature_window_bundle_entries=(
    FeatureWindowBundleBindingSpec(
        "_inspector",
        InspectorFeature,
        "inspector",                     # key prefix for generated names
        task_panel_label="Inspector",
        task_panel_style="round",
    ),
),
```

`SceneBundleBindingSpec` with `include_nav_action=True` automatically creates a scene
navigation action and registers it with the command palette, enabling scenes to be switched
via the palette keyboard shortcut.

#### Common mistakes and anti-patterns

- **Setting `initial_scene_name` to a scene not declared in `scene_bundle_entries`** — bootstrap
  will fail at startup with a scene resolution error. Every scene name referenced must have a
  matching `SceneBundleBindingSpec`.
- **Manually mutating host attributes after bootstrap** — the host is fully populated by
  bootstrap; adding or replacing attributes after the fact bypasses the spec graph and can
  produce inconsistent state.
- **Creating features without `HOST_REQUIREMENTS`** — this is not a crash, but it silently
  disables the framework's startup validation. Always declare `HOST_REQUIREMENTS` on every
  feature so configuration errors are caught at startup, not at runtime.
- **Calling framework APIs in feature `__init__`** — the feature constructor must not call
  any `gui_do` runtime APIs. All runtime interactions must occur in `build` or later phases.

#### Cross-links to related systems

- §8.2 Feature Lifecycle — features declared here run their lifecycle through the framework
- §8.3 Events and Actions — `action_entries` drive action registration
- §8.9 Scene, Window, and Task-Panel Presentation Models — `scene_bundle_entries` and
  `feature_window_bundle_entries` configure presentation

For field-level reference for all spec types listed above, see
[Appendix F: Specifications and Option Reference](#appendix-f-specifications-and-option-reference).

[Back to Table of Contents](#table-of-contents)

---

### 8.2 Feature Lifecycle and Feature Types

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

The feature lifecycle system is what allows `gui_do` to compose applications from independent,
self-contained behavioral units without any of them needing to know about each other. A
`Feature` declares its resource requirements, receives those resources through the `host`
argument during each lifecycle phase, and manages its own state. The framework provides the
correct ordering of phases, the routing of events, and the cleanup of features on scene
transitions. The feature author only needs to implement the methods and declare the requirements.

This system exists because the alternative — a monolithic application class that manages all
state and behavior — does not scale. When an application grows beyond a few screens of code,
a monolith becomes difficult to test, difficult to refactor, and difficult to extend. The
feature model encourages small, focused, independently testable units with clearly separated
concerns.

#### Mental model and lifecycle placement

A Feature is a state machine with distinct phases. `build` is the construction state; it runs
once when the scene activates. `bind_runtime` is the wiring state; it runs once after all
features have been built. The event loop then repeatedly calls `on_update` and `draw` every
frame, and `handle_event` for every routed event. When the scene exits, teardown hooks run
and the feature is deactivated.

The key mental model for lifecycle placement is: **build creates, bind connects, update drives,
draw renders, handle_event responds**. Any code that violates this assignment — subscribing in
`build`, creating controls in `bind_runtime`, running animations in `build` — will produce
bugs that are often subtle and hard to diagnose.

#### Primary public APIs and key types

From **Tier 1**:
- `Feature` — standard interactive feature; builds controls, handles events
- `DirectFeature` — lightweight feature that renders directly to the surface without the control tree
- `LogicFeature` — feature with no UI; for domain logic, shared state, background computation
- `RoutedFeature` — a `Feature` that additionally participates in action routing
- `FeatureMessage` — a named message with optional payload, for loose-coupled cross-feature events
- `FeatureManager` — manages the collection of active features; usually not needed directly
- `ScenePresentationModel` — holds scene-level presentation context; available on host
- `SceneSetupSpec` — static specification for a scene's layout and feature list

From **Tier 18** (advanced wiring helpers):
- `setup_routed_runtime`, `shutdown_routed_runtime` — wire/unwire a full `RoutedRuntimeSpec`
- `bind_routed_feature_lifecycle`, `shutdown_routed_feature_lifecycle` — per-feature routed wiring
- `register_routed_feature_companions` — register logic companion features alongside a routed feature
- `bind_feature_event_subscription`, `unbind_feature_event_subscription` — managed event subscriptions

#### Typical usage flow

1. Subclass the appropriate Feature type (`Feature`, `LogicFeature`, etc.).
2. Declare `HOST_REQUIREMENTS` — a dict mapping lifecycle method names to tuples of required
   host attribute names.
3. Implement `build(host)` — create controls, initialize observable state.
4. Implement `bind_runtime(host)` — subscribe to observables, bind controls to data, wire
   cross-feature interactions.
5. Optionally implement `on_update(host)`, `handle_event(host, event)`, `draw(host, surface, theme)`.
6. Implement `shutdown_runtime(host)` — dispose subscriptions and any managed resources.
7. Register the feature via `feature_entries` in `HostApplicationBindingSpec`.

#### Minimal example

```python
from gui_do import Feature, ObservableValue, LabelControl

class GreetingFeature(Feature):
    HOST_REQUIREMENTS = {
        "build": ("app", "screen_rect", "controls"),
        "bind_runtime": ("app",),
    }

    def build(self, host):
        self.greeting = ObservableValue("Hello!")
        self._label = LabelControl(
            rect=host.screen_rect.inflate(-40, -40),
            text=self.greeting.get(),
        )
        host.controls.add(self._label)
        self._sub = None

    def bind_runtime(self, host):
        self._sub = self.greeting.subscribe(
            lambda v: self._label.set_text(v)
        )

    def shutdown_runtime(self, host):
        if self._sub is not None:
            self.greeting.unsubscribe(self._sub)
```

#### Advanced pattern: logic-presentation split

A `LogicFeature` computes state and exposes it as observables; a `RoutedFeature` subscribes
and drives the UI. The two are registered as companions:

```python
# Logic side
class CountLogic(LogicFeature):
    HOST_REQUIREMENTS = {"build": ("app",)}
    def build(self, host):
        self.count = ObservableValue(0)
    def increment(self):
        self.count.set(self.count.get() + 1)

# Presentation side
class CountDisplay(RoutedFeature):
    HOST_REQUIREMENTS = {
        "build": ("app", "screen_rect", "controls"),
        "bind_runtime": ("app", "_count_logic"),
    }
    def build(self, host):
        self._label = LabelControl(rect=host.screen_rect, text="0")
        host.controls.add(self._label)
    def bind_runtime(self, host):
        self._sub = host._count_logic.count.subscribe(
            lambda v: self._label.set_text(str(v))
        )
```

#### Common mistakes and anti-patterns

- **Subscribing in `build`** — sibling feature observables may not exist yet. Always subscribe
  in `bind_runtime`.
- **Accessing sibling features in `build`** — sibling build order is not guaranteed. Use
  `bind_runtime` for any cross-feature access.
- **Skipping `shutdown_runtime` cleanup** — subscriptions not disposed during shutdown
  produce memory leaks and phantom callbacks.
- **Creating controls outside of `build`** — controls created in `bind_runtime` or later may
  miss the initial layout pass.
- **Using `DirectFeature` for interactive UI** — `DirectFeature` bypasses the control tree
  and does not participate in hit-testing or focus. Use `Feature` for any interactive element.

#### Cross-links to related systems

- §8.1 Bootstrap — features are registered via `feature_entries` in the bootstrap spec
- §8.3 Events and Actions — events are routed to `handle_event`; `RoutedFeature` receives named action messages
- §8.4 State and Observables — observables drive cross-feature reactive state

For field-level reference for `FeatureSpec`, `RoutedRuntimeSpec`, and `RuntimeSceneSpec`, see
[Appendix F: Specifications and Option Reference](#appendix-f-specifications-and-option-reference).

[Back to Table of Contents](#table-of-contents)

---

### 8.3 Events, Actions, Input Mapping, and Routing

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

`gui_do` maintains a strict normalization layer between raw pygame input and application-level
event handling. Every raw pygame event is converted to a `GuiEvent` before any framework or
application code sees it. This normalization exists for three reasons: it provides a type-safe,
semantically meaningful event type (via the `EventType` enum) instead of raw integer event
types; it attaches metadata that the framework adds during routing (such as scene-local pointer
coordinates, control identifiers, and window focus context); and it provides propagation
control (`propagation_stopped`, `default_prevented`) that allows features to intercept and
consume events in a predictable, documented way.

The action system provides a named command abstraction on top of the event system. Instead of
checking for specific key codes in every feature's `handle_event`, a developer declares a named
action (e.g., `"open_panel"`) and binds it to a key via the `InputMap`. The `ActionManager`
dispatches the named action when the key is pressed. Features respond to action names, not to
raw key codes, making it trivial to rebind keys without changing any feature code.

#### Mental model and lifecycle placement

Think of the event system as a funnel that narrows from raw input to typed events to named
actions. At the wide end, raw pygame events arrive in arbitrary order. The funnel normalizes
them to `GuiEvent` objects, applies routing logic (overlay state, focus state, scene scope),
and delivers them either to features via `handle_event` or to action handlers via the action
registry. Named actions are the narrowest part of the funnel: by the time an action fires, the
platform-specific key code is gone and only the semantic intent ("open panel", "exit") remains.

#### Primary public APIs and key types

From **Tier 4**:
- `GuiEvent` — canonical normalized event object
- `EventType` — enum: `PASS`, `QUIT`, `KEY_DOWN`, `KEY_UP`, `MOUSE_BUTTON_DOWN`, `MOUSE_BUTTON_UP`, `MOUSE_MOTION`, `MOUSE_WHEEL`, `TEXT_INPUT`, `TEXT_EDITING`
- `EventPhase` — enum: `CAPTURE`, `TARGET`, `BUBBLE`
- `EventManager` — manages event normalization and dispatch
- `EventBus` — pub/sub bus for typed events
- `ActionManager` — registers and dispatches named actions; provides `bind_global_key`, `unbind_global_key`, `trigger_global_key_from_event`
- `ActionRegistry` — holds `ActionDescriptor` entries by action id
- `ActionDescriptor` — describes a named action with label and optional callback
- `InputMap` — maps (key, modifier, scope) tuples to action ids; provides `InputBinding`
- `InputBinding` — a single key-to-action mapping with optional modifier and scope
- `KeyChordManager`, `KeyChord`, `ChordStep` — multi-key chord sequences
- `FocusManager` — tracks which control has keyboard focus
- `FocusScope`, `FocusScopeManager` — named focus groups for tab-order scoping
- `WindowFocusManager` — manages focus cycling between floating windows
- `FocusRing` — ordered cycle of focus candidates within a scope
- `GestureRecognizer` — recognizes multi-step pointer gestures
- `EventRecorder`, `EventPlayback`, `RecordedEvent` — record and replay event sequences for testing
- `InputSnapshot` — immutable snapshot of keyboard/pointer state at a point in time
- `Signal`, `SignalConnection` — typed callback signal for one-to-many synchronous dispatch

From **Tier 1** (spec types):
- `ActionSpec` — declarative action descriptor for bootstrap
- `ActionHotkeySpec` — binds a hotkey to an action id
- `ControlKeyBindingSpec` — binds a key to a specific control
- `EventSubscriptionSpec` — declarative event handler registration

From **Tier 30**:
- `InteractionStateMachine`, `InteractionPhase`, `InteractionContext`, `InteractionTransition` — multi-phase pointer/keyboard gesture state machine

From **Tier 4** (action middleware):
- `ActionContext`, `ActionMiddleware` — middleware pipeline for action dispatch interception

#### Typical usage flow

1. Declare named actions via `ActionBindingSpec` entries in `HostApplicationBindingSpec`.
2. Optionally declare `ActionHotkeySpec` entries (or include them in `RoutedRuntimeSpec`)
   to bind keys to action ids.
3. In feature code, implement `handle_event` to check `event.type` and `event.key` for
   events not covered by named actions.
4. For multi-phase pointer interactions, use `InteractionStateMachine` to track phases
   (pressed, dragging, released) with guarded transitions.

#### Minimal example

```python
import pygame
from gui_do import Feature, GuiEvent, EventType

class KeyboardFeature(Feature):
    HOST_REQUIREMENTS = {"build": ("app",), "bind_runtime": ("app",)}

    def build(self, host):
        pass

    def bind_runtime(self, host):
        pass

    def handle_event(self, host, event: GuiEvent) -> bool:
        if event.type == EventType.KEY_DOWN and event.key == pygame.K_SPACE:
            print("Space pressed!")
            return True   # consume the event
        return False
```

#### Advanced pattern: interaction state machine for drag tracking

`InteractionStateMachine` tracks pointer gestures through phases without writing ad-hoc state
machines in `handle_event`:

```python
from gui_do import InteractionStateMachine, InteractionPhase, InteractionContext

class DragFeature(Feature):
    HOST_REQUIREMENTS = {"build": ("app", "screen_rect", "controls"), "bind_runtime": ("app",)}

    def build(self, host):
        self._ism = InteractionStateMachine()

    def handle_event(self, host, event: GuiEvent) -> bool:
        ctx = InteractionContext(event=event)
        new_phase = self._ism.process(ctx)
        if new_phase == InteractionPhase.DRAG:
            # respond to drag motion
            return True
        return False
```

`EventRecorder` and `EventPlayback` are used in the test suite to deterministically replay
sequences of events — see §9 Testing for usage.

#### Common mistakes and anti-patterns

- **Handling raw pygame events instead of `GuiEvent`** — raw events lack the routing metadata
  that gui_do attaches. Always receive events through `handle_event`, which already receives
  normalized `GuiEvent` instances.
- **Registering scene-scoped actions as global keys** — global keys (`bind_global_key`) are
  checked before focus dispatch and apply to all scenes. If an action should only be active in
  one scene, use scene-scoped `InputMap` bindings instead.
- **Forgetting to return `True` when consuming** — if `handle_event` handles an event but
  returns `None` or `False`, the event continues to propagate to other features. This can
  produce double-handling and unexpected behavior.
- **Not checking `propagation_stopped`** — if custom routing code delivers events manually,
  always check `event.propagation_stopped` before delivering to the next recipient.

#### Cross-links to related systems

- §8.2 Feature Lifecycle — events are delivered through `handle_event`
- §8.7 Focus and Accessibility — focus state affects which features receive keyboard events
- §8.8 Overlays — overlays intercept events before features during modal operation

For field-level reference for `ActionSpec`, `ActionHotkeySpec`, `InputBinding`, and shortcut specs, see
[Appendix F: Specifications and Option Reference](#appendix-f-specifications-and-option-reference).

[Back to Table of Contents](#table-of-contents)

---

### 8.4 State and Observables

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

The state and observables system provides the reactive data layer that decouples producers of
data from consumers of data. In `gui_do`, the state system exists at two levels. At the local
level, individual features own `ObservableValue`, `ObservableList`, and `ObservableDict`
instances that drive their controls and are accessible to sibling features. At the application
level, `AppStateStore` provides a single source of truth for state that must be shared across
scenes or that benefits from transactional update semantics.

Without a reactive state layer, feature code would need to imperatively update every control
that displays a piece of data whenever that data changes — the exact coupling problem that the
framework's data-driven design is built to avoid. Observable values solve this by making state
self-notifying: write to the value, and every subscriber (control, sibling feature, diagnostic
system) is updated automatically.

#### Mental model and lifecycle placement

Observables are created during `build` (or in the feature's `__init__` for values that exist
before the feature is built). Subscriptions are created during `bind_runtime`. Subscriptions
are disposed during `shutdown_runtime`. Observable values are written from any phase — from
`on_update` for per-frame state, from `handle_event` for event-driven state, or from background
coroutines for async state.

Think of observables as the "wires" in the data-driven model. The spec graph describes the
structure; the observables carry the live data through that structure at runtime.

#### Primary public APIs and key types

From **Tier 3**:
- `ObservableValue` — wraps a single reactive value; `.subscribe(cb)` returns a handle; `.get()` / `.set(v)` for access
- `ComputedValue` — derived `ObservableValue` that recomputes from source observables automatically
- `PresentationModel` — base class for view-model objects; holds a collection of `ObservableValue` fields
- `ObservableList` — reactive mutable list; fires `CollectionChange` events with `ChangeKind` on mutation
- `ObservableDict` — reactive mutable dict; same semantics as `ObservableList`
- `ChangeKind` — enum: added, removed, moved, replaced
- `CollectionChange` — event carrying kind, affected index/key, old and new values
- `CollectionViewQuery` — filter/sort/group specification for a live collection view
- `CollectionView` — a live filtered/sorted view over an `ObservableList`
- `Binding`, `BindingGroup` — named property-to-observable bindings for controls
- `ObservableStream` — push-based observable sequence (event stream, not value)
- `SelectionModel`, `SelectionMode` — single/multi-selection tracking over a collection
- `InvalidationTracker` — mark-and-sweep dirty tracking for explicit invalidation patterns
- `reactive_batch` — context manager that batches all subscriber notifications until exit
- `is_batching` — predicate: returns `True` if currently inside a `reactive_batch` block

From **Tier 27**:
- `AppStateStore` — single-source-of-truth state container with selector and transaction support
- `StateSelector` — derives a computed slice of `AppStateStore` state
- `StateTransaction` — atomic multi-field update; subscribers fire once when transaction commits

#### Typical usage flow

1. Create `ObservableValue` instances in feature `__init__` or `build`.
2. Pass them to controls during `build` for automatic binding.
3. In `bind_runtime`, subscribe to sibling features' observables using `.subscribe(callback)`.
4. Store subscription handles; dispose them in `shutdown_runtime`.
5. Write to observables from event handlers, `on_update`, or background coroutines.
6. For application-wide state, use `AppStateStore` with `StateSelector` for derived slices.

#### Minimal example

```python
from gui_do import ObservableValue, ObservableList, reactive_batch, ComputedValue

# Simple reactive value
score = ObservableValue(0)
handle = score.subscribe(lambda v: print(f"Score: {v}"))
score.set(42)          # prints "Score: 42"
score.unsubscribe(handle)

# Derived value via ComputedValue
display_text = ComputedValue(score, lambda s: f"Score: {s:,}")
# display_text.get() → "Score: 42"

# Reactive list
items = ObservableList()
items.subscribe(lambda change: print(f"Changed: {change.kind}"))
items.append("item_a")  # fires subscriber

# Atomic batch update
x = ObservableValue(0)
y = ObservableValue(0)
with reactive_batch():
    x.set(10)
    y.set(20)
# both subscribers fire once after the block exits
```

#### Advanced pattern: AppStateStore with selectors and transactions

`AppStateStore` provides a Redux-style central state store for application-wide data. Selectors
derive computed values; transactions batch updates atomically:

```python
from gui_do import AppStateStore, StateSelector, StateTransaction

store = AppStateStore({"score": 0, "level": 1})

score_selector = StateSelector(store, lambda s: s["score"])
score_selector.subscribe(lambda v: print(f"Score changed to {v}"))

with StateTransaction(store) as tx:
    tx.set("score", 100)
    tx.set("level", 2)
# score_selector and any "level" selectors fire once after transaction
```

`CollectionView` provides a live filtered/sorted view over an `ObservableList` using a
`CollectionViewQuery`. The view updates automatically when the source list changes and applies
the filter/sort without modifying the source:

```python
from gui_do import ObservableList, CollectionView, CollectionViewQuery

raw = ObservableList([3, 1, 4, 1, 5, 9, 2])
view = CollectionView(raw, CollectionViewQuery(sort_key=lambda x: x, filter_fn=lambda x: x > 2))
# view contains [3, 4, 5, 9], sorted, filtered live
```

#### Common mistakes and anti-patterns

- **Polling `.get()` in `on_update`** — this burns CPU every frame and introduces one-frame
  display latency. Subscribe once and update the UI in the callback.
- **Subscribing in `build`** — at `build` time, sibling features may not have been built yet.
  Observable subscriptions that depend on sibling state must be created in `bind_runtime`.
- **Not disposing subscriptions in `shutdown_runtime`** — undisposed subscriptions prevent the
  feature from being garbage-collected and cause callbacks to fire on destroyed objects.
- **Sharing mutable plain Python `list` or `dict` across features** — plain collections have no
  notification mechanism. Use `ObservableList` and `ObservableDict` whenever a collection is
  shared between features and one feature must react to changes made by another.
- **Using `StateTransaction` for local-only state** — `AppStateStore` and `StateTransaction`
  are for application-wide shared state. For state that is local to a single feature, plain
  `ObservableValue` instances are more appropriate and carry less overhead.

#### Cross-links to related systems

- §8.2 Feature Lifecycle — observables are created in `build`, subscribed in `bind_runtime`
- §8.5 Controls — controls accept observables for reactive data binding
- §8.11 Persistence — `WorkspacePersistenceManager` saves and restores application state
- §8.14 Data and Dataflow Helpers — `CollectionView`, `SortFilterProxySource`, and `DataflowPipeline` extend the observable model for data-intensive scenarios

[Back to Table of Contents](#table-of-contents)

---


### 8.5 Controls and Control Composition

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Controls are the reusable visual and interactive primitives that features compose to build
their UI. They handle their own rendering, hit-testing, and event dispatch within the control
tree. By using controls rather than drawing directly to the screen surface, features benefit
from the framework's layout engine, focus system, accessibility tree, and theme system — all
without any additional work. A feature creates controls in `build`, configures them in
`bind_runtime`, and lets the framework drive rendering from that point on.

The control system is organized into two tiers: primary controls (Tier 12) cover the
essential building blocks for any interactive UI, and extended controls (Tier 13) provide
specialized components for richer interfaces.

#### Mental model and lifecycle placement

Controls are children of panels which are children of scene roots. A feature owns one root
`PanelControl` (or a `WindowPresenter` that owns the panel). Every control a feature creates
lives inside that root panel. Controls from different features never share parent panels —
cross-feature interactions go through observables and messages, not direct control references.
Controls are created once during `build` and persist for the scene's lifetime.

#### Primary public APIs and key types

From **Tier 12** (Primary Controls):
- `PanelControl` — container for other controls; the standard root element
- `LabelControl` — static or dynamic text display
- `ButtonControl` — clickable button with optional icon and label
- `ToggleControl` — boolean on/off control
- `SliderControl` — continuous value selection along an axis
- `ScrollbarControl` — scroll position indicator and drag handle
- `CanvasControl`, `CanvasEventPacket` — raw drawing surface with pointer event support
- `CanvasViewport` — scrollable/zoomable wrapper around `CanvasControl`
- `FrameControl` — bordered container; provides visual grouping
- `ImageControl` — displays a pygame surface or loaded image asset
- `ArrowBoxControl` — a box with a directional arrow indicator
- `ButtonGroupControl` — mutually exclusive button selection group
- `TabControl`, `TabItem` — tabbed panel switcher
- `DockWorkspacePanel` — panel embedding a `DockWorkspace` layout

From **Tier 13** (Extended Controls):
- `TextInputControl` — single-line text entry with cursor and selection
- `TextAreaControl` — multi-line text editing area
- `RichLabelControl` — text label with inline markup and mixed styling
- `DropdownControl`, `DropdownOption` — collapsible option picker
- `ListViewControl`, `ListItem` — virtualized scrollable item list
- `OverlayPanelControl` — panel that renders as a floating overlay layer
- `DataGridControl`, `GridColumn`, `GridRow` — tabular data display with sortable columns
- `TreeControl`, `TreeNode` — hierarchical expandable item tree
- `SplitterControl` — resizable split between two child panels
- `SpinnerControl` — numeric value spinner with increment/decrement
- `RangeSliderControl` — dual-handle range selection slider
- `ColorPickerControl` — interactive color selection widget
- `ScrollViewControl` — scrollable container with automatic scrollbars
- `ProgressBarControl` — linear progress indicator
- `AnimatedImageControl` — animated image display with frame control
- `ErrorBoundary` — renders a fallback if child controls raise during render or event handling
- `WindowControl` — chrome control for a floating draggable/resizable window
- `TaskPanelControl` — chrome control for the scene's task panel
- `WindowPresenter` — base class for window-level UI construction; subclass for custom windows
- `MenuBarControl`, `MenuEntry` — horizontal menu bar with drop-down menus
- `SceneMenuStripControl` — scene-level navigation menu strip
- `NotificationPanelControl` — inline notification display panel
- `PropertyInspectorPanel` — auto-generated property inspector from `PropertyRegistry`
- `ToolbarControl`, `ToolbarItem` — horizontal toolbar with icon buttons
- `StatusBarControl`, `StatusSlot` — bottom-of-window status bar with labeled slots
- `ExpanderControl` — collapsible section with toggle header
- `DatePickerControl` — calendar-based date selection
- `TimePickerControl` — time-of-day selection
- `BreadcrumbControl`, `BreadcrumbItem` — hierarchical path navigation
- `SplitButtonControl`, `SplitButtonOption` — button with drop-down secondary actions
- `ChipInputControl` — tag entry with removable chips

From **Tier 1** (spec-driven control helpers):
- `ControlDefinition` — declarative descriptor for a control spec
- `build_specs_from_column_section` — builds control specs from a column-based section layout

#### Typical usage flow

1. In `build(host)`, create a root `PanelControl` and register it with the scene via
   `host.app.add_control(root, scene_name="main")` or equivalent.
2. Add child controls to the root using `root.add(child_control)`.
3. In `bind_runtime(host)`, subscribe to observables and bind callbacks to control event
   handlers (e.g., `button.on_click = self._handle_click`).
4. Let the framework drive rendering — do not call render methods manually.

#### Minimal example

```python
import pygame
from gui_do import Feature, PanelControl, LabelControl, ButtonControl, ObservableValue

class CounterFeature(Feature):
    HOST_REQUIREMENTS = {
        "build": ("app", "screen_rect", "controls"),
        "bind_runtime": ("app",),
    }

    def build(self, host):
        self._count = ObservableValue(0)
        root = PanelControl(rect=pygame.Rect(50, 50, 300, 120))
        self._label = LabelControl(
            rect=pygame.Rect(8, 8, 284, 30),
            text="Count: 0",
        )
        btn = ButtonControl(
            rect=pygame.Rect(8, 50, 120, 32),
            label="Increment",
            on_click=lambda e: self._count.set(self._count.get() + 1),
        )
        root.add(self._label)
        root.add(btn)
        host.controls.add(root)

    def bind_runtime(self, host):
        self._sub = self._count.subscribe(
            lambda v: self._label.set_text(f"Count: {v}")
        )

    def shutdown_runtime(self, host):
        self._count.unsubscribe(self._sub)
```

#### Advanced pattern: WindowPresenter for floating windows

`WindowPresenter` is the recommended pattern for features with floating, toggle-able windows.
Subclass it to own window layout, then instantiate it in the feature's `build`:

```python
from gui_do import WindowPresenter, LabelControl, PanelControl

class InspectorPresenter(WindowPresenter):
    def build(self, host, window_rect):
        panel = PanelControl(rect=window_rect)
        panel.add(LabelControl(rect=..., text="Inspector"))
        return panel

class InspectorFeature(Feature):
    HOST_REQUIREMENTS = {"build": ("app", "screen_rect"), "bind_runtime": ("app",)}

    def build(self, host):
        from my_app.inspector_presenter import InspectorPresenter
        self._presenter = InspectorPresenter()
        self._presenter.build(host, window_rect=pygame.Rect(200, 100, 400, 500))
```

Combine with `TabbedPresenterSpec` and `TabBuilderSpec` for multi-tab window content.
`ErrorBoundary` wraps subtrees that may throw during rendering, rendering a fallback instead
of crashing the frame.

#### Common mistakes and anti-patterns

- **Direct cross-feature control references** — one feature holding a reference to another
  feature's control creates hidden coupling. Share data via observables; let each feature
  manage its own controls.
- **Using controls as state** — a label's displayed text is not the source of truth for the
  underlying value. Observable values own the state; controls mirror it.
- **Creating controls outside `build`** — controls created in `bind_runtime`, `on_update`, or
  event handlers miss the initial layout pass and may not be correctly registered with the
  focus and hit-testing systems.
- **Not adding a root to the scene** — a `PanelControl` created but not added to the scene
  via the host's control registration will never be rendered or receive events.

#### Cross-links to related systems

- §8.2 Feature Lifecycle — controls are created in `build`
- §8.6 Layout Systems — controls are positioned by layout engines
- §8.7 Focus and Accessibility — controls participate in the focus ring and accessibility tree
- §8.9 Scene, Window, and Task-Panel Presentation Models — `WindowPresenter` and window chrome

[Back to Table of Contents](#table-of-contents)

---

### 8.6 Layout Systems

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

`gui_do` provides multiple layout engines because no single algorithm is optimal for all use
cases. A toolbar has different spatial requirements than a data grid, which has different
requirements than a responsive dialog that rearranges at narrow widths. Rather than exposing
one general-purpose layout engine that requires complex configuration for every case, the
framework provides a family of engines, each optimized for a specific spatial pattern. The
developer chooses the simplest engine that covers the spatial requirement, keeping configuration
minimal and readable.

Layout engines exist in the framework because hardcoded pixel positions produce interfaces that
break on window resize, on different DPI settings, and on dynamic content changes. Layout
engines compute positions deterministically from constraints, ensuring the interface adapts
correctly.

#### Mental model and lifecycle placement

Layout runs as a pass triggered by `LayoutManager` during the frame cycle — after controls
are built and before drawing. Features create layout objects during `build` and register them
with their root panel. The layout pass then measures and arranges all registered controls
according to the engine's constraints. Changing a layout constraint after initial layout
triggers a re-layout on the next frame.

#### Primary public APIs and key types

From **Tier 8** (Layout & Spatial):
- `LayoutAxis` — axis enum (horizontal/vertical) used by flex and flow layouts
- `LayoutManager` — manages layout passes for a scene's control tree
- `WindowTilingManager` — arranges floating windows in tiling mode (split, cascade, fill)
- `ConstraintLayout`, `AnchorConstraint` — anchor-based relationships between controls
- `DockPane`, `DockTabs`, `DockSplit`, `DockWorkspace` — workbench-style multi-pane dock layout
- `FlexLayout`, `FlexItem`, `FlexDirection`, `FlexAlign`, `FlexJustify` — flexbox-style row/column layout
- `GridLayout`, `GridTrack`, `GridPlacement` — fixed-track grid layout with spanning
- `CellCaretLayout`, `CellCaretState` — cell-by-cell caret navigation for grid-style editors
- `LayoutAnimator` — animates layout transitions when constraints change
- `LayoutPass`, `MeasureContext`, `ArrangeContext`, `LayoutRoot` — low-level layout pass primitives for custom engines
- `ResponsiveLayout`, `Breakpoint` — selects a layout policy based on a width breakpoint
- `SnapGrid`, `AlignmentGuide`, `SnapComposer`, `SnapTarget` — snap-to-grid alignment for drag-placed controls
- `FlowLayout`, `FlowItem` — wrapping flow layout for tag/chip collections
- `Viewport` — scrollable/zoomable view over a larger content area

From **Tier 28** (Adaptive Constraint Layout v2):
- `ConstraintAttr` — attribute enum for constraint anchors (left, right, top, bottom, centerX, centerY, width, height)
- `LayoutConstraint` — declarative constraint between two control attributes
- `ConstraintSet` — collection of constraints for a layout scope
- `ConstraintLayoutEngine` — priority-based constraint solver; resolves conflicting constraints by priority
- `AdaptivePolicy` — breakpoint-aware constraint policy selection
- `resolve_adaptive_policy` — selects the appropriate `ConstraintSet` for a given viewport width

From **Tier 29** (Unified Virtualization Core):
- `MeasureMode` — enum for measurement semantics
- `MeasurePolicy` — specifies how items are measured in the virtualized window
- `VirtualizedWindow` — windowing structure for a virtualized list/tree/grid
- `RecyclePool` — recycles control instances for re-use across item scroll positions
- `VirtualizationCore` — manages windowing, recycling, and identity tracking for large collections

#### Typical usage flow

**FlexLayout (recommended for toolbars and panels):**
```python
from gui_do import FlexLayout, FlexItem, FlexDirection

layout = FlexLayout(direction=FlexDirection.ROW, gap=8)
layout.add(FlexItem(control=sidebar_panel, grow=0, basis=200))
layout.add(FlexItem(control=main_panel, grow=1))
root_panel.set_layout(layout)
```

**GridLayout (recommended for forms and data grids):**
```python
from gui_do import GridLayout, GridTrack, GridPlacement

grid = GridLayout(
    columns=[GridTrack(size=120), GridTrack(grow=1)],
    rows=[GridTrack(size=32), GridTrack(size=32)],
    gap=4,
)
grid.place(label_control, GridPlacement(row=0, column=0))
grid.place(field_control, GridPlacement(row=0, column=1))
root_panel.set_layout(grid)
```

#### Minimal example

```python
from gui_do import FlexLayout, FlexItem, FlexDirection, PanelControl, LabelControl, ButtonControl
import pygame

def build(self, host):
    root = PanelControl(rect=pygame.Rect(0, 0, 600, 400))
    sidebar = PanelControl(rect=pygame.Rect(0, 0, 200, 400))
    content = PanelControl(rect=pygame.Rect(0, 0, 400, 400))
    layout = FlexLayout(direction=FlexDirection.ROW, gap=0)
    layout.add(FlexItem(control=sidebar, grow=0, basis=200))
    layout.add(FlexItem(control=content, grow=1))
    root.set_layout(layout)
    root.add(sidebar)
    root.add(content)
    host.controls.add(root)
```

#### Advanced pattern: adaptive constraint layout with breakpoints

`ConstraintLayoutEngine` with `AdaptivePolicy` for responsive rearrangement:

```python
from gui_do import ConstraintLayoutEngine, ConstraintSet, LayoutConstraint, ConstraintAttr, AdaptivePolicy, resolve_adaptive_policy

wide_constraints = ConstraintSet([
    LayoutConstraint(ConstraintAttr.LEFT, sidebar, ConstraintAttr.RIGHT),
])
narrow_constraints = ConstraintSet([
    LayoutConstraint(ConstraintAttr.TOP, sidebar, ConstraintAttr.BOTTOM),
])
policy = AdaptivePolicy(
    breakpoints={600: wide_constraints, 0: narrow_constraints}
)
active = resolve_adaptive_policy(policy, viewport_width=800)
engine = ConstraintLayoutEngine(active)
```

`VirtualizationCore` with `RecyclePool` enables O(visible rows) rendering of lists with
thousands of items by reusing control instances as they scroll in and out of the viewport.

#### Common mistakes and anti-patterns

- **Mixing conflicting layout systems in one container** — a panel can have one active layout
  engine. Applying both `FlexLayout` and `GridLayout` to the same panel produces undefined results.
- **Hardcoding pixel positions where responsive layout is needed** — if the window is resizable,
  fixed positions break. Use a layout engine instead.
- **Calling layout APIs before controls are added to the container** — layout is computed at
  the layout pass, but controls must be registered with the panel before the pass runs.

#### Cross-links to related systems

- §8.5 Controls — layouts position controls
- §8.7 Focus — layout order affects focus cycling order
- §8.9 Window presentation — window chrome uses layout engines internally

[Back to Table of Contents](#table-of-contents)

---

### 8.7 Focus and Accessibility

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Keyboard focus is the mechanism by which the framework routes keyboard events to the correct
control. Without a focus system, every control would need to check whether it is the intended
recipient for every key event — an O(n) problem that also requires controls to know about
each other. The focus system solves this by maintaining a single focused control at all times
and delivering keyboard events only to that control's subtree, plus any global bindings.

The accessibility system provides a parallel semantic tree that mirrors the control tree in
a machine-readable format. This enables testing tools, diagnostic inspectors, and assistive
technology integrations to traverse the application's UI without parsing pixel data.

#### Mental model and lifecycle placement

`FocusManager` is the single source of truth for which control holds focus. Controls join
the focus ring during `build`; the ring is an ordered cycle that Tab and Shift+Tab navigate.
`FocusScopeManager` allows focus to be locked to a subtree — for example, to keep focus
inside a modal dialog while it is open. When the dialog closes, the lock is released and
focus returns to its previous position.

Accessibility nodes are created during `build` alongside their corresponding controls, and
removed during teardown. The `AccessibilityBus` delivers announcements for live-region
changes — for example, when a status label updates to reflect a completed operation.

#### Primary public APIs and key types

From **Tier 4** (Focus):
- `FocusManager` — tracks the currently focused control; provides `set_focus`, `clear_focus`, `get_focused`
- `FocusScope` — named focus group; groups controls for Tab-order scoping
- `FocusScopeManager` — manages multiple `FocusScope` instances; locks/unlocks scope on demand
- `WindowFocusManager` — manages focus cycling between floating windows (Alt+Tab style)
- `FocusRing` — ordered cycle of focusable controls; wraps around at ends

From **Tier 21** (Accessibility):
- `AccessibilityRole` — enum: BUTTON, LABEL, TEXT_INPUT, CHECKBOX, SLIDER, PANEL, DIALOG, MENU, LIST, etc.
- `LivePoliteness` — enum for live-region announcement priority: OFF, POLITE, ASSERTIVE
- `AccessibilityNode` — semantic node with role, name, description, live politeness, and child nodes
- `AccessibilityTree` — the root tree structure; provides traversal and lookup
- `AccessibilityAnnouncement` — an event emitted when a live-region node changes
- `AccessibilityBus` — pub/sub bus for `AccessibilityAnnouncement` events

From **Tier 1** (spec types):
- `StaticAccessibilitySpec` — declarative accessibility annotation for a host-level control
- `AccessibilitySequenceSpec` — declares the full sequential focus order for a scene
- `TaskPanelFocusToggleSpec` — automatically excludes a window's controls from the focus ring when the window is hidden

#### Typical usage flow

1. During `build`, add accessibility nodes to the `AccessibilityTree` for custom controls
   that are not automatically annotated by the control base class.
2. Declare `StaticAccessibilitySpec` entries in `HostApplicationBindingSpec` for top-level
   controls that need accessibility labels.
3. Use `AccessibilitySequenceSpec` to specify the full Tab order for a scene.
4. For modal dialogs, use `FocusScopeManager.lock(scope)` when the dialog opens and
   `FocusScopeManager.unlock()` when it closes.
5. Use `TaskPanelFocusToggleSpec` in `RoutedRuntimeSpec` to automatically manage focus
   exclusion for task-panel-toggled windows.

#### Minimal example

```python
from gui_do import AccessibilityTree, AccessibilityNode, AccessibilityRole

def build(self, host):
    # ... create controls ...
    tree = AccessibilityTree()
    node = AccessibilityNode(
        role=AccessibilityRole.BUTTON,
        name="Submit Form",
        description="Submits the current form values",
    )
    tree.root.add_child(node)
    host.app.set_accessibility_tree(tree)
```

#### Advanced pattern: modal focus locking and live announcements

```python
from gui_do import FocusScopeManager, FocusScope, AccessibilityBus, AccessibilityAnnouncement, LivePoliteness

# Lock focus to dialog scope on open
scope_manager = FocusScopeManager()
dialog_scope = FocusScope("dialog")
scope_manager.lock(dialog_scope)

# Announce a live-region change
bus = AccessibilityBus()
bus.announce(AccessibilityAnnouncement(
    message="Operation complete",
    politeness=LivePoliteness.POLITE,
))
```

#### Common mistakes and anti-patterns

- **Window controls still in focus ring when window is hidden** — if a floating window is
  hidden via task panel toggle but its controls remain in the focus ring, Tab navigation
  will stall invisibly. Use `TaskPanelFocusToggleSpec` to handle this automatically.
- **Missing semantic roles on custom canvas widgets** — `CanvasControl` is opaque to the
  accessibility tree. If you build interactive content on a canvas, create corresponding
  `AccessibilityNode` entries manually.
- **Building accessibility nodes before the tree is initialized** — accessibility trees are
  initialized during bootstrap. Create nodes in `build`, not in `__init__`.

#### Cross-links to related systems

- §8.3 Events — focus state determines which feature receives keyboard events
- §8.5 Controls — controls register with the focus ring during `build`
- §8.8 Overlays — modal dialogs lock the focus scope
- §8.9 Window presentation — `WindowFocusManager` handles inter-window focus

For field-level reference for `StaticAccessibilitySpec` and `AccessibilitySequenceSpec`, see
[Appendix F: Specifications and Option Reference](#appendix-f-specifications-and-option-reference).

[Back to Table of Contents](#table-of-contents)

---

### 8.8 Overlays, Dialogs, Notifications, and Command Surfaces

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Transient and modal surfaces — dialogs, toast notifications, context menus, tooltips, the
command palette, shortcut help overlays — need their own event routing layer so they do not
destabilize the main control tree's event flow. A modal dialog must intercept all keyboard and
mouse input while it is open; a toast notification must not intercept any input. A context
menu must dismiss when the user clicks outside it. Each of these behaviors requires a different
routing contract, and mixing them into the main control tree would make the main tree's routing
logic exponentially more complex.

`gui_do` addresses this by providing a family of overlay managers, each responsible for one
surface kind and one dismissal contract. Features use the managers through their host-provided
handles; the managers handle routing, z-ordering, and cleanup.

#### Mental model and lifecycle placement

Overlay managers sit above the main control tree in the event routing order. When an overlay
is active, events pass through the overlay's routing layer first. If the overlay consumes an
event, the main tree never sees it. Different overlay types intercept different event sets:
modal dialogs consume all input; toasts consume only clicks within their bounds; tooltips
consume no input.

Overlay managers are available on the host after bootstrap and are used from `build`,
`bind_runtime`, and event handlers — wherever the feature needs to show or update a surface.

#### Primary public APIs and key types

From **Tier 9** (Overlay Managers & Windows):
- `OverlayManager`, `OverlayHandle` — generic overlay placement with configurable event interception
- `Alignment`, `PlacementResult`, `PopupPlacement`, `Side`, `compute_popup_rect` — popup anchor and placement utilities
- `DialogManager`, `DialogHandle` — modal and non-modal dialog surfaces
- `ToastManager`, `ToastHandle`, `ToastSeverity` — transient notification banners (INFO, SUCCESS, WARNING, ERROR)
- `ContextMenuManager`, `ContextMenuItem`, `ContextMenuHandle` — right-click context menus with dismissal
- `CommandPaletteManager`, `CommandEntry`, `CommandPaletteHandle` — searchable command palette
- `TooltipManager`, `TooltipHandle` — hover-dwell tooltips with configurable delay
- `MenuBarManager` — drop-down menu bar management
- `FileDialogManager`, `FileDialogOptions`, `FileDialogHandle` — native file open/save dialogs
- `NotificationCenter`, `NotificationRecord` — persistent notification log
- `ResizeManager` — manages resize handles on floating windows
- `CursorManager`, `CursorHandle`, `CursorShape` — cursor shape management with stacking
- `DragDropManager`, `DragPayload` — drag-and-drop source/target coordination
- `ClipboardManager` — clipboard read/write
- `TransferData`, `TransferManager` — typed data transfer between controls
- `ShortcutHelpOverlay`, `ShortcutSection`, `ShortcutEntry` — full-screen/partial shortcut reference overlay

From **Tier 1** (spec types):
- `ShortcutOverlaySpec` — configuration for shortcut help overlay behavior
- `NotificationSpec` — declarative notification entry for the notification center

#### Typical usage flow

**Toast notification:**
```python
host.toast_manager.show("File saved!", severity=ToastSeverity.SUCCESS)
```

**Modal dialog:**
```python
dialog_control = MyDialogControl(rect=pygame.Rect(200, 150, 400, 300))
handle = host.dialog_manager.show(dialog_control, modal=True)
handle.on_dismiss = lambda: self._on_dialog_closed()
```

**Context menu:**
```python
items = [
    ContextMenuItem("cut", "Cut", on_select=self._cut),
    ContextMenuItem("copy", "Copy", on_select=self._copy),
    ContextMenuItem("paste", "Paste", on_select=self._paste),
]
host.context_menu_manager.show(items, anchor=event.pos)
```

#### Minimal example

```python
from gui_do import Feature, ButtonControl, ToastSeverity
import pygame

class NotificationFeature(Feature):
    HOST_REQUIREMENTS = {
        "build": ("app", "screen_rect", "controls", "toast_manager"),
        "bind_runtime": ("app",),
    }

    def build(self, host):
        btn = ButtonControl(
            rect=pygame.Rect(20, 20, 140, 32),
            label="Show Toast",
            on_click=lambda e: host.toast_manager.show(
                "Operation complete!",
                severity=ToastSeverity.SUCCESS,
            ),
        )
        host.controls.add(btn)

    def bind_runtime(self, host):
        pass
```

#### Advanced pattern: shortcut help overlay with manual sections

`ShortcutHelpOverlay` renders the action registry's shortcuts alongside manually declared
sections. Configure via `ShortcutOverlaySpec` in `RoutedRuntimeSpec`:

```python
from gui_do import ShortcutOverlaySpec, ShortcutSection, ShortcutEntry

shortcut_overlay=ShortcutOverlaySpec(
    activation_key=pygame.K_F1,
    manual_sections=[
        ShortcutSection(
            title="Navigation",
            entries=[
                ShortcutEntry(label="Next Scene", key_display="Ctrl+Tab"),
                ShortcutEntry(label="Previous Scene", key_display="Ctrl+Shift+Tab"),
            ],
        ),
    ],
    exclude_section_titles=["Debug"],
)
```

`CommandPaletteManager` can be populated with dynamic `CommandEntry` values from a callable,
allowing the palette to reflect the current application state (e.g., recently opened files,
active window names) without rebuilding the spec:

```python
from gui_do import CommandEntry

def get_recent_entries():
    return [
        CommandEntry(id=f"recent_{i}", label=path, on_select=lambda p=path: self._open(p))
        for i, path in enumerate(self._recent_files)
    ]
# Pass get_recent_entries as the custom_entries_provider in PaletteBindingSpec
```

#### Common mistakes and anti-patterns

- **Overlay without a dismissal contract** — if a user cannot close an overlay, they are
  stuck. Always provide at least one reliable dismissal path (Escape, button, outside click).
- **Expecting toast clicks to pass through to underlying controls** — `ToastManager` consumes
  clicks within the toast rect. Do not place interactive UI under a toast.
- **Using `OverlayHandle` after the overlay is dismissed** — check that the handle is still
  valid before calling methods on it. A dismissed overlay's handle is invalidated.
- **Showing a dialog without a host reference in scope** — dialog handles deliver callbacks
  asynchronously; ensure the feature that shows the dialog is still alive when callbacks fire.

#### Cross-links to related systems

- §8.3 Events — overlays intercept events before features
- §8.7 Focus — modal dialogs lock the focus scope via `FocusScopeManager`
- §8.9 Scene, Window, and Task-Panel Presentation Models — command palette is declared per-scene

For field-level reference for `NotificationSpec`, `FileDialogOptions`, `CursorSpec`, and overlay specs, see
[Appendix F: Specifications and Option Reference](#appendix-f-specifications-and-option-reference).

[Back to Table of Contents](#table-of-contents)

---


### 8.9 Scene, Window, and Task-Panel Presentation Models

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Scenes are the top-level interaction contexts of a `gui_do` application. Each scene is a
named configuration of features, windows, and chrome elements that is activated as a unit
and deactivated as a unit during scene transitions. Within a scene, windows are floating or
docked UI surfaces that can be individually shown and hidden. The task panel is a persistent
chrome element at the edge of the screen that houses toggle buttons for windows and provides
scene-navigation access. Menu strips expose scene navigation and window visibility commands
through a familiar horizontal menu.

This system exists because different phases of an application's workflow often require
completely different UI configurations. A "settings" scene, a "main workspace" scene, and an
"onboarding" scene each have entirely different feature layouts, window arrangements, and
available commands. By making scenes a first-class concept, `gui_do` allows each configuration
to be independently specified, tested, and transitioned between with smooth animations.

#### Mental model and lifecycle placement

Think of scenes as top-level "modes." Each mode is a named collection of features and their
associated windows, chrome, and actions. When the active scene changes, the departing scene's
features are deactivated and the arriving scene's features are activated and built fresh (or
restored from a prewarm cache). Windows are registered within scenes and track their own
visibility state through `ScenePresentationModel`.

The task panel and scene menu strip are optional per-scene chrome elements. They are declared
in the spec and built during the scene's activation phase. The `ScenePresentationModel` object
coordinates window visibility state across the task panel toggle buttons, the scene menu strip's
Windows section, and the command palette's window entries.

#### Primary public APIs and key types

From **Tier 1** (spec types relevant to scene/window presentation):
- `ScenePresentationModel` — tracks registered windows and their visibility state per scene
- `WindowSpec` — declarative descriptor for a feature's floating window
- `AnchoredWindowSpec` — window with a fixed anchor point and size
- `SceneTaskPanelSpec` — declares a scene's task panel chrome element
- `TaskPanelButtonSpec` — a single button entry in the task panel
- `TaskPanelWindowToggleGroupSpec` — a group of auto-generated window toggle buttons
- `TaskPanelFocusToggleSpec` — auto-manages focus exclusion when a window is hidden
- `TaskPanelSceneNavButtonSpec` — a scene-navigation button in the task panel
- `TabbedPresenterSpec` — specifies tabbed content inside a window
- `TabBuilderSpec` — factory spec for one tab's control tree
- `FeatureWindowBundleBindingSpec` — bundles a feature with its managed window and task panel button
- `WindowToggleBindingSpec` — binding for a window visibility toggle action
- `SceneMenuStripSpec` — declares a scene's menu strip chrome element

From **Tier 18** (advanced presentation helpers):
- `set_window_visible_state` — programmatically show or hide a window
- `toggle_window_visibility` — toggle a window's current visibility
- `create_anchored_feature_window` — creates a floating anchored window for a feature
- `create_feature_presented_window` — creates a window using a `WindowPresenter` subclass
- `add_window_scene_menu_strip` — adds a menu strip entry for a window
- `ensure_scene_task_panel` — initializes the task panel for the current scene
- `add_task_panel_buttons` — registers buttons with the task panel
- `add_task_panel_window_toggle_group` — registers the auto-toggle-button group
- `add_task_panel_scene_nav_button` — adds a scene navigation button to the task panel
- `add_window_toggle_task_panel_controls` — wires window visibility to task panel controls
- `ActiveTabUpdateRouter` — routes updates only to the active tab's presenter efficiently
- `TabLayoutContext` — provides layout context for tabbed window content
- `setup_routed_runtime`, `shutdown_routed_runtime` — wire and unwire the full `RoutedRuntimeSpec`
- `setup_routed_feature_runtime`, `register_routed_feature_companions` — per-feature routed wiring

#### Typical usage flow

1. Declare `SceneBundleBindingSpec` entries in `HostApplicationBindingSpec` for each scene.
2. For features with managed windows, use `FeatureWindowBundleBindingSpec` instead of
   plain `feature_entries`.
3. If the scene needs a task panel, declare `SceneTaskPanelSpec` and use
   `ensure_scene_task_panel` in the feature's `build`.
4. For tabbed windows, declare `TabbedPresenterSpec` with `TabBuilderSpec` factories.
5. Use `TaskPanelFocusToggleSpec` in `RoutedRuntimeSpec` to auto-manage focus on toggle.
6. Optionally declare a `SceneMenuStripSpec` for scene navigation and window menu access.

#### Minimal example

```python
from gui_do import (
    HostApplicationBindingSpec,
    FeatureWindowBundleBindingSpec,
    SceneBundleBindingSpec,
    build_host_application_config,
    bootstrap_host_application,
)
from my_app.inspector_feature import InspectorFeature

config = build_host_application_config(
    HostApplicationBindingSpec(
        display_size=(1280, 720),
        window_title="My App",
        initial_scene_name="main",
        fonts={"default": {"file": "assets/Body.ttf", "size": 14}},
        scene_bundle_entries=(
            SceneBundleBindingSpec(scene_name="main", pretty_name="Main"),
        ),
        feature_window_bundle_entries=(
            FeatureWindowBundleBindingSpec(
                "_inspector",
                InspectorFeature,
                "inspector",
                task_panel_label="Inspector",
                task_panel_style="round",
            ),
        ),
    )
)
bootstrap_host_application(config)
```

#### Advanced pattern: tabbed windows with ActiveTabUpdateRouter

For windows with multiple tabs where only the active tab should receive updates:

```python
from gui_do import TabbedPresenterSpec, TabBuilderSpec, ActiveTabUpdateRouter

TABBED_SPEC = TabbedPresenterSpec(
    tabs=[
        TabBuilderSpec(tab_id="overview", label="Overview", factory=OverviewPresenter),
        TabBuilderSpec(tab_id="details", label="Details", factory=DetailsPresenter),
    ],
)
# ActiveTabUpdateRouter routes on_update calls only to the active tab's presenter,
# avoiding unnecessary computation in hidden tabs.
```

`ScenePresentationModel.handle_window_toggle` coordinates the task panel button and the scene
menu strip's Windows section when `connect_window_presentation=True` in `PaletteBindingSpec`.

#### Common mistakes and anti-patterns

- **Mismatching scene scope for action handlers** — an action declared as scene-scoped will
  not fire when a different scene is active. Verify that action scope matches the intended
  triggering scene.
- **Not synchronizing task panel button state with window visibility** — if you show/hide a
  window programmatically via `set_window_visible_state`, ensure the task panel button's
  toggle state is updated via `ScenePresentationModel`.
- **Creating window controls in `bind_runtime`** — window controls must be created in `build`
  so that sibling features can access them during their own `bind_runtime` phase.

#### Cross-links to related systems

- §8.2 Feature Lifecycle — scenes activate and deactivate features
- §8.5 Controls — `WindowControl` and `TaskPanelControl` are Tier 13 controls
- §8.7 Focus — `TaskPanelFocusToggleSpec` manages focus ring membership
- §8.8 Overlays — command palette integration via `SceneCommandPaletteSpec`

For field-level reference for `WindowSpec`, `AnchoredWindowSpec`, `SceneTaskPanelSpec`,
`TaskPanelFocusToggleSpec`, and presentation specs, see
[Appendix F: Specifications and Option Reference](#appendix-f-specifications-and-option-reference).

[Back to Table of Contents](#table-of-contents)

---

### 8.10 Scheduling, Timing, Animation, and Transitions

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

GUI applications must execute time-based work — animations, timed callbacks, multi-step
workflows — without blocking the main thread or disrupting the frame budget. `gui_do` provides
a layered scheduling system that spans the full range from simple one-shot timers up to full
cooperative coroutine scheduling. Each layer is designed to match a specific use case: tweens
for value interpolation, `AnimationStateMachine` for state-driven animations, `SceneTimeline`
for scripted sequences, and `CooperativeScheduler` for general multi-step workflows.

All of these systems respect the frame budget. The scheduler has a contractual budget:
`fraction = 0.12` of `dt_ms`, clamped to a `floor = 0.5 ms` and a `ceiling = 4.0 ms`. This
ensures that scheduling work cannot starve rendering under slow frames or over-allocate under
fast frames. The contract is enforced by `tests/test_runtime_operating_contracts.py`.

#### Mental model and lifecycle placement

Think of the scheduling layer as a time-sliced cooperative multitasking system embedded in
the frame loop. Each frame, the scheduler is given a budget slice and runs as many pending
tasks as fit. Tasks that exceed the budget are resumed on the next frame. This is the
mechanism that allows long-running workflows to proceed incrementally without ever blocking
the UI thread.

Tweens, animations, and timers register themselves with the appropriate manager in `build` or
`bind_runtime` and are ticked automatically by the framework on each frame. Features do not
need to drive them manually from `on_update` — they only need to register and configure them.

#### Primary public APIs and key types

From **Tier 5** (Scheduling & Animation):
- `TaskEvent`, `TaskScheduler` — per-scene message dispatch scheduler with budget clamping
- `Timers` — one-shot and repeating timer callbacks; automatically ticked each frame
- `TweenManager`, `TweenHandle`, `Easing` — property interpolation with easing functions
- `AnimationSequence`, `AnimationHandle` — sequence of timed animation steps
- `TransitionManager`, `TransitionSpec`, `TransitionEvent` — scene and value transition coordination
- `AnimationStateMachine`, `AnimationTransitionMode` — state-machine-driven animation control
- `SceneTimeline` — scripted event sequence relative to scene entry time
- `Debouncer`, `Throttler` — rate-limiting for high-frequency callbacks
- `CooperativeScheduler`, `CoroutineHandle` — frame-budgeted cooperative coroutine runner
- `Pause`, `Sleep`, `WaitForEvent`, `WaitForSignal`, `WaitUntil`, `WaitForAll` — yield primitives for `CooperativeScheduler` coroutines

From **Tier 26** (Cancelable Dataflow Pipeline):
- `CancellationToken`, `PipelineStage`, `DataflowPipeline`, `PipelineHandle` — multi-stage
  cancelable async processing pipeline (also see §8.14 Data and Dataflow Helpers)

#### Typical usage flow

**Tween (value interpolation):**
```python
# In bind_runtime:
handle = host.tween_manager.to(self.panel, "alpha", target=255, duration=0.3, easing=Easing.EASE_OUT)
```

**Cooperative coroutine:**
```python
from gui_do import CooperativeScheduler, Sleep, WaitForSignal

def confirm_and_delete(host, item):
    handle = host.dialog_manager.show(ConfirmDialog(), modal=True)
    confirmed = yield WaitForSignal(handle.on_confirm)
    if confirmed:
        host.toasts.show("Item deleted")

# In bind_runtime:
host.scheduler.run(confirm_and_delete(host, self._selected_item))
```

**Debounced search:**
```python
from gui_do import Debouncer

self._debounce = Debouncer(delay=0.3, callback=self._run_search)
# In handle_event:
if event.type == EventType.TEXT_INPUT:
    self._debounce.trigger()
```

#### Minimal example

```python
from gui_do import TweenManager, Easing, Feature, ButtonControl, PanelControl
import pygame

class FadeFeature(Feature):
    HOST_REQUIREMENTS = {"build": ("app", "screen_rect", "controls", "tween_manager"), "bind_runtime": ("app",)}

    def build(self, host):
        self._panel = PanelControl(rect=pygame.Rect(50, 50, 200, 100))
        self._panel.alpha = 0
        btn = ButtonControl(
            rect=pygame.Rect(8, 8, 120, 32),
            label="Fade In",
            on_click=lambda e: host.tween_manager.to(
                self._panel, "alpha", 255, duration=0.4, easing=Easing.EASE_OUT
            ),
        )
        self._panel.add(btn)
        host.controls.add(self._panel)

    def bind_runtime(self, host):
        pass
```

#### Advanced pattern: AnimationStateMachine for sprite animation

`AnimationStateMachine` manages state-driven animations — for example, a character sprite that
transitions between idle, walking, and running states:

```python
from gui_do import AnimationStateMachine, AnimationTransitionMode

asm = AnimationStateMachine()
asm.add_state("idle", loop=True, frames=[...])
asm.add_state("walk", loop=True, frames=[...])
asm.add_transition("idle", "walk", trigger="start_walk", mode=AnimationTransitionMode.IMMEDIATE)
asm.add_transition("walk", "idle", trigger="stop_walk", mode=AnimationTransitionMode.ON_COMPLETE)
asm.set_state("idle")

# Each frame:
asm.update(dt)
asm.trigger("start_walk")  # transitions to walk state
```

`CooperativeScheduler` with `WaitForAll` enables fan-out workflows — launch multiple sub-tasks
and wait for all to complete before proceeding.

#### Common mistakes and anti-patterns

- **Unbounded computation in `on_update`** — any work that takes significant time belongs in
  a `CooperativeScheduler` coroutine, not directly in `on_update`. Long `on_update` implementations
  block rendering and produce frame drops.
- **Blocking I/O inside coroutines** — `CooperativeScheduler` coroutines run on the main
  thread. Blocking I/O (file read, network request) will freeze the frame. Use
  `DataflowPipeline` with background threads for I/O-bound work.
- **Not canceling tweens on scene exit** — if a tween is still active when the scene
  transitions out, it will try to apply mutations to controls that no longer exist. Cancel
  active tweens in `shutdown_runtime` or use `TweenHandle.cancel()`.
- **Using `Sleep` in a coroutine expecting frame-exact timing** — `Sleep` waits at least
  the specified duration but is not frame-exact. For frame-synchronized timing, use
  `Timers` or `SceneTimeline`.

#### Cross-links to related systems

- §8.2 Feature Lifecycle — `on_update` is the frame-level hook that drives scheduling
- §8.10 (self) — `DataflowPipeline` (Tier 26) is also documented in §8.14
- §8.16 Telemetry — scheduler telemetry spans measure dispatch budget usage

[Back to Table of Contents](#table-of-contents)

---

### 8.11 Persistence and Workspace/Session State

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Applications that require session continuity — remembering which scene the user was in,
which windows were open, what values were typed into settings — need a persistence layer.
`gui_do` provides workspace persistence through `WorkspacePersistenceManager`, which saves
and restores a structured snapshot of the session. The snapshot includes scene identity,
feature-level state, scene node positions, and named settings values.

The persistence system also provides stateful undo/redo via `CommandHistory`, a versioned
snapshot and migration system via `SnapshotMigrator`, and named settings via `SettingsRegistry`.
These systems are composable: workspace persistence uses `SettingsRegistry` for settings
round-trips, and `SnapshotMigrator` provides schema evolution for snapshots saved by older
versions of the application.

#### Mental model and lifecycle placement

The workspace is a JSON snapshot taken at a save point. On restore, `GuiApplication.restore_workspace`
(or `load_workspace`) reads the snapshot, switches to the saved scene, replays feature states,
restores scene node positions, and replays settings values. The restore report is a structured
object that identifies what was applied, what was skipped (unknown keys), and what was missing
(expected but not found settings blocks).

`CommandHistory` is a per-feature or per-context undo stack. `Command` objects are executable
and undoable operations that can be composed into `CommandTransaction` for grouped undo steps.
`UndoContextManager` provides named routing across multiple independent undo stacks.

#### Primary public APIs and key types

From **Tier 11** (State & Persistence):
- `CommandHistory`, `Command`, `CommandTransaction` — undo/redo stack with grouped operations
- `StateMachine` — simple explicit state machine with transition guards
- `HierarchicalStateMachine` — nested state machine with enter/exit hooks and history
- `Router`, `RouteEntry` — URL-style feature routing for navigation history
- `SettingsRegistry`, `SettingDescriptor` — typed named settings with defaults and validation
- `WorkspaceState`, `WorkspacePersistenceManager`, `DEFAULT_WORKSPACE_STATE_PATH` — session save/restore
- `SceneSnapshot`, `NodeSnapshot` — snapshot of scene or node state for save/restore

From **Tier 23** (Undo Context Routing):
- `UndoContextManager` — routes undo/redo operations to the correct named stack

From **Tier 32** (Portable Snapshot & Migration Layer):
- `SchemaVersion` — version identifier for a snapshot schema
- `VersionedSnapshot` — snapshot payload with embedded version metadata
- `MigrationStep` — a single transformation from version N to version N+1
- `MigrationRegistry` — registers all known migration steps
- `SnapshotMigrator` — BFS migration graph that walks from old version to current
- `MigrationError` — raised when no migration path exists to the target version
- `make_snapshot` — creates a `VersionedSnapshot` with the current schema version
- `read_version` — reads the schema version from a snapshot without deserializing the payload

**[CONTRACT]** Workspace restore report fields (from `docs/runtime_operating_contracts.md`):
- `target_scene` — the scene name the restore targeted
- `switched_scene` — whether the active scene was actually switched
- `restored_feature_states` — list of feature state keys that were restored
- `restored_scene_nodes` — list of scene node identifiers that were restored
- `applied_settings` — list of settings keys successfully applied
- `skipped_settings` — list of settings keys that were unknown and skipped
- `missing_settings_blocks` — list of expected settings blocks not found in snapshot

#### Typical usage flow

**Save workspace:**
```python
host.app.save_workspace(path="./session.json")
```

**Load workspace:**
```python
report = host.app.load_workspace(path="./session.json")
if report.skipped_settings:
    host.toast_manager.show(
        f"{len(report.skipped_settings)} settings could not be restored",
        severity=ToastSeverity.WARNING,
    )
```

**Undo/redo:**
```python
history = CommandHistory()
history.execute(PaintCommand(canvas, color, position))
history.undo()   # reverts the paint
history.redo()   # re-applies it
```

#### Minimal example

```python
from gui_do import WorkspacePersistenceManager, SettingsRegistry, SettingDescriptor

# Register typed settings
settings = SettingsRegistry()
settings.register(SettingDescriptor(key="theme", dtype=str, default="light"))
settings.register(SettingDescriptor(key="font_size", dtype=int, default=14))

# Save
manager = WorkspacePersistenceManager(path="./workspace.json")
manager.save(host.app, settings)

# Restore
report = manager.restore(host.app, settings)
print(f"Applied: {report.applied_settings}")
print(f"Skipped: {report.skipped_settings}")
```

#### Advanced pattern: versioned snapshots with migration

When the application's persistence schema evolves between versions, `SnapshotMigrator`
ensures old snapshots can still be loaded:

```python
from gui_do import (
    SchemaVersion, VersionedSnapshot, MigrationStep, MigrationRegistry, SnapshotMigrator, make_snapshot, read_version
)

v1 = SchemaVersion(major=1, minor=0)
v2 = SchemaVersion(major=2, minor=0)

def migrate_v1_to_v2(data: dict) -> dict:
    # Rename "color" to "theme_color"
    data["theme_color"] = data.pop("color", "white")
    return data

registry = MigrationRegistry()
registry.register(MigrationStep(from_version=v1, to_version=v2, migrate=migrate_v1_to_v2))

migrator = SnapshotMigrator(registry=registry, current_version=v2)
snapshot = load_raw_snapshot_from_disk()
current_data = migrator.migrate(snapshot)
```

#### Common mistakes and anti-patterns

- **Assuming all settings keys exist after restore** — always use the restore report's
  `skipped_settings` and `missing_settings_blocks` fields to handle partial restores gracefully.
- **Restoring snapshots without version checks** — always call `read_version` before
  deserializing payload. An old snapshot with a newer schema will produce incorrect data.
- **Using `DEFAULT_WORKSPACE_STATE_PATH` in multi-instance scenarios** — multiple concurrent
  instances will clobber each other's workspace. Use per-instance paths derived from a unique
  identifier.
- **Forgetting to register settings before save/restore** — a setting that is not registered
  in `SettingsRegistry` will not be included in saves or restores.

#### Cross-links to related systems

- §8.1 Bootstrap — workspace restore is initiated during `GuiApplication.run_entrypoint`
- §8.2 Feature Lifecycle — `shutdown_runtime` is the correct place to save per-feature state
- §8.16 Telemetry — telemetry logs can be saved alongside workspace state for diagnostics

For field-level reference for `SchemaVersion`, `VersionedSnapshot`, and `MigrationStep`, see
[Appendix F: Specifications and Option Reference](#appendix-f-specifications-and-option-reference).

[Back to Table of Contents](#table-of-contents)

---

### 8.12 Theme, Styling, and Visual Systems

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

The theme system centralizes all visual design decisions — colors, font sizes, spacing values,
border radii, icon sizes — into named tokens that controls and features read at render time.
Without a centralized theme system, changing the visual style of an application requires finding
and updating every hardcoded color literal and font size across the codebase. With a theme system,
the developer changes one set of tokens and all controls that use those tokens update automatically.

`gui_do`'s theme system also provides the mechanism for switching between themes at runtime
(for example, between a light and a dark mode). The `ThemeInvalidationBus` ensures that all
cached rendered surfaces are flushed when the theme changes, so stale visuals never appear
after a theme switch.

#### Mental model and lifecycle placement

The `ThemeManager` holds the active `ColorTheme` and `DesignTokens`. Controls read theme
values at render time — they do not cache colors at construction time. This means a theme
switch takes effect on the next frame without requiring any control to be rebuilt. The
`FontRoleRegistry` maps semantic role names (such as "heading", "body.small", "caption") to
configured font objects. Features declare font roles in the bootstrap spec; controls reference
roles by name.

`ScopedTheme` and `ScopedThemeManager` allow a subtree to override specific theme tokens
locally — for example, applying a dark panel style to a sidebar while the rest of the
application uses a light theme.

#### Primary public APIs and key types

From **Tier 6** (Theme & Font Management):
- `FontManager` — loads and caches font objects; resolves font role names to pygame font instances
- `FontRoleRegistry` — maps semantic role names to font configurations (size, weight, file, system name)
- `ColorTheme` — a named set of color mappings from semantic role names to RGBA tuples
- `ThemeManager`, `DesignTokens` — active theme holder and named scalar/color token store
- `ScopedTheme`, `ScopedThemeManager` — per-subtree theme overrides

From **Tier 22** (Theme Invalidation):
- `ThemeInvalidationBus` — broadcast channel for theme change notifications; subscribe to invalidate surface caches on theme switch

From **Tier 1** (spec helpers):
- `FontRoleBindingSpec` — declarative binding of a semantic role name to a font config and size
- `setup_standard_font_roles` — convenience function to register a standard set of roles from a fonts dictionary

#### Typical usage flow

1. Declare the `fonts` dictionary in `HostApplicationBindingSpec` with named font configurations.
2. Add `FontRoleBindingSpec` entries to map semantic role names to the configured fonts.
3. Controls reference font roles by name; they are resolved through `FontRoleRegistry` at render time.
4. For custom rendering in `draw`, query `host.theme_manager` for design tokens and the
   active color theme.
5. If the application supports theme switching, register surface caches with
   `ThemeInvalidationBus` so they flush on theme change.

#### Minimal example

```python
from gui_do import (
    HostApplicationBindingSpec,
    FontRoleBindingSpec,
    setup_standard_font_roles,
)

# In HostApplicationBindingSpec:
fonts={
    "default": {"file": "assets/fonts/Body.ttf", "size": 14},
    "window": "assets/fonts/Title.ttf",
},
font_role_entries=(
    FontRoleBindingSpec("title", size=18, font="window"),
    FontRoleBindingSpec("body", size=14, font="default"),
    FontRoleBindingSpec("caption", size=11, font="default"),
),
```

Controls that accept a `font_role` parameter will automatically resolve the correct font at
render time. Custom draw code reads from the theme:

```python
def draw(self, host, surface, theme):
    color = theme.color_theme.get("panel.background")
    font = host.font_manager.get_role("body")
    rendered = font.render("Hello", True, color)
    surface.blit(rendered, self._rect.topleft)
```

#### Advanced pattern: ScopedTheme for per-window overrides

```python
from gui_do import ScopedTheme, ScopedThemeManager

# Create a dark overlay for one window only
dark_theme = ScopedTheme(overrides={"panel.background": (30, 30, 30, 255)})
scope_manager = ScopedThemeManager()
scope_manager.push(dark_theme)
# Controls inside this scope read the overridden background
scope_manager.pop()
```

`ThemeInvalidationBus` subscription for cached surfaces:

```python
from gui_do import ThemeInvalidationBus

class CachingControl:
    def __init__(self):
        self._cache = None
        ThemeInvalidationBus.instance().subscribe(self._invalidate)

    def _invalidate(self):
        self._cache = None  # force re-render on next draw
```

#### Common mistakes and anti-patterns

- **Hardcoding color literals in draw code** — this bypasses the theme system and breaks
  theme switching. Always read colors from `theme.color_theme` or `theme.design_tokens`.
- **Caching rendered text surfaces without invalidation** — text surfaces baked at one theme's
  font and color will be stale after a theme switch. Subscribe to `ThemeInvalidationBus`.
- **Registering fonts outside the bootstrap phase** — font role registration happens during
  bootstrap. Attempting to call `FontRoleRegistry.define` after bootstrap completes may not
  take effect in all font consumers.

#### Cross-links to related systems

- §8.1 Bootstrap — `fonts` and `font_role_entries` are declared in the bootstrap spec
- §8.5 Controls — all standard controls read font roles and color theme at render time
- §8.16 Telemetry — theme invalidation events can be tracked through telemetry spans

For field-level reference for `FontRoleBindingSpec`, `CursorSpec`, and `CursorBindingSpec`, see
[Appendix F: Specifications and Option Reference](#appendix-f-specifications-and-option-reference).

[Back to Table of Contents](#table-of-contents)

---


### 8.13 Text, Input, Forms, and Validation Systems

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Structured text entry, document editing, form modeling, and field validation appear in nearly
every non-trivial application. Implementing these from scratch in each feature produces
inconsistent UX, duplicated validation logic, and fragile cross-field dependency handling.
`gui_do` provides a layered system that separates the concerns: input controls handle
keystroke-level editing, `FormModel` models the logical form, `ValidationRule` and
`FieldError` carry validation results, and `SchemaFormRuntime` drives the full validation
lifecycle with a configurable `ValidationPolicy`.

#### Mental model and lifecycle placement

Think of text input as a three-layer stack. At the bottom, `TextInputControl` and
`TextAreaControl` handle raw keystroke processing, selection, cursor movement, and IME
input. At the middle, `FormField` binds a control's value to a `FormModel`, converting
raw strings into typed domain values. At the top, `ValidationRule` objects run on each
change or on submission and produce `FieldError` objects displayed beside the field.
`SchemaFormRuntime` orchestrates this whole stack from a declarative `FieldGraphSchema`.

#### Primary public APIs and key types

From **Tier 10** (Forms, Validation, and Document Editing):
- `FormModel`, `FormField` — logical form with typed fields
- `ValidationRule`, `FieldError` — validation contract and error result
- `FormSchema`, `SchemaField` — declarative schema for a form's fields and constraints
- `DocumentModel` — rich-text document backing for `TextAreaControl`; spans and editing operations
- `WizardFlow`, `WizardStep`, `WizardHandle` — multi-step guided workflow with per-step validation
- `RequiredValidator`, `LengthValidator`, `PatternValidator`, `RangeValidator`, `DependentValidator` — built-in validators
- `CompositeValidator` — runs multiple validators in sequence; stops at first failure or collects all

From **Tier 14** (Text, Formatting, and Localization):
- `TextFormatter`, `NumericFormatter`, `PatternFormatter`, `FixedPatternFormatter` — format value to string
- `TextFlow`, `TextSpan` — multi-run text layout with mixed styling
- `TextSearcher`, `TextMatch` — substring and regex search over text content
- `StringTable`, `LocaleRegistry` — locale-keyed string tables for internationalization

From **Tier 24** (Async Form Validation):
- `AsyncFieldValidator` — async validation for a single field (e.g., server-side uniqueness check)
- `AsyncFormValidator` — coordinates multiple `AsyncFieldValidator` instances with debouncing and stale-result suppression

From **Tier 31** (Schema Form Runtime):
- `FieldSchema`, `FieldGraphSchema` — DAG of fields with visibility and dependency declarations
- `ValidationPolicy` — controls when validation fires: `ON_CHANGE`, `ON_BLUR`, `ON_SUBMIT`, `ALWAYS`
- `SchemaFormRuntime` — drives `FieldGraphSchema` with a `ValidationPolicy`, manages field lifecycle

From **Tier 13** (Extended Controls — input-specific):
- `TextInputControl`, `TextAreaControl` — single-line and multi-line text entry
- `SpinnerControl`, `RangeSliderControl` — numeric entry with increment/decrement
- `DatePickerControl`, `TimePickerControl` — date and time selection
- `ColorPickerControl` — interactive color selection
- `ChipInputControl` — tag entry with removable chips

#### Typical usage flow

1. Declare `FormSchema` with `SchemaField` entries for each field (name, dtype, validators).
2. Build a `FieldGraphSchema` from the schema (for visibility dependencies).
3. Construct `SchemaFormRuntime` with the graph schema and a `ValidationPolicy`.
4. In the feature's `build`, create `TextInputControl` instances for each field and bind them
   to the `FormModel` via `FormField`.
5. In `bind_runtime`, subscribe to the form model's `on_validation_changed` to update error
   display labels beside each field.
6. For async validation (e.g., email availability), add `AsyncFieldValidator` instances to an
   `AsyncFormValidator` and connect it to the form model.

#### Minimal example

```python
from gui_do import (
    FormSchema, SchemaField, SchemaFormRuntime, FieldGraphSchema,
    ValidationPolicy, RequiredValidator, PatternValidator,
    LengthValidator, FieldError,
)

EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

schema = FormSchema([
    SchemaField(key="email", dtype=str, validators=[
        RequiredValidator(),
        PatternValidator(pattern=EMAIL_PATTERN, message="Enter a valid email address"),
    ]),
    SchemaField(key="password", dtype=str, validators=[
        RequiredValidator(),
        LengthValidator(minimum=8, message="Password must be at least 8 characters"),
    ]),
])

graph = FieldGraphSchema.from_form_schema(schema)
runtime = SchemaFormRuntime(graph_schema=graph, policy=ValidationPolicy.ON_CHANGE)

# On submit:
errors: dict[str, FieldError] = runtime.validate_all()
if not errors:
    submit_form(runtime.get_values())
```

#### Advanced pattern: AsyncFormValidator for server-side checks

```python
from gui_do import AsyncFieldValidator, AsyncFormValidator

async def check_username_available(value: str) -> str | None:
    exists = await my_api.check_username(value)
    return "Username already taken" if exists else None

async_validator = AsyncFormValidator()
async_validator.add(AsyncFieldValidator(
    key="username",
    validate=check_username_available,
    debounce=0.4,
))
runtime.set_async_validator(async_validator)
```

`DependentValidator` fires only when a condition on another field passes:

```python
from gui_do import DependentValidator

DependentValidator(
    condition=lambda form: form.get("type") == "company",
    validators=[RequiredValidator()],
)
```

#### Common mistakes and anti-patterns

- **Validating only on submit** — use `ValidationPolicy.ON_CHANGE` or `ON_BLUR` for continuous feedback.
- **Wiring async validators without stale-result suppression** — `AsyncFormValidator` handles
  this via generation tracking; custom async paths must suppress stale results manually.
- **Using `TextInputControl.value` as source of truth** — the `FormField` or `FormModel` owns the typed value.

#### Cross-links to related systems

- §8.4 State and Observables — `FormField` binds to `ObservableValue`
- §8.5 Controls — input controls are Tier 13 extended controls
- §8.14 Data and Dataflow Helpers — `DataflowPipeline` for search-as-you-type patterns

[Back to Table of Contents](#table-of-contents)

---

### 8.14 Data and Dataflow Helpers

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Features that display large datasets — file listings, search results, log records, entity
tables — need efficient loading, sorting, filtering, diff-based updates, and virtualized
rendering. `gui_do` provides a composable data pipeline: async loading, sort/filter projection,
diff calculation, and virtualized windowing, available as composable building blocks.

#### Mental model and lifecycle placement

Data flows from a source through a projection layer into a virtualized rendering layer.
The source is a `FixedItemSource` or `AsyncDataProvider`. The projection layer is a
`SortFilterProxySource`. The rendering layer is `ListViewControl` or `VirtualizationCore`.
`ListDiffCalculator` computes minimal patches for incremental updates. `DataflowPipeline`
provides multi-stage cancelable processing with `CancellationToken`.

#### Primary public APIs and key types

From **Tier 15** (Data & Collections):
- `VirtualItemSource` — abstract base: `count` and `get_item(index)` on demand
- `FixedItemSource` — wraps a plain list as a `VirtualItemSource`
- `SortFilterProxySource` — sort/filter projection without copying source data
- `AsyncDataProvider`, `LoadState`, `LoadStateKind` — async loading with `IDLE/LOADING/LOADED/ERROR` state
- `ObjectPool` — pre-allocated pool for high-churn objects; reduces GC pressure
- `DataCache`, `CacheStats` — LRU-style keyed cache with hit/miss metrics
- `ListDiffCalculator`, `ListDiff`, `DiffInsert`, `DiffRemove`, `DiffMove` — minimal list patch computation

From **Tier 26** (Cancelable Dataflow Pipeline):
- `CancellationToken` — generation-based cancellation for stale pipeline runs
- `PipelineStage` — a single transformation stage
- `DataflowPipeline` — multi-stage cancelable processing pipeline
- `PipelineHandle` — handle for monitoring and canceling a running pipeline

From **Tier 27** (Transactional App State Store):
- `AppStateStore` — centralized state container with immutable transactions
- `StateSelector` — derived slice of store state subscribed to relevant keys
- `StateTransaction` — atomic state update across multiple keys

From **Tier 29** (Unified Virtualization Core):
- `MeasureMode`, `MeasurePolicy` — measurement semantics for virtualized windows
- `VirtualizedWindow` — windowing structure for virtualized list/tree/grid rendering
- `RecyclePool` — recycles control instances across scroll positions
- `VirtualizationCore` — manages windowing, recycling, and identity tracking for large collections

#### Typical usage flow

```python
from gui_do import FixedItemSource, SortFilterProxySource

source = FixedItemSource(items=my_item_list)
proxy = SortFilterProxySource(source)
proxy.set_filter(lambda item: item.is_active)
proxy.set_sort_key(lambda item: item.name.lower())
list_view.set_source(proxy)

# Change filter live — ListViewControl reacts automatically:
proxy.set_filter(lambda item: query in item.name.lower())
```

#### Minimal example

```python
from gui_do import DataflowPipeline, PipelineStage, CancellationToken

def search_stage(query, token: CancellationToken):
    if token.is_cancelled:
        return []
    return [item for item in full_dataset if query in item.name]

def rank_stage(results, token: CancellationToken):
    if token.is_cancelled:
        return []
    return sorted(results, key=lambda i: i.relevance, reverse=True)

pipeline = DataflowPipeline(stages=[
    PipelineStage(search_stage),
    PipelineStage(rank_stage),
])

# On new search query — cancels previous run automatically:
handle = pipeline.run(query=user_query, on_complete=self._on_results_ready)
```

#### Common mistakes and anti-patterns

- **Full-list redraws without `ListDiffCalculator`** — computing which rows changed is cheap; full redraws are not.
- **Not canceling stale `DataflowPipeline` generations** — results from earlier runs may arrive after later ones.
- **Using `ObjectPool` with objects still referenced elsewhere** — produces silent aliasing bugs.

#### Cross-links to related systems

- §8.4 State and Observables — `StateSelector` subscribes to `AppStateStore`
- §8.5 Controls — `ListViewControl`, `DataGridControl`, `TreeControl` consume item sources
- §8.10 Scheduling — `CooperativeScheduler` for background work
- §8.16 Telemetry — pipeline stage timing via telemetry spans

[Back to Table of Contents](#table-of-contents)

---

### 8.15 Graphics and Audio Integration Points

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

Some features require rendering beyond the standard control tree: particle effects, tile-based
maps, 2D scene graphs with camera transforms, custom draw overlays, or post-processing effects.
`gui_do` provides a graphics abstraction layer built on pygame for this. For audio, a semantic
event bus decouples features from mixer internals.

#### Mental model and lifecycle placement

Custom rendering lives in the feature's `draw(host, screen)` hook or inside `CanvasControl`.
Heavy geometry or texture operations should be precomputed in `on_update` or cached in an
`OffscreenRenderTarget`. Audio cues are event-driven: declare named cues in `SoundBankRegistry`
and publish them via `SoundEventBus`. Features never call the mixer directly.

#### Primary public APIs and key types

From **Tier 16** (Graphics and Rendering):
- `DrawContext`, `DrawPhase` — structured draw pass with explicit phases
- `DirtyRegionTracker` — per-frame dirty-rect accumulation; gates re-rendering of unchanged regions
- `SurfaceCompositor`, `Layer` — layered compositing pipeline with z-order and blend modes
- `ShapeRenderer` — convenience renderer for rounded rects, arrows, circles, lines
- `SurfaceEffects` — post-processing effects (blur, tint, darken)
- `VectorPath` — declarative path builder (move_to, line_to, curve_to, arc)
- `SpriteSheet`, `FrameAnimation` — frame extraction from a sprite atlas with playback control
- `ParticleSystem`, `Emitter`, `ParticleLayer` — particle emission with configurable spawn rate, velocity, lifetime, color
- `TileSet`, `TileMap` — grid-based tile rendering; only visible tiles are drawn
- `SceneGraph2D`, `Node2D`, `Camera2D` — hierarchical 2D transform tree with camera viewport
- `RenderTarget`, `LiveRenderTarget`, `OffscreenRenderTarget`, `create_render_target`, `create_surface` — offscreen surface management
- `AssetRegistry` — centralized loaded-asset registry; prevents duplicate loading
- `BuiltInGraphicsFactory` — factory for standard built-in graphics components
- `DebugOverlay` — renders diagnostic overlays over the live scene

From **Tier 20** (Audio):
- `SoundCue` — a named sound event
- `SoundBankRegistry` — registry of named sound files or generated tones
- `SoundEventBus` — semantic event bus routing `SoundCue` publications to the mixer

#### Typical usage flow

```python
# Particle effect — in build:
from gui_do import ParticleSystem, Emitter
self.particles = ParticleSystem()
self.emitter = Emitter(spawn_rate=30, lifetime=1.5)
self.particles.add_emitter(self.emitter)

# In on_update:
self.particles.tick(dt)

# In draw:
self.particles.draw(screen)

# Audio cue — in event handler:
from gui_do import SoundCue
host.sound_bus.publish(SoundCue("button_click"))
```

#### Minimal example

```python
from gui_do import OffscreenRenderTarget, create_render_target, ShapeRenderer
import pygame

class BackgroundFeature(Feature):
    HOST_REQUIREMENTS = {"build": ("app", "screen_rect"), "bind_runtime": ("app",)}

    def build(self, host):
        self._target: OffscreenRenderTarget = create_render_target(
            size=(host.screen_rect.width, host.screen_rect.height)
        )
        renderer = ShapeRenderer(surface=self._target.surface)
        renderer.draw_rounded_rect(
            rect=pygame.Rect(0, 0, host.screen_rect.width, host.screen_rect.height),
            radius=12,
            color=(30, 30, 40, 255),
        )

    def draw(self, host, screen):
        screen.blit(self._target.surface, (0, 0))

    def bind_runtime(self, host):
        pass
```

#### Advanced pattern: SceneGraph2D with Camera2D

```python
from gui_do import SceneGraph2D, Node2D, Camera2D
import pygame

graph = SceneGraph2D()
camera = Camera2D(viewport=pygame.Rect(0, 0, 800, 600))
camera.set_position(100, 200)

world_node = Node2D(position=(0, 0))
sprite_node = Node2D(position=(250, 300))
sprite_node.surface = my_sprite_surface
world_node.add_child(sprite_node)
graph.root.add_child(world_node)

# In draw:
graph.draw(screen, camera=camera)
```

#### Common mistakes and anti-patterns

- **Full-surface redraw every frame** — use `DirtyRegionTracker` to gate rendering to changed regions only.
- **Loading assets in `draw`** — `AssetRegistry.load` involves disk I/O; load in `build`.
- **Audio cues on pointer-move events** — pointer-move fires every frame; trigger cues on semantic actions.
- **Particles without viewport bounds** — unconstrained particles render outside the visual area.

#### Cross-links to related systems

- §8.2 Feature Lifecycle — `draw` and `on_update` hooks
- §8.5 Controls — `CanvasControl` embeds custom 2D content
- §8.10 Scheduling — particle tick in `on_update`
- §8.16 Telemetry — instrument draw cost

[Back to Table of Contents](#table-of-contents)

---

### 8.16 Telemetry, Introspection, and Operational Hooks

[Back to Table of Contents](#table-of-contents)

#### What it is and why it exists

When frame rate drops, a layout pass is slow, or a routing decision is wrong, developers
need structured observability rather than visual inspection. `gui_do` provides `TelemetryCollector`
for performance sampling, `PropertyRegistry` for runtime property inspection, and
`SceneSpatialIndex` for geometric queries about control layout.

#### Mental model and lifecycle placement

Telemetry is frame-sampling based: the collector records `TelemetrySample` objects with span
names, durations, and metadata. Telemetry is off by default; enable via
`configure_telemetry(enabled=True)` or `TelemetryConfig` in `HostApplicationConfig`.

`PropertyRegistry` is populated via `@ui_property` decorators on control classes.
`PropertyInspectorModel` reads the registry to drive `PropertyInspectorPanel`.

`SceneSpatialIndex` answers layout queries: which controls overlap a rect, which control is
at a point. It is rebuilt after each layout pass.

#### Primary public APIs and key types

From **Tier 7** (Telemetry):
- `TelemetryCollector`, `TelemetrySample` — collector and sample record
- `configure_telemetry` — enables/disables the global collector
- `telemetry_collector` — module-level singleton for the active `TelemetryCollector`
- `analyze_telemetry_log_file`, `analyze_telemetry_records` — offline and live analysis
- `load_telemetry_log_file` — loads a saved telemetry log for offline inspection
- `render_telemetry_report` — formats an analysis result for human-readable display

From **Tier 17** (Introspection):
- `SceneSpatialIndex` — geometric query engine for the control tree
- `ui_property` — decorator that marks a control attribute as inspectable
- `PropertyDescriptor`, `PropertyRegistry`, `property_registry` — property metadata and registry
- `PropertyInspectorModel` — view model driving `PropertyInspectorPanel`
- `InspectedProperty` — a single inspected property with current value and metadata

#### Minimal example

```python
from gui_do import configure_telemetry, telemetry_collector, analyze_telemetry_records, render_telemetry_report

configure_telemetry(enabled=True)
# ... run application scenarios ...
report = analyze_telemetry_records(telemetry_collector.records)
print(render_telemetry_report(report))
```

#### Advanced pattern: DebugOverlay with spatial index

```python
from gui_do import SceneSpatialIndex, DebugOverlay

def draw(self, host, screen):
    index: SceneSpatialIndex = host.app.get_spatial_index()
    hits = index.query_point(self._mouse_pos)
    DebugOverlay(screen).draw_bounds(hits, color=(255, 0, 0))
```

#### Common mistakes and anti-patterns

- **Profiling during idle loop** — profile during active user scenarios, not quiet frames.
- **Relying on visual inspection alone** — telemetry records actual durations; the eye cannot distinguish 16ms from 18ms.
- **Forgetting to call `configure_telemetry` before scenarios** — early frames are not recorded.

#### Cross-links to related systems

- §8.10 Scheduling — scheduler budget tracked via telemetry spans
- §8.11 Persistence — telemetry logs alongside workspace state
- §8.15 Graphics — `DebugOverlay` visualizes spatial index results

[Back to Table of Contents](#table-of-contents)

---

## Integration Patterns and Composition Recipes

[Back to Table of Contents](#table-of-contents)

This chapter collects four composite patterns that each combine multiple `gui_do` systems into
a production-ready configuration. Each recipe explains the goal, the rationale for the
combination, step-by-step implementation, a complete code listing, and validation notes.

---

### Recipe 1: Routed Feature + Actions + Shortcut Overlay

**Goal:** A feature with discoverable keyboard shortcuts, auto-wired via `RoutedRuntimeSpec`.

**Why this combination:** `RoutedRuntimeSpec` with `ShortcutOverlaySpec` eliminates boilerplate
for action registration, keyboard shortcut binding, and keeping the help overlay synchronized
with the registered action list.

**Step-by-step:**
1. Declare `ActionSpec` entries in `HostApplicationConfig.action_entries`.
2. Build a `RoutedRuntimeSpec` with a `ShortcutOverlaySpec`.
3. Build a `RoutedFeatureLifecycleSpec` referencing the runtime spec.
4. In `bind_runtime`, call `bind_routed_feature_lifecycle(self, host, self._lifecycle_spec)`.
5. In `shutdown_runtime`, call `shutdown_routed_feature_lifecycle(self, host, self._lifecycle_spec)`.

```python
import pygame
from gui_do import (
    RoutedFeature, RoutedRuntimeSpec, RoutedFeatureLifecycleSpec,
    ShortcutOverlaySpec,
    bind_routed_feature_lifecycle, shutdown_routed_feature_lifecycle,
    PanelControl, LabelControl,
)

class ToolFeature(RoutedFeature):
    HOST_REQUIREMENTS = {
        "build": ("app", "screen_rect", "controls"),
        "bind_runtime": ("app",),
        "shutdown_runtime": ("app",),
    }

    def __init__(self):
        self._lifecycle_spec = RoutedFeatureLifecycleSpec(
            runtime_spec=RoutedRuntimeSpec(
                shortcut_overlay=ShortcutOverlaySpec(activation_key=pygame.K_F9),
            )
        )

    def build(self, host):
        root = PanelControl(rect=pygame.Rect(0, 0, 800, 600))
        root.add(LabelControl(rect=pygame.Rect(8, 8, 300, 24), text="Ready"))
        host.controls.add(root)

    def bind_runtime(self, host):
        bind_routed_feature_lifecycle(self, host, self._lifecycle_spec)

    def shutdown_runtime(self, host):
        shutdown_routed_feature_lifecycle(self, host, self._lifecycle_spec)
```

**Validation:** F9 toggles the shortcut overlay. All registered `ActionSpec` entries appear
in the overlay automatically.

---

### Recipe 2: Window Presenter + Task Panel + Focus Toggle

**Goal:** A floating window in a scene, toggled from the task panel, with correct focus routing.

**Why this combination:** `WindowPresenter` separates window layout from the owning feature.
`FeatureWindowBundleBindingSpec` wires feature, window, and task panel in one spec.
`TaskPanelFocusToggleSpec` auto-excludes the window's controls from Tab cycling while hidden.

**Step-by-step:**
1. Implement a `WindowPresenter` subclass owning the window's control layout.
2. In feature `build`, call `create_feature_presented_window`.
3. In `RoutedRuntimeSpec`, add a `TaskPanelFocusToggleSpec`.
4. Wire the task panel toggle to `set_window_visible_state` (automatic with bundle spec).

```python
from gui_do import (
    WindowPresenter, PanelControl, LabelControl,
    TaskPanelFocusToggleSpec,
    RoutedFeature, RoutedRuntimeSpec, RoutedFeatureLifecycleSpec,
    create_feature_presented_window,
    bind_routed_feature_lifecycle, shutdown_routed_feature_lifecycle,
)
import pygame

class InspectorPresenter(WindowPresenter):
    def build(self, host, window_rect):
        panel = PanelControl(rect=window_rect)
        panel.add(LabelControl(rect=pygame.Rect(8, 8, 200, 24), text="Inspector"))
        return panel

class InspectorFeature(RoutedFeature):
    HOST_REQUIREMENTS = {
        "build": ("app", "screen_rect", "controls"),
        "bind_runtime": ("app",),
        "shutdown_runtime": ("app",),
    }

    def __init__(self):
        self._lifecycle_spec = RoutedFeatureLifecycleSpec(
            runtime_spec=RoutedRuntimeSpec(
                task_panel_focus_toggles=[
                    TaskPanelFocusToggleSpec(window_key="inspector"),
                ],
            )
        )

    def build(self, host):
        create_feature_presented_window(
            host=host,
            window_key="inspector",
            presenter_class=InspectorPresenter,
            window_rect=pygame.Rect(900, 50, 350, 500),
        )

    def bind_runtime(self, host):
        bind_routed_feature_lifecycle(self, host, self._lifecycle_spec)

    def shutdown_runtime(self, host):
        shutdown_routed_feature_lifecycle(self, host, self._lifecycle_spec)
```

**Validation:** Task panel toggle button shows/hides the window. While hidden, Tab does not
cycle into the inspector's controls. Button toggle state matches window visibility.

---

### Recipe 3: State Store + Persistence + Snapshot Migration

**Goal:** Centralized application state that survives schema evolution across releases.

**Why this combination:** `AppStateStore` is the single source of truth. `WorkspacePersistenceManager`
saves and restores it. `SnapshotMigrator` forward-migrates old snapshots so schema-breaking
updates do not lose user data.

**Step-by-step:**
1. Define `AppStateStore` with initial state.
2. Use `StateSelector` in features to derive needed state slices.
3. On save, call `make_snapshot(version, store.get_all())` and persist.
4. On load, call `read_version(raw)` then `SnapshotMigrator.migrate(snapshot)`.
5. Register `MigrationStep` objects for each schema transition.

```python
from gui_do import (
    AppStateStore, StateSelector,
    SchemaVersion, MigrationStep, MigrationRegistry,
    SnapshotMigrator, make_snapshot, read_version,
    WorkspacePersistenceManager,
)

V1 = SchemaVersion(major=1, minor=0)
V2 = SchemaVersion(major=2, minor=0)

def migrate_v1_to_v2(data: dict) -> dict:
    data["accent_color"] = data.pop("highlight_color", "#007AFF")
    return data

registry = MigrationRegistry()
registry.register(MigrationStep(from_version=V1, to_version=V2, migrate=migrate_v1_to_v2))
migrator = SnapshotMigrator(registry=registry, current_version=V2)

store = AppStateStore(initial={"accent_color": "#007AFF", "font_size": 14})

def save(path: str):
    snapshot = make_snapshot(version=V2, data=store.get_all())
    WorkspacePersistenceManager(path=path).save_raw(snapshot)

def load(path: str):
    raw = WorkspacePersistenceManager(path=path).load_raw()
    migrated_data = migrator.migrate(raw)
    store.replace_all(migrated_data)
```

**Validation:** Loading a V1 snapshot applies the migration and produces a V2 state dict.
Restore report's `skipped_settings` and `missing_settings_blocks` are non-fatal.

---

### Recipe 4: Dataflow Pipeline + Telemetry + ErrorBoundary

**Goal:** Safe background processing with measurable performance and UI failure containment.

**Why this combination:** `DataflowPipeline` with `CancellationToken` ensures stale runs do
not corrupt results. Telemetry spans identify bottlenecks. `ErrorBoundary` wraps the output
control tree so rendering exceptions degrade gracefully rather than crashing the frame.

**Step-by-step:**
1. Define `DataflowPipeline` with per-stage `PipelineStage` functions.
2. Each stage checks its `CancellationToken` before expensive work.
3. Instrument stage callbacks with `telemetry_collector` calls.
4. Wrap the result presenter in `ErrorBoundary` in `build`.
5. Expose progress via `ObservableValue[LoadStateKind]`.

```python
import time
from gui_do import (
    DataflowPipeline, PipelineStage, CancellationToken,
    configure_telemetry, telemetry_collector,
    ErrorBoundary, ObservableValue, LoadStateKind,
    RoutedFeature, PanelControl,
)

configure_telemetry(enabled=True)

def search_stage(query: str, token: CancellationToken):
    t0 = time.perf_counter()
    if token.is_cancelled:
        return []
    results = [item for item in big_dataset if query.lower() in item.name.lower()]
    telemetry_collector.record("search_stage", duration=time.perf_counter() - t0)
    return results

def rank_stage(results: list, token: CancellationToken):
    if token.is_cancelled:
        return []
    return sorted(results, key=lambda i: i.relevance, reverse=True)

pipeline = DataflowPipeline(stages=[
    PipelineStage(search_stage),
    PipelineStage(rank_stage),
])

class SearchFeature(RoutedFeature):
    def build(self, host):
        self._status = ObservableValue(LoadStateKind.IDLE)
        result_panel = PanelControl(rect=...)
        safe_panel = ErrorBoundary(child=result_panel, fallback_text="Results unavailable")
        host.controls.add(safe_panel)

    def _run_search(self, query: str):
        self._status.set(LoadStateKind.LOADING)
        pipeline.run(query, on_complete=self._on_results_ready)

    def _on_results_ready(self, results):
        self._status.set(LoadStateKind.LOADED)
```

**Validation:** Rapid typing produces only the latest result. Telemetry report identifies
the slowest stage. A deliberate presenter exception renders the fallback text.

[Back to Table of Contents](#table-of-contents)

---

## End-to-End Reference Application

[Back to Table of Contents](#table-of-contents)

The following listing is a self-contained reference application demonstrating the core
`gui_do` systems in combination. It is intentionally short and pedagogical — production
applications will extend each section significantly.

```python
"""
gui_do End-to-End Reference Application

Demonstrates:
  - HostApplicationConfig construction with real field names
  - A RoutedFeature with build / bind_runtime / shutdown_runtime
  - ObservableValue subscribed to a LabelControl
  - RoutedRuntimeSpec with ShortcutOverlaySpec
  - RoutedFeatureLifecycleSpec + bind_routed_feature_lifecycle
  - ActionSpec entries (exit + help)
  - RuntimeSceneSpec with bind_escape_to_exit=True
  - TelemetryConfig enabled
  - Workspace save/load hooks
"""

import pygame
from gui_do import (
    HostApplicationConfig,
    HostApplicationBindingSpec,
    SceneBundleBindingSpec,
    ActionSpec,
    TelemetryConfig,
    FontRoleBindingSpec,
    build_host_application_config,
    bootstrap_host_application,
    RoutedFeature,
    RoutedRuntimeSpec,
    RoutedFeatureLifecycleSpec,
    RuntimeSceneSpec,
    ShortcutOverlaySpec,
    bind_routed_feature_lifecycle,
    shutdown_routed_feature_lifecycle,
    PanelControl,
    LabelControl,
    ButtonControl,
    ObservableValue,
    WorkspacePersistenceManager,
    configure_telemetry,
    telemetry_collector,
)

WORKSPACE_PATH = "./my_app_session.json"


class CounterFeature(RoutedFeature):
    HOST_REQUIREMENTS = {
        "build": ("app", "screen_rect", "controls"),
        "bind_runtime": ("app",),
        "shutdown_runtime": ("app",),
    }

    def __init__(self):
        self._count = ObservableValue(0)
        self._lifecycle_spec = RoutedFeatureLifecycleSpec(
            runtime_spec=RoutedRuntimeSpec(
                scene_spec=RuntimeSceneSpec(bind_escape_to_exit=True),
                shortcut_overlay=ShortcutOverlaySpec(activation_key=pygame.K_F9),
            )
        )

    def build(self, host):
        root = PanelControl(rect=pygame.Rect(40, 40, 400, 160))
        self._label = LabelControl(
            rect=pygame.Rect(8, 8, 380, 32),
            text="Count: 0",
        )
        btn = ButtonControl(
            rect=pygame.Rect(8, 56, 140, 36),
            label="Increment",
            on_click=lambda _e: self._count.set(self._count.get() + 1),
        )
        save_btn = ButtonControl(
            rect=pygame.Rect(160, 56, 140, 36),
            label="Save Session",
            on_click=lambda _e: self._save_workspace(host),
        )
        root.add(self._label)
        root.add(btn)
        root.add(save_btn)
        host.controls.add(root)

    def bind_runtime(self, host):
        self._sub = self._count.subscribe(
            lambda v: self._label.set_text(f"Count: {v}")
        )
        bind_routed_feature_lifecycle(self, host, self._lifecycle_spec)
        self._restore_workspace(host)

    def shutdown_runtime(self, host):
        self._count.unsubscribe(self._sub)
        shutdown_routed_feature_lifecycle(self, host, self._lifecycle_spec)

    def _save_workspace(self, host):
        WorkspacePersistenceManager(path=WORKSPACE_PATH).save(host.app)

    def _restore_workspace(self, host):
        manager = WorkspacePersistenceManager(path=WORKSPACE_PATH)
        if manager.has_saved_state():
            report = manager.restore(host.app)
            if report and report.skipped_settings:
                print(f"Skipped settings: {report.skipped_settings}")


def main():
    configure_telemetry(enabled=True)

    config: HostApplicationConfig = build_host_application_config(
        HostApplicationBindingSpec(
            display_size=(900, 600),
            window_title="gui_do Reference App",
            initial_scene_name="main",
            fonts={
                "default": {"file": "assets/fonts/Body.ttf", "size": 14},
            },
            font_role_entries=(
                FontRoleBindingSpec("body", size=14, font="default"),
                FontRoleBindingSpec("caption", size=11, font="default"),
            ),
            action_entries=(
                ActionSpec(action_id="exit", label="Exit", key=pygame.K_ESCAPE),
                ActionSpec(action_id="help", label="Shortcuts", key=pygame.K_F9),
            ),
            scene_bundle_entries=(
                SceneBundleBindingSpec(
                    scene_name="main",
                    pretty_name="Main",
                    feature_entries=(CounterFeature,),
                ),
            ),
            telemetry=TelemetryConfig(enabled=True),
        )
    )

    bootstrap_host_application(config)


if __name__ == "__main__":
    main()
```

### What This Listing Demonstrates

**Bootstrap pipeline** — `HostApplicationBindingSpec` is the single declarative entry point.
Fonts, actions, scenes, and features are all registered before `bootstrap_host_application`
wires them together. `build_host_application_config` validates the spec and produces a typed
`HostApplicationConfig`.

**RoutedFeature + RoutedRuntimeSpec** — `CounterFeature` extends `RoutedFeature` and declares
a `RoutedFeatureLifecycleSpec`. This auto-registers actions, wires the shortcut overlay, and
binds escape-to-exit without the feature explicitly calling action registry APIs.

**ObservableValue + LabelControl** — the counter is an `ObservableValue`. The label subscribes
to it and updates on every change. The button mutates the observable; the label reacts. The
control is never queried for state.

**Shortcut overlay** — F9 toggles the shortcut help overlay, which renders all registered
`ActionSpec` entries automatically.

**Workspace persistence** — "Save Session" calls `WorkspacePersistenceManager.save`;
`bind_runtime` calls `restore` if saved state exists. The restore report's `skipped_settings`
field is checked and logged — it is non-fatal.

**Telemetry** — `configure_telemetry(enabled=True)` is called before bootstrap. After the
session ends, call `analyze_telemetry_records` and `render_telemetry_report`.

### Validation Checklist

1. The application opens a 900×600 window titled "gui_do Reference App".
2. Clicking "Increment" updates the label to "Count: N" on each click.
3. Pressing F9 toggles the shortcut help overlay showing Exit and Shortcuts actions.
4. Pressing Escape exits the application.
5. Clicking "Save Session" writes `./my_app_session.json` without errors.
6. Closing and reopening the application restores the previous session without fatal errors.
7. Loading a workspace with an unknown settings key places it in `skipped_settings`, not an exception.
8. Telemetry records are non-empty after the session ends.

[Back to Table of Contents](#table-of-contents)

---


## Testing, Diagnostics, and Reliability

[Back to Table of Contents](#table-of-contents)

### Contract Tests

The `gui_do` test suite contains a dedicated contract-test layer. These tests verify
framework-level behavioral guarantees that must remain stable across all changes to
implementation details. Run them before any release or significant refactor:

```
python -m pytest -q tests/test_public_api_exports.py tests/test_public_api_docs_contracts.py tests/test_runtime_operating_contracts.py tests/test_boundary_contracts.py tests/test_gui_application_workspace_contracts.py
```

Each file covers a distinct guarantee:

- **`test_public_api_exports.py`** — verifies that all names listed in `gui_do.__all__` are
  importable and present. Catches renames, deletions, and refactors that accidentally break
  the public surface without updating the `__init__.py` exports.
- **`test_public_api_docs_contracts.py`** — verifies that API names match the contract
  documentation in `docs/public_api_spec.md`. If a name is added to exports but not to the
  contract doc (or vice versa), this test fails.
- **`test_runtime_operating_contracts.py`** — verifies runtime guarantees: scheduler budget
  values (fraction, floor, ceiling), event normalization behavior, scene isolation, and
  deterministic candidate ordering in routing. These are the numeric and behavioral contracts
  that this manual references in `[CONTRACT]`-tagged statements.
- **`test_boundary_contracts.py`** — verifies the `gui_do` / `demo_features` boundary: no
  module in `gui_do/` imports from `demo_features/`; consumer code imports from the `gui_do`
  root only.
- **`test_gui_application_workspace_contracts.py`** — verifies workspace restore report
  behavior: all expected fields are present, unknown settings keys appear in `skipped_settings`
  rather than raising, missing settings blocks appear in `missing_settings_blocks`.

### Runtime Behavior Tests

Beyond contract tests, the test suite covers runtime behaviors that validate day-to-day
feature development patterns:

- **Workspace load/save behavior** — verifies that save/restore round-trips through
  `WorkspacePersistenceManager` preserve scene identity and settings values.
- **Overlay, tooltip, and cursor routing** — verifies that overlays correctly intercept or
  pass through events according to their dismissal contract (modal dialogs consume all input;
  toasts consume only intra-bound clicks; tooltips consume nothing).
- **Layout and animation determinism** — verifies that repeated layout passes over identical
  constraints produce identical control positions, and that tweens applied with the same
  parameters produce consistent interpolation curves.
- **Control runtime** — verifies that controls correctly register with focus rings, respond
  to accessibility queries, and produce consistent hit-test results.
- **Accessibility specs** — verifies that `StaticAccessibilitySpec` and
  `AccessibilitySequenceSpec` annotations produce the expected `AccessibilityTree` structure.

### Debug and Trace Tools

`gui_do` provides built-in tools for diagnosing runtime issues without external debuggers:

- **`EventRecorder` / `EventPlayback`** — records a stream of input events to a log file and
  replays it deterministically. Use to reproduce rare interaction bugs: record the session,
  share the log file, replay to reproduce. This is the recommended first step in any
  regression triage workflow.
- **`DebugOverlay`** — renders diagnostic information over the live scene: control bounds,
  focus ring state, hit regions, and spatial index query results. Enable in `build` and
  disable in production by checking a feature flag.
- **`PropertyInspectorPanel`** — a live runtime inspector driven by `PropertyInspectorModel`
  and `PropertyRegistry`. Add `@ui_property` decorators to custom controls to expose their
  attributes for inspection without modifying the draw code.
- **Telemetry log analysis** — `analyze_telemetry_log_file(path)` and `render_telemetry_report`
  provide frame-budget and pipeline profiling from recorded sessions. Use `load_telemetry_log_file`
  to load a saved log for offline analysis.

### Maintainer Release Runbook

Follow this gate sequence before each release:

1. **Run the full contract test suite** (five files listed above). All tests must pass with
   no unexpected xfails.
2. **Verify `__all__` completeness** — run `test_public_api_exports.py` in isolation to
   confirm every name in `__all__` is importable.
3. **Confirm boundary integrity** — run `test_boundary_contracts.py` to confirm no reverse
   imports from `demo_features` to `gui_do`.
4. **Review the Maintainer Diff Checklist** — work through all four categories below. Resolve
   any delta or record explicit TODO entries in the Migration chapter.
5. **Run telemetry baseline** — run the demo application through a representative scenario
   with telemetry enabled. Compare the resulting report against the previous baseline. Flag any
   regression in scheduler budget usage, overlay routing cost, or draw time.
6. **Build the demo** — run `python gui_do_demo.py` and exercise the primary demo features.
   Confirm no import errors, no uncaught exceptions, and no visual regressions.

### Regression Triage Workflow

When a regression is reported, follow this sequence to localize it efficiently:

1. **Reproduce** — use `EventRecorder` / `EventPlayback` to capture a deterministic
   reproduction. If the bug is in a layout or rendering issue, use `DebugOverlay` to snapshot
   control bounds before and after the regression commit.
2. **Trace** — enable telemetry and replay the reproduction. Use `analyze_telemetry_records`
   to identify which system's latency changed.
3. **Localize** — run the relevant contract test file in isolation. If a contract test fails,
   the regression is in the system that contract covers. If all contract tests pass, the
   regression is in a behavior that lacks contract coverage — add a contract test as part of
   the fix.
4. **Test-first** — write a failing test that reproduces the bug before writing the fix.
5. **Patch** — implement the minimal fix. Rerun the full contract suite and the regression test.
6. **Adjacent contracts** — scan for other contracts that exercise the same system path. Run
   them to confirm the fix does not introduce adjacent failures.

### Maintainer Diff Checklist

[Back to Table of Contents](#table-of-contents)

This checklist must be run at the start of every manual regeneration pass. It ensures the
manual stays synchronized with the codebase as it evolves. Work through each category in
order. Record unresolved ambiguities as explicit TODO notes in the
[Migration, Versioning, and Deprecation Notes](#migration-versioning-and-deprecation-notes) section.

#### Inventory Delta Checks

1. **Root export changes** — Compare current `gui_do/__init__.py` tier sections with
   [Appendix D (API Quick Index)](#appendix-d-api-quick-index) and [D.1 (Tier Matrix)](#d1-tier-matrix).
   For every tier block in `__init__.py`:
   - Are all exported names listed in the correct chapter's "Primary public APIs" section?
   - Are any names present in `__init__.py` but missing from the manual?
   - Are any names present in the manual but no longer exported by `__init__.py`?
   - Has a new tier been added? If yes, assign it to the most thematically appropriate
     system chapter and add it to the Tier Matrix.

2. **Docs contract changes** — Review `docs/` for changes since the last manual regeneration:
   - `docs/public_api_spec.md` — has the tier grouping or stability policy changed?
   - `docs/runtime_operating_contracts.md` — have scheduler budget values (fraction/floor/ceiling),
     restore report fields, or cross-system guarantees changed?
   - `docs/architecture_boundary_spec.md` — are there new boundary rules that affect which
     patterns are recommended?
   - `docs/event_system_spec.md` — are there changes to event routing or `EventType` members?

3. **Contract and runtime test additions** — List `tests/` and filter for new files matching
   `test_*_contracts.py` or `test_runtime_*`. For each new file:
   - Identify which system chapter it covers.
   - Ensure that chapter's `[CONTRACT]`-tagged statements are consistent with the new tests.
   - Update the contract test command in [Contract Alignment](#contract-alignment) if the
     set of high-priority tests has changed.

4. **Demo composition pattern changes** — Scan `demo_features/` for new feature packages,
   new `__init__.py` exports, or new usage patterns:
   - Have any new composition patterns been established that the Integration Patterns chapter
     should document?
   - Have any existing patterns been deprecated or replaced?

#### Content Integrity Checks

1. **API reconciliation** — For every system chapter that covers a changed tier:
   - Update the "Primary public APIs and key types" list to match `__init__.py`.
   - Update any code examples that reference removed or renamed symbols.
   - Verify that the [API Quick Index](#appendix-d-api-quick-index) and
     [Tier Matrix](#d1-tier-matrix) reflect the same changes.

2. **Removed API cleanup** — Search `MANUAL.md` for any API name that no longer appears in
   `gui_do/__init__.py`. Remove it from examples, recipes, and appendix entries. If the removal
   is significant, add a migration note in
   [Migration, Versioning, and Deprecation Notes](#migration-versioning-and-deprecation-notes).

3. **Abstraction-level placement** — Verify that Tier 1 APIs are presented first in every
   system chapter that has a Tier 1 entry. Lower-tier APIs should appear in "Advanced patterns"
   or "Primary public APIs" sections, not in the opening overview. This keeps the beginner path
   clean and ensures experienced users can find lower-level hooks.

#### Navigation and Structure Checks

1. **TOC and anchor integrity** — For every new section added to the manual:
   - Confirm the section heading has a matching entry in the [Table of Contents](#table-of-contents)
     with a correct `(#anchor-name)` link.
   - Confirm the anchor name is stable and matches the heading text after GitHub-Flavored Markdown
     anchor normalization (lowercase, spaces to hyphens, punctuation stripped).

2. **Back-to-top links** — Verify that every major section (H2) and every system chapter (H3)
   has a `[Back to Table of Contents](#table-of-contents)` link immediately below its heading.

3. **Chapter order stability** — Confirm the top-level section order matches the fixed order
   defined in the orchestrator prompt. If a structural reorder is intentional, record the reason
   in migration notes.

#### Operational Checks

1. **Contract test run** — Execute the high-priority contract test suite before finalizing:

   ```bash
   python -m pytest -q \
     tests/test_public_api_exports.py \
     tests/test_public_api_docs_contracts.py \
     tests/test_runtime_operating_contracts.py \
     tests/test_boundary_contracts.py \
     tests/test_gui_application_workspace_contracts.py
   ```

   All tests must pass. Any failure indicates a discrepancy between the manual content,
   the contract docs, and the code that must be resolved before publication.

2. **End-to-end reference validation** — Verify the assumptions made in the
   [End-to-End Reference Application](#end-to-end-reference-application) chapter against the
   current demo runner. Confirm that the listed feature classes, spec types, and configuration
   patterns still exist and function as described.

3. **Unresolved ambiguities** — Record any gaps discovered during this checklist pass as
   explicit TODO notes in
   [Migration, Versioning, and Deprecation Notes](#migration-versioning-and-deprecation-notes)
   rather than leaving them as silent omissions.

---

## Performance and Scaling Guidance

[Back to Table of Contents](#table-of-contents)

### Scheduler Budget Contract

The cooperative scheduler operates under a frame-budget contract documented in
`docs/runtime_operating_contracts.md` §6. The budget for each frame is:

- **fraction** = `0.12` of `dt_ms` (12% of the elapsed frame time)
- **floor** = `0.5 ms` (minimum budget even on very fast frames)
- **ceiling** = `4.0 ms` (maximum budget even on very slow frames)

This contract ensures that the scheduler cannot starve rendering under slow frames (the ceiling
prevents unlimited task expansion) and cannot under-utilize on fast frames (the floor provides
a minimum slice). The values are verified by `tests/test_runtime_operating_contracts.py`.
Application code that runs in scheduled tasks should be written to complete within a single
budget slice; tasks that exceed the slice are resumed on the next frame.

### Dirty-Region Rendering

For scenes with complex or frequently changing visual content, `DirtyRegionTracker` is the
primary frame-rate optimization. The tracker accumulates dirty rects over a frame and maintains
an incremental union rect. `overlaps_dirty(rect)` is O(1) because it tests against the union
rect, not each individual dirty rect. `consume_dirty_regions()` returns the accumulated dirty
list and resets the tracker for the next frame.

The recommended pattern is to mark only changed regions as dirty during `on_update`, then in
`draw`, check `overlaps_dirty(my_rect)` before re-rendering. For large scenes, this reduces
per-frame draw cost from O(all controls) to O(changed controls).

### Virtualization and Incremental Rendering

For features that display large collections (thousands of items), `VirtualizationCore` and
`VirtualizedWindow` provide O(visible rows) rendering by maintaining a sliding window over
the full dataset. `RecyclePool` recycles control instances as rows scroll in and out of view,
eliminating the cost of constructing new control objects on every scroll event.

`ListDiffCalculator` reduces the cost of incremental updates: instead of rebuilding the full
list on every data change, compute a minimal patch (`DiffInsert`, `DiffRemove`, `DiffMove`)
and apply only the changed operations to the live list view. This is especially important
for features that subscribe to fast-changing data streams.

### Practical Scaling Checklist

- **Enforce scene-scoped updates** — features should only process updates when their scene is
  active. Guard `on_update` and event handlers with a scene-active check.
- **Avoid per-frame full collection reallocation** — use `ObjectPool` for high-churn objects
  such as particle records, event records, and temporary render items.
- **Debounce expensive form and search operations** — use `Debouncer` to rate-limit calls
  to validation pipelines, search queries, and layout recomputes triggered by text input.
- **Use `DataflowPipeline` + `CancellationToken`** — for any background processing that may
  be preempted by new user input; this prevents stale results from appearing in the UI.
- **Profile representative user interactions** — idle loop telemetry does not reflect real
  frame cost. Profile search queries, scene transitions, and scroll events.
- **Use `DirtyRegionTracker` to gate draw regions** — even simple scenes benefit from skipping
  unchanged regions during the draw pass.
- **Prefer `SortFilterProxySource`** — for filtered list views, prefer proxy-based filtering
  over allocating new lists; the proxy maintains the original source reference.

[Back to Table of Contents](#table-of-contents)

---

## Migration, Versioning, and Deprecation Notes

[Back to Table of Contents](#table-of-contents)

### Versioned Snapshot Strategy

When a workspace snapshot schema changes between application versions, `SnapshotMigrator`
provides a BFS migration graph that transforms old snapshots forward to the current schema
without requiring all-at-once rewrites.

The recommended workflow:

1. Write snapshots with `make_snapshot(current_version, state_dict)`. The resulting
   `VersionedSnapshot` embeds the `SchemaVersion` alongside the payload.
2. On load, call `read_version(raw)` to extract the stored version before deserializing the
   payload. This allows early detection of unsupported or future versions.
3. Pass the raw snapshot to `SnapshotMigrator.migrate(snapshot)`. The migrator walks
   registered `MigrationStep` objects in BFS order from the stored version to the current
   schema version, applying each step's `migrate` function in sequence.
4. Restore the migrated data into the runtime.

`MigrationStep` objects are registered on `MigrationRegistry`, one per version transition.
Each step knows its source and target version and provides a pure function that transforms
the data dict. `MigrationError` is raised if no registered path exists from the stored
version to the current version.

**Contract:** old snapshots must never be silently discarded. If migration fails (no path),
the application must inform the user and provide a recovery option — either manual migration
or starting with defaults while preserving the old file.

### Deprecation Handling

The recommended deprecation policy for `gui_do` changes:

- **Prefer additive transitions** — add new fields or parameters alongside old ones. Mark
  old names with Python deprecation warnings (`warnings.warn(..., DeprecationWarning)`).
  Keep old behavior functional for at least one release cycle.
- **Remove legacy behavior only with a migration path** — before removing a deprecated API,
  document the replacement and provide a migration note in this section.
- **Centralize all deprecation notes here** — this section is the canonical record of pending
  and completed deprecations.

As of this generation, no formal deprecations are cataloged in the public API. Maintainers
should add entries to this section whenever a formal deprecation is introduced.

### Upgrade Checklist

When upgrading the `gui_do` version used by a dependent application:

1. Run the full contract test suite before the upgrade.
2. Apply the upgrade and run the contract test suite again. Investigate all new failures.
3. Verify that all consumer imports use `from gui_do import ...` from the root; confirm no
   submodule imports that bypass the public surface.
4. Check action, input, and focus routing behavior in all active scenes for behavioral
   regressions.
5. Load an existing workspace file and inspect the restore report for new entries in
   `skipped_settings` or `missing_settings_blocks`.
6. Re-run telemetry baseline scenarios and compare to the pre-upgrade baseline report.

[Back to Table of Contents](#table-of-contents)

---

## FAQ and Troubleshooting

[Back to Table of Contents](#table-of-contents)

**Q: Should I build apps directly with controls or with features?**

Use features as the architectural unit. Controls are implementation details inside feature
boundaries. Features provide lifecycle orchestration, event routing, observable wiring, and
clean teardown. A control alone cannot do any of these things — it has no `bind_runtime`,
no `on_update`, and no clean way to subscribe to observables or actions. Every interactive
behavior in a `gui_do` application belongs in a feature; controls are the visual representation
that features build and manage.

**Q: When should I use `RoutedFeature` over `Feature`?**

Use `RoutedFeature` when you need topic-based message dispatch, declarative keyboard shortcut
binding, shortcut overlay integration, or task-panel focus toggle management — wired from a
single `RoutedRuntimeSpec`. If your feature only needs basic lifecycle phases (`build`,
`bind_runtime`, `on_update`, `draw`, `shutdown_runtime`) and a control tree with no
cross-system routing requirements, plain `Feature` is sufficient and has less overhead.

**Q: Why are some key handlers not firing?**

Check in order: (1) **Focus ownership** — is another control capturing keyboard input? Use
`DebugOverlay` to confirm which control holds focus. (2) **Window scope** — is the action
registered as window-scoped but the target window is hidden or inactive? (3) **Overlay modal
capture** — is a modal overlay consuming all keyboard events before they reach your handler?
(4) **Scene scope** — is the action registered for a different scene than the currently
active one? Use `EventRecorder` to trace the exact event routing sequence.

**Q: Why do toast clicks not pass through to underlying controls?**

By contract, a toast's bounding rect consumes left-click events to prevent accidental
activation of controls beneath the toast. This is an intentional part of the toast routing
contract. If you need intentional interaction with a toast, use the `on_click` callback in
the toast API. If you need controls beneath a toast to remain interactive, dismiss the toast
before displaying the interactive content.

**Q: How do I avoid breaking workspace restore across versions?**

Use `VersionedSnapshot` with `SchemaVersion` and register `MigrationStep` objects for every
schema change. On each load, call `read_version` before deserializing and run the migrator.
Always inspect the restore report: `skipped_settings` identifies unknown keys (non-fatal,
but worth logging), and `missing_settings_blocks` identifies expected blocks that were absent
from the snapshot. Handle these gracefully — for example, with a toast notification — rather
than raising exceptions.

**Q: How do I confirm my API usage is within the supported surface?**

Use explicit named imports from the `gui_do` root: `from gui_do import Feature`. Run
`tests/test_public_api_exports.py` to verify all names you use are present in `gui_do.__all__`.
Avoid importing from internal submodules (`gui_do.features.*`, `gui_do.controls.*`, etc.) —
these are not part of the public contract and may change without notice.

**Q: Why does my feature's `bind_runtime` run before my sibling's `build`?**

It does not. The framework guarantees that all features in a scene complete their `build`
calls before any feature's `bind_runtime` is called. This ordering is enforced by the scene
activation sequence in the bootstrap runtime. If you observe ordering problems, confirm that
the affected features are declared in the same scene in their `SceneBundleBindingSpec` entries
— features in different scenes do not share this ordering guarantee across scene boundaries.

**Q: How do I add a keyboard shortcut without manually wiring every event handler?**

Declare an `ActionSpec` in `HostApplicationConfig.action_entries` with the desired `key`.
Include it in a `RoutedRuntimeSpec` via `ShortcutOverlaySpec` or `ActionHotkeySpec`. The
framework registers the action with the action registry and input map automatically, and the
shortcut appears in the help overlay without any additional wiring in your event handlers.

[Back to Table of Contents](#table-of-contents)

---

## Appendix A: Glossary

[Back to Table of Contents](#table-of-contents)

**Feature** — the primary lifecycle-managed unit of application behavior in `gui_do`. A feature
encapsulates a coherent piece of UI or logic: it creates controls in `build`, wires observables
and actions in `bind_runtime`, processes time-based work in `on_update`, renders custom content
in `draw`, and cleans up in `shutdown_runtime`. Features belong to exactly one scene and are
never shared across scenes. The four feature types (`DirectFeature`, `Feature`, `LogicFeature`,
`RoutedFeature`) differ in which host attributes they can access and what routing capabilities
they provide.

**Spec** — a declarative data object that describes runtime wiring, configuration, or behavior
without executing it. Specs are pure data: they are constructed before bootstrap and processed
by the framework during activation. Examples include `ActionSpec`, `WindowSpec`, `RoutedRuntimeSpec`,
and `FontRoleBindingSpec`. Using specs instead of procedural registration keeps bootstrap code
readable and testable.

**Host** — a plain Python namespace object passed to each lifecycle method. It receives all
runtime members as attributes during bootstrap: `app`, `controls`, `action_registry`, `toast_manager`,
etc. Features declare which host attributes they require via `HOST_REQUIREMENTS`. The host is the
only mechanism through which features interact with framework services.

**Scene** — a named top-level interaction context. Each scene is an independently specified
collection of features, windows, chrome elements, and actions. Activating a scene activates its
features; deactivating it runs their `shutdown_runtime`. Features from different scenes are
completely isolated at the control, event, and observable levels.

**Window presentation** — the system that manages floating or docked UI surfaces within a scene:
which windows are registered, which are visible, how the task panel toggle buttons drive
visibility, and how `FocusScopeManager` excludes hidden windows from the focus ring.

**Routed runtime** — a declarative bundle of hotkeys, shortcut overlays, task-panel focus
toggles, and message subscriptions for a feature, declared in `RoutedRuntimeSpec` and wired
via `bind_routed_feature_lifecycle`. Features that use routed runtime avoid manually calling
action registry and input map APIs.

**Observable** — a value container with automatic subscriber notification on change.
`ObservableValue` is the primary type. Subscribers are callables registered via `subscribe`;
they are called synchronously when the value changes via `set`. Subscriptions must be canceled
in `shutdown_runtime` to prevent memory leaks. `ComputedValue` derives its value from other
observables and recomputes automatically.

**Workspace state** — the persisted runtime context saved by `WorkspacePersistenceManager`.
It contains the active scene name, feature-level states, scene node positions, and named
settings values. On restore, the runtime switches to the saved scene, replays feature states,
and applies settings. The restore report identifies applied, skipped, and missing entries.

**Contract test** — an automated test in the `tests/` suite that verifies a framework-level
behavioral guarantee rather than implementation details. Contract tests cover the scheduler
budget, event routing, workspace restore behavior, boundary integrity, and API surface
completeness. They are intended to remain stable across refactors and serve as the primary
compatibility signal for library consumers.

**Tier** — a grouping of public API exports in `gui_do/__init__.py` organized by abstraction
level and recommended usage priority. Tier 1 is the most stable and most commonly needed;
higher tiers provide more specialized capabilities. Tier 19 contains infrastructure internals
not intended for application code. See the Tier Matrix in §D.1.

[Back to Table of Contents](#table-of-contents)

---

## Appendix B: Lifecycle and Event Routing Sequence

[Back to Table of Contents](#table-of-contents)

The following numbered sequence is the authoritative reference for the order of operations
from bootstrap through frame rendering and scene transitions.

1. **Bootstrap** — `bootstrap_host_application(config)` reads `HostApplicationConfig`,
   initializes pygame, builds the `GuiApplication`, registers actions and input maps, loads
   fonts, and prepares the initial scene.
2. **Scene activation — build pass** — all features in the initial scene receive their
   `build(host)` call in declaration order. All features in the scene complete `build`
   before any feature's `bind_runtime` is called.
3. **Scene activation — bind pass** — all features receive `bind_runtime(host)` in declaration
   order. At this point, all sibling controls are already built and all host services are
   available.
4. **Runtime loop begins** — `GuiApplication.run_entrypoint()` enters the frame loop.
5. **Event normalization** — raw pygame events are converted to `GuiEvent` objects with
   `EventType` and normalized coordinates, captured state, and focus context.
6. **Routing pass** — `GuiEvent` objects pass through the overlay/focus/window/scene routing
   layers in order: modal overlay (if active) → window focus → scene event routing →
   feature `handle_event` calls.
7. **Feature `handle_event`** — features receive events in routing order. An event consumed
   by a higher-priority handler (overlay, modal dialog) does not reach lower-priority handlers.
8. **Feature `on_update`** — features receive the frame's `dt` value in declaration order.
   After all feature `on_update` calls, the cooperative scheduler dispatches pending scheduled
   tasks within the frame budget.
9. **Draw pass** — feature `draw` calls in declaration order, then control tree rendering,
   then overlay rendering, then present to the display surface.
10. **Scene transition** — on a scene switch, departing features receive `shutdown_runtime`
    in reverse declaration order. Arriving features receive `build` then `bind_runtime` in
    declaration order.
11. **App exit** — on `GuiApplication.quit()` or the escape-to-exit action, active features
    receive `shutdown_runtime` in reverse declaration order. If a workspace auto-save is
    configured, it runs before exit.

[Back to Table of Contents](#table-of-contents)

---

## Appendix C: System Dependency Map

[Back to Table of Contents](#table-of-contents)

This map describes the dependency relationships between the major systems. Understanding
these relationships helps maintainers identify the impact radius of a change.

**Bootstrap (Tier 1)** is the integration layer. It depends on every other system: spec types,
feature lifecycle, scene and window presentation, action and input systems, font and theme
configuration, and telemetry. Changes to any spec type must be verified against the bootstrap
spec processing path.

**Features (Tiers 1–2)** depend on the control system, observable state, event and action
systems, and focus management. Features are the primary consumer of all other systems — any
change to a system that features use must be checked for feature-level behavioral impact.

**Layout (Tier 8) and Focus (Tier 4)** depend on the control tree and scene/window visibility
state. `FocusManager` and `LayoutManager` operate on the same control tree that window
presentation manages. Hiding a window (scene/window presentation) must notify both the layout
and focus systems.

**Overlays (Tier 9)** depend on event routing and focus policy. Overlay managers intercept
events before feature handlers and may lock the focus scope. Changes to overlay routing
directly affect all features that use the event system.

**Persistence (Tiers 11, 32)** depends on state models and scene/window registration.
`WorkspacePersistenceManager` records scene identity and settings; `SnapshotMigrator` depends
on stable `SchemaVersion` contracts. Changes to scene names or settings keys are breaking
changes from the persistence perspective.

**Scheduling (Tier 5) and Animation** depend on the feature update loop and scene scope.
The cooperative scheduler and tween system are driven by `on_update`; they are scoped to the
active scene and must be cleaned up in `shutdown_runtime`.

**Telemetry and Introspection (Tiers 7, 17)** cross-cut all runtime layers. They observe
the frame loop, layout pass, event routing, and scheduler without altering behavior. They are
safe to enable or disable without breaking correctness.

**Audio (Tier 20)** depends on pygame's mixer and is surfaced through `SoundEventBus`. It
has no dependency on the control tree or layout system, making it safe to modify independently.

**Service scope (Tier 25)** is available at any tier as a dependency injection container.
`ServiceScope` and `ScopeStack` can be used to provide optional services to features without
adding them to the host namespace.

[Back to Table of Contents](#table-of-contents)

---

## Appendix D: API Quick Index

[Back to Table of Contents](#table-of-contents)

This index organizes all public `gui_do` exports by functional topic. Every name in
`gui_do.__all__` appears in exactly one topic group. Use this index when you know the
functional area but not the exact type name. For tier-to-system mappings, see §D.1.

**Bootstrap and Application Setup**
`bootstrap_host_application`, `build_host_application_config`, `HostApplicationConfig`,
`HostApplicationBindingSpec`, `FeatureWindowBundleBindingSpec`, `SceneBundleBindingSpec`,
`TelemetryConfig`, `GuiApplication`, `create_display`, `SceneTransitionManager`, `SceneTransitionStyle`

**Feature Types and Lifecycle**
`Feature`, `DirectFeature`, `LogicFeature`, `RoutedFeature`, `FeatureSpec`,
`RoutedRuntimeSpec`, `RoutedFeatureLifecycleSpec`, `RuntimeSceneSpec`,
`bind_routed_feature_lifecycle`, `shutdown_routed_feature_lifecycle`,
`bind_routed_scene_lifecycle`, `setup_routed_feature_runtime`, `register_routed_feature_companions`,
`setup_routed_runtime`, `shutdown_routed_runtime`

**Scene, Window, and Task Panel**
`ScenePresentationModel`, `WindowSpec`, `AnchoredWindowSpec`, `WindowPresenter`,
`SceneTaskPanelSpec`, `TaskPanelButtonSpec`, `TaskPanelWindowToggleGroupSpec`,
`TaskPanelFocusToggleSpec`, `TaskPanelSceneNavButtonSpec`,
`TabbedPresenterSpec`, `TabBuilderSpec`, `FeatureWindowBundleBindingSpec`, `WindowToggleBindingSpec`,
`SceneMenuStripSpec`, `set_window_visible_state`, `toggle_window_visibility`,
`create_anchored_feature_window`, `create_feature_presented_window`,
`add_window_scene_menu_strip`, `ensure_scene_task_panel`, `add_task_panel_buttons`,
`add_task_panel_window_toggle_group`, `add_task_panel_scene_nav_button`,
`add_window_toggle_task_panel_controls`, `ActiveTabUpdateRouter`, `TabLayoutContext`

**Specs and Configuration**
`ActionSpec`, `ActionHotkeySpec`, `FontRoleBindingSpec`, `CursorSpec`, `CursorBindingSpec`,
`StaticAccessibilitySpec`, `AccessibilitySequenceSpec`,
`ShortcutOverlaySpec`, `ShortcutSection`, `ShortcutEntry`,
`NotificationSpec`, `ControlDefinition`, `build_specs_from_column_section`,
`setup_standard_font_roles`

**Events and Routing**
`GuiEvent`, `EventType`, `EventPhase`, `EventManager`, `EventRecorder`, `EventPlayback`,
`GuiEventPump`, `EventFilter`, `EventBus`, `EventSubscription`

**Actions and Input Mapping**
`ActionManager`, `ActionRegistry`, `ActionHandle`, `InputMap`, `InputBinding`,
`HotkeyListener`, `GestureRecognizer`, `ActionMiddleware`

**Focus and Focus Scope**
`FocusManager`, `FocusScope`, `FocusScopeManager`, `WindowFocusManager`, `FocusRing`

**State and Observables**
`ObservableValue`, `ComputedValue`, `PresentationModel`, `ObservableList`, `ObservableDict`,
`Binding`, `BindingGroup`, `AppStateStore`, `StateSelector`, `StateTransaction`

**Controls — Primary (Tier 12)**
`PanelControl`, `LabelControl`, `ButtonControl`, `ToggleControl`, `SliderControl`,
`ScrollbarControl`, `CanvasControl`, `CanvasEventPacket`, `CanvasViewport`, `FrameControl`,
`ImageControl`, `ArrowBoxControl`, `ButtonGroupControl`, `TabControl`, `TabItem`,
`DockWorkspacePanel`

**Controls — Extended (Tier 13)**
`TextInputControl`, `TextAreaControl`, `RichLabelControl`, `DropdownControl`, `DropdownOption`,
`ListViewControl`, `ListItem`, `OverlayPanelControl`, `DataGridControl`, `GridColumn`, `GridRow`,
`TreeControl`, `TreeNode`, `SplitterControl`, `SpinnerControl`, `RangeSliderControl`,
`ColorPickerControl`, `ScrollViewControl`, `ProgressBarControl`, `AnimatedImageControl`,
`ErrorBoundary`, `WindowControl`, `TaskPanelControl`, `MenuBarControl`, `MenuEntry`,
`SceneMenuStripControl`, `NotificationPanelControl`, `PropertyInspectorPanel`,
`ToolbarControl`, `ToolbarItem`, `StatusBarControl`, `StatusSlot`, `ExpanderControl`,
`DatePickerControl`, `TimePickerControl`, `BreadcrumbControl`, `BreadcrumbItem`,
`SplitButtonControl`, `SplitButtonOption`, `ChipInputControl`

**Layout**
`LayoutAxis`, `LayoutManager`, `WindowTilingManager`, `ConstraintLayout`, `AnchorConstraint`,
`DockPane`, `DockTabs`, `DockSplit`, `DockWorkspace`, `FlexLayout`, `FlexItem`, `FlexDirection`, `FlexAlign`, `FlexJustify`,
`GridLayout`, `GridTrack`, `GridPlacement`, `CellCaretLayout`, `CellCaretState`,
`LayoutAnimator`, `LayoutPass`, `MeasureContext`, `ArrangeContext`, `LayoutRoot`,
`ResponsiveLayout`, `Breakpoint`, `SnapGrid`, `AlignmentGuide`, `SnapComposer`, `SnapTarget`,
`FlowLayout`, `FlowItem`, `Viewport`,
`ConstraintAttr`, `LayoutConstraint`, `ConstraintSet`, `ConstraintLayoutEngine`, `AdaptivePolicy`, `resolve_adaptive_policy`,
`MeasureMode`, `MeasurePolicy`, `VirtualizedWindow`, `RecyclePool`, `VirtualizationCore`

**Overlays and Transient Surfaces**
`OverlayManager`, `OverlayHandle`, `Alignment`, `PlacementResult`, `PopupPlacement`, `Side`, `compute_popup_rect`,
`DialogManager`, `DialogHandle`, `ToastManager`, `ToastHandle`, `ToastSeverity`,
`ContextMenuManager`, `ContextMenuItem`, `ContextMenuHandle`,
`CommandPaletteManager`, `CommandEntry`, `CommandPaletteHandle`,
`TooltipManager`, `TooltipHandle`, `MenuBarManager`,
`FileDialogManager`, `FileDialogOptions`, `FileDialogHandle`,
`NotificationCenter`, `NotificationRecord`, `ResizeManager`,
`CursorManager`, `CursorHandle`, `CursorShape`,
`DragDropManager`, `DragPayload`, `ClipboardManager`,
`TransferData`, `TransferManager`, `ShortcutHelpOverlay`

**Forms and Validation**
`FormModel`, `FormField`, `ValidationRule`, `FieldError`, `FormSchema`, `SchemaField`,
`DocumentModel`, `WizardFlow`, `WizardStep`, `WizardHandle`,
`RequiredValidator`, `LengthValidator`, `PatternValidator`, `RangeValidator`, `DependentValidator`, `CompositeValidator`,
`AsyncFieldValidator`, `AsyncFormValidator`,
`FieldSchema`, `FieldGraphSchema`, `ValidationPolicy`, `SchemaFormRuntime`

**Text and Localization**
`TextFormatter`, `NumericFormatter`, `PatternFormatter`, `FixedPatternFormatter`,
`TextFlow`, `TextSpan`, `TextSearcher`, `TextMatch`, `StringTable`, `LocaleRegistry`

**Data and Collections**
`VirtualItemSource`, `FixedItemSource`, `SortFilterProxySource`, `AsyncDataProvider`, `LoadState`, `LoadStateKind`,
`ObjectPool`, `DataCache`, `CacheStats`, `ListDiffCalculator`, `ListDiff`, `DiffInsert`, `DiffRemove`, `DiffMove`

**Dataflow Pipeline**
`CancellationToken`, `PipelineStage`, `DataflowPipeline`, `PipelineHandle`

**Graphics and Rendering**
`BuiltInGraphicsFactory`, `DirtyRegionTracker`, `DrawContext`, `DrawPhase`, `AssetRegistry`, `DebugOverlay`,
`SurfaceCompositor`, `Layer`, `ShapeRenderer`, `SurfaceEffects`, `VectorPath`,
`SpriteSheet`, `FrameAnimation`, `ParticleSystem`, `Emitter`, `ParticleLayer`,
`TileSet`, `TileMap`, `RenderTarget`, `LiveRenderTarget`, `OffscreenRenderTarget`,
`create_render_target`, `create_surface`, `Node2D`, `SceneGraph2D`, `Camera2D`

**Audio**
`SoundCue`, `SoundBankRegistry`, `SoundEventBus`

**Scheduling and Animation**
`TaskEvent`, `TaskScheduler`, `Timers`, `TweenManager`, `TweenHandle`, `Easing`,
`AnimationSequence`, `AnimationHandle`, `TransitionManager`, `TransitionSpec`, `TransitionEvent`,
`AnimationStateMachine`, `AnimationTransitionMode`, `SceneTimeline`, `Debouncer`, `Throttler`,
`CooperativeScheduler`, `CoroutineHandle`, `Pause`, `Sleep`, `WaitForEvent`, `WaitForSignal`, `WaitUntil`, `WaitForAll`

**Theme and Fonts**
`FontManager`, `FontRoleRegistry`, `ColorTheme`, `ThemeManager`, `DesignTokens`, `ScopedTheme`, `ScopedThemeManager`,
`ThemeInvalidationBus`

**Telemetry**
`TelemetryCollector`, `TelemetrySample`, `configure_telemetry`, `telemetry_collector`,
`analyze_telemetry_log_file`, `analyze_telemetry_records`, `load_telemetry_log_file`, `render_telemetry_report`

**Introspection**
`SceneSpatialIndex`, `ui_property`, `PropertyDescriptor`, `PropertyRegistry`, `property_registry`,
`PropertyInspectorModel`, `InspectedProperty`

**Accessibility**
`AccessibilityRole`, `LivePoliteness`, `AccessibilityNode`, `AccessibilityTree`,
`AccessibilityAnnouncement`, `AccessibilityBus`

**Persistence and State Management**
`CommandHistory`, `Command`, `CommandTransaction`, `StateMachine`, `HierarchicalStateMachine`,
`Router`, `RouteEntry`, `SettingsRegistry`, `SettingDescriptor`,
`WorkspaceState`, `WorkspacePersistenceManager`, `DEFAULT_WORKSPACE_STATE_PATH`,
`SceneSnapshot`, `NodeSnapshot`, `UndoContextManager`

**Snapshot and Migration**
`SchemaVersion`, `VersionedSnapshot`, `MigrationStep`, `MigrationRegistry`, `SnapshotMigrator`,
`MigrationError`, `make_snapshot`, `read_version`

**Service Scope**
`ServiceKey`, `ServiceScope`, `ScopeStack`

**Interaction State Machine**
`InteractionStateMachine`, `InteractionPhase`, `InteractionContext`

### D.1 Tier Matrix

[Back to Table of Contents](#table-of-contents)

The tier matrix maps every public tier in `gui_do/__init__.py` to its corresponding system
chapter, stability level, and primary contents. Tiers are listed in ascending order; Tier 1
is the most stable entry point for new applications.

| Tier | Name | System Chapter | Key Exports (representative) |
|------|------|---------------|------------------------------|
| 1 | Primary Entry Points & Data-Driven APIs | 8.1, 8.2 | `bootstrap_host_application`, `HostApplicationConfig`, `Feature`, `DirectFeature`, `LogicFeature`, `RoutedFeature`, `FeatureSpec`, `WindowSpec`, `RuntimeSceneSpec`, `ActionSpec` |
| 2 | Core Application & Scene Management | 8.1 | `GuiApplication`, `create_display`, `SceneTransitionManager`, `SceneTransitionStyle` |
| 3 | Essential Data & State Management | 8.4 | `ObservableValue`, `PresentationModel`, `ComputedValue`, `ObservableList`, `ObservableDict`, `Binding`, `BindingGroup` |
| 4 | Events, Actions, Focus & Input | 8.3, 8.7 | `GuiEvent`, `EventType`, `EventPhase`, `EventManager`, `ActionManager`, `InputMap`, `FocusManager`, `FocusScope` |
| 5 | Scheduling & Animation | 8.10 | `TaskScheduler`, `Timers`, `TweenManager`, `CooperativeScheduler`, `TransitionManager`, `AnimationStateMachine` |
| 6 | Theme & Font Management | 8.12 | `ThemeManager`, `ColorTheme`, `FontManager`, `FontRoleRegistry`, `ScopedTheme` |
| 7 | Telemetry & Diagnostics | 8.16 | `TelemetryCollector`, `TelemetrySample`, `configure_telemetry`, `telemetry_collector` |
| 8 | Layout & Spatial | 8.6 | `LayoutManager`, `ConstraintLayout`, `DockWorkspace`, `FlexLayout`, `GridLayout`, `SnapGrid`, `Viewport` |
| 9 | Overlay Managers & Windows | 8.8 | `OverlayManager`, `DialogManager`, `ToastManager`, `ContextMenuManager`, `CommandPaletteManager`, `TooltipManager`, `FileDialogManager` |
| 10 | Forms & Data Binding | 8.13 | `FormModel`, `FormField`, `FormSchema`, `WizardFlow`, `DocumentModel` |
| 11 | State & Persistence | 8.11 | `StateMachine`, `HierarchicalStateMachine`, `CommandHistory`, `WorkspaceState`, `WorkspacePersistenceManager` |
| 12 | Primary Controls | 8.5 | `PanelControl`, `LabelControl`, `ButtonControl`, `ToggleControl`, `SliderControl`, `CanvasControl`, `TabControl` |
| 13 | Extended Controls | 8.5 | `TextInputControl`, `TextAreaControl`, `DropdownControl`, `ListViewControl`, `DataGridControl`, `TreeControl`, `WindowControl`, `WindowPresenter` |
| 14 | Text & Localization | 8.13 | `TextFormatter`, `TextFlow`, `TextSearcher`, `LocaleRegistry`, `StringTable` |
| 15 | Data & Collections | 8.14 | `VirtualItemSource`, `SortFilterProxySource`, `AsyncDataProvider`, `ObjectPool`, `ListDiffCalculator` |
| 16 | Graphics & Rendering | 8.15 | `DrawContext`, `DirtyRegionTracker`, `AssetRegistry`, `SurfaceCompositor`, `ParticleSystem`, `TileMap`, `SceneGraph2D` |
| 17 | Introspection & Inspection | 8.16 | `PropertyRegistry`, `ui_property`, `PropertyInspectorModel`, `SceneSpatialIndex` |
| 18 | Advanced Runtime & Bootstrapping | 8.2, 8.9 | `setup_routed_runtime`, `ensure_scene_task_panel`, `add_task_panel_buttons`, `ActiveTabUpdateRouter` |
| 19 | Infrastructure & Internals | (avoid) | `UiEngine` |
| 20 | Audio | 8.15 | `SoundCue`, `SoundBankRegistry`, `SoundEventBus` |
| 21 | Accessibility | 8.7 | `AccessibilityRole`, `AccessibilityNode`, `AccessibilityTree`, `AccessibilityBus` |
| 22 | Theme Invalidation | 8.12 | `ThemeInvalidationBus` |
| 23 | Undo Context Routing | 8.11 | `UndoContextManager` |
| 24 | Async Form Validation | 8.13 | `AsyncFieldValidator`, `AsyncFormValidator` |
| 25 | Scoped Service Graph | 8.1 | `ServiceKey`, `ServiceScope`, `ScopeStack` |
| 26 | Cancelable Dataflow Pipeline | 8.14 | `DataflowPipeline`, `PipelineStage`, `CancellationToken`, `PipelineHandle` |
| 27 | Transactional App State Store | 8.4 | `AppStateStore`, `StateSelector`, `StateTransaction` |
| 28 | Adaptive Constraint Layout v2 | 8.6 | `ConstraintLayoutEngine`, `ConstraintSet`, `LayoutConstraint`, `AdaptivePolicy` |
| 29 | Unified Virtualization Core | 8.6 | `VirtualizationCore`, `VirtualizedWindow`, `RecyclePool` |
| 30 | Interaction State Machine Framework | 8.3 | `InteractionStateMachine`, `InteractionPhase`, `InteractionContext` |
| 31 | Schema-Driven Form Runtime | 8.13 | `SchemaFormRuntime`, `FieldGraphSchema`, `ValidationPolicy` |
| 32 | Portable Snapshot & Migration Layer | 8.11 | `SnapshotMigrator`, `MigrationRegistry`, `VersionedSnapshot`, `MigrationStep` |

### D.2 Selection Heuristics

[Back to Table of Contents](#table-of-contents)

Use these decision rules to choose the right tier and type when you are unsure where to start.

**Primary rules:**
1. **Start at Tier 1.** If `HostApplicationConfig` + `bootstrap_host_application` + `Feature`
   types solve the problem, stop there. Do not descend to lower tiers unless you have a
   specific need that Tier 1 does not cover.
2. **Descend one tier at a time.** When Tier 1 is insufficient, look at Tier 2 or 3 before
   skipping to Tier 10. The tiers are ordered by abstraction level; lower-tier types always
   compose better with other lower-tier types.
3. **Use Tier 18 helpers when extending bootstrap behavior.** They are stable extension points
   designed for advanced scene and window wiring that cannot be expressed in Tier 1 specs alone.
4. **Never import from `gui_do.*` submodules.** Always use `from gui_do import ClassName`.
   Internal submodule APIs are not stable and may change without notice.
5. **Avoid Tier 19 (`UiEngine`) in application code.** Tier 19 is framework internals. If you
   find yourself needing it, open a feature request — the need should be surfaced as a Tier 18
   or Tier 1 API.

**Decision shortcuts:**
- Need to set up an application → `HostApplicationConfig` + `bootstrap_host_application`
- Need cross-feature behavior → lifecycle specs + `RoutedRuntimeSpec` + routed wiring helpers
- Need heavy dataset UI (thousands of items) → virtualization/dataflow APIs before custom loops
- Need maintainable persistence across versions → `WorkspacePersistenceManager` + `SnapshotMigrator`
- Need discoverable keyboard shortcuts → `ShortcutOverlaySpec` in `RoutedRuntimeSpec`
- Need flexible form validation → `SchemaFormRuntime` + `ValidationPolicy` + optional `AsyncFormValidator`
- Need particle effects or custom 2D rendering → `ParticleSystem` / `SceneGraph2D` inside `draw`
- Need audio cue playback → `SoundEventBus` + `SoundBankRegistry`

[Back to Table of Contents](#table-of-contents)

---

## Appendix E: Architecture Templates

[Back to Table of Contents](#table-of-contents)

These four templates provide starting configurations for common application archetypes. Each
template describes the key architectural decisions and which `gui_do` systems to use.

### Template 1: Small Single-Scene App

Use for: personal tools, utilities, focused single-workflow applications.

- **Scenes:** 1 scene, 2–4 `Feature` instances.
- **State:** `ObservableValue` instances owned by features; no cross-feature state sharing.
- **Actions:** `ActionSpec` entries for primary commands; `RuntimeSceneSpec` with
  `bind_escape_to_exit=True`.
- **Chrome:** no task panel, no window presenter. A single root `PanelControl` per feature.
- **Persistence:** optional; if needed, `WorkspacePersistenceManager` with a single settings block.
- **Testing:** contract tests for public API + at least one behavior test per feature.

### Template 2: Multi-Window Workbench

Use for: IDEs, editors, design tools, dashboards with multiple independent panels.

- **Scenes:** 2+ scenes with `SceneMenuStripSpec` for navigation.
- **Task panel:** `SceneTaskPanelSpec` with per-window `TaskPanelFocusToggleSpec` for every
  managed window.
- **Windows:** `WindowPresenter` subclass per window; `FeatureWindowBundleBindingSpec` for
  self-contained feature+window+task-panel-button wiring.
- **Shortcuts:** `RoutedRuntimeSpec` with `ShortcutOverlaySpec` per primary feature.
- **Persistence:** `WorkspacePersistenceManager` with per-window visibility and position settings.
- **Testing:** include `test_*_window_contracts.py` validating focus toggle behavior.

### Template 3: Data-Heavy Analysis Tool

Use for: log viewers, data explorers, monitoring dashboards.

- **Data layer:** `AsyncDataProvider` → `SortFilterProxySource` → `VirtualizationCore`.
- **Processing:** `DataflowPipeline` with `CancellationToken` for background transforms.
- **Rendering:** `DirtyRegionTracker` for incremental rendering of large canvas content.
- **Updates:** `ListDiffCalculator` for incremental list/grid updates.
- **Telemetry:** `TelemetryConfig` enabled; telemetry baselines in test suite.
- **Testing:** include tests for stale-generation cancellation in pipeline stages.

### Template 4: Long-Running Workflow App

Use for: installation wizards, multi-step configuration flows, batch processing tools.

- **Scheduling:** `CooperativeScheduler` coroutines for multi-step background work; yield
  `WaitForEvent` on user confirmation steps.
- **Progress:** `ObservableValue[LoadStateKind]` exposed by the background coroutine; UI
  feature subscribes to drive a `ProgressBarControl`.
- **User input:** `WizardFlow` with `WizardStep` instances for guided multi-step user input.
- **Persistence:** `SnapshotMigrator` for versioned session state; `SettingsRegistry` for
  typed, validated settings that round-trip through workspace save/restore.
- **Testing:** include tests for coroutine cancellation, stale result suppression, and
  workspace restore with schema migration.

[Back to Table of Contents](#table-of-contents)

---

## Appendix F: Specifications and Option Reference

[Back to Table of Contents](#table-of-contents)

This appendix provides a concise field-level reference for the major specification types in
`gui_do`. Each entry lists the spec's purpose, its key fields, and what each field controls.
Cross-reference links point to the chapter where the spec is introduced and used in context.

---

### F.1 Bootstrap Specs

**`HostApplicationConfig`** — Top-level bootstrap configuration object. The primary argument to
`bootstrap_host_application`. → See [§8.1 Application Bootstrap](#81-application-bootstrap-and-host-configuration)

| Field | Type | Purpose |
|-------|------|---------|
| `title` | `str` | Window title bar text |
| `display_size` | `tuple[int, int]` | Initial window pixel dimensions |
| `target_fps` | `int` | Frame rate cap for the event loop |
| `scene_bindings` | `list[SceneBundleBindingSpec]` | Declares all scenes and their features |
| `action_entries` | `list[ActionSpec]` | Global action registry entries |
| `font_entries` | `list[FontRoleBindingSpec]` | Font role assignments |
| `cursor_entries` | `list[CursorSpec]` | Cursor shape registrations |
| `telemetry` | `TelemetryConfig \| None` | Telemetry capture settings |
| `initial_scene` | `str` | Name of the scene activated on startup |

---

**`HostApplicationBindingSpec`** — Companion spec that links a `Feature` class to a host
configuration entry. Used internally by `FeatureWindowBundleBindingSpec` and related helpers.
→ See [§8.1](#81-application-bootstrap-and-host-configuration)

| Field | Type | Purpose |
|-------|------|---------|
| `feature_class` | `type[Feature]` | The feature class to instantiate |
| `host_requirements` | `list[str]` | Host attributes the feature expects |

---

**`SceneBundleBindingSpec`** — Declares one named scene and the features it contains.
→ See [§8.1](#81-application-bootstrap-and-host-configuration)

| Field | Type | Purpose |
|-------|------|---------|
| `scene_name` | `str` | Unique identifier for the scene |
| `feature_bindings` | `list[HostApplicationBindingSpec]` | Ordered feature list for the scene |
| `menu_strip` | `SceneMenuStripSpec \| None` | Optional chrome menu strip for the scene |
| `task_panel` | `SceneTaskPanelSpec \| None` | Optional task panel chrome for the scene |

---

**`FeatureWindowBundleBindingSpec`** — Bundles a feature with a window presenter and an optional
task-panel toggle button, eliminating the need to wire them separately in a `SceneBundleBindingSpec`.
→ See [§8.9 Scene, Window, and Task-Panel Presentation Models](#89-scene-window-and-task-panel-presentation-models)

| Field | Type | Purpose |
|-------|------|---------|
| `feature_class` | `type[Feature]` | The feature whose lifetime is tied to the window |
| `window_spec` | `WindowSpec` | Declares the window dimensions and appearance |
| `task_panel_toggle` | `TaskPanelFocusToggleSpec \| None` | Button spec for task panel, or `None` |

---

**`TelemetryConfig`** — Configures the telemetry subsystem. All fields are optional; omit the
whole config to disable telemetry entirely. → See [§8.16](#816-telemetry-introspection-and-operational-hooks)

| Field | Type | Purpose |
|-------|------|---------|
| `enabled` | `bool` | Master enable/disable switch |
| `log_path` | `str \| None` | File path for the log output; `None` = in-memory only |
| `sample_interval_frames` | `int` | Number of frames between telemetry samples |
| `max_records` | `int \| None` | Maximum records to retain in memory before rotation |

---

### F.2 Feature and Lifecycle Specs

**`FeatureSpec`** — Compact data bag that configures a `Feature` at construction time without
subclassing. Used when minor parametric variation is needed across feature instances.
→ See [§8.2 Feature Lifecycle](#82-feature-lifecycle-and-feature-types)

| Field | Type | Purpose |
|-------|------|---------|
| `feature_id` | `str` | Unique string identifier for the feature within its scene |
| `config` | `dict` | Arbitrary key/value config passed into the feature |

---

**`RoutedRuntimeSpec`** — Declarative bundle that describes all of a `RoutedFeature`'s cross-system
wiring: shortcuts, topic subscriptions, and task-panel toggle.
→ See [§8.2](#82-feature-lifecycle-and-feature-types)

| Field | Type | Purpose |
|-------|------|---------|
| `hotkeys` | `list[ActionHotkeySpec]` | Keyboard shortcuts managed by this spec |
| `shortcut_overlay` | `ShortcutOverlaySpec \| None` | Shortcut help overlay section spec |
| `topic_subscriptions` | `list[str]` | Event bus topics this feature subscribes to |
| `task_panel_toggle` | `TaskPanelFocusToggleSpec \| None` | Task-panel focus toggle integration |

---

**`RoutedFeatureLifecycleSpec`** — Passed to `bind_routed_feature_lifecycle` / `shutdown_routed_feature_lifecycle`.
Holds the resolved host, the `RoutedRuntimeSpec`, and the feature's runtime state containers.
→ See [§8.2](#82-feature-lifecycle-and-feature-types)

| Field | Type | Purpose |
|-------|------|---------|
| `host` | host namespace | Live host reference injected by the framework |
| `spec` | `RoutedRuntimeSpec` | The declarative routing specification |
| `state` | `dict` | Mutable runtime state for subscriptions and handles |

---

**`RuntimeSceneSpec`** — Groups scene-level configuration into a single spec: scene name, exit
behavior, and the list of feature bindings. → See [§8.1](#81-application-bootstrap-and-host-configuration)

| Field | Type | Purpose |
|-------|------|---------|
| `scene_name` | `str` | Unique name matched by `initial_scene` |
| `bind_escape_to_exit` | `bool` | If `True`, Escape key triggers application quit |
| `feature_bindings` | `list[HostApplicationBindingSpec]` | Feature list for the scene |

---

### F.3 Action and Input Specs

**`ActionSpec`** — Declares one named action in the action registry.
→ See [§8.3 Events, Actions, Input Mapping, and Routing](#83-events-actions-input-mapping-and-routing)

| Field | Type | Purpose |
|-------|------|---------|
| `action_id` | `str` | Unique identifier string for the action |
| `label` | `str` | Human-readable label (used in help overlays) |
| `key` | `int \| None` | pygame key constant for default binding, or `None` |
| `modifiers` | `int` | Modifier mask (e.g., `pygame.KMOD_CTRL`) |
| `category` | `str \| None` | Optional grouping category for shortcut overlays |
| `scope` | `str` | `"scene"` or `"window"` — controls routing scope |

---

**`ActionHotkeySpec`** — Associates an existing action ID with a specific key in a
`RoutedRuntimeSpec`. Used to override or extend the default binding declared in `ActionSpec`.
→ See [§8.3](#83-events-actions-input-mapping-and-routing)

| Field | Type | Purpose |
|-------|------|---------|
| `action_id` | `str` | Action to bind |
| `key` | `int` | pygame key constant |
| `modifiers` | `int` | Modifier mask |

---

**`ShortcutOverlaySpec`** — Declares the shortcut help overlay section for a `RoutedFeature`.
→ See [§8.3](#83-events-actions-input-mapping-and-routing) and [§8.8](#88-overlays-dialogs-notifications-and-command-surfaces)

| Field | Type | Purpose |
|-------|------|---------|
| `section_title` | `str` | Heading shown in the shortcut overlay |
| `entries` | `list[ShortcutEntry]` | Per-shortcut display lines |

---

**`ShortcutSection`** — A grouped section within the shortcut help overlay.

| Field | Type | Purpose |
|-------|------|---------|
| `title` | `str` | Group heading text |
| `entries` | `list[ShortcutEntry]` | Lines within this group |

---

**`ShortcutEntry`** — One line in the shortcut overlay display.

| Field | Type | Purpose |
|-------|------|---------|
| `key_label` | `str` | Key combination label (e.g., `"Ctrl+S"`) |
| `description` | `str` | Short description of what the action does |

---

**`InputBinding`** — Represents a resolved key-to-action mapping entry in `InputMap`.
→ See [§8.3](#83-events-actions-input-mapping-and-routing)

| Field | Type | Purpose |
|-------|------|---------|
| `action_id` | `str` | Target action identifier |
| `key` | `int` | pygame key constant |
| `modifiers` | `int` | Required modifier mask |

---

### F.4 Window and Presentation Specs

**`WindowSpec`** — Declares a managed floating or docked window surface.
→ See [§8.9](#89-scene-window-and-task-panel-presentation-models)

| Field | Type | Purpose |
|-------|------|---------|
| `window_id` | `str` | Unique identifier for the window |
| `title` | `str` | Window title bar text |
| `initial_rect` | `pygame.Rect` | Starting position and size |
| `min_size` | `tuple[int, int] \| None` | Minimum resize bounds |
| `resizable` | `bool` | Whether the user can resize the window |
| `initially_visible` | `bool` | Visibility state at scene activation |

---

**`AnchoredWindowSpec`** — Extension of `WindowSpec` that anchors the window to a parent
rect or screen edge rather than using absolute positioning.
→ See [§8.9](#89-scene-window-and-task-panel-presentation-models)

| Field | Type | Purpose |
|-------|------|---------|
| (inherits `WindowSpec`) | — | All `WindowSpec` fields |
| `anchor` | `Alignment` | Which edge/corner to anchor to |
| `anchor_target` | `pygame.Rect \| None` | Reference rect; `None` = screen edge |
| `offset` | `tuple[int, int]` | Pixel offset from the anchor point |

---

**`SceneTaskPanelSpec`** — Configures the task panel chrome for a scene.
→ See [§8.9](#89-scene-window-and-task-panel-presentation-models)

| Field | Type | Purpose |
|-------|------|---------|
| `panel_id` | `str` | Unique identifier for the panel |
| `position` | `str` | `"left"`, `"right"`, `"top"`, or `"bottom"` |
| `width` | `int` | Pixel width (for left/right panels) |
| `button_groups` | `list[TaskPanelWindowToggleGroupSpec]` | Ordered button groups |

---

**`TaskPanelButtonSpec`** — One button entry in the task panel.

| Field | Type | Purpose |
|-------|------|---------|
| `label` | `str` | Button label text |
| `action_id` | `str \| None` | Action to fire on click, or `None` |
| `icon` | `str \| None` | Optional icon name from `AssetRegistry` |
| `tooltip` | `str \| None` | Hover tooltip text |

---

**`TaskPanelWindowToggleGroupSpec`** — Groups window toggle buttons under a shared heading
in the task panel. → See [§8.9](#89-scene-window-and-task-panel-presentation-models)

| Field | Type | Purpose |
|-------|------|---------|
| `group_label` | `str \| None` | Optional group heading, or `None` for no heading |
| `toggles` | `list[TaskPanelFocusToggleSpec]` | Toggle button specs |

---

**`TaskPanelFocusToggleSpec`** — Wires a task-panel toggle button to a window's
`FocusScopeManager` visibility state. → See [§8.9](#89-scene-window-and-task-panel-presentation-models)

| Field | Type | Purpose |
|-------|------|---------|
| `window_id` | `str` | Window identifier to toggle |
| `label` | `str` | Button label |
| `shortcut_action_id` | `str \| None` | Optional action that also toggles the window |
| `initially_active` | `bool` | Whether the button is pressed at scene start |

---

**`TaskPanelSceneNavButtonSpec`** — A task-panel button that triggers a scene transition.
→ See [§8.9](#89-scene-window-and-task-panel-presentation-models)

| Field | Type | Purpose |
|-------|------|---------|
| `label` | `str` | Button label |
| `target_scene` | `str` | Scene name to switch to on click |
| `icon` | `str \| None` | Optional icon name |

---

**`TabbedPresenterSpec`** — Configures a `TabbedPresenterControl` layout region that renders
tab switching through the task panel. → See [§8.9](#89-scene-window-and-task-panel-presentation-models)

| Field | Type | Purpose |
|-------|------|---------|
| `presenter_id` | `str` | Unique identifier |
| `tabs` | `list[TabBuilderSpec]` | Ordered tab entries |
| `initial_tab` | `str \| None` | ID of tab shown first; `None` = first tab |

---

**`TabBuilderSpec`** — One tab entry in a `TabbedPresenterSpec`.

| Field | Type | Purpose |
|-------|------|---------|
| `tab_id` | `str` | Unique identifier within the presenter |
| `label` | `str` | Tab label text |
| `feature_class` | `type[Feature] \| None` | Feature whose `draw` occupies the tab, if any |

---

**`SceneMenuStripSpec`** — Configures a horizontal menu strip at the top of a scene.
→ See [§8.9](#89-scene-window-and-task-panel-presentation-models)

| Field | Type | Purpose |
|-------|------|---------|
| `entries` | `list[MenuEntry]` | Top-level menu entries |

---

**`WindowToggleBindingSpec`** — Declaratively binds an action to a window visibility toggle
without writing handler code. → See [§8.9](#89-scene-window-and-task-panel-presentation-models)

| Field | Type | Purpose |
|-------|------|---------|
| `action_id` | `str` | Action that triggers the toggle |
| `window_id` | `str` | Window whose visibility is toggled |

---

### F.5 Accessibility Specs

**`StaticAccessibilitySpec`** — Attaches a fixed accessibility label and role to a control.
→ See [§8.7 Focus and Accessibility](#87-focus-and-accessibility)

| Field | Type | Purpose |
|-------|------|---------|
| `role` | `AccessibilityRole` | Semantic role (e.g., `button`, `listitem`, `group`) |
| `label` | `str` | Human-readable name for screen readers |
| `live` | `LivePoliteness \| None` | Live region politeness level, or `None` |

---

**`AccessibilitySequenceSpec`** — Declares the focus-traversal order for a control group.
→ See [§8.7](#87-focus-and-accessibility)

| Field | Type | Purpose |
|-------|------|---------|
| `sequence` | `list[str]` | Ordered list of control IDs in traversal order |
| `wrap` | `bool` | If `True`, traversal wraps from last to first |

---

### F.6 Font, Cursor, and Control Specs

**`FontRoleBindingSpec`** — Assigns a font file and size to a named font role.
→ See [§8.12 Theme, Styling, and Visual Systems](#812-theme-styling-and-visual-systems)

| Field | Type | Purpose |
|-------|------|---------|
| `role_name` | `str` | Logical role name (e.g., `"body"`, `"heading"`, `"mono"`) |
| `font_path` | `str` | Relative path to the `.ttf` or `.otf` file |
| `size` | `int` | Font point size |
| `bold` | `bool` | Whether to synthesize bold |
| `italic` | `bool` | Whether to synthesize italic |

---

**`CursorSpec`** — Registers a named cursor shape from an image file.
→ See [§8.8](#88-overlays-dialogs-notifications-and-command-surfaces)

| Field | Type | Purpose |
|-------|------|---------|
| `cursor_id` | `str` | Unique identifier for the cursor |
| `image_path` | `str` | Path to the cursor image |
| `hotspot` | `tuple[int, int]` | Pixel offset of the click point within the image |

---

**`CursorBindingSpec`** — Binds a cursor shape to a control's hover region.

| Field | Type | Purpose |
|-------|------|---------|
| `cursor_id` | `str` | Cursor to display on hover |
| `control_id` | `str` | Target control |

---

**`ControlDefinition`** — Declarative spec for building a control programmatically in
data-driven control gallery systems. → See [§8.5 Controls and Control Composition](#85-controls-and-control-composition)

| Field | Type | Purpose |
|-------|------|---------|
| `control_class` | `type` | Control class to instantiate |
| `rect` | `pygame.Rect` | Initial rect |
| `kwargs` | `dict` | Constructor arguments |

---

**`NotificationSpec`** — Configures a toast notification before showing it.
→ See [§8.8](#88-overlays-dialogs-notifications-and-command-surfaces)

| Field | Type | Purpose |
|-------|------|---------|
| `message` | `str` | Notification text |
| `severity` | `ToastSeverity` | Visual severity level (`info`, `warning`, `error`) |
| `duration_ms` | `int \| None` | Auto-dismiss delay in milliseconds; `None` = sticky |
| `on_click` | `Callable \| None` | Callback invoked when the toast is clicked |

---

### F.7 Persistence and Migration Specs

**`SchemaVersion`** — Identifies a snapshot schema version for migration matching.
→ See [§8.11 Persistence and Workspace/Session State](#811-persistence-and-workspacesession-state)

| Field | Type | Purpose |
|-------|------|---------|
| `major` | `int` | Major version number; incremented on breaking changes |
| `minor` | `int` | Minor version; incremented on backward-compatible additions |

---

**`VersionedSnapshot`** — Wraps a serializable payload with a `SchemaVersion` for safe migration.
→ See [§8.11](#811-persistence-and-workspacesession-state)

| Field | Type | Purpose |
|-------|------|---------|
| `version` | `SchemaVersion` | Version at the time the snapshot was created |
| `payload` | `dict` | Arbitrary serializable state data |

---

**`MigrationStep`** — One node in the migration graph. Registered on `MigrationRegistry`.
→ See [§8.11](#811-persistence-and-workspacesession-state)

| Field | Type | Purpose |
|-------|------|---------|
| `from_version` | `SchemaVersion` | Source version for this step |
| `to_version` | `SchemaVersion` | Target version for this step |
| `migrate` | `Callable[[dict], dict]` | Pure function that transforms the payload |

---

### F.8 Overlay and Dialog Specs

**`FileDialogOptions`** — Configures the file open/save dialog behavior.
→ See [§8.8](#88-overlays-dialogs-notifications-and-command-surfaces)

| Field | Type | Purpose |
|-------|------|---------|
| `mode` | `str` | `"open"` or `"save"` |
| `initial_dir` | `str \| None` | Starting directory, or `None` for last-used |
| `filters` | `list[tuple[str, str]]` | Filter entries, each `(label, pattern)` |
| `title` | `str \| None` | Dialog title override, or `None` for default |
| `allow_multiple` | `bool` | Whether multiple files can be selected (`"open"` only) |

---

**`TransitionSpec`** — Configures a scene or layout transition animation.
→ See [§8.10 Scheduling, Timing, Animation, and Transitions](#810-scheduling-timing-animation-and-transitions)

| Field | Type | Purpose |
|-------|------|---------|
| `style` | `SceneTransitionStyle` | Transition visual style (fade, slide, etc.) |
| `duration_ms` | `int` | Animation duration in milliseconds |
| `easing` | `Easing` | Easing function applied to the animation |

---

[Back to Table of Contents](#table-of-contents)
