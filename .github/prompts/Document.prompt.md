---
name: Document
description: trigger a full readme rebuild
---

<!-- Tip: Use /create-prompt in chat to generate content with agent assistance -->

## Documentation Principles

gui_do is a data-driven, feature-lifecycle-oriented GUI framework. Documentation must prioritize declarative specs, lifecycle orchestration, and runtime wiring through public APIs.

Primary truth sources for architecture and API behavior:
- gui_do/features/data_driven_runtime.py
- gui_do/features/feature_lifecycle.py
- gui_do/app/gui_application.py
- gui_do/overlays/* (especially overlay_manager.py, shortcut_help_overlay.py, toast_manager.py)
- demo_features/* as runnable reference patterns

## Documentation Structure & Purpose

The README must guide developers into declarative + lifecycle composition first and keep lower-level APIs as secondary material. All examples must be current with the package as it exists now.

## Content Guidelines

### 1. Project Overview
- Start with project name and 2-3 sentence plain-English summary.
- Emphasize declarative runtime setup, feature composition, and reactive state.
- Explain what boilerplate gui_do removes (scene wiring, event routing, overlays, lifecycle sequencing).

### 2. Table of Contents
- Include all top-level sections and major subsections.
- Keep hierarchy clear.
- Add back-to-top links for each major section.

### 3. API Organization Section
- Keep the tiered model and intent:
- Tier 1: Primary APIs (HostApplicationConfig, bootstrap_host_application, Feature* types, Specs, lifecycle helpers).
- Tier 2-7: Runtime infrastructure (state/data/events/scheduling/layout/theme/overlays/persistence).
- Tier 8+: Individual controls and lower-level internals (available, but secondary).
- Explicitly steer new users to Tier 1 first.

### 4. Overview Section
- Explain how observable data, feature lifecycle phases, declarative specs, and runtime wiring work together.
- Mention what gui_do handles automatically (rendering, keyboard/mouse routing, scene transitions, overlay dispatch, focus behavior).
- Include current overlay/event nuances:
- OverlayManager supports dismiss-on-escape, dismiss-on-outside-click, and modal key consumption for unhandled keys.
- Toast clicks are consumed (no click-through), with optional per-toast click callbacks.

### 5. Comprehensive Tutorial Section
- Keep beginner-to-advanced flow.
- Cover Feature, DirectFeature, LogicFeature, RoutedFeature with practical guidance.
- Use current public APIs and demo_features patterns.
- Include declarative runtime helpers and examples of RoutedRuntimeSpec usage.

### 6. Minimal Runnable Example
- Title exactly: Minimal Runnable Example and Configuration
- Content is one single runnable listing (no prose around it).
- Include HostApplicationConfig + FeatureSpec + bootstrap_host_application + run loop.
- Ensure imports and API names are current.

### 7. Data-Driven Bootstrap and Runtime
- Cover HostApplicationConfig and bootstrap_host_application in depth.
- Explain beginner-to-advanced spec composition:
- FeatureSpec, SceneSetupSpec, ActionSpec, WindowSpec, runtime scene specs.
- Routed runtime helpers and specs (for declarative runtime wiring).
- Include examples that match current package behavior.

### 8. Feature Lifecycle and Messaging
- Explain lifecycle order and intent: build, bind_runtime, handle_event, on_update, draw (+ relevant optional hooks if public).
- Explain feature messaging and coordination via FeatureManager.
- Include guidance on where to place subscriptions, action bindings, and cleanup.

### 9. Common Patterns
- Keep real-world patterns, updated to current usage:
- Scene menu strip/task panel declarative setup.
- Window toggles and focus-aware key routing.
- Shortcut help overlay setup and filtering/manual-shortcut patterns.
- Toast notifications with optional click callback behavior.
- Observable/reactive state flow across features.

### 10. Benefits of Data-Driven Lifecycle Approach
- Keep concise list of major benefits (about 8-10).
- Focus on composability, testability, deterministic wiring, and reduced boilerplate.

### 11. FAQ
- Keep practical Q&A for new users.
- Include at least one question each for:
- Direct controls vs feature composition.
- Lifecycle hook selection.
- Event handling and routing.
- Overlay behavior (escape/outside-click/modal key capture).
- Toast click behavior (default consume + optional callback).

### 12. See Also
- Link docs contracts/specs and architecture documents under docs/.
- Link primary source files (data_driven_runtime.py, feature_lifecycle.py, gui_application.py).
- Link demo_features/ as living examples.

## Content Rules

### DO:
- Keep data-driven + lifecycle-first framing.
- Use current public APIs and runnable examples.
- Start with Tier 1 APIs before infrastructure/control details.
- Keep examples practical and aligned to current behavior.
- Preserve TOC coverage and back-to-top navigation.

### DON'T:
- Add sections not listed above.
- Depend on private/internal names (leading underscore) in beginner docs.
- Use stale API names or signatures.
- Over-focus on individual controls outside data-driven patterns.
- Present behavior that contradicts current runtime/overlay/focus semantics.

## Post-Generation

- Place unittest badge at the top of README.
- Verify all TOC links and section anchors.
- Ensure examples run against current API.
- Remove stale or contradictory statements.

---

## TUTORIAL.md Generation

After generating README.md, generate or update TUTORIAL.md in the project root.

### Purpose

TUTORIAL.md is a standalone beginner tutorial for gui_do. It must teach the framework from zero to a complete runnable app while staying accurate to current declarative runtime and lifecycle behavior.

### Generate vs Update Behavior

- If TUTORIAL.md does not exist: generate complete tutorial from scratch using all required sections below.
- If TUTORIAL.md exists: read and update sections that are stale or missing newer APIs/patterns; preserve sections that are still accurate.

### Audience

Developers with basic Python knowledge who are new to gui_do and possibly new to GUI frameworks.

### Required Tutorial Structure (keep section order)

#### 1. Introduction
- What gui_do is (plain English, 2-3 sentences).
- What will be built.
- Assumed prerequisites.

#### 2. Core Concepts
- Data-driven design via specs (contrast imperative wiring vs declarative specs).
- Reactive programming with current observable API names:
- ObservableValue, ObservableList, ObservableDict, optional ComputedValue mention.
- Feature lifecycle and hook roles (build, bind_runtime, handle_event, on_update, draw).

#### 3. Installation and Setup
- pip install command.
- Minimal imports.
- Clarify bootstrap path vs manual GuiApplication surface path.

#### 4. Your First Application — Step by Step
Use these exact steps with runnable snippets:
1. Create a surface and GuiApplication (and explain bootstrap alternative).
2. Define a Feature with build hook.
3. Declare HostApplicationConfig + FeatureSpec.
4. Call bootstrap_host_application.
5. Add main run loop.
6. Show full combined listing.

#### 5. Observable Data and Reactive UI
- Show ObservableValue usage.
- Show subscription/update flow.
- Include at least one practical UI update binding pattern.
- Explain signal/subscription cleanup basics.

#### 6. Feature Types
- Feature, DirectFeature, LogicFeature, RoutedFeature.
- When to use each.

#### 7. Feature Messaging
- Publish/subscribe between features.
- Practical two-feature interaction example.

#### 8. Scene Navigation
- SceneSetupSpec and scene switching.
- Action-based or programmatic navigation.

#### 9. Spec Reference for Beginners
Include concise descriptions + snippets for:
- FeatureSpec
- SceneSetupSpec
- ActionSpec
- WindowSpec
- Task panel spec/runtime helper patterns if applicable
- Toast/notification specs or manager usage if applicable
- Shortcut/help overlay spec/runtime helper patterns if applicable

#### 10. Complete Example Application
- 40+ lines, runnable.
- At least two features.
- Shared observable data.
- One action/button flow.
- Run loop included.

#### 11. Next Steps
- Point to README.md, demo_features/, docs/.
- Encourage reading data_driven_runtime.py and feature_lifecycle.py.

### Mandatory Current-Behavior Coverage

Tutorial content must reflect these current behaviors where relevant:
- Declarative routed runtime wiring via RoutedRuntimeSpec and helper utilities.
- Overlay routing semantics: escape dismissal, outside-click dismissal, optional modal key capture.
- Shortcut help overlay can be configured with manual shortcut content and filtering.
- Toast clicks are consumed by default to prevent click-through; optional on_click callback is explicit.
- Focus behavior should be described in lifecycle/routing terms consistent with current runtime.

### Content Rules for TUTORIAL.md

#### DO:
- Use plain, approachable language.
- Introduce concepts before using them.
- Keep snippets runnable or clearly state dependencies from prior steps.
- Prefer public APIs and current examples from demo_features/.
- Keep section structure exactly as required.

#### DON'T:
- Assume lifecycle knowledge before explanation.
- Use stale names (for example generic Observable when ObservableValue is intended).
- Rely on private/internal symbols in beginner examples.
- Skip the step-by-step build-up.
- Add extra top-level sections outside required structure.
