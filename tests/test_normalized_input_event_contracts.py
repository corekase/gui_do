import unittest
from types import SimpleNamespace

from pygame.locals import MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION

from gui.utility.input.normalized_event import normalize_input_event


class NormalizedInputEventContractsTests(unittest.TestCase):
    def test_left_down_and_left_up_predicates(self) -> None:
        down = normalize_input_event(SimpleNamespace(type=MOUSEBUTTONDOWN, button=1))
        up = normalize_input_event(SimpleNamespace(type=MOUSEBUTTONUP, button=1))
        motion = normalize_input_event(SimpleNamespace(type=MOUSEMOTION, rel=(1, 2)))

        self.assertTrue(down.is_left_down)
        self.assertFalse(down.is_left_up)
        self.assertTrue(up.is_left_up)
        self.assertFalse(up.is_left_down)
        self.assertFalse(motion.is_left_down)
        self.assertFalse(motion.is_left_up)

    def test_normalized_fields_preserve_canonical_defaults(self) -> None:
        norm = normalize_input_event(SimpleNamespace(type=MOUSEMOTION))

        self.assertIsNone(norm.button)
        self.assertIsNone(norm.key)
        self.assertIsNone(norm.pos)
        self.assertEqual(norm.rel, (0, 0))
        self.assertEqual(norm.wheel_delta, 0)

    def test_normalization_is_cached_per_event_instance(self) -> None:
        event = SimpleNamespace(type=MOUSEMOTION, rel=(1, 2))

        first = normalize_input_event(event)
        second = normalize_input_event(event)

        self.assertIs(first, second)

    def test_normalization_still_works_for_events_without_setattr(self) -> None:
        class ReadOnlyEvent:
            __slots__ = ('type', 'button')

            def __init__(self, event_type: int, button: int) -> None:
                self.type = event_type
                self.button = button

        event = ReadOnlyEvent(MOUSEBUTTONDOWN, 1)

        first = normalize_input_event(event)
        second = normalize_input_event(event)

        self.assertTrue(first.is_left_down)
        self.assertTrue(second.is_left_down)
        self.assertIsNot(first, second)


if __name__ == '__main__':
    unittest.main()
