import unittest
from types import SimpleNamespace

from demo_parts.mandel_events import MANDEL_KIND_COMPLETE, MANDEL_KIND_FAILED, MANDEL_KIND_RUNNING_ITERATIVE, MANDEL_KIND_STATUS, MandelStatusEvent
from gui import EventBus
from gui_do_demo import _MandelPresentationModel
from gui_do_demo import GuiDoDemo


class GuiDoDemoPresentationModelTests(unittest.TestCase):
    def test_status_text_updates_via_set_status(self) -> None:
        model = _MandelPresentationModel()

        model.set_status("Mandelbrot: running iterative")

        self.assertEqual(model.status_text.value, "Mandelbrot: running iterative")

    def test_observer_receives_status_updates_and_dispose_unsubscribes(self) -> None:
        model = _MandelPresentationModel()
        seen = []
        model.bind(model.status_text, lambda text: seen.append(text))

        model.set_status("Mandelbrot: running")
        model.dispose()
        model.set_status("Mandelbrot: complete")

        self.assertEqual(seen, ["Mandelbrot: running"])

    def test_publish_mandel_event_uses_bus_when_ready(self) -> None:
        demo = GuiDoDemo.__new__(GuiDoDemo)
        demo.mandel_model = _MandelPresentationModel()
        demo.app = SimpleNamespace(events=EventBus())
        demo._mandel_status_topic = "demo.mandel.status"
        demo._mandel_status_scope = "main"
        demo._mandel_status_bus_ready = True
        demo._mandel_status_subscription = demo.app.events.subscribe(
            demo._mandel_status_topic,
            demo._on_mandel_status_event,
            scope=demo._mandel_status_scope,
        )

        demo._publish_mandel_event("status", "Mandelbrot: event-bus")

        self.assertEqual(demo.mandel_model.status_text.value, "Mandelbrot: event-bus")

    def test_publish_mandel_event_falls_back_without_bus(self) -> None:
        demo = GuiDoDemo.__new__(GuiDoDemo)
        demo.mandel_model = _MandelPresentationModel()
        demo._mandel_status_bus_ready = False

        demo._publish_mandel_event("status", "Mandelbrot: direct")

        self.assertEqual(demo.mandel_model.status_text.value, "Mandelbrot: direct")

    def test_format_mandel_status_maps_typed_payloads(self) -> None:
        demo = GuiDoDemo.__new__(GuiDoDemo)

        self.assertEqual(demo._format_mandel_status({"kind": MANDEL_KIND_RUNNING_ITERATIVE}), "Mandelbrot: running iterative")
        self.assertEqual(demo._format_mandel_status({"kind": "failed", "detail": "boom"}), "Mandelbrot failed: boom")

    def test_mandel_status_event_round_trip_payload(self) -> None:
        event = MandelStatusEvent(kind="status", detail="hello")

        payload = event.to_payload()
        round_trip = MandelStatusEvent.from_payload(payload)

        self.assertEqual(round_trip, event)

    def test_publish_mandel_running_status_includes_task_count_and_mode(self) -> None:
        demo = GuiDoDemo.__new__(GuiDoDemo)
        demo.mandel_model = _MandelPresentationModel()
        demo._mandel_status_bus_ready = False
        demo._mandel_running_mode = "running iterative"
        demo.mandel_task_ids = {"iter", "aux"}

        published = []

        def _capture(kind, detail=None):
            published.append((kind, detail))
            demo.mandel_model.set_status(str(detail))

        demo._publish_mandel_event = _capture

        demo._publish_mandel_running_status()

        self.assertEqual(published, [(MANDEL_KIND_STATUS, "Mandelbrot: running iterative (2 tasks)")])

    def test_update_mandel_events_publishes_running_count_when_busy(self) -> None:
        demo = GuiDoDemo.__new__(GuiDoDemo)
        demo.mandel_model = _MandelPresentationModel()
        demo._mandel_running_mode = "running iterative"
        demo.mandel_task_ids = {"iter"}

        class _BusyScheduler:
            def get_finished_events(self):
                return []

            def get_failed_events(self):
                return []

            def tasks_busy_match_any(self, *_args):
                return True

            def clear_events(self):
                return None

        demo.mandel_scheduler = _BusyScheduler()
        demo.mandel_task_id_pool = ("iter",)
        demo._set_mandel_task_buttons_disabled = lambda _disabled: None
        published = []

        def _capture(kind, detail=None):
            published.append((kind, detail))
            demo.mandel_model.set_status(str(detail))

        demo._publish_mandel_event = _capture

        demo._update_mandel_events()

        self.assertIn((MANDEL_KIND_STATUS, "Mandelbrot: running iterative (1 task)"), published)

    def test_update_mandel_events_marks_complete_when_running_ends(self) -> None:
        demo = GuiDoDemo.__new__(GuiDoDemo)
        demo.mandel_model = _MandelPresentationModel()
        demo.mandel_model.set_status("Mandelbrot: running iterative (1 task)")
        demo._mandel_running_mode = "running iterative"
        demo.mandel_task_ids = {"iter"}

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

        demo.mandel_scheduler = _FinishedScheduler()
        demo.mandel_task_id_pool = ("iter",)
        demo._set_mandel_task_buttons_disabled = lambda _disabled: None
        published = []

        def _capture(kind, detail=None):
            published.append((kind, detail))

        demo._publish_mandel_event = _capture

        demo._update_mandel_events()

        self.assertIn((MANDEL_KIND_COMPLETE, None), published)
        self.assertIsNone(demo._mandel_running_mode)

    def test_update_mandel_events_aggregates_multiple_failures(self) -> None:
        demo = GuiDoDemo.__new__(GuiDoDemo)
        demo.mandel_model = _MandelPresentationModel()
        demo._mandel_running_mode = "running 4M 4Tasks"
        demo.mandel_task_ids = {"can1", "can2", "can3"}

        class _FailedScheduler:
            def get_finished_events(self):
                return []

            def get_failed_events(self):
                return [
                    SimpleNamespace(task_id="can1", error="boom"),
                    SimpleNamespace(task_id="can2", error="bang"),
                ]

            def tasks_busy_match_any(self, *_args):
                return True

            def clear_events(self):
                return None

        demo.mandel_scheduler = _FailedScheduler()
        demo.mandel_task_id_pool = ("can1", "can2", "can3")
        demo._set_mandel_task_buttons_disabled = lambda _disabled: None
        published = []

        def _capture(kind, detail=None):
            published.append((kind, detail))
            if detail is not None:
                demo.mandel_model.set_status(str(detail))

        demo._publish_mandel_event = _capture

        demo._update_mandel_events()

        self.assertIn((MANDEL_KIND_FAILED, "2 tasks failed - can1: boom; can2: bang"), published)

    def test_update_mandel_events_single_failure_includes_task_id(self) -> None:
        demo = GuiDoDemo.__new__(GuiDoDemo)
        demo.mandel_model = _MandelPresentationModel()
        demo._mandel_running_mode = "running iterative"
        demo.mandel_task_ids = {"iter"}

        class _SingleFailedScheduler:
            def get_finished_events(self):
                return []

            def get_failed_events(self):
                return [SimpleNamespace(task_id="iter", error="boom")]

            def tasks_busy_match_any(self, *_args):
                return False

            def clear_events(self):
                return None

        demo.mandel_scheduler = _SingleFailedScheduler()
        demo.mandel_task_id_pool = ("iter",)
        demo._set_mandel_task_buttons_disabled = lambda _disabled: None
        published = []

        def _capture(kind, detail=None):
            published.append((kind, detail))

        demo._publish_mandel_event = _capture

        demo._update_mandel_events()

        self.assertIn((MANDEL_KIND_FAILED, "iter: boom"), published)

    def test_update_mandel_events_failure_summary_is_deterministically_sorted(self) -> None:
        demo = GuiDoDemo.__new__(GuiDoDemo)
        demo.mandel_model = _MandelPresentationModel()
        demo._mandel_running_mode = "running 4M 4Tasks"
        demo.mandel_task_ids = {"can1", "can2", "can3"}

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

        demo.mandel_scheduler = _UnorderedFailedScheduler()
        demo.mandel_task_id_pool = ("can1", "can2", "can3")
        demo._set_mandel_task_buttons_disabled = lambda _disabled: None
        published = []

        def _capture(kind, detail=None):
            published.append((kind, detail))

        demo._publish_mandel_event = _capture

        demo._update_mandel_events()

        self.assertIn((MANDEL_KIND_FAILED, "2 tasks failed - can1: boom; can2: bang"), published)

    def test_format_mandel_failure_summary_caps_preview_and_reports_remainder(self) -> None:
        demo = GuiDoDemo.__new__(GuiDoDemo)
        demo._mandel_failure_preview_limit = 2

        detail = demo._format_mandel_failure_summary(
            [
                ("can1", "boom"),
                ("can2", "bang"),
                ("can3", "biff"),
                ("can4", "bop"),
            ]
        )

        self.assertEqual(detail, "4 tasks failed - can1: boom; can2: bang; +2 more")

    def test_update_mandel_events_applies_capped_failure_summary(self) -> None:
        demo = GuiDoDemo.__new__(GuiDoDemo)
        demo.mandel_model = _MandelPresentationModel()
        demo._mandel_running_mode = "running 4M 4Tasks"
        demo._mandel_failure_preview_limit = 2
        demo.mandel_task_ids = {"can1", "can2", "can3", "can4"}

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

        demo.mandel_scheduler = _ManyFailedScheduler()
        demo.mandel_task_id_pool = ("can1", "can2", "can3", "can4")
        demo._set_mandel_task_buttons_disabled = lambda _disabled: None
        published = []

        def _capture(kind, detail=None):
            published.append((kind, detail))

        demo._publish_mandel_event = _capture

        demo._update_mandel_events()

        self.assertIn((MANDEL_KIND_FAILED, "4 tasks failed - can1: boom; can2: bang; +2 more"), published)

    def test_set_mandel_failure_preview_limit_clamps_and_returns_value(self) -> None:
        demo = GuiDoDemo.__new__(GuiDoDemo)

        low = demo.set_mandel_failure_preview_limit(0)
        high = demo.set_mandel_failure_preview_limit(999)
        normal = demo.set_mandel_failure_preview_limit(4)

        self.assertEqual(low, 1)
        self.assertEqual(high, 20)
        self.assertEqual(normal, 4)
        self.assertEqual(demo._mandel_failure_preview_limit, 4)

    def test_configured_preview_limit_controls_failure_summary(self) -> None:
        demo = GuiDoDemo.__new__(GuiDoDemo)
        demo.set_mandel_failure_preview_limit(1)

        detail = demo._format_mandel_failure_summary(
            [
                ("can1", "boom"),
                ("can2", "bang"),
                ("can3", "biff"),
            ]
        )

        self.assertEqual(detail, "3 tasks failed - can1: boom; +2 more")

    def test_adjust_mandel_failure_preview_limit_publishes_status(self) -> None:
        demo = GuiDoDemo.__new__(GuiDoDemo)
        demo._mandel_failure_preview_limit = 3
        published = []
        demo._publish_mandel_event = lambda kind, detail=None: published.append((kind, detail))

        consumed = demo._adjust_mandel_failure_preview_limit(1)

        self.assertTrue(consumed)
        self.assertEqual(demo._mandel_failure_preview_limit, 4)
        self.assertIn((MANDEL_KIND_STATUS, "Mandelbrot failure preview limit: 4"), published)

    def test_adjust_mandel_failure_preview_limit_reports_bound(self) -> None:
        demo = GuiDoDemo.__new__(GuiDoDemo)
        demo._mandel_failure_preview_limit = 1
        published = []
        demo._publish_mandel_event = lambda kind, detail=None: published.append((kind, detail))

        consumed = demo._adjust_mandel_failure_preview_limit(-1)

        self.assertTrue(consumed)
        self.assertEqual(demo._mandel_failure_preview_limit, 1)
        self.assertIn((MANDEL_KIND_STATUS, "Mandelbrot failure preview limit: 1 (at bound)"), published)


if __name__ == "__main__":
    unittest.main()
