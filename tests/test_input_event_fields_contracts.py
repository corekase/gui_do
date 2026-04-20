import unittest
from types import SimpleNamespace

from gui.utility.input.event_fields import (
    event_button,
    event_key,
    event_pos,
    event_rel,
    event_wheel_delta,
)


class InputEventFieldsContractsTests(unittest.TestCase):
    def test_event_button_normalization(self) -> None:
        self.assertEqual(event_button(SimpleNamespace(button=1)), 1)
        self.assertIsNone(event_button(SimpleNamespace(button='1')))

    def test_event_key_normalization(self) -> None:
        self.assertEqual(event_key(SimpleNamespace(key=32)), 32)
        self.assertIsNone(event_key(SimpleNamespace(key='k')))

    def test_event_pos_requires_int_pair(self) -> None:
        self.assertEqual(event_pos(SimpleNamespace(pos=(2, 3))), (2, 3))
        self.assertIsNone(event_pos(SimpleNamespace(pos=(2.0, 3))))
        self.assertIsNone(event_pos(SimpleNamespace(pos=(2,))))

    def test_event_rel_defaults_when_invalid(self) -> None:
        self.assertEqual(event_rel(SimpleNamespace(rel=(1, -1))), (1, -1))
        self.assertEqual(event_rel(SimpleNamespace(rel=(1.0, -1))), (0, 0))
        self.assertEqual(event_rel(SimpleNamespace()), (0, 0))

    def test_event_wheel_delta_normalization(self) -> None:
        self.assertEqual(event_wheel_delta(SimpleNamespace(y=2)), 2)
        self.assertEqual(event_wheel_delta(SimpleNamespace(y='3')), 3)
        self.assertEqual(event_wheel_delta(SimpleNamespace(y=True)), 0)
        self.assertEqual(event_wheel_delta(SimpleNamespace()), 0)


if __name__ == '__main__':
    unittest.main()
