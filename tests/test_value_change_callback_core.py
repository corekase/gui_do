import unittest

from gui.core.value_change_callback import dispatch_value_change
from gui.core.value_change_reason import ValueChangeReason


class ValueChangeCallbackCoreTests(unittest.TestCase):
    def test_dispatch_handles_value_only_callback(self) -> None:
        seen = []

        dispatch_value_change(lambda value: seen.append(("value", value)), 42, ValueChangeReason.PROGRAMMATIC)

        self.assertEqual(seen, [("value", 42)])

    def test_dispatch_handles_value_and_reason_callback(self) -> None:
        seen = []

        dispatch_value_change(lambda value, reason: seen.append((value, reason)), 5, ValueChangeReason.KEYBOARD)

        self.assertEqual(seen, [(5, ValueChangeReason.KEYBOARD)])

    def test_dispatch_handles_varargs_callback(self) -> None:
        seen = []

        def callback(*args):
            seen.append(args)

        dispatch_value_change(callback, 7, ValueChangeReason.WHEEL)

        self.assertEqual(seen, [(7, ValueChangeReason.WHEEL)])

    def test_dispatch_ignores_none_callback(self) -> None:
        dispatch_value_change(None, 1, ValueChangeReason.PROGRAMMATIC)


if __name__ == "__main__":
    unittest.main()
