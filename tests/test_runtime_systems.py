import unittest

from gui_do.features.feature_lifecycle import Feature, FeatureManager
from gui_do.features.runtime_systems import (
    CapabilityContractRuntime,
    CapabilityProviderSpec,
    CapabilityRequirementSpec,
    CheckpointDomainSpec,
    CheckpointRecoveryRuntime,
    CheckpointSpec,
    ContractMigrationRuntime,
    ContractMigrationSpec,
    DependencyValidationError,
    DurableOperationBindingSpec,
    DurableOperationQueueRuntime,
    DurableOperationQueueSpec,
    EffectBindingSpec,
    EffectLifetimeOrchestrator,
    EventPipelineRuntime,
    EventPipelineSpec,
    EventPipelineStageSpec,
    FeatureDependencySpec,
    FeatureHealthRuntime,
    FeatureHotSwapManager,
    ExecutionContextRuntime,
    ExecutionContextSpec,
    HealthProbeSpec,
    MigrationStepSpec,
    MigrationTargetSpec,
    PolicyDecision,
    ProjectionNodeSpec,
    ProjectionRuntime,
    ProjectionSpec,
    QoSPolicyRuntime,
    QoSPolicySpec,
    RecomputeNodeSpec,
    RecomputeOrchestrator,
    ReactiveDependencyGraphRuntime,
    ReactiveGraphSpec,
    ReactiveNodeSpec,
    ReactiveSourceSpec,
    ReplaySpec,
    ReplacePolicySpec,
    RuntimePolicyEngine,
    RuntimePolicySpec,
    RuntimeReplayHarness,
    SagaCompensationRuntime,
    SagaSpec,
    SagaStepSpec,
    WorkloadBudgetBrokerRuntime,
    WorkloadBudgetClassSpec,
    WorkloadBudgetSpec,
    WorkflowCoordinator,
    WorkflowSpec,
    WorkflowStepSpec,
    build_routed_runtime_systems,
    validate_feature_dependencies,
)


class _App:
    def __init__(self):
        self.active_scene_name = "main"


class _Host:
    def __init__(self, app):
        self.app = app


class _BaseFeature(Feature):
    def __init__(self, name="base"):
        super().__init__(name)
        self.built = False
        self.bound = False
        self.shutdowns = 0
        self.value = 0

    def build(self, host):
        _ = host
        self.built = True

    def bind_runtime(self, host):
        _ = host
        self.bound = True

    def shutdown_runtime(self, host):
        _ = host
        self.shutdowns += 1

    def save_state(self):
        return {"value": self.value}

    def restore_state(self, state):
        self.value = int(state.get("value", 0))


class TestDependencyValidation(unittest.TestCase):
    def test_missing_dependency_raises(self):
        app = _App()
        host = _Host(app)
        manager = FeatureManager(app)
        feature = _BaseFeature("consumer")
        manager.register(feature, host)

        with self.assertRaises(DependencyValidationError):
            validate_feature_dependencies(
                feature,
                (
                    FeatureDependencySpec(feature_name="provider", required=True),
                ),
            )


class TestWorkflowCoordinator(unittest.TestCase):
    def test_runs_steps_and_completes(self):
        feature = _BaseFeature("flow")
        replay = RuntimeReplayHarness(ReplaySpec(enabled=True, max_records=32))
        workflow = WorkflowCoordinator(feature, replay_harness=replay)
        workflow.register(
            WorkflowSpec(
                name="sync",
                steps=(
                    WorkflowStepSpec(name="add1", handler=lambda payload: int(payload) + 1),
                    WorkflowStepSpec(name="mul2", handler=lambda payload: int(payload) * 2),
                ),
            )
        )

        run = workflow.start("sync", 3)
        workflow.pump()
        workflow.pump()
        workflow.pump()

        self.assertEqual("completed", run.status)
        self.assertEqual(8, run.payload)
        self.assertGreaterEqual(len(replay.records()), 1)


class TestRecomputeOrchestrator(unittest.TestCase):
    def test_recompute_order_and_assignment(self):
        feature = _BaseFeature("recompute")
        feature.order = []
        orchestrator = RecomputeOrchestrator(
            feature,
            (
                RecomputeNodeSpec(
                    name="a",
                    compute=lambda f: (f.order.append("a") or 10),
                    target_attr_name="a_value",
                ),
                RecomputeNodeSpec(
                    name="b",
                    depends_on=("a",),
                    compute=lambda f: (f.order.append("b") or f.a_value + 2),
                    target_attr_name="b_value",
                ),
            ),
        )

        processed = orchestrator.pump()

        self.assertEqual(2, processed)
        self.assertEqual(["a", "b"], feature.order)
        self.assertEqual(10, feature.a_value)
        self.assertEqual(12, feature.b_value)


class TestQoSPolicyRuntime(unittest.TestCase):
    def test_budget_is_enforced_per_update(self):
        qos = QoSPolicyRuntime((QoSPolicySpec(policy_name="workflow", max_work_units_per_update=2),))
        qos.begin_update()
        self.assertTrue(qos.acquire("workflow"))
        self.assertTrue(qos.acquire("workflow"))
        self.assertFalse(qos.acquire("workflow"))


class TestFeatureHealthRuntime(unittest.TestCase):
    def test_health_aggregate_reflects_probe_failures(self):
        feature = _BaseFeature("health")
        runtime = FeatureHealthRuntime(
            feature,
            (
                HealthProbeSpec(name="ok", evaluator=lambda f: True),
                HealthProbeSpec(name="warn", evaluator=lambda f: False, failure_state="degraded"),
            ),
        )

        runtime.run_probes()
        snapshot = runtime.snapshot()

        self.assertEqual("degraded", snapshot["aggregate_state"])
        self.assertEqual("ok", snapshot["probes"]["ok"])
        self.assertEqual("degraded", snapshot["probes"]["warn"])


class TestReplayHarness(unittest.TestCase):
    def test_replay_buffer_is_bounded(self):
        harness = RuntimeReplayHarness(ReplaySpec(enabled=True, max_records=2))
        harness.record("a", {"v": 1})
        harness.record("b", {"v": 2})
        harness.record("c", {"v": 3})

        seen = []
        harness.replay(lambda kind, payload: seen.append((kind, payload["v"])))

        self.assertEqual([("b", 2), ("c", 3)], seen)


class TestFeatureHotSwapManager(unittest.TestCase):
    def test_replace_transfers_state(self):
        app = _App()
        host = _Host(app)
        manager = FeatureManager(app)

        current = _BaseFeature("swap")
        current.value = 42
        manager.register(current, host)
        manager.build_features(host)
        manager.bind_runtime(host)

        def _factory():
            return _BaseFeature("swap")

        hot_swap = FeatureHotSwapManager(manager, host)
        replaced = hot_swap.replace(
            "swap",
            _factory,
            policy=ReplacePolicySpec(enabled=True, transfer_state=True, allow_cross_type=False),
        )

        self.assertIs(replaced, manager.get("swap"))
        self.assertTrue(replaced.built)
        self.assertTrue(replaced.bound)
        self.assertEqual(42, replaced.value)
        self.assertEqual(1, current.shutdowns)


class TestRuntimePolicyEngine(unittest.TestCase):
    def test_policy_engine_denies_target(self):
        engine = RuntimePolicyEngine(
            (
                RuntimePolicySpec(name="deny_pipeline", target="event_pipeline", action="deny", priority=10),
            )
        )
        engine.begin_update()

        decision = engine.evaluate("event_pipeline", units=1)

        self.assertIsInstance(decision, PolicyDecision)
        self.assertFalse(decision.allowed)
        self.assertEqual(0, decision.units)


class TestEffectLifetimeOrchestrator(unittest.TestCase):
    def test_register_and_cancel_group(self):
        class _Scope:
            def __init__(self):
                self.cleanups = []

            def add_cleanup(self, cleanup):
                self.cleanups.append(cleanup)

        class _Disposable:
            def __init__(self):
                self.disposed = 0

            def dispose(self):
                self.disposed += 1

        scope = _Scope()
        feature = _BaseFeature("effects")
        orchestrator = EffectLifetimeOrchestrator(feature, scope)
        disposable = _Disposable()

        orchestrator.register(
            EffectBindingSpec(name="main", group="g1", factory=lambda *_args: disposable),
            host=None,
        )
        orchestrator.cancel_group("g1")

        self.assertEqual(1, disposable.disposed)


class TestEventPipelineRuntime(unittest.TestCase):
    def test_pipeline_filter_map_window(self):
        seen = []
        runtime = EventPipelineRuntime(
            feature=_BaseFeature("pipeline"),
            specs=(
                EventPipelineSpec(
                    name="events",
                    handler=lambda payload, *_args: seen.append(payload),
                    stages=(
                        EventPipelineStageSpec(kind="filter", predicate=lambda value: int(value) % 2 == 0),
                        EventPipelineStageSpec(kind="map", mapper=lambda value: int(value) * 10),
                        EventPipelineStageSpec(kind="window", window_size=2),
                    ),
                ),
            ),
        )

        runtime.publish("events", 1)
        runtime.publish("events", 2)
        runtime.publish("events", 4)
        runtime.on_update()

        self.assertEqual([(20, 40)], seen)


class _ImmediateOperationBus:
    class _Handle:
        def __init__(self, result=None, error=None):
            self.result = result
            self.error = error
            self.is_pending = False
            self.is_complete = error is None
            self.is_failed = error is not None
            self.is_cancelled = False
            self.is_timed_out = False

        def cancel(self):
            self.is_cancelled = True

    def __init__(self):
        self.calls = []

    def call(self, operation_name, payload):
        self.calls.append((operation_name, payload))
        return self._Handle(result={"ok": True, "payload": payload})


class TestDurableOperationQueueRuntime(unittest.TestCase):
    def test_enqueue_and_pump(self):
        bus = _ImmediateOperationBus()
        runtime = DurableOperationQueueRuntime(
            DurableOperationQueueSpec(
                queue_name="jobs",
                bindings=(
                    DurableOperationBindingSpec(queue_operation="import", operation_name="run_import"),
                ),
            ),
            operation_bus=bus,
        )
        record = runtime.enqueue("import", {"path": "demo.csv"})
        runtime.pump()

        self.assertEqual("completed", record.status)
        self.assertEqual(1, len(bus.calls))


class TestCapabilityContractRuntime(unittest.TestCase):
    def test_provider_registration_and_requirements(self):
        feature = _BaseFeature("caps")
        runtime = CapabilityContractRuntime(feature, runtime_scope=None)
        runtime.register_providers(
            (
                CapabilityProviderSpec(capability="storage", version="2.1", value_factory=lambda *_args: {"name": "store"}),
            ),
            host=None,
        )
        runtime.validate_requirements(
            (
                CapabilityRequirementSpec(capability="storage", min_version="2.0", attr_name="storage_capability"),
            ),
            target=feature,
        )

        self.assertEqual({"name": "store"}, feature.storage_capability)


class TestProjectionRuntime(unittest.TestCase):
    def test_projection_order_and_assignment(self):
        feature = _BaseFeature("projection")
        feature.base_value = 3
        runtime = ProjectionRuntime(
            feature,
            ProjectionSpec(
                nodes=(
                    ProjectionNodeSpec(
                        name="a",
                        compute=lambda f, _p: int(f.base_value) + 1,
                        target_attr_name="a_value",
                    ),
                    ProjectionNodeSpec(
                        name="b",
                        depends_on=("a",),
                        compute=lambda _f, p: int(p.value("a")) * 2,
                        target_attr_name="b_value",
                    ),
                )
            ),
        )

        runtime.pump()

        self.assertEqual(4, feature.a_value)
        self.assertEqual(8, feature.b_value)


class TestRoutedRuntimeSystemsIntegration(unittest.TestCase):
    def test_build_routed_runtime_systems_with_new_specs(self):
        feature = _BaseFeature("integrated")
        host = _Host(_App())

        class _Scope:
            def add_cleanup(self, _cleanup):
                return None

            def get_optional_service(self, _key):
                return None

        systems = build_routed_runtime_systems(
            feature,
            host,
            runtime_scope=_Scope(),
            policy_specs=(RuntimePolicySpec(name="allow_all", target="*", action="allow"),),
            effect_bindings=(EffectBindingSpec(name="x", factory=lambda *_args: lambda: None),),
            event_pipeline_specs=(
                EventPipelineSpec(name="events", handler=lambda *_args: None),
            ),
            durable_queue_spec=DurableOperationQueueSpec(
                bindings=(DurableOperationBindingSpec(queue_operation="q", operation_name="q_op"),)
            ),
            capability_providers=(
                CapabilityProviderSpec(capability="storage", version="1.0", value_factory=lambda *_args: object()),
            ),
            capability_requirements=(
                CapabilityRequirementSpec(capability="storage", min_version="1.0", optional=False),
            ),
            projection_spec=ProjectionSpec(
                nodes=(ProjectionNodeSpec(name="p", compute=lambda *_args: 1, target_attr_name="proj"),)
            ),
        )

        self.assertIsNotNone(systems)
        self.assertIsNotNone(systems.policy_engine)
        self.assertIsNotNone(systems.effects)
        self.assertIsNotNone(systems.event_pipelines)
        self.assertIsNotNone(systems.durable_queue)
        self.assertIsNotNone(systems.capability_contracts)
        self.assertIsNotNone(systems.projection)


class TestExecutionContextRuntime(unittest.TestCase):
    def test_context_creation_cancellation_and_expiry(self):
        runtime = ExecutionContextRuntime(
            ExecutionContextSpec(enabled=True, default_priority=2, default_deadline_updates=1)
        )
        runtime.begin_update()
        parent = runtime.current
        child = runtime.create_context(metadata={"source": "test"})
        self.assertEqual(parent.context_id, child.parent_context_id)
        self.assertEqual(2, child.priority)
        runtime.cancel(child)
        self.assertTrue(child.cancelled)
        runtime.begin_update()
        self.assertTrue(runtime.is_expired(child))


class TestWorkloadBudgetBrokerRuntime(unittest.TestCase):
    def test_budget_enforces_caps(self):
        runtime = WorkloadBudgetBrokerRuntime(
            WorkloadBudgetSpec(
                classes=(
                    WorkloadBudgetClassSpec(name="workflow", max_units_per_update=2),
                )
            )
        )
        runtime.begin_update()
        self.assertTrue(runtime.acquire("workflow"))
        self.assertTrue(runtime.acquire("workflow"))
        self.assertFalse(runtime.acquire("workflow"))


class TestCheckpointRecoveryRuntime(unittest.TestCase):
    def test_checkpoint_capture_and_restore(self):
        feature = _BaseFeature("checkpoint")
        feature.value = 5

        runtime = CheckpointRecoveryRuntime(
            feature,
            CheckpointSpec(
                enabled=True,
                interval_updates=100,
                domains=(CheckpointDomainSpec(name="value", capture=lambda f: f.value, restore=lambda payload, f: setattr(f, "value", int(payload))),),
            ),
        )
        runtime.capture_now(reason="manual")
        feature.value = 99
        restored = runtime.restore_latest()
        self.assertTrue(restored)
        self.assertEqual(5, feature.value)


class TestSagaCompensationRuntime(unittest.TestCase):
    def test_saga_compensates_on_failure(self):
        feature = _BaseFeature("saga")
        feature.events = []
        runtime = SagaCompensationRuntime(
            feature,
            (
                SagaSpec(
                    name="demo",
                    steps=(
                        SagaStepSpec(
                            name="one",
                            handler=lambda payload, f, _run: (f.events.append("one") or {"v": 1}),
                            compensate=lambda payload, f, _run: f.events.append("undo_one"),
                        ),
                        SagaStepSpec(name="two", handler=lambda *_args: (_ for _ in ()).throw(RuntimeError("boom"))),
                    ),
                ),
            ),
        )
        run = runtime.start("demo", {})
        runtime.pump()
        runtime.pump()
        self.assertEqual("failed", run.status)
        self.assertEqual(["one", "undo_one"], feature.events)


class TestReactiveDependencyGraphRuntime(unittest.TestCase):
    def test_reactive_graph_marks_dirty_from_source(self):
        feature = _BaseFeature("reactive")
        feature.base = 2
        callback_holder = {"fn": None}

        def _subscribe(callback, *_args):
            callback_holder["fn"] = callback

            class _Connection:
                def disconnect(self):
                    return None

            return _Connection()

        runtime = ReactiveDependencyGraphRuntime(
            feature,
            ReactiveGraphSpec(
                sources=(ReactiveSourceSpec(name="src", subscribe=_subscribe, invalidates=("n1",)),),
                nodes=(
                    ReactiveNodeSpec(name="n1", compute=lambda f, _r: int(f.base) + 1, target_attr_name="n1"),
                    ReactiveNodeSpec(name="n2", depends_on=("n1",), compute=lambda _f, r: int(r.value("n1")) * 2, target_attr_name="n2"),
                ),
            ),
        )

        class _Scope:
            def add_cleanup(self, _cleanup):
                return None

        runtime.bind_sources(_Scope(), host=None)
        runtime.pump()
        self.assertEqual(3, feature.n1)
        self.assertEqual(6, feature.n2)
        feature.base = 4
        callback_holder["fn"]()
        runtime.pump()
        self.assertEqual(5, feature.n1)
        self.assertEqual(10, feature.n2)


class TestContractMigrationRuntime(unittest.TestCase):
    def test_applies_migration_chain(self):
        feature = _BaseFeature("migration")
        feature.payload = {"count": "2"}
        feature.payload_version = "1.0"

        runtime = ContractMigrationRuntime(
            feature,
            ContractMigrationSpec(
                steps=(
                    MigrationStepSpec(
                        contract="payload",
                        from_version="1.0",
                        to_version="2.0",
                        migrate=lambda payload, _feature: {"count": int(payload.get("count", 0))},
                    ),
                ),
                targets=(
                    MigrationTargetSpec(
                        name="payload_main",
                        contract="payload",
                        version_attr="payload_version",
                        payload_attr="payload",
                        target_version="2.0",
                    ),
                ),
                strict=True,
            ),
        )

        reports = runtime.apply()
        self.assertEqual("2.0", feature.payload_version)
        self.assertEqual(2, feature.payload["count"])
        self.assertEqual("migrated", reports[0]["status"])


class TestNewRuntimeSystemsIntegration(unittest.TestCase):
    def test_build_routed_runtime_systems_builds_all_new_systems(self):
        feature = _BaseFeature("integrated_new")
        host = _Host(_App())

        class _Scope:
            def add_cleanup(self, _cleanup):
                return None

            def get_optional_service(self, _key):
                return None

        feature.contract_payload = {"value": "7"}
        feature.contract_payload_version = "1.0"

        systems = build_routed_runtime_systems(
            feature,
            host,
            runtime_scope=_Scope(),
            execution_context_spec=ExecutionContextSpec(enabled=True),
            budget_spec=WorkloadBudgetSpec(classes=(WorkloadBudgetClassSpec(name="event_pipeline", max_units_per_update=1),)),
            checkpoint_spec=CheckpointSpec(enabled=True, interval_updates=100),
            saga_specs=(SagaSpec(name="sg", steps=(SagaStepSpec(name="s1", handler=lambda payload, *_args: payload),)),),
            reactive_graph_spec=ReactiveGraphSpec(nodes=(ReactiveNodeSpec(name="r1", compute=lambda *_args: 1, target_attr_name="r1"),)),
            migration_spec=ContractMigrationSpec(
                steps=(MigrationStepSpec(contract="contract_payload", from_version="1.0", to_version="2.0", migrate=lambda payload, _feature: {"value": int(payload["value"])}),),
                targets=(MigrationTargetSpec(name="payload", contract="contract_payload", version_attr="contract_payload_version", payload_attr="contract_payload", target_version="2.0"),),
            ),
        )

        self.assertIsNotNone(systems)
        self.assertIsNotNone(systems.execution_context)
        self.assertIsNotNone(systems.budget_broker)
        self.assertIsNotNone(systems.checkpoint)
        self.assertIsNotNone(systems.saga)
        self.assertIsNotNone(systems.reactive_graph)
        self.assertIsNotNone(systems.migration)
        self.assertEqual("2.0", feature.contract_payload_version)


if __name__ == "__main__":
    unittest.main()
