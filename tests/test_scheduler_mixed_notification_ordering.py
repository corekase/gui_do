import unittest
from concurrent.futures import Future

from gui.utility.scheduler import Scheduler, Task


class SchedulerGuiStub:
    pass


class SchedulerMixedNotificationOrderingBatch9Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.scheduler = Scheduler(SchedulerGuiStub())

    def tearDown(self) -> None:
        self.scheduler.shutdown()

    def test_update_reports_preloaded_failure_and_completion_failure_together(self) -> None:
        failing_future: Future[object] = Future()
        failing_future.set_exception(ValueError("boom"))

        self.scheduler.tasks["task"] = Task(
            id="task",
            run_callable=lambda: None,
            message_method=None,
            future=failing_future,
            generation=1,
        )
        self.scheduler._task_generation["task"] = 1
        self.scheduler._running.add("task")

        self.scheduler._task_generation["other"] = 4
        self.scheduler._enqueue_task_failure("other", 4, "preloaded")
        self.scheduler._enqueue_task_completion("task", 1, failing_future)

        finished = self.scheduler.update()
        failed = self.scheduler.get_failed_tasks()

        self.assertEqual(finished, [])
        self.assertEqual(len(failed), 2)
        self.assertIn(("other", "preloaded"), failed)
        self.assertTrue(any(item[0] == "task" and "ValueError: boom" in item[1] for item in failed))

    def test_update_filters_stale_preloaded_failure_while_keeping_completion_failure(self) -> None:
        failing_future: Future[object] = Future()
        failing_future.set_exception(RuntimeError("bad"))

        self.scheduler.tasks["task"] = Task(
            id="task",
            run_callable=lambda: None,
            message_method=None,
            future=failing_future,
            generation=3,
        )
        self.scheduler._task_generation["task"] = 3
        self.scheduler._running.add("task")

        self.scheduler._enqueue_task_failure("task", 2, "stale")
        self.scheduler._enqueue_task_completion("task", 3, failing_future)

        self.scheduler.update()
        failed = self.scheduler.get_failed_tasks()

        self.assertEqual(len(failed), 1)
        self.assertEqual(failed[0][0], "task")
        self.assertIn("RuntimeError: bad", failed[0][1])

    def test_update_with_preloaded_failure_does_not_pollute_next_cycle(self) -> None:
        self.scheduler._task_generation["task"] = 1
        self.scheduler._enqueue_task_failure("task", 1, "once")

        self.scheduler.update()
        self.assertEqual(self.scheduler.get_failed_tasks(), [("task", "once")])

        self.scheduler.update()
        self.assertEqual(self.scheduler.get_failed_tasks(), [])


if __name__ == "__main__":
    unittest.main()
