import unittest

from gui.utility.engine import Engine
from gui.utility.state_manager import StateManager


class RecordingClock:
    def __init__(self) -> None:
        self.ticks = []

    def tick(self, fps: int) -> None:
        self.ticks.append(fps)


class EngineTestabilityTests(unittest.TestCase):
    def test_run_does_not_hard_exit_when_exit_disabled(self) -> None:
        state = StateManager(mouse_pos_provider=lambda: (0, 0))
        quit_calls = []
        exit_calls = []
        clock = RecordingClock()

        engine = Engine(
            state,
            fps=30,
            clock=clock,
            ticks_provider=lambda: 123,
            display_flip=lambda: None,
            quit_callable=lambda: quit_calls.append(True),
            exit_callable=lambda code: exit_calls.append(code),
            exit_on_finish=False,
        )

        # No active context means the loop exits immediately but still performs cleanup.
        engine.run()

        self.assertEqual(quit_calls, [True])
        self.assertEqual(exit_calls, [])
        self.assertEqual(clock.ticks, [])

    def test_run_reraises_exception_and_still_quits(self) -> None:
        class BrokenStateManager(StateManager):
            def __enter__(self):
                raise RuntimeError("boom")

        state = BrokenStateManager(mouse_pos_provider=lambda: (0, 0))
        quit_calls = []
        exit_codes = []

        def failing_quit() -> None:
            quit_calls.append(True)

        def record_exit(code: int) -> None:
            exit_codes.append(code)

        engine = Engine(
            state,
            quit_callable=failing_quit,
            exit_callable=record_exit,
            exit_on_finish=True,
        )

        with self.assertRaises(RuntimeError):
            engine.run()

        self.assertEqual(quit_calls, [True])
        self.assertEqual(exit_codes, [])

    def test_run_exits_with_zero_on_clean_shutdown(self) -> None:
        state = StateManager(mouse_pos_provider=lambda: (0, 0))
        exit_codes = []

        engine = Engine(
            state,
            quit_callable=lambda: None,
            exit_callable=lambda code: exit_codes.append(code),
            exit_on_finish=True,
        )

        engine.run()

        self.assertEqual(exit_codes, [0])


if __name__ == "__main__":
    unittest.main()
