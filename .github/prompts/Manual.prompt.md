---
name: Manual
description: generate or evolve a complete MANUAL.md reference guide
---

<!-- Tip: Use /create-prompt in chat to generate content with agent assistance -->

Generate or update a single-file, complete reference manual at repository root: MANUAL.md.

The manual is the primary learning and reference source for gui_do. It must teach the framework end-to-end, from first principles to advanced usage, while staying aligned with current code, tests, demos, and contracts.

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
- A "What Changed Since Last Manual" summary when an older MANUAL.md existed.
- A "Known Non-Goals" subsection to prevent misuse and wrong expectations.
- A "Contract Alignment" note that points readers to docs/ contracts when behavior is normative.
- A "Maintainer Diff Checklist" subsection under testing/maintenance guidance that is explicitly designed for future manual regeneration passes.

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
