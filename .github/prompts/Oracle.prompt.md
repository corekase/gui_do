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
- **Architectural patterns to preserve and extend**: All recommendations must align with (1) feature lifecycle phases (`build` → `bind_runtime` → `on_update` → `draw` → `shutdown_runtime`), (2) reactive state and subscription lifecycle, (3) declarative spec-driven composition, and (4) scene-local isolation with shared app managers.
- **Feature types to promote**: Emphasize how new systems integrate with `Feature`, `DirectFeature`, `LogicFeature`, and `RoutedFeature`. Highlight `RoutedFeature` + `RoutedRuntimeSpec` patterns as the preferred extension mechanism for event-driven and scheduler-managed behavior.
- **Current baseline to account for**: Treat the following as already-implemented framework capabilities and build recommendations on top of them rather than re-proposing them as net-new:
	- `FeatureRuntimeScope`
	- Declarative service/effect specs (`ServiceBindingSpec`, `ServiceConsumerSpec`, `StoreSubscriptionSpec`, `StoreSelectorSpec`, `ObservableEffectSpec`, `SignalEffectSpec`)
	- Operation and failure-policy specs (`FeatureOperationSpec`, `FailurePolicySpec`) backed by `FeatureOperationBus`

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
	- **How lifecycle order and subscription cleanup will be enforced** (this is critical: document which lifecycle phase(s) the system relies on and how subscribers will be cleaned up to avoid leaks).
3. Recommended implementation sequence with dependency notes.
4. Brief rationale for what was intentionally deferred and why.
5. Summary of architectural patterns demonstrated by the proposal (what existing pattern does it extend or build upon?).

## Evaluation Lens for New Recommendations

For each candidate system, explicitly describe how it composes with the current routed runtime facilities:

- Does it register through `RoutedRuntimeSpec` or a sibling declarative spec?
- Does it rely on runtime-scope ownership for cleanup?
- If asynchronous or effect-driven, how it interoperates with operation bus/failure policy semantics.
