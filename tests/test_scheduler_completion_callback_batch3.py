import unittest
from concurrent.futures import Future

from gui.utility.scheduler import Scheduler, Task


class SchedulerGuiStub:
    pass


class ExecutorStub:
    def __init__(self, future: Future[object]) -> None:
        self._future = future

    def submit(self, _callable):
        return self._future

    def shutdown(self, wait: bool = False, cancel_futures: bool = True) -> None:
        return None


class SchedulerCompletionCallbackBatch3Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.scheduler = Scheduler(SchedulerGuiStub())

    def tearDown(self) -> None:
        self.scheduler.shutdown()

    def test_done_callback_stale_generation_is_ignored_after_readd(self) -> None:
        self.scheduler.add_task("task", lambda _task_id: "old")
        old_future: Future[object] = Future()
        self.scheduler._executor = ExecutorStub(old_future)

        with self.scheduler._lock:
            self.scheduler._submit_ready_tasks()

        old_generation = self.scheduler._task_generation["task"]
        old_future.set_result("old-result")

        self.scheduler.remove_tasks("task")
        self.scheduler.add_task("task", lambda _task_id: "fresh")
        fresh_generation = self.scheduler._task_generation["task"]
        self.assertGreater(fresh_generation, old_generation)

        with self.scheduler._lock:
            self.scheduler._collect_finished_tasks()

        self.assertEqual(self.scheduler.get_finished_tasks(), [])
        self.assertNotEqual(self.scheduler.pop_result("task", default=None), "old-result")

    def test_collect_finished_tasks_ignores_completion_with_mismatched_future(self) -> None:
        expected_future: Future[object] = Future()
        other_future: Future[object] = Future()
        other_future.set_result("wrong")

        self.scheduler.tasks["task"] = Task(
            id="task",
            run_callable=lambda: None,
            message_method=None,
            future=expected_future,
            generation=1,
        )
        self.scheduler._task_generation["task"] = 1
        self.scheduler._running.add("task")

        self.scheduler._enqueue_task_completion("task", 1, other_future)

        with self.scheduler._lock:
            self.scheduler._collect_finished_tasks()

        self.assertEqual(self.scheduler.get_finished_tasks(), [])
        self.assertIn("task", self.scheduler.tasks)
        self.assertIn("task", self.scheduler._running)

    def test_collect_finished_tasks_ignores_completion_when_task_missing(self) -> None:
        future: Future[object] = Future()
        future.set_result("ghost")

        self.scheduler._task_generation["ghost"] = 1
        self.scheduler._running.add("ghost")
        self.scheduler._enqueue_task_completion("ghost", 1, future)

        with self.scheduler._lock:
            self.scheduler._collect_finished_tasks()

        self.assertEqual(self.scheduler.get_finished_tasks(), [])
        self.assertIn("ghost", self.scheduler._running)


if __name__ == "__main__":
    unittest.main()
