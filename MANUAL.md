# gui_do Manual

## 1. Title and Purpose
[Back to Table of Contents](#table-of-contents)

This manual is for people building or maintaining apps on top of `gui_do`: framework users, demo authors, and contributors who need the current runtime model rather than a stale architectural summary.

The package is intentionally data-driven. The most important way to read this manual is to connect three lenses at once:

1. What the runtime actually does today in code.
2. What the tests lock in as behavior.
3. What the docs describe as the supported contract.

That triad matters because `gui_do` is not just a widget collection. It is a runtime with declarative bootstrap specs, scene-scoped optional chrome, routed feature wiring, and lifecycle-owned cleanup rules. The manual therefore focuses on how to compose the system safely, how the main spec families map to the runtime, and where the hidden boundaries are.

## 2. Table of Contents
[Back to Table of Contents](#table-of-contents)

- [1. Title and Purpose](#1-title-and-purpose)
- [2. Table of Contents](#2-table-of-contents)
- [3. How to Use This Manual](#3-how-to-use-this-manual)
- [4. Feature Organization Conventions](#4-feature-organization-conventions)
- [5. Conceptual Foundations](#5-conceptual-foundations)
- [6. Quickstart Path](#6-quickstart-path)
- [7. Architecture and Runtime Model](#7-architecture-and-runtime-model)
- [8. Core Workflow: Build, Bind, Route, Update, Draw](#8-core-workflow-build-bind-route-update-draw)
- [9. Main Systems Reference](#9-main-systems-reference)
- [10. Integration Patterns and Composition Recipes](#10-integration-patterns-and-composition-recipes)
- [11. End-to-End Reference Application](#11-end-to-end-reference-application)
- [12. Testing, Diagnostics, and Reliability](#12-testing-diagnostics-and-reliability)
- [13. Performance and Scaling Guidance](#13-performance-and-scaling-guidance)
- [14. Migration, Versioning, and Deprecation Notes](#14-migration-versioning-and-deprecation-notes)
- [15. FAQ and Troubleshooting](#15-faq-and-troubleshooting)
- [16. Appendix](#16-appendix)
  - [Appendix A. Glossary](#appendix-a-glossary)
  - [Appendix B. Lifecycle and Event Routing Sequence](#appendix-b-lifecycle-and-event-routing-sequence)
  - [Appendix C. System Dependency Map](#appendix-c-system-dependency-map)
  - [Appendix D. API Quick Index by Topic](#appendix-d-api-quick-index-by-topic)
    - [Appendix D.1. Tier-to-System Reference Matrix](#appendix-d1-tier-to-system-reference-matrix)
    - [Appendix D.2. Public API Selection Heuristics](#appendix-d2-public-api-selection-heuristics)
  - [Appendix E. Architecture Templates](#appendix-e-architecture-templates)
  - [Appendix F. Specifications and Option Reference](#appendix-f-specifications-and-option-reference)

## 3. How to Use This Manual
[Back to Table of Contents](#table-of-contents)

Start with the sections that match your task, not the sections that match the package layout.

If you are wiring an app or demo, read the quickstart, runtime model, and core workflow first. If you are changing behavior, read the systems chapter for the affected subsystem and then the testing section. If you are trying to understand why the code is organized in a package-folder pattern, read the feature organization and appendix sections together.

The manual uses a tri-lens framing throughout:

- Runtime lens: what the live code path does.
- Contract lens: what tests and docs require.
- Composition lens: how to build on the public surface without reaching into private internals.

Where the docs and tests disagree with an intuition, prefer the contract. Where the code and a prose doc disagree, prefer the code plus the nearest regression test. This is especially important for data-driven specs, because many of them are convenience layers around a smaller number of runtime primitives.

The supported consumer import path is the root `gui_do` package. The demo entrypoint is a consumer of that root surface, not a peer framework module. The manual intentionally follows that boundary.

## 4. Feature Organization Conventions
[Back to Table of Contents](#table-of-contents)

The demo package layout is not arbitrary. It is a convention that keeps consumer code readable and keeps the framework boundary clean.

Each demo feature or scene lives in its own folder package under `demo_features/`. The current repository follows that pattern with packages such as `main`, `life`, `systems`, `mandelbrot`, `moving_shapes`, and `showcase`. Each package has its own `__init__.py` and keeps feature-specific code local to that folder.

The required default pattern is:

- one folder package per feature or scene,
- at least one `*_feature.py` module,
- at least one `*_specs.py` module,
- a clean package export surface in `__init__.py`,
- optional `FEATURE_PACKAGE_INFO` metadata only, not runtime registration logic.

The repository test contract makes one extra point explicit: demo feature packages should not re-export `*Feature` symbols from their package `__init__.py`. Keep the canonical feature class import inside the concrete module. That makes the package boundary obvious and prevents a layer of accidental aliasing.

The root `demo_features` package should stay small. In the current repo it is used for bootstrap-facing files such as `demo_config.py` and shared assets under `demo_features/data/`. The top-level demo entrypoint, `gui_do_demo.py`, consumes the framework through the root `gui_do` imports and then hands off to `bootstrap_host_application`.

## 5. Conceptual Foundations
[Back to Table of Contents](#table-of-contents)

`gui_do` is built around a data-driven runtime model. Instead of wiring everything imperatively in one place, you declare feature specs, scene specs, window specs, action specs, and optional chrome specs. The framework then expands those declarations into runtime objects and bindings.

The core mental model is:

- features are the unit of behavior,
- scenes are the unit of runtime isolation,
- runtime scopes own subscriptions and cleanup,
- routed runtime helpers translate declarative specs into live services, actions, and effects,
- optional chrome is opt-in and scene-scoped.

Ownership is part of the design, not an implementation detail. `FeatureRuntimeScope` exists so a feature binding can own its subscriptions, connections, disposables, and child service scope together. That is what makes automatic cleanup a lifecycle guarantee rather than a best-effort cleanup convention.

The runtime also exposes higher-level routed faculties discovered at generation time. The main idea is that a routed feature does not manually recreate every service or effect. Instead, a `RoutedRuntimeSpec` can declare things like service bindings, store subscriptions, observable effects, signal effects, operations, failure policies, shortcut overlays, task-panel toggles, pointer actions, dependency wiring, budgets, checkpoints, workflows, and replay support. The framework uses those declarations to keep `bind_runtime` methods short and declarative.

Two more concepts matter everywhere:

- unified visibility: scene menu strip, task panel, and command palette all participate in one shared window-management model,
- opt-out fields: windows can explicitly exclude themselves from that shared model with `window_management_opt_in=False`.

## 6. Quickstart Path
[Back to Table of Contents](#table-of-contents)

The fastest successful path is to start from the demo bootstrap and then work outward.

1. Read `gui_do_demo.py` to see the entry pattern.
2. Read `demo_features/demo_config.py` to see a real `HostApplicationBindingSpec` assembled from current repo assets and scene entries.
3. Read `gui_do/__init__.py` to see the supported import surface.
4. Read the tests for the subsystem you are changing.
5. Run the app and then tighten the contract with tests.

The first milestone is just “the runtime launches and switches to the initial scene.” The second milestone is “the scene has the expected chrome and input routing.” The third milestone is “window visibility, action bindings, and feature lifecycles all agree.” Do not try to optimize before you get those three pieces aligned.

The most common early failures are:

- importing from internal `gui_do.*` modules in consumer code instead of the root package,
- using the wrong working directory for relative assets,
- omitting the feature package files that the demo layout contract expects,
- wiring a command palette or task panel partially and expecting the other chrome to auto-sync without the shared visibility model being present.

Minimal bootstrap pattern:

```python
from gui_do import bootstrap_host_application
from demo_features.demo_config import DEMO_BOOTSTRAP_CONFIG


class GuiDoDemo:
    def __init__(self) -> None:
        bootstrap_host_application(self, DEMO_BOOTSTRAP_CONFIG)


if __name__ == "__main__":
    GuiDoDemo().app.run_entrypoint(target_fps=DEMO_BOOTSTRAP_CONFIG.target_fps)
```

That is intentionally small. The real composition belongs in specs, not in the entrypoint.

## 7. Architecture and Runtime Model
[Back to Table of Contents](#table-of-contents)

The architecture is tiered. The root package exposes the supported consumer surface, and the runtime grows from there into events, data/state, scheduling, layout, overlays, controls, forms, persistence, graphics, and diagnostics.

At the top level, `bootstrap_host_application` assembles a host from declarative config. Under that, `GuiApplication` is the runtime coordinator, event dispatcher, and scene manager. The event system normalizes raw `pygame` events to `GuiEvent` before app-level dispatch. Data/state primitives such as `ObservableValue`, `PresentationModel`, `CollectionView`, and `Binding` support reactive composition. Scheduling and animation systems drive timed work and interpolation. The chrome systems manage menu strips, task panels, overlays, and the command palette.

The runtime guarantees that matter most are:

- events are normalized before app dispatch,
- the active scene is the unit of runtime routing,
- optional chrome is only created when declared,
- visibility entries across menu strip, task panel, and command palette stay synchronized when those facilities coexist,
- scheduler dispatch obeys bounded policy rather than unbounded frame consumption,
- lifecycle cleanup is owned by the runtime scope that created the binding.

The architectural boundary is strict: `gui_do` must not import `demo_features`. Demo code is consumer code. That matters because the framework is intended to be reusable as a package, not just as the implementation for one demo app.

## 8. Core Workflow: Build, Bind, Route, Update, Draw
[Back to Table of Contents](#table-of-contents)

The practical runtime flow is easiest to understand as a sequence:

1. Build the feature objects and supporting scene/runtime specs.
2. Bind runtime services, actions, subscriptions, and chrome.
3. Route input into the event pipeline.
4. Update reactive state, scene state, and scheduled work.
5. Draw the current scene and its chrome.

The framework separates “construction” from “runtime binding” for a reason. Building a feature should establish its model and any static controls. Binding runtime should attach listeners, services, and owned cleanups. Routing should then operate on live objects, not on half-initialized state.

`build` and `bind_runtime` are the key lifecycle hooks. `build` is where a feature constructs its controls or state model. `bind_runtime` is where it attaches live services, input handlers, observable subscriptions, operation buses, and scene-local helpers. Routed features can use `RoutedRuntimeSpec` and `RoutedFeatureLifecycleSpec` so that most of that wiring is declarative and the method bodies stay short.

The message coordination path is also explicit. `FeatureMessage` exists for feature-to-feature or feature-to-host coordination, while routed runtime helpers expose higher-level operational constructs such as operation buses and runtime scopes.

Minimal lifecycle sketch:

```python
from gui_do import Feature, ObservableValue


class CounterFeature(Feature):
    def build(self, host) -> None:
        self.count = ObservableValue(0)

    def bind_runtime(self, host) -> None:
        self.count.subscribe(lambda value: print("count:", value))
```

The important part is not the particular counter. It is the split between model creation and runtime attachment.

## 9. Main Systems Reference
[Back to Table of Contents](#table-of-contents)

### 9.1 Application Bootstrap and Host Configuration
[Back to Table of Contents](#table-of-contents)

`bootstrap_host_application`, `HostApplicationConfig`, and `build_host_application_config` are the entry trio for app assembly. They exist so an app can be described declaratively rather than hand-wired in the entrypoint.

Mental model: bootstrap consumes a host plus a fully formed config and populates display, fonts, app runtime, scene transitions, features, actions, chrome, accessibility, and scene switching helpers.

Typical flow:

1. Create `HostApplicationBindingSpec`.
2. Convert it with `build_host_application_config`.
3. Pass the result to `bootstrap_host_application`.

Verified example:

```python
from gui_do import HostApplicationBindingSpec, build_host_application_config, bootstrap_host_application

config = build_host_application_config(
    HostApplicationBindingSpec(
        display_size=(1920, 1080),
        window_title="gui_do demo",
        fonts={"default": {"file": "demo_features/data/fonts/Gimbot.ttf", "size": 14}},
        initial_scene_name="main",
    )
)
bootstrap_host_application(self, config)
```

Advanced pattern: build scene bundles with `SceneBundleBindingSpec` so scene setup, runtime startup, root creation, and navigation action emission travel together.

Common mistakes: passing internal object graphs into the entrypoint instead of a supported config spec; trying to register demo-specific code in `gui_do` internals.

Related: [Feature Lifecycle and Feature Types](#92-feature-lifecycle-and-feature-types), [State and Observables](#94-state-and-observables), [Appendix F](#appendix-f-specifications-and-option-reference).

### 9.2 Feature Lifecycle and Feature Types
[Back to Table of Contents](#table-of-contents)

The core types are `Feature`, `DirectFeature`, `LogicFeature`, `RoutedFeature`, `FeatureManager`, `FeatureMessage`, `ScenePresentationModel`, and `SceneSetupSpec`.

Why they exist: they separate feature ownership, logical composition, and routed runtime wiring. A direct feature can be mostly self-contained, while a routed feature uses declarative runtime specs to connect services and effects.

Lifecycle placement: feature construction happens before runtime binding; `FeatureManager` coordinates the sequence and ensures runtime hooks are invoked in a predictable order.

Minimal verified example:

```python
from gui_do import Feature


class MyFeature(Feature):
    def build(self, host) -> None:
        self.title = "Hello"

    def bind_runtime(self, host) -> None:
        pass
```

Advanced pattern: use `RoutedFeatureLifecycleSpec` when a routed feature needs companion providers or a runtime spec factory. That keeps feature classes thin and shifts the declarative wiring into data.

Common mistakes: using `bind_runtime` to create what should have been built during `build`; mutating shared services without an owned runtime scope; forgetting that lifecycle cleanup is expected to be owned and deterministic.

Cross-links: [Core Workflow](#8-core-workflow-build-bind-route-update-draw), [State and Observables](#94-state-and-observables), [Appendix B](#appendix-b-lifecycle-and-event-routing-sequence).

### 9.3 Events, Actions, Input Mapping, and Routing
[Back to Table of Contents](#table-of-contents)

Core APIs: `GuiEvent`, `EventType`, `EventPhase`, `EventManager`, `ActionManager`, `ActionRegistry`, `InputMap`, `InputBinding`, `EventBus`, `GestureRecognizer`, `EventRecorder`, `EventPlayback`, `Signal`, `SignalConnection`, `KeyChordManager`, `KeyChord`, and `ChordStep`.

Why they exist: the runtime normalizes raw platform input into a single event model and then dispatches through action and scene routing layers. That keeps keyboard, pointer, and text input on the same semantic footing.

Typical usage flow:

1. Raw `pygame` input enters the runtime.
2. It becomes `GuiEvent`.
3. Global keys, pointer binds, overlays, focus, and scene handlers are consulted in order.
4. Action handlers dispatch to named app actions.

Minimal example:

```python
from gui_do import InputMap

input_map = InputMap()
input_map.bind("exit", key=27)
```

Advanced pattern: global key and pointer binds can be scene-scoped. For command palette behavior, `SceneCommandPaletteSpec` uses two binds: one for toggling the palette, and one for acting on the entry under the pointer while the palette remains open.

Common mistakes: treating pointer and keyboard handling as separate systems; bypassing `GuiEvent` and routing raw platform events directly; forgetting that event order is part of the contract.

Cross-links: [Command Palette](#98-overlays-dialogs-notifications-and-command-surfaces), [Architecture and Runtime Model](#7-architecture-and-runtime-model), [Appendix B](#appendix-b-lifecycle-and-event-routing-sequence).

### 9.4 State and Observables
[Back to Table of Contents](#table-of-contents)

Key types: `ObservableValue`, `ComputedValue`, `PresentationModel`, `Binding`, `BindingGroup`, `ObservableStream`, `ObservableList`, `ObservableDict`, `CollectionView`, `CollectionViewQuery`, `SelectionModel`, `SelectionMode`, `reactive_batch`, and `InvalidationTracker`.

Why they exist: the UI needs a reactive state layer that can stay coherent under repeated updates, derived values, and view projections.

Lifecycle model: state objects usually outlive a single event handler but are still owned by a feature or runtime scope. That is why runtime scope cleanup is so important for subscriptions and observers.

Minimal example:

```python
from gui_do import ObservableValue

counter = ObservableValue(0)
unsubscribe = counter.subscribe(lambda value: print(value))
counter.value = 1
unsubscribe()
```

Advanced pattern: use `reactive_batch` when several state updates should invalidate as one logical change rather than many small ones.

Common mistakes: creating derived state without considering invalidation order; leaving subscriptions unowned; mixing presentation state and imperative side effects in the same object.

Cross-links: [Feature Lifecycle](#92-feature-lifecycle-and-feature-types), [Testing, Diagnostics, and Reliability](#12-testing-diagnostics-and-reliability), [Appendix A](#appendix-a-glossary).

### 9.5 Controls and Control Composition
[Back to Table of Contents](#table-of-contents)

Core controls include `PanelControl`, `LabelControl`, `ButtonControl`, `ToggleControl`, `SliderControl`, `ScrollbarControl`, `CanvasControl`, `FrameControl`, `ImageControl`, `ArrowBoxControl`, `ButtonGroupControl`, `TabControl`, `DockWorkspacePanel`, `TextInputControl`, `TextAreaControl`, `RichLabelControl`, `DropdownControl`, `ListViewControl`, `OverlayPanelControl`, `DataGridControl`, `TreeControl`, `SplitterControl`, `SpinnerControl`, `RangeSliderControl`, `ColorPickerControl`, `ScrollViewControl`, `ProgressBarControl`, `AnimatedImageControl`, `ErrorBoundary`, `WindowControl`, `TaskPanelControl`, and `WindowPresenter`.

Why they exist: controls are the reusable UI primitives, while features decide how to compose them into scenes and workflows.

Typical usage flow: create controls in `build`, attach them to a container, then use feature runtime binding to connect events, accessibility, and actions.

Minimal example:

```python
from gui_do import ButtonControl, LabelControl
```

Advanced pattern: use window presenters and task-panel controls as chrome surfaces, not as scene content. That keeps the scene chrome contract intact.

Common mistakes: adding task-panel chrome into a window container; depending on control internals instead of using the provided composition helpers; assuming a control is focusable without checking its tab-index and accessibility contract.

Cross-links: [Layouts](#96-layout-systems), [Focus and Accessibility](#97-focus-and-accessibility), [Overlays](#98-overlays-dialogs-notifications-and-command-surfaces).

### 9.6 Layout Systems
[Back to Table of Contents](#table-of-contents)

Public layout types include `LayoutAxis`, `ConstraintLayout`, `AnchorConstraint`, `DockPane`, `DockTabs`, `DockSplit`, `DockWorkspace`, `FlexLayout`, `FlexItem`, `GridLayout`, `GridTrack`, `GridPlacement`, `FlowLayout`, `FlowItem`, `LayoutAnimator`, `LayoutPass`, `MeasureContext`, `ArrangeContext`, `LayoutRoot`, `Viewport`, and `WindowLayoutHandler`.

Why they exist: they provide the geometry layer that makes control composition predictable. Layouts are intended to be nested and measured/arranged in passes.

Typical flow: measure, arrange, then let the runtime render or route focus based on the resulting geometry.

Advanced pattern: when building dense demo scenes, keep layout constants near the feature definition so geometry is easy to tune and reason about.

Common mistakes: mixing layout responsibilities into control event handlers; assuming padding/gap are inherited; relying on ad hoc placement logic for a container that already has a layout helper.

Cross-links: [Controls](#95-controls-and-control-composition), [Architecture](#7-architecture-and-runtime-model), [Appendix E](#appendix-e-architecture-templates).

### 9.7 Focus and Accessibility
[Back to Table of Contents](#table-of-contents)

Core types: `FocusManager`, `FocusScope`, `FocusScopeManager`, `WindowFocusManager`, and `FocusRing`, plus the accessibility sequence helpers in the data-driven runtime.

Why they exist: focus is not just a visual state; it is part of routing. Accessibility metadata also depends on predictable tab order and ownership.

Typical flow: controls opt into focus behavior, runtime helpers assign tab order, and focus scopes keep navigation bounded to the active scene or chrome area.

Minimal example:

```python
from gui_do import FocusManager
```

Advanced pattern: use `apply_accessibility_sequence` or `apply_accessibility_sequence_from_attrs` to assign contiguous tab order and roles from declarative specs.

Common mistakes: letting focusable controls share ambiguous tab positions; forgetting that scene chrome and window chrome are part of the accessibility model; building a visible control that is not actually reachable.

Cross-links: [Controls](#95-controls-and-control-composition), [State and Observables](#94-state-and-observables), [Appendix F](#appendix-f-specifications-and-option-reference).

### 9.8 Overlays, Dialogs, Notifications, and Command Surfaces
[Back to Table of Contents](#table-of-contents)

Core types: `OverlayManager`, `DialogManager`, `ToastManager`, `ContextMenuManager`, `CommandPaletteManager`, `TooltipManager`, `MenuBarManager`, `FileDialogManager`, `NotificationCenter`, `ResizeManager`, `CursorManager`, `DragDropManager`, `ClipboardManager`, `TransferManager`, `ShortcutHelpOverlay`, and `CommandEntry`.

Why they exist: these surfaces are transient, scene-aware interaction layers that sit above normal scene content.

The command palette uses a two-bind model. `SceneCommandPaletteSpec` declares a `toggle` bind and an `action` bind. The toggle bind opens or closes the palette. The action bind activates the targeted entry while preserving the open palette state so repeated actions do not collapse the surface unexpectedly.

Verified example:

```python
from gui_do import PaletteInputBindSpec, SceneCommandPaletteSpec

spec = SceneCommandPaletteSpec(
    scene_name="main",
    toggle=PaletteInputBindSpec(action_name="command_palette_toggle", key=116),
    action=PaletteInputBindSpec(action_name="command_palette_action", pointer_button=2),
)
```

Advanced pattern: use `PaletteBindingSpec` with `group_order` and a custom entries provider to place built-in scene/window entries around user-defined command entries. When `connect_window_presentation=True`, the window entries follow the same ordering as the task panel toggle group.

Common mistakes: binding the palette action like a normal dismissing toggle; activating pointer entries without the logical-pointer fallback when `event.pos` is missing; assuming one chrome surface can diverge from the other visibility surfaces.

Cross-links: [Events and Routing](#93-events-actions-input-mapping-and-routing), [Scene/Window/Task-Panel Presentation Models](#99-scene-window-and-task-panel-presentation-models), [Appendix F](#appendix-f-specifications-and-option-reference).

### 9.9 Scene, Window, and Task-Panel Presentation Models
[Back to Table of Contents](#table-of-contents)

Key types and helpers: `ScenePresentationModel`, `FeatureWindowPresentationModel`, `WindowSpec`, `AnchoredWindowSpec`, `SceneTaskPanelSpec`, `TaskPanelButtonSpec`, `RightAnchoredTaskPanelButtonSpec`, `TaskPanelWindowToggleGroupSpec`, `TaskPanelSceneNavButtonSpec`, `SceneMenuOptions`, `WindowMenuOptions`, `MenuStripSpec`, `add_menu_strip_from_spec`, `add_standard_menu_strip`, `add_window_menu_strip`, `add_task_panel_window_toggle_group`, `add_window_toggle_task_panel_controls`, `collect_window_toggle_controls`, and `apply_window_toggle_accessibility`.

Why they exist: they keep scene chrome, window chrome, and task-panel chrome aligned while still allowing each facility to be omitted.

Unified visibility rule: scene menu strip, task panel, and command palette are one synchronized visibility model. If a window sets `window_management_opt_in=False`, it opts out of all three systems.

Minimal example:

```python
from gui_do import WindowSpec

window_spec = WindowSpec(
    key="systems",
    feature_attribute_name="_systems_feature",
    toggle_attribute_name="systems_toggle",
    action_name="toggle_systems",
    action_label="Toggle Systems",
    task_panel_toggle_button_id="systems_toggle_button",
    task_panel_label="Systems",
    task_panel_style="round",
    task_panel_slot_index=1,
    accessibility_label="Systems window",
)
```

Advanced pattern: use `FeatureWindowBundleBindingSpec` when a feature and its window toggle metadata should be declared together. It reduces drift between feature registration and visibility registration.

Common mistakes: treating task panel controls as window chrome; assuming a scene menu strip and task panel can expose different windows when the shared visibility model is present; forgetting that opt-out must be explicit.

Cross-links: [Application Bootstrap](#91-application-bootstrap-and-host-configuration), [Command Surfaces](#98-overlays-dialogs-notifications-and-command-surfaces), [Appendix F](#appendix-f-specifications-and-option-reference).

### 9.10 Scheduling, Timing, Animation, and Transitions
[Back to Table of Contents](#table-of-contents)

Core types: `TaskScheduler`, `TaskEvent`, `Timers`, `TweenManager`, `TweenHandle`, `Easing`, `AnimationSequence`, `AnimationHandle`, `TransitionManager`, `TransitionSpec`, `TransitionEvent`, `AnimationStateMachine`, `AnimationTransitionMode`, `SceneTimeline`, `Debouncer`, `Throttler`, `CooperativeScheduler`, `CoroutineHandle`, `Pause`, `Sleep`, `WaitForEvent`, `WaitForSignal`, `WaitUntil`, and `WaitForAll`.

Why they exist: they provide bounded, composable time-based behavior without pushing all timing logic into the main loop.

Typical flow: schedule work, let the runtime advance it, and keep side effects owned by the runtime scope or scheduler handle.

Advanced pattern: prefer declarative timing and transition helpers over ad hoc frame counting in feature code. It keeps the behavior testable and makes budget limits easier to reason about.

Common mistakes: blocking the event loop with long-running operations; encoding animation state directly into input handlers; forgetting to cancel scheduled work during teardown.

Cross-links: [Performance Guidance](#13-performance-and-scaling-guidance), [Core Workflow](#8-core-workflow-build-bind-route-update-draw).

### 9.11 Persistence and Workspace/Session State
[Back to Table of Contents](#table-of-contents)

Core types: `WorkspaceState`, `WorkspacePersistenceManager`, `SceneSnapshot`, `NodeSnapshot`, `SettingsRegistry`, `SettingDescriptor`, `SceneTransitionManager`, and `SceneTransitionStyle`.

Why they exist: the runtime can restore workspace and scene state, not just restart from scratch.

Behavioral notes:

- workspace restore returns a report,
- load/save failures do not abort shutdown sequencing,
- missing settings blocks are skipped and reported rather than crashing the restore flow,
- scene transitions are part of the host model rather than ad hoc entrypoint logic.

Minimal example:

```python
report = app.load_workspace(manager, Path("workspace.json"))
```

Advanced pattern: use the restore summary to drive diagnostics or migration checks instead of guessing which settings or scenes were applied.

Common mistakes: treating workspace restore as a side effect with no return value; assuming every settings key is present; bypassing the documented restore report.

Cross-links: [Testing and Reliability](#12-testing-diagnostics-and-reliability), [Appendix B](#appendix-b-lifecycle-and-event-routing-sequence).

### 9.12 Theme, Styling, and Visual Systems
[Back to Table of Contents](#table-of-contents)

Core types: `ThemeManager`, `ColorTheme`, `DesignTokens`, `FontManager`, `FontRoleRegistry`, `ScopedTheme`, `ScopedThemeManager`, and the theme-related drawing helpers in the control layer.

Why they exist: the framework keeps typography, color, and scoped visual state separate so scenes can be themed without coupling themselves to a single global style object.

Advanced pattern: use font roles rather than hard-coded font paths in control logic. That keeps controls and scenes visually adaptable.

Common mistakes: resolving font or color choices inside event logic; using asset-specific styling rules where a shared role would be more maintainable.

Cross-links: [Application Bootstrap](#91-application-bootstrap-and-host-configuration), [Performance and Scaling Guidance](#13-performance-and-scaling-guidance).

### 9.13 Text, Input, Forms, and Validation Systems
[Back to Table of Contents](#table-of-contents)

Core types: `TextFlow`, `TextSpan`, `TextFormatter`, `NumericFormatter`, `PatternFormatter`, `FixedPatternFormatter`, `TextSearcher`, `TextMatch`, `StringTable`, `LocaleRegistry`, `FormModel`, `FormField`, `ValidationRule`, `FieldError`, `FormSchema`, `SchemaField`, `DocumentModel`, `WizardFlow`, `WizardStep`, `WizardHandle`, and the validator classes such as `Validator`, `RequiredValidator`, `RangeValidator`, `LengthValidator`, `PatternValidator`, `CustomValidator`, `DependentValidator`, and `ValidationPipeline`.

Why they exist: text and validation need their own model layer because they are richer than basic key events and single-control input.

Advanced pattern: make text-input control behavior respect the actual input model, especially when a field starts text input, handles composition, or participates in locale-aware rendering.

Common mistakes: assuming wrapped visual lines are the same thing as logical lines; confusing text-input focus with ordinary mouse focus; pushing validation into the view layer instead of the form model.

Cross-links: [Controls](#95-controls-and-control-composition), [FAQ and Troubleshooting](#15-faq-and-troubleshooting), [Appendix F](#appendix-f-specifications-and-option-reference).

### 9.14 Data and Dataflow Helpers
[Back to Table of Contents](#table-of-contents)

Core types: `VirtualItemSource`, `FixedItemSource`, `SortFilterProxySource`, `AsyncDataProvider`, `LoadState`, `LoadStateKind`, `ObjectPool`, `DataCache`, `CacheStats`, `ListDiffCalculator`, `ListDiff`, `DiffInsert`, `DiffRemove`, `DiffMove`, and the reactive graph and dataflow helpers surfaced through routed runtime specs.

Why they exist: data views, caches, and derived projections are more efficient and more predictable when they are modeled explicitly.

Advanced pattern: use list diff and proxy-source helpers when you need stable view updates rather than replacing an entire collection every frame.

Common mistakes: recomputing derived collections in an uncontrolled loop; bypassing the proxy layer and losing invalidation benefits; conflating source identity with presentation identity.

Cross-links: [State and Observables](#94-state-and-observables), [Performance Guidance](#13-performance-and-scaling-guidance).

### 9.15 Graphics and Audio Integration Points
[Back to Table of Contents](#table-of-contents)

Graphics types: `BuiltInGraphicsFactory`, `DirtyRegionTracker`, `DrawContext`, `DrawPhase`, `AssetRegistry`, `DebugOverlay`, `SurfaceCompositor`, `Layer`, `ShapeRenderer`, `SurfaceEffects`, `VectorPath`, `SpriteSheet`, `FrameAnimation`, `ParticleSystem`, `Emitter`, `ParticleLayer`, `TileSet`, `TileMap`, `RenderTarget`, `LiveRenderTarget`, `OffscreenRenderTarget`, `create_render_target`, `create_surface`, `Node2D`, `SceneGraph2D`, and `Camera2D`.

Audio integration is intentionally a separate subsystem in the package tree. The manual does not assume a single audio workflow; instead it treats audio as a subsystem that should be wired like other runtime services.

Why they exist: rendering and asset management are kept separate from feature logic so drawing remains predictable and testable.

Advanced pattern: use offscreen render targets and dirty-region tracking when you need scene-level redraw efficiency instead of repainting everything.

Common mistakes: loading assets from arbitrary locations without respecting the current working directory contract; rebuilding surfaces every frame when a cached render target would do; conflating graphics state with feature state.

Cross-links: [Performance and Scaling Guidance](#13-performance-and-scaling-guidance), [Application Bootstrap](#91-application-bootstrap-and-host-configuration).

### 9.16 Telemetry, Introspection, and Operational Hooks
[Back to Table of Contents](#table-of-contents)

Core types: `TelemetryCollector`, `TelemetrySample`, `configure_telemetry`, `telemetry_collector`, `analyze_telemetry_log_file`, `analyze_telemetry_records`, `load_telemetry_log_file`, `render_telemetry_report`, `SceneSpatialIndex`, `PropertyRegistry`, `PropertyDescriptor`, `ui_property`, `PropertyInspectorModel`, and `InspectedProperty`.

Why they exist: the runtime needs observability and operational hooks that are cheap enough to leave in place.

Behavioral notes: telemetry is used in high-frequency app paths, not just in one-off diagnostics. The restore report and runtime profiler-style hooks are part of the operational story.

Advanced pattern: use telemetry and introspection to validate performance-sensitive refactors before and after a change rather than after a regression is already visible to users.

Common mistakes: treating telemetry as an afterthought; leaving diagnostics unbounded in high-frequency loops; using reflection or probing where a proper property registry already exists.

Cross-links: [Testing and Reliability](#12-testing-diagnostics-and-reliability), [Performance Guidance](#13-performance-and-scaling-guidance).

## 10. Integration Patterns and Composition Recipes
[Back to Table of Contents](#table-of-contents)

The cleanest composition recipes in this codebase are declarative rather than imperative.

Use `HostApplicationBindingSpec` when you want a single config object to define display, fonts, scenes, features, windows, actions, accessibility, and palette behavior. Use `SceneBundleBindingSpec` when a scene needs setup, runtime startup, navigation, and root creation as one bundle. Use `FeatureWindowBundleBindingSpec` when a feature and its window toggle metadata are inseparable.

For routed features, the best pattern is usually:

1. Build the feature and its persistent model.
2. Declare a `RoutedRuntimeSpec` for its runtime wiring.
3. Let `setup_routed_runtime` or the routed feature lifecycle helpers do the binding.
4. Keep the feature class focused on domain logic.

For chrome integration, prefer the unified visibility model. If a scene has a task panel, a scene menu strip, and a command palette, use the same `window_management_opt_in` rule consistently and let the shared presentation model keep the lists in sync.

For command palette composition, use built-in entries for scenes and windows plus a custom entries provider for app-specific commands. That keeps the palette discoverable without hardcoding the menu structure in one place.

Recipe sketch:

```python
from gui_do import HostApplicationBindingSpec, PaletteBindingSpec

spec = HostApplicationBindingSpec(
    display_size=(1920, 1080),
    window_title="gui_do demo",
    fonts={"default": {"file": "demo_features/data/fonts/Gimbot.ttf", "size": 14}},
    initial_scene_name="main",
    palette_spec=PaletteBindingSpec(include_scene_entries=True, include_window_entries=True),
)
```

The main rule is simple: let the spec say what exists, then let the runtime assemble the object graph.

## 11. End-to-End Reference Application
[Back to Table of Contents](#table-of-contents)

The reference application is the demo entrypoint plus `demo_features/demo_config.py`.

The reference flow is:

1. `gui_do_demo.py` imports `bootstrap_host_application` from `gui_do`.
2. `demo_features.demo_config` builds `DEMO_BOOTSTRAP_CONFIG` from current assets and scene bundles.
3. The host gets display, fonts, scene transitions, features, actions, window presentation, accessibility, and runtime binding.
4. The initial scene is selected.
5. The app enters `run_entrypoint`.

The demo config shows the current repository conventions in one place:

- scene bundles for `main` and `control_showcase`,
- feature bundles for `systems`, `life`, and `mandelbrot`,
- a custom command palette provider that adds main-scene commands,
- a palette toggle action,
- cursor and font assets resolved from repo-relative paths,
- telemetry disabled for the demo.

Validation checklist for a reference app:

1. The app launches from the repo root.
2. The initial scene is active.
3. The task panel and command palette show the same opted-in windows.
4. `window_management_opt_in=False` windows do not appear in shared window-management surfaces.
5. A path-based asset still resolves when it is relative to the process working directory.
6. The demo entrypoint imports only from `gui_do` root exports.

## 12. Testing, Diagnostics, and Reliability
[Back to Table of Contents](#table-of-contents)

This repo treats tests as part of the contract, not as a separate quality stage.

The most useful test families are:

- boundary tests that guard the framework/demo import split,
- public API export tests that check the root surface,
- docs contract tests that look for the required contract language,
- runtime operating tests that lock in scene chrome, bounded-area, and restore behavior,
- subsystem tests for command palette, task panel, feature lifecycle, and data-driven runtime specs.

For maintenance, use a diff checklist mindset:

1. Did the change preserve the public root import contract?
2. Did the change preserve the scene chrome contract?
3. Did the change alter any opt-in or opt-out defaults?
4. Did the change require a test update or a new regression test?
5. Did the docs and the code still agree on the current field names?

The most important diagnostics are the ones that show ownership and scope. If a subscription, handle, or disposable is not clearly owned by a runtime scope, it is a likely leak or double-dispose risk. If a scene chrome surface does not share the window-visibility model, it is a likely contract drift risk.

When debugging command palette issues, the tests to think about first are the palette-binding tests and the command-button activation tests. When debugging window visibility, think in terms of the unified visibility model, not in terms of individual UI surfaces.

## 13. Performance and Scaling Guidance
[Back to Table of Contents](#table-of-contents)

`gui_do` is designed to keep high-frequency paths measurable and bounded.

The main performance habits are:

- prefer declarative wiring over repeated imperative setup,
- keep subscriptions owned so teardown is cheap,
- use runtime scopes to make cleanup deterministic,
- batch reactive updates when a group of changes forms one logical operation,
- prefer diff/proxy/dataflow helpers over full collection rebuilds when the UI only needs incremental changes,
- use telemetry in hot paths where it helps explain runtime cost.

The scheduler budget policy is intentionally bounded. That means frame-time budgeting should be treated as an explicit contract rather than an optimization afterthought.

For graphics-heavy or scene-heavy demos, keep in mind:

1. Asset loads resolved relative to the process working directory should be stable and predictable.
2. Offscreen or dirty-region techniques are better than unconditional redraws when the scene is large.
3. Window and task-panel chrome should not be recomputed from scratch if the shared presentation model already knows the visibility state.

Scaling tip: if a feature class starts accumulating too many imperative bindings, move those bindings into a routed runtime spec and let the helper functions own the repetitive wiring.

## 14. Migration, Versioning, and Deprecation Notes
[Back to Table of Contents](#table-of-contents)

The package treats the root `gui_do` import as the stable consumer surface. Internal modules are implementation details unless explicitly promoted to the root API.

When migrating code inside this repo, prefer these rules:

- use explicit named imports from `gui_do`,
- avoid star imports,
- avoid reaching into `gui_do.features.*` or other internal modules from consumer code,
- prefer the current spec types and helper builders over legacy handwritten setup code,
- remove stale prose when the runtime contract changes.

Deprecation guidance is intentionally conservative. If an older path is still documented as supported, keep it stable until the docs and tests move together. If a new helper is added but a legacy path still works, prefer the new helper in new code and leave a test in place for the older behavior until the migration is complete.

Obsolete content should be removed from the manual when the live code path has moved on. That is especially important for chrome rules, palette behavior, and spec fields that are often renamed during cleanup passes.

## 15. FAQ and Troubleshooting
[Back to Table of Contents](#table-of-contents)

Why is my asset path failing? Usually because the path is being resolved relative to the process working directory. If you launch from a different directory, a relative asset path can point somewhere else.

Why does a scene chrome item appear in one place but not another? The scene menu strip, task panel, and command palette are unified by the same visibility model. If one surface is missing a window, check the opt-in flag on the underlying window spec and the shared presentation model rather than patching the surface in isolation.

Why did my command palette entry close after activation? The toggle and action binds are different. The action bind is supposed to activate entries while preserving the open palette state when that is the intended interaction model.

Why is text input acting oddly on wrapped lines? The text controls treat logical lines and visual wrap lines differently. That distinction matters in caret movement, Home/End behavior, and selection boundaries.

Why does a feature leak subscriptions or handlers? Most likely a runtime-owned cleanup was not attached to the correct feature scope. The fix is usually to move the binding into the runtime-scope ownership path.

Why should I care about the package layout contract? Because the demo packages are part of the way the repo keeps reusable framework code separate from consumer code. The package layout is not just tidy; it is part of the boundary that keeps the framework importable.

## 16. Appendix
[Back to Table of Contents](#table-of-contents)

### Appendix A. Glossary
[Back to Table of Contents](#table-of-contents)

- Feature: a unit of behavior with build and runtime phases.
- Scene: a runtime context that scopes routing, chrome, and visibility.
- Runtime scope: an ownership container for subscriptions, services, and cleanup.
- Routed runtime: declarative binding that wires services, effects, and operations.
- Chrome: scene or window UI that is not the main content surface.
- Opt-in: a spec flag that includes a window in shared visibility systems.
- Opt-out: an explicit exclusion from those systems.
- Presentation model: the object graph that tracks scene/window ownership and visibility.
- Command palette: the command surface that exposes scene and window entries plus custom actions.

### Appendix B. Lifecycle and Event Routing Sequence
[Back to Table of Contents](#table-of-contents)

1. Host bootstrap creates display, app, scene transitions, features, and chrome bindings.
2. Feature `build` constructs feature-owned state and controls.
3. Feature `bind_runtime` attaches live subscriptions, services, and actions.
4. Raw input is normalized to `GuiEvent`.
5. Global keys and global pointer actions are checked first.
6. Overlays, focus, window chrome, features, and scene handlers are consulted in order.
7. Scene update work runs only for the active scene.
8. Scheduling, animation, and transition work advance.
9. Draw occurs using the current scene and chrome state.
10. Teardown disposes runtime-owned cleanup in reverse order.

### Appendix C. System Dependency Map
[Back to Table of Contents](#table-of-contents)

The main dependency shape is:

- bootstrap depends on config/spec builders,
- feature lifecycle depends on state, events, scheduling, and runtime scopes,
- command surfaces depend on actions, events, focus, and window presentation,
- task panel and scene menu strip depend on the shared visibility model,
- persistence depends on workspace state and scene snapshots,
- telemetry and introspection depend on runtime hooks and property registries.

In practice, the system graph is safest when dependencies flow downward from the root package and upward from specs into runtime objects, not sideways through consumer-only modules.

### Appendix D. API Quick Index by Topic
[Back to Table of Contents](#table-of-contents)

Bootstrap: `bootstrap_host_application`, `HostApplicationConfig`, `build_host_application_config`, `SceneBundleBindingSpec`, `FeatureWindowBundleBindingSpec`.

Feature lifecycle: `Feature`, `DirectFeature`, `LogicFeature`, `RoutedFeature`, `FeatureManager`, `FeatureRuntimeScope`, `FeatureOperationBus`, `FeatureOperationContext`.

Events and actions: `GuiEvent`, `EventManager`, `EventBus`, `ActionManager`, `ActionRegistry`, `InputMap`, `InputBinding`.

State and observables: `ObservableValue`, `PresentationModel`, `Binding`, `CollectionView`, `ObservableList`, `ObservableDict`.

Chrome and overlays: `MenuStripSpec`, `SceneTaskPanelSpec`, `TaskPanelWindowToggleGroupSpec`, `SceneCommandPaletteSpec`, `PaletteBindingSpec`, `CommandPaletteManager`, `CommandEntry`, `OverlayManager`.

Layout and controls: `FlexLayout`, `GridLayout`, `ConstraintLayout`, `PanelControl`, `ButtonControl`, `TextInputControl`, `TextAreaControl`, `WindowControl`, `TaskPanelControl`.

Persistence and diagnostics: `WorkspacePersistenceManager`, `WorkspaceState`, `SceneSnapshot`, `TelemetryCollector`, `TelemetrySample`, `configure_telemetry`.

#### Appendix D.1. Tier-to-System Reference Matrix
[Back to Table of Contents](#table-of-contents)

| Tier / Area | Main chapter |
| --- | --- |
| Bootstrap and host config | [9.1 Application Bootstrap and Host Configuration](#91-application-bootstrap-and-host-configuration) |
| Feature lifecycle | [9.2 Feature Lifecycle and Feature Types](#92-feature-lifecycle-and-feature-types) |
| Events, actions, input | [9.3 Events, Actions, Input Mapping, and Routing](#93-events-actions-input-mapping-and-routing) |
| State and observables | [9.4 State and Observables](#94-state-and-observables) |
| Controls | [9.5 Controls and Control Composition](#95-controls-and-control-composition) |
| Layout | [9.6 Layout Systems](#96-layout-systems) |
| Focus and accessibility | [9.7 Focus and Accessibility](#97-focus-and-accessibility) |
| Overlays and command surfaces | [9.8 Overlays, Dialogs, Notifications, and Command Surfaces](#98-overlays-dialogs-notifications-and-command-surfaces) |
| Scene/window/task-panel presentation | [9.9 Scene, Window, and Task-Panel Presentation Models](#99-scene-window-and-task-panel-presentation-models) |
| Scheduling and animation | [9.10 Scheduling, Timing, Animation, and Transitions](#910-scheduling-timing-animation-and-transitions) |
| Persistence | [9.11 Persistence and Workspace/Session State](#911-persistence-and-workspace-session-state) |
| Theme and styling | [9.12 Theme, Styling, and Visual Systems](#912-theme-styling-and-visual-systems) |
| Text, input, forms | [9.13 Text, Input, Forms, and Validation Systems](#913-text-input-forms-and-validation-systems) |
| Data and dataflow | [9.14 Data and Dataflow Helpers](#914-data-and-dataflow-helpers) |
| Graphics and audio | [9.15 Graphics and Audio Integration Points](#915-graphics-and-audio-integration-points) |
| Telemetry and introspection | [9.16 Telemetry, Introspection, and Operational Hooks](#916-telemetry-introspection-and-operational-hooks) |

#### Appendix D.2. Public API Selection Heuristics
[Back to Table of Contents](#table-of-contents)

Use the root `gui_do` import when the symbol is meant for consumers.

Use a concrete internal module only when you are working inside the framework implementation and the symbol is not part of the public contract.

Use a spec builder when the work is about app assembly, scene composition, or window/chrome declaration.

Use a runtime scope when the work is about ownership, cleanup, and deterministic teardown.

Use tests as the final arbiter when a behavior seems ambiguous or underdocumented.

### Appendix E. Architecture Templates
[Back to Table of Contents](#table-of-contents)

Template 1: demo entrypoint.

```python
from gui_do import bootstrap_host_application

bootstrap_host_application(self, DEMO_BOOTSTRAP_CONFIG)
```

Template 2: routed feature.

```python
class MyRoutedFeature(Feature):
    def build(self, host) -> None:
        self.model = ...

    def bind_runtime(self, host) -> None:
        ...
```

Template 3: unified visibility declaration.

```python
WindowSpec(..., window_management_opt_in=True)
```

Template 4: command palette with two binds.

```python
SceneCommandPaletteSpec(
    scene_name="main",
    toggle=PaletteInputBindSpec(action_name="command_palette_toggle", key=116),
    action=PaletteInputBindSpec(action_name="command_palette_action", pointer_button=2),
)
```

Template 5: runtime scope ownership.

```python
runtime_scope.bind_service("db", database)
runtime_scope.subscribe(observable, handler)
runtime_scope.dispose()
```

### Appendix F. Specifications and Option Reference
[Back to Table of Contents](#table-of-contents)

This appendix catalogs the discovered spec families and their notable fields or options. It is intentionally focused on the options that shape behavior in the current repository.

#### F.1 Bootstrap, Scene, and Window Bundle Specs

| Spec name | Field or option name | Purpose | Default / notable behavior | Cross-reference chapter |
| --- | --- | --- | --- | --- |
| `HostApplicationBindingSpec` | `display_size`, `window_title`, `fonts`, `initial_scene_name` | Define app bootstrap inputs | Required assembly inputs | [9.1](#91-application-bootstrap-and-host-configuration) |
| `HostApplicationBindingSpec` | `scene_bundle_entries`, `feature_entries`, `window_entries` | Group scene and feature declarations | Accepts binding specs or concrete specs | [9.1](#91-application-bootstrap-and-host-configuration) |
| `HostApplicationBindingSpec` | `palette_spec` | Declare palette behavior | Optional | [9.8](#98-overlays-dialogs-notifications-and-command-surfaces) |
| `SceneBundleBindingSpec` | `scene_name`, `pretty_name`, `transition_style`, `transition_duration` | Bundle scene setup | Can emit setup/runtime/root/nav specs | [9.1](#91-application-bootstrap-and-host-configuration) |
| `SceneBundleBindingSpec` | `make_initial` | Mark initial scene | Optional initial scene flag | [9.1](#91-application-bootstrap-and-host-configuration) |
| `SceneBundleBindingSpec` | `tiling_enabled`, `tiling_gap`, `tiling_padding`, `tiling_avoid_task_panel`, `tiling_center_on_failure`, `tiling_relayout` | Control scene tiling defaults | Used by scene setup helpers | [9.1](#91-application-bootstrap-and-host-configuration) |
| `SceneBundleBindingSpec` | `pristine_asset`, `bind_escape_to_exit`, `prewarm` | Runtime scene startup options | Emitted into `RuntimeSceneSpec` when requested | [9.11](#911-persistence-and-workspace-session-state) |
| `FeatureWindowBundleBindingSpec` | `feature_attribute_name`, `factory`, `window_key` | Pair feature and window metadata | Self-contained feature/window bundle | [9.9](#99-scene-window-and-task-panel-presentation-models) |
| `FeatureWindowBundleBindingSpec` | `task_panel_slot_index`, `task_panel_label`, `task_panel_style` | Window toggle presentation | Slot ordering feeds task panel and palette order | [9.9](#99-scene-window-and-task-panel-presentation-models) |
| `FeatureWindowBundleBindingSpec` | `window_effects`, `window_management_opt_in` | Window behavior and shared visibility opt-in | `window_management_opt_in=True` by default | [9.9](#99-scene-window-and-task-panel-presentation-models) |
| `WindowSpec` | `feature_attribute_name`, `toggle_attribute_name` | Bind a feature-owned window toggle | Root binding metadata for presentation | [9.9](#99-scene-window-and-task-panel-presentation-models) |
| `WindowSpec` | `task_panel_slot_index`, `task_panel_label`, `task_panel_style` | Task-panel presentation | `window_management_opt_in=True` by default | [9.9](#99-scene-window-and-task-panel-presentation-models) |
| `WindowSpec` | `window_management_opt_in` | Shared chrome inclusion flag | Opts out of menu strip, task panel, and command palette | [9.9](#99-scene-window-and-task-panel-presentation-models) |
| `AnchoredWindowSpec` | `anchor`, `margin`, `use_frame_backdrop`, `window_management_opt_in` | Presenter-backed anchored window options | Opt-in by default | [9.9](#99-scene-window-and-task-panel-presentation-models) |
| `RuntimeSceneSpec` | `scene_name`, `pristine_asset`, `bind_escape_to_exit`, `prewarm` | Scene startup options | `pristine_asset=None`, `bind_escape_to_exit=False`, `prewarm=False` | [9.11](#911-persistence-and-workspace-session-state) |
| `SceneRootSpec` | `scene_name`, `control_id`, `draw_background` | Declare scene root control | `draw_background=False` by default | [9.1](#91-application-bootstrap-and-host-configuration) |
| `CursorSpec` | `name`, `path`, `hotspot` | Register application cursor | Hotspot is a tuple coordinate | [9.15](#915-graphics-and-audio-integration-points) |
| `FontRoleBindingSpec` | `role`, `size`, `font`, `bold`, `italic` | Declare font-role bindings | Style flags default to `False` | [9.12](#912-theme-styling-and-visual-systems) |
| `ActionSpec` | `action_id`, `label`, `kind`, `target`, `category`, `key` | Declare host-level actions | `kind` drives handler creation | [9.3](#93-events-actions-input-mapping-and-routing) |
| `ActionBindingSpec` | `kind`, `action_id`, `label`, `target`, `category`, `key` | Builder-friendly action declaration | Same logical role as `ActionSpec` | [9.3](#93-events-actions-input-mapping-and-routing) |

#### F.2 Window Chrome, Task Panel, Menu Strip, and Palette Specs

| Spec name | Field or option name | Purpose | Default / notable behavior | Cross-reference chapter |
| --- | --- | --- | --- | --- |
| `SceneTaskPanelSpec` | `scene_name`, `control_id`, `height` | Create a scene task panel | `height=50` by default | [9.9](#99-scene-window-and-task-panel-presentation-models) |
| `SceneTaskPanelSpec` | `hidden_peek_pixels`, `animation_step_px`, `dock_bottom`, `auto_hide` | Task-panel presentation and motion | Auto-hide is enabled by default | [9.9](#99-scene-window-and-task-panel-presentation-models) |
| `TaskPanelButtonSpec` | `attr_name`, `control_id`, `label`, `on_click`, `slot_index`, `style` | Declare task-panel buttons | `style="angle"` by default | [9.9](#99-scene-window-and-task-panel-presentation-models) |
| `RightAnchoredTaskPanelButtonSpec` | `width`, `height`, `top_offset`, `right_padding` | Declare a right-anchored task-panel button | Optional focus-cycle inclusion | [9.9](#99-scene-window-and-task-panel-presentation-models) |
| `TaskPanelWindowToggleGroupSpec` | `start_index` | Place automatic window toggles | Default `1` | [9.9](#99-scene-window-and-task-panel-presentation-models) |
| `TaskPanelSceneNavButtonSpec` | `control_id`, `slot_index`, `label`, `target_scene`, `accessibility_label` | Declare task-panel scene navigation | Defaults to a return button | [9.9](#99-scene-window-and-task-panel-presentation-models) |
| `MenuStripSpec` | `scenes_shown`, `windows_shown` | Control menu strip sections | Both default to `True` | [9.8](#98-overlays-dialogs-notifications-and-command-surfaces) |
| `MenuStripSpec` | `scene_menu_mode`, `scene_menu_opt_in_scene_names`, `scene_menu_include_current_scene` | Control scene menu population | Defaults to `add_all` mode | [9.8](#98-overlays-dialogs-notifications-and-command-surfaces) |
| `MenuStripSpec` | `static_entries`, `tools_exclude_labels`, `on_window_toggled` | Customize window and tool entries | Optional hooks and filters | [9.8](#98-overlays-dialogs-notifications-and-command-surfaces) |
| `SceneCommandPaletteSpec` | `scene_name`, `toggle`, `action` | Declare palette input binds | Two-bind model by design | [9.8](#98-overlays-dialogs-notifications-and-command-surfaces) |
| `PaletteInputBindSpec` | `action_name`, `key`, `pointer_button` | One palette input bind | Key and pointer are both optional | [9.8](#98-overlays-dialogs-notifications-and-command-surfaces) |
| `PaletteBindingSpec` | `enable_builtin_entries`, `include_scene_entries`, `include_window_entries` | Select built-in palette groups | All default to `True` | [9.8](#98-overlays-dialogs-notifications-and-command-surfaces) |
| `PaletteBindingSpec` | `group_order`, `custom_entries_provider`, `connect_window_presentation` | Control palette composition | Window entries can follow task-panel ordering | [9.8](#98-overlays-dialogs-notifications-and-command-surfaces) |
| `TaskPanelFocusToggleSpec` | `action_name`, `scene_name`, `key` | Register task-panel focus toggle | Scene-scoped action binding | [9.7](#97-focus-and-accessibility) |
| `GlobalPointerActionSpec` | `action_name`, `button`, `scene_name` | Register global pointer action | Routed before overlay/focus/scene handlers | [9.3](#93-events-actions-input-mapping-and-routing) |
| `LogicBindingSpec` | `alias`, `provider_name` | Map routed-feature aliases | Connects logical providers | [9.2](#92-feature-lifecycle-and-feature-types) |
| `TooltipBindingSpec` | `control_attr`, `message` | Attach tooltips by attribute | Skips missing controls | [9.8](#98-overlays-dialogs-notifications-and-command-surfaces) |

#### F.3 Routed Runtime, Operations, and Lifecycle Specs

| Spec name | Field or option name | Purpose | Default / notable behavior | Cross-reference chapter |
| --- | --- | --- | --- | --- |
| `RoutedRuntimeSpec` | `scene_name`, `scheduler_attr_name`, `runtime_scope_attr_name` | Define routed runtime anchors | Defaults to `scene_name="main"` | [9.2](#92-feature-lifecycle-and-feature-types) |
| `RoutedRuntimeSpec` | `service_bindings`, `service_consumers`, `logic_bindings` | Declare service and alias wiring | All default to empty sequences | [9.2](#92-feature-lifecycle-and-feature-types) |
| `RoutedRuntimeSpec` | `store_subscriptions`, `store_selectors`, `observable_effects`, `signal_effects` | Declare reactive bindings | Declarative effects are owned by runtime scope | [9.4](#94-state-and-observables) |
| `RoutedRuntimeSpec` | `failure_policies`, `operations`, `operation_bus_attr_name` | Declare operation bus behavior | Optional operation bus | [9.2](#92-feature-lifecycle-and-feature-types) |
| `RoutedRuntimeSpec` | `action_hotkeys`, `control_key_bindings`, `event_subscriptions` | Declare input and event hooks | Optional scene/runtime bindings | [9.3](#93-events-actions-input-mapping-and-routing) |
| `RoutedRuntimeSpec` | `shortcut_overlays`, `task_panel_focus_toggles`, `global_pointer_actions` | Declare chrome and pointer hooks | Higher-level routed faculties | [9.8](#98-overlays-dialogs-notifications-and-command-surfaces) |
| `RoutedRuntimeSpec` | `feature_dependencies` | Declare ordered feature requirements | Optional dependency list | [9.2](#92-feature-lifecycle-and-feature-types) |
| `RoutedRuntimeSpec` | `execution_context_spec`, `budget_spec`, `checkpoint_spec` | Declare execution and budget state | Optional operational wiring | [9.10](#910-scheduling-timing-animation-and-transitions) |
| `RoutedRuntimeSpec` | `saga_specs`, `reactive_graph_spec`, `migration_spec` | Declare durable workflow and migration behavior | Optional advanced runtime graphs | [9.10](#910-scheduling-timing-animation-and-transitions) |
| `RoutedRuntimeSpec` | `policy_specs`, `effect_bindings`, `event_pipelines` | Declare runtime policy and pipelines | Optional policy/effect layers | [9.10](#910-scheduling-timing-animation-and-transitions) |
| `RoutedRuntimeSpec` | `durable_queue_spec`, `capability_providers`, `capability_requirements` | Declare durable operations and capabilities | Optional durable runtime layers | [9.10](#910-scheduling-timing-animation-and-transitions) |
| `RoutedRuntimeSpec` | `projection_spec`, `workflow_specs`, `recompute_nodes` | Declare derived runtime work | Optional recomputation and workflow graph | [9.14](#914-data-and-dataflow-helpers) |
| `RoutedRuntimeSpec` | `qos_policies`, `health_probes`, `replay_spec`, `replace_policy` | Declare reliability and replay behavior | Optional operational policy stack | [9.16](#916-telemetry-introspection-and-operational-hooks) |
| `RoutedFeatureLifecycleSpec` | `companion_providers`, `runtime_spec`, `runtime_spec_factory` | Keep routed feature lifecycle thin | Runtime spec can be generated per feature | [9.2](#92-feature-lifecycle-and-feature-types) |
| `FailurePolicySpec` | `retries`, `retry_delay_seconds`, `timeout_seconds` | Define retry/timeout policy | Values are clamped non-negative | [9.2](#92-feature-lifecycle-and-feature-types) |
| `FailurePolicySpec` | `publish_topic`, `publish_scope` | Publish failure outcomes | Optional telemetry/event integration | [9.16](#916-telemetry-introspection-and-operational-hooks) |
| `FeatureOperationSpec` | `name`, `handler`, `failure_policy` | Register an operation handler | Optionally references a failure policy | [9.2](#92-feature-lifecycle-and-feature-types) |
| `FeatureOperationContext` | `feature`, `host`, `runtime_scope`, `handle`, `attempt_index` | Pass execution context to operations | Tracks attempt count and cancellation state | [9.2](#92-feature-lifecycle-and-feature-types) |
| `FeatureOperationHandle` | `request_id`, `operation_name`, `status`, `result`, `error`, `progress` | Track one operation request | Mutable status handle with cancel support | [9.2](#92-feature-lifecycle-and-feature-types) |
| `FeatureRuntimeScope` | cleanup bag, child `ServiceScope` | Own subscriptions and service disposal | Reverse-order cleanup on dispose | [9.2](#92-feature-lifecycle-and-feature-types) |
| `FeatureWindowBundleBindingSpec` | `window_management_opt_in` | Control shared visibility participation | True by default | [9.9](#99-scene-window-and-task-panel-presentation-models) |
| `SceneSetupBindingSpec` | `tiling_enabled`, `tiling_gap`, `tiling_padding` | Scene layout defaults | Helps scene setup helpers stay concise | [9.1](#91-application-bootstrap-and-host-configuration) |
| `RuntimeSceneBindingSpec` | `pristine_asset`, `bind_escape_to_exit`, `prewarm` | Shorthand runtime scene inputs | Mirrors `RuntimeSceneSpec` | [9.11](#911-persistence-and-workspace-session-state) |
| `SceneRootBindingSpec` | `scene_name`, `control_id`, `draw_background` | Shorthand scene root inputs | Mirrors `SceneRootSpec` | [9.1](#91-application-bootstrap-and-host-configuration) |
| `CursorBindingSpec` | `name`, `path`, `hotspot` | Shorthand cursor inputs | Hotspot defaults to `(0, 0)` | [9.15](#915-graphics-and-audio-integration-points) |
| `SceneBundleBindingSpec` | `emit_scene_setup_spec`, `emit_runtime_scene_spec`, `emit_nav_action_spec`, `emit_scene_root_spec` | Control which specs are emitted | Fine-grained bundle generation | [9.1](#91-application-bootstrap-and-host-configuration) |

#### F.4 Accessibility and Tab-Builder Specs

| Spec name | Field or option name | Purpose | Default / notable behavior | Cross-reference chapter |
| --- | --- | --- | --- | --- |
| `AccessibilitySequenceSpec` | `control_attr`, `role`, `label` | Apply accessibility metadata from attributes | Skips missing attributes | [9.7](#97-focus-and-accessibility) |
| `TabBuilderSpec` | `key`, `label`, `builder_attr` | Bind tab labels to builders | Declarative tab-builder entry | [9.7](#97-focus-and-accessibility) |
| `PresenterLabelSpec` | `control_id`, `height`, `text`, `advance`, `width`, `x_offset` | Place labels in tab-builder helpers | `advance=None` uses context default | [9.5](#95-controls-and-control-composition) |
| `PresenterButtonSpec` | `control_id`, `width`, `height`, `text`, `handler_attr`, `advance`, `x_offset`, `style` | Place buttons in tab-builder helpers | Handler resolved by attribute name | [9.5](#95-controls-and-control-composition) |
| `StaticAccessibilitySpec` | `control_attr`, `role`, `label` | Attach static accessibility metadata | Host-level annotation | [9.7](#97-focus-and-accessibility) |

#### F.5 Helper Builder and Runtime Composition Notes

| Builder/helper | Notable option or behavior | Purpose | Cross-reference chapter |
| --- | --- | --- | --- |
| `build_feature_window_bundle_specs` | Consumes feature/window bundle inputs | Produce aligned feature and window specs | [9.1](#91-application-bootstrap-and-host-configuration) |
| `build_window_toggle_specs` | Converts window binding inputs to `WindowSpec` | Build window visibility model inputs | [9.9](#99-scene-window-and-task-panel-presentation-models) |
| `build_scene_bundle_specs` | Converts scene bundle inputs | Emit scene setup, runtime, root, and nav specs | [9.1](#91-application-bootstrap-and-host-configuration) |
| `build_action_specs` | Converts action binding inputs to `ActionSpec` | Create host-level actions | [9.3](#93-events-actions-input-mapping-and-routing) |
| `setup_scene_command_palette_bindings` | Uses toggle/action two-bind model | Register palette input bindings | [9.8](#98-overlays-dialogs-notifications-and-command-surfaces) |
| `bind_palette_window_action_bind` | Activates window entries with logical-pointer fallback | Preserve open palette behavior | [9.8](#98-overlays-dialogs-notifications-and-command-surfaces) |
| `bind_runtime_scene_exit_keys` | Binds exit only for opted-in scenes | Scene-scoped exit wiring | [9.11](#911-persistence-and-workspace-session-state) |
| `apply_runtime_scene_pristine_assets` | Applies only configured assets | Scene restore/bootstrap helper | [9.11](#911-persistence-and-workspace-session-state) |
| `prewarm_runtime_scenes` | Queues opted-in scenes for prewarm | Deferred startup support | [9.11](#911-persistence-and-workspace-session-state) |
