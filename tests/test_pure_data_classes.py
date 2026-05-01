"""Tests for ToastSeverity, NotificationRecord, AnimationTransitionMode, and
TaskScheduler.recommended_worker_count — pure-logic classes with no display deps."""
import unittest

from gui_do.overlays.toast_manager import ToastSeverity
from gui_do.overlays.notification_center import NotificationRecord
from gui_do.scheduling.animation_state_machine import AnimationTransitionMode
from gui_do.scheduling.task_scheduler import TaskScheduler


# ===========================================================================
# ToastSeverity enum
# ===========================================================================


class TestToastSeverity(unittest.TestCase):
    def test_members_exist(self):
        self.assertIn("INFO", ToastSeverity.__members__)
        self.assertIn("SUCCESS", ToastSeverity.__members__)
        self.assertIn("WARNING", ToastSeverity.__members__)
        self.assertIn("ERROR", ToastSeverity.__members__)

    def test_unique_values(self):
        values = [s.value for s in ToastSeverity]
        self.assertEqual(len(values), len(set(values)))


# ===========================================================================
# NotificationRecord dataclass
# ===========================================================================


class TestNotificationRecord(unittest.TestCase):
    def test_message_stored(self):
        r = NotificationRecord(message="Build done")
        self.assertEqual("Build done", r.message)

    def test_defaults(self):
        r = NotificationRecord(message="hi")
        self.assertEqual("", r.title)
        self.assertEqual(ToastSeverity.INFO, r.severity)
        self.assertEqual("", r.topic)
        self.assertFalse(r.read)
        self.assertIsNone(r.data)

    def test_timestamp_is_string(self):
        r = NotificationRecord(message="test")
        self.assertIsInstance(r.timestamp, str)
        self.assertGreater(len(r.timestamp), 0)

    def test_custom_fields(self):
        r = NotificationRecord(
            message="error",
            title="Error",
            severity=ToastSeverity.ERROR,
            topic="build.failed",
            read=True,
            data={"code": 42},
        )
        self.assertEqual("Error", r.title)
        self.assertEqual(ToastSeverity.ERROR, r.severity)
        self.assertEqual("build.failed", r.topic)
        self.assertTrue(r.read)
        self.assertEqual({"code": 42}, r.data)

    def test_read_is_mutable(self):
        r = NotificationRecord(message="m")
        r.read = True
        self.assertTrue(r.read)


# ===========================================================================
# AnimationTransitionMode enum
# ===========================================================================


class TestAnimationTransitionMode(unittest.TestCase):
    def test_interrupt_value(self):
        self.assertEqual("interrupt", AnimationTransitionMode.INTERRUPT.value)

    def test_complete_then_transition_value(self):
        self.assertEqual("complete_then_transition", AnimationTransitionMode.COMPLETE_THEN_TRANSITION.value)

    def test_reverse_then_transition_value(self):
        self.assertEqual("reverse_then_transition", AnimationTransitionMode.REVERSE_THEN_TRANSITION.value)

    def test_three_members(self):
        self.assertEqual(3, len(list(AnimationTransitionMode)))


# ===========================================================================
# TaskScheduler.recommended_worker_count (static)
# ===========================================================================


class TestTaskSchedulerRecommendedWorkerCount(unittest.TestCase):
    def test_returns_positive_int(self):
        count = TaskScheduler.recommended_worker_count()
        self.assertIsInstance(count, int)
        self.assertGreater(count, 0)

    def test_respects_cap(self):
        count = TaskScheduler.recommended_worker_count(logical_cpus=32, cap=4)
        self.assertLessEqual(count, 4)

    def test_respects_reserve_for_ui(self):
        count1 = TaskScheduler.recommended_worker_count(logical_cpus=4, reserve_for_ui=0)
        count2 = TaskScheduler.recommended_worker_count(logical_cpus=4, reserve_for_ui=2)
        self.assertGreaterEqual(count1, count2)

    def test_minimum_one(self):
        count = TaskScheduler.recommended_worker_count(logical_cpus=1, reserve_for_ui=10, cap=1)
        self.assertGreaterEqual(count, 1)

    def test_custom_logical_cpus(self):
        count = TaskScheduler.recommended_worker_count(logical_cpus=8, reserve_for_ui=1, cap=10)
        self.assertGreater(count, 0)


if __name__ == "__main__":
    unittest.main()
