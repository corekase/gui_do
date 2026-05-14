---
name: Optimize
description: Performance-first, then resource-efficiency optimization pass across the entire package — discovers all subsystems from source at invocation time
---

## Role

You are an agent performing an optimization pass on this package. The primary criterion is **performance** — throughput, latency, and computational complexity. The secondary criterion is **resource efficiency** — memory, surface allocations, and cache utilization. Correctness and test coverage must not regress. Portability is required: no OS-specific extensions or non-portable native code.

## Phase 1 — Discovery

Before analyzing any code, collect the ground truth from the live codebase.

### 1a. Enumerate Subsystems

List the contents of `gui_do/`. Every subdirectory is a subsystem. Record the full ordered list — this list drives every subsequent step and must not be hardcoded here. Within the `gui_do/controls/` directory, also list its subdirectories (e.g., `base`, `input`, `display`, `chrome`, `composite`, `data`, `canvas`) and treat each as a separate subsystem. Append `demo_features/` and `tests/` at the end as the final two entries (for analysis only — do not optimize demo or test code).

### 1b. Enumerate Runtime Systems from Source

Read `gui_do/__init__.py` in full. Identify every exported runtime class and spec (anything that ends in `Runtime`, `Coordinator`, `Orchestrator`, `Engine`, `Harness`, `Manager`, `Broker`, or `Spec`) and the files they originate from. Group them by the source file they are defined in. This list defines the set of runtime systems to audit for hotpath and allocation issues. Do not hardcode names — extract them from the actual file.

### 1c. Record Baseline

Run `python -m unittest discover -s tests -p "test_*.py" 2>&1 | tail -3` and record the test count and pass/fail result. This baseline must be maintained throughout.

## Phase 2 — Analysis Pass

For every subsystem discovered in Phase 1a, read all `.py` files in that subsystem and identify every optimization opportunity. Record each finding with:

1. **Location** — file, class, and method or function name.
2. **Problem** — what makes the current code slow or wasteful (e.g., O(n) scan on a `list` where a `dict` or `set` lookup is possible, per-tick collection snapshot that allocates a new list every frame, duplicate geometry computation across branches, unconditional redraw without a dirty flag, repeated `str()`/`int()` coercion on the same value).
3. **Fix** — the specific change to make.
4. **Scale** — classify as `local` (self-contained change within one function or class) or `structural` (requires changes across multiple files or reorganization of data ownership).

Apply the optimization priority order below when assigning significance to each finding.

## Optimization Priority Order

Work through every file in every subsystem and evaluate against these priorities, highest-leverage first.

**Priority 1 — Algorithmic complexity.**
Find every place a linear-time operation is used where a constant-time one is available:
- `list` or `deque` membership tests (`x in list`) that should use a `set` or `dict` key lookup.
- Linear removal from lists (`list.remove(x)`) where an `O(1)` dict or set removal is possible.
- Repeated full-collection scans that should be pre-indexed at construction time.
- O(n²) nested loops over data that is stable between calls and could be pre-processed once.

Fix the data structure and all operations that depend on it together.

**Priority 2 — Hotpath duplicate computation.**
In per-event and per-frame paths:
- Find any block of geometry, rect, or state computation that is repeated identically across two or more branches of the same function (e.g., mouse-down, motion, and mouse-up each independently recomputing the same handle rect). Extract once per call.
- Find any method called more than once in the same logical operation with the same arguments where the result cannot have changed between calls. Cache the result in a local variable.
- Find any attribute access chain repeated more than twice inside a loop (e.g., `self._foo.bar.baz`). Cache in a local before the loop.

**Priority 3 — Per-tick allocation.**
Find places that construct a new throwaway collection every update cycle solely to enable safe iteration (e.g., `list(self._items)` at the top of an `on_update` method). Replace with:
- A deferred-removal pattern using a pending-removal set that is drained after iteration.
- A generation counter or snapshot-on-write flag that avoids allocation when no mutation occurred.

**Priority 4 — Repeated type coercions.**
In render and text paths, find calls to `str()`, `int()`, `float()`, or `round()` on the same value more than once in the same call chain. Cache the converted value at the top of the function and reuse it.

**Priority 5 — Dirty-flag / lazy evaluation.**
Find draw or layout operations that unconditionally recompute derived geometry, text metrics, or layout results on every frame when an `_is_dirty` or `_needs_layout` flag pattern could gate the computation. Introduce invalidation only where:
- The recomputation cost is measurable (more than a few arithmetic operations).
- The set of events that dirty the result is well-defined and easy to intercept.

**Priority 6 — Allocation in tight loops.**
Find object construction (tuples, `pygame.Rect`, event objects, intermediate lists) inside loops that execute on every event or every frame. Hoist construction outside the loop or replace with in-place mutation where the contract permits.

**Priority 7 — Runtime system pump and dispatch overhead.**
For every runtime system discovered in Phase 1b, read its source file and analyze:
- The `pump()` / `begin_update()` / `on_update()` methods for unnecessary allocations, redundant dict lookups, or O(n) scans over structures that could be pre-sorted or pre-indexed.
- Subscription and cleanup loops for repeated container copies or deferred-list rebuilds that could be avoided.
- Status-transition logic for branches that can be simplified or short-circuited when state has not changed.
- Internal `snapshot()` methods called in tight paths — ensure they do not produce throwaway copies unless the caller actually needs a copy.

**Priority 8 — Surface and rendering allocations.**
In `graphics/`, `controls/`, and any `draw()` method, find:
- `pygame.Surface` created every frame where one created once (and sized correctly) would suffice.
- `pygame.Rect` constructed from raw integers inside draw loops — replace with a cached rect that is updated only when dimensions change.
- Blits of invisible or zero-alpha surfaces that produce no visible output but still consume blit time.

## Phase 3 — Plan Presentation

After completing the analysis of all subsystems, present the full written plan grouped by subsystem and ordered within each subsystem by priority level. For each entry record Location, Problem, Fix, and Scale. Do not change any code yet.

Present the plan and wait for explicit confirmation before proceeding to Phase 4.

## Phase 4 — Implementation

Once the plan is confirmed, work through it item by item in the order presented.

### Local optimizations

Batch all `local` items within a single subsystem, apply them, then run the test suite and confirm the baseline is maintained before moving to the next subsystem.

### Structural optimizations

For each `structural` item:
1. Write a focused subplan describing the change, all files affected, and the sequence of edits.
2. Present the subplan and wait for confirmation.
3. Execute the subplan fully.
4. Run the full test suite and confirm the baseline is maintained.
5. Resume the main plan.

## Constraints

- Every optimization must leave the test suite passing at the Phase 1c baseline. Run the full suite after each local batch and after every structural subplan.
- Do not change public API signatures unless the change is genuinely necessary and all callers are updated in the same pass.
- Do not add compatibility constructs for old behavior: no adapters, aliases, wrapper layers, fallback paths, feature flags, or dual-API branches.
- Do not add OS-specific code, platform guards, or non-portable native extensions.
- If a structure appears unoptimized but exists for a documented reason (e.g., a deque as a bounded history ring buffer, a pre-allocated list for frame-reuse), note it in the plan as a deliberate design choice and skip it.
- Do not optimize `demo_features/` or `tests/` code — analyze them in Phase 2 for context only.

## Runtime Facilities Safety Guard

When optimizing any runtime system discovered in Phase 1b, do not alter lifecycle or safety semantics:

- Preserve teardown guarantees for runtime scopes, effect subscriptions, and operation timers.
- Preserve failure-policy behavior (retry, timeout, failure publication) while optimizing internal mechanics.
- Keep behavior deterministic and scene-portable. Do not introduce speculative concurrency.
- Preserve semantics discovered in the source: dependency validation order, workflow step progression, recompute topological order, QoS budget enforcement logic, health state transition thresholds, replay ring-buffer bounds, hot-swap safety checks, policy admission decisions, event pipeline stage sequencing, durable queue idempotency and status transitions, capability version validation, projection dependency ordering.
