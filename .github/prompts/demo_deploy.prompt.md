---
name: demo_deploy
description: Integrate missing controls/systems into demo scenes with practical examples
---

<!-- Tip: Use /create-prompt in chat to generate content with agent assistance -->

Update the demo so **new controls** are integrated into the controls showcase, and **new systems** are integrated where needed across the demo.

## Objective

Ensure controls are demonstrated in the controls showcase and systems are integrated in the scenes/features where they are most useful, using real use-cases where possible.

## Required Actions

1. Integrate new and missing controls into the controls showcase.
2. Integrate new systems into a Systems window in the main scene:
	- If a Systems window definition is not present in the main scene, create one, add it to the main scene composition, set its dimensions to 80% of screen width and 80% of screen height, and center it when it is initially made visible.
	- For any newly created Systems window, populate a tab strip with the systems the window demonstrates.
	- If a Systems window definition already exists, update its existing tabs with the new system examples where they fit, and only create new tabs for systems that do not belong in an existing tab.
	- Ensure systems not currently covered by the demo are added to this Systems window.
3. Prefer realistic usage patterns for each integrated item.
4. If a control/system does not have a clear in-repo use-case, add a clean placeholder example with sensible names, structure, and sample data.
5. Update `demo_features/showcase/showcase_feature.py` with any missing example controls.
6. Follow the existing layout/composition patterns already used in that feature file.

## Quality Expectations

- Keep examples consistent with established demo architecture.
- Avoid ad hoc layout logic that conflicts with current scene structure.
- Keep naming and grouping understandable for someone exploring the demo for the first time.
- Keep Systems window tab organization stable and non-duplicative; do not split related systems across multiple tabs without a clear functional reason.
- Prefer updating existing systems demo structures over introducing parallel patterns that overlap in responsibility.
