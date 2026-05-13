---
name: Manual.p6
description: Expand Main Systems chapters 9–12 (Scene/Window, Scheduling, Persistence, Theme)
---

# Manual Step 6 — Systems 9–12

## Scope

Replace four system chapter placeholders:
- `### Scene, Window, and Task-Panel Presentation Models` (8.9)
- `### Scheduling, Timing, Animation, and Transitions` (8.10)
- `### Persistence and Workspace/Session State` (8.11)
- `### Theme, Styling, and Visual Systems` (8.12)

Replace from `### Scene, Window, and Task-Panel Presentation Models` through to (but not
including) `### Text, Input, Forms, and Validation Systems`.

## Inventory (Required Before Writing)

1. Read the current text of these four sections in `MANUAL.md`.
2. Read `gui_do/__init__.py` **Tier 18** (scene/window presentation helpers), **Tier 5**
   (scheduling and animation), **Tier 11** (state and persistence), **Tier 23** (undo),
   **Tier 32** (snapshot/migration), **Tier 6** (theme/font), and **Tier 22** (theme
   invalidation) sections. Extract all exported names from each tier block.
3. Read `docs/runtime_operating_contracts.md` sections 2, 4, and 6 — Section 4 gives
   workspace restore report fields; Section 6 gives scheduler budget values (fraction/floor/ceiling).

Use only names found in the actual `gui_do/__init__.py` tier blocks. For runtime constants
(scheduler budget), use the values from `docs/runtime_operating_contracts.md` Section 6 —
do not hardcode values that may have changed.

## Standard Chapter Template

Every chapter: What/why · Mental model · Primary APIs · Typical usage flow · Minimal example ·
Advanced pattern · Common mistakes · Cross-links · `[Back to Table of Contents](#table-of-contents)`

---

## 8.9 — Scene, Window, and Task-Panel Presentation Models

**What/why:** Scenes define broad interaction contexts; windows define focused work surfaces
within a scene; task panels expose discoverable commands. This system coordinates what is
visible, what has focus, and which actions are available at any moment.

**Mental model:** Think of scenes as top-level "modes" of the application (e.g., main desktop vs
control showcase). Within a scene, windows are floating or docked UI surfaces that can be
individually shown/hidden. The task panel is a persistent chrome element that houses toggle
buttons for windows and navigation. Menu strips expose scene-navigation and window commands.

**APIs (Tier 1 Spec types and Tier 18 helpers from `gui_do/__init__.py`):**
Use the window/scene spec types from TIER 1 (`ScenePresentationModel`, `WindowPresenter`,
`WindowSpec`, `AnchoredWindowSpec`, `SceneTaskPanelSpec`, `TaskPanelButtonSpec`,
`TaskPanelFocusToggleSpec`, `FeatureWindowBundleBindingSpec`, `WindowToggleBindingSpec`,
`TabbedPresenterSpec`, `TabBuilderSpec`) and the window presentation helpers from TIER 18
(`set_window_visible_state`, `toggle_window_visibility`, `create_anchored_feature_window`,
`create_feature_presented_window`, `add_window_scene_menu_strip`, `ensure_scene_task_panel`,
`ActiveTabUpdateRouter`, `TabLayoutContext`, etc.). Always verify names in `__init__.py`
\u2014 new helpers may have been added.

**`ScenePresentationModel`:** Tracks which windows are registered in a scene and their
visibility state. Provides `handle_window_toggle` for menu strip integration.

**`WindowPresenter`:** Base class for window-level UI construction. Subclass it to own the
layout and control creation for a floating window. The Feature class instantiates it in
`build` and delegates all window-internal concerns to it.

**`AnchoredWindowSpec`:** Defines a window's size, anchoring strategy, and chrome properties.
Use with `create_anchored_feature_window` or `FeatureWindowBundleBindingSpec`.

**`TabbedPresenterSpec` + `TabBuilderSpec`:** Declaratively specify tabbed window content.
`TabBuilderSpec` provides the factory for each tab's control tree. `ActiveTabUpdateRouter`
efficiently routes updates only to the active tab's presenter.

**`TaskPanelFocusToggleSpec`:** When a window is shown/hidden, this spec automatically
excludes/includes the window's controls in the focus ring, prevents focus-cycling stalls,
and registers the appropriate action and hotkey.

**Typical usage:**
1. Declare `WindowSpec` or `AnchoredWindowSpec` in config.
2. Implement `WindowPresenter` subclass for window-internal layout.
3. Use `FeatureWindowBundleBindingSpec` to wire feature + window + task panel in one spec.
4. Set `TaskPanelFocusToggleSpec` in `RoutedRuntimeSpec` to auto-manage focus on toggle.

**Minimal example:** `create_feature_presented_window` call showing a simple anchored window.

**Advanced pattern:** Multi-window scene with `TabbedPresenterSpec` + `TabBuilderSpec` for
tabbed content inside each window, `ActiveTabUpdateRouter` for efficient tab-change routing,
and `ScenePresentationModel.handle_window_toggle` wired to the scene menu strip.

**Mistakes:** Mismatching scene scope and window scope for action handlers; not synchronizing
task panel button state with window visibility; creating windows in `bind_runtime` instead of
`build` (window controls must exist when sibling features bind).

Also include operation-bus usage guidance for scene-local window/task-panel actions that need
retry/timeout/failure publication semantics.

**Cross-links:** 8.2 (Feature lifecycle), 8.5 (Controls), 8.7 (Focus), 8.8 (Overlays)

---

## 8.10 — Scheduling, Timing, Animation, and Transitions

**What/why:** Time-based work (animations, timed callbacks, cooperative background tasks)
must execute within frame budgets. gui_do provides a layered scheduling system from simple
timers up to full cooperative coroutine scheduling.

**Mental model:** The scheduler is a per-scene resource. Frame time is divided: the scheduler
runs each frame but cannot exceed its budget (fraction=0.12 of dt ms, floor=0.5 ms,
ceiling=4.0 ms). Animations and tweens are registered once and tick automatically each frame.

**APIs (Tier 5 from `gui_do/__init__.py`):**
Use all names discovered from the TIER 5 section in the inventory step. This tier covers
the scheduler, tweens, animations, transitions, animation state machine, scene timeline,
debouncers/throttlers, and cooperative scheduler with all its yield primitives. Check
`__init__.py` for any new scheduling types added since the last generation.

**Cancelable Dataflow Pipeline (Tier 26 from `gui_do/__init__.py`):**
Use all names from the TIER 26 section. Cross-reference with 8.14 (Data chapter).

**`TweenManager`:** Interpolates a named property on an object from current to target value
over a duration, using an `Easing` function.
`TweenHandle` lets you cancel or chain tweens.

**`AnimationStateMachine`:** State-machine-driven animation — declare states and transitions;
the machine drives `AnimationSequence` instances based on current state.

**`CooperativeScheduler`:** Runs Python generator-based coroutines that yield control at safe
points using yield primitives. The scheduler resumes coroutines each frame within budget.
Use for multi-step workflows that span multiple frames without blocking the UI thread.

**`SceneTimeline`:** Drives a sequence of timed events relative to scene entry. Useful for
tutorial flows and scripted demo sequences.

**`Debouncer` and `Throttler`:** Rate-limit callbacks — `Debouncer` fires only after a quiet
period; `Throttler` fires at most once per interval. Use for search inputs and resize handlers.

**Scheduler budget contract:** Read values from `docs/runtime_operating_contracts.md` Section 6
(do not hardcode values here — use the current values from the doc).

**Typical usage:**
```python
# Tween a control's alpha on show:
self._tween = host.tweens.to(self.panel, "alpha", 255, duration=0.2)

# Cooperative coroutine:
def my_workflow(host):
    yield Sleep(1.0)
    host.toasts.show("Done!")
host.scheduler.run(my_workflow(host))
```

**Minimal example:** `TweenManager` fade-in on button click.

**Advanced pattern:** `CooperativeScheduler` coroutine that `WaitForSignal` on a user
confirmation, then continues a multi-step workflow — all within the frame budget, no threads.

**Mistakes:** Unbounded work per frame in `on_update` (blocks rendering); creating coroutines
with blocking I/O inside (use `DataflowPipeline` for that); not canceling tweens on scene exit
(stale tweens apply mutations to dead controls).

Add one focused subsection connecting timer-backed operation failure policies to scheduling
semantics (timeouts/retries as first-class scheduled work).

**Cross-links:** 8.2 (Feature lifecycle — `on_update`), 8.14 (Data pipeline), 8.16 (Telemetry)

---

## 8.11 — Persistence and Workspace/Session State

**What/why:** Users expect their session to survive application restarts. gui_do provides a
workspace persistence layer that saves and restores scene state, feature state, window
positions, and settings, with a robust restore-report contract.

**Mental model:** The workspace is a JSON snapshot of the session at a save point. On restore,
the runtime switches to the saved scene, replays feature states, restores scene snapshots,
and replays settings. Unknown keys are skipped, not fatal. The restore report tells you exactly
what was applied, skipped, or missing.

**APIs (Tier 11 from `gui_do/__init__.py`):**
Use all names discovered from the TIER 11 section in the inventory step. Covers persistence
(workspace, settings, scene/node snapshots) and state management (command history,
state machines, router).

**Snapshot & Migration (Tier 32 from `gui_do/__init__.py`):**
Use all names from the TIER 32 section. Check `__init__.py` for any migration API additions.

**Also include (Tier 23 from `gui_do/__init__.py`):**
Use names from the TIER 23 section (undo context).

**Restore report fields:** Read from `docs/runtime_operating_contracts.md` Section 4.
Do not hardcode field names here — use the current fields from the doc.

**`SnapshotMigrator`:** BFS migration graph — register `MigrationStep` objects that transform
a `VersionedSnapshot` from version N to N+1. On load, the migrator walks the registered steps
to bring an old snapshot up to the current schema before passing it to the runtime.

**`SettingsRegistry`:** Named settings with `SettingDescriptor` — type, default, validation.
Registered settings participate in workspace save/restore.

**`CommandHistory`:** Undo/redo stack. `Command` is an executable+undoable action pair.
`CommandTransaction` groups multiple commands into a single undo step.

**`UndoContextManager` (Tier 23):** Named multi-stack undo/redo routing. Different UI panels
can have their own independent undo stacks, all routed through a single manager.

**Typical usage:**
```python
# Save:
host.app.save_workspace(path)

# Load:
report = host.app.load_workspace(path)
if report and report.skipped_settings:
    host.toasts.show("Some settings could not be restored")
```

Include persistence-operation guidance showing how save/restore actions can be modeled as
declarative feature operations with failure policies.

**Minimal example:** Full save/load cycle with restore report inspection.

**Advanced pattern:** Versioned snapshots with `SnapshotMigrator` — when schema evolves,
register migration steps to transform old snapshots forward. `SettingsRegistry` with
`SettingDescriptor` for typed, validated settings that automatically round-trip through
workspace save/restore.

**Mistakes:** Assuming all settings keys always exist (use restore report to detect missing);
restoring snapshots without version checks (always call `read_version` first); using
`DEFAULT_WORKSPACE_STATE_PATH` in multi-instance scenarios without per-instance paths.

**Cross-links:** 8.1 (Bootstrap), 8.2 (Feature lifecycle — `shutdown_runtime`), 8.16 (Telemetry)

---

## 8.12 — Theme, Styling, and Visual Systems

**What/why:** Theming centralizes design tokens, colors, and font roles so that changing the
visual style does not require touching individual controls or features.

**Mental model:** The `ThemeManager` holds the active theme. `DesignTokens` provide named
values (colors, sizes, radii) that controls read at render time. `FontRoleRegistry` maps
semantic role names (e.g., "heading", "body", "caption") to font configurations. When the
theme changes, `ThemeInvalidationBus` notifies all registered caches to flush.

**APIs (Tier 6 and Tier 22 from `gui_do/__init__.py`):**
Use all names from TIER 6 (theme, font, design tokens, scoped theme) and TIER 22 (theme
invalidation bus) discovered in the inventory step. Check `__init__.py` for any new theme
types added since the last generation.

**Specs (from Tier 1 discovery):** `FontRoleBindingSpec`, `CursorSpec`, `CursorBindingSpec` —
verify these still appear in the Tier 1 block.

**`ColorTheme`:** A named set of color mappings from semantic roles to RGBA values.

**`DesignTokens`:** Named scalar or color values that controls and features query at render
time. Centralizes all magic numbers (border radii, spacing, icon sizes).

**`ScopedTheme` and `ScopedThemeManager`:** Apply a local theme override to a subtree.
Useful for windows that should look different from the main scene (e.g., a dark sidebar in a
light-themed app).

**`ThemeInvalidationBus`:** Broadcast channel — when the active theme changes, all subscribers
(typically cached rendered surfaces) receive an invalidation signal and must re-render.
Register caches here rather than polling the theme manager.

**`setup_standard_font_roles`:** Convenience function to register a standard set of font roles
from a font config dictionary.

**Typical usage:**
1. Declare `fonts` dict in `HostApplicationConfig` with named font configurations.
2. Use `FontRoleBindingSpec` entries to map semantic roles to font configurations.
3. Controls read font roles by name; they automatically pick up the right font.
4. On theme switch, call `host.theme_manager.set_theme(name)` — `ThemeInvalidationBus`
   handles cache flush.

**Minimal example:** Declaring two font roles and referencing them in controls.

**Advanced pattern:** `ScopedThemeManager` for per-window theme overrides; `ThemeInvalidationBus`
subscription in a custom control that caches rendered text surfaces.

**Mistakes:** Hardcoding color literals in feature or control draw code (breaks theme switching);
changing theme without invalidating surface caches (stale colors persist); registering fonts
outside the config phase (font role registry may not be initialized yet).

**Cross-links:** 8.1 (Bootstrap — font config), 8.5 (Controls — rendering), 8.16 (Telemetry)

---

## Replace Target

Replace from the line containing:
```
### Scene, Window, and Task-Panel Presentation Models
```
through to (but not including) the line containing:
```
### Text, Input, Forms, and Validation Systems
```

Include the `### Scene, Window, and Task-Panel Presentation Models` heading in your output.
