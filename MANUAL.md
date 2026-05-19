# gui_do Manual

A discovery-verified, code-aligned manual for building, operating, and maintaining gui_do applications. This document explains conceptual foundations first, then walks through practical setup, architecture, and all public runtime systems, with contract notes that map directly to the current source, tests, and docs.

## Table of Contents

- [Title and Purpose](#gui_do-manual)
- [Table of Contents](#table-of-contents)
- [How to Use This Manual](#how-to-use-this-manual)
- [Conceptual Foundations (Theory)](#conceptual-foundations-theory)
- [Quickstart Path (Practice)](#quickstart-path-practice)
- [Architecture and Runtime Model](#architecture-and-runtime-model)
- [Core Workflow: Build, Bind, Route, Update, Draw](#core-workflow-build-bind-route-update-draw)
- [Main Systems Reference](#main-systems-reference)
- [8.1 Application Bootstrap and Host Configuration](#application-bootstrap-and-host-configuration)
- [8.2 Feature Lifecycle and Feature Types](#feature-lifecycle-and-feature-types)
- [8.3 Events, Actions, Input Mapping, and Routing](#events-actions-input-mapping-and-routing)
- [8.4 State and Observables](#state-and-observables)
- [8.5 Controls and Control Composition](#controls-and-control-composition)
- [8.6 Layout Systems](#layout-systems)
- [8.7 Focus and Accessibility](#focus-and-accessibility)
- [8.8 Overlays, Dialogs, Notifications, and Command Surfaces](#overlays-dialogs-notifications-and-command-surfaces)
- [8.9 Scene, Window, and Task-Panel Presentation Models](#scene-window-and-task-panel-presentation-models)
- [8.10 Scheduling, Timing, Animation, and Transitions](#scheduling-timing-animation-and-transitions)
- [8.11 Persistence and Workspace/Session State](#persistence-and-workspacesession-state)
- [8.12 Theme, Styling, and Visual Systems](#theme-styling-and-visual-systems)
- [8.13 Text, Input, Forms, and Validation Systems](#text-input-forms-and-validation-systems)
- [8.14 Data and Dataflow Helpers](#data-and-dataflow-helpers)
- [8.15 Graphics and Audio Integration Points](#graphics-and-audio-integration-points)
- [8.16 Telemetry, Introspection, and Operational Hooks](#telemetry-introspection-and-operational-hooks)
- [Integration Patterns and Composition Recipes](#integration-patterns-and-composition-recipes)
- [End-to-End Reference Application](#end-to-end-reference-application)
- [Testing, Diagnostics, and Reliability](#testing-diagnostics-and-reliability)
- [Performance and Scaling Guidance](#performance-and-scaling-guidance)
- [Migration, Versioning, and Deprecation Notes](#migration-versioning-and-deprecation-notes)
- [FAQ and Troubleshooting](#faq-and-troubleshooting)
- [Appendix](#appendix)
- [Appendix A: Glossary](#appendix-a-glossary)
- [Appendix B: Lifecycle and Event Sequence](#appendix-b-lifecycle-and-event-sequence)
- [Appendix C: System Dependency Map](#appendix-c-system-dependency-map)
- [Appendix D: API Quick Index](#appendix-d-api-quick-index)
- [Appendix D.1: Tier Matrix](#appendix-d1-tier-matrix)
- [Appendix D.2: Selection Heuristics](#appendix-d2-selection-heuristics)
- [Appendix E: Architecture Templates](#appendix-e-architecture-templates)
- [Appendix F: Specifications and Option Reference](#appendix-f-specifications-and-option-reference)

## How to Use This Manual
[Back to Table of Contents](#table-of-contents)

This manual is organized to support three usage modes.

- Learn mode: start at theory, then move into quickstart and the core workflow before opening system chapters.
- Build mode: use quickstart, architecture/runtime model, then system chapters 8.1 through 8.16 as you wire concrete features.
- Maintain mode: use testing, migration, and appendices (tier matrix and specification reference) to validate change impact.

### Reading Paths

- Beginner path: sections 4, 5, 6, 7, then 8.1, 8.2, 8.3, 8.4, 8.5, and 8.9.
- Intermediate path: sections 6, 7, then the specific system chapters you are actively integrating.
- Maintainer path: sections 11, 12, 13, 15 and Appendix D through F.

### Tri-Lens Markers

Use each chapter through three lenses.

- Concept lens: why this system exists and where it fits.
- Implementation lens: which APIs/specs to use and in which lifecycle phase.
- Reliability lens: teardown, failure modes, and tests that guard the contract.

### Contract Alignment

Normative behavior is defined by code and contracts in `docs/`.

- `docs/public_api_spec.md` for tiered public API framing.
- `docs/runtime_operating_contracts.md` for scheduler and workspace restore runtime guarantees.
- `docs/architecture_boundary_spec.md` for framework/demo boundary rules.

### Known Non-Goals

- Exact OS-native widget parity across all platforms.
- Replacing domain/business architecture decisions in consumer applications.
- Making internal infrastructure tiers a beginner entrypoint.
- Treating star-import behavior as a compatibility guarantee.

## Conceptual Foundations (Theory)
[Back to Table of Contents](#table-of-contents)

gui_do is designed so application structure is declarative while feature behavior stays imperative. The framework expects you to describe scenes, features, actions, windows, and runtime wiring through spec objects, then uses bootstrap and lifecycle helpers to build, bind, route, and tear down those systems consistently.

### Data-Driven Design

Data-driven design in gui_do means the runtime configuration is first-class data. You do not wire the app by hand with long sequences of calls that are difficult to diff and test. Instead, you shape a `HostApplicationBindingSpec` (or direct `HostApplicationConfig`) and let `build_host_application_config` plus `bootstrap_host_application` realize the full graph.

This split is intentional. Build-time assembly resolves declarations and cross references. Run-time execution consumes that assembled configuration and starts the app. The two-phase model gives deterministic setup and makes configuration testable in isolation before any frame loop starts.

In imperative UI wiring, adding one shortcut often means touching input handlers, action routing, and cleanup logic in multiple locations. In gui_do, that is typically one declaration (`ActionSpec`, `ActionHotkeySpec`, or a routed runtime bind spec) with wiring and teardown handled by runtime helpers.

The same pattern protects your bootstrap layer from internal package refactors. If a feature package reorganizes into `*_feature.py`, `*_presenter.py`, or `*_logic_feature.py`, bootstrap behavior remains stable so long as the exported integration names and binding specs stay consistent.

Data-driven specs are also forward-compatible by design. Named fields let new optional behavior land without breaking all existing call sites. That is much harder with broad positional-argument APIs.

The boundary is clear: structure and runtime graph wiring are declarative; feature behavior in `build`, `bind_runtime`, `handle_event`, `on_update`, and `draw` remains imperative Python.

```python
from gui_do import HostApplicationBindingSpec, build_host_application_config, bootstrap_host_application


class MyHost:
	pass


host = MyHost()
config = build_host_application_config(
	HostApplicationBindingSpec(
		display_size=(1280, 720),
		window_title="My gui_do app",
		initial_scene_name="main",
		feature_entries=(),
	)
)
bootstrap_host_application(host, config)
```

[Back to Table of Contents](#table-of-contents)

### Reactive Data and Observable State

Reactive state in gui_do is built on observables. Producers update values; subscribers react without producer-side knowledge of who is listening. This lets controls and sibling features update from a shared state source without brittle direct coupling.

Core primitives are `ObservableValue`, `ObservableList`, and `ObservableDict`. For multi-write bursts, `reactive_batch` and `is_batching` reduce redundant notification churn. For derived state, `ComputedValue` models dependency-driven recomputation in a first-class way.

The lifecycle rule is strict: subscribe in runtime phases (`bind_runtime`) and dispose in teardown (`shutdown_runtime`). Doing subscription work in `build` is a common source of ordering bugs and dangling callbacks.

#### Automatic Subscription Ownership and Cleanup

Automatic ownership exists as a safety contract, not convenience sugar. `FeatureRuntimeScope` can own unsubscribe/disconnect/dispose operations and run them during `dispose()`. Routed runtime bindings (`setup_routed_runtime` and `shutdown_routed_runtime`) rely on this to keep setup and cleanup symmetric.

Operationally, this prevents major failure classes: leaked subscribers, retained feature instances after scene switch, callbacks against dead controls, duplicate notification chains after repeated bind cycles, and partial cleanup when one teardown branch is forgotten.

This does not replace lifecycle discipline. You still bind in the right phase and ensure shutdown runs. The framework guarantees owned runtime resources do not outlive the feature scope that created them.

```python
from gui_do import FeatureRuntimeScope


# Fragile pattern: manual handle tracking everywhere.
unsub = observable.subscribe(handler)
# ... later, easy to forget unsub()

# Lifecycle-owned pattern.
scope = FeatureRuntimeScope()
scope.subscribe(observable, handler)
# ... at shutdown
scope.dispose()
```

[Back to Table of Contents](#table-of-contents)

### Feature Composition and Lifecycles

Features are the primary composition unit. `Feature`, `DirectFeature`, `LogicFeature`, and `RoutedFeature` give explicit tradeoffs for UI-heavy, draw-heavy, logic-heavy, and routed orchestration scenarios.

Lifecycle semantics matter more than inheritance style. `build` creates stable structure. `bind_runtime` wires dynamic dependencies (subscriptions, actions, cross-feature links). `handle_event`, `on_update`, and `draw` run frame-time behavior. `shutdown_runtime` unwinds runtime-owned resources.

`HOST_REQUIREMENTS` makes dependency expectations explicit per phase and fails early when host members are missing. This prevents hidden runtime assumptions.

For inter-feature coordination, use messages (`FeatureMessage`) and shared observables instead of direct cross-feature control mutation. That keeps boundaries clear as scenes grow.

Routed runtime facilities extend lifecycle composition by declaring services, effects, subscriptions, and operations in one `RoutedRuntimeSpec`. Setup occurs in `setup_routed_runtime`; teardown occurs in `shutdown_routed_runtime`, with runtime-scope ownership handling cleanup symmetry.

[Back to Table of Contents](#table-of-contents)

### Higher-Level Runtime Faculties and Composition

The routed runtime control plane now includes higher-level faculties that sit beside service/effect/operation wiring rather than replacing them. These are declared through sibling fields on `RoutedRuntimeSpec` and materialized into runtime systems during bind.

#### Spec Family Discovery Table

| Spec family | Key specs | Runtime counterparts | Primary role |
| --- | --- | --- | --- |
| Policy/admission | `RuntimePolicySpec` | `RuntimePolicyEngine`, `PolicyDecision` | Evaluate whether work should run and under which policy gate |
| Effect lifetime | `EffectBindingSpec` | `EffectLifetimeOrchestrator` | Own effect setup/teardown within runtime scope |
| Event pipelines | `EventPipelineStageSpec`, `EventPipelineSpec` | `EventPipelineRuntime` | Compose staged routed event processing |
| Durable operations | `DurableOperationBindingSpec`, `DurableOperationQueueSpec`, `DurableQueueRecord` | `DurableOperationQueueRuntime` | Retry/recover durable operation records |
| Capability contracts | `CapabilityProviderSpec`, `CapabilityRequirementSpec` | `CapabilityContractRuntime` | Match required vs provided capabilities across runtime participants |
| Projections | `ProjectionNodeSpec`, `ProjectionSpec` | `ProjectionRuntime` | Incremental derived projection updates |
| Dependencies | `FeatureDependencySpec` | (validated during routed setup) | Declare feature dependency constraints |
| Workflow/recompute | `WorkflowStepSpec`, `WorkflowSpec`, `RecomputeNodeSpec` | `WorkflowCoordinator`, `RecomputeOrchestrator` | Multi-step orchestration and deterministic recompute ordering |
| QoS/health/replay/hot-swap | `QoSPolicySpec`, `HealthProbeSpec`, `ReplaySpec`, `ReplacePolicySpec` | `QoSPolicyRuntime`, `FeatureHealthRuntime`, `RuntimeReplayHarness`, `FeatureHotSwapManager` | Budgets, degradation, diagnostics replay, controlled replacement |

These families exist to keep runtime orchestration declarative and lifecycle-safe. They allow teams to evolve control-plane behavior without scattering cross-cutting code across many feature classes.

See [Appendix F: Specifications and Option Reference](#appendix-f-specifications-and-option-reference).

[Back to Table of Contents](#table-of-contents)

## Quickstart Path (Practice)
[Back to Table of Contents](#table-of-contents)

This path is designed for fast confidence, not completeness. The shortest reliable route is to bootstrap a host from a binding spec, register one scene and one feature, then prove one reactive update and one action path end to end.

### Milestone Path

1. A: App boots and enters initial scene.
2. B: One feature adds one visible control.
3. C: One observable updates one control without manual redraw wiring.
4. D: One action/hotkey triggers behavior.
5. E: One overlay path (for example shortcut help) opens and closes correctly.
6. F: Workspace save/load roundtrip returns a restore report.

```python
from gui_do import HostApplicationBindingSpec, build_host_application_config, bootstrap_host_application


class DemoHost:
	pass


host = DemoHost()
config = build_host_application_config(
	HostApplicationBindingSpec(
		display_size=(1280, 720),
		window_title="Quickstart",
		initial_scene_name="main",
		scene_bundle_entries=(),
		feature_entries=(),
	)
)
bootstrap_host_application(host, config)
host.app.run_entrypoint(target_fps=config.target_fps)
```

### Common Early Failures

- Feature does not appear: validate `feature_specs`/scene assignment matches an existing runtime scene.
- Hotkey does nothing: validate action registration and scene scope for key binding.
- Overlay captures unexpected input: review dismiss and consume policy.
- State changes but UI does not: move subscription setup to `bind_runtime` and ensure cleanup does not run early.

[Back to Table of Contents](#table-of-contents)

## Architecture and Runtime Model
[Back to Table of Contents](#table-of-contents)

### Boundary Model: Framework vs Consumer

The boundary contract is explicit in `docs/architecture_boundary_spec.md`.

- `gui_do/` is reusable framework/runtime code and must not depend on `demo_features/`.
- `gui_do_demo.py` is consumer integration code and imports from the root `gui_do` package.
- Boundary tests enforce this shape (see `tests/test_boundary_contracts.py`).

### Tiered Public API Model

Public exports are tiered in `gui_do/__init__.py`.

- Tier 1: primary entrypoints and data-driven specs.
- Tier 2 to Tier 7: core app/runtime systems.
- Tier 8+: specialized systems (controls, layout, overlays, data, graphics, introspection, migration, and others).

Recommended rule: start at lower tier numbers first and descend only when you need finer control.

### Runtime Guarantees

- Scheduler dispatch budget clamp: fraction `0.12`, floor `0.5 ms`, ceiling `4.0 ms`.
- Workspace restore returns a report with `skipped_settings` and `missing_settings_blocks`.
- Event routing and focus behavior are contract-tested, not best-effort conventions.

### Event Pipeline Mental Model

At runtime, input is normalized to `GuiEvent`, routed through overlay/focus/scene handling, then dispatched to features/actions according to active context. Propagation control (`propagation_stopped` and `default_prevented`) is treated as a hard stop signal in the routing flow.

[Back to Table of Contents](#table-of-contents)

## Feature Organization Conventions
[Back to Table of Contents](#table-of-contents)

Use `demo_features/` as the canonical packaging model: one feature package per folder, package root as the integration surface, and package-local files separated by concern. This structure keeps growth predictable when lifecycle, runtime wiring, and presenters evolve.

Each feature folder is a Python package with `__init__.py`. In this repository, packages such as `demo_features/main`, `demo_features/showcase`, and `demo_features/systems` include package-level metadata and package-scoped organization cues, while concrete feature modules and specs stay inside the same package folder.

The main architectural value is boundary stability. Bootstrap and composition code should target package surfaces and declared specs rather than deep internal file paths. That allows internal refactors (splitting presenters, moving spec definitions, adding logic companions) without forcing cascading integration edits.

This model becomes more important as routed runtime facilities are used. Once features own service bindings, effects, operation buses, projections, and other declarative runtime systems, package-scoped boundaries prevent accidental cross-feature imports and lifecycle coupling.

```python
# Recommended package-root import style for consumers.
from demo_features.main.main_feature import MainFeature
from demo_features.showcase.showcase_feature import ShowcaseFeature

from gui_do import FeatureWindowBundleBindingSpec

bundles = (
	FeatureWindowBundleBindingSpec("_main_feature", MainFeature, "main"),
	FeatureWindowBundleBindingSpec("_showcase_feature", ShowcaseFeature, "showcase"),
)
```

[Back to Table of Contents](#table-of-contents)

## Core Workflow: Build, Bind, Route, Update, Draw
[Back to Table of Contents](#table-of-contents)

The core workflow is phase-separation as an engineering discipline.

- Build: create stable control/window structure.
- Bind: connect runtime dependencies, subscriptions, actions, and cross-feature links.
- Route: process messages and events through declared handlers.
- Update: run frame-time logic and scheduler work.
- Draw: custom render pass for visuals outside standard control rendering.

`RoutedRuntimeSpec` and `RoutedFeatureLifecycleSpec` reduce lifecycle boilerplate when you have repeating runtime binds. In many features, `bind_routed_feature_lifecycle` and `shutdown_routed_feature_lifecycle` are the safest way to keep setup/teardown symmetric.

```python
from gui_do import (
	RoutedFeature,
	bind_routed_feature_lifecycle,
	shutdown_routed_feature_lifecycle,
)


class DemoFeature(RoutedFeature):
	def bind_runtime(self, host):
		bind_routed_feature_lifecycle(self, host, self._lifecycle_spec)

	def shutdown_runtime(self, host):
		shutdown_routed_feature_lifecycle(self, host, self._lifecycle_spec)
```

When operations need retries/timeouts/failure publication, declare `FeatureOperationSpec` plus `FailurePolicySpec` and let `FeatureOperationBus` handle lifecycle and timers under the runtime scope.

[Back to Table of Contents](#table-of-contents)

## Main Systems Reference
[Back to Table of Contents](#table-of-contents)

This section is organized as operational chapters. Each chapter explains why the system exists, where it fits in lifecycle flow, and how to avoid the failure modes that usually appear after apps scale past one scene.

### General Usage of gui_do Systems

gui_do systems are intentionally modular and declarative. You can opt into only the surfaces you need. In particular, task panel, command palette, and unified menu strip are optional facilities, not mandatory framework pillars.

For lifecycle safety, register input binds and runtime subscriptions during `bind_runtime`, and dispose them in `shutdown_runtime` (or through routed runtime helpers that own cleanup in `FeatureRuntimeScope`). Avoid partial teardown where setup and cleanup code paths drift.

Task panel usage is scene-scoped through specs such as `SceneTaskPanelSpec`, `TaskPanelSlotLayoutSpec`, and `TaskPanelWindowToggleGroupSpec`. You can also wire focus visibility semantics with `TaskPanelFocusToggleSpec`.

Unified menu-strip usage is driven by `MenuStripControl`, `MenuEntry`, `SceneMenuOptions`, `WindowMenuOptions`, and high-level helpers (`add_standard_menu_strip`, `add_menu_strip_from_spec`, `add_window_menu_strip`). Scene/window sections are declarative and insertion-order configurable.

Command palette usage is scene-scoped through `SceneCommandPaletteSpec` and two `PaletteInputBindSpec` binds (`toggle` and `action`), each independently key/pointer configurable.

See [Appendix F: Specifications and Option Reference](#appendix-f-specifications-and-option-reference).

### Application Bootstrap and Host Configuration
[Back to Table of Contents](#table-of-contents)

`HostApplicationConfig` and `bootstrap_host_application` form the deterministic host startup boundary. If you prefer higher-level declarative assembly, `HostApplicationBindingSpec` and `build_host_application_config` provide structured binding-to-config conversion.

Primary APIs include `HostApplicationConfig`, `HostApplicationBindingSpec`, `build_host_application_config`, and `bootstrap_host_application`, plus Tier-1 spec families for scenes, features, actions, windows, fonts, cursors, and accessibility.

Typical usage flow:

1. Define binding specs for scenes/features/windows/actions.
2. Build config with `build_host_application_config`.
3. Bootstrap host once and run entrypoint.

```python
from gui_do import build_host_application_config, bootstrap_host_application, HostApplicationBindingSpec


class Host:
	pass


host = Host()
config = build_host_application_config(HostApplicationBindingSpec(initial_scene_name="main"))
bootstrap_host_application(host, config)
```

Common mistakes:

- Declaring feature scene names that are not present in runtime scene setup.
- Ad-hoc host mutation that bypasses config graph intent.
- Missing `initial_scene_name` when multiple scenes are configured.

### Feature Lifecycle and Feature Types
[Back to Table of Contents](#table-of-contents)

Feature lifecycle is the center of app composition. Use `Feature` for standard UI composition, `DirectFeature` for direct draw paths, `LogicFeature` for non-visual orchestration, and `RoutedFeature` when route/spec-driven runtime behavior is first-class.

Lifecycle placement:

- `build`: construct controls/windows/static structures.
- `bind_runtime`: subscribe, bind actions, wire cross-feature interactions.
- `handle_event`: consume routed events.
- `on_update`: frame-time logic.
- `draw`: custom drawing.
- `shutdown_runtime`: unwind runtime resources.

Use `bind_routed_feature_lifecycle` and `shutdown_routed_feature_lifecycle` when a feature declares `RoutedFeatureLifecycleSpec`. This is the easiest way to keep runtime setup and teardown symmetric.

Runtime scope teardown guarantees matter for service/effect/operation facilities. If `setup_routed_runtime` is used, `shutdown_routed_runtime` must run so owned subscriptions, operation registrations, and service scope resources are disposed.

```python
from gui_do import Feature


class MyFeature(Feature):
	HOST_REQUIREMENTS = {"build": ("app",), "bind_runtime": ("app",)}

	def build(self, host):
		self._built = True

	def bind_runtime(self, host):
		self._bound = True
```

Common mistakes:

- Subscribing in `build` before all runtime peers exist.
- Forgetting `shutdown_routed_feature_lifecycle` for routed features.
- Coupling features through direct control references instead of messages/observables.

### Events, Actions, Input Mapping, and Routing
[Back to Table of Contents](#table-of-contents)

Input is normalized into `GuiEvent`, then routed through overlays, focus/window/scene context, and action dispatch surfaces. Action APIs (`ActionManager`, `ActionRegistry`, `ActionDescriptor`, `InputMap`) map physical input to logical commands.

This separation lets you evolve shortcuts and command surfaces without rewriting feature event handlers.

```python
from gui_do import ActionManager


actions = ActionManager()
actions.register_action("app.exit", lambda _e: True)
actions.bind_key(27, "app.exit")
```

Advanced pattern: use `KeyChordManager` for multi-step key chords and keep command semantics centralized in the action layer.

Common mistakes:

- Handling raw pygame events directly in features when normalized routing already exists.
- Ignoring scene/window scope while binding actions.
- Treating propagation flags as advisory instead of hard routing stops.

### State and Observables
[Back to Table of Contents](#table-of-contents)

Reactive state APIs include `ObservableValue`, `ObservableList`, `ObservableDict`, `ComputedValue`, `reactive_batch`, and Tier-27 store APIs (`AppStateStore`, `StateSelector`, `StateTransaction`).

Typical usage flow:

1. Create observable/store state.
2. Subscribe in `bind_runtime`.
3. Dispose or scope-own subscriptions in teardown.

```python
from gui_do import ObservableValue


count = ObservableValue(0)
unsubscribe = count.subscribe(lambda value: print("count", value))
count.value = 1
unsubscribe()
```

Declarative routed-runtime equivalents are `StoreSubscriptionSpec`, `StoreSelectorSpec`, `ObservableEffectSpec`, and `SignalEffectSpec`.

#### Automatic Subscription Ownership and Cleanup

Automatic ownership via `FeatureRuntimeScope` is a lifecycle-safety contract. When routed runtime binds observable effects/selectors/signals, cleanup handles are collected in scope ownership and disposed together.

This prevents leaks and teardown drift:

- subscription leaks across scene transitions,
- retained feature instances after runtime shutdown,
- callbacks targeting dead controls,
- duplicate callbacks after repeated bind cycles,
- partial cleanup when one manual path is forgotten.

Fragile manual pattern:

```python
self._unsub = source.subscribe(self._on_change)
# if shutdown path misses self._unsub(), callback leak remains
```

Lifecycle-owned pattern:

```python
from gui_do import FeatureRuntimeScope

scope = FeatureRuntimeScope()
scope.subscribe(source, self._on_change)
# guaranteed symmetric cleanup
scope.dispose()
```

Automatic ownership complements explicit lifecycle discipline; it does not replace proper bind/shutdown phase design.

### Controls and Control Composition
[Back to Table of Contents](#table-of-contents)

Controls are reusable UI primitives; features are lifecycle owners. Compose control trees inside feature-owned roots and keep state in observables/store rather than inside control instances.

Primary APIs are Tier 12 and Tier 13 controls, including `PanelControl`, `LabelControl`, `ButtonControl`, `ToggleControl`, `SliderControl`, `TextInputControl`, `DataGridControl`, `TreeControl`, `WindowControl`, `TaskPanelControl`, `MenuStripControl`, and related chrome controls.

`WindowPresenter` and `TabbedPresenterSpec` support presenter-based window composition where feature lifecycle and window UI responsibilities remain separate.

```python
from pygame import Rect
from gui_do import PanelControl, LabelControl, ButtonControl


def build_ui(host):
	root = host.app.add(PanelControl("root", Rect(10, 10, 320, 220)), scene_name="main")
	root.add(LabelControl("status", Rect(10, 10, 180, 24), "Ready"))
	root.add(ButtonControl("go", Rect(10, 42, 100, 28), "Go", on_click=lambda: None))
```

Common mistakes:

- Cross-feature direct control mutation.
- Using controls as source-of-truth state.
- Creating controls in update loop instead of `build`.

See [Appendix F: Specifications and Option Reference](#appendix-f-specifications-and-option-reference).

### Layout Systems
[Back to Table of Contents](#table-of-contents)

Layout systems reduce manual pixel math and make resize behavior explicit. Core families include `FlexLayout`, `GridLayout`, `FlowLayout`, `ConstraintLayout`/`ConstraintLayoutEngine`, docking/layout handlers, and adaptive/virtualized tiers (`AdaptivePolicy`, `VirtualizationCore`).

Use one primary layout owner per region. Mixed ownership without clear boundaries is a common source of drift.

```python
from gui_do import FlexLayout, FlexDirection, FlexItem


layout = FlexLayout(direction=FlexDirection.ROW, gap=8)
layout.add(FlexItem(control=sidebar, grow=0, basis=220))
layout.add(FlexItem(control=content, grow=1))
```

Advanced pattern: combine adaptive constraints with virtualization for large dashboards that reflow by breakpoint.

Common mistakes:

- Hardcoding dimensions where adaptive policy is required.
- Calling layout against nodes not yet attached.

See [Appendix F: Specifications and Option Reference](#appendix-f-specifications-and-option-reference).

### Focus and Accessibility
[Back to Table of Contents](#table-of-contents)

Focus and accessibility keep keyboard interaction coherent and semantic output inspectable. Core APIs include `FocusManager`, `FocusScopeManager`, `FocusRing`, `WindowFocusManager`, `AccessibilityNode`, `AccessibilityTree`, `AccessibilityBus`, and `AccessibilityAnnouncement`.

Use `TaskPanelFocusToggleSpec` when visibility toggles should also update focus eligibility. This avoids focus traversal landing on hidden window controls.

```python
from gui_do import AccessibilityTree, AccessibilityNode


tree = AccessibilityTree()
tree.root.add_child(AccessibilityNode(role="button", name="Submit"))
```

Anti-pattern: registering focus/accessibility event subscriptions outside runtime ownership and forgetting teardown. Prefer routed runtime setup plus scope-owned cleanup.

See [Appendix F: Specifications and Option Reference](#appendix-f-specifications-and-option-reference).

### Overlays, Dialogs, Notifications, and Command Surfaces
[Back to Table of Contents](#table-of-contents)

Overlay managers handle transient/modal surfaces so feature event flow remains stable. This includes dialogs, toasts, context menus, notifications, tooltips, and command palette.

Command palette binding is currently two-bind and scene-scoped through `SceneCommandPaletteSpec`:

- `toggle: PaletteInputBindSpec` controls open/close.
- `action: PaletteInputBindSpec` opens palette if closed (returns immediately) and, when already open, triggers entry activation at pointer via `try_activate_action_at`.

Both toggle/action support optional key and optional pointer button independently.

Concrete demo usage currently sets toggle to `F5` and action to pointer button `2` (middle click) in both main and showcase specs.

```python
from gui_do import SceneCommandPaletteSpec, PaletteInputBindSpec


palette_spec = SceneCommandPaletteSpec(
	scene_name="main",
	toggle=PaletteInputBindSpec(action_name="command_palette_toggle", key=pygame.K_F5),
	action=PaletteInputBindSpec(action_name="command_palette_action", pointer_button=2),
)
```

Common mistakes:

- Missing dismissal policy on modal overlays.
- Assuming toast click-through behavior.
- Binding overlay actions outside lifecycle-owned runtime setup.

See [Appendix F: Specifications and Option Reference](#appendix-f-specifications-and-option-reference).

### Scene, Window, and Task-Panel Presentation Models
[Back to Table of Contents](#table-of-contents)

Scenes define interaction context; windows define focused work surfaces inside scenes; task panel, command palette, and unified menu strip are optional management surfaces that can control the same window visibility state.

Primary APIs include `ScenePresentationModel`, `WindowPresenter`, `WindowSpec`, `AnchoredWindowSpec`, `FeatureWindowBundleBindingSpec`, `WindowToggleBindingSpec`, `SceneTaskPanelSpec`, `TaskPanelSlotLayoutSpec`, `TaskPanelWindowToggleGroupSpec`, and helpers from tier 18 such as `set_window_visible_state`, `toggle_window_visibility`, `create_anchored_feature_window`, `create_feature_presented_window`, `ensure_scene_task_panel`, `add_standard_menu_strip`, and `add_menu_strip_from_spec`.

#### Unified Window-Visibility Management

The three user-facing surfaces share one visibility source of truth:

- Window section in `MenuStripControl`.
- Window entries in command palette.
- Task-panel window toggles.

Window participation is opt-in by default. Setting `window_management_opt_in=False` on window/binding specs opts a window out of all three automatic surfaces while keeping the window fully functional for manual control.

Scene participation in auto scene menu is also opt-in by default; `MenuStripSpec.scene_menu_opt_in=False` opts that scene out.

Synchronization semantics:

- Toggling in any participating surface updates shared visibility state.
- Other surfaces reflect the change (not independent copies).
- Opted-out windows are excluded from auto menu/palette/task-panel management.

Task-panel behavior details: left-click window toggle shows/raises window; right-click hides it. Slot index controls ordering and should be intentional for predictable UX.

```python
from gui_do import FeatureWindowBundleBindingSpec, MenuStripSpec


window_binding = FeatureWindowBundleBindingSpec(
	feature_attribute_name="_systems_feature",
	factory=SystemsFeature,
	key="systems",
	window_management_opt_in=False,
)

menu_spec = MenuStripSpec(
	control_id="main_menu",
	scene_name="main",
	scene_menu_opt_in=False,
)
```

Use operation specs (`FeatureOperationSpec` with `FailurePolicySpec`) when window actions require retry/timeout/error publication semantics rather than direct callback-only behavior.

Cross-links: 8.8 command surfaces, 8.7 focus lifecycle, 8.2 feature lifecycle.

See [Appendix F: Specifications and Option Reference](#appendix-f-specifications-and-option-reference).

### Scheduling, Timing, Animation, and Transitions
[Back to Table of Contents](#table-of-contents)

Timing systems coordinate per-frame work under budget constraints. APIs include `CooperativeScheduler`, `SceneTimeline`, `TweenManager`, `AnimationSequence`, `AnimationStateMachine`, `Debouncer`, and `Throttler`.

Budget contract from runtime docs: fraction `0.12` of frame dt milliseconds, floor `0.5 ms`, ceiling `4.0 ms`.

```python
handle = host.tweens.to(panel, "alpha", 255, duration=0.2)
```

Use dataflow/cancellation for preemptible background transformations and keep `on_update` lightweight.

Timeouts/retries in operation policies are timer-backed scheduled work, so they belong in the same reliability budget thinking as animations and cooperative tasks.

See [Appendix F: Specifications and Option Reference](#appendix-f-specifications-and-option-reference).

### Persistence and Workspace/Session State
[Back to Table of Contents](#table-of-contents)

Persistence APIs support save/load and schema evolution. Core types include `WorkspacePersistenceManager`, `SettingsRegistry`, `SettingDescriptor`, `CommandHistory`, `Command`, `CommandTransaction`, `UndoContextManager`, `SchemaVersion`, `VersionedSnapshot`, `MigrationStep`, `MigrationRegistry`, `SnapshotMigrator`, `make_snapshot`, and `read_version`.

Restore report contract includes `skipped_settings` and `missing_settings_blocks`; missing keys are non-fatal by contract.

```python
host.app.save_workspace("workspace.json")
report = host.app.load_workspace("workspace.json")
if report and report.skipped_settings:
	host.toasts.show("Some settings were skipped during restore")
```

Use snapshot migration whenever persisted schema changes across releases.

See [Appendix F: Specifications and Option Reference](#appendix-f-specifications-and-option-reference).

### Theme, Styling, and Visual Systems
[Back to Table of Contents](#table-of-contents)

Theme and font systems centralize visual policy. APIs include `ThemeManager`, `ColorTheme`, `DesignTokens`, `FontManager`, `ScopedTheme`, `ScopedThemeManager`, `ThemeInvalidationBus`, and font-role bindings through `FontRoleBindingSpec`.

`setup_standard_font_roles` is the fastest way to bootstrap consistent role mapping from configured fonts.

Theme invalidation should be event-driven, not polled. If custom controls cache rendered surfaces, subscribe to invalidation and rebuild cache on theme change.

```python
host.theme_manager.set_theme("default")
```

See [Appendix F: Specifications and Option Reference](#appendix-f-specifications-and-option-reference).

### Text, Input, Forms, and Validation Systems
[Back to Table of Contents](#table-of-contents)

Text/form systems combine control-level input with schema/validation orchestration. Core APIs include `TextInputControl`, `TextAreaControl`, `FormModel`, `FormSchema`, `ValidationPipeline`, `Validator` families, `AsyncFormValidator`, and schema runtime types (`FieldSchema`, `FieldGraphSchema`, `ValidationPolicy`, `SchemaFormRuntime`).

Use synchronous validation for local invariants and async validation for remote checks. Keep async validators cancellable to avoid stale-result flicker.

```python
from gui_do import RequiredValidator, PatternValidator, ValidationPipeline


email_rules = ValidationPipeline((RequiredValidator(), PatternValidator(r".+@.+\..+")))
```

See [Appendix F: Specifications and Option Reference](#appendix-f-specifications-and-option-reference).

### Data and Dataflow Helpers
[Back to Table of Contents](#table-of-contents)

Data systems cover source abstraction, transformation, cancellation, and virtualized rendering. Key APIs include `VirtualItemSource`, `FixedItemSource`, `SortFilterProxySource`, `AsyncDataProvider`, `DataflowPipeline`, `CancellationToken`, `VirtualizationCore`, `RecyclePool`, `DataCache`, and `ListDiffCalculator`.

Use `DataflowPipeline` for multi-stage, cancellable transformations. Prefer incremental diff updates over full redraw/rebuild when lists are large.

```python
from gui_do import FixedItemSource, SortFilterProxySource


source = FixedItemSource(items)
proxy = SortFilterProxySource(source)
proxy.set_filter(lambda item: item.active)
proxy.set_sort_key(lambda item: item.name)
```

When task semantics matter (timeouts/retries/published failures), route heavy actions through `FeatureOperationBus` instead of ad-hoc callbacks.

See [Appendix F: Specifications and Option Reference](#appendix-f-specifications-and-option-reference).

### Graphics and Audio Integration Points
[Back to Table of Contents](#table-of-contents)

Graphics/audio integrations include `DirtyRegionTracker`, `SurfaceCompositor`, `DrawContext`, `ShapeRenderer`, `SpriteSheet`, `ParticleSystem`, `SceneGraph2D`, `Camera2D`, `RenderTarget` helpers, and audio APIs `SoundCue`, `SoundBankRegistry`, `SoundEventBus`.

Use dirty-region and offscreen-target strategies when draw complexity grows. Trigger audio cues from semantic actions/events rather than raw pointer noise.

```python
host.sound_bus.publish(SoundCue("notify"))
```

See [Appendix F: Specifications and Option Reference](#appendix-f-specifications-and-option-reference).

### Telemetry, Introspection, and Operational Hooks
[Back to Table of Contents](#table-of-contents)

Operational visibility comes from telemetry and runtime inspection APIs: `TelemetryConfig`, `configure_telemetry`, `telemetry_collector`, `analyze_telemetry_records`, `render_telemetry_report`, `SceneSpatialIndex`, `ui_property`, `PropertyRegistry`, and `PropertyInspectorModel`.

Collect measurements during representative scenarios, not idle loops. Correlate telemetry output with spatial/property inspection to localize regressions quickly.

```python
from gui_do import configure_telemetry, telemetry_collector, analyze_telemetry_records


configure_telemetry(enabled=True)
report = analyze_telemetry_records(telemetry_collector.records)
```

See [Appendix F: Specifications and Option Reference](#appendix-f-specifications-and-option-reference).

## Integration Patterns and Composition Recipes
[Back to Table of Contents](#table-of-contents)

### Recipe 1: Routed Feature + Actions + Shortcut Overlay

Goal: keep hotkey registration and shortcut discoverability declarative.

Pattern: define action/hotkey specs and `ShortcutOverlaySpec` in `RoutedRuntimeSpec`, then bind/unbind with routed lifecycle helpers.

Validation: verify overlay toggles with declared key and reflects current action registry groups.

### Recipe 2: Window Presenter + Task Panel + Focus Toggle

Goal: maintain clean window UI composition with predictable focus and visibility behavior.

Pattern: presenter-based windows + task-panel toggle group + `TaskPanelFocusToggleSpec`.

Validation: hidden windows leave focus traversal; toggles remain synchronized.

### Recipe 3: Store + Persistence + Migration

Goal: preserve state continuity across schema changes.

Pattern: use store selectors for runtime state, persist snapshots with schema versions, migrate via `SnapshotMigrator` before restore.

Validation: restore report inspected and migration tests cover old versions.

### Recipe 4: Dataflow + Telemetry + Error Boundary

Goal: resilient and measurable heavy-data UI behavior.

Pattern: cancellable pipeline, telemetry instrumentation, and `ErrorBoundary` around high-risk rendered subtree.

Validation: stale generations cancel and telemetry identifies slowest stages.

## End-to-End Reference Application
[Back to Table of Contents](#table-of-contents)

```python
import pygame

from gui_do import (
	ActionHotkeySpec,
	Feature,
	FeatureSpec,
	HostApplicationConfig,
	LabelControl,
	ObservableValue,
	PaletteInputBindSpec,
	RoutedFeatureLifecycleSpec,
	RoutedRuntimeSpec,
	RuntimeSceneSpec,
	SceneCommandPaletteSpec,
	SceneSetupSpec,
	ShortcutOverlaySpec,
	TelemetryConfig,
	bind_routed_feature_lifecycle,
	bootstrap_host_application,
	shutdown_routed_feature_lifecycle,
)


class CounterFeature(Feature):
	scene_name = "main"

	def __init__(self):
		self.count = ObservableValue(0)
		self._sub = None
		self._runtime_spec = RoutedRuntimeSpec(
			scene_name="main",
			shortcut_overlays=(
				ShortcutOverlaySpec(
					attr_name="_help_overlay",
					action_registry_attr="action_registry",
					toggle_action_name="show_help",
					toggle_key=pygame.K_F9,
					toggle_scene_name="main",
					toggle_global_key=True,
				),
			),
			command_palette=SceneCommandPaletteSpec(
				scene_name="main",
				toggle=PaletteInputBindSpec(action_name="command_palette_toggle", key=pygame.K_F5),
				action=PaletteInputBindSpec(action_name="command_palette_action", pointer_button=2),
			),
			action_hotkeys=(
				ActionHotkeySpec(action_name="inc", handler=lambda _e: self._inc(), key=pygame.K_F2, scene_name="main", global_key=True),
			),
		)
		self._lifecycle_spec = RoutedFeatureLifecycleSpec(runtime_spec=self._runtime_spec)

	def _inc(self):
		self.count.value += 1
		return True

	def build(self, host):
		self.label = host.app.add(LabelControl("count_label", pygame.Rect(20, 20, 220, 28), "Count: 0"), scene_name="main")

	def bind_runtime(self, host):
		self._sub = self.count.subscribe(lambda v: setattr(self.label, "text", f"Count: {v}"))
		bind_routed_feature_lifecycle(self, host, self._lifecycle_spec)

	def shutdown_runtime(self, host):
		if callable(self._sub):
			self._sub()
			self._sub = None
		shutdown_routed_feature_lifecycle(self, host, self._lifecycle_spec)


class DemoHost:
	pass


host = DemoHost()
config = HostApplicationConfig(
	scene_specs=(SceneSetupSpec("main"),),
	feature_specs=(FeatureSpec(attr_name="counter_feature", factory=CounterFeature),),
	runtime_scene_specs=(RuntimeSceneSpec(scene_name="main", bind_escape_to_exit=True),),
	telemetry=TelemetryConfig(enabled=True),
	target_fps=60,
)
bootstrap_host_application(host, config)
host.app.run_entrypoint(target_fps=config.target_fps)
```

### What This Listing Demonstrates

This listing demonstrates bootstrap configuration, scene/feature registration, routed runtime lifecycle wiring, observable-driven UI updates, command palette two-bind behavior, shortcut overlay toggling, and telemetry-enabled startup.

### Validation Checklist

1. App opens into `main`.
2. Press `F2` and confirm label increments.
3. Press `F5` to toggle command palette.
4. Press `F9` to toggle shortcut help overlay.
5. Confirm clean shutdown with no repeated callbacks on relaunch.

## Testing, Diagnostics, and Reliability
[Back to Table of Contents](#table-of-contents)

Contract and runtime tests are a first-class part of gui_do documentation maintenance because the framework is explicitly contract-driven.

### Contract Tests

Run the high-priority contract suite:

```bash
python -m pytest -q tests/test_public_api_exports.py tests/test_public_api_docs_contracts.py tests/test_runtime_operating_contracts.py tests/test_boundary_contracts.py tests/test_gui_application_workspace_contracts.py
```

Coverage intent:

- `test_public_api_exports.py`: public export importability and root-surface consistency.
- `test_public_api_docs_contracts.py`: docs/API contract coherence.
- `test_runtime_operating_contracts.py`: scheduler/event/workspace guarantees.
- `test_boundary_contracts.py`: framework-consumer import boundary.
- `test_gui_application_workspace_contracts.py`: workspace save/load behavior and report semantics.

### Runtime Behavior Tests

Prioritize overlay routing, command palette behavior, task-panel/window visibility synchronization, restore-report handling, and routed runtime setup/teardown correctness.

Runtime-facility coverage should include:

- service publication and consumption lifecycle,
- effect subscription ownership and cleanup,
- operation failure-policy behavior (retry/timeout/publication),
- routed teardown guarantees (`shutdown_routed_runtime`).

### Debug and Trace Tools

- `EventRecorder`/`EventPlayback` for reproducible input traces.
- `DebugOverlay` for visual state checks.
- `PropertyInspectorPanel` for runtime property inspection.
- Telemetry analyzers (`analyze_telemetry_log_file`, `render_telemetry_report`).

### Maintainer Release Runbook

1. Run contract tests and key runtime tests.
2. Diff tier exports in `gui_do/__init__.py`.
3. Reconcile manual chapters and spec appendix for changed APIs.
4. Validate demo usage still matches documented patterns.
5. Confirm workspace restore and scheduler budget statements still align with contracts.

### Regression Triage Workflow

1. Reproduce with deterministic input where possible.
2. Capture trace/events.
3. Localize failing layer (routing, lifecycle, state, layout, overlay).
4. Add/adjust test first.
5. Patch and rerun adjacent contract tests.

### Maintainer Diff Checklist

Inventory delta checks:

1. Compare root exports in `gui_do/__init__.py` with Appendix D and D.1.
2. Check `docs/` contracts for changed guarantees and policies.
3. Scan `tests/` for new contract/runtime modules affecting documentation.
4. Scan `demo_features/` for newly recommended composition patterns.

Content integrity checks:

1. Update both chapter prose and appendix index for each changed system.
2. Remove obsolete APIs from examples and references.
3. Place newly added APIs at the right abstraction level (Tier 1 first).

Navigation and structure checks:

1. Confirm new/changed sections are present in TOC.
2. Keep back-to-TOC links on major sections.
3. Preserve top-level chapter ordering unless intentionally restructured.

Operational checks:

1. Re-run high-priority contract suite.
2. Validate end-to-end listing assumptions against current runtime behavior.
3. Capture unresolved ambiguities in migration/deprecation notes.

## Performance and Scaling Guidance
[Back to Table of Contents](#table-of-contents)

### Scheduler Budget Contract

Current contract values are:

- fraction: `0.12` of frame dt milliseconds,
- floor: `0.5 ms`,
- ceiling: `4.0 ms`.

These prevent starvation on fast frames and runaway dispatch under slow frames.

### Dirty-Region Rendering

Use `DirtyRegionTracker` to avoid full-surface redraw in complex scenes. Incremental union caching allows fast overlap checks and bounded repaint sets.

### Virtualization and Incremental Updates

- Use `VirtualizationCore`/`VirtualizedWindow` for very large item sets.
- Use `ListDiffCalculator` for patch-style updates.
- Use `RecyclePool` and `ObjectPool` for high-churn object reuse.

### Practical Scaling Checklist

1. Keep updates scene-scoped.
2. Avoid per-frame large allocation bursts.
3. Debounce expensive text/search handlers.
4. Use cancellable dataflow for preemptible background work.
5. Profile representative workflows.
6. Gate redraw with dirty-region logic.

## Migration, Versioning, and Deprecation Notes
[Back to Table of Contents](#table-of-contents)

### Versioned Snapshot Strategy

Use the migration layer for any persisted schema evolution.

1. Save snapshots with `make_snapshot` using current `SchemaVersion`.
2. On load, inspect with `read_version`.
3. Run `SnapshotMigrator.migrate` with registered `MigrationStep` edges.
4. Restore only after migration resolves to current version.

### Deprecation Handling

Prefer additive transitions and explicit migration paths before removals. Keep deprecation notes centralized here to avoid fragmented guidance.

No formal deprecated public API catalog is maintained in this generation; add entries here when deprecations are introduced.

### Upgrade Checklist

1. Run contract tests pre/post upgrade.
2. Verify root-surface imports (`from gui_do import ...`) for consumer code.
3. Validate input/focus/routing in active scenes.
4. Validate workspace restore report handling for skipped/missing settings.
5. Compare telemetry baselines for major interaction flows.

## FAQ and Troubleshooting
[Back to Table of Contents](#table-of-contents)

### Should I build apps directly with controls or with features?

Use features as the architectural unit. Controls are implementation details inside feature lifecycle ownership.

### When should I use RoutedFeature over Feature?

Use `RoutedFeature` when declarative routed runtime facilities are central to behavior (actions/effects/operations/command surfaces). Use plain `Feature` for simpler lifecycle + control composition.

### Why are key handlers not firing?

Check focus ownership, scene scope, overlay capture, and action registration scope. Event tracing with `EventRecorder` helps isolate the first drop point.

### Why do toast clicks not pass through?

Toast interaction is intentionally consumed inside toast bounds by default to avoid accidental underlying clicks.

### How do I avoid breaking workspace restore across versions?

Always version snapshots and maintain migration steps. Treat restore report fields as operational signals, not optional diagnostics.

### How do I verify supported API usage?

Prefer root imports from `gui_do` and run public export contract tests.

### Why does bind ordering feel wrong between sibling features?

All scene features build first, then bind. If ordering appears wrong, verify scene assignments and feature registration assumptions.

### How do I add shortcuts without scattering handler code?

Declare action and hotkey specs (or routed runtime action binds) and keep command logic centralized.

## Appendix
[Back to Table of Contents](#table-of-contents)

Appendices provide glossary, lifecycle sequencing, dependency mapping, API indexing, tier mapping, architecture templates, and specification options.

### Appendix A: Glossary
[Back to Table of Contents](#table-of-contents)

Feature: lifecycle-managed behavior unit (`Feature`, `DirectFeature`, `LogicFeature`, `RoutedFeature`) that owns setup, runtime wiring, and teardown.

Spec: declarative configuration object that describes runtime wiring and options.

Host: plain Python object populated by bootstrap with app/runtime members.

Scene: top-level interaction context; features and window surfaces operate within scene scope.

Routed runtime: declarative runtime binding surface (`RoutedRuntimeSpec`) for actions, effects, operations, and advanced runtime faculties.

Observable: value/collection with subscription-based change notification.

Workspace state: persisted runtime state used for save/load continuity.

Runtime scope: lifecycle-owned container (`FeatureRuntimeScope`) for cleanup and scoped services.

Failure policy: declarative retry/timeout/publication policy for feature operations.

### Appendix B: Lifecycle and Event Sequence
[Back to Table of Contents](#table-of-contents)

1. Bootstrap initializes host from config/bindings.
2. Scene features run `build`.
3. Scene features run `bind_runtime`.
4. Frame loop starts.
5. Input normalizes into `GuiEvent`.
6. Overlay/focus/window/scene routing executes.
7. Feature event handlers run.
8. `on_update` runs; scheduler/operations advance.
9. Draw phase executes and presents frame.
10. Scene transition tears down departing runtime and binds arriving runtime.
11. App exit tears down runtime and may persist workspace state.

### Appendix C: System Dependency Map
[Back to Table of Contents](#table-of-contents)

Bootstrap and lifecycle systems anchor all other subsystems. Event/action routing depends on scene/focus context. Controls depend on layout/theme/input/state. Overlays depend on routing and focus capture rules. Persistence depends on state models and scene/window registration. Telemetry/introspection cross-cut all layers.

### Appendix D: API Quick Index
[Back to Table of Contents](#table-of-contents)

Bootstrap and composition: `HostApplicationConfig`, `HostApplicationBindingSpec`, `build_host_application_config`, `bootstrap_host_application`, `SceneBundleBindingSpec`, `FeatureWindowBundleBindingSpec`.

Feature lifecycle/routed runtime: `Feature`, `RoutedFeature`, `RoutedRuntimeSpec`, `RoutedFeatureLifecycleSpec`, `bind_routed_feature_lifecycle`, `shutdown_routed_feature_lifecycle`, `FeatureRuntimeScope`, `FeatureOperationBus`.

Events/actions/input: `GuiEvent`, `EventType`, `ActionManager`, `ActionRegistry`, `InputMap`, `KeyChordManager`.

State/reactivity: `ObservableValue`, `ObservableList`, `ObservableDict`, `ComputedValue`, `reactive_batch`, `AppStateStore`, `StateSelector`, `StateTransaction`.

Controls/chrome: `PanelControl`, `ButtonControl`, `LabelControl`, `MenuStripControl`, `TaskPanelControl`, `WindowControl`, `ErrorBoundary`.

Menu-strip surfaces: `MenuEntry`, `SceneMenuOptions`, `WindowMenuOptions`, `MenuStripSpec`, `add_standard_menu_strip`, `add_menu_strip_from_spec`, `add_window_menu_strip`.

Command palette surfaces: `SceneCommandPaletteSpec`, `PaletteInputBindSpec`, `setup_scene_command_palette_bindings`.

Layout and virtualization: `FlexLayout`, `GridLayout`, `ConstraintLayout`, `AdaptivePolicy`, `VirtualizationCore`.

Forms/validation: `FormSchema`, `ValidationPipeline`, `AsyncFormValidator`, `SchemaFormRuntime`.

Dataflow: `DataflowPipeline`, `PipelineStage`, `CancellationToken`.

Graphics/audio/telemetry: `DirtyRegionTracker`, `SceneGraph2D`, `SoundEventBus`, `TelemetryConfig`.

### Appendix D.1: Tier Matrix
[Back to Table of Contents](#table-of-contents)

| Tier | System | Representative types |
| --- | --- | --- |
| 1 | Primary entry points and data-driven APIs | `HostApplicationConfig`, `HostApplicationBindingSpec`, `RoutedRuntimeSpec` |
| 2 | Core application and scene management | `GuiApplication`, `SceneManager`, `SceneTransitionStyle` |
| 3 | Essential data and state | `ObservableValue`, `ObservableList`, `ObservableDict` |
| 4 | Events, actions, focus, input | `GuiEvent`, `ActionManager`, `FocusManager` |
| 5 | Scheduling and animation | `CooperativeScheduler`, `TweenManager`, `SceneTimeline` |
| 6 | Theme and font management | `ThemeManager`, `ColorTheme`, `FontManager` |
| 7 | Telemetry and diagnostics | `TelemetryCollector`, `TelemetryConfig`, `render_telemetry_report` |
| 8 | Layout and spatial | `FlexLayout`, `GridLayout`, `ConstraintLayout` |
| 9 | Overlay managers and windows | `DialogManager`, `ToastManager`, `CommandPaletteManager` |
| 10 | Forms and data binding | `FormModel`, `FormSchema`, `ValidationPipeline` |
| 11 | State and persistence | `WorkspacePersistenceManager`, `SettingsRegistry`, `CommandHistory` |
| 12 | Primary controls | `PanelControl`, `ButtonControl`, `LabelControl` |
| 13 | Extended controls | `TextInputControl`, `DataGridControl`, `WindowControl` |
| 14 | Text and localization | `TextMeasurer`, `StringTable`, `LocaleRegistry` |
| 15 | Data and collections | `SortFilterProxySource`, `AsyncDataProvider`, `DataCache` |
| 16 | Graphics and rendering | `DirtyRegionTracker`, `SurfaceCompositor`, `SceneGraph2D` |
| 17 | Introspection and inspection | `SceneSpatialIndex`, `PropertyRegistry`, `PropertyInspectorModel` |
| 18 | Advanced runtime and bootstrap helpers | `FeatureRuntimeScope`, `bind_routed_feature_lifecycle`, `add_menu_strip_from_spec` |
| 19 | Infrastructure and internals | `UiEngine` |
| 20 | Audio | `SoundCue`, `SoundBankRegistry`, `SoundEventBus` |
| 21 | Accessibility | `AccessibilityNode`, `AccessibilityTree`, `AccessibilityBus` |
| 22 | Theme invalidation | `ThemeInvalidationBus` |
| 23 | Undo context routing | `UndoContextManager` |
| 24 | Async form validation | `AsyncFormValidator`, `AsyncFieldValidator` |
| 25 | Scoped service graph | `ServiceScope`, `ServiceKey`, `ScopeStack` |
| 26 | Cancelable dataflow pipeline | `DataflowPipeline`, `PipelineStage`, `PipelineHandle` |
| 27 | Transactional app state store | `AppStateStore`, `StateSelector`, `StateTransaction` |
| 28 | Adaptive constraint layout v2 | `ConstraintAttr`, `ConstraintSet`, `AdaptivePolicy` |
| 29 | Unified virtualization core | `VirtualizedWindow`, `RecyclePool`, `VirtualizationCore` |
| 30 | Interaction state machine framework | `InteractionPhase`, `InteractionTransition`, `InteractionStateMachine` |
| 31 | Schema-driven form runtime | `FieldGraphSchema`, `ValidationPolicy`, `SchemaFormRuntime` |
| 32 | Portable snapshot and migration | `SchemaVersion`, `VersionedSnapshot`, `SnapshotMigrator` |

### Appendix D.2: Selection Heuristics
[Back to Table of Contents](#table-of-contents)

1. Start at Tier 1 and only descend as needed.
2. Prefer declarative specs over ad-hoc imperative glue.
3. Use Tier 18 helpers for lifecycle-safe extended wiring.
4. Prefer root imports from `gui_do` in consumer code.
5. Avoid Tier 19 internals in application code.

### Appendix E: Architecture Templates
[Back to Table of Contents](#table-of-contents)

Template 1: small single-scene app with a few `Feature` instances and observable state.

Template 2: multi-window workbench using `FeatureWindowBundleBindingSpec`, menu strip, task panel, and command palette.

Template 3: data-heavy analysis app using `DataflowPipeline`, virtualization, and telemetry.

Template 4: long-running workflow app with scheduler coroutines, operation policies, and snapshot migration.

### Appendix F: Specifications and Option Reference
[Back to Table of Contents](#table-of-contents)

This appendix lists key spec families and option semantics. For narrative behavior and lifecycle placement, cross-reference chapters 4 through 8.16.

#### Bootstrap and Composition Specs

| Spec name | Field/option | Purpose | Default/notable behavior | Cross-reference |
| --- | --- | --- | --- | --- |
| `HostApplicationBindingSpec` | `display_size`, `window_title`, `initial_scene_name` | Host bootstrap core identity | Required for practical bootstraps | 8.1 |
| `HostApplicationBindingSpec` | `scene_bundle_entries`, `feature_entries`, `feature_window_bundle_entries` | Declarative scene/feature/window composition | Empty tuples are valid no-op | 8.1, 8.2, 8.9 |
| `HostApplicationBindingSpec` | `action_entries`, `font_role_entries`, `cursor_entries`, `palette_spec` | Optional runtime integration surfaces | Optional, additive | 8.3, 8.8, 8.12 |
| `SceneBundleBindingSpec` | `scene_name`, `pretty_name`, `transition_style` | Scene declaration bundle | Can emit nav/root specs | 6, 8.1, 8.9 |
| `FeatureWindowBundleBindingSpec` | `feature_attribute_name`, `factory`, `key` | Feature + window bundle unit | Window management opt-in defaults true | 8.9 |

#### Action/Input/Palette Specs

| Spec name | Field/option | Purpose | Default/notable behavior | Cross-reference |
| --- | --- | --- | --- | --- |
| `ActionSpec` | `action_name`, `handler`, scope options | Register named action | Scope-sensitive routing | 8.3 |
| `ActionHotkeySpec` | `action_name`, `key`, `scene_name`, `global_key` | Bind key to action | Key optional if action only | 8.3 |
| `ControlKeyBindingSpec` | `key`, `control_attr`, `scene_name` | Control activation via key | Auto action name if omitted | 8.3, 8.5 |
| `PaletteInputBindSpec` | `action_name`, `key`, `pointer_button` | One command palette bind | Key and pointer can be combined | 8.8 |
| `SceneCommandPaletteSpec` | `scene_name`, `toggle`, `action` | Two-bind palette model | `toggle` and `action` independent | 8.8, 8.9 |

#### Menu Strip and Window-Visibility Specs

| Spec name | Field/option | Purpose | Default/notable behavior | Cross-reference |
| --- | --- | --- | --- | --- |
| `MenuStripSpec` | `control_id`, `scene_name` | Attach unified menu strip | Scene-scoped | 8.9 |
| `MenuStripSpec` | `scenes_shown`, `windows_shown` | Enable dynamic scene/window sections | Both default true in spec | 8.9 |
| `MenuStripSpec` | `scene_menu_label`, `window_menu_label` | Section labels | Defaults `Scene`/`Window` | 8.9 |
| `MenuStripSpec` | `scene_menu_insert_index`, `window_menu_insert_index` | Dynamic insertion positions | Defaults `0`/`1` | 8.9 |
| `MenuStripSpec` | `scene_menu_mode`, `scene_menu_opt_in_scene_names` | Scene discovery mode | `add_all` or `opt_in` | 8.9 |
| `MenuStripSpec` | `scene_menu_include_current_scene` | Include active scene as target | Default false | 8.9 |
| `MenuStripSpec` | `scene_menu_opt_in` | Scene participation opt-in | Default true; false opts scene out | 8.9 |
| `WindowSpec`/`AnchoredWindowSpec`/`FeatureWindowBundleBindingSpec` | `window_management_opt_in` | Window participation in auto surfaces | Default true; false opts out of menu/palette/task panel | 8.9 |

#### Routed Runtime and Lifecycle Specs

| Spec name | Field/option | Purpose | Default/notable behavior | Cross-reference |
| --- | --- | --- | --- | --- |
| `RoutedRuntimeSpec` | `scene_name`, `action_hotkeys`, `event_subscriptions` | Core routed runtime declaration | Additive optional collections | 8.2, 8.3 |
| `RoutedRuntimeSpec` | `store_subscriptions`, `store_selectors`, `observable_effects`, `signal_effects` | Declarative reactive wiring | Owned by runtime scope cleanup | 8.4 |
| `RoutedRuntimeSpec` | `failure_policies`, `operations` | Operation orchestration | Backed by `FeatureOperationBus` | 8.10, 8.14 |
| `RoutedRuntimeSpec` | `command_palette`, `shortcut_overlays`, `task_panel_focus_toggles` | Command/help/focus surfaces | Scene-scoped by spec | 8.8, 8.9 |
| `RoutedFeatureLifecycleSpec` | `runtime_spec` or `runtime_spec_factory` | Lifecycle entry for routed runtime | One of fields required | 7, 8.2 |

#### Advanced Runtime Faculties Specs

| Spec name | Field/option | Purpose | Default/notable behavior | Cross-reference |
| --- | --- | --- | --- | --- |
| `RuntimePolicySpec` | policy fields | Admission/policy gating | Materialized by `RuntimePolicyEngine` | 4 |
| `EffectBindingSpec` | effect binding fields | Declarative effect ownership | Managed by `EffectLifetimeOrchestrator` | 4 |
| `EventPipelineStageSpec`, `EventPipelineSpec` | stage graph fields | Routed event stream composition | Materialized by `EventPipelineRuntime` | 4 |
| `DurableOperationBindingSpec`, `DurableOperationQueueSpec` | durable op queue config | Recovery-aware operation queues | Runtime record type `DurableQueueRecord` | 4 |
| `CapabilityProviderSpec`, `CapabilityRequirementSpec` | capability contract fields | Capability negotiation/validation | Managed by `CapabilityContractRuntime` | 4 |
| `ProjectionNodeSpec`, `ProjectionSpec` | projection graph fields | Incremental projections | Managed by `ProjectionRuntime` | 4 |
| `FeatureDependencySpec` | dependency declaration fields | Startup/runtime dependency validation | Checked in routed setup | 4 |
| `WorkflowStepSpec`, `WorkflowSpec` | workflow sequencing | Declarative multi-step orchestration | `WorkflowCoordinator` runtime | 4 |
| `RecomputeNodeSpec` | recompute node config | Deterministic recompute ordering | `RecomputeOrchestrator` runtime | 4 |
| `QoSPolicySpec` | QoS budget config | Backpressure and runtime QoS | `QoSPolicyRuntime` runtime | 4, 12 |
| `HealthProbeSpec` | probe declarations | Health/degradation monitoring | `FeatureHealthRuntime` runtime | 4, 11 |
| `ReplaySpec` | replay capture config | Runtime capture/replay | `RuntimeReplayHarness` runtime | 4, 11 |
| `ReplacePolicySpec` | replacement policy | Controlled feature replacement | `FeatureHotSwapManager` integration | 4 |

#### Persistence and Migration Specs

| Spec name | Field/option | Purpose | Default/notable behavior | Cross-reference |
| --- | --- | --- | --- | --- |
| `SettingDescriptor` | key/type/default/validator metadata | Typed settings registry entry | Missing keys are skippable during restore | 8.11 |
| `MigrationStep` | source/target/transform | One directed schema migration edge | Used by `SnapshotMigrator` BFS pathing | 13, 8.11 |
| `TelemetryConfig` | enabled and telemetry options | Runtime telemetry bootstrap behavior | Can be disabled by default | 8.16 |

All spec-heavy chapters should point here when introducing options.
