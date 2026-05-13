---
name: Manual.p9
description: Enrichment pass for concise examples and specification options appendix
---

# Manual Step 9 - Enrichment and Specification Cross-Link Pass

## Scope

Run an update-only enrichment pass over `MANUAL.md`.

This step must:
1. Add concise code examples to material that explains behavior but currently has no example.
2. Add and maintain an appendix section named:
   - `### Appendix F: Specifications and Option Reference`
3. Add links from specification-heavy sections to Appendix F entries.
4. Keep entries concise and practical; avoid repeating long chapter prose.
5. Normalize markdown display for double-underscore identifiers so names like `__init__.py`, `__version__`, and `__demo__` are not misparsed as emphasis.

Appendix F must include dedicated entries for the newer routed runtime families:
- `ServiceBindingSpec` / `ServiceConsumerSpec`
- `StoreSubscriptionSpec` / `StoreSelectorSpec`
- `ObservableEffectSpec` / `SignalEffectSpec`
- `FeatureOperationSpec` / `FailurePolicySpec`
- `FeatureRuntimeScope` and `FeatureOperationBus` as runtime counterparts
- `FeatureDependencySpec`
- `WorkflowStepSpec` / `WorkflowSpec` / `WorkflowCoordinator`
- `RecomputeNodeSpec` / `RecomputeOrchestrator`
- `QoSPolicySpec` / `QoSPolicyRuntime`
- `HealthProbeSpec` / `FeatureHealthRuntime`
- `ReplaySpec` / `RuntimeReplayHarness`
- `ReplacePolicySpec` / `FeatureHotSwapManager`
6. Appendix F links from specification-heavy sections include the routed runtime facilities above.
Do not rewrite the whole manual. Use targeted updates only.

## Run Mode Guard

- This step is update mode only.
- If `MANUAL.md` does not exist, stop and report that step 1-8 must run first.
- Do not create a from-scratch manual in this step.

## Discovery Before Edits (Required)

1. Read `MANUAL.md` fully.
2. Identify major sections that describe workflow, contracts, or APIs without any code block.
3. Read `gui_do/__init__.py` tier exports to verify names used in newly added examples.
4. Read relevant specs from `docs/` as needed to confirm terminology and option names.

## Example Enrichment Rules

When adding examples:
- Keep examples concise (typically 8-25 lines).
- Use only public root imports from `gui_do`.
- Prefer realistic snippets that demonstrate one key point clearly.
- Do not duplicate near-identical examples in multiple sections.
- If one example serves several sections, keep one canonical block and add links.
- Use Python fenced blocks.

When enriching prose and references:
- Wrap double-underscore identifiers (for example `__init__.py`, `__version__`, `__demo__`) in inline code formatting.
- Do not leave raw double-underscore names in plain text where markdown can interpret underscores as emphasis.

Target areas include any chapter that currently explains concepts with no example,
including but not limited to conceptual foundations, architecture/workflow, and system chapters.

## Appendix F Requirements

Create or update:

`### Appendix F: Specifications and Option Reference`

Inside Appendix F:
1. Organize by specification type families (for example: bootstrap specs, feature specs,
   action/input specs, window/presentation specs, overlay specs, persistence/migration specs).
2. For each spec entry include:
   - Spec name
   - Purpose (1-2 sentences)
   - Key options/fields and what they control
   - Defaults/notes if known from code/docs
   - Cross-reference links to chapters that use the spec
3. Keep entries concise and practical; avoid repeating long chapter prose.

## Linking Requirements

- In each section that introduces or relies on specs, add a short link note such as:
  `See [Appendix F: Specifications and Option Reference](#appendix-f-specifications-and-option-reference)`
- Ensure links resolve and anchor text is consistent.
- Keep existing TOC and back-to-top conventions intact.

## Quality Gates

Before finishing, verify:
1. `MANUAL.md` still has no `<!-- MANUAL_PLACEHOLDER: -->` comments.
2. Newly added examples use API names that exist in `gui_do/__init__.py` exports.
3. Appendix F exists and contains concrete options for each listed spec family.
4. Specification-heavy sections contain links to Appendix F.
5. No unrelated section rewrites were introduced.
6. Double-underscore identifiers display correctly and are not misparsed by markdown.

## Output Report

Report:
- Which sections gained new concise examples.
- Whether Appendix F was created or updated.
- How many sections now link to Appendix F.
