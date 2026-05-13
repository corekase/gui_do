---
name: DemoDeploy
description: Integrate missing controls/systems into demo features with practical, feature-lifecycle-aligned examples
---

<!-- Tip: Use /create-prompt in chat to generate content with agent assistance -->

Update the demo features so **new controls** are integrated into the controls showcase, and **new systems** are integrated where needed across demo scenes using feature-lifecycle patterns and data-driven composition.

## Objective

Ensure controls are demonstrated in the controls showcase and systems are integrated in the demo features where they are most useful, using real use-cases where possible. All integrations must follow the established feature-lifecycle patterns (`build` → `bind_runtime` → `on_update` → `shutdown_runtime`) and data-driven composition conventions.

All additions must also follow the Demo Feature Layout Standard in `docs/demo_feature_layout.md`: organize new code inside the feature package being updated, and place each new class/spec/helper in the correct module type within that feature folder.

## Required Actions

1. **Integrate new and missing controls into the controls showcase** using the established Feature pattern:
   - Update the showcase feature to demonstrate each control type in a realistic context.
   - Group controls by functional category (input, display, chrome, composite, data-bound).
   - For each control, show both basic usage and at least one advanced composition pattern (e.g., binding to an ObservableValue, custom event handling).
   - Ensure cleanup of subscriptions and resources in `shutdown_runtime`.

2. **Integrate new systems into appropriate demo features** (not necessarily a single Systems window):
   - Identify which demo features are the best fit for each system (preference: add to existing features rather than creating new ones).
   - Prefer systems integration patterns that align with the feature lifecycle:
     - Use `LogicFeature` for background systems (scheduling, data processing, persistence).
     - Use `RoutedFeature` for systems that respond to actions or routing events.
     - Use `Feature` with lifecycle observables for systems that drive UI updates.
   - If a dedicated Systems window or feature is the clearest fit, create one with proper encapsulation:
     - Define a `SystemsFeature` class (or similar) that owns system demonstrations.
     - Use `FeatureSpec` and declarative composition in the config.
     - Populate tabs or panels using data-driven specs where practical.
     - Ensure all subscription cleanup in `shutdown_runtime`.
   - **Systems priority**: Explicitly include graphics/runtime systems that are easy to miss in control-focused passes:
     - `ParticleSystem`, Emitters, and ParticleLayer for graphics.
     - Scheduling systems (CooperativeScheduler, TweenManager, AnimationSequence).
     - Persistence (WorkspacePersistenceManager, SceneSnapshot).
     - Data systems (ObservableList/ObservableDict, CollectionView, SortFilterProxySource).
     - If a system belongs better in another scene/feature than a centralized Systems feature, integrate it there and document the placement rationale in code comments.

3. **Prefer realistic usage patterns** for each integrated item:
   - Show data flowing through observables to controls.
   - Demonstrate lifecycle cleanup (unsubscribe in `shutdown_runtime`).
   - Use multi-feature composition where practical (e.g., a LogicFeature computing data + a RoutedFeature displaying it).
   - Avoid toy examples; aim for patterns that users could extract and adapt.

4. **For controls/systems without a clear in-repo use-case**, add a clean placeholder example:
   - Use sensible names, realistic structure, and sample data.
   - Include explanatory comments showing typical usage.
   - Ensure the example demonstrates the full lifecycle pattern.

5. **Update `demo_features/showcase/showcase_feature.py`** with missing example controls:
   - Follow the existing layout/composition patterns already used in that feature file.
   - Maintain the established feature structure (Feature class, presenter if needed, specs file if data-driven).

6. **Organize every new addition by the Demo Feature Layout Standard**:
   - Place new code in the specific feature folder being integrated (for example, `demo_features/<feature_name>/`), not in unrelated root-level demo modules.
   - Ensure each feature package keeps a clean `__init__.py` public export surface and no compatibility shims.
   - Place UI/runtime feature classes in `*_feature.py` modules.
   - Place companion logic Feature classes in `*_logic_feature.py` modules.
   - Place declarative specs and composition data in `*_specs.py` modules.
   - Place presenters/adapters in purpose-named modules such as `*_presenter.py` when needed.
   - Keep feature-specific helpers local to that feature package.
   - If a new feature is required, create it as its own folder package with `__init__.py`, at least one `*_feature.py`, and at least one `*_specs.py`.
   - Keep the `demo_features/` root limited to bootstrap/shared files (for example `demo_config.py`, `data/`, and feature folders).

## Quality Expectations

- Keep examples consistent with established **feature-lifecycle** patterns and the **feature-lifecycle oriented architecture**.
- Avoid ad hoc layout logic; use proper layout systems (constraint, flex, grid).
- Keep naming and grouping understandable for someone exploring the demo for the first time.
- Ensure multi-feature examples clearly document cross-feature communication (via FeatureMessage, shared observables, or action routing).
- Prefer updating existing demo structures over introducing parallel patterns that overlap in responsibility.
- Ensure each created/updated artifact is written to the canonical feature-local file for its role (feature, logic feature, specs, presenter, helper) rather than appending unrelated concerns to a single module.
- Ensure systems coverage includes representative examples of major runtime domains:
  - Graphics pipelines (particles, 2D scene graph, rendering).
  - State and runtime orchestration (state machines, command history, app state).
  - Scheduling and animation (cooperative scheduler, tweens, transitions).
  - Persistence (workspace save/restore, scene snapshots).
  - Reactive data and dataflow (ObservableValue/List/Dict, async providers, collection views).
- **Subscription safety**: Ensure all subscription setups in `bind_runtime` have corresponding cleanup in `shutdown_runtime` to prevent memory leaks.
