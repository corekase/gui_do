"""Tests for GuiEvent, EventType, EventPhase."""
import unittest
import pygame

from gui_do.events.gui_event import EventType, EventPhase, GuiEvent

pygame.init()


def _event(kind=EventType.PASS, **kwargs):
    return GuiEvent(kind=kind, type=0, **kwargs)


# ===========================================================================
# EventType
# ===========================================================================


class TestEventType(unittest.TestCase):
    def test_pass_value(self):
        self.assertEqual("pass", EventType.PASS.value)

    def test_quit_value(self):
        self.assertEqual("quit", EventType.QUIT.value)

    def test_key_down_value(self):
        self.assertEqual("key_down", EventType.KEY_DOWN.value)

    def test_key_up_value(self):
        self.assertEqual("key_up", EventType.KEY_UP.value)

    def test_mouse_button_down(self):
        self.assertEqual("mouse_button_down", EventType.MOUSE_BUTTON_DOWN.value)

    def test_mouse_button_up(self):
        self.assertEqual("mouse_button_up", EventType.MOUSE_BUTTON_UP.value)

    def test_mouse_motion(self):
        self.assertEqual("mouse_motion", EventType.MOUSE_MOTION.value)

    def test_mouse_wheel(self):
        self.assertEqual("mouse_wheel", EventType.MOUSE_WHEEL.value)

    def test_text_input(self):
        self.assertEqual("text_input", EventType.TEXT_INPUT.value)


# ===========================================================================
# EventPhase
# ===========================================================================


class TestEventPhase(unittest.TestCase):
    def test_capture(self):
        self.assertEqual("capture", EventPhase.CAPTURE.value)

    def test_target(self):
        self.assertEqual("target", EventPhase.TARGET.value)

    def test_bubble(self):
        self.assertEqual("bubble", EventPhase.BUBBLE.value)


# ===========================================================================
# GuiEvent — initial defaults
# ===========================================================================


class TestGuiEventDefaults(unittest.TestCase):
    def test_kind_stored(self):
        event = _event(EventType.QUIT)
        self.assertIs(EventType.QUIT, event.kind)

    def test_phase_default_target(self):
        event = _event()
        self.assertIs(EventPhase.TARGET, event.phase)

    def test_propagation_stopped_false(self):
        event = _event()
        self.assertFalse(event.propagation_stopped)

    def test_default_prevented_false(self):
        event = _event()
        self.assertFalse(event.default_prevented)

    def test_key_none_by_default(self):
        event = _event()
        self.assertIsNone(event.key)

    def test_pos_none_by_default(self):
        event = _event()
        self.assertIsNone(event.pos)

    def test_button_none_by_default(self):
        event = _event()
        self.assertIsNone(event.button)

    def test_wheel_x_zero(self):
        event = _event()
        self.assertEqual(0, event.wheel_x)

    def test_wheel_y_zero(self):
        event = _event()
        self.assertEqual(0, event.wheel_y)


# ===========================================================================
# GuiEvent — is_kind
# ===========================================================================


class TestGuiEventIsKind(unittest.TestCase):
    def test_is_kind_match(self):
        event = _event(EventType.QUIT)
        self.assertTrue(event.is_kind(EventType.QUIT))

    def test_is_kind_no_match(self):
        event = _event(EventType.PASS)
        self.assertFalse(event.is_kind(EventType.QUIT))

    def test_is_kind_multiple(self):
        event = _event(EventType.KEY_DOWN)
        self.assertTrue(event.is_kind(EventType.KEY_UP, EventType.KEY_DOWN))


# ===========================================================================
# GuiEvent — is_quit / is_key_down / is_key_up
# ===========================================================================


class TestGuiEventQueryMethods(unittest.TestCase):
    def test_is_quit_true(self):
        event = _event(EventType.QUIT)
        self.assertTrue(event.is_quit())

    def test_is_quit_false(self):
        event = _event(EventType.PASS)
        self.assertFalse(event.is_quit())

    def test_is_key_down_any(self):
        event = _event(EventType.KEY_DOWN, key=65)
        self.assertTrue(event.is_key_down())

    def test_is_key_down_specific(self):
        event = _event(EventType.KEY_DOWN, key=65)
        self.assertTrue(event.is_key_down(65))

    def test_is_key_down_wrong_key(self):
        event = _event(EventType.KEY_DOWN, key=65)
        self.assertFalse(event.is_key_down(66))

    def test_is_key_up(self):
        event = _event(EventType.KEY_UP, key=65)
        self.assertTrue(event.is_key_up(65))

    def test_is_mouse_down_any(self):
        event = _event(EventType.MOUSE_BUTTON_DOWN, button=1)
        self.assertTrue(event.is_mouse_down())

    def test_is_mouse_down_button1(self):
        event = _event(EventType.MOUSE_BUTTON_DOWN, button=1)
        self.assertTrue(event.is_mouse_down(1))

    def test_is_mouse_down_wrong_button(self):
        event = _event(EventType.MOUSE_BUTTON_DOWN, button=3)
        self.assertFalse(event.is_mouse_down(1))

    def test_is_mouse_up(self):
        event = _event(EventType.MOUSE_BUTTON_UP, button=2)
        self.assertTrue(event.is_mouse_up(2))

    def test_is_mouse_motion(self):
        event = _event(EventType.MOUSE_MOTION)
        self.assertTrue(event.is_mouse_motion())

    def test_is_mouse_wheel(self):
        event = _event(EventType.MOUSE_WHEEL)
        self.assertTrue(event.is_mouse_wheel())

    def test_is_left_down_true(self):
        event = _event(EventType.MOUSE_BUTTON_DOWN, button=1)
        self.assertTrue(event.is_left_down())

    def test_is_left_down_false_wrong_button(self):
        event = _event(EventType.MOUSE_BUTTON_DOWN, button=3)
        self.assertFalse(event.is_left_down())

    def test_is_left_up_true(self):
        event = _event(EventType.MOUSE_BUTTON_UP, button=1)
        self.assertTrue(event.is_left_up())


# ===========================================================================
# GuiEvent — stop_propagation / prevent_default
# ===========================================================================


class TestGuiEventMutators(unittest.TestCase):
    def test_stop_propagation(self):
        event = _event()
        event.stop_propagation()
        self.assertTrue(event.propagation_stopped)

    def test_prevent_default(self):
        event = _event()
        event.prevent_default()
        self.assertTrue(event.default_prevented)

    def test_with_phase(self):
        event = _event()
        result = event.with_phase(EventPhase.BUBBLE)
        self.assertIs(EventPhase.BUBBLE, result.phase)
        self.assertIs(event, result)


if __name__ == "__main__":
    unittest.main()
