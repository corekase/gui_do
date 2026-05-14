---
name: Oracle
# Oracle: Roadmap and Extension Guidance for gui_do

description: Analyze and prioritize the next generalized systems/features or extension gaps beyond the current routed runtime faculties baseline. This prompt is up-to-date with all implemented runtime systems as of the current codebase. It does NOT reference MANUAL.md as the baseline; instead, it enumerates the actual implemented systems and guides the roadmap based on the current set of systems.
---

## Objective

Produce a prioritized roadmap of the best next generalized systems to implement, ordered so early choices maximize the value of later systems. Recommendations must be actionable, concrete, and reflect the current architecture.

## Current Baseline (Implemented Systems)

The following higher-level runtime faculties and systems are already implemented and should NOT be proposed again except to identify extension gaps or limitations:

- **Execution Context Propagation** (`ExecutionContextSpec`, `ExecutionContextRuntime`)
- **Workload Budgeting and Arbitration** (`WorkloadBudgetSpec`, `WorkloadBudgetBrokerRuntime`)
- **Checkpoint and Recovery** (`CheckpointSpec`, `CheckpointRecoveryRuntime`)
- **Saga Compensation and Orchestration** (`SagaSpec`, `SagaCompensationRuntime`)
- **Reactive Dependency Graph** (`ReactiveGraphSpec`, `ReactiveDependencyGraphRuntime`)
- **Contract Migration** (`ContractMigrationSpec`, `ContractMigrationRuntime`)
- **Workflow Orchestration** (`WorkflowSpec`, `WorkflowCoordinator`)
- **Derived-State Recompute** (`RecomputeNodeSpec`, `RecomputeOrchestrator`)
- **QoS Policy and Backpressure** (`QoSPolicySpec`, `QoSPolicyRuntime`)
- **Feature Health Monitoring** (`HealthProbeSpec`, `FeatureHealthRuntime`)
- **Replay and Diagnostics** (`ReplaySpec`, `RuntimeReplayHarness`)
- **Hot-Swap/Replace Policy** (`ReplacePolicySpec`, `FeatureHotSwapManager`)
- **Runtime Policy Engine** (`RuntimePolicySpec`, `PolicyDecision`, `RuntimePolicyEngine`)
- **Effect Lifetime Ownership** (`EffectBindingSpec`, `EffectLifetimeOrchestrator`)
- **Event Pipeline** (`EventPipelineStageSpec`, `EventPipelineSpec`, `EventPipelineRuntime`)
- **Durable Operation Queue** (`DurableOperationQueueSpec`, `DurableQueueRecord`, `DurableOperationQueueRuntime`)
- **Capability Contracts/Negotiation** (`CapabilityProviderSpec`, `CapabilityRequirementSpec`, `CapabilityContractRuntime`)
- **Incremental Projection** (`ProjectionNodeSpec`, `ProjectionSpec`, `ProjectionRuntime`)

All of the above are available as declarative specs and runtime managers, integrated with the feature lifecycle and routed runtime composition. Do NOT propose simple wrappers or duplicates of these unless you are identifying a concrete extension gap.

## Scope and Constraints

- Prioritize platform-portable, architecture-level systems that extend the above baseline.
- Favor additions that integrate cleanly with data-driven runtime and feature lifecycle patterns.
- Identify dependencies between candidates so foundational systems come first.
- Exclude anything requiring native OS extensions, non-portable APIs, or platform-specific bindings.

## Required Output

1. **Ranked list of candidate systems** (highest priority first).
2. For each candidate:
   - What problem it solves.
   - Why it is generalized (not one-off).
   - Why it belongs at its priority rank.
   - Expected impact on existing architecture and downstream features.
   - Key implementation risks and mitigation notes.
   - How lifecycle order and subscription cleanup will be enforced (specify lifecycle phase(s) and teardown strategy).
3. Recommended implementation sequence with dependency notes.
4. Brief rationale for what was intentionally deferred and why.
5. Summary of architectural patterns demonstrated by the proposal (what existing pattern does it extend or build upon?).

## Evaluation Lens for New Recommendations

For each candidate system, explicitly describe how it composes with the current routed runtime facilities:

- Does it register through `RoutedRuntimeSpec` or a sibling declarative spec?
- Does it rely on runtime-scope ownership for cleanup?
- If asynchronous or effect-driven, how it interoperates with operation bus/failure policy semantics.

## Guidance

- Do NOT reference MANUAL.md or any prior baseline. Use only the enumerated implemented systems above as the current baseline.
- All recommendations must be actionable and justified by the present architecture.
- If no major gaps are found, recommend only targeted extensions or integration patterns.
- If proposing a new system, clearly state how it composes with and extends the above faculties.
- If deferring a system, explain why (e.g., not portable, not general, or blocked by a dependency).
