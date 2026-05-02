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
