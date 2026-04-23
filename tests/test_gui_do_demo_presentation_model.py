import unittest
from types import SimpleNamespace

from demo_parts.life_demo_part import LifeSimulationFeature
from demo_parts.mandelbrot_demo_part import MandelbrotRenderFeature
from demo_parts.mandelbrot_demo_part import MANDEL_KIND_COMPLETE, MANDEL_KIND_FAILED, MANDEL_KIND_RUNNING_ITERATIVE, MANDEL_KIND_STATUS, MandelStatusEvent
from gui import EventBus
from gui_do_demo import GuiDoDemo
from shared.part_lifecycle import PartManager

class GuiDoDemoPresentationModelTests(unittest.TestCase):
    def _make_part(self):
        demo = GuiDoDemo.__new__(GuiDoDemo)
        demo.app = SimpleNamespace(events=EventBus())
        part = MandelbrotRenderFeature()
        part.demo = demo
        part.status_label = SimpleNamespace(text="Mandelbrot: idle")
        part.help_label = SimpleNamespace(text="")
        demo._mandel_feature = part
        return demo, part

    def test_publish_mandel_event_uses_bus_when_ready(self) -> None:
        demo, part = self._make_part()
        part.status_bus_ready = True
        demo.app.events.subscribe(part.status_topic, lambda payload: part.on_status_event(demo, payload), scope=part.status_scope)

        demo._mandel_feature.publish_event("status", "Mandelbrot: event-bus")

        self.assertEqual(part.status_text, "Mandelbrot: event-bus")

    def test_publish_mandel_event_falls_back_without_bus(self) -> None:
        demo, part = self._make_part()
        part.status_bus_ready = False

        demo._mandel_feature.publish_event("status", "Mandelbrot: direct")

        self.assertEqual(part.status_text, "Mandelbrot: direct")

    def test_format_mandel_status_maps_typed_payloads(self) -> None:
        demo = GuiDoDemo.__new__(GuiDoDemo)
        demo._mandel_feature = MandelbrotRenderFeature()

        self.assertEqual(demo._mandel_feature.format_status(demo, {"kind": MANDEL_KIND_RUNNING_ITERATIVE}), "Mandelbrot: running iterative")
        self.assertEqual(demo._mandel_feature.format_status(demo, {"kind": "failed", "detail": "boom"}), "Mandelbrot failed: boom")

    def test_mandel_status_event_round_trip_payload(self) -> None:
        event = MandelStatusEvent(kind="status", detail="hello")

        payload = event.to_payload()
        round_trip = MandelStatusEvent.from_payload(payload)

        self.assertEqual(round_trip, event)

    def test_publish_mandel_running_status_includes_task_count_and_mode(self) -> None:
        demo, mandel_part = self._make_part()
        mandel_part.running_mode = "running iterative"
        mandel_part.task_ids = {"iter", "aux"}
        mandel_part.status_bus_ready = False

        demo._mandel_feature.publish_running_status()

        self.assertEqual(mandel_part.status_text, "Mandelbrot: running iterative (2 tasks)")

    def test_publish_mandel_running_status_dedupes_when_bus_is_ready(self) -> None:
        demo = GuiDoDemo.__new__(GuiDoDemo)

        publish_calls = []

        class _EventsStub:
            def publish(self, topic, payload, scope=None):
                publish_calls.append((topic, payload, scope))

        demo.app = SimpleNamespace(events=_EventsStub())

        mandel_part = MandelbrotRenderFeature()
        mandel_part.running_mode = "running iterative"
        mandel_part.task_ids = {"iter", "aux"}
        mandel_part.demo = demo
        mandel_part.status_bus_ready = True
        mandel_part.status_label = SimpleNamespace(text="Mandelbrot: idle")
        mandel_part.help_label = SimpleNamespace(text="")
        demo._mandel_feature = mandel_part

        demo._mandel_feature.publish_running_status()
        demo._mandel_feature.publish_running_status()

        self.assertEqual(len(publish_calls), 1)

    def test_update_mandel_events_publishes_running_count_when_busy(self) -> None:
        demo, mandel_part = self._make_part()
        mandel_part.running_mode = "running iterative"
        mandel_part.task_ids = {"iter"}

        class _BusyScheduler:
            def get_finished_events(self):
                return []

            def get_failed_events(self):
                return []

            def tasks_busy_match_any(self, *_args):
                return True

            def clear_events(self):
                return None

        mandel_part.scheduler = _BusyScheduler()

        demo._mandel_feature.update_events()

        self.assertEqual(mandel_part.status_text, "Mandelbrot: running iterative (1 task)")

    def test_update_mandel_events_marks_complete_when_running_ends(self) -> None:
        demo, mandel_part = self._make_part()
        mandel_part.status_text = "Mandelbrot: running iterative (1 task)"
        mandel_part.running_mode = "running iterative"
        mandel_part.task_ids = {"iter"}

        class _FinishedScheduler:
            def get_finished_events(self):
                return [SimpleNamespace(task_id="iter")]

            def get_failed_events(self):
                return []

            def tasks_busy_match_any(self, *_args):
                return False

            def clear_events(self):
                return None

            def pop_result(self, _task_id, _default):
                return None

        mandel_part.scheduler = _FinishedScheduler()

        demo._mandel_feature.update_events()

        self.assertEqual(mandel_part.status_text, "Mandelbrot: complete")
        self.assertIsNone(demo._mandel_feature.running_mode)

    def test_update_mandel_events_aggregates_multiple_failures(self) -> None:
        demo, mandel_part = self._make_part()
        mandel_part.running_mode = "running 4M 4Tasks"
        mandel_part.task_ids = {"can1", "can2", "can3"}

        class _FailedScheduler:
            def get_finished_events(self):
                return []

            def get_failed_events(self):
                return [
                    SimpleNamespace(task_id="can1", error="boom"),
                    SimpleNamespace(task_id="can2", error="bang"),
                ]

            def tasks_busy_match_any(self, *_args):
                return False

            def clear_events(self):
                return None

        mandel_part.scheduler = _FailedScheduler()

        demo._mandel_feature.update_events()

        self.assertEqual(mandel_part.status_text, "Mandelbrot failed: 2 tasks failed - can1: boom; can2: bang")

    def test_update_mandel_events_single_failure_includes_task_id(self) -> None:
        demo, mandel_part = self._make_part()
        mandel_part.running_mode = "running iterative"
        mandel_part.task_ids = {"iter"}

        class _SingleFailedScheduler:
            def get_finished_events(self):
                return []

            def get_failed_events(self):
                return [SimpleNamespace(task_id="iter", error="boom")]

            def tasks_busy_match_any(self, *_args):
                return False

            def clear_events(self):
                return None

        mandel_part.scheduler = _SingleFailedScheduler()

        demo._mandel_feature.update_events()

        self.assertEqual(mandel_part.status_text, "Mandelbrot failed: iter: boom")

    def test_update_mandel_events_failure_summary_is_deterministically_sorted(self) -> None:
        demo, mandel_part = self._make_part()
        mandel_part.running_mode = "running 4M 4Tasks"
        mandel_part.task_ids = {"can1", "can2", "can3"}

        class _UnorderedFailedScheduler:
            def get_finished_events(self):
                return []

            def get_failed_events(self):
                return [
                    SimpleNamespace(task_id="can2", error="bang"),
                    SimpleNamespace(task_id="can1", error="boom"),
                ]

            def tasks_busy_match_any(self, *_args):
                return False

            def clear_events(self):
                return None

        mandel_part.scheduler = _UnorderedFailedScheduler()

        demo._mandel_feature.update_events()

        self.assertEqual(mandel_part.status_text, "Mandelbrot failed: 2 tasks failed - can1: boom; can2: bang")

    def test_format_mandel_failure_summary_caps_preview_and_reports_remainder(self) -> None:
        demo = GuiDoDemo.__new__(GuiDoDemo)
        mandel_part = MandelbrotRenderFeature()
        mandel_part.failure_preview_limit = 2
        demo._mandel_feature = mandel_part

        mandel_part.demo = demo
        detail = demo._mandel_feature.format_failure_summary(
            [
                ("can1", "boom"),
                ("can2", "bang"),
                ("can3", "biff"),
                ("can4", "bop"),
            ]
        )

        self.assertEqual(detail, "4 tasks failed - can1: boom; can2: bang; +2 more")

    def test_update_mandel_events_applies_capped_failure_summary(self) -> None:
        demo, mandel_part = self._make_part()
        mandel_part.running_mode = "running 4M 4Tasks"
        mandel_part.failure_preview_limit = 2
        mandel_part.task_ids = {"can1", "can2", "can3", "can4"}
        mandel_part.task_id_pool = ("can1", "can2", "can3", "can4")

        class _ManyFailedScheduler:
            def get_finished_events(self):
                return []

            def get_failed_events(self):
                return [
                    SimpleNamespace(task_id="can3", error="biff"),
                    SimpleNamespace(task_id="can1", error="boom"),
                    SimpleNamespace(task_id="can4", error="bop"),
                    SimpleNamespace(task_id="can2", error="bang"),
                ]

            def tasks_busy_match_any(self, *_args):
                return False

            def clear_events(self):
                return None

        mandel_part.scheduler = _ManyFailedScheduler()

        demo._mandel_feature.update_events()

        self.assertEqual(mandel_part.status_text, "Mandelbrot failed: 4 tasks failed - can1: boom; can2: bang; +2 more")

    def test_set_mandel_failure_preview_limit_clamps_and_returns_value(self) -> None:
        demo, _mandel_part = self._make_part()

        low = demo._mandel_feature.set_failure_preview_limit(demo, 0)
        high = demo._mandel_feature.set_failure_preview_limit(demo, 999)
        normal = demo._mandel_feature.set_failure_preview_limit(demo, 4)

        self.assertEqual(low, 1)
        self.assertEqual(high, 20)
        self.assertEqual(normal, 4)
        self.assertEqual(demo._mandel_feature.failure_preview_limit, 4)

    def test_set_mandel_failure_preview_limit_refreshes_help_label_when_available(self) -> None:
        demo, mandel_part = self._make_part()

        demo._mandel_feature.set_failure_preview_limit(demo, 6)

        self.assertIn("Failure preview [ ]: 6", mandel_part.help_label.text)

    def test_configured_preview_limit_controls_failure_summary(self) -> None:
        demo, mandel_part = self._make_part()
        demo._mandel_feature.set_failure_preview_limit(demo, 1)

        mandel_part.demo = demo
        detail = demo._mandel_feature.format_failure_summary(
            [
                ("can1", "boom"),
                ("can2", "bang"),
                ("can3", "biff"),
            ]
        )

        self.assertEqual(detail, "3 tasks failed - can1: boom; +2 more")

    def test_format_mandel_help_text_includes_modes_and_preview_limit(self) -> None:
        demo = GuiDoDemo.__new__(GuiDoDemo)
        mandel_part = MandelbrotRenderFeature()
        mandel_part.failure_preview_limit = 5
        demo._mandel_feature = mandel_part

        text = demo._mandel_feature.format_help_text()

        self.assertIn("Modes: Iterative, Recursive, 1M 4Tasks, 4M 4Tasks", text)
        self.assertIn("Failure preview [ ]: 5", text)

    def test_adjust_mandel_failure_preview_limit_publishes_status(self) -> None:
        demo, mandel_part = self._make_part()
        mandel_part.failure_preview_limit = 3

        consumed = demo._mandel_feature.adjust_failure_preview_limit(demo, 1)

        self.assertTrue(consumed)
        self.assertEqual(demo._mandel_feature.failure_preview_limit, 4)
        self.assertEqual(mandel_part.status_text, "Mandelbrot failure preview limit: 4")

    def test_adjust_mandel_failure_preview_limit_reports_bound(self) -> None:
        demo, mandel_part = self._make_part()
        mandel_part.failure_preview_limit = 1

        consumed = demo._mandel_feature.adjust_failure_preview_limit(demo, -1)

        self.assertTrue(consumed)
        self.assertEqual(demo._mandel_feature.failure_preview_limit, 1)
        self.assertEqual(mandel_part.status_text, "Mandelbrot failure preview limit: 1 (at bound)")

    def test_mandel_part_posts_status_message_to_life_part(self) -> None:
        demo = SimpleNamespace()

        life = LifeSimulationFeature()
        mandel = MandelbrotRenderFeature()
        mandel.status_label = SimpleNamespace(text="Mandelbrot: idle")
        mandel.help_label = SimpleNamespace(text="")
        mandel.update_events = lambda: None

        manager = PartManager(SimpleNamespace())
        manager.register(life, host=demo)
        manager.register(mandel, host=demo)

        mandel.on_update(demo)
        life.on_update(demo)

        self.assertEqual(life.last_mandel_status, "Mandelbrot: idle")


if __name__ == "__main__":
    unittest.main()
