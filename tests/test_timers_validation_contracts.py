import unittest

from gui.utility.events import GuiError
from gui.utility.scheduler import Timers


class TimersValidationContractTests(unittest.TestCase):
    def test_add_timer_rejects_unhashable_id(self) -> None:
        timers = Timers()

        with self.assertRaises(GuiError):
            timers.add_timer([], 10, lambda: None)  # type: ignore[arg-type]

    def test_add_timer_rejects_non_positive_duration(self) -> None:
        timers = Timers()

        with self.assertRaises(GuiError):
            timers.add_timer("t", 0, lambda: None)
        with self.assertRaises(GuiError):
            timers.add_timer("t", -1, lambda: None)

    def test_add_timer_rejects_non_callable_callback(self) -> None:
        timers = Timers()

        with self.assertRaises(GuiError):
            timers.add_timer("t", 10, None)  # type: ignore[arg-type]

    def test_remove_timer_rejects_unhashable_id(self) -> None:
        timers = Timers()

        with self.assertRaises(GuiError):
            timers.remove_timer({})  # type: ignore[arg-type]

    def test_remove_timer_ignores_missing_timer(self) -> None:
        timers = Timers()

        timers.remove_timer("missing")

        self.assertEqual(timers.timers, {})

    def test_add_timer_replaces_existing_id(self) -> None:
        timers = Timers()
        fired = []

        timers.add_timer("tick", 10, lambda: fired.append("first"))
        timers.add_timer("tick", 5, lambda: fired.append("second"))

        timers.timer_updates(0)
        timers.timer_updates(6)

        self.assertEqual(fired, ["second"])


if __name__ == "__main__":
    unittest.main()
