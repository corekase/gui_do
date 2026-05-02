---
name: Document
description: trigger a full readme rebuild
---

<!-- Tip: Use /create-prompt in chat to generate content with agent assistance -->

## Documentation Principles

gui_do is a **data-driven, feature-lifecycle-oriented GUI framework**. The primary sources of truth are `gui_do/features/data_driven_runtime.py` and `gui_do/features/feature_lifecycle.py`. All documentation must reflect this architectural focus.

## Documentation Structure & Purpose

The README should guide developers to the data-driven feature-lifecycle approach first, and only mention lower-level APIs when necessary for advanced use cases. All code examples must follow data-driven and feature-lifecycle patterns.

## Content Guidelines

### 1. Project Overview
- Start with the project name and a 2-3 sentence description in plain English
- Emphasize data-driven design and feature-based composition
- Highlight what the framework provides to developers

### 2. Table of Contents
- Use indentation to show hierarchy (sections, subsections)
- Link to all main sections and major subsections
- Include back-to-top links for all sections

### 3. API Organization Section
- Show that the public API is tiered by purpose and intended use
- Tier 1: Primary entry points (Specs, Features, bootstrap_host_application, HostApplicationConfig)
- Tier 2-7: Core infrastructure (data, events, scheduling, themes, overlays)
- Tier 8+: Individual controls and advanced internals (secondary/discouraged)
- Use this as the gateway—guide users to Tier 1 first

### 4. Overview Section
- Written in plain English, explain major systems from data-driven and lifecycle perspectives
- Explain how observable data, features, and lifecycle hooks work together
- Discuss automatic features (rendering, event routing, scene management, etc.)
- Clarify what types of applications this framework excels at
- Emphasize gui_do as "plumbing" that eliminates boilerplate

### 5. Comprehensive Tutorial Section
- Start with beginner concepts (observable data, features, lifecycle hooks)
- Progress to advanced patterns (feature messaging, custom rendering, scene transitions)
- Cover all feature types: Feature, DirectFeature, LogicFeature, RoutedFeature
- For each major concept, include code examples from the current package
- Explain what gui_do automates so developers focus on domain logic
- Include subsections with back-to-top links

### 6. Minimal Runnable Example
- **Title only:** "Minimal Runnable Example and Configuration"
- **Content:** A single code listing (no other text)
- **Must include:** Declarative config (HostApplicationConfig), feature example, bootstrap call, run loop
- **Must be current:** Generated from actual package code (use demo_features/ as reference)

### 7. Data-Driven Bootstrap and Runtime
- Cover HostApplicationConfig and bootstrap_host_application
- Explain all major Spec types (FeatureSpec, SceneSetupSpec, ActionSpec, WindowSpec, etc.)
- Show how specs eliminate boilerplate
- Progress from beginner to advanced specs
- Avoid explaining public API unless required for data-driven use

### 8. Feature Lifecycle and Messaging
- Explain lifecycle hooks (build, bind_runtime, handle_event, on_update, draw)
- Cover all feature types and when to use each
- Explain feature messaging and FeatureManager coordination
- Include subsections progressing from basic to advanced

### 9. Common Patterns
- Window toggles with task panel buttons
- Scene navigation with action specs
- Observable state management in features
- Feature-to-feature messaging
- Practical, real-world patterns

### 10. Benefits of Data-Driven Lifecycle Approach
- Explain why data-driven + lifecycle approach is better
- Declarative, automatic wiring, composability, testability, clear flow
- ~8-10 key benefits with brief explanations

### 11. FAQ
- "Can I still use controls directly?" → Yes but discouraged; compose via features
- "How do I customize controls?" → Create a Feature with a factory
- "Low-level event handling?" → Use Feature.handle_event()
- "Access app from feature?" → Via context parameter
- "Mix old and new styles?" → Not recommended; stay consistent
- Other practical questions developers ask

### 12. See Also
- Link to comprehensive docs (public_api_spec.md, architecture_boundary_spec.md, runtime_operating_contracts.md)
- Link to feature source files (feature_lifecycle.py, data_driven_runtime.py)
- Link to demo_features/ for examples

## Content Rules

### DO:
- Center everything on data-driven and feature-lifecycle patterns
- Use current package code for all examples
- Start with primary APIs (Specs, Features, bootstrap) before mentioning others
- Include code examples for every major concept
- Organize beginner → intermediate → advanced
- Link from TOC to all main sections
- Include back-to-top links in all sections
- Make it clear that gui_do automates rendering, routing, scene management, and more

### DON'T:
- Include sections not explicitly named here
- Explain individual controls unless needed for data-driven patterns
- Add low-level API details unless essential for feature use
- Include theoretical content without practical examples
- Remove back-to-top links or section links
- Create subsections for controls or low-level APIs

## Post-Generation

- Place a pytest unittest badge at the very beginning of the README
- Remove any sections that aren't explicitly named above
- Verify all links in the Table of Contents work
- Ensure all code examples follow data-driven and feature-lifecycle patterns

---

## TUTORIAL.md Generation

After generating README.md, generate (or update) a **TUTORIAL.md** file in the root of the project.

### Purpose

TUTORIAL.md is a standalone, beginner-focused tutorial that teaches gui_do from scratch. It covers the three foundational concepts of the framework — **data-driven design**, **reactive programming**, and the **feature lifecycle** — and walks a beginner through building a complete, runnable application from the first line of code to a finished product.

### Generate vs. Update Behavior

- **If TUTORIAL.md does not exist:** Generate the full tutorial from scratch covering all sections below.
- **If TUTORIAL.md already exists:** Read it, then update or expand any section that is out of date, missing information, or does not yet cover newly introduced APIs or patterns visible in the current codebase. Preserve any section that is already accurate and complete. Add new sections at the appropriate location if new concepts need coverage.

### Audience

A developer who has never used gui_do before. Assume Python knowledge (functions, classes, modules) but do not assume GUI framework experience.

### Structure and Content Requirements

The tutorial must contain all of the following sections in order:

#### 1. Introduction
- What gui_do is in plain English (2-3 sentences)
- What the reader will learn and build
- What prior knowledge is assumed

#### 2. Core Concepts
- **Data-driven design:** what it means — behavior is described by data structures (Specs), not by writing imperative setup code. Show a contrast: manual setup vs. spec-based setup.
- **Reactive programming:** what it means in gui_do — observable data that automatically triggers UI updates when it changes. Introduce `Observable`, `ObservableList`, signals.
- **Feature lifecycle:** explain what a Feature is and why it exists. List and explain all lifecycle hooks in order: `build`, `bind_runtime`, `handle_event`, `on_update`, `draw`. Explain when each fires and what it is for.

#### 3. Installation and Setup
- How to install gui_do (pip command)
- Minimal imports needed to start
- How to create the pygame display surface and hand it to gui_do

#### 4. Your First Application — Step by Step
Walk through building a complete basic application with these explicit steps:
1. Create a surface and a `GuiApplication`
2. Define a simple `Feature` with a `build` hook that adds a label
3. Use `HostApplicationConfig` and `FeatureSpec` to declare the feature
4. Call `bootstrap_host_application` to wire everything together
5. Write the main run loop
6. Run and see the result

Each step must include a full, runnable code snippet. At the end of this section, present the complete combined listing.

#### 5. Observable Data and Reactive UI
- Introduce `Observable` for single values
- Show how a feature reads and writes observable data
- Show how to bind a label or control to an observable so the UI updates automatically
- Explain signals: what they are, how `connect()` works, how to emit and handle changes

#### 6. Feature Types
Explain each feature type and when to use it:
- `Feature` — general-purpose, draws and handles events
- `DirectFeature` — bypasses scene routing; handles raw events directly
- `LogicFeature` — no drawing, pure logic/data
- `RoutedFeature` — receives events only when focus or scene context matches

#### 7. Feature Messaging
- Explain the publish/subscribe model between features
- Show how to publish a message from one feature
- Show how to subscribe and handle a message in another feature
- Practical example: a counter feature that reacts to a button press from another feature

#### 8. Scene Navigation
- What scenes are and why you use them
- How to declare multiple scenes with `SceneSetupSpec`
- How to navigate between scenes using `ActionSpec` or programmatically
- Example: a two-scene app with a "Go to settings" button

#### 9. Spec Reference for Beginners
Briefly cover the most commonly used Specs with a one-sentence description and a usage snippet for each:
- `FeatureSpec`
- `SceneSetupSpec`
- `ActionSpec`
- `WindowSpec`
- `TaskPanelSpec` (if applicable)
- `ToastSpec` (if applicable)

#### 10. Complete Example Application
A full, self-contained application (≥ 40 lines of real code) that combines:
- At least two features
- Observable data shared between features
- At least one reactive UI binding
- A simple action or button
- A run loop

This is the capstone of the tutorial. The code must be correct and runnable against the current package.

#### 11. Next Steps
- Point to README.md for the full API overview
- Point to demo_features/ for more complex examples
- Point to docs/ for architecture and contract documentation
- Encourage reading feature_lifecycle.py and data_driven_runtime.py directly

### Content Rules for TUTORIAL.md

#### DO:
- Use plain, approachable language throughout
- Introduce one concept per section before using it in a subsequent section
- Provide a runnable code snippet in every section that introduces code
- Use current package APIs only — cross-reference demo_features/ and feature_lifecycle.py for accuracy
- Clearly label each step in the step-by-step section with a step number
- Make every code example self-contained or clearly state what it depends on from a prior step

#### DON'T:
- Assume the reader knows what a feature lifecycle is before you explain it
- Use low-level control APIs (direct pygame drawing calls, raw UiNode manipulation) without first explaining why
- Reference internal/private APIs (names starting with `_`)
- Skip the step-by-step walkthrough in favor of a single large code dump
- Add sections not listed above
