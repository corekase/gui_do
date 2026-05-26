---
name: Manual
description: Monolithic serial generator for MANUAL.md (program + section input list)
agent: agent
---

# gui_do Manual Generator Program (Monolithic, Serial, Discovery-Only)

This prompt defines a single monolithic program for generating the manual.
It is intentionally structured as:
1. Program instructions (how to generate)
2. Input list (what sections to generate)

The program must generate MANUAL.md in strict serial order, section by section.

## Program

You are generating or updating MANUAL.md from the current repository state.
Do not use stale assumptions. Discover everything from code, tests, docs, and demos at runtime.

### Core generation standard

1. Be verbose, comprehensive, and high-signal.
2. Longer is better when it adds substance, clarity, and practical value.
3. Do not be redundant or repetitive.
4. Explain both how and why for every major concept.
5. Prefer progressive explanations over repetitive bullet dumps.

### Code example standard

1. Add code examples at every reasonable opportunity.
2. Every example must be introspected and verified against the current gui_do codebase at generation time.
3. Examples must use current public API names and valid field names.
4. Examples must explain how and why the shown pattern works.
5. If a section is concept-heavy, still include at least one concise, relevant code example unless impossible.

### Execution model (strict)

1. Generate serially only.
2. Never perform parallel generation.
3. Never generate multiple sections concurrently.
4. Complete one section, then continue to the next.
5. If partial update mode is requested, still process selected sections serially in listed order.

Rationale: parallel section generation can hang and can produce inconsistent cross-links.

### Discovery model

Before writing each section, perform a targeted discovery pass across:
1. gui_do package exports and owning modules
2. Relevant tests that assert behavior
3. Relevant docs under docs/
4. Relevant demo usage under demo_features/

Source-of-truth priority:
1. Current runtime behavior in gui_do code
2. Tests
3. Contract and architecture docs
4. Demo specs/examples
5. Existing prose docs

### Public API completeness contract

The generated manual must be driven by the current exported API surface, not by a static assumption set.

1. Inventory the current root-package public API from `gui_do/__init__.py` and its `__all__` definition.
2. Use `docs/public_api_spec.md` to verify the intended public-surface grouping and tier model.
3. Build a generation-time tier-to-chapter mapping from the current root exports.
4. Ensure every currently exported public system family is documented in at least one main chapter and indexed in the appendix.
5. Ensure every currently exported public type, helper family, runtime spec family, manager family, and subsystem cluster appears at least once in the manual by name or in a verified API table.
6. Do not silently omit newer tiers or small exported subsystems just because they do not have a dedicated top-level chapter title.
7. If an exported public API does not fit naturally into an existing chapter, document it in the closest chapter and explicitly index it in Appendix D.
8. Clearly distinguish public APIs from advanced-runtime helpers and from infrastructure/internal exports that are not recommended for normal application code.

### Document navigation contract

The generated output must include a full Table of Contents near the top.
1. Every major section must be listed with a working anchor link.
2. Every section heading must include a link back to Table of Contents directly below the heading:
   [Back to Table of Contents](#table-of-contents)
3. All cross-references must resolve.

### Document structure contract

Generate sections in this fixed order:
1. Title and Purpose
2. Table of Contents
3. How to Use This Manual
4. Feature Organization Conventions
5. Conceptual Foundations (Theory)
6. Quickstart Path (Practice)
7. Architecture and Runtime Model
8. Core Workflow: Build, Bind, Route, Update, Draw
9. Main Systems Reference
10. Integration Patterns and Composition Recipes
11. End-to-End Reference Application
12. Testing, Diagnostics, and Reliability
13. Performance and Scaling Guidance
14. Migration, Versioning, and Deprecation Notes
15. FAQ and Troubleshooting
16. Appendix

Main Systems Reference fixed chapter order:
1. Application Bootstrap and Host Configuration
2. Feature Lifecycle and Feature Types
3. Events, Actions, Input Mapping, and Routing
4. State and Observables
5. Controls and Control Composition
6. Layout Systems
7. Focus and Accessibility
8. Overlays, Dialogs, Notifications, and Command Surfaces
9. Scene, Window, and Task-Panel Presentation Models
10. Scheduling, Timing, Animation, and Transitions
11. Persistence and Workspace/Session State
12. Theme, Styling, and Visual Systems
13. Text, Input, Forms, and Validation Systems
14. Data and Dataflow Helpers
15. Graphics and Audio Integration Points
16. Telemetry, Introspection, and Operational Hooks

Each system chapter must include:
1. What it is and why it exists
2. Mental model and lifecycle placement
3. Primary public APIs and key types
4. Typical usage flow
5. Minimal verified example
6. At least one advanced pattern
7. Common mistakes and anti-patterns
8. Cross-links to related chapters
9. Back-to-TOC link

### Required topical coverage

The generated manual must include and correctly cross-link:
1. Data-driven runtime model and lifecycle model
2. Automatic subscription ownership and cleanup as lifecycle safety
3. Runtime-scope ownership and teardown discipline
4. Declarative service/effect/operation specs and failure policies
5. Higher-level routed runtime faculties discovered at generation time
6. Unified menu-strip model only (no split narrative)
7. Command palette two-bind model and behavior details
8. Unified window-visibility model across menu strip, command palette, task panel
9. Scene/window opt-in and opt-out behavior using current discovered fields
10. Contract-test and maintenance checklist guidance
11. File path resolution behavior from process working directory
12. Demo feature package organization convention
13. Task-panel window-toggle placement API:
   `TaskPanelWindowToggleGroupSpec(flow_start_slot, flow_slot_assignments, panel_rect_overrides)`
   with explicit guidance for non-linear placement and slot-flow fallback
14. Task-panel window-toggle identity/geometry reporting API:
   `SceneTaskPanelItemsResult.window_toggle_placements` and `TaskPanelWindowTogglePlacement`
   with panel-relative rect semantics (ignoring auto-hide offsets)
15. Automatic window layout API and compatibility aliases:
   `set_window_layout_enabled()`, `is_window_layout_enabled()`, `toggle_window_layout_enabled()`
   and the compatibility `*_window_tiling_enabled()` aliases, with scene-scoped behavior
16. Unified window z-order API and forced relayout behavior:
   `raise_window()`, `lower_window()`, `tile_windows(..., force=True)` and how they interact
   with automatic layout enablement
17. Window layout handler operating contract:
   when layout handling is disabled, automatic relayout and automatic window interference stop;
   when enabled, raise/lower events relayout all windows through the handler; explicit one-time
   relayout requests still run through the handler via the forced path
18. Public API tier coverage derived from current `gui_do.__all__`, including all currently exported tiers and system families
19. Per-scene optional facilities and bounded-area APIs, including unified window visibility management, task panel, scene menu strip, command palette, and `GuiApplication.bounded_area_rect()`
20. Text and localization APIs, including formatter, text-flow, text-search, string-table, and locale-registry systems
21. Advanced data and collection APIs, including virtual item sources, async data loading, sort/filter proxies, object pooling, caches, and diff calculators
22. Graphics and rendering APIs, including render targets, draw phases, scene graph, particle systems, tile maps, asset registries, compositors, and debugging overlays
23. Introspection and inspection APIs, including scene spatial index, property registry, property inspector models, and inspection workflows
24. Advanced runtime and bootstrapping helpers, including feature/runtime helper families, presenter/tab helpers, host-action declaration helpers, runtime wiring helpers, and routed-runtime setup/shutdown helpers
25. Audio APIs, including sound cues, sound-bank registries, and sound-event bus patterns
26. Accessibility APIs, including accessibility tree, roles, live announcements, politeness, and accessibility bus patterns
27. Theme invalidation APIs, including automatic visual cache invalidation on theme switch
28. Undo-context routing APIs, including named undo/redo stack routing and selection guidance
29. Async form-validation APIs, including debounced cross-field validation flows
30. Scoped service-graph APIs, including typed service keys, scopes, and scope stacks
31. Cancelable dataflow-pipeline APIs, including cancellation tokens, stages, pipeline handles, and stale-generation behavior
32. Transactional app-state store APIs, including selectors, transactions, and snapshot semantics
33. Adaptive constraint layout v2 APIs, including adaptive policies and priority-based constraints
34. Virtualization core APIs, including measure policy, recycle pool, virtualized windows, and virtualization engine responsibilities
35. Interaction state machine APIs, including phases, contexts, guarded transitions, and input-phase coordination
36. Schema-driven form runtime APIs, including field graph schemas, validation policies, and schema runtime behaviors
37. Portable snapshot and migration APIs, including schema versions, versioned snapshots, migration registries, migration steps, and snapshot migrator workflows
38. Infrastructure and internal caution guidance for exports that are public but not recommended as normal application entry points, such as low-level runtime engine helpers

### Appendix contract

Appendix must include at least:
1. Appendix A: Glossary
2. Appendix B: Lifecycle and Event Routing Sequence
3. Appendix C: System Dependency Map
4. Appendix D: API Quick Index by Topic
5. Appendix D.1: Tier-to-System Reference Matrix
6. Appendix D.2: Public API Selection Heuristics
7. Appendix E: Architecture Templates
8. Appendix F: Specifications and Option Reference

Appendix F is mandatory and must cover all discovered spec families and subspecs with tables that include:
1. Spec name
2. Field or option name
3. Purpose
4. Default or notable behavior
5. Cross-reference chapter

Appendix D is mandatory as a true API coverage index and must include:
1. Every currently exported root-package public symbol grouped by current tier/system
2. A chapter or appendix target for every exported symbol family
3. Tier-to-chapter mapping for all current tiers discovered from `gui_do/__init__.py`
4. Explicit entries for advanced-runtime helpers, optional facilities, and public-but-not-primary APIs

### Special normalization and cleanup

1. Normalize markdown display for double-underscore names by using inline code formatting.
2. Replace all occurrences of pygame-ce with pygame.
3. Remove obsolete, stale, or superseded content.
4. Ensure no placeholder markers remain.

### Final enrichment pass (mandatory and single)

After all sections are generated, run exactly one final enrichment pass across the full document.
This pass must:
1. Find opportunities to inline additional insights and best practices.
2. Improve explanations where depth is insufficient.
3. Add missing code examples where appropriate.
4. Improve markdown structure and cross-link clarity.
5. Preserve section order and avoid unnecessary rewrites.

### Completion gates

Before finishing, verify:
1. MANUAL.md exists.
2. Full TOC exists and links resolve.
3. Every section has a back-to-TOC link.
4. No placeholder comments remain.
5. Code examples are verified against current APIs.
6. Spec-heavy sections link to Appendix F.
7. Appendix F covers discovered specs and subspecs.
8. Obsolete content removed.
9. pygame-ce string no longer appears.
10. Every currently exported root-package public API family discovered from `gui_do.__all__` is documented somewhere in the manual.
11. Appendix D includes a complete current API quick index and tier-to-chapter mapping.
12. Public systems introduced in tiers beyond the core chapter names are not omitted.

## Input List (Section-by-Section Targets)

Use this as the terse generation input list. Expand each item using the Program rules above.

1. Title and purpose framing for gui_do manual audience and intent
2. Full navigable TOC with internal links
3. How to use manual: reading paths, tri-lens framing, contract alignment
4. Feature organization conventions from real demo_features package patterns
5. Conceptual foundations:
   data-driven architecture, observables, feature lifecycles, runtime ownership,
   routed runtime composition, higher-level runtime faculties discovered at runtime
6. Quickstart path:
   milestone path, common failure modes, first-success patterns
7. Architecture and runtime model:
   boundary model, tier model, runtime guarantees, event pipeline
8. Core workflow:
   build, bind_runtime, route, update, draw; message coordination; routed lifecycle helpers
9. Systems: Application Bootstrap and Host Configuration through State and Observables
10. Systems: Controls and Control Composition through Overlays, Dialogs, Notifications, and Command Surfaces (include command palette two-bind model in Overlays, Dialogs, Notifications, and Command Surfaces)
11. Systems: Scene, Window, and Task-Panel Presentation Models through Theme, Styling, and Visual Systems (include unified window-visibility guidance and automatic-layout API guidance in Scene, Window, and Task-Panel Presentation Models)
11a. In Scene, Window, and Task-Panel Presentation Models, explicitly document task-panel window-toggle placement and geometry reporting APIs with verified demo usage examples
11b. In Layout Systems and Scene, Window, and Task-Panel Presentation Models, explicitly document automatic layout enable/disable semantics, handler-controlled raise/lower relayout behavior, compatibility tiling aliases, and the explicit F3-style one-time relayout path using `tile_windows(..., force=True)`
12. Systems: Text, Input, Forms, and Validation Systems through Telemetry, Introspection, and Operational Hooks
12a. Within the existing system chapters, explicitly cover the remaining exported public tiers that may not be obvious from chapter names: text/localization, advanced data/collections, graphics/rendering, introspection/inspection, advanced runtime/bootstrap helpers, audio, accessibility, theme invalidation, undo-context routing, async form validation, scoped service graph, cancelable dataflow pipeline, transactional app state store, adaptive constraint layout v2, virtualization core, interaction state machines, schema-driven form runtime, and snapshot/migration APIs
13. Integration patterns and composition recipes
14. End-to-end reference application listing with validation checklist
15. Testing, diagnostics, reliability, maintainer diff checklist
16. Performance and scaling guidance
17. Migration, versioning, deprecation notes
18. FAQ and troubleshooting
19. Appendices A-E
20. Appendix F specifications and option reference for all discovered spec families and subspecs
21. Single final enrichment pass across complete document

## Operating note

This prompt is the authoritative entrypoint for manual generation behavior.
