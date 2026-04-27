"""Tests for NotificationCenter and NotificationRecord."""
import unittest
from unittest.mock import MagicMock, call

from gui_do.core.notification_center import (
    NotificationCenter,
    NotificationRecord,
)
from gui_do.core.toast_manager import ToastSeverity


def _make_event_bus() -> MagicMock:
    bus = MagicMock()
    bus.subscribe = MagicMock()
    bus.unsubscribe = MagicMock()
    return bus


class TestNotificationRecord(unittest.TestCase):

    def test_default_read_state(self):
        rec = NotificationRecord(message="hello")
        self.assertFalse(rec.read)

    def test_severity_default_info(self):
        rec = NotificationRecord(message="hello")
        self.assertIs(rec.severity, ToastSeverity.INFO)

    def test_timestamp_populated(self):
        rec = NotificationRecord(message="hello")
        self.assertIsInstance(rec.timestamp, str)
        self.assertTrue(len(rec.timestamp) > 0)


class TestNotificationCenterAdd(unittest.TestCase):

    def _make_center(self, max_records=50):
        bus = _make_event_bus()
        center = NotificationCenter(bus, max_records=max_records)
        return center, bus

    def test_add_increments_unread_count(self):
        center, _ = self._make_center()
        center.add(NotificationRecord("a"))
        center.add(NotificationRecord("b"))
        self.assertEqual(center.unread_count.value, 2)

    def test_add_appends_to_records(self):
        center, _ = self._make_center()
        rec = NotificationRecord("hello")
        center.add(rec)
        self.assertIn(rec, center.all_records)

    def test_max_records_caps_list(self):
        center, _ = self._make_center(max_records=3)
        for i in range(5):
            center.add(NotificationRecord(f"msg {i}"))
        self.assertLessEqual(len(center.all_records), 3)

    def test_max_records_keeps_newest(self):
        center, _ = self._make_center(max_records=3)
        for i in range(5):
            center.add(NotificationRecord(f"msg {i}"))
        messages = [r.message for r in center.all_records]
        self.assertIn("msg 4", messages)
        self.assertNotIn("msg 0", messages)


class TestNotificationCenterMarkRead(unittest.TestCase):

    def _make_center(self):
        return NotificationCenter(_make_event_bus())

    def test_mark_read_decrements_unread_count(self):
        center = self._make_center()
        rec1 = NotificationRecord("a")
        rec2 = NotificationRecord("b")
        center.add(rec1)
        center.add(rec2)
        center.mark_read(rec1)
        self.assertEqual(center.unread_count.value, 1)
        self.assertTrue(rec1.read)

    def test_mark_all_read_zeros_unread_count(self):
        center = self._make_center()
        center.add(NotificationRecord("a"))
        center.add(NotificationRecord("b"))
        center.add(NotificationRecord("c"))
        center.mark_all_read()
        self.assertEqual(center.unread_count.value, 0)
        for r in center.all_records:
            self.assertTrue(r.read)

    def test_mark_read_already_read_is_idempotent(self):
        center = self._make_center()
        rec = NotificationRecord("a")
        center.add(rec)
        center.mark_read(rec)
        center.mark_read(rec)  # second call should not go below 0
        self.assertEqual(center.unread_count.value, 0)

    def test_clear_empties_records_and_resets_count(self):
        center = self._make_center()
        center.add(NotificationRecord("a"))
        center.add(NotificationRecord("b"))
        center.clear()
        self.assertEqual(center.all_records, [])
        self.assertEqual(center.unread_count.value, 0)


class TestNotificationCenterSubscribe(unittest.TestCase):

    def test_subscribe_registers_on_bus(self):
        bus = _make_event_bus()
        center = NotificationCenter(bus)
        center.subscribe("app.error", severity=ToastSeverity.ERROR, title="Error")
        bus.subscribe.assert_called_once()

    def test_subscribe_topic_and_severity_stored(self):
        bus = _make_event_bus()
        center = NotificationCenter(bus)
        center.subscribe("app.warn", severity=ToastSeverity.WARNING, title="Warn")
        # Verify internal severity_map stores the subscription
        self.assertIn("app.warn", center._severity_map)
        self.assertIs(center._severity_map["app.warn"], ToastSeverity.WARNING)

    def test_on_bus_message_dict_payload(self):
        bus = _make_event_bus()
        center = NotificationCenter(bus)
        center.subscribe("app.info", severity=ToastSeverity.INFO, title="Info")
        # Simulate the bus handler being called with a dict payload
        handler = bus.subscribe.call_args[0][1]
        handler({"message": "disk full"})
        self.assertEqual(len(center.all_records), 1)
        self.assertEqual(center.all_records[0].message, "disk full")
        self.assertIs(center.all_records[0].severity, ToastSeverity.INFO)

    def test_on_bus_message_string_payload(self):
        bus = _make_event_bus()
        center = NotificationCenter(bus)
        center.subscribe("app.info", severity=ToastSeverity.INFO, title="Info")
        handler = bus.subscribe.call_args[0][1]
        handler("simple message")
        self.assertEqual(center.all_records[0].message, "simple message")

    def test_unsubscribe_all_clears_severity_map(self):
        bus = _make_event_bus()
        center = NotificationCenter(bus)
        center.subscribe("a", severity=ToastSeverity.INFO, title="A")
        center.subscribe("b", severity=ToastSeverity.WARNING, title="B")
        center.unsubscribe_all()
        self.assertEqual(center._severity_map, {})

    def test_records_observable_fires_on_add(self):
        center = NotificationCenter(_make_event_bus())
        fired = []
        center.records.subscribe(lambda v: fired.append(len(v)))
        center.add(NotificationRecord("x"))
        self.assertTrue(len(fired) > 0)

    def test_unread_count_observable_fires_on_add(self):
        center = NotificationCenter(_make_event_bus())
        counts = []
        center.unread_count.subscribe(lambda v: counts.append(v))
        center.add(NotificationRecord("x"))
        self.assertIn(1, counts)


if __name__ == "__main__":
    unittest.main()
