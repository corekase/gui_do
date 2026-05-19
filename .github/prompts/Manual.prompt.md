---
name: Manual
description: Generate or update MANUAL.md — invoke this file directly to run the full pipeline
agent: agent
---


# gui_do Manual — Discovery-Based Pipeline Orchestrator

You are an agent. Execute the following steps **strictly sequentially** in a single session. Each step must:
- Perform a discovery pass of the current codebase, tests, demo features, and docs before writing.
- Generate documentation that is fully discovery-based: all API names, specs, and examples must be verified from the current source code at the time of invocation. Never assume or copy from prior content.
- Write or update only the section(s) owned by the current subprompt, using precise replace targets. Never update sections outside your scope.
- Remove obsolete information and add new information as discovered. If MANUAL.md exists, update only changed or placeholder sections; if not, generate a new manual from scratch.
- Require a complete, navigable Table of Contents with working links and back-to-top anchors for every major section.
- Require a full, up-to-date Specifications appendix, with all fields and options for each spec, and links from relevant sections.
- Require that all code examples are verified against the current API.
- Require that the enrichment pass (final step) fills in missing details and adds code examples wherever possible, with all code validated.
- Enforce that the pipeline always runs sequentially, never in parallel, and that each subprompt only updates the section(s) it owns.
- Enforce that all navigation, coverage, and accuracy gates are met, and that double-underscore identifiers are always formatted to avoid markdown misparsing.

## Execution Model

1. Check if `MANUAL.md` exists at the repository root.
2. If it does not exist, run all subprompts in sequence to generate a new manual from scratch.
3. If it exists, update only changed or placeholder sections, removing obsolete information and adding new discoveries. If the user specifies changed chapters, run only those subprompts.
4. Each subprompt must:
   - Read the relevant code, tests, and docs before writing.
   - Replace only the section(s) it owns, using precise replace targets.
   - Add or update code examples, usage flows, and advanced patterns, all verified.
   - Add links to the specifications appendix where relevant.
   - Enforce navigation and completeness rules (ToC, back-to-top links, etc.).
   - Remove or update obsolete content as needed.
5. After all steps, verify that MANUAL.md contains no placeholders, all navigation links work, all code examples are valid, and all specs are up to date.

## Subprompt Structure

The manual is split into 9 subprompts, each owning a distinct, manageable section or set of sections:
1. Full skeleton, preamble, and ToC
2. Conceptual Foundations (Theory)
3. Quickstart Path, Architecture, Core Workflow
4. Main Systems Reference (Systems 8.1–8.4)
5. Main Systems Reference (Systems 8.5–8.8)
6. Main Systems Reference (Systems 8.9–8.12)
7. Main Systems Reference (Systems 8.13–8.16), Integration Patterns, E2E Reference
8. Testing, Diagnostics, Performance, Migration, FAQ, Appendices
9. Enrichment pass: fill in missing details, add/verify code examples, update Specifications appendix

Each subprompt must be executed strictly sequentially. Never run subprompts in parallel or batch steps. Each subprompt must verify its section(s) are fully written and non-empty before proceeding.

## Quality Gates

- All navigation, coverage, and accuracy gates must be met.
- All code examples must be valid and verified against the current API.
- All specification-heavy sections must link to the Specifications appendix.
- All obsolete information must be removed, and new discoveries added.
- Double-underscore identifiers must be formatted to avoid markdown misparsing.

## Completion Check

After all steps, verify:
- MANUAL.md exists and contains no placeholders.
- All navigation links work.
- All code examples are valid.
- All specs are up to date.
- All obsolete information is removed.

---

## Theory Section Update (Required)

The Conceptual Foundations (Theory) section must now cover the new higher-level runtime faculties as a major aspect. These include:
- Runtime policy/admission control (`RuntimePolicySpec`, `PolicyDecision`, `RuntimePolicyEngine`)
- Effect lifetime ownership (`EffectBindingSpec`, `EffectLifetimeOrchestrator`)
- Routed event stream pipelines (`EventPipelineStageSpec`, `EventPipelineSpec`, `EventPipelineRuntime`)
- Durable operation queue/recovery (`DurableOperationBindingSpec`, `DurableOperationQueueSpec`, `DurableQueueRecord`, `DurableOperationQueueRuntime`)
- Capability contracts/negotiation (`CapabilityProviderSpec`, `CapabilityRequirementSpec`, `CapabilityContractRuntime`)
- Incremental projections (`ProjectionNodeSpec`, `ProjectionSpec`, `ProjectionRuntime`)
- Dependency validation (`FeatureDependencySpec`)
Describe their role, how they fit into the overall architecture, and how they are composed declaratively and managed through the feature lifecycle. Remove any outdated references to prior runtime facility patterns.

| Step | Sub-prompt file | Scope |
|------|----------------|-------|
| 1 | `.github/prompts/manual/Manual.p1.prompt.md` | Full MANUAL.md skeleton + preamble chapters |
| 2 | `.github/prompts/manual/Manual.p2.prompt.md` | Conceptual Foundations chapter |
| 3 | `.github/prompts/manual/Manual.p3.prompt.md` | Quickstart Path + Architecture + Core Workflow |
| 4 | `.github/prompts/manual/Manual.p4.prompt.md` | Systems 8.1–8.4 |
| 5 | `.github/prompts/manual/Manual.p5.prompt.md` | Systems 8.5–8.8 |
| 6 | `.github/prompts/manual/Manual.p6.prompt.md` | Systems 8.9–8.12 |
| 7 | `.github/prompts/manual/Manual.p7.prompt.md` | Systems 8.13–8.16 + Integration Patterns + E2E Reference |
| 8 | `.github/prompts/manual/Manual.p8.prompt.md` | Testing/Diagnostics · Performance · Migration · FAQ · Appendices |
| 9 | `.github/prompts/manual/Manual.p9.prompt.md` | Enrichment pass: add concise examples where missing + build/link specifications options appendix |

## Focused Update Subprompts

For targeted documentation updates on specific topics, the following focused subprompts are available:

| Topic | Sub-prompt file | Scope |
|-------|-----------------|-------|
| Command Palette | `.github/prompts/manual/CommandPalette.prompt.md` | Generate/update 8.8.X Command Palette section with two-bind input model, specs, lifecycle, and examples |

### Command Palette Update Notes (May 2026)

The command palette has been refactored with a cleaner two-bind input model:

**Spec Structure**:
- `PaletteInputBindSpec`: Defines one bind with `action_name` (required), `key` (optional), and `pointer_button` (optional)
- `SceneCommandPaletteSpec`: Has two `PaletteInputBindSpec` instances:
  - `toggle`: Opens/closes the palette itself. Can be key, button, or both.
  - `action`: Shows palette if closed (stops), or toggles window entries at pointer if already open. Can be key, button, or both.

**Implementation Details**:
- Toggle bind fires the `_toggle` handler that toggles `palette_manager.is_open`
- Action bind fires the `_action` handler that:
  1. If palette is closed: opens it and **returns immediately** (fully consumes event)
  2. If palette is already open: calls `palette_manager.try_activate_window_at(pos)` to toggle window entry visibility
  3. Non-window entries at pointer position are silently ignored
- Both binds support key and pointer button independently via `spec.toggle.key`, `spec.toggle.pointer_button`, `spec.action.key`, `spec.action.pointer_button`
- Current demo configuration: toggle=F5, action=middle-click (button 2)

When updating CommandPalette.prompt.md, verify:
- Confirm `PaletteInputBindSpec` structure with actual field definitions from data_driven_runtime.py
- Confirm toggle/action semantics match the actual handler logic in `setup_scene_command_palette_bindings()`
- Include concrete examples from demo_features/main/main_specs.py and demo_features/showcase/showcase_specs.py
- Explain why action bind stops on first trigger (palette open) vs subsequent triggers (window toggle)
- Document the full flexibility: each bind can use key, button, or both independently

## Completion Check

After all assigned steps are done:
- Confirm `MANUAL.md` exists and contains no remaining `<!-- MANUAL_PLACEHOLDER: -->` comments.
- Confirm each major chapter includes concise examples, either embedded or via links to
  relevant example blocks added during step 9.
- Confirm specification-heavy sections link to the specifications/options appendix added in
  step 9.
- Confirm markdown rendering for double-underscore identifiers is normalized so names like
  `__init__.py`, `__version__`, and `__demo__` are displayed with inline code formatting and
  are not misparsed as emphasis.
- **pygame-ce cleanup.** Search `MANUAL.md` for all exact occurrences of the string `pygame-ce` and replace every one with `pygame`. The project targets generic pygame and documentation must not name the pygame-ce variant.
- Report: steps executed, line count of final MANUAL.md, any sections that were skipped and why.

## Runtime Facilities Coverage Requirement

Across the full manual pipeline, ensure explicit coverage of routed runtime facilities and lifecycle-safe teardown:

- Runtime scope ownership model (`FeatureRuntimeScope`) and why setup/cleanup must pair across lifecycle phases.
- Automatic feature subscription ownership for observable subscriptions, including framework-driven cleanup during feature runtime shutdown. This must be documented as its own section in the theory chapter, because it is a lifecycle-safety mechanism rather than a convenience feature.
- Declarative service wiring (`ServiceBindingSpec`, `ServiceConsumerSpec`).
- Declarative reactive wiring (`StoreSubscriptionSpec`, `StoreSelectorSpec`, `ObservableEffectSpec`, `SignalEffectSpec`).
- Operation orchestration and resilience (`FeatureOperationSpec`, `FailurePolicySpec`, `FeatureOperationBus`).
- Clear anti-pattern notes for leaks and partial teardown when `shutdown_runtime` does not unwind routed runtime resources.
- In Section 4 (Conceptual Foundations / Theory), include these higher-level routed runtime faculties as a significant architectural pillar (not a footnote), including why they exist as declarative control-plane/runtime-plane composition.
- Do not keep a hardcoded long list of every higher-level faculty in this prompt. At generation time, introspect the current `gui_do/__init__.py` tier exports and the relevant docs/tests, then generate a markdown table for each discovered spec family. Each table must list the spec name, purpose, key fields/options, field defaults/notes, and the manual appendix or chapter that explains it. Use that table output to decide whether a topic belongs in the theory chapter, a system chapter, or the specifications appendix.
- If a spec family grows too large for one subsection, split it into its own subprompt or a dedicated subsection instead of flattening the content into a single bullet list.

## Unified Menu Strip Coverage Requirement

The manual pipeline must treat the unified menu-strip API as the only supported menu-strip surface. Do not describe or preserve split legacy narratives for separate regular-menu and scene-menu controls.

### Required API Surface to Document

Document and cross-link these names exactly as discovered from the current codebase:
- `MenuStripControl`
- `MenuEntry`
- `SceneMenuOptions`
- `WindowMenuOptions`
- `MenuStripSpec`
- `add_menu_strip_from_spec`
- `add_standard_menu_strip`
- `add_window_menu_strip`

### Menu-Strip Opt-In/Opt-Out Behavior

The menu-strip system supports explicit opt-in/opt-out fields for both scene and window menu sections:

- **Scene menu opt-in:**
  - The `scene_menu_opt_in` field (default: `True`) is available in `MenuStripSpec`.
  - If `scene_menu_opt_in` is `False`, the scene is excluded from the Scene menu section. If not defined, the scene is included by default.

- **Window menu opt-in:**
  - The `window_management_opt_in` field (default: `True`) is available in all window spec dataclasses (e.g., `WindowSpec`, `AnchoredWindowSpec`, `FeatureWindowBundleBindingSpec`).
  - If `window_management_opt_in` is `False`, the window is excluded from the Window menu section, command palette, and task panel. If not defined, the window is included by default.

This behavior ensures that both scene and window menu participation is explicit and consistent. Setting either field to `False` opts out the item; omitting the field opts in by default. This matches the unified menu-strip contract and provides fine-grained control over menu composition.

#### Example: Opting Out a Window
```python
FeatureWindowBundleBindingSpec(
    feature_attribute_name="_systems_feature",
    factory=SystemsFeature,
    window_key="systems",
    window_management_opt_in=False,  # This window will not appear in the Window menu, command palette, or task panel
)
```

#### Example: Opting Out a Scene
```python
MenuStripSpec(
    control_id="main_menu",
    rect=(0, 0, 800, 24),
    scene_name="main",
    scene_menu_opt_in=False,  # This scene will not appear in the Scene menu
    # ...other fields...
)
```

See the [Specifications Appendix](#appendix-f-specifications-and-option-reference) for all available fields and their defaults.

### Required Behavioral Semantics

The menu-strip documentation must explicitly explain and exemplify all of the following:

- Unified top-level model:
  The same control supports ordinary static menus (`MenuEntry` with `ContextMenuItem` callbacks/signals) and optional automatic Scene/Window sections.

- Dynamic insertion indices:
  Scene and Window sections can each be inserted at independently configured indices (`scene_menu_insert_index`, `window_menu_insert_index`) relative to static top-level entries.

- User-defined section names:
  Scene and Window section labels are user-spec configurable (`scene_menu_label`, `window_menu_label`) and are not hardcoded by the runtime contract.

- Scene discovery modes:
  `scene_menu_mode` supports:
  - `add_all`: include all discoverable scenes governed by runtime scene eligibility.
  - `opt_in`: include only user-marked scenes via `scene_menu_opt_in_scene_names`.

- Current scene filtering:
  The active/current scene is excluded from Scene menu options by default (and this behavior must be described as the default operational contract unless explicitly configured otherwise).

- Empty Scene menu-open behavior:
  If filtering leaves no scene targets, the Scene top-level entry remains highlightable like other menu headers but has no flyout to open.

- Window menu behavior:
  Window section lists visible-toggle entries using scene window pretty names/titles from the current target scene context and keeps standard toggle callback behavior.

### Required Usage Guidance

Include a dedicated subsection in the relevant manual chapter that is verbose, comprehensive, and non-redundant, covering:

- When to use static-only menu strips versus dynamic Scene/Window-enabled strips.
- How to choose insertion indices to preserve expected menu order.
- How to choose `add_all` versus `opt_in` scene mode and how to maintain opt-in lists over time.
- How current-scene exclusion affects navigation UX and why it prevents redundant no-op actions.
- How to wire callbacks/signals for static `ContextMenuItem` actions and dynamic scene/window actions.

## Unified Window-Visibility Management Coverage Requirement

The manual pipeline must include a dedicated section explaining how the three user-facing window-management surfaces work together:
- unified menu strip Window section,
- command palette window entries,
- scene task-panel window toggles.

This section must explain, with discovered API names and concrete examples, that:
- windows opt in to unified visibility management by default,
- setting `window_management_opt_in=False` on the appropriate window/binding spec opts a window out of all three management surfaces,
- opt-out is intentional for manually managed windows (for example, auxiliary/debug/utility windows) that users want to control outside automatic menu/palette/task-panel handling.

The section must also describe synchronization semantics:
- toggling visibility from any one surface updates the shared window visibility state,
- the other two surfaces reflect that state (same source of truth, not independent toggles),
- opt-out windows remain fully functional but are excluded from automatic visibility orchestration.

Place this section in the scene/window/task-panel chapter (8.9) and cross-link from the command palette and menu-strip discussions.
- How this API is used in the demo scenes (main and control_showcase) and control showcase control gallery.

### Required Examples

Provide at least these verified examples:

- Static-only menu strip with multiple top-level menus and item callbacks.
- Scene+Window dynamic menu strip with custom labels and independent insertion indices.
- Opt-in Scene mode example with explicit `scene_menu_opt_in_scene_names`.
- Spec-driven wiring example using `MenuStripSpec` + `add_menu_strip_from_spec`.

All examples must be discovery-verified against the current code and must not mention removed/legacy split menu-strip APIs.

---

# Shared Specification

All sub-prompts inherit these shared rules. Sub-prompt files do not need to repeat them fully — they reference this document for the common framework.

## Source-of-Truth Priority

1. Current code behavior in `gui_do` package.
2. Tests asserting behavior.
3. Contract/spec docs under `docs/`.
4. Demo feature usage patterns under `demo_features/`.
5. Existing README/TUTORIAL prose.

## File Path Resolution Contract (Required)

When documenting file-related APIs (persistence, telemetry, asset/image/font loading,
event recording playback files, and file dialog defaults), enforce this behavior:

- Relative paths and bare filenames are resolved from the process current working directory.
- The expected working directory is the launching application directory (for this repo,
  the project root when launching from `gui_do_demo.py`).
- Absolute paths remain absolute and are never rewritten.

Manual sections that show file-path examples must reflect this contract explicitly and
must avoid language that implies package-relative defaults (for example relative to
`gui_do/` source files).

## Demo Features Organization Convention (Required)

Document the project and examples using `demo_features/` as the canonical feature organization pattern:

- One folder per feature package under `demo_features/`.
- Each feature folder has one package root `__init__.py` as the only supported public import surface.
- Internal implementation is split into focused files in that same folder (for example `*_feature.py`, `*_presenter.py`, `*_specs.py`, `*_logic_feature.py`).
- Cross-feature imports should target package roots, not internal submodules.

When describing best practices for user projects, present this pattern as the recommended default.

### Mandatory Manual Section: Feature Organization Conventions

The generated MANUAL.md must include one dedicated section named exactly:

`## Feature Organization Conventions`

This section is required even if nearby chapters already discuss architecture or lifecycle. Do not merge it away into short bullets inside other sections.

The section must be verbose, comprehensive, and non-redundant. It must explain, in substantial prose:

- Why each feature should live in its own folder/package and how this enables safe growth over time.
- Why that folder must be a Python package with `__init__.py` as the package-level integration surface.
- How package-root imports and clear boundaries support maintainability as features add lifecycle hooks, runtime wiring, and internal modules.
- How this organization model scales especially when gui_do feature-to-feature communication and routed runtime facilities are introduced.

Use current `demo_features/` packages as concrete evidence, not hypothetical names. Discover real folders and reference multiple existing examples from the repository to illustrate:

- Package root layout (`demo_features/<feature>/__init__.py`).
- Growth through focused internal files in the same package.
- Import boundary discipline across feature packages.

The section must avoid repeating the same point in different wording. Prefer progressive explanation: baseline structure -> package surface role -> growth mechanics -> cross-feature communication implications.

At least one short code example must show a package-root export/import pattern aligned with actual `demo_features/` organization discovered at generation time.

## Verbosity Standard

Write comprehensive prose throughout. Every major concept should have enough explanation that a developer reading only that section comes away with a genuine working mental model — not just a list of bullet points. Terse bullet lists are acceptable only in quick-reference appendices and API signature sections. Conceptual sections and system chapters must contain substantial paragraphs that explain *what*, *why*, *how it compares to alternatives*, and *how it connects to adjacent systems*. Cover the material as thoroughly as it requires; do not pad unnecessarily but do not truncate genuine content either.

## Document Structure (Fixed Section Order)

MANUAL.md must contain these top-level sections in this order:

1. Title and Purpose
2. Table of Contents
3. How to Use This Manual (includes Reading Paths, Tri-Lens Markers, Contract Alignment)
4. Conceptual Foundations (Theory)
5. Quickstart Path (Practice)
6. Architecture and Runtime Model
7. Core Workflow: Build, Bind, Route, Update, Draw
8. Main Systems Reference (16 system chapters in fixed order — see below)
9. Integration Patterns and Composition Recipes
10. End-to-End Reference Application
11. Testing, Diagnostics, and Reliability
12. Performance and Scaling Guidance
13. Migration, Versioning, and Deprecation Notes
14. FAQ and Troubleshooting
15. Appendix (A: Glossary · B: Lifecycle/Event Sequence · C: System Dependency Map · D: API Quick Index · D.1: Tier Matrix · D.2: Selection Heuristics · E: Architecture Templates · F: Specifications and Option Reference)

## System Chapters (Fixed Order)

| # | Chapter title |
|---|--------------|
| 8.1 | Application Bootstrap and Host Configuration |
| 8.2 | Feature Lifecycle and Feature Types |
| 8.3 | Events, Actions, Input Mapping, and Routing |
| 8.4 | State and Observables |
| 8.5 | Controls and Control Composition |
| 8.6 | Layout Systems |
| 8.7 | Focus and Accessibility |
| 8.8 | Overlays, Dialogs, Notifications, and Command Surfaces |
| 8.9 | Scene, Window, and Task-Panel Presentation Models |
| 8.10 | Scheduling, Timing, Animation, and Transitions |
| 8.11 | Persistence and Workspace/Session State |
| 8.12 | Theme, Styling, and Visual Systems |
| 8.13 | Text, Input, Forms, and Validation Systems |
| 8.14 | Data and Dataflow Helpers |
| 8.15 | Graphics and Audio Integration Points |
| 8.16 | Telemetry, Introspection, and Operational Hooks |

## System Chapter Template

Every system chapter must include all of these subsections:

- **What it is and why it exists** — purpose and design rationale
- **Mental model and lifecycle placement** — how to think about it; when in the lifecycle it is used; **especially for systems involved in subscriptions, explicitly state which lifecycle phase subscriptions should be registered in and which phase they must be cleaned up in**
- **Primary public APIs and key types** — list the relevant exports by name
- **Typical usage flow** — numbered steps for the common case
- **Minimal example** — short runnable code block
- **Advanced pattern(s)** — at least one non-trivial composition
- **Common mistakes and anti-patterns** — specific, actionable; **especially for systems involving subscriptions, observables, or lifecycle phases, always include at least one detailed anti-pattern about subscription lifecycle and memory safety**
- **Cross-links to related systems** — reference other chapters by number
- **Back-to-top link** — `[Back to Table of Contents](#table-of-contents)`

## Navigation Rules

- Every major section must have a `[Back to Table of Contents](#table-of-contents)` link.
- All TOC links must resolve to stable anchor names.
- Keep anchor names consistent across manual updates.

## Quality Gates (All Sub-Prompts Must Pass)

1. **Coverage**: every assigned system has a chapter or explicit non-applicability note.
2. **Accuracy**: examples and statements match current behavior; no stale API names.
3. **Navigation**: TOC links resolve; back-to-top links present in every major section.
4. **Coherence**: section ordering supports learning progression.
5. **Maintenance**: obsolete content removed or quarantined in migration notes.

## Codebase Discovery Protocol

Sub-prompts must **discover API names from the actual codebase** rather than from pre-compiled
lists. The codebase has two authoritative sources that are always current:

### Primary Sources

| Source | What to read | What it provides |
|--------|-------------|------------------|
| `gui_do/__init__.py` | Tier comment sections (`# TIER N: ...`) | All public exports, grouped by tier |
| `docs/runtime_operating_contracts.md` | Sections 4 and 6 | Scheduler budget values, restore report fields |
| `docs/public_api_spec.md` | All sections | Tier descriptions, stability policy |
| `docs/architecture_boundary_spec.md` | All | Boundary rules between library and demo |
| `tests/` directory listing | Filename scan | Contract test file names |
| `demo_features/` | Key files | Real usage patterns |

### Discovery Rule

Each sub-prompt must read its relevant tier sections from `gui_do/__init__.py` **before**
writing any API names into MANUAL.md content. The tier comment headers are the canonical
grouping key. Do not copy names from prior MANUAL.md content without verifying they still
appear in `__init__.py`. Do not invent or assume names.

`gui_do/__init__.py` is intentionally organized with tier comment blocks in this form:
```python
# ============================================================================
# TIER N: SYSTEM NAME
# ============================================================================
from .some.module import TypeA, TypeB
```

Read the full `gui_do/__init__.py` to see what tiers currently exist and which names each
tier contains. New tiers added to `__init__.py` must be discovered and included in the
appropriate system chapter.

### Tier → System Chapter Mapping

Use this table to know which tiers belong to which system chapter. **Verify against
`gui_do/__init__.py`** — if new tiers exist that are not in this table, assign them to the
most thematically appropriate chapter and note the addition.

| System Chapter | Primary Tiers | Notes |
|----------------|--------------|-------|
| 8.1 Bootstrap and Host Configuration | 1, 2 | Specs, builders, bootstrap, app, scene mgmt |
| 8.2 Feature Lifecycle and Feature Types | 1 (Feature classes only), 18 | Feature types, routed wiring helpers |
| 8.3 Events, Actions, Input Mapping, and Routing | 4 (events + actions + input + focus) | Also covers `FocusManager` for routing context |
| 8.4 State and Observables | 3, 27 | Core observables + transactional store |
| 8.5 Controls and Control Composition | 12, 13 | Basic + extended + chrome controls |
| 8.6 Layout Systems | 8, 28, 29 | Layout engines + adaptive constraint + virtualization |
| 8.7 Focus and Accessibility | 4 (Focus* only), 21 | Focus managers + accessibility tree |
| 8.8 Overlays, Dialogs, Notifications, and Command Surfaces | 9 | All overlay managers |
| 8.9 Scene, Window, and Task-Panel Presentation Models | 18 (window helpers only) | Presentation helpers from Tier 18 |
| 8.10 Scheduling, Timing, Animation, and Transitions | 5 | Scheduler, tweens, coroutines, timers |
| 8.11 Persistence and Workspace/Session State | 11, 23, 32 | State machines, persistence, undo, migration |
| 8.12 Theme, Styling, and Visual Systems | 6, 22 | Theme + font + invalidation bus |
| 8.13 Text, Input, Forms, and Validation Systems | 10, 14, 24, 31 | Forms + text + async validation + schema runtime |
| 8.14 Data and Dataflow Helpers | 15, 26 | Collections + async pipeline |
| 8.15 Graphics and Audio Integration Points | 16, 20 | Rendering, graphics, audio |
| 8.16 Telemetry, Introspection, and Operational Hooks | 7, 17 | Telemetry + property inspection |

### Runtime Facts (read from docs, not hardcoded here)

- **Scheduler budget**: Read `docs/runtime_operating_contracts.md` Section 6 for the
  exact `fraction`, `floor`, and `ceiling` values.
- **Workspace restore report fields**: Read `docs/runtime_operating_contracts.md` Section 4.
- **Event types**: Read the `EventType` enum from `gui_do/__init__.py` Tier 4 source or
  `gui_do/events/gui_event.py` for the current enum members.
- **Contract test files**: List `tests/` directory and filter for `test_*_contracts.py`
  and `test_runtime_*` filenames to discover the current contract test set.

### Tier Listing (autodiscovered — do not hardcode here)

Read `gui_do/__init__.py` directly. The file is organized with tier comment headers that
identify each group. All names exported from each tier block are the authoritative public API
for that tier at the time of generation. Do not rely on any cached or prior-run list.

As a structural reference (not exhaustive): as of the last audit, tiers run from 1 through
at least 32. Check `gui_do/__init__.py` to find the actual highest tier number and any new
tiers added since the last manual generation.

---

# Original Full Specification (Reference)

The sections below are the full original specification for content requirements. Sub-prompts refer to their assigned subsections here. Do not generate output from this file directly — use the sub-prompts.

The manual is the primary learning and reference source for gui_do. It must teach the framework end-to-end, from first principles to advanced usage, while staying aligned with current code, tests, demos, and contracts.

## Verbosity Standard

The manual must be genuinely comprehensive and verbose throughout. "Verbose" means: every major concept gets multiple paragraphs of explanation that stand alone as complete understanding, not just terse bullet lists. Readers should be able to understand not only what something does but why it works that way, how it compares to alternatives, and how it connects to adjacent systems. Terse sections are appropriate only for quick-reference appendices and API signatures. Conceptual chapters, system chapters, and integration patterns must each contain substantial prose. The goal is a manual that replaces the need to read source code to understand purpose and design.

## Objective

Produce a conceptually complete MANUAL.md that:
- Teaches theory first, then practical application of that theory.
- Contains chapters for every major system exposed by gui_do.
- Uses a logical progression that maximizes user comprehension and successful implementation.
- Includes a top-level table of contents with working internal links.
- Includes back-to-top links from every major section/chapter.
- Includes appendices needed for practical day-to-day use.

## Invocation Model (Expensive, Infrequent)

Treat this as a high-cost, deep-maintenance operation. On every invocation, do a full inventory pass before writing final content.

### Required Inventory Pass

1. Discover current documentation state:
- Read existing MANUAL.md if present.
- Read README.md, TUTORIAL.md, and docs/*.md contracts/specs.
- Inspect public package surface (especially gui_do/__init__.py exports and top-level package modules).
- Use demo_features/ and tests/ as behavior evidence.

2. Build a coverage matrix:
- Existing manual topics currently covered.
- New APIs/systems/features that must be added.
- Stale or obsolete content to remove.
- Content that remains valid but needs restructuring.

3. Apply maintenance actions:
- Add missing material.
- Update changed behavior and signatures.
- Remove obsolete sections or clearly label them as legacy/deprecated only when still useful historically.
- Reorder sections when needed for better learning flow.

4. Rewrite MANUAL.md as a coherent single document (not patch-notes style).

## Source-of-Truth Priority

When conflicts exist, use this precedence:
1. Current code behavior in gui_do package.
2. Tests asserting behavior.
3. Contract/spec docs under docs/.
4. Demo features usage patterns.
5. Existing README/TUTORIAL prose.

Avoid preserving stale statements just because they already exist.

## Audience

- Primary: Developers new to gui_do.
- Secondary: Existing users needing complete API/system reference.
- Tone: Precise, technical, practical, and teachable.

## Required Document Structure (Top-Level)

Use these top-level sections in this order:

1. Title and Purpose
2. Table of Contents
3. How to Use This Manual
4. Conceptual Foundations (Theory)
5. Quickstart Path (Practice)
6. Architecture and Runtime Model
7. Core Workflow: Build, Bind, Route, Update, Draw
8. Main Systems Reference (one chapter per system)
9. Integration Patterns and Composition Recipes
10. Testing, Diagnostics, and Reliability
11. Performance and Scaling Guidance
12. Migration, Versioning, and Deprecation Notes
13. FAQ and Troubleshooting
14. Appendix

---

## Conceptual Foundations Chapter Requirements

This chapter is the most important in the manual. It must be written first and treated as the theoretical backbone that every subsequent chapter references back to. It must be very long — many paragraphs per concept, not bullet lists. Each subsection should read as a complete, standalone explanation that a developer could read in isolation and come away with a genuine mental model.

In addition to core data-driven/reactive/lifecycle theory, treat the newly implemented higher-level runtime faculties as a significant conceptual aspect in Theory, not merely an appendix detail. Explain when to use each faculty, how they compose through `RoutedRuntimeSpec` sibling specs, and how lifecycle-safe ownership/cleanup is enforced.

### Data-Driven Design

This subsection must be comprehensive — a minimum of five to eight substantial paragraphs covering all of the following points in depth:

- **What it means**: Explain that data-driven design separates the description of what a program should do from the code that carries out those actions. In gui_do this means that application structure is expressed as configuration data — specs, bindings, and descriptors — rather than as sequences of imperative calls. The runtime receives that data and performs all wiring automatically. A developer describes a scene, its features, its actions, and its windows through spec objects; the framework interprets those specs and builds the live application.

- **The spec pipeline**: Describe in detail how `HostApplicationBindingSpec` and `build_host_application_config` form the entry point. A developer populates spec objects (`FeatureSpec`, `SceneSetupSpec`, `ActionSpec`, `WindowSpec`, and dozens of others) and hands them to the builder. The builder performs a single deterministic pass that resolves all cross-references, validates requirements, and produces a fully wired `HostApplicationConfig` ready to hand to `bootstrap_host_application`. Explain why this two-step (build config then run) design is deliberate: it separates the description phase from the execution phase, making both independently testable.

- **How it differs from imperative wiring**: Describe a concrete contrast. In an imperative approach, adding a keyboard shortcut would require finding the input-handling code, inserting a new branch, wiring a callback, and ensuring cleanup on scene exit. In the data-driven approach, the developer adds one `ActionSpec` entry to the config. The framework picks it up, registers it with the action registry, routes the key through the input map, and tears it down when the scene exits — with no manual wiring. The developer never touches the router.

- **Reorganization without bootstrap impact**: Explain why internal code reorganization — moving a class from one file to another, extracting a presenter into its own module, splitting a feature into logic + presentation companions — never requires changes to bootstrap code. The bootstrap only consumes public class references and spec values, not file paths or module locations. As long as each feature package's `__init__.py` continues to export the same public names, the bootstrap is completely insulated from structural changes inside the package. This is a direct consequence of data-driven design: the data that drives the application (the spec objects and class references) is kept in one place (`__init__.py` surfaces and the config module), not scattered throughout the application's internal structure.

- **Testability**: Explain how data-driven design makes the framework trivially testable at every level. Specs can be constructed and validated in unit tests with no running display. Feature instances can be built with mock hosts. The entire app config can be assembled and inspected without starting the event loop. This determinism is only possible because the application's structure is data, not hidden inside call sequences.

- **The design philosophy behind specs**: Explain that the framework's authors chose to expose richer, named specs over primitive arguments because specs are inherently self-documenting, composable, and forward-compatible. A `ShortcutOverlaySpec` with named fields can be extended with new optional fields in future versions without breaking existing callers. A raw positional-argument API cannot offer the same stability. Specs are also the serialization boundary: they are pure data and could, in principle, be stored, loaded, or generated programmatically.

- **Where the boundary is**: Clarify what is and is not data-driven. The wiring of the application (scene graph, action registry, input routing, feature orchestration) is data-driven. The runtime behavior of individual features (what they do in `on_update`, `handle_event`, and `draw`) is imperative Python inside feature methods. The philosophy is: describe structure declaratively, implement behavior imperatively.

### Reactive Data and Observable State

This subsection must be comprehensive — a minimum of five to seven substantial paragraphs covering all of the following:

- **What reactive data means**: Explain the reactive programming model as it applies to a GUI framework. A value is reactive when changes to it automatically propagate to everything that depends on it, without the producer needing to know who the consumers are. In a traditional imperative GUI, updating a value means manually calling every UI element that displays it. In a reactive model, the value itself holds a list of subscribers and notifies them when it changes. The UI element subscribes once; after that, updates flow automatically.

- **The observable primitives**: Describe `ObservableValue`, `ObservableList`, and `ObservableDict` in depth. `ObservableValue` wraps a single value; any code that calls `.subscribe(callback)` is notified when the value changes. `ObservableList` and `ObservableDict` provide the same notification semantics for mutable collections, with change events that identify what was added, removed, or modified. Explain that these are the building blocks for all reactive state in gui_do and that virtually every piece of live data that drives UI should be expressed as one of these types.

- **Subscription lifecycle and cleanup**: Explain that subscriptions must be managed carefully. A subscription holds a reference back to the subscriber, so failing to unsubscribe when a feature or control is destroyed will result in memory leaks and callbacks firing on dead objects. Explain where to subscribe (typically in `bind_runtime` or `on_create`) and where to unsubscribe (typically in feature teardown or presenter lifecycle cleanup). Describe the pattern of storing subscription handles and calling unsubscribe in cleanup methods.

- **How controls bind to observable state**: Explain the binding model used in gui_do controls. Controls generally expose a value property that accepts either a plain value or an observable. When bound to an observable, the control registers an internal subscription and refreshes its display whenever the observable changes. This means the feature code never needs to touch a control to update its displayed state — it only changes the observable, and the control updates itself. Describe why this is the correct approach: it keeps features decoupled from specific control implementations and makes it easy to swap one control for another without changing the data logic.

- **Derived and computed state**: Describe patterns for building derived state. When one observable should always reflect a function of another (for example, a label text that should always show the count of items in an observable list), the right approach is a subscriber that writes to a second observable whenever the source changes. Explain when this is appropriate versus when a direct binding is better. If `ComputedValue` exists in the public API, describe it specifically; otherwise describe the manual derivation pattern.

- **Cross-feature reactive state**: Explain that observable values are the preferred mechanism for features to share live data. One feature owns an `ObservableValue` and exposes it through its public interface; other features subscribe to it. This is looser coupling than direct method calls: the producing feature never knows who is observing, and observers do not depend on the producer's internal implementation. Describe how this is set up during `bind_runtime` when features can access each other's state through the host or through a shared state store.

- **Anti-patterns**: Describe common reactive mistakes in detail: polling an observable in `on_update` instead of subscribing (creates unnecessary CPU load and introduces latency), subscribing in `build` before the runtime is ready (subscriptions created before bind_runtime may fire before controls exist), forgetting to unsubscribe (produces memory leaks and phantom callbacks), and sharing mutable plain Python objects across features instead of observables (breaks the reactive contract and prevents automatic UI updates).

### Feature Composition and Lifecycles

This subsection must be comprehensive — a minimum of six to eight substantial paragraphs covering all of the following:

- **What a Feature is**: Explain that a Feature is the primary unit of application behavior in gui_do. It is a self-contained object that declares what resources it requires from the host, builds its own UI elements, registers its own event handlers, and tears itself down cleanly. Features are composable: an application is a collection of features that coexist in scenes, each managing its own slice of the UI and data. The framework orchestrates their lifecycle phases in the correct order and routes events to the correct feature.

- **Feature types and when to use each**: Give a detailed explanation of each Feature type:
  - `DirectFeature`: Renders directly to the screen surface on every update. Use for background elements (animated backdrops, full-screen effects) that do not need the control tree. It is the lowest-overhead feature type.
  - `Feature`: The standard feature. Builds controls in the scene's control tree during `build`. Participates in focus, hit-testing, and event routing. Use for any feature that shows interactive UI.
  - `LogicFeature`: Has no UI of its own. Exists to hold domain logic, manage shared state, run background computations, and publish results that other features react to. Use when behavior needs to be separated from presentation and tested in isolation.
  - `RoutedFeature`: A Feature that also participates in the action routing infrastructure. It can define route targets that receive named messages and dispatch them to specific handler methods. Use when a feature must respond to framework-level actions or coordinate with the action registry.

- **Lifecycle phases in depth**: Describe every lifecycle phase with precision and detail:
  - `build(host)`: Called once when the scene is being constructed. Use this phase to create controls, add them to the scene tree, build window specs, and set up any static structure that does not depend on runtime state. `host` provides all resources declared in `HOST_REQUIREMENTS`. Controls created here exist for the lifetime of the scene.
  - `bind_runtime(host)`: Called after all features in the scene have completed `build`. By this point, all controls exist and all sibling features are built. Use this phase to subscribe to observable values, bind controls to data, register callbacks, initialize state from runtime sources (screen size, settings, etc.), and wire up cross-feature interactions.
  - `handle_event(host, event)`: Called for routed `GuiEvent` objects that reach the feature. The routing layer filters by scene, focus, and overlay state before calling this method. Return `True` to consume the event and stop propagation; return `False` or `None` to pass it on.
  - `on_update(host)`: Called every frame. Use for per-frame logic, scheduler interaction, and lightweight state transitions. Keep this method fast; avoid expensive computation here.
  - `draw(host, surface, theme)`: Called every frame after update. Use for custom drawing paths that bypass normal control rendering when needed.
  - `shutdown_runtime(host)`: Called during teardown for runtime bindings. Unsubscribe/disconnect/cancel all runtime resources and unwind routed runtime scope ownership.

- **HOST_REQUIREMENTS protocol**: Explain the `HOST_REQUIREMENTS` dictionary in detail. It declares what attributes the host must provide for each lifecycle method. The framework validates these at startup and provides clear error messages for missing bindings. This protocol is how features express their dependencies declaratively — a feature says "I need `app`, `screen_rect`, and `scene_presentation` in `build`" and the framework ensures those are available before calling the method. This replaces constructor injection and makes dependency relationships explicit and machine-verifiable.

- **Feature messaging and coordination**: Describe the inter-feature communication model. Features do not hold references to each other directly. Instead, they communicate through `FeatureMessage` publishing. A feature publishes a message by name with optional payload; the framework delivers it to any feature that has registered a handler for that name. This is the loose-coupling mechanism that prevents features from depending on each other's implementations. Describe common patterns: a LogicFeature publishing a "data_ready" message when a background computation finishes, a RoutedFeature listening for route-targeted messages to update its display, and features using observable state as a shared bus when tighter coupling is acceptable.

- **Scene assignment and multi-scene composition**: Explain how features declare their scene membership via `scene_name`. A feature belongs to exactly one scene (or the global scene). The framework activates and deactivates features as scenes transition, calling lifecycle teardown on the departing scene's features and lifecycle build/bind on the arriving scene's features. Describe how this makes scene transitions safe: features from the previous scene do not receive events or update calls after the transition, so there is no risk of stale state from one scene leaking into another.

- **The folder/package composition convention**: Explain the established organizational convention for demo_features and how it should be followed in any similar project. Each feature package lives in its own folder. The `__init__.py` is the sole public surface — it exports the Feature class and any public types, and nothing else. Internal files are separated by concern: the feature file owns the Feature class and lifecycle methods; the presenter file owns the WindowPresenter; the specs file owns shared constants and spec objects; logic companion files own background computation; standalone data types live in their own files. This separation makes each file's purpose immediately clear from its name and prevents concerns from bleeding across files. Crucially, the bootstrap code never imports from internal submodules — it only imports from the package surface. This means any internal reorganization is completely transparent to bootstrap consumers.

- **Composition recipes**: Describe the most common multi-feature patterns:
  - Logic + presentation split: a `LogicFeature` runs computations and publishes results via observables; a `RoutedFeature` subscribes to those observables and drives the UI. This is the cleanest separation and makes both halves independently testable.
  - Presenter pattern: a `WindowPresenter` subclass handles window layout and control construction, while the Feature handles lifecycle and routing. The Feature lazily imports the presenter in `build` to avoid circular imports.
  - Background feature pattern: a `LogicFeature` drives a cooperative scheduler or coroutine for long-running work, publishing progress and results to observables that the UI feature displays.

---

## Main Systems Reference Requirements

Create distinct chapters for each major gui_do system area that is currently exposed and relevant. At minimum, ensure coverage for:
- Application bootstrap and host configuration
- Feature lifecycle and feature types
- Events, actions, input mapping, and routing
- State and observables
- Controls and control composition
- Layout systems
- Focus and accessibility
- Overlays, dialogs, notifications, and command surfaces
- Scene/window/task-panel presentation models
- Scheduling, timing, animation, and transitions
- Persistence and workspace/session state
- Theme/styling and visual systems
- Text/input/forms and validation systems
- Data and dataflow helpers
- Graphics/audio integration points (if exposed)
- Telemetry/introspection and operational hooks

For each system chapter include:
- What it is and why it exists.
- Mental model and lifecycle placement.
- Primary public APIs and key types.
- Typical usage flow.
- Minimal example.
- Advanced pattern(s).
- Common mistakes and anti-patterns.
- Cross-links to related systems.
- Back-to-top link.

If a listed area is not currently exposed/public, explicitly state that status and avoid fabricating APIs.

## Theory and Practice Pairing

For each major theoretical concept, provide a practical section immediately after it:
- Concept explanation.
- Implementation pattern.
- Runnable or near-runnable example.
- Validation/testing note.

## Table of Contents and Navigation Rules

- Place full table of contents near the top (after title/purpose).
- Include all major sections and system chapters.
- Every major section must include:
  - A link target from the TOC.
  - A Back to Table of Contents link.
- Ensure anchor names are consistent and stable.

## Completeness Rules

- The manual must be single-file and self-contained.
- Prefer public API names; do not teach internal-only symbols as primary guidance.
- Include enough detail for users to build non-trivial applications without leaving MANUAL.md.
- Include practical recipes that span multiple systems (for example: routed feature + actions + overlay + persistence).

## Appendix Requirements

Include appendices that materially improve usability, such as:
- Glossary of gui_do terminology.
- Lifecycle and event-routing sequence reference.
- System dependency map (which systems depend on which).
- API quick index by topic.
- Common architecture templates.
- Optional: Deprecated/legacy notes (only if still relevant to maintenance).

## Quality Gates (Must Pass Before Finalizing)

1. Coverage gate:
- Every major exposed system has a chapter or explicit non-applicability note.

2. Accuracy gate:
- Examples and statements match current behavior.
- No known stale API names remain.

3. Navigation gate:
- TOC links resolve.
- Back-to-top links present in every major section.

4. Coherence gate:
- Section ordering supports learning progression from fundamentals to advanced.
- No contradictory guidance across chapters.

5. Maintenance gate:
- Obsolete content has been removed or clearly quarantined in migration/deprecation notes.

## Output Requirements

- Write/update MANUAL.md in repository root.
- Deliver complete final manual content, not an outline.
- Keep section titles stable where practical to preserve anchor links across revisions.
- Include concise, actionable examples throughout.

## Suggested Sensible Enhancements (Apply by Default)

In addition to the base request, include:
- A short "Reading Paths" section for beginner, intermediate, and maintainer audiences.
- A "Known Non-Goals" subsection to prevent misuse and wrong expectations.
- A "Contract Alignment" note that points readers to docs/ contracts when behavior is normative.
- A "Maintainer Diff Checklist" subsection under testing/maintenance guidance that is explicitly designed for future manual regeneration passes.

Do NOT include a version/generation header, pipeline metadata, generation date, or
"What Changed Since Last Manual" section. Each generation is self-contained and describes
the current state of the codebase only.

## Maintainer Diff Checklist Requirements

Require a concrete checklist that includes at minimum:

1. Inventory delta checks:
- root export changes (gui_do/__init__.py)
- docs contract changes (docs/*.md)
- contract/runtime test additions under tests/
- demo composition pattern changes under demo_features/

2. Content integrity checks:
- added/removed APIs reconciled across chapters and appendix index
- examples updated to avoid stale symbols
- abstraction-level placement validated (Tier 1-first guidance retained)

3. Navigation checks:
- TOC and anchor integrity for all new/changed sections
- back-to-top links preserved in major sections

4. Operational checks:
- high-priority contract tests rerun
- end-to-end reference listing assumptions revalidated

## Non-Goals

- Do not split output across multiple files.
- Do not produce a lightweight summary-only manual.
- Do not preserve outdated sections purely for historical completeness.
