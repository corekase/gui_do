"""
Unit tests for Canvas widget and CanvasEventPacket.

Tests cover:
- CanvasEventPacket creation and data storage
- Canvas event handling and queueing
- Event blocking when queue is full
- Position calculation relative to canvas
"""

import unittest
from unittest.mock import Mock, MagicMock
from pygame import Rect
from gui.widgets.canvas import Canvas, CanvasEventPacket
from gui.utility.constants import CanvasEvent
from pygame.locals import MOUSEWHEEL, MOUSEMOTION, MOUSEBUTTONDOWN, MOUSEBUTTONUP


class MockGUI:
    """Mock GuiManager for testing."""
    def __init__(self):
        self.bitmap_factory = Mock()
        self.surface = Mock()

    def copy_graphic_area(self, surface, rect):
        """Mock copy_graphic_area."""
        return Mock()

    def set_pristine(self, backdrop, obj):
        """Mock set_pristine."""
        pass

    def convert_to_window(self, pos, window):
        """Mock convert_to_window - simple identity function for testing."""
        return pos

    def get_mouse_pos(self):
        """Mock get_mouse_pos."""
        return (50, 50)


class MockEvent:
    """Mock pygame event."""
    def __init__(self, event_type, y=None, rel=None, button=None):
        self.type = event_type
        self.y = y
        self.rel = rel
        self.button = button


class CanvasEventPacketTests(unittest.TestCase):
    """Tests for CanvasEventPacket class."""

    def test_event_packet_creation(self):
        """CanvasEventPacket should initialize with None values."""
        packet = CanvasEventPacket()

        self.assertIsNone(packet.type)
        self.assertIsNone(packet.pos)
        self.assertIsNone(packet.rel)
        self.assertIsNone(packet.button)
        self.assertIsNone(packet.y)

    def test_event_packet_data_assignment(self):
        """CanvasEventPacket should accept data assignment."""
        packet = CanvasEventPacket()
        packet.type = CanvasEvent.MouseMotion
        packet.pos = (100, 200)
        packet.rel = (10, -5)

        self.assertEqual(packet.type, CanvasEvent.MouseMotion)
        self.assertEqual(packet.pos, (100, 200))
        self.assertEqual(packet.rel, (10, -5))

    def test_event_packet_button_data(self):
        """CanvasEventPacket should store button data."""
        packet = CanvasEventPacket()
        packet.type = CanvasEvent.MouseButtonDown
        packet.button = 1
        packet.pos = (50, 75)

        self.assertEqual(packet.type, CanvasEvent.MouseButtonDown)
        self.assertEqual(packet.button, 1)
        self.assertEqual(packet.pos, (50, 75))


class CanvasEventHandlingTests(unittest.TestCase):
    """Tests for Canvas widget event handling."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_gui = MockGUI()
        self.canvas = Canvas(
            self.mock_gui,
            id='test_canvas',
            rect=Rect(10, 20, 200, 150),
            backdrop=None,
            canvas_callback=None,
            automatic_pristine=False
        )
        self.canvas.window = None
        self.canvas.surface = Mock()

    def test_canvas_initialization(self):
        """Canvas should initialize with no queued event."""
        self.assertFalse(self.canvas.queued_event)
        self.assertIsNone(self.canvas.CEvent)

    def test_mouse_wheel_event_queued(self):
        """MouseWheel event should be queued with correct data."""
        self.canvas.get_collide = Mock(return_value=True)
        event = MockEvent(MOUSEWHEEL, y=1)

        result = self.canvas.handle_event(event, None)

        self.assertTrue(self.canvas.queued_event)
        self.assertIsNotNone(self.canvas.CEvent)
        self.assertEqual(self.canvas.CEvent.type, CanvasEvent.MouseWheel)
        self.assertEqual(self.canvas.CEvent.y, 1)

    def test_mouse_motion_event_queued(self):
        """MouseMotion event should be queued with relative movement."""
        self.canvas.get_collide = Mock(return_value=True)
        event = MockEvent(MOUSEMOTION, rel=(5, -3))

        result = self.canvas.handle_event(event, None)

        self.assertTrue(self.canvas.queued_event)
        self.assertEqual(self.canvas.CEvent.type, CanvasEvent.MouseMotion)
        self.assertEqual(self.canvas.CEvent.rel, (5, -3))

    def test_mouse_button_down_event_queued(self):
        """MouseButtonDown event should be queued with button info."""
        self.canvas.get_collide = Mock(return_value=True)
        event = MockEvent(MOUSEBUTTONDOWN, button=1)

        result = self.canvas.handle_event(event, None)

        self.assertTrue(self.canvas.queued_event)
        self.assertEqual(self.canvas.CEvent.type, CanvasEvent.MouseButtonDown)
        self.assertEqual(self.canvas.CEvent.button, 1)

    def test_mouse_button_up_event_queued(self):
        """MouseButtonUp event should be queued with button info."""
        self.canvas.get_collide = Mock(return_value=True)
        event = MockEvent(MOUSEBUTTONUP, button=3)

        result = self.canvas.handle_event(event, None)

        self.assertTrue(self.canvas.queued_event)
        self.assertEqual(self.canvas.CEvent.type, CanvasEvent.MouseButtonUp)
        self.assertEqual(self.canvas.CEvent.button, 3)

    def test_position_relative_to_canvas(self):
        """Event position should be relative to canvas, not screen."""
        self.canvas.get_collide = Mock(return_value=True)
        self.mock_gui.get_mouse_pos = Mock(return_value=(60, 80))
        event = MockEvent(MOUSEMOTION, rel=(5, 5))

        # Canvas draw_rect is at (10, 20), mouse is at (60, 80)
        # Relative position should be (50, 60)
        result = self.canvas.handle_event(event, None)

        self.assertEqual(self.canvas.CEvent.pos, (50, 60))

    def test_event_blocks_while_queued(self):
        """New events should not be queued while previous event is pending."""
        self.canvas.get_collide = Mock(return_value=True)
        event1 = MockEvent(MOUSEMOTION, rel=(5, 5))
        event2 = MockEvent(MOUSEMOTION, rel=(10, 10))

        # First event gets queued
        result1 = self.canvas.handle_event(event1, None)
        self.assertTrue(self.canvas.queued_event)

        # Second event should be blocked
        result2 = self.canvas.handle_event(event2, None)
        self.assertTrue(self.canvas.queued_event)
        # Event should still have first event's data
        self.assertEqual(self.canvas.CEvent.rel, (5, 5))

    def test_read_event_clears_queue(self):
        """read_event() should clear the queue flag."""
        self.canvas.get_collide = Mock(return_value=True)
        event = MockEvent(MOUSEMOTION, rel=(5, 5))

        self.canvas.handle_event(event, None)
        self.assertTrue(self.canvas.queued_event)

        packet = self.canvas.read_event()
        self.assertFalse(self.canvas.queued_event)
        self.assertIsNotNone(packet)

    def test_read_event_returns_none_without_queue(self):
        """read_event() should return None if no event queued."""
        result = self.canvas.read_event()

        self.assertIsNone(result)

    def test_event_not_queued_outside_canvas(self):
        """Events outside canvas bounds should not be queued."""
        self.canvas.get_collide = Mock(return_value=False)
        event = MockEvent(MOUSEMOTION, rel=(5, 5))

        result = self.canvas.handle_event(event, None)

        self.assertFalse(self.canvas.queued_event)
        self.assertIsNone(self.canvas.CEvent)

    def test_callback_consumed_event(self):
        """Canvas callback should consume event (return False)."""
        callback = Mock()
        self.canvas.canvas_callback = callback
        self.canvas.get_collide = Mock(return_value=True)
        event = MockEvent(MOUSEMOTION, rel=(5, 5))

        result = self.canvas.handle_event(event, None)

        callback.assert_called_once()
        self.assertFalse(result)

    def test_no_callback_signals_event(self):
        """Without callback, canvas should signal event (return True)."""
        self.canvas.canvas_callback = None
        self.canvas.get_collide = Mock(return_value=True)
        event = MockEvent(MOUSEMOTION, rel=(5, 5))

        result = self.canvas.handle_event(event, None)

        self.assertTrue(result)

    def test_focused_method_detects_focus(self):
        """focused() should return True when mouse is over canvas."""
        self.canvas.draw_rect = Rect(10, 20, 200, 150)
        self.mock_gui.convert_to_window = Mock(return_value=(50, 50))
        self.mock_gui.get_mouse_pos = Mock(return_value=(60, 70))

        result = self.canvas.focused()

        # Position (50, 50) is within canvas rect (10, 20, 200, 150)
        self.assertTrue(result)

    def test_focused_method_detects_no_focus(self):
        """focused() should return False when mouse is outside canvas."""
        self.canvas.draw_rect = Rect(10, 20, 200, 150)
        self.mock_gui.convert_to_window = Mock(return_value=(250, 250))
        self.mock_gui.get_mouse_pos = Mock(return_value=(260, 270))

        result = self.canvas.focused()

        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()
