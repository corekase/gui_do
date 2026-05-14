---
name: Document
description: Rebuild README.md and TUTORIAL.md from the current codebase. The MANUAL.md is separate (Manual.prompt.md pipeline).
---

## Execution Order Requirement

All work in this prompt must run sequentially and never concurrently.

- Perform generation and any sub-generation in strict order.
- Do not parallelize reads, drafting, rewrites, compliance checks, or enrichment steps.
- Finish each step fully before starting the next step.

## Scope

This prompt generates two files only:

1. **README.md** — a high-level project overview that sells gui_do and links to TUTORIAL.md and MANUAL.md as the primary learning resources.
2. **TUTORIAL.md** — a complete step-by-step project tutorial that teaches the full gui_do programming model from zero.

MANUAL.md is produced by a separate prompt pipeline (`Manual.prompt.md`). Do not regenerate or modify MANUAL.md from this prompt.

Manual-first execution policy: treat `MANUAL.md` as already refreshed by the preceding Manual prompt run. For this prompt, consider `MANUAL.md` the current reference surface and link to it frequently for deeper system and specification details.

### File Presence Modes (Required)

Apply this two-mode behavior for `README.md` and `TUTORIAL.md`:

- If a target file already exists, always update it in place (do not skip and do not replace with a brand-new rewrite unless required to restore compliance).
- If a target file does not exist, generate that missing file from scratch.
- If one exists and the other is missing, update the existing file and generate the missing file from scratch in the same run.
- If both exist, update both.
- If both are missing, generate both from scratch.

---

## Autodiscovery Requirement

Before writing either file, autodiscover the current state of the codebase:

1. **Read `gui_do/__init__.py`** from top to bottom. Collect all tier comment headers and all exported names. Use these as the authoritative API surface. Do not use names from memory or prior runs — verify against the current file.
2. **Read `gui_do/_version.py`** to get `__version__` and `__demo__`.
3. **List `demo_features/`** and read each package `__init__.py` to understand what demo patterns are available.
4. **Read `docs/runtime_operating_contracts.md`** for behavioral guarantees (scheduler budget, restore report fields, event normalization contract).
5. **Read `MANUAL.md`** title and TOC only (first ~80 lines) to extract the exact section headings to link to.
6. **Read `TUTORIAL.md`** if it exists, to determine whether to generate from scratch or update.

Use this discovered data exclusively. Every API name in examples must be verified present in `gui_do/__init__.py`.

---

## Documentation Principles

gui_do is a data-driven, feature-lifecycle-oriented GUI framework built on pygame.

Primary truth sources for architecture and API behavior:
- `gui_do/__init__.py` — authoritative public API (tiers 1–32)
- `gui_do/features/data_driven_runtime.py`
- `gui_do/features/feature_lifecycle.py`
- `gui_do/app/gui_application.py`
- `gui_do/overlays/` (especially `overlay_manager.py`, `shortcut_help_overlay.py`, `toast_manager.py`)
- `demo_features/` as runnable reference patterns


## New Runtime Faculties Coverage (Required)

When generating or updating README.md and TUTORIAL.md, include current guidance for the routed runtime facilities and all higher-level runtime faculties (see MANUAL.md for the current list and details):

- Explain feature-owned runtime scope semantics and lifecycle pairing (`bind_runtime` setup, `shutdown_runtime` teardown).
- Include at least one concise tutorial/example pattern that references declarative runtime wiring with:
  - `ServiceBindingSpec` / `ServiceConsumerSpec`
  - One reactive effect spec (`StoreSubscriptionSpec`, `StoreSelectorSpec`, `ObservableEffectSpec`, or `SignalEffectSpec`)
  - `FeatureOperationSpec` with `FailurePolicySpec` for operation-level retry/timeout behavior
- Include guidance for all higher-level runtime faculties and where they fit:
  - runtime policy/admission control (`RuntimePolicySpec`, `PolicyDecision`, `RuntimePolicyEngine`)
  - effect lifetime ownership (`EffectBindingSpec`, `EffectLifetimeOrchestrator`)
  - routed event stream pipelines (`EventPipelineStageSpec`, `EventPipelineSpec`, `EventPipelineRuntime`)
  - durable operation queue/recovery (`DurableOperationBindingSpec`, `DurableOperationQueueSpec`, `DurableQueueRecord`, `DurableOperationQueueRuntime`)
  - capability contracts/negotiation (`CapabilityProviderSpec`, `CapabilityRequirementSpec`, `CapabilityContractRuntime`)
  - incremental projections (`ProjectionNodeSpec`, `ProjectionSpec`, `ProjectionRuntime`)
  - dependency validation (`FeatureDependencySpec`)

**Manual-first policy:** MANUAL.md is always current for these topics. Link to MANUAL.md for all faculty/system details and do not duplicate full explanations here.
  - workflow orchestration (`WorkflowStepSpec`, `WorkflowSpec`, `WorkflowCoordinator`)
  - recompute orchestration (`RecomputeNodeSpec`, `RecomputeOrchestrator`)
  - QoS/backpressure (`QoSPolicySpec`, `QoSPolicyRuntime`)
  - health/degradation probes (`HealthProbeSpec`, `FeatureHealthRuntime`)
  - replay capture (`ReplaySpec`, `RuntimeReplayHarness`)
  - hot-swap policy (`ReplacePolicySpec`, `FeatureHotSwapManager`)
- Ensure wording distinguishes declarative wiring (specs) from imperative feature behavior.
- Keep examples on public root imports only and verify names against `gui_do/__init__.py`.
- Prefer linking to relevant MANUAL.md chapter/appendix targets instead of duplicating long explanation blocks.
- Because `Manual.prompt.md` always runs first, treat MANUAL.md as current for faculty details: keep README/TUTORIAL faculty explanations concise and link frequently to MANUAL.md theory and system chapters.

## Demo Features Organizational Convention

This convention must be reflected accurately in documentation:

**Folder-per-feature/scene**: Each subfolder under `demo_features/` is exactly one feature package (or a tightly related cluster).

**Best-practice package layout**: Treat `demo_features/` as the canonical organizational model for user projects:
- One folder per feature.
- One package `__init__.py` per feature folder as the only public import surface.
- Feature internals split into focused files inside that same folder (for example `*_feature.py`, `*_presenter.py`, `*_specs.py`, `*_logic_feature.py`).
- Avoid cross-feature imports of internal submodules; import only feature package roots.

**`__init__.py` is the sole public surface**: All cross-package imports target the package root only. Internal reorganizations have zero effect on bootstrap. The data (specs and config) drives wiring; code location is irrelevant to bootstrap.

**File-per-concern within a folder**: Each file inside a feature folder owns exactly one concern (`*_feature.py`, `*_presenter.py`, `*_specs.py`, `*_logic_feature.py`).

Documentation must present this folder+`__init__.py` model as the established pattern and must not suggest internal submodule imports at any layer.

---

## README.md Generation

### Generate vs Update Behavior

- If README.md does not exist: generate from scratch using all required sections below, constructing the header from the Media Block spec and the badge URL verbatim.
- If README.md exists: read it fully, then update sections that are stale, incomplete, or missing newer patterns. Preserve sections that are accurate and match the required structure. Do not silently omit required sections. Always carry forward the preserved header elements (heading, demonstration block, badge) exactly as specified under **Preserved README Header Elements**.

### Purpose

README.md is a high-level project overview. Its job is to:
- Explain what gui_do is in plain English
- Communicate its strengths and distinguishing characteristics
- Describe the range of applications it is suited for
- Provide a minimal taste of the programming model
- Point developers to TUTORIAL.md and MANUAL.md as the primary learning resources

README.md is **not** a tutorial, reference manual, or API listing. Those live in TUTORIAL.md and MANUAL.md respectively. The README should leave the reader wanting to explore those documents.

### Required Section Order

Write README.md with exactly these top-level sections, in this order:

#### 1. Overview

- Unittest badge (first line, before the project heading).
- Project name (`gui_do`) heading, followed by the latest demo video block (see Media Block spec below).
- One-paragraph plain-English description (3–5 sentences):
  - What gui_do is (a Python GUI framework built on pygame)
  - The central programming model (declarative specs, feature lifecycle, reactive state)
  - What it automates away (event routing, overlay dispatch, focus management, scene transitions, lifecycle sequencing)
  - Who it is for (Python developers building desktop tools, game UIs, simulations, and interactive applications)

#### 2. Strengths

A focused list (6–10 items) of gui_do's distinguishing characteristics. Each item is a short heading + one-sentence explanation. Cover:
- Declarative runtime wiring — specs describe what, bootstrap builds how
- Feature lifecycle isolation — each feature owns its build, bind, update, draw, and teardown
- Reactive state — `ObservableValue`, `ObservableList`, `ObservableDict` trigger UI updates without polling
- Composable overlays — dialogs, toasts, tooltips, command palette, context menus with consistent routing
- Tiered API surface — 32 tiers from high-level bootstrap helpers down to 2D scene graph and audio
- Scene management — multi-scene apps with animated transitions and scene-scoped routing
- Persistence and migration — workspace state saved/restored with versioned snapshot migration
- Accessibility and focus — semantic accessibility tree, focus rings, live region announcements
- Built-in diagnostics — telemetry spans, property inspector, event recorder/playback
- Extensible without framework changes — new features add behavior by implementing lifecycle methods

#### 3. Use Cases

A prose section (or short list with brief descriptions) covering the range of applications gui_do is suited for:
- Developer tools and internal utilities (dashboards, inspectors, data explorers)
- Game interfaces and HUDs (particle effects, tile maps, 2D scene graph, audio cues)
- Interactive simulations (cellular automata, physics visualizations, parameter explorers)
- Data visualization tools (sortable/filterable lists, grids, charts with dirty-region rendering)
- Multi-window workbench applications (tabbed panels, task panels, floating tool windows)
- Rapid prototyping of GUI layouts with the constraint and flex layout systems

#### 4. Quick Look

A single minimal runnable listing demonstrating the core pattern. Title this section exactly: `Quick Look`. The listing must:
- Use `HostApplicationBindingSpec`, `build_host_application_config`, `bootstrap_host_application`
- Define one `Feature` subclass with `build` and `bind_runtime`
- Show one `ObservableValue` wired to a `LabelControl`
- Include the run loop (`host.app.run_entrypoint`)
- All names verified present in `gui_do/__init__.py`

#### 5. Documentation

This section is the primary navigation hub. Write it with the following structure:

```
## Documentation

| Document | Purpose |
|----------|---------|
| [TUTORIAL.md](TUTORIAL.md) | Step-by-step project tutorial — start here if you are new to gui_do |
| [MANUAL.md](MANUAL.md) | Complete developer reference for all systems and APIs |
```

Then add a brief paragraph explaining the split:
- TUTORIAL.md teaches the framework through building a complete project from scratch, explaining both how and why at every step.
- MANUAL.md is the comprehensive reference organized by system, with API tables, usage patterns, examples, integration recipes, and appendices.

#### 6. Installation

One section, short and direct:
- Local install from repository root: `python -m pip install -e . --no-deps`
- Dependency note: requires `pygame` and `numpy`

#### 7. Project Structure

Brief overview of the repository layout: `gui_do/` (library), `demo_features/` (runnable reference patterns), `tests/` (contract and behavioral tests), `docs/` (architecture contracts), `TUTORIAL.md`, `MANUAL.md`.

#### 8. See Also

Links to:
- `TUTORIAL.md` and `MANUAL.md` (primary learning resources)
- `demo_features/` (living reference patterns)
- `docs/` (architecture boundary and runtime contracts)
- `gui_do/__init__.py` (authoritative public API source)

### Preserved README Header Elements

If README.md exists, read it before generating and extract its header elements (heading, demonstration block URL, badge text) for reuse. If README.md does not exist, construct the header from the Media Block spec and the verbatim badge line below — no file read is needed. Regardless of where these elements appear in the existing file, always output them in the canonical order below. The following elements must appear in the generated file regardless of which path applies:

- **Project heading**: `# gui_do` (second line of the file, immediately after the unittest badge)
- **Latest Demonstration block**: the `### Latest Demonstration` section with its surrounding `---` dividers and the `<a href=...><img ...></a>` video thumbnail block. Read `gui_do/_version.py` `__demo__` and use that value as `URLPART`. If README.md existed and the URL already matched, preserve it unchanged; otherwise construct it from the Media Block spec below.
- **Unittest badge**: `[![unittest](https://github.com/corekase/gui_do/actions/workflows/unittest.yml/badge.svg?branch=main)](https://github.com/corekase/gui_do/actions/workflows/unittest.yml)` — copy this line verbatim; do not alter the URL or badge text.

No whitespace rule: there must be no blank line between the unittest badge line and the `# gui_do` project heading.

The ordering of these three elements must remain:
1. Unittest badge line (line 1 of the file)
2. `# gui_do` (line 2, immediately adjacent to line 1 with no intervening blank line)
3. `### Latest Demonstration` block (with `---` dividers)

### Media Block Spec

Read `gui_do/_version.py` for `__demo__`. Use its value as `URLPART`.

Position: immediately below the `# gui_do` project name heading. Header order is always: badge first, then heading, then demonstration block.

Exact format:
```
### Latest Demonstration

---

<a href="https://www.youtube.com/watch?v=URLPART"><img src="https://img.youtube.com/vi/URLPART/0.jpg" alt="Demo Video"></img></a>

---
```

### Content Rules for README.md

**DO:**
- Keep it high-level and motivating — not a reference
- Link TUTORIAL.md and MANUAL.md as the primary next steps after every section that might prompt deeper questions
- Use current API names (verified from autodiscovery)
- Keep the listing in Quick Look to ≤ 40 lines

**DON'T:**
- Include a full API reference, tier listing, or control catalog — that belongs in MANUAL.md
- Include step-by-step tutorial content — that belongs in TUTORIAL.md
- Use private/internal symbols
- Add sections not listed above

---

## TUTORIAL.md Generation

### Purpose

TUTORIAL.md is a complete, standalone, beginning-to-end tutorial that teaches gui_do by building a real project. It must explain both **how** to do things and **why** you are doing them at every step. A reader who finishes the tutorial should understand the gui_do programming model well enough to build their own feature-complete application.

### Generate vs Update Behavior

- If TUTORIAL.md does not exist: generate from scratch using all required sections below.
- If TUTORIAL.md exists: read it fully, then update sections that are stale, incomplete, or missing newer patterns. Preserve sections that are accurate. Do not silently omit required sections.

### Audience

Developers with working Python knowledge who are new to gui_do. They may be new to GUI frameworks entirely. No assumed knowledge of pygame internals.

### The Project

The tutorial builds a single complete project from scratch — a **multi-feature interactive application** that the reader constructs step by step. Choose a project that demonstrates the full programming model naturally:

- At least two features with distinct responsibilities
- Observable state shared or communicated between features
- At least one action wired to a keyboard shortcut
- A reactive UI (label or display that updates automatically when state changes)
- A clean shutdown

Good example projects: a note-taking tool, a simple dashboard with a counter and log, a two-panel data explorer. Pick one that is genuinely usable, not a toy.

State the chosen project clearly at the start of the tutorial and keep the narrative focused on building it throughout.

### Autodiscovery for Tutorial

Before writing tutorial content:
1. Read `gui_do/__init__.py` fully to verify every API name used in examples.
2. Read `demo_features/__init__.py` and subdirectory `__init__.py` files to identify patterns available as reference.
3. Read `MANUAL.md` section headings (TOC) to identify cross-reference targets.

Every API name in the tutorial must be verified present in `gui_do/__init__.py`. Do not use names from memory.

### Required Tutorial Structure

Write TUTORIAL.md with exactly these sections, in this order. Each section must include both explanatory prose and runnable code snippets. The narrative thread of building the project must run continuously through all sections.

#### 1. Introduction

- What gui_do is (2–3 plain-English sentences)
- What we will build: state the project, name its features, describe the end result
- Prerequisites: Python, pip, pygame, numpy; no GUI framework experience required
- Link to MANUAL.md for deeper reference on any topic covered here

#### 2. Core Concepts

Introduce the three core ideas before any code:

**Declarative specs vs imperative wiring.** Explain why gui_do uses data objects (specs) to declare application structure instead of imperative call sequences. Explain the benefit: the bootstrap system reads specs and wires everything automatically, so features never need to know about each other's internals.

**Reactive state.** Explain `ObservableValue` — a value that notifies subscribers when it changes. Contrast with polling. Show the subscribe/unsubscribe pattern. Mention `ObservableList` and `ObservableDict` for collections. Briefly mention `ComputedValue` for derived state.

**Feature lifecycle.** Explain the runtime phases (`build`, `bind_runtime`, `handle_event`, `on_update`, `draw`, `shutdown_runtime`) and the intent of each. Reflect current signatures in prose/examples (`on_update(host)`, `draw(host, surface, theme)`). Explain that all features in a scene complete `build` before any `bind_runtime` runs — this is a framework guarantee, not a coincidence. Explain that subscriptions are set up in `bind_runtime` and torn down in `shutdown_runtime`.

#### 3. Installation and Setup

- Install command: `python -m pip install -e . --no-deps` (local editable install, no binary dependency compilation)
- Dependencies: requires `pygame` and `numpy` (numpy is used internally for pixel buffer operations via `PixelArray`)
- Verify install: `python -c "import gui_do; print(gui_do.__version__)"`
- Minimal imports needed to start: `from gui_do import HostApplicationBindingSpec, build_host_application_config, bootstrap_host_application, Feature`
- Clarify the two startup paths: declarative bootstrap (recommended, covered in this tutorial) vs manual `GuiApplication` construction (advanced, see MANUAL.md)

#### 4. Your First Feature

*Narrative: build the first piece of the project.*

Step by step, with a numbered sequence and a code snippet after each step:

1. **Define the feature class.** Show a `Feature` subclass with an empty `build` method. Explain why `Feature` is the right choice here (vs `DirectFeature`, `RoutedFeature` — covered in Section 6). Explain that `build` is where the control tree is constructed.
2. **Add a control.** Show adding a `LabelControl` inside `build`. Explain that controls are layout objects inside the feature's region, not independent widgets. Explain `host.screen_rect` as the available canvas.
3. **Declare the config.** Show `HostApplicationBindingSpec` with a `SceneBundleBindingSpec` and a `FeatureSpec`. Explain each field. Show `build_host_application_config`.
4. **Bootstrap and run.** Show `bootstrap_host_application(config)` and `host.app.run_entrypoint(target_fps=60)`. Explain what `bootstrap_host_application` does (reads specs, initializes all systems, returns the host object). Explain `run_entrypoint` (starts the frame loop).
5. **Show the full listing.** Combine all steps into a single runnable file. The reader should be able to run it and see a window.

#### 5. Reactive State: Making the UI Respond

*Narrative: add the project's first interactive element.*

1. **Introduce `ObservableValue`.** Show declaring one on the feature. Explain that it is just a value — setting `.value` fires all subscribers.
2. **Add a button.** Show a `ButtonControl` with an `on_click` callback that updates the observable.
3. **Wire the observable to the label.** In `bind_runtime`, show `self._sub = self._count.subscribe(lambda v: setattr(self._label, "text", f"Count: {v}"))` — or equivalently the property-setter form `self._label.text = f"Count: {v}"` inside the callback. Explain why this is in `bind_runtime` and not `build` (controls exist after build; subscriptions need a live control tree).
4. **Unsubscribe in `shutdown_runtime`.** Show `if self._sub: self._sub(); self._sub = None`. Explain why: subscriptions hold references; failing to unsubscribe causes memory leaks and callbacks firing after the feature is gone.
5. **Run the updated listing.** Show the full file for this step.

#### 6. Feature Types

Explain when to use each type. Use the project as context:

- **`Feature`** — standard choice; all five lifecycle methods; use when building a visual feature with state and interaction.
- **`DirectFeature`** — full control; no default method stubs; use when you need to override the exact set of lifecycle methods with no defaults. Rarely needed.
- **`DirectFeature`** — feature subtype with direct-event/update/draw hooks for high-control rendering paths; use when bypassing standard control rendering/event paths is intentional.
- **`LogicFeature`** — no draw or control tree; use for background computation, cross-feature coordination, or data pipeline management.
- **`RoutedFeature`** — extends `Feature` with topic-based message dispatch; use when declaring hotkeys, shortcut overlays, and event subscriptions via `RoutedRuntimeSpec` and `RoutedFeatureLifecycleSpec`.

#### 7. A Second Feature and Feature Communication

*Narrative: add the project's second feature.*

1. **Define the second feature.** It has a different visual region and a different responsibility in the project.
2. **Shared state via `ObservableValue`.** Show two approaches:
   - Both features reference an observable stored on one of them, accessed through the host (if the host carries it as an attribute set in `build`).
   - Or: use `FeatureMessage` to send a typed message from one feature to another via `FeatureManager`.
3. **Feature messaging.** Show a concrete `FeatureMessage` subclass, publishing it from one feature, and receiving it in another. Explain when to use messaging (when features should not hold direct references to each other).
4. **Updated full listing** showing both features working together.

#### 8. Actions and Keyboard Shortcuts

*Narrative: wire a keyboard shortcut to the project's primary action.*

1. **Declare an `ActionSpec`.** Show adding it to `HostApplicationBindingSpec` with an `ActionHotkeySpec` (key name). Explain that this is the entire registration — no manual input map wiring needed.
2. **Handle the action in the feature.** For a plain `Feature`, show binding an action callback via `host.actions.bind(action_id, callback)` in `bind_runtime`, and unbinding in `shutdown_runtime`.
3. **`RoutedFeature` shortcut.** Show the same pattern using `RoutedRuntimeSpec` with the action name — demonstrate that the routed lifecycle handles binding and unbinding automatically via `bind_routed_feature_lifecycle` / `shutdown_routed_feature_lifecycle`.
4. **Shortcut help overlay.** Show adding `ShortcutOverlaySpec` to `RoutedRuntimeSpec` so users can discover keyboard shortcuts by pressing a configurable toggle key.
5. **Updated listing** showing the action wired and triggering behavior in the project.

#### 9. Spec Reference for Builders

A concise reference section (not a tutorial — link to MANUAL.md for full detail). Include one short paragraph + minimal snippet for each:

- **`FeatureSpec`** — declares a feature class and its scene membership
- **`FeatureSpec`** — declares a feature attribute slot and factory used during bootstrap
- **`SceneBundleBindingSpec`** — declares a named scene with transition style and escape behavior
- **`ActionSpec` + `ActionHotkeySpec`** — declares a named action with optional keyboard binding
- **`ShortcutOverlaySpec`** — configures the shortcut discovery overlay
- **`RoutedRuntimeSpec` + `RoutedFeatureLifecycleSpec`** — declarative bundle of runtime wiring for a `RoutedFeature`, including higher-level runtime faculties
- **Higher-level runtime faculties** — concise references for policy/effects/pipelines/durable-queue/capability/projection plus dependency/workflow/recompute/QoS/health/replay/hot-swap specs and managers
- **`ToastManager`** — brief note on how to show a toast notification from a feature (via `host.toasts.show(...)`)
- Link each to the corresponding section in MANUAL.md

#### 10. Complete Project Listing

The full, runnable, end-to-end listing of the project built throughout the tutorial. Requirements:

- Minimum 60 lines of meaningful application code (not counting blank lines and comments)
- Two or more features with distinct responsibilities
- Observable state wired to UI controls
- At least one keyboard action with `ActionSpec`
- At least one `RoutedFeature` with `RoutedRuntimeSpec`
- Clean subscription teardown in `shutdown_runtime`
- A comment above each logical section explaining what it does and why

This listing must run as-is. All imports must be from `gui_do` root. All API names verified in `gui_do/__init__.py`.

#### 11. Next Steps

- What to read next: MANUAL.md (link directly), then `demo_features/` as living examples
- What to explore: overlays, persistence, scene navigation, telemetry, graphics
- The MANUAL.md sections most relevant to common next steps: system chapters 8.1 (bootstrap), 8.2 (features), 8.3 (events/actions), 8.4 (state/observables)
- Encouragement: `data_driven_runtime.py` and `feature_lifecycle.py` are readable and well-commented; reading them will demystify bootstrap entirely

### Content Rules for TUTORIAL.md

**DO:**
- Explain **why** before showing how at every step
- Keep the project narrative continuous — every section advances the same project
- Show the full updated listing at the end of each step that changes the code
- Use public APIs only — everything must be importable from `gui_do` root
- Cross-reference MANUAL.md for deeper coverage of any topic

**DON'T:**
- Use private/internal symbols (`_` prefix) in any example
- Jump to a new topic without explaining why it is needed for the project
- Omit `shutdown_runtime` cleanup for any subscription set up in `bind_runtime`
- Add extra top-level sections outside the required structure
- Use stale API names — verify every name against the current `gui_do/__init__.py`

---

## Post-Generation Compliance Pass

After generating both files, run a compliance pass:

1. **README.md header check.** Confirm the file opens with the unittest badge line on line 1, then `# gui_do` on line 2, then the `### Latest Demonstration` block (with `---` dividers). Confirm there is no blank line between line 1 and line 2. If the badge appears anywhere else, move it to line 1. Confirm the video URL uses the `__demo__` value from `gui_do/_version.py`. Confirm the badge URL is the exact verbatim string from the existing README.
2. **README.md structure check.** Confirm the eight required sections are present in order after the header.
3. **TUTORIAL.md structure check.** Confirm all 11 required sections are present in order. Confirm the install command is `python -m pip install -e . --no-deps`. Confirm no private/internal symbol appears in any code example.
4. **TUTORIAL.md enrichment pass (required after main generation).** Re-read TUTORIAL.md from top to bottom and enrich any section that is thin on explanation or examples.
  - Add explanatory prose wherever reasoning is missing (especially "why" and lifecycle intent).
  - Add or expand runnable code snippets wherever a required concept lacks a concrete example.
  - If a step says to show a full updated listing, ensure that listing is present and complete for that step.
  - Keep the existing 11-section order unchanged; enrich content in place rather than adding new top-level sections.
  - Normalize markdown rendering for double-underscore names so they are never misparsed as emphasis. For names like `__init__.py`, `__version__`, and `__demo__`, use inline code formatting consistently.
  - Re-verify every added API name against `gui_do/__init__.py`.
5. **README/TUTORIAL identifier formatting check.** Re-read both files and normalize any raw double-underscore identifiers that could be misparsed by markdown emphasis. Ensure names like `__init__.py`, `__version__`, and `__demo__` are rendered with inline code formatting.
6. **API name verification.** For every name used in code listings in both files: confirm it appears in `gui_do/__init__.py`. Flag and fix any names that do not.
7. **Cross-reference check.** Confirm TUTORIAL.md links to MANUAL.md in Sections 1, 9, and 11. Confirm README.md links to both TUTORIAL.md and MANUAL.md in the Documentation section.
8. **Run a text search** (e.g. `rg "MANUAL_PLACEHOLDER\|from gui_do\." README.md TUTORIAL.md`) to catch any internal submodule imports or stale placeholder text. Fix violations before completing.
9. **pygame-ce cleanup.** Search both README.md and TUTORIAL.md for all exact occurrences of the string `pygame-ce` and replace every one with `pygame`. The project targets generic pygame and documentation must not name the pygame-ce variant.

Report: what was checked, what was fixed, and confirm both files are complete and compliant.
