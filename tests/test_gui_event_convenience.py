"""Tests for GuiEvent convenience helper methods: is_left_down/up, is_right_down/up,
is_middle_down/up, is_text_event, and clone."""
import unittest

from gui.core.gui_event import EventPhase, EventType, GuiEvent


def _make(kind: EventType, **kwargs) -> GuiEvent:
    return GuiEvent(kind=kind, type=0, **kwargs)


class IsLeftDownUpTests(unittest.TestCase):

    def test_is_left_down_true_for_button_1_down(self) -> None:
        ev = _make(EventType.MOUSE_BUTTON_DOWN, button=1)
        self.assertTrue(ev.is_left_down())

    def test_is_left_down_false_for_button_3_down(self) -> None:
        ev = _make(EventType.MOUSE_BUTTON_DOWN, button=3)
        self.assertFalse(ev.is_left_down())

    def test_is_left_down_false_for_button_1_up(self) -> None:
        ev = _make(EventType.MOUSE_BUTTON_UP, button=1)
        self.assertFalse(ev.is_left_down())

    def test_is_left_up_true_for_button_1_up(self) -> None:
        ev = _make(EventType.MOUSE_BUTTON_UP, button=1)
        self.assertTrue(ev.is_left_up())

    def test_is_left_up_false_for_button_1_down(self) -> None:
        ev = _make(EventType.MOUSE_BUTTON_DOWN, button=1)
        self.assertFalse(ev.is_left_up())

    def test_is_left_up_false_for_button_3_up(self) -> None:
        ev = _make(EventType.MOUSE_BUTTON_UP, button=3)
        self.assertFalse(ev.is_left_up())


class IsRightDownUpTests(unittest.TestCase):

    def test_is_right_down_true_for_button_3_down(self) -> None:
        ev = _make(EventType.MOUSE_BUTTON_DOWN, button=3)
        self.assertTrue(ev.is_right_down())

    def test_is_right_down_false_for_button_1_down(self) -> None:
        ev = _make(EventType.MOUSE_BUTTON_DOWN, button=1)
        self.assertFalse(ev.is_right_down())

    def test_is_right_down_false_for_button_3_up(self) -> None:
        ev = _make(EventType.MOUSE_BUTTON_UP, button=3)
        self.assertFalse(ev.is_right_down())

    def test_is_right_up_true_for_button_3_up(self) -> None:
        ev = _make(EventType.MOUSE_BUTTON_UP, button=3)
        self.assertTrue(ev.is_right_up())

    def test_is_right_up_false_for_button_1_up(self) -> None:
        ev = _make(EventType.MOUSE_BUTTON_UP, button=1)
        self.assertFalse(ev.is_right_up())


class IsMiddleDownUpTests(unittest.TestCase):

    def test_is_middle_down_true_for_button_2_down(self) -> None:
        ev = _make(EventType.MOUSE_BUTTON_DOWN, button=2)
        self.assertTrue(ev.is_middle_down())

    def test_is_middle_down_false_for_button_1_down(self) -> None:
        ev = _make(EventType.MOUSE_BUTTON_DOWN, button=1)
        self.assertFalse(ev.is_middle_down())

    def test_is_middle_up_true_for_button_2_up(self) -> None:
        ev = _make(EventType.MOUSE_BUTTON_UP, button=2)
        self.assertTrue(ev.is_middle_up())

    def test_is_middle_up_false_for_button_2_down(self) -> None:
        ev = _make(EventType.MOUSE_BUTTON_DOWN, button=2)
        self.assertFalse(ev.is_middle_up())


class IsTextEventTests(unittest.TestCase):

    def test_is_text_event_true_for_text_input(self) -> None:
        ev = _make(EventType.TEXT_INPUT, text="a")
        self.assertTrue(ev.is_text_event())

    def test_is_text_event_true_for_text_editing(self) -> None:
        ev = _make(EventType.TEXT_EDITING)
        self.assertTrue(ev.is_text_event())

    def test_is_text_event_false_for_key_down(self) -> None:
        ev = _make(EventType.KEY_DOWN, key=65)
        self.assertFalse(ev.is_text_event())

    def test_is_text_event_false_for_mouse_down(self) -> None:
        ev = _make(EventType.MOUSE_BUTTON_DOWN, button=1)
        self.assertFalse(ev.is_text_event())


class CloneTests(unittest.TestCase):

    def test_clone_returns_different_object(self) -> None:
        ev = _make(EventType.KEY_DOWN, key=65)
        cloned = ev.clone()
        self.assertIsNot(cloned, ev)

    def test_clone_preserves_fields(self) -> None:
        ev = _make(EventType.MOUSE_BUTTON_DOWN, button=1, pos=(10, 20))
        cloned = ev.clone()
        self.assertEqual(cloned.kind, EventType.MOUSE_BUTTON_DOWN)
        self.assertEqual(cloned.button, 1)
        self.assertEqual(cloned.pos, (10, 20))

    def test_clone_propagation_state_is_independent(self) -> None:
        ev = _make(EventType.KEY_DOWN, key=65)
        cloned = ev.clone()
        cloned.stop_propagation()
        self.assertFalse(ev.propagation_stopped)
        self.assertTrue(cloned.propagation_stopped)

    def test_clone_default_prevented_is_independent(self) -> None:
        ev = _make(EventType.MOUSE_BUTTON_DOWN, button=1)
        cloned = ev.clone()
        cloned.prevent_default()
        self.assertFalse(ev.default_prevented)
        self.assertTrue(cloned.default_prevented)

    def test_clone_of_clone_is_independent(self) -> None:
        ev = _make(EventType.MOUSE_WHEEL, wheel_y=3)
        first = ev.clone()
        second = first.clone()
        second.prevent_default()
        self.assertFalse(first.default_prevented)

    def test_clone_preserves_phase(self) -> None:
        ev = _make(EventType.MOUSE_MOTION)
        ev.phase = EventPhase.CAPTURE
        cloned = ev.clone()
        self.assertEqual(cloned.phase, EventPhase.CAPTURE)


if __name__ == "__main__":
    unittest.main()
