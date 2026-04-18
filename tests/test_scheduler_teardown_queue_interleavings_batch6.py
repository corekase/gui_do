import unittest
from concurrent.futures import Future

from gui.utility.scheduler import Scheduler, Task


class SchedulerGuiStub:
    pass


class SchedulerTeardownQueueInterleavingsBatch6Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.scheduler = Scheduler(SchedulerGuiStub())

    def tearDown(self) -> None:
        self.scheduler.shutdown()

    def test_update_ignores_preloaded_completion_after_remove_all(self) -> None:
        done_future: Future[object] = Future()
        done_future.set_result("old-result")

        self.scheduler.tasks["task"] = Task(
            id="task",
            run_callable=lambda: None,
            message_method=None,
            future=done_future,
            generation=1,
        )
        self.scheduler._task_generation["task"] = 1
        self.scheduler._running.add("task")
        self.scheduler._enqueue_task_completion("task", 1, done_future)

        self.scheduler.remove_all()
        finished = self.scheduler.update()

        self.assertEqual(finished, [])
        self.assertEqual(self.scheduler.get_finished_tasks(), [])
        self.assertIsNone(self.scheduler.pop_result("task", default=None))

    def test_update_ignores_preloaded_failure_after_remove_all(self) -> None:
        self.scheduler.add_task("task", lambda _task_id: None)
        self.scheduler._enqueue_task_failure("task", self.scheduler._task_generation["task"], "old-failure")

        self.scheduler.remove_all()
        self.scheduler.update()

        self.assertEqual(self.scheduler.get_failed_tasks(), [])

    def test_update_with_mixed_preloaded_queues_after_remove_all_stays_clean(self) -> None:
        good_future: Future[object] = Future()
        good_future.set_result("value")

        self.scheduler.tasks["a"] = Task(id="a", run_callable=lambda: None, message_method=None, future=good_future, generation=1)
        self.scheduler._task_generation["a"] = 1
        self.scheduler._running.add("a")
        self.scheduler._enqueue_task_completion("a", 1, good_future)
        self.scheduler._enqueue_task_failure("a", 1, "stale-failure")

        self.scheduler.remove_all()
        finished = self.scheduler.update()

        self.assertEqual(finished, [])
        self.assertEqual(self.scheduler.get_finished_tasks(), [])
        self.assertEqual(self.scheduler.get_failed_tasks(), [])
        self.assertEqual(self.scheduler.tasks, {})
        self.assertEqual(list(self.scheduler._pending), [])
        self.assertEqual(self.scheduler.read_suspended(), [])


if __name__ == "__main__":
    unittest.main()
