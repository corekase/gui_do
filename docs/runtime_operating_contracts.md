# Runtime Operating Contracts

## Purpose

Define final operating contracts for the data-driven GUI runtime so release quality can be measured and enforced.

## 1. System Guarantees

The runtime guarantees these behaviors:

- Canonical event normalization to GuiEvent before app-level dispatch.
- Scene-isolated update execution for scene-contained runtime systems.
- Deterministic candidate ordering for window focus cycling.
- Scheduler dispatch budget clamping with fixed min and max bounds.

## 2. Cross-System Behavior Contracts

The runtime must preserve these system interactions:

- Action routing honors scene scope and window-only scope precedence.
- Workspace restore can switch scene, replay feature state, restore scene snapshots, and replay settings.
- Application workspace facade methods return restore reports (GuiApplication.restore_workspace and GuiApplication.load_workspace).
- Missing settings keys are skipped without aborting restore.

## 3. Determinism and Safety Rails

Required deterministic policies:

- Window focus candidates are sorted by control_id.
- Key binding dispatch uses a stable candidate order based on scene and window scope.
- Scheduler dispatch budget math is clamped to fixed bounds.

Safety rails:

- Unknown settings keys are skipped during restore replay.
- Missing settings blocks are tracked in restore summaries.

## 4. Observability and Diagnostics

The runtime exposes:

- Telemetry spans in high-frequency app paths.
- A structured restore summary via WorkspacePersistenceManager.restore.

The restore report includes:

- target_scene
- switched_scene
- restored_feature_states
- restored_scene_nodes
- applied_settings
- skipped_settings
- missing_settings_blocks

## 5. Public Surface Stability Policy

The gui_do root import is treated as the stable consumer API.

Stable extension abstractions for demo composition include:

- ActiveTabUpdateRouter
- TabLayoutContext
- FeatureSpec
- WindowSpec
- RuntimeSceneSpec
- ActionSpec
- TabBuilderSpec
- AnchoredWindowSpec
- bootstrap_host_application

## 6. Performance Budgets

Scheduler message dispatch budget contract:

- fraction: 0.12 of dt milliseconds
- floor: 0.5 ms
- ceiling: 4.0 ms

This gives predictable upper bounds under slow frames and avoids starvation under fast frames.

## Release Gate

A release is considered final-ready only when:

- runtime guarantees tests pass,
- cross-system integration tests pass,
- docs contracts pass,
- full test suite passes.
