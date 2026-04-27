"""Tests for ToastManager (Feature 9)."""
import unittest
from unittest.mock import MagicMock

from pygame import Rect

from gui_do.core.toast_manager import ToastManager, ToastHandle, ToastSeverity


def _mgr(**kwargs) -> ToastManager:
    return ToastManager(Rect(0, 0, 800, 600), **kwargs)


class TestShowReturnsHandle(unittest.TestCase):
    def test_show_returns_handle(self) -> None:
        mgr = _mgr()
        handle = mgr.show("Hello")
        self.assertIsInstance(handle, ToastHandle)
        self.assertTrue(handle.is_visible)


class TestVisibleCountIncrementsOnShow(unittest.TestCase):
    def test_visible_count_increments(self) -> None:
        mgr = _mgr()
        mgr.show("A")
        mgr.show("B")
        self.assertEqual(mgr.visible_count, 2)


class TestDismissRemovesToast(unittest.TestCase):
    def test_dismiss_removes_toast(self) -> None:
        mgr = _mgr()
        handle = mgr.show("Hi")
        handle.dismiss()
        self.assertFalse(handle.is_visible)
        self.assertEqual(mgr.visible_count, 0)


class TestDismissAllClearsAll(unittest.TestCase):
    def test_dismiss_all_clears_all(self) -> None:
        mgr = _mgr()
        mgr.show("A")
        mgr.show("B")
        count = mgr.dismiss_all()
        self.assertEqual(count, 2)
        self.assertEqual(mgr.visible_count, 0)


class TestPersistentToastNotExpired(unittest.TestCase):
    def test_persistent_toast_not_expired_after_update(self) -> None:
        mgr = _mgr()
        handle = mgr.show_persistent("Keep me")
        mgr.update(100.0)
        self.assertTrue(handle.is_visible)


class TestToastExpiresAfterDuration(unittest.TestCase):
    def test_toast_expires_after_duration(self) -> None:
        mgr = _mgr(default_duration_seconds=2.0)
        handle = mgr.show("Bye")
        mgr.update(2.1)
        self.assertFalse(handle.is_visible)


class TestToastStillVisibleBeforeDuration(unittest.TestCase):
    def test_toast_still_visible_before_duration(self) -> None:
        mgr = _mgr(default_duration_seconds=2.0)
        handle = mgr.show("Stay")
        mgr.update(1.0)
        self.assertTrue(handle.is_visible)


class TestMaxVisibleTrimsOldest(unittest.TestCase):
    def test_max_visible_trims_oldest(self) -> None:
        mgr = _mgr(max_visible=3)
        for i in range(5):
            mgr.show(f"Toast {i}")
        self.assertEqual(mgr.visible_count, 3)


class TestSeverityInfo(unittest.TestCase):
    def test_severity_info(self) -> None:
        mgr = _mgr()
        handle = mgr.show("Info", severity=ToastSeverity.INFO)
        self.assertTrue(handle.is_visible)


class TestSeverityError(unittest.TestCase):
    def test_severity_error(self) -> None:
        mgr = _mgr()
        handle = mgr.show("Error!", severity=ToastSeverity.ERROR)
        self.assertTrue(handle.is_visible)


class TestEventBusMessageTriggersToast(unittest.TestCase):
    def test_event_bus_message_triggers_toast(self) -> None:
        mgr = _mgr()
        mgr.on_event_bus_message({"message": "From bus", "severity": "WARNING"})
        self.assertEqual(mgr.visible_count, 1)


class TestEventBusMessageIgnoresNonDict(unittest.TestCase):
    def test_event_bus_message_ignores_non_dict(self) -> None:
        mgr = _mgr()
        mgr.on_event_bus_message("not a dict")
        self.assertEqual(mgr.visible_count, 0)


if __name__ == "__main__":
    unittest.main()
