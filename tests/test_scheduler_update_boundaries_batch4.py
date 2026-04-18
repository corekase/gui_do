import unittest

from gui.utility.scheduler import Scheduler, Task


class SchedulerGuiStub:
    pass


class SchedulerUpdateBoundariesBatch4Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.scheduler = Scheduler(SchedulerGuiStub())

    def tearDown(self) -> None:
        self.scheduler.shutdown()

    def test_update_respects_ingest_and_dispatch_limits_across_cycles(self) -> None:
        observed = []

        def on_message(payload: object) -> None:
            observed.append(payload)

        self.scheduler.tasks["task"] = Task(
            id="task",
            run_callable=lambda: None,
            message_method=on_message,
            generation=1,
        )
        self.scheduler._task_generation["task"] = 1
        self.scheduler.set_message_ingest_limit(2)
        self.scheduler.set_message_dispatch_limit(1)

        for value in ["a", "b", "c"]:
            self.scheduler.send_message("task", value)

        finished_1 = self.scheduler.update()
        self.assertEqual(finished_1, [])
        self.assertEqual(observed, ["a"])
        self.assertEqual(self.scheduler._task_message_counts.get("task"), 2)

        finished_2 = self.scheduler.update()
        self.assertEqual(finished_2, [])
        self.assertEqual(observed, ["a", "b"])
        self.assertEqual(self.scheduler._task_message_counts.get("task"), 1)

        finished_3 = self.scheduler.update()
        self.assertEqual(finished_3, [])
        self.assertEqual(observed, ["a", "b", "c"])
        self.assertIsNone(self.scheduler._task_message_counts.get("task"))

    def test_update_drains_message_callback_failures_same_cycle(self) -> None:
        def failing_callback(_payload: object) -> None:
            raise RuntimeError("broken")

        self.scheduler.tasks["task"] = Task(
            id="task",
            run_callable=lambda: None,
            message_method=failing_callback,
            generation=1,
        )
        self.scheduler._task_generation["task"] = 1

        self.scheduler.send_message("task", "x")
        self.scheduler.update()

        failed = self.scheduler.get_failed_tasks()
        self.assertEqual(len(failed), 1)
        self.assertEqual(failed[0][0], "task")
        self.assertIn("Task message callback failed: RuntimeError: broken", failed[0][1])

    def test_update_with_zero_message_work_keeps_busy_false(self) -> None:
        self.assertFalse(self.scheduler.tasks_busy())
        finished = self.scheduler.update()
        self.assertEqual(finished, [])
        self.assertFalse(self.scheduler.tasks_busy())


if __name__ == "__main__":
    unittest.main()
