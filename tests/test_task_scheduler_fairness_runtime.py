import threading
import time
import unittest

from gui_do.core.task_scheduler import TaskScheduler


class TaskSchedulerFairnessRuntimeTests(unittest.TestCase):
    def tearDown(self) -> None:
        # Individual tests own scheduler shutdown where they need explicit cleanup.
        pass

    def test_dispatch_time_budget_limits_per_update_work(self) -> None:
        scheduler = TaskScheduler(max_workers=1)
        gate = threading.Event()
        delivered = []

        def logic(_task_id):
            gate.wait(timeout=1.0)
            return None

        def on_message(payload):
            delivered.append(payload)
            time.sleep(0.01)

        scheduler.add_task("slow", logic, message_method=on_message)
        scheduler.set_message_ingest_limit(None)
        scheduler.set_message_dispatch_limit(None)
        scheduler.set_message_dispatch_time_budget_ms(1.0)

        # Submit the task so send_message observes an active task with callback.
        scheduler.update()
        scheduler.send_message("slow", 1)
        scheduler.send_message("slow", 2)
        scheduler.send_message("slow", 3)

        scheduler.update()
        self.assertEqual(delivered, [1])

        scheduler.update()
        scheduler.update()
        self.assertEqual(delivered, [1, 2, 3])

        gate.set()
        scheduler.shutdown()

    def test_dispatch_time_budget_validation_and_readback(self) -> None:
        scheduler = TaskScheduler(max_workers=1)
        try:
            self.assertIsNone(scheduler.get_message_dispatch_time_budget_ms())
            scheduler.set_message_dispatch_time_budget_ms(2.5)
            self.assertEqual(scheduler.get_message_dispatch_time_budget_ms(), 2.5)
            scheduler.set_message_dispatch_time_budget_ms(None)
            self.assertIsNone(scheduler.get_message_dispatch_time_budget_ms())
            with self.assertRaises(ValueError):
                scheduler.set_message_dispatch_time_budget_ms(0)
            with self.assertRaises(ValueError):
                scheduler.set_message_dispatch_time_budget_ms(-1)
            with self.assertRaises(ValueError):
                scheduler.set_message_dispatch_time_budget_ms("bad")
        finally:
            scheduler.shutdown()

    def test_recommended_worker_count_reserves_ui_capacity(self) -> None:
        self.assertEqual(TaskScheduler.recommended_worker_count(logical_cpus=4), 3)
        self.assertEqual(TaskScheduler.recommended_worker_count(logical_cpus=1), 1)
        self.assertEqual(TaskScheduler.recommended_worker_count(logical_cpus=32), 4)
        self.assertEqual(TaskScheduler.recommended_worker_count(logical_cpus=8, reserve_for_ui=2, cap=6), 6)


if __name__ == "__main__":
    unittest.main()
