---
name: Manual.p1
description: Write the full MANUAL.md skeleton — all headers, TOC, preamble chapters fully written, content-heavy chapters as stable placeholders
---

# Manual Step 1 — Skeleton + Preamble

## Scope

Write (or fully rewrite) `MANUAL.md` at the repository root.

This step establishes the **complete document structure**: every section header, a working TOC,
and full prose for the chapters this step owns. Chapters owned by later steps get a short,
distinctive placeholder that the later sub-prompt will replace.

## Codebase Discovery (Required Before Writing)

Before writing any content, perform this discovery pass:

1. **Read `gui_do/__init__.py`** — scan all tier comment blocks (`# TIER N: NAME`) to build
   a complete list of tiers currently in the codebase. This drives the Appendix D.1 tier matrix
   skeleton and informs the TOC.
2. **Read `docs/public_api_spec.md`** — understand tier groupings and stability policy.
3. **Read `docs/runtime_operating_contracts.md`** — note the restore report fields (Section 4)
   and scheduler budget values (Section 6) for use in placeholder content.
4. **List `tests/` directory** — note which `test_*_contracts.py` files exist for the
   Maintainer Diff Checklist operational section.

The system chapters in the TOC (8.1–8.N) must reflect the tier structure found in
`gui_do/__init__.py`. The chapter list in `#prompt:Manual.prompt.md` under "System Chapters"
is the current editorial organization — use it as the default. If new tiers in `__init__.py`
have no corresponding chapter, note them as candidates for a new chapter in the skeleton.

## What This Step Fully Writes

These sections must contain complete, final prose (not placeholders):

- **Title and Purpose** — one paragraph explaining what MANUAL.md is and who it is for. Do not include a version header, generation date, or pipeline metadata in the output.
- **How to Use This Manual** — full prose for: Learn/Build/Maintain modes, Reading Paths (beginner/intermediate/maintainer), Tri-Lens Markers, Contract Alignment.
- **Known Non-Goals** — brief list of what gui_do intentionally does not aim to do.
- **Maintainer Diff Checklist** — the concrete checklist that lives inside the Testing chapter (see spec below).

## What This Step Writes as Placeholders

For all other chapters (Conceptual Foundations through Appendix), write a one-paragraph placeholder
using this exact pattern so later sub-prompts can find and replace it:

```
<!-- MANUAL_PLACEHOLDER: [chapter name] — expand with Manual.pN.prompt.md -->

*This section is reserved. Run the corresponding pipeline sub-prompt to expand it.*
```

Use the chapter's actual name in place of `[chapter name]`.

## New Runtime Facilities Skeleton Note (Required)

When writing placeholders and TOC structure, ensure downstream chapters have clear room to document:

- `FeatureRuntimeScope` lifecycle ownership
- Declarative service/effect specs in routed runtime
- Operation orchestration with failure policies

Do not add placeholder chapter names for these; integrate them into existing architecture/system chapters.

## Table of Contents

Write a complete, working TOC with links to all sections and subsections as defined in
`#prompt:Manual.prompt.md` under "Document Structure" and "System Chapters". Every entry must
have a working `(#anchor-name)` link in GitHub-Flavored Markdown format.

Every major section must have a `[Back to Table of Contents](#table-of-contents)` link
immediately below its heading.

## Maintainer Diff Checklist (Full Content)

Write this as a subsection inside `## Testing, Diagnostics, and Reliability`.
Include all four categories:

**Inventory delta checks:**
1. Compare current root exports in `gui_do/__init__.py` with Appendix D and D.1 entries.
2. Check `docs/` contracts for changed guarantees, policies, or boundary rules.
3. Check `tests/` for new contract/runtime test modules that imply manual updates.
4. Check `demo_features/` for new recommended composition patterns to document.

**Content integrity checks:**
1. Every changed system has updates in both chapter narrative and quick-index references.
2. Removed APIs are deleted from examples, recipes, and appendix indexes.
3. Added APIs are classified at the right abstraction level (Tier 1 first, then lower tiers).


**Navigation and structure checks:**
1. All newly added sections are present in TOC and resolve correctly.
2. Every major section still contains a Back to Table of Contents link.
3. Top-level chapter order remains stable unless intentional restructure is recorded.

**Operational checks:**
1. Re-run high-priority contract tests (command below).
2. Validate end-to-end reference listing assumptions against current runtime behavior.
3. Record unresolved ambiguities as explicit TODO notes in migration/deprecation section.

Contract test command:
```bash
python -m pytest -q tests/test_public_api_exports.py tests/test_public_api_docs_contracts.py tests/test_runtime_operating_contracts.py tests/test_boundary_contracts.py tests/test_gui_application_workspace_contracts.py
```

## Manual Conformance Report Section

Do not write a Manual Conformance Report section in MANUAL.md. This is an internal
pipeline artifact and must not appear in the published output.

## Output

**From-Scratch Rebuild Mode** (`MANUAL.md` does not exist):
- Use `create_file` to create `MANUAL.md` with the full skeleton.

**Update Run** (`MANUAL.md` exists):
- Do NOT replace the entire file. Only update the sections p1 owns:
  - Replace the preamble (title paragraph through end of `## How to Use This Manual`)
    using a targeted `replace_string_in_file`.
  - Replace the `## Table of Contents` block using a targeted `replace_string_in_file`.
  - Leave all sections from `## Conceptual Foundations` onward untouched.
- If p1 is running as part of the full 9-step pipeline and `MANUAL.md` already has content,
  continue update behavior above and do not perform full-file replacement.

Verify: check that the file exists and line count is reasonable (>100 lines) before finishing.
