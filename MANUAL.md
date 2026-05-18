# gui_do Manual: Theory, Practice, and Systems Reference

## Title and Purpose

gui_do is a data-driven GUI framework where application structure is declared through specs and wiring descriptors, while feature behavior remains imperative and testable. This manual is the single-file reference for building, operating, and maintaining gui_do applications from first bootstrap through advanced runtime composition.

[Back to Table of Contents](#table-of-contents)

## Table of Contents

- [Title and Purpose](#title-and-purpose)
- [Table of Contents](#table-of-contents)
- [How to Use This Manual](#how-to-use-this-manual)
- [Conceptual Foundations (Theory)](#conceptual-foundations-theory)
- [Quickstart Path (Practice)](#quickstart-path-practice)
- [Architecture and Runtime Model](#architecture-and-runtime-model)
- [Feature Organization Conventions](#feature-organization-conventions)
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

This manual is written in three modes that you can move between based on the task in front of you:

- Learn mode: start with theory, then architecture, then system chapters in order.
- Build mode: start with quickstart, then core workflow, then the relevant system chapter.
- Maintain mode: start with testing/reliability, migration notes, and appendices D through F.

### Reading Paths

- Beginner path: Conceptual Foundations -> Quickstart -> Core Workflow -> 8.1/8.2/8.3/8.4 -> FAQ.
- Intermediate path: Architecture -> Feature Organization Conventions -> main systems by active subsystem.
- Maintainer path: Runtime contracts, testing chapter, performance, migration, and appendices D/D.1/F.

### Tri-Lens Markers

Use these lenses while reading:

- Control-plane lens: declarative specs that describe intent and ownership.
- Runtime-plane lens: concrete managers created from those specs during `bind_runtime` and frame updates.
- Lifecycle lens: where setup occurs, where updates run, and where cleanup must happen.

### Contract Alignment

Normative guarantees are defined in repository contracts and tests, especially `docs/public_api_spec.md`, `docs/runtime_operating_contracts.md`, and contract tests under `tests/`. When this manual describes runtime behavior, these contracts are the source of truth.

### Known Non-Goals

- Exact parity with native OS widget toolkits.
- Replacement of application-domain architecture decisions.
- Beginner-first exposure of internal infrastructure APIs.
- Treating star-import behavior as a compatibility guarantee.

[Back to Table of Contents](#table-of-contents)

## Conceptual Foundations (Theory)

gui_do is built around a deliberate split between declarative structure and imperative behavior. You describe what exists and how systems should be wired using specs, and the framework realizes that description into runtime objects during lifecycle setup. You then implement feature behavior inside lifecycle methods. This split is not cosmetic. It is the reason the framework can validate dependencies early, compose optional systems safely, and tear down runtime resources without leaking subscriptions or stale handlers.

See [Appendix F: Specifications and Option Reference](#appendix-f-specifications-and-option-reference).

### Data-Driven Design

Data-driven design in gui_do means the application graph is expressed as data first. `HostApplicationBindingSpec`, `HostApplicationConfig`, `FeatureSpec`, `SceneBundleBindingSpec`, `ActionSpec`, `WindowSpec`, `RuntimeSceneSpec`, and related specs capture the shape of your program without executing it yet. The bootstrap path then turns that specification graph into a live runtime.

The key pipeline is `build_host_application_config(...)` followed by `bootstrap_host_application(host, config)`. The builder phase normalizes and assembles declarative entries. The bootstrap phase creates display and app objects, registers cursors/fonts/actions, instantiates features, wires scene/window presentation, binds runtime, and switches to the initial scene. This staged model keeps description and execution separate, which makes failures easier to localize and makes configuration testable independently from live frame loops.

Compared with imperative wiring, this substantially reduces incidental coupling. In imperative GUI code, adding one shortcut can require touching event loops, action callbacks, and cleanup code in multiple places. In gui_do, adding a shortcut is usually one `ActionSpec` plus optional `ActionHotkeySpec` or routed runtime declarations. The registry and map wiring is applied by runtime helpers (`declare_host_actions`, `register_action_hotkeys`, and routed lifecycle helpers), then unwound during teardown.

This model also decouples bootstrap from internal file layout. Moving implementation from one module to another does not force bootstrap rewrites when public names stay stable at package boundaries. The design documents call out this separation explicitly, and demo package layout docs reinforce package-local encapsulation with stable integration surfaces.

Data-driven structure gives straightforward test seams. You can build configs without opening a window, inspect generated spec bundles, assert scene/action/window composition, and run contract tests against root exports and runtime guarantees. The framework's contract tests in `tests/test_runtime_operating_contracts.py`, `tests/test_public_api_docs_contracts.py`, and `tests/test_boundary_contracts.py` are built around this determinism.

Specs also serve as a durable compatibility boundary. A named dataclass field can be added as an optional capability with defaults, while callers remain source-compatible. In contrast, ad hoc positional APIs tend to become brittle as systems grow. This is why gui_do uses a large spec vocabulary instead of a small set of overloaded calls.

The boundary of this pattern is explicit: app composition and cross-system wiring are declarative; feature behavior in `build`, `bind_runtime`, `handle_event`, `on_update`, `draw`, and `shutdown_runtime` remains imperative Python. You describe structure declaratively and implement behavior imperatively.

[Back to Table of Contents](#table-of-contents)

### Reactive Data and Observable State

Reactive state in gui_do is built on observable primitives. Instead of manually pushing updates into every control, producers update observables and consumers subscribe once. The producer does not need to know which controls or sibling features are listening.

The core primitives are `ObservableValue`, `ObservableList`, and `ObservableDict`. `ObservableValue` tracks one value and notifies subscribers on mutation. Collection observables notify with `CollectionChange` metadata keyed by `ChangeKind`. This gives consumers richer information than raw polling and supports incremental updates.

`ComputedValue` provides derived state as a first-class observable. It is ideal when a value should always mirror one or more sources. It avoids repetitive manual subscribe/recompute plumbing and keeps derivation intent explicit. For multi-step mutation bursts, `reactive_batch` and `is_batching` let you coalesce change notifications and avoid transient intermediate redraw churn.

Lifecycle placement is critical. Subscribe in `bind_runtime` once controls and sibling features exist. Dispose in `shutdown_runtime` (or routed lifecycle shutdown) to avoid leaks and phantom callbacks on dead controls. This discipline is central to memory safety in long-running scenes.

Control binding follows the same principle: features mutate state, controls react. A control should mirror an observable source, not become the source of truth itself. This makes control swaps and presenter refactors low-risk.

Cross-feature communication can use observables or messages. Observables are best for continuously changing state. `FeatureMessage` is often better for discrete events. Both avoid tight direct references and preserve replaceability.

Anti-patterns remain consistent across systems: polling observables every frame, creating subscriptions in `build`, forgetting disposal, and sharing mutable plain containers where observables are expected. These patterns either waste frame budget or break update propagation guarantees.

[Back to Table of Contents](#table-of-contents)

### Feature Composition and Lifecycles

`Feature` is the primary behavior unit in gui_do. Feature classes are lifecycle-managed, scene-scoped components that own UI creation, runtime wiring, and teardown. The framework orchestrates phase ordering so sibling features can reliably integrate.

The type variants exist for clear use-cases. `DirectFeature` is minimal and draw-oriented for surface-level effects. `Feature` is the standard interactive UI unit in the control tree. `LogicFeature` separates non-visual logic and state publication. `RoutedFeature` extends feature behavior with routing-oriented lifecycle helpers and declarative runtime facilities.

The lifecycle order is foundational: `build` first, `bind_runtime` after all scene features are built, then frame phases (`handle_event`, `on_update`, `draw`), and teardown in `shutdown_runtime`. This ordering enables safe cross-feature references during bind and deterministic cleanup at shutdown.

`HOST_REQUIREMENTS` acts as declarative dependency metadata for lifecycle methods. Features can declare required host attributes and rely on framework validation to fail early when wiring is incomplete.

Feature coordination is intentionally decoupled. `FeatureMessage` allows topic-style signaling without direct object ownership. Observables provide shared live state channels. Routed facilities add another layer: declarative registration of runtime subscriptions, service scopes, operation handlers, and higher-level orchestration runtimes.

Runtime-scope ownership is a major safety mechanism. `FeatureRuntimeScope` owns cleanup callbacks and service lifetime. `setup_routed_runtime` attaches services/effects/subscriptions to this scope; `shutdown_routed_runtime` and `shutdown_routed_feature_lifecycle` unwind them. The anti-pattern is partial teardown, where a feature drops only some bindings and leaks the rest. Lifecycle-owned scope teardown is the correct model.

[Back to Table of Contents](#table-of-contents)

### Higher-Level Runtime Faculties and Composition

The routed runtime system is now a control-plane/runtime-plane composition framework, not just a hotkey helper. `RoutedRuntimeSpec` can declare sibling runtime faculties that are created together during bind, updated in frame loops, and disposed together on shutdown. This is a central architectural pillar.

Dependency validation starts with `FeatureDependencySpec`, providing startup guardrails for required feature presence. Runtime policy and admission control are expressed through `RuntimePolicySpec` and evaluated by `RuntimePolicyEngine`, yielding `PolicyDecision` outcomes for allowed/denied/limited work.

Effect ownership uses `EffectBindingSpec` with `EffectLifetimeOrchestrator`, grouping cancellable effects under runtime scope cleanup. Routed event stream handling is modeled by `EventPipelineStageSpec` and `EventPipelineSpec`, executed by `EventPipelineRuntime` with staged behaviors like filter/map/debounce/throttle/window.

Durable operation recovery is represented by `DurableOperationBindingSpec`, `DurableOperationQueueSpec`, `DurableQueueRecord`, and `DurableOperationQueueRuntime`. This enables idempotency-aware queueing, bounded inflight work, and persistence-backed retries. Capability negotiation is handled by `CapabilityProviderSpec`, `CapabilityRequirementSpec`, and `CapabilityContractRuntime`, so feature contracts can validate versioned capabilities at runtime.

Incremental projection and recomputation are split into complementary facilities: `ProjectionNodeSpec`/`ProjectionSpec`/`ProjectionRuntime` for projection graphs, and `RecomputeNodeSpec`/`RecomputeOrchestrator` for deterministic recompute scheduling. Workflow orchestration (`WorkflowStepSpec`, `WorkflowSpec`, `WorkflowCoordinator`) supports multi-step feature-local orchestration with operation-handle waiting semantics.

Resilience and operations controls continue with `QoSPolicySpec`/`QoSPolicyRuntime` for per-update budget gating, `HealthProbeSpec`/`FeatureHealthRuntime` for aggregate health states, `ReplaySpec`/`RuntimeReplayHarness` for bounded runtime capture/replay, and `ReplacePolicySpec`/`FeatureHotSwapManager` for controlled replacement.

All of these faculties are declarative entries on `RoutedRuntimeSpec`, then lifecycle-owned runtime instances after binding. Their value is not only capability breadth but cleanup correctness: setup and teardown remain paired by lifecycle, avoiding leaked subscriptions, orphaned callbacks, and half-decommissioned runtime services.

[Back to Table of Contents](#table-of-contents)

## Quickstart Path (Practice)

This quickstart follows the real bootstrap pattern used by the demo: build a `HostApplicationBindingSpec`, convert it with `build_host_application_config(...)`, then initialize your host with `bootstrap_host_application(...)`.

See [Appendix F: Specifications and Option Reference](#appendix-f-specifications-and-option-reference).

```python
from gui_do import (
	HostApplicationBindingSpec,
	SceneBundleBindingSpec,
	ActionBindingSpec,
	TelemetryConfig,
	build_host_application_config,
	bootstrap_host_application,
)


class MyHost:
	def __init__(self) -> None:
		config = build_host_application_config(
			HostApplicationBindingSpec(
				display_size=(1280, 720),
				window_title="My gui_do app",
				fonts={"default": {"file": "assets/font.ttf", "size": 14}},
				initial_scene_name="main",
				scene_bundle_entries=(
					SceneBundleBindingSpec(scene_name="main", pretty_name="Main", emit_scene_setup_spec=True),
				),
				action_entries=(
					ActionBindingSpec(kind="exit", action_id="exit", label="Exit"),
				),
				telemetry=TelemetryConfig(enabled=False),
				target_fps=60,
			)
		)
		bootstrap_host_application(self, config)
```

Milestone progression for first-time app assembly:

1. App opens to one scene without bootstrap errors.
2. One feature creates one visible control in `build`.
3. One `ObservableValue` drives one visible label update.
4. One action and one hotkey invoke expected behavior.
5. One overlay/toast route does not leak events to underlying controls.
6. Workspace load/save completes with restore report inspection.

Common early failures and direct fixes:

- Feature not visible: verify feature entries and scene names line up.
- Hotkey does nothing: verify `ActionSpec`/`ActionBindingSpec` and key scope.
- Overlay captures unexpected keys: inspect overlay dismissal and key routing policy.
- State changes without UI updates: move subscriptions to `bind_runtime` and ensure teardown is not premature.

[Back to Table of Contents](#table-of-contents)

## Architecture and Runtime Model

The repository intentionally separates reusable library code from consumer/demo code. `gui_do/` is the framework package. `demo_features/` and `gui_do_demo.py` are consumer-side integration code. This boundary is contract-checked in `tests/test_boundary_contracts.py` and documented in architecture contracts.

See [Appendix F: Specifications and Option Reference](#appendix-f-specifications-and-option-reference).

The recommended import model is root-import only (`from gui_do import ...`). Consumer code should not rely on internal modules. Tiered exports in `gui_do/__init__.py` communicate abstraction order: start with Tier 1 bootstrap and feature composition, then descend into lower-level tiers only when a higher abstraction does not fit your need.

Runtime guarantees are explicitly documented and tested:

- Canonical `GuiEvent` normalization before dispatch.
- Scene-isolated runtime update behavior.
- Deterministic focus candidate ordering.
- Scheduler budget clamping: fraction 0.12, floor 0.5 ms, ceiling 4.0 ms.
- Workspace restore that reports applied/skipped/missing settings instead of failing hard on unknown keys.

`GuiApplication.process_event` is best understood as a normalized, staged routing pipeline: input normalization, quit handling, shared input-state updates, pointer/logicalization work, overlay routing, keyboard routing, feature/scene handlers, and stop-signal checks (`propagation_stopped`, `default_prevented`).

Known non-goals in architecture terms: gui_do does not try to be a native-widget parity layer, does not replace domain architecture decisions, and does not treat internal infrastructure APIs as beginner defaults.

[Back to Table of Contents](#table-of-contents)

## Feature Organization Conventions

Feature packaging is a scaling strategy, not only a style preference. As a feature grows from one visual widget into lifecycle wiring, runtime facilities, cross-feature messaging, and persistence state, single-file implementations become fragile. A dedicated package per feature keeps boundaries visible and allows growth without collapsing maintainability.

The repository already shows this growth pattern in several packages: `demo_features/life/` contains `life_feature.py`, `life_logic_feature.py`, `life_presenter.py`, `life_specs.py`, and runtime helpers; `demo_features/mandelbrot/` similarly separates feature, logic, presenter, and helpers; `demo_features/systems/` demonstrates broad split by concern (`systems_*_helpers.py`, presenter, feature, specs, models). This is exactly the kind of structure you want once a feature has both UI and runtime orchestration responsibilities.

The organizational contract requires each feature folder to be a Python package with `__init__.py`. That package root is the integration boundary that should remain stable while internals evolve. Internal modules can split and merge as needed, but external bootstrap and cross-feature imports should target package-level surfaces.

Even in codebases where historical imports still target `*_feature.py` directly, package-root surfaces should be treated as the default architecture direction because they isolate churn. As routed runtime faculties are introduced (service bindings, effect ownership, operation queues, policy engines, replay harnesses), this isolation becomes more important: runtime composition evolves quickly and should not force broad import rewrites.

Short package-root export/import pattern:

```python
# demo_features/life/__init__.py
from .life_feature import LifeFeature
from .life_logic_feature import LifeLogicFeature

__all__ = ["LifeFeature", "LifeLogicFeature"]

# consumer/bootstrap module
from demo_features.life import LifeFeature
```

Cross-feature import discipline follows the same rule: import public package-root symbols from sibling packages rather than internal helper modules. This keeps relationships explicit, prevents accidental reach-in dependencies, and reduces breakage during refactors.

When documenting package metadata or module contract points, keep double-underscore identifiers in inline code form (for example `__init__.py`, `__version__`, and `__demo__`) so markdown does not misparse underscores as emphasis.

[Back to Table of Contents](#table-of-contents)

## Core Workflow: Build, Bind, Route, Update, Draw

The five-phase workflow is the practical operating model of gui_do features.

See [Appendix F: Specifications and Option Reference](#appendix-f-specifications-and-option-reference).

`build` creates stable structure: control trees, presenter objects, and static feature-owned state. Avoid runtime subscriptions and cross-feature binding here.

`bind_runtime` wires host-dependent behavior after all scene features are built. This is where you subscribe to observables, register action/hotkey/event wiring, configure routed runtime systems, and resolve sibling interactions.

`route` is event/message handling through registered action maps, event subscriptions, and feature handlers. `RoutedFeature` plus routed lifecycle specs is useful when the feature has non-trivial action and runtime integration.

`update` is frame-time logic: scheduler pump, animation progress, staged runtime-system pumps, projection/recompute work, and health/policy checks.

`draw` handles custom rendering beyond control-tree defaults.

For routed runtime composition, `RoutedRuntimeSpec` and `RoutedFeatureLifecycleSpec` reduce repetitive setup/teardown boilerplate. The lifecycle pair:

- `bind_routed_feature_lifecycle(feature, host, lifecycle_spec)`
- `shutdown_routed_feature_lifecycle(feature, host, lifecycle_spec)`

ensures runtime scope ownership is preserved across service publication/consumption, reactive effects, operation bus/failure-policy bindings, and higher-level facilities such as dependency checks, workflow coordination, recompute/projection pipelines, QoS policy, health probes, replay capture, and hot-swap policy.

```python
from gui_do import RoutedRuntimeSpec, RoutedFeatureLifecycleSpec
from gui_do import bind_routed_feature_lifecycle, shutdown_routed_feature_lifecycle


class ExampleFeature:
	def __init__(self) -> None:
		self._runtime = RoutedRuntimeSpec(scene_name="main")
		self._lifecycle = RoutedFeatureLifecycleSpec(runtime_spec=self._runtime)

	def bind_runtime(self, host) -> None:
		bind_routed_feature_lifecycle(self, host, self._lifecycle)

	def shutdown_runtime(self, host) -> None:
		shutdown_routed_feature_lifecycle(self, host, self._lifecycle)
```

[Back to Table of Contents](#table-of-contents)

## Main Systems Reference

Before chapter-level details, keep one global mental model: systems in gui_do are modular, declarative, and lifecycle-driven. You describe setup with specs and helper APIs, then runtime managers run within scene and feature lifecycles. Most integration bugs come from breaking lifecycle ownership, not from wrong control syntax.

See [Appendix F: Specifications and Option Reference](#appendix-f-specifications-and-option-reference).

The Task Panel, Scene Menu Strip, and Command Palette are optional facilities. They are not implicitly created. A scene has them only when user-side specs and setup helpers declare them. This optionality is part of runtime contract behavior and should influence architecture decisions: include these facilities intentionally when discoverability or window navigation warrants them; omit them for simpler, narrower scenes.

Task Panel usage is typically scene-scoped via `SceneTaskPanelSpec`, optional `TaskPanelSlotLayoutSpec`, and button/toggle declarations (`TaskPanelButtonSpec`, `TaskPanelWindowToggleGroupSpec`, `TaskPanelFocusToggleSpec`). Scene menu strip behavior is declared with `SceneMenuStripSpec` and related helpers (`add_scene_menu_strip_from_spec`, `add_standard_scene_menu_strip`, or window menu-strip helpers). Command Palette activation is scene-scoped through `SceneCommandPaletteSpec` and palette behavior via `PaletteBindingSpec`.

Global key/focus behavior should be registered in `bind_runtime` and removed in `shutdown_runtime` (or routed lifecycle shutdown). For declarative features, prefer `RoutedRuntimeSpec` plus routed lifecycle helpers so teardown is automatic and symmetric. Anti-patterns to avoid: registering hotkeys in ad hoc module-level code, creating task-panel toggles without focus exclusion support, and partially tearing down only some overlay/action subscriptions.

```python
from gui_do import (
	RoutedRuntimeSpec,
	TaskPanelFocusToggleSpec,
	SceneCommandPaletteSpec,
	ActionHotkeySpec,
)

RUNTIME_SPEC = RoutedRuntimeSpec(
	scene_name="main",
	action_hotkeys=(ActionHotkeySpec(action_name="help", handler=lambda _e: True),),
	task_panel_focus_toggles=(
		TaskPanelFocusToggleSpec(action_name="toggle_systems", scene_name="main", key=0),
	),
	command_palette=SceneCommandPaletteSpec(key=0, scene_name="main"),
)
```

[Back to Table of Contents](#table-of-contents)

### 8.1 Application Bootstrap and Host Configuration

Bootstrap is the deterministic root of application assembly. `HostApplicationConfig` and `bootstrap_host_application` provide a stable two-phase model: build declarative config, then realize runtime state on the host. This separates specification from execution and keeps startup behavior measurable.

Primary public APIs include `HostApplicationBindingSpec`, `HostApplicationConfig`, `build_host_application_config`, `bootstrap_host_application`, and bundle builders such as `SceneBundleBindingSpec` and `FeatureWindowBundleBindingSpec`. Typical flow: author binding spec entries, build the config, bootstrap host, run `host.app.run_entrypoint(...)`.

Minimal usage:

```python
from gui_do import HostApplicationBindingSpec, build_host_application_config, bootstrap_host_application

config = build_host_application_config(
	HostApplicationBindingSpec(
		display_size=(1280, 720),
		window_title="App",
		fonts={"default": {"file": "assets/font.ttf", "size": 14}},
		initial_scene_name="main",
	)
)

host = type("Host", (), {})()
bootstrap_host_application(host, config)
```

Advanced pattern: use `scene_bundle_entries` and `feature_window_bundle_entries` to compose scene setup, runtime scene specs, navigation actions, scene roots, and window toggle metadata in a compact declarative graph.

Common mistakes: post-bootstrap host mutations that bypass config intent, feature/window specs with mismatched scenes, and missing initial scene declarations.

Cross-links: 8.2, 8.3, 8.11.

[Back to Table of Contents](#table-of-contents)

### 8.2 Feature Lifecycle and Feature Types

Feature lifecycle is where gui_do enforces composability and teardown safety. `Feature`, `DirectFeature`, `LogicFeature`, and `RoutedFeature` let you choose UI-heavy, draw-heavy, logic-only, or routed-runtime composition patterns without breaking a common lifecycle contract.

Lifecycle placement:

1. `build(host)`: instantiate controls, presenters, and static structures.
2. `bind_runtime(host)`: wire subscriptions, actions, event handlers, and cross-feature links.
3. `handle_event(host, event)`: consume/forward routed events.
4. `on_update(host)`: frame-based updates and scheduler work.
5. `draw(host, surface, theme)`: custom render behavior.
6. `shutdown_runtime(host)`: dispose runtime-owned resources.

`HOST_REQUIREMENTS` provides declarative dependency declaration per phase. Routed-lifecycle helpers (`bind_routed_feature_lifecycle`, `shutdown_routed_feature_lifecycle`) extend this model by pairing setup and cleanup for routed runtime facilities, including services, effects, operation policies, and higher-level runtime systems.

Minimal pattern:

```python
from gui_do import Feature


class CounterFeature(Feature):
	def build(self, host) -> None:
		self._sub = None

	def bind_runtime(self, host) -> None:
		pass

	def shutdown_runtime(self, host) -> None:
		if self._sub is not None:
			self._sub.dispose()
			self._sub = None
```

Advanced pattern: split logic and presentation (`LogicFeature` + `RoutedFeature` companion) and register companions using routed helpers to keep behavior decoupled.

Anti-pattern: partial teardown where only obvious subscriptions are disposed but runtime scope services/effects/operations remain registered.

Cross-links: 8.4, 8.9, 8.10.

[Back to Table of Contents](#table-of-contents)

### 8.3 Events, Actions, Input Mapping, and Routing

gui_do routes normalized `GuiEvent` values, not raw input events, through deterministic pipelines. `EventType` includes `PASS`, `QUIT`, `KEY_DOWN`, `KEY_UP`, `MOUSE_BUTTON_DOWN`, `MOUSE_BUTTON_UP`, `MOUSE_MOTION`, `MOUSE_WHEEL`, `TEXT_INPUT`, and `TEXT_EDITING`. `GuiEvent` carries routing metadata like `phase`, `propagation_stopped`, and `default_prevented`.

Actions are named commands managed by `ActionRegistry`/`ActionManager`, while `InputMap` and hotkey specs bind keys/chords to those actions. Focus and overlay state influence candidate dispatch order, and deterministic ordering constraints are contract-tested.

Typical flow:

1. Declare actions via `ActionSpec` or `ActionBindingSpec`.
2. Bind keys with `ActionHotkeySpec`, `ControlKeyBindingSpec`, or routed runtime declarations.
3. Handle routed events in features, respecting stop/default-prevented semantics.

Minimal declaration snippet:

```python
from gui_do import ActionSpec

actions = (
	ActionSpec(action_id="exit", label="Exit", kind="exit"),
	ActionSpec(action_id="palette_open", label="Command Palette", kind="palette_open"),
)
```

Advanced pattern: combine `InteractionStateMachine` (Tier 30) with action routing for guarded gesture workflows.

Common mistakes: mixing raw event handling with normalized `GuiEvent` routing, assuming global scope for scene-bound actions, and ignoring `propagation_stopped`/`default_prevented` in custom handlers.

Cross-links: 8.7, 8.8, 8.16.

[Back to Table of Contents](#table-of-contents)

### 8.4 State and Observables

Reactive state is the preferred coordination channel for controls and features. Core APIs include `ObservableValue`, `ObservableList`, `ObservableDict`, `ComputedValue`, `reactive_batch`, `CollectionView`, and store-centric APIs (`AppStateStore`, `StateSelector`, `StateTransaction`).

Mental model: features write state; controls and sibling features subscribe. This keeps producers decoupled from consumers and supports incremental updates.

Minimal lifecycle-safe example:

```python
from gui_do import ObservableValue

self.count = ObservableValue(0)

def bind_runtime(self, host):
	self._sub = self.count.subscribe(lambda value: setattr(self.label, "text", str(value)))

def shutdown_runtime(self, host):
	if self._sub is not None:
		self._sub.dispose()
		self._sub = None
```

Advanced pattern: declarative routed reactive wiring with `StoreSubscriptionSpec`, `StoreSelectorSpec`, `ObservableEffectSpec`, and `SignalEffectSpec` on `RoutedRuntimeSpec`, so registration and cleanup are lifecycle-owned.

Common mistakes: polling in `on_update`, subscribing before control availability, leaking subscriptions, and sharing mutable plain dict/list state where observables are expected.

Cross-links: 8.2, 8.13, 8.14.

[Back to Table of Contents](#table-of-contents)

### 8.5 Controls and Control Composition

Controls are reusable UI primitives organized into primary and extended families (Tiers 12 and 13). Features should own a root control subtree and avoid direct cross-feature control dependencies.

Primary controls include `PanelControl`, `LabelControl`, `ButtonControl`, `ToggleControl`, `SliderControl`, `ScrollbarControl`, `CanvasControl`, `CanvasViewport`, `FrameControl`, `ImageControl`, and other baseline building blocks. Extended controls cover richer components like `TextInputControl`, `DropdownControl`, `ListViewControl`, `DataGridControl`, `TreeControl`, `WindowControl`, `TaskPanelControl`, `MenuBarControl`, `ToolbarControl`, and `PropertyInspectorPanel`.

`WindowPresenter` is the preferred split point for window-level composition: presenters own detailed layout, while features own lifecycle and routing.

Minimal usage flow:

1. Build root `PanelControl` in `build`.
2. Add child controls and configure identifiers.
3. Wire callbacks/subscriptions in `bind_runtime`.
4. Dispose subscriptions and runtime resources in `shutdown_runtime`.

```python
from pygame import Rect
from gui_do import PanelControl, LabelControl, ButtonControl

def build(self, host):
	self.root = host.app.add(PanelControl("root", Rect(0, 0, 480, 320)), scene_name="main")
	self.label = self.root.add(LabelControl("status", Rect(12, 12, 260, 24), "Ready"))
	self.root.add(ButtonControl("go", Rect(12, 44, 120, 30), "Go", on_click=self._on_go))
```

Advanced pattern: combine `WindowPresenter` with `TabbedPresenterSpec` and `TabBuilderSpec` for large windowed workspaces.

Common mistakes: building controls in `on_update`, storing business state in control objects, and coupling one feature to another feature's control attributes.

Cross-links: 8.2, 8.6, 8.9.

[Back to Table of Contents](#table-of-contents)

### 8.6 Layout Systems

Layout systems prevent brittle pixel math and give predictable behavior under resize, docking, and viewport changes. Core families span Tier 8 (`FlexLayout`, `GridLayout`, `ConstraintLayout`, `DockWorkspace`, `FlowLayout`), Tier 28 (`AdaptivePolicy`, `ConstraintSet`, `resolve_adaptive_policy`), and Tier 29 virtualization-aware structures.

Choose the simplest model that captures intent:

- `FlexLayout` for row/column proportional structures.
- `GridLayout` for tabular or form-like structure.
- `ConstraintLayout` for relationship-based positioning.
- `DockWorkspace` for IDE/workbench surface organization.
- Adaptive policy for breakpoint-driven constraint switching.

Minimal flex snippet:

```python
from gui_do import FlexLayout, FlexDirection, FlexItem

layout = FlexLayout(direction=FlexDirection.ROW, gap=8)
layout.add(FlexItem(control=self.sidebar, grow=0, basis=220))
layout.add(FlexItem(control=self.main_area, grow=1))
```

Advanced pattern: adaptive constraints for mobile/desktop breakpoints using `ConstraintSet` plus `AdaptivePolicy` resolution.

Common mistakes: mixing multiple layout engines in one container without clear ownership, hardcoding dimensions that conflict with adaptive rules, and invoking layout before control attachment.

Cross-links: 8.5, 8.9, 8.12.

[Back to Table of Contents](#table-of-contents)

### 8.7 Focus and Accessibility

Focus and accessibility are parallel correctness systems. Focus determines which control receives keyboard input (`FocusManager`, `FocusScopeManager`, `WindowFocusManager`, `FocusRing`). Accessibility models semantic structure with `AccessibilityNode`, `AccessibilityTree`, and announcement channels (`AccessibilityBus`, `AccessibilityAnnouncement`).

Lifecycle model:

- Register focusable/semantic elements after controls exist.
- Keep hidden/disabled controls out of active focus rings.
- Dispose scope subscriptions and runtime wiring on shutdown.

Minimal accessibility setup:

```python
from gui_do import AccessibilityTree, AccessibilityNode, AccessibilityRole

tree = AccessibilityTree()
tree.root.add_child(AccessibilityNode(role=AccessibilityRole.BUTTON, name="Submit"))
```

`TaskPanelFocusToggleSpec` is important for lifecycle-safe window toggling: hidden window controls should be excluded from focus traversal to avoid keyboard traps.

Anti-pattern: registering focus/accessibility observers outside runtime scope ownership, then forgetting to dispose them when scenes change.

Cross-links: 8.3, 8.8, 8.9.

[Back to Table of Contents](#table-of-contents)

### 8.8 Overlays, Dialogs, Notifications, and Command Surfaces

Overlay systems manage transient UI surfaces with explicit routing and dismissal contracts. Tier 9 includes managers for dialogs, toasts, context menus, command palette, tooltips, file dialogs, notification center, cursor overlays, drag/drop, and shortcut help overlays.

Key APIs include `OverlayManager`, `DialogManager`, `ToastManager`, `CommandPaletteManager`, `TooltipManager`, `NotificationCenter`, `ShortcutHelpOverlay`, and placement helpers (`PopupPlacement`, `compute_popup_rect`).

Typical flow:

1. Show overlay through the appropriate manager.
2. Rely on manager-specific dismissal behavior.
3. Pair any runtime subscriptions/hotkeys with lifecycle teardown.

```python
def on_saved(host):
	host.toasts.show("Saved", severity=host.toasts.ToastSeverity.SUCCESS)
```

Advanced pattern: command palette composition using `PaletteBindingSpec` and scene command-palette key setup with scene/window entry groups.

Common mistakes: overlays with no dismissal path, expecting toast clicks to pass through to underlying controls, and leaving overlay hotkeys registered after feature teardown.

Cross-links: 8.3, 8.7, 8.9.

[Back to Table of Contents](#table-of-contents)

### 8.9 Scene, Window, and Task-Panel Presentation Models

Scene and window presentation defines what is visible, what receives focus, and which toggles/commands are exposed in a scene context. This chapter combines Tier 1 spec types with Tier 18 helper APIs used for presentation composition.

Core types include `ScenePresentationModel`, `WindowSpec`, `AnchoredWindowSpec`, `FeatureWindowBundleBindingSpec`, `WindowToggleBindingSpec`, `SceneTaskPanelSpec`, `TaskPanelButtonSpec`, `TaskPanelFocusToggleSpec`, `WindowPresenter`, `TabbedPresenterSpec`, and `TabBuilderSpec`. Runtime helpers include `set_window_visible_state`, `toggle_window_visibility`, `create_anchored_feature_window`, `create_feature_presented_window`, `ensure_scene_task_panel`, and scene menu-strip helpers.

Typical flow:

1. Declare window/task-panel specs in host binding config.
2. Build windows in feature `build`.
3. Bind visibility/focus toggles in runtime.
4. Dispose routed bindings during shutdown.

For actions that need retries, timeouts, and failure publication, expose scene-local operations through `FeatureOperationSpec` + `FailurePolicySpec` and call them via `FeatureOperationBus` rather than ad hoc callbacks.

Common mistakes: creating windows in `bind_runtime` (too late for sibling bind assumptions), mismatch between task-panel toggle metadata and scene scope, and failing to sync visibility with focus eligibility.

Cross-links: 8.2, 8.5, 8.7, 8.8.

[Back to Table of Contents](#table-of-contents)

### 8.10 Scheduling, Timing, Animation, and Transitions

Scheduling is budget-governed. Runtime contract values are fixed at fraction 0.12 of frame dt milliseconds, floor 0.5 ms, and ceiling 4.0 ms for scheduler dispatch clamping. This provides bounded work under slow frames and prevents starvation under fast frames.

Tier 5 APIs include `TaskScheduler`, `Timers`, `TweenManager`, `AnimationSequence`, `TransitionManager`, `AnimationStateMachine`, `SceneTimeline`, `Debouncer`, `Throttler`, and `CooperativeScheduler` (`Sleep`, `Pause`, `WaitForSignal`, `WaitForEvent`, `WaitUntil`, `WaitForAll`).

Minimal tween example:

```python
def fade_in(host, panel):
	host.tweens.to(panel, "alpha", 255, duration=0.2)
```

Advanced pattern: cooperative multi-step workflow using `CooperativeScheduler` plus operation bus handles, where timeout/retry policy is declared via `FailurePolicySpec` and driven as scheduled work instead of blocking loops.

Common mistakes: heavy compute in `on_update`, coroutine steps that perform blocking I/O, and forgetting cancellation on scene exit.

Cross-links: 8.2, 8.14, 8.16.

[Back to Table of Contents](#table-of-contents)

### 8.11 Persistence and Workspace/Session State

Persistence in gui_do combines workspace/session restore with versioned snapshot migration and undo/state tools. Core APIs include `WorkspacePersistenceManager`, `WorkspaceState`, `SettingsRegistry`, `SettingDescriptor`, `SceneSnapshot`, `NodeSnapshot`, `CommandHistory`, `CommandTransaction`, `UndoContextManager`, and Tier 32 migration APIs (`SchemaVersion`, `VersionedSnapshot`, `MigrationStep`, `MigrationRegistry`, `SnapshotMigrator`, `make_snapshot`, `read_version`).

Restore behavior is contract-driven. Restore reports expose `target_scene`, `switched_scene`, `restored_feature_states`, `restored_scene_nodes`, `applied_settings`, `skipped_settings`, and `missing_settings_blocks`.

Minimal flow:

```python
report = host.app.load_workspace("workspace.json")
if report and report.skipped_settings:
	host.app.toasts.show("Some settings were skipped")
```

Advanced pattern: maintain forward-only migration paths with `SnapshotMigrator` so old persisted states are transformed into current schema before feature restore.

Common mistakes: assuming all settings exist across versions, skipping version reads before migration, and using one shared default workspace path for multi-instance deployments.

Cross-links: 8.1, 8.2, 8.16.

[Back to Table of Contents](#table-of-contents)

### 8.12 Theme, Styling, and Visual Systems

Theme and font systems decouple visual semantics from individual controls. Primary APIs include `ThemeManager`, `ColorTheme`, `DesignTokens`, `FontManager`, `FontRoleRegistry`, `ScopedTheme`, `ScopedThemeManager`, and `ThemeInvalidationBus`.

Use role mappings in bootstrap (`FontRoleBindingSpec`, font dictionaries, `setup_standard_font_roles`) so controls consume semantic roles rather than hardcoded font objects. On theme switch, invalidation signaling should clear cached visual surfaces.

Minimal setup:

```python
from gui_do import FontRoleBindingSpec

font_roles = (
	FontRoleBindingSpec(role="title", size=16, font="default", bold=True),
	FontRoleBindingSpec(role="body", size=14, font="default"),
)
```

Advanced pattern: per-window scoped theme overrides via `ScopedThemeManager`, with cache listeners subscribed to `ThemeInvalidationBus`.

Common mistakes: hardcoded literal colors in draw code, updating theme state without invalidating caches, and late font registration outside config/bootstrap path.

Cross-links: 8.1, 8.5, 8.15.

[Back to Table of Contents](#table-of-contents)

### 8.13 Text, Input, Forms, and Validation Systems

Text and form systems span raw input controls, form models, validation pipelines, schema runtimes, and async validation. Primary APIs include `TextInputControl`, `TextAreaControl`, `DocumentModel`, `FormModel`, `FormSchema`, `SchemaField`, `ValidationPipeline`, validators (`RequiredValidator`, `PatternValidator`, `DependentValidator`), `AsyncFieldValidator`, `AsyncFormValidator`, and schema runtime APIs (`FieldGraphSchema`, `ValidationPolicy`, `SchemaFormRuntime`).

Typical usage flow:

1. Define schema and validators.
2. Build form runtime (`SchemaFormRuntime`) with policy.
3. Bind controls to field state.
4. Use async validators for remote checks where needed.

```python
from gui_do import FormSchema, SchemaField, RequiredValidator, PatternValidator

schema = FormSchema(
	fields=(
		SchemaField(name="email", validators=(RequiredValidator(), PatternValidator(r".+@.+"))),
		SchemaField(name="password", validators=(RequiredValidator(),)),
	)
)
```

Advanced pattern: combine `AsyncFormValidator` with debounce/stale-generation handling so outdated remote responses do not overwrite newer local input state.

Common mistakes: running full validation on every keystroke without policy controls, failing to cancel stale async checks, and mixing text rendering concerns with form domain logic.

Cross-links: 8.4, 8.5, 8.14.

[Back to Table of Contents](#table-of-contents)

### 8.14 Data and Dataflow Helpers

Data helpers support loading, filtering, sorting, diffing, caching, and cancelable multi-stage processing. Core APIs include `VirtualItemSource`, `FixedItemSource`, `SortFilterProxySource`, `AsyncDataProvider`, `DataCache`, `ObjectPool`, `ListDiffCalculator`, and `DataflowPipeline` with `PipelineStage` and `CancellationToken`.

Minimal source/proxy setup:

```python
from gui_do import FixedItemSource, SortFilterProxySource

source = FixedItemSource(items)
proxy = SortFilterProxySource(source)
proxy.set_filter(lambda item: item.active)
proxy.set_sort_key(lambda item: item.name)
```

Advanced pattern: multi-stage `DataflowPipeline` (load -> transform -> rank) where each new user query cancels stale generations through `CancellationToken`.

Operational guidance: if the task has retries/timeouts/publication semantics, expose it as a `FeatureOperationSpec` under failure policies instead of a one-off callback chain.

Common mistakes: full collection redraws without diffing, stale pipeline generations that keep running after new inputs, and unbounded in-memory growth without cache expiry.

Cross-links: 8.10, 8.13, 8.16.

[Back to Table of Contents](#table-of-contents)

### 8.15 Graphics and Audio Integration Points

Graphics and audio systems support high-fidelity rendering and semantic cue playback while staying integrated with feature lifecycle. Graphics APIs include `DirtyRegionTracker`, `DrawContext`, `SurfaceCompositor`, `Layer`, `ShapeRenderer`, `SurfaceEffects`, `VectorPath`, `SpriteSheet`, `FrameAnimation`, `ParticleSystem`, `TileMap`, `SceneGraph2D`, `Camera2D`, and offscreen targets (`RenderTarget`, `OffscreenRenderTarget`, `create_render_target`). Audio APIs include `SoundCue`, `SoundBankRegistry`, and `SoundEventBus`.

Typical flow:

1. Initialize graphics/audio resources in build/setup.
2. Update animation/particle state in `on_update`.
3. Draw via control tree hooks or feature `draw`.
4. Publish semantic sound cues on meaningful user/system events.

```python
def on_update(self, host):
	self.particles.tick(host.app.dt)

def draw(self, host, surface, theme):
	self.particles.draw(surface)
	host.sound_bus.publish(host.sound_cue_factory("notify"))
```

Advanced pattern: combine `DirtyRegionTracker` with offscreen render targets and scene graph transforms to redraw only changed regions in large viewports.

Common mistakes: full-surface redraw every frame despite dirtiness tracking, loading assets during draw calls, and firing audio from low-level noise rather than semantic actions.

Cross-links: 8.2, 8.5, 8.10, 8.16.

[Back to Table of Contents](#table-of-contents)

### 8.16 Telemetry, Introspection, and Operational Hooks

Operational visibility is provided by telemetry, property inspection, and spatial indexing. Tier 7 APIs (`configure_telemetry`, `telemetry_collector`, `analyze_telemetry_records`, `analyze_telemetry_log_file`, `render_telemetry_report`) give performance trace workflows. Tier 17 APIs (`ui_property`, `PropertyRegistry`, `PropertyInspectorModel`, `SceneSpatialIndex`) support runtime introspection and debug UIs.

Minimal telemetry run:

```python
from gui_do import configure_telemetry, telemetry_collector, analyze_telemetry_records, render_telemetry_report

configure_telemetry(enabled=True)
report = analyze_telemetry_records(telemetry_collector.records)
print(render_telemetry_report(report))
```

Advanced pattern: correlate telemetry samples with property-inspector snapshots and spatial index overlays to localize frame-cost regressions to specific control regions.

Common mistakes: profiling only idle loops, omitting telemetry enablement before scenario runs, and treating visual guesswork as a substitute for recorded evidence.

Cross-links: 8.10, 8.11, 8.15.

[Back to Table of Contents](#table-of-contents)

## Integration Patterns and Composition Recipes

### Recipe 1: Routed Feature + Actions + Shortcut Overlay

Goal: expose discoverable keyboard commands with lifecycle-safe setup/teardown.

Pattern: declare actions in config, include `ShortcutOverlaySpec` and `ActionHotkeySpec` in `RoutedRuntimeSpec`, and bind/unbind through routed feature lifecycle helpers.

Validation: help overlay toggles from the declared key/action and disappears cleanly after feature shutdown.

### Recipe 2: Window Presenter + Task Panel + Focus Toggle

Goal: scene-local floating windows that remain keyboard-coherent.

Pattern: define window specs/bundles, build presenter-backed windows in `build`, and attach `TaskPanelFocusToggleSpec` so hidden windows are excluded from focus traversal.

Validation: task-panel state reflects actual visibility and tab traversal never lands on hidden controls.

### Recipe 3: App State + Persistence + Migration

Goal: durable, evolvable state.

Pattern: manage state in `AppStateStore`, snapshot with `make_snapshot`, load with `read_version`, migrate through `SnapshotMigrator`, then restore features.

Validation: restore report fields are inspected and migration paths cover all supported legacy versions.

### Recipe 4: Dataflow Pipeline + Telemetry + Error Boundary

Goal: resilient background processing with diagnostics.

Pattern: pipeline stages use cancellation tokens; telemetry captures per-stage behavior; UI subtree is wrapped by `ErrorBoundary` for graceful failure.

Validation: stale work is canceled, bottlenecks are visible in reports, and UI remains responsive during stage failures.

[Back to Table of Contents](#table-of-contents)

## End-to-End Reference Application

```python
from gui_do import (
	ActionSpec,
	EventType,
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
	TelemetryConfig,
	bootstrap_host_application,
	bind_routed_feature_lifecycle,
	shutdown_routed_feature_lifecycle,
)
from pygame import Rect, K_F9


class CounterFeature(RoutedFeature):
	name = "counter"
	scene_name = "main"

	def __init__(self):
		super().__init__(self.name)
		self.count = ObservableValue(0)
		self._sub = None
		self._runtime = RoutedRuntimeSpec(
			scene_name="main",
			shortcut_overlays=(
				ShortcutOverlaySpec(
					attr_name="help_overlay",
					toggle_action_name="help",
					toggle_key=K_F9,
					manual_shortcut_lines=("F9: Toggle Help",),
				),
			),
		)
		self._lifecycle = RoutedFeatureLifecycleSpec(runtime_spec=self._runtime)

	def build(self, host):
		self.label = host.app.add(LabelControl("count_label", Rect(20, 20, 240, 28), "Count: 0"), scene_name="main")

	def bind_runtime(self, host):
		self._sub = self.count.subscribe(lambda value: setattr(self.label, "text", f"Count: {value}"))
		bind_routed_feature_lifecycle(self, host, self._lifecycle)

	def handle_event(self, host, event):
		if event.kind is EventType.KEY_DOWN and event.key is not None:
			self.count.value = int(self.count.value) + 1
			return True
		return False

	def shutdown_runtime(self, host):
		if self._sub is not None:
			self._sub.dispose()
			self._sub = None
		shutdown_routed_feature_lifecycle(self, host, self._lifecycle)


CONFIG = HostApplicationConfig(
	display_size=(960, 540),
	window_title="gui_do Reference",
	fonts={"default": {"file": "demo_features/data/fonts/Gimbot.ttf", "size": 14}},
	font_role_specs=(),
	cursors=(),
	scene_specs=(SceneSetupSpec(name="main", pretty_name="Main"),),
	feature_specs=(FeatureSpec(attr_name="counter_feature", factory=CounterFeature),),
	window_specs=(),
	runtime_scene_specs=(RuntimeSceneSpec(scene_name="main", bind_escape_to_exit=True),),
	action_specs=(
		ActionSpec(action_id="exit", label="Exit", kind="exit"),
		ActionSpec(action_id="help", label="Help", kind="palette_open"),
	),
	static_accessibility_specs=(),
	initial_scene_name="main",
	telemetry=TelemetryConfig(enabled=True),
	target_fps=60,
)


class ReferenceHost:
	def __init__(self):
		bootstrap_host_application(self, CONFIG)

	def load_last_workspace(self):
		return self.app.load_workspace("workspace.json")

	def save_workspace_now(self):
		return self.app.save_workspace("workspace.json")


if __name__ == "__main__":
	host = ReferenceHost()
	host.load_last_workspace()
	host.app.run_entrypoint(target_fps=CONFIG.target_fps)
	host.save_workspace_now()
```

### What This Listing Demonstrates

The listing shows end-to-end wiring of `HostApplicationConfig` bootstrap, scene/feature registration, observable-to-control updates, routed runtime shortcut overlay setup, lifecycle-safe bind/shutdown pairing, host action declarations, telemetry enablement, and workspace load/save hooks.

### Validation Checklist

1. App opens and enters `main`.
2. Key input increments observable and updates label text.
3. F9 toggles the shortcut overlay.
4. Runtime teardown disposes subscriptions and routed resources.
5. Workspace load/save hooks execute without crashing loop shutdown.

[Back to Table of Contents](#table-of-contents)

## Testing, Diagnostics, and Reliability

Reliability work in gui_do is contract-first. The framework behavior is defended by public-surface tests, boundary tests, runtime contract tests, and targeted subsystem tests across controls, layout, persistence, and feature runtime facilities.

### Contract Tests

Run the high-priority contract suite:

```bash
python -m pytest -q tests/test_public_api_exports.py tests/test_public_api_docs_contracts.py tests/test_runtime_operating_contracts.py tests/test_boundary_contracts.py tests/test_gui_application_workspace_contracts.py
```

- `tests/test_public_api_exports.py`: verifies root-exported names are available.
- `tests/test_public_api_docs_contracts.py`: verifies docs/API alignment.
- `tests/test_runtime_operating_contracts.py`: checks deterministic runtime guarantees and scheduler budget contract.
- `tests/test_boundary_contracts.py`: enforces `gui_do` vs `demo_features` import boundaries.
- `tests/test_gui_application_workspace_contracts.py`: validates workspace restore/load contracts.

### Runtime Behavior Tests

Expected coverage includes workspace save/load flows, overlay routing contracts, deterministic layout/animation behavior, accessibility semantics, and routed runtime lifecycle safety for services/effects/operation buses.

### Debug and Trace Tools

- `EventRecorder` and `EventPlayback` for reproducible input traces.
- `DebugOverlay` for visual runtime inspection.
- `PropertyInspectorPanel` plus `PropertyInspectorModel` for runtime state introspection.
- Telemetry analysis functions (`analyze_telemetry_log_file`, `analyze_telemetry_records`, `render_telemetry_report`) for performance diagnosis.

### Maintainer Release Runbook

1. Run contract tests and runtime guarantees first.
2. Re-run scene/window/overlay regression slices relevant to touched systems.
3. Validate docs contracts and boundary contracts.
4. Validate end-to-end reference behavior assumptions.
5. Record any unresolved ambiguities in migration notes.

### Regression Triage Workflow

1. Reproduce with a minimal scenario.
2. Capture event/telemetry traces.
3. Localize to one subsystem/lifecycle phase.
4. Write or extend a failing test.
5. Patch with lifecycle-safe cleanup.
6. Re-check adjacent contract suites.

### Maintainer Diff Checklist

Inventory delta checks:

1. Compare root exports in `gui_do/__init__.py` with Appendix D and D.1.
2. Check `docs/` for changed guarantees/policies/boundary rules.
3. Check `tests/` for new contract/runtime modules that imply documentation updates.
4. Check `demo_features/` for updated recommended composition patterns.

Content integrity checks:

1. Ensure changed systems update both chapter prose and quick-index entries.
2. Remove retired APIs from examples and appendix index.
3. Classify added APIs at proper abstraction level (Tier 1 first).

Navigation and structure checks:

1. Ensure all added sections are present in TOC and anchors resolve.
2. Verify back-to-TOC links remain present in major sections.
3. Keep top-level chapter order stable unless intentionally redesigned.

Operational checks:

1. Re-run contract tests command above.
2. Revalidate end-to-end assumptions against runtime behavior.
3. Track unresolved ambiguities in migration/deprecation notes.

[Back to Table of Contents](#table-of-contents)

## Performance and Scaling Guidance

### Scheduler Budget Contract

Runtime dispatch is clamped with fraction 0.12 of dt milliseconds, floor 0.5 ms, and ceiling 4.0 ms. The goal is bounded burst behavior under slow frames and non-starvation under fast frames.

### Dirty-Region Rendering

`DirtyRegionTracker` is the primary incremental redraw optimization for complex surfaces. It tracks dirty rectangles and supports fast overlap checks so unchanged areas can be skipped.

### Virtualization and Incremental Rendering

Use `VirtualizationCore`/`VirtualizedWindow` for large datasets, `RecyclePool` for item reuse, and `ListDiffCalculator` for minimal redraw patches.

### Practical Scaling Checklist

1. Keep update/event handlers scene-scoped.
2. Avoid per-frame full collection reallocation.
3. Use debouncing/throttling for expensive user-driven operations.
4. Use cancelable `DataflowPipeline` generations for preemptible background work.
5. Profile representative interactive scenarios, not idle-only loops.
6. Gate expensive redraw regions with dirty tracking.

[Back to Table of Contents](#table-of-contents)

## Migration, Versioning, and Deprecation Notes

### Versioned Snapshot Strategy

Recommended migration sequence:

1. Save with `make_snapshot(current_version, state_dict)`.
2. Read stored version via `read_version(raw_snapshot)`.
3. Apply forward migration with `SnapshotMigrator` and registered `MigrationStep` entries.
4. Restore migrated payload into runtime systems.

`MigrationRegistry` stores step graph metadata; unresolved migration paths raise `MigrationError`.

### Deprecation Handling

Prefer additive transitions and explicit migration paths before removals. Keep deprecation policy centralized in this chapter. No formal deprecated public API catalog is currently maintained in-repo; add entries here when deprecations are introduced.

### Upgrade Checklist

1. Run contract tests before and after upgrade.
2. Verify consumer imports stay root-based (`from gui_do import ...`).
3. Validate action/input/focus behavior in active scenes.
4. Inspect restore reports for skipped/missing settings behavior.
5. Compare telemetry baselines for representative scenarios.
6. Verify routed runtime docs/examples still use current service/effect/operation/failure terminology.

[Back to Table of Contents](#table-of-contents)

## FAQ and Troubleshooting

### Should I build apps directly with controls or with features?

Use features as architectural boundaries. Controls are implementation detail within feature ownership. Feature lifecycle gives you deterministic setup, runtime wiring, and cleanup guarantees that controls alone do not provide.

### When should I use `RoutedFeature` over `Feature`?

Use `RoutedFeature` when you need declarative runtime wiring (hotkeys, overlays, service/effect/operation runtime systems) and predictable teardown through routed lifecycle helpers. Use `Feature` for simpler control-tree behavior where routed composition is unnecessary.

### Why are some key handlers not firing?

Check focus ownership, scene/window scope alignment, overlay modal capture, and whether action/key binding declarations are attached to the active context. Use event recording to verify where routing stops.

### Why do toast clicks not pass through?

By design, toast regions consume clicks to avoid accidental interaction with covered controls. Use explicit toast click handlers for intended actions.

### How do I preserve workspace restore compatibility?

Use versioned snapshots and forward migration steps. Always inspect restore report fields for skipped/missing blocks and surface non-fatal restore issues to users.

### How do I verify I am using supported APIs?

Import from root exports and run public API contract tests. Avoid internal-module imports as application dependencies.

[Back to Table of Contents](#table-of-contents)

## Appendix

### Appendix A: Glossary

- Feature: lifecycle-managed behavior unit (`Feature`, `DirectFeature`, `LogicFeature`, `RoutedFeature`) that owns UI/runtime work for one scene context.
- Spec: declarative data object that describes runtime wiring and composition intent.
- Host: plain Python object passed to bootstrap and populated with runtime members.
- Scene: top-level interaction context; feature execution and routing are scene-scoped.
- Window presentation: visibility/focus/toggle model for windowed surfaces within scenes.
- Routed runtime: declarative runtime bundle for subscriptions, hotkeys, operations, and advanced faculties.
- Observable: value/collection with subscriber notifications on mutation.
- Workspace state: persisted scene/feature/settings context for restore.
- Contract test: test verifying documented framework guarantees.
- Tier: grouped public export level indicating recommended abstraction order.
- Runtime scope: lifecycle-owned container for cleanup/service ownership.
- Feature operation: declaratively registered operation-bus handler.
- Failure policy: declarative retry/timeout/publication behavior for operations.

### Appendix B: Lifecycle and Event Sequence

1. `bootstrap_host_application` initializes host from config.
2. Feature `build` completes for the active scene.
3. Feature `bind_runtime` completes after scene build phase.
4. Runtime loop begins.
5. Each frame normalizes raw events into `GuiEvent`.
6. Overlay/focus/window/scene routing executes.
7. Feature event handlers run in routing order.
8. Feature `on_update` runs; schedulers and routed runtime systems pump.
9. Feature/control draw passes render output.
10. Scene transition triggers departing feature teardown and arriving feature build/bind.
11. App shutdown triggers runtime teardown and optional workspace save.

### Appendix C: System Dependency Map

Bootstrap and configuration (Tier 1) depend on spec families and feed all downstream systems. Feature lifecycle depends on control, event, state, and scheduling systems. Layout/focus rely on control tree and presentation visibility. Overlays depend on routing/focus policies. Persistence depends on state models and scene/window registration metadata.

Scheduling/animation sits in the update loop and cross-cuts data, rendering, and operations. Telemetry/introspection cross-cut nearly every system. Audio hooks depend on semantic events from action/feature layers. Scoped services and routed runtime systems operate as composition infrastructure that can be introduced at many abstraction levels.

### Appendix D: API Quick Index

Bootstrap and composition:

- `HostApplicationConfig`, `HostApplicationBindingSpec`, `build_host_application_config`, `bootstrap_host_application`
- `FeatureSpec`, `WindowSpec`, `RuntimeSceneSpec`, `SceneBundleBindingSpec`, `FeatureWindowBundleBindingSpec`
- `ActionSpec`, `ActionBindingSpec`, `ActionHotkeySpec`, `ControlKeyBindingSpec`
- `SceneRootSpec`, `SceneSetupSpec`, `SceneSetupBindingSpec`, `RuntimeSceneBindingSpec`

Features and routed runtime:

- `Feature`, `DirectFeature`, `LogicFeature`, `RoutedFeature`, `FeatureManager`, `FeatureMessage`
- `RoutedRuntimeSpec`, `RoutedFeatureLifecycleSpec`, `FeatureRuntimeScope`
- `ServiceBindingSpec`, `ServiceConsumerSpec`, `ObservableEffectSpec`, `SignalEffectSpec`
- `FeatureOperationSpec`, `FailurePolicySpec`, `FeatureOperationBus`
- Higher faculties: `FeatureDependencySpec`, `RuntimePolicySpec`, `EffectBindingSpec`, `EventPipelineSpec`, `DurableOperationQueueSpec`, `CapabilityProviderSpec`, `ProjectionSpec`, `WorkflowSpec`, `RecomputeNodeSpec`, `QoSPolicySpec`, `HealthProbeSpec`, `ReplaySpec`, `ReplacePolicySpec`

Events/actions/focus:

- `GuiEvent`, `EventType`, `EventPhase`, `EventManager`, `EventBus`, `EventRecorder`, `EventPlayback`
- `ActionManager`, `ActionRegistry`, `ActionDescriptor`, `InputMap`, `KeyChordManager`
- `FocusManager`, `FocusScope`, `FocusScopeManager`, `WindowFocusManager`, `FocusRing`

State/data/scheduling:

- `ObservableValue`, `ObservableList`, `ObservableDict`, `ComputedValue`, `reactive_batch`
- `AppStateStore`, `StateSelector`, `StateTransaction`
- `TaskScheduler`, `Timers`, `TweenManager`, `TransitionManager`, `CooperativeScheduler`
- `DataflowPipeline`, `PipelineStage`, `CancellationToken`

Controls/layout/overlays:

- Controls: `PanelControl`, `LabelControl`, `ButtonControl`, `CanvasControl`, `TextInputControl`, `ListViewControl`, `DataGridControl`, `WindowPresenter`, `TaskPanelControl`
- Layout: `FlexLayout`, `GridLayout`, `ConstraintLayout`, `DockWorkspace`, `AdaptivePolicy`, `VirtualizationCore`
- Overlays: `DialogManager`, `ToastManager`, `CommandPaletteManager`, `TooltipManager`, `ShortcutHelpOverlay`, `OverlayManager`

Persistence/theme/graphics/diagnostics:

- `WorkspacePersistenceManager`, `SettingsRegistry`, `SnapshotMigrator`, `make_snapshot`, `read_version`
- `ThemeManager`, `ColorTheme`, `DesignTokens`, `ThemeInvalidationBus`, `ScopedThemeManager`
- `DirtyRegionTracker`, `SurfaceCompositor`, `ParticleSystem`, `SceneGraph2D`, `SoundEventBus`
- `configure_telemetry`, `telemetry_collector`, `PropertyInspectorModel`, `SceneSpatialIndex`

### Appendix D.1: Tier Matrix

| Tier | System | Representative types |
|---|---|---|
| 1 | Primary entry points and data-driven APIs | `HostApplicationConfig`, `FeatureSpec`, `RoutedRuntimeSpec`, `bootstrap_host_application` |
| 2 | Core application and scene management | `GuiApplication`, `create_display`, `SceneTransitionManager` |
| 3 | Essential data/state | `ObservableValue`, `ComputedValue`, `ObservableList`, `reactive_batch` |
| 4 | Events/actions/focus/input | `GuiEvent`, `ActionManager`, `InputMap`, `FocusManager` |
| 5 | Scheduling and animation | `TaskScheduler`, `TweenManager`, `CooperativeScheduler`, `SceneTimeline` |
| 6 | Theme and fonts | `ThemeManager`, `ColorTheme`, `FontManager`, `DesignTokens` |
| 7 | Telemetry and diagnostics | `configure_telemetry`, `TelemetryCollector`, `analyze_telemetry_records` |
| 8 | Layout and spatial | `FlexLayout`, `GridLayout`, `DockWorkspace`, `ConstraintLayout` |
| 9 | Overlay managers and windows | `DialogManager`, `ToastManager`, `CommandPaletteManager`, `OverlayManager` |
| 10 | Forms and data binding | `FormModel`, `FormSchema`, `ValidationPipeline`, `WizardFlow` |
| 11 | State and persistence | `WorkspacePersistenceManager`, `SettingsRegistry`, `CommandHistory` |
| 12 | Primary controls | `PanelControl`, `LabelControl`, `ButtonControl`, `CanvasControl` |
| 13 | Extended controls | `TextInputControl`, `ListViewControl`, `WindowPresenter`, `TaskPanelControl` |
| 14 | Text and localization | `TextFlow`, `TextFormatter`, `StringTable`, `LocaleRegistry` |
| 15 | Data and collections | `AsyncDataProvider`, `SortFilterProxySource`, `DataCache`, `ListDiffCalculator` |
| 16 | Graphics and rendering | `DirtyRegionTracker`, `SurfaceCompositor`, `ParticleSystem`, `SceneGraph2D` |
| 17 | Introspection and inspection | `ui_property`, `PropertyInspectorModel`, `SceneSpatialIndex` |
| 18 | Advanced runtime and bootstrapping | `set_window_visible_state`, `create_feature_presented_window`, `bind_routed_feature_lifecycle` |
| 19 | Infrastructure internals | `UiEngine` |
| 20 | Audio | `SoundCue`, `SoundBankRegistry`, `SoundEventBus` |
| 21 | Accessibility | `AccessibilityNode`, `AccessibilityTree`, `AccessibilityBus` |
| 22 | Theme invalidation | `ThemeInvalidationBus` |
| 23 | Undo context routing | `UndoContextManager` |
| 24 | Async form validation | `AsyncFieldValidator`, `AsyncFormValidator` |
| 25 | Scoped service graph | `ServiceKey`, `ServiceScope`, `ScopeStack` |
| 26 | Cancelable dataflow pipeline | `CancellationToken`, `DataflowPipeline`, `PipelineHandle` |
| 27 | Transactional app state store | `AppStateStore`, `StateSelector`, `StateTransaction` |
| 28 | Adaptive constraint layout v2 | `ConstraintSet`, `AdaptivePolicy`, `resolve_adaptive_policy` |
| 29 | Unified virtualization core | `VirtualizedWindow`, `RecyclePool`, `VirtualizationCore` |
| 30 | Interaction state machine framework | `InteractionPhase`, `InteractionStateMachine` |
| 31 | Schema-driven form runtime | `FieldGraphSchema`, `ValidationPolicy`, `SchemaFormRuntime` |
| 32 | Portable snapshot and migration layer | `SchemaVersion`, `VersionedSnapshot`, `SnapshotMigrator` |

### Appendix D.2: Selection Heuristics

1. Start at Tier 1 abstractions first.
2. Descend one tier at a time only when needed.
3. Prefer Tier 18 extension helpers over internal-engine use for bootstrap extensions.
4. Import from root package in consumer code.
5. Avoid Tier 19 (`UiEngine`) in application-layer code.

Shortcuts:

- App setup: `HostApplicationConfig` + `bootstrap_host_application`.
- Cross-feature composition: routed lifecycle specs and helpers.
- Data-heavy UI: virtualization/dataflow before custom loops.
- Durable state: workspace persistence plus snapshot migration.
- Discoverable shortcuts: `ShortcutOverlaySpec` in routed runtime.

### Appendix E: Architecture Templates

Template 1: Small single-scene app

- One scene, few features.
- Observable state and simple action specs.
- Minimal overlays, no task panel required.

Template 2: Multi-window workbench

- Multiple windows with scene menu strip and task panel toggles.
- Presenter-backed windows and routed runtime lifecycle wiring.
- Focus toggle specs for hidden-window safety.

Template 3: Data-heavy analysis tool

- Async providers + proxy sources + virtualization core.
- Cancelable dataflow pipeline for query churn.
- Telemetry enabled for performance baselining.

Template 4: Long-running workflow app

- Cooperative scheduler or operation bus for staged workflows.
- Progress as observables.
- Versioned persistence and migration support.

[Back to Table of Contents](#table-of-contents)

### Appendix F: Specifications and Option Reference

#### Bootstrap and host specs

`HostApplicationBindingSpec`
- Purpose: user-facing bootstrap declaration compiled into `HostApplicationConfig`.
- Key options: `display_size`, `window_title`, `fonts`, `initial_scene_name`, `scene_entries`, `feature_entries`, `window_entries`, `runtime_scene_entries`, `action_entries`, `scene_bundle_entries`, `feature_window_bundle_entries`, `font_role_entries`, `cursor_entries`, `scene_root_entries`, `telemetry`, `target_fps`, `palette_spec`.
- Used in: Quickstart, 8.1.

`HostApplicationConfig`
- Purpose: final bootstrap input consumed by `bootstrap_host_application`.
- Key options: `display_size`, `window_title`, `fonts`, `font_role_specs`, `cursors`, `scene_specs`, `feature_specs`, `window_specs`, `runtime_scene_specs`, `action_specs`, `static_accessibility_specs`, `initial_scene_name`, `scene_roots`, `telemetry`, `target_fps`, `palette_spec`.
- Used in: 8.1, End-to-End Reference.

`SceneBundleBindingSpec`
- Purpose: emits scene setup/runtime/action/root specs from one declaration.
- Key options: scene identity/transition fields, runtime scene fields (`pristine_asset`, `bind_escape_to_exit`, `prewarm`), nav action fields, scene-root fields.
- Used in: Quickstart, 8.1.

#### Feature and routed lifecycle specs

`FeatureSpec`
- Purpose: host attribute + feature factory registration.
- Key options: `attr_name`, `factory`.

`RoutedRuntimeSpec`
- Purpose: declarative control-plane for routed runtime wiring and higher-level faculties.
- Key options:
- Core: `scene_name`, scheduler/scope attribute settings.
- Service/reactive: `service_bindings`, `service_consumers`, `store_subscriptions`, `store_selectors`, `observable_effects`, `signal_effects`.
- Operation: `failure_policies`, `operations`, operation-bus attributes.
- Input/overlay: `action_hotkeys`, `control_key_bindings`, `event_subscriptions`, `shortcut_overlays`, `task_panel_focus_toggles`, `global_pointer_actions`, `command_palette`.
- Advanced faculties: dependency, policy, effect, event pipeline, durable queue, capability, projection, workflow, recompute, QoS, health, replay, and hot-swap specs with runtime attr-name fields.
- Used in: Theory, Core Workflow, 8.2, 8.3, 8.4.

`RoutedFeatureLifecycleSpec`
- Purpose: binds companion providers and runtime spec setup/teardown into one lifecycle object.
- Key options: `companion_providers`, `runtime_spec`, `runtime_spec_factory`, `runtime_spec_attr_name`, `scheduler_attr_name`.
- Used in: Core Workflow, 8.2.

#### Action, input, and event specs

`ActionSpec`
- Purpose: named action declaration.
- Key options: `action_id`, `label`, `kind`, `target`, `category`, `key`.

`ActionHotkeySpec`
- Purpose: bind action handler and optional key/scene scope.
- Key options: `action_name`, `handler`, `key`, `scene_name`.

`ControlKeyBindingSpec`
- Purpose: key-driven control activation.
- Key options: `key`, `control_attr`, `action_name`, `scene_name`.

`EventSubscriptionSpec`
- Purpose: feature-managed event-bus binding.
- Key options: `attr_name`, `topic`, `handler`, `scope`.

#### Window and command-surface specs

`WindowSpec`
- Purpose: feature window presentation mapping.
- Key options: feature/toggle/action/task-panel/accessibility/window-effect fields.

`AnchoredWindowSpec`
- Purpose: anchored presenter-backed window geometry/chrome declaration.
- Key options: `control_id`, `title`, `size`, `anchor`, `margin`, `use_frame_backdrop`.

`FeatureWindowBundleBindingSpec` and `WindowToggleBindingSpec`
- Purpose: shorthand/bundled window toggle declarations.

`SceneTaskPanelSpec`, `TaskPanelSlotLayoutSpec`, `TaskPanelButtonSpec`, `TaskPanelWindowToggleGroupSpec`, `TaskPanelFocusToggleSpec`
- Purpose: optional task-panel creation, slot layout, explicit buttons, auto-toggle grouping, and focus-safe window toggles.

`SceneCommandPaletteSpec` and `PaletteBindingSpec`
- Purpose: per-scene palette activation and built-in/custom entry group composition.

`ShortcutOverlaySpec`
- Purpose: declarative shortcut help overlay setup.
- Key options: overlay attr, dimensions, offsets, toggle action/key fields, manual shortcut lines/sections and inclusion/exclusion controls.

#### Reactive and operation specs

`ServiceBindingSpec` / `ServiceConsumerSpec`
- Purpose: scoped service publication and consumption.

`StoreSubscriptionSpec` / `StoreSelectorSpec` / `ObservableEffectSpec` / `SignalEffectSpec`
- Purpose: lifecycle-owned reactive wiring.

`FailurePolicySpec` / `FeatureOperationSpec`
- Purpose: retry/timeout/publication policy and operation-bus handler declarations.

#### Higher-level runtime faculty specs

`FeatureDependencySpec`, `RuntimePolicySpec`, `EffectBindingSpec`, `EventPipelineStageSpec`, `EventPipelineSpec`, `DurableOperationBindingSpec`, `DurableOperationQueueSpec`, `CapabilityProviderSpec`, `CapabilityRequirementSpec`, `ProjectionNodeSpec`, `ProjectionSpec`, `WorkflowStepSpec`, `WorkflowSpec`, `RecomputeNodeSpec`, `QoSPolicySpec`, `HealthProbeSpec`, `ReplaySpec`, `ReplacePolicySpec`.

- Purpose: declarative admission, effect ownership, stream processing, durable operation recovery, capability negotiation, projection/recompute orchestration, QoS, health monitoring, replay diagnostics, and hot-swap policy.
- Used in: Theory and Core Workflow; chapters 8.9 to 8.16 where relevant.

#### Persistence and migration specs

`RuntimeSceneSpec`
- Purpose: runtime behavior per scene.
- Key options: `scene_name`, `pristine_asset`, `bind_escape_to_exit`, `prewarm`.

`MigrationStepSpec`, `MigrationTargetSpec`, `ContractMigrationSpec`
- Purpose: runtime migration graph declarations for contract payloads.

`NotificationSpec`
- Purpose: pre-seeded notification center records.
- Key options: `message`, `title`, `severity`.

[Back to Table of Contents](#table-of-contents)
