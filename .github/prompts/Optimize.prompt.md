---
name: Optimize
description: Performs a performance-first, then resource-efficiency optimization pass across the entire package, covering algorithms, data structures, hotpath computation, and allocation patterns.
---

You are performing an optimization pass on this package. The primary optimization criterion is **performance** — throughput, latency, and computational complexity. The secondary criterion is **resource efficiency** — memory, surface allocations, and cache utilization. Correctness and test coverage must not regress. Portability is required: do not introduce OS-specific extensions or non-portable native code.

## Planning Phase

Before changing any code, analyze the entire package and produce a written plan. The plan must list every concrete optimization opportunity you found, grouped by subsystem. For each entry record:

1. **Location** — file, class, and method or function name.
2. **Problem** — what makes the current code slow or wasteful (e.g., O(n) scan on a structure that should be O(1), duplicate method calls per event, per-tick snapshot allocations, repeated type coercions, redundant recomputation of geometry).
3. **Fix** — the specific change to make.
4. **Scale** — classify as `local` (self-contained, safe to inline immediately) or `structural` (requires non-trivial reorganization across multiple files or classes).

Present the full plan and wait for confirmation before executing. Once confirmed, work through the plan item by item.

## Optimization Priorities

Work through opportunities in this order:

**1. Algorithmic complexity.** This is the highest-leverage category. Find every place a linear-time operation is used where a constant-time one is available: `list`/`deque` membership tests or removals that should use `dict[key, None]` or `set`; repeated full-collection scans that should be index lookups; O(n²) nested loops over static data that can be pre-indexed. Fix the data structure and the operations together.

**2. Hotpath duplicate computation.** In per-event and per-frame paths, find any block of geometry, layout, or state computation that is repeated identically across two or more branches (e.g., mouse-down, motion, and mouse-up all recomputing the same handle rectangle). Extract the computation once per call site, cache the result in a local variable, and use it across all branches. Also find any method that is called more than once in the same logical operation with the same arguments and whose result does not change between calls — cache the result in a local variable.

**3. Per-tick allocation and snapshot patterns.** Find places that produce a new collection every tick solely to avoid mutation during iteration (e.g., `list(self._items.items())` at the top of an update loop). Replace with a deferred-removal or generation-guard pattern that avoids the allocation while keeping safe iteration semantics.

**4. Repeated type coercions and string operations.** Find render and text paths that call `str()`, `int()`, or equivalent on the same value multiple times per call. Cache the converted value at the top of the function.

**5. Invalidation and lazy evaluation.** Find draw or layout operations that recompute derived values unconditionally every frame when an `_is_dirty` / `_needs_layout` flag pattern could limit recomputation to frames where inputs actually changed. Only introduce invalidation where the recomputation cost is meaningful and the dirtying events are well-defined.

**6. Allocation reduction in tight loops.** Find object construction (tuples, rects, event objects, intermediate lists) inside loops that execute on every event or every frame. Hoist construction outside the loop or replace with in-place mutation where the contract permits.

## Structural Changes

If an opportunity is classified `structural`, do not inline it into the main pass. Instead:

1. Write a focused subplan describing the change, the files affected, and the sequence of edits.
2. Execute the subplan fully.
3. Run the full test suite (`python -m unittest discover -s tests -p "test_*.py"`).
4. Confirm tests pass, then resume the main plan.

## Constraints

- Every optimization must leave the test suite fully passing. Run the full suite after each `local` batch and after every `structural` subplan.
- Do not change public API signatures unless the change is genuinely necessary and the impact on callers is addressed in the same pass.
- Do not add compatibility constructs for old behavior during optimization (no adapters, aliases, wrapper layers, fallback code paths, feature flags, or dual-API branches kept only for backward behavior).
- When an optimization requires behavior or API cleanup, update the internal `gui_do` implementation and any affected demo code in the same pass so the codebase stays on one clean API.
- Do not add OS-specific code, platform guards, or non-portable native extensions.
- If a structure appears unoptimized but exists for a documented reason (e.g., a deque used as a bounded history buffer, not as a set), note it in the plan as a deliberate design choice and skip it.
- Apply best patterns and practices for the relevant domain (Python data structures, pygame surface management, event routing, scheduler design) throughout. If you encounter a structure that violates domain best practices independently of performance, correct it as part of the same pass.
