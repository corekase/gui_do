---
name: Manual.p8
description: Expand Testing/Diagnostics, Performance, Migration, FAQ, and all Appendices
---

# Manual Step 8 — Reference Tail Chapters + Appendices

## Scope

Replace placeholders for:
- `## Testing, Diagnostics, and Reliability`
- `## Performance and Scaling Guidance`
- `## Migration, Versioning, and Deprecation Notes`
- `## FAQ and Troubleshooting`
- `## Appendix`

Replace from `## Testing, Diagnostics, and Reliability` through the end of the file.

## Inventory (Required Before Writing)

1. Read the current content of these sections in `MANUAL.md` (from
   `## Testing, Diagnostics, and Reliability` to end of file).
2. Read `docs/runtime_operating_contracts.md` all sections:
   - Section 4: workspace restore report fields
   - Section 5: stability policy
   - Section 6: scheduler budget values (fraction/floor/ceiling) — use these exact values,
     do not hardcode values from prior runs
3. **List the `tests/` directory** and filter for `test_*_contracts.py` and
   `test_runtime_*` filenames. Use the actual file names found; do not assume filenames.
4. Read `gui_do/__init__.py` **Tier 7** (telemetry), **Tier 17** (introspection), **Tier 16**
   (graphics/debug overlay), and **Tier 32** (snapshot/migration) for API names used in
   the testing, diagnostics, and migration chapters.
5. Read `gui_do/__init__.py` completely to build the Appendix D.1 Tier-to-System matrix.
   The matrix must reflect the actual tiers in `__init__.py` — if new tiers exist beyond
   the previous highest tier, include them as rows.

For the Appendix D Quick Index: read all tier sections from `gui_do/__init__.py` and use
that as the authoritative source of names. Do not use names from prior MANUAL.md content
without verifying they still appear in the actual `__init__.py` export.

---

## Chapter: Testing, Diagnostics, and Reliability

Write full prose for all subsections. Include the Maintainer Diff Checklist as a required
subsection (see `#prompt:manual/Manual.p1.prompt.md` for its required content).
Do NOT write a Manual Conformance Report section — this is an internal pipeline artifact
and must not appear in the published output.

### Contract Tests
Explain what the contract test suite validates and how to run it:
```bash
python -m pytest -q tests/test_public_api_exports.py tests/test_public_api_docs_contracts.py tests/test_runtime_operating_contracts.py tests/test_boundary_contracts.py tests/test_gui_application_workspace_contracts.py
```
Explain what each test file covers:
- `test_public_api_exports.py`: verifies all `__all__` names are importable and present.
- `test_public_api_docs_contracts.py`: verifies API names match contract documentation.
- `test_runtime_operating_contracts.py`: verifies runtime guarantees (scheduler budget,
  event normalization, scene isolation, deterministic candidate order).
- `test_boundary_contracts.py`: verifies the gui_do/demo boundary (no reverse imports).
- `test_gui_application_workspace_contracts.py`: verifies workspace restore behavior.

### Runtime Behavior Tests
Target areas: workspace load/save behavior, overlay/tooltip/cursor routing, layout and
animation determinism, control runtime, accessibility specs.

Also include runtime-facility test coverage expectations:
- service/effect registration and cleanup behavior
- operation retry/timeout/failure publication behavior
- routed teardown disposal guarantees

### Debug and Trace Tools
- `EventRecorder`/`EventPlayback` for reproducible input traces and regression reproduction.
- `DebugOverlay` for visual control-tree state inspection.
- `PropertyInspectorPanel` for runtime property inspection.
- Telemetry log analysis (`analyze_telemetry_log_file`, `render_telemetry_report`) for
  frame-budget and pipeline profiling.

### Maintainer Release Runbook
Step-by-step release gate sequence — see spec in `#prompt:manual/Manual.p1.prompt.md`.

### Regression Triage Workflow
Triage sequence: reproduce → trace → localize → test-first → patch → adjacent contracts.

### Maintainer Diff Checklist
Full four-category checklist (inventory delta, content integrity, navigation, operational) —
see spec in `#prompt:manual/Manual.p1.prompt.md`.

`[Back to Table of Contents](#table-of-contents)`

---

## Chapter: Performance and Scaling Guidance

### Scheduler Budget Contract
State the contract values read from `docs/runtime_operating_contracts.md` Section 6
(fraction, floor, ceiling) and explain their purpose: upper bound under slow frames, no
starvation under fast frames. Do not hardcode values here — read the doc.

### Dirty-Region Rendering
Explain `DirtyRegionTracker` as the primary frame-rate optimization for complex scenes.
Describe the incremental union cache: `overlaps_dirty()` is O(1) because the tracker maintains
a running union rect; iterating all dirty rects per overlaps check is avoided.

### Virtualization and Incremental Rendering
- `VirtualizationCore` and `VirtualizedWindow` for large datasets.
- `ListDiffCalculator` for minimal update sets rather than full redraws.
- `RecyclePool` for item view reuse.

### Practical Scaling Checklist
- Enforce scene-scoped updates and handlers.
- Avoid per-frame full collection reallocation (use `ObjectPool` for high-churn types).
- Debounce expensive form and search operations with `Debouncer`.
- Use `DataflowPipeline` + `CancellationToken` for preemptible background work.
- Profile representative user interactions, not synthetic idle scenarios.
- Use `DirtyRegionTracker` to gate expensive draw regions.

`[Back to Table of Contents](#table-of-contents)`

---

## Chapter: Migration, Versioning, and Deprecation Notes

### Versioned Snapshot Strategy
Explain the recommended workflow using `SnapshotMigrator`:
1. Write snapshot with `make_snapshot(current_version, state_dict)`.
2. On load, call `read_version(raw)` to get the stored version.
3. Pass to `SnapshotMigrator.migrate(snapshot)` which applies registered `MigrationStep` objects
   in BFS order to reach the current schema version.
4. Restore the migrated snapshot into the runtime.

Explain that migration steps are registered on `MigrationRegistry` and are one-directional
(each step knows its source and target version). `MigrationError` is raised for unresolvable paths.

### Deprecation Handling
Recommended policy:
- Prefer additive transitions: add new fields/parameters, keep old ones with deprecation warnings.
- Remove legacy behavior only after providing a migration path.
- Centralize deprecation notes in this section.

State that no deprecated public APIs are cataloged as of the time of this generation. Maintainers should
add entries here when formal deprecations are introduced.

### Upgrade Checklist
- Run contract tests before and after upgrade.
- Verify root import usage for consumer entrypoints (`from gui_do import ...` only).
- Check action/input/focus routing behavior in active scenes.
- Validate workspace restore report for skipped/missing settings.
- Re-run telemetry baseline scenarios and compare to previous baseline.
- Verify prompts/docs/examples that describe routed runtime include current service/effect/operation/failure-policy terminology.

`[Back to Table of Contents](#table-of-contents)`

---

## Chapter: FAQ and Troubleshooting

Write prose answers (not one-liners) for each question:

**Q: Should I build apps directly with controls or with features?**
A: Use features as the architectural unit. Controls are implementation details inside feature
boundaries. Features provide lifecycle orchestration, event routing, observable wiring, and
clean teardown. A control alone cannot do any of these things.

**Q: When should I use `RoutedFeature` over `Feature`?**
A: Use `RoutedFeature` when you need topic-based message dispatch and declarative runtime
wiring (hotkeys, overlays, task-panel toggles) from a single spec. If your feature only needs
basic lifecycle phases and a control tree, plain `Feature` is sufficient.

**Q: Why are some key handlers not firing?**
A: Check: (1) focus ownership — is another control capturing keyboard input? (2) window scope
— is the action registered in a window scope but the window is hidden? (3) overlay modal
capture — is an overlay consuming unhandled keys? (4) scene scope — is the action registered
for a different scene? Use `EventRecorder` to trace the event routing.

**Q: Why do toast clicks not pass through?**
A: By contract, toast bounds consume left-click events to prevent accidental clicks on controls
beneath a toast. Use the `on_click` callback in the toast API for intentional interactions.

**Q: How do I avoid breaking workspace restore across versions?**
A: Use `VersionedSnapshot` with `SchemaVersion`; register `MigrationStep` objects for every
schema change; inspect the restore report for `skipped_settings` and `missing_settings_blocks`
and handle them gracefully (e.g., with a toast notification).

**Q: How do I confirm my API usage is within the supported surface?**
A: Use explicit named imports from the `gui_do` root (e.g., `from gui_do import Feature`).
Run `tests/test_public_api_exports.py` to verify all names you use are in `__all__`. Avoid
importing from internal submodules (`gui_do.features.*`, `gui_do.controls.*`, etc.).

**Q: Why does my feature's `bind_runtime` run before my sibling's `build`?**
A: It does not. The framework guarantees that all features in a scene complete `build` before
any feature's `bind_runtime` is called. If you see ordering issues, confirm features are
declared in the same scene in `FeatureSpec` entries.

**Q: How do I add a keyboard shortcut without touching every location where that key is handled?**
A: Declare an `ActionSpec` in config and an `ActionHotkeySpec` (or include it in a
`RoutedRuntimeSpec`). The framework registers it with the action registry and input map
automatically. No manual wiring in event handlers needed.

`[Back to Table of Contents](#table-of-contents)`

---

## Chapter: Appendix

### Appendix A: Glossary

Write a glossary with a paragraph-length entry for each term (not just one-line definitions):
- **Feature** — lifecycle-managed application behavior unit (types: DirectFeature, Feature, LogicFeature, RoutedFeature)
- **Spec** — declarative data object describing runtime wiring
- **Host** — plain Python object passed to bootstrap; receives all runtime members as attributes
- **Scene** — top-level interaction context; features belong to exactly one scene
- **Window presentation** — the window-level visibility, focus, and routing model
- **Routed runtime** — declarative bundle of hotkeys, overlays, subscriptions, and toggles for a feature
- **Observable** — a value with automatic subscriber notification on change
- **Workspace state** — persisted runtime context (scene, feature states, settings) for session restore
- **Contract test** — automated test that verifies framework-level behavioral guarantees
- **Tier** — grouping of public API exports by abstraction level and recommended usage priority
- **Runtime scope** — lifecycle-owned container for cleanup and scene-local service ownership
- **Feature operation** — declarative operation handler bound through routed runtime specs
- **Failure policy** — operation retry/timeout/publication rules applied declaratively

### Appendix B: Lifecycle and Event Routing Sequence

Write a numbered reference sequence:
1. `bootstrap_host_application` initializes host from config specs.
2. All feature `build(host)` calls in scene order.
3. All feature `bind_runtime(host)` calls (all build done first).
4. Runtime loop begins.
5. Each frame: raw pygame events → `GuiEvent` normalization.
6. Overlay/focus/window/scene routing pass.
7. Feature `handle_event` calls in routing order.
8. Feature `on_update` calls; scheduler dispatches scheduled tasks.
9. Feature `draw` calls; control tree renders; present to screen.
10. On scene transition: `shutdown_runtime` for departing features; `build` + `bind_runtime` for arriving features.
11. On app exit: `shutdown_runtime` for all active features; workspace save.

### Appendix C: System Dependency Map

Write as prose paragraphs, not just a list:
- Bootstrap (Tier 1) depends on: all spec types, Feature lifecycle, scene/window presentation, action/input, font/theme config.
- Features (Tier 1-2) depend on: controls, data/observables, event/action systems.
- Layout (Tier 8) and focus (Tier 4) depend on: control tree and scene/window visibility.
- Overlays (Tier 9) depend on: event routing and focus policy.
- Persistence (Tier 11, 32) depends on: state models and scene/window registration.
- Scheduling (Tier 5) and animation depend on: feature update loop and scene scope.
- Telemetry/introspection (Tiers 7, 17) cross-cut all runtime layers.
- Audio (Tier 20) depends on: pygame mixer; surface through `SoundEventBus`.
- Service scope (Tier 25) is usable at any tier as a dependency container.

### Appendix D: API Quick Index by Topic

Build this index from the `gui_do/__init__.py` tiers discovered in the inventory step.
Organize by **topic** (not by tier number), grouping related exports under meaningful
headings (Bootstrap, Features, Events, Actions, Observables, Controls, Layout, etc.).

For each topic group, list ALL names from the relevant tiers. Do not pre-filter or truncate.
If a new tier was discovered in `__init__.py` that does not map to an existing topic group,
create a new group for it.

The completeness of this index is the primary coverage signal for the manual. Every name
in `gui_do.__all__` should appear in exactly one topic group.

### Appendix D.1: Tier-to-System Reference Matrix

Build this table from the `gui_do/__init__.py` tiers discovered in the inventory step.
Write one row per tier. For each tier, use the tier comment header name as the "System" column,
and list representative key types (3-5 of the most important names for that tier).

The table must include ALL tiers found in `gui_do/__init__.py` — including any new tiers
added since the last generation. If the highest tier number has increased, all new rows
must be present. Do not truncate at a previously known maximum tier number.
| 18 | Advanced runtime helpers | `set_window_visible_state`, `create_feature_presented_window`, `ActiveTabUpdateRouter` |
| 19 | Infrastructure internals | `UiEngine` — avoid in application code |
| 20 | Audio | `SoundCue`, `SoundBankRegistry`, `SoundEventBus` |
The table must include ALL tiers found in `gui_do/__init__.py`. Do not continue the old
hardcoded rows here — build the full table fresh from the inventory step.

### Appendix D.2: Public API Selection Heuristics

Write as decision rules:
1. Start at Tier 1. If `HostApplicationConfig` + `bootstrap_host_application` + Feature types solve the problem, stop there.
2. Descend one tier at a time when you need finer control.
3. Use Tier 18 helpers when extending bootstrap behavior — they are stable extension points.
4. Never import from `gui_do.*` submodules in application code; always use `from gui_do import ...`.
5. Avoid Tier 19 (`UiEngine`) in application code; it is framework internals.

Decision shortcuts:
- Need app setup → `HostApplicationConfig` + `bootstrap_host_application`
- Need cross-feature behavior → lifecycle specs + routed runtime helpers
- Need heavy dataset UI → virtualization/dataflow APIs before custom loops
- Need maintainable persistence → `WorkspacePersistenceManager` + `SnapshotMigrator`
- Need discoverable shortcuts → `ShortcutOverlaySpec` in `RoutedRuntimeSpec`

### Appendix E: Architecture Templates

**Template 1: Small Single-Scene App**
- 1 scene, 2–4 `Feature` instances
- `ObservableValue` state in features
- `ActionSpec` entries for commands, `RuntimeSceneSpec` with `bind_escape_to_exit=True`
- No task panel, no window presenter

**Template 2: Multi-Window Workbench**
- 2+ scenes with scene menu strip
- `SceneTaskPanelSpec` + per-window `TaskPanelFocusToggleSpec`
- `WindowPresenter` subclass per window
- `RoutedRuntimeSpec` with `ShortcutOverlaySpec`
- `FeatureWindowBundleBindingSpec` for self-contained feature+window bundles

**Template 3: Data-Heavy Analysis Tool**
- `AsyncDataProvider` + `SortFilterProxySource` + `VirtualizationCore`
- `DataflowPipeline` with `CancellationToken` for background transforms
- `DirtyRegionTracker` for incremental rendering
- `TelemetryConfig` enabled; telemetry baselines in tests

**Template 4: Long-Running Workflow App**
- `CooperativeScheduler` coroutines for multi-step background work
- `ObservableValue` progress exposed to UI feature
- `WizardFlow` for guided multi-step user input
- `SnapshotMigrator` for versioned session state

`[Back to Table of Contents](#table-of-contents)`

---

## Replace Target

Replace from the line containing:
```
## Testing, Diagnostics, and Reliability
```
through to the end of the file (last character).

Include the `## Testing, Diagnostics, and Reliability` heading in your output.
