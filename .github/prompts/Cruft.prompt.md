---
name: Cruft
description: Removes dead code, stale imports, compatibility shims, and backward-compat constructs from the package to keep the codebase lean and maintainable.
---

You are performing a cruft-removal pass on this package. Your job is to find and eliminate dead code and compatibility structures that have accumulated since the last cleanup. Work through the categories below in order. After completing each category, run the full test suite (`python -m unittest discover -s tests -p "test_*.py"`) to confirm nothing broke before proceeding.

## What to Remove

**Dead imports.** Scan every source file — including `TYPE_CHECKING` blocks — for imports that reference symbols or module paths that no longer exist, have been renamed, or are never used in the file. Remove each dead import line. Pay special attention to relative import paths that were not updated after package reorganizations.

**Unused code.** Find and remove:
- Module-level variables and constants that are never read outside the file they are defined in.
- Private methods and functions that are never called from anywhere in the package or the tests.
- Public methods and classes that are not referenced by any internal code, test, or the demo, and are not part of the declared public API (`gui_do.__all__`).
- Entire source files that are unreachable (not imported by any other module, not a test file, not a demo entrypoint).
- Unused function/method parameters, including parameters that are accepted but silently ignored throughout the entire call chain.

**Compatibility aliases and shims.** Remove:
- Module-level name aliases of the form `NewName = OldName` or `OldName = NewName` that exist only for backward compatibility.
- Pass-through facade modules whose entire purpose is to re-export symbols from a relocated module.
- Collapsed coordinator or facade classes that once delegated to another object but whose routing layer has since been inlined into the caller.
- `getattr`/`hasattr` duck-typed probing fallbacks in production code that guard against missing attributes or methods that are now guaranteed to exist by the canonical contract.
- Legacy conditional branches (e.g., `if scene_name == "..."`) that are permanently dead because the triggering condition can never be satisfied given the current architecture.
- **Known deprecated patterns to prioritize**: Look for and remove optional `changed_keys=None` parameter paths in `AppStateStore`, scene generator interface shims (if any), and hardcoded timing workarounds like `_FONT_SIZE` constants that could be derived from proper font metrics.

**Stale test infrastructure.** Remove test helper stubs, fixture builders, or shared factory presets that are no longer consumed by any test. Do not remove tests themselves unless the functionality they cover has been deleted.

## What NOT to Remove

- Any structure that exists for a documented performance reason (caches, pools, deferred removal buffers, memoization dictionaries). If unsure, check for a comment or a note in memory before removing.
- Symbols listed in `gui_do.__all__` — those are public API and must not be removed without an explicit API-change decision.
- Lifecycle hook methods (`on_added_to_gui`, `on_enabled_changed`, `_on_window_visibility_changed`, etc.) that appear unread but are called indirectly through parent dispatch or callback chains. Confirm with a cross-file reference search before deleting any hook.
- `__init__.py` re-exports that are part of the declared package surface.
- New routed runtime facilities and their spec types unless truly unreachable and not exported:
	- `FeatureRuntimeScope`, `FeatureOperationBus`, `FeatureOperationHandle`, `FeatureOperationContext`
	- `ServiceBindingSpec`, `ServiceConsumerSpec`
	- `StoreSubscriptionSpec`, `StoreSelectorSpec`
	- `ObservableEffectSpec`, `SignalEffectSpec`
	- `FeatureOperationSpec`, `FailurePolicySpec`
	- `FeatureDependencySpec`
	- `WorkflowStepSpec`, `WorkflowSpec`, `WorkflowCoordinator`
	- `RecomputeNodeSpec`, `RecomputeOrchestrator`
	- `QoSPolicySpec`, `QoSPolicyRuntime`
	- `HealthProbeSpec`, `FeatureHealthRuntime`
	- `ReplaySpec`, `RuntimeReplayHarness`
	- `ReplacePolicySpec`, `FeatureHotSwapManager`

## New Runtime Facilities Cleanup Rules

When auditing for dead code and shims, treat runtime-facility wiring as first-class architecture.

- Preserve lifecycle ownership semantics: `bind_runtime` setup must pair with `shutdown_runtime` disposal.
- Do not collapse or remove `runtime_scope_attr_name` / `operation_bus_attr_name` paths as "unused" if they are part of `RoutedRuntimeSpec` composition.
- Do not collapse or remove `feature_dependencies`, `workflow_specs`, `recompute_nodes`, `qos_policies`, `health_probes`, `replay_spec`, `replace_policy`, or their `*_attr_name` mappings as "unused" if they are part of routed runtime composition.
- Do not remove operation failure publication paths solely because they are scene-scoped or callback-driven; verify no tests or demo features consume those topics first.
- If removing a feature subscription/helper, verify equivalent cleanup still occurs through runtime scope disposal.

## Process

Work subsystem by subsystem (`gui_do/app`, `gui_do/events`, `gui_do/data`, `gui_do/scheduling`, `gui_do/graphics`, `gui_do/layout`, `gui_do/theme`, `gui_do/focus`, `gui_do/actions`, `gui_do/controls/base`, `gui_do/controls/input`, `gui_do/controls/display`, `gui_do/controls/chrome`, `gui_do/controls/composite`, `gui_do/controls/data`, `gui_do/controls/canvas`, `gui_do/overlays`, `gui_do/features`, `gui_do/persistence`, `gui_do/accessibility`, `gui_do/audio`, `gui_do/state`, `gui_do/text`, `gui_do/forms`, `gui_do/telemetry`, `gui_do/introspection`, `demo_features/`, `tests/`). For each subsystem, complete all four removal categories, then run the test suite before moving to the next subsystem. Record a summary of what was removed (file, symbol, reason) as you go so the session has a clear audit trail.
