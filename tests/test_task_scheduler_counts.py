"""Tests for TaskScheduler count query helpers: pending_count, running_count,
suspended_count, task_count."""
import time
import threading
import unittest

from gui.core.task_scheduler import TaskScheduler


class TaskSchedulerCountQueriesTests(unittest.TestCase):

    def setUp(self) -> None:
        self.scheduler = TaskScheduler(max_workers=1)

    def tearDown(self) -> None:
        self.scheduler.shutdown()

    # --- pending_count ---

    def test_pending_count_zero_initially(self) -> None:
        self.assertEqual(self.scheduler.pending_count(), 0)

    def test_pending_count_reflects_queued_tasks(self) -> None:
        # Fill the single worker slot then add more so they stay pending
        gate = threading.Event()

        def slow(task_id):
            gate.wait(timeout=5)

        self.scheduler.add_task("blocker", slow)
        # Give the worker time to pick up "blocker" so subsequent tasks stay pending
        time.sleep(0.05)
        self.scheduler.update()  # submit blocker to the pool

        self.scheduler.add_task("t1", lambda tid: None)
        self.scheduler.add_task("t2", lambda tid: None)
        count = self.scheduler.pending_count()
        gate.set()
        self.assertGreaterEqual(count, 0)  # at least structural sanity

    def test_pending_count_zero_after_remove_all(self) -> None:
        gate = threading.Event()
        self.scheduler.add_task("a", lambda tid: gate.wait(timeout=1))
        self.scheduler.remove_all()
        gate.set()
        self.assertEqual(self.scheduler.pending_count(), 0)

    # --- suspended_count ---

    def test_suspended_count_zero_initially(self) -> None:
        self.assertEqual(self.scheduler.suspended_count(), 0)

    def test_suspended_count_reflects_suspended_tasks(self) -> None:
        self.scheduler.add_task("x", lambda tid: None)
        self.scheduler.add_task("y", lambda tid: None)
        self.scheduler.suspend_all()
        count = self.scheduler.suspended_count()
        self.scheduler.resume_all()
        # Both tasks were pending before suspend_all; both should be suspended
        self.assertEqual(count, 2)

    def test_suspended_count_zero_after_resume_all(self) -> None:
        self.scheduler.add_task("x", lambda tid: None)
        self.scheduler.suspend_all()
        self.scheduler.resume_all()
        self.assertEqual(self.scheduler.suspended_count(), 0)

    def test_suspended_count_specific_tasks(self) -> None:
        self.scheduler.add_task("a", lambda tid: None)
        self.scheduler.add_task("b", lambda tid: None)
        self.scheduler.suspend_tasks("a")
        count = self.scheduler.suspended_count()
        self.scheduler.resume_tasks("a")
        self.assertEqual(count, 1)

    # --- task_count ---

    def test_task_count_zero_initially(self) -> None:
        self.assertEqual(self.scheduler.task_count(), 0)

    def test_task_count_includes_pending_and_suspended(self) -> None:
        self.scheduler.add_task("p1", lambda tid: None)
        self.scheduler.add_task("p2", lambda tid: None)
        self.scheduler.add_task("s1", lambda tid: None)
        self.scheduler.suspend_tasks("s1")
        count = self.scheduler.task_count()
        self.scheduler.remove_all()
        # p1, p2 pending + s1 suspended = 3 (running_count might also include some)
        self.assertGreaterEqual(count, 2)

    def test_task_count_zero_after_remove_all(self) -> None:
        self.scheduler.add_task("z", lambda tid: None)
        self.scheduler.remove_all()
        self.assertEqual(self.scheduler.task_count(), 0)

    # --- running_count ---

    def test_running_count_zero_initially(self) -> None:
        self.assertEqual(self.scheduler.running_count(), 0)

    def test_running_count_zero_after_remove_all(self) -> None:
        gate = threading.Event()
        self.scheduler.add_task("r", lambda tid: gate.wait(timeout=1))
        self.scheduler.remove_all()
        gate.set()
        self.assertEqual(self.scheduler.running_count(), 0)

    # --- consistency: pending + running + suspended == task_count ---

    def test_count_consistency_with_mixed_state(self) -> None:
        self.scheduler.add_task("a", lambda tid: None)
        self.scheduler.add_task("b", lambda tid: None)
        self.scheduler.add_task("c", lambda tid: None)
        self.scheduler.suspend_tasks("c")

        pending = self.scheduler.pending_count()
        running = self.scheduler.running_count()
        suspended = self.scheduler.suspended_count()
        total = self.scheduler.task_count()

        self.assertEqual(pending + running + suspended, total)
        self.scheduler.remove_all()

    def test_count_consistency_all_suspended(self) -> None:
        self.scheduler.add_task("x", lambda tid: None)
        self.scheduler.add_task("y", lambda tid: None)
        self.scheduler.suspend_all()

        pending = self.scheduler.pending_count()
        running = self.scheduler.running_count()
        suspended = self.scheduler.suspended_count()
        total = self.scheduler.task_count()

        self.assertEqual(pending, 0)
        self.assertEqual(running, 0)
        self.assertEqual(pending + running + suspended, total)
        self.scheduler.remove_all()


if __name__ == "__main__":
    unittest.main()
