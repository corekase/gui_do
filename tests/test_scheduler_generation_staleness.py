import unittest
from concurrent.futures import Future

from gui.utility.scheduler import Scheduler, Task


class SchedulerGuiStub:
    pass


class SchedulerGenerationStalenessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.scheduler = Scheduler(SchedulerGuiStub())

    def tearDown(self) -> None:
        self.scheduler.shutdown()

    def test_stale_messages_from_removed_generation_are_dropped(self) -> None:
        observed = []

        def on_message(payload: object) -> None:
            observed.append(payload)

        self.scheduler.add_task("task", lambda task_id: None, message_method=on_message)
        first_generation = self.scheduler._task_generation["task"]

        self.scheduler.send_message("task", "old")

        self.scheduler.remove_tasks("task")
        self.scheduler.add_task("task", lambda task_id: None, message_method=on_message)
        second_generation = self.scheduler._task_generation["task"]

        self.assertGreater(second_generation, first_generation)

        self.scheduler.send_message("task", "new")

        self.scheduler._drain_incoming_task_messages()
        self.scheduler._dispatch_task_messages()

        self.assertEqual(observed, ["new"])
        self.assertIsNone(self.scheduler._task_message_counts.get("task"))

    def test_stale_completion_from_removed_generation_is_ignored(self) -> None:
        self.scheduler.add_task("task", lambda task_id: None)

        stale_generation = self.scheduler._task_generation["task"]
        stale_future: Future[object] = Future()
        stale_future.set_result("stale-result")
        stale_task = Task(
            id="task",
            run_callable=lambda: None,
            message_method=None,
            future=stale_future,
            generation=stale_generation,
        )
        self.scheduler.tasks["task"] = stale_task
        self.scheduler._running.add("task")

        self.scheduler.remove_tasks("task")
        self.scheduler.add_task("task", lambda task_id: None)
        fresh_generation = self.scheduler._task_generation["task"]
        self.assertGreater(fresh_generation, stale_generation)

        self.scheduler._enqueue_task_completion("task", stale_generation, stale_future)
        self.scheduler._collect_finished_tasks()

        self.assertEqual(self.scheduler.get_finished_tasks(), [])
        self.assertNotEqual(self.scheduler.pop_result("task", default=None), "stale-result")

    def test_stale_failure_from_removed_generation_is_ignored(self) -> None:
        self.scheduler.add_task("task", lambda task_id: None)
        stale_generation = self.scheduler._task_generation["task"]

        self.scheduler.remove_tasks("task")
        self.scheduler.add_task("task", lambda task_id: None)
        fresh_generation = self.scheduler._task_generation["task"]
        self.assertGreater(fresh_generation, stale_generation)

        self.scheduler._enqueue_task_failure("task", stale_generation, "stale-failure")
        self.scheduler._enqueue_task_failure("task", fresh_generation, "fresh-failure")
        self.scheduler._drain_incoming_task_failures()

        failed = self.scheduler.get_failed_tasks()
        self.assertEqual(failed, [("task", "fresh-failure")])


if __name__ == "__main__":
    unittest.main()
