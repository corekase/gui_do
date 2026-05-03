---
name: Oracle
description: Analyze and prioritize the next generalized systems/features to implement
---

<!-- Tip: Use /create-prompt in chat to generate content with agent assistance -->

Perform a comprehensive package analysis and recommend which generalized systems should be implemented next.

Focus on **platform-portable, architecture-level systems** that naturally extend the existing framework and improve flexibility, composability, or runtime behavior.

## Objective

Produce a prioritized roadmap of the best next generalized systems to implement, ordered so early choices maximize the value of later systems.

## Scope

- Prioritize "systems" work over one-off controls or narrow feature additions.
- Favor additions that integrate cleanly with existing data-driven runtime and feature lifecycle patterns.
- Identify dependencies between candidates so foundational systems come first.

## Hard Constraint

- Exclude anything requiring native OS extensions, non-portable APIs, platform-specific bindings, or other non-portable constructs.

## Required Output

1. Ranked list of candidate systems (highest priority first).
2. For each candidate:
	- What problem it solves.
	- Why it is generalized (not one-off).
	- Why it belongs at its priority rank.
	- Expected impact on existing architecture and downstream features.
	- Key implementation risks and mitigation notes.
3. Recommended implementation sequence with dependency notes.
4. Brief rationale for what was intentionally deferred and why.
