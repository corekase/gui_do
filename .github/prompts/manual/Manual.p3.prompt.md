---
name: Manual.p3
description: Expand Quickstart Path + Architecture + Core Workflow chapters
---

# Manual Step 3 — Quickstart, Architecture, and Core Workflow

## Scope

Replace three consecutive chapter placeholders in `MANUAL.md`:
- `## Quickstart Path (Practice)`
- `## Architecture and Runtime Model`
- `## Core Workflow: Build, Bind, Route, Update, Draw`

## Inventory (Required Before Writing)

1. Read the current content of all three sections in `MANUAL.md` (from the first
   `## Quickstart Path` to just before `## Main Systems Reference`). That is your replace range.
2. Read `gui_do/__init__.py` **Tier 1 and Tier 2** sections to discover current bootstrap,
   spec, and app types for the Quickstart and Architecture chapters.
3. Read `demo_features/demo_config.py` top portion to verify the real bootstrap pattern
   and confirm which field names `HostApplicationConfig` currently uses.
4. Read `docs/architecture_boundary_spec.md` for the boundary model section of the
   Architecture chapter.

Use only names found in the actual files. Do not assume field names or class names.

## Chapter 1: Quickstart Path (Practice)

Write a practical, step-by-step path from installation to a working app. Must include:

### Step 1: Install and Verify
```bash
python -m pip install -e . --no-deps
python -m pytest -q tests/test_public_api_exports.py
```
Note: requires `pygame` and `numpy` (`numpy` is used internally for pixel buffer operations via `PixelArray`).

### Step 2: Create a Minimal Host
Show a complete `HostApplicationConfig` construction with all required fields. Use real field names.
Key fields: `display_size`, `window_title`, `fonts`, `font_role_specs`, `cursors`, `scene_specs`,
`feature_specs`, `window_specs`, `runtime_scene_specs`, `action_specs`,
`static_accessibility_specs`, `initial_scene_name`.

### Step 3: Add a Feature with Observable State
Show a minimal `Feature` subclass with `__init__`, `build`, `bind_runtime`, and `shutdown_runtime`
methods. The feature should create an `ObservableValue`, a `LabelControl`, and wire them with a
subscription.

Also include one concise note or snippet showing the routed declarative equivalent using runtime
effect specs (for example `StoreSubscriptionSpec` or `ObservableEffectSpec`) and mention that
teardown is handled via routed runtime shutdown.

### Step 4: Add an Action and Runtime Scene Policy
Show adding an `ActionSpec` and `RuntimeSceneSpec` to the config. Include `bind_escape_to_exit`.

### Step 5: Run Loop
Show a host class that calls `bootstrap_host_application` and then `self.app.run_entrypoint(target_fps=120)`.

### Guided Build Track (Beginner)
Six-milestone progression:
- A: app boots to a single scene with no errors
- B: one feature creates one visible control
- C: one observable updates one control reactively
- D: one action and one hotkey trigger expected behavior
- E: one overlay and one toast route without input leakage
- F: workspace save/load roundtrip succeeds

Beginner confidence checklist:
- you can explain where `build` ends and `bind_runtime` begins
- you can add/remove one feature through specs only
- you can trace one keypress through routing to action execution

### Quickstart Failure Modes
Cover the four most common early failures with specific fixes:
- feature never appears → verify `feature_specs` + scene name match
- hotkey does nothing → verify action descriptor + input binding scope
- overlay blocks unexpected keys → check `consume_unhandled_keys` and dismissal settings
- state updates but UI does not → ensure subscription in `bind_runtime` not disposed early

---

## Chapter 2: Architecture and Runtime Model

Write substantial prose for each subsection:

### Boundary Model: Framework vs Consumer
- `gui_do/`: reusable framework code (runtime, controls, events, layout, state, persistence, etc.)
- `demo_features/` and `gui_do_demo.py`: consumer integration layer
- Hard rule: `gui_do/` must not import from `demo_features/`
- Consumer entrypoints import from `gui_do` root, never from `gui_do.*` internal modules
- Enforced by `tests/test_boundary_contracts.py`

### Tiered Public API Model
Explain the tier model in detail. Describe the purpose of each tier group:
- Tier 1: lifecycle + data-driven runtime specs and bootstrap (start here for all new apps)
- Tier 2-7: core app, data/state, events/actions, scheduling, theme, telemetry
- Tier 8+: layout, overlays, forms, state/persistence, controls, graphics, introspection, etc.

Explain that tier number indicates recommended approach order: when two tiers offer overlapping
capability, use the lower-numbered (more abstract) tier first.

### Runtime Guarantees
List and explain each contractual guarantee:
- Canonical `GuiEvent` normalization before app-level dispatch
- Scene-isolated update execution for scene-contained runtime systems
- Deterministic candidate ordering for window focus cycling (sorted by `control_id`)
- Scheduler dispatch budget clamping: fraction=0.12, floor=0.5 ms, ceiling=4.0 ms
- Missing settings keys are skipped without aborting workspace restore

### Event Pipeline
Describe the full `GuiApplication.process_event` flow in order:
1. Normalize raw input to `GuiEvent`
2. Handle quit events early
3. Update shared input state
4. Update logical pointer state; apply pointer lock/capture clamping
5. Logicalize pointer events while preserving raw coordinates
6. Route overlays/toasts/focus management
7. Route keyboard events through keyboard manager and screen handler policy
8. Route feature handlers, scene dispatch, then fallthrough handlers
9. Respect `propagation_stopped` and `default_prevented` as hard stop signals

### Known Non-Goals
Brief list of what gui_do intentionally does not aim to do:
- OS-native widget parity across all platforms
- Replace domain-layer architecture decisions for application business logic
- Expose internal infrastructure tiers as beginner entry points
- Make star-import behavior part of public API compatibility

---

## Chapter 3: Core Workflow: Build, Bind, Route, Update, Draw

Write prose that explains how the five phases form a complete application programming model.

### Phase Reference
Detailed description of each phase and its invariants:
- **build**: instantiate controls, initialize local observables, declare static structure.
  Invariant: no subscriptions, no runtime dependencies should be wired here.
- **bind_runtime**: attach all host-dependent wiring — actions, subscriptions, cross-feature refs.
  Invariant: all siblings are built; controls exist; safe to subscribe.
- **route**: consume messages and events through declared mappings and handlers.
- **update**: execute frame-based logic, scheduled workloads, per-frame state transitions.
- **draw**: custom render pass for anything controls cannot express.

### Message and Logic Coordination
- Describe `FeatureMessage` publishing and how features communicate without direct coupling.
- Describe `LogicFeature` as the coordination hub for shared state.
- Explain when to use observable state vs messages for cross-feature communication.

### When to Use Routed Runtime Specs
Explain `RoutedRuntimeSpec` and `RoutedFeatureLifecycleSpec` — when they reduce boilerplate:
- Multiple action hotkeys for one feature
- Shortcut overlays tied to feature lifecycle
- Task-panel focus toggles
- Event subscriptions with auto-cleanup

Include a prose explanation of `bind_routed_feature_lifecycle` and `shutdown_routed_feature_lifecycle`.

Explicitly include the newer routed runtime facilities:
- service publication/consumption specs
- reactive effect specs
- operation/failure-policy specs and operation bus behavior

---

## Replace Target

Replace from the line containing:
```
## Quickstart Path (Practice)
```
through to (but not including) the line containing:
```
## Main Systems Reference
```

Include the `## Quickstart Path (Practice)` heading in your output.
