import unittest

from gui_do.features.feature_lifecycle import Feature, FeatureManager
from gui_do.features.runtime_systems import (
    DependencyValidationError,
    FeatureDependencySpec,
    FeatureHealthRuntime,
    FeatureHotSwapManager,
    HealthProbeSpec,
    QoSPolicyRuntime,
    QoSPolicySpec,
    RecomputeNodeSpec,
    RecomputeOrchestrator,
    ReplaySpec,
    ReplacePolicySpec,
    RuntimeReplayHarness,
    WorkflowCoordinator,
    WorkflowSpec,
    WorkflowStepSpec,
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


if __name__ == "__main__":
    unittest.main()
