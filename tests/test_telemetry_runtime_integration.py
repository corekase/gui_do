import unittest
from types import SimpleNamespace

from gui import EventBus
from gui.core.task_scheduler import TaskScheduler
from gui.core.telemetry import telemetry_collector
from shared.feature_lifecycle import Feature
from shared.feature_lifecycle import FeatureManager


class _StubFeature(Feature):
    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.calls = 0

    def on_update(self, host) -> None:
        del host
        self.calls += 1


class TelemetryRuntimeIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.collector = telemetry_collector()
        self.collector.reset()
        self.collector.clear_filters()
        self.collector.enable()

    def tearDown(self) -> None:
        self.collector.disable()
        self.collector.clear_filters()
        self.collector.reset()

    def test_event_bus_publish_is_instrumented(self) -> None:
        bus = EventBus()
        received = []
        bus.subscribe("topic", lambda payload: received.append(payload))

        bus.publish("topic", {"ok": True})

        self.assertEqual(received, [{"ok": True}])
        points = {(sample.system, sample.point) for sample in self.collector.snapshot()}
        self.assertIn(("event_bus", "publish"), points)
        self.assertIn(("event_bus", "publish_handler"), points)

    def test_scheduler_update_is_instrumented(self) -> None:
        scheduler = TaskScheduler(max_workers=1)
        try:
            scheduler.add_task("demo", lambda _task_id: 123)
            for _ in range(20):
                scheduler.update()
                if scheduler.get_finished_tasks():
                    break

            points = {(sample.system, sample.point) for sample in self.collector.snapshot()}
            self.assertIn(("task_scheduler", "update"), points)
            self.assertIn(("task_scheduler", "collect_finished_tasks"), points)
        finally:
            scheduler.shutdown()

    def test_feature_manager_update_and_message_are_instrumented(self) -> None:
        app = SimpleNamespace(active_scene_name="main")
        manager = FeatureManager(app)
        part_a = _StubFeature("a")
        part_b = _StubFeature("b")
        manager.register(part_a, host=app)
        manager.register(part_b, host=app)

        sent = manager.send_message("a", "b", {"topic": "ping"})
        manager.update_features(host=app)

        self.assertTrue(sent)
        points = {(sample.system, sample.point) for sample in self.collector.snapshot()}
        self.assertIn(("feature_lifecycle", "send_message"), points)
        self.assertIn(("feature_lifecycle", "feature_update"), points)


if __name__ == "__main__":
    unittest.main()
