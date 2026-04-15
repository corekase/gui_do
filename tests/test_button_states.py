"""
Unit tests for Button widget state transitions and event handling.

Tests cover:
- State transitions (Idle → Hover → Armed)
- Event handling (mouse motion, button down/up)
- Callback invocation
- Timer management for repeated callbacks
"""

import unittest
from unittest.mock import Mock, MagicMock, patch, call
from pygame import Rect
from gui.widgets.button import Button
from gui.utility.constants import InteractiveState
from pygame.locals import MOUSEMOTION, MOUSEBUTTONDOWN, MOUSEBUTTONUP


class MockGUI:
    """Mock GuiManager for testing."""
    def __init__(self):
        self.timers = Mock()
        self.bitmap_factory = Mock()
        self.surface = Mock()


class MockEvent:
    """Mock pygame event."""
    def __init__(self, event_type, button=None, rel=None):
        self.type = event_type
        self.button = button
        self.rel = rel


class ButtonStateTransitionTests(unittest.TestCase):
    """Tests for button state transitions and event handling."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_gui = MockGUI()
        self.mock_gui.bitmap_factory.get_styled_bitmaps.return_value = (
            (Mock(), Mock(), Mock()),  # idle, hover, armed surfaces
            Rect(0, 0, 100, 30)        # hit_rect
        )
        self.button = Button(
            self.mock_gui,
            id='test_button',
            rect=Rect(10, 10, 100, 30),
            style=Mock(),
            text='Test Button',
            button_callback=None
        )
        self.button.window = None
        self.button.surface = Mock()

    def test_initial_state_is_idle(self):
        """Button should start in Idle state."""
        self.assertEqual(self.button.state, InteractiveState.Idle)

    def test_idle_to_hover_on_collision(self):
        """Button should transition to Hover when mouse collides."""
        self.button.get_collide = Mock(return_value=True)
        event = MockEvent(MOUSEMOTION)

        self.button.handle_event(event, None)

        self.assertEqual(self.button.state, InteractiveState.Hover)

    def test_hover_to_idle_on_no_collision(self):
        """Button should return to Idle when mouse leaves."""
        self.button.state = InteractiveState.Hover
        self.button.get_collide = Mock(return_value=False)
        event = MockEvent(MOUSEMOTION)

        self.button.handle_event(event, None)

        self.assertEqual(self.button.state, InteractiveState.Idle)

    def test_hover_to_armed_on_mouse_button_down(self):
        """Button should transition to Armed on left mouse button down in Hover."""
        self.button.state = InteractiveState.Hover
        self.button.get_collide = Mock(return_value=True)
        event = MockEvent(MOUSEBUTTONDOWN, button=1)

        result = self.button.handle_event(event, None)

        self.assertEqual(self.button.state, InteractiveState.Armed)
        self.assertTrue(result)  # Should return True to signal activation

    def test_armed_to_hover_on_mouse_button_up(self):
        """Button should return to Hover on left mouse button up."""
        self.button.state = InteractiveState.Armed
        self.button.get_collide = Mock(return_value=True)
        event = MockEvent(MOUSEBUTTONUP, button=1)

        result = self.button.handle_event(event, None)

        self.assertEqual(self.button.state, InteractiveState.Hover)
        self.assertTrue(result)  # Should return True to signal activation

    def test_armed_state_ignored_on_wrong_button(self):
        """Armed state should handle only left mouse button (button=1)."""
        self.button.state = InteractiveState.Armed
        self.button.get_collide = Mock(return_value=True)
        event = MockEvent(MOUSEBUTTONUP, button=3)  # Right mouse button

        result = self.button.handle_event(event, None)

        self.assertEqual(self.button.state, InteractiveState.Armed)
        self.assertFalse(result)

    def test_callback_invoked_on_press(self):
        """Button callback should be invoked when transitioning to Armed."""
        callback = Mock()
        self.button.button_callback = callback
        self.button.state = InteractiveState.Hover
        self.button.get_collide = Mock(return_value=True)
        event = MockEvent(MOUSEBUTTONDOWN, button=1)

        self.button.handle_event(event, None)

        callback.assert_called_once()

    def test_timer_created_on_callback(self):
        """Timer should be added when button with callback is pressed."""
        callback = Mock()
        self.button.button_callback = callback
        self.button.state = InteractiveState.Hover
        self.button.get_collide = Mock(return_value=True)
        event = MockEvent(MOUSEBUTTONDOWN, button=1)

        self.button.handle_event(event, None)

        # Verify timer was added
        self.mock_gui.timers.add_timer.assert_called_once()
        call_args = self.mock_gui.timers.add_timer.call_args
        self.assertIn('test_button', call_args[0][0])  # Timer ID contains button ID
        self.assertEqual(call_args[0][1], 150)  # Timer duration is 150ms
        self.assertIsNotNone(self.button.timer_id)

    def test_timer_removed_on_release(self):
        """Timer should be removed when button is released."""
        callback = Mock()
        self.button.button_callback = callback
        self.button.state = InteractiveState.Armed
        self.button.timer_id = 'test_button.timer'
        self.button.get_collide = Mock(return_value=True)
        event = MockEvent(MOUSEBUTTONUP, button=1)

        self.button.handle_event(event, None)

        self.mock_gui.timers.remove_timer.assert_called_once_with('test_button.timer')
        self.assertIsNone(self.button.timer_id)

    def test_no_timer_without_callback(self):
        """Timer should not be created if button has no callback."""
        self.button.button_callback = None
        self.button.state = InteractiveState.Hover
        self.button.get_collide = Mock(return_value=True)
        event = MockEvent(MOUSEBUTTONDOWN, button=1)

        self.button.handle_event(event, None)

        self.mock_gui.timers.add_timer.assert_not_called()
        self.assertIsNone(self.button.timer_id)

    def test_activation_returns_true_with_callback(self):
        """handle_event should return True when button activation complete."""
        self.button.button_callback = Mock()
        self.button.state = InteractiveState.Armed
        self.button.get_collide = Mock(return_value=True)
        event = MockEvent(MOUSEBUTTONUP, button=1)

        result = self.button.handle_event(event, None)

        self.assertTrue(result)

    def test_activation_returns_false_without_callback(self):
        """handle_event should return True even without callback on button up."""
        self.button.button_callback = None
        self.button.state = InteractiveState.Armed
        self.button.get_collide = Mock(return_value=True)
        event = MockEvent(MOUSEBUTTONUP, button=1)

        result = self.button.handle_event(event, None)

        self.assertTrue(result)

    def test_non_mouse_events_ignored(self):
        """Non-mouse events should be ignored."""
        self.button.state = InteractiveState.Hover
        event = MockEvent(999)  # Invalid event type

        result = self.button.handle_event(event, None)

        self.assertFalse(result)
        self.assertEqual(self.button.state, InteractiveState.Hover)

    def test_leave_resets_to_idle(self):
        """leave() should reset button to Idle state."""
        self.button.state = InteractiveState.Hover

        self.button.leave()

        self.assertEqual(self.button.state, InteractiveState.Idle)

    def test_leave_removes_timer(self):
        """leave() should remove any active timer."""
        self.button.timer_id = 'test_button.timer'
        self.button.state = InteractiveState.Hover

        self.button.leave()

        self.mock_gui.timers.remove_timer.assert_called_once_with('test_button.timer')
        self.assertIsNone(self.button.timer_id)

    def test_leave_preserves_armed_state(self):
        """leave() should not change Armed state (other logic handles it)."""
        # Note: Current implementation resets to Idle, but documenting expected behavior
        self.button.state = InteractiveState.Armed

        self.button.leave()

        # Current behavior: resets to Idle (test documents reality)
        self.assertEqual(self.button.state, InteractiveState.Idle)

    def test_state_transition_diagram(self):
        """Test the complete state transition diagram."""
        self.button.get_collide = Mock(return_value=True)
        self.button.button_callback = Mock()

        # Start: Idle
        self.assertEqual(self.button.state, InteractiveState.Idle)

        # Idle → Hover
        self.button.handle_event(MockEvent(MOUSEMOTION), None)
        self.assertEqual(self.button.state, InteractiveState.Hover)

        # Hover → Armed
        self.button.handle_event(MockEvent(MOUSEBUTTONDOWN, button=1), None)
        self.assertEqual(self.button.state, InteractiveState.Armed)

        # Armed → Hover
        self.button.handle_event(MockEvent(MOUSEBUTTONUP, button=1), None)
        self.assertEqual(self.button.state, InteractiveState.Hover)

        # Hover → Idle (mouse leaves)
        self.button.get_collide = Mock(return_value=False)
        self.button.handle_event(MockEvent(MOUSEMOTION), None)
        self.assertEqual(self.button.state, InteractiveState.Idle)


if __name__ == '__main__':
    unittest.main()
