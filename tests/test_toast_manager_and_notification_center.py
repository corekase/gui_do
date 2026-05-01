"""Tests for ToastManager and NotificationCenter.

Both modules are tested for state-management logic only; draw() is not called
so no pygame display is required.
"""
import unittest

import pygame

from gui_do.overlays.toast_manager import ToastManager, ToastHandle, ToastSeverity
from gui_do.overlays.notification_center import NotificationCenter, NotificationRecord


# ---------------------------------------------------------------------------
# pygame minimal init — needed for pygame.Rect
# ---------------------------------------------------------------------------
pygame.init()
_SCREEN = pygame.Rect(0, 0, 1280, 720)


# ===========================================================================
# ToastManager
# ===========================================================================


class TestToastManagerInitialState(unittest.TestCase):
    def setUp(self):
        self.mgr = ToastManager(_SCREEN)

    def test_visible_count_zero_initially(self):
        self.assertEqual(0, self.mgr.visible_count)

    def test_dismiss_all_on_empty_returns_zero(self):
        self.assertEqual(0, self.mgr.dismiss_all())


class TestToastManagerShow(unittest.TestCase):
    def setUp(self):
        self.mgr = ToastManager(_SCREEN)

    def test_show_returns_handle(self):
        h = self.mgr.show("hello")
        self.assertIsInstance(h, ToastHandle)

    def test_show_increments_visible_count(self):
        self.mgr.show("one")
        self.assertEqual(1, self.mgr.visible_count)

    def test_show_handle_is_visible(self):
        h = self.mgr.show("msg")
        self.assertTrue(h.is_visible)

    def test_show_multiple(self):
        self.mgr.show("a")
        self.mgr.show("b")
        self.mgr.show("c")
        self.assertEqual(3, self.mgr.visible_count)

    def test_max_visible_respected(self):
        mgr = ToastManager(_SCREEN, max_visible=2)
        mgr.show("a")
        mgr.show("b")
        mgr.show("c")   # oldest dropped
        self.assertEqual(2, mgr.visible_count)

    def test_show_severity_default_info(self):
        # Just verify no exception and default works
        h = self.mgr.show("info msg")
        self.assertTrue(h.is_visible)

    def test_show_custom_severity(self):
        h = self.mgr.show("error!", severity=ToastSeverity.ERROR)
        self.assertTrue(h.is_visible)

    def test_show_persistent_returns_handle(self):
        h = self.mgr.show_persistent("stay here")
        self.assertIsInstance(h, ToastHandle)
        self.assertTrue(h.is_visible)


class TestToastManagerDismiss(unittest.TestCase):
    def setUp(self):
        self.mgr = ToastManager(_SCREEN)

    def test_dismiss_removes_toast(self):
        h = self.mgr.show("bye")
        h.dismiss()
        self.assertFalse(h.is_visible)
        self.assertEqual(0, self.mgr.visible_count)

    def test_dismiss_all(self):
        self.mgr.show("one")
        self.mgr.show("two")
        count = self.mgr.dismiss_all()
        self.assertEqual(2, count)
        self.assertEqual(0, self.mgr.visible_count)

    def test_dismiss_one_leaves_others(self):
        h1 = self.mgr.show("keep")
        h2 = self.mgr.show("drop")
        h2.dismiss()
        self.assertTrue(h1.is_visible)
        self.assertFalse(h2.is_visible)
        self.assertEqual(1, self.mgr.visible_count)

    def test_dismiss_already_gone_no_error(self):
        h = self.mgr.show("msg")
        h.dismiss()
        h.dismiss()   # second dismiss should not raise


class TestToastManagerUpdate(unittest.TestCase):
    def setUp(self):
        self.mgr = ToastManager(_SCREEN, default_duration_seconds=1.0)

    def test_update_removes_expired_toast(self):
        self.mgr.show("transient", duration_seconds=0.5)
        self.mgr.update(0.6)
        self.assertEqual(0, self.mgr.visible_count)

    def test_update_keeps_unexpired_toast(self):
        self.mgr.show("alive", duration_seconds=2.0)
        self.mgr.update(0.5)
        self.assertEqual(1, self.mgr.visible_count)

    def test_persistent_toast_not_expired_by_update(self):
        self.mgr.show_persistent("persistent")
        self.mgr.update(999.0)
        self.assertEqual(1, self.mgr.visible_count)

    def test_update_expires_only_old_toasts(self):
        self.mgr.show("short", duration_seconds=0.5)
        self.mgr.show("long", duration_seconds=5.0)
        self.mgr.update(1.0)
        self.assertEqual(1, self.mgr.visible_count)


class TestToastManagerEventBusMessage(unittest.TestCase):
    def setUp(self):
        self.mgr = ToastManager(_SCREEN)

    def test_dict_payload_shows_toast(self):
        self.mgr.on_event_bus_message({"message": "from bus"})
        self.assertEqual(1, self.mgr.visible_count)

    def test_non_dict_payload_ignored(self):
        self.mgr.on_event_bus_message("plain string")
        # no assertion — should not raise; toast may or may not be added
        # but the important thing is no exception

    def test_empty_dict_no_error(self):
        self.mgr.on_event_bus_message({})


# ===========================================================================
# NotificationCenter
# ===========================================================================


class TestNotificationCenterInitialState(unittest.TestCase):
    def setUp(self):
        self.nc = NotificationCenter()

    def test_unread_count_zero_initially(self):
        self.assertEqual(0, self.nc.unread_count.value)

    def test_records_empty_initially(self):
        self.assertEqual([], self.nc.records.value)

    def test_all_records_empty(self):
        self.assertEqual([], self.nc.all_records)


class TestNotificationCenterAdd(unittest.TestCase):
    def setUp(self):
        self.nc = NotificationCenter()

    def test_add_record_appears_in_all_records(self):
        r = NotificationRecord("test message")
        self.nc.add(r)
        self.assertIn(r, self.nc.all_records)

    def test_add_increments_unread_count(self):
        self.nc.add(NotificationRecord("msg"))
        self.assertEqual(1, self.nc.unread_count.value)

    def test_add_updates_records_observable(self):
        self.nc.add(NotificationRecord("msg"))
        self.assertEqual(1, len(self.nc.records.value))

    def test_add_most_recent_first(self):
        r1 = NotificationRecord("first")
        r2 = NotificationRecord("second")
        self.nc.add(r1)
        self.nc.add(r2)
        self.assertIs(r2, self.nc.all_records[0])

    def test_add_respects_max_records(self):
        nc = NotificationCenter(max_records=3)
        for i in range(5):
            nc.add(NotificationRecord(f"msg {i}"))
        self.assertEqual(3, len(nc.all_records))

    def test_add_fires_subscriber_on_records(self):
        events = []
        self.nc.records.subscribe(events.append)
        self.nc.add(NotificationRecord("ping"))
        self.assertEqual(1, len(events))

    def test_add_fires_subscriber_on_unread_count(self):
        events = []
        self.nc.unread_count.subscribe(events.append)
        self.nc.add(NotificationRecord("ping"))
        self.assertEqual(1, len(events))


class TestNotificationCenterMarkRead(unittest.TestCase):
    def setUp(self):
        self.nc = NotificationCenter()

    def test_mark_read_decrements_unread(self):
        r = NotificationRecord("msg")
        self.nc.add(r)
        self.nc.mark_read(r)
        self.assertEqual(0, self.nc.unread_count.value)

    def test_mark_all_read(self):
        self.nc.add(NotificationRecord("a"))
        self.nc.add(NotificationRecord("b"))
        self.nc.mark_all_read()
        self.assertEqual(0, self.nc.unread_count.value)

    def test_mark_read_sets_flag(self):
        r = NotificationRecord("msg")
        self.nc.add(r)
        self.nc.mark_read(r)
        self.assertTrue(r.read)

    def test_mark_read_twice_no_error(self):
        r = NotificationRecord("msg")
        self.nc.add(r)
        self.nc.mark_read(r)
        self.nc.mark_read(r)   # idempotent

    def test_mark_all_read_sets_all_flags(self):
        r1, r2 = NotificationRecord("a"), NotificationRecord("b")
        self.nc.add(r1)
        self.nc.add(r2)
        self.nc.mark_all_read()
        self.assertTrue(r1.read)
        self.assertTrue(r2.read)


class TestNotificationCenterClear(unittest.TestCase):
    def setUp(self):
        self.nc = NotificationCenter()

    def test_clear_removes_all_records(self):
        self.nc.add(NotificationRecord("x"))
        self.nc.add(NotificationRecord("y"))
        self.nc.clear()
        self.assertEqual([], self.nc.all_records)

    def test_clear_resets_unread_count(self):
        self.nc.add(NotificationRecord("x"))
        self.nc.clear()
        self.assertEqual(0, self.nc.unread_count.value)

    def test_clear_resets_records_observable(self):
        self.nc.add(NotificationRecord("x"))
        self.nc.clear()
        self.assertEqual([], self.nc.records.value)


class TestNotificationCenterSubscribe(unittest.TestCase):
    """Subscribe without a real EventBus — verifies graceful no-op."""

    def test_subscribe_without_event_bus_no_error(self):
        nc = NotificationCenter(event_bus=None)
        nc.subscribe("topic.x")   # should not raise

    def test_unsubscribe_all_no_error(self):
        nc = NotificationCenter()
        nc.subscribe("a")
        nc.unsubscribe_all()   # should not raise


class TestNotificationCenterBusIntegration(unittest.TestCase):
    """Use a real EventBus to verify subscribe + delivery."""

    def setUp(self):
        from gui_do.events.event_bus import EventBus
        self.bus = EventBus()
        self.nc = NotificationCenter(self.bus)

    def test_message_creates_record(self):
        self.nc.subscribe("build.done")
        self.bus.publish("build.done", "Build finished")
        self.assertEqual(1, len(self.nc.all_records))

    def test_message_uses_subscribed_severity(self):
        self.nc.subscribe("build.error", severity=ToastSeverity.ERROR)
        self.bus.publish("build.error", "oops")
        self.assertEqual(ToastSeverity.ERROR, self.nc.all_records[0].severity)

    def test_dict_payload_extracts_message(self):
        self.nc.subscribe("info")
        self.bus.publish("info", {"message": "hello"})
        self.assertEqual("hello", self.nc.all_records[0].message)

    def test_dict_payload_can_override_severity(self):
        self.nc.subscribe("ev", severity=ToastSeverity.INFO)
        self.bus.publish("ev", {"message": "warn", "severity": "WARNING"})
        self.assertEqual(ToastSeverity.WARNING, self.nc.all_records[0].severity)

    def test_record_topic_set_correctly(self):
        self.nc.subscribe("build.done")
        self.bus.publish("build.done", "ok")
        self.assertEqual("build.done", self.nc.all_records[0].topic)

    def test_unsubscribed_topic_ignored(self):
        self.bus.publish("unmonitored", "data")
        self.assertEqual(0, len(self.nc.all_records))


if __name__ == "__main__":
    unittest.main()
