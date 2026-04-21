import unittest
from types import SimpleNamespace

from demo_parts.mandel_events import MANDEL_KIND_RUNNING_ITERATIVE, MandelStatusEvent
from gui.core.event_bus import EventBus
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


if __name__ == "__main__":
    unittest.main()
