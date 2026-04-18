import unittest
from concurrent.futures import Future

from gui.utility.scheduler import Scheduler, Task


class SchedulerGuiStub:
    pass


class SchedulerCompletionQueueFilteringBatch10Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.scheduler = Scheduler(SchedulerGuiStub())

    def tearDown(self) -> None:
        self.scheduler.shutdown()

    def test_update_collects_only_valid_completion_from_mixed_queue(self) -> None:
        expected_future: Future[object] = Future()
        expected_future.set_result("ok")
        mismatched_future: Future[object] = Future()
        mismatched_future.set_result("wrong")
        stale_future: Future[object] = Future()
        stale_future.set_result("stale")

        self.scheduler.tasks["task"] = Task(
            id="task",
            run_callable=lambda: None,
            message_method=None,
            future=expected_future,
            generation=2,
        )
        self.scheduler._task_generation["task"] = 2
        self.scheduler._running.add("task")

        self.scheduler._enqueue_task_completion("task", 1, stale_future)
        self.scheduler._enqueue_task_completion("task", 2, mismatched_future)
        self.scheduler._enqueue_task_completion("task", 2, expected_future)

        finished = self.scheduler.update()

        self.assertEqual(finished, ["task"])
        self.assertEqual(self.scheduler.get_finished_tasks(), ["task"])
        self.assertEqual(self.scheduler.pop_result("task"), "ok")
        self.assertNotIn("task", self.scheduler.tasks)

    def test_update_ignores_all_invalid_completions_and_leaves_task_running(self) -> None:
        expected_future: Future[object] = Future()
        stale_future: Future[object] = Future()
        stale_future.set_result("stale")
        mismatched_future: Future[object] = Future()
        mismatched_future.set_result("wrong")

        self.scheduler.tasks["task"] = Task(
            id="task",
            run_callable=lambda: None,
            message_method=None,
            future=expected_future,
            generation=3,
        )
        self.scheduler._task_generation["task"] = 3
        self.scheduler._running.add("task")

        self.scheduler._enqueue_task_completion("task", 2, stale_future)
        self.scheduler._enqueue_task_completion("task", 3, mismatched_future)

        finished = self.scheduler.update()

        self.assertEqual(finished, [])
        self.assertEqual(self.scheduler.get_finished_tasks(), [])
        self.assertIn("task", self.scheduler.tasks)
        self.assertIn("task", self.scheduler._running)


if __name__ == "__main__":
    unittest.main()
