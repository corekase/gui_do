from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Sequence

from .runtime_facilities import FeatureOperationHandle


@dataclass(frozen=True)
class FeatureDependencySpec:
    """Declarative dependency on another registered feature name."""

    feature_name: str
    required: bool = True


class DependencyValidationError(ValueError):
    """Raised when declared feature dependencies are not satisfied."""


@dataclass(frozen=True)
class WorkflowStepSpec:
    """One workflow step handler with optional compensator metadata."""

    name: str
    handler: Callable[..., object]
    compensate: Callable[..., object] | None = None
    failure_policy: str | None = None


@dataclass(frozen=True)
class WorkflowSpec:
    """Declarative multi-step workflow definition."""

    name: str
    steps: Sequence[WorkflowStepSpec]
    auto_start: bool = False
    initial_payload: object | None = None


@dataclass(frozen=True)
class RecomputeNodeSpec:
    """Declarative derived-state compute node for scene update passes."""

    name: str
    compute: Callable[..., object]
    depends_on: Sequence[str] = field(default_factory=tuple)
    target_attr_name: str | None = None


@dataclass(frozen=True)
class QoSPolicySpec:
    """Declarative per-update budget policy for runtime work classes."""

    policy_name: str
    max_work_units_per_update: int = 16
    drop_policy: str = "defer"


@dataclass(frozen=True)
class HealthProbeSpec:
    """Declarative health probe that evaluates one runtime condition."""

    name: str
    evaluator: Callable[..., object]
    failure_state: str = "degraded"


@dataclass(frozen=True)
class ReplaySpec:
    """Declarative runtime replay/capture settings."""

    enabled: bool = False
    max_records: int = 1024
    capture_updates: bool = True
    capture_workflows: bool = True


@dataclass(frozen=True)
class ReplacePolicySpec:
    """Declarative hot-swap policy for feature replacement."""

    enabled: bool = True
    transfer_state: bool = True
    allow_cross_type: bool = False


@dataclass
class WorkflowRun:
    """Mutable in-flight workflow state."""

    run_id: str
    workflow_name: str
    payload: object = None
    status: str = "pending"
    step_index: int = 0
    waiting_handle: FeatureOperationHandle | None = None
    error: BaseException | None = None


class WorkflowCoordinator:
    """Coordinates multi-step, feature-local workflows."""

    def __init__(self, feature, *, operation_bus=None, replay_harness=None) -> None:
        self._feature = feature
        self._operation_bus = operation_bus
        self._replay = replay_harness
        self._specs: dict[str, WorkflowSpec] = {}
        self._runs: dict[str, WorkflowRun] = {}
        self._counter = 0

    def register(self, spec: WorkflowSpec) -> None:
        self._specs[str(spec.name)] = spec

    def start(self, workflow_name: str, payload: object = None) -> WorkflowRun:
        name = str(workflow_name)
        spec = self._specs.get(name)
        if spec is None:
            raise KeyError(f"unknown workflow: {name}")
        self._counter += 1
        run = WorkflowRun(
            run_id=f"wf_{self._counter}",
            workflow_name=name,
            payload=payload,
            status="running",
        )
        self._runs[run.run_id] = run
        if self._replay is not None:
            self._replay.record("workflow_start", {"workflow": name, "run_id": run.run_id})
        return run

    def active_runs(self) -> tuple[WorkflowRun, ...]:
        return tuple(self._runs.values())

    def cancel_all(self) -> None:
        for run in self._runs.values():
            run.status = "cancelled"
            if run.waiting_handle is not None and hasattr(run.waiting_handle, "cancel"):
                try:
                    run.waiting_handle.cancel()
                except Exception:
                    pass
        self._runs.clear()

    def pump(self, *, max_steps: int | None = None) -> int:
        processed = 0
        for run_id in tuple(self._runs.keys()):
            run = self._runs.get(run_id)
            if run is None:
                continue
            if run.status not in ("pending", "running"):
                self._runs.pop(run_id, None)
                continue
            if max_steps is not None and processed >= int(max_steps):
                break
            processed += self._pump_one(run)
            if run.status in ("completed", "failed", "cancelled"):
                self._runs.pop(run.run_id, None)
        return processed

    def _pump_one(self, run: WorkflowRun) -> int:
        spec = self._specs.get(run.workflow_name)
        if spec is None:
            run.status = "failed"
            run.error = KeyError(f"missing workflow spec: {run.workflow_name}")
            return 1

        if run.waiting_handle is not None:
            handle = run.waiting_handle
            if handle.is_pending:
                return 0
            run.waiting_handle = None
            if handle.is_failed or handle.is_timed_out:
                run.status = "failed"
                run.error = handle.error
                return 1
            if handle.is_cancelled:
                run.status = "cancelled"
                return 1
            run.payload = handle.result
            run.step_index += 1

        if run.step_index >= len(spec.steps):
            run.status = "completed"
            if self._replay is not None:
                self._replay.record("workflow_complete", {"workflow": run.workflow_name, "run_id": run.run_id})
            return 1

        step = spec.steps[run.step_index]
        try:
            result = _invoke_callable(step.handler, run.payload, self._feature, run)
        except Exception as exc:
            run.status = "failed"
            run.error = exc
            if self._replay is not None:
                self._replay.record(
                    "workflow_failed",
                    {
                        "workflow": run.workflow_name,
                        "run_id": run.run_id,
                        "step": step.name,
                        "error": str(exc),
                    },
                )
            return 1

        if isinstance(result, FeatureOperationHandle):
            run.waiting_handle = result
            return 1

        run.payload = result if result is not None else run.payload
        run.step_index += 1
        if self._replay is not None:
            self._replay.record(
                "workflow_step",
                {
                    "workflow": run.workflow_name,
                    "run_id": run.run_id,
                    "step": step.name,
                    "step_index": run.step_index,
                },
            )
        return 1

    def dispose(self) -> None:
        self.cancel_all()
        self._specs.clear()


class RecomputeOrchestrator:
    """Tracks dirty derived-state nodes and recomputes deterministically."""

    def __init__(self, feature, node_specs: Sequence[RecomputeNodeSpec], *, replay_harness=None) -> None:
        self._feature = feature
        self._nodes: dict[str, RecomputeNodeSpec] = {str(spec.name): spec for spec in node_specs}
        self._order = _topological_order(self._nodes)
        self._dirty: set[str] = set(self._nodes.keys())
        self._replay = replay_harness

    def mark_dirty(self, name: str) -> None:
        if name in self._nodes:
            self._dirty.add(name)

    def mark_all_dirty(self) -> None:
        self._dirty.update(self._nodes.keys())

    def pump(self, *, max_nodes: int | None = None) -> int:
        processed = 0
        for name in self._order:
            if name not in self._dirty:
                continue
            if max_nodes is not None and processed >= int(max_nodes):
                break
            spec = self._nodes[name]
            value = _invoke_callable(spec.compute, self._feature)
            if spec.target_attr_name:
                setattr(self._feature, str(spec.target_attr_name), value)
            self._dirty.discard(name)
            processed += 1
            if self._replay is not None:
                self._replay.record("recompute", {"node": name})
        return processed

    def dispose(self) -> None:
        self._dirty.clear()
        self._nodes.clear()


class QoSPolicyRuntime:
    """Per-update work budget bookkeeping for runtime systems."""

    def __init__(self, policies: Sequence[QoSPolicySpec]) -> None:
        self._limits: dict[str, tuple[int, str]] = {
            str(policy.policy_name): (max(0, int(policy.max_work_units_per_update)), str(policy.drop_policy))
            for policy in policies
        }
        self._used: dict[str, int] = {name: 0 for name in self._limits}

    def begin_update(self) -> None:
        for key in tuple(self._used.keys()):
            self._used[key] = 0

    def acquire(self, policy_name: str, *, units: int = 1) -> bool:
        name = str(policy_name)
        entry = self._limits.get(name)
        if entry is None:
            return True
        limit, _drop_policy = entry
        if limit <= 0:
            return False
        next_used = self._used.get(name, 0) + max(1, int(units))
        if next_used > limit:
            return False
        self._used[name] = next_used
        return True

    def dispose(self) -> None:
        self._limits.clear()
        self._used.clear()


class FeatureHealthRuntime:
    """Evaluates feature probes and tracks aggregate health state."""

    _ORDER = {"ok": 0, "degraded": 1, "failed": 2}

    def __init__(self, feature, probes: Sequence[HealthProbeSpec]) -> None:
        self._feature = feature
        self._probes = tuple(probes)
        self._states: dict[str, str] = {str(probe.name): "ok" for probe in self._probes}
        self._errors: dict[str, str] = {}

    @property
    def aggregate_state(self) -> str:
        highest = "ok"
        for state in self._states.values():
            if self._ORDER.get(state, 1) > self._ORDER.get(highest, 0):
                highest = state
        return highest

    def run_probes(self, host=None) -> None:
        for probe in self._probes:
            name = str(probe.name)
            try:
                result = _invoke_callable(probe.evaluator, self._feature, host)
            except Exception as exc:
                self._states[name] = "failed"
                self._errors[name] = str(exc)
                continue
            if result is True or result == "ok":
                self._states[name] = "ok"
                self._errors.pop(name, None)
            elif isinstance(result, str) and result in ("ok", "degraded", "failed"):
                self._states[name] = result
                if result == "ok":
                    self._errors.pop(name, None)
            elif result is False:
                self._states[name] = str(probe.failure_state)
            else:
                self._states[name] = "ok"

    def report_failure(self, probe_name: str, error: BaseException) -> None:
        key = str(probe_name)
        self._states[key] = "failed"
        self._errors[key] = str(error)

    def snapshot(self) -> dict[str, object]:
        return {
            "aggregate_state": self.aggregate_state,
            "probes": dict(self._states),
            "errors": dict(self._errors),
        }

    def dispose(self) -> None:
        self._states.clear()
        self._errors.clear()


class RuntimeReplayHarness:
    """Bounded in-memory record/replay buffer for runtime events."""

    def __init__(self, spec: ReplaySpec | None) -> None:
        self._spec = spec if spec is not None else ReplaySpec()
        self._records: list[dict[str, object]] = []

    @property
    def enabled(self) -> bool:
        return bool(self._spec.enabled)

    def record(self, kind: str, payload: dict[str, object] | None = None) -> None:
        if not self.enabled:
            return
        self._records.append({"kind": str(kind), "payload": dict(payload or {})})
        max_records = max(1, int(self._spec.max_records))
        if len(self._records) > max_records:
            overflow = len(self._records) - max_records
            del self._records[:overflow]

    def records(self) -> tuple[dict[str, object], ...]:
        return tuple(self._records)

    def replay(self, callback: Callable[[str, dict[str, object]], object]) -> None:
        for entry in tuple(self._records):
            callback(str(entry.get("kind", "")), dict(entry.get("payload", {})))

    def dispose(self) -> None:
        self._records.clear()


class FeatureHotSwapManager:
    """Replaces one registered feature instance while preserving lifecycle order."""

    def __init__(self, feature_manager, host) -> None:
        self._feature_manager = feature_manager
        self._host = host

    def replace(self, feature_name: str, factory: Callable[[], object], *, policy: ReplacePolicySpec | None = None):
        policy_obj = policy if policy is not None else ReplacePolicySpec()
        if not policy_obj.enabled:
            raise RuntimeError("feature hot swap is disabled by policy")

        manager = self._feature_manager
        current = manager.get(feature_name)
        if current is None:
            raise KeyError(f"unknown feature: {feature_name}")

        host_obj = manager._feature_hosts.get(current.name, self._host)
        state = None
        if policy_obj.transfer_state and hasattr(current, "save_state"):
            state = current.save_state()

        replacement = factory()
        if not policy_obj.allow_cross_type and type(replacement) is not type(current):
            raise TypeError("replacement type must match existing feature type")

        manager.unregister(current.name, host_obj)
        manager.register(replacement, host_obj)
        replacement.build(host_obj)
        replacement.bind_runtime(host_obj)
        manager._runtime_bound.add(replacement.name)
        if state is not None and hasattr(replacement, "restore_state"):
            replacement.restore_state(state)
        return replacement


class RoutedRuntimeSystems:
    """Container for routed runtime meta-systems updated each frame."""

    def __init__(
        self,
        feature,
        *,
        workflow_coordinator: WorkflowCoordinator | None = None,
        recompute: RecomputeOrchestrator | None = None,
        qos: QoSPolicyRuntime | None = None,
        health: FeatureHealthRuntime | None = None,
        replay: RuntimeReplayHarness | None = None,
    ) -> None:
        self._feature = feature
        self.workflow_coordinator = workflow_coordinator
        self.recompute = recompute
        self.qos = qos
        self.health = health
        self.replay = replay

    def on_update(self, host) -> None:
        if self.qos is not None:
            self.qos.begin_update()
        if self.replay is not None and self.replay.enabled:
            self.replay.record("update_begin", {"feature": getattr(self._feature, "name", "")})

        if self.recompute is not None:
            max_nodes = None
            if self.qos is not None and not self.qos.acquire("recompute", units=1):
                max_nodes = 0
            self.recompute.pump(max_nodes=max_nodes)

        if self.workflow_coordinator is not None:
            max_steps = None
            if self.qos is not None and not self.qos.acquire("workflow", units=1):
                max_steps = 0
            self.workflow_coordinator.pump(max_steps=max_steps)

        if self.health is not None:
            self.health.run_probes(host)

        if self.replay is not None and self.replay.enabled:
            self.replay.record("update_end", {"feature": getattr(self._feature, "name", "")})

    def dispose(self) -> None:
        if self.workflow_coordinator is not None:
            self.workflow_coordinator.dispose()
        if self.recompute is not None:
            self.recompute.dispose()
        if self.qos is not None:
            self.qos.dispose()
        if self.health is not None:
            self.health.dispose()
        if self.replay is not None:
            self.replay.dispose()


def validate_feature_dependencies(feature, dependency_specs: Sequence[FeatureDependencySpec]) -> None:
    """Validate declared feature dependencies against the manager registry."""

    if not dependency_specs:
        return
    manager = getattr(feature, "_feature_manager", None)
    if manager is None:
        raise DependencyValidationError("feature dependency validation requires a registered feature manager")
    known = set(manager.names())
    missing = [spec.feature_name for spec in dependency_specs if spec.required and spec.feature_name not in known]
    if missing:
        csv = ", ".join(sorted(str(name) for name in missing))
        raise DependencyValidationError(f"missing required feature dependencies: {csv}")


def build_routed_runtime_systems(
    feature,
    host,
    *,
    operation_bus=None,
    dependency_specs: Sequence[FeatureDependencySpec] = (),
    workflow_specs: Sequence[WorkflowSpec] = (),
    recompute_nodes: Sequence[RecomputeNodeSpec] = (),
    qos_policies: Sequence[QoSPolicySpec] = (),
    health_probes: Sequence[HealthProbeSpec] = (),
    replay_spec: ReplaySpec | None = None,
) -> RoutedRuntimeSystems | None:
    """Build runtime systems for routed features from declarative specs."""

    validate_feature_dependencies(feature, tuple(dependency_specs))

    replay = RuntimeReplayHarness(replay_spec) if replay_spec is not None else None
    qos = QoSPolicyRuntime(tuple(qos_policies)) if qos_policies else None
    recompute = RecomputeOrchestrator(feature, tuple(recompute_nodes), replay_harness=replay) if recompute_nodes else None
    health = FeatureHealthRuntime(feature, tuple(health_probes)) if health_probes else None

    workflow = None
    if workflow_specs:
        workflow = WorkflowCoordinator(feature, operation_bus=operation_bus, replay_harness=replay)
        for workflow_spec in workflow_specs:
            workflow.register(workflow_spec)
        for workflow_spec in workflow_specs:
            if workflow_spec.auto_start:
                workflow.start(workflow_spec.name, workflow_spec.initial_payload)

    if workflow is None and recompute is None and qos is None and health is None and replay is None:
        return None

    return RoutedRuntimeSystems(
        feature,
        workflow_coordinator=workflow,
        recompute=recompute,
        qos=qos,
        health=health,
        replay=replay,
    )


def _invoke_callable(handler: Callable[..., object], *args) -> object:
    for argc in range(len(args), -1, -1):
        try:
            return handler(*args[:argc])
        except TypeError:
            continue
    return handler()


def _topological_order(nodes: dict[str, RecomputeNodeSpec]) -> tuple[str, ...]:
    order: list[str] = []
    temporary: set[str] = set()
    permanent: set[str] = set()

    def _visit(name: str) -> None:
        if name in permanent:
            return
        if name in temporary:
            raise ValueError(f"cycle in recompute graph at node: {name}")
        temporary.add(name)
        spec = nodes.get(name)
        if spec is not None:
            for dependency in spec.depends_on:
                dep = str(dependency)
                if dep in nodes:
                    _visit(dep)
        temporary.remove(name)
        permanent.add(name)
        order.append(name)

    for node_name in nodes:
        _visit(node_name)
    return tuple(order)
