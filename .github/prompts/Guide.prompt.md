---
name: Guide
description: Monolithic serial generator for README.md and TUTORIAL.md, discovery-based and linked to MANUAL.md
agent: agent
---

# gui_do Guide Generator Program (Monolithic, Serial, Discovery-Only)

This prompt defines a single monolithic program for generating and updating project-facing guidance documents.
It is intentionally structured as:
1. Program instructions (how to generate)
2. Input list (what to generate)

The program generates and maintains:
1. README.md
2. TUTORIAL.md

## Program

You are generating or updating README.md and TUTORIAL.md from the current repository state.
Discover everything from source code, docs, tests, and demo features at runtime.

### Core generation standard

1. Be verbose, comprehensive, and high-signal where depth improves user success.
2. Prefer depth over broad but shallow lists.
3. Longer is better only when new content adds practical value.
4. Explain both how and why for important design and workflow decisions.
5. Do not be redundant or repetitive; avoid rephrasing the same point across adjacent sections.
6. Use progressive explanation: fundamentals first, then composition, then advanced patterns.

### Depth and anti-redundancy policy

For each substantial tutorial topic, include when material exists:
1. Problem framing and learner objective.
2. Conceptual model and lifecycle placement.
3. Runtime behavior and ownership semantics.
4. API map and role of key symbols.
5. Decision guidance and tradeoffs.
6. Failure modes and recovery guidance.
7. Verification cues (tests, demos, or implementation anchors).

Redundancy guardrails:
1. Explain a concept deeply at its primary section.
2. In later sections, link back and add only new context.
3. Avoid repeating identical checklists; tailor them to section goals.
4. Avoid duplicate code snippets unless the second snippet demonstrates a meaningfully different constraint.

### Workflow context

This prompt runs after the Manual prompt in the project workflow.
Treat MANUAL.md as current, authoritative reference material.
Use MANUAL.md for deep-system links and avoid duplicating full reference detail that belongs there.

Guide-writing posture:
1. README.md is discovery-oriented and motivational.
2. TUTORIAL.md is execution-oriented and learning-complete.
3. Default to expanding TUTORIAL.md depth rather than adding reference-style bulk to README.md.

### Execution model (strict)

1. Execute strictly serially.
2. Never run parallel generation or concurrent section writing.
3. Complete discovery first, then README.md, then TUTORIAL.md, then compliance pass.
4. Complete each stage before moving to the next stage.

### Scope and file-presence behavior

This prompt always handles both target files in one run.

1. If README.md exists: update in place.
2. If README.md is missing: generate from scratch.
3. If TUTORIAL.md exists: update in place.
4. If TUTORIAL.md is missing: generate from scratch.
5. If one exists and one is missing: update the existing file and generate the missing file in the same run.

### Writing standard

1. Be discovery-driven, concrete, and accurate.
2. Be verbose where explanation is needed, especially in TUTORIAL.md.
3. Explain both how and why for core concepts and workflow decisions.
4. Use only API names verified from current gui_do/__init__.py exports.
5. Keep README.md high-level and motivational, not a reference manual.
6. Keep TUTORIAL.md stepwise, complete, and runnable.
7. Keep terminology consistent across README.md, TUTORIAL.md, and MANUAL.md.
8. Prefer explicit transitions that explain why each tutorial step is introduced when it is.

### TUTORIAL-first quality profile

When tradeoffs are required, prioritize TUTORIAL.md quality.

TUTORIAL.md should:
1. Read as a cohesive learning journey, not disconnected recipes.
2. Include enough implementation detail for a reader to reproduce outcomes without hidden assumptions.
3. Show both baseline paths and at least one advanced/production-ready refinement path where relevant.
4. Provide short checkpoints that confirm expected behavior after major milestones.
5. Make lifecycle safety, runtime ownership, and teardown discipline explicit whenever state, subscriptions, routing, or async behavior appear.

### Discovery protocol (required)

Before writing either file, collect current facts from:
1. gui_do/__init__.py: all tier headers and all exported names (authoritative API surface)
2. gui_do/_version.py: __version__ and __demo__
3. demo_features/ package layout and package-root __init__.py files
4. docs/runtime_operating_contracts.md: behavioral guarantees and contract values
5. MANUAL.md: title and table-of-contents headings for deep-link targets
6. pyproject.toml and dependency requirement files (for example requirements-ci.txt) to discover install-time dependencies users must install manually when using --no-deps
7. Existing README.md and TUTORIAL.md when present

Before writing each major section, identify section-specific evidence from the discovered sources.
Do not include claims that cannot be tied to current code/tests/docs.

Use discovered data only. Do not assume names from memory.

Source-of-truth priority:
1. Current runtime behavior in gui_do code
2. Tests asserting behavior
3. Runtime/contracts docs
4. demo_features usage
5. Existing prose docs

### README.md contract

README.md is a project overview and onboarding handoff.
It introduces gui_do, shows one quick pattern, and directs readers to TUTORIAL.md and MANUAL.md.

README.md required top-level section order:
1. Overview
2. Strengths
3. Use Cases
4. Quick Look
5. Documentation
6. Installation
7. Project Structure
8. See Also

README.md header contract:
1. Line 1: exact unittest badge line
2. Line 2: # gui_do
3. Immediately below heading: Latest Demonstration media block
4. No blank line between line 1 and line 2
5. Demonstration URL must use __demo__ from gui_do/_version.py
6. In the media block template below, replace URLPART with the discovered __demo__ value in both places: the anchor href and the image src.

Exact badge line:
[![unittest](https://github.com/corekase/gui_do/actions/workflows/unittest.yml/badge.svg?branch=main)](https://github.com/corekase/gui_do/actions/workflows/unittest.yml)

Latest Demonstration media block format:
### Latest Demonstration

---

<a href="https://www.youtube.com/watch?v=URLPART"><img src="https://img.youtube.com/vi/URLPART/0.jpg" alt="Demo Video"></img></a>

---

README.md content rules:
1. Keep it high-level, concise, and motivating.
2. Include a minimal quick-look listing that is runnable and uses verified public APIs.
3. Link prominently to TUTORIAL.md and MANUAL.md.
4. Do not include full API catalogs, tier dumps, or exhaustive control lists.
5. In Installation, explicitly use `python -m pip install -e . --no-deps` rather than creating a virtual environment workflow or a dependency-installing editable install command.
6. In Installation, list the discovered dependencies users must install manually because `--no-deps` skips dependency installation.
7. In Installation, state that manual dependency installation is required because building binary dependencies can be problematic on Windows.
8. Keep code examples minimal and orientation-focused; defer deep implementation to TUTORIAL.md and MANUAL.md.

### TUTORIAL.md contract

TUTORIAL.md is a full, end-to-end tutorial that teaches gui_do by building one continuous project.
It must be comprehensive, stepwise, and explicit about both how and why.

TUTORIAL.md required section order:
1. Introduction
2. Core Concepts
3. Installation and Setup
4. Your First Feature
5. Reactive State: Making the UI Respond
6. Feature Types
7. A Second Feature and Feature Communication
8. Actions and Keyboard Shortcuts
9. Spec Reference for Builders
10. Complete Project Listing
11. Next Steps

TUTORIAL.md content rules:
1. Keep one continuous project narrative across all sections.
2. Use runnable code snippets with verified public root imports.
3. Include full updated listings at major project milestones.
4. Include lifecycle-safe cleanup in all subscription examples.
5. Link to MANUAL.md for deeper system and specification coverage.
6. Do not use private or internal symbols in examples.
7. In Installation and Setup, explicitly use `python -m pip install -e . --no-deps` and avoid virtual environment creation steps unless the repository itself requires them.
8. In Installation and Setup, list the discovered dependencies users must install manually because `--no-deps` skips dependency installation.
9. In Installation and Setup, state that manual dependency installation is required because building binary dependencies can be problematic on Windows.

TUTORIAL.md depth contract:
1. Each major section must include purpose, implementation steps, and expected runtime outcome.
2. Each major section must include at least one introspected code example unless no direct usage exists.
3. For API-dense sections, include both a minimal example and an applied integration example.
4. Include explicit "why this step now" transitions between sections.
5. For behavior-sensitive topics (ownership, routing, teardown, cancellation, migration), include boundary-case examples.
6. Add concise troubleshooting notes near the step where the error is likely to appear.

TUTORIAL.md code example contract:
1. Source examples from current gui_do/, tests/, demo_features/, docs/, or existing tutorial/readme content when verified.
2. Prefer adapting real snippets over inventing unverified code.
3. Preserve semantic behavior when trimming setup for readability.
4. Validate all symbol names, fields, and call patterns against current implementation.
5. If no direct snippet exists, provide the smallest valid inferred example and label it as inferred.
6. In accompanying prose, state expected output/behavior and include at least one caution note for non-trivial examples.

TUTORIAL.md progression contract:
1. Ensure each section consumes artifacts created earlier in the tutorial project.
2. Ensure no step depends on code that has not yet been introduced.
3. Ensure milestone listings are synchronized with the latest step content.
4. Ensure final complete listing is internally consistent and runnable.

### Major systems and runtime faculties coverage

Across README.md and TUTORIAL.md:
1. Discover major systems from current tiers and exports.
2. Cover each major system at an appropriate level.
3. Explain declarative wiring versus imperative feature behavior.
4. Link each major concept to the corresponding MANUAL.md section when deeper detail is needed.

For each covered major system in TUTORIAL.md, include:
1. What problem it solves in the tutorial project.
2. Which public APIs are used and why.
3. One applied snippet in the tutorial project context.
4. One common mistake and how to avoid it.

### demo_features organization convention

Reflect project conventions accurately:
1. One folder per feature package under demo_features/.
2. Each package uses __init__.py as the public import surface.
3. Internal feature concerns are split into focused files.
4. Cross-feature imports target package roots, not internal submodules.

### Post-generation compliance pass (required)

After generating README.md and TUTORIAL.md, verify and fix:
1. README header order and media block correctness.
2. README section order and completeness.
3. TUTORIAL section order and completeness.
4. API name validation against gui_do/__init__.py.
5. Cross-reference links to MANUAL.md and TUTORIAL.md/README.md where required.
6. No MANUAL placeholders or stale scaffolding tokens.
7. No from gui_do.<submodule> imports in examples.
8. Replace any occurrence of pygame-ce with pygame.
9. Normalize double-underscore identifiers with inline code formatting.
10. Installation commands in both files use `python -m pip install -e . --no-deps` when describing editable installation.
11. Installation sections in both files include a dependency list discovered from repository dependency files for manual installation.
12. Installation sections in both files explain the Windows binary dependency rationale for manual dependency installation with `--no-deps`.
13. TUTORIAL.md sections include introspected examples wherever evidence allows.
14. Any inferred examples are explicitly labeled and justified by nearby verified patterns.
15. TUTORIAL.md progression remains continuous with no forward references to not-yet-introduced code.

### Final enrichment pass (required and single)

Run exactly one enrichment pass after main generation.
This pass must:
1. Expand thin explanations where reasoning is missing.
2. Add concrete runnable examples where required concepts lack examples.
3. Improve narrative continuity across tutorial sections.
4. Preserve required section order and contracts.
5. Keep README concise and keep TUTORIAL comprehensive.
6. Remove repeated explanations and duplicate snippets that do not add new value.
7. Improve transitions and milestone validation cues in TUTORIAL.md.

### Completion gates

Before finishing, verify:
1. README.md and TUTORIAL.md exist.
2. Both files satisfy required section order.
3. README header contract is satisfied exactly.
4. TUTORIAL includes complete project flow and final full listing.
5. All code examples use verified public APIs.
6. MANUAL.md links are present where deeper detail is expected.
7. pygame-ce is absent.
8. Double-underscore identifiers are correctly formatted.
9. TUTORIAL.md includes introspected, validated examples for all major API/system sections where discoverable evidence exists.
10. Any inferred tutorial examples are clearly labeled and behaviorally consistent with discovered patterns.
11. TUTORIAL.md maintains a continuous, runnable project narrative from first feature to complete listing.

## Input List

Use this as the terse generation input list. Expand each item using the Program rules above.
For each TUTORIAL.md item, include motivation, implementation steps, introspected code example(s), expected outcome, and a brief troubleshooting note.

1. Discovery inventory from code, docs, demos, and existing docs
2. README.md update-or-generate decision
3. README.md canonical header assembly using __demo__
4. README.md Overview section
5. README.md Strengths section
6. README.md Use Cases section
7. README.md Quick Look runnable listing
8. README.md Documentation navigation table and explanation
9. README.md Installation section
10. README.md Project Structure section
11. README.md See Also links
12. TUTORIAL.md update-or-generate decision
13. TUTORIAL.md Introduction section
14. TUTORIAL.md Core Concepts section
15. TUTORIAL.md Installation and Setup section
16. TUTORIAL.md Your First Feature section
17. TUTORIAL.md Reactive State section
18. TUTORIAL.md Feature Types section
19. TUTORIAL.md Second Feature and Communication section
20. TUTORIAL.md Actions and Keyboard Shortcuts section
21. TUTORIAL.md Spec Reference for Builders section
22. TUTORIAL.md Complete Project Listing section
23. TUTORIAL.md Next Steps section
24. Cross-link pass to MANUAL.md anchors and docs navigation targets
25. Compliance pass for structure, API validity, imports, placeholders, and pygame naming
26. Single final enrichment pass across README.md and TUTORIAL.md

## Operating note

This prompt is the authoritative entrypoint for generating and maintaining README.md and TUTORIAL.md in the gui_do documentation workflow.
