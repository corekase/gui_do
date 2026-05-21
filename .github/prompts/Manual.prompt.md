---
name: Manual
description: Monolithic serial generator for MANUAL.md (program + section input list)
agent: agent
---

# gui_do Manual Generator Program (Monolithic, Serial, Discovery-Only)

This prompt replaces the old multi-subprompt manual pipeline with a single monolithic program.
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

### Required topical coverage migrated from prior prompts

The generated manual must include and correctly cross-link:
1. Data-driven runtime model and lifecycle model
2. Automatic subscription ownership and cleanup as lifecycle safety
3. Runtime-scope ownership and teardown discipline
4. Declarative service/effect/operation specs and failure policies
5. Higher-level routed runtime faculties discovered at generation time
6. Unified menu-strip model only (no legacy split narrative)
7. Command palette two-bind model and behavior details
8. Unified window-visibility model across menu strip, command palette, task panel
9. Scene/window opt-in and opt-out behavior using current discovered fields
10. Contract-test and maintenance checklist guidance
11. File path resolution behavior from process working directory
12. Demo feature package organization convention

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
11. Systems: Scene, Window, and Task-Panel Presentation Models through Theme, Styling, and Visual Systems (include unified window-visibility guidance in Scene, Window, and Task-Panel Presentation Models)
12. Systems: Text, Input, Forms, and Validation Systems through Telemetry, Introspection, and Operational Hooks
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

This prompt is a one-time conversion target from the old Manual prompt and subprompt set into a single monolithic generator. The subprompt files are legacy reference material only; this prompt is the authoritative entrypoint for generation behavior.
