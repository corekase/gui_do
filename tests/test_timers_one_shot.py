import unittest

from gui import Timers


class TimersOneShotTests(unittest.TestCase):
    def setUp(self) -> None:
        self.timers = Timers()

    # --- add_once basic fire behaviour ---

    def test_add_once_fires_after_delay(self) -> None:
        fired = []
        self.timers.add_once("t", 0.1, lambda: fired.append(True))

        self.timers.update(0.05)
        self.assertEqual(fired, [], "should not fire before delay elapsed")

        self.timers.update(0.06)
        self.assertEqual(fired, [True], "should fire exactly once when delay elapses")

    def test_add_once_fires_only_once(self) -> None:
        fired = []
        self.timers.add_once("t", 0.1, lambda: fired.append(True))

        self.timers.update(1.0)
        self.assertEqual(fired, [True], "one-shot must fire exactly once regardless of excess time")

    def test_add_once_auto_removes_after_fire(self) -> None:
        self.timers.add_once("t", 0.1, lambda: None)

        self.assertTrue(self.timers.has_timer("t"), "timer should exist before firing")
        self.timers.update(0.2)
        self.assertFalse(self.timers.has_timer("t"), "timer should be gone after it fires")

    def test_add_once_does_not_fire_before_delay(self) -> None:
        fired = []
        self.timers.add_once("t", 0.5, lambda: fired.append(True))
        self.timers.update(0.49)
        self.assertEqual(fired, [])
        self.assertTrue(self.timers.has_timer("t"), "timer should still be registered")

    # --- has_timer query ---

    def test_has_timer_false_for_missing_id(self) -> None:
        self.assertFalse(self.timers.has_timer("nonexistent"))

    def test_has_timer_true_for_repeating_timer(self) -> None:
        self.timers.add_timer("r", 0.1, lambda: None)
        self.assertTrue(self.timers.has_timer("r"))

    def test_has_timer_true_for_pending_one_shot(self) -> None:
        self.timers.add_once("o", 0.5, lambda: None)
        self.assertTrue(self.timers.has_timer("o"))

    def test_has_timer_false_after_remove_timer(self) -> None:
        self.timers.add_timer("r", 0.1, lambda: None)
        self.timers.remove_timer("r")
        self.assertFalse(self.timers.has_timer("r"))

    # --- add_once validation ---

    def test_add_once_rejects_zero_delay(self) -> None:
        with self.assertRaises(ValueError):
            self.timers.add_once("t", 0, lambda: None)

    def test_add_once_rejects_negative_delay(self) -> None:
        with self.assertRaises(ValueError):
            self.timers.add_once("t", -1.0, lambda: None)

    def test_add_once_rejects_non_callable(self) -> None:
        with self.assertRaises(ValueError):
            self.timers.add_once("t", 0.1, "not-a-callable")  # type: ignore[arg-type]

    # --- coexistence: repeating and one-shot side by side ---

    def test_repeating_timer_continues_after_one_shot_fires(self) -> None:
        repeat_ticks = []
        once_ticks = []
        self.timers.add_timer("repeat", 0.1, lambda: repeat_ticks.append(True))
        self.timers.add_once("once", 0.15, lambda: once_ticks.append(True))

        self.timers.update(0.2)

        self.assertGreaterEqual(len(repeat_ticks), 2, "repeating timer should have fired twice in 0.2 s")
        self.assertEqual(once_ticks, [True], "one-shot should fire exactly once")
        self.assertTrue(self.timers.has_timer("repeat"), "repeating timer should still be registered")
        self.assertFalse(self.timers.has_timer("once"), "one-shot should have been removed")

    # --- add_once overwrites existing timer ---

    def test_add_once_overwrites_existing_repeating_timer_with_same_id(self) -> None:
        repeat_ticks = []
        once_ticks = []
        self.timers.add_timer("shared", 0.05, lambda: repeat_ticks.append(True))
        self.timers.add_once("shared", 0.1, lambda: once_ticks.append(True))

        self.timers.update(0.2)

        # The once-timer replaced the repeating timer; only the one-shot should fire.
        self.assertEqual(once_ticks, [True])
        self.assertEqual(repeat_ticks, [], "replaced repeating timer must not fire")


if __name__ == "__main__":
    unittest.main()
