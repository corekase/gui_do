import unittest

from gui_do.core.value_change_callback import dispatch_value_change
from gui_do.core.value_change_callback import validate_value_change_callback
from gui_do.core.value_change_reason import ValueChangeReason


class ValueChangeCallbackCoreTests(unittest.TestCase):
    def test_dispatch_calls_callback_with_value_and_reason(self) -> None:
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

    def test_validate_accepts_none_callback(self) -> None:
        validate_value_change_callback(None)

    def test_validate_accepts_callable_callback(self) -> None:
        validate_value_change_callback(lambda value, reason: None)

    def test_validate_rejects_non_callable(self) -> None:
        with self.assertRaises(TypeError):
            validate_value_change_callback("not_callable")  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
