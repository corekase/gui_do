from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Sequence

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


@dataclass(frozen=True)
class RuntimePolicySpec:
    """Declarative runtime policy rule evaluated per update."""

    name: str
    target: str
    action: str = "allow"  # allow | deny | limit
    max_units: int | None = None
    priority: int = 0
    cooldown_updates: int = 0
    predicate: Callable[[Mapping[str, object]], bool] | None = None


@dataclass(frozen=True)
class EffectBindingSpec:
    """Declarative effect registration entry for lifecycle-owned runtime effects."""

    name: str
    factory: Callable[..., object]
    group: str = "default"


@dataclass(frozen=True)
class EventPipelineStageSpec:
    """One declarative stage for an event pipeline."""

    kind: str
    predicate: Callable[[object], bool] | None = None
    mapper: Callable[[object], object] | None = None
    interval_updates: int = 0
    window_size: int = 0


@dataclass(frozen=True)
class EventPipelineSpec:
    """Declarative event stream pipeline."""

    name: str
    handler: Callable[..., object]
    source: Callable[..., object] | None = None
    stages: Sequence[EventPipelineStageSpec] = field(default_factory=tuple)
    max_queue_size: int = 128


@dataclass(frozen=True)
class DurableOperationBindingSpec:
    """Declarative mapping from queue operation names to operation-bus names."""

    queue_operation: str
    operation_name: str
    idempotency_key_selector: Callable[[object], str | None] | None = None


@dataclass(frozen=True)
class DurableOperationQueueSpec:
    """Declarative durable operation queue configuration."""

    queue_name: str = "default"
    bindings: Sequence[DurableOperationBindingSpec] = field(default_factory=tuple)
    max_inflight: int = 1
    max_records: int = 512
    storage_factory: Callable[..., object] | None = None


@dataclass(frozen=True)
class CapabilityProviderSpec:
    """Declarative provider entry for capability contract negotiation."""

    capability: str
    version: str = "1.0"
    value_factory: Callable[..., object] | None = None
    service_key: object | None = None


@dataclass(frozen=True)
class CapabilityRequirementSpec:
    """Declarative consumer requirement for a capability contract."""

    capability: str
    min_version: str = "1.0"
    optional: bool = False
    attr_name: str | None = None


@dataclass(frozen=True)
class ProjectionNodeSpec:
    """Declarative node in an incremental projection graph."""

    name: str
    compute: Callable[..., object]
    depends_on: Sequence[str] = field(default_factory=tuple)
    target_attr_name: str | None = None


@dataclass(frozen=True)
class ProjectionSpec:
    """Declarative projection runtime configuration."""

    nodes: Sequence[ProjectionNodeSpec] = field(default_factory=tuple)
    max_nodes_per_update: int | None = None


@dataclass
class PolicyDecision:
    """One policy evaluation decision."""

    allowed: bool
    units: int
    reason: str = ""


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


class RuntimePolicyEngine:
    """Evaluates declarative runtime policies for per-update admission decisions."""

    def __init__(self, policies: Sequence[RuntimePolicySpec]) -> None:
        self._policies = tuple(sorted(policies, key=lambda spec: int(spec.priority), reverse=True))
        self._tick = 0
        self._cooldowns: dict[str, int] = {}

    def begin_update(self) -> None:
        self._tick += 1
        expired = [name for name, end_tick in self._cooldowns.items() if end_tick <= self._tick]
        for name in expired:
            self._cooldowns.pop(name, None)

    def evaluate(self, target: str, *, units: int = 1, context: Mapping[str, object] | None = None) -> PolicyDecision:
        base_units = max(1, int(units))
        ctx = dict(context or {})
        ctx.setdefault("target", str(target))
        for spec in self._policies:
            if str(spec.target) not in ("*", str(target)):
                continue
            if spec.name in self._cooldowns:
                continue
            predicate = spec.predicate
            if callable(predicate) and not bool(predicate(ctx)):
                continue
            action = str(spec.action).lower()
            if action == "deny":
                self._set_cooldown(spec)
                return PolicyDecision(False, 0, f"denied by policy {spec.name}")
            if action == "limit":
                limited = max(0, int(spec.max_units if spec.max_units is not None else base_units))
                self._set_cooldown(spec)
                return PolicyDecision(limited > 0, limited, f"limited by policy {spec.name}")
            if action == "allow":
                self._set_cooldown(spec)
                return PolicyDecision(True, base_units, f"allowed by policy {spec.name}")
        return PolicyDecision(True, base_units, "default_allow")

    def dispose(self) -> None:
        self._cooldowns.clear()

    def _set_cooldown(self, spec: RuntimePolicySpec) -> None:
        cooldown = max(0, int(spec.cooldown_updates))
        if cooldown > 0:
            self._cooldowns[str(spec.name)] = self._tick + cooldown


class EffectLifetimeOrchestrator:
    """Owns and organizes feature runtime effects into cancellable groups."""

    def __init__(self, feature, runtime_scope) -> None:
        self._feature = feature
        self._runtime_scope = runtime_scope
        self._entries: dict[str, object] = {}
        self._groups: dict[str, list[Callable[[], object]]] = {}

    def register(self, spec: EffectBindingSpec, *, host=None) -> object:
        instance = _invoke_callable(spec.factory, self._feature, host, self._runtime_scope)
        cleanup = _resolve_cleanup_callable(instance)
        if cleanup is not None:
            self.add_cleanup(cleanup, group=str(spec.group))
        self._entries[str(spec.name)] = instance
        return instance

    def add_cleanup(self, cleanup: Callable[[], object], *, group: str = "default") -> None:
        key = str(group)
        self._groups.setdefault(key, []).append(cleanup)
        self._runtime_scope.add_cleanup(cleanup)

    def resolve(self, name: str, default: object = None) -> object:
        return self._entries.get(str(name), default)

    def cancel_group(self, group: str) -> None:
        key = str(group)
        cleanups = self._groups.pop(key, [])
        for cleanup in reversed(cleanups):
            try:
                cleanup()
            except Exception:
                pass

    def dispose(self) -> None:
        for group in tuple(self._groups.keys()):
            self.cancel_group(group)
        self._entries.clear()


class EventPipelineRuntime:
    """Feature-local event pipelines with staged transform/filter/shape behavior."""

    def __init__(self, feature, specs: Sequence[EventPipelineSpec], *, replay_harness=None) -> None:
        self._feature = feature
        self._replay = replay_harness
        self._tick = 0
        self._pipelines: dict[str, dict[str, object]] = {}
        for spec in specs:
            self._pipelines[str(spec.name)] = {
                "spec": spec,
                "queue": deque(maxlen=max(1, int(spec.max_queue_size))),
                "debounce_pending": None,
                "debounce_due_tick": 0,
                "throttle_last_tick": -1_000_000,
                "window": [],
            }

    def publish(self, pipeline_name: str, payload: object) -> None:
        entry = self._pipelines.get(str(pipeline_name))
        if entry is None:
            raise KeyError(f"unknown pipeline: {pipeline_name}")
        entry["queue"].append(payload)

    def bind_sources(self, runtime_scope, *, host=None) -> None:
        for entry in self._pipelines.values():
            spec = entry["spec"]
            source = getattr(spec, "source", None)
            if not callable(source):
                continue
            callback = lambda payload, _name=str(spec.name): self.publish(_name, payload)
            subscription = _invoke_callable(source, callback, self._feature, host)
            cleanup = _resolve_cleanup_callable(subscription)
            if cleanup is not None:
                runtime_scope.add_cleanup(cleanup)

    def on_update(self, *, max_events: int | None = None) -> int:
        self._tick += 1
        processed = 0
        for name, entry in self._pipelines.items():
            spec: EventPipelineSpec = entry["spec"]
            queue: deque = entry["queue"]
            while queue and (max_events is None or processed < int(max_events)):
                payload = queue.popleft()
                emitted = self._apply_stages(payload, spec, entry)
                if emitted is _SKIP:
                    continue
                _invoke_callable(spec.handler, emitted, self._feature)
                processed += 1
                if self._replay is not None:
                    self._replay.record("event_pipeline", {"pipeline": name})
            emitted_debounce = self._flush_debounce_if_due(spec, entry)
            if emitted_debounce is not _SKIP and (max_events is None or processed < int(max_events)):
                _invoke_callable(spec.handler, emitted_debounce, self._feature)
                processed += 1
        return processed

    def dispose(self) -> None:
        self._pipelines.clear()

    def _apply_stages(self, payload: object, spec: EventPipelineSpec, entry: dict[str, object]) -> object:
        current = payload
        for stage in spec.stages:
            kind = str(stage.kind).lower()
            if kind == "filter":
                predicate = stage.predicate
                if callable(predicate) and not bool(predicate(current)):
                    return _SKIP
            elif kind == "map":
                mapper = stage.mapper
                if callable(mapper):
                    current = mapper(current)
            elif kind == "throttle":
                min_interval = max(0, int(stage.interval_updates))
                last_tick = int(entry["throttle_last_tick"])
                if min_interval > 0 and (self._tick - last_tick) < min_interval:
                    return _SKIP
                entry["throttle_last_tick"] = self._tick
            elif kind == "debounce":
                wait_updates = max(1, int(stage.interval_updates))
                entry["debounce_pending"] = current
                entry["debounce_due_tick"] = self._tick + wait_updates
                return _SKIP
            elif kind == "window":
                window_size = max(1, int(stage.window_size))
                window = entry["window"]
                window.append(current)
                if len(window) < window_size:
                    return _SKIP
                current = tuple(window)
                window.clear()
        return current

    def _flush_debounce_if_due(self, spec: EventPipelineSpec, entry: dict[str, object]) -> object:
        pending = entry.get("debounce_pending")
        if pending is None:
            return _SKIP
        if int(entry.get("debounce_due_tick", 0)) > self._tick:
            return _SKIP
        entry["debounce_pending"] = None
        entry["debounce_due_tick"] = 0
        return pending


@dataclass
class DurableQueueRecord:
    """Mutable durable queue entry."""

    record_id: str
    queue_operation: str
    payload: object
    idempotency_key: str | None = None
    status: str = "pending"
    attempts: int = 0
    result: object = None
    error: str | None = None
    active_handle: FeatureOperationHandle | None = None


class DurableOperationQueueRuntime:
    """Feature-local durable queue backed by operation bus handlers."""

    def __init__(self, spec: DurableOperationQueueSpec, *, operation_bus=None, storage=None, replay_harness=None) -> None:
        self._spec = spec
        self._operation_bus = operation_bus
        self._storage = storage
        self._replay = replay_harness
        self._counter = 0
        self._records: list[DurableQueueRecord] = []
        self._bindings = {str(binding.queue_operation): binding for binding in spec.bindings}
        self._restore_records()

    def enqueue(self, queue_operation: str, payload: object) -> DurableQueueRecord:
        binding = self._bindings.get(str(queue_operation))
        if binding is None:
            raise KeyError(f"unknown durable queue operation: {queue_operation}")
        idem = binding.idempotency_key_selector(payload) if callable(binding.idempotency_key_selector) else None
        if idem:
            existing = self._find_record_by_idempotency(idem)
            if existing is not None:
                return existing
        self._counter += 1
        record = DurableQueueRecord(
            record_id=f"dq_{self._counter}",
            queue_operation=str(queue_operation),
            payload=payload,
            idempotency_key=idem,
        )
        self._records.append(record)
        self._trim_to_budget()
        self._save_records()
        return record

    def pump(self, *, max_items: int | None = None) -> int:
        processed = 0
        if self._operation_bus is None:
            return processed
        inflight_limit = max(1, int(self._spec.max_inflight))
        for record in self._records:
            if max_items is not None and processed >= int(max_items):
                break
            if record.status in ("completed", "failed", "cancelled"):
                continue
            if record.active_handle is not None:
                if record.active_handle.is_pending:
                    continue
                self._commit_handle(record)
                processed += 1
                continue
            if self._inflight_count() >= inflight_limit:
                break
            binding = self._bindings.get(record.queue_operation)
            if binding is None:
                record.status = "failed"
                record.error = f"missing binding: {record.queue_operation}"
                processed += 1
                continue
            handle = self._operation_bus.call(binding.operation_name, record.payload)
            record.active_handle = handle
            record.status = "running"
            record.attempts += 1
            if not handle.is_pending:
                self._commit_handle(record)
                processed += 1
        if processed > 0:
            self._save_records()
        return processed

    def records(self) -> tuple[DurableQueueRecord, ...]:
        return tuple(self._records)

    def dispose(self) -> None:
        for record in self._records:
            if record.active_handle is not None and record.active_handle.is_pending:
                try:
                    record.active_handle.cancel()
                except Exception:
                    pass
                record.status = "cancelled"
        self._save_records()

    def _commit_handle(self, record: DurableQueueRecord) -> None:
        handle = record.active_handle
        if handle is None:
            return
        if handle.is_complete:
            record.status = "completed"
            record.result = handle.result
            record.error = None
        elif handle.is_failed or handle.is_timed_out:
            record.status = "failed"
            record.error = str(handle.error)
        elif handle.is_cancelled:
            record.status = "cancelled"
            record.error = None
        record.active_handle = None
        if self._replay is not None:
            self._replay.record("durable_queue", {"record_id": record.record_id, "status": record.status})

    def _inflight_count(self) -> int:
        return sum(1 for record in self._records if record.active_handle is not None and record.active_handle.is_pending)

    def _find_record_by_idempotency(self, idempotency_key: str) -> DurableQueueRecord | None:
        for record in reversed(self._records):
            if record.idempotency_key == idempotency_key and record.status != "failed":
                return record
        return None

    def _trim_to_budget(self) -> None:
        limit = max(1, int(self._spec.max_records))
        if len(self._records) <= limit:
            return
        overflow = len(self._records) - limit
        removable = [record for record in self._records if record.status in ("completed", "cancelled", "failed")]
        for record in removable[:overflow]:
            self._records.remove(record)

    def _restore_records(self) -> None:
        if self._storage is None or not hasattr(self._storage, "load_records"):
            return
        loaded = self._storage.load_records(self._spec.queue_name)
        if not loaded:
            return
        self._records.clear()
        for raw in loaded:
            self._counter += 1
            self._records.append(
                DurableQueueRecord(
                    record_id=str(raw.get("record_id") or f"dq_{self._counter}"),
                    queue_operation=str(raw.get("queue_operation", "")),
                    payload=raw.get("payload"),
                    idempotency_key=raw.get("idempotency_key"),
                    status=str(raw.get("status", "pending")),
                    attempts=int(raw.get("attempts", 0)),
                    result=raw.get("result"),
                    error=raw.get("error"),
                )
            )

    def _save_records(self) -> None:
        if self._storage is None or not hasattr(self._storage, "save_records"):
            return
        payload = [
            {
                "record_id": record.record_id,
                "queue_operation": record.queue_operation,
                "payload": record.payload,
                "idempotency_key": record.idempotency_key,
                "status": record.status,
                "attempts": record.attempts,
                "result": record.result,
                "error": record.error,
            }
            for record in self._records
        ]
        self._storage.save_records(self._spec.queue_name, payload)


class CapabilityContractRuntime:
    """Registers capability providers and validates consumer requirements."""

    def __init__(self, feature, *, runtime_scope=None) -> None:
        self._feature = feature
        self._runtime_scope = runtime_scope
        self._providers: dict[str, tuple[str, object]] = {}

    def register_providers(self, providers: Sequence[CapabilityProviderSpec], *, host=None) -> None:
        for provider in providers:
            value = None
            if provider.service_key is not None and self._runtime_scope is not None:
                value = self._runtime_scope.get_optional_service(provider.service_key)
            if value is None and callable(provider.value_factory):
                value = _invoke_callable(provider.value_factory, self._feature, host, self._runtime_scope)
            self._providers[str(provider.capability)] = (str(provider.version), value)

    def validate_requirements(self, requirements: Sequence[CapabilityRequirementSpec], *, target=None) -> None:
        for requirement in requirements:
            capability = str(requirement.capability)
            provided = self._providers.get(capability)
            if provided is None:
                if requirement.optional:
                    if requirement.attr_name and target is not None:
                        setattr(target, str(requirement.attr_name), None)
                    continue
                raise ValueError(f"missing required capability: {capability}")
            version, value = provided
            if _parse_version(version) < _parse_version(str(requirement.min_version)):
                if requirement.optional:
                    if requirement.attr_name and target is not None:
                        setattr(target, str(requirement.attr_name), None)
                    continue
                raise ValueError(
                    f"capability '{capability}' version {version} below required {requirement.min_version}"
                )
            if requirement.attr_name and target is not None:
                setattr(target, str(requirement.attr_name), value)

    def snapshot(self) -> dict[str, tuple[str, object]]:
        return dict(self._providers)

    def dispose(self) -> None:
        self._providers.clear()


class ProjectionRuntime:
    """Incremental projection graph runtime with dependency-aware invalidation."""

    def __init__(self, feature, spec: ProjectionSpec, *, replay_harness=None) -> None:
        self._feature = feature
        self._spec = spec
        self._replay = replay_harness
        self._nodes: dict[str, ProjectionNodeSpec] = {str(node.name): node for node in spec.nodes}
        self._dependents: dict[str, set[str]] = {}
        for node in spec.nodes:
            for dependency in node.depends_on:
                self._dependents.setdefault(str(dependency), set()).add(str(node.name))
        self._order = _topological_order(self._nodes)
        self._dirty: set[str] = set(self._nodes.keys())
        self._values: dict[str, object] = {}

    def mark_dirty(self, name: str) -> None:
        key = str(name)
        if key not in self._nodes:
            return
        stack = [key]
        while stack:
            current = stack.pop()
            if current in self._dirty:
                continue
            self._dirty.add(current)
            stack.extend(self._dependents.get(current, ()))

    def mark_all_dirty(self) -> None:
        self._dirty.update(self._nodes.keys())

    def value(self, name: str, default=None):
        return self._values.get(str(name), default)

    def pump(self, *, max_nodes: int | None = None) -> int:
        processed = 0
        node_cap = self._spec.max_nodes_per_update if max_nodes is None else max_nodes
        for name in self._order:
            if name not in self._dirty:
                continue
            if node_cap is not None and processed >= int(node_cap):
                break
            node = self._nodes[name]
            result = _invoke_callable(node.compute, self._feature, self)
            self._values[name] = result
            if node.target_attr_name:
                setattr(self._feature, str(node.target_attr_name), result)
            self._dirty.discard(name)
            processed += 1
            if self._replay is not None:
                self._replay.record("projection", {"node": name})
        return processed

    def dispose(self) -> None:
        self._nodes.clear()
        self._dependents.clear()
        self._dirty.clear()
        self._values.clear()


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
        policy_engine: RuntimePolicyEngine | None = None,
        effects: EffectLifetimeOrchestrator | None = None,
        event_pipelines: EventPipelineRuntime | None = None,
        durable_queue: DurableOperationQueueRuntime | None = None,
        capability_contracts: CapabilityContractRuntime | None = None,
        projection: ProjectionRuntime | None = None,
        workflow_coordinator: WorkflowCoordinator | None = None,
        recompute: RecomputeOrchestrator | None = None,
        qos: QoSPolicyRuntime | None = None,
        health: FeatureHealthRuntime | None = None,
        replay: RuntimeReplayHarness | None = None,
    ) -> None:
        self._feature = feature
        self.policy_engine = policy_engine
        self.effects = effects
        self.event_pipelines = event_pipelines
        self.durable_queue = durable_queue
        self.capability_contracts = capability_contracts
        self.projection = projection
        self.workflow_coordinator = workflow_coordinator
        self.recompute = recompute
        self.qos = qos
        self.health = health
        self.replay = replay

    def on_update(self, host) -> None:
        if self.policy_engine is not None:
            self.policy_engine.begin_update()
        if self.qos is not None:
            self.qos.begin_update()
        if self.replay is not None and self.replay.enabled:
            self.replay.record("update_begin", {"feature": getattr(self._feature, "name", "")})

        if self.event_pipelines is not None:
            max_events = None
            if self.qos is not None and not self.qos.acquire("event_pipeline", units=1):
                max_events = 0
            decision = self.policy_engine.evaluate("event_pipeline", units=1) if self.policy_engine is not None else None
            if decision is not None and not decision.allowed:
                max_events = 0
            self.event_pipelines.on_update(max_events=max_events)

        if self.projection is not None:
            max_nodes = None
            if self.qos is not None and not self.qos.acquire("projection", units=1):
                max_nodes = 0
            decision = self.policy_engine.evaluate("projection", units=1) if self.policy_engine is not None else None
            if decision is not None and not decision.allowed:
                max_nodes = 0
            self.projection.pump(max_nodes=max_nodes)

        if self.recompute is not None:
            max_nodes = None
            if self.qos is not None and not self.qos.acquire("recompute", units=1):
                max_nodes = 0
            decision = self.policy_engine.evaluate("recompute", units=1) if self.policy_engine is not None else None
            if decision is not None and not decision.allowed:
                max_nodes = 0
            self.recompute.pump(max_nodes=max_nodes)

        if self.workflow_coordinator is not None:
            max_steps = None
            if self.qos is not None and not self.qos.acquire("workflow", units=1):
                max_steps = 0
            decision = self.policy_engine.evaluate("workflow", units=1) if self.policy_engine is not None else None
            if decision is not None and not decision.allowed:
                max_steps = 0
            self.workflow_coordinator.pump(max_steps=max_steps)

        if self.durable_queue is not None:
            max_items = None
            if self.qos is not None and not self.qos.acquire("durable_queue", units=1):
                max_items = 0
            decision = self.policy_engine.evaluate("durable_queue", units=1) if self.policy_engine is not None else None
            if decision is not None and not decision.allowed:
                max_items = 0
            self.durable_queue.pump(max_items=max_items)

        if self.health is not None:
            self.health.run_probes(host)

        if self.replay is not None and self.replay.enabled:
            self.replay.record("update_end", {"feature": getattr(self._feature, "name", "")})

    def dispose(self) -> None:
        if self.policy_engine is not None:
            self.policy_engine.dispose()
        if self.effects is not None:
            self.effects.dispose()
        if self.event_pipelines is not None:
            self.event_pipelines.dispose()
        if self.durable_queue is not None:
            self.durable_queue.dispose()
        if self.capability_contracts is not None:
            self.capability_contracts.dispose()
        if self.projection is not None:
            self.projection.dispose()
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
    runtime_scope=None,
    operation_bus=None,
    dependency_specs: Sequence[FeatureDependencySpec] = (),
    policy_specs: Sequence[RuntimePolicySpec] = (),
    effect_bindings: Sequence[EffectBindingSpec] = (),
    event_pipeline_specs: Sequence[EventPipelineSpec] = (),
    durable_queue_spec: DurableOperationQueueSpec | None = None,
    capability_providers: Sequence[CapabilityProviderSpec] = (),
    capability_requirements: Sequence[CapabilityRequirementSpec] = (),
    projection_spec: ProjectionSpec | None = None,
    workflow_specs: Sequence[WorkflowSpec] = (),
    recompute_nodes: Sequence[RecomputeNodeSpec] = (),
    qos_policies: Sequence[QoSPolicySpec] = (),
    health_probes: Sequence[HealthProbeSpec] = (),
    replay_spec: ReplaySpec | None = None,
) -> RoutedRuntimeSystems | None:
    """Build runtime systems for routed features from declarative specs."""

    validate_feature_dependencies(feature, tuple(dependency_specs))

    replay = RuntimeReplayHarness(replay_spec) if replay_spec is not None else None
    policy_engine = RuntimePolicyEngine(tuple(policy_specs)) if policy_specs else None
    qos = QoSPolicyRuntime(tuple(qos_policies)) if qos_policies else None
    recompute = RecomputeOrchestrator(feature, tuple(recompute_nodes), replay_harness=replay) if recompute_nodes else None
    health = FeatureHealthRuntime(feature, tuple(health_probes)) if health_probes else None
    effects = None
    if effect_bindings and runtime_scope is not None:
        effects = EffectLifetimeOrchestrator(feature, runtime_scope)
        for effect_spec in effect_bindings:
            effects.register(effect_spec, host=host)
    event_pipelines = EventPipelineRuntime(feature, tuple(event_pipeline_specs), replay_harness=replay) if event_pipeline_specs else None
    if event_pipelines is not None and runtime_scope is not None:
        event_pipelines.bind_sources(runtime_scope, host=host)

    durable_queue = None
    if durable_queue_spec is not None:
        storage = _invoke_callable(durable_queue_spec.storage_factory, feature, host, runtime_scope) if callable(durable_queue_spec.storage_factory) else None
        durable_queue = DurableOperationQueueRuntime(
            durable_queue_spec,
            operation_bus=operation_bus,
            storage=storage,
            replay_harness=replay,
        )

    capability_contracts = None
    if capability_providers or capability_requirements:
        capability_contracts = CapabilityContractRuntime(feature, runtime_scope=runtime_scope)
        capability_contracts.register_providers(tuple(capability_providers), host=host)
        capability_contracts.validate_requirements(tuple(capability_requirements), target=feature)

    projection = ProjectionRuntime(feature, projection_spec, replay_harness=replay) if projection_spec is not None else None

    workflow = None
    if workflow_specs:
        workflow = WorkflowCoordinator(feature, operation_bus=operation_bus, replay_harness=replay)
        for workflow_spec in workflow_specs:
            workflow.register(workflow_spec)
        for workflow_spec in workflow_specs:
            if workflow_spec.auto_start:
                workflow.start(workflow_spec.name, workflow_spec.initial_payload)

    if (
        policy_engine is None
        and effects is None
        and event_pipelines is None
        and durable_queue is None
        and capability_contracts is None
        and projection is None
        and workflow is None
        and recompute is None
        and qos is None
        and health is None
        and replay is None
    ):
        return None

    return RoutedRuntimeSystems(
        feature,
        policy_engine=policy_engine,
        effects=effects,
        event_pipelines=event_pipelines,
        durable_queue=durable_queue,
        capability_contracts=capability_contracts,
        projection=projection,
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


_SKIP = object()


def _resolve_cleanup_callable(instance: object) -> Callable[[], object] | None:
    if instance is None:
        return None
    if callable(instance):
        return instance
    disconnect = getattr(instance, "disconnect", None)
    if callable(disconnect):
        return disconnect
    cancel = getattr(instance, "cancel", None)
    if callable(cancel):
        return cancel
    dispose = getattr(instance, "dispose", None)
    if callable(dispose):
        return dispose
    return None


def _parse_version(value: str) -> tuple[int, ...]:
    parts: list[int] = []
    for entry in str(value).split("."):
        token = entry.strip()
        if token.isdigit():
            parts.append(int(token))
            continue
        digits = ""
        for ch in token:
            if ch.isdigit():
                digits += ch
            else:
                break
        if digits:
            parts.append(int(digits))
        else:
            parts.append(0)
    return tuple(parts) if parts else (0,)


def _topological_order(nodes: dict[str, object]) -> tuple[str, ...]:
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
