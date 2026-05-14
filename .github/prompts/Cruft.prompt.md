---
name: Cruft
description: Removes dead code, stale imports, and compatibility structures from the package — without touching the public API without explicit confirmation
---

## Role

You are an agent performing a cruft-removal pass on this package. Your job is to find and eliminate dead code and compatibility structures that have accumulated since the last cleanup. Work subsystem by subsystem in the order produced by the Discovery Phase. After completing each subsystem, run the test suite before moving on.

## Phase 1 — Discovery

Before touching any file, collect the ground truth from the live codebase.

### 1a. Enumerate Subsystems

List the contents of `gui_do/`. Every subdirectory is a subsystem. Record the full ordered list — this list drives every subsequent step and must not be hardcoded here. Within the `gui_do/controls/` directory, also list its subdirectories (e.g., `base`, `input`, `display`, `chrome`, `composite`, `data`, `canvas`) and treat each as a separate subsystem. Append `demo_features/` and `tests/` at the end of the list as the final two entries.

### 1b. Enumerate the Public API

Read `gui_do/__init__.py` in full. Collect every exported name — these are the names assigned in import statements at module scope or listed in `__all__`. Store this set as the **Protected API Set**. No symbol in this set may be deleted or renamed without explicit user confirmation (see the API Protection rule below).

### 1c. Record the Baseline Test Count

Run `python -m unittest discover -s tests -p "test_*.py" 2>&1 | tail -3` and record the number of tests run and the pass/fail result. This is the baseline that must be maintained throughout.

## Phase 2 — Subsystem Pass

For every subsystem discovered in Phase 1a, execute all four removal categories in order. After finishing all four categories for a subsystem, run the test suite and confirm it still matches the baseline before proceeding to the next subsystem. Record every removal in an audit trail (file, symbol or construct, reason).

### Category A — Dead Imports

Scan every `.py` file in the subsystem, including `TYPE_CHECKING` blocks. Identify and remove:
- Imports of symbols or module paths that no longer exist.
- Imports of symbols that exist but are never referenced anywhere in the same file.
- Relative import paths that were not updated after package reorganizations.

Before removing any import that names a symbol in the Protected API Set, verify the import is genuinely unused in this specific file. If a cross-file usage exists (re-exported, forwarded), do not remove it.

### Category B — Unused Private Code

Find and remove:
- Module-level variables and constants that are never read outside the file they are defined in, and are not in the Protected API Set.
- Private methods and functions (names starting with `_`) that are never called from anywhere in the package, tests, or demo — confirmed by a workspace-wide reference search.
- Entire source files that are unreachable: not imported by any other module, not a test file, not a demo entrypoint, not referenced from `gui_do/__init__.py`.
- Function or method parameters that are accepted but silently ignored (assigned to `_`, never read) throughout the entire call chain — only remove if the parameter is not part of a declared interface or override contract.

Do not remove any name that appears in the Protected API Set.

### Category C — Compatibility Aliases and Shims

Find and remove:
- Module-level name aliases of the form `NewName = OldName` or `OldName = NewName` that exist only for backward compatibility and are not in the Protected API Set.
- Pass-through facade modules whose entire purpose is to re-export symbols from a relocated module, when the facade itself is not in the Protected API Set.
- `getattr`/`hasattr` duck-typed probing fallbacks in production code that guard against missing attributes or methods that are now guaranteed to exist by the current class contract — verified by checking all concrete subclasses.
- Dead conditional branches where the branch condition is permanently false given the current architecture (e.g., a version check that can never be true, a `scene_name` comparison to a scene that no longer exists). Remove only the dead branch, not the surrounding live logic.
- Collapsed coordinator or facade classes that once delegated to another object but whose routing layer has since been inlined into the caller — only if the class is not in the Protected API Set.

Do not remove anything in the Protected API Set. If a candidate for removal appears in the Protected API Set, flag it in the audit trail and skip it.

### Category D — Stale Test Infrastructure

In the `tests/` subsystem only: remove test helper stubs, fixture builders, or shared factory presets that are no longer consumed by any test function. Do not remove test functions themselves unless the functionality they cover was deleted during this same pass.

## API Protection Rule

Any name that appears in the Protected API Set collected in Phase 1b must not be deleted, renamed, or made private without first asking the user an explicit confirmation question that names the specific symbol and the reason for removal. Wait for the user's response before proceeding. Do not batch API-removal questions — ask one at a time.

## Preservation Rules — Do Not Remove

- Any structure that exists for a documented performance reason: caches, pools, deferred-removal buffers, memoization dictionaries. If there is a comment explaining the structure, treat that as sufficient documentation.
- Lifecycle hook methods (e.g., `on_added_to_gui`, `on_enabled_changed`, `_on_window_visibility_changed`) that appear unread but may be dispatched through parent callback chains. Always confirm with a workspace-wide reference search before deleting any hook.
- `__init__.py` re-exports that are part of the declared package surface (Protected API Set).
- `bind_runtime` / `shutdown_runtime` pairing. Do not remove one side of a lifecycle pair even if the removed side appears to have no callers — the framework calls these through the lifecycle dispatch mechanism.
- Routed runtime spec fields and `*_attr_name` mappings (e.g., `runtime_scope_attr_name`, `operation_bus_attr_name`, `feature_dependencies`, `workflow_specs`, `recompute_nodes`, `qos_policies`, `health_probes`, `replay_spec`, `replace_policy`, `policy_specs`, `effect_bindings`, `event_pipelines`, `durable_queue_spec`, `capability_providers`, `capability_requirements`, `projection_spec`). These are set by the framework dynamically and are not "unused" simply because no explicit call site reads them in user code.
- Operation failure publication paths that are scene-scoped or callback-driven. Verify that no test or demo consumes those topics before removing.

## After All Subsystems

1. Run the full test suite and confirm the result matches the Phase 1c baseline.
2. Present the complete audit trail grouped by subsystem, listing every removed symbol, file, or construct with its reason.
3. List any candidates that were flagged but skipped because they are in the Protected API Set, so the user can decide whether to raise an API-change request.
