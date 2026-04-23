import unittest
from unittest import mock

from gui.loop.ui_engine import UiEngine


class _StubInputState:
    def __init__(self) -> None:
        pass


class _StubApp:
    def __init__(self) -> None:
        self.running = True
        self.input_state = _StubInputState()
        self.processed_events = []
        self.update_calls = 0
        self.draw_calls = 0
        self.shutdown_calls = 0

    def process_event(self, event) -> None:
        self.processed_events.append(event)

    def update(self, _dt_seconds: float) -> None:
        self.update_calls += 1

    def draw(self) -> None:
        self.draw_calls += 1

    def shutdown(self) -> None:
        self.shutdown_calls += 1


class UiEngineRuntimeTests(unittest.TestCase):
    def test_run_stops_without_update_draw_after_quit_event(self) -> None:
        app = _StubApp()

        def _process_event(_event) -> None:
            app.running = False

        app.process_event = _process_event
        engine = UiEngine(app)

        with mock.patch("pygame.event.get", return_value=[object()]), mock.patch("pygame.display.flip"):
            frames = engine.run()

        self.assertEqual(frames, 0)
        self.assertEqual(app.update_calls, 0)
        self.assertEqual(app.draw_calls, 0)
        self.assertEqual(app.shutdown_calls, 1)

    def test_run_respects_max_frames_and_returns_processed_count(self) -> None:
        app = _StubApp()
        engine = UiEngine(app)

        with mock.patch("pygame.event.get", return_value=[]), mock.patch("pygame.display.flip"):
            frames = engine.run(max_frames=3)

        self.assertEqual(frames, 3)
        self.assertTrue(app.running)
        self.assertEqual(app.update_calls, 3)
        self.assertEqual(app.draw_calls, 3)
        self.assertEqual(app.shutdown_calls, 1)


if __name__ == "__main__":
    unittest.main()
