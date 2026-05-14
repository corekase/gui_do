---
name: DemoDeploy
description: Auto-discover controls and systems from the live codebase at invocation time, then integrate missing items into the controls showcase and systems demo
---

## Role

You are an agent. Execute all steps below sequentially. Gather evidence from the live codebase before writing any code. Do not reference MANUAL.md or any pre-compiled list of controls or systems — discover everything directly from source at invocation time.

## Objective

1. Discover every control type and every runtime system available in the current `gui_do` package by reading the codebase.
2. Identify which controls are missing from the showcase and which runtime systems are missing from the demo.
3. Implement all gaps: missing controls go into the appropriate showcase tab; missing systems go into the Systems demo window or into the most appropriate existing demo feature.

## Step 1 — Auto-Discover Controls

Read `gui_do/__init__.py` and collect every exported name that ends in `Control` or that is documented as a user-facing interactive or display widget (e.g. labels, inputs, panels, sliders, canvases, dropdowns, list views, progress bars, chips, color pickers, tooltips, etc.). Do not hardcode a list here — extract the names from the actual file.

Then audit the showcase feature to determine which of those controls already appear. The showcase lives under `demo_features/showcase/`. Read the helper files (`showcase_basics_helpers.py`, `showcase_extended_helpers.py`, `showcase_advanced_helpers.py`, `showcase_data_helpers.py`, and any other `showcase_*_helpers.py` present) and the specs file (`showcase_specs.py`) to enumerate what is already placed in the grid.

A control is considered **present** in the showcase only if it is actually instantiated (not merely imported) in one of those files.

Produce an explicit gap list: controls present in `gui_do/__init__.py` but not instantiated in any showcase helper file.

## Step 2 — Auto-Discover Runtime Systems

Read `gui_do/__init__.py` and collect every exported spec or runtime class related to routed runtime faculties. The canonical groupings to look for include (but are not limited to) the following families — discover the actual names from the source:

- Execution context propagation
- Workload budget/arbitration
- Checkpoint and recovery
- Saga compensation and orchestration
- Reactive dependency graph
- Contract migration
- Workflow orchestration
- Derived-state recompute
- QoS policy / backpressure
- Feature health monitoring
- Replay and diagnostics capture
- Hot-swap / replace policy
- Runtime policy engine
- Effect lifetime ownership
- Event pipeline (staged transform/filter/shape)
- Durable operation queue
- Capability contracts / negotiation
- Incremental projection

For each family, check whether a demonstration exists in the systems demo (`demo_features/systems/`) or any other demo feature. Read the systems feature file (`systems_feature.py`) and its helper modules to inventory what is already exercised.

A system family is considered **present** if it is instantiated and its spec/runtime is used in a non-trivial way (not just imported).

Produce an explicit gap list: system families whose spec/runtime classes exist in `gui_do/__init__.py` but are not demonstrably used in any demo feature.

## Step 3 — Plan the Implementation

For the control gaps:
- Assign each missing control to the appropriate showcase tab based on its functional category:
  - **Basics tab**: fundamental input and display controls (buttons, labels, text inputs, checkboxes, radio, sliders, progress bars, scrollbars).
  - **Extended tab**: richer input and composite controls (dropdowns, list views, tree views, color pickers, chip inputs, toggle groups, date/time pickers, spinners, segmented controls, rating controls).
  - **Advanced tab**: graphics, canvas, camera, particle layer, scene graph, tile map, image controls.
  - **Data tab**: data-bound controls, collection views, virtualized windows, grids.
  - If a control does not fit any existing tab, place it in the most semantically appropriate tab and note the rationale in a comment.
- Each control must be shown in a realistic context (not just instantiated with defaults). Show an observable binding, an event callback, or a non-trivial initial value where it improves clarity.

For the system gaps:
- If a system maps naturally to an existing Systems tab (e.g., infrastructure, motion, data, scheduling, persistence, state, history, theme, graphics, validation, text), add it to that tab's helper module.
- If a system does not fit any current Systems tab cleanly, add a new tab to the Systems demo window, with a corresponding `systems_*_helpers.py` file and an entry in the Systems presenter/specs.
- If a system is better demonstrated inside another demo feature (e.g., a scheduling system fits inside the moving-shapes feature), integrate it there instead and leave a cross-reference comment.

## Step 4 — Implement Control Gaps

For each missing control:

1. Open the relevant showcase helper file (`showcase_basics_helpers.py`, `showcase_extended_helpers.py`, `showcase_advanced_helpers.py`, or `showcase_data_helpers.py`).
2. Add the control to the appropriate grid column section following the existing placement pattern (label + control, within a column layout using the column's `Rect` helpers).
3. If the control requires a new observable, declare it alongside the section where it is placed and clean it up in `shutdown_runtime`.
4. If placing the control requires changes to `showcase_specs.py` (e.g., adding a new constant), update that file first.
5. If a new showcase helper file is needed for a new functional group, create it following the `showcase_*_helpers.py` naming convention and wire it into `showcase_feature.py`.

Follow the column layout conventions already present in each helper file exactly — use the same `Rect`-based placement, the same label height constants, and the same row-gap values. Do not introduce a new layout system unless the existing approach is fundamentally inadequate for the new control.

## Step 5 — Implement System Gaps

For each missing system family:

1. Determine the target helper module in `demo_features/systems/` (existing or new).
2. In the helper module, add a `build_<system>_section` (or equivalent) function that:
   - Instantiates the relevant spec and runtime classes using names discovered from `gui_do/__init__.py`.
   - Wires them into the feature using `setup_routed_runtime` / `RoutedRuntimeSpec` where applicable.
   - Adds a small label, status display, or interactive button that exercises the system and shows output.
   - Stores any runtime instances on the feature object for use in `on_update` or `shutdown_runtime`.
3. Call `build_<system>_section` from the appropriate Systems tab build function (or from the new tab's build function).
4. In `systems_feature.py`, call any required per-update method (e.g., `pump()`, `begin_update()`, `run_probes()`) inside the feature's `on_update`.
5. In `systems_feature.py`'s `shutdown_runtime`, call `dispose()` on every runtime instance created for the system and invoke `shutdown_routed_runtime` if a `RoutedRuntimeSpec` was used.

## Constraints and Conventions

### Code Layout (Demo Feature Layout Standard)

Read `docs/demo_feature_layout.md` at invocation time. The rules found there are the authoritative layout standard for all new and modified demo feature code. The summary below reflects those rules; if the file and this summary conflict, the file takes precedence.

The Demo Feature Layout Standard applies to all code that lives under `demo_features/`. It does **not** apply to `gui_do/` itself — internal library systems, runtime classes, and spec types that live inside `gui_do/` are not features and are therefore not forced to conform to these feature layout standards.

- New code belongs inside the feature folder being updated (`demo_features/showcase/` or `demo_features/systems/`), not in unrelated modules.
- Each feature package keeps a clean `__init__.py` with no compatibility shims.
- UI/runtime Feature classes → `*_feature.py`.
- Companion LogicFeature classes → `*_logic_feature.py`.
- Declarative specs and composition data → `*_specs.py`.
- Presenters/adapters → `*_presenter.py`.
- Tab-specific helpers → `*_helpers.py` (named after the tab topic).
- The `demo_features/` root is limited to bootstrap-facing files (`demo_config.py`, `__init__.py`, `data/`, feature folders).
- If a new demo feature package is needed, create a new folder under `demo_features/` with its own `__init__.py`, at least one `*_feature.py`, and at least one `*_specs.py`. Register it in `demo_config.py`.

### Routed Runtime Facilities

When demonstrating a runtime system that participates in routed feature wiring, prefer the following patterns (use names discovered from `gui_do/__init__.py` at invocation time):

- Declare a `RoutedRuntimeSpec` with the relevant sub-specs; call `setup_routed_runtime` in `bind_runtime` and `shutdown_routed_runtime` in `shutdown_runtime`.
- Use `ServiceBindingSpec` / `ServiceConsumerSpec` for scene-local service access.
- Use `StoreSubscriptionSpec`, `StoreSelectorSpec`, `ObservableEffectSpec`, `SignalEffectSpec` for reactive wiring.
- Use `FeatureOperationSpec` + `FailurePolicySpec` for operations that need timeout/retry/failure reporting.
- Use the higher-level runtime spec families (workflow, recompute, QoS, health, replay, policy, effect, pipeline, durable queue, capability, projection, execution context, budget, checkpoint, saga, reactive graph, migration) exactly as exported — do not hard-code class names that were not confirmed to exist in `gui_do/__init__.py` at the time of execution.

### Subscription and Lifecycle Safety

- Every `bind_runtime` subscription must have a corresponding `shutdown_runtime` cleanup.
- Every runtime manager instance created in `build` or `bind_runtime` must be disposed in `shutdown_runtime`.
- Routed runtime teardown (`shutdown_routed_runtime`) must be called before feature-local disposal when both are used.
- Do not leave dangling observable callbacks or timer handles across scene transitions.

### Realism Over Boilerplate

- Show data flowing through observables to controls — avoid controls that display only hard-coded strings.
- For system demos, show a state transition, a computation result, or a UI update that would not be visible without the system being active.
- Avoid toy examples; aim for patterns a developer could extract and adapt.
- Where a minimal realistic example is not feasible, add a clearly commented placeholder that describes what a full integration would look like.

### Quality Gates (Must Pass Before Finishing)

1. Every control exported from `gui_do/__init__.py` and ending in `Control` (or identified as a user-facing widget) is instantiated in at least one showcase helper file.
2. Every runtime system family that exports a spec and a runtime class in `gui_do/__init__.py` is exercised in at least one demo feature.
3. No stale import names — all names used in demo code are confirmed to exist in `gui_do/__init__.py` at execution time.
4. All `bind_runtime` subscriptions have matching `shutdown_runtime` cleanup.
5. All new or modified files follow the Demo Feature Layout Standard (correct module type, correct folder, correct naming).
6. The showcase tabs remain logically grouped and navigable after new additions.
7. The Systems demo window remains organized: each system family appears in exactly one tab or is cross-referenced to the demo feature where it is integrated.
